#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ELYUL = ["Apache-2.0"]
# ///
"""Classify each attack spot as 'linear' or 'polarized'.

Empirical polarization measure:
  For each spot, compute the bet_freq distribution.
  Polarized = spot where the bottom-eq combos bet a LOT (because they're bluffs)
              AND middle-eq combos check.
  Linear = monotonic relationship between eq and bet_freq.

We measure polarization as:
  polarization_score = bet_freq(low_eq_quartile) - bet_freq(mid_eq_quartile)

  High positive → polarized (low bets more than middle, U-shape)
  Near zero or negative → linear (monotonic)

Then group spots by polarization, verify prediction accuracy on each group.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"
BET_ATK = ROOT / "scripts" / "three_class_model" / "attack_bet_size.csv"


def main() -> int:
    main_df = pd.read_csv(DATA, low_memory=False)
    bet_df = pd.read_csv(BET_ATK)[["spot_id", "primary_size_pot"]].drop_duplicates(subset=["spot_id"])
    df = main_df.merge(bet_df, on="spot_id", how="left")
    df = df[(df["action_context"] == "attack") &
            (df["eq_percentile"].notna()) &
            (df["primary_size_pot"].notna())].copy()
    print(f"Attack rows: {len(df)}")
    print(f"Spots: {df['spot_id'].nunique()}")

    # ── Compute polarization score per spot ──
    print(f"\nComputing per-spot polarization scores...")
    rows = []
    for sid, sub in df.groupby("spot_id"):
        # split combos in spot by eq_percentile quartile
        if len(sub) < 50:
            continue
        sub = sub.copy()
        sub["eq_q"] = pd.qcut(sub["eq_percentile"], q=4, labels=False, duplicates="drop")
        if sub["eq_q"].nunique() < 4:
            continue
        # mean bet_freq per quartile
        means = sub.groupby("eq_q")["bet_freq"].mean()
        low_bet = means.get(0, 0)
        mid_bet = means.get(1, 0) + means.get(2, 0)
        mid_bet = mid_bet / 2
        high_bet = means.get(3, 0)
        polar_score = low_bet - mid_bet  # positive = polarized
        linear_score = high_bet - low_bet  # positive = linear monotonic
        # spot context
        rows.append({
            "spot_id": sid,
            "n": len(sub),
            "primary_size_pot": sub["primary_size_pot"].iloc[0],
            "board_family": sub["board_family"].iloc[0],
            "street": sub["street"].iloc[0],
            "family": sub["family"].iloc[0],
            "low_bet_freq": low_bet,
            "mid_bet_freq": mid_bet,
            "high_bet_freq": high_bet,
            "polar_score": polar_score,
            "linear_score": linear_score,
        })
    spot_meta = pd.DataFrame(rows)
    print(f"Spots with full quartile data: {len(spot_meta)}")

    # ── Classify ──
    # Polarization >= 0.10 (low bets 10pp+ more than middle) → polarized
    spot_meta["spot_type"] = spot_meta.apply(
        lambda r: "polarized" if r["polar_score"] >= 0.10 else "linear", axis=1
    )
    print(f"\nSpot classification:")
    print(spot_meta["spot_type"].value_counts())

    # ── Per (bet_size × board × street) — which combinations polarize? ──
    print(f"\n=== Polarization rate by (size × board × street) ===")
    spot_meta["size_bucket"] = spot_meta["primary_size_pot"].apply(
        lambda s: "small (≤45%)" if s < 0.45 else ("mid" if s < 0.85 else "big (≥85%)")
    )
    for (sb, bf, st), sub in spot_meta.groupby(["size_bucket", "board_family", "street"]):
        if len(sub) < 5:
            continue
        rate = (sub["spot_type"] == "polarized").mean() * 100
        avg_polar = sub["polar_score"].mean()
        print(f"  {sb:12s} × {bf:18s} × {st:6s}  n_spots={len(sub):3d}  polar_rate={rate:5.1f}%  avg_polar_score={avg_polar:+.3f}")

    # ── Merge back into row-level data ──
    df = df.merge(spot_meta[["spot_id", "spot_type", "polar_score"]], on="spot_id", how="left")
    df = df[df["spot_type"].notna()].copy()
    print(f"\nRows after merge: {len(df)}")

    # ── Build 3-band ground truth ──
    def freq_to_3band(f):
        if f < 0.25: return "LOW"
        if f < 0.75: return "MIX"
        return "HIGH"
    df["actual_3"] = df["bet_freq"].apply(freq_to_3band)

    # ── For LINEAR spots, simple eq → band mapping ──
    def linear_pred(eq):
        if eq < 0.30: return "LOW"
        if eq < 0.70: return "MIX"
        return "HIGH"

    # ── For POLARIZED spots, predict CHECK heavy except extremes ──
    def polarized_pred(eq):
        if eq < 0.15: return "MIX"  # bluff candidate band
        if eq < 0.80: return "LOW"  # CHECK
        return "MIX"  # value/slowplay

    df["pred"] = df.apply(
        lambda r: linear_pred(r["eq_percentile"]) if r["spot_type"] == "linear" else polarized_pred(r["eq_percentile"]),
        axis=1,
    )
    df["correct"] = df["pred"] == df["actual_3"]

    print(f"\n=== Spot-type-aware prediction accuracy ===")
    overall = df["correct"].mean() * 100
    print(f"Overall: {overall:.1f}%")
    for st, sub in df.groupby("spot_type"):
        acc = sub["correct"].mean() * 100
        print(f"  {st:10s}: n={len(sub):6d} ({len(sub)/len(df)*100:.0f}%)  acc={acc:5.1f}%")

    # ── Cross-tab ──
    print(f"\nConfusion (pred row × actual col):")
    print(pd.crosstab(df["pred"], df["actual_3"]))

    # ── Per spot_type × bucket ──
    print(f"\n=== Per spot_type × equity_bucket ===")
    for st in ["linear", "polarized"]:
        for bk in ["best_hands", "good_hands", "weak_hands", "trash_hands"]:
            sub = df[(df["spot_type"] == st) & (df["equity_bucket"] == bk)]
            if len(sub) < 100:
                continue
            acc = sub["correct"].mean() * 100
            print(f"  {st:10s} × {bk:13s}  n={len(sub):6d}  acc={acc:5.1f}%")

    # ── Save spot classification ──
    spot_meta.to_csv(ROOT / "scripts" / "three_class_model" / "spot_polarization.csv", index=False)
    print(f"\nSaved spot_polarization.csv ({len(spot_meta)} rows)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
