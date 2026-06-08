"""eq grid (24-cell 非線形) + 線形 adjust のハイブリッド公式。

【設計】
Step 1: grid[tier][board_label] で base score (非線形相互作用を吸収)
Step 2: 線形 adjust を加算

eq_score = GridBase[mv_cat][board_label]
         + w_kicker * tp_kicker
         + w_draw * dv_value
         + w_overcards * overcards
         + w_undercards * undercards
         + w_oppr * opp_range
         + w_op_margin * op_margin  (overpair 用)
         + w_fd * fd_potential

【期待】
- Grid 単独: 58%
- + 線形 adjust: 65%+ 期待
- 中級者には「step 1 grid + step 2 adjust」で運用可能
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_GRID_LINEAR_HYBRID.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}

MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_ORDER = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]
BOARD_TYPES = ["dry","paired","connected","monotone"]
OPP_R = {"SRP":0, "DEF":1, "3BP":2, "4BP":3}
DV_BASE = {"combo_draw":4, "nut_flush_draw":3, "flush_draw":3, "oesd":3, "gutshot":1,
           "twocards_bdfd":1, "onecard_bdfd":0, "no_draw":0}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_label(flop: str) -> str:
    if len(flop) < 6: return "dry"
    cards = [flop[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return "dry"
    suits = [c[1].lower() for c in cards]
    paired = (rvals[0] == rvals[1] or rvals[1] == rvals[2])
    monotone = len(set(suits)) == 1
    gap_top = rvals[0] - rvals[1]; gap_bot = rvals[1] - rvals[2]
    connected = (gap_top <= 2 and gap_bot <= 2 and not paired)
    if paired: return "paired"
    if monotone: return "monotone"
    if connected: return "connected"
    return "dry"


def board_high_rank(flop: str) -> int:
    if len(flop) < 6: return 6
    cards = [flop[i*2:i*2+2] for i in range(3)]
    try:
        rvals = [RANKS.index(c[0].upper()) for c in cards]
    except ValueError:
        return 6
    return max(rvals)


print("Loading rows + computing grid lookup + features...")
grid_dist: dict[tuple[str, str], dict[str, int]] = defaultdict(lambda: defaultdict(int))
rows_data = []

with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", "")
        dv = r.get("dv_cat", "no_draw")
        eq_b = r.get("equity_bucket", "")
        if eq_b not in EQ_LABEL_TO_IDX or mv not in MV_TIER_MAP: continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb: continue
        try:
            a_r = RANKS.index(ca[0].upper())
            b_r = RANKS.index(cb[0].upper())
            if a_r < b_r: a_r, b_r = b_r, a_r
        except ValueError:
            continue

        tier = MV_TIER_MAP[mv]
        bl = board_label(board)
        bh = board_high_rank(board)
        pot = parse_pot(r["scenario_id"])
        opp_r = OPP_R[pot]
        dv_v = DV_BASE.get(dv, 0)

        # TP kicker rank (only for top_pair)
        tp_kicker = b_r if (mv == "top_pair" and a_r == bh) else 0
        # Overpair margin
        op_margin = (a_r - bh) if mv == "overpair" else 0
        # Overcards (only if not overpair/TP)
        overcards = sum(1 for r2 in (a_r, b_r) if r2 > bh) if mv not in ("overpair","top_pair","set","two_pair","trips","fullhouse","quads") else 0

        grid_dist[(tier, bl)][eq_b] += 1
        rows_data.append({
            "tier": tier, "board_label": bl, "true_eq_idx": EQ_LABEL_TO_IDX[eq_b],
            "tp_kicker": tp_kicker, "op_margin": op_margin, "overcards": overcards,
            "dv": dv_v, "opp_r": opp_r,
        })

# Build grid base score (modal eq → numeric value)
EQ_VALUE = {"best_hands":9, "good_hands":6, "weak_hands":3, "trash_hands":0}
grid_base: dict[tuple[str, str], float] = {}
grid_modal: dict[tuple[str, str], str] = {}
for key, dist in grid_dist.items():
    total = sum(dist.values())
    if total < 50:
        # use mean-weighted eq value
        weighted = sum(dist[b] * EQ_VALUE[b] for b in dist) / total if total > 0 else 3
        grid_base[key] = weighted
        grid_modal[key] = "(low n)"
        continue
    # Use expected value (probabilistic)
    expected = sum(dist[b] * EQ_VALUE[b] for b in dist) / total
    modal = max(dist.items(), key=lambda x: x[1])
    grid_base[key] = expected
    grid_modal[key] = modal[0]

print(f"\n=== Grid base score (expected eq value, 0-9) ===")
print(f"{'tier':18}", end="")
for bl in BOARD_TYPES: print(f"{bl:>10}", end="")
print()
for tier in TIER_ORDER:
    print(f"  {tier:16}", end="")
    for bl in BOARD_TYPES:
        v = grid_base.get((tier, bl), 0)
        print(f"{v:>9.2f}", end=" ")
    print()


print(f"\n=== Modal eq_bucket per cell ===")
print(f"{'tier':18}", end="")
for bl in BOARD_TYPES: print(f"{bl:>14}", end="")
print()
for tier in TIER_ORDER:
    print(f"  {tier:16}", end="")
    for bl in BOARD_TYPES:
        print(f"{grid_modal.get((tier, bl), '?')[:12]:>14}", end="")
    print()

# Convert to arrays
N = len(rows_data)
print(f"\nLoaded {N:,} rows")

grid_vals = np.array([grid_base.get((r["tier"], r["board_label"]), 3) for r in rows_data], dtype=np.float32)
tp_kicker = np.array([r["tp_kicker"] for r in rows_data], dtype=np.float32)
op_margin = np.array([r["op_margin"] for r in rows_data], dtype=np.float32)
overcards = np.array([r["overcards"] for r in rows_data], dtype=np.float32)
dv_vals = np.array([r["dv"] for r in rows_data], dtype=np.float32)
opp_r_vals = np.array([r["opp_r"] for r in rows_data], dtype=np.float32)
y = np.array([r["true_eq_idx"] for r in rows_data], dtype=np.int8)


def predict(coeffs, intercept, t_weak, t_good, t_best):
    # coeffs = (w_grid, w_kicker, w_op, w_oc, w_dv, w_opr)
    score = (coeffs[0] * grid_vals
             + coeffs[1] * tp_kicker
             + coeffs[2] * op_margin
             + coeffs[3] * overcards
             + coeffs[4] * dv_vals
             + coeffs[5] * opp_r_vals
             + intercept)
    preds = np.zeros(N, dtype=np.int8)
    preds = np.where(score >= t_weak, 1, preds)
    preds = np.where(score >= t_good, 2, preds)
    preds = np.where(score >= t_best, 3, preds)
    return preds


def objective(trial):
    w_grid = trial.suggest_float("w_grid", 0.5, 3.0)
    w_kicker = trial.suggest_float("w_kicker", -2.0, 2.0)
    w_op = trial.suggest_float("w_op", -2.0, 2.0)
    w_oc = trial.suggest_float("w_oc", -3.0, 1.0)
    w_dv = trial.suggest_float("w_dv", -1.0, 3.0)
    w_opr = trial.suggest_float("w_opr", -3.0, 3.0)
    intercept = trial.suggest_float("intercept", -5.0, 5.0)
    t_weak = trial.suggest_float("t_weak", -5.0, 8.0)
    t_good = trial.suggest_float("t_good", t_weak + 0.1, 15.0)
    t_best = trial.suggest_float("t_best", t_good + 0.1, 25.0)
    coeffs = (w_grid, w_kicker, w_op, w_oc, w_dv, w_opr)
    preds = predict(coeffs, intercept, t_weak, t_good, t_best)
    return float((preds == y).mean() * 100)


print(f"\n=== Optuna 500 trials ===")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=500, show_progress_bar=True)

best = study.best_params
print(f"\nBest accuracy: {study.best_value:.2f}%")
print(f"Params:")
for k, v in best.items():
    print(f"  {k:12} = {v:+.3f}")


# Grid-only baseline (no linear adj)
def predict_grid_only(t_weak, t_good, t_best):
    score = grid_vals
    preds = np.zeros(N, dtype=np.int8)
    preds = np.where(score >= t_weak, 1, preds)
    preds = np.where(score >= t_good, 2, preds)
    preds = np.where(score >= t_best, 3, preds)
    return preds


def obj_grid(trial):
    t_weak = trial.suggest_float("t_weak", 0, 5)
    t_good = trial.suggest_float("t_good", t_weak + 0.1, 8)
    t_best = trial.suggest_float("t_best", t_good + 0.1, 10)
    preds = predict_grid_only(t_weak, t_good, t_best)
    return float((preds == y).mean() * 100)


print(f"\n=== Grid-only baseline ===")
study_grid = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study_grid.optimize(obj_grid, n_trials=100, show_progress_bar=False)
print(f"Grid-only best: {study_grid.best_value:.2f}%")


# Integer version
print(f"\n=== Integer rounded ===")
int_w = {k: round(v) for k, v in best.items() if k.startswith("w_") or k == "intercept"}
int_w_grid = max(1, int_w["w_grid"])  # must be positive
int_intercept = int_w["intercept"]
int_tw = round(best["t_weak"])
int_tg = max(int_tw+1, round(best["t_good"]))
int_tb = max(int_tg+1, round(best["t_best"]))
preds_int = predict(
    (int_w_grid, int_w["w_kicker"], int_w["w_op"], int_w["w_oc"], int_w["w_dv"], int_w["w_opr"]),
    int_intercept, int_tw, int_tg, int_tb
)
acc_int = float((preds_int == y).mean() * 100)
print(f"Integer accuracy: {acc_int:.2f}%")
print(f"Coefficients: w_grid={int_w_grid}, w_kicker={int_w['w_kicker']}, w_op={int_w['w_op']}, w_oc={int_w['w_oc']}, w_dv={int_w['w_dv']}, w_opr={int_w['w_opr']}, intercept={int_intercept}")
print(f"Thresholds: t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")


# Report
lines = []
lines.append("# eq grid + 線形 adjust ハイブリッド公式")
lines.append("")
lines.append("Grid (tier × board の非線形相互作用) + 線形 adjust の段階式モデル。")
lines.append("")
lines.append("## 概念")
lines.append("")
lines.append("```")
lines.append("Step 1: GridBase[mv_tier][board_label] で base eq score lookup")
lines.append("Step 2: Score = w_grid × GridBase")
lines.append("              + w_kicker × tp_kicker")
lines.append("              + w_op     × op_margin       (overpair only)")
lines.append("              + w_oc     × overcards_count")
lines.append("              + w_dv     × draw_value")
lines.append("              + w_opr    × opp_range")
lines.append("              + intercept")
lines.append("")
lines.append("Step 3: Score >= T_best → best / >= T_good → good / >= T_weak → weak / else trash")
lines.append("```")
lines.append("")

lines.append("## 性能")
lines.append("")
lines.append(f"| variant | accuracy |")
lines.append(f"|---|---:|")
lines.append(f"| **Grid + 線形 (連続)** | **{study.best_value:.2f}%** |")
lines.append(f"| Grid + 線形 (整数) | {acc_int:.2f}% |")
lines.append(f"| Grid 単独 (modal lookup) | 58.0% |")
lines.append(f"| Grid 単独 (expected value optimized) | {study_grid.best_value:.2f}% |")
lines.append(f"| eq 分解 線形 | 59.5% |")
lines.append(f"| 8-feature 線形 | 58.8% |")
lines.append("")

lines.append("## GridBase 表 (tier × board → expected eq score)")
lines.append("")
lines.append("| tier | dry | paired | connected | monotone |")
lines.append("|------|---:|---:|---:|---:|")
for tier in TIER_ORDER:
    row = f"| {tier} |"
    for bl in BOARD_TYPES:
        v = grid_base.get((tier, bl), 0)
        row += f" {v:.2f} |"
    lines.append(row)
lines.append("")

lines.append("## 整数係数 (書籍向け)")
lines.append("")
lines.append("| 係数 | 値 |")
lines.append("|------|---:|")
lines.append(f"| w_grid | +{int_w_grid} |")
lines.append(f"| w_kicker | {int_w['w_kicker']:+d} |")
lines.append(f"| w_op (overpair margin) | {int_w['w_op']:+d} |")
lines.append(f"| w_oc (overcards) | {int_w['w_oc']:+d} |")
lines.append(f"| w_dv (draw value) | {int_w['w_dv']:+d} |")
lines.append(f"| w_opr (opp range) | {int_w['w_opr']:+d} |")
lines.append(f"| intercept | {int_intercept:+d} |")
lines.append("")
lines.append(f"閾値: t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
