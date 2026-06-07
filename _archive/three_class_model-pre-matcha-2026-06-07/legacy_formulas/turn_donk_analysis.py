#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Turn donk lead 解析 — BB が turn で lead する頻度パターン.

Data: turn_cash100_btn_raw, turn_mtt25_btn_raw, turn_mtt50_btn_raw, turn_mtt100_btn_raw
全て active=BB / hero=BB / OOP / Turn / attack
→ BB の Turn donk decision (X か R<size>)
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def get_scenario(p):
    if 'turn_cash100_btn' in p: return 'Cash 100bb'
    if 'turn_mtt25_btn' in p: return 'MTT 25bb'
    if 'turn_mtt50_btn' in p: return 'MTT 50bb'
    if 'turn_mtt100_btn' in p: return 'MTT 100bb'
    return 'other'


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "turn") & (df["action_context"] == "attack") &
              df["source_path"].str.contains("turn_(cash100|mtt25|mtt50|mtt100)_btn_raw")].copy()
    sub["scenario"] = sub["source_path"].apply(get_scenario)
    sub["bet_freq"] = sub["bet_freq"].fillna(0)
    sub["check_freq"] = sub["check_freq"].fillna(0)

    print(f"=== Turn Donk Lead data inventory ===")
    print(f"Total rows: {len(sub)}")
    print()
    for sc, ss in sub.groupby("scenario"):
        print(f"  {sc}: {len(ss):>6} rows  (mean bet_freq: {ss['bet_freq'].mean()*100:.1f}%)")
    print()

    # Per scenario: overall donk frequency
    print("=== Overall donk frequency per scenario ===")
    for sc, ss in sub.groupby("scenario"):
        total = ss["bet_freq"].mean() * 100
        print(f"  {sc}: BB donks {total:.1f}% of all turn spots")
    print()

    # Per (scenario × board_family) donk freq
    print("=== Donk frequency per (scenario × board_family) ===")
    for sc, ss in sub.groupby("scenario"):
        print(f"\n  --- {sc} ---")
        for bf, ss2 in ss.groupby("board_family"):
            if len(ss2) < 100: continue
            avg_donk = ss2["bet_freq"].mean() * 100
            print(f"    {bf:20s}: donk_freq={avg_donk:5.1f}% (n={len(ss2)})")

    # Per (scenario × mv_cat) donk freq
    print("\n=== Donk frequency per mv_cat (Cash 100bb only) ===")
    cash = sub[sub["scenario"] == "Cash 100bb"]
    for mv, ss in cash.groupby("mv_cat"):
        if len(ss) < 50: continue
        avg = ss["bet_freq"].mean() * 100
        bet_only_freq = (ss["bet_freq"] >= 0.5).mean() * 100
        print(f"  {mv:20s}: avg_freq={avg:5.1f}%, BET-modal {bet_only_freq:5.1f}% (n={len(ss)})")

    print("\n=== Donk frequency per mv_cat (MTT 50bb only) ===")
    mtt = sub[sub["scenario"] == "MTT 50bb"]
    for mv, ss in mtt.groupby("mv_cat"):
        if len(ss) < 50: continue
        avg = ss["bet_freq"].mean() * 100
        bet_only_freq = (ss["bet_freq"] >= 0.5).mean() * 100
        print(f"  {mv:20s}: avg_freq={avg:5.1f}%, BET-modal {bet_only_freq:5.1f}% (n={len(ss)})")

    # Top donk spots per scenario (mv × board)
    print("\n=== Top 10 BB donk-modal cells (MTT 50bb) ===")
    mtt_cells = mtt.groupby(["mv_cat", "dv_cat", "board_family"]).agg(
        n=("bet_freq", "count"),
        avg_donk=("bet_freq", "mean"),
    ).reset_index()
    mtt_cells = mtt_cells[mtt_cells["n"] >= 30].sort_values("avg_donk", ascending=False)
    for _, r in mtt_cells.head(10).iterrows():
        print(f"  mv={r['mv_cat']:14s} × dv={r['dv_cat']:15s} × bf={r['board_family']:18s}: donk_freq={r['avg_donk']*100:5.1f}% (n={int(r['n']):4d})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
