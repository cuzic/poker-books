#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""huge_gap_breakdown.py — huge_gap (ev_gap > 0.5 BB) の発生条件を集計。

街 × action_context × mv_cat × dv_cat × board_family × bet_size × bucket で
huge_gap がどこに集中しているかを可視化する。
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA = Path("/home/cuzic/poker-books/scripts/three_class_model/dataset_unified.csv")
HUGE = 0.5


def ev_gap_row(r):
    if r["action_context"] == "defense":
        evs = [r["ev_fold"], r["ev_call"], r["ev_raise"]]
    else:
        evs = [r["ev_bet"], r["ev_check"]]
    evs = [e for e in evs if pd.notna(e)]
    if len(evs) < 2:
        return None
    s = sorted(evs, reverse=True)
    return s[0] - s[1]


def turn_bet_size(s):
    if "_R4" in s or "_R5" in s or "_R6" in s: return "small_33"
    if "_R7" in s or "_R8" in s or "_R9" in s: return "med_67"
    if "_R13" in s or "_R14" in s: return "big_100"
    if "_R16" in s or "_R17" in s or "_R19" in s: return "overbet_185"
    return "other"


def river_bet_size(s):
    if "_R4" in s: return "small_30"
    if "_R7" in s or "_R8" in s: return "med_75"
    if "_R13" in s: return "med_100"
    if "_R16" in s: return "overbet"
    if "_R89" in s or "_R35" in s: return "allin"
    return "other"


def main():
    df = pd.read_csv(DATA, low_memory=False)
    df["ev_gap"] = df.apply(ev_gap_row, axis=1)
    df = df[df["ev_gap"].notna()].copy()

    print(f"全 rows: {len(df):,}")
    print(f"huge_gap (>={HUGE} BB): {(df['ev_gap'] >= HUGE).sum():,} ({(df['ev_gap'] >= HUGE).mean()*100:.1f}%)\n")

    df["bet_size"] = df.apply(
        lambda r: turn_bet_size(r["source_path"]) if r["street"] == "turn"
        else river_bet_size(r["source_path"]) if r["street"] == "river"
        else "—", axis=1)

    for street in ["flop", "turn", "river"]:
        for ctx in ["attack", "defense"]:
            sub = df[(df["street"] == street) & (df["action_context"] == ctx)]
            if len(sub) == 0: continue
            huge = sub[sub["ev_gap"] >= HUGE]
            print(f"\n{'='*60}")
            print(f"  {street.upper()} / {ctx}   全 {len(sub):,}  huge {len(huge):,} ({len(huge)/len(sub)*100:.1f}%)  mean_gap={sub['ev_gap'].mean():.3f} BB")
            print('='*60)

            if len(huge) == 0: continue

            # 1) mv_cat 別
            print("\n  ▼ mv_cat 別の huge 件数 (上位 10)")
            for mv, n in huge["mv_cat"].value_counts().head(10).items():
                m = huge[huge["mv_cat"] == mv]["ev_gap"].mean()
                print(f"    {mv:20s} n={n:>5,}  mean_gap={m:.3f} BB")

            # 2) bet_size 別 (defense のみ)
            if ctx == "defense" and street in {"turn", "river"}:
                print("\n  ▼ bet_size 別の huge 件数")
                for bs, n in huge["bet_size"].value_counts().items():
                    m = huge[huge["bet_size"] == bs]["ev_gap"].mean()
                    print(f"    {bs:20s} n={n:>5,}  mean_gap={m:.3f} BB")

            # 3) bucket 別 (利用可能なら)
            if "equity_bucket" in huge.columns and huge["equity_bucket"].notna().any():
                print("\n  ▼ equity_bucket 別")
                for b, n in huge["equity_bucket"].value_counts().items():
                    m = huge[huge["equity_bucket"] == b]["ev_gap"].mean()
                    print(f"    {b:20s} n={n:>5,}  mean_gap={m:.3f} BB")

            # 4) 最大級の huge_gap top 5 (具体的な「困る」状況)
            print("\n  ▼ huge_gap 上位 5 (mv × dv × board × bet_size × bucket)")
            top = huge.nlargest(5, "ev_gap")[
                ["mv_cat","dv_cat","board_family","bet_size","equity_bucket","ev_gap","fold_freq","call_freq","raise_freq","bet_freq","check_freq"]
            ] if "equity_bucket" in huge.columns else huge.nlargest(5, "ev_gap")[
                ["mv_cat","dv_cat","board_family","bet_size","ev_gap"]
            ]
            print(top.to_string(index=False))

            # 5) 組合せ集計 (mv × board)
            print("\n  ▼ huge 集中: mv_cat × board_family (上位 8 組)")
            pivot = huge.groupby(["mv_cat", "board_family"]).size().sort_values(ascending=False).head(8)
            for (mv, bf), n in pivot.items():
                gap_mean = huge[(huge["mv_cat"]==mv) & (huge["board_family"]==bf)]["ev_gap"].mean()
                print(f"    {mv:18s} × {bf:18s} n={n:>5,}  mean_gap={gap_mean:.3f} BB")


if __name__ == "__main__":
    main()
