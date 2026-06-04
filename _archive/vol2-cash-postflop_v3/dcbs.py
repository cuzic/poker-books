#!/usr/bin/env python3
"""
DCBS (Defense CBS) — BB defense (continue freq) 専用モデル、4 context

UCBS-v2 が cbet 用なのに対し、DCBS は OOP defense 用。
構造: HP-based continue freq 表 (context 別) + 少数の kicker 修正

continue_freq = base_dcbs[context][HP] + kicker_offset[context][hand]

注: depth で defense 戦略が大きく変化:
  - 浅 (mtt_25bb): air も 67% continue
  - 深 (mtt_100bb): air は 28% に縮減
"""
from __future__ import annotations
import sys, json
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")
from ucbs_v2 import HP_TABLE


# ─── DCBS context 別パラメータ (4 context) ─────────────────────
DCBS_CONTEXTS = {
    # mtt_25bb: 浅、bet も小さく BB defense 広い
    "mtt_25bb": {
        "base": {2: 0.67, 3: 0.98, 5: 0.99, 7: 1.00, 8: 1.00, 9: 1.00},
        "kicker": {
            "ace_high":     +0.10,
            "king_high":    +0.01,
            "no_made_hand": -0.12,
            "low_pair":     +0.00,
        },
    },
    "mtt_50bb": {
        "base": {2: 0.54, 3: 0.95, 5: 0.96, 7: 1.00, 8: 1.00, 9: 1.00},
        "kicker": {
            "ace_high":     +0.17,
            "king_high":    +0.06,
            "no_made_hand": -0.13,
            "low_pair":     -0.10,
        },
    },
    # mtt_100bb: 深、bet 大きく BB defense 控えめ
    "mtt_100bb": {
        "base": {2: 0.28, 3: 0.84, 5: 0.87, 7: 0.98, 8: 1.00, 9: 1.00},
        "kicker": {
            "ace_high":     +0.05,
            "king_high":    +0.05,
            "no_made_hand": +0.00,
            "low_pair":     -0.10,
        },
    },
    "cash_100bb": {
        "base": {2: 0.40, 3: 0.85, 5: 0.98, 7: 1.00, 8: 1.00, 9: 1.00},
        "kicker": {
            "ace_high":     +0.05,
            "king_high":    +0.00,
            "no_made_hand": -0.03,
            "low_pair":     -0.02,
        },
    },
}


@dataclass
class DCBSDecision:
    hp: int
    base: float
    kicker_offset: float
    continue_freq: float
    fold_freq: float
    hand: str
    context: str


def dcbs_predict(hand_type: str, context: str = "mtt_25bb") -> DCBSDecision:
    """DCBS continue freq 予測"""
    ctx = DCBS_CONTEXTS[context]
    hp = HP_TABLE.get(hand_type, 2)
    # base lookup (HP のフォールバック)
    if hp in ctx["base"]:
        base = ctx["base"][hp]
    elif hp >= 7:
        base = 1.0
    elif hp >= 5:
        base = ctx["base"].get(5, 0.95)
    elif hp >= 3:
        base = ctx["base"].get(3, 0.90)
    else:
        base = ctx["base"].get(2, 0.50)

    kicker = ctx["kicker"].get(hand_type, 0.0) if hp == 2 else 0.0
    cont = max(0.02, min(0.99, base + kicker))
    return DCBSDecision(
        hp=hp, base=base, kicker_offset=kicker,
        continue_freq=cont, fold_freq=1.0 - cont,
        hand=hand_type, context=context,
    )


# ─── 評価 (4 context) ────────────────────────────────
def evaluate():
    files = {
        "mtt_25bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT25_BB.jsonl",
        "mtt_50bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT50_BB.jsonl",
        "mtt_100bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT100_BB.jsonl",
        "cash_100bb": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_CASH100_BB.jsonl",
    }
    print(f"{'context':>14s}  {'records':>7s}  {'combos':>7s}  {'WRMSE':>7s}  {'WMAE':>7s}")
    print("-" * 60)
    for ctx, fp in files.items():
        records = []
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE or vals.get("total", 0) < 3:
                        continue
                    records.append({"hand": h, "n": vals["total"],
                                    "gto": vals["cont_pct"] / 100.0})
        sse, sae, total_n = 0.0, 0.0, 0.0
        for r in records:
            d = dcbs_predict(r["hand"], ctx)
            err = d.continue_freq - r["gto"]
            sse += r["n"] * err * err
            sae += r["n"] * abs(err)
            total_n += r["n"]
        wrmse = (sse / total_n) ** 0.5 if total_n else 0
        wmae = sae / total_n if total_n else 0
        print(f"  {ctx:>12s}  {len(records):>7d}  {int(total_n):>7d}  "
              f"{wrmse*100:>5.2f}%  {wmae*100:>5.2f}%")


if __name__ == "__main__":
    print("=" * 60)
    print("DCBS (Defense CBS) 4 context 評価")
    print("=" * 60)
    evaluate()
    print("\n=== Demo: 各 context で同じ手の continue freq ===")
    for hand in ["no_made_hand", "ace_high", "top_pair", "third_pair"]:
        print(f"\n{hand}:")
        for ctx in DCBS_CONTEXTS.keys():
            d = dcbs_predict(hand, ctx)
            print(f"  {ctx:14s} continue {d.continue_freq*100:5.1f}%")
