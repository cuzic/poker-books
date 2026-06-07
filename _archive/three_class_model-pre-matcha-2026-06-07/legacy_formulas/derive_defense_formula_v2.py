#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy", "scikit-learn"]
# ///
"""Defense formula v2: include equity_bucket + use decision tree to discover structure.

Strategy:
  1. Fit a shallow decision tree (depth 3-4) on (bucket, mv, dv, board) → modal action
  2. Inspect splits — derive a simple additive scoring rule
  3. Evaluate EV loss
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


BUCKET_SCORE = {"trash_hands": 0, "weak_hands": 1, "good_hands": 2, "best_hands": 3}

# Initial guesses, will be refined
MV_SCORE = {
    "no_made_hand": 0,
    "king_high": 0, "ace_high": 0,
    "low_pair": 1, "underpair": 1, "third_pair": 1, "second_pair": 1,
    "top_pair": 2,
    "overpair": 3,
    "two_pair": 4, "set": 4, "trips": 4,
    "straight": 5, "flush": 5, "fullhouse": 5, "quads": 5,
}
DV_SCORE = {
    "no_draw": 0,
    "twocards_bdfd": 0, "onecard_bdfd": 0, "gutshot": 0,
    "oesd": 1, "flush_draw": 1, "nut_flush_draw": 1,
    "combo_draw": 2,
}


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    df = df[(df["action_context"] == "defense") &
            (df["ev_call"].notna()) & (df["ev_fold"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    df["fold_freq"] = df["fold_freq"].fillna(0)
    df["call_freq"] = df["call_freq"].fillna(0)
    df["raise_freq"] = df["raise_freq"].fillna(0)
    print(f"Defense rows: {len(df)}")

    df["modal"] = df[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()

    # ── Encode features as integer scores ──
    df["bucket_s"] = df["equity_bucket"].map(BUCKET_SCORE).fillna(1).astype(int)
    df["mv_s"] = df["mv_cat"].map(MV_SCORE).fillna(0).astype(int)
    df["dv_s"] = df["dv_cat"].map(DV_SCORE).fillna(0).astype(int)
    # board adj
    board_adj = {"paired": -1, "monotone": -1, "dynamic": 0, "dynamic_2tone": 0,
                  "dry_high": 0, "low_dry": 0, "unknown": 0}
    df["board_s"] = df["board_family"].map(board_adj).fillna(0).astype(int)

    # ── Fit a depth-3 decision tree ──
    X = df[["bucket_s", "mv_s", "dv_s", "board_s"]].values
    y = df["modal"].values
    tree = DecisionTreeClassifier(max_depth=3, min_samples_leaf=500, random_state=0)
    tree.fit(X, y)
    print(f"\n=== Decision tree (depth 3) ===")
    print(export_text(tree, feature_names=["bucket", "mv", "dv", "board"]))
    print(f"Tree accuracy: {tree.score(X, y)*100:.1f}%")

    # ── Try additive scoring: combined = α·bucket + β·mv + γ·dv + δ·board ──
    # Grid search on integer weights
    print(f"\n=== Grid search on linear weights ===")
    best = (None, 0)
    for a in [1, 2, 3, 4]:
        for b in [1, 2, 3]:
            for g in [1, 2]:
                for d in [0, 1, 2]:
                    df["score"] = a*df["bucket_s"] + b*df["mv_s"] + g*df["dv_s"] - d*(df["board_s"] == -1).astype(int)
                    # find best thresholds
                    for tc in range(0, 8):
                        for tr in range(tc+1, 18):
                            pred = pd.Series(np.where(df["score"] < tc, "FOLD",
                                              np.where(df["score"] < tr, "CALL", "RAISE")), index=df.index)
                            acc = (pred == df["modal"]).mean()
                            if acc > best[1]:
                                best = ((a, b, g, d, tc, tr), acc)
    (a, b, g, d, tc, tr), acc = best
    print(f"Best: α={a}, β={b}, γ={g}, δ={d}, CALL≥{tc}, RAISE≥{tr}  acc={acc*100:.1f}%")

    df["score"] = a*df["bucket_s"] + b*df["mv_s"] + g*df["dv_s"] - d*(df["board_s"] == -1).astype(int)
    df["pred"] = np.where(df["score"] < tc, "FOLD",
                  np.where(df["score"] < tr, "CALL", "RAISE"))
    df["correct"] = df["pred"] == df["modal"]
    print(f"Accuracy overall: {df['correct'].mean()*100:.1f}%")
    print("Confusion:")
    print(pd.crosstab(df["pred"], df["modal"]))

    # ── EV loss ──
    df["best_ev"] = df[["ev_fold", "ev_call", "ev_raise"]].max(axis=1)
    def ev_chosen(r):
        if r["pred"] == "FOLD": return r["ev_fold"]
        if r["pred"] == "CALL": return r["ev_call"]
        return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]
    df["ev_pred"] = df.apply(ev_chosen, axis=1)
    df["loss"] = df["best_ev"] - df["ev_pred"]
    print(f"\nMean EV loss: {df['loss'].mean():.4f} BB")
    print(f"Mean always-CALL loss: {(df['best_ev'] - df['ev_call']).mean():.4f} BB")
    print(f"Mean always-FOLD loss: {(df['best_ev'] - df['ev_fold']).mean():.4f} BB")

    # ── Per ev_gap category ──
    def best_chosen_gap(r):
        evs = [e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)]
        if len(evs) < 2: return None
        evs.sort(reverse=True)
        return evs[0] - evs[1]
    df["ev_gap"] = df.apply(best_chosen_gap, axis=1)
    df_g = df[df["ev_gap"].notna()].copy()
    df_g["gap_cat"] = pd.cut(df_g["ev_gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                              labels=["tiny", "small", "med", "large", "huge"])
    print(f"\n=== EV loss per gap ===")
    for cat in df_g["gap_cat"].cat.categories:
        sub = df_g[df_g["gap_cat"] == cat]
        if len(sub) == 0: continue
        l_call = (sub["best_ev"] - sub["ev_call"]).mean()
        l_form = sub["loss"].mean()
        print(f"  {str(cat):8s} n={len(sub):6d} always_CALL={l_call:.4f}BB formula={l_form:.4f}BB")

    # ── Per bucket ──
    print(f"\n=== Per bucket ===")
    for bk, sub in df.groupby("equity_bucket"):
        if len(sub) < 100: continue
        print(f"  {bk:13s} n={len(sub):6d} acc={sub['correct'].mean()*100:5.1f}% loss={sub['loss'].mean():.4f}BB")

    # ── Score → modal distribution ──
    print(f"\n=== Score → modal action ===")
    for s, sub in df.groupby("score"):
        if len(sub) < 500: continue
        dist = sub["modal"].value_counts(normalize=True).to_dict()
        dist_str = " ".join(f"{k}:{v*100:.0f}%" for k, v in sorted(dist.items()))
        pred_act = "FOLD" if s < tc else ("CALL" if s < tr else "RAISE")
        print(f"  score={int(s):2d} n={len(sub):6d} pred={pred_act:5s} actual={dist_str}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
