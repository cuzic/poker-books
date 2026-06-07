#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v8 — final unified formulas for all 5 streets (incl. river defense).

Each street uses bet_size-aware logic where applicable.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
WEAK_PAIR_MID = {"second_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DRY_BOARDS = {"dry_high", "low_dry"}


# ── Flop defense v7 (mv-based) ──
def flop_def(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bf = r["board_family"]
    if mv in AIR and dv == "no_draw": return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}: return "FOLD"
    if mv == "overpair": return "RAISE"
    return "CALL"


# ── Turn defense v6 (vs OB → fold weak draws) ──
def turn_def(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
    weak_no_draw = dv in {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
    if bs == "overbet_185p":
        if weak_mv and weak_no_draw: return "FOLD"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
    return "CALL"


# ── River attack v7 (polarized + slowplay strong on dry) ──
def river_atk(r):
    mv = r["mv_cat"]; bf = r["board_family"]
    if mv in STRONG and bf in DRY_BOARDS: return "CHECK"
    if mv == "top_pair" and bf in {"dynamic", "dynamic_2tone"}: return "CHECK"
    VALUE = {"top_pair", "overpair"} | STRONG
    BLUFF = {"no_made_hand", "king_high"}
    if mv in VALUE or mv in BLUFF: return "BET"
    return "CHECK"


# ── River defense v8 (NEW) ──
def river_def(r):
    """River defense — only FOLD/CALL/RAISE (no future cards).
    Fold pressure extreme: even mid pairs often fold.
    Strong nut hands (fullhouse, quads) raise.

    Bet size buckets:
      small_30p:  ≤40% pot — call wider
      med_75p:    50-100% pot
      overbet:    >100% pot — fold tighter
    """
    mv = r["mv_cat"]; bs = r["bet_size"]
    # RAISE the nuts only
    if mv in {"fullhouse", "quads"}: return "RAISE"
    # FOLD air always
    if mv in AIR: return "FOLD"
    # FOLD weak pairs always (low/under/3rd often fold even vs small bet)
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
    # 2nd pair: vs overbet FOLD, else CALL
    if mv == "second_pair":
        return "FOLD" if bs == "overbet" else "CALL"
    # Two pair: vs overbet usually FOLD (counterintuitive but true)
    if mv == "two_pair":
        return "FOLD" if bs == "overbet" else "CALL"
    # Top pair: vs overbet FOLD half, vs smaller CALL
    if mv == "top_pair":
        return "FOLD" if bs == "overbet" else "CALL"
    # set/trips/straight/flush — CALL
    return "CALL"


def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def best_ev_atk(r):
    return max(r["ev_bet"], r["ev_check"])


def ev_of_def(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_of_atk(r, p):
    return r["ev_bet"] if p == "BET" else r["ev_check"]


def ev_gap_row(r):
    evs = [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise"),
           r.get("ev_bet"), r.get("ev_check")]
    evs = sorted([e for e in evs if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def turn_bet_size(s):
    if "_R2." in s: return "small_25p"
    if "_R6." in s: return "med_67p"
    if "_R16" in s: return "overbet_185p"
    return "other"


def river_bet_size(s):
    """Categorize river bet size by code in filename."""
    if "_R4" in s: return "small_30p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R13" in s: return "med_100p"
    if "_R16" in s: return "overbet"
    if "_R89" in s: return "allin"
    return "other"


def prep_def(df, street, bet_size_fn=None):
    sub = df[(df["street"] == street) & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    if bet_size_fn is not None:
        sub["bet_size"] = sub["source_path"].apply(bet_size_fn)
    return sub[sub["ev_gap"].notna()]


def prep_atk(df, street):
    sub = df[(df["street"] == street) & (df["action_context"] == "attack") &
              df["ev_bet"].notna() & df["ev_check"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    sub["modal"] = (sub["bet_freq"].fillna(0) >= 0.5).map({True: "BET", False: "CHECK"})
    sub["best_ev"] = sub.apply(best_ev_atk, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def evaluate(sub, formula, ev_fn, label):
    sub_c = sub.copy()
    sub_c["pred"] = sub_c.apply(formula, axis=1)
    sub_c["ev_p"] = sub_c.apply(lambda r: ev_fn(r, r["pred"]), axis=1)
    sub_c["loss"] = sub_c["best_ev"] - sub_c["ev_p"]
    acc = (sub_c["pred"] == sub_c["modal"]).mean() * 100
    mean_l = sub_c["loss"].mean()
    huge = sub_c[sub_c["ev_gap"] > 0.5]
    huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
    n_huge = len(huge)
    print(f"  {label:30s} n={len(sub_c):6d} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={n_huge})={huge_l:.4f}BB")
    return sub_c


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    print("=== Flop defense ===")
    fd = prep_def(df, "flop")
    evaluate(fd, flop_def, ev_of_def, "v7 (mv-based)")

    print("\n=== Turn defense ===")
    td = prep_def(df, "turn", turn_bet_size)
    evaluate(td, turn_def, ev_of_def, "v6 (size+draw aware)")

    print("\n=== River attack ===")
    ra = prep_atk(df, "river")
    evaluate(ra, river_atk, ev_of_atk, "v7 (polar+slowplay)")

    print("\n=== River defense ===")
    rd = prep_def(df, "river", river_bet_size)
    if len(rd) > 0:
        print(f"  Bet size dist: {rd['bet_size'].value_counts().to_dict()}")
        # Baselines
        print(f"  always_FOLD loss: {(rd['best_ev']-rd['ev_fold']).mean():.4f}BB")
        print(f"  always_CALL loss: {(rd['best_ev']-rd['ev_call']).mean():.4f}BB")
        evaluate(rd, river_def, ev_of_def, "v8 (size-aware)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
