#!/usr/bin/env python3
"""
Score 式の精密化スクリプト

複数の式バリエーションを試し、GTO レンジ（poker-coaching の 6-max GTO チャート、
17.0% / 21.4% / 27.8% / 43.3% / 24.3% raise）への一致率を最大化する組み合わせを
探す。

検証データ: poker-coaching online-6max-gto-charts.pdf から画像抽出
"""

from __future__ import annotations

from dataclasses import dataclass


CARD_VALUE = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
}


@dataclass
class FormulaConfig:
    """Score 式の係数設定."""
    pair_bonus: float = 10.0
    suited_bonus: float = 3.0
    connector_bonus: float = 1.0
    gap2_bonus: float = 0.5
    gap_penalty_threshold: int = 5  # 差がこれ以上でペナルティ
    gap_penalty: float = 1.0
    low_card_threshold: int = 9  # 両方この値未満でペナルティ
    low_card_penalty: float = 1.0

    # Refinements (default 0 = no effect)
    ace_bonus: float = 0.0  # A を含むハンド全体に追加
    small_pair_bonus: float = 0.0  # 22-66 のペアに追加（22-99 ではなく）
    small_pair_threshold: int = 6  # ペア値がこれ以下でボーナス
    suited_skip_low_penalty: bool = False  # スーテッドは低カードペナルティ免除
    suited_connector_bonus: float = 0.0  # スーテッドかつ差<=3 に追加
    small_ace_bonus: float = 0.0  # A2s-A8s に追加（オフスーツは除く）

    def calc_score(self, hand: str) -> float:
        if len(hand) == 2 and hand[0] == hand[1]:
            v = CARD_VALUE[hand[0]]
            score = v * 2 + self.pair_bonus
            if v <= self.small_pair_threshold:
                score += self.small_pair_bonus
            return score

        h_rank, l_rank, suit = hand[0], hand[1], hand[2]
        h = CARD_VALUE[h_rank]
        l = CARD_VALUE[l_rank]
        if h < l:
            h, l = l, h
        diff = h - l

        score = h + l

        if suit == "s":
            score += self.suited_bonus
            if 0 < diff <= 3:
                score += self.suited_connector_bonus
        if diff == 1:
            score += self.connector_bonus
        elif diff in (2, 3):
            score += self.gap2_bonus

        if diff >= self.gap_penalty_threshold:
            score -= self.gap_penalty
        if h < self.low_card_threshold and l < self.low_card_threshold:
            if not (suit == "s" and self.suited_skip_low_penalty):
                score -= self.low_card_penalty

        # A blocker bonus
        if h == 14 or l == 14:
            score += self.ace_bonus
            # Small Ace specifically (A2-A8)
            if l <= 8 and l >= 2:
                if suit == "s":
                    score += self.small_ace_bonus

        return score


# ============================================================================
# GTO ranges (extracted from poker-coaching 6-max GTO chart PDF)
# ============================================================================

# LJ / UTG (17.0%, 226 combos)
GTO_UTG = {
    "AA", "KK", "QQ", "JJ", "TT", "99",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s",
    "KQs", "KJs", "KTs", "K9s", "K8s",
    "QJs", "QTs", "Q9s",
    "JTs", "J9s",
    "T9s",
    "AKo", "AQo", "AJo", "ATo",
    "KQo", "KJo",
    "QJo",
}

# HJ / MP (21.4%, 284 combos)
GTO_MP = GTO_UTG | {
    "88",
    "A2s", "K7s", "K6s", "Q8s", "J8s", "T8s",
    "98s", "87s", "76s",
    "KTo", "QTo", "JTo",
    "A9o",
}

# CO (27.8%, 368 combos)
GTO_CO = GTO_MP | {
    "K5s", "K4s", "K3s", "K2s",
    "Q7s", "Q6s", "Q5s", "Q4s", "Q3s", "Q2s",
    "J7s", "T7s", "97s", "65s",
    "T9o", "J9o", "Q9o",
    "A8o", "A7o", "A6o", "A5o",
}

