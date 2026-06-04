#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Evaluate a hand-crafted Pure-Check flowchart derived from the depth=5 tree.

The flowchart is written as readable conditions a human can execute in 5-10 seconds.
We score it against the full dataset (out-of-fold via spot-level holdout).

Goal: precision ≥ 90% on PURE_CHECK calls; coverage 30%+; LOW↔HIGH leak < 2%.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"


def pure_check_flowchart(row) -> bool:
    """Returns True if the flowchart fires "PURE_CHECK".

    Tightened v2: OOP-only, board-discriminated rules.
    Goal: precision ≥ 90%, leak ≤ 2%.
    """
    is_oop = row["hero_rel"] == "OOP"
    if not is_oop:
        return False
    if row["street"] != "flop":
        return False  # turn/river too line-dependent for simple rules
    mv = row["mv_cat"]
    dv = row["dv_cat"]
    if mv == "unknown" or dv == "unknown":
        return False  # unreliable feature; defer

    n_suits = int(row["n_suits"])
    spread = int(row.get("spread", 99))
    paired = bool(row["paired"])

    has_draw = dv in {"fd", "oesd", "combo_draw", "gutshot"}
    if has_draw:
        return False  # draws can lead

    is_strong = mv in {"top_pair", "overpair", "two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
    if is_strong:
        return False  # strong made hands may lead

    # Only the WEAK-OR-AIR side of OOP/flop gets pure-checked:
    is_air = mv in {"no_made_hand", "ace_high", "king_high"}
    is_weak_made = mv in {"low_pair", "underpair", "third_pair", "second_pair"}

    # Rule 1: OOP × Flop × Rainbow + non-connected (spread > 4) + air/weak made + no draw
    if n_suits == 3 and spread > 4 and not paired and (is_air or is_weak_made):
        return True

    # Rule 2: OOP × Flop × Rainbow PAIRED + air/weak → PURE_CHECK
    # (paired flop = SB has range adv, BB checks; donk freq < 5%)
    if n_suits == 3 and paired and (is_air or is_weak_made):
        return True

    # Rule 3: OOP × Flop × 2-tone disconnected + air + no draw
    if n_suits == 2 and spread > 4 and is_air:
        return True

    return False


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")

    pred_check = df.apply(pure_check_flowchart, axis=1)
    df["pred_check"] = pred_check.astype(int)
    df["actual_check"] = (df["bet_freq"] < 0.15).astype(int)

    flagged = df[pred_check]
    n_flagged = len(flagged)
    coverage = n_flagged / len(df)

    # precision
    tp = ((df["pred_check"] == 1) & (df["actual_check"] == 1)).sum()
    fp = ((df["pred_check"] == 1) & (df["actual_check"] == 0)).sum()
    precision = tp / max(tp + fp, 1)

    # leak: PURE_CHECK but actual bet_freq ≥ 0.75 (LOW↔HIGH)
    leak = ((df["pred_check"] == 1) & (df["bet_freq"] >= 0.75)).sum()
    leak_rate = leak / max(n_flagged, 1)

    print(f"\n=== Flowchart performance ===")
    print(f"Flagged as PURE_CHECK: {n_flagged} / {len(df)} = {coverage*100:.1f}% coverage")
    print(f"Precision (truly bet_freq < 0.15): {precision*100:.1f}%")
    print(f"Leak rate (actual bet_freq ≥ 0.75): {leak/len(df)*100:.2f}% of all data, {leak_rate*100:.2f}% of flagged")

    # Stratified by hero_rel / street
    print(f"\n=== Per-context performance ===")
    print(f"  context             flagged  precision")
    for (rel, st), sub in df.groupby(["hero_rel", "street"]):
        sub_pred = sub["pred_check"].sum()
        if sub_pred < 20:
            continue
        sub_tp = ((sub["pred_check"] == 1) & (sub["actual_check"] == 1)).sum()
        prec = sub_tp / max(sub_pred, 1)
        print(f"  {rel}/{st:6s}   {sub_pred:6d}    {prec*100:.1f}%")

    # Bet-freq distribution within flagged set
    print(f"\n=== bet_freq distribution within flagged (PURE_CHECK) predictions ===")
    bins = [0, 0.10, 0.15, 0.25, 0.50, 0.75, 1.01]
    labels = ["≤10%", "10-15%", "15-25%", "25-50%", "50-75%", "≥75%"]
    flagged_bf = flagged["bet_freq"]
    for lo, hi, lbl in zip(bins[:-1], bins[1:], labels):
        n = ((flagged_bf >= lo) & (flagged_bf < hi)).sum()
        print(f"  {lbl:8s}  {n:6d}  ({n/n_flagged*100:.1f}%)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
