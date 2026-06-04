#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Compare Cash 100bb vs MTT 50bb defense formulas.

After MTT data is fetched, run both data sources through the same v7-turn / v14-river
formulas and see if huge_loss patterns are similar or different.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}


def turn_v8(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
    is_dynamic = bf in DYNAMIC
    if bs == "overbet_185p" or bs == "overbet":
        if weak_mv and dv in WEAK_DRAWS: return "FOLD"
        if bf == "dry_high" and mv in AIR and dv in {"flush_draw"}: return "FOLD"
        if is_dynamic and mv in AIR and dv == "oesd": return "FOLD"
        if is_dynamic and mv == "top_pair" and dv == "no_draw": return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        if is_dynamic and weak_mv and dv in WEAK_DRAWS: return "FOLD"
        if is_dynamic and dv == "oesd" and weak_mv: return "FOLD"
        return "CALL"


def river_v14(r):
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dyn = bf in DYNAMIC
    if mv == "quads": return "RAISE"
    if mv == "fullhouse" and bs not in {"overbet"}: return "RAISE"
    if mv == "fullhouse" and bs == "overbet": return "CALL"
    if bs == "allin":
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85: return "CALL"
        if bf in DRY and mv in {"set", "trips", "straight", "flush"}: return "CALL"
        if eb == "good_hands" and mv in {"straight", "flush", "trips"}: return "CALL"
        if bf == "monotone" and mv == "flush": return "CALL"
        if is_dyn and mv == "top_pair" and eb in {"weak_hands", "good_hands"}: return "CALL"
        return "FOLD"
    if mv in {"straight", "flush", "trips"}: return "CALL"
    if mv == "top_pair" and bf in DRY and bs in {"overbet", "med_100p"}: return "CALL"
    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96: return "RAISE"
        return "CALL"
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if is_dyn and mv in {"two_pair"}: return "CALL"
            return "FOLD"
        if bs == "med_100p": return "FOLD"
        return "CALL"
    return "FOLD"


def best_ev(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_gap_row(r):
    evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def turn_bs(s):
    if "_R2." in s: return "small_25p"
    if "_R6." in s: return "med_67p"
    if "_R16" in s: return "overbet_185p"
    return "other"


def river_bs(s):
    if "_R89" in s: return "allin"
    if "_R16" in s: return "overbet"
    if "_R13" in s: return "med_100p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


def evaluate(sub, formula, ev_fn, bs_fn, label):
    sub = sub.copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(bs_fn)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    sub["pred"] = sub.apply(formula, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_fn(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]
    acc = (sub["pred"] == sub["modal"]).mean() * 100
    mean_l = sub["loss"].mean()
    huge = sub[sub["ev_gap"] > 0.5]
    huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
    print(f"  {label:30s} n={len(sub):5d} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")
    return sub


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    # Filter to turn defense per source
    print("=== TURN DEFENSE: Cash vs MTT 50bb ===")
    turn_base = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
                    df["ev_call"].notna() & df["ev_fold"].notna() &
                    df["mv_cat"].notna() & (df["mv_cat"] != "")]
    cash_turn = turn_base[turn_base["source_path"].str.contains("def_cash100_bb_turn")]
    mtt_turn = turn_base[turn_base["source_path"].str.contains("def_mtt50_bb_turn")]
    if len(cash_turn) > 0:
        evaluate(cash_turn, turn_v8, ev_of, turn_bs, "Cash 100bb v8")
    if len(mtt_turn) > 0:
        evaluate(mtt_turn, turn_v8, ev_of, turn_bs, "MTT 50bb v8")
    else:
        print("  MTT 50bb turn defense: NO DATA YET")

    print("\n=== RIVER DEFENSE: Cash vs MTT 50bb ===")
    river_base = df[(df["street"] == "river") & (df["action_context"] == "defense") &
                     df["ev_call"].notna() & df["ev_fold"].notna() &
                     df["mv_cat"].notna() & (df["mv_cat"] != "") &
                     df["equity_bucket"].notna() & (df["equity_bucket"] != "")]
    cash_river = river_base[river_base["source_path"].str.contains("def_cash100_bb_river")]
    mtt_river = river_base[river_base["source_path"].str.contains("def_mtt50_bb_river")]
    if len(cash_river) > 0:
        evaluate(cash_river, river_v14, ev_of, river_bs, "Cash 100bb v14")
    if len(mtt_river) > 0:
        evaluate(mtt_river, river_v14, ev_of, river_bs, "MTT 50bb v14")
    else:
        print("  MTT 50bb river defense: NO DATA YET")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
