#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Defense formula analysis for turn + river using newly fetched data.

Same Strategy F structure as flop defense — see if it generalizes.
Without equity_bucket (not in slimmed data), we use mv_cat + dv_cat + board_family.
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


def analyze(df: pd.DataFrame, street: str) -> None:
    print(f"\n{'='*70}\n=== {street.upper()} DEFENSE ===\n{'='*70}")
    sub = df[(df["street"] == street) & (df["action_context"] == "defense") &
              (df["ev_call"].notna()) & (df["ev_fold"].notna())].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    print(f"Rows: {len(sub)}, source files: {sub['source_path'].nunique()}")
    if len(sub) < 100:
        print("Insufficient data.")
        return

    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["mv_s"] = sub["mv_cat"].map(MV).fillna(0).astype(int)
    sub["dv_s"] = sub["dv_cat"].map(DV).fillna(0).astype(int)
    sub["best_ev"] = sub[["ev_fold", "ev_call", "ev_raise"]].max(axis=1)

    # Use eq_percentile as proxy for bucket if available, else mv-based
    has_eq = sub["eq_percentile"].notna().mean() > 0.5
    print(f"eq_percentile available: {has_eq*100:.0f}%")

    if has_eq:
        sub["bucket_s"] = pd.cut(sub["eq_percentile"], bins=[-0.01, 0.25, 0.5, 0.75, 1.01],
                                  labels=[0, 1, 2, 3]).cat.codes.clip(lower=0)
    else:
        sub["bucket_s"] = pd.cut(sub["mv_s"], bins=[-1, 0, 2, 3, 6],
                                  labels=[0, 1, 2, 3]).cat.codes.clip(lower=0)
        print("(using mv_s → bucket proxy: 0=high_card, 1=pair, 2=OP+, 3=2P+)")

    # Apply Strategy F
    sub["pred_F"] = np.where((sub["bucket_s"] <= 1) & (sub["mv_s"] == 0) & (sub["dv_s"] == 0), "FOLD",
                     np.where((sub["bucket_s"] >= 3) & (sub["mv_s"] >= 3), "RAISE", "CALL"))

    # Simpler "no_mv AND no_dv → FOLD; 2P+ → RAISE; else CALL"
    sub["pred_simple"] = np.where((sub["mv_s"] == 0) & (sub["dv_s"] == 0), "FOLD",
                          np.where(sub["mv_s"] >= 4, "RAISE", "CALL"))

    def loss_of(col):
        def ev_chosen(r):
            if r[col] == "FOLD": return r["ev_fold"]
            if r[col] == "CALL": return r["ev_call"]
            return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]
        s = sub.copy()
        s["ev_pred"] = s.apply(ev_chosen, axis=1)
        s["loss"] = s["best_ev"] - s["ev_pred"]
        acc = (s[col] == s["modal"]).mean() * 100
        loss = s["loss"].mean()
        # huge_gap
        def gap(r):
            evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
            return evs[0] - evs[1] if len(evs) >= 2 else None
        s["gap"] = s.apply(gap, axis=1)
        huge = s[s["gap"] > 0.50]
        huge_loss = huge["loss"].mean() if len(huge) > 0 else float("nan")
        print(f"  {col:18s}  acc={acc:5.1f}%  mean_loss={loss:.4f}BB  huge_gap_loss={huge_loss:.4f}BB (n_huge={len(huge)})")
        return s

    print(f"\nBaselines:")
    print(f"  always_FOLD loss: {(sub['best_ev'] - sub['ev_fold']).mean():.4f} BB")
    print(f"  always_CALL loss: {(sub['best_ev'] - sub['ev_call']).mean():.4f} BB")

    print(f"\nFormulas:")
    loss_of("pred_F")
    loss_of("pred_simple")

    # Per mv_cat
    sub["pred"] = sub["pred_F"]
    def ev_chosen(r):
        if r["pred"] == "FOLD": return r["ev_fold"]
        if r["pred"] == "CALL": return r["ev_call"]
        return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]
    sub["ev_pred"] = sub.apply(ev_chosen, axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_pred"]

    print(f"\nPer mv_cat (formula F):")
    for mv, ss in sub.groupby("mv_cat"):
        if len(ss) < 100: continue
        acc = (ss["pred"] == ss["modal"]).mean() * 100
        modal_dist = ss["modal"].value_counts(normalize=True).to_dict()
        modal_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(modal_dist.items()))
        print(f"  {mv:15s} n={len(ss):5d} acc={acc:5.1f}% loss={ss['loss'].mean():.4f}BB  actual={modal_str}")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    for st in ["flop", "turn", "river"]:
        analyze(df, st)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
