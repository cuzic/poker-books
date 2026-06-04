#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Investigate the U-shape: are low-eq bets real, and if so, what combos?

Hypothesis: the U-shape isn't "all low-eq combos bet". It's "bluff-selected combos in
the low-eq tail bet at high freq, while most low-eq combos check".
Mean is dragged up by the bluff candidates.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")


def main() -> int:
    df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "dataset_unified.csv", low_memory=False)
    df = df[(df["action_context"] == "attack") & (df["eq_percentile"].notna()) & (df["hand_eq"].notna())].copy()
    print(f"Attack rows with eq: {len(df)}")

    # ── Q1: is the U-shape in eq_percentile or in hand_eq (raw equity)? ──
    print(f"\n=== Q1: U-shape — eq_percentile vs hand_eq (raw equity) ===")
    df["eqp_bin"] = pd.cut(df["eq_percentile"], bins=[0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.001],
                            labels=[f"{i*10}-{(i+1)*10}" for i in range(10)])
    df["he_bin"] = pd.cut(df["hand_eq"], bins=[0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.001],
                           labels=[f"{i*10}-{(i+1)*10}" for i in range(10)])
    print(f"  bin       eq_percentile_mean_bet   hand_eq_mean_bet")
    for i in range(10):
        lab = f"{i*10}-{(i+1)*10}"
        ep_sub = df[df["eqp_bin"] == lab]
        he_sub = df[df["he_bin"] == lab]
        if len(ep_sub) < 100 or len(he_sub) < 100:
            continue
        print(f"  {lab:8s}   {ep_sub['bet_freq'].mean()*100:7.1f}%   ({len(ep_sub):6d})    {he_sub['bet_freq'].mean()*100:7.1f}%   ({len(he_sub):6d})")

    # ── Q2: distribution of bet_freq WITHIN low-eq bin ──
    print(f"\n=== Q2: bet_freq distribution within eq_percentile 0-10% ===")
    low = df[df["eqp_bin"] == "0-10"]
    print(f"n={len(low)}")
    print(f"bet_freq quantiles:")
    for q in [0.1, 0.25, 0.5, 0.75, 0.9, 0.95]:
        print(f"  q{int(q*100)} = {low['bet_freq'].quantile(q)*100:.1f}%")
    # share at extremes
    print(f"\n  bet_freq < 5%:  {(low['bet_freq']<0.05).sum()} ({(low['bet_freq']<0.05).mean()*100:.1f}%)")
    print(f"  bet_freq 5-25%: {((low['bet_freq']>=0.05)&(low['bet_freq']<0.25)).sum()} ({((low['bet_freq']>=0.05)&(low['bet_freq']<0.25)).mean()*100:.1f}%)")
    print(f"  bet_freq 25-75%: {((low['bet_freq']>=0.25)&(low['bet_freq']<0.75)).sum()} ({((low['bet_freq']>=0.25)&(low['bet_freq']<0.75)).mean()*100:.1f}%)")
    print(f"  bet_freq >= 75%: {(low['bet_freq']>=0.75).sum()} ({(low['bet_freq']>=0.75).mean()*100:.1f}%)")

    # ── Q3: what kind of combos are the bluff bettors (bet > 75% with eq < 0.1)? ──
    print(f"\n=== Q3: top hand169 in low-eq high-bet (eq<10% AND bet_freq>=75%) ===")
    bluffers = low[low["bet_freq"] >= 0.75]
    print(f"n={len(bluffers)}")
    print(f"top 20 hand169:")
    print(bluffers["hand169"].value_counts().head(20))
    print(f"\nMV/DV distribution:")
    print(bluffers["mv_cat"].value_counts().head(10))
    print(bluffers["dv_cat"].value_counts().head(10))

    # ── Q4: what kind of combos are the pure CHECK (bet<5% with eq<0.1)? ──
    print(f"\n=== Q4: top hand169 in low-eq low-bet (eq<10% AND bet_freq<5%) ===")
    folders = low[low["bet_freq"] < 0.05]
    print(f"n={len(folders)}")
    print(f"top 20 hand169:")
    print(folders["hand169"].value_counts().head(20))
    print(f"\nMV/DV distribution:")
    print(folders["mv_cat"].value_counts().head(10))
    print(folders["dv_cat"].value_counts().head(10))

    # ── Q5: in low-eq bluffers, blocker presence ──
    print(f"\n=== Q5: A/K/blocker rate in bluffers vs folders (eq<10%) ===")
    def has_high(row, rank):
        return rank in str(row.get("card_a", ""))[0] + str(row.get("card_b", ""))[0]
    for label, subset in [("bluffers", bluffers), ("folders", folders)]:
        if len(subset) == 0:
            continue
        a = subset.apply(lambda r: has_high(r, "A"), axis=1).mean() * 100
        k = subset.apply(lambda r: has_high(r, "K"), axis=1).mean() * 100
        q = subset.apply(lambda r: has_high(r, "Q"), axis=1).mean() * 100
        is_pair = subset.apply(lambda r: str(r.get("card_a",""))[0] == str(r.get("card_b",""))[0], axis=1).mean() * 100
        is_suited = subset.apply(lambda r: len(str(r.get("card_a",""))) >= 2 and len(str(r.get("card_b",""))) >= 2 and str(r.get("card_a",""))[1] == str(r.get("card_b",""))[1], axis=1).mean() * 100
        print(f"  {label:9s}  has_A={a:.0f}% has_K={k:.0f}% has_Q={q:.0f}% pair={is_pair:.0f}% suited={is_suited:.0f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
