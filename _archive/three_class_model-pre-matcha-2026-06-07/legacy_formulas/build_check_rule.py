#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "scikit-learn", "numpy"]
# ///
"""Build an interpretable shallow decision tree that predicts "is this a confident Pure Check?"

This is a binary classifier with high-precision target: when the tree says "yes, this is a
confident check", we want >90% of those to actually be LOW (bet_freq < 25%).

Use case in the book:
  1. Apply this tree first (5-7 yes/no questions).
  2. If it says "PURE_CHECK" → check the hand.
  3. If it says "AMBIGUOUS" → fall back to 25-cell table / mix / use GTO chart.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.tree import DecisionTreeClassifier, export_text

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features, encode_categoricals  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"
OUT_DIR = ROOT / "scripts" / "three_class_model"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")

    # Binary target: confident pure check = bet_freq < 0.15
    # (We tighten from 0.25 to make the positive class very clean for the rule)
    df["pure_check"] = (df["bet_freq"] < 0.15).astype(int)
    print(f"Pure check class share: {df['pure_check'].mean()*100:.1f}%")

    X, feat_names = encode_categoricals(df)
    y = df["pure_check"].values
    groups = df["spot_id"].values

    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42)

    # Sweep depths; we want high PRECISION on the positive (pure_check) class
    # — at the cost of low recall. The book uses the rule only when it fires.
    print()
    print(f"  depth  coverage  precision_check  recall_check  accuracy")
    print(f"  ─────  ────────  ───────────────  ────────────  ────────")
    for depth in [3, 4, 5, 6, 7, 8]:
        precs, recs, accs, covers = [], [], [], []
        for tr, te in sgkf.split(X, y, groups=groups):
            clf = DecisionTreeClassifier(
                max_depth=depth,
                min_samples_leaf=300,
                class_weight={0: 1, 1: 0.5},  # bias toward NOT predicting check (precision boost)
                random_state=42,
            )
            clf.fit(X.iloc[tr], y[tr])
            pred = clf.predict(X.iloc[te])
            tp = int(((pred == 1) & (y[te] == 1)).sum())
            fp = int(((pred == 1) & (y[te] == 0)).sum())
            fn = int(((pred == 0) & (y[te] == 1)).sum())
            tn = int(((pred == 0) & (y[te] == 0)).sum())
            prec = tp / max(tp + fp, 1)
            rec = tp / max(tp + fn, 1)
            acc = (tp + tn) / max(tp + tn + fp + fn, 1)
            cover = (pred == 1).mean()
            precs.append(prec); recs.append(rec); accs.append(acc); covers.append(cover)
        print(f"  {depth}      {np.mean(covers)*100:5.1f}%    {np.mean(precs)*100:5.1f}%           {np.mean(recs)*100:5.1f}%        {np.mean(accs)*100:5.1f}%")

    # Final tree on full data with depth 5 for inspection
    print()
    print(f"=== Final tree (depth=5) ===")
    final = DecisionTreeClassifier(
        max_depth=5, min_samples_leaf=300,
        class_weight={0: 1, 1: 0.5}, random_state=42,
    )
    final.fit(X, y)
    out = export_text(final, feature_names=feat_names, max_depth=5)
    (OUT_DIR / "pure_check_tree.txt").write_text(out)
    # Print just the leaves with class=1 (PURE_CHECK) paths
    lines = out.splitlines()
    print(f"Tree saved → pure_check_tree.txt ({len(lines)} lines)")
    print()
    print(f"=== Feature importance (top 15) ===")
    imp = pd.Series(final.feature_importances_, index=feat_names).sort_values(ascending=False)
    for n, v in imp.head(15).items():
        if v > 0.001:
            print(f"  {v:.3f}  {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
