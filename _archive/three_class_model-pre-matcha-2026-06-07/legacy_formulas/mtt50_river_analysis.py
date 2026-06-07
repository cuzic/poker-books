#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""MTT 50bb river defense detailed analysis."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}


def river_v14_cash(r):
    """Cash 100bb v14 baseline."""
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dyn = bf in DYNAMIC
    if mv == "quads": return "RAISE"
    if mv == "fullhouse" and bs not in {"overbet"}: return "RAISE"
    if mv == "fullhouse" and bs == "overbet": return "CALL"
    if bs == "allin":
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85: return "CALL"
        if bf in DRY and mv in {"set", "trips", "straight", "flush"}: return "CALL"
        if eb == "good_hands" and mv in {"straight", "flush", "trips"}: return "CALL"
        if bf == "monotone" and mv == "flush": return "CALL"
        if is_dyn and mv == "top_pair" and eb in {"weak_hands", "good_hands"}: return "CALL"
        return "FOLD"
    if mv in {"straight", "flush", "trips"}: return "CALL"
    if mv == "top_pair" and bf in DRY and bs in {"overbet", "med_100p"}: return "CALL"
    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96: return "RAISE"
        return "CALL"
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if is_dyn and mv in {"two_pair"}: return "CALL"
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


def mtt50_river_bs(s):
    """MTT 50bb river bet sizes from our fetch."""
    if "_R35" in s: return "allin"            # 235% pot all-in
    if "_R89" in s: return "allin"            # ultra all-in
    if "_R13" in s: return "med_100p"         # 100% pot
    if "_R16" in s: return "overbet"          # 75% (slightly bigger pot now)
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "river") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_mtt50_bb_river") &
              df["ev_call"].notna() & df["ev_fold"].notna() &
              df["mv_cat"].notna() & (df["mv_cat"] != "") &
              df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["bet_size"] = sub["source_path"].apply(mtt50_river_bs)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub = sub[sub["ev_gap"].notna()]

    print(f"=== MTT 50bb river defense: {len(sub)} rows ===")
    print(f"Bet size dist: {sub['bet_size'].value_counts().to_dict()}")
    print(f"Modal dist: {sub['modal'].value_counts(normalize=True).round(2).to_dict()}")
    print(f"Bucket dist: {sub['equity_bucket'].value_counts().to_dict()}")

    # Baselines
    print(f"\n=== Baselines ===")
    print(f"  always_FOLD loss: {(sub['best_ev'] - sub['ev_fold']).mean():.4f}BB")
    print(f"  always_CALL loss: {(sub['best_ev'] - sub['ev_call']).mean():.4f}BB")

    # Per bet_size breakdown
    print(f"\n=== Per bet_size ===")
    for bs_v, ss in sub.groupby("bet_size"):
        l_fold = (ss["best_ev"] - ss["ev_fold"]).mean()
        l_call = (ss["best_ev"] - ss["ev_call"]).mean()
        md = ss["modal"].value_counts(normalize=True).to_dict()
        mdstr = " ".join(f"{k}:{v*100:3.0f}%" for k, v in sorted(md.items()))
        print(f"  {bs_v:12s} n={len(ss):4d} F_loss={l_fold:.4f} C_loss={l_call:.4f}  {mdstr}")

    # Apply Cash v14
    sub["pred"] = sub.apply(river_v14_cash, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_of(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]
    acc = (sub["pred"] == sub["modal"]).mean() * 100
    huge = sub[sub["ev_gap"] > 0.5]
    print(f"\n=== Cash v14 on MTT 50bb river ===")
    print(f"  acc={acc:.1f}% mean={sub['loss'].mean():.4f}BB huge(n={len(huge)})={huge['loss'].mean():.4f}BB")

    # Top huge mistakes
    huge_m = huge[huge["pred"] != huge["modal"]].copy()
    if len(huge_m) > 0:
        keys = ["equity_bucket", "mv_cat", "bet_size", "board_family"]
        cells = huge_m.groupby(keys).agg(
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
        print(f"\n=== Top MTT 50bb river huge-mistake cells ===")
        for _, r in cells.head(20).iterrows():
            dist = f"F:{r['fold_avg']*100:3.0f}%/C:{r['call_avg']*100:3.0f}%/R:{r['raise_avg']*100:3.0f}%"
            print(f"  eb={r['equity_bucket']:13s} mv={r['mv_cat']:14s} bs={r['bet_size']:10s} bf={r['board_family']:18s}  n={int(r['n']):4d} {r['pred']:5s}→{r['actual']:5s} {dist} eqp={r['eqp_avg']:.2f} mean={r['mean_l']:.3f} total={r['total']:6.1f}")
        cells["cum"] = cells["total"].cumsum() / cells["total"].sum() * 100
        if len(cells) >= 5: print(f"\nTop 5 = {cells.head(5)['cum'].iloc[-1]:.1f}%, top 10 = {cells.head(10)['cum'].iloc[-1] if len(cells)>=10 else 100:.1f}%")

    # Per (bucket × bet_size)
    print(f"\n=== Modal per (bucket × bet_size) ===")
    for (eb, bs_v), ss in sub.groupby(["equity_bucket", "bet_size"]):
        if len(ss) < 50: continue
        md = ss["modal"].value_counts(normalize=True).to_dict()
        mdstr = " ".join(f"{k}:{v*100:3.0f}%" for k, v in sorted(md.items()))
        pred = ss["pred"].iloc[0]
        acc = (ss["pred"] == ss["modal"]).mean() * 100
        print(f"  {eb:13s} × {bs_v:12s} n={len(ss):4d} pred={pred:5s} acc={acc:5.1f}%  {mdstr}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
