#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Verify defense-side framework on the unified dataset (120 defense spots).

Defense actions: FOLD / CALL / RAISE
Framework rules:
  best_hands:
    - 2P+ / overpair → RAISE
    - top_pair → CALL
  good_hands → CALL
  weak_hands → CALL (defaults) / FOLD vs big bet
  trash_hands → FOLD (defaults) / RAISE if bluff candidate

Evaluation:
  1) Modal action match (predict action with highest freq)
  2) Per-action band match (3-band on each)
  3) Per-bucket × board accuracy
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def has_strong_draw(dv_cat: str) -> bool:
    return dv_cat in {"oesd", "flush_draw", "combo_draw", "gutshot", "nut_flush_draw"}


def predict_defense_action(bucket: str, mv_cat: str, dv_cat: str, board_family: str) -> str:
    """Predict modal action: FOLD / CALL / RAISE."""
    nut_2p = mv_cat in {"set", "trips", "two_pair", "straight", "flush", "fullhouse", "quads"}
    is_overpair = mv_cat == "overpair"
    is_top_pair = mv_cat == "top_pair"
    is_bluff_candidate = has_strong_draw(dv_cat)

    paired = board_family == "paired"

    if bucket == "best_hands":
        if nut_2p or is_overpair:
            return "RAISE"
        if is_top_pair:
            return "CALL"
        return "CALL"

    if bucket == "good_hands":
        return "CALL"

    if bucket == "weak_hands":
        return "CALL"  # MDF default

    if bucket == "trash_hands":
        if paired and is_bluff_candidate:
            return "RAISE"  # CR bluff
        return "FOLD"

    return "CALL"


def actual_modal(row) -> str:
    """Ground truth modal action."""
    a = {"FOLD": row.get("fold_freq", 0) or 0,
         "CALL": row.get("call_freq", 0) or 0,
         "RAISE": row.get("raise_freq", 0) or 0}
    return max(a, key=lambda k: a[k])


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    print(f"Loaded {len(df)} rows total")

    # Filter to defense
    df = df[df["action_context"] == "defense"].copy()
    print(f"Defense rows: {len(df)} / spots: {df['spot_id'].nunique()}")

    # Filter to spots with usable buckets
    df = df[df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    print(f"With equity_bucket: {len(df)} / spots: {df['spot_id'].nunique()}")

    # Ground truth modal action
    df["actual_modal"] = df.apply(actual_modal, axis=1)
    print(f"\nActual modal distribution:")
    print(df["actual_modal"].value_counts())

    # Predict
    df["pred_modal"] = df.apply(
        lambda r: predict_defense_action(
            r["equity_bucket"], r["mv_cat"], r["dv_cat"],
            str(r.get("board_family", "")),
        ),
        axis=1,
    )
    df["correct"] = df["pred_modal"] == df["actual_modal"]
    overall = df["correct"].mean() * 100
    print(f"\n=== Defense modal accuracy: {overall:.1f}% ===")
    print("Confusion (pred row × actual col):")
    print(pd.crosstab(df["pred_modal"], df["actual_modal"]))

    print(f"\n=== Per-bucket ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 50:
            continue
        acc = sub["correct"].mean() * 100
        # actual distribution
        dist = sub["actual_modal"].value_counts(normalize=True).to_dict()
        dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
        print(f"  {bk:13s} n={len(sub):6d}  acc={acc:5.1f}%  actual_dist={dist_str}")

    print(f"\n=== Per-board-family ===")
    for bf, sub in df.groupby("board_family"):
        if len(sub) < 50:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {bf:18s} n={len(sub):6d}  acc={acc:5.1f}%")

    # ── Bet sizing analysis ──
    # Defense varies by bet size. Use the R-prefixed action's size as proxy.
    # Extract from flop_actions (last R<num> in X-R<num> pattern)
    import re
    SIZE_RE = re.compile(r"R(\d+(?:\.\d+)?)")
    def extract_size(row):
        # use the most recent bet line
        line = row.get("flop_actions") or ""
        if not line and row.get("turn_actions"):
            line = row.get("turn_actions") or ""
        m = SIZE_RE.findall(str(line))
        if not m:
            return None
        return float(m[-1])
    df["bet_size"] = df.apply(extract_size, axis=1)

    print(f"\n=== Bet size distribution ===")
    print(df["bet_size"].dropna().describe())

    # Per-bucket × bet_size bucketing
    def size_bucket(s):
        if pd.isna(s):
            return "unknown"
        if s < 3:
            return "small"
        if s < 8:
            return "mid"
        return "big"
    df["size_bucket"] = df["bet_size"].apply(size_bucket)
    print(f"\n=== Per (bucket × bet_size) actual distribution ===")
    for bk in ["best_hands", "good_hands", "weak_hands", "trash_hands"]:
        for sz in ["small", "mid", "big"]:
            sub = df[(df["equity_bucket"] == bk) & (df["size_bucket"] == sz)]
            if len(sub) < 30:
                continue
            dist = sub["actual_modal"].value_counts(normalize=True).to_dict()
            dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
            acc = sub["correct"].mean() * 100
            print(f"  {bk:13s} × {sz:5s}  n={len(sub):5d}  acc={acc:5.1f}%  actual={dist_str}")

    # Confusion analysis: where do we go wrong?
    print(f"\n=== Top error patterns ===")
    err = df[~df["correct"]]
    print(err.groupby(["equity_bucket", "pred_modal", "actual_modal"]).size().sort_values(ascending=False).head(15))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
