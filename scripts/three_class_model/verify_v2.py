#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Verify v2 of the unified framework with refined trash bluff rules.

Key changes from v1:
- trash bluff = only OESD/FD/combo_draw/gutshot+blocker (not blanket BW/connector)
- best top_pair on dry_high → predict 50/50 (count as mixed)
- good_hands → CHECK (66% correct)
- weak_hands → CHECK
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "knowledges" / "gto_wizard_full"
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"


def has_strong_draw(dv_cat: str) -> bool:
    """Strong = OESD, flush_draw, combo_draw, gutshot, nut_flush_draw"""
    return dv_cat in {"oesd", "flush_draw", "combo_draw", "gutshot", "nut_flush_draw"}


def has_bdfd(dv_cat: str) -> bool:
    return dv_cat in {"onecard_bdfd", "twocards_bdfd"}


RANKS = "23456789TJQKA"
BROADWAY = set("TJQKA")


def predict_v2(bucket: str, mv_cat: str, dv_cat: str,
                board_family: str, card_a: str, card_b: str) -> str:
    """Return BET / CHECK predicted action for attack context."""
    nut_2p = mv_cat in {"set", "trips", "two_pair", "straight", "flush", "fullhouse", "quads"}
    is_overpair = mv_cat == "overpair"
    is_top_pair = mv_cat == "top_pair"
    paired_board = board_family == "paired"
    monotone_board = board_family == "monotone"
    dry_high_board = board_family == "dry_high"

    if bucket == "best_hands":
        if nut_2p or is_overpair:
            return "BET"
        if is_top_pair:
            if paired_board:
                return "BET"
            if dry_high_board:
                return "CHECK"  # slowplay
            return "BET"
        return "BET"

    if bucket == "good_hands":
        # 66% are CHECK; some value with TP that wasn't classified as best
        if paired_board:
            return "BET"  # paired board pushes everyone to bet
        return "CHECK"

    if bucket == "weak_hands":
        if paired_board:
            return "BET"
        return "CHECK"

    if bucket == "trash_hands":
        if monotone_board:
            return "CHECK"
        if paired_board:
            return "BET"  # 72% bluff on paired
        # Refined bluff selection: only strong draws bluff at scale
        if has_strong_draw(dv_cat):
            return "BET"
        if has_bdfd(dv_cat):
            # BDFD → bet half the time; conservative predict CHECK to match median
            return "CHECK"
        return "CHECK"

    return "CHECK"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    # filter to attack only (no F/C action in spot)
    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")

    # Determine attack vs defense per spot
    spot_is_defense = {}
    for p in DATA.glob("**/*.json"):
        d = json.loads(p.read_text())
        actions = d.get("action_solutions") or []
        codes = [(a.get("action") or {}).get("code") for a in actions]
        spot_id = (d.get("_meta") or {}).get("id") or p.stem
        spot_is_defense[spot_id] = "F" in codes or "C" in codes

    df["is_defense"] = df["spot_id"].map(lambda s: spot_is_defense.get(s, False))
    attack = df[~df["is_defense"]].copy()
    print(f"Attack rows: {len(attack)}")

    # Apply predictions
    attack["pred"] = attack.apply(
        lambda r: predict_v2(r["equity_bucket"], r["mv_cat"], r["dv_cat"],
                              str(r.get("board_family", "")),
                              str(r.get("card_a", "")), str(r.get("card_b", ""))),
        axis=1,
    )
    attack["actual"] = (attack["bet_freq"] >= 0.50).map({True: "BET", False: "CHECK"})
    attack["correct"] = attack["pred"] == attack["actual"]

    overall = attack["correct"].mean()
    print(f"\n=== v2 overall accuracy: {overall*100:.1f}% ===")
    print(f"Confusion (pred row, actual col):")
    conf = pd.crosstab(attack["pred"], attack["actual"])
    print(conf)

    print(f"\n=== Per-bucket accuracy ===")
    for bk, sub in attack.groupby("equity_bucket"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean()
        bet_rate_actual = (sub["actual"] == "BET").mean()
        bet_rate_pred = (sub["pred"] == "BET").mean()
        print(f"  {bk:13s}  n={len(sub):6d}  acc={acc*100:5.1f}%  actual_bet={bet_rate_actual*100:.0f}%  pred_bet={bet_rate_pred*100:.0f}%")

    print(f"\n=== Per-board-family accuracy ===")
    for bf, sub in attack.groupby("board_family"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean()
        print(f"  {bf:18s}  n={len(sub):6d}  acc={acc*100:5.1f}%")

    print(f"\n=== Top error patterns ===")
    err = attack[~attack["correct"]]
    print(err.groupby(["equity_bucket", "pred", "actual"]).size().sort_values(ascending=False).head(10))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
