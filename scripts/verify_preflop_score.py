#!/usr/bin/env python3
"""
Score 式の検証スクリプト

『迷わないポーカー① プリフロップ』の Score 式と各ポジションのしきい値が、
標準的な GTO オープンレンジ（6-max 100BB Cash）とどの程度整合するかを検証する。

Score 式（巻1 第5章現行版）:
  Score = H + L + ボーナス − ペナルティ
    H: 高カード値（A=14, K=13, ... 2=2）
    L: 低カード値
    ボーナス:
      ペア: +10
      スーテッド: +3
      コネクター（差=1）: +1
      ギャップ2以内（差=2 or 3）: +0.5
    ペナルティ:
      ギャップ4以上（差5以上）: −1
      両方9未満: −1

しきい値（巻1 第5章現行版）:
  UTG ≥ 23 / MP ≥ 22 / CO ≥ 21 / BTN ≥ 18 / SB ≥ 20

GTO 標準オープンレンジ（6-max 100BB Cash、GTO Wizard / PokerSnowie 等の業界標準値）:
  UTG: 約 17%（22+, ATs+, KTs+, QTs+, JTs, T9s, 98s, AJo+, KQo）
  MP:  約 22%（UTG + 22+, A2s+, K9s+, Q9s+, J9s, T9s, 98s, ATo+, KJo+）
  CO:  約 27%（MP + 33+, A2s+, K7s+, Q8s+, J8s+, T8s+, 97s+, 87s, 76s, ATo+, KTo+, QJo）
  BTN: 約 45%（CO + 22+, A2s+, K2s+, Q5s+, J7s+, T7s+, 96s+, 85s+, 74s+, 64s+, 54s, A2o+, K9o+, Q9o+, J9o+, T9o, 98o）
  SB:  約 35%（CO 相当の少しタイト気味）
"""

from __future__ import annotations

from dataclasses import dataclass


# ============================================================================
# Score formula
# ============================================================================

CARD_VALUE = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
}


def calc_score(hand: str) -> float:
    """Calculate Score for a hand string like 'AKs', 'QJo', '77'."""
    if len(hand) == 2 and hand[0] == hand[1]:
        # Pocket pair
        v = CARD_VALUE[hand[0]]
        return v * 2 + 10  # H + L + pair bonus

    # Two distinct ranks (e.g., 'AKs', 'QJo')
    h_rank, l_rank, suit = hand[0], hand[1], hand[2]
    h = CARD_VALUE[h_rank]
    l = CARD_VALUE[l_rank]
    if h < l:
        h, l = l, h
    diff = h - l

    score = h + l

    # Bonus
    if suit == "s":
        score += 3  # suited
    if diff == 1:
        score += 1  # connector
    elif diff in (2, 3):
        score += 0.5  # 2-gap

    # Penalty
    if diff >= 5:
        score -= 1
    if h < 9 and l < 9:
        score -= 1

    return score


# ============================================================================
# GTO Standard ranges (6-max 100BB Cash)
# These are derived from GTO Wizard / PokerSnowie / standard published ranges.
# ============================================================================

def hand_in_set(hand: str, range_set: set[str]) -> bool:
    """Check if a hand string is in a set, with normalization."""
    return hand in range_set


# 各ポジションの GTO RFI レンジを poker-coaching の Implementable GTO Charts
# (PDF 抽出画像) からピクセル解析で構築。
#
# データ:        knowledges/preflop/gto-charts.json
# 抽出スクリプト: scripts/extract_gto_charts.py
# 出典:           https://www.pokercoaching.com/  Implementable GTO Charts
#
# 6-max ↔ 9-max のポジション対応:
#   LJ (Lojack) = UTG（6-max では最早ポジション）
#   HJ (Hijack) = MP（6-max のミドル）
#   CO / BTN / SB / BB は同じ
#
# 公開頻度: UTG 17.0% / MP 21.4% / CO 27.8% / BTN 43.3% / SB raise=24.3%（混合）

import json
from pathlib import Path

_GTO_DATA_PATH = Path(__file__).parent.parent / "knowledges" / "preflop" / "gto-charts.json"
_GTO_DATA = json.loads(_GTO_DATA_PATH.read_text())


def _raise_hands(label: str) -> set[str]:
    """Get raise-action hands from GTO chart by label."""
    chart = _GTO_DATA[label]
    hands = set(chart["actions"].get("raise", []))
    # Include "mixed_raise" cells as raise (純粋 GTO に近い)
    hands |= set(chart["actions"].get("mixed_raise", []))
    return hands


# UTG (LJ) RFI 17.0% / 226 combos
UTG_OPEN = _raise_hands("LJ_RFI")

# MP (HJ) RFI 21.4% / 284 combos
MP_OPEN = _raise_hands("HJ_RFI")

