#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v5 formulas — refined to fix the top huge-loss cells.

Flop defense v5:
  - FOLD: bucket≤1 AND (mv∈{air,A/K-high} OR mv∈{low_pair,third_pair}) AND no_strong_draw
  - CALL: set/two_pair/trips → CALL (slowplay, no RAISE)
  - RAISE: only overpair on best bucket (clear value raise)

Turn defense v5:
  - vs overbet (≥100% pot):
    FOLD: weakish mv (no_made/A-high/K-high/low/under/2nd/3rd/under_pair)
          AND dv ∈ {no_draw, gutshot, BDFD, oesd}   ← include weak draws too
          NOT including flush_draw / combo_draw (those still defend)
  - vs medium (≤67% pot):
    FOLD: only air (no_made/A-high/K-high) AND no_draw
    CALL: else
  (No RAISE on turn — slowplay)

River attack v5:
  - BET: 2P+, set, trips, straight, flush, fullhouse, quads, overpair
  - BET: top_pair AND board ∈ {dry_high, low_dry, paired}  ← not on dynamic
  - BET: bluff = no_made_hand AND board ∈ {dynamic, dynamic_2tone}  ← dynamic only
  - BET: king_high — keep
  - CHECK: low/2nd/3rd pair, ace_high, top_pair on dynamic
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def flop_v4(r):
    """previous best — for comparison."""
    bucket = r["bucket_s"]
    mv = r["mv_s"]
    dv = r["dv_s"]
    if bucket <= 1 and mv == 0 and dv == 0: return "FOLD"
    if bucket >= 3 and mv >= 3: return "RAISE"
    return "CALL"


def flop_v5(r):
    """v5: expanded FOLD criteria, slowplay strong hands, RAISE only overpair on best."""
    bucket = r["bucket_s"]
    mv_cat = r["mv_cat"]
    dv_cat = r["dv_cat"]
    bf = r["board_family"]

    # Aggressive folds for weak/trash on non-monotone boards
    if bucket <= 1:
        weak_made = mv_cat in {"no_made_hand", "ace_high", "king_high",
                                "low_pair", "underpair", "third_pair"}
        no_strong_draw = dv_cat in {"no_draw", "twocards_bdfd", "onecard_bdfd"}
        if weak_made and no_strong_draw:
            return "FOLD"

    # Value raise: best bucket + overpair (clear top hand)
    if bucket >= 3 and mv_cat == "overpair":
        return "RAISE"

    # Top pair RAISE on dry boards (range advantage situation)
    if bucket >= 2 and mv_cat == "top_pair" and bf in {"low_dry", "dry_high"}:
        return "CALL"  # actually most TP just calls — RAISE was over-aggressive

    return "CALL"


