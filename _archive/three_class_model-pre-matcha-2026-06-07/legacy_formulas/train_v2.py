#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "scikit-learn", "numpy"]
# ///
"""Train v2 model with enriched features. Compare to v1 baseline."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402
from features_v2 import add_v2_features, encode_v2  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"


def evaluate(X, y, groups, name: str, clf):
    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42)
    labels = ["LOW", "MIX", "HIGH"]
    accs = []
    confs = np.zeros((3, 3), dtype=int)
    for tr, te in sgkf.split(X, y, groups=groups):
        clf.fit(X.iloc[tr], y[tr])
        p = clf.predict(X.iloc[te])
        accs.append((p == y[te]).mean())
        confs += confusion_matrix(y[te], p, labels=labels)
    acc = float(np.mean(accs))
    print(f"\n=== {name} ===")
    print(f"accuracy = {acc*100:.1f}%")
    print(f"confusion {labels}:")
    print(confs)
    total = confs.sum()
    print(f"LOW↔HIGH confusion: {(confs[0,2]+confs[2,0])/total*100:.2f}%")
    for i, lbl in enumerate(labels):
        rec = confs[i, i] / max(confs[i].sum(), 1)
        prec = confs[i, i] / max(confs[:, i].sum(), 1)
        print(f"  {lbl}: prec={prec*100:.0f}% recall={rec*100:.0f}%")
    return acc, confs


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    print(f"Loaded {len(df)} rows")
    df = add_features(df)
    df = add_v2_features(df)

    # Filter to informative spots only (the realistic challenge)
    spot_mean = df.groupby("spot_id")["bet_freq"].mean()
    keep = spot_mean[(spot_mean >= 0.05) & (spot_mean <= 0.95)].index
    df = df[df["spot_id"].isin(keep)].copy()
    print(f"Filtered: {len(df)} rows / {df['spot_id'].nunique()} spots")
    print(f"Label dist: {df['label'].value_counts().to_dict()}")

    X_v2, _ = encode_v2(df)
    y = df["label"].values
    groups = df["spot_id"].values

    # v2 GBT
    clf = GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42)
    evaluate(X_v2, y, groups, "v2 GBT n=300", clf)

    # Feature importance
    clf2 = GradientBoostingClassifier(n_estimators=300, max_depth=5, learning_rate=0.05, random_state=42)
    clf2.fit(X_v2, y)
    imp = pd.Series(clf2.feature_importances_, index=X_v2.columns).sort_values(ascending=False)
    print("\nTop 20 features:")
    for name, val in imp.head(20).items():
        print(f"  {val:.3f}  {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
