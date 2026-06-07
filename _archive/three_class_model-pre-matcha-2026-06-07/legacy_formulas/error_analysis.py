#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Investigate defense prediction errors in detail.

Three angles:
  1. Where does Stage 1 (eq_percentile prediction) fail? — large prediction error cells
  2. Where does Stage 2 (eq → action) fail at boundaries? — bin 3 (30-40%) and bin 9 (90-100%)
  3. Sample failed rows: actual hand169, board, opponent action, etc.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def eq_to_action(eq):
    if eq is None or pd.isna(eq):
        return "CALL"
    if eq < 0.40:
        return "FOLD"
    return "CALL"


def actual_modal(row):
    a = {"FOLD": row.get("fold_freq", 0) or 0,
         "CALL": row.get("call_freq", 0) or 0,
         "RAISE": row.get("raise_freq", 0) or 0}
    return max(a, key=lambda k: a[k])


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = df[(df["action_context"] == "defense") & (df["eq_percentile"].notna()) & (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    df["actual_modal"] = df.apply(actual_modal, axis=1)
    df["pred_oracle"] = df["eq_percentile"].apply(eq_to_action)
    df["correct"] = df["pred_oracle"] == df["actual_modal"]
    print(f"n={len(df)}, oracle acc={df['correct'].mean()*100:.1f}%")

    # ── Errors by eq bin × bucket ──
    df["eq_bin"] = pd.cut(df["eq_percentile"], bins=[0, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 1.001],
                          labels=["0-20", "20-30", "30-40", "40-50", "50-70", "70-90", "90-100"])

    print(f"\n=== Errors per (eq_bin × bucket × board) ===")
    err = df[~df["correct"]]
    grouped = err.groupby(["eq_bin", "equity_bucket", "board_family", "pred_oracle", "actual_modal"]).size().reset_index(name="n_err")
    grouped = grouped.sort_values("n_err", ascending=False)
    print(grouped.head(25).to_string(index=False))

    # ── Identify specific spots where weak_hands fails ──
    print(f"\n=== weak_hands error breakdown by source spot ===")
    weak = df[df["equity_bucket"] == "weak_hands"]
    print(f"weak_hands n={len(weak)}, correct={weak['correct'].mean()*100:.1f}%")
    for spot_id, sub in weak.groupby("spot_id"):
        if len(sub) < 50:
            continue
        acc = sub["correct"].mean() * 100
        src = sub["source_path"].iloc[0]
        eq_med = sub["eq_percentile"].median() * 100
        # actual modal counts
        modals = sub["actual_modal"].value_counts().to_dict()
        modal_str = " ".join(f"{k}:{v}" for k, v in sorted(modals.items()))
        print(f"  {spot_id:15s} n={len(sub):4d} acc={acc:5.1f}% eq_med={eq_med:.0f}% modals={modal_str}  ({src})")

    # ── Look at boundary bin 30-40% detailed ──
    print(f"\n=== eq 30-40% (boundary): which combos? ===")
    boundary = df[(df["eq_percentile"] >= 0.30) & (df["eq_percentile"] < 0.40)]
    if len(boundary) > 0:
        print(f"n={len(boundary)}, correct={boundary['correct'].mean()*100:.1f}%")
        # Per board_family
        for bf, sub in boundary.groupby("board_family"):
            if len(sub) < 100:
                continue
            dist = sub["actual_modal"].value_counts(normalize=True).to_dict()
            dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
            print(f"  {bf:18s} n={len(sub):5d}  actual_dist={dist_str}")

    # ── Look at bin 90-100% (RAISE boundary) ──
    print(f"\n=== eq 90-100% (high-eq boundary): CALL vs RAISE ===")
    high_eq = df[df["eq_percentile"] >= 0.90]
    if len(high_eq) > 0:
        print(f"n={len(high_eq)}, correct={high_eq['correct'].mean()*100:.1f}%")
        for bf, sub in high_eq.groupby("board_family"):
            if len(sub) < 100:
                continue
            dist = sub["actual_modal"].value_counts(normalize=True).to_dict()
            dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
            print(f"  {bf:18s} n={len(sub):5d}  actual_dist={dist_str}")
        # Per source / depth
        print(f"  per source path/spot:")
        for sid, sub in high_eq.groupby("spot_id"):
            if len(sub) < 50:
                continue
            modals = sub["actual_modal"].value_counts(normalize=True).to_dict()
            src = sub["source_path"].iloc[0]
            print(f"    {sid:15s} n={len(sub):3d}  {{ {'  '.join(f'{k}={v*100:.0f}%' for k,v in sorted(modals.items()))} }}  {src}")

    # ── Specific examples of wrong-direction errors ──
    print(f"\n=== Sample wrong-direction errors (FOLD pred but actual CALL+) ===")
    wrong1 = df[(df["pred_oracle"] == "FOLD") & (df["actual_modal"] == "CALL")]
    print(f"FOLD→CALL errors: {len(wrong1)}")
    # group by spot
    for sid, sub in wrong1.groupby("spot_id"):
        if len(sub) < 30:
            continue
        eq_range = (sub["eq_percentile"].min()*100, sub["eq_percentile"].max()*100)
        print(f"  {sid:15s} n={len(sub):4d}  eq=[{eq_range[0]:.0f}-{eq_range[1]:.0f}]%  top hand169:")
        top = sub["hand169"].value_counts().head(5).to_dict()
        for h, n in top.items():
            row = sub[sub["hand169"] == h].iloc[0]
            print(f"    {h:5s} (n={n}) board={row.get('board_flop','')!r} eq={row['eq_percentile']*100:.0f}%")

    print(f"\n=== Sample wrong-direction errors (CALL pred but actual FOLD) ===")
    wrong2 = df[(df["pred_oracle"] == "CALL") & (df["actual_modal"] == "FOLD")]
    print(f"CALL→FOLD errors: {len(wrong2)}")
    for sid, sub in wrong2.groupby("spot_id"):
        if len(sub) < 30:
            continue
        eq_range = (sub["eq_percentile"].min()*100, sub["eq_percentile"].max()*100)
        print(f"  {sid:15s} n={len(sub):4d}  eq=[{eq_range[0]:.0f}-{eq_range[1]:.0f}]%  top hand169:")
        top = sub["hand169"].value_counts().head(5).to_dict()
        for h, n in top.items():
            row = sub[sub["hand169"] == h].iloc[0]
            print(f"    {h:5s} (n={n}) board={row.get('board_flop','')!r} eq={row['eq_percentile']*100:.0f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
