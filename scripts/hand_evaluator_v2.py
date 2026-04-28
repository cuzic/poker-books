#!/usr/bin/env python3
"""フロップ HandScore 評価関数 v2 (PokerBench キャリブレーション済み).

v1 (hand_evaluator.py) からの主な変更:
  - OESD単体: 8 → 14 (PokerBench で P(Bet)=90.5% と高い)
  - FD+OESD コンボ: 12 → 17 (P(Bet)=100%)
  - フラッシュドロー単体: 10 → 12
  - ガットショット: 5 → 10 (P(Bet)=63.4%)
  - TP+中キッカー: 10 → 8 (P(Bet)=23.5% で OESD より弱い)
  - TP+弱キッカー: 10 → 6 (P(Bet)=9.6%)
  - セカンドペア弱: 5 → 3 (P(Bet)=3.6%)
  - バックドアドロー: 2 → 4 (P(Bet)=34% でエアより上)
  - セカンドペア強: 8 → 9 (P(Bet)=38.5%)

これにより HandScore が **GTO アクション (Bet) と単調に対応** するよう改善する。
"""
from __future__ import annotations

from collections import Counter
from typing import NamedTuple

RANK_STR = "23456789TJQKA"
RANK_MAP = {r: i + 2 for i, r in enumerate(RANK_STR)}


class Card(NamedTuple):
    rank: int
    suit: str


def parse_card(s: str) -> Card:
    s = s.strip()
    return Card(RANK_MAP[s[0].upper()], s[1].lower())


def parse_combo(s: str) -> list[Card]:
    s = s.replace(",", "").replace(" ", "")
    return [parse_card(s[i:i + 2]) for i in range(0, len(s), 2)]


def parse_board(s: str) -> list[Card]:
    if "," in s:
        return [parse_card(c.strip()) for c in s.split(",")]
    s = s.replace(" ", "")
    return [parse_card(s[i:i + 2]) for i in range(0, len(s), 2)]


def _has_flush(cards: list[Card]) -> bool:
    return any(v >= 5 for v in Counter(c.suit for c in cards).values())


def _has_straight(ranks: list[int]) -> bool:
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 4):
        window = unique[i:i + 5]
        if window[-1] - window[0] == 4 and len(set(window)) == 5:
            return True
    return False


def _flush_draw(cards: list[Card]) -> bool:
    return any(v == 4 for v in Counter(c.suit for c in cards).values())


def _oesd(ranks: list[int]) -> bool:
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 3):
        window = unique[i:i + 4]
        if window[-1] - window[0] == 3:
            low_end = window[0] - 1
            high_end = window[-1] + 1
            if low_end >= 1 and high_end <= 14:
                return True
    return False


def _gutshot(ranks: list[int]) -> bool:
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 3):
        window = unique[i:i + 4]
        span = window[-1] - window[0]
        if span == 3:
            low_end = window[0] - 1
            high_end = window[-1] + 1
            if not (low_end >= 1 and high_end <= 14):
                return True
        elif span == 4 and len(set(window)) == 4:
            return True
    return False


def _backdoor_flush(cards: list[Card]) -> bool:
    return any(v == 3 for v in Counter(c.suit for c in cards).values())


def _backdoor_straight(ranks: list[int]) -> bool:
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 2):
        window = unique[i:i + 3]
        if window[-1] - window[0] == 2:
            return True
    return False


