#!/usr/bin/env python3
"""
3betスコア式の検証スクリプト

巻1 第12章の 3bet スコア式と GTO 3bet レンジ（poker-coaching の 6-max GTO チャート）
の整合性を確認する。

3bet スコア式（巻1 第12章）:
  Score₃ = H + 0.5L + B + S + C − G − R
    H: 高カード値（A=14, K=13, ... 2=2）
    L: 低カード値
    B: ブロッカー
      A を含む: +3
      K を含む: +2
      A・K 両方: +4（+5 にはしない）
    S: スーテッド → +2
    C: コネクター／ギャップ2以内
      差 = 1: +1
      差 = 2 or 3: +0.5
    G: ギャップ4以上ペナルティ −1（差5以上）
    R: 相手レンジ強度（暫定 0、応用編で扱う）

しきい値（vs RFI ポジション）:
  対UTG ≥ 23 / 対MP ≥ 21 / 対CO ≥ 19 / 対BTN ≥ 18

GTO 3bet 頻度（poker-coaching 6-max GTO チャート、IP 3bet）:
  HJ vs LJ: 8.1%
  CO vs LJ: 8.6%, CO vs HJ: 推定 10-11%
  BTN vs LJ: 7.2%, BTN vs HJ: 推定 8-10%, BTN vs CO: 推定 10-13%
  SB vs LJ-BTN: 7-15%
  BB vs LJ-BTN: 6-13%
"""

from __future__ import annotations


CARD_VALUE = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
}


def calc_3bet_score(hand: str) -> float:
    """巻1 第12章の Score₃ を計算."""
    if len(hand) == 2 and hand[0] == hand[1]:
        v = CARD_VALUE[hand[0]]
        # H + 0.5L for pair
        score = v + 0.5 * v
        # Blocker
        if v == 14:  # AA
            score += 3
        elif v == 13:  # KK
            score += 2
        return score

    h_rank, l_rank, suit = hand[0], hand[1], hand[2]
    h = CARD_VALUE[h_rank]
    l = CARD_VALUE[l_rank]
    if h < l:
        h, l = l, h
    diff = h - l

    score = h + 0.5 * l

    # Blocker
    has_a = (h == 14 or l == 14)
    has_k = (h == 13 or l == 13)
    if has_a and has_k:
        score += 4  # AK
    elif has_a:
        score += 3
    elif has_k:
        score += 2

    # Suited
    if suit == "s":
        score += 2

    # Connector / 2-gap
    if diff == 1:
        score += 1
    elif diff in (2, 3):
        score += 0.5

    # KTs special
    if hand == "KTs":
        score += 0.5  # 0.5 (gap2) → upgraded to 1 effectively

    # Gap penalty (差 5 以上 = -1)
    if diff >= 5:
        score -= 1

    return score


# Approximate GTO 3bet ranges (extracted from poker-coaching PDF, hand-curated)
# These are the IP 3bet hands (only red cells, not call cells).

# HJ vs LJ (~8.1%, 108 combos)
HJ_VS_LJ_3BET = {
    "AA", "KK", "QQ", "JJ", "TT", "99",
    "AKs", "AQs", "AJs", "ATs", "A5s",
    "KQs",
    "AKo", "AQo", "KQo",
}

# CO vs LJ (~8.6%, 114 combos)
CO_VS_LJ_3BET = {
    "AA", "KK", "QQ", "JJ", "TT", "99", "88",
    "AKs", "AQs", "AJs", "ATs", "A5s",
    "KQs",
    "AKo", "AQo", "KQo",
}

# BTN vs LJ (~7.2%, 96 combos pure 3bet)
BTN_VS_LJ_3BET = {
    "AA", "KK", "QQ", "JJ",
    "AKs", "AQs", "A5s", "A4s", "A3s",
    "AKo", "AQo", "AJo", "KQo",
}

# SB vs LJ (~7.2%, 96 combos)
SB_VS_LJ_3BET = {
    "AA", "KK", "QQ", "JJ", "TT", "99",
    "AKs", "AQs", "AJs", "ATs", "A5s",
    "KQs", "KJs",
    "AKo", "AQo",
}

# BB vs LJ (~5.7%, 76 combos)
BB_VS_LJ_3BET = {
    "AA", "KK", "QQ", "JJ", "TT",
    "AKs", "AQs", "AJs", "A5s",
    "KQs",
    "AKo", "AQo",
}