# CO RFI 27.8% / 386 combos (実測 29.1% — pixel 解析の誤差含む)
CO_OPEN = _raise_hands("CO_RFI")

# BTN RFI 43.3% / 602 combos (実測 45.4%)
BTN_OPEN = _raise_hands("BTN_RFI")

# SB RFI raise-only 24.3% / 322 combos
# 注: SB は GTO で混合戦略 (raise + limp) を採るため、PDF チャートのピクセル抽出は
# 縞模様セルで信頼性が低い（AA が limp 判定されるなど）。代わりに poker-coaching の
# 6-max GTO 解説で示される標準的な「raise-only ~24%」レンジを手作業で採用する。
SB_OPEN = {
    # Pairs (78)
    "22", "33", "44", "55", "66", "77", "88", "99", "TT", "JJ", "QQ", "KK", "AA",
    # Suited As (48)
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    # Suited Ks: KQs-K8s (20)
    "KQs", "KJs", "KTs", "K9s", "K8s",
    # Suited Qs: QJs-Q8s (16)
    "QJs", "QTs", "Q9s", "Q8s",
    # Suited Js: JTs, J9s, J8s (12)
    "JTs", "J9s", "J8s",
    # Suited Ts: T9s, T8s (8)
    "T9s", "T8s",
    # Low SCs (20)
    "98s", "87s", "76s", "65s", "54s",
    # Offsuit broadway (60+12): AKo, AQo, AJo, ATo, A9o + KQo, KJo, KTo, QJo, QTo, JTo
    "AKo", "AQo", "AJo", "ATo", "A9o",
    "KQo", "KJo", "KTo", "QJo", "QTo", "JTo",
}


GTO_RANGES = {
    "UTG": UTG_OPEN,
    "MP": MP_OPEN,
    "CO": CO_OPEN,
    "BTN": BTN_OPEN,
    "SB": SB_OPEN,
}


# Current thresholds (digest / new preflop chapter 5)
CURRENT_THRESHOLDS = {
    "UTG": 24,
    "MP": 22,
    "CO": 21,
    "BTN": 18,
    "SB": 22,
}


# ============================================================================
# All 169 hands
# ============================================================================

def all_hands() -> list[str]:
    """Generate all 169 hand strings (13 pairs + 78 suited + 78 offsuit)."""
    ranks = "AKQJT98765432"
    hands = []
    for i, h in enumerate(ranks):
        for j, l in enumerate(ranks):
            if i == j:
                hands.append(f"{h}{h}")
            elif i < j:
                # h is higher rank
                hands.append(f"{h}{l}s")
                hands.append(f"{h}{l}o")
    return hands


def hand_combo_count(hand: str) -> int:
    """Combo count for a hand string."""
    if len(hand) == 2:  # Pair
        return 6
    suit = hand[2]
    return 4 if suit == "s" else 12


# ============================================================================
# Verification
# ============================================================================

@dataclass
class Discrepancy:
    hand: str
    score: float
    in_gto: bool
    score_says_open: bool

    @property
    def kind(self) -> str:
        if self.in_gto and not self.score_says_open:
            return "FN"  # GTO opens, Score says fold (false negative)
        if not self.in_gto and self.score_says_open:
            return "FP"  # Score opens, GTO doesn't (false positive)
        return "OK"


def verify_position(position: str, threshold: float, gto_range: set[str]) -> dict:
    """Verify Score formula prediction against GTO range for a position."""
    hands = all_hands()
    tp = tn = fp = fn = 0
    fp_combos = fn_combos = 0
    discrepancies = []

    for hand in hands:
        score = calc_score(hand)
        score_says_open = score >= threshold
        in_gto = hand_in_set(hand, gto_range)
        combos = hand_combo_count(hand)

        if score_says_open and in_gto:
            tp += 1
        elif not score_says_open and not in_gto:
            tn += 1
        elif score_says_open and not in_gto:
            fp += 1
            fp_combos += combos
            discrepancies.append(Discrepancy(hand, score, in_gto, score_says_open))
        else:  # not score_says_open and in_gto
            fn += 1
            fn_combos += combos
            discrepancies.append(Discrepancy(hand, score, in_gto, score_says_open))

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / total * 100 if total > 0 else 0

    # Total combo counts
    gto_combos = sum(hand_combo_count(h) for h in gto_range)
    score_open_combos = sum(hand_combo_count(h) for h in hands if calc_score(h) >= threshold)

    return {
        "position": position,
        "threshold": threshold,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "accuracy": accuracy,
        "gto_combos": gto_combos,
        "gto_pct": gto_combos / 1326 * 100,
        "score_open_combos": score_open_combos,
        "score_open_pct": score_open_combos / 1326 * 100,
        "fp_combos": fp_combos,
        "fn_combos": fn_combos,
        "discrepancies": discrepancies,
    }


