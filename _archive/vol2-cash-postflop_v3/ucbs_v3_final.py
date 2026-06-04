#!/usr/bin/env python3
"""
UCBS-v3 最終モデル (A + C3 Board family)

定義:
  freq = base[ctx5][band]                      ← Vol2 と同じ 25 cell
       + α[ctx13]                              ← context lift
       + β[ctx13] · I(CBS ≥ 7)                 ← 強い役の追加 lift
       + cat_offset[hand_category]             ← slowplay/trash/premium
       + ε[board_family][ctx_group]            ← 板テクスチャ別 (C3)

context 5 群: cash / mtt_short / mtt_deep / 3bp / turn
context 13 個: cash_100bb, mtt_25/50/100/200bb, mtt_3bp_20/25/50/100bb,
              {mtt_25,50,100,cash_100}bb_turn_btn
board family: dry_high (baseline) / paired / dynamic / low_dry
ctx group: cash / mtt_srp / 3bp

fit: WLS、combos 加重、ridge λ=0.001、Stage 1 で base、Stage 2 で全 layer
精度: 全体 WRMSE 18.32%、63 params
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ucbs_candidates_fit import CTX13, CTX13_TO_5, BANDS, cbs_band, load_all
from ucbs_v3_axes import board_family, ctx_group, AxisModel


def main():
    print("Loading data...")
    records = load_all()
    print(f"Loaded {len(records)} records, {sum(r['n'] for r in records):.0f} combos\n")

    print("Fitting A+C3 model...")
    model = AxisModel(["C3"])
    model.fit(records)

    # ── parameter dump ──
    params = {
        "model": "UCBS-v3 (A+C3 Board family)",
        "version": "1.0",
        "n_params": model.n_params(),
        "formula": (
            "freq = base[ctx5][band] + α[ctx13] + β[ctx13]·I(CBS≥7) "
            "+ cat_offset[cat] + ε[board_family][ctx_group]"
        ),
        "base": {},        # base[ctx5][band]
        "alpha": {},       # α[ctx13]
        "beta": {},        # β[ctx13]
        "cat_offset": {"default": 0.0},
        "epsilon": {},     # ε[board_family][ctx_group]
        "tables": {
            "HP": {"flush_combo": 9, "trips_set": 9, "two_pair": 8,
                    "top_pair": 7, "second_pair": 5, "low_pair": 3,
                    "high_card": 2},
            "DP": {"no_draw": 0, "gutshot": 1, "oesd": 2, "fd": 2, "combo_draw": 3},
            "bands": {"air": "CBS 0-2", "weak": "CBS 3-4", "mid": "CBS 5-6",
                       "strong": "CBS 7-8", "nut": "CBS 9+"},
            "categories": {"slowplay": "set/trips/two_pair/fullhouse/flush/straight/quads",
                            "trash": "low_pair (5 以下の pair)",
                            "premium": "overpair / underpair"},
            "board_families": {
                "dry_high": "ペアなし、J 以上のハイカード、ストフラ系なし (baseline)",
                "paired": "ボードに同ランクが含まれる",
                "dynamic": "モノトーン、または連結 + ツーフラ",
                "low_dry": "ペアなし、ハイカード T 以下、ドロー薄",
            },
            "ctx_groups": {"cash": ["cash_100bb", "cash_100bb_turn_btn"],
                            "mtt_srp": ["mtt_25bb", "mtt_50bb", "mtt_100bb", "mtt_200bb",
                                        "mtt_25bb_turn_btn", "mtt_50bb_turn_btn",
                                        "mtt_100bb_turn_btn"],
                            "3bp": ["mtt_3bp_20bb", "mtt_3bp_25bb",
                                     "mtt_3bp_50bb", "mtt_3bp_100bb"]},
        },
    }

    # base
    for (c5, band), v in model.base.items():
        params["base"].setdefault(c5, {})[band] = round(v, 4)

    # α / β
    for c in CTX13:
        params["alpha"][c] = round(model.theta[model.idx[("alpha", c)]], 4)
        params["beta"][c] = round(model.theta[model.idx[("beta", c)]], 4)

    # cat_offset
    for cat in ("slowplay", "trash", "premium"):
        params["cat_offset"][cat] = round(model.theta[model.idx[("cat", cat)]], 4)

    # epsilon
    for fam in ("paired", "dynamic", "low_dry"):
        params["epsilon"][fam] = {}
        for cg in ("cash", "mtt_srp", "3bp"):
            params["epsilon"][fam][cg] = round(model.theta[model.idx[("c3", (fam, cg))]], 4)
    # baseline (dry_high) は 0
    params["epsilon"]["dry_high"] = {"cash": 0.0, "mtt_srp": 0.0, "3bp": 0.0}

    out_path = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/ucbs_v3_params.json")
    out_path.write_text(json.dumps(params, indent=2, ensure_ascii=False))
    print(f"\n書き出し: {out_path}")

    # ── 人間向け Markdown 表 ──
    md = ["# UCBS-v3 確定パラメータ (A+C3 Board family)\n",
          f"全 {model.n_params()} params、WRMSE {18.32:.2f}%\n",
          "## 1. Vol2 base[ctx5][band] (25 cell)\n",
          "| ctx5 | air | weak | mid | strong | nut |",
          "|---|---:|---:|---:|---:|---:|"]
    for c5 in ("cash", "mtt_short", "mtt_deep", "3bp", "turn"):
        row = [c5]
        for band in BANDS:
            v = params["base"].get(c5, {}).get(band)
            row.append(f"{v*100:.0f}%" if v is not None else "—")
        md.append("| " + " | ".join(row) + " |")

    md.append("\n## 2. α[ctx13] / β[ctx13] (context lift)\n")
    md.append("| ctx13 | α | β (CBS≥7) |")
    md.append("|---|---:|---:|")
    for c in CTX13:
        a = params["alpha"][c]
        b = params["beta"][c]
        md.append(f"| {c} | {a*100:+.0f} | {b*100:+.0f} |")

    md.append("\n## 3. Category offset\n")
    md.append("| category | offset |")
    md.append("|---|---:|")
    for cat in ("default", "slowplay", "trash", "premium"):
        md.append(f"| {cat} | {params['cat_offset'][cat]*100:+.0f} |")

    md.append("\n## 4. Board family ε[family][ctx_group]\n")
    md.append("| family | cash | mtt_srp | 3bp |")
    md.append("|---|---:|---:|---:|")
    for fam in ("dry_high", "paired", "dynamic", "low_dry"):
        row = [fam]
        for cg in ("cash", "mtt_srp", "3bp"):
            v = params["epsilon"][fam][cg]
            row.append(f"{v*100:+.0f}")
        md.append("| " + " | ".join(row) + " |")

    md.append("\n## 5. 板分類ロジック\n")
    md.append("```")
    md.append("paired      ← ボードに同ランクあり")
    md.append("dynamic     ← モノトーン OR (ストレート連結 + ツーフラ)")
    md.append("dry_high    ← 上記以外で、最高ランク J 以上 (baseline)")
    md.append("low_dry     ← 上記以外で、最高ランク T 以下")
    md.append("```\n")

    md_path = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/UCBS_V3_PARAMS.md")
    md_path.write_text("\n".join(md))
    print(f"書き出し: {md_path}")


if __name__ == "__main__":
    main()
