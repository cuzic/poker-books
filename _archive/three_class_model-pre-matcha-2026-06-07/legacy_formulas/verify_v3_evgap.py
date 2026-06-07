#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Verify v3 with ev_gap-aware 3-class prediction (BET / CHECK / MIXED).

Predictions:
  - If framework says BET and ev_gap > threshold → "BET"
  - If framework says CHECK and ev_gap > threshold → "CHECK"
  - Otherwise → "MIXED" (defer / randomize)

Actual ground truth labels (per-combo):
  - actual = "BET" if bet_freq >= 0.65
  - actual = "CHECK" if bet_freq <= 0.35
  - actual = "MIXED" otherwise

Metrics:
  - Accuracy on "decided" subset
  - Coverage (how many rows we make a deterministic call on)
  - MIXED detection F1
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402
from verify_v2 import predict_v2  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)

    # Restrict to attack only (ev_check defined; defense logic separate)
    df = df[df["ev_check"].notna() & df["ev_bet"].notna()].copy()
    df["abs_ev_gap"] = (df["ev_bet"] - df["ev_check"]).abs()

    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")
    print(f"abs_ev_gap distribution (quantiles):")
    for q in [0.25, 0.5, 0.75, 0.9, 0.95]:
        print(f"  q{int(q*100)} = {df['abs_ev_gap'].quantile(q):.3f}")

    # ── Define ground truth labels ──
    def gt_label(freq):
        if freq <= 0.35:
            return "CHECK"
        if freq >= 0.65:
            return "BET"
        return "MIXED"
    df["actual_3"] = df["bet_freq"].apply(gt_label)
    print(f"\nGround-truth distribution:")
    print(df["actual_3"].value_counts())

    # ── Framework predicts BET/CHECK ──
    df["pred_v2"] = df.apply(
        lambda r: predict_v2(
            r["equity_bucket"], r["mv_cat"], r["dv_cat"],
            str(r.get("board_family", "")),
            str(r.get("card_a", "")), str(r.get("card_b", "")),
        ),
        axis=1,
    )

    # ── Sweep ev_gap threshold ──
    print(f"\n=== Threshold sweep: framework + ev_gap → 3-class ===")
    print(f"  τ      coverage  acc_on_decided  MIXED_recall")
    for tau in [0.10, 0.15, 0.20, 0.30, 0.40, 0.50, 0.75, 1.00]:
        # If ev_gap >= tau, output framework prediction; else MIXED
        df["pred_3"] = df.apply(
            lambda r, t=tau: r["pred_v2"] if r["abs_ev_gap"] >= t else "MIXED",
            axis=1,
        )
        decided = df[df["pred_3"] != "MIXED"]
        coverage = len(decided) / len(df)
        acc_decided = (decided["pred_3"] == decided["actual_3"]).mean() if len(decided) > 0 else 0
        # MIXED recall: of true-MIXED rows, how many did we predict MIXED?
        true_mixed = df[df["actual_3"] == "MIXED"]
        if len(true_mixed) > 0:
            mixed_recall = (true_mixed["pred_3"] == "MIXED").mean()
        else:
            mixed_recall = 0
        print(f"  {tau:.2f}   {coverage*100:5.1f}%       {acc_decided*100:5.1f}%      {mixed_recall*100:5.1f}%")

    # At optimal τ=0.30, print full breakdown
    print(f"\n=== Full breakdown at τ=0.30 ===")
    df["pred_3"] = df.apply(
        lambda r: r["pred_v2"] if r["abs_ev_gap"] >= 0.30 else "MIXED",
        axis=1,
    )
    conf = pd.crosstab(df["pred_3"], df["actual_3"])
    print(conf)
    for cls in ["BET", "CHECK", "MIXED"]:
        tp = ((df["pred_3"] == cls) & (df["actual_3"] == cls)).sum()
        fp = ((df["pred_3"] == cls) & (df["actual_3"] != cls)).sum()
        fn = ((df["pred_3"] != cls) & (df["actual_3"] == cls)).sum()
        prec = tp / max(tp + fp, 1) * 100
        rec = tp / max(tp + fn, 1) * 100
        f1 = 2 * prec * rec / max(prec + rec, 0.01)
        print(f"  {cls}: prec={prec:.1f}%  recall={rec:.1f}%  f1={f1:.1f}%")

    # Per-bucket × ctx at τ=0.30
    print(f"\n=== Per-bucket at τ=0.30 ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 1000:
            continue
        decided = sub[sub["pred_3"] != "MIXED"]
        cov = len(decided) / len(sub) * 100
        acc = (decided["pred_3"] == decided["actual_3"]).mean() * 100 if len(decided) > 0 else 0
        print(f"  {bk:13s} n={len(sub):6d} coverage={cov:.0f}% acc_on_decided={acc:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
