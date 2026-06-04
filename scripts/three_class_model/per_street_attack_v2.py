#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Per-street attack v2: handle missing equity_bucket on river.

For each street, derive the simplest 'default + exceptions' rule using available features.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def find_high_cells(sub: pd.DataFrame, keys: list, n_min=30, iqr_max=0.10) -> pd.DataFrame:
    stats = sub.groupby(keys).agg(
        n=("bet_freq", "count"),
        bet_median=("bet_freq", "median"),
        bet_iqr=("bet_freq", lambda x: x.quantile(0.75) - x.quantile(0.25)),
        bet_mean=("bet_freq", "mean"),
    ).reset_index()
    return stats[(stats["bet_iqr"] < iqr_max) & (stats["n"] >= n_min)]


def analyze(df, street, keys, label):
    print(f"\n{'='*70}\n=== {label} ===\n{'='*70}")
    sub = df[(df["street"] == street) & (df["action_context"] == "attack") &
              (df["ev_bet"].notna()) & (df["ev_check"].notna())].copy()
    for k in keys:
        sub = sub[sub[k].notna() & (sub[k] != "")]
    print(f"Rows: {len(sub)}")
    if len(sub) == 0:
        print("No data")
        return
    sub["best_ev"] = sub[["ev_bet", "ev_check"]].max(axis=1)
    sub["modal"] = (sub["bet_freq"] >= 0.5).map({True: "BET", False: "CHECK"})
    print(f"BET_modal: {(sub['modal']=='BET').mean()*100:.1f}%")
    print(f"always_CHECK loss: {(sub['best_ev']-sub['ev_check']).mean():.4f} BB")
    print(f"always_BET loss:   {(sub['best_ev']-sub['ev_bet']).mean():.4f} BB")

    stats = find_high_cells(sub, keys)
    high_bet = stats[stats["bet_median"] >= 0.75]
    high_check = stats[stats["bet_median"] < 0.25]
    print(f"\nHIGH BET cells: {len(high_bet)}  |  HIGH CHECK cells: {len(high_check)}")
    if len(high_bet) > 0:
        print(f"\n  --- Top BET cells ---")
        for _, r in high_bet.sort_values("n", ascending=False).head(15).iterrows():
            vals = " × ".join(f"{r[k]}" for k in keys)
            print(f"    {vals:60s} bet={r['bet_median']*100:3.0f}% n={int(r['n'])}")
    if len(high_check) > 0 and len(high_check) <= 10:
        print(f"\n  --- HIGH CHECK cells (rare) ---")
        for _, r in high_check.sort_values("n", ascending=False).head(8).iterrows():
            vals = " × ".join(f"{r[k]}" for k in keys)
            print(f"    {vals:60s} check={(1-r['bet_median'])*100:3.0f}% n={int(r['n'])}")

    # default CHECK + HIGH BET override
    high_set = set(tuple(r[k] for k in keys) for _, r in high_bet.iterrows())
    sub["pred"] = sub.apply(lambda r: "BET" if tuple(r[k] for k in keys) in high_set else "CHECK", axis=1)
    sub["loss"] = sub["best_ev"] - sub.apply(lambda r: r["ev_bet"] if r["pred"]=="BET" else r["ev_check"], axis=1)
    print(f"\ndefault CHECK + {len(high_bet)} BET cells: loss={sub['loss'].mean():.4f} BB acc={(sub['pred']==sub['modal']).mean()*100:.1f}%")

    # By board
    print(f"\n--- Per board_family ---")
    for bf, ss in sub.groupby("board_family"):
        if len(ss) < 200: continue
        br = (ss["modal"]=="BET").mean()*100
        print(f"  {bf:18s} n={len(ss):6d} BET_modal={br:5.1f}%")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    # Flop with full features
    analyze(df, "flop", ["equity_bucket", "mv_cat", "board_family", "dv_cat"], "FLOP ATTACK (full features)")
    # Turn with full features
    analyze(df, "turn", ["equity_bucket", "mv_cat", "board_family", "dv_cat"], "TURN ATTACK (full features)")
    # River — fallback to mv+board only
    analyze(df, "river", ["mv_cat", "board_family", "dv_cat"], "RIVER ATTACK (mv+board+dv only — no bucket)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
