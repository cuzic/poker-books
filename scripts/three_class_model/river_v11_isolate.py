#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Test each river v11 rule individually starting from v9 baseline."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


AIR = {"no_made_hand", "ace_high", "king_high"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}


def v9(r):
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


def v9_rule1(r):
    """v9 + Rule X4 only: dynamic + no_made + med_100p → CALL."""
    bf = r["board_family"]; is_dynamic = bf in DYNAMIC
    if is_dynamic and r["mv_cat"] == "no_made_hand" and r["bet_size"] == "med_100p":
        return "CALL"
    return v9(r)


def v9_rule2(r):
    """v9 + Rule X2: dynamic + straight + overbet → RAISE."""
    bf = r["board_family"]; is_dynamic = bf in DYNAMIC
    if is_dynamic and r["mv_cat"] == "straight" and r["bet_size"] == "overbet":
        return "RAISE"
    return v9(r)


def v9_rule3(r):
    """v9 + dynamic allin → only flush calls."""
    bf = r["board_family"]; is_dynamic = bf in DYNAMIC
    if r["bet_size"] == "allin" and is_dynamic:
        if r["mv_cat"] in {"flush", "straight_flush"}: return "CALL"
        if r["mv_cat"] in {"fullhouse", "quads"}: return "RAISE"
        return "FOLD"
    return v9(r)


def v9_rule4(r):
    """v9 + Rule X3: dynamic + 2P + overbet → CALL."""
    bf = r["board_family"]; is_dynamic = bf in DYNAMIC
    if is_dynamic and r["mv_cat"] == "two_pair" and r["bet_size"] == "overbet":
        return "CALL"
    return v9(r)


def best_ev(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_gap(r):
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
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(river_bs)
    sub["ev_gap"] = sub.apply(ev_gap, axis=1)
    sub = sub[sub["ev_gap"].notna()]

    print(f"Total rows: {len(sub)}")
    for label, f in [
        ("v9 baseline", v9),
        ("v9+R1 (no_made+100p)", v9_rule1),
        ("v9+R2 (straight+overbet)", v9_rule2),
        ("v9+R3 (allin dyn tight)", v9_rule3),
        ("v9+R4 (2P+overbet)", v9_rule4),
    ]:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:30s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge={huge_l:.4f}BB")

    # Combined: v9 + R1 + R2 + R3 only (skip R4 if hurts)
    def v9_combined(r):
        bf = r["board_family"]; is_dynamic = bf in DYNAMIC
        bs = r["bet_size"]; mv = r["mv_cat"]
        # Apply rules in order
        if is_dynamic and mv == "no_made_hand" and bs == "med_100p": return "CALL"
        if is_dynamic and mv == "straight" and bs == "overbet": return "RAISE"
        if bs == "allin" and is_dynamic:
            if mv in {"flush", "straight_flush"}: return "CALL"
            if mv in {"fullhouse", "quads"}: return "RAISE"
            return "FOLD"
        return v9(r)

    print(f"\n--- combined ---")
    s = sub.copy()
    s["pred"] = s.apply(v9_combined, axis=1)
    s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
    s["loss"] = s["best_ev"] - s["ev_p"]
    acc = (s["pred"] == s["modal"]).mean() * 100
    mean_l = s["loss"].mean()
    huge = s[s["ev_gap"] > 0.5]
    huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
    print(f"  v9+R1+R2+R3 (no R4): acc={acc:5.1f}% mean={mean_l:.4f}BB huge={huge_l:.4f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
