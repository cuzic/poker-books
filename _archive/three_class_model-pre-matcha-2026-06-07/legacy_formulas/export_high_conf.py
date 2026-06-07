#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Export HIGH confidence cells for both attack and defense.

For book inclusion: "instant-decision" cells where IQR < 10% and bet/fold/call
freq is highly consistent across combos.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"
BET_ATK = ROOT / "scripts" / "three_class_model" / "attack_bet_size.csv"
BET_DEF = ROOT / "scripts" / "three_class_model" / "spot_bet_info.csv"

OUT_DIR = ROOT / "scripts" / "three_class_model"


def freq_to_3band_attack(f):
    if f < 0.25: return "CHECK主体"
    if f < 0.75: return "MIX(混合)"
    return "BET主体"


def actual_modal_defense(row):
    f = row.get("fold_freq", 0) or 0
    c = row.get("call_freq", 0) or 0
    r = row.get("raise_freq", 0) or 0
    a = {"FOLD": f, "CALL": c, "RAISE": r}
    return max(a, key=lambda k: a[k])


def size_bucket(s):
    if pd.isna(s): return "unknown"
    if s < 0.45: return "small (≤33%)"
    if s < 0.85: return "mid (50%)"
    return "big (≥85%)"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    bet_atk = pd.read_csv(BET_ATK)[["spot_id", "primary_size_pot"]].drop_duplicates(subset=["spot_id"])
    bet_def = pd.read_csv(BET_DEF)[["spot_id", "bet_size_pot_ratio"]].drop_duplicates(subset=["spot_id"])
    df = df.merge(bet_atk, on="spot_id", how="left")
    df = df.merge(bet_def, on="spot_id", how="left")
    df["bet_size_pot"] = df["primary_size_pot"].fillna(df["bet_size_pot_ratio"])
    df["size_bucket"] = df["bet_size_pot"].apply(size_bucket)

    df = df[df["eq_percentile"].notna() & df["equity_bucket"].notna() & (df["equity_bucket"] != "")].copy()

    # ── ATTACK cells ──
    atk = df[df["action_context"] == "attack"].copy()
    atk["actual_band"] = atk["bet_freq"].apply(freq_to_3band_attack)
    print(f"Attack rows: {len(atk)}")

    keys_a = ["size_bucket", "equity_bucket", "mv_cat", "board_family", "dv_cat"]
    cell_a = atk.groupby(keys_a)["bet_freq"].agg([
        ("median", "median"),
        ("count", "count"),
        ("q25", lambda x: x.quantile(0.25)),
        ("q75", lambda x: x.quantile(0.75)),
    ]).reset_index()
    cell_a["iqr"] = cell_a["q75"] - cell_a["q25"]
    cell_a["pred_band"] = cell_a["median"].apply(freq_to_3band_attack)
    cell_a_high = cell_a[(cell_a["iqr"] < 0.10) & (cell_a["count"] >= 30)].copy()
    cell_a_high = cell_a_high.sort_values(["board_family", "equity_bucket", "mv_cat", "size_bucket"])
    print(f"Attack HIGH cells (IQR<10%, n>=30): {len(cell_a_high)}")

    # ── DEFENSE cells ──
    defe = df[df["action_context"] == "defense"].copy()
    defe["actual_modal"] = defe.apply(actual_modal_defense, axis=1)
    print(f"\nDefense rows: {len(defe)}")

    keys_d = ["size_bucket", "equity_bucket", "mv_cat", "board_family", "dv_cat"]
    # cell-level FOLD/CALL/RAISE share
    cell_d = defe.groupby(keys_d).agg(
        n=("bet_freq", "count"),
        fold_mean=("fold_freq", "mean"),
        call_mean=("call_freq", "mean"),
        raise_mean=("raise_freq", "mean"),
        fold_iqr=("fold_freq", lambda x: x.quantile(0.75) - x.quantile(0.25)),
        call_iqr=("call_freq", lambda x: x.quantile(0.75) - x.quantile(0.25)),
    ).reset_index()
    cell_d["primary_iqr"] = cell_d[["fold_iqr", "call_iqr"]].max(axis=1)
    # modal action
    def modal_of(row):
        d = {"FOLD": row["fold_mean"], "CALL": row["call_mean"], "RAISE": row["raise_mean"]}
        return max(d, key=lambda k: d[k])
    cell_d["pred_modal"] = cell_d.apply(modal_of, axis=1)
    cell_d_high = cell_d[(cell_d["primary_iqr"] < 0.10) & (cell_d["n"] >= 30)].copy()
    cell_d_high = cell_d_high.sort_values(["board_family", "equity_bucket", "mv_cat", "size_bucket"])
    print(f"Defense HIGH cells (IQR<10%, n>=30): {len(cell_d_high)}")

    # ── Save CSVs ──
    atk_path = OUT_DIR / "HIGH_CONFIDENCE_ATTACK.csv"
    cell_a_high[["size_bucket", "equity_bucket", "mv_cat", "board_family", "dv_cat",
                  "median", "iqr", "count", "pred_band"]].to_csv(atk_path, index=False)
    print(f"\nSaved → {atk_path}")
    def_path = OUT_DIR / "HIGH_CONFIDENCE_DEFENSE.csv"
    cell_d_high[["size_bucket", "equity_bucket", "mv_cat", "board_family", "dv_cat",
                  "fold_mean", "call_mean", "raise_mean", "n", "pred_modal"]].to_csv(def_path, index=False)
    print(f"Saved → {def_path}")

    # ── Build markdown report ──
    md = []
    md.append("# HIGH-Confidence Postflop Decision Cells")
    md.append(f"\nGenerated from {len(df):,} rows ({df['spot_id'].nunique()} spots).")
    md.append(f"HIGH confidence = IQR < 10%, n ≥ 30. These are 'instant decision' cells.")
    md.append(f"\n## Summary")
    md.append(f"- Attack HIGH cells: **{len(cell_a_high)}** cells")
    md.append(f"- Defense HIGH cells: **{len(cell_d_high)}** cells")

    # ── Attack table ──
    md.append(f"\n## Attack (acting first / facing no bet)\n")
    md.append("BET主体 = 80%+ bet、CHECK主体 = <20% bet、MIX = 混合\n")
    md.append(f"### BET主体 セル (always bet)\n")
    md.append("| board | bucket | MV | DV | size | median bet | n |")
    md.append("|---|---|---|---|---|---:|---:|")
    for _, r in cell_a_high[cell_a_high["pred_band"] == "BET主体"].iterrows():
        md.append(f"| {r['board_family']} | {r['equity_bucket']} | {r['mv_cat']} | {r['dv_cat']} | {r['size_bucket']} | {r['median']*100:.0f}% | {int(r['count'])} |")

    md.append(f"\n### CHECK主体 セル (always check)\n")
    md.append("| board | bucket | MV | DV | size | median bet | n |")
    md.append("|---|---|---|---|---|---:|---:|")
    for _, r in cell_a_high[cell_a_high["pred_band"] == "CHECK主体"].iterrows():
        md.append(f"| {r['board_family']} | {r['equity_bucket']} | {r['mv_cat']} | {r['dv_cat']} | {r['size_bucket']} | {r['median']*100:.0f}% | {int(r['count'])} |")

    # ── Defense table ──
    md.append(f"\n## Defense (facing a bet)\n")
    md.append(f"### FOLD modal セル (always fold)\n")
    md.append("| board | bucket | MV | DV | bet_size | F | C | R | n |")
    md.append("|---|---|---|---|---|---:|---:|---:|---:|")
    for _, r in cell_d_high[cell_d_high["pred_modal"] == "FOLD"].iterrows():
        md.append(f"| {r['board_family']} | {r['equity_bucket']} | {r['mv_cat']} | {r['dv_cat']} | {r['size_bucket']} | {r['fold_mean']*100:.0f}% | {r['call_mean']*100:.0f}% | {r['raise_mean']*100:.0f}% | {int(r['n'])} |")

    md.append(f"\n### CALL modal セル (always call)\n")
    md.append("| board | bucket | MV | DV | bet_size | F | C | R | n |")
    md.append("|---|---|---|---|---|---:|---:|---:|---:|")
    for _, r in cell_d_high[cell_d_high["pred_modal"] == "CALL"].iterrows():
        md.append(f"| {r['board_family']} | {r['equity_bucket']} | {r['mv_cat']} | {r['dv_cat']} | {r['size_bucket']} | {r['fold_mean']*100:.0f}% | {r['call_mean']*100:.0f}% | {r['raise_mean']*100:.0f}% | {int(r['n'])} |")

    md.append(f"\n### RAISE modal セル (always raise)\n")
    md.append("| board | bucket | MV | DV | bet_size | F | C | R | n |")
    md.append("|---|---|---|---|---|---:|---:|---:|---:|")
    for _, r in cell_d_high[cell_d_high["pred_modal"] == "RAISE"].iterrows():
        md.append(f"| {r['board_family']} | {r['equity_bucket']} | {r['mv_cat']} | {r['dv_cat']} | {r['size_bucket']} | {r['fold_mean']*100:.0f}% | {r['call_mean']*100:.0f}% | {r['raise_mean']*100:.0f}% | {int(r['n'])} |")

    md_path = OUT_DIR / "HIGH_CONFIDENCE_CELLS.md"
    md_path.write_text("\n".join(md))
    print(f"Saved → {md_path}")

    # ── Print quick visualization ──
    print(f"\n=== ATTACK summary ===")
    print(cell_a_high.groupby("pred_band").size())
    print(f"\n=== DEFENSE summary ===")
    print(cell_d_high.groupby("pred_modal").size())

    # ── Sample inspection: most populated HIGH cells ──
    print(f"\n=== TOP 15 ATTACK HIGH cells by n ===")
    top_a = cell_a_high.sort_values("count", ascending=False).head(15)
    for _, r in top_a.iterrows():
        print(f"  {r['board_family']:18s} {r['equity_bucket']:13s} {r['mv_cat']:15s} {r['dv_cat']:18s} {r['size_bucket']:15s}  med={r['median']*100:5.0f}%  →{r['pred_band']:11s} n={int(r['count'])}")

    print(f"\n=== TOP 15 DEFENSE HIGH cells by n ===")
    top_d = cell_d_high.sort_values("n", ascending=False).head(15)
    for _, r in top_d.iterrows():
        print(f"  {r['board_family']:18s} {r['equity_bucket']:13s} {r['mv_cat']:15s} {r['dv_cat']:18s} {r['size_bucket']:15s}  F={r['fold_mean']*100:3.0f}% C={r['call_mean']*100:3.0f}% R={r['raise_mean']*100:3.0f}%  →{r['pred_modal']:5s} n={int(r['n'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
