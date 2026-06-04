#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Defense v3: board sub-classification + per-board action mapping.

Combines:
- Stage 1: eq_percentile per cell (bucket × MV × board_sub × DV)
- Stage 2: board-specific eq → action mapping

Mapping per board_sub derived from data:
  dry_high (static):   eq<35→FOLD, eq>=35→CALL (with broadway raise at very top)
  broadway_connected:  eq<35→FOLD, eq>=35→CALL (slowplay)
  broadway_connector:  eq<35→FOLD, eq>=35→CALL/RAISE
  paired:              custom (often more RAISE)
  monotone:            mostly CHECK then call
  low_connector:       eq<35→FOLD, eq>=80→RAISE (deny equity), else CALL
  low_disconnected:    eq<35→FOLD, eq>=35→CALL
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from board_subfamily import board_subfamily  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def eq_to_action_by_board(eq, board_sub):
    """Board-specific eq → action mapping."""
    if eq is None or pd.isna(eq):
        return "CALL"

    # 1) Very low eq → FOLD (universal)
    if eq < 0.30:
        return "FOLD"

    # 2) Boundary 30-50%: depends on board
    if eq < 0.50:
        # FOLD-favored boards: connectors (dynamic), low_connector, paired
        if board_sub in {"low_connector", "broadway_connector", "paired_low"}:
            return "FOLD"
        # CALL-favored (dry boards have MDF kicking in)
        return "CALL"

    # 3) Middle 50-80%: CALL universally
    if eq < 0.80:
        return "CALL"

    # 4) High eq 80-100%: RAISE on dynamic/connected boards, CALL on static
    if board_sub in {"low_connector", "broadway_connector"}:
        return "RAISE"  # protect / deny equity
    if board_sub == "paired_high":
        return "CALL"  # slowplay vs paired (KK8, AA7)
    if board_sub == "broadway_connected":
        return "CALL"  # KJT — slowplay (82% CALL in data)
    if board_sub == "dry_high":
        # split: 80-95 CALL, 95+ RAISE
        return "CALL"
    return "CALL"


def actual_modal(row):
    a = {"FOLD": row.get("fold_freq", 0) or 0,
         "CALL": row.get("call_freq", 0) or 0,
         "RAISE": row.get("raise_freq", 0) or 0}
    return max(a, key=lambda k: a[k])


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = df[(df["action_context"] == "defense") & (df["eq_percentile"].notna()) & (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    df["board_sub"] = df["board_flop"].apply(board_subfamily)
    df["actual_modal"] = df.apply(actual_modal, axis=1)
    print(f"Defense rows: {len(df)}")
    print(f"\nBoard sub-family distribution:")
    print(df["board_sub"].value_counts())

    # ── Per (board_sub × eq_bin) actual distribution to confirm patterns ──
    df["eq_bin"] = pd.cut(df["eq_percentile"], bins=[0,0.2,0.3,0.4,0.5,0.7,0.9,1.001],
                          labels=["0-20","20-30","30-40","40-50","50-70","70-90","90-100"])
    print(f"\n=== Per (board_sub × eq_bin) actual modal dist (top boards) ===")
    for bs in df["board_sub"].value_counts().head(8).index:
        print(f"\n  --- {bs} ---")
        sub_all = df[df["board_sub"] == bs]
        for eb in ["0-20","20-30","30-40","40-50","50-70","70-90","90-100"]:
            cell = sub_all[sub_all["eq_bin"] == eb]
            if len(cell) < 50:
                continue
            dist = cell["actual_modal"].value_counts(normalize=True).to_dict()
            dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
            n = len(cell)
            print(f"    {eb:6s}  n={n:5d}  {dist_str}")

    # ── Apply prediction ──
    df["pred"] = df.apply(lambda r: eq_to_action_by_board(r["eq_percentile"], r["board_sub"]), axis=1)
    df["correct"] = df["pred"] == df["actual_modal"]
    print(f"\n=== v3 oracle (actual eq) + board-specific mapping ===")
    print(f"Overall accuracy: {df['correct'].mean()*100:.1f}%")
    print(pd.crosstab(df["pred"], df["actual_modal"]))

    print(f"\n=== Per bucket ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {bk:13s} n={len(sub):6d}  acc={acc:5.1f}%")

    print(f"\n=== Per board_sub ===")
    for bs, sub in df.groupby("board_sub"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {bs:25s} n={len(sub):6d}  acc={acc:5.1f}%")

    # Train/test split for honest accuracy
    spots = sorted(df["spot_id"].unique())
    half = len(spots) // 2
    test_spots = set(spots[half:])
    test = df[df["spot_id"].isin(test_spots)]
    print(f"\n=== Hold-out test ({len(test)} rows) ===")
    print(f"Accuracy: {test['correct'].mean()*100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
