#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Build the equity-bucket-based decision model.

For each spot:
1. Rank combos by ev_check (proxy for current equity / SDV).
2. Partition into 4 buckets matching the GTO Wizard total_combos per bucket.
3. Tag each combo with its bucket: best / good / weak / trash.
4. Cross-tabulate (bucket × context) → bet_freq.

Output:
- dataset_with_buckets.csv: per-combo with bucket assigned
- bucket_summary.md: pivot tables
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "knowledges" / "gto_wizard_full"
DATASET = ROOT / "scripts" / "three_class_model" / "dataset_full.csv"
OUT_CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"
OUT_MD = ROOT / "scripts" / "three_class_model" / "BUCKET_MODEL_REPORT.md"

BUCKET_ORDER = ["best_hands", "good_hands", "weak_hands", "trash_hands"]


def load_spot_bucket_sizes(spot_id: str) -> dict[str, float]:
    """Aggregate total_combos per bucket across all actions for one spot."""
    sizes: dict[str, float] = defaultdict(float)
    for p in DATA.glob(f"**/{spot_id}.json"):
        d = json.loads(p.read_text())
        for a in d.get("action_solutions") or []:
            for b in a.get("equity_buckets") or []:
                sizes[b["name"]] += b.get("total_combos", 0) or 0
        return dict(sizes)
    return dict(sizes)


def main() -> int:
    df = pd.read_csv(DATASET, low_memory=False)
    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")

    # Filter to rows where ev_check is available
    df = df[df["ev_check"].notna()].copy()
    print(f"After ev_check filter: {len(df)}")

    # Per spot: rank combos by ev_check (desc), partition by bucket sizes
    bucket_assignment: dict[tuple[str, int], str] = {}
    rank_within_spot: dict[tuple[str, int], int] = {}
    for spot_id, group in df.groupby("spot_id"):
        sizes = load_spot_bucket_sizes(spot_id)
        if not sizes:
            continue
        total = sum(sizes.values())
        if total < 1:
            continue
        # Sort combos descending by ev_check (high ev_check = good equity)
        sorted_g = group.sort_values("ev_check", ascending=False).reset_index()
        # Assign cumulative bucket boundaries
        ordered_buckets = [(name, sizes.get(name, 0)) for name in BUCKET_ORDER]
        idx = 0
        for bname, bsize in ordered_buckets:
            n_assign = int(round(bsize))
            for j in range(idx, min(idx + n_assign, len(sorted_g))):
                row_idx = int(sorted_g.loc[j, "index"])
                bucket_assignment[(spot_id, row_idx)] = bname
            idx += n_assign
        # remaining combos (if any) → last bucket
        while idx < len(sorted_g):
            row_idx = int(sorted_g.loc[idx, "index"])
            bucket_assignment[(spot_id, row_idx)] = BUCKET_ORDER[-1]
            idx += 1

    # Apply assignments
    df["equity_bucket"] = df.apply(
        lambda r: bucket_assignment.get((r["spot_id"], r.name), "unknown"),
        axis=1,
    )
    print(f"Bucket assignment dist:")
    print(df["equity_bucket"].value_counts())

    # Save augmented dataset
    df.to_csv(OUT_CSV, index=False)
    print(f"Saved → {OUT_CSV}")

    # Build markdown report
    md = ["# Equity-Bucket Decision Model", ""]
    md += [f"Source: {len(df)} rows / {df['spot_id'].nunique()} spots", ""]

    # 1. Overall bucket × bet_freq
    md += ["## 1. Bet frequency by equity bucket (overall)", ""]
    md += ["| bucket | n_rows | bet_freq_median | bet_freq_mean |"]
    md += ["|---|---:|---:|---:|"]
    for b in BUCKET_ORDER:
        sub = df[df["equity_bucket"] == b]
        if len(sub) == 0:
            md += [f"| {b} | 0 | — | — |"]
            continue
        md += [f"| {b} | {len(sub)} | {sub['bet_freq'].median()*100:.1f}% | {sub['bet_freq'].mean()*100:.1f}% |"]
    md += [""]

    # 2. By context (street, hero_rel, line)
    md += ["## 2. Bucket × context", ""]
    df["context"] = df["street"] + "/" + df["hero_rel"] + "/" + df["line"]
    for ctx, sub in df.groupby("context"):
        if len(sub) < 100:
            continue
        md += [f"### {ctx} (n={len(sub)})", ""]
        md += ["| bucket | n | bet_freq_median |"]
        md += ["|---|---:|---:|"]
        for b in BUCKET_ORDER:
            cell = sub[sub["equity_bucket"] == b]
            if len(cell) < 20:
                md += [f"| {b} | {len(cell)} | — |"]
                continue
            md += [f"| {b} | {len(cell)} | {cell['bet_freq'].median()*100:.1f}% |"]
        md += [""]

    # 3. Bucket × Board family
    md += ["## 3. Bucket × board family (overall)", ""]
    # need board_family — add quick derive
    from train_tree import add_features
    df_ext = add_features(df)
    for bf, sub in df_ext.groupby("board_family"):
        if len(sub) < 200:
            continue
        md += [f"### {bf} (n={len(sub)})", ""]
        md += ["| bucket | n | bet_freq_median |"]
        md += ["|---|---:|---:|"]
        for b in BUCKET_ORDER:
            cell = sub[sub["equity_bucket"] == b]
            if len(cell) < 30:
                md += [f"| {b} | {len(cell)} | — |"]
                continue
            md += [f"| {b} | {len(cell)} | {cell['bet_freq'].median()*100:.1f}% |"]
        md += [""]

    # 4. EV gap analysis: do confident actions (high gap) follow bucket pattern more cleanly?
    md += ["## 4. Bucket pattern at HIGH EV gap (>0.5 — clear best action)", ""]
    sub = df[df["ev_gap"] > 0.5]
    md += [f"n={len(sub)} ({len(sub)/len(df)*100:.1f}% of data)", ""]
    md += ["| bucket | n | bet_freq_median |"]
    md += ["|---|---:|---:|"]
    for b in BUCKET_ORDER:
        cell = sub[sub["equity_bucket"] == b]
        if len(cell) < 30:
            md += [f"| {b} | {len(cell)} | — |"]
            continue
        md += [f"| {b} | {len(cell)} | {cell['bet_freq'].median()*100:.1f}% |"]
    md += [""]

    OUT_MD.write_text("\n".join(md))
    print(f"Report → {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
