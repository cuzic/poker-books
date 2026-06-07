#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""River defense huge-gap analysis — find top loss cells."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}


def river_v8(r):
    mv = r["mv_cat"]; bs = r["bet_size"]
    if mv in {"fullhouse", "quads"}: return "RAISE"
    if mv in AIR: return "FOLD"
    if mv in {"low_pair", "underpair", "third_pair"}: return "FOLD"
    if mv == "second_pair":
        return "FOLD" if bs == "overbet" else "CALL"
    if mv == "two_pair":
        return "FOLD" if bs == "overbet" else "CALL"
    if mv == "top_pair":
        return "FOLD" if bs == "overbet" else "CALL"
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
    if "_R4" in s: return "small_30p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R13" in s: return "med_100p"
    if "_R16" in s: return "overbet"
    if "_R89" in s: return "allin"
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

    sub["pred"] = sub.apply(river_v8, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_of(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]

    print(f"River defense rows: {len(sub)}")
    print(f"Modal dist: {sub['modal'].value_counts(normalize=True).round(2).to_dict()}")

    huge = sub[sub["ev_gap"] > 0.5].copy()
    mistakes = huge[huge["pred"] != huge["modal"]].copy()
    print(f"\nhuge_gap n={len(huge)}, mistakes n={len(mistakes)}")

    # Top mistake cells
    keys = ["mv_cat", "bet_size", "board_family"]
    cells = mistakes.groupby(keys).agg(
        n=("loss", "count"),
        total=("loss", "sum"),
        mean_l=("loss", "mean"),
        actual=("modal", lambda x: x.mode().iat[0] if len(x) else "?"),
        pred=("pred", lambda x: x.mode().iat[0] if len(x) else "?"),
    ).reset_index().sort_values("total", ascending=False)

    print(f"\n=== Top huge-mistake cells (river defense) ===")
    print(f"{'mv':16s} {'bet_size':12s} {'board':18s}  n     pred→actual  mean_loss  total_BB")
    for _, r in cells.head(25).iterrows():
        print(f"  {r['mv_cat']:14s} {r['bet_size']:12s} {r['board_family']:18s}  n={int(r['n']):4d} {r['pred']:5s}→{r['actual']:5s}  {r['mean_l']:.3f}    {r['total']:7.1f}")

    cells["cum"] = cells["total"].cumsum() / cells["total"].sum() * 100
    if len(cells) >= 5: print(f"\nTop 5 cells: {cells.head(5)['cum'].iloc[-1]:.1f}% of huge loss")
    if len(cells) >= 10: print(f"Top 10 cells: {cells.head(10)['cum'].iloc[-1]:.1f}% of huge loss")

    # Per (mv, bet_size) — what's the modal distribution?
    print(f"\n=== Modal dist per (mv × bet_size) ===")
    g = sub.groupby(["mv_cat", "bet_size"])
    for (mv, bs), ss in g:
        if len(ss) < 20: continue
        mod = ss["modal"].value_counts(normalize=True).to_dict()
        modstr = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(mod.items()))
        pred = ss["pred"].iloc[0]
        l = ss["loss"].mean()
        marker = "✓" if (ss["pred"] == ss["modal"]).mean() > 0.7 else "✗"
        print(f"  {marker} {mv:14s} × {bs:12s} n={len(ss):4d}  pred={pred:5s} loss={l:.3f}  actual={modstr}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
