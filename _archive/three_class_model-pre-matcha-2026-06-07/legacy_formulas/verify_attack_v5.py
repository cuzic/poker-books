#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Attack v5: 3-band prediction with size axis.

Strategy:
  Small bet (<45% pot): mixed across all eq bands
  Big bet (>=85% pot): polarized — CHECK heavy middle, BET extremes

Predict 3-band per (eq_bin, size_bucket).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")


def size_bucket(s):
    if pd.isna(s):
        return "unknown"
    if s < 0.45:
        return "small"
    if s < 0.85:
        return "mid"
    return "big"


def freq_to_3band(f):
    if f < 0.25: return "LOW"
    if f < 0.75: return "MIX"
    return "HIGH"


def predict_attack(eq, size_b, board_family, equity_bucket, mv_cat):
    """Predict 3-band for attack action."""
    if pd.isna(eq) or pd.isna(size_b) or size_b == "unknown":
        return "MIX"

    if size_b == "small":
        # Small bet: mostly MIX across eq, except 30-50 lean CHECK (LOW), 90+ lean HIGH
        if eq < 0.30 and equity_bucket == "trash_hands":
            # Pure check unless draw
            return "LOW"
        if eq >= 0.85:
            return "MIX"  # value+slowplay split, MIX is safest
        if 0.30 <= eq < 0.50:
            return "LOW"  # CHECK (medium-weak)
        return "MIX"

    if size_b == "big":
        # Big bet: polarized → mostly LOW (CHECK) except extremes
        if eq < 0.10:
            # Very low eq: data shows BET:12% CHECK:64% MIX:24%
            return "LOW"  # CHECK modal
        if eq >= 0.90:
            # 90-100: BET:38% CHECK:35% MIX:27% — borderline BET
            return "MIX"
        if eq >= 0.85:
            return "MIX"
        # middle eq: CHECK heavy
        return "LOW"

    return "MIX"


def main() -> int:
    main_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "dataset_unified.csv", low_memory=False)
    bet_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "attack_bet_size.csv")
    bet_df = bet_df[["spot_id", "primary_size_pot"]].drop_duplicates(subset=["spot_id"])
    df = main_df.merge(bet_df, on="spot_id", how="left")

    df = df[(df["action_context"] == "attack") &
            (df["eq_percentile"].notna()) &
            (df["primary_size_pot"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    df["size_bucket"] = df["primary_size_pot"].apply(size_bucket)
    df["actual_band"] = df["bet_freq"].apply(freq_to_3band)
    print(f"Attack rows with eq + size: {len(df)} / spots: {df['spot_id'].nunique()}")
    print(f"\nActual 3-band distribution:")
    print(df["actual_band"].value_counts())

    df["pred_band"] = df.apply(
        lambda r: predict_attack(r["eq_percentile"], r["size_bucket"],
                                  str(r.get("board_family", "")),
                                  r["equity_bucket"], r["mv_cat"]),
        axis=1,
    )
    df["correct"] = df["pred_band"] == df["actual_band"]
    print(f"\n=== v5 overall accuracy: {df['correct'].mean()*100:.1f}% ===")
    print(pd.crosstab(df["pred_band"], df["actual_band"], normalize="index").round(2))

    print(f"\n=== Per (size_bucket × bucket) ===")
    for sz in ["small", "big"]:
        for bk in ["best_hands","good_hands","weak_hands","trash_hands"]:
            sub = df[(df["size_bucket"] == sz) & (df["equity_bucket"] == bk)]
            if len(sub) < 100:
                continue
            acc = sub["correct"].mean() * 100
            actual_dist = sub["actual_band"].value_counts(normalize=True).to_dict()
            dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(actual_dist.items()))
            print(f"  size={sz:5s} bucket={bk:13s} n={len(sub):6d}  acc={acc:5.1f}%  actual_dist={dist_str}")

    print(f"\n=== Per board_family ===")
    for bf, sub in df.groupby("board_family"):
        if len(sub) < 500:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {bf:18s} n={len(sub):6d}  acc={acc:5.1f}%")

    # Confidence tier: per cell IQR
    keys = ["size_bucket", "equity_bucket", "mv_cat", "board_family"]
    cell_iqr = df.groupby(keys)["bet_freq"].agg([
        ("q25", lambda x: x.quantile(0.25)),
        ("q75", lambda x: x.quantile(0.75)),
        "count",
    ]).reset_index()
    cell_iqr["iqr"] = cell_iqr["q75"] - cell_iqr["q25"]
    cell_iqr = cell_iqr[cell_iqr["count"] >= 30]
    cell_iqr["confidence"] = cell_iqr["iqr"].apply(
        lambda x: "HIGH" if x < 0.10 else ("MED" if x < 0.30 else "LOW")
    )
    print(f"\n=== Cell confidence distribution ===")
    print(cell_iqr["confidence"].value_counts())

    # Apply confidence to rows
    conf_dict = {(r["size_bucket"], r["equity_bucket"], r["mv_cat"], r["board_family"]): r["confidence"]
                 for _, r in cell_iqr.iterrows()}
    df["conf"] = df.apply(lambda r: conf_dict.get((r["size_bucket"], r["equity_bucket"], r["mv_cat"], r["board_family"]), "LOW"), axis=1)
    print(f"\n=== Accuracy by confidence ===")
    for tier in ["HIGH","MED","LOW"]:
        sub = df[df["conf"] == tier]
        if len(sub) < 100:
            continue
        cov = len(sub) / len(df) * 100
        acc = sub["correct"].mean() * 100
        print(f"  {tier}: n={len(sub):6d} ({cov:.0f}%)  acc={acc:5.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
