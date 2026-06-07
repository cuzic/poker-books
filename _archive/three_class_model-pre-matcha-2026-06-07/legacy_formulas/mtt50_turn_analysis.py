#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""MTT 50bb turn defense detailed analysis.

MTT 50bb solver uses bimodal turn cbet sizes:
  - R2.3 (~25% pot) — small block bet
  - R10.6 (~117% pot) — overbet / commit

Derive MTT-specific turn defense formula and compare to Cash v8.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
WEAK_DRAWS = {"no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot"}


def mtt50_turn_bs(s):
    """MTT 50bb bet size categorization."""
    if "_R2." in s: return "small_25p"
    if "_R10" in s: return "overbet_117p"
    return "other"


def cash_turn_v8(r):
    """Cash-tuned v8 (current best on Cash 100bb)."""
    mv = r["mv_cat"]; dv = r["dv_cat"]; bs = r["bet_size"]; bf = r["board_family"]
    weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
    is_dynamic = bf in DYNAMIC
    # Adapt bs naming
    if bs in {"overbet_185p", "overbet_117p"}:
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


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_mtt50_bb_turn") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(mtt50_turn_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]

    print(f"=== MTT 50bb turn defense: {len(sub)} rows ===")
    print(f"Bet size distribution: {sub['bet_size'].value_counts().to_dict()}")
    print(f"Modal distribution: {sub['modal'].value_counts(normalize=True).round(2).to_dict()}")

    # Per bet_size baselines
    print(f"\n=== Per bet_size baselines (always_FOLD vs always_CALL) ===")
    for bs_v, ss in sub.groupby("bet_size"):
        l_fold = (ss["best_ev"] - ss["ev_fold"]).mean()
        l_call = (ss["best_ev"] - ss["ev_call"]).mean()
        modal_dist = ss["modal"].value_counts(normalize=True).to_dict()
        modal_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(modal_dist.items()))
        print(f"  {bs_v}: n={len(ss)} F_loss={l_fold:.4f} C_loss={l_call:.4f}  modal={modal_str}")

    # Apply Cash v8 to MTT data
    print(f"\n=== Cash v8 applied to MTT 50bb ===")
    sub["pred_v8"] = sub.apply(cash_turn_v8, axis=1)
    sub["ev_v8"] = sub.apply(lambda r: ev_of(r, r["pred_v8"]), axis=1)
    sub["loss_v8"] = sub["best_ev"] - sub["ev_v8"]
    acc = (sub["pred_v8"] == sub["modal"]).mean() * 100
    huge = sub[sub["ev_gap"] > 0.5]
    print(f"  acc={acc:.1f}% mean={sub['loss_v8'].mean():.4f}BB huge(n={len(huge)})={huge['loss_v8'].mean():.4f}BB")

    # Cross-tab pred vs modal
    print(f"\nConfusion matrix (pred row × modal col):")
    print(pd.crosstab(sub["pred_v8"], sub["modal"]))

    # Per (mv × dv × bet_size × board) — find biggest huge_loss cells
    huge_m = huge[huge["pred_v8"] != huge["modal"]].copy()
    if len(huge_m) > 0:
        keys = ["mv_cat", "dv_cat", "bet_size", "board_family"]
        cells = huge_m.groupby(keys).agg(
            n=("loss_v8", "count"),
            total=("loss_v8", "sum"),
            mean_l=("loss_v8", "mean"),
            actual=("modal", lambda x: x.mode().iat[0] if len(x) else "?"),
            pred=("pred_v8", lambda x: x.mode().iat[0] if len(x) else "?"),
            fold_avg=("fold_freq", "mean"),
            call_avg=("call_freq", "mean"),
            raise_avg=("raise_freq", "mean"),
        ).reset_index().sort_values("total", ascending=False)
        print(f"\n=== Top MTT 50bb v8 huge-mistake cells ===")
        for _, r in cells.head(25).iterrows():
            dist = f"F:{r['fold_avg']*100:3.0f}%/C:{r['call_avg']*100:3.0f}%/R:{r['raise_avg']*100:3.0f}%"
            print(f"  mv={r['mv_cat']:14s} dv={r['dv_cat']:18s} bs={r['bet_size']:14s} bf={r['board_family']:18s}  n={int(r['n']):4d} {r['pred']:5s}→{r['actual']:5s} {dist} mean={r['mean_l']:.3f} total={r['total']:6.1f}")
        cells["cum"] = cells["total"].cumsum() / cells["total"].sum() * 100
        if len(cells) >= 5: print(f"\nTop 5 = {cells.head(5)['cum'].iloc[-1]:.1f}%, top 10 = {cells.head(10)['cum'].iloc[-1] if len(cells)>=10 else 100:.1f}%")

    # Per (mv × bet_size) distribution
    print(f"\n=== Modal distribution per (mv × bet_size) ===")
    for (mv, bs_v), ss in sub.groupby(["mv_cat", "bet_size"]):
        if len(ss) < 30: continue
        modal_dist = ss["modal"].value_counts(normalize=True).to_dict()
        modal_str = " ".join(f"{k}:{v*100:3.0f}%" for k, v in sorted(modal_dist.items()))
        pred = ss["pred_v8"].iloc[0]
        acc = (ss["pred_v8"] == ss["modal"]).mean() * 100
        print(f"  {mv:14s} × {bs_v:14s}  n={len(ss):4d}  pred={pred:5s} acc={acc:5.1f}% actual={modal_str}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
