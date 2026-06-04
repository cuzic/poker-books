#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v7: simpler 3-band (LOW / MIX / HIGH) with confidence tier.

LOW   = bet_freq < 25%
MIX   = 25-75%
HIGH  = bet_freq >= 75%

Same cell key as v6: (bucket, mv_simple, board_family, dv_cat).
Per-cell IQR → confidence tier (HIGH/MED/LOW).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402
from verify_v6_mv_sub import simplify_mv  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"


def freq_to_3band(f: float) -> str:
    if f < 0.25:
        return "LOW"
    if f < 0.75:
        return "MIX"
    return "HIGH"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    df["mv_simple"] = df["mv_cat"].apply(simplify_mv)
    df["actual_3"] = df["bet_freq"].apply(freq_to_3band)

    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")
    print(f"\nActual 3-band distribution:")
    print(df["actual_3"].value_counts())

    keys = ["equity_bucket", "mv_simple", "board_family", "dv_cat"]
    cell = (
        df.groupby(keys)["bet_freq"]
        .agg(["median", "count",
              ("q25", lambda x: x.quantile(0.25)),
              ("q75", lambda x: x.quantile(0.75))])
        .reset_index()
    )
    cell["iqr"] = cell["q75"] - cell["q25"]
    cell["pred_3"] = cell["median"].apply(freq_to_3band)
    cell["confidence"] = cell["iqr"].apply(lambda x: "HIGH" if x < 0.10 else ("MED" if x < 0.30 else "LOW"))
    cell = cell[cell["count"] >= 30].copy()
    print(f"\nCells with n>=30: {len(cell)}")
    print(f"\n3-band pred distribution across cells:")
    print(cell["pred_3"].value_counts())
    print(f"\nConfidence tier distribution across cells:")
    print(cell["confidence"].value_counts())

    cell_dict = {(r["equity_bucket"], r["mv_simple"], r["board_family"], r["dv_cat"]): (r["pred_3"], r["confidence"], r["iqr"], r["count"])
                 for _, r in cell.iterrows()}

    def lookup(r):
        return cell_dict.get((r["equity_bucket"], r["mv_simple"], r["board_family"], r["dv_cat"]), (None, None, None, 0))
    df[["pred_3","confidence","cell_iqr","cell_n"]] = df.apply(lambda r: pd.Series(lookup(r)), axis=1)
    df = df[df["pred_3"].notna()].copy()
    df["exact"] = df["pred_3"] == df["actual_3"]
    print(f"\nRows assignable: {len(df)}")

    print(f"\n=== v7 3-band overall ===")
    print(f"Exact: {df['exact'].mean()*100:.1f}%")
    conf = pd.crosstab(df["pred_3"], df["actual_3"], normalize="index") * 100
    print(conf.round(0).astype(int).reindex(["LOW","MIX","HIGH"], columns=["LOW","MIX","HIGH"]))

    print(f"\n=== Per predicted-class ===")
    for cls in ["LOW","MIX","HIGH"]:
        rows = df[df["pred_3"] == cls]
        if len(rows) < 100:
            continue
        acc = rows["exact"].mean()*100
        # also precision against actual
        tp = ((df["pred_3"] == cls) & (df["actual_3"] == cls)).sum()
        fp = ((df["pred_3"] == cls) & (df["actual_3"] != cls)).sum()
        prec = tp / max(tp+fp, 1) * 100
        actual_match_dist = rows["actual_3"].value_counts(normalize=True)
        print(f"  {cls:5s} n={len(rows):6d}  prec={prec:.1f}%  actual_dist={dict((k, f'{v*100:.0f}%') for k,v in actual_match_dist.items())}")

    print(f"\n=== By confidence tier ===")
    for tier in ["HIGH", "MED", "LOW"]:
        rows = df[df["confidence"] == tier]
        if len(rows) < 100:
            continue
        cov = len(rows) / len(df) * 100
        acc = rows["exact"].mean()*100
        print(f"  {tier} n={len(rows):6d} ({cov:.0f}%)  exact={acc:.1f}%")

    # Sample big cells
    print(f"\n=== Top cells (n>=500) ===")
    big = cell[cell["count"]>=500].sort_values("count", ascending=False).head(30)
    for _, r in big.iterrows():
        print(f"  {r['equity_bucket']:13s} × {r['mv_simple']:13s} × {r['board_family']:18s} × {r['dv_cat']:18s}  med={r['median']*100:5.0f}% iqr={r['iqr']*100:4.0f}%  pred={r['pred_3']:4s}  conf={r['confidence']:4s}  n={r['count']:.0f}")

    out_path = ROOT / "scripts" / "three_class_model" / "v7_3band_table.csv"
    cell.to_csv(out_path, index=False)
    print(f"\nSaved → {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
