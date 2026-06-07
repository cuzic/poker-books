#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Turn v10 — v8 + bucket override layer."""
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


def turn_v10(r):
    """v8 + bucket override pre-filter."""
    eb = r.get("equity_bucket")
    bs = r["bet_size"]
    # Bucket pre-filter: best/good always CALL
    if eb == "best_hands": return "CALL"
    if eb == "good_hands": return "CALL"
    # trash: FOLD vs overbet unconditionally (no draw saves)
    if eb == "trash_hands" and bs == "overbet_185p": return "FOLD"
    # Otherwise fall through to v8 logic
    return turn_v8(r)


def turn_v11(r):
    """v8 + tighter bucket integration."""
    eb = r.get("equity_bucket")
    bs = r["bet_size"]
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]
    eqp = r.get("eq_percentile")
    is_dynamic = bf in DYNAMIC
    has_strong_draw = dv in {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}

    # best/good → CALL
    if eb == "best_hands": return "CALL"
    if eb == "good_hands": return "CALL"
    # trash: FOLD vs overbet, FOLD vs med_67p unless strong draw
    if eb == "trash_hands":
        if bs == "overbet_185p": return "FOLD"
        if bs == "med_67p" and not has_strong_draw: return "FOLD"
        # vs small_25p, trash with any draw can call
        if has_strong_draw: return "CALL"
        return "FOLD"
    # weak_hands: v8 logic for nuance
    return turn_v8(r)


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


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "") &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(turn_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    for label, f in [("v8 baseline", turn_v8),
                      ("v10 bucket pre-filter", turn_v10),
                      ("v11 tighter bucket", turn_v11)]:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:25s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
