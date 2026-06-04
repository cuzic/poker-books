#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Defense formula v3: cleanest possible memorizable form.

Compare:
  A. Bucket-only:  FOLD if trash else CALL
  B. v2 formula:   score = 2·bucket + mv + dv;  <2→FOLD, ≥2→CALL, ≥6→RAISE
  C. v2 with explicit RAISE at score≥6 for best bucket only
  D. Bucket + best→RAISE (simplest with RAISE)

Goal: maximize EV at high-gap decisions while keeping rule memorizable.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


BUCKET = {"trash_hands": 0, "weak_hands": 1, "good_hands": 2, "best_hands": 3}
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


def eval_strategy(df: pd.DataFrame, pred_col: str, name: str):
    df = df.copy()
    def ev_chosen(r):
        if r[pred_col] == "FOLD": return r["ev_fold"]
        if r[pred_col] == "CALL": return r["ev_call"]
        return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]
    df["ev_pred"] = df.apply(ev_chosen, axis=1)
    df["loss"] = df["best_ev"] - df["ev_pred"]
    acc = (df[pred_col] == df["modal"]).mean() * 100
    loss = df["loss"].mean()
    print(f"  {name:35s} acc={acc:5.1f}% mean_loss={loss:.4f}BB")
    # huge-gap breakdown
    huge = df[df["ev_gap"] > 0.50]
    if len(huge) > 0:
        print(f"  {'':35s}   huge-gap (n={len(huge):5d}): loss={huge['loss'].mean():.4f}BB")
    return df["loss"], (df[pred_col] == df["modal"])


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    df = df[(df["action_context"] == "defense") &
            (df["ev_call"].notna()) & (df["ev_fold"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        df[c] = df[c].fillna(0)
    df["modal"] = df[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    df["bucket_s"] = df["equity_bucket"].map(BUCKET).fillna(1).astype(int)
    df["mv_s"] = df["mv_cat"].map(MV).fillna(0).astype(int)
    df["dv_s"] = df["dv_cat"].map(DV).fillna(0).astype(int)
    df["best_ev"] = df[["ev_fold", "ev_call", "ev_raise"]].max(axis=1)

    def gap(r):
        evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
        return evs[0] - evs[1] if len(evs) >= 2 else None
    df["ev_gap"] = df.apply(gap, axis=1)
    df = df[df["ev_gap"].notna()].copy()
    print(f"Defense rows: {len(df)}\n")

    # ── Strategy A: bucket only ──
    df["pred_A"] = np.where(df["bucket_s"] == 0, "FOLD", "CALL")
    # ── Strategy B: score-based (v2 best) ──
    df["score"] = 2*df["bucket_s"] + df["mv_s"] + df["dv_s"]
    df["pred_B"] = np.where(df["score"] < 2, "FOLD",
                    np.where(df["score"] < 13, "CALL", "RAISE"))
    # ── Strategy C: with RAISE at score ≥ 6 ──
    df["pred_C"] = np.where(df["score"] < 2, "FOLD",
                    np.where(df["score"] < 6, "CALL", "RAISE"))
    # ── Strategy D: bucket only + best→RAISE if overpair+ ──
    df["pred_D"] = np.where(df["bucket_s"] == 0, "FOLD",
                    np.where((df["bucket_s"] == 3) & (df["mv_s"] >= 3), "RAISE", "CALL"))
    # ── Strategy E: refined — FOLD trash AND no draw; CALL everything else; RAISE if 2P+ ──
    df["pred_E"] = np.where((df["bucket_s"] == 0) & (df["dv_s"] == 0), "FOLD",
                    np.where(df["mv_s"] >= 4, "RAISE", "CALL"))
    # ── Strategy F: weighted bucket more — best→RAISE if MV≥3, weak with mv=0+dv=0→FOLD ──
    df["pred_F"] = np.where((df["bucket_s"] <= 1) & (df["mv_s"] == 0) & (df["dv_s"] == 0), "FOLD",
                    np.where((df["bucket_s"] >= 3) & (df["mv_s"] >= 3), "RAISE", "CALL"))

    print(f"=== Strategy comparison ===")
    for name, col in [("A: Bucket only (trash→FOLD)", "pred_A"),
                       ("B: 2·B + MV + DV (no RAISE)", "pred_B"),
                       ("C: B + RAISE if score≥6", "pred_C"),
                       ("D: Bucket + best+OP→RAISE", "pred_D"),
                       ("E: trash∧no_dv→F; 2P+→R", "pred_E"),
                       ("F: weak∧no_md_dv→F; best∧OP→R", "pred_F")]:
        eval_strategy(df, col, name)

    # ── Baseline: Oracle, always-CALL ──
    print(f"\n=== Baselines ===")
    print(f"  {'Always CALL':35s} loss={(df['best_ev'] - df['ev_call']).mean():.4f}BB")
    print(f"  {'Oracle (max)':35s} loss=0.0000BB (by definition)")

    # ── Per-gap detail for E and F ──
    print(f"\n=== Per ev_gap (best strategies) ===")
    df["gap_cat"] = pd.cut(df["ev_gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                            labels=["tiny", "small", "med", "large", "huge"])
    for col, name in [("pred_A", "A:bucket"), ("pred_E", "E:trash+2P"), ("pred_F", "F:refined")]:
        def ev_chosen(r):
            if r[col] == "FOLD": return r["ev_fold"]
            if r[col] == "CALL": return r["ev_call"]
            return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]
        df[f"loss_{col}"] = df["best_ev"] - df.apply(ev_chosen, axis=1)

    print(f"  gap_cat   call    A:bucket  E:trash+2P  F:refined")
    for cat in df["gap_cat"].cat.categories:
        sub = df[df["gap_cat"] == cat]
        if len(sub) == 0: continue
        l_call = (sub["best_ev"] - sub["ev_call"]).mean()
        l_A = sub["loss_pred_A"].mean()
        l_E = sub["loss_pred_E"].mean()
        l_F = sub["loss_pred_F"].mean()
        print(f"  {str(cat):8s} {l_call:.4f}  {l_A:.4f}    {l_E:.4f}      {l_F:.4f}  n={len(sub)}")

    # ── Per-bucket ──
    print(f"\n=== Per-bucket EV loss (strategy F) ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 100: continue
        acc = (sub["pred_F"] == sub["modal"]).mean() * 100
        loss = sub["loss_pred_F"].mean()
        print(f"  {bk:13s} n={len(sub):6d} acc={acc:5.1f}% loss={loss:.4f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
