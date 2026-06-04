#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""MTT 50bb river v15 — true-allin aware, lower eqp threshold for calling."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}


def river_v14_cash(r):
    """Cash 100bb v14 baseline."""
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


def river_mtt50_v15(r):
    """MTT 50bb v15 — true allin (no raise option), wider call threshold."""
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dyn = bf in DYNAMIC

    # MTT 50bb has only 2 sizes: med_100p and allin (true all-in, no raise above)
    if bs == "allin":
        # All-in: no raise option, just call/fold
        # Bucket-based with lower eqp threshold than Cash (because allin commits less in MTT)
        if eb == "best_hands": return "CALL"  # all best_hands call (no raise above allin)
        if eb == "good_hands": return "CALL"
        if eb == "weak_hands":
            # eqp threshold ~0.65 for calling allin
            if pd.notna(eqp) and eqp > 0.65: return "CALL"
            return "FOLD"
        # trash → FOLD
        return "FOLD"

    # vs med_100p (effectively bet 100% pot, raise still possible)
    if bs == "med_100p":
        # Nut hands raise
        if mv == "quads": return "RAISE"
        if mv == "fullhouse": return "RAISE"
        if eb == "best_hands":
            if pd.notna(eqp) and eqp > 0.93: return "RAISE"
            # straight/flush/trips raise on best bucket
            if mv in {"straight", "flush", "trips"}: return "RAISE"
            return "CALL"
        if eb == "good_hands":
            # 2P/straight/flush on good bucket → RAISE on dynamic (commit)
            if mv in {"two_pair", "straight", "flush"} and is_dyn: return "RAISE"
            return "CALL"
        if eb == "weak_hands":
            # weak bucket on med_100p: depends on mv
            if mv in {"straight", "flush", "trips"}: return "CALL"  # made hand bluff catch
            if mv in {"top_pair", "two_pair", "second_pair", "third_pair"}:
                # Bluff catch on med_100p (MTT polarization)
                if pd.notna(eqp) and eqp > 0.55: return "CALL"
                return "FOLD"
            return "FOLD"
        # trash bucket
        return "FOLD"

    # default fallback (shouldn't hit for MTT 50bb river)
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


def mtt50_river_bs(s):
    if "_R35" in s: return "allin"
    if "_R89" in s: return "allin"
    if "_R13" in s: return "med_100p"
    if "_R16" in s: return "overbet"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "river") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_mtt50_bb_river") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "") &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(mtt50_river_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    print(f"=== MTT 50bb river: {len(sub)} rows ===")
    for label, f in [("Cash v14", river_v14_cash),
                      ("MTT v15 (true allin)", river_mtt50_v15)]:
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
