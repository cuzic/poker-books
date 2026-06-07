#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""MTT 50bb turn defense v9 — MTT-specific commit-or-fold formula."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
COMMIT_HANDS = {"set", "trips", "straight", "two_pair", "flush", "fullhouse", "quads"}
WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
STRONG_DRAWS = {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}


def cash_turn_v8(r):
    """Cash baseline (current Cash 100bb best)."""
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


def mtt50_turn_v9(r):
    """MTT 50bb-specific: commit-or-fold on overbet, simple call on small."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dynamic = bf in DYNAMIC
    is_monotone = bf == "monotone"

    if bs == "overbet_117p":
        # RAISE: commit value hands (MTT: SPR low → low risk commit)
        if mv in COMMIT_HANDS and bf != "monotone": return "RAISE"
        # CALL: bluff catchers
        if mv == "top_pair": return "CALL"
        if mv == "second_pair" and bf in DRY: return "CALL"   # MTT bluff catch
        if mv == "second_pair" and dv == "no_draw": return "CALL"  # bluff catch even on dynamic
        if mv == "fullhouse": return "CALL"  # slowplay
        # FOLD draws on monotone (no implied odds at low SPR)
        if is_monotone and dv in STRONG_DRAWS: return "FOLD"
        # FOLD: weak made + no/weak draw
        if mv in AIR | WEAK_PAIR_LOW and dv in WEAK_DRAWS: return "FOLD"
        # CALL: weak with strong draw on non-monotone
        return "CALL"

    else:  # small_25p (or other)
        # vs small bet, easy call pot odds — only fold deep trash
        if mv in AIR and dv == "no_draw": return "FOLD"
        return "CALL"


def mtt50_turn_v10(r):
    """v9 + refinements based on residual."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dynamic = bf in DYNAMIC
    is_monotone = bf == "monotone"

    if bs == "overbet_117p":
        # RAISE commits — but exclude monotone (flush board, less commit)
        if mv in {"set", "trips", "straight"} and bf != "monotone": return "RAISE"
        if mv == "two_pair" and bf == "dry_high": return "RAISE"
        if mv == "two_pair" and bf in DYNAMIC: return "RAISE"  # 2P dynamic too
        # Flush on monotone: RAISE
        if mv == "flush" and is_monotone: return "RAISE"
        # CALL: bluff catchers
        if mv == "top_pair": return "CALL"
        if mv == "second_pair" and dv == "no_draw": return "CALL"
        if mv == "fullhouse": return "CALL"
        # FOLD weak / draws on monotone
        if is_monotone and dv in STRONG_DRAWS: return "FOLD"
        if is_monotone and mv in AIR | WEAK_PAIR_LOW: return "FOLD"
        # FOLD on dry: weak + weak_draw
        if mv in AIR | WEAK_PAIR_LOW and dv in WEAK_DRAWS: return "FOLD"
        return "CALL"

    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
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


def mtt50_turn_bs(s):
    if "_R2." in s: return "small_25p"
    if "_R10" in s: return "overbet_117p"
    return "other"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_mtt50_bb_turn") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(mtt50_turn_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]

    print(f"=== MTT 50bb turn defense: {len(sub)} rows ===")
    for label, f in [("Cash v8 (baseline)", cash_turn_v8),
                      ("MTT v9 (commit-or-fold)", mtt50_turn_v9),
                      ("MTT v10 (refined)", mtt50_turn_v10)]:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:30s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge={huge_l:.4f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
