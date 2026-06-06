#!/usr/bin/env python3
# Run with: python3 build_unified_rows.py  (requires system pandas)
"""
build_unified_rows.py
---------------------
Merges all probe phase CSV files into a single unified dataset.

Input files (relative to this script's directory):
  probe_priority_rows.csv  -> source_phase = 'priority'
  probe_phase2_rows.csv    -> source_phase = 'phase2'
  probe_phase3_rows.csv    -> source_phase = 'phase3'
  probe_phase4_rows.csv    -> source_phase = 'phase4'
  probe_phase5_rows.csv    -> source_phase = 'phase5'
  probe_phase6_rows.csv    -> source_phase = 'phase6'
  past_r1_rows.csv         -> source_phase = 'past_r1'

Output:
  ../../scripts/three_class_model/dataset_unified_v2.csv

Notes:
  - All input files share identical 38-column schemas, so no outer-join padding needed.
  - Duplicate rows (scenario_ids N_mtt_3bp_flop, N_mtt200_turn, N_mtt200_river appear
    in both priority and phase2) are deduplicated: priority takes precedence.
  - Missing input CSVs are skipped gracefully.
"""

import os
import sys
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "../../scripts/three_class_model/dataset_unified_v2.csv")

INPUT_FILES = [
    ("priority", os.path.join(SCRIPT_DIR, "probe_priority_rows.csv")),
    ("phase2",   os.path.join(SCRIPT_DIR, "probe_phase2_rows.csv")),
    ("phase3",   os.path.join(SCRIPT_DIR, "probe_phase3_rows.csv")),
    ("phase4",   os.path.join(SCRIPT_DIR, "probe_phase4_rows.csv")),
    ("phase5",   os.path.join(SCRIPT_DIR, "probe_phase5_rows.csv")),
    ("phase6",   os.path.join(SCRIPT_DIR, "probe_phase6_rows.csv")),
    ("past_r1",  os.path.join(SCRIPT_DIR, "past_r1_rows.csv")),
]

# Scenario IDs that appear in multiple phases and must be deduplicated.
# priority is fetched first so it takes precedence; phase2 duplicates are dropped.
DEDUP_PREFER_FIRST = {
    "N_mtt_3bp_flop",
    "N_mtt200_turn",
    "N_mtt200_river",
}


def load_csv(phase_name: str, path: str) -> pd.DataFrame | None:
    if not os.path.exists(path):
        print(f"  [SKIP] {path} not found — regenerate with: python3 probe_{phase_name}.py")
        return None
    df = pd.read_csv(path, dtype=str)
    df.insert(0, "source_phase", phase_name)
    print(f"  [OK]   {os.path.basename(path)}: {len(df):,} rows, {len(df.columns)} cols")
    return df


def main():
    print("=== build_unified_rows.py ===\n")
    print("Loading input CSVs...")
    frames = []
    for phase_name, path in INPUT_FILES:
        df = load_csv(phase_name, path)
        if df is not None:
            frames.append(df)

    if not frames:
        print("ERROR: No input files found. Aborting.")
        sys.exit(1)

    print(f"\nConcatenating {len(frames)} DataFrames (outer-join schema)...")
    combined = pd.concat(frames, axis=0, ignore_index=True, sort=False)
    total_before_dedup = len(combined)
    print(f"  Total rows before dedup: {total_before_dedup:,}")

    # Deduplicate: for scenario_ids that appear in both priority and phase2,
    # keep only the first occurrence (priority rows come first).
    # A row is a duplicate if (scenario_id, board_str, card_a, card_b) is repeated.
    dedup_mask = combined["scenario_id"].isin(DEDUP_PREFER_FIRST)
    dedup_subset = combined[dedup_mask].copy()
    rest = combined[~dedup_mask].copy()

    key_cols = ["scenario_id", "board_str", "card_a", "card_b"]
    dedup_subset = dedup_subset.drop_duplicates(subset=key_cols, keep="first")
    combined = pd.concat([dedup_subset, rest], axis=0, ignore_index=True)

    removed = total_before_dedup - len(combined)
    print(f"  Removed {removed:,} duplicate rows (priority takes precedence over phase2)")
    print(f"  Total rows after dedup: {len(combined):,}")

    # Fill missing values in optional columns with empty string
    combined = combined.fillna("")

    # --- Summary statistics ---
    print("\n=== Row count per scenario_id ===")
    scenario_counts = combined.groupby("scenario_id").size().sort_values(ascending=False)
    for sid, n in scenario_counts.items():
        print(f"  {sid}: {n:,}")

    print("\n=== Row count per source_phase ===")
    phase_counts = combined.groupby("source_phase").size().sort_values(ascending=False)
    for phase, n in phase_counts.items():
        print(f"  {phase}: {n:,}")

    print("\n=== Missing value % per source_phase (formula columns) ===")
    formula_cols = ["formula_action", "formula_loss", "formula_correct"]
    for phase in combined["source_phase"].unique():
        sub = combined[combined["source_phase"] == phase]
        for col in formula_cols:
            if col in sub.columns:
                missing_pct = (sub[col] == "").mean() * 100
                if missing_pct > 0:
                    print(f"  {phase} / {col}: {missing_pct:.1f}% missing")

    print(f"\n=== Schema ({len(combined.columns)} columns) ===")
    print("  " + ", ".join(combined.columns.tolist()))

    # Save output
    output_path = os.path.normpath(OUTPUT_PATH)
    print(f"\nSaving to {output_path} ...")
    combined.to_csv(output_path, index=False)
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"Done. {len(combined):,} rows saved ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
