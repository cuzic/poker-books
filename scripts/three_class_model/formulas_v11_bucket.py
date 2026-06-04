#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v11 — use equity_bucket (GTO Wizard's relative strength) as primary axis.

The user's insight: on turn/river, hand strength is largely determined.
Relative equity vs villain's range is the most predictive feature.

Test bucket-based formulas for turn defense and river defense.
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


# ── Turn defense ──
def turn_v11_pure_bucket(r):
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    if eb == "best_hands": return "CALL"   # strong relative equity
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        # vs overbet fold weak, vs medium call
        if bs == "overbet_185p": return "FOLD"
        return "CALL"
    # trash
    return "FOLD"


def turn_v11_bucket_plus(r):
    """v11 + dv consideration: trash with strong draw can call."""
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    dv = r["dv_cat"]
    has_strong_draw = dv in {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}
    if eb == "best_hands": return "CALL"
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        if bs == "overbet_185p": return "FOLD"
        return "CALL"
    # trash
    if has_strong_draw and bs != "overbet_185p": return "CALL"
    return "FOLD"


# ── River defense ──
def river_v11_pure_bucket(r):
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    # Nuts: raise
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if eb == "best_hands":
        # best hands call (some raise variants based on mv)
        return "CALL"
    if eb == "good_hands":
        # vs allin we tighten further
        if bs == "allin": return "FOLD"
        return "CALL"
    if eb == "weak_hands":
        # vs small bet call (catch wider), vs large bet fold
        if bs in {"small_30p", "med_75p"}: return "CALL"
        return "FOLD"
    return "FOLD"


def river_v11_bucket_plus(r):
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if eb == "best_hands":
        # raise the highest equity hands
        if pd.notna(eqp) and eqp > 0.95 and bs != "allin": return "RAISE"
        return "CALL"
    if eb == "good_hands":
        if bs == "allin": return "FOLD"
        return "CALL"
    if eb == "weak_hands":
        if bs in {"small_30p", "med_75p"}: return "CALL"
        return "FOLD"
    return "FOLD"


# ── Old best v8/v10 for comparison ──
WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}


def turn_v8(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
    is_dynamic = bf in DYNAMIC
    if bs == "overbet_185p":
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


def river_v10(r):
    mv = r["mv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dyn = bf in DYNAMIC
    if is_dyn and mv == "flush" and bs == "med_100p": return "RAISE"
    if is_dyn and bs == "small_30p" and mv in {"top_pair", "second_pair"}: return "FOLD"
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if bs == "allin":
        if mv in {"set", "trips", "straight", "flush", "straight_flush"}: return "CALL"
        return "FOLD"
    if bf in DRY and mv == "top_pair" and bs == "overbet": return "CALL"
    if is_dyn and mv == "two_pair" and bs == "overbet": return "CALL"
    if is_dyn and mv in {"top_pair", "two_pair", "second_pair"} and bs == "med_100p":
        return "FOLD"
    if mv in AIR: return "FOLD"
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
    is_big = bs in {"overbet", "med_100p"}
    if mv == "second_pair": return "FOLD" if is_big else "CALL"
    if mv == "two_pair": return "FOLD" if is_big else "CALL"
    if mv == "top_pair": return "FOLD" if is_big else "CALL"
    return "CALL"


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


def evaluate(df, street, formulas, bs_fn, label):
    sub = df[(df["street"] == street) & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "") &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(bs_fn)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    print(f"\n=== {label} (n={len(sub)}) ===")
    for name, f in formulas:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {name:30s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    evaluate(df, "turn", [
        ("v8 (mv+dv+board)", turn_v8),
        ("v11 pure bucket", turn_v11_pure_bucket),
        ("v11 bucket+draw", turn_v11_bucket_plus),
    ], turn_bs, "TURN DEFENSE")

    evaluate(df, "river", [
        ("v10 (current best)", river_v10),
        ("v11 pure bucket", river_v11_pure_bucket),
        ("v11 bucket+eqp", river_v11_bucket_plus),
    ], river_bs, "RIVER DEFENSE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