GTO_3BET_RANGES = {
    "HJ_vs_LJ": (HJ_VS_LJ_3BET, 8.1, 23),  # 対UTG
    "CO_vs_LJ": (CO_VS_LJ_3BET, 8.6, 23),  # 対UTG
    "BTN_vs_LJ": (BTN_VS_LJ_3BET, 7.2, 23),
    "SB_vs_LJ": (SB_VS_LJ_3BET, 7.2, 23),
    "BB_vs_LJ": (BB_VS_LJ_3BET, 5.7, 23),
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


def predict_3bet(hand: str, threshold: float, opp_pos: str = "early") -> bool:
    """書籍の判定ルール（ペアは別ルール、ノン・ペアはスコア式）。

    opp_pos: "early" (UTG/MP) or "late" (CO/BTN)
      JJ/TT は early ならコール、late なら3bet。
    """
    # Pair rule (ch12-2)
    if len(hand) == 2 and hand[0] == hand[1]:
        rank = hand[0]
        if rank in ("A", "K", "Q"):  # QQ+
            return True
        if rank in ("J", "T"):  # JJ, TT
            return opp_pos == "late"
        return False  # 99 以下
    # Non-pair: score formula
    return calc_3bet_score(hand) >= threshold


def verify_3bet_position(label: str, threshold: float, gto_range: set[str], opp_pos: str = "early") -> dict:
    hands = all_hands()
    tp = tn = fp = fn = 0
    fns = []
    fps = []
    for hand in hands:
        score = calc_3bet_score(hand)
        score_says_3bet = predict_3bet(hand, threshold, opp_pos)
        in_gto = hand in gto_range
        if score_says_3bet and in_gto:
            tp += 1
        elif not score_says_3bet and not in_gto:
            tn += 1
        elif score_says_3bet and not in_gto:
            fp += 1
            fps.append((hand, score))
        else:
            fn += 1
            fns.append((hand, score))

    correct_combos = 0
    total_combos = 0
    score_3bet_combos = 0
    for h in hands:
        c = hand_combo_count(h)
        total_combos += c
        s_3bet = predict_3bet(h, threshold, opp_pos)
        in_gto = h in gto_range
        if s_3bet:
            score_3bet_combos += c
        if s_3bet == in_gto:
            correct_combos += c

    gto_combos = sum(hand_combo_count(h) for h in gto_range)
    return {
        "label": label,
        "threshold": threshold,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn,
        "hand_acc": (tp + tn) / 169 * 100,
        "combo_acc": correct_combos / total_combos * 100,
        "gto_pct": gto_combos / 1326 * 100,
        "score_3bet_pct": score_3bet_combos / 1326 * 100,
        "fps": fps,
        "fns": fns,
    }


def main():
    print("=" * 78)
    print("3bet スコア式 ─ 各ポジションでの GTO 一致率")
    print("=" * 78)
    print()
    print("Score₃ = H + 0.5L + B + S + C − G")
    print("  B: A=+3, K=+2, AK=+4 / S(suited)=+2 / C: 差1=+1, 差2-3=+0.5 / G: 差5以上=-1")
    print()
    print(f"{'Spot':<12} {'Thr':>5} {'GTO%':>5} {'Score%':>7} {'TP':>4} {'TN':>4} {'FP':>4} {'FN':>4} {'Hand%':>6} {'Combo%':>7}")
    print("-" * 78)
    results = []
    for label, (range_set, _gto_pct, threshold) in GTO_3BET_RANGES.items():
        r = verify_3bet_position(label, threshold, range_set)
        results.append(r)
        print(f"{label:<12} {r['threshold']:>5.0f} {r['gto_pct']:>4.1f}% {r['score_3bet_pct']:>6.1f}% "
              f"{r['tp']:>4} {r['tn']:>4} {r['fp']:>4} {r['fn']:>4} {r['hand_acc']:>5.1f}% {r['combo_acc']:>6.1f}%")

    avg_combo = sum(r["combo_acc"] for r in results) / len(results)
    print(f"\n対UTG 平均コンボ加重精度: {avg_combo:.2f}%")

    # Detailed breakdown for one key spot
    print()
    print("=" * 78)
    print("詳細: BTN vs LJ (3bet 7.2%, threshold 23)")
    print("=" * 78)
    r = next(x for x in results if x["label"] == "BTN_vs_LJ")
    print(f"  False Negatives (GTO 3bet but Score < 23) {len(r['fns'])} 種:")
    for h, s in sorted(r["fns"], key=lambda x: -x[1])[:10]:
        print(f"    {h:<5} score={s:.1f}")
    print(f"  False Positives (Score >= 23 but GTO no 3bet) {len(r['fps'])} 種:")
    for h, s in sorted(r["fps"], key=lambda x: x[1])[:10]:
        print(f"    {h:<5} score={s:.1f}")


if __name__ == "__main__":
    main()