# BTN (43.3%, 574 combos)
GTO_BTN = GTO_CO | {
    "77", "66", "55", "44", "33", "22",
    "T6s", "96s", "86s", "75s", "54s",
    "J6s", "J5s", "J4s",
    "T8o", "T7o", "98o", "87o", "76o", "65o",
    "K9o", "K8o", "K7o", "K6o",
    "Q8o", "Q7o", "J8o", "J7o",
    "A4o", "A3o", "A2o",
}

# SB (24.3% raise, 322 combos)
# SB has unique mixed strategy (raise + limp); we use raise-only here
GTO_SB = {
    "AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "44", "33", "22",
    "AKs", "AQs", "AJs", "ATs", "A9s", "A8s", "A7s", "A6s", "A5s", "A4s", "A3s", "A2s",
    "KQs", "KJs", "KTs", "K9s", "K8s",
    "QJs", "QTs", "Q9s",
    "JTs", "J9s",
    "T9s", "98s", "87s", "76s", "65s",
    "AKo", "AQo", "AJo", "ATo", "A9o", "A8o", "A7o",
    "KQo", "KJo", "KTo",
    "QJo", "QTo",
    "JTo",
}


GTO_RANGES = {
    "UTG": (GTO_UTG, 17.0),
    "MP": (GTO_MP, 21.4),
    "CO": (GTO_CO, 27.8),
    "BTN": (GTO_BTN, 43.3),
    "SB": (GTO_SB, 24.3),
}


def all_hands() -> list[str]:
    ranks = "AKQJT98765432"
    hands = []
    for i, h in enumerate(ranks):
        for j, l in enumerate(ranks):
            if i == j:
                hands.append(f"{h}{h}")
            elif i < j:
                hands.append(f"{h}{l}s")
                hands.append(f"{h}{l}o")
    return hands


def hand_combo_count(hand: str) -> int:
    if len(hand) == 2:
        return 6
    return 4 if hand[2] == "s" else 12


# ============================================================================
# Threshold optimization
# ============================================================================

def find_optimal_thresholds(config: FormulaConfig, ranges: dict) -> dict:
    """各ポジションで最適しきい値を求める（コンボ加重精度最大）."""
    hands = all_hands()
    scores = {h: config.calc_score(h) for h in hands}

    results = {}
    for pos, (gto_range, target_pct) in ranges.items():
        best_acc = 0.0
        best_thr = 0.0
        for thr_int in range(20, 80):
            thr = thr_int * 0.5
            correct = 0
            total = 0
            for h in hands:
                combos = hand_combo_count(h)
                total += combos
                score_open = scores[h] >= thr
                in_gto = h in gto_range
                if score_open == in_gto:
                    correct += combos
            acc = correct / total * 100
            if acc > best_acc:
                best_acc = acc
                best_thr = thr
        # Calculate at-best stats
        score_open_combos = sum(hand_combo_count(h) for h in hands if scores[h] >= best_thr)
        results[pos] = {
            "threshold": best_thr,
            "accuracy": best_acc,
            "score_pct": score_open_combos / 1326 * 100,
            "gto_pct": target_pct,
        }
    return results


def total_accuracy(config: FormulaConfig, ranges: dict) -> float:
    """5 ポジションの平均精度."""
    results = find_optimal_thresholds(config, ranges)
    return sum(r["accuracy"] for r in results.values()) / len(results)


# ============================================================================
# Formula search
# ============================================================================

def search_formula() -> tuple[FormulaConfig, float]:
    """Grid search over formula refinements."""
    base = FormulaConfig()
    best_config = base
    best_acc = total_accuracy(base, GTO_RANGES)
    print(f"Base: avg accuracy = {best_acc:.2f}%")

    # Try variations
    variations = []

    # A bonus
    for a_bonus in [0.0, 0.5, 1.0, 1.5]:
        for sa_bonus in [0.0, 0.5, 1.0, 1.5, 2.0]:
            for sp_bonus in [0.0, 0.5, 1.0, 1.5]:
                for sk_low in [False, True]:
                    for sc_bonus in [0.0, 0.5, 1.0]:
                        cfg = FormulaConfig(
                            ace_bonus=a_bonus,
                            small_ace_bonus=sa_bonus,
                            small_pair_bonus=sp_bonus,
                            suited_skip_low_penalty=sk_low,
                            suited_connector_bonus=sc_bonus,
                        )
                        acc = total_accuracy(cfg, GTO_RANGES)
                        if acc > best_acc:
                            best_acc = acc
                            best_config = cfg
                            variations.append((acc, cfg))

    return best_config, best_acc


