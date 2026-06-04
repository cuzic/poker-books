#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v5: 5-band prediction (0-20, 20-40, 40-60, 60-80, 80-100% bet).

This captures GTO's mixed strategy nature explicitly instead of forcing binary.

Approach:
- Predict band based on (bucket, board_family, dv_cat)
- Use data-driven median bet_freq per cell, mapped to band
- Evaluate accuracy on exact band match + ±1 band tolerance
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"


BANDS = [
    ("almost_check", 0.0, 0.20),
    ("lean_check",   0.20, 0.40),
    ("pure_mix",     0.40, 0.60),
    ("lean_bet",     0.60, 0.80),
    ("almost_bet",   0.80, 1.001),
]
BAND_NAMES = [b[0] for b in BANDS]


def freq_to_band(f: float) -> str:
    for name, lo, hi in BANDS:
        if lo <= f < hi:
            return name
    return "almost_bet"


def band_to_idx(b: str) -> int:
    return BAND_NAMES.index(b)


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)

    # Restrict to attack
    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")
    df["actual_band"] = df["bet_freq"].apply(freq_to_band)
    print(f"\nActual band distribution:")
    print(df["actual_band"].value_counts())

    # Build data-driven prediction table: median bet_freq per (bucket, board, dv) → band
    print(f"\n=== Building per-cell prediction table ===")
    cell_table = (
        df.groupby(["equity_bucket", "board_family", "dv_cat"])["bet_freq"]
        .agg(["median", "mean", "count"])
        .reset_index()
    )
    cell_table["pred_band"] = cell_table["median"].apply(freq_to_band)
    print(f"Total cells: {len(cell_table)}")
    print(f"Cells with n>=30:")
    print(cell_table[cell_table["count"] >= 30][["equity_bucket","board_family","dv_cat","median","pred_band","count"]].head(20))

    # Apply: each row gets the cell's predicted band
    table_dict = {
        (r["equity_bucket"], r["board_family"], r["dv_cat"]): (r["pred_band"], r["count"])
        for _, r in cell_table.iterrows()
    }
    def lookup_band(r):
        key = (r["equity_bucket"], r["board_family"], r["dv_cat"])
        return table_dict.get(key, ("pure_mix", 0))[0]
    df["pred_band"] = df.apply(lookup_band, axis=1)

    # Accuracy: exact + ±1 tolerance
    df["exact"] = df["pred_band"] == df["actual_band"]
    df["pred_idx"] = df["pred_band"].apply(band_to_idx)
    df["actual_idx"] = df["actual_band"].apply(band_to_idx)
    df["band_diff"] = (df["pred_idx"] - df["actual_idx"]).abs()
    df["within1"] = df["band_diff"] <= 1

    print(f"\n=== v5 5-band accuracy ===")
    print(f"Exact match (5-band):    {df['exact'].mean()*100:.1f}%")
    print(f"Within ±1 band:           {df['within1'].mean()*100:.1f}%")
    print(f"Within ±2 bands:         {(df['band_diff']<=2).mean()*100:.1f}%")
    avg_diff = df["band_diff"].mean()
    print(f"Mean band-diff:           {avg_diff:.2f}")

    print(f"\n=== Confusion (pred-row, actual-col) ===")
    conf = pd.crosstab(df["pred_band"], df["actual_band"], normalize="index") * 100
    print(conf.round(0).astype(int).reindex(BAND_NAMES, columns=BAND_NAMES))

    # Per-bucket
    print(f"\n=== Per-bucket exact + within-1 ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 100:
            continue
        ex = sub["exact"].mean() * 100
        w1 = sub["within1"].mean() * 100
        print(f"  {bk:13s} n={len(sub):6d}  exact={ex:5.1f}%  within±1={w1:5.1f}%")

    # Sample cells: most populated
    print(f"\n=== Top 30 most populated cells with median and band ===")
    top_cells = cell_table[cell_table["count"] >= 200].sort_values("count", ascending=False).head(30)
    for _, r in top_cells.iterrows():
        print(f"  {r['equity_bucket']:13s} × {r['board_family']:18s} × {r['dv_cat']:18s}  med={r['median']*100:5.0f}%  band={r['pred_band']:13s}  n={r['count']:.0f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
