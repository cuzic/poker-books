"""eq を 4 要素に分解した公式 + optuna 最適化。

【分解】
equity = MV (made value) + DV (draw value) + BoardAdj (board × hero range の相性)
       - OppRangeStr (相手 range の強さ)

各要素は人間が暗算できる単純な lookup:
- MV: mv_cat → 0-10
- DV: dv_cat → 0-4
- OppRangeStr: pot_type → 0-3
- BoardAdj: board feat (paired/mono/connected/broadway) で +/-

【数式】
EqScore = MV + DV - OppRangeStr + BoardAdj_for_hero
EqScore >= T_best  → best_hands
       >= T_good  → good_hands
       >= T_weak  → weak_hands
       else       → trash_hands
"""
from __future__ import annotations
import csv, re
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_DECOMPOSE_FORMULA.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}

# MV — made hand 強さ
MV_BASE = {
    "straight_flush":10, "quads":10, "fullhouse":9,
    "flush":7, "straight":7, "set":7, "trips":6,
    "two_pair":5,
    "overpair":4, "top_pair":3,
    "second_pair":2, "third_pair":1, "underpair":1, "low_pair":1,
    "king_high":0, "ace_high":0, "no_made_hand":0,
}

# DV — draw 強さ (probabilistic outs)
DV_BASE = {
    "combo_draw":4, "nut_flush_draw":3, "flush_draw":3,
    "oesd":3, "gutshot":1,
    "twocards_bdfd":1, "onecard_bdfd":0,
    "no_draw":0,
}

# OppRange — 相手 range の強さ (= pot_type で proxy)
OPP_R = {"SRP":0, "DEF":1, "3BP":2, "4BP":3}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_features(board: str) -> tuple:
    """(b_high, paired, monotone, twotone, connected, broadway_count, ace, low_only)"""
    if len(board) < 6: return (6, 0, 0, 0, 0, 0, 0, 0)
    cards = [board[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return (6, 0, 0, 0, 0, 0, 0, 0)
    suits = [c[1].lower() for c in cards]
    paired = 1 if rvals[0] == rvals[1] or rvals[1] == rvals[2] else 0
    monotone = 1 if len(set(suits)) == 1 else 0
    twotone = 1 if len(set(suits)) == 2 else 0
    gap_top = rvals[0] - rvals[1]; gap_bot = rvals[1] - rvals[2]
    connected = 1 if (gap_top <= 2 and gap_bot <= 2 and not paired) else 0
    broadway_count = sum(1 for r in rvals if r >= 8)
    ace = 1 if rvals[0] == 12 else 0
    low_only = 1 if rvals[0] <= 5 else 0
    return (rvals[0], paired, monotone, twotone, connected, broadway_count, ace, low_only)


print("Loading rows...")
X_list = []; y_list = []
n_read = 0; n_skipped = 0
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        n_read += 1
        mv = r.get("mv_cat", "")
        dv = r.get("dv_cat", "no_draw")
        eq_b = r.get("equity_bucket", "")
        if eq_b not in EQ_LABEL_TO_IDX or mv not in MV_BASE:
            n_skipped += 1; continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6:
            n_skipped += 1; continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb:
            n_skipped += 1; continue
        try:
            a_r = RANKS.index(ca[0].upper())
            b_r = RANKS.index(cb[0].upper())
            if a_r < b_r: a_r, b_r = b_r, a_r
        except ValueError:
            n_skipped += 1; continue
        pot = parse_pot(r["scenario_id"])
        b_high, paired, mono, twotone, connected, broadway, ace, low_only = board_features(board)

        # MV base
        mv_v = MV_BASE[mv]
        # MV adjustment for kicker / overpair etc
        # TP kicker bonus (a_r is hero's higher rank, if hero has TP with high kicker)
        tp_kicker = b_r if (mv == "top_pair" and a_r == b_high) else 0
        # Overpair adjustment (overpair value depends on board high)
        op_margin = (a_r - b_high) if mv == "overpair" else 0

        # DV
        dv_v = DV_BASE.get(dv, 0)

        # Opp range
        opp_r = OPP_R[pot]

        # Board adj
        # Board が hero に有利か (heuristic): paired board → check 多, monotone → polar
        # 各 board feat を 1 ずつ feature にして optuna に任せる

        # final X row
        X_list.append([
            mv_v, dv_v, opp_r, tp_kicker, op_margin,
            b_high, paired, mono, twotone, connected, broadway, ace, low_only,
            a_r, b_r,  # 自分のカード rank (raw)
        ])
        y_list.append(EQ_LABEL_TO_IDX[eq_b])

X = np.array(X_list, dtype=np.float32)
y = np.array(y_list, dtype=np.int8)
print(f"Loaded {len(X):,} rows ({n_skipped} skipped of {n_read})")
print(f"Feature dim: {X.shape[1]}")

FEATURE_NAMES = [
    "MV","DV","OppRange","tp_kicker","op_margin",
    "b_high","paired","monotone","twotone","connected","broadway","ace","low_only",
    "a_r","b_r",
]


def predict_eq(coeffs, intercept, X, t_weak, t_good, t_best):
    scores = X @ coeffs + intercept
    preds = np.zeros(len(scores), dtype=np.int8)
    preds = np.where(scores >= t_weak, 1, preds)
    preds = np.where(scores >= t_good, 2, preds)
    preds = np.where(scores >= t_best, 3, preds)
    return preds


def objective(trial):
    coeffs = np.array([trial.suggest_float(f"w_{name}", -3.0, 3.0) for name in FEATURE_NAMES], dtype=np.float32)
    intercept = trial.suggest_float("intercept", -10.0, 10.0)
    t_weak = trial.suggest_float("t_weak", -20.0, 10.0)
    t_good = trial.suggest_float("t_good", t_weak + 0.1, 15.0)
    t_best = trial.suggest_float("t_best", t_good + 0.1, 25.0)
    preds = predict_eq(coeffs, intercept, X, t_weak, t_good, t_best)
    return float((preds == y).mean() * 100)


# Constrained version: MV, DV positive; OppRange negative
def objective_constrained(trial):
    # Force MV, DV positive (>=0) and OppRange negative (<=0) for interpretability
    w_mv = trial.suggest_float("w_MV", 0.5, 3.0)
    w_dv = trial.suggest_float("w_DV", 0.0, 2.0)
    w_or = trial.suggest_float("w_OppRange", -3.0, 0.0)
    others = [trial.suggest_float(f"w_{name}", -3.0, 3.0) for name in FEATURE_NAMES[3:]]
    coeffs = np.array([w_mv, w_dv, w_or] + others, dtype=np.float32)
    intercept = trial.suggest_float("intercept", -10.0, 10.0)
    t_weak = trial.suggest_float("t_weak", -20.0, 10.0)
    t_good = trial.suggest_float("t_good", t_weak + 0.1, 15.0)
    t_best = trial.suggest_float("t_best", t_good + 0.1, 25.0)
    preds = predict_eq(coeffs, intercept, X, t_weak, t_good, t_best)
    return float((preds == y).mean() * 100)


print("\n=== Optuna unconstrained (500 trials) ===")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study1 = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study1.optimize(objective, n_trials=500, show_progress_bar=True)
print(f"Best accuracy: {study1.best_value:.2f}%")

print("\n=== Optuna constrained (MV+, DV+, OR-) (500 trials) ===")
study2 = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=43))
study2.optimize(objective_constrained, n_trials=500, show_progress_bar=True)
print(f"Best (constrained) accuracy: {study2.best_value:.2f}%")

