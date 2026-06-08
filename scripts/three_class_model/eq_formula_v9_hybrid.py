"""暗算可能な計算式 — base 加算 + 主要 if-then 補正項。

【設計】
Step 1: base = MV + DV - OppR   (3 軸の単純加算)
Step 2: + 主要 if-then 補正 (interaction の手動エンコード)

【if-then 補正項】(RF importance + outlier 分析より)

A. mv_tier × board interaction:
  - ツーペア × paired board       → 大幅減点 (board crushed)
  - set × paired                  → 加点 (full house potential)
  - set × monotone/connected      → 減点 (vs flush/straight risk)
  - 強い made × monotone (not flush) → 減点
  - TP+ × paired                  → 減点

B. hero × board interaction:
  - hero_overpair × dry           → 加点
  - hero_overcards × wet          → 加点 (semi-bluff)
  - hero_overcards × dry          → 減点

C. 既存項目:
  - MV (made hand tier): 0-10
  - DV (draw value): 0-4
  - OppR (pot type): 0-3
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_FORMULA_V9.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}

# 6 tier ベース
MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_BASE = {"ナッツメイド":9, "ストロング":7, "ツーペア":6,
             "トップペア以上":4, "ミドルペア":2, "エア":0}
DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
OPP_R = {"SRP":0,"DEF":1,"3BP":2,"4BP":3}


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


def hero_features(card_a, card_b, board):
    """hero feat for interaction."""
    try:
        a_r = RANKS.index(card_a[0].upper())
        b_r = RANKS.index(card_b[0].upper())
        if a_r < b_r: a_r, b_r = b_r, a_r
        cards = [board[i*2:i*2+2] for i in range(3)]
        rvals = [RANKS.index(c[0].upper()) for c in cards]
        b_high = max(rvals)
        hero_pair = int(a_r == b_r)
        overpair = int(hero_pair and a_r > b_high)
        underpair = int(hero_pair and a_r < b_high)
        overcards = sum(1 for r in (a_r, b_r) if r > b_high)
        return overpair, underpair, overcards
    except (ValueError, IndexError):
        return 0, 0, 0


print("Loading rows + computing features...")
records = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", "")
        eq_b = r.get("equity_bucket", "")
        if eq_b not in EQ_LABEL_TO_IDX or mv not in MV_TIER_MAP: continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb: continue

        tier = MV_TIER_MAP[mv]
        bl = board_label(board)
        dv = DV_BASE.get(r.get("dv_cat", "no_draw"), 0)
        opp_r = OPP_R[parse_pot(r["scenario_id"])]
        op, up, oc = hero_features(ca, cb, board)

        records.append({
            "tier": tier, "bl": bl, "dv": dv, "opp_r": opp_r,
            "op": op, "up": up, "oc": oc,
            "y": EQ_LABEL_TO_IDX[eq_b],
        })

print(f"Loaded {len(records):,} records")

# Convert to arrays for fast evaluation
N = len(records)
TIERS = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]
BLS = ["dry","paired","connected","monotone"]
tier_idx_arr = np.array([TIERS.index(r["tier"]) for r in records], dtype=np.int8)
bl_idx_arr = np.array([BLS.index(r["bl"]) for r in records], dtype=np.int8)
mv_base_arr = np.array([TIER_BASE[r["tier"]] for r in records], dtype=np.float32)
dv_arr = np.array([r["dv"] for r in records], dtype=np.float32)
opp_arr = np.array([r["opp_r"] for r in records], dtype=np.float32)
op_arr = np.array([r["op"] for r in records], dtype=np.float32)
up_arr = np.array([r["up"] for r in records], dtype=np.float32)
oc_arr = np.array([r["oc"] for r in records], dtype=np.float32)
y_arr = np.array([r["y"] for r in records], dtype=np.int8)

# Pre-compute mask arrays for interactions
# Tier indices: 0=ナッツ, 1=ストロング, 2=ツーペア, 3=TP+, 4=MP, 5=エア
# BL indices: 0=dry, 1=paired, 2=connected, 3=monotone

is_strong = (tier_idx_arr <= 1).astype(np.float32)
is_2pair = (tier_idx_arr == 2).astype(np.float32)
is_tp = (tier_idx_arr == 3).astype(np.float32)
is_mp = (tier_idx_arr == 4).astype(np.float32)
is_air = (tier_idx_arr == 5).astype(np.float32)

is_dry = (bl_idx_arr == 0).astype(np.float32)
is_paired = (bl_idx_arr == 1).astype(np.float32)
is_conn = (bl_idx_arr == 2).astype(np.float32)
is_mono = (bl_idx_arr == 3).astype(np.float32)
is_wet = (is_conn + is_mono).clip(0, 1)

# Pre-compute interaction features
i_2pair_paired = is_2pair * is_paired
i_strong_paired = is_strong * is_paired
i_strong_mono = is_strong * is_mono
i_strong_conn = is_strong * is_conn
i_tp_paired = is_tp * is_paired
i_tp_mono = is_tp * is_mono
i_mp_dry = is_mp * is_dry
i_air_wet = is_air * is_wet
i_op_dry = op_arr * is_dry
i_op_wet = op_arr * is_wet
i_oc_wet = oc_arr * is_wet
i_oc_dry = oc_arr * is_dry


def predict_score(params):
    """params dict with w_*, t_*."""
    score = (params["w_mv"] * mv_base_arr
             + params["w_dv"] * dv_arr
             - params["w_opp"] * opp_arr
             # tier × board interactions
             + params["w_2pair_paired"] * i_2pair_paired
             + params["w_strong_paired"] * i_strong_paired
             + params["w_strong_mono"] * i_strong_mono
             + params["w_strong_conn"] * i_strong_conn
             + params["w_tp_paired"] * i_tp_paired
             + params["w_tp_mono"] * i_tp_mono
             + params["w_mp_dry"] * i_mp_dry
             + params["w_air_wet"] * i_air_wet
             # hero × board
             + params["w_op_dry"] * i_op_dry
             + params["w_op_wet"] * i_op_wet
             + params["w_oc_wet"] * i_oc_wet
             + params["w_oc_dry"] * i_oc_dry
             + params["intercept"])
    return score


def predict_bucket(params, t_weak, t_good, t_best):
    score = predict_score(params)
    preds = np.zeros(N, dtype=np.int8)
    preds = np.where(score >= t_weak, 1, preds)
    preds = np.where(score >= t_good, 2, preds)
    preds = np.where(score >= t_best, 3, preds)
    return preds


def objective(trial):
    params = {
        "w_mv": trial.suggest_float("w_mv", 0.5, 2.0),
        "w_dv": trial.suggest_float("w_dv", 0.0, 2.0),
        "w_opp": trial.suggest_float("w_opp", 0.0, 3.0),
        # tier × board interaction
        "w_2pair_paired": trial.suggest_float("w_2pair_paired", -10.0, 5.0),
        "w_strong_paired": trial.suggest_float("w_strong_paired", -5.0, 5.0),
        "w_strong_mono": trial.suggest_float("w_strong_mono", -5.0, 5.0),
        "w_strong_conn": trial.suggest_float("w_strong_conn", -5.0, 5.0),
        "w_tp_paired": trial.suggest_float("w_tp_paired", -5.0, 5.0),
        "w_tp_mono": trial.suggest_float("w_tp_mono", -5.0, 5.0),
        "w_mp_dry": trial.suggest_float("w_mp_dry", -5.0, 5.0),
        "w_air_wet": trial.suggest_float("w_air_wet", -5.0, 5.0),
        # hero × board
        "w_op_dry": trial.suggest_float("w_op_dry", -3.0, 3.0),
        "w_op_wet": trial.suggest_float("w_op_wet", -3.0, 3.0),
        "w_oc_wet": trial.suggest_float("w_oc_wet", -2.0, 3.0),
        "w_oc_dry": trial.suggest_float("w_oc_dry", -3.0, 2.0),
        "intercept": trial.suggest_float("intercept", -10.0, 5.0),
    }
    t_weak = trial.suggest_float("t_weak", -10.0, 5.0)
    t_good = trial.suggest_float("t_good", t_weak + 0.1, 10.0)
    t_best = trial.suggest_float("t_best", t_good + 0.1, 20.0)
    preds = predict_bucket(params, t_weak, t_good, t_best)
    return float((preds == y_arr).mean() * 100)


print(f"\n=== Optuna 1000 trials ===")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=1000, show_progress_bar=True)

best = study.best_params
print(f"\nBest accuracy: {study.best_value:.2f}%")
print(f"Params:")
for k, v in sorted(best.items()):
    print(f"  {k:18} = {v:+.3f}")

# Integer version
print(f"\n=== Integer rounded ===")
int_params = {k: round(v) for k, v in best.items() if k.startswith("w_") or k == "intercept"}
int_tw = round(best["t_weak"])
int_tg = max(int_tw+1, round(best["t_good"]))
int_tb = max(int_tg+1, round(best["t_best"]))
preds_int = predict_bucket(int_params, int_tw, int_tg, int_tb)
acc_int = float((preds_int == y_arr).mean() * 100)
print(f"Integer accuracy: {acc_int:.2f}%")
print(f"Params:")
for k, v in sorted(int_params.items()):
    if v != 0:
        print(f"  {k:18} = {v:+d}")
print(f"Thresholds: t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")


# Report
lines = []
lines.append("# 暗算可能な eq 計算式 v9 — base + if-then 補正")
lines.append("")
lines.append("線形 base + 主要 interaction の if-then 補正項を data 駆動で学習。")
lines.append("")
lines.append("## 性能")
lines.append("")
lines.append(f"| variant | accuracy |")
lines.append(f"|---|---:|")
lines.append(f"| **v9 連続** | **{study.best_value:.2f}%** |")
lines.append(f"| **v9 整数 (書籍向け)** | **{acc_int:.2f}%** |")
lines.append(f"| (参考) Grid + 線形 (60.42%) | 60.42% |")
lines.append(f"| (参考) DT depth 5 | 64.32% |")
lines.append(f"| (参考) RF (上限) | 76.61% |")
lines.append("")

lines.append("## 公式 (整数版)")
lines.append("")
lines.append("```")
lines.append("Score = w_mv × MV + w_dv × DV − w_opp × OppR + intercept")
lines.append("")
lines.append("MV (made tier):  ナッツ=9, ストロング=7, ツーペア=6,")
lines.append("                 TP+=4, MP=2, エア=0")
lines.append("DV (draw):       combo=4, NFD/FD/OESD=3, gutshot=1, BDFD=1, none=0")
lines.append("OppR (pot):      SRP=0, DEF=1, 3BP=2, 4BP=3")
lines.append("")
lines.append("+ if-then 補正項:")
for k, v in sorted(int_params.items()):
    if v != 0 and k.startswith("w_") and k not in ("w_mv","w_dv","w_opp"):
        lines.append(f"  if {k[2:]:18} : {v:+d}")
lines.append("")
lines.append(f"if Score >= {int_tb}: best")
lines.append(f"elif Score >= {int_tg}: good")
lines.append(f"elif Score >= {int_tw}: weak")
lines.append("else: trash")
lines.append("```")
lines.append("")

lines.append("## 全係数")
lines.append("")
lines.append("| 係数 | 連続 | 整数 |")
lines.append("|------|---:|---:|")
for k in sorted(best.keys()):
    if k.startswith("w_") or k == "intercept":
        v = best[k]
        iv = round(v)
        lines.append(f"| {k} | {v:+.3f} | {iv:+d} |")
lines.append("")
lines.append(f"閾値: t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
