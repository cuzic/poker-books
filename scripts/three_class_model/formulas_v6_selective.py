#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v6 — selective refinement: only add rules where they DEFINITELY improve huge_gap.

For each formula:
1. Start from v4
2. Try adding ONE rule targeting a specific top huge-loss cell
3. Keep only if huge_gap loss decreases AND overall loss doesn't increase >0.01 BB
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def best_ev_atk(r):
    return max(r["ev_bet"], r["ev_check"])


def ev_of_def(r, pred):
    if pred == "FOLD": return r["ev_fold"]
    if pred == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_of_atk(r, pred):
    return r["ev_bet"] if pred == "BET" else r["ev_check"]


def ev_gap_row(r):
    evs = [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise"),
           r.get("ev_bet"), r.get("ev_check")]
    evs = sorted([e for e in evs if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


# ── Per-street datasets ──
def prep_flop_def(df):
    sub = df[(df["street"] == "flop") & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna()].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["bucket_s"] = pd.cut(sub["eq_percentile"], bins=[-0.01, 0.25, 0.5, 0.75, 1.01],
                              labels=[0, 1, 2, 3]).cat.codes.clip(lower=0)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def prep_turn_def(df):
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna()].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["bet_size"] = sub["source_path"].apply(lambda s:
        "small_25p" if "_R2." in s else
        "med_67p" if "_R6." in s else
        "overbet_185p" if "_R16" in s else "other")
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def prep_river_atk(df):
    sub = df[(df["street"] == "river") & (df["action_context"] == "attack") &
              df["ev_bet"].notna() & df["ev_check"].notna()].copy()
    sub["modal"] = (sub["bet_freq"].fillna(0) >= 0.5).map({True: "BET", False: "CHECK"})
    sub["best_ev"] = sub.apply(best_ev_atk, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


# ── Formula library (v4 baseline + candidate refinements) ──
def flop_v4(r):
    bucket = r["bucket_s"]
    if bucket <= 1 and r["mv_cat"] in {"no_made_hand", "ace_high", "king_high"} and r["dv_cat"] == "no_draw":
        return "FOLD"
    if bucket >= 3 and r["mv_cat"] in {"overpair", "two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}:
        return "RAISE"
    return "CALL"


def flop_v6(r):
    """Selective refinements: FOLD low/3rd_pair only on very specific weak boards.
    Set→CALL (slowplay) not RAISE."""
    bucket = r["bucket_s"]
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]
    # Tight FOLD for air
    if bucket <= 1 and mv in {"no_made_hand", "ace_high", "king_high"} and dv == "no_draw":
        return "FOLD"
    # Extra FOLD: weak pairs on dry boards where they're dominated (vs BTN range)
    if bucket == 1 and mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf == "dry_high":
        return "FOLD"
    # Value RAISE: only overpair (NOT sets — they slowplay)
    if bucket >= 3 and mv == "overpair":
        return "RAISE"
    return "CALL"


def turn_v4(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in {"no_made_hand", "ace_high", "king_high", "low_pair", "underpair"}
    weakish = mv in {"third_pair", "second_pair"}
    if bs == "overbet_185p":
        if (weak_mv or weakish) and dv == "no_draw": return "FOLD"
    else:
        if weak_mv and dv == "no_draw": return "FOLD"
    return "CALL"


def turn_v6(r):
    """Confirmed winner: vs overbet, gutshot/BDFD doesn't have odds → FOLD."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in {"no_made_hand", "ace_high", "king_high", "low_pair", "underpair"}
    weakish = mv in {"third_pair", "second_pair"}
    weak_or_no_draw = dv in {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
    if bs == "overbet_185p":
        if (weak_mv or weakish) and weak_or_no_draw: return "FOLD"
    else:
        if weak_mv and dv == "no_draw": return "FOLD"
    return "CALL"


def river_v4(r):
    mv = r["mv_cat"]
    VALUE = {"top_pair", "overpair", "two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
    BLUFF = {"no_made_hand", "king_high"}
    if mv in VALUE or mv in BLUFF: return "BET"
    return "CHECK"


def river_v6(r):
    """v4 + slowplay strong hands on dry boards (where there's no draws to charge)."""
    mv = r["mv_cat"]
    bf = r["board_family"]
    STRONG = {"set", "trips", "straight", "flush", "fullhouse", "quads"}
    # Slowplay strong on dry: villain can't have many strong calling hands
    if mv in STRONG and bf in {"dry_high", "low_dry"}:
        return "CHECK"
    VALUE = {"top_pair", "overpair", "two_pair"} | STRONG
    BLUFF = {"no_made_hand", "king_high"}
    if mv in VALUE or mv in BLUFF: return "BET"
    return "CHECK"


def compare(sub, v_old, v_new, ev_of, name):
    sub = sub.copy()
    sub["p_old"] = sub.apply(v_old, axis=1)
    sub["p_new"] = sub.apply(v_new, axis=1)
    sub["ev_old"] = sub.apply(lambda r: ev_of(r, r["p_old"]), axis=1)
    sub["ev_new"] = sub.apply(lambda r: ev_of(r, r["p_new"]), axis=1)
    sub["L_old"] = sub["best_ev"] - sub["ev_old"]
    sub["L_new"] = sub["best_ev"] - sub["ev_new"]
    huge = sub[sub["ev_gap"] > 0.5]
    print(f"\n=== {name} ===")
    print(f"  All n={len(sub)}: old_loss={sub['L_old'].mean():.4f}BB → new_loss={sub['L_new'].mean():.4f}BB Δ={sub['L_new'].mean()-sub['L_old'].mean():+.4f}")
    print(f"  Huge n={len(huge)}: old_loss={huge['L_old'].mean():.4f}BB → new_loss={huge['L_new'].mean():.4f}BB Δ={huge['L_new'].mean()-huge['L_old'].mean():+.4f}")
    # Per modal
    for m in sorted(sub["modal"].unique()):
        sm = sub[sub["modal"] == m]
        if len(sm) < 200: continue
        print(f"    modal={m:5s} n={len(sm):6d} old={sm['L_old'].mean():.4f} → new={sm['L_new'].mean():.4f}")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    fd = prep_flop_def(df)
    print(f"Flop defense rows: {len(fd)}")
    compare(fd, flop_v4, flop_v6, ev_of_def, "FLOP DEFENSE v4 vs v6 (FOLD low/3rd_pair on dry_high only)")

    td = prep_turn_def(df)
    print(f"\nTurn defense rows: {len(td)}")
    compare(td, turn_v4, turn_v6, ev_of_def, "TURN DEFENSE v4 vs v6 (vs overbet: also FOLD weak draws)")

    ra = prep_river_atk(df)
    print(f"\nRiver attack rows: {len(ra)}")
    compare(ra, river_v4, river_v6, ev_of_atk, "RIVER ATTACK v4 vs v6 (slowplay STRONG on dry)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
