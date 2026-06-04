#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy", "scikit-learn"]
# ///
"""Identify which trash_hands combos bluff vs check.

Hypothesis: bluffs come from combos with blockers / high A-K-Q kickers / BD draws.
Method:
- Filter trash_hands rows
- Split into bluffers (bet_freq >= 0.50) vs folders (bet_freq < 0.10)
- Compare feature distributions
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    trash = df[df["equity_bucket"] == "trash_hands"].copy()
    print(f"trash_hands total: {len(trash)}")

    # IP attack contexts (where bluffs happen)
    ip_attack = trash[(trash["hero_rel"] == "IP") & (trash["street"].isin(["flop", "turn"]))]
    print(f"trash IP attack flop+turn: {len(ip_attack)}")

    bluff = ip_attack[ip_attack["bet_freq"] >= 0.50]
    fold = ip_attack[ip_attack["bet_freq"] < 0.10]
    mid = ip_attack[(ip_attack["bet_freq"] >= 0.10) & (ip_attack["bet_freq"] < 0.50)]
    print(f"  bluff (≥50% bet): {len(bluff)} ({len(bluff)/len(ip_attack)*100:.1f}%)")
    print(f"  fold (<10% bet):  {len(fold)} ({len(fold)/len(ip_attack)*100:.1f}%)")
    print(f"  mid (10-50%):     {len(mid)} ({len(mid)/len(ip_attack)*100:.1f}%)")

    # Compare features
    print(f"\n=== Feature distribution: bluff vs fold ===")
    for col in ["mv_cat", "dv_cat"]:
        print(f"\n{col}:")
        bv = bluff[col].value_counts(normalize=True) * 100
        fv = fold[col].value_counts(normalize=True) * 100
        all_keys = sorted(set(bv.index) | set(fv.index))
        print(f"  {col:25s}  bluff%   fold%   ratio")
        for k in all_keys:
            b = bv.get(k, 0)
            f = fv.get(k, 0)
            ratio = b / max(f, 0.1)
            if b + f > 2:  # only show significant categories
                print(f"  {k:25s}  {b:5.1f}    {f:5.1f}    {ratio:.2f}x")

    # Hand class (top hands in bluff vs fold)
    print(f"\n=== Top hand169 in bluff (IP flop/turn trash) ===")
    print(bluff["hand169"].value_counts().head(20))
    print(f"\n=== Top hand169 in fold (IP flop/turn trash) ===")
    print(fold["hand169"].value_counts().head(20))

    # Compare by has_A/has_K (blocker proxy)
    print(f"\n=== Blocker hypothesis (high card in hand) ===")
    for cls in ["bluff", "fold"]:
        sub = bluff if cls == "bluff" else fold
        has_a = sub["card_a"].str.startswith("A") | sub["card_b"].str.startswith("A")
        has_k = sub["card_a"].str.startswith("K") | sub["card_b"].str.startswith("K")
        has_q = sub["card_a"].str.startswith("Q") | sub["card_b"].str.startswith("Q")
        print(f"  {cls}: has_A={has_a.mean()*100:.1f}% has_K={has_k.mean()*100:.1f}% has_Q={has_q.mean()*100:.1f}%")

    # Per board family
    print(f"\n=== Bluff frequency by board family (IP trash) ===")
    for bf, sub in ip_attack.groupby("board_family"):
        if len(sub) < 100:
            continue
        bluff_rate = (sub["bet_freq"] >= 0.50).mean() * 100
        mean_bet = sub["bet_freq"].mean() * 100
        print(f"  {bf:18s}  n={len(sub):6d}  bluff%={bluff_rate:.1f}%  mean_bet={mean_bet:.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