def find_optimal_threshold(_position: str, gto_range: set[str]) -> tuple[float, float]:
    """Find threshold that maximizes combo-weighted accuracy."""
    hands = all_hands()
    best_acc = 0.0
    best_thr = 0.0
    for thr_int in range(10, 40):
        thr = thr_int + 0.0
        # Combo-weighted accuracy
        correct_combos = 0
        total_combos = 0
        for hand in hands:
            score = calc_score(hand)
            score_says_open = score >= thr
            in_gto = hand_in_set(hand, gto_range)
            combos = hand_combo_count(hand)
            total_combos += combos
            if score_says_open == in_gto:
                correct_combos += combos
        acc = correct_combos / total_combos * 100
        if acc > best_acc:
            best_acc = acc
            best_thr = thr
    return best_thr, best_acc


# ============================================================================
# Main report
# ============================================================================

def main():
    print("=" * 78)
    print("Score 式の検証 ─ 各ポジションでの GTO 一致率")
    print("=" * 78)
    print()
    print(f"使用する Score 式:")
    print(f"  Score = H + L + ボーナス − ペナルティ")
    print(f"  ボーナス: ペア+10 / スーテッド+3 / コネクター+1 / ギャップ2以内+0.5")
    print(f"  ペナルティ: ギャップ4以上（差5以上）−1 / 両方9未満−1")
    print()

    print(f"{'Pos':<5} {'Thr':>5} {'GTO%':>6} {'Score%':>7} {'TP':>4} {'TN':>4} {'FP':>4} {'FN':>4} {'Hand%':>6} {'Combo%':>7}")
    print("-" * 78)
    results = {}
    hands = all_hands()
    for pos in ["UTG", "MP", "CO", "BTN", "SB"]:
        thr = CURRENT_THRESHOLDS[pos]
        result = verify_position(pos, thr, GTO_RANGES[pos])
        # Combo-weighted accuracy
        correct_combos = 0
        total_combos = 0
        for hand in hands:
            score = calc_score(hand)
            score_says_open = score >= thr
            in_gto = hand_in_set(hand, GTO_RANGES[pos])
            combos = hand_combo_count(hand)
            total_combos += combos
            if score_says_open == in_gto:
                correct_combos += combos
        combo_acc = correct_combos / total_combos * 100
        result["combo_accuracy"] = combo_acc
        results[pos] = result
        print(f"{pos:<5} {thr:>5.1f} {result['gto_pct']:>5.1f}% {result['score_open_pct']:>6.1f}% "
              f"{result['tp']:>4} {result['tn']:>4} {result['fp']:>4} {result['fn']:>4} {result['accuracy']:>5.1f}% {combo_acc:>6.1f}%")

    print()
    print("=" * 78)
    print("最適しきい値（精度最大化）")
    print("=" * 78)
    print(f"{'Pos':<5} {'現行':>6} {'最適':>6} {'現行Acc':>9} {'最適Acc':>9}")
    print("-" * 78)
    for pos in ["UTG", "MP", "CO", "BTN", "SB"]:
        opt_thr, opt_acc = find_optimal_threshold(pos, GTO_RANGES[pos])
        cur_acc = results[pos]["accuracy"]
        marker = " ◀ 改善" if opt_thr != CURRENT_THRESHOLDS[pos] else ""
        print(f"{pos:<5} {CURRENT_THRESHOLDS[pos]:>6.1f} {opt_thr:>6.1f} {cur_acc:>8.1f}% {opt_acc:>8.1f}%{marker}")

    print()
    print("=" * 78)
    print("主要な不一致ハンド（False Positive/Negative）")
    print("=" * 78)
    for pos in ["UTG", "MP", "CO", "BTN", "SB"]:
        result = results[pos]
        fns = [d for d in result["discrepancies"] if d.kind == "FN"]
        fps = [d for d in result["discrepancies"] if d.kind == "FP"]
        if not fns and not fps:
            continue
        print(f"\n[{pos}] しきい値 {result['threshold']}")
        if fns:
            print(f"  FN（GTO は開くが Score は fold）{len(fns)} 種:")
            for d in sorted(fns, key=lambda x: -x.score)[:10]:
                print(f"    {d.hand:<5} score={d.score:.1f}")
            if len(fns) > 10:
                print(f"    ... ほか {len(fns)-10} 種")
        if fps:
            print(f"  FP（Score は開くが GTO は fold）{len(fps)} 種:")
            for d in sorted(fps, key=lambda x: x.score)[:10]:
                print(f"    {d.hand:<5} score={d.score:.1f}")
            if len(fps) > 10:
                print(f"    ... ほか {len(fps)-10} 種")


if __name__ == "__main__":
    main()
