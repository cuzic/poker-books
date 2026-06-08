"""Grid 9 cell + 補正 4 個に圧縮した action loss 最適化 v3。

【Grid 圧縮: 24 → 9 cells】
- tier 6 → 3:
  - 強 (ナッツメイド + ストロング)
  - 中 (ツーペア + TP+)
  - 弱 (ミドルペア + エア)
- board 4 → 3:
  - dry
  - paired
  - wet (connected + monotone)
→ 3 × 3 = 9 cells

【補正圧縮: 9 → 4】
- C1 (強手 × paired/wet × SRP → raise): 旧 c_strong_paired_srp + c_strong_wet_srp
- C2 (TP+ × connected × SRP → raise): 旧 c_tp_conn_srp
- C3 (エア × 大 bet/3-4BP 特殊 board → fold): 旧 c_air_bigbet + c_air_paired_3bp/4bp + c_air_mono_4bp
- C4 (ミドル × dry × SRP → call): 旧 c_mid_dry_srp

【期待】 パラメータ数 41 → 9 + 6 + 4 + 2 = 21 で over-fit 回避
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/ACTION_LOSS_COMPRESSED.md"

RANKS = "23456789TJQKA"
MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}

# 圧縮 tier: 6 → 3
TIER_COMPACT = {
    "ナッツメイド":2, "ストロング":2,   # 強
    "ツーペア":1, "トップペア以上":1,   # 中
    "ミドルペア":0, "エア":0,           # 弱
}
TIER_NAMES = ["弱(MP/エア)", "中(2P/TP+)", "強(ナッツ/ストロング)"]
# Original tier_idx for tier × board interaction
TIERS_ORIG = ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]
BLS_ORIG = ["dry","paired","connected","monotone"]

# 圧縮 board: 4 → 3
def board_compact(bl_orig_idx):
    if bl_orig_idx == 0: return 0  # dry
    if bl_orig_idx == 1: return 1  # paired
    return 2  # wet (connected/monotone)
BL_NAMES = ["dry", "paired", "wet"]

DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_label(board: str) -> int:
    if len(board) < 6: return 0
    cards = [board[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return 0
    suits = [c[1].lower() for c in cards]
    if rvals[0]==rvals[1] or rvals[1]==rvals[2]: return 1  # paired
    if len(set(suits))==1: return 3  # monotone
    if rvals[0]-rvals[1] <=2 and rvals[1]-rvals[2] <=2: return 2  # connected
    return 0  # dry


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_h = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_h)
    except (ValueError, IndexError):
        return 0


print("Loading...")
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
        bl_orig = board_label(board)
        records.append({
            "tier_orig": TIERS_ORIG.index(tier),
            "tier_c": TIER_COMPACT[tier],
            "bl_orig": bl_orig,
            "bl_c": board_compact(bl_orig),
            "dv": DV_BASE.get(r.get("dv_cat", "no_draw"), 0),
            "opp_r": OPP_R[parse_pot(r["scenario_id"])],
            "bs": BS_BASE[bs_str],
            "oc": hero_oc(ca, cb, board),
            "best_action": {"fold":0,"call":1,"raise":2}[ba],
            "ev_fold": efv, "ev_call": ecv, "ev_raise": erv, "best_ev": be,
            "pot": parse_pot(r["scenario_id"]),
        })

N = len(records)
print(f"Loaded {N:,} rows ({n_skip} skipped)")

tier_orig_arr = np.array([r["tier_orig"] for r in records], dtype=np.int8)
tier_c_arr = np.array([r["tier_c"] for r in records], dtype=np.int8)
bl_orig_arr = np.array([r["bl_orig"] for r in records], dtype=np.int8)
bl_c_arr = np.array([r["bl_c"] for r in records], dtype=np.int8)
dv_arr = np.array([r["dv"] for r in records], dtype=np.float32)
opp_arr = np.array([r["opp_r"] for r in records], dtype=np.float32)
bs_arr = np.array([r["bs"] for r in records], dtype=np.float32)
oc_arr = np.array([r["oc"] for r in records], dtype=np.float32)
best_actions_arr = np.array([r["best_action"] for r in records], dtype=np.int8)
ev_arr = np.stack([[r["ev_fold"], r["ev_call"], r["ev_raise"]] for r in records]).astype(np.float32)
best_evs_arr = np.array([r["best_ev"] for r in records], dtype=np.float32)
pot_arr = np.array([{"SRP":0,"DEF":1,"3BP":2,"4BP":3}[r["pot"]] for r in records], dtype=np.int8)
grid_c_idx = (tier_c_arr.astype(np.int32) * 3 + bl_c_arr.astype(np.int32))

# Masks for 4 compressed corrections
is_strong = (tier_c_arr == 2).astype(np.float32)
is_mid = (tier_c_arr == 1).astype(np.float32)
is_weak = (tier_c_arr == 0).astype(np.float32)
is_tp = ((tier_orig_arr == 2)).astype(np.float32)  # TP+ specifically
is_air = ((tier_orig_arr == 0)).astype(np.float32)
is_mp = ((tier_orig_arr == 1)).astype(np.float32)
is_dry_c = (bl_c_arr == 0).astype(np.float32)
is_paired_c = (bl_c_arr == 1).astype(np.float32)
is_wet_c = (bl_c_arr == 2).astype(np.float32)
is_conn_orig = (bl_orig_arr == 2).astype(np.float32)
is_srp = (pot_arr == 0).astype(np.float32)
is_3bp_4bp = ((pot_arr == 2) | (pot_arr == 3)).astype(np.float32)
is_bigbet = (bs_arr >= 3).astype(np.float32)

# Compressed corrections (4 個)
i_C1 = is_strong * (is_paired_c + is_wet_c).clip(0,1) * is_srp  # 強手 × wet/paired × SRP
i_C2 = is_tp * is_conn_orig * is_srp                            # TP+ × connected × SRP
i_C3 = is_air * (is_bigbet + is_3bp_4bp * (is_paired_c + is_wet_c)).clip(0,1)  # エア × {大bet | 3-4BP 特殊board}
i_C4 = is_mp * is_dry_c * is_srp                                # ミドル × dry × SRP


def evaluate(params):
    grid = np.array([params[f"g_{t}_{b}"] for t in range(3) for b in range(3)], dtype=np.float32)
    eq_score = grid[grid_c_idx] + params["w_dv"] * dv_arr + params["w_oc"] * oc_arr
    action_score = (params["w_tier"] * tier_orig_arr.astype(np.float32)
                    + eq_score
                    + params["w_pot"] * opp_arr
                    - params["w_bs"] * bs_arr
                    + params["intercept"]
                    + params["C1"] * i_C1
                    + params["C2"] * i_C2
                    + params["C3"] * i_C3
                    + params["C4"] * i_C4)
    preds = np.where(action_score >= params["t_raise"], 2,
                     np.where(action_score >= params["t_call"], 1, 0)).astype(np.int8)
    pred_evs = ev_arr[np.arange(N), preds]
    losses = np.maximum(0, best_evs_arr - pred_evs)
    acc = float((preds == best_actions_arr).mean() * 100)
    avg_loss = float(losses.mean())
    huge = float((losses > 5).mean() * 100)
    return acc, avg_loss, huge


def objective(trial):
    params = {}
    for t in range(3):
        for b in range(3):
            params[f"g_{t}_{b}"] = trial.suggest_float(f"g_{t}_{b}", 0, 12)
    params["w_dv"] = trial.suggest_float("w_dv", 0, 3)
    params["w_oc"] = trial.suggest_float("w_oc", -2, 2)
    params["w_tier"] = trial.suggest_float("w_tier", 0, 4)
    params["w_pot"] = trial.suggest_float("w_pot", 0, 3)
    params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
    params["intercept"] = trial.suggest_float("intercept", -10, 10)
    params["C1"] = trial.suggest_float("C1", -5, 20)
    params["C2"] = trial.suggest_float("C2", -5, 20)
    params["C3"] = trial.suggest_float("C3", -20, 5)
    params["C4"] = trial.suggest_float("C4", -10, 10)
    t_call = trial.suggest_float("t_call", -10, 15)
    t_raise = trial.suggest_float("t_raise", t_call + 0.5, 40)
    params["t_call"] = t_call; params["t_raise"] = t_raise
    _, avg_loss, _ = evaluate(params)
    return avg_loss


optuna.logging.set_verbosity(optuna.logging.WARNING)
print(f"\n=== Optuna: 21 params, minimize avg_loss (3000 trials) ===")
study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=3000, show_progress_bar=True)
best = study.best_params
acc_b, avg_b, huge_b = evaluate(best)
print(f"\nBest (連続): acc={acc_b:.2f}%, avg_loss={avg_b:.4f} BB, huge={huge_b:.2f}%")

# Integer
def int_params(p):
    out = {k: round(v) for k, v in p.items() if k.startswith("g_") or k.startswith("w_") or k in ("C1","C2","C3","C4","intercept")}
    out["t_call"] = round(p["t_call"])
    out["t_raise"] = max(out["t_call"]+1, round(p["t_raise"]))
    return out

ip = int_params(best)
acc_i, avg_i, huge_i = evaluate(ip)
print(f"\nInteger: acc={acc_i:.2f}%, avg_loss={avg_i:.4f}, huge={huge_i:.2f}%")

print("\n=== Compressed Grid (3x3) ===")
print(f"{'tier':22}", end=" ")
for bl in BL_NAMES: print(f"{bl:>10}", end=" ")
print()
for t in range(3):
    print(f"  {TIER_NAMES[t]:20}", end=" ")
    for b in range(3):
        print(f"{best[f'g_{t}_{b}']:>9.2f}", end=" ")
    print()

print(f"\nBase: w_tier={best['w_tier']:.2f}, w_dv={best['w_dv']:.2f}, w_oc={best['w_oc']:.2f}, w_pot={best['w_pot']:.2f}, w_bs={best['w_bs']:.2f}, intercept={best['intercept']:.2f}")
print(f"Corrections: C1={best['C1']:+.2f}, C2={best['C2']:+.2f}, C3={best['C3']:+.2f}, C4={best['C4']:+.2f}")
print(f"Thresholds: t_call={best['t_call']:.2f}, t_raise={best['t_raise']:.2f}")

# Report
lines = []
lines.append("# Compressed Action Loss Formula (21 params)")
lines.append("")
lines.append("Grid 24→9 cells + 補正 9→4 個に圧縮、過剰適合回避。")
lines.append("")
lines.append("## 性能")
lines.append("")
lines.append(f"| variant | accuracy | avg loss | huge% |")
lines.append(f"|---|---:|---:|---:|")
lines.append(f"| **v3 連続 (21 params)** | {acc_b:.2f}% | **{avg_b:.4f} BB** | {huge_b:.2f}% |")
lines.append(f"| **v3 整数 (書籍向け)** | {acc_i:.2f}% | **{avg_i:.4f} BB** | {huge_i:.2f}% |")
lines.append(f"| v1 整数 (24 grid + no correction) | 66.5% | 0.48 BB | 2.28% |")
lines.append(f"| v2 整数 (24 grid + 9 corrections) | 64.2% | 0.65 BB | 3.16% |")
lines.append(f"| 既存公式 v9b/v15 | 59.5% | 1.86 BB | 9.65% |")
lines.append("")

lines.append("## Compressed Grid (3 tier × 3 board = 9 cells)")
lines.append("")
lines.append("| tier | dry | paired | wet (connected/mono) |")
lines.append("|------|---:|---:|---:|")
for t in range(3):
    row = f"| **{TIER_NAMES[t]}** |"
    for b in range(3):
        v = round(best[f'g_{t}_{b}'])
        row += f" {v} |"
    lines.append(row)
lines.append("")

lines.append("## 4 補正項")
lines.append("")
lines.append("| 補正 | 整数 | 意味 |")
lines.append("|------|---:|------|")
lines.append(f"| **C1** | {ip['C1']:+d} | 強手 × wet/paired × SRP → raise 促進 |")
lines.append(f"| **C2** | {ip['C2']:+d} | TP+ × connected × SRP → raise 促進 |")
lines.append(f"| **C3** | {ip['C3']:+d} | エア × {{overbet+ or 3-4BP 特殊board}} → fold 促進 |")
lines.append(f"| **C4** | {ip['C4']:+d} | ミドル × dry × SRP → call 維持 |")
lines.append("")

lines.append("## 公式 (整数版、書籍掲載可)")
lines.append("")
lines.append("```")
lines.append(f"Score = {ip['w_tier']} × tier_orig (0-5) + GridBase[tier_c][board_c]")
lines.append(f"      + {ip['w_dv']} × DV + {ip['w_oc']} × overcards")
lines.append(f"      + {ip['w_pot']} × pot - {ip['w_bs']} × bs + ({ip['intercept']})")
lines.append("      + 補正 (該当 spot のみ):")
lines.append(f"        if 強手 × wet/paired × SRP: {ip['C1']:+d}")
lines.append(f"        if TP+ × connected × SRP: {ip['C2']:+d}")
lines.append(f"        if エア × 大 bet/3-4BP 特殊: {ip['C3']:+d}")
lines.append(f"        if ミドル × dry × SRP: {ip['C4']:+d}")
lines.append("")
lines.append(f"if Score >= {ip['t_raise']}: raise")
lines.append(f"elif Score >= {ip['t_call']}: call")
lines.append("else: fold")
lines.append("```")
lines.append("")
lines.append("## 暗記負荷")
lines.append("")
lines.append("- Grid 9 cells (3×3 表)")
lines.append("- Base weights 6 個")
lines.append("- Corrections 4 個 (例外として暗記)")
lines.append("- 計 19 項目 (旧 v1 は 30+ 項目だった)")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