def evaluate_minimal_refinements():
    """最低限の追加で大きな改善が得られるか確認."""
    print("=" * 78)
    print("最低限の追加（単一修正）の効果")
    print("=" * 78)
    base = FormulaConfig()
    base_acc = total_accuracy(base, GTO_RANGES)
    print(f"\nBase（現行）: {base_acc:.2f}%")

    refinements = [
        ("A 全体に +0.5", FormulaConfig(ace_bonus=0.5)),
        ("A 全体に +1.0", FormulaConfig(ace_bonus=1.0)),
        ("A 全体に +1.5", FormulaConfig(ace_bonus=1.5)),
        ("A2s-A8s に +1.0", FormulaConfig(small_ace_bonus=1.0)),
        ("A2s-A8s に +2.0", FormulaConfig(small_ace_bonus=2.0)),
        ("22-66 に +1.0", FormulaConfig(small_pair_bonus=1.0)),
        ("22-66 に +2.0", FormulaConfig(small_pair_bonus=2.0)),
        ("スーテッド差3以内 +1", FormulaConfig(suited_connector_bonus=1.0)),
        ("スーテッド低カードペナルティ免除", FormulaConfig(suited_skip_low_penalty=True)),
        ("A全体+0.5 + 22-44+1 + sc+1", FormulaConfig(ace_bonus=0.5, small_pair_bonus=1.0, small_pair_threshold=4, suited_connector_bonus=1.0)),
    ]
    for name, cfg in refinements:
        acc = total_accuracy(cfg, GTO_RANGES)
        print(f"  {name:<35} {acc:.2f}%（{acc-base_acc:+.2f}%）")
    print()


def main():
    print("=" * 78)
    print("Score 式 ─ 現行版の検証")
    print("=" * 78)
    cur = FormulaConfig()
    cur_results = find_optimal_thresholds(cur, GTO_RANGES)
    print(f"\n{'Pos':<5} {'最適しきい値':>10} {'GTO%':>6} {'Score%':>7} {'Acc%':>6}")
    for pos, r in cur_results.items():
        print(f"{pos:<5} {r['threshold']:>10.1f} {r['gto_pct']:>5.1f}% {r['score_pct']:>6.1f}% {r['accuracy']:>5.1f}%")
    cur_avg = sum(r["accuracy"] for r in cur_results.values()) / 5
    print(f"\n平均精度: {cur_avg:.2f}%")

    print()
    print("=" * 78)
    print("式の精密化探索（grid search）")
    print("=" * 78)
    best_cfg, best_acc = search_formula()
    print(f"\n最良: 平均精度 {best_acc:.2f}%（+{best_acc-cur_avg:.2f}%）")
    print(f"設定:")
    print(f"  ace_bonus           = {best_cfg.ace_bonus}")
    print(f"  small_ace_bonus     = {best_cfg.small_ace_bonus}")
    print(f"  small_pair_bonus    = {best_cfg.small_pair_bonus}")
    print(f"  suited_skip_low_pen = {best_cfg.suited_skip_low_penalty}")
    print(f"  suited_conn_bonus   = {best_cfg.suited_connector_bonus}")

    print(f"\n精密化版での各ポジション最適しきい値:")
    new_results = find_optimal_thresholds(best_cfg, GTO_RANGES)
    print(f"\n{'Pos':<5} {'最適しきい値':>10} {'GTO%':>6} {'Score%':>7} {'Acc%':>6}")
    for pos, r in new_results.items():
        print(f"{pos:<5} {r['threshold']:>10.1f} {r['gto_pct']:>5.1f}% {r['score_pct']:>6.1f}% {r['accuracy']:>5.1f}%")


if __name__ == "__main__":
    evaluate_minimal_refinements()
    main()
