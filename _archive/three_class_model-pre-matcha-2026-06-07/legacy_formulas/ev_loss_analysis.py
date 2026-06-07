#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Reframe the evaluation: instead of accuracy, measure EV cost of prediction errors.

Hypothesis: most errors happen at low ev_gap, so EV cost is small even if accuracy is.
"Right" framework: predict modal where ev_gap is large, randomize where ev_gap is small.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def freq_to_3band(f):
    if f < 0.25: return "LOW"
    if f < 0.75: return "MIX"
    return "HIGH"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    df = df[(df["action_context"] == "attack") &
            (df["eq_percentile"].notna()) &
            (df["ev_bet"].notna()) & (df["ev_check"].notna())].copy()
    print(f"Attack rows with EV data: {len(df)}")

    # Per-row metrics
    df["actual_band"] = df["bet_freq"].apply(freq_to_3band)
    df["ev_gap"] = (df["ev_bet"] - df["ev_check"]).abs()
    df["best_action_ev"] = df[["ev_bet", "ev_check"]].max(axis=1)

    # Simple framework: predict based on eq_percentile bin
    def pred_action(eq):
        if eq < 0.30: return "CHECK"
        if eq < 0.70: return "CHECK"  # default for middle
        return "BET"
    df["pred_action"] = df["eq_percentile"].apply(pred_action)

    # EV chosen by prediction
    df["pred_ev"] = df.apply(
        lambda r: r["ev_bet"] if r["pred_action"] == "BET" else r["ev_check"], axis=1
    )
    df["ev_loss"] = df["best_action_ev"] - df["pred_ev"]
    # Loss is always non-negative (best_ev >= chosen_ev)

    # ── Distribution of ev_gap ──
    print(f"\n=== ev_gap distribution (BB) ===")
    for q in [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95, 0.99]:
        print(f"  q{int(q*100)}: {df['ev_gap'].quantile(q):.4f}")

    # ── How much of ev_gap is "tiny" vs "matters"? ──
    print(f"\n=== ev_gap categories ===")
    df["gap_cat"] = pd.cut(df["ev_gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                            labels=["tiny (<0.01)", "small (0.01-0.05)", "med (0.05-0.15)", "large (0.15-0.50)", "huge (>0.5)"])
    print(df["gap_cat"].value_counts(normalize=True).round(3) * 100)

    # ── EV loss by prediction outcome ──
    print(f"\n=== Total EV loss using prediction (CHECK if eq<70, BET otherwise) ===")
    total_loss = df["ev_loss"].sum()
    mean_loss = df["ev_loss"].mean()
    print(f"Mean EV loss per decision: {mean_loss:.4f} BB")
    print(f"Total EV loss over {len(df)} decisions: {total_loss:.1f} BB")

    # ── EV loss segmented by ev_gap ──
    print(f"\n=== EV loss by ev_gap category ===")
    for cat in df["gap_cat"].cat.categories:
        sub = df[df["gap_cat"] == cat]
        if len(sub) == 0:
            continue
        mean_loss = sub["ev_loss"].mean()
        max_loss = sub["ev_loss"].max()
        n_nonzero = (sub["ev_loss"] > 0.001).sum()
        print(f"  {str(cat):20s}  n={len(sub):6d}  mean_loss={mean_loss:.4f}BB  max_loss={max_loss:.3f}BB  n_with_loss>0={n_nonzero}")

    # ── How does accuracy look at high ev_gap? ──
    print(f"\n=== Accuracy vs EV loss tradeoff ===")
    # Define correctness as pred matching modal direction
    df["actual_action"] = (df["bet_freq"] >= 0.5).map({True: "BET", False: "CHECK"})
    df["correct"] = df["pred_action"] == df["actual_action"]
    for cat in df["gap_cat"].cat.categories:
        sub = df[df["gap_cat"] == cat]
        if len(sub) == 0: continue
        acc = sub["correct"].mean() * 100
        loss = sub["ev_loss"].mean()
        print(f"  {str(cat):20s}  acc={acc:5.1f}%  mean_loss={loss:.4f}BB")

    # ── What if we predict the BEST action by EV (oracle)? ──
    df["oracle_action"] = df.apply(lambda r: "BET" if r["ev_bet"] > r["ev_check"] else "CHECK", axis=1)
    df["oracle_correct"] = df["oracle_action"] == df["actual_action"]
    print(f"\n=== Oracle (pick max EV per combo) ===")
    print(f"Oracle accuracy: {df['oracle_correct'].mean()*100:.1f}%")
    print(f"Oracle EV loss: 0 (by definition)")

    # ── If we ALWAYS check ──
    df["always_check_ev"] = df["ev_check"]
    df["always_check_loss"] = df["best_action_ev"] - df["always_check_ev"]
    print(f"\n=== ALWAYS CHECK strategy ===")
    print(f"Mean EV loss per decision: {df['always_check_loss'].mean():.4f} BB")
    print(f"Total EV loss: {df['always_check_loss'].sum():.1f} BB")
    # accuracy
    df["check_only_correct"] = df["actual_action"] == "CHECK"
    print(f"Modal-action accuracy: {df['check_only_correct'].mean()*100:.1f}%")

    # ── If we ALWAYS bet ──
    df["always_bet_loss"] = df["best_action_ev"] - df["ev_bet"]
    print(f"\n=== ALWAYS BET strategy ===")
    print(f"Mean EV loss per decision: {df['always_bet_loss'].mean():.4f} BB")
    print(f"Modal-action accuracy: {(df['actual_action'] == 'BET').mean()*100:.1f}%")

    # ── Decompose loss in HIGH confidence vs LOW confidence ──
    print(f"\n=== Loss in HIGH-ev_gap subset (where it matters) ===")
    high_gap = df[df["ev_gap"] > 0.15]
    print(f"  n={len(high_gap)} ({len(high_gap)/len(df)*100:.1f}% of data)")
    print(f"  framework loss: {high_gap['ev_loss'].sum():.1f} BB")
    print(f"  always-check loss: {high_gap['always_check_loss'].sum():.1f} BB")
    # What if we predict CORRECTLY only on high-ev_gap, random on rest?
    high_gap_correct_pred = high_gap.apply(lambda r: "BET" if r["ev_bet"] > r["ev_check"] else "CHECK", axis=1)
    high_gap_loss = high_gap["best_action_ev"] - high_gap.apply(
        lambda r: r["ev_bet"] if (r["ev_bet"] > r["ev_check"]) else r["ev_check"], axis=1
    )
    print(f"  optimal-on-high-gap loss: {high_gap_loss.sum():.1f} BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
