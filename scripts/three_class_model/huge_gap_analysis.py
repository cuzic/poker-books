#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Huge-gap analysis — find the few specific cells where each formula loses BIG.

For each street + context, filter rows where ev_gap > 0.50 BB (huge),
then break down by mv_cat × dv_cat × bet_size to find where the
formula's prediction diverges from optimal.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


MV = {
    "no_made_hand": 0, "king_high": 0, "ace_high": 0,
    "low_pair": 1, "underpair": 1, "third_pair": 1, "second_pair": 1,
    "top_pair": 2, "overpair": 3,
    "two_pair": 4, "set": 4, "trips": 4,
    "straight": 5, "flush": 5, "fullhouse": 5, "quads": 5,
}
DV = {
    "no_draw": 0, "twocards_bdfd": 0, "onecard_bdfd": 0, "gutshot": 0,
    "oesd": 1, "flush_draw": 1, "nut_flush_draw": 1,
    "combo_draw": 2,
}


def ev_gap(r):
    evs = [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise"), r.get("ev_bet"), r.get("ev_check")]
    evs = sorted([e for e in evs if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def flop_defense_pred(r):
    bucket = r["bucket_s"]
    mv = r["mv_s"]
    dv = r["dv_s"]
    if bucket <= 1 and mv == 0 and dv == 0: return "FOLD"
    if bucket >= 3 and mv >= 3: return "RAISE"
    return "CALL"


def turn_defense_pred(r):
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bs = r["bet_size"]
    weak_mv = mv in {"no_made_hand", "ace_high", "king_high", "low_pair", "underpair"}
    weakish = mv in {"third_pair", "second_pair"}
    no_draw = dv == "no_draw"
    if bs == "overbet_185p":
        if (weak_mv or weakish) and no_draw: return "FOLD"
    else:
        if weak_mv and no_draw: return "FOLD"
    return "CALL"


def river_attack_pred(r):
    mv = r["mv_cat"]
    VALUE = {"top_pair", "overpair", "two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
    BLUFF = {"no_made_hand", "king_high"}
    if mv in VALUE or mv in BLUFF: return "BET"
    return "CHECK"


def loss_per_row(r, pred):
    """How much EV is lost by picking pred vs best_ev."""
    if pred == "FOLD": return r["best_ev"] - r["ev_fold"]
    if pred == "CALL": return r["best_ev"] - r["ev_call"]
    if pred == "RAISE":
        return r["best_ev"] - (r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"])
    if pred == "BET": return r["best_ev"] - r["ev_bet"]
    if pred == "CHECK": return r["best_ev"] - r["ev_check"]
    return 0


def analyze_street(df, street, context, pred_fn, label):
    print(f"\n{'='*78}\n=== {label} HUGE-GAP ANALYSIS ===\n{'='*78}")
    sub = df[(df["street"] == street) & (df["action_context"] == context)].copy()
    if context == "defense":
        sub = sub[sub["ev_call"].notna() & sub["ev_fold"].notna()]
    else:
        sub = sub[sub["ev_bet"].notna() & sub["ev_check"].notna()]
    if len(sub) == 0:
        print("No data")
        return
    for c in ["fold_freq", "call_freq", "raise_freq", "bet_freq", "check_freq"]:
        if c in sub.columns:
            sub[c] = sub[c].fillna(0)
    if context == "defense":
        sub["best_ev"] = sub[["ev_fold", "ev_call", "ev_raise"]].max(axis=1)
        sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    else:
        sub["best_ev"] = sub[["ev_bet", "ev_check"]].max(axis=1)
        sub["modal"] = (sub["bet_freq"] >= 0.5).map({True: "BET", False: "CHECK"})

    sub["mv_s"] = sub["mv_cat"].map(MV).fillna(0).astype(int)
    sub["dv_s"] = sub["dv_cat"].map(DV).fillna(0).astype(int)
    if "eq_percentile" in sub.columns and sub["eq_percentile"].notna().mean() > 0.5:
        sub["bucket_s"] = pd.cut(sub["eq_percentile"], bins=[-0.01, 0.25, 0.5, 0.75, 1.01],
                                  labels=[0, 1, 2, 3]).cat.codes.clip(lower=0)
    else:
        sub["bucket_s"] = sub["mv_s"].clip(0, 3)

    # Need bet_size for turn
    if street == "turn":
        sub["bet_size"] = sub["source_path"].apply(lambda s:
            "small_25p" if "_R2." in s else
            "med_67p" if "_R6." in s else
            "overbet_185p" if "_R16" in s else "other")

    sub["ev_gap"] = sub.apply(ev_gap, axis=1)
    sub = sub[sub["ev_gap"].notna()].copy()
    sub["pred"] = sub.apply(pred_fn, axis=1)
    sub["loss"] = sub.apply(lambda r: loss_per_row(r, r["pred"]), axis=1)

    huge = sub[sub["ev_gap"] > 0.50].copy()
    huge_mistake = huge[huge["pred"] != huge["modal"]].copy()
    print(f"\nTotal rows: {len(sub)},  huge_gap rows: {len(huge)},  huge mistakes: {len(huge_mistake)}")
    print(f"huge mistake rate: {len(huge_mistake)/max(len(huge),1)*100:.1f}%")
    print(f"huge mean_loss (all): {huge['loss'].mean():.4f} BB")
    print(f"huge mean_loss (mistakes only): {huge_mistake['loss'].mean() if len(huge_mistake)>0 else 0:.4f} BB")

    # Top mistake cells — group by (mv_cat, dv_cat) and optionally bet_size
    keys = ["mv_cat", "dv_cat"]
    if "bet_size" in huge_mistake.columns:
        keys.append("bet_size")
    keys.append("board_family")

    if len(huge_mistake) == 0:
        print("\nNo huge_mistakes — formula optimal in huge gap region!")
        return

    cells = huge_mistake.groupby(keys).agg(
        n=("loss", "count"),
        total_lost=("loss", "sum"),
        mean_loss=("loss", "mean"),
        actual_modal=("modal", lambda x: x.mode().iat[0] if len(x) else "?"),
        predicted=("pred", lambda x: x.mode().iat[0] if len(x) else "?"),
    ).reset_index().sort_values("total_lost", ascending=False)

    print(f"\n=== TOP huge-mistake cells by total BB lost ===")
    print(f"{' × '.join(k for k in keys)}  |  n     pred → actual    mean_loss   total_lost_BB")
    for _, r in cells.head(20).iterrows():
        key_str = " × ".join(str(r[k])[:13] for k in keys)
        print(f"  {key_str:60s}  n={int(r['n']):4d}  {r['predicted']:5s}→{r['actual_modal']:5s}  {r['mean_loss']:.3f} BB  total={r['total_lost']:7.1f} BB")

    # What % of total huge loss is concentrated in top N cells?
    cells["cum_pct"] = cells["total_lost"].cumsum() / cells["total_lost"].sum() * 100
    print(f"\nTop 5 cells account for {cells.head(5)['cum_pct'].iloc[-1] if len(cells)>=5 else 100:.1f}% of huge loss")
    print(f"Top 10 cells account for {cells.head(10)['cum_pct'].iloc[-1] if len(cells)>=10 else 100:.1f}% of huge loss")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    analyze_street(df, "flop", "defense", flop_defense_pred, "FLOP DEFENSE")
    analyze_street(df, "turn", "defense", turn_defense_pred, "TURN DEFENSE")
    analyze_street(df, "river", "attack", river_attack_pred, "RIVER ATTACK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
