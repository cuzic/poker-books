#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Analyze trash bluff selection by blocker presence.

For each trash combo in attack contexts:
  - has_A_blocker: hand contains an A
  - has_K_blocker: hand contains a K
  - has_top_blocker: hand contains a card matching board top
  - has_pair_blocker (on paired boards): hand contains the paired rank

Compare bluff rate (bet_freq >= 0.50) between:
  - blocker vs no_blocker subsets
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"

RANKS = "23456789TJQKA"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)

    trash_attack = df[
        (df["equity_bucket"] == "trash_hands") &
        (df["hero_rel"] == "IP") &
        (df["street"].isin(["flop", "turn"]))
    ].copy()

    # Build blocker features
    def has_rank(row, target_rank):
        return target_rank in (row["card_a"][0] + row["card_b"][0])

    def top_rank(row):
        b = str(row.get("board_flop", ""))
        if len(b) < 6:
            return ""
        return max(b[0], b[2], b[4], key=lambda c: RANKS.index(c) if c in RANKS else -1)

    trash_attack["has_A"] = trash_attack.apply(lambda r: has_rank(r, "A"), axis=1)
    trash_attack["has_K"] = trash_attack.apply(lambda r: has_rank(r, "K"), axis=1)
    trash_attack["has_Q"] = trash_attack.apply(lambda r: has_rank(r, "Q"), axis=1)
    trash_attack["has_J"] = trash_attack.apply(lambda r: has_rank(r, "J"), axis=1)
    trash_attack["board_top"] = trash_attack.apply(top_rank, axis=1)
    trash_attack["has_top_blocker"] = trash_attack.apply(
        lambda r: r["board_top"] in (r["card_a"][0] + r["card_b"][0]), axis=1
    )
    trash_attack["bluff"] = (trash_attack["bet_freq"] >= 0.50).astype(int)

    print(f"Trash (IP, flop+turn) n={len(trash_attack)}")
    print(f"Overall bluff rate: {trash_attack['bluff'].mean()*100:.1f}%")
    print()

    # ── Overall blocker effect ──
    print(f"=== Blocker effect (averaged across all DVs and boards) ===")
    for col, label in [
        ("has_A", "A blocker"),
        ("has_K", "K blocker"),
        ("has_Q", "Q blocker"),
        ("has_J", "J blocker"),
        ("has_top_blocker", "top blocker"),
    ]:
        with_b = trash_attack[trash_attack[col]]["bluff"].mean() * 100
        without_b = trash_attack[~trash_attack[col]]["bluff"].mean() * 100
        n_with = trash_attack[col].sum()
        n_without = (~trash_attack[col]).sum()
        diff = with_b - without_b
        print(f"  {label:15s}  with: {with_b:5.1f}% (n={n_with:6.0f})  without: {without_b:5.1f}% (n={n_without:6.0f})  diff={diff:+.1f}pp")

    # ── Stratified by DV ──
    print(f"\n=== A-blocker effect, stratified by DV ===")
    for dv, sub in trash_attack.groupby("dv_cat"):
        if len(sub) < 200:
            continue
        with_a = sub[sub["has_A"]]["bluff"].mean() * 100
        without_a = sub[~sub["has_A"]]["bluff"].mean() * 100
        n_with = sub["has_A"].sum()
        print(f"  dv={dv:18s}  with_A={with_a:5.1f}% (n={n_with:5.0f})  without_A={without_a:5.1f}%  diff={with_a-without_a:+.1f}pp")

    # ── Stratified by board_family ──
    print(f"\n=== A-blocker effect, stratified by board_family ===")
    for bf, sub in trash_attack.groupby("board_family"):
        if len(sub) < 200:
            continue
        with_a = sub[sub["has_A"]]["bluff"].mean() * 100
        without_a = sub[~sub["has_A"]]["bluff"].mean() * 100
        n_with = sub["has_A"].sum()
        print(f"  board={bf:18s}  with_A={with_a:5.1f}% (n={n_with:5.0f})  without_A={without_a:5.1f}%  diff={with_a-without_a:+.1f}pp")

    # ── Combined: A blocker × DV BDFD ==
    print(f"\n=== Combined: A blocker AND draw (best bluffer profile) ===")
    sub = trash_attack[(trash_attack["has_A"]) & (trash_attack["dv_cat"].isin({"twocards_bdfd", "onecard_bdfd", "gutshot"}))]
    no_sub = trash_attack[(~trash_attack["has_A"]) & (trash_attack["dv_cat"].isin({"twocards_bdfd", "onecard_bdfd", "gutshot"}))]
    print(f"  A blocker × DV(BDFD/gut)    n={len(sub)}  bluff={sub['bluff'].mean()*100:.1f}%")
    print(f"  no A     × DV(BDFD/gut)    n={len(no_sub)}  bluff={no_sub['bluff'].mean()*100:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
