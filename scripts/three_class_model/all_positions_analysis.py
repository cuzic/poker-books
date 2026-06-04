#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""全ポジション × 全 depth の体系的分析:
1. River lead (donk) パターン (BB 主体)
2. Flop CBet (attack) — BTN/CO/HJ/LJ/SB 全ポジション × MTT 50/100/200bb
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    # ── 1. River lead (donk) check ──
    print("=" * 70)
    print("=== 1. River lead (donk) inventory ===")
    print("=" * 70)
    riv = df[(df["street"] == "river") & (df["action_context"] == "attack")].copy()
    riv["bet_freq"] = riv["bet_freq"].fillna(0)
    print(f"All river attack rows: {len(riv)}")
    print(f"By hero position:")
    for hp, ss in riv.groupby("hero_pos"):
        avg_bet = ss["bet_freq"].mean() * 100
        print(f"  {hp}: n={len(ss):>6}  mean bet_freq={avg_bet:5.1f}%")

    bb_riv = riv[riv["hero_pos"] == "BB"]
    if len(bb_riv) > 0:
        print(f"\nBB river attack (potential donk): {len(bb_riv)} rows")
        print(f"Source paths:")
        for sp in bb_riv["source_path"].value_counts().head(5).index:
            ss = bb_riv[bb_riv["source_path"] == sp]
            print(f"  {sp[:60]}: n={len(ss)}, mean bet_freq={ss['bet_freq'].mean()*100:.1f}%")

    # ── 2. Flop CBet across positions (MTT 50/100/200bb) ──
    print("\n" + "=" * 70)
    print("=== 2. Flop CBet (attack) by position × MTT depth ===")
    print("=" * 70)
    def get_mtt_depth(p):
        if 'mtt50bb_raw' in p and 'def_' not in p: return 'MTT 50bb'
        if 'mtt100bb_raw' in p and 'def_' not in p: return 'MTT 100bb'
        if 'mtt200bb_raw' in p and 'def_' not in p: return 'MTT 200bb'
        return None
    flop_atk = df[(df["street"] == "flop") & (df["action_context"] == "attack")].copy()
    flop_atk["scenario"] = flop_atk["source_path"].apply(get_mtt_depth)
    mtt_flop = flop_atk[flop_atk["scenario"].notna()].copy()
    mtt_flop["bet_freq"] = mtt_flop["bet_freq"].fillna(0)

    print(f"\nMean cbet frequency per (scenario × position):")
    for (sc, pos), ss in mtt_flop.groupby(["scenario", "hero_pos"]):
        avg = ss["bet_freq"].mean() * 100
        print(f"  {sc} × {pos}: n={len(ss):>5}  mean bet_freq={avg:5.1f}%")

    # ── 3. Position-specific cbet patterns by mv ──
    print("\n=== Cbet frequency per mv_cat × position (MTT 50bb) ===")
    mtt50 = mtt_flop[mtt_flop["scenario"] == "MTT 50bb"]
    print(f"\nmv_cat        BTN  CO   HJ   LJ   SB")
    for mv, ss_all in mtt50.groupby("mv_cat"):
        if len(ss_all) < 200: continue
        row = f"{mv:14s}"
        for pos in ["BTN", "CO", "HJ", "LJ", "SB"]:
            ss = ss_all[ss_all["hero_pos"] == pos]
            avg = ss["bet_freq"].mean() * 100 if len(ss) > 0 else 0
            row += f"  {avg:4.1f}%"
        print(f"  {row}")

    # ── 4. Cbet by board_family × position ──
    print("\n=== Cbet by board_family × position (MTT 50bb) ===")
    print(f"\nboard_family        BTN   CO    HJ    LJ    SB")
    for bf, ss_all in mtt50.groupby("board_family"):
        if len(ss_all) < 200: continue
        row = f"{bf:18s}"
        for pos in ["BTN", "CO", "HJ", "LJ", "SB"]:
            ss = ss_all[ss_all["hero_pos"] == pos]
            avg = ss["bet_freq"].mean() * 100 if len(ss) > 0 else 0
            row += f"  {avg:5.1f}%"
        print(f"  {row}")

    # ── 5. BB defense across MTT depths (25/50/100bb) ──
    print("\n=== BB Flop defense across MTT depths ===")
    bb_def = df[(df["street"] == "flop") & (df["action_context"] == "defense") &
                 df["source_path"].str.contains("def_mtt(25|50|100)_bb_raw", regex=True)].copy()
    bb_def["depth"] = bb_def["source_path"].apply(
        lambda p: "25bb" if "mtt25" in p else "50bb" if "mtt50" in p else "100bb"
    )
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        bb_def[c] = bb_def[c].fillna(0)

    print("\nFold/Call/Raise by depth (overall):")
    for d, ss in bb_def.groupby("depth"):
        f = ss["fold_freq"].mean() * 100
        c = ss["call_freq"].mean() * 100
        r = ss["raise_freq"].mean() * 100
        print(f"  {d}: F={f:5.1f}% C={c:5.1f}% R={r:5.1f}%  (n={len(ss)})")

    print("\nFold rate by mv_cat × depth (BB defense):")
    print(f"\nmv_cat        25bb    50bb    100bb")
    for mv, ss_all in bb_def.groupby("mv_cat"):
        if len(ss_all) < 200: continue
        row = f"{mv:14s}"
        for d in ["25bb", "50bb", "100bb"]:
            ss = ss_all[ss_all["depth"] == d]
            avg = ss["fold_freq"].mean() * 100 if len(ss) > 0 else 0
            row += f"  {avg:5.1f}%"
        print(f"  {row}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