best = study1.best_params
weighted = [(name, best[f"w_{name}"]) for name in FEATURE_NAMES]
weighted.sort(key=lambda x: -abs(x[1]))
print("\nTop features (unconstrained):")
for name, w in weighted:
    print(f"  {name:18} = {w:+.3f}")
print(f"intercept = {best['intercept']:+.3f}")
print(f"t_weak={best['t_weak']:.2f}, t_good={best['t_good']:.2f}, t_best={best['t_best']:.2f}")


# Integer version
int_coeffs = np.array([round(best[f"w_{name}"]) for name in FEATURE_NAMES], dtype=np.float32)
int_intercept = round(best["intercept"])
int_tw = round(best["t_weak"]); int_tg = max(int_tw+1, round(best["t_good"]))
int_tb = max(int_tg+1, round(best["t_best"]))
preds_int = predict_eq(int_coeffs, int_intercept, X, int_tw, int_tg, int_tb)
acc_int = float((preds_int == y).mean() * 100)
print(f"\nInteger version: acc={acc_int:.2f}%")
print(f"  Coefficients (|w|>=1):")
for name, w in zip(FEATURE_NAMES, int_coeffs):
    if abs(w) >= 1:
        print(f"    {name:18} = {int(w):+d}")
print(f"  intercept={int_intercept}, t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")


# Report
lines = []
lines.append("# eq 分解公式 — MV + DV + Board − OppRange")
lines.append("")
lines.append("equity を 4 要素に分解。各要素は人間が暗算できる単純な lookup。")
lines.append("")
lines.append("## 概念")
lines.append("")
lines.append("```")
lines.append("EqScore = MV (made value) + DV (draw value) + BoardAdj − OppRangeStr")
lines.append("```")
lines.append("")
lines.append("## 性能")
lines.append("")
lines.append("| variant | accuracy |")
lines.append("|---|---:|")
lines.append(f"| 連続係数 (unconstrained) | **{study1.best_value:.2f}%** |")
lines.append(f"| 連続係数 (constrained: MV+, DV+, OR-) | {study2.best_value:.2f}% |")
lines.append(f"| 整数係数 | {acc_int:.2f}% |")
lines.append("| (参考) 45-feature 線形 | 確認待ち |")
lines.append("| (参考) 30-feature 線形 | 52.2% |")
lines.append("| (参考) 24-cell grid | 58.0% |")
lines.append("")

lines.append("## 入力値テーブル (素人用 lookup)")
lines.append("")
lines.append("### MV — made hand 強さ (mv_cat 別)")
lines.append("")
for cat in ["straight_flush","quads","fullhouse","flush","straight","set","trips","two_pair",
            "overpair","top_pair","second_pair","third_pair","underpair","low_pair",
            "no_made_hand","ace_high","king_high"]:
    lines.append(f"- {cat}: {MV_BASE.get(cat, 0)}")
lines.append("")
lines.append("### DV — draw 強さ (dv_cat 別)")
lines.append("")
for cat in ["combo_draw","nut_flush_draw","flush_draw","oesd","gutshot","twocards_bdfd","onecard_bdfd","no_draw"]:
    lines.append(f"- {cat}: {DV_BASE.get(cat, 0)}")
lines.append("")
lines.append("### OppRange — 相手 range の強さ (pot_type 別)")
lines.append("")
for k, v in OPP_R.items():
    lines.append(f"- {k}: {v}")
lines.append("")

lines.append("## 最適パラメータ (連続)")
lines.append("")
lines.append("| 特徴量 | 連続係数 | 整数 |")
lines.append("|---|---:|---:|")
for name, w in weighted:
    lines.append(f"| {name} | {w:+.3f} | {round(w):+d} |")
lines.append(f"| **intercept** | {best['intercept']:+.3f} | {int_intercept:+d} |")
lines.append("")
lines.append(f"閾値: t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
