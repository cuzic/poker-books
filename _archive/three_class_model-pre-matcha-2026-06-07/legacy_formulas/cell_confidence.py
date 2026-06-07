#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Cell-level confidence: predict per-cell whether the band prediction will be accurate.

For each cell (bucket, mv_simple, board_family, dv_cat) we measure:
- median bet_freq → predicted band
- IQR (Q75 - Q25) → cell spread
- std bet_freq
- n combos
- Exact accuracy of band-prediction on combos in this cell

Hypothesis: low IQR ↔ high Exact. Confidence = f(IQR or std).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402
from verify_v6_mv_sub import freq_to_band, simplify_mv  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    df["mv_simple"] = df["mv_cat"].apply(simplify_mv)
    df["actual_band"] = df["bet_freq"].apply(freq_to_band)

    # Per-cell stats
    keys = ["equity_bucket", "mv_simple", "board_family", "dv_cat"]
    cell_stats = (
        df.groupby(keys)["bet_freq"]
        .agg(["median", "mean", "std",
              ("q25", lambda x: x.quantile(0.25)),
              ("q75", lambda x: x.quantile(0.75)),
              "count"])
        .reset_index()
    )
    cell_stats["iqr"] = cell_stats["q75"] - cell_stats["q25"]
    cell_stats["pred_band"] = cell_stats["median"].apply(freq_to_band)
    cell_stats = cell_stats[cell_stats["count"] >= 30].copy()
    print(f"Cells with n>=30: {len(cell_stats)}")

    # Apply prediction per row
    cell_dict = {(r["equity_bucket"], r["mv_simple"], r["board_family"], r["dv_cat"]): (r["pred_band"], r["iqr"], r["std"], r["count"])
                 for _, r in cell_stats.iterrows()}

    def lookup(r):
        return cell_dict.get((r["equity_bucket"], r["mv_simple"], r["board_family"], r["dv_cat"]), (None, None, None, 0))
    df[["pred_band","cell_iqr","cell_std","cell_n"]] = df.apply(lambda r: pd.Series(lookup(r)), axis=1)
    df = df[df["pred_band"].notna()].copy()
    df["exact"] = df["pred_band"] == df["actual_band"]
    print(f"Rows assignable to cells: {len(df)}")

    # ── Predictability vs IQR ──
    print(f"\n=== Cell IQR vs Exact accuracy ===")
    bins = [(0.0,0.1),(0.1,0.2),(0.2,0.3),(0.3,0.4),(0.4,0.5),(0.5,1.0)]
    print(f"  IQR range       n_cells  n_rows   exact%   modal_band")
    for lo, hi in bins:
        cells = cell_stats[(cell_stats["iqr"]>=lo) & (cell_stats["iqr"]<hi)]
        rows = df[(df["cell_iqr"]>=lo) & (df["cell_iqr"]<hi)]
        if len(rows) < 100:
            continue
        acc = rows["exact"].mean() * 100
        modal_band = rows["pred_band"].mode().iloc[0] if len(rows) > 0 else "n/a"
        print(f"  {lo:.1f}-{hi:.1f}        {len(cells):3d}     {len(rows):6d}   {acc:5.1f}%   {modal_band}")

    # ── By predicted band ──
    print(f"\n=== Predicted band → Exact accuracy ===")
    for band in ["almost_check","lean_check","pure_mix","lean_bet","almost_bet"]:
        rows = df[df["pred_band"]==band]
        if len(rows) < 100:
            continue
        acc = rows["exact"].mean()*100
        avg_iqr = rows["cell_iqr"].mean()
        print(f"  {band:15s} n={len(rows):6d}  exact={acc:5.1f}%  avg_iqr={avg_iqr:.2f}")

    # ── Show high-confidence vs low-confidence cells ──
    print(f"\n=== Sample HIGH-CONFIDENCE cells (low IQR, large n) ===")
    high_conf = cell_stats[(cell_stats["iqr"]<0.10) & (cell_stats["count"]>=500)].sort_values("count", ascending=False).head(20)
    for _, r in high_conf.iterrows():
        print(f"  {r['equity_bucket']:13s} × {r['mv_simple']:13s} × {r['board_family']:18s} × {r['dv_cat']:18s}  med={r['median']*100:5.0f}% iqr={r['iqr']*100:4.0f}%  band={r['pred_band']:13s}  n={r['count']:.0f}")

    print(f"\n=== Sample LOW-CONFIDENCE cells (high IQR, large n) ===")
    low_conf = cell_stats[(cell_stats["iqr"]>0.40) & (cell_stats["count"]>=500)].sort_values("count", ascending=False).head(20)
    for _, r in low_conf.iterrows():
        print(f"  {r['equity_bucket']:13s} × {r['mv_simple']:13s} × {r['board_family']:18s} × {r['dv_cat']:18s}  med={r['median']*100:5.0f}% iqr={r['iqr']*100:4.0f}%  band={r['pred_band']:13s}  n={r['count']:.0f}")

    # ── Saving useful table for the book ──
    cell_stats["confidence"] = cell_stats["iqr"].apply(
        lambda x: "HIGH" if x < 0.10 else ("MED" if x < 0.30 else "LOW")
    )
    out_path = ROOT / "scripts" / "three_class_model" / "cell_with_confidence.csv"
    cell_stats[["equity_bucket","mv_simple","board_family","dv_cat","median","iqr","count","pred_band","confidence"]].to_csv(out_path, index=False)
    print(f"\nSaved → {out_path}")

    # ── HIGH/MED/LOW summary ──
    print(f"\n=== Summary by confidence tier ===")
    df_conf = df.merge(cell_stats[keys + ["confidence"]], on=keys, how="left")
    for tier in ["HIGH", "MED", "LOW"]:
        sub = df_conf[df_conf["confidence"] == tier]
        if len(sub) < 100:
            continue
        cov = len(sub) / len(df_conf) * 100
        acc = sub["exact"].mean() * 100
        print(f"  {tier} n={len(sub):6d} ({cov:.0f}% of data)  exact={acc:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
