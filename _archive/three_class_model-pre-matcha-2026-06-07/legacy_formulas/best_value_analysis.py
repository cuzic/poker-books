#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Analyze best_hands bucket: what distinguishes value-bettors from slowplayers."""
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
    best = df[df["equity_bucket"] == "best_hands"].copy()
    print(f"best_hands total: {len(best)}")

    ip_attack = best[(best["hero_rel"] == "IP") & (best["street"].isin(["flop", "turn"]))]
    print(f"best IP attack flop+turn: {len(ip_attack)}")

    valuebet = ip_attack[ip_attack["bet_freq"] >= 0.75]
    slowplay = ip_attack[ip_attack["bet_freq"] < 0.25]
    mixed = ip_attack[(ip_attack["bet_freq"] >= 0.25) & (ip_attack["bet_freq"] < 0.75)]
    print(f"  value (>=75% bet): {len(valuebet)} ({len(valuebet)/len(ip_attack)*100:.1f}%)")
    print(f"  slowplay (<25%):   {len(slowplay)} ({len(slowplay)/len(ip_attack)*100:.1f}%)")
    print(f"  mixed (25-75%):    {len(mixed)} ({len(mixed)/len(ip_attack)*100:.1f}%)")

    print(f"\n=== MV in value vs slowplay ===")
    for col in ["mv_cat"]:
        bv = valuebet[col].value_counts(normalize=True) * 100
        sv = slowplay[col].value_counts(normalize=True) * 100
        keys = sorted(set(bv.index) | set(sv.index))
        print(f"  {col:25s}  value%  slow%   ratio")
        for k in keys:
            v = bv.get(k, 0)
            s = sv.get(k, 0)
            ratio = v / max(s, 0.1)
            if v + s > 2:
                print(f"  {k:25s}  {v:5.1f}   {s:5.1f}   {ratio:.2f}x")

    print(f"\n=== DV in value vs slowplay ===")
    for col in ["dv_cat"]:
        bv = valuebet[col].value_counts(normalize=True) * 100
        sv = slowplay[col].value_counts(normalize=True) * 100
        keys = sorted(set(bv.index) | set(sv.index))
        print(f"  {col:25s}  value%  slow%   ratio")
        for k in keys:
            v = bv.get(k, 0)
            s = sv.get(k, 0)
            ratio = v / max(s, 0.1)
            if v + s > 2:
                print(f"  {k:25s}  {v:5.1f}   {s:5.1f}   {ratio:.2f}x")

    print(f"\n=== Top hand169 in valuebet ===")
    print(valuebet["hand169"].value_counts().head(15))
    print(f"\n=== Top hand169 in slowplay ===")
    print(slowplay["hand169"].value_counts().head(15))

    print(f"\n=== Slowplay rate by board family (best IP) ===")
    for bf, sub in ip_attack.groupby("board_family"):
        if len(sub) < 100:
            continue
        sp_rate = (sub["bet_freq"] < 0.25).mean() * 100
        vb_rate = (sub["bet_freq"] >= 0.75).mean() * 100
        print(f"  {bf:18s}  n={len(sub):5d}  value={vb_rate:.1f}%  slow={sp_rate:.1f}%")

    # Also: good_hands bucket pattern (the "checked-most" middle)
    print(f"\n=== good_hands IP attack flop+turn breakdown ===")
    good = df[(df["equity_bucket"] == "good_hands") & (df["hero_rel"] == "IP") & (df["street"].isin(["flop","turn"]))]
    g_value = good[good["bet_freq"] >= 0.75]
    g_check = good[good["bet_freq"] < 0.25]
    g_mid = good[(good["bet_freq"] >= 0.25) & (good["bet_freq"] < 0.75)]
    print(f"  total: {len(good)}")
    print(f"  value(>=75%): {len(g_value)} ({len(g_value)/len(good)*100:.1f}%)")
    print(f"  check(<25%):  {len(g_check)} ({len(g_check)/len(good)*100:.1f}%)")
    print(f"  mid:          {len(g_mid)} ({len(g_mid)/len(good)*100:.1f}%)")
    if len(g_value) > 100:
        print(f"  top mv in good_hands valuebet:")
        print("    ", g_value["mv_cat"].value_counts().head(5).to_dict())
    if len(g_check) > 100:
        print(f"  top mv in good_hands check:")
        print("    ", g_check["mv_cat"].value_counts().head(5).to_dict())

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
