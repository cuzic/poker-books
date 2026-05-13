#!/usr/bin/env python3
"""OLS regression + correlation analysis on 168-board GTO dataset.

Usage:
  python3 regression.py --results /path/to/results_dir [--target btn_cbet_pct]

Output:
  - Pearson correlation table
  - OLS coefficients (per feature)
  - R² and RMSE
  - Suggested formula
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:
    print("numpy required: pip install numpy", file=sys.stderr)
    sys.exit(1)


# ── Feature engineering ───────────────────────────────────────────────────────

def build_features(board: dict) -> dict[str, float]:
    r_hi  = board.get("r_hi",  board.get("r1", 0))
    r_mid = board.get("r_mid", board.get("r2", 0))
    r_lo  = board.get("r_lo",  board.get("r3", 0))
    spread   = board.get("spread",   r_hi - r_lo)
    top_diff = board.get("top_diff", r_hi - r_mid)
    mid_diff = board.get("mid_diff", r_mid - r_lo)

    return {
        "top_rank":       float(r_hi),
        "spread":         float(spread),
        "top_diff":       float(top_diff),
        "mid_diff":       float(mid_diff),
        "is_2tone":       float(board.get("is_2tone", False)),
        "is_monotone":    float(board.get("is_monotone", False)),
        "is_paired":      float(board.get("is_paired", False)),
        # Derived
        "density_wet":    float(spread <= 2),           # OESD-dense
        "high_connected": float(r_hi >= 10 and top_diff <= 4),
        "kicker_rank":    float(r_mid),
        # Interactions
        "top_x_2tone":    float(r_hi) * float(board.get("is_2tone", False)),
        "top_x_mono":     float(r_hi) * float(board.get("is_monotone", False)),
    }


FEATURE_NAMES = [
    "top_rank", "spread", "top_diff", "mid_diff",
    "is_2tone", "is_monotone", "is_paired",
    "density_wet", "high_connected", "kicker_rank",
    "top_x_2tone", "top_x_mono",
]

TARGETS = [
    "btn_cbet_pct",
    "bb_fold_vs33", "bb_fold_vs50", "bb_fold_vs75",
    "cbet_overpair", "cbet_underpair", "cbet_two_overcards", "cbet_air",
]


# ── Statistics helpers ────────────────────────────────────────────────────────

def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 2:
        return float("nan")
    xm, ym = x - x.mean(), y - y.mean()
    denom = math.sqrt((xm**2).sum() * (ym**2).sum())
    return float((xm * ym).sum() / denom) if denom > 0 else float("nan")


def ols(X: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, float, float]:
    """Return (coeffs, R², RMSE). X should include a bias column."""
    coeffs, *_ = np.linalg.lstsq(X, y, rcond=None)
    y_hat = X @ coeffs
    ss_res = ((y - y_hat)**2).sum()
    ss_tot = ((y - y.mean())**2).sum()
    r2   = float(1 - ss_res / ss_tot) if ss_tot > 0 else float("nan")
    rmse = float(math.sqrt(ss_res / len(y)))
    return coeffs, r2, rmse


# ── Main ──────────────────────────────────────────────────────────────────────

def load_data(results_dir: Path) -> list[dict]:
    rows = []
    for f in sorted(results_dir.glob("*.json")):
        if f.name.startswith("regression"):
            continue
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if "error" in d or "btn_cbet_pct" not in d:
            continue
        rows.append(d)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="../../knowledges/flop/results/168board_study",
                    help="Directory containing board result JSON files")
    ap.add_argument("--target", default="btn_cbet_pct",
                    help="Primary regression target")
    args = ap.parse_args()

    results_dir = Path(args.results)
    if not results_dir.exists():
        print(f"ERROR: {results_dir} not found", file=sys.stderr)
        sys.exit(1)

    rows = load_data(results_dir)
    if not rows:
        print("No valid results found.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(rows)} boards")
    print()

    # ── Build arrays ──────────────────────────────────────────────────────────
    feats = [build_features(r) for r in rows]
    F_mat = np.array([[f[k] for k in FEATURE_NAMES] for f in feats])
    # Add bias column
    X = np.hstack([F_mat, np.ones((len(rows), 1))])
    feat_labels = FEATURE_NAMES + ["bias"]

    # ── Pearson correlations with primary target ──────────────────────────────
    target_vals = np.array([r[args.target] for r in rows], dtype=float)

    print(f"=== Pearson correlations → {args.target} ===")
    print(f"  {'feature':<18}  r")
    print("  " + "-" * 30)
    cors = {k: pearson(F_mat[:, i], target_vals)
            for i, k in enumerate(FEATURE_NAMES)}
    for k, r in sorted(cors.items(), key=lambda x: -abs(x[1]) if not math.isnan(x[1]) else 0):
        if math.isnan(r):
            print(f"  {k:<18}  NaN (zero variance)")
            continue
        bar = "█" * int(abs(r) * 20)
        sign = "+" if r >= 0 else "-"
        print(f"  {k:<18}  {sign}{abs(r):.3f}  {bar}")
    print()

    # ── Per-category breakdown ────────────────────────────────────────────────
    cats = {}
    for r in rows:
        c = r.get("category", "unknown")
        cats.setdefault(c, []).append(r[args.target])
    print(f"=== {args.target} by board category ===")
    for c, vals in sorted(cats.items()):
        arr = np.array(vals)
        print(f"  {c:<12}  n={len(vals):3d}  "
              f"mean={arr.mean():.1f}%  "
              f"sd={arr.std():.1f}  "
              f"min={arr.min():.1f}  "
              f"max={arr.max():.1f}")
    print()

    # ── OLS regression ────────────────────────────────────────────────────────
    print(f"=== OLS regression → {args.target} ===")
    coeffs, r2, rmse = ols(X, target_vals)
    print(f"  R² = {r2:.4f}   RMSE = {rmse:.2f}%")
    print()
    print(f"  {'feature':<18}  coeff")
    print("  " + "-" * 32)
    for label, c in sorted(zip(feat_labels, coeffs),
                            key=lambda x: -abs(x[1])):
        print(f"  {label:<18}  {c:+.3f}")
    print()

    # ── Multi-target summary ──────────────────────────────────────────────────
    print("=== R² for all targets ===")
    for tgt in TARGETS:
        y = np.array([r.get(tgt, float("nan")) for r in rows])
        mask = ~np.isnan(y)
        if mask.sum() < 10:
            print(f"  {tgt:<24}  n={mask.sum():3d}  (too few)")
            continue
        _, r2_t, rmse_t = ols(X[mask], y[mask])
        print(f"  {tgt:<24}  n={mask.sum():3d}  R²={r2_t:.3f}  RMSE={rmse_t:.2f}%")
    print()

    # ── Simple formula suggestion (top-3 features by |coeff| from OLS) ────────
    top3 = sorted(zip(feat_labels[:-1], coeffs[:-1]),
                  key=lambda x: -abs(x[1]))[:3]
    bias = coeffs[-1]
    print("=== Candidate simple formula ===")
    print(f"  {args.target} ≈ {bias:.1f}")
    for fname, c in top3:
        sign = "+" if c >= 0 else ""
        print(f"    {sign}{c:.2f} × {fname}")
    print()

    # ── Save combined dataset JSON ────────────────────────────────────────────
    out_json = results_dir / "combined_dataset.json"
    out_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2))
    print(f"Combined dataset: {out_json}")


if __name__ == "__main__":
    main()
