#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy", "scikit-learn"]
# ///
"""Two-stage approach: predict eq_percentile first, then action.

Stage 1 analysis:
  - How well can (MV, DV, board, position) predict eq_percentile?
  - Compute correlation, R² of linear/tree regression
  - Visualize eq_percentile distribution per (bucket, mv, board)

Stage 2 analysis:
  - How does eq_percentile relate to bet_freq (attack) or fold_freq (defense)?
  - Is the relationship monotonic / linear?
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.tree import DecisionTreeRegressor

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    # restrict to rows with eq_percentile (Format A only)
    df = df[df["eq_percentile"].notna()].copy()
    print(f"Rows with eq_percentile: {len(df)} / spots: {df['spot_id'].nunique()}")

    # ── Stage 1: Predict eq_percentile from features ──
    cat_cols = ["mv_cat", "dv_cat", "board_family", "street", "hero_rel", "action_context"]
    num_cols = []
    X_cat = pd.get_dummies(df[cat_cols], drop_first=False)
    X = X_cat
    y = df["eq_percentile"].values
    groups = df["spot_id"].values

    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42)
    # Strat by binned y
    y_strat = pd.qcut(y, q=5, labels=False, duplicates="drop")

    print(f"\n=== Stage 1: features → eq_percentile ===")
    for name, mdl in [
        ("Linear", LinearRegression()),
        ("Tree d=5", DecisionTreeRegressor(max_depth=5, min_samples_leaf=200, random_state=42)),
        ("Tree d=8", DecisionTreeRegressor(max_depth=8, min_samples_leaf=100, random_state=42)),
        ("GBT n=150", GradientBoostingRegressor(n_estimators=150, max_depth=4, learning_rate=0.1, random_state=42)),
    ]:
        r2s, maes = [], []
        for tr, te in sgkf.split(X, y_strat, groups=groups):
            mdl.fit(X.iloc[tr], y[tr])
            pred = mdl.predict(X.iloc[te])
            r2s.append(r2_score(y[te], pred))
            maes.append(mean_absolute_error(y[te], pred))
        print(f"  {name:15s}  R²={np.mean(r2s):.3f}  MAE={np.mean(maes):.3f}")

    # ── eq_percentile distribution per cell ──
    print(f"\n=== eq_percentile median + IQR per (bucket × MV × board) — top 20 by n ===")
    cell = (
        df.groupby(["equity_bucket", "mv_cat", "board_family"])["eq_percentile"]
        .agg(["median", "count",
              ("q25", lambda x: x.quantile(0.25)),
              ("q75", lambda x: x.quantile(0.75))])
        .reset_index()
        .sort_values("count", ascending=False)
        .head(20)
    )
    for _, r in cell.iterrows():
        print(f"  {r['equity_bucket']:13s} × {r['mv_cat']:15s} × {r['board_family']:18s}  med={r['median']*100:5.1f}%  IQR=[{r['q25']*100:4.0f}-{r['q75']*100:4.0f}]%  n={r['count']:.0f}")

    # ── Stage 2: eq_percentile → bet_freq (attack) ──
    attack = df[df["action_context"] == "attack"].copy()
    print(f"\n=== Stage 2A: eq_percentile → bet_freq (attack, n={len(attack)}) ===")
    # bin eq_percentile and report mean bet_freq
    attack["eq_bin"] = pd.cut(attack["eq_percentile"], bins=10, labels=False)
    print(f"  eq% bin   bet_freq mean   median   n")
    for b in sorted(attack["eq_bin"].dropna().unique()):
        sub = attack[attack["eq_bin"] == b]
        mean_bet = sub["bet_freq"].mean()
        med_bet = sub["bet_freq"].median()
        print(f"  bin {int(b):2d} ({b*10:2.0f}-{(b+1)*10:2.0f}%)  mean={mean_bet*100:5.1f}%  med={med_bet*100:5.1f}%  n={len(sub):6d}")

    # ── Stage 2: eq_percentile → fold_freq (defense) ──
    defense = df[df["action_context"] == "defense"].copy()
    print(f"\n=== Stage 2B: eq_percentile → action dist (defense, n={len(defense)}) ===")
    if len(defense) > 100:
        defense["eq_bin"] = pd.cut(defense["eq_percentile"], bins=10, labels=False)
        print(f"  eq% bin   FOLD%   CALL%   RAISE%   n")
        for b in sorted(defense["eq_bin"].dropna().unique()):
            sub = defense[defense["eq_bin"] == b]
            f = sub["fold_freq"].mean()
            c = sub["call_freq"].mean()
            r = sub["raise_freq"].mean()
            print(f"  bin {int(b):2d} ({b*10:2.0f}-{(b+1)*10:2.0f}%)  fold={f*100:5.1f}%  call={c*100:5.1f}%  raise={r*100:5.1f}%  n={len(sub):6d}")

    # ── Correlation tests ──
    print(f"\n=== Correlations ===")
    print(f"attack: corr(eq_percentile, bet_freq) = {attack['eq_percentile'].corr(attack['bet_freq']):.3f}")
    if len(defense) > 100:
        print(f"defense: corr(eq_percentile, fold_freq) = {defense['eq_percentile'].corr(defense['fold_freq']):.3f}")
        print(f"defense: corr(eq_percentile, raise_freq) = {defense['eq_percentile'].corr(defense['raise_freq']):.3f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
