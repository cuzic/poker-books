#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""River defense v9 — dynamic-board aware rules."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


AIR = {"no_made_hand", "ace_high", "king_high"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}


def river_v8(r):
    mv = r["mv_cat"]; bs = r["bet_size"]
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if mv in AIR: return "FOLD"
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
    if mv == "second_pair": return "FOLD" if bs == "overbet" else "CALL"
    if mv == "two_pair": return "FOLD" if bs == "overbet" else "CALL"
    if mv == "top_pair": return "FOLD" if bs == "overbet" else "CALL"
    return "CALL"


def river_v9(r):
    """v9 with corrected bet_size: handle allin separately."""
    mv = r["mv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    is_dynamic = bf in DYNAMIC
    is_big = bs in {"overbet", "allin", "med_100p"}

    if mv in {"fullhouse", "quads"}: return "RAISE"

    # vs all-in (>200% pot): nutted-only call
    if bs == "allin":
        if mv in {"set", "trips", "straight", "flush"}: return "CALL"
        return "FOLD"

    # Rule A: dry + TP + overbet → CALL
    if bf in DRY and mv == "top_pair" and bs == "overbet":
        return "CALL"

    # Rule B: dynamic + 2P/TP/2nd_pair + med_100p → FOLD
    if is_dynamic and mv in {"top_pair", "two_pair", "second_pair"} and bs == "med_100p":
        return "FOLD"

    # Default v8 logic
    if mv in AIR: return "FOLD"
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
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


def river_bs(s):
    # Order matters — check most specific first
    if "_R89" in s: return "allin"        # 421% pot all-in
    if "_R16" in s: return "overbet"      # ~75% pot (because pot grows on river)
    if "_R13" in s: return "med_100p"     # 100% pot
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"     # 20-30% pot
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
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub["bet_size"] = sub["source_path"].apply(river_bs)
    sub = sub[sub["ev_gap"].notna()]

    for label, f in [("v8 baseline", river_v8), ("v9 dynamic-aware", river_v9)]:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {label:25s} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")

    # ── Per (board_family × bet_size) breakdown ──
    print(f"\n=== Per (board × bet_size) ===")
    s = sub.copy()
    s["pred_v8"] = s.apply(river_v8, axis=1)
    s["pred_v9"] = s.apply(river_v9, axis=1)
    s["loss_v8"] = s["best_ev"] - s.apply(lambda r: ev_of(r, r["pred_v8"]), axis=1)
    s["loss_v9"] = s["best_ev"] - s.apply(lambda r: ev_of(r, r["pred_v9"]), axis=1)
    for (bf, bs_v), ss in s.groupby(["board_family", "bet_size"]):
        if len(ss) < 50: continue
        l8 = ss["loss_v8"].mean()
        l9 = ss["loss_v9"].mean()
        print(f"  {bf:18s} × {bs_v:12s} n={len(ss):5d}  v8={l8:.3f}  v9={l9:.3f}  Δ={l9-l8:+.3f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
