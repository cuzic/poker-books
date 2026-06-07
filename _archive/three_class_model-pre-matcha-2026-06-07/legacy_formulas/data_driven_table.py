#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Build a data-driven replacement for the existing 25-cell table.

Instead of predicting per-combo bet/check, aggregate the GTO Wizard data by
  (position, street, board_family, mv_cat, dv_cat) → median bet_freq.

This gives a lookup table that's both interpretable and data-grounded.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"


def mv_band(mv: str) -> str:
    """5-band MV reduction matching the book's existing scheme."""
    if mv in {"no_made_hand", "ace_high", "king_high"}:
        return "air"
    if mv in {"low_pair", "underpair", "third_pair"}:
        return "weak"
    if mv in {"second_pair"}:
        return "mid"
    if mv in {"top_pair", "overpair"}:
        return "strong"
    if mv in {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}:
        return "nut"
    return "unknown"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    df["mv_band"] = df["mv_cat"].apply(mv_band)
    df = df[(df["mv_band"] != "unknown") & (df["dv_cat"] != "unknown")]
    print(f"Loaded {len(df)} rows (after unknown filter)")

    band_order = ["air", "weak", "mid", "strong", "nut"]

    # Main table: (position, street, mv_band) → median bet_freq
    print(f"\n=== Data-driven 25-cell base (median bet_freq %) ===")
    print(f"Filtered to: family=cash, street=flop, line=srp, dv=no_draw")
    sub = df[(df["family"] == "cash") & (df["street"] == "flop") & (df["line"] == "srp") & (df["dv_cat"] == "no_draw")]
    print(f"  n_rows={len(sub)}")
    pivot = sub.pivot_table(
        index="hero_rel", columns="mv_band",
        values="bet_freq", aggfunc=["median", "count"],
    )
    pivot = pivot.reindex(columns=pd.MultiIndex.from_product([["median", "count"], band_order]), fill_value=np.nan)
    # print cleanly
    print()
    print("  Position  |   air    weak    mid   strong   nut")
    print("  ----------|--------------------------------------")
    for pos in pivot.index:
        med_row = pivot["median"].loc[pos]
        cnt_row = pivot["count"].loc[pos]
        vals = []
        for b in band_order:
            m = med_row.get(b, np.nan)
            c = cnt_row.get(b, 0)
            if pd.isna(m):
                vals.append("  --  ")
            else:
                vals.append(f"{m*100:5.0f}%")
        print(f"  {pos:8s}  |  {'  '.join(vals)}")
    print()
    print("  Counts per cell:")
    for pos in pivot.index:
        cnt_row = pivot["count"].loc[pos]
        vals = [f"{int(cnt_row.get(b, 0)):>6d}" for b in band_order]
        print(f"  {pos:8s}  |  {' '.join(vals)}")

    # Board family stratification (most important refinement)
    print(f"\n=== Stratified by board_family (cash + flop + srp + IP, no_draw) ===")
    sub2 = df[(df["family"] == "cash") & (df["street"] == "flop") & (df["line"] == "srp") & (df["dv_cat"] == "no_draw") & (df["hero_rel"] == "IP")]
    if len(sub2) > 50:
        p2 = sub2.pivot_table(
            index="board_family", columns="mv_band",
            values="bet_freq", aggfunc="median",
        )
        p2 = p2.reindex(columns=band_order)
        print()
        print("  IP board_family ×   air    weak    mid   strong   nut")
        print("  --------------------------------------------------------")
        for bf in p2.index:
            vals = []
            for b in band_order:
                v = p2.loc[bf, b] if b in p2.columns else np.nan
                vals.append(f"{v*100:5.0f}%" if not pd.isna(v) else "  --  ")
            print(f"  {bf:18s}  |  {'  '.join(vals)}")

    # Same for OOP
    sub3 = df[(df["family"] == "cash") & (df["street"] == "flop") & (df["line"] == "srp") & (df["dv_cat"] == "no_draw") & (df["hero_rel"] == "OOP")]
    if len(sub3) > 50:
        p3 = sub3.pivot_table(
            index="board_family", columns="mv_band",
            values="bet_freq", aggfunc="median",
        )
        p3 = p3.reindex(columns=band_order)
        print()
        print("  OOP board_family ×  air    weak    mid   strong   nut")
        print("  --------------------------------------------------------")
        for bf in p3.index:
            vals = []
            for b in band_order:
                v = p3.loc[bf, b] if b in p3.columns else np.nan
                vals.append(f"{v*100:5.0f}%" if not pd.isna(v) else "  --  ")
            print(f"  {bf:18s}  |  {'  '.join(vals)}")

    # Compare with existing 25-cell (the published values)
    print(f"\n=== Published vs data-driven (cash IP/OOP combined, srp+flop+no_draw) ===")
    print("  Band:        air   weak   mid  strong  nut")
    print("  Published:    44    37    42    57    62")
    sub_all = df[(df["family"] == "cash") & (df["street"] == "flop") & (df["line"] == "srp") & (df["dv_cat"] == "no_draw")]
    medians = [sub_all[sub_all["mv_band"] == b]["bet_freq"].median() for b in band_order]
    vals = [f"{m*100:5.0f}%" if not pd.isna(m) else "  --  " for m in medians]
    print(f"  Data:        {' '.join(vals)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
