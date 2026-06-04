#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "scikit-learn", "numpy"]
# ///
"""Compare decision tree vs RandomForest vs GradientBoosting on the dataset.

This tells us:
- if accuracy is feature-limited (all models cap at ~55%) → need better features/data
- if accuracy is model-limited (GBT >> tree) → keep building data, switch to GBT
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features, encode_categoricals  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    print(f"Loaded {len(df)} rows")
    df = add_features(df)
    # Optional: drop heavily-LOW-biased "donk validation" topics for fairer eval
    # (keep all data for now; mark with a flag for later filtering)

    X, _ = encode_categoricals(df)
    y = df["label"].values
    groups = df["spot_id"].values

    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42)

    models = {
        "tree d=7": DecisionTreeClassifier(max_depth=7, min_samples_leaf=200,
                                            class_weight="balanced", random_state=42),
        "rf d=10 n=200": RandomForestClassifier(n_estimators=200, max_depth=10,
                                                  min_samples_leaf=50, class_weight="balanced",
                                                  random_state=42, n_jobs=-1),
        "gbt d=5 n=200": GradientBoostingClassifier(n_estimators=200, max_depth=5,
                                                      learning_rate=0.05, random_state=42),
    }
    labels = ["LOW", "MIX", "HIGH"]

    for name, clf in models.items():
        accs = []
        confs = np.zeros((3, 3), dtype=int)
        for tr, te in sgkf.split(X, y, groups=groups):
            clf.fit(X.iloc[tr], y[tr])
            pred = clf.predict(X.iloc[te])
            accs.append((pred == y[te]).mean())
            confs += confusion_matrix(y[te], pred, labels=labels)
        mean_acc = float(np.mean(accs))
        print(f"\n=== {name} ===")
        print(f"accuracy = {mean_acc*100:.1f}%")
        print(f"confusion (rows=true, cols=pred) {labels}:")
        print(confs)
        total = confs.sum()
        print(f"LOW↔HIGH confusion: {(confs[0,2]+confs[2,0])/total*100:.2f}%")
        # Per-class precision/recall
        for i, lbl in enumerate(labels):
            tp = confs[i, i]
            recall = tp / max(confs[i].sum(), 1)
            precision = tp / max(confs[:, i].sum(), 1)
            f1 = 2 * precision * recall / max(precision + recall, 1e-9)
            print(f"  {lbl}: prec={precision*100:.0f}% recall={recall*100:.0f}% f1={f1*100:.0f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
