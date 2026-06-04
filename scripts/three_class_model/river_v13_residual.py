#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Residual analysis on river v13."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}


def river_v13(r):
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
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if is_dyn and mv in {"top_pair", "two_pair"}: return "CALL"
            return "FOLD"
        if bs == "med_100p": return "FOLD"
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
    sub["pred"] = sub.apply(river_v13, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_of(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]
    huge = sub[sub["ev_gap"] > 0.5].copy()
    mistakes = huge[huge["pred"] != huge["modal"]].copy()
    print(f"Total: {len(sub)} huge: {len(huge)} mistakes: {len(mistakes)}")
    print(f"acc huge: {(huge['pred']==huge['modal']).mean()*100:.1f}%")
    print(f"mean huge loss: {huge['loss'].mean():.4f} BB")

    keys = ["equity_bucket", "mv_cat", "bet_size", "board_family"]
    cells = mistakes.groupby(keys).agg(
        n=("loss", "count"),
        total=("loss", "sum"),
        mean_l=("loss", "mean"),
        actual=("modal", lambda x: x.mode().iat[0] if len(x) else "?"),
        pred=("pred", lambda x: x.mode().iat[0] if len(x) else "?"),
        fold_avg=("fold_freq", "mean"),
        call_avg=("call_freq", "mean"),
        raise_avg=("raise_freq", "mean"),
        eqp_avg=("eq_percentile", "mean"),
    ).reset_index().sort_values("total", ascending=False)

    print(f"\n=== Top remaining huge-mistake cells (river v13) ===")
    for _, r in cells.head(20).iterrows():
        dist = f"F:{r['fold_avg']*100:3.0f}%/C:{r['call_avg']*100:3.0f}%/R:{r['raise_avg']*100:3.0f}%"
        eqp_str = f"eqp={r['eqp_avg']:.2f}" if pd.notna(r["eqp_avg"]) else "eqp=NaN"
        print(f"  eb={r['equity_bucket']:13s} mv={r['mv_cat']:14s} bs={r['bet_size']:12s} bf={r['board_family']:18s}  n={int(r['n']):4d} {r['pred']:5s}→{r['actual']:5s} {dist} {eqp_str} mean={r['mean_l']:.3f} total={r['total']:6.1f}")

    cells["cum"] = cells["total"].cumsum() / cells["total"].sum() * 100
    if len(cells) >= 5: print(f"\nTop 5 = {cells.head(5)['cum'].iloc[-1]:.1f}%, top 10 = {cells.head(10)['cum'].iloc[-1] if len(cells)>=10 else 100:.1f}%")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
