#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Build a single-formula bet/check decision rule from MV + DV + Board.

Goal: memorizable integer score that uses all 3 axes, with binary BET/CHECK output.
Evaluate against actual GTO bet_freq:
  - "data label" = BET if bet_freq >= 0.50, else CHECK
  - Accuracy = % of rows where formula matches data label
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402
from full_tables import mv_band  # noqa: E402


# ── Formula coefficients (tuneable) ──
MV_SCORE = {"air": 0, "weak": 1, "mid": 1, "strong": 3, "nut": 6}
DV_SCORE = {
    "no_draw": 0,
    "twocards_bdfd": 2,
    "onecard_bdfd": 1,
    "gutshot": 2,
    "fd": 3,
    "flush_draw": 3,
    "nut_flush_draw": 3,
    "oesd": 3,
    "combo_draw": 4,
}
BOARD_SCORE = {
    "monotone": -2,
    "dynamic_2tone": -3,
    "dry_high": 0,
    "dynamic": 0,
    "low_dry": 0,
    "paired": 3,
}
THRESHOLD = 3  # BET if score >= THRESHOLD


def score_row(row) -> int:
    mv = mv_band(row["mv_cat"])
    return (
        MV_SCORE.get(mv, 0)
        + DV_SCORE.get(row["dv_cat"], 0)
        + BOARD_SCORE.get(row["board_family"], 0)
    )


def main() -> int:
    df = pd.read_csv("scripts/three_class_model/dataset_gtow.csv", low_memory=False)
    df = add_features(df)
    df["mv_band"] = df["mv_cat"].apply(mv_band)
    df = df[(df["mv_band"] != "unknown") & (df["dv_cat"] != "unknown")]

    # Focus on Cash IP Flop SRP (where the existing 25-cell applies)
    base = df[(df["family"] == "cash") & (df["street"] == "flop") & (df["line"] == "srp") & (df["hero_rel"] == "IP")]
    print(f"Eval on Cash IP Flop SRP: {len(base)} rows")

    base["formula_score"] = base.apply(score_row, axis=1)
    base["formula_bet"] = base["formula_score"] >= THRESHOLD
    base["data_bet"] = base["bet_freq"] >= 0.50

    overall_acc = (base["formula_bet"] == base["data_bet"]).mean()
    print(f"\n=== Single-formula accuracy ===")
    print(f"BET if Score >= {THRESHOLD}, where Score = MV + DV + Board")
    print(f"  MV  : {MV_SCORE}")
    print(f"  DV  : {DV_SCORE}")
    print(f"  Brd : {BOARD_SCORE}")
    print()
    print(f"Overall accuracy: {overall_acc*100:.1f}%")

    # Precision/recall for BET and CHECK
    tp = ((base["formula_bet"]) & (base["data_bet"])).sum()
    tn = ((~base["formula_bet"]) & (~base["data_bet"])).sum()
    fp = ((base["formula_bet"]) & (~base["data_bet"])).sum()
    fn = ((~base["formula_bet"]) & (base["data_bet"])).sum()
    print(f"  BET precision={tp/max(tp+fp,1)*100:.1f}% recall={tp/max(tp+fn,1)*100:.1f}%")
    print(f"  CHECK precision={tn/max(tn+fn,1)*100:.1f}% recall={tn/max(tn+fp,1)*100:.1f}%")

    # By board × MV breakdown
    print(f"\n=== Per (board × MV-band) — formula prediction vs data median ===")
    band_order = ["air", "weak", "mid", "strong", "nut"]
    bf_order = ["dry_high", "dynamic", "dynamic_2tone", "low_dry", "monotone", "paired"]
    print(f"  {'board':18s} {'band':6s}  formula  data%  match?")
    print(f"  {'-'*18} {'-'*6}  -------  -----  ------")
    for bf in bf_order:
        for band in band_order:
            sub = base[(base["board_family"] == bf) & (base["mv_band"] == band) & (base["dv_cat"] == "no_draw")]
            if len(sub) < 30:
                continue
            data_pct = sub["bet_freq"].median() * 100
            data_bet = data_pct >= 50
            formula_score = MV_SCORE[band] + 0 + BOARD_SCORE[bf]
            formula_bet = formula_score >= THRESHOLD
            match = "✓" if (formula_bet == data_bet) else "✗"
            print(f"  {bf:18s} {band:6s}  {'BET' if formula_bet else 'CHK':3s}({formula_score:+d})  {data_pct:4.0f}%   {match}")

    # DV impact check
    print(f"\n=== DV effect (dry_high only) — formula prediction vs data median ===")
    print(f"  {'mv_band':8s} {'dv':18s}  formula  data%  match?")
    for band in band_order:
        for dv in ["no_draw", "twocards_bdfd", "onecard_bdfd", "gutshot", "flush_draw", "oesd"]:
            sub = base[(base["board_family"] == "dry_high") & (base["mv_band"] == band) & (base["dv_cat"] == dv)]
            if len(sub) < 30:
                continue
            data_pct = sub["bet_freq"].median() * 100
            data_bet = data_pct >= 50
            formula_score = MV_SCORE[band] + DV_SCORE.get(dv, 0) + 0
            formula_bet = formula_score >= THRESHOLD
            match = "✓" if (formula_bet == data_bet) else "✗"
            print(f"  {band:8s} {dv:18s}  {'BET' if formula_bet else 'CHK':3s}({formula_score:+d})  {data_pct:4.0f}%   {match}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
