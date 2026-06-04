#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Find residual huge_loss cells in turn v6 and river v9."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
WEAK_PAIR_MID = {"second_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}


def turn_v6(r):
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID
    weak_no_draw = dv in {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}
    if bs == "overbet_185p":
        if weak_mv and weak_no_draw: return "FOLD"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
    return "CALL"


def river_v9(r):
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


def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of_def(r, p):
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


def river_bs(s):
    if "_R89" in s: return "allin"
    if "_R16" in s: return "overbet"
    if "_R13" in s: return "med_100p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


def analyze(df, street, pred_fn, bs_fn, label):
    sub = df[(df["street"] == street) & (df["action_context"] == "defense") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["bet_size"] = sub["source_path"].apply(bs_fn)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]
    sub["pred"] = sub.apply(pred_fn, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]

    print(f"\n{'='*78}\n=== {label} ===\n{'='*78}")
    print(f"Rows: {len(sub)}, huge_gap rows: {len(sub[sub['ev_gap']>0.5])}")
    huge = sub[sub["ev_gap"] > 0.5].copy()
    mistakes = huge[huge["pred"] != huge["modal"]].copy()
    print(f"  Modal acc on huge: {(huge['pred']==huge['modal']).mean()*100:.1f}%")
    print(f"  Mean huge loss: {huge['loss'].mean():.4f}BB")
    print(f"  Mistake-only mean loss: {mistakes['loss'].mean() if len(mistakes) else 0:.4f}BB")

    keys = ["mv_cat", "dv_cat", "bet_size", "board_family"]
    cells = mistakes.groupby(keys).agg(
        n=("loss", "count"),
        total=("loss", "sum"),
        mean_l=("loss", "mean"),
        actual=("modal", lambda x: x.mode().iat[0] if len(x) else "?"),
        pred=("pred", lambda x: x.mode().iat[0] if len(x) else "?"),
    ).reset_index().sort_values("total", ascending=False)

    print(f"\n=== Top residual huge-mistake cells ===")
    for _, r in cells.head(20).iterrows():
        print(f"  mv={r['mv_cat']:14s} dv={r['dv_cat']:18s} bs={r['bet_size']:14s} bf={r['board_family']:18s}  n={int(r['n']):4d} {r['pred']:5s}→{r['actual']:5s} mean={r['mean_l']:.3f} total={r['total']:7.1f}")
    cells["cum"] = cells["total"].cumsum() / cells["total"].sum() * 100
    if len(cells) >= 5: print(f"\nTop 5 cells = {cells.head(5)['cum'].iloc[-1]:.1f}% of huge loss")
    if len(cells) >= 10: print(f"Top 10 cells = {cells.head(10)['cum'].iloc[-1]:.1f}% of huge loss")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    analyze(df, "turn", turn_v6, turn_bs, "TURN DEFENSE v6 — residual")
    analyze(df, "river", river_v9, river_bs, "RIVER DEFENSE v9 — residual")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
