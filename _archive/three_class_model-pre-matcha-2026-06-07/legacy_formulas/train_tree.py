#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "scikit-learn", "numpy"]
# ///
"""Train a shallow decision tree on the extracted dataset.

Reads scripts/three_class_model/dataset_gtow.csv.
Features (all human-computable in 5s):
  context:  family, depth_bb_bucket, hero_rel (IP/OOP), line, street
  board:    top_rank, paired, spread_bucket, n_suits, has_A_top, has_K_top
  hand:     mv_cat, dv_cat, has_A, has_K, is_pair, is_suited, gap_bucket

Label: bet_freq → LOW (<25%) / MIX (25-75%) / HIGH (≥75%)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = Path("/home/cuzic/poker-books")
CSV = ROOT / "scripts" / "three_class_model" / "dataset_gtow.csv"
OUT_DIR = ROOT / "scripts" / "three_class_model"

RANKS = "23456789TJQKA"


def rank_idx(r: str) -> int:
    return RANKS.index(r) if r in RANKS else -1


def label_for(freq: float) -> str:
    if freq < 0.25:
        return "LOW"
    if freq < 0.75:
        return "MIX"
    return "HIGH"


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    # ── label ──
    df["label"] = df["bet_freq"].apply(label_for)

    # ── context ──
    def depth_bucket(d):
        if d <= 30:
            return "short"
        if d <= 75:
            return "mid"
        if d <= 150:
            return "deep"
        return "very_deep"
    df["depth_bucket"] = df["depth_bb"].apply(depth_bucket)

    # ── board features (use first 3 cards = flop) ──
    def flop_features(b: str) -> pd.Series:
        if len(b) < 6:
            return pd.Series({"top_rank": -1, "mid_rank": -1, "bot_rank": -1,
                              "paired": False, "spread": -1, "n_suits": -1,
                              "monotone": False, "twotone": False})
        ranks = sorted([rank_idx(b[0]), rank_idx(b[2]), rank_idx(b[4])], reverse=True)
        suits = [b[1], b[3], b[5]]
        return pd.Series({
            "top_rank": ranks[0],
            "mid_rank": ranks[1],
            "bot_rank": ranks[2],
            "paired": ranks[0] == ranks[1] or ranks[1] == ranks[2],
            "spread": ranks[0] - ranks[2],
            "n_suits": len(set(suits)),
            "monotone": len(set(suits)) == 1,
            "twotone": len(set(suits)) == 2,
        })

    feats = df["board_flop"].apply(flop_features)
    df = pd.concat([df, feats], axis=1)

    # top_rank bucket: A=12,K=11,Q=10,J=9,T=8,low=else
    def top_rank_bucket(r):
        if r == 12:
            return "A"
        if r == 11:
            return "K"
        if r == 10:
            return "Q"
        if r == 9:
            return "J"
        if r == 8:
            return "T"
        return "low"
    df["top_rank_bucket"] = df["top_rank"].apply(top_rank_bucket)

    def spread_bucket(s):
        if s < 0:
            return "unk"
        if s <= 3:
            return "connected"
        if s <= 7:
            return "medium"
        return "wide"
    df["spread_bucket"] = df["spread"].apply(spread_bucket)

    # board family (rough)
    def board_family(row):
        if row["paired"]:
            return "paired"
        if row["monotone"]:
            return "monotone"
        if row["n_suits"] == 2 and row["spread"] <= 4:
            return "dynamic_2tone"
        if row["spread"] <= 4:
            return "dynamic"
        if row["top_rank"] >= 9:  # J+
            return "dry_high"
        return "low_dry"
    df["board_family"] = df.apply(board_family, axis=1)

    # ── hand features ──
    def hand_features(row) -> pd.Series:
        ca = str(row["card_a"]) if row["card_a"] else ""
        cb = str(row["card_b"]) if row["card_b"] else ""
        if len(ca) != 2 or len(cb) != 2:
            return pd.Series({"has_A": False, "has_K": False, "is_pair": False,
                              "is_suited": False, "hand_high": -1, "hand_low": -1})
        r1, s1 = ca[0], ca[1]
        r2, s2 = cb[0], cb[1]
        i1, i2 = rank_idx(r1), rank_idx(r2)
        return pd.Series({
            "has_A": "A" in (r1, r2),
            "has_K": "K" in (r1, r2),
            "is_pair": r1 == r2,
            "is_suited": s1 == s2,
            "hand_high": max(i1, i2),
            "hand_low": min(i1, i2),
        })
    h = df.apply(hand_features, axis=1)
    df = pd.concat([df, h], axis=1)

    # hand_high relative to board top
    df["hand_high_vs_top"] = (df["hand_high"] - df["top_rank"]).clip(-12, 12)

    return df


def encode_categoricals(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """One-hot encode categorical cols, return (X, feature_names)."""
    cat_cols = [
        "family", "depth_bucket", "hero_rel", "line", "street",
        "top_rank_bucket", "spread_bucket", "board_family",
        "mv_cat", "dv_cat",
    ]
    num_cols = [
        "paired", "monotone", "twotone", "n_suits",
        "has_A", "has_K", "is_pair", "is_suited",
        "hand_high_vs_top", "spread",
    ]
    X = pd.get_dummies(df[cat_cols + num_cols], columns=cat_cols, drop_first=False)
    return X, list(X.columns)


def main() -> int:
    df = pd.read_csv(CSV, dtype={"card_a": str, "card_b": str, "board_flop": str})
    print(f"Loaded {len(df)} rows from {CSV.name}")
    df = add_features(df)

    label_counts = df["label"].value_counts()
    print(f"Label dist: {dict(label_counts)}")

    X, feat_names = encode_categoricals(df)
    y = df["label"].values
    groups = df["spot_id"].values  # avoid spot-leakage in CV

    # ── group-aware K-fold so train/test don't share spots ──
    sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    results: list[dict] = []
    for depth in [4, 5, 6, 7, 8]:
        accs, confs, reports = [], [], []
        for tr_idx, te_idx in sgkf.split(X, y, groups=groups):
            clf = DecisionTreeClassifier(
                max_depth=depth,
                min_samples_leaf=200,
                class_weight="balanced",
                random_state=42,
            )
            clf.fit(X.iloc[tr_idx], y[tr_idx])
            pred = clf.predict(X.iloc[te_idx])
            accs.append((pred == y[te_idx]).mean())
            confs.append(confusion_matrix(y[te_idx], pred, labels=["LOW", "MIX", "HIGH"]))
            reports.append(classification_report(y[te_idx], pred, labels=["LOW", "MIX", "HIGH"], zero_division=0, output_dict=True))
        mean_acc = float(np.mean(accs))
        mean_conf = np.sum(confs, axis=0)
        results.append({"depth": depth, "acc": mean_acc, "conf": mean_conf.tolist()})
        print(f"\n=== max_depth={depth} ===")
        print(f"mean accuracy = {mean_acc*100:.1f}%")
        print(f"confusion (rows=true, cols=pred) [LOW/MIX/HIGH]:")
        print(mean_conf)
        # LOW↔HIGH confusion (the worst kind)
        low_to_high = mean_conf[0, 2]
        high_to_low = mean_conf[2, 0]
        total = mean_conf.sum()
        print(f"LOW↔HIGH confusion: {(low_to_high + high_to_low)/total*100:.2f}% of all preds")

    # Train final tree on full data with best-looking depth for visualization
    best_depth = max(results, key=lambda r: r["acc"])["depth"]
    print(f"\n=== Final tree (max_depth={best_depth}, fit on full data) ===")
    final = DecisionTreeClassifier(
        max_depth=best_depth, min_samples_leaf=200,
        class_weight="balanced", random_state=42,
    )
    final.fit(X, y)
    tree_txt = export_text(final, feature_names=feat_names, max_depth=best_depth)
    (OUT_DIR / "tree.txt").write_text(tree_txt)
    print(f"Tree text written to {OUT_DIR / 'tree.txt'} ({len(tree_txt.splitlines())} lines)")

    (OUT_DIR / "cv_results.json").write_text(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
