#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""River v12 — bucket-centric formula with eq_percentile fine-tuning.

User insight: on river, relative equity (bucket + eqp) is most predictive.
Add nuance via mv_cat for nut RAISE decisions.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}


def river_v11_eqp(r):
    """Baseline v11."""
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.95 and bs != "allin": return "RAISE"
        return "CALL"
    if eb == "good_hands":
        if bs == "allin": return "FOLD"
        return "CALL"
    if eb == "weak_hands":
        if bs in {"small_30p", "med_75p"}: return "CALL"
        return "FOLD"
    return "FOLD"


def river_v12(r):
    """v12: refined bucket cutoffs with eqp granularity."""
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]

    # Nut raise always
    if mv in {"fullhouse", "quads"}: return "RAISE"

    # vs allin: pure equity-based — only top equity calls
    if bs == "allin":
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85: return "CALL"
        # On dry boards, set+/straight+ has good equity vs nutted shove range
        if bf in DRY and mv in {"set", "trips", "straight", "flush"}: return "CALL"
        return "FOLD"

    if eb == "best_hands":
        # very strong → RAISE for value
        if pd.notna(eqp) and eqp > 0.93: return "RAISE"
        return "CALL"

    if eb == "good_hands":
        return "CALL"

    if eb == "weak_hands":
        # vs small/medium bet, weak bucket can call
        if bs in {"small_30p", "med_75p"}: return "CALL"
        # vs overbet, weak bucket folds
        return "FOLD"

    # trash_hands
    return "FOLD"


def river_v13(r):
    """v13: even finer eqp thresholds + bluff catch on no_made + med."""
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dyn = bf in DYNAMIC

    if mv in {"fullhouse", "quads"}: return "RAISE"

    if bs == "allin":
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85: return "CALL"
        if bf in DRY and mv in {"set", "trips", "straight", "flush"}: return "CALL"
        return "FOLD"

    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.93: return "RAISE"
        return "CALL"

    if eb == "good_hands":
        return "CALL"

    if eb == "weak_hands":
        # Refined cutoff: vs medium+ size, weak hands fold unless dynamic bluff-catch
        if bs == "overbet":
            # Special: dynamic + 2P/TP can bluff catch overbet (weak bucket TPs)
            if is_dyn and mv in {"top_pair", "two_pair"}: return "CALL"
            return "FOLD"
        if bs == "med_100p":
            return "FOLD"
        # smaller bets: CALL
        return "CALL"

    # trash_hands
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


def river_bs(s):
    if "_R89" in s: return "allin"
    if "_R16" in s: return "overbet"
    if "_R13" in s: return "med_100p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "river") & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "") &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(river_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]

    for label, f in [("v11 bucket+eqp (baseline)", river_v11_eqp),
                      ("v12 refined cutoffs", river_v12),
                      ("v13 + dynamic bluff catch", river_v13)]:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:30s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
