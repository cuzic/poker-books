#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Test bucket-based formula on MTT 50bb turn and river."""
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
STRONG_DRAWS = {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}
COMMIT_HANDS = {"set", "trips", "straight", "two_pair", "flush", "fullhouse", "quads"}


def cash_turn_v8(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
    is_dynamic = bf in DYNAMIC
    if bs in {"overbet_185p", "overbet_117p"}:
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


def mtt_turn_bucket(r):
    """Bucket-based for MTT 50bb turn."""
    eb = r.get("equity_bucket")
    bs = r["bet_size"]
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]
    is_dynamic = bf in DYNAMIC

    # Best/good buckets → CALL (high enough equity)
    if eb == "best_hands":
        # RAISE the commit hands on overbet
        if bs == "overbet_117p" and mv in COMMIT_HANDS and bf != "monotone": return "RAISE"
        return "CALL"
    if eb == "good_hands":
        if bs == "overbet_117p" and mv in COMMIT_HANDS and bf != "monotone": return "RAISE"
        return "CALL"

    # Weak: depends on size + draw
    if eb == "weak_hands":
        # vs overbet: fold weak+no_draw; call if has draw
        if bs == "overbet_117p":
            if dv in STRONG_DRAWS and bf != "monotone": return "CALL"
            return "FOLD"
        # vs small bet: call (pot odds)
        return "CALL"

    # Trash → FOLD vs overbet; call only with strong draw on non-monotone small bet
    if eb == "trash_hands":
        if bs == "overbet_117p": return "FOLD"
        if dv in STRONG_DRAWS and bf != "monotone": return "CALL"
        return "FOLD"

    return "FOLD"


def mtt_turn_hybrid(r):
    """Hybrid: bucket as primary + Cash v8 patterns layered."""
    eb = r.get("equity_bucket")
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dynamic = bf in DYNAMIC

    if eb == "best_hands":
        if bs == "overbet_117p" and mv in COMMIT_HANDS and bf != "monotone": return "RAISE"
        return "CALL"
    if eb == "good_hands":
        if bs == "overbet_117p" and mv in COMMIT_HANDS and bf != "monotone": return "RAISE"
        return "CALL"
    if eb == "weak_hands":
        if bs == "overbet_117p":
            # Strong draws can continue on non-monotone
            if dv in STRONG_DRAWS and bf != "monotone": return "CALL"
            # 2nd_pair × dry → CALL (bluff catch)
            if mv == "second_pair" and bf in DRY: return "CALL"
            return "FOLD"
        return "CALL"
    if eb == "trash_hands":
        if bs == "overbet_117p": return "FOLD"
        if dv in STRONG_DRAWS and bf != "monotone": return "CALL"
        if mv in AIR and dv == "no_draw": return "FOLD"
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


def mtt50_turn_bs(s):
    if "_R2." in s: return "small_25p"
    if "_R10" in s: return "overbet_117p"
    return "other"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_mtt50_bb_turn") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "") &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(mtt50_turn_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    print(f"=== MTT 50bb turn defense (rows with bucket): {len(sub)} ===")
    for label, f in [("Cash v8 baseline", cash_turn_v8),
                      ("MTT bucket pure", mtt_turn_bucket),
                      ("MTT bucket+layer", mtt_turn_hybrid)]:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:25s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge={huge_l:.4f}BB")

    # River
    print("\n=== MTT 50bb river defense ===")
    riv = df[(df["street"] == "river") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_mtt50_bb_river") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "") &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        riv[c] = riv[c].fillna(0)
    riv["modal"] = riv[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    riv["best_ev"] = riv.apply(best_ev, axis=1)
    riv["ev_gap"] = riv.apply(ev_gap_row, axis=1)
    riv = riv[riv["ev_gap"].notna()]
    print(f"  MTT river n={len(riv)} rows")
    print(f"  Bet sizes: {riv['source_path'].str.extract(r'_R([\\d.]+)\\.json$', expand=False).value_counts().to_dict()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
