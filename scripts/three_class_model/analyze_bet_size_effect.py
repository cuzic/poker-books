#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Analyze how bet_size affects defense action at each eq_percentile range."""
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


def actual_modal(row):
    a = {"FOLD": row.get("fold_freq", 0) or 0,
         "CALL": row.get("call_freq", 0) or 0,
         "RAISE": row.get("raise_freq", 0) or 0}
    return max(a, key=lambda k: a[k])


def main() -> int:
    main_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "dataset_unified.csv", low_memory=False)
    bet_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "spot_bet_info.csv")
    # Merge on spot_id
    bet_df = bet_df[["spot_id", "bet_size_pot_ratio", "pot_odds", "hero_stack_bb"]].drop_duplicates(subset=["spot_id"])
    df = main_df.merge(bet_df, on="spot_id", how="left")
    print(f"Merged rows: {len(df)}")

    df = df[(df["action_context"] == "defense") &
            (df["eq_percentile"].notna()) &
            (df["bet_size_pot_ratio"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    print(f"Defense rows with bet_size: {len(df)} / spots: {df['spot_id'].nunique()}")

    df["size_bucket"] = df["bet_size_pot_ratio"].apply(size_bucket)
    df["actual_modal"] = df.apply(actual_modal, axis=1)
    df["eq_bin"] = pd.cut(df["eq_percentile"], bins=[0, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 1.001],
                          labels=["0-20", "20-30", "30-40", "40-50", "50-70", "70-90", "90-100"])

    print(f"\nSize bucket distribution:")
    print(df["size_bucket"].value_counts())
    print(f"\nbet_size_pot_ratio distribution:")
    print(df["bet_size_pot_ratio"].describe())

    # ── Per (eq_bin × size_bucket) modal distribution ──
    print(f"\n=== eq_bin × bet_size → action modal distribution ===")
    for eb in ["0-20", "20-30", "30-40", "40-50", "50-70", "70-90", "90-100"]:
        print(f"\n  --- eq_bin {eb} ---")
        for sz in ["small", "mid", "big"]:
            sub = df[(df["eq_bin"] == eb) & (df["size_bucket"] == sz)]
            if len(sub) < 50:
                continue
            dist = sub["actual_modal"].value_counts(normalize=True).to_dict()
            dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
            modal = max(dist, key=lambda k: dist[k])
            print(f"    size={sz:5s}  n={len(sub):5d}  modal={modal:5s}  {dist_str}")

    # ── Build size-aware mapping ──
    print(f"\n=== Suggested size-aware mapping (modal action per cell) ===")
    print(f"  eq_bin    size  modal_action")
    for eb in ["0-20", "20-30", "30-40", "40-50", "50-70", "70-90", "90-100"]:
        for sz in ["small", "mid", "big"]:
            sub = df[(df["eq_bin"] == eb) & (df["size_bucket"] == sz)]
            if len(sub) < 50:
                continue
            dist = sub["actual_modal"].value_counts(normalize=True).to_dict()
            modal = max(dist, key=lambda k: dist[k])
            print(f"  {eb:8s}  {sz:5s}  {modal:5s}  ({dist.get(modal,0)*100:.0f}%)")

    # ── Apply size-aware mapping ──
    # Hardcode the empirical mapping
    def eq_size_to_action(eq, sz):
        if pd.isna(eq) or pd.isna(sz) or sz == "unknown":
            return "CALL"
        if sz == "small":
            if eq < 0.20: return "FOLD"
            if eq < 0.90: return "CALL"
            return "CALL"  # 90+
        if sz == "mid":
            if eq < 0.35: return "FOLD"
            if eq < 0.90: return "CALL"
            return "CALL"
        # big
        if eq < 0.50: return "FOLD"
        if eq < 0.90: return "CALL"
        return "RAISE"

    df["pred"] = df.apply(lambda r: eq_size_to_action(r["eq_percentile"], r["size_bucket"]), axis=1)
    df["correct"] = df["pred"] == df["actual_modal"]
    print(f"\n=== v4 (eq + bet_size) accuracy ===")
    print(f"Overall: {df['correct'].mean()*100:.1f}%")
    print(pd.crosstab(df["pred"], df["actual_modal"]))

    print(f"\n=== Per bucket ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {bk:13s} n={len(sub):6d}  acc={acc:5.1f}%")

    print(f"\n=== Per size_bucket ===")
    for sz, sub in df.groupby("size_bucket"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {sz:10s} n={len(sub):6d}  acc={acc:5.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