def turn_v4(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in {"no_made_hand", "ace_high", "king_high", "low_pair", "underpair"}
    weakish = mv in {"third_pair", "second_pair"}
    no_draw = dv == "no_draw"
    if bs == "overbet_185p":
        if (weak_mv or weakish) and no_draw: return "FOLD"
    else:
        if weak_mv and no_draw: return "FOLD"
    return "CALL"


def turn_v5(r):
    """vs overbet, fold even with weak draws (gutshot/BDFD). Keep FD/combo_draw."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in {"no_made_hand", "ace_high", "king_high", "low_pair", "underpair"}
    weakish = mv in {"third_pair", "second_pair"}
    weak_draw = dv in {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
    if bs == "overbet_185p":
        # vs overbet: even gutshot doesn't have odds
        if (weak_mv or weakish) and weak_draw:
            return "FOLD"
        # also fold weak made without ANY draw vs overbet
        if mv == "third_pair" and dv == "no_draw":
            return "FOLD"
    else:
        # vs 67%: fold weak made with no draw
        if weak_mv and dv == "no_draw":
            return "FOLD"
    return "CALL"


def river_v4(r):
    mv = r["mv_cat"]
    VALUE = {"top_pair", "overpair", "two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
    BLUFF = {"no_made_hand", "king_high"}
    if mv in VALUE or mv in BLUFF: return "BET"
    return "CHECK"


def river_v5(r):
    """Board-aware polarization: slowplay strong hands on dry, TP only on dry, bluff on dynamic."""
    mv = r["mv_cat"]
    bf = r["board_family"]
    STRONG = {"set", "trips", "straight", "flush", "fullhouse", "quads"}
    # Slowplay strong nutted hands on dry boards (they're way ahead, no draws to charge)
    if mv in STRONG:
        if bf in {"dry_high", "low_dry"}:
            return "CHECK"   # slowplay
        return "BET"  # bet on dynamic to charge draws

    if mv == "two_pair":
        if bf == "dry_high":
            return "CHECK"  # slowplay sometimes
        return "BET"

    if mv == "overpair":
        return "BET" if bf != "paired" else "CHECK"

    if mv == "top_pair":
        # On dry, bet for value (no draws to fear). On dynamic, check (vulnerable).
        return "BET" if bf in {"dry_high", "low_dry", "paired"} else "CHECK"

    # Bluffs
    if mv == "no_made_hand" and bf in {"dynamic", "dynamic_2tone", "monotone"}:
        return "BET"
    if mv == "king_high":
        return "BET"

    return "CHECK"


def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def best_ev_atk(r):
    return max(r["ev_bet"], r["ev_check"])


def ev_of(r, pred, ctx):
    if ctx == "defense":
        if pred == "FOLD": return r["ev_fold"]
        if pred == "CALL": return r["ev_call"]
        return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]
    else:
        return r["ev_bet"] if pred == "BET" else r["ev_check"]


def evaluate(df, pred_old_fn, pred_new_fn, ctx, label):
    print(f"\n=== {label} ===")
    sub = df.copy()
    sub["pred_old"] = sub.apply(pred_old_fn, axis=1)
    sub["pred_new"] = sub.apply(pred_new_fn, axis=1)
    sub["ev_old"] = sub.apply(lambda r: ev_of(r, r["pred_old"], ctx), axis=1)
    sub["ev_new"] = sub.apply(lambda r: ev_of(r, r["pred_new"], ctx), axis=1)
    sub["loss_old"] = sub["best_ev"] - sub["ev_old"]
    sub["loss_new"] = sub["best_ev"] - sub["ev_new"]

    acc_old = (sub["pred_old"] == sub["modal"]).mean() * 100
    acc_new = (sub["pred_new"] == sub["modal"]).mean() * 100
    print(f"  Overall: old acc={acc_old:.1f}% loss={sub['loss_old'].mean():.4f}BB  →  new acc={acc_new:.1f}% loss={sub['loss_new'].mean():.4f}BB")

    huge = sub[sub["ev_gap"] > 0.5]
    if len(huge) > 0:
        print(f"  Huge gap (n={len(huge)}): old={huge['loss_old'].mean():.4f}BB  →  new={huge['loss_new'].mean():.4f}BB  save={huge['loss_old'].mean() - huge['loss_new'].mean():+.4f}BB")


def ev_gap_row(r):
    evs = [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise"), r.get("ev_bet"), r.get("ev_check")]
    evs = sorted([e for e in evs if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def prep_def(df, street):
    sub = df[(df["street"] == street) & (df["action_context"] == "defense") &
              (df["ev_call"].notna()) & (df["ev_fold"].notna())].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    MV_MAP = {}
    for i, vals in enumerate([
        {"no_made_hand", "king_high", "ace_high"},
        {"low_pair", "underpair", "third_pair", "second_pair"},
        {"top_pair"},
        {"overpair"},
        {"two_pair", "set", "trips"},
        {"straight", "flush", "fullhouse", "quads"},
    ]):
        for k in vals:
            MV_MAP[k] = i
    sub["mv_s"] = sub["mv_cat"].fillna("").map(MV_MAP).fillna(0).astype(int)
    sub["dv_s"] = sub["dv_cat"].fillna("").map({"no_draw": 0, "twocards_bdfd": 0, "onecard_bdfd": 0,
                                                 "gutshot": 0, "oesd": 1, "flush_draw": 1, "nut_flush_draw": 1,
                                                 "combo_draw": 2}).fillna(0).astype(int)
    if sub["eq_percentile"].notna().mean() > 0.5:
        sub["bucket_s"] = pd.cut(sub["eq_percentile"], bins=[-0.01, 0.25, 0.5, 0.75, 1.01],
                                  labels=[0, 1, 2, 3]).cat.codes.clip(lower=0)
    else:
        sub["bucket_s"] = sub["mv_s"].clip(0, 3)
    if street == "turn":
        sub["bet_size"] = sub["source_path"].apply(lambda s:
            "small_25p" if "_R2." in s else
            "med_67p" if "_R6." in s else
            "overbet_185p" if "_R16" in s else "other")
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def prep_atk(df, street):
    sub = df[(df["street"] == street) & (df["action_context"] == "attack") &
              (df["ev_bet"].notna()) & (df["ev_check"].notna())].copy()
    sub["modal"] = (sub["bet_freq"].fillna(0) >= 0.5).map({True: "BET", False: "CHECK"})
    sub["best_ev"] = sub.apply(best_ev_atk, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    fd = prep_def(df, "flop")
    print(f"FLOP defense rows: {len(fd)}")
    evaluate(fd, flop_v4, flop_v5, "defense", "FLOP DEFENSE v4 → v5")

    td = prep_def(df, "turn")
    print(f"\nTURN defense rows: {len(td)}")
    evaluate(td, turn_v4, turn_v5, "defense", "TURN DEFENSE v4 → v5")

    ra = prep_atk(df, "river")
    print(f"\nRIVER attack rows: {len(ra)}")
    evaluate(ra, river_v4, river_v5, "attack", "RIVER ATTACK v4 → v5")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
