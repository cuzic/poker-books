#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Test each new turn/river rule individually before combining."""
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


def turn_v7(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
    is_dynamic = bf in DYNAMIC
    if bs == "overbet_185p":
        if weak_mv and dv in WEAK_DRAWS: return "FOLD"
        if bf == "dry_high" and mv in AIR and dv in {"flush_draw"}: return "FOLD"
        if is_dynamic and mv in AIR and dv == "oesd": return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        if is_dynamic and weak_mv and dv in WEAK_DRAWS: return "FOLD"
        if is_dynamic and mv == "top_pair" and dv == "no_draw" and bf in {"dynamic", "monotone"}:
            return "FOLD"
        return "CALL"


# Turn v8 — refined TP × dynamic rule
def turn_v8_R1(r):
    """v7 minus over-aggressive TP × dynamic FOLD; TP only folds vs overbet."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
    is_dynamic = bf in DYNAMIC
    if bs == "overbet_185p":
        if weak_mv and dv in WEAK_DRAWS: return "FOLD"
        if bf == "dry_high" and mv in AIR and dv in {"flush_draw"}: return "FOLD"
        if is_dynamic and mv in AIR and dv == "oesd": return "FOLD"
        # NEW: TP × dynamic × overbet → FOLD
        if is_dynamic and mv == "top_pair" and dv == "no_draw": return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        if is_dynamic and weak_mv and dv in WEAK_DRAWS: return "FOLD"
        # REMOVED: dynamic + TP rule (was over-aggressive)
        return "CALL"


def turn_v8_R2(r):
    """v7 + OESD on dynamic vs med_67p → FOLD."""
    res = turn_v7(r)
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    if bs != "overbet_185p" and bf in DYNAMIC and dv == "oesd" and mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID:
        return "FOLD"
    return res


def turn_v8_R3(r):
    """v7 + A/K-high × gutshot × overbet × dry_high → CALL (not FOLD)."""
    res = turn_v7(r)
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    if bs == "overbet_185p" and bf == "dry_high" and mv in {"ace_high", "king_high"} and dv == "gutshot":
        return "CALL"
    return res


def turn_v8_combined(r):
    """v7 + R1 (TP overbet only) + R2 (OESD med_67p FOLD). Drop R3."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
    is_dynamic = bf in DYNAMIC
    if bs == "overbet_185p":
        if weak_mv and dv in WEAK_DRAWS: return "FOLD"
        if bf == "dry_high" and mv in AIR and dv in {"flush_draw"}: return "FOLD"
        if is_dynamic and mv in AIR and dv == "oesd": return "FOLD"
        # R1: TP × dynamic × overbet → FOLD
        if is_dynamic and mv == "top_pair" and dv == "no_draw": return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        if is_dynamic and weak_mv and dv in WEAK_DRAWS: return "FOLD"
        # R2: OESD on dynamic vs med_67p → FOLD (extension of weak_draw logic)
        if is_dynamic and dv == "oesd" and weak_mv: return "FOLD"
        return "CALL"


# River v10 — additive
def river_v9_1(r):
    mv = r["mv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dynamic = bf in DYNAMIC
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if bs == "allin":
        if mv in {"set", "trips", "straight", "flush", "straight_flush"}: return "CALL"
        return "FOLD"
    if bf in DRY and mv == "top_pair" and bs == "overbet": return "CALL"
    if is_dynamic and mv == "two_pair" and bs == "overbet": return "CALL"
    if is_dynamic and mv in {"top_pair", "two_pair", "second_pair"} and bs == "med_100p":
        return "FOLD"
    if mv in AIR: return "FOLD"
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
    is_big = bs in {"overbet", "med_100p"}
    if mv == "second_pair": return "FOLD" if is_big else "CALL"
    if mv == "two_pair": return "FOLD" if is_big else "CALL"
    if mv == "top_pair": return "FOLD" if is_big else "CALL"
    return "CALL"


def river_v10_R1(r):
    """v9.1 + dynamic + no_made + med_100p → CALL (bluff catch, n=370 100% CALL)."""
    bf = r["board_family"]; is_dyn = bf in DYNAMIC
    if is_dyn and r["mv_cat"] == "no_made_hand" and r["bet_size"] == "med_100p":
        return "CALL"
    return river_v9_1(r)


def river_v10_R2(r):
    """v9.1 + dynamic + allin: set/straight FOLD."""
    bf = r["board_family"]; is_dyn = bf in DYNAMIC
    mv = r["mv_cat"]
    if r["bet_size"] == "allin" and is_dyn:
        # On dynamic allin, set/straight fold (very tight)
        if mv in {"set", "straight"}: return "FOLD"
    return river_v9_1(r)


def river_v10_R3(r):
    """v9.1 + flush × med_100p × dynamic → RAISE."""
    bf = r["board_family"]; is_dyn = bf in DYNAMIC
    if is_dyn and r["mv_cat"] == "flush" and r["bet_size"] == "med_100p":
        return "RAISE"
    return river_v9_1(r)


def river_v10_R4(r):
    """v9.1 + TP × allin × dynamic → CALL (98% CALL!)."""
    bf = r["board_family"]; is_dyn = bf in DYNAMIC
    if r["bet_size"] == "allin" and is_dyn and r["mv_cat"] == "top_pair":
        return "CALL"
    return river_v9_1(r)


def river_v10_R5(r):
    """v9.1 + TP / 2nd_pair × small_30p × dynamic → FOLD (100% FOLD)."""
    bf = r["board_family"]; is_dyn = bf in DYNAMIC
    if is_dyn and r["bet_size"] == "small_30p" and r["mv_cat"] in {"top_pair", "second_pair"}:
        return "FOLD"
    return river_v9_1(r)


def river_v10_R6(r):
    """v9.1 + fullhouse × overbet × dynamic → CALL (99% CALL, don't RAISE)."""
    bf = r["board_family"]; is_dyn = bf in DYNAMIC
    if is_dyn and r["mv_cat"] == "fullhouse" and r["bet_size"] == "overbet":
        return "CALL"
    return river_v9_1(r)


def river_v10_combined(r):
    """v9.1 + R3 (flush 100p RAISE) + R5 (TP/2nd 30p FOLD) — only proven helpful."""
    mv = r["mv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dyn = bf in DYNAMIC
    if is_dyn and mv == "flush" and bs == "med_100p": return "RAISE"
    if is_dyn and bs == "small_30p" and mv in {"top_pair", "second_pair"}: return "FOLD"
    return river_v9_1(r)


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

    print(f"\n=== {label} (n={len(sub)}) ===")
    for name, f in formulas:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {name:30s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge={huge_l:.4f}BB")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    evaluate(df, "turn", [
        ("v7 baseline", turn_v7),
        ("v7+R1 (TP overbet only)", turn_v8_R1),
        ("v7+R2 (OESD med_67p FOLD)", turn_v8_R2),
        ("v7+R3 (A/K gutshot OB CALL)", turn_v8_R3),
        ("v8 combined R1+R2+R3", turn_v8_combined),
    ], turn_bs, "TURN DEFENSE")

    evaluate(df, "river", [
        ("v9.1 baseline", river_v9_1),
        ("v9.1+R1 (no_made 100p CALL)", river_v10_R1),
        ("v9.1+R2 (dyn allin set/str FOLD)", river_v10_R2),
        ("v9.1+R3 (flush 100p RAISE)", river_v10_R3),
        ("v9.1+R4 (TP allin CALL)", river_v10_R4),
        ("v9.1+R5 (TP/2nd 30p FOLD)", river_v10_R5),
        ("v9.1+R6 (FH overbet CALL)", river_v10_R6),
        ("v10 combined R1-R6", river_v10_combined),
    ], river_bs, "RIVER DEFENSE")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
