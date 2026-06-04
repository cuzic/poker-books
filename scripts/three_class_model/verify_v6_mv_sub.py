#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v6: 5-band prediction with MV-level subdivision.

v5 used (bucket, board, dv) → band.
v6 adds mv_cat as a 4th axis → (bucket, mv_cat, board, dv) → band.

This should especially help best_hands (currently 18.7% exact) by separating
2P+/overpair (value bet) from top_pair (slowplay candidate).
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


# Simplify mv_cat to broader groups to avoid cell sparsity
def simplify_mv(mv: str) -> str:
    if mv in {"set", "trips", "two_pair", "straight", "flush", "fullhouse", "quads"}:
        return "2P_plus"
    if mv == "overpair":
        return "overpair"
    if mv == "top_pair":
        return "top_pair"
    if mv == "second_pair":
        return "second_pair"
    if mv == "third_pair":
        return "third_pair"
    if mv in {"low_pair", "underpair"}:
        return "weak_pair"
    if mv == "ace_high":
        return "ace_high"
    if mv == "king_high":
        return "king_high"
    if mv == "no_made_hand":
        return "no_made"
    return "other"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    df["mv_simple"] = df["mv_cat"].apply(simplify_mv)
    df["actual_band"] = df["bet_freq"].apply(freq_to_band)

    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")
    print(f"\nmv_simple distribution:")
    print(df["mv_simple"].value_counts())

    # Build the (bucket, mv_simple, board, dv) → median table
    keys = ["equity_bucket", "mv_simple", "board_family", "dv_cat"]
    cell_table = (
        df.groupby(keys)["bet_freq"]
        .agg(["median", "count"])
        .reset_index()
    )
    cell_table["pred_band"] = cell_table["median"].apply(freq_to_band)
    print(f"\nTotal cells: {len(cell_table)}")
    print(f"Cells with n>=30: {(cell_table['count']>=30).sum()}")

    # Build lookup with fallback strategy:
    #   Priority 1: full (bucket, mv, board, dv) cell with n>=20
    #   Priority 2: (bucket, mv, board, dv=no_draw) — drop DV
    #   Priority 3: (bucket, board, dv) v5-style
    full_table = {(r["equity_bucket"], r["mv_simple"], r["board_family"], r["dv_cat"]): (r["pred_band"], r["count"], r["median"])
                  for _, r in cell_table.iterrows() if r["count"] >= 20}
    # Fallback: aggregate on (bucket, mv, board) ignoring dv
    fb1 = (df.groupby(["equity_bucket","mv_simple","board_family"])["bet_freq"].median().to_dict())
    # Fallback: (bucket, board) only
    fb2 = (df.groupby(["equity_bucket","board_family"])["bet_freq"].median().to_dict())

    def predict_band(r):
        key = (r["equity_bucket"], r["mv_simple"], r["board_family"], r["dv_cat"])
        if key in full_table:
            return full_table[key][0]
        k2 = (r["equity_bucket"], r["mv_simple"], r["board_family"])
        if k2 in fb1:
            return freq_to_band(fb1[k2])
        k3 = (r["equity_bucket"], r["board_family"])
        if k3 in fb2:
            return freq_to_band(fb2[k3])
        return "pure_mix"

    df["pred_band"] = df.apply(predict_band, axis=1)

    df["exact"] = df["pred_band"] == df["actual_band"]
    df["pred_idx"] = df["pred_band"].apply(band_to_idx)
    df["actual_idx"] = df["actual_band"].apply(band_to_idx)
    df["band_diff"] = (df["pred_idx"] - df["actual_idx"]).abs()
    df["within1"] = df["band_diff"] <= 1

    print(f"\n=== v6 accuracy ===")
    print(f"Exact (5-band):    {df['exact'].mean()*100:.1f}%")
    print(f"Within ±1 band:     {df['within1'].mean()*100:.1f}%")
    print(f"Within ±2 bands:   {(df['band_diff']<=2).mean()*100:.1f}%")
    print(f"Mean band-diff:    {df['band_diff'].mean():.2f}")

    print(f"\n=== Per-bucket ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 100:
            continue
        ex = sub["exact"].mean() * 100
        w1 = sub["within1"].mean() * 100
        print(f"  {bk:13s} n={len(sub):6d}  exact={ex:5.1f}%  within±1={w1:5.1f}%")

    print(f"\n=== Per-bucket × mv_simple ===")
    for (bk, mv), sub in df.groupby(["equity_bucket","mv_simple"]):
        if len(sub) < 1000:
            continue
        ex = sub["exact"].mean() * 100
        w1 = sub["within1"].mean() * 100
        actual_dist = sub["actual_band"].value_counts(normalize=True).idxmax()
        print(f"  {bk:13s} × {mv:13s} n={len(sub):6d}  exact={ex:5.1f}%  ±1={w1:5.1f}%  modal_actual={actual_dist}")

    # Sample table rows for the book — top by count
    print(f"\n=== Top cells (n>=200) ===")
    big = cell_table[cell_table["count"] >= 200].sort_values("count", ascending=False).head(40)
    for _, r in big.iterrows():
        print(f"  {r['equity_bucket']:13s} × {r['mv_simple']:13s} × {r['board_family']:18s} × {r['dv_cat']:18s}  med={r['median']*100:5.0f}%  band={r['pred_band']:13s}  n={r['count']:.0f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
