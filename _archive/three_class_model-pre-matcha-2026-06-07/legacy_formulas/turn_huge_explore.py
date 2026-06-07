#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""turn_huge_explore.py — Turn defense huge_gap の真の集中地を探る。

v8 適用後の残存 huge_gap を mv × dv × board × bet_size の cross-tab で深掘り。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}


def turn_bet_size(s):
    if "_R4" in s or "_R5" in s or "_R6" in s: return "small_33"
    if "_R7" in s or "_R8" in s or "_R9" in s: return "med_67"
    if "_R13" in s or "_R14" in s: return "big_100"
    if "_R16" in s or "_R17" in s or "_R19" in s: return "overbet_185"
    return "other"


def turn_def_v8(r):
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
    weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
    if bs == "overbet_185":
        if weak_mv and weak_no_draw: return "FOLD"
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw": return "FOLD"
        if mv in AIR and dv in {"flush_draw", "nut_flush_draw"} and bf == "dry_high": return "FOLD"
        if mv in AIR and dv == "oesd" and bf in DYNAMIC_BOARDS: return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
        if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW: return "FOLD"
        if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p: return "FOLD"
        return "CALL"


def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of_def(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    if p == "RAISE": return r["ev_raise"]


def ev_gap_row(r):
    evs = [e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)]
    if len(evs) < 2: return None
    s = sorted(evs, reverse=True)
    return s[0] - s[1]


def main():
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
             df["ev_call"].notna() & df["ev_fold"].notna() & df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub["bet_size"] = sub["source_path"].apply(turn_bet_size)
    sub = sub[sub["ev_gap"].notna()]
    sub["v8_pred"] = sub.apply(turn_def_v8, axis=1)
    sub["v8_loss"] = sub.apply(lambda r: best_ev_def(r) - ev_of_def(r, turn_def_v8(r)), axis=1)

    huge = sub[sub["ev_gap"] > 0.5]
    print(f"全 huge_gap rows: {len(huge):,}, v8 total_loss: {huge['v8_loss'].sum():.1f}BB")

    # 1) mv × bet_size の v8 残存 huge loss
    print("\n▼ mv_cat × bet_size 別の v8 残存 huge_loss (上位 15)")
    g = huge.groupby(["mv_cat", "bet_size"]).agg(n=("v8_loss", "size"), mean_loss=("v8_loss", "mean"), total=("v8_loss", "sum")).reset_index()
    g = g.sort_values("total", ascending=False).head(15)
    print(f"{'mv_cat':14s} {'bet_size':14s} {'n':>5s} {'mean_loss':>10s} {'total_loss':>11s}")
    for _, r in g.iterrows():
        print(f"{r['mv_cat']:14s} {r['bet_size']:14s} {r['n']:>5} {r['mean_loss']:>9.3f}BB {r['total']:>10.1f}BB")

    # 2) mv × dv × board × bet_size の細粒度
    print("\n▼ mv × dv × board × bet_size 別の huge_loss (上位 15)")
    g2 = huge.groupby(["mv_cat", "dv_cat", "board_family", "bet_size"]).agg(n=("v8_loss", "size"), mean_loss=("v8_loss", "mean"), total=("v8_loss", "sum"), gto_F=("fold_freq", "mean"), gto_C=("call_freq", "mean"), v8=("v8_pred", "first")).reset_index()
    g2 = g2.sort_values("total", ascending=False).head(20)
    print(f"{'mv':12s} {'dv':14s} {'board':16s} {'bs':14s} {'n':>5s} {'gto_F%':>7s} {'gto_C%':>7s} {'v8':>5s} {'mean_loss':>10s}")
    for _, r in g2.iterrows():
        print(f"{r['mv_cat']:12s} {r['dv_cat']:14s} {r['board_family']:16s} {r['bet_size']:14s} {r['n']:>5} {r['gto_F']*100:>6.0f}% {r['gto_C']*100:>6.0f}% {r['v8']:>5s} {r['mean_loss']:>9.3f}BB")

    # 3) Where v8 mispredicts most
    mispred = huge[huge["v8_pred"] != huge["modal"]]
    print(f"\n▼ v8 が GTO modal と違う huge_gap rows: {len(mispred):,}")
    g3 = mispred.groupby(["mv_cat", "dv_cat", "board_family", "bet_size"]).agg(n=("v8_loss", "size"), mean_loss=("v8_loss", "mean"), total=("v8_loss", "sum"), gto_F=("fold_freq", "mean"), gto_C=("call_freq", "mean"), v8=("v8_pred", "first"), modal=("modal", "first")).reset_index()
    g3 = g3.sort_values("total", ascending=False).head(15)
    print(f"{'mv':12s} {'dv':14s} {'board':16s} {'bs':14s} {'n':>5s} {'gto_F%':>7s} {'gto_C%':>7s} {'v8':>5s} {'modal':>6s} {'loss':>8s}")
    for _, r in g3.iterrows():
        print(f"{r['mv_cat']:12s} {r['dv_cat']:14s} {r['board_family']:16s} {r['bet_size']:14s} {r['n']:>5} {r['gto_F']*100:>6.0f}% {r['gto_C']*100:>6.0f}% {r['v8']:>5s} {r['modal']:>6s} {r['mean_loss']:>7.3f}BB")


if __name__ == "__main__":
    raise SystemExit(main())
