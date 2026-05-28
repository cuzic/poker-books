#!/usr/bin/env python3
"""
Light UCBS v2 - CBS-band base 表で精度向上 + 暗算可能

設計:
- CBS バンド (0-2 air / 3-4 weak / 5-6 mid / 7-8 strong / 9+ nut) で 5 区分
- context は 5 種 (cash/mtt_short/mtt_deep/3bp/turn)
- 合計 25 数値 + 例外 (low_pair -10 のみ)
- 暗算ステップ: HP+DP → CBS → context+band で freq → 微調整
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")
from ucbs_v2 import HP_TABLE, DP_TABLE


def cbs_band(cbs: int) -> str:
    """CBS を 5 バンドに分類"""
    if cbs <= 2: return "air"
    if cbs <= 4: return "weak"
    if cbs <= 6: return "mid"
    if cbs <= 8: return "strong"
    return "nut"


# 5 context × 5 band の base 表 (合計 25 数値、暗算で覚えやすく丸め)
LIGHT_V2_BASE = {
    # データ fit ベース、暗記しやすく丸め
    "cash":      {"air": 0.45, "weak": 0.40, "mid": 0.40, "strong": 0.60, "nut": 0.60},
    "mtt_short": {"air": 0.40, "weak": 0.30, "mid": 0.35, "strong": 0.60, "nut": 0.75},
    "mtt_deep":  {"air": 0.40, "weak": 0.40, "mid": 0.40, "strong": 0.60, "nut": 0.60},
    "3bp":       {"air": 0.45, "weak": 0.50, "mid": 0.60, "strong": 0.70, "nut": 0.60},
    "turn":      {"air": 0.05, "weak": 0.05, "mid": 0.10, "strong": 0.30, "nut": 0.40},
}

# 例外: low_pair (trash) は context 問わず -10
LIGHT_V2_OFFSET = {
    "low_pair": -0.10,
}


def light_ucbs_v2(hand: str, draw: str, context: str = "cash") -> float:
    """暗算ステップ:
    1. HP + DP = CBS
    2. CBS → band
    3. LIGHT_V2_BASE[context][band]
    4. low_pair なら -10
    """
    hp = HP_TABLE.get(hand, 0)
    dp = DP_TABLE.get(draw, 0)
    cbs = hp + dp
    band = cbs_band(cbs)
    base = LIGHT_V2_BASE[context][band]
    base += LIGHT_V2_OFFSET.get(hand, 0.0)
    return max(0.05, min(0.95, base))


def fit_light_v2():
    """データから 5 context × 5 band の best fit を計算"""
    files = {
        "cash":      [("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json", "cash")],
        "mtt_short": [
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_SRP25.jsonl", "mtt"),
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT50BB.jsonl", "mtt"),
        ],
        "mtt_deep": [
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT100BB.jsonl", "mtt"),
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT200BB.jsonl", "mtt"),
        ],
        "3bp": [
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP25.jsonl", "mtt"),
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP50.jsonl", "mtt"),
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP100.jsonl", "mtt"),
        ],
        "turn": [
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl", "mtt"),
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT50_BTN.jsonl", "mtt"),
            ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_CASH100_BTN.jsonl", "mtt"),
        ],
    }

    print("=" * 70)
    print("Light UCBS v2 — context × band の最適値計算")
    print("=" * 70)
    new_base = {}
    for ctx, file_list in files.items():
        band_agg = {b: {"sum": 0, "n": 0} for b in ["air", "weak", "mid", "strong", "nut"]}
        for fp, fmt in file_list:
            if not Path(fp).exists():
                continue
            records = load_records(fp, fmt)
            for r in records:
                cbs = HP_TABLE.get(r["hand"], 0) + DP_TABLE.get(r.get("draw", "no_draw"), 0)
                band = cbs_band(cbs)
                band_agg[band]["sum"] += r["n"] * r["gto"]
                band_agg[band]["n"] += r["n"]
        new_base[ctx] = {}
        for b, vals in band_agg.items():
            if vals["n"] > 0:
                avg = vals["sum"] / vals["n"]
                new_base[ctx][b] = round(avg * 100) / 100
        print(f"  {ctx}: {new_base[ctx]}")
    return new_base


def load_records(fp, fmt):
    out = []
    if fmt == "cash":
        with open(fp) as f:
            data = json.load(f)
        for pos, boards in data.items():
            for board_key, info in boards.items():
                for h, vals in info.get("hand_cats", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("combos", 0)
                    if n < 5: continue
                    out.append({"hand": h, "n": n,
                                "gto": vals["bet_pct"]/100.0, "draw": "no_draw"})
    else:
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("total", 0)
                    if n < 3: continue
                    out.append({"hand": h, "n": n,
                                "gto": vals["bet_pct"]/100.0, "draw": "no_draw"})
    return out


def evaluate_against_v2():
    test = {
        "cash_100bb": ("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json", "cash", "cash"),
        "mtt_25bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_SRP25.jsonl", "mtt", "mtt_short"),
        "mtt_50bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT50BB.jsonl", "mtt", "mtt_short"),
        "mtt_100bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT100BB.jsonl", "mtt", "mtt_deep"),
        "mtt_200bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT200BB.jsonl", "mtt", "mtt_deep"),
        "3bp_25bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP25.jsonl", "mtt", "3bp"),
        "3bp_50bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP50.jsonl", "mtt", "3bp"),
        "3bp_100bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP100.jsonl", "mtt", "3bp"),
        "turn_mtt25": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl", "mtt", "turn"),
        "turn_cash100": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_CASH100_BTN.jsonl", "mtt", "turn"),
    }
    full_v2 = {
        "cash_100bb": 16.43, "mtt_25bb": 15.46, "mtt_50bb": 12.96,
        "mtt_100bb": 21.95, "mtt_200bb": 14.10,
        "3bp_25bb": 18.65, "3bp_50bb": 8.62, "3bp_100bb": 13.37,
        "turn_mtt25": 7.02, "turn_cash100": 16.11,
    }
    print("\n" + "=" * 70)
    print("Light UCBS v2 評価 (vs フル UCBS-v2)")
    print("=" * 70)
    print(f"{'context':>16s}  {'Light v2':>9s}  {'Full v2':>8s}  {'差':>6s}")
    print("-" * 60)
    for label, (fp, fmt, ctx) in test.items():
        if not Path(fp).exists():
            continue
        records = load_records(fp, fmt)
        if not records: continue
        sse, total_n = 0.0, 0.0
        for r in records:
            pred = light_ucbs_v2(r["hand"], r.get("draw", "no_draw"), ctx)
            err = pred - r["gto"]
            sse += r["n"] * err * err
            total_n += r["n"]
        wrmse = (sse / total_n) ** 0.5 if total_n else 0
        full = full_v2.get(label, 0)
        diff = (wrmse * 100) - full
        marker = " ◎" if diff < 3 else (" ○" if diff < 6 else (" △" if diff < 10 else " ×"))
        print(f"  {label:>14s}  {wrmse*100:>7.2f}%  {full:>6.2f}%  {diff:>+5.2f}pt{marker}")


def show_table():
    print("\n" + "=" * 70)
    print("Light UCBS v2 — 暗記用 25-cell 表")
    print("=" * 70)
    print(f"{'context':>12s}  " + "  ".join(f"{b:>6s}" for b in ["air", "weak", "mid", "strong", "nut"]))
    print("-" * 60)
    for ctx, bands in LIGHT_V2_BASE.items():
        row = [f"{ctx:>12s}"]
        for b in ["air", "weak", "mid", "strong", "nut"]:
            row.append(f"{bands[b]*100:>5.0f}%")
        print("  ".join(row))
    print("\n例外: low_pair -10pt (context 共通)")


if __name__ == "__main__":
    # データから best fit を計算
    new_base = fit_light_v2()
    # ハードコード値の精度を測定
    evaluate_against_v2()
    show_table()
