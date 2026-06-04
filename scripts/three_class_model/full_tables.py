#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Generate the full set of data-driven tables for the framework redesign proposal."""
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


def pivot_print(df: pd.DataFrame, title: str, index_col: str, min_n: int = 30) -> None:
    band_order = ["air", "weak", "mid", "strong", "nut"]
    print(f"\n=== {title} ===")
    if len(df) == 0:
        print("  (no rows)")
        return
    print(f"  n_rows={len(df)}")
    median = df.pivot_table(index=index_col, columns="mv_band", values="bet_freq", aggfunc="median")
    count = df.pivot_table(index=index_col, columns="mv_band", values="bet_freq", aggfunc="count")
    median = median.reindex(columns=band_order)
    count = count.reindex(columns=band_order)

    print(f"  {index_col:18s} |   air    weak    mid   strong   nut")
    print(f"  {'-'*18}-+--------------------------------------")
    for idx in median.index:
        cells = []
        for b in band_order:
            n = count.loc[idx, b] if b in count.columns else 0
            if pd.isna(n) or n < min_n:
                cells.append("  --  ")
                continue
            m = median.loc[idx, b]
            cells.append(f"{m*100:5.0f}%" if not pd.isna(m) else "  --  ")
        print(f"  {str(idx):18s} |  {'  '.join(cells)}")
    print(f"  Counts per cell:")
    for idx in count.index:
        cells = []
        for b in band_order:
            n = count.loc[idx, b] if b in count.columns else 0
            cells.append(f"{'  --' if pd.isna(n) else f'{int(n):>5d}'}")
        print(f"  {str(idx):18s} |  {' '.join(cells)}")


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    df["mv_band"] = df["mv_cat"].apply(mv_band)
    df = df[(df["mv_band"] != "unknown") & (df["dv_cat"] != "unknown")]
    print(f"Loaded {len(df)} rows (after unknown filter)")

    # 1. CORE table: MTT OOP flop SRP × board_family (largest dataset, 128k rows)
    mtt_oop_flop = df[(df["family"] == "mtt") & (df["street"] == "flop") & (df["line"] == "srp") & (df["hero_rel"] == "OOP") & (df["dv_cat"] == "no_draw")]
    pivot_print(mtt_oop_flop, "MTT SRP Flop OOP, no_draw — board_family (CORE)", "board_family")

    # 2. Cash IP flop SRP × board_family (the 25-cell parent context)
    cash_ip_flop = df[(df["family"] == "cash") & (df["street"] == "flop") & (df["line"] == "srp") & (df["hero_rel"] == "IP") & (df["dv_cat"] == "no_draw")]
    pivot_print(cash_ip_flop, "Cash SRP Flop IP, no_draw — board_family", "board_family")

    # 3. MTT IP turn SRP — turn context
    mtt_ip_turn = df[(df["family"] == "mtt") & (df["street"] == "turn") & (df["line"] == "srp") & (df["hero_rel"] == "IP") & (df["dv_cat"] == "no_draw")]
    pivot_print(mtt_ip_turn, "MTT SRP Turn IP, no_draw — board_family", "board_family")

    # 4. MTT OOP turn SRP
    mtt_oop_turn = df[(df["family"] == "mtt") & (df["street"] == "turn") & (df["line"] == "srp") & (df["hero_rel"] == "OOP") & (df["dv_cat"] == "no_draw")]
    pivot_print(mtt_oop_turn, "MTT SRP Turn OOP, no_draw — board_family", "board_family")

    # 5. DV impact: MTT OOP flop dry_high
    dv_impact = df[(df["family"] == "mtt") & (df["street"] == "flop") & (df["line"] == "srp") & (df["hero_rel"] == "OOP") & (df["board_family"] == "dry_high")]
    pivot_print(dv_impact, "MTT SRP Flop OOP dry_high — DV impact", "dv_cat")

    # 5. 3BP comparison
    threebp = df[(df["family"] == "cash") & (df["street"] == "flop") & (df["line"] == "srp_3bet") & (df["dv_cat"] == "no_draw") & (df["hero_rel"] == "IP")]
    if len(threebp) > 20:
        pivot_print(threebp, "Cash 3BP Flop IP, no_draw — board_family", "board_family")

    # 6. Spread of bet_freq within high-N cells: how reliable are these medians?
    print(f"\n=== Reliability (MTT SRP Flop OOP no_draw): n + IQR per cell ===")
    rel = mtt_oop_flop.copy()
    band_order = ["air", "weak", "mid", "strong", "nut"]
    for bf, sub in rel.groupby("board_family"):
        for band in band_order:
            cell = sub[sub["mv_band"] == band]["bet_freq"]
            if len(cell) < 30:
                continue
            print(f"  {bf:20s} × {band:6s}  n={len(cell):5d}  median={cell.median()*100:.0f}%  IQR=[{cell.quantile(0.25)*100:.0f}-{cell.quantile(0.75)*100:.0f}]%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
