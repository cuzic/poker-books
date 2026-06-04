#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""River defense analysis using v7-style mv_cat-based formula."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR = {"low_pair", "underpair", "third_pair", "second_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}


def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of_def(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_gap_row(r):
    evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


# ── Candidate river defense formulas ──
def river_v1_always_call(r):
    return "CALL"


def river_v2_basic(r):
    """Like turn v6 base: FOLD air+no_draw, CALL else."""
    mv = r["mv_cat"]; dv = r["dv_cat"]
    if mv in AIR and dv == "no_draw":
        return "FOLD"
    return "CALL"


def river_v3_river_aware(r):
    """River has no draws by definition (no future cards). Just FOLD weak made."""
    mv = r["mv_cat"]
    # On river dv mostly = no_draw (made flushes/straights count as made)
    if mv in AIR:
        return "FOLD"
    return "CALL"


def river_v4_turn_like(r):
    """Apply turn defense v6 structure: bet-size dependent."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in AIR | {"low_pair", "underpair", "third_pair"}
    weakish = mv == "second_pair"
    weak_or_no_draw = dv in {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
    if bs == "overbet":
        if (weak_mv or weakish) and weak_or_no_draw:
            return "FOLD"
    else:
        if mv in AIR:
            return "FOLD"
    return "CALL"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "river") & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    print(f"River defense rows: {len(sub)} (sources: {sub['source_path'].nunique()})")
    if len(sub) < 100:
        print("Insufficient data.")
        return 0

    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)

    # bet_size from filename
    def bs(s):
        if "_R16" in s: return "overbet"  # high bet ~150%+
        if "_R7" in s or "_R8" in s: return "med_75p"
        return "small_50p"
    sub["bet_size"] = sub["source_path"].apply(bs)

    print(f"\nModal dist: {sub['modal'].value_counts(normalize=True).round(3).to_dict()}")
    print(f"Bet size dist: {sub['bet_size'].value_counts().to_dict()}")

    print(f"\n=== Per mv_cat ===")
    for mv, ss in sub.groupby("mv_cat"):
        if len(ss) < 50: continue
        mod = ss["modal"].value_counts(normalize=True).to_dict()
        modstr = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(mod.items()))
        print(f"  {mv:15s} n={len(ss):4d}  {modstr}")

    print(f"\n=== Per bet_size ===")
    for bs_v, ss in sub.groupby("bet_size"):
        mod = ss["modal"].value_counts(normalize=True).to_dict()
        modstr = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(mod.items()))
        l_call = (ss["best_ev"] - ss["ev_call"]).mean()
        l_fold = (ss["best_ev"] - ss["ev_fold"]).mean()
        print(f"  {bs_v:12s} n={len(ss):4d}  {modstr}  always_CALL={l_call:.4f}  always_FOLD={l_fold:.4f}")

    print(f"\n=== Strategy comparison ===")
    print(f"  Baselines:")
    print(f"    always_FOLD: loss={(sub['best_ev']-sub['ev_fold']).mean():.4f}BB")
    print(f"    always_CALL: loss={(sub['best_ev']-sub['ev_call']).mean():.4f}BB")
    for label, f in [
        ("v2: FOLD air+no_draw", river_v2_basic),
        ("v3: FOLD all air", river_v3_river_aware),
        ("v4: turn-like (size-aware)", river_v4_turn_like),
    ]:
        sub_c = sub.copy()
        sub_c["pred"] = sub_c.apply(f, axis=1)
        sub_c["ev_p"] = sub_c.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
        sub_c["loss"] = sub_c["best_ev"] - sub_c["ev_p"]
        acc = (sub_c["pred"] == sub_c["modal"]).mean() * 100
        mean = sub_c["loss"].mean()
        huge = sub_c[sub_c["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:30s} acc={acc:5.1f}% mean={mean:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")

    print(f"\n=== Per mv with v3 prediction ===")
    sub_c = sub.copy()
    sub_c["pred"] = sub_c.apply(river_v3_river_aware, axis=1)
    sub_c["ev_p"] = sub_c.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
    sub_c["loss"] = sub_c["best_ev"] - sub_c["ev_p"]
    for mv, ss in sub_c.groupby("mv_cat"):
        if len(ss) < 50: continue
        pred = ss["pred"].iloc[0]
        acc = (ss["pred"] == ss["modal"]).mean() * 100
        loss = ss["loss"].mean()
        print(f"  {mv:15s} pred={pred:5s} n={len(ss):4d} acc={acc:5.1f}% loss={loss:.4f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
