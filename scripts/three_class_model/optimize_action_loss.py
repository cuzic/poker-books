"""action loss を直接 minimize する公式設計。

【設計】
1. eq_score = features の線形和 (eq_bucket を中間ステップにしない)
2. action_score = w_tier × tier + eq_score + w_pot × pot - w_bs × bs
3. action: action_score >= T_raise → raise, >= T_call → call, else fold
4. optuna で avg_loss (期待 EV 損失) を minimize

【メトリクス】
- best_action accuracy
- avg_loss = mean(max(0, best_ev - pred_ev))  ← これを最小化
- huge_loss = % of rows with loss > 5
- 公式 v9b/v10/v15 比較
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/ACTION_LOSS_FORMULA.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}
EQ_VAL = {"best_hands":9, "good_hands":6, "weak_hands":3, "trash_hands":0}

MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_BASE = {"ナッツメイド":5, "ストロング":4, "ツーペア":3,
             "トップペア以上":2, "ミドルペア":1, "エア":0}
DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_label(board: str) -> str:
    if len(board) < 6: return "dry"
    cards = [board[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return "dry"
    suits = [c[1].lower() for c in cards]
    if rvals[0] == rvals[1] or rvals[1] == rvals[2]: return "paired"
    if len(set(suits)) == 1: return "monotone"
    g1 = rvals[0] - rvals[1]; g2 = rvals[1] - rvals[2]
    if g1 <= 2 and g2 <= 2: return "connected"
    return "dry"


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper())
        b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_high = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_high)
    except (ValueError, IndexError):
        return 0


print("Loading rows + computing features...")
records = []
n_skip = 0
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", "")
        bs = r.get("ip_bet_size", "")
        if mv not in MV_TIER_MAP or bs not in BS_BASE: n_skip+=1; continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: n_skip+=1; continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb: n_skip+=1; continue
        try:
            ba = r["best_action"].lower()
            efv = float(r["ev_fold"]); ecv = float(r["ev_call"]); erv = float(r["ev_raise"])
            be = float(r["best_ev"])
        except (KeyError, ValueError):
            n_skip+=1; continue

        tier = MV_TIER_MAP[mv]
        bl = board_label(board)
        dv = DV_BASE.get(r.get("dv_cat", "no_draw"), 0)
        opp_r = OPP_R[parse_pot(r["scenario_id"])]
        bs_v = BS_BASE[bs]
        oc = hero_oc(ca, cb, board)

        records.append({
            "tier_idx": TIER_BASE[tier], "bl": bl, "dv": dv, "opp_r": opp_r,
            "bs": bs_v, "oc": oc,
            "best_action": ba,
            "ev_fold": efv, "ev_call": ecv, "ev_raise": erv, "best_ev": be,
        })

print(f"Loaded {len(records):,} records ({n_skip} skipped)")

N = len(records)
TIERS = ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]
BLS = ["dry","paired","connected","monotone"]
tier_idx_arr = np.array([r["tier_idx"] for r in records], dtype=np.int8)
bl_idx_arr = np.array([BLS.index(r["bl"]) for r in records], dtype=np.int8)
dv_arr = np.array([r["dv"] for r in records], dtype=np.float32)
opp_arr = np.array([r["opp_r"] for r in records], dtype=np.float32)
bs_arr = np.array([r["bs"] for r in records], dtype=np.float32)
oc_arr = np.array([r["oc"] for r in records], dtype=np.float32)
best_actions_arr = np.array([{"fold":0,"call":1,"raise":2}[r["best_action"]] for r in records], dtype=np.int8)
ev_arr = np.stack([[r["ev_fold"], r["ev_call"], r["ev_raise"]] for r in records]).astype(np.float32)
best_evs_arr = np.array([r["best_ev"] for r in records], dtype=np.float32)

# Grid: 6 tiers × 4 boards = 24 cells
# Will be optimized as 24 parameters
TIER_ORDER = ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]
# pre-compute grid index
grid_idx_arr = (tier_idx_arr.astype(np.int32) * 4 + bl_idx_arr.astype(np.int32))


def evaluate(params):
    """params: 24 grid values + 5 weights + 2 thresholds."""
    grid = np.array([params[f"g_{t}_{b}"] for t in range(6) for b in range(4)], dtype=np.float32)
    eq_score = grid[grid_idx_arr]  # lookup
    # eq adjustments
    eq_score = eq_score + params["w_dv"] * dv_arr + params["w_oc"] * oc_arr
    # action score
    action_score = (params["w_tier"] * tier_idx_arr.astype(np.float32)
                    + eq_score
                    + params["w_pot"] * opp_arr
                    - params["w_bs"] * bs_arr
                    + params["intercept"])
    preds = np.where(action_score >= params["t_raise"], 2,
                     np.where(action_score >= params["t_call"], 1, 0)).astype(np.int8)
    pred_evs = ev_arr[np.arange(N), preds]
    losses = np.maximum(0, best_evs_arr - pred_evs)
    acc = float((preds == best_actions_arr).mean() * 100)
    avg_loss = float(losses.mean())
    huge = float((losses > 5).mean() * 100)
    return acc, avg_loss, huge


def objective_loss(trial):
    """Minimize avg loss."""
    params = {}
    for t in range(6):
        for b in range(4):
            params[f"g_{t}_{b}"] = trial.suggest_float(f"g_{t}_{b}", 0, 10)
    params["w_dv"] = trial.suggest_float("w_dv", 0, 3)
    params["w_oc"] = trial.suggest_float("w_oc", -2, 2)
    params["w_tier"] = trial.suggest_float("w_tier", 0, 3)
    params["w_pot"] = trial.suggest_float("w_pot", 0, 3)
    params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
    params["intercept"] = trial.suggest_float("intercept", -10, 10)
    t_call = trial.suggest_float("t_call", -10, 15)
    t_raise = trial.suggest_float("t_raise", t_call + 0.5, 30)
    params["t_call"] = t_call
    params["t_raise"] = t_raise
    _, avg_loss, _ = evaluate(params)
    return avg_loss


def objective_acc(trial):
    """Maximize accuracy."""
    params = {}
    for t in range(6):
        for b in range(4):
            params[f"g_{t}_{b}"] = trial.suggest_float(f"g_{t}_{b}", 0, 10)
    params["w_dv"] = trial.suggest_float("w_dv", 0, 3)
    params["w_oc"] = trial.suggest_float("w_oc", -2, 2)
    params["w_tier"] = trial.suggest_float("w_tier", 0, 3)
    params["w_pot"] = trial.suggest_float("w_pot", 0, 3)
    params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
    params["intercept"] = trial.suggest_float("intercept", -10, 10)
    t_call = trial.suggest_float("t_call", -10, 15)
    t_raise = trial.suggest_float("t_raise", t_call + 0.5, 30)
    params["t_call"] = t_call
    params["t_raise"] = t_raise
    acc, _, _ = evaluate(params)
    return acc


optuna.logging.set_verbosity(optuna.logging.WARNING)

print("\n=== Optuna: minimize avg_loss (1500 trials) ===")
study_loss = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study_loss.optimize(objective_loss, n_trials=1500, show_progress_bar=True)
best_loss = study_loss.best_params
acc_l, avg_l, huge_l = evaluate(best_loss)
print(f"\nBest loss: acc={acc_l:.2f}%, avg_loss={avg_l:.4f} BB, huge={huge_l:.2f}%")

print("\n=== Optuna: maximize accuracy (1500 trials) ===")
study_acc = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study_acc.optimize(objective_acc, n_trials=1500, show_progress_bar=True)
best_acc = study_acc.best_params
acc_a, avg_a, huge_a = evaluate(best_acc)
print(f"\nBest acc: acc={acc_a:.2f}%, avg_loss={avg_a:.4f} BB, huge={huge_a:.2f}%")

# Integer version (from best_loss)
def int_params(p):
    out = {k: round(v) for k, v in p.items() if k.startswith("g_") or k.startswith("w_") or k == "intercept"}
    out["t_call"] = round(p["t_call"])
    out["t_raise"] = max(out["t_call"]+1, round(p["t_raise"]))
    return out

ip = int_params(best_loss)
acc_i, avg_i, huge_i = evaluate(ip)
print(f"\nInteger (from loss-opt): acc={acc_i:.2f}%, avg_loss={avg_i:.4f}, huge={huge_i:.2f}%")


# Grid display
print(f"\n=== Optimal Grid (loss-minimized) ===")
print(f"{'tier':16}", end=" ")
for bl in BLS: print(f"{bl:>10}", end=" ")
print()
for t in range(6):
    print(f"  {TIER_ORDER[t]:14}", end=" ")
    for b in range(4):
        v = best_loss[f"g_{t}_{b}"]
        print(f"{v:>9.2f}", end=" ")
    print()

print(f"\nWeights (loss-minimized):")
for k in ["w_tier","w_dv","w_oc","w_pot","w_bs","intercept","t_call","t_raise"]:
    print(f"  {k} = {best_loss[k]:+.3f}")


# Report
lines = []
lines.append("# Action Loss を直接最小化する公式")
lines.append("")
lines.append("eq_bucket accuracy を経由せず、最終 action の loss (期待 EV 損失) を直接 minimize。")
lines.append("")
lines.append("## 公式構造")
lines.append("")
lines.append("```")
lines.append("Step 1: eq_score = GridBase[tier][board] + w_dv × DV + w_oc × overcards")
lines.append("Step 2: action_score = w_tier × tier + eq_score + w_pot × pot - w_bs × bs + intercept")
lines.append("Step 3: action: >= T_raise raise / >= T_call call / else fold")
lines.append("```")
lines.append("")

lines.append("## 性能")
lines.append("")
lines.append(f"| variant | accuracy | avg loss | huge% |")
lines.append(f"|---|---:|---:|---:|")
lines.append(f"| **Loss-optimized (連続)** | {acc_l:.2f}% | **{avg_l:.4f} BB** | {huge_l:.2f}% |")
lines.append(f"| Acc-optimized (連続) | **{acc_a:.2f}%** | {avg_a:.4f} BB | {huge_a:.2f}% |")
lines.append(f"| Loss-optimized (整数) | {acc_i:.2f}% | {avg_i:.4f} BB | {huge_i:.2f}% |")
lines.append(f"| (参考) tier+eq 旧式 (eq 真値) | 71.0% | 0.34 BB | 1.22% |")
lines.append(f"| (参考) 既存公式 v9b/v15 | 59.5% | 1.86 BB | 9.65% |")
lines.append("")

lines.append("## Optimal Grid (loss-minimized、連続値)")
lines.append("")
lines.append("| tier | dry | paired | connected | monotone |")
lines.append("|------|---:|---:|---:|---:|")
for t in range(6):
    row = f"| {TIER_ORDER[t]} |"
    for b in range(4):
        v = best_loss[f"g_{t}_{b}"]
        row += f" {v:.2f} |"
    lines.append(row)
lines.append("")

lines.append("## 重み (loss-minimized)")
lines.append("")
lines.append("| 係数 | 連続 | 整数 |")
lines.append("|------|---:|---:|")
for k in ["w_tier","w_dv","w_oc","w_pot","w_bs","intercept"]:
    iv = ip.get(k, 0)
    lines.append(f"| {k} | {best_loss[k]:+.3f} | {iv:+d} |")
lines.append(f"| t_call | {best_loss['t_call']:.2f} | {ip['t_call']} |")
lines.append(f"| t_raise | {best_loss['t_raise']:.2f} | {ip['t_raise']} |")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
