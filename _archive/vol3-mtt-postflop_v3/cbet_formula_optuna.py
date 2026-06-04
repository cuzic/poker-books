"""
CBet Formula Optimization via Optuna
=====================================
Target: predict hand-level CBet% from board/hand/scenario features.
Each data point = (board, scenario, hand_type, draw_type) → bet_pct.
Weighted MSE loss (weight = n_combos for that cell).

Usage:
  uv run mtt-postflop/cbet_formula_optuna.py
"""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# 1. Constants / Mappings
# ---------------------------------------------------------------------------

FINDINGS_DIR = Path(__file__).parent / "findings"

# Scenarios to load (skip old SBR25.jsonl — different field format)
SCENARIO_FILES = [
    "draw_study_SRP25.jsonl",
    "draw_study_SRP20.jsonl",
    "draw_study_3BP20.jsonl",
    "draw_study_SRP25_SB.jsonl",
    "draw_study_SRP20_SB.jsonl",
    "draw_study_3BP25_SB.jsonl",
    "draw_study_SRP20_CO.jsonl",
    "draw_study_SRP25_SB_cc.jsonl",
    "draw_study_SRP20_SB_cc.jsonl",
    "draw_study_LIMP25_SB.jsonl",
    "draw_study_LIMP20_SB.jsonl",
]

# Scenario → (SBR, pf_3bp, pf_limp)
SCENARIO_META: dict[str, tuple[float, int, int]] = {
    "SRP25":       (25.0, 0, 0),
    "SRP20":       (20.0, 0, 0),
    "3BP20":       (20.0, 1, 0),
    "SRP25_SB":    (25.0, 0, 0),
    "SRP20_SB":    (20.0, 0, 0),
    "3BP25_SB":    (25.0, 1, 0),
    "SRP20_CO":    (20.0, 0, 0),
    "SRP25_SB_cc": (25.0, 0, 0),
    "SRP20_SB_cc": (20.0, 0, 0),
    "LIMP25_SB":   (25.0, 0, 1),
    "LIMP20_SB":   (20.0, 0, 1),
}

# Board group → (board_type, top_rank, span, fd_board_prior)
# board_type 1-7; top_rank 2-14 (Ace=14); span = top - bottom; fd=1 if monotone suit possible
# fd_board: 1 if board has 2 same suit (fd possible), derived from board_id suffix (_rain/_fd)
BOARD_META: dict[str, tuple[int, int, int]] = {
    "K98":  (2, 13, 5),   # 型2 high-connected
    "T98":  (3, 10, 2),   # 型3 OESD/wet
    "K72":  (5, 13, 11),  # 型5 disconnected
    "Q83":  (2, 12, 5),   # 型2 semi-connected
    "J73":  (5, 11, 8),   # 型5 disconnected
    "A94":  (1, 14, 10),  # 型1 ace-high dry
    "765":  (6, 7, 2),    # 型6 low-wet
    "KJT":  (3, 13, 3),   # 型3 high-OESD
    "T74":  (5, 10, 6),   # 型5 mid-disconnected
    "A72":  (1, 14, 12),  # 型1 ace-high very dry
    "742":  (1, 7, 5),    # 型1 low dry (ace absent → using 型1 low dry)
    "KK8":  (7, 13, 5),   # 型7 paired
    "AA7":  (7, 14, 7),   # 型7 paired ace
}

# Hand type → normalized strength [0,1]
HAND_NORM: dict[str, float] = {
    "no_made_hand": 0.00,
    "ace_high":     0.10,
    "underpair":    0.20,
    "low_pair":     0.25,
    "third_pair":   0.35,
    "second_pair":  0.45,
    "top_pair":     0.60,
    "overpair":     0.72,
    "two_pair":     0.82,
    "set":          0.90,
    "flush":        0.88,
    "straight":     0.87,
}

# Draw type → draw equity bonus [0,1]
DRAW_EQUITY: dict[str, float] = {
    "no_draw":       0.00,
    "twocards_bdfd": 0.10,
    "gutshot":       0.20,
    "oesd":          0.35,
    "fd":            0.30,
    "fd_gutshot":    0.45,
    "fd_oesd":       0.55,
}


