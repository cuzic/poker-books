#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Residual on turn v8."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
WEAK_PAIR_MID = {"second_pair"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}


def turn_v8(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
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
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(turn_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    sub["pred"] = sub.apply(turn_v8, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_of(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]
    huge = sub[sub["ev_gap"] > 0.5].copy()
    mistakes = huge[huge["pred"] != huge["modal"]].copy()
    print(f"Total: {len(sub)} huge: {len(huge)} mistakes: {len(mistakes)}")
    print(f"acc huge: {(huge['pred']==huge['modal']).mean()*100:.1f}%")
    print(f"mean huge loss: {huge['loss'].mean():.4f} BB")

    keys = ["mv_cat", "dv_cat", "bet_size", "board_family"]
    cells = mistakes.groupby(keys).agg(
        n=("loss", "count"),
        total=("loss", "sum"),
        mean_l=("loss", "mean"),
        actual=("modal", lambda x: x.mode().iat[0] if len(x) else "?"),
        pred=("pred", lambda x: x.mode().iat[0] if len(x) else "?"),
        fold_avg=("fold_freq", "mean"),
        call_avg=("call_freq", "mean"),
        raise_avg=("raise_freq", "mean"),
    ).reset_index().sort_values("total", ascending=False)

    print(f"\n=== Top remaining mistakes (turn v8) ===")
    for _, r in cells.head(15).iterrows():
        dist = f"F:{r['fold_avg']*100:3.0f}%/C:{r['call_avg']*100:3.0f}%/R:{r['raise_avg']*100:3.0f}%"
        print(f"  mv={r['mv_cat']:14s} dv={r['dv_cat']:18s} bs={r['bet_size']:14s} bf={r['board_family']:18s}  n={int(r['n']):4d} {r['pred']:5s}→{r['actual']:5s} {dist} mean={r['mean_l']:.3f} total={r['total']:6.1f}")
    cells["cum"] = cells["total"].cumsum() / cells["total"].sum() * 100
    if len(cells) >= 5: print(f"\nTop 5 = {cells.head(5)['cum'].iloc[-1]:.1f}%, top 10 = {cells.head(10)['cum'].iloc[-1] if len(cells)>=10 else 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
