#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Verify v4: expanded slowplay range for best_hands.

Changes from v2:
- best_hands × monotone → CHECK (was BET) ← v3 finding: monotone reduces value bet
- best_hands × flush (made) on non-monotone → CHECK (nut slowplay)
- best_hands × top_pair × dynamic_2tone → CHECK (added to slowplay zone)
- best_hands × 2P+ on dynamic → BET (kept, GTO bets for protection)
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
    return dv_cat in {"oesd", "flush_draw", "combo_draw", "gutshot", "nut_flush_draw"}


def predict_v4(bucket: str, mv_cat: str, dv_cat: str, board_family: str) -> str:
    nut_2p = mv_cat in {"set", "trips", "two_pair", "straight", "flush", "fullhouse", "quads"}
    is_overpair = mv_cat == "overpair"
    is_top_pair = mv_cat == "top_pair"
    is_flush = mv_cat == "flush"

    paired = board_family == "paired"
    monotone = board_family == "monotone"
    dynamic_2tone = board_family == "dynamic_2tone"
    dry_high = board_family == "dry_high"

    if bucket == "best_hands":
        # 1) Made flush (nuts) on non-monotone → slowplay (no one has flush to call)
        if is_flush and not monotone:
            return "CHECK"
        # 2) Monotone: slowplay most best (range advantage diluted)
        if monotone:
            return "CHECK"
        # 3) top_pair board-dependent slowplays
        if is_top_pair:
            if paired:
                return "BET"
            if dry_high or dynamic_2tone:
                return "CHECK"  # slowplay
            return "BET"  # dynamic / low_dry / etc — protect
        # 4) 2P+ / overpair → BET (with monotone exception above)
        if nut_2p or is_overpair:
            return "BET"
        return "BET"

    if bucket == "good_hands":
        if paired:
            return "BET"
        return "CHECK"

    if bucket == "weak_hands":
        if paired:
            return "BET"
        return "CHECK"

    if bucket == "trash_hands":
        if monotone:
            return "CHECK"
        if paired:
            return "BET"
        if has_strong_draw(dv_cat):
            return "BET"
        return "CHECK"

    return "CHECK"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)

    # Per-spot is_defense flag
    spot_is_defense = {}
    for p in DATA.glob("**/*.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        actions = d.get("action_solutions") or []
        codes = [(a.get("action") or {}).get("code") for a in actions]
        spot_id = (d.get("_meta") or {}).get("id") or p.stem
        spot_is_defense[spot_id] = "F" in codes or "C" in codes

    df["is_defense"] = df["spot_id"].map(lambda s: spot_is_defense.get(s, False))
    attack = df[~df["is_defense"]].copy()
    print(f"Attack rows: {len(attack)}")

    attack["pred"] = attack.apply(
        lambda r: predict_v4(r["equity_bucket"], r["mv_cat"], r["dv_cat"],
                              str(r.get("board_family", ""))),
        axis=1,
    )
    attack["actual"] = (attack["bet_freq"] >= 0.50).map({True: "BET", False: "CHECK"})
    attack["correct"] = attack["pred"] == attack["actual"]

    overall = attack["correct"].mean() * 100
    print(f"\n=== v4 overall accuracy: {overall:.1f}% ===")
    print(f"Confusion (pred row, actual col):")
    print(pd.crosstab(attack["pred"], attack["actual"]))

    print(f"\n=== Per-bucket ===")
    for bk, sub in attack.groupby("equity_bucket"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean() * 100
        pred_bet = (sub["pred"] == "BET").mean() * 100
        actual_bet = (sub["actual"] == "BET").mean() * 100
        print(f"  {bk:13s} n={len(sub):6d}  acc={acc:5.1f}%  pred_bet={pred_bet:.0f}%  actual_bet={actual_bet:.0f}%")

    print(f"\n=== Per-board-family ===")
    for bf, sub in attack.groupby("board_family"):
        if len(sub) < 100:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {bf:20s} n={len(sub):6d}  acc={acc:5.1f}%")

    # Best_hands × board_family detailed
    print(f"\n=== best_hands × board breakdown ===")
    best = attack[attack["equity_bucket"] == "best_hands"]
    for bf, sub in best.groupby("board_family"):
        if len(sub) < 50:
            continue
        acc = sub["correct"].mean() * 100
        pred_bet = (sub["pred"] == "BET").mean() * 100
        actual_bet = (sub["actual"] == "BET").mean() * 100
        print(f"  best × {bf:15s}  n={len(sub):5d}  acc={acc:.1f}%  pred_bet={pred_bet:.0f}% actual_bet={actual_bet:.0f}%")

    print(f"\n=== Top error patterns ===")
    err = attack[~attack["correct"]]
    print(err.groupby(["equity_bucket", "board_family", "pred", "actual"]).size().sort_values(ascending=False).head(15))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