# ---------------------------------------------------------------------------
# 2. Data Loading
# ---------------------------------------------------------------------------

@dataclass
class DataPoint:
    y: float          # bet_pct / 100  (target, in [0,1])
    w: float          # weight = n_combos
    ras: float        # no_draw bet_pct / 100
    de: float         # draw equity proxy
    hand_norm: float  # hand strength [0,1]
    sbr_n: float      # (SBR - 20) / 10
    pf_3bp: float     # 0 or 1
    pf_limp: float    # 0 or 1
    board_type: int   # 1-7
    top_rank_n: float # (rank - 2) / 12  → [0,1]
    span_n: float     # span / 12        → [0,1]
    fd_board: float   # 1 if board has fd potential (from _fd suffix)


def load_data() -> list[DataPoint]:
    data: list[DataPoint] = []

    for fname in SCENARIO_FILES:
        fpath = FINDINGS_DIR / fname
        if not fpath.exists():
            print(f"  [WARN] missing: {fname}")
            continue

        with open(fpath) as f:
            for line in f:
                rec = json.loads(line.strip())
                if not rec:
                    continue

                scenario = rec["scenario"]
                if scenario not in SCENARIO_META:
                    continue

                sbr, pf_3bp, pf_limp = SCENARIO_META[scenario]
                sbr_n = (sbr - 20.0) / 10.0   # SRP20→0, SRP25→0.5

                # Board group and fd flag
                board_id = rec["board_id"]
                group = rec["group"]
                fd_board = 1.0 if board_id.endswith("_fd") else 0.0

                if group not in BOARD_META:
                    continue
                btype, top_rank, span = BOARD_META[group]
                top_rank_n = (top_rank - 2) / 12.0
                span_n = span / 12.0

                # RAS proxy: no_draw aggregate bet%
                draw_agg = rec.get("draw_agg", {})
                nd = draw_agg.get("no_draw", {})
                ras = nd.get("bet_pct", 50.0) / 100.0

                # Expand cross-table
                cross = rec.get("cross", {})
                for key, cell in cross.items():
                    avg = cell.get("avg", 0.0)
                    n = cell.get("n", 0)
                    if n == 0:
                        continue

                    # Parse "hand_type|draw_type"
                    parts = key.split("|")
                    if len(parts) != 2:
                        continue
                    hand_str, draw_str = parts

                    hand_n = HAND_NORM.get(hand_str)
                    de = DRAW_EQUITY.get(draw_str)
                    if hand_n is None or de is None:
                        continue

                    y = avg / 100.0
                    y = max(0.0, min(1.0, y))

                    data.append(DataPoint(
                        y=y,
                        w=float(n),
                        ras=ras,
                        de=de,
                        hand_norm=hand_n,
                        sbr_n=sbr_n,
                        pf_3bp=float(pf_3bp),
                        pf_limp=float(pf_limp),
                        board_type=btype,
                        top_rank_n=top_rank_n,
                        span_n=span_n,
                        fd_board=fd_board,
                    ))

    print(f"Loaded {len(data)} data points from {len(SCENARIO_FILES)} files")
    return data


def to_arrays(data: list[DataPoint]):
    """Convert data points to numpy arrays."""
    n = len(data)
    ras    = np.array([d.ras       for d in data])
    de     = np.array([d.de        for d in data])
    hand   = np.array([d.hand_norm for d in data])
    sbr_n  = np.array([d.sbr_n    for d in data])
    p3bp   = np.array([d.pf_3bp   for d in data])
    plimp  = np.array([d.pf_limp  for d in data])
    btype  = np.array([d.board_type for d in data])
    topR   = np.array([d.top_rank_n for d in data])
    span   = np.array([d.span_n   for d in data])
    fd     = np.array([d.fd_board  for d in data])
    y      = np.array([d.y        for d in data])
    w      = np.array([d.w        for d in data])
    w = w / w.sum()   # normalize weights
    return ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd, y, w


# ---------------------------------------------------------------------------
# 3. Helper: sigmoid / logit / clamp
# ---------------------------------------------------------------------------

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -15, 15)))

def clamp01(x: np.ndarray) -> np.ndarray:
    return np.clip(x, 1e-6, 1 - 1e-6)

