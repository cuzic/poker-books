#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Analyze attack-side: eq_percentile × offered bet_size → bet_freq.

Hypothesis: U-shape weakens or changes when conditioned on offered size.
Small size → bluff bet more (low eq), big size → polarize harder.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")


def size_bucket(s):
    if pd.isna(s):
        return "unknown"
    if s < 0.45:
        return "small"
    if s < 0.85:
        return "mid"
    return "big"


def main() -> int:
    main_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "dataset_unified.csv", low_memory=False)
    bet_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "attack_bet_size.csv")
    bet_df = bet_df[["spot_id", "primary_size_pot", "largest_size_pot", "n_sizes"]].drop_duplicates(subset=["spot_id"])
    df = main_df.merge(bet_df, on="spot_id", how="left")

    df = df[(df["action_context"] == "attack") &
            (df["eq_percentile"].notna()) &
            (df["primary_size_pot"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    df["size_bucket"] = df["primary_size_pot"].apply(size_bucket)
    print(f"Attack rows with eq + size: {len(df)} / spots: {df['spot_id'].nunique()}")

    df["eq_bin"] = pd.cut(df["eq_percentile"], bins=[0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.001],
                           labels=[f"{i*10}-{(i+1)*10}" for i in range(10)])

    print(f"\nSize bucket distribution:")
    print(df["size_bucket"].value_counts())
    print(f"\nbet_size_pot distribution:")
    print(df["primary_size_pot"].describe())

    # ── eq × bet_size → bet_freq mean ──
    print(f"\n=== eq_bin × size_bucket → bet_freq (mean / median) ===")
    print(f"  eq_bin   size   mean_bet   median_bet   n")
    for eb in df["eq_bin"].dropna().unique():
        for sz in ["small", "mid", "big"]:
            sub = df[(df["eq_bin"] == eb) & (df["size_bucket"] == sz)]
            if len(sub) < 100:
                continue
            print(f"  {str(eb):8s} {sz:5s}   {sub['bet_freq'].mean()*100:5.1f}%      {sub['bet_freq'].median()*100:5.1f}%   {len(sub):6d}")

    # ── How does action_modal (3-band) change with size? ──
    def freq_to_3band(f):
        if f < 0.25: return "CHECK"
        if f < 0.75: return "MIX"
        return "BET"

    df["actual_3"] = df["bet_freq"].apply(freq_to_3band)
    print(f"\n=== eq_bin × size_bucket → 3-band distribution ===")
    for eb in df["eq_bin"].dropna().unique():
        for sz in ["small", "mid", "big"]:
            sub = df[(df["eq_bin"] == eb) & (df["size_bucket"] == sz)]
            if len(sub) < 100:
                continue
            dist = sub["actual_3"].value_counts(normalize=True).to_dict()
            dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
            print(f"  {str(eb):8s} {sz:5s}  n={len(sub):6d}  {dist_str}")

    # ── Plot the U-shape per size ──
    print(f"\n=== U-shape per size (mean bet_freq by eq_bin) ===")
    print(f"  eq_bin     small_mean  mid_mean  big_mean")
    for eb in sorted(df["eq_bin"].dropna().unique()):
        s_mean = df[(df["eq_bin"] == eb) & (df["size_bucket"] == "small")]["bet_freq"].mean()
        m_mean = df[(df["eq_bin"] == eb) & (df["size_bucket"] == "mid")]["bet_freq"].mean()
        b_mean = df[(df["eq_bin"] == eb) & (df["size_bucket"] == "big")]["bet_freq"].mean()
        print(f"  {str(eb):8s}  {s_mean*100 if not pd.isna(s_mean) else 0:7.1f}%   {m_mean*100 if not pd.isna(m_mean) else 0:5.1f}%   {b_mean*100 if not pd.isna(b_mean) else 0:5.1f}%")

    # ── Per board × size analysis for polarization ──
    print(f"\n=== eq × board × size → bet_freq (Cash IP only for cleanness, n>=200) ===")
    cash_ip = df[(df["family"] == "mtt") & (df["hero_rel"] == "IP")]
    print(f"  IP attack data: {len(cash_ip)} rows")
    for bf in ["dry_high", "dynamic", "paired", "monotone", "dynamic_2tone", "low_dry"]:
        sub_bf = cash_ip[cash_ip["board_family"] == bf]
        if len(sub_bf) < 200:
            continue
        print(f"\n  --- board={bf} ---")
        for eb in ["0-10","30-40","60-70","80-90"]:
            for sz in ["small", "mid", "big"]:
                cell = sub_bf[(sub_bf["eq_bin"] == eb) & (sub_bf["size_bucket"] == sz)]
                if len(cell) < 30:
                    continue
                print(f"    eq={eb:5s} size={sz:5s} mean_bet={cell['bet_freq'].mean()*100:5.1f}% n={len(cell):5d}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
