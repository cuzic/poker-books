#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "scikit-learn", "numpy"]
# ///
"""Confidence-aware evaluation.

For each prediction, the GBT gives a probability distribution over [LOW, MIX, HIGH].
We define confidence = max(proba). We sweep a confidence threshold τ and report:
  - coverage(τ) = fraction of predictions with confidence ≥ τ
  - accuracy(τ) = accuracy on covered predictions
  - LOW↔HIGH confusion(τ) on covered predictions

User goal: even if raw accuracy is ~60%, can we restrict to a high-coverage subset
where accuracy is 85%+ and LOW↔HIGH confusion is near 0?

This is the "predict-when-confident, defer-when-not" framework.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features, encode_categoricals  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    # Use FULL dataset (no filter) — donk=0% spots are easy LOW cases the model SHOULD recognize confidently
    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")

    X, _ = encode_categoricals(df)
    y = df["label"].values
    groups = df["spot_id"].values
    labels = ["LOW", "MIX", "HIGH"]

    sgkf = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=42)
    # Gather out-of-fold predictions
    all_pred = np.empty(len(y), dtype=object)
    all_proba = np.zeros((len(y), 3))
    all_true = y.copy()

    for fold, (tr, te) in enumerate(sgkf.split(X, y, groups=groups)):
        clf = HistGradientBoostingClassifier(
            max_iter=300, max_depth=6, learning_rate=0.05, random_state=42
        )
        clf.fit(X.iloc[tr], y[tr])
        prob = clf.predict_proba(X.iloc[te])
        # ensure column order matches our labels
        col_order = [list(clf.classes_).index(lbl) for lbl in labels]
        prob_reordered = prob[:, col_order]
        all_proba[te] = prob_reordered
        pred = np.array([labels[i] for i in np.argmax(prob_reordered, axis=1)])
        all_pred[te] = pred
        print(f"  fold {fold} done")

    confidence = all_proba.max(axis=1)
    correct = (all_pred == all_true)

    # Overall stats
    print(f"\n=== Overall (no threshold) ===")
    print(f"accuracy = {correct.mean()*100:.1f}%")
    overall_conf = confusion_matrix(all_true, all_pred, labels=labels)
    print(f"LOW↔HIGH confusion: {(overall_conf[0,2]+overall_conf[2,0])/overall_conf.sum()*100:.2f}%")

    # Sweep thresholds
    print(f"\n=== Confidence threshold sweep ===")
    print(f"  τ      coverage  accuracy  LOW↔HIGH  (LOW%/MIX%/HIGH% of covered)")
    print(f"  ─────  ────────  ────────  ────────  ──────────────────────")
    for tau in [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90]:
        mask = confidence >= tau
        if mask.sum() < 100:
            continue
        cov = mask.mean()
        acc = correct[mask].mean()
        cm = confusion_matrix(all_true[mask], all_pred[mask], labels=labels)
        tot = cm.sum()
        lh = (cm[0, 2] + cm[2, 0]) / max(tot, 1) * 100
        pred_dist = pd.Series(all_pred[mask]).value_counts(normalize=True)
        l_p = pred_dist.get("LOW", 0) * 100
        m_p = pred_dist.get("MIX", 0) * 100
        h_p = pred_dist.get("HIGH", 0) * 100
        print(f"  {tau:.2f}   {cov*100:5.1f}%    {acc*100:5.1f}%    {lh:5.2f}%   {l_p:.0f}/{m_p:.0f}/{h_p:.0f}")

    # Per-class confidence distribution
    print(f"\n=== Per-true-class: median confidence and accuracy ===")
    for lbl in labels:
        m = all_true == lbl
        median_conf = float(np.median(confidence[m]))
        acc_lbl = correct[m].mean()
        print(f"  true={lbl}: n={m.sum()} median_conf={median_conf:.2f} acc={acc_lbl*100:.1f}%")

    # Per-predicted-class: precision and median confidence
    print(f"\n=== Per-predicted-class: precision (PPV) and median confidence ===")
    for lbl in labels:
        m = all_pred == lbl
        if m.sum() == 0:
            continue
        median_conf = float(np.median(confidence[m]))
        prec = (all_true[m] == lbl).mean()
        print(f"  pred={lbl}: n={m.sum()} median_conf={median_conf:.2f} precision={prec*100:.1f}%")

    # Save out-of-fold results for offline analysis
    out = pd.DataFrame({
        "true": all_true,
        "pred": all_pred,
        "confidence": confidence,
        "p_LOW": all_proba[:, 0],
        "p_MIX": all_proba[:, 1],
        "p_HIGH": all_proba[:, 2],
    })
    out.to_csv(ROOT / "scripts" / "three_class_model" / "oof_predictions.csv", index=False)
    print(f"\nOOF predictions saved → oof_predictions.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
