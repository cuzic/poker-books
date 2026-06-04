#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Verify defense framework v2: eq_percentile-based two-stage.

Stage 1: (bucket, mv, board, dv) → predicted eq_percentile (lookup median)
Stage 2: eq_percentile bin → modal action (FOLD / CALL / RAISE)

Compare two scenarios:
  (a) ORACLE: use actual eq_percentile (best-case accuracy)
  (b) PREDICTED: use Stage1 median lookup (realistic accuracy)
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def eq_to_action(eq: float) -> str:
    """Stage 2: monotonic defense action mapping (v3 — calibrated to modal in each bin).

    Bin → modal action (from actual data):
      < 0.40  → FOLD (bins 0-3 all FOLD-modal)
      ≥ 0.40  → CALL (bins 4-9 all CALL-modal, including 90-100% which is 63% CALL)
    """
    if eq is None or pd.isna(eq):
        return "CALL"
    if eq < 0.40:
        return "FOLD"
    return "CALL"


def actual_modal(row) -> str:
    a = {"FOLD": row.get("fold_freq", 0) or 0,
         "CALL": row.get("call_freq", 0) or 0,
         "RAISE": row.get("raise_freq", 0) or 0}
    return max(a, key=lambda k: a[k])


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    print(f"Loaded {len(df)} rows")

    # Defense + has eq_percentile (Format A only)
    df = df[(df["action_context"] == "defense") & (df["eq_percentile"].notna()) & (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    print(f"Defense + eq_percentile + bucket: {len(df)} rows / spots: {df['spot_id'].nunique()}")

    df["actual_modal"] = df.apply(actual_modal, axis=1)
    print(f"\nActual modal:")
    print(df["actual_modal"].value_counts())

    # ── (a) ORACLE: use actual eq_percentile ──
    df["pred_oracle"] = df["eq_percentile"].apply(eq_to_action)
    df["oracle_correct"] = df["pred_oracle"] == df["actual_modal"]
    print(f"\n=== (a) ORACLE: actual eq_percentile → action ===")
    print(f"Accuracy: {df['oracle_correct'].mean()*100:.1f}%")
    print("Confusion:")
    print(pd.crosstab(df["pred_oracle"], df["actual_modal"]))

    # ── Build Stage 1 lookup table from training ──
    # Split by spot for honest evaluation
    spots = sorted(df["spot_id"].unique())
    half = len(spots) // 2
    train_spots = set(spots[:half])
    test_spots = set(spots[half:])
    train = df[df["spot_id"].isin(train_spots)]
    test = df[df["spot_id"].isin(test_spots)]
    print(f"\nTrain/Test split: {len(train)}/{len(test)} rows ({len(train_spots)}/{len(test_spots)} spots)")

    # Per-cell median eq_percentile
    keys = ["equity_bucket", "mv_cat", "board_family", "dv_cat"]
    cell_med = train.groupby(keys)["eq_percentile"].median().to_dict()
    # fallback to (bucket, board) only
    fallback = train.groupby(["equity_bucket", "board_family"])["eq_percentile"].median().to_dict()

    def predict_eq(r):
        key = (r["equity_bucket"], r["mv_cat"], r["board_family"], r["dv_cat"])
        if key in cell_med:
            return cell_med[key]
        k2 = (r["equity_bucket"], r["board_family"])
        if k2 in fallback:
            return fallback[k2]
        return 0.5

    test = test.copy()
    test["pred_eq"] = test.apply(predict_eq, axis=1)
    test["pred_stage2"] = test["pred_eq"].apply(eq_to_action)
    test["pred_correct"] = test["pred_stage2"] == test["actual_modal"]

    print(f"\n=== (b) PREDICTED: Stage1 lookup + Stage2 mapping ===")
    print(f"Accuracy: {test['pred_correct'].mean()*100:.1f}%")
    print(f"MAE on eq_percentile: {(test['pred_eq'] - test['eq_percentile']).abs().mean():.3f}")
    print("Confusion:")
    print(pd.crosstab(test["pred_stage2"], test["actual_modal"]))

    # Per-bucket
    print(f"\n=== Per-bucket on TEST (predicted) ===")
    for bk, sub in test.groupby("equity_bucket"):
        if len(sub) < 50:
            continue
        acc = sub["pred_correct"].mean() * 100
        print(f"  {bk:13s} n={len(sub):6d}  acc={acc:5.1f}%")

    print(f"\n=== Per-board on TEST (predicted) ===")
    for bf, sub in test.groupby("board_family"):
        if len(sub) < 50:
            continue
        acc = sub["pred_correct"].mean() * 100
        print(f"  {bf:18s} n={len(sub):6d}  acc={acc:5.1f}%")

    # Stage 2 calibration: how accurate is eq_to_action on the actual distribution?
    print(f"\n=== Stage 2 mapping calibration (test set, oracle eq) ===")
    test["pred_oracle"] = test["eq_percentile"].apply(eq_to_action)
    test["oracle_correct"] = test["pred_oracle"] == test["actual_modal"]
    print(f"Oracle accuracy: {test['oracle_correct'].mean()*100:.1f}%")

    # Drill: per eq_percentile bin, what's our Stage2 accuracy?
    test["eq_bin"] = pd.cut(test["eq_percentile"], bins=10, labels=False)
    print(f"\n  eq_bin    pred_action  actual_modal_dist            oracle_acc%")
    for b in sorted(test["eq_bin"].dropna().unique()):
        sub = test[test["eq_bin"] == b]
        dist = sub["actual_modal"].value_counts(normalize=True)
        dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
        modal_pred = eq_to_action(b * 0.1 + 0.05)
        acc = (sub["actual_modal"] == modal_pred).mean() * 100
        print(f"  bin {int(b):2d}    {modal_pred:5s}        {dist_str:60s}  {acc:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
