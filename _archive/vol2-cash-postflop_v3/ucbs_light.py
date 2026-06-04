#!/usr/bin/env python3
"""
Light UCBS / Light DCBS - 暗算優先の簡易版

設計原則:
1. Confidence (HIGH/MID/LOW) を廃止 → Direction のみ
2. Size (33/116) 一律 33 に統一 (overbet 廃止)
3. Context は 2 区分のみ: "標準" (cash 100bb / mtt 25-50bb) vs "深 MTT/cash deep"
4. 例外ルールは 2 つだけ (trash, premium)
5. β, position lift, A-x, 型6, mono は全廃

合計: 6 step 程度、~5-8 秒で計算可
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")
from ucbs_v2 import HP_TABLE, DP_TABLE
from calc import classify_board_type7
from ucbs_v2 import extract_board_features, parse_board_type


# ════════════════════════════════════════════════════════
# Light UCBS (cbet)
# ════════════════════════════════════════════════════════

# 2 区分の context (深い/標準) × 2 direction = 4 base 値
LIGHT_BASE = {
    "cbet_std":   {True: 0.65, False: 0.40},   # cash 100bb / mtt 25-50bb 標準
    "cbet_deep":  {True: 0.55, False: 0.30},   # mtt_100/200, cash deep (打ち負け多)
    "cbet_3bp":   {True: 0.75, False: 0.40},   # 3BP IP (低 SPR で wide cbet)
    "cbet_turn":  {True: 0.45, False: 0.20},   # turn 2nd barrel (全体 bet 低下)
}

# Hand 別補正 (UCBS-v2 で大きい影響のもののみ)
LIGHT_OFFSET = {
    "low_pair":   -0.20,  # trash
    "overpair":   +0.10,  # premium
    "underpair":  +0.10,  # premium
    # それ以外は補正なし
}


def light_ucbs(hand_type: str, draw_type: str, context: str = "cbet_std") -> float:
    """Light UCBS の cbet freq 予測 (5-8 step)"""
    # Step 1: HP + DP = CBS
    hp = HP_TABLE.get(hand_type, 0)
    dp = DP_TABLE.get(draw_type, 0)
    cbs = hp + dp

    # Step 2: direction (≥5 で bet 寄り)
    direction = (cbs >= 5)

    # Step 3: base lookup
    base = LIGHT_BASE[context][direction]

    # Step 4: 強い役は +10
    if cbs >= 7:
        base += 0.10

    # Step 5: hand offset
    base += LIGHT_OFFSET.get(hand_type, 0.0)

    return max(0.05, min(0.95, base))


# ════════════════════════════════════════════════════════
# Light DCBS (defense)
# ════════════════════════════════════════════════════════

# HP-based simple table + depth 補正
def light_dcbs(hand_type: str, depth_class: str = "shallow") -> float:
    """Light DCBS の continue freq 予測 (3-5 step)
    depth_class: "shallow" (25bb), "mid" (50bb), "deep" (100bb+, cash)
    """
    hp = HP_TABLE.get(hand_type, 2)

    # Step 1: HP 区分で base
    if hp >= 5:
        base = 0.98  # pair (mid+) は call
    elif hp >= 3:
        base = 0.92  # 弱 pair (under/third)
    else:  # HP == 2: air
        if hand_type == "ace_high":
            base = 0.72
        elif hand_type == "no_made_hand":
            base = 0.45
        else:  # king_high, low_pair
            base = 0.60

    # Step 2: depth 補正
    if depth_class == "shallow":  # 25bb
        if hp <= 2:
            base += 0.15  # 浅で air も continue
    elif depth_class == "deep":   # 100bb+
        if hp <= 2:
            base -= 0.20  # 深で air は fold
        elif hp == 3:
            base -= 0.10  # 深で弱 pair も少し fold
    # "mid" は base そのまま

    return max(0.02, min(0.99, base))


# ════════════════════════════════════════════════════════
# 評価関数 (UCBS-v2 のフル context と精度比較)
# ════════════════════════════════════════════════════════

def evaluate_light_ucbs():
    """Light UCBS を主要 context で評価"""
    test_files = {
        "cash_100bb": ("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json", "cbet_std", "cash"),
        "mtt_25bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_SRP25.jsonl", "cbet_std", "mtt"),
        "mtt_50bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT50BB.jsonl", "cbet_std", "mtt"),
        "mtt_100bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT100BB.jsonl", "cbet_deep", "mtt"),
        "mtt_200bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT200BB.jsonl", "cbet_deep", "mtt"),
        "3bp_25bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP25.jsonl", "cbet_3bp", "mtt"),
        "3bp_50bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP50.jsonl", "cbet_3bp", "mtt"),
        "turn_mtt25": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl", "cbet_turn", "mtt"),
        "turn_cash100": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_CASH100_BTN.jsonl", "cbet_turn", "mtt"),
    }

    print("=" * 70)
    print("Light UCBS 評価 (vs フル UCBS-v2)")
    print("=" * 70)
    print(f"{'context':>16s}  {'Light':>7s}  {'Full v2':>8s}  {'差':>6s}")
    print("-" * 50)

    full_v2_wrmse = {
        "cash_100bb": 16.43, "mtt_25bb": 15.46, "mtt_50bb": 12.96,
        "mtt_100bb": 21.95, "mtt_200bb": 14.10,
        "3bp_25bb": 18.65, "3bp_50bb": 8.62,
        "turn_mtt25": 7.02, "turn_cash100": 16.11,
    }

    for label, (fp, ctx, fmt) in test_files.items():
        if not Path(fp).exists():
            continue
        records = load_records(fp, fmt)
        if not records:
            continue
        sse, total_n = 0.0, 0.0
        for r in records:
            pred = light_ucbs(r["hand"], r.get("draw", "no_draw"), ctx)
            err = pred - r["gto"]
            sse += r["n"] * err * err
            total_n += r["n"]
        wrmse = (sse / total_n) ** 0.5 if total_n else 0
        full = full_v2_wrmse.get(label, 0)
        diff = (wrmse * 100) - full
        print(f"  {label:>14s}  {wrmse*100:>5.2f}%  {full:>6.2f}%  {diff:>+5.2f}pt")


def load_records(fp, fmt):
    """fp から records を読む。fmt='cash' は cash_5cat、'mtt' は draw_study"""
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
    else:  # mtt
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


def evaluate_light_dcbs():
    """Light DCBS を 4 context で評価"""
    test_files = {
        "mtt_25bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT25_BB.jsonl", "shallow"),
        "mtt_50bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT50_BB.jsonl", "mid"),
        "mtt_100bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT100_BB.jsonl", "deep"),
        "cash_100bb": ("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_CASH100_BB.jsonl", "deep"),
    }
    full_dcbs = {"mtt_25bb": 14.36, "mtt_50bb": 14.87,
                 "mtt_100bb": 15.86, "cash_100bb": 17.17}

    print("\n" + "=" * 70)
    print("Light DCBS 評価 (vs フル DCBS)")
    print("=" * 70)
    print(f"{'context':>16s}  {'Light':>7s}  {'Full':>8s}  {'差':>6s}")
    print("-" * 50)
    for label, (fp, depth) in test_files.items():
        if not Path(fp).exists():
            continue
        records = []
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("total", 0)
                    if n < 3: continue
                    records.append({"hand": h, "n": n,
                                    "gto": vals["cont_pct"]/100.0})
        sse, total_n = 0.0, 0.0
        for r in records:
            pred = light_dcbs(r["hand"], depth)
            err = pred - r["gto"]
            sse += r["n"] * err * err
            total_n += r["n"]
        wrmse = (sse / total_n) ** 0.5 if total_n else 0
        full = full_dcbs.get(label, 0)
        diff = (wrmse * 100) - full
        print(f"  {label:>14s}  {wrmse*100:>5.2f}%  {full:>6.2f}%  {diff:>+5.2f}pt")


def demo():
    print("\n" + "=" * 70)
    print("Light UCBS Demo: 計算例")
    print("=" * 70)
    print("\n[top_pair + no_draw、cash 100bb cbet]")
    print(f"  HP=7, DP=0, CBS=7")
    print(f"  direction = (7 ≥ 5) = True")
    print(f"  base = LIGHT_BASE['cbet_std'][True] = 65%")
    print(f"  CBS≥7 なので +10 → 75%")
    print(f"  offset = 0 (default)")
    print(f"  → freq = 75%")
    print(f"  (実装値: {light_ucbs('top_pair', 'no_draw', 'cbet_std')*100:.0f}%)")

    print("\n[low_pair + no_draw、mtt 25bb cbet]")
    print(f"  HP=2, DP=0, CBS=2")
    print(f"  direction = (2 ≥ 5) = False")
    print(f"  base = LIGHT_BASE['cbet_std'][False] = 40%")
    print(f"  CBS<7、補正なし")
    print(f"  low_pair offset = -20 → 20%")
    print(f"  → freq = 20%")
    print(f"  (実装値: {light_ucbs('low_pair', 'no_draw', 'cbet_std')*100:.0f}%)")

    print("\n[no_made_hand defense、mtt 25bb]")
    print(f"  HP=2、shallow 補正で +15")
    print(f"  base = 45% (air no kicker) + 15 = 60%")
    print(f"  (実装値: {light_dcbs('no_made_hand', 'shallow')*100:.0f}%)")


if __name__ == "__main__":
    evaluate_light_ucbs()
    evaluate_light_dcbs()
    demo()
