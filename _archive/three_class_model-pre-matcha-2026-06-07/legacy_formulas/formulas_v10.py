#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""v10 — final refinement targeting residual huge_loss cells.

Turn v7: extend FOLD criteria on DYNAMIC boards
  - dynamic + weak_made + medium bet → FOLD (even with weak draws)
  - dry + overbet + flush_draw → FOLD (overbet erodes implied odds)

River v10: dynamic-board bluff-catching + allin tightness
  - dynamic + (TP/2P) + overbet → CALL (bluff catch — wide vil bluff range)
  - dynamic + no_made + med_100p → CALL (bluff catch on dynamic)
  - vs allin: only nutted hands (set+ on dry, straight+ on dynamic) call
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
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}


# ── Turn formulas ──
def turn_v6(r):
    """Previous best."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
    if bs == "overbet_185p":
        if weak_mv and dv in WEAK_DRAWS: return "FOLD"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
    return "CALL"


def turn_v7(r):
    """v7: dynamic-board awareness on medium bet, tighter overbet defense."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
    is_dynamic = bf in DYNAMIC

    if bs == "overbet_185p":
        # vs overbet: fold weak made + weak draws (no implied odds)
        if weak_mv and dv in WEAK_DRAWS: return "FOLD"
        # NEW: vs overbet on dry_high + flush draw alone → FOLD (overbet kills FD odds)
        if bf == "dry_high" and mv in AIR and dv in {"flush_draw"}: return "FOLD"
        # vs overbet + OESD on dynamic → FOLD (also no odds)
        if is_dynamic and mv in AIR and dv == "oesd": return "FOLD"
        return "CALL"
    else:
        # medium 67% bet
        if mv in AIR and dv == "no_draw": return "FOLD"
        # NEW: dynamic + weak_made + weak_draw → FOLD (med-bet pressure on dynamic)
        if is_dynamic and weak_mv and dv in WEAK_DRAWS: return "FOLD"
        # NEW: dynamic + top_pair + no_draw → FOLD (vulnerable to many draws)
        if is_dynamic and mv == "top_pair" and dv == "no_draw" and bf in {"dynamic", "monotone"}:
            return "FOLD"
        return "CALL"


# ── River formulas ──
def river_v9(r):
    mv = r["mv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dynamic = bf in DYNAMIC
    is_big = bs in {"overbet", "allin", "med_100p"}
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if bs == "allin":
        if mv in {"set", "trips", "straight", "flush"}: return "CALL"
        return "FOLD"
    if bf in DRY and mv == "top_pair" and bs == "overbet": return "CALL"
    if is_dynamic and mv in {"top_pair", "two_pair", "second_pair"} and bs == "med_100p": return "FOLD"
    if mv in AIR: return "FOLD"
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
    if mv == "second_pair": return "FOLD" if is_big else "CALL"
    if mv == "two_pair": return "FOLD" if is_big else "CALL"
    if mv == "top_pair": return "FOLD" if is_big else "CALL"
    return "CALL"


def river_v10(r):
    """v9.1: v9 + ONLY proven-helpful rule (dynamic + 2P + overbet → CALL bluff catch)."""
    mv = r["mv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dynamic = bf in DYNAMIC

    if mv in {"fullhouse", "quads"}: return "RAISE"

    if bs == "allin":
        if mv in {"set", "trips", "straight", "flush", "straight_flush"}: return "CALL"
        return "FOLD"

    # v9 Rule A: dry + TP + overbet → CALL (catch wide bluff range)
    if bf in DRY and mv == "top_pair" and bs == "overbet": return "CALL"

    # NEW Rule C: dynamic + 2P + overbet → CALL (bluff catch on dynamic polarized overbet)
    if is_dynamic and mv == "two_pair" and bs == "overbet": return "CALL"

    # v9 Rule B: dynamic + TP/2P/2nd + med_100p → FOLD (draws complete)
    if is_dynamic and mv in {"top_pair", "two_pair", "second_pair"} and bs == "med_100p":
        return "FOLD"

    # Default
    if mv in AIR: return "FOLD"
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
    is_big = bs in {"overbet", "med_100p"}
    if mv == "second_pair": return "FOLD" if is_big else "CALL"
    if mv == "two_pair": return "FOLD" if is_big else "CALL"
    if mv == "top_pair": return "FOLD" if is_big else "CALL"
    return "CALL"


# ── Evaluation ──
def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of_def(r, p):
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
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["bet_size"] = sub["source_path"].apply(bs_fn)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    print(f"\n=== {label} ===")
    for name, f in formulas:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {name:20s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    evaluate(df, "turn", [("v6 baseline", turn_v6), ("v7 dynamic+", turn_v7)], turn_bs, "TURN DEFENSE")
    evaluate(df, "river", [("v9 baseline", river_v9), ("v10 dynamic+bluff", river_v10)], river_bs, "RIVER DEFENSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
