"""Action loss 最適化 v2 — huge loss 分析を反映した補正項追加。

【追加補正項】
A. 強い手 × wet × SRP → raise 促進
  - if_strong_wet_srp: ストロング/ナッツ × (connected or monotone) × SRP → +X

B. 弱手 × 大 bet → fold 促進
  - if_air_bigbet: エア × bs ≥ 3 (overbet+) → -X

C. その他の huge loss 多いパターン
  - if_tp_conn_srp: TP+ × connected × SRP → +X (raise)
  - if_mid_dry_srp: ミドルペア × dry × SRP → +X (call、fold loss 回避)
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/ACTION_LOSS_FORMULA_V2.md"

RANKS = "23456789TJQKA"
MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIERS = ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]
BLS = ["dry","paired","connected","monotone"]
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
    if rvals[0]==rvals[1] or rvals[1]==rvals[2]: return "paired"
    if len(set(suits))==1: return "monotone"
    if rvals[0]-rvals[1] <=2 and rvals[1]-rvals[2] <=2: return "connected"
    return "dry"


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_h = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_h)
    except (ValueError, IndexError):
        return 0


print("Loading rows...")
records = []
n_skip = 0
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", "")
        bs_str = r.get("ip_bet_size", "")
        if mv not in MV_TIER_MAP or bs_str not in BS_BASE: n_skip+=1; continue
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
        records.append({
            "tier_idx": TIERS.index(tier),
            "bl_idx": BLS.index(bl),
            "dv": DV_BASE.get(r.get("dv_cat", "no_draw"), 0),
            "opp_r": OPP_R[parse_pot(r["scenario_id"])],
            "bs": BS_BASE[bs_str],
            "oc": hero_oc(ca, cb, board),
            "best_action": {"fold":0,"call":1,"raise":2}[ba],
            "ev_fold": efv, "ev_call": ecv, "ev_raise": erv, "best_ev": be,
            "pot": parse_pot(r["scenario_id"]),
        })

print(f"Loaded {len(records):,} records ({n_skip} skipped)")
N = len(records)

# Pre-compute arrays
tier_idx_arr = np.array([r["tier_idx"] for r in records], dtype=np.int8)
bl_idx_arr = np.array([r["bl_idx"] for r in records], dtype=np.int8)
dv_arr = np.array([r["dv"] for r in records], dtype=np.float32)
opp_arr = np.array([r["opp_r"] for r in records], dtype=np.float32)
bs_arr = np.array([r["bs"] for r in records], dtype=np.float32)
oc_arr = np.array([r["oc"] for r in records], dtype=np.float32)
best_actions_arr = np.array([r["best_action"] for r in records], dtype=np.int8)
ev_arr = np.stack([[r["ev_fold"], r["ev_call"], r["ev_raise"]] for r in records]).astype(np.float32)
best_evs_arr = np.array([r["best_ev"] for r in records], dtype=np.float32)
pot_arr = np.array([{"SRP":0,"DEF":1,"3BP":2,"4BP":3}[r["pot"]] for r in records], dtype=np.int8)
grid_idx_arr = (tier_idx_arr.astype(np.int32) * 4 + bl_idx_arr.astype(np.int32))

# Masks for new corrections
is_strong_or_nut = (tier_idx_arr >= 4).astype(np.float32)  # ストロング/ナッツ
is_air = (tier_idx_arr == 0).astype(np.float32)
is_mp = (tier_idx_arr == 1).astype(np.float32)
is_tp = (tier_idx_arr == 2).astype(np.float32)
is_wet = ((bl_idx_arr == 2) | (bl_idx_arr == 3)).astype(np.float32)  # connected or monotone
is_conn = (bl_idx_arr == 2).astype(np.float32)
is_dry = (bl_idx_arr == 0).astype(np.float32)
is_paired = (bl_idx_arr == 1).astype(np.float32)
is_mono = (bl_idx_arr == 3).astype(np.float32)
is_srp = (pot_arr == 0).astype(np.float32)
is_3bp = (pot_arr == 2).astype(np.float32)
is_4bp = (pot_arr == 3).astype(np.float32)
is_bigbet = (bs_arr >= 3).astype(np.float32)  # overbet 以上

# Interaction features
i_strong_wet_srp = is_strong_or_nut * is_wet * is_srp
i_strong_dry_srp = is_strong_or_nut * is_dry * is_srp
i_strong_paired_srp = is_strong_or_nut * is_paired * is_srp
i_tp_conn_srp = is_tp * is_conn * is_srp
i_mid_dry_srp = is_mp * is_dry * is_srp
i_air_bigbet = is_air * is_bigbet
i_air_paired_3bp = is_air * is_paired * is_3bp
i_air_paired_4bp = is_air * is_paired * is_4bp
i_air_mono_4bp = is_air * is_mono * is_4bp


def evaluate(params):
    grid = np.array([params[f"g_{t}_{b}"] for t in range(6) for b in range(4)], dtype=np.float32)
    eq_score = grid[grid_idx_arr] + params["w_dv"] * dv_arr + params["w_oc"] * oc_arr
    action_score = (params["w_tier"] * tier_idx_arr.astype(np.float32)
                    + eq_score
                    + params["w_pot"] * opp_arr
                    - params["w_bs"] * bs_arr
                    + params["intercept"]
                    # NEW corrections
                    + params["c_strong_wet_srp"] * i_strong_wet_srp
                    + params["c_strong_dry_srp"] * i_strong_dry_srp
                    + params["c_strong_paired_srp"] * i_strong_paired_srp
                    + params["c_tp_conn_srp"] * i_tp_conn_srp
                    + params["c_mid_dry_srp"] * i_mid_dry_srp
                    + params["c_air_bigbet"] * i_air_bigbet
                    + params["c_air_paired_3bp"] * i_air_paired_3bp
                    + params["c_air_paired_4bp"] * i_air_paired_4bp
                    + params["c_air_mono_4bp"] * i_air_mono_4bp)
    preds = np.where(action_score >= params["t_raise"], 2,
                     np.where(action_score >= params["t_call"], 1, 0)).astype(np.int8)
    pred_evs = ev_arr[np.arange(N), preds]
    losses = np.maximum(0, best_evs_arr - pred_evs)
    acc = float((preds == best_actions_arr).mean() * 100)
    avg_loss = float(losses.mean())
    huge = float((losses > 5).mean() * 100)
    return acc, avg_loss, huge


def objective_loss(trial):
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
    # corrections
    params["c_strong_wet_srp"] = trial.suggest_float("c_strong_wet_srp", -5, 20)
    params["c_strong_dry_srp"] = trial.suggest_float("c_strong_dry_srp", -5, 20)
    params["c_strong_paired_srp"] = trial.suggest_float("c_strong_paired_srp", -5, 20)
    params["c_tp_conn_srp"] = trial.suggest_float("c_tp_conn_srp", -5, 20)
    params["c_mid_dry_srp"] = trial.suggest_float("c_mid_dry_srp", -5, 10)
    params["c_air_bigbet"] = trial.suggest_float("c_air_bigbet", -20, 5)
    params["c_air_paired_3bp"] = trial.suggest_float("c_air_paired_3bp", -20, 5)
    params["c_air_paired_4bp"] = trial.suggest_float("c_air_paired_4bp", -20, 5)
    params["c_air_mono_4bp"] = trial.suggest_float("c_air_mono_4bp", -20, 5)
    t_call = trial.suggest_float("t_call", -10, 15)
    t_raise = trial.suggest_float("t_raise", t_call + 0.5, 40)
    params["t_call"] = t_call
    params["t_raise"] = t_raise
    _, avg_loss, _ = evaluate(params)
    return avg_loss


optuna.logging.set_verbosity(optuna.logging.WARNING)
print(f"\n=== Optuna: minimize avg_loss with 9 corrections (2000 trials) ===")
study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective_loss, n_trials=2000, show_progress_bar=True)
best = study.best_params
acc_b, avg_b, huge_b = evaluate(best)
print(f"\nBest: acc={acc_b:.2f}%, avg_loss={avg_b:.4f} BB, huge={huge_b:.2f}%")

# Integer
def int_params(p):
    out = {k: round(v) for k, v in p.items() if k.startswith("g_") or k.startswith("w_") or k.startswith("c_") or k == "intercept"}
    out["t_call"] = round(p["t_call"])
    out["t_raise"] = max(out["t_call"]+1, round(p["t_raise"]))
    return out

ip = int_params(best)
acc_i, avg_i, huge_i = evaluate(ip)
print(f"\nInteger: acc={acc_i:.2f}%, avg_loss={avg_i:.4f}, huge={huge_i:.2f}%")

print(f"\n=== New corrections (連続) ===")
for k in sorted(best.keys()):
    if k.startswith("c_"):
        print(f"  {k:24} = {best[k]:+.3f}  (int: {ip[k]:+d})")

print(f"\n=== Grid ===")
print(f"{'tier':16}", end=" ")
for bl in BLS: print(f"{bl:>10}", end=" ")
print()
for t in range(6):
    print(f"  {TIERS[t]:14}", end=" ")
    for b in range(4):
        print(f"{best[f'g_{t}_{b}']:>9.2f}", end=" ")
    print()

print(f"\nBase weights:")
for k in ["w_tier","w_dv","w_oc","w_pot","w_bs","intercept","t_call","t_raise"]:
    print(f"  {k:12} = {best[k]:+.3f} (int: {ip[k]:+d})")


# Report
lines = []
lines.append("# Action Loss 公式 v2 — 9 個の補正項追加")
lines.append("")
lines.append("v1 (avg loss 0.48 BB) に huge loss の主要 spot に対する補正項を追加。")
lines.append("")
lines.append("## 性能比較")
lines.append("")
lines.append(f"| variant | accuracy | avg loss | huge% |")
lines.append(f"|---|---:|---:|---:|")
lines.append(f"| **v2 連続** | {acc_b:.2f}% | **{avg_b:.4f} BB** | {huge_b:.2f}% |")
lines.append(f"| **v2 整数** | {acc_i:.2f}% | **{avg_i:.4f} BB** | {huge_i:.2f}% |")
lines.append(f"| v1 整数 (前回) | 66.5% | 0.48 BB | 2.28% |")
lines.append(f"| 既存公式 v9b/v15 | 59.5% | 1.86 BB | 9.65% |")
lines.append("")

lines.append("## 9 つの補正項 (整数)")
lines.append("")
lines.append("| 補正 | 値 | 効果 |")
lines.append("|------|---:|------|")
correction_meanings = {
    "c_strong_wet_srp": "ストロング/ナッツ × wet × SRP → raise 促進",
    "c_strong_dry_srp": "ストロング/ナッツ × dry × SRP → raise 促進",
    "c_strong_paired_srp": "ストロング/ナッツ × paired × SRP → raise 促進",
    "c_tp_conn_srp": "TP+ × connected × SRP → raise 検討",
    "c_mid_dry_srp": "ミドルペア × dry × SRP → call 維持",
    "c_air_bigbet": "エア × bs ≥ overbet → fold 促進",
    "c_air_paired_3bp": "エア × paired × 3BP → fold 促進",
    "c_air_paired_4bp": "エア × paired × 4BP → fold 促進",
    "c_air_mono_4bp": "エア × monotone × 4BP → fold 促進",
}
for k in sorted(best.keys()):
    if k.startswith("c_"):
        lines.append(f"| {k} | {ip[k]:+d} | {correction_meanings.get(k, '')} |")
lines.append("")

lines.append("## 公式 (整数版)")
lines.append("")
lines.append("```")
lines.append(f"Score = {ip['w_tier']} × tier_idx + GridBase[tier][board]")
lines.append(f"      + {ip['w_dv']} × DV + {ip['w_oc']} × overcards")
lines.append(f"      + {ip['w_pot']} × pot - {ip['w_bs']} × bs + ({ip['intercept']})")
lines.append("      + 補正項 (該当する spot のみ):")
for k in sorted(best.keys()):
    if k.startswith("c_") and ip[k] != 0:
        lines.append(f"        if {correction_meanings.get(k, k)}: {ip[k]:+d}")
lines.append("")
lines.append(f"if Score >= {ip['t_raise']}: raise")
lines.append(f"elif Score >= {ip['t_call']}: call")
lines.append("else: fold")
lines.append("```")
lines.append("")

lines.append("## Grid 表 (整数)")
lines.append("")
lines.append("| tier | dry | paired | connected | monotone |")
lines.append("|------|---:|---:|---:|---:|")
for t in range(6):
    row = f"| {TIERS[t]} |"
    for b in range(4):
        v = round(best[f"g_{t}_{b}"])
        row += f" {v} |"
    lines.append(row)
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