def evaluate(combo: str, board: str) -> tuple[int, str]:
    """v2 改訂版 HandScore."""
    hole = parse_combo(combo)
    board_cards = parse_board(board)
    all_cards = hole + board_cards

    hole_ranks = [c.rank for c in hole]
    board_ranks = sorted([c.rank for c in board_cards], reverse=True)
    all_ranks = [c.rank for c in all_cards]

    rank_counts = Counter(all_ranks)
    hole_rank_set = set(hole_ranks)

    # --- メイドハンド ---
    if _has_flush(all_cards):
        return 20, "フラッシュ/SF"
    if _has_straight(all_ranks):
        return 18, "ストレート"
    for r, cnt in rank_counts.items():
        if cnt >= 3:
            label = "セット" if r in hole_rank_set else "トリップス"
            return 18, label

    pairs = [r for r, cnt in rank_counts.items() if cnt == 2]
    hole_pairs = [r for r in pairs if r in hole_rank_set]

    if len(pairs) >= 2 and hole_pairs:
        return 15, "2ペア"

    if hole_pairs:
        paired_rank = hole_pairs[0]
        top_board = board_ranks[0] if board_ranks else 0
        second_board = board_ranks[1] if len(board_ranks) > 1 else 0

        other_hole = [r for r in hole_ranks if r != paired_rank]
        kicker = max(other_hole) if other_hole else 0

        fd = _flush_draw(all_cards)
        oesd_draw = _oesd(all_ranks)
        gs = _gutshot(all_ranks)
        has_strong_draw = fd or oesd_draw

        # オーバーペア
        if paired_rank > top_board:
            return 15, "オーバーペア"

        # トップペア (v2 で TP+中/弱を下げる)
        if paired_rank == top_board:
            if kicker == 14:
                base, label = 15, "TPTK"
            elif kicker >= 12:
                base, label = 12, "TP+強キッカー"
            elif kicker >= 8:
                base, label = 8, "TP+中キッカー"   # v1: 10 → v2: 8
            else:
                base, label = 6, "TP+弱キッカー"   # v1: 10 → v2: 6
            # コンボドロー: TP + ドローはむしろ弱め (P(Bet)=0% in PokerBench)
            # → 単独 TP に戻す
            if has_strong_draw and base < 15:
                # TP+FD/OESD は実際は弱い (showdown 価値はあるがブラフされやすい)
                return base + 1, f"{label}+ドロー"
            return base, label

        # セカンドペア (v2 で弱を 3 へ、強を 9 へ)
        if paired_rank == second_board:
            if kicker >= 12:
                base, label = 9, "セカンドペア強"   # v1: 8 → v2: 9
            else:
                base, label = 3, "セカンドペア弱"   # v1: 5 → v2: 3
            if has_strong_draw:
                return base + 4, f"{label}+ドロー"
            return base, label

        # ボトムペア / アンダーペア
        base, label = 4, "弱ペア/ボトムペア"
        if has_strong_draw:
            return 8, "ドロー+弱ペア"
        return base, label

    # --- ドローのみ (v2 で大幅に再調整) ---
    fd = _flush_draw(all_cards)
    oesd_draw = _oesd(all_ranks)
    gs = _gutshot(all_ranks)
    bd_flush = _backdoor_flush(all_cards)
    bd_str = _backdoor_straight(all_ranks)

    if fd and oesd_draw:
        return 17, "コンボドロー(FD+OESD)"  # v1: 12 → v2: 17
    if fd:
        return 12, "フラッシュドロー"          # v1: 10 → v2: 12
    if oesd_draw:
        return 14, "OESD"                    # v1: 8 → v2: 14 (大改訂)
    if gs:
        return 10, "ガットショット"             # v1: 5 → v2: 10
    if bd_flush and bd_str:
        return 5, "ダブルバックドアドロー"
    if bd_flush or bd_str:
        return 4, "バックドアドロー"            # v1: 2 → v2: 4

    return 2, "エア"


def bucket(score: int) -> str:
    """HandScore → H1/H2/H3 バケツ.

    v2 では境界値を再調整: H3 ≥ 14 (was 15), H2 ≥ 7 (was 8), H1 < 7
    """
    if score >= 14:
        return "H3"
    elif score >= 7:
        return "H2"
    else:
        return "H1"


def _run_tests() -> None:
    cases = [
        ("KhKd", "Kc,7d,2s", 18, "H3", "セット"),
        ("AhKh", "Ks,7d,2c", 15, "H3", "TPTK"),
        ("KhQd", "Ks,7d,2c", 12, "H2", "TP+強キッカー"),
        ("Kh9d", "Ks,7d,2c", 8,  "H2", "TP+中キッカー (v2)"),
        ("Kh3d", "Ks,7d,2c", 6,  "H1", "TP+弱キッカー (v2: H1 へ)"),
        ("AhAs", "Ts,9d,8c", 15, "H3", "オーバーペア"),
        ("9h9d", "Ks,7d,2c", 4,  "H1", "弱ペア (v2)"),
        ("7h6h", "Ks,7d,2c", 3,  "H1", "セカンドペア弱 (v2)"),
        ("AhJh", "Ks,7h,2h", 12, "H2", "FD単独 (v2: 12)"),
        ("JhTh", "9h,8h,2s", 17, "H3", "FD+OESD (v2: 17)"),
        ("JsTd", "9h,8c,2d", 14, "H3", "OESD単独 (v2: 14)"),
        ("AhQd", "Ks,7d,2c", 2,  "H1", "エア"),
        ("QhJh", "Ah,Kh,Th", 20, "H3", "フラッシュ"),
        ("QhJd", "Ah,Kc,Ts", 18, "H3", "ストレート"),
        ("2h2d", "Ks,7d,2c", 18, "H3", "セット"),
        ("9h8h", "Ts,7d,2h", 14, "H3", "OESD (v2)"),
        ("AhQh", "Kh,Jh,2c", 12, "H2", "FD単独 (一端ふさがり)"),
        ("Ts9h", "8d,7c,2s", 14, "H3", "OESD"),
        ("Th9h", "Ks,7d,2c", 4,  "H1", "BDFD+BDSD"),
    ]

    passed = 0
    failed = 0
    for combo, board, exp_score, exp_bucket, note in cases:
        score, label = evaluate(combo, board)
        b = bucket(score)
        ok = score == exp_score and b == exp_bucket
        status = "✓" if ok else "✗"
        if not ok:
            failed += 1
            print(f"{status} {combo} on {board}: score={score}({label}) bucket={b}"
                  f" | expected score={exp_score} bucket={exp_bucket} ({note})")
        else:
            passed += 1
            print(f"{status} {combo} on {board}: {label} (H={score}, {b}) [{note}]")

    print(f"\n{passed} passed, {failed} failed")


if __name__ == "__main__":
    _run_tests()
