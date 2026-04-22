#!/usr/bin/env python3
"""BDM (Board Deficit Model) 公式実装。

flop 編の新モデル。2階層構成:
  - d3(): 暗算モデル (初学者向け、R²=0.873, 覚える数字10個)
  - bdm_v5(): 精密モデル (上級者向け、R²=0.914, 覚える数字約25個)

両関数は ranks: list[int], suits: list[str], paired: bool を受け、
CBet 頻度 (%) を返す。
"""
from __future__ import annotations

RANK_VALUES = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
}


def is_monotone(suits: list[str]) -> bool:
    """3 枚とも同じスート（指定のもののみ判定）。"""
    non_q = [s for s in suits if s != "?"]
    return len(non_q) >= 3 and len(set(non_q)) == 1


def is_two_tone(suits: list[str]) -> bool:
    """3 枚中 2 枚が同じスート。略記で ss/hh/dd などの '?' 付きは 2-tone と見做す。"""
    if "?" in suits:
        return True
    s_counts: dict[str, int] = {}
    for s in suits:
        s_counts[s] = s_counts.get(s, 0) + 1
    return 2 in s_counts.values()


def is_wet_for_d3(ranks: list[int], suits: list[str]) -> bool:
    """D3 のウェット判定。連続3枚 or 2-tone or 高ボード連続 (max_diff<=4 & top>=T)。"""
    h = max(ranks)
    max_diff = h - min(ranks)
    if max_diff <= 2:
        return True
    if is_two_tone(suits):
        return True
    if max_diff <= 4 and h >= 10:
        return True
    return False


def d3(ranks: list[int], suits: list[str], paired: bool) -> int:
    """D3 暗算モデル。4 ステップのチェックリスト。

    Args:
        ranks: 3 枚のランク値 (14=A, 2=2)
        suits: 3 枚のスート (未指定は "?")
        paired: ペアボードか

    Returns:
        CBet 頻度 %（0〜100 の整数）
    """
    h = max(ranks)
    rs = sorted(ranks, reverse=True)

    # Step 1: モノトーン
    if is_monotone(suits):
        return 20

    # Step 2: ペアボード
    if paired:
        if rs[0] == rs[1]:
            # トップがペア (AAK, KK9, 772 など)
            pair_rank = rs[0]
            kicker = rs[2]
            if pair_rank >= 12:  # QQ+
                return 80 if kicker >= 8 else 50
            return 72  # TT 以下の top pair
        # キッカーがトップ (K44, A99 など)
        pair_rank = rs[1]
        if h >= 13 and pair_rank <= 7:  # K44, A33 型
            return 45
        if h >= 13 and pair_rank >= 8:  # A99, K88 型
            return 75
        return 55  # Q/J ハイ + ローペア

    # Step 3 & 4: トップ × ウェット マトリクス
    wet = is_wet_for_d3(ranks, suits)
    if h >= 12:  # A/K/Q
        return 55 if wet else 85
    return 30 if wet else 55  # J 以下


def bdm_v5(ranks: list[int], suits: list[str], paired: bool) -> int:
    """BDM v5 精密モデル。4項減算式 + Extra ルール + ペア override。

    CBet = 90 − HighCardDeficit − TextureCost − SuitPenalty − Extra
           (pair/mono は override)
    """
    h = max(ranks)
    rs = sorted(ranks, reverse=True)
    mid = rs[1]
    low = rs[2]
    max_diff = h - low

    # Monotone override
    if is_monotone(suits):
        return 18

    # Pair override
    if paired:
        if rs[0] == rs[1]:
            pair_rank = rs[0]
            kicker = rs[2]
            top_is_pair = True
        else:
            pair_rank = rs[1]
            kicker = rs[0]
            top_is_pair = False

        if top_is_pair:
            if pair_rank >= 12:
                return 82 if kicker >= 8 else 50
            if pair_rank >= 8:
                return 75
            return 68
        # top is kicker
        if h >= 13 and pair_rank <= 7:
            return 45
        if h >= 13 and pair_rank >= 8:
            return 76
        if h >= 11 and pair_rank <= 7:
            return 55
        return 65

    # --- 非ペア 4項減算 ---
    base_by_top = {
        14: 90, 13: 90, 12: 85,
        11: 55, 10: 55, 9: 55, 8: 55,
        7: 60, 6: 60, 5: 60, 4: 60, 3: 60, 2: 60,
    }
    base = base_by_top.get(h, 60)

    # TextureCost
    if max_diff <= 2:
        if h <= 8:
            cp = 5
        elif h == 9:
            cp = 10 if not is_two_tone(suits) else 20
        elif h == 10:
            cp = 15 if is_two_tone(suits) else 20
        elif h == 11:
            cp = 25
        else:
            cp = 30
    elif max_diff <= 4:
        cp = 5 if h <= 8 else (15 if h <= 10 else 25)
    elif max_diff <= 7:
        cp = 5
    else:
        cp = 0

    # SuitPenalty
    sp = 10 if is_two_tone(suits) else 0

    # Extra (ブロードウェイ補正)
    extra = 0
    if mid == 10 and h >= 12 and not is_two_tone(suits):
        extra += 15  # KT5r, QT3r
    if low >= 10 and is_two_tone(suits):
        extra += 10  # KQTss, QJTss
    if h >= 12 and mid >= 10 and is_two_tone(suits) and low < 10:
        extra += 15  # AT7ss, KJ2ss
    if h == 12 and mid < 10 and is_two_tone(suits):
        extra += 10  # Q83ss

    return max(0, min(100, base - cp - sp - extra))


# ---------------------------------------------------------------------------
# 動作確認用エントリポイント
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys

    sys.path.insert(0, "/home/cuzic/poker-books/scripts")
    from verify_flop_gto import GTO_BOARD_DATA, parse_board
    from statistics import correlation

    print(f"{'board':10s} {'actual':>6} {'D3':>6} {'BDM v5':>7}")
    print("-" * 35)

    actuals = []
    d3_preds = []
    bdm_preds = []
    for board, freq, _, _ in GTO_BOARD_DATA:
        ranks, suits, paired = parse_board(board)
        d3_p = d3(ranks, suits, paired)
        bdm_p = bdm_v5(ranks, suits, paired)
        actuals.append(float(freq))
        d3_preds.append(d3_p)
        bdm_preds.append(bdm_p)
        print(f"{board:10s} {freq:>6} {d3_p:>6} {bdm_p:>7}")

    def r2(a, p):
        m = sum(a) / len(a)
        ss_tot = sum((ai - m) ** 2 for ai in a)
        ss_res = sum((ai - pi) ** 2 for ai, pi in zip(a, p))
        return 1 - ss_res / ss_tot

    def mae(a, p):
        return sum(abs(ai - pi) for ai, pi in zip(a, p)) / len(a)

    print()
    print(f"D3    : R² = {r2(actuals, d3_preds):.3f}  MAE = {mae(actuals, d3_preds):.2f}  "
          f"r = {correlation(actuals, d3_preds):.3f}")
    print(f"BDM v5: R² = {r2(actuals, bdm_preds):.3f}  MAE = {mae(actuals, bdm_preds):.2f}  "
          f"r = {correlation(actuals, bdm_preds):.3f}")
