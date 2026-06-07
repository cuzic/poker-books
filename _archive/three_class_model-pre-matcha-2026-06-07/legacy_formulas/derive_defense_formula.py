#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy", "scikit-learn"]
# ///
"""Derive a simple Chen-style additive scoring formula for defense.

Goal:
  DefenseScore = MV_value + DV_value + Board_adjust + Size_adjust
  Map score → action via 2 thresholds.

Approach:
  1. Try hand-crafted scoring first (intuition-driven)
  2. Then use logistic regression / decision tree to refine coefficients
  3. Verify EV loss vs the 228-cell HIGH-only baseline
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


# ── Hand-crafted scoring v1 ──
MV_SCORE = {
    "no_made_hand": 0,
    "king_high": 1,
    "ace_high": 1,
    "low_pair": 2,
    "underpair": 2,
    "third_pair": 2,
    "second_pair": 3,
    "top_pair": 4,
    "overpair": 5,
    "two_pair": 6,
    "set": 7,
    "trips": 7,
    "straight": 8,
    "flush": 8,
    "fullhouse": 9,
    "quads": 9,
}

DV_SCORE = {
    "no_draw": 0,
    "twocards_bdfd": 1,
    "onecard_bdfd": 1,
    "gutshot": 1,
    "oesd": 2,
    "flush_draw": 2,
    "nut_flush_draw": 2,
    "combo_draw": 3,
}

BOARD_ADJ = {
    "dry_high": 0,
    "low_dry": 0,
    "dynamic": -1,         # more polarized villain → fold weak more
    "dynamic_2tone": 0,
    "paired": -1,          # villain has trips often
    "monotone": -2,        # flushes
    "unknown": 0,
}


def defense_score(mv: str, dv: str, board: str) -> int:
    return MV_SCORE.get(mv, 0) + DV_SCORE.get(dv, 0) + BOARD_ADJ.get(board, 0)


def score_to_action(score: int, threshold_call: int = 2, threshold_raise: int = 6) -> str:
    if score < threshold_call:
        return "FOLD"
    if score < threshold_raise:
        return "CALL"
    return "RAISE"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    df = df[(df["action_context"] == "defense") &
            (df["ev_call"].notna()) & (df["ev_fold"].notna())].copy()
    print(f"Defense rows: {len(df)}")

    # Compute score per row
    df["def_score"] = df.apply(
        lambda r: defense_score(r["mv_cat"], r["dv_cat"], str(r.get("board_family", ""))),
        axis=1,
    )

    # Actual modal
    df["fold_freq"] = df["fold_freq"].fillna(0)
    df["call_freq"] = df["call_freq"].fillna(0)
    df["raise_freq"] = df["raise_freq"].fillna(0)
    df["actual_modal"] = df.apply(
        lambda r: max({"FOLD": r["fold_freq"], "CALL": r["call_freq"], "RAISE": r["raise_freq"]}.items(),
                       key=lambda x: x[1])[0],
        axis=1,
    )

    # ── Tune thresholds via grid search ──
    print(f"\n=== Threshold grid search ===")
    best = (None, 0)
    grid_results = []
    for tc in range(0, 6):
        for tr in range(tc + 1, 10):
            df["pred"] = df["def_score"].apply(lambda s: score_to_action(s, tc, tr))
            acc = (df["pred"] == df["actual_modal"]).mean() * 100
            grid_results.append((tc, tr, acc))
            if acc > best[1]:
                best = ((tc, tr), acc)
    grid_results.sort(key=lambda x: -x[2])
    print(f"Top 10 threshold combos:")
    for tc, tr, acc in grid_results[:10]:
        print(f"  CALL≥{tc}, RAISE≥{tr}: acc={acc:.1f}%")

    # Apply best thresholds
    best_tc, best_tr = best[0]
    df["pred"] = df["def_score"].apply(lambda s: score_to_action(s, best_tc, best_tr))
    df["correct"] = df["pred"] == df["actual_modal"]
    print(f"\n=== With best thresholds CALL≥{best_tc}, RAISE≥{best_tr} ===")
    print(f"Accuracy: {df['correct'].mean()*100:.1f}%")
    print("Confusion:")
    print(pd.crosstab(df["pred"], df["actual_modal"]))

    # ── EV loss ──
    df["ev_pred"] = df.apply(
        lambda r: r["ev_fold"] if r["pred"] == "FOLD" else (r["ev_call"] if r["pred"] == "CALL" else (r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"])),
        axis=1,
    )
    df["best_ev"] = df[["ev_fold", "ev_call", "ev_raise"]].max(axis=1)
    df["loss"] = df["best_ev"] - df["ev_pred"]
    print(f"\nMean EV loss per decision: {df['loss'].mean():.4f} BB")
    print(f"Total: {df['loss'].sum():.1f} BB")

    # ── EV loss per ev_gap ──
    def ev_gap(r):
        evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
        return evs[0] - evs[1] if len(evs) >= 2 else None
    df["ev_gap"] = df.apply(ev_gap, axis=1)
    df_g = df[df["ev_gap"].notna()].copy()
    df_g["gap_cat"] = pd.cut(df_g["ev_gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                              labels=["tiny", "small", "med", "large", "huge"])
    print(f"\n=== EV loss per ev_gap ===")
    for cat in df_g["gap_cat"].cat.categories:
        sub = df_g[df_g["gap_cat"] == cat]
        if len(sub) == 0: continue
        loss_call = (sub["best_ev"] - sub["ev_call"]).mean()
        loss_formula = sub["loss"].mean()
        print(f"  {str(cat):8s}  n={len(sub):6d}  always_CALL_loss={loss_call:.4f}BB  formula_loss={loss_formula:.4f}BB")

    # ── Per bucket ──
    print(f"\n=== Per bucket ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 100: continue
        acc = sub["correct"].mean() * 100
        loss = sub["loss"].mean()
        print(f"  {bk:13s}  n={len(sub):6d}  acc={acc:5.1f}%  loss={loss:.4f}BB")

    # ── Show example: score → action mapping table ──
    print(f"\n=== Score → modal action distribution (top 15 by n) ===")
    for s, sub in df.groupby("def_score"):
        if len(sub) < 500: continue
        dist = sub["actual_modal"].value_counts(normalize=True).to_dict()
        dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
        print(f"  score={s:2d}  n={len(sub):6d}  pred_modal={score_to_action(s, best_tc, best_tr):5s}  actual={dist_str}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