def wmse(pred: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    return float(np.sum(w * (pred - y) ** 2))

def wrmse(pred: np.ndarray, y: np.ndarray, w: np.ndarray) -> float:
    return math.sqrt(wmse(pred, y, w))


# ---------------------------------------------------------------------------
# 4. Formula Implementations (F1–F8)
# ---------------------------------------------------------------------------

def f1_linear_logistic(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F1: Linear logistic (5 param)."""
    a = trial.suggest_float("a", -5, 5)
    b = trial.suggest_float("b", -5, 5)
    c = trial.suggest_float("c", -5, 5)
    d = trial.suggest_float("d", -3, 3)
    e = trial.suggest_float("e", -5, 5)
    logit_p = a * ras + b * de + c * hand + d * sbr_n + e
    return sigmoid(logit_p)


def f2_ras_gate(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F2: RAS-gate — high-ras → bluff-heavy, low-ras → value-only."""
    k = trial.suggest_float("k", 1, 20)
    t = trial.suggest_float("t", 0.3, 0.8)
    a = trial.suggest_float("a", -5, 5)
    b = trial.suggest_float("b", -5, 5)
    c = trial.suggest_float("c", -3, 3)
    d = trial.suggest_float("d", -5, 5)
    gate = sigmoid(k * (ras - t))
    bluff_comp = sigmoid(a * de + b * hand + c * sbr_n + d)
    return gate * 0.9 + (1 - gate) * bluff_comp


def f3_ras_de_interact(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F3: RAS×DE interaction (7 param)."""
    a = trial.suggest_float("a", -5, 5)
    b = trial.suggest_float("b", -5, 5)
    c = trial.suggest_float("c", -5, 5)
    d = trial.suggest_float("d", -10, 10)
    e = trial.suggest_float("e", -10, 10)
    f = trial.suggest_float("f", -3, 3)
    g = trial.suggest_float("g", -5, 5)
    logit_p = (a * ras + b * de + c * hand
               + d * ras * de + e * (1 - ras) * de
               + f * sbr_n + g)
    return sigmoid(logit_p)


def f4_three_zone(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F4: Three-zone piecewise linear on composite score."""
    a = trial.suggest_float("a", 0, 3)
    b = trial.suggest_float("b", 0, 3)
    c = trial.suggest_float("c", 0, 3)
    t1 = trial.suggest_float("t1", 0.2, 0.5)
    t2 = trial.suggest_float("t2", 0.5, 0.9)
    p_low  = trial.suggest_float("p_low",  0.0, 0.3)
    p_high = trial.suggest_float("p_high", 0.7, 1.0)
    p_mid  = trial.suggest_float("p_mid",  0.3, 0.7)
    score = np.clip(a * ras + b * de + c * hand, 0, a + b + c + 1e-8)
    score = score / (a + b + c + 1e-8)   # normalize to [0,1]
    result = np.where(score < t1, p_low,
             np.where(score > t2, p_high,
             p_mid + (p_high - p_mid) * (score - t1) / (t2 - t1 + 1e-8)))
    return result


def f5_board_categorical(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F5: Board-type categorical intercepts (11 param)."""
    beta = [trial.suggest_float(f"b{i}", -4, 4) for i in range(1, 8)]
    a = trial.suggest_float("a", -5, 5)
    b = trial.suggest_float("b", -5, 5)
    c = trial.suggest_float("c", -3, 3)
    d = trial.suggest_float("d", -3, 3)
    intercept = np.array([beta[bt - 1] for bt in btype])
    logit_p = intercept + a * de + b * hand + c * sbr_n + d * p3bp
    return sigmoid(logit_p)


def f6_multiplicative(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F6: Multiplicative (5 param)."""
    a   = trial.suggest_float("a",   0.1, 3.0)
    b   = trial.suggest_float("b",   0.0, 5.0)
    c   = trial.suggest_float("c",  -2.0, 2.0)
    k3b = trial.suggest_float("k3b", 0.5, 1.5)
    klm = trial.suggest_float("klm", 0.5, 1.5)
    p = (ras ** a) * (1 + de * b) * (1 + (hand - 0.5) * c) * (k3b ** p3bp) * (klm ** plimp)
    return np.clip(p, 0.0, 1.0)


def f7_full_poly(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F7: Full polynomial with cross terms (10 param)."""
    a  = trial.suggest_float("a",  -5, 5)
    b  = trial.suggest_float("b",  -5, 5)
    c  = trial.suggest_float("c",  -5, 5)
    d  = trial.suggest_float("d",  -3, 3)
    e  = trial.suggest_float("e",  -3, 3)
    f  = trial.suggest_float("f",  -5, 5)
    g  = trial.suggest_float("g",  -5, 5)
    h  = trial.suggest_float("h",  -5, 5)
    i_ = trial.suggest_float("i",  -5, 5)
    j  = trial.suggest_float("j",  -5, 5)
    logit_p = (a * ras + b * de + c * hand + d * sbr_n + e * p3bp
               + f * ras * de + g * ras * hand + h * de * hand
               + i_ * ras * sbr_n + j)
    return sigmoid(logit_p)


def f8_board_practical(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd):
    """F8: Player-practical (no ras proxy) — uses board features directly."""
    w1 = trial.suggest_float("w1", 0.0, 2.0)   # top_rank weight
    w2 = trial.suggest_float("w2", 0.0, 2.0)   # compactness weight
    w3 = trial.suggest_float("w3", 0.0, 2.0)   # fd_board weight
    a  = trial.suggest_float("a",  -5, 5)
    b  = trial.suggest_float("b",  -5, 5)
    c  = trial.suggest_float("c",  -5, 5)
    d  = trial.suggest_float("d",  -5, 5)
    e  = trial.suggest_float("e",  -3, 3)
    f  = trial.suggest_float("f",  -3, 3)
    g  = trial.suggest_float("g",  -5, 5)
    board_score = w1 * topR + w2 * (1 - span) + w3 * fd
    logit_p = (a * board_score + b * de + c * hand
               + d * board_score * de + e * sbr_n + f * p3bp + g)
    return sigmoid(logit_p)


FORMULAS = {
    "F1_Linear":       f1_linear_logistic,
    "F2_RAS_Gate":     f2_ras_gate,
    "F3_RAS_DE_Int":   f3_ras_de_interact,
    "F4_ThreeZone":    f4_three_zone,
    "F5_BoardCat":     f5_board_categorical,
    "F6_Multiplicat":  f6_multiplicative,
    "F7_FullPoly":     f7_full_poly,
    "F8_Practical":    f8_board_practical,
}


# ---------------------------------------------------------------------------
# 5. Optuna Objective Factory
# ---------------------------------------------------------------------------

def make_objective(fn, arrays):
    ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd, y, w = arrays

    def objective(trial):
        try:
            pred = fn(trial, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd)
            pred = np.clip(pred, 0.0, 1.0)
            return wmse(pred, y, w)
        except Exception:
            return 1.0

    return objective


# ---------------------------------------------------------------------------
# 6. Baseline Models
# ---------------------------------------------------------------------------

def baseline_mean(arrays):
    ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd, y, w = arrays
    pred = np.full_like(y, np.average(y, weights=w))
    return wmse(pred, y, w)


def baseline_ras_only(arrays):
    """Simple linear regression on RAS only."""
    ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd, y, w = arrays
    # Weighted linear regression: y ~ a*ras + b
    A = np.column_stack([ras, np.ones_like(ras)])
    Aw = A * w[:, None]
    coeffs, _, _, _ = np.linalg.lstsq(Aw, y * w, rcond=None)
    pred = A @ coeffs
    pred = np.clip(pred, 0, 1)
    return wmse(pred, y, w)


# ---------------------------------------------------------------------------
# 7. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("CBet Formula Optimization (Optuna)")
    print("=" * 60)

    data = load_data()
    if not data:
        print("No data loaded. Exiting.")
        return

    arrays = to_arrays(data)
    ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd, y, w = arrays

    # Quick stats
    print(f"\nData stats:")
    print(f"  n_points  = {len(data)}")
    print(f"  y range   = [{y.min():.3f}, {y.max():.3f}]  mean={np.average(y, weights=w):.3f}")
    print(f"  ras range = [{ras.min():.3f}, {ras.max():.3f}]")

    bm = baseline_mean(arrays)
    br = baseline_ras_only(arrays)
    print(f"\nBaseline WMSE:")
    print(f"  Mean-only : {bm:.5f}  (WRMSE={math.sqrt(bm)*100:.1f}%)")
    print(f"  RAS-only  : {br:.5f}  (WRMSE={math.sqrt(br)*100:.1f}%)")

    N_TRIALS = 500
    results = {}

    print(f"\nRunning Optuna ({N_TRIALS} trials each)…")
    print("-" * 60)

    for name, fn in FORMULAS.items():
        study = optuna.create_study(direction="minimize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        objective = make_objective(fn, arrays)
        study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=False)

        best = study.best_value
        rmse_pct = math.sqrt(best) * 100
        results[name] = {
            "wmse": best,
            "wrmse_pct": rmse_pct,
            "params": study.best_params,
        }
        print(f"  {name:<16} WMSE={best:.5f}  WRMSE={rmse_pct:.1f}%")

    # ---------------------------------------------------------------------------
    # 8. Results Summary
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY (sorted by WRMSE)")
    print("=" * 60)
    print(f"{'Formula':<16}  {'WMSE':>8}  {'WRMSE%':>8}  {'R²':>6}")
    print("-" * 50)

    sorted_res = sorted(results.items(), key=lambda x: x[1]["wmse"])
    for name, r in sorted_res:
        r2 = 1 - r["wmse"] / bm
        print(f"{name:<16}  {r['wmse']:>8.5f}  {r['wrmse_pct']:>7.1f}%  {r2:>6.3f}")

    print(f"\n{'Baseline mean':<16}  {bm:>8.5f}  {math.sqrt(bm)*100:>7.1f}%  {'0.000':>6}")
    print(f"{'Baseline RAS':<16}  {br:>8.5f}  {math.sqrt(br)*100:>7.1f}%  {1-br/bm:>6.3f}")

    # Best formula details
    best_name, best_r = sorted_res[0]
    print(f"\nBest formula: {best_name}")
    print("Best parameters:")
    for k, v in sorted(best_r["params"].items()):
        print(f"  {k:6s} = {v:+.4f}")

    # ---------------------------------------------------------------------------
    # 9. Prediction samples for best formula
    # ---------------------------------------------------------------------------
    print(f"\nSample predictions ({best_name}) vs actual:")
    print(f"{'hand|draw':<30} {'ras':>5} {'y_true':>7} {'y_pred':>7} {'diff':>7}")
    print("-" * 60)

    fn_best = FORMULAS[best_name]

    class _MockTrial:
        """Replay best params."""
        def __init__(self, params):
            self._p = params
        def suggest_float(self, name, lo, hi):
            return self._p[name]
        def suggest_int(self, name, lo, hi):
            return int(self._p[name])

    mock = _MockTrial(best_r["params"])
    pred_all = fn_best(mock, ras, de, hand, sbr_n, p3bp, plimp, btype, topR, span, fd)
    pred_all = np.clip(pred_all, 0.0, 1.0)

    for d_pt, y_t, y_p, r_as in sorted(
        zip(data, y, pred_all, ras),
        key=lambda x: abs(x[1] - x[2]),
        reverse=True
    )[:20]:
        key = f"{d_pt.hand_norm:.2f}h|{d_pt.de:.2f}d"
        diff = y_t - y_p
        print(f"{key:<30} {r_as:>5.2f} {y_t:>7.1%} {y_p:>7.1%} {diff:>+7.1%}")

    # ---------------------------------------------------------------------------
    # 10. Per-board-type breakdown for best formula
    # ---------------------------------------------------------------------------
    print(f"\nPer-board-type WRMSE ({best_name}):")
    for bt in range(1, 8):
        mask = btype == bt
        if mask.sum() == 0:
            continue
        ys = y[mask]; ps = pred_all[mask]; ws = w[mask]
        ws = ws / ws.sum()
        bt_rmse = math.sqrt(wmse(ps, ys, ws)) * 100
        print(f"  型{bt}: n={mask.sum():3d}  WRMSE={bt_rmse:.1f}%")

    print("\nDone.")


if __name__ == "__main__":
    main()
