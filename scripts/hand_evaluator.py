#!/usr/bin/env python3
"""フロップ HandScore 評価関数.

combo (例: "AhKs") と board (例: "Ks,7d,2c") を受け取り
HandScore (0-20) とカテゴリラベルを返す。

HandScore 基準 (フロップ時点の評価):
  20: フラッシュ / SF
  18: セット / ストレート / トリップス
  15: 2ペア / TPTK (Aキッカー) / オーバーペア
  12: TP+強キッカー(Q+) / コンボドロー (FD or OESD + 弱ペア)
  10: フラッシュドロー単体 / TP+中キッカー / TP+弱キッカー
   8: OESD / セカンドペア強 (Q+キッカー)
   5: ガットショット / セカンドペア弱 / 弱ペア / アンダーペア
   2: バックドアドロー / エア

使用例:
    from hand_evaluator import evaluate, bucket
    score, label = evaluate("AhKs", "Ks,7d,2c")  # -> (15, "TPTK")
    b = bucket(score)  # -> "H3"
"""
from __future__ import annotations

from collections import Counter
from typing import NamedTuple

RANK_STR = "23456789TJQKA"
RANK_MAP = {r: i + 2 for i, r in enumerate(RANK_STR)}  # '2'->2, 'A'->14


class Card(NamedTuple):
    rank: int   # 2-14
    suit: str   # h/s/d/c


def parse_card(s: str) -> Card:
    s = s.strip()
    return Card(RANK_MAP[s[0].upper()], s[1].lower())


def parse_combo(s: str) -> list[Card]:
    """"AhKs" -> [Card(14,'h'), Card(13,'s')]"""
    s = s.replace(",", "").replace(" ", "")
    return [parse_card(s[i:i + 2]) for i in range(0, len(s), 2)]


def parse_board(s: str) -> list[Card]:
    """"Ks,7d,2c" or "Ks7d2c" -> list[Card]"""
    if "," in s:
        return [parse_card(c.strip()) for c in s.split(",")]
    s = s.replace(" ", "")
    return [parse_card(s[i:i + 2]) for i in range(0, len(s), 2)]


# ---------------------------------------------------------------------------
# 手牌判定ヘルパー
# ---------------------------------------------------------------------------

def _has_flush(cards: list[Card]) -> bool:
    return any(v >= 5 for v in Counter(c.suit for c in cards).values())


def _has_straight(ranks: list[int]) -> bool:
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique  # Ace-low
    for i in range(len(unique) - 4):
        window = unique[i:i + 5]
        if window[-1] - window[0] == 4 and len(set(window)) == 5:
            return True
    return False


def _flush_draw(cards: list[Card]) -> bool:
    """同一スーツが4枚 (フラッシュドロー)."""
    return any(v == 4 for v in Counter(c.suit for c in cards).values())


def _oesd(ranks: list[int]) -> bool:
    """4連続ランクかつ両端オープン (真のOESD).

    J-Q-K-A や A-2-3-4 は一端がAでふさがるためOESDではなく
    _gutshot で H=5 として扱う。
    """
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 3):
        window = unique[i:i + 4]
        if window[-1] - window[0] == 3:
            low_end = window[0] - 1
            high_end = window[-1] + 1
            # 両端に完成カードが存在できる (1=A-low も有効)
            if low_end >= 1 and high_end <= 14:
                return True
    return False


def _gutshot(ranks: list[int]) -> bool:
    """インサイドストレートドロー、または一端ふさがりの4連続ランク."""
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 3):
        window = unique[i:i + 4]
        span = window[-1] - window[0]
        if span == 3:
            # 4連続だが一端がふさがり (J-Q-K-A や A-2-3-4)
            low_end = window[0] - 1
            high_end = window[-1] + 1
            if not (low_end >= 1 and high_end <= 14):
                return True
        elif span == 4 and len(set(window)) == 4:
            # 真のインサイドドロー (1箇所ギャップ)
            return True
    return False


def _backdoor_flush(cards: list[Card]) -> bool:
    """同一スーツが3枚 (バックドアフラッシュドロー)."""
    return any(v == 3 for v in Counter(c.suit for c in cards).values())


def _backdoor_straight(ranks: list[int]) -> bool:
    """連続した3ランク (バックドアストレートドロー)."""
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 2):
        window = unique[i:i + 3]
        if window[-1] - window[0] == 2:
            return True
    return False


# ---------------------------------------------------------------------------
# メイン評価関数
# ---------------------------------------------------------------------------

def evaluate(combo: str, board: str) -> tuple[int, str]:
    """HandScore とカテゴリラベルを返す.

    Args:
        combo: ホールカード文字列 (例: "AhKs", "TsTd")
        board: ボードカード文字列 (例: "Ks,7d,2c" or "Ks7d2c")

    Returns:
        (score, label): score は 0-20 の HandScore, label は日本語カテゴリ名
    """
    hole = parse_combo(combo)
    board_cards = parse_board(board)
    all_cards = hole + board_cards

    hole_ranks = [c.rank for c in hole]
    board_ranks = sorted([c.rank for c in board_cards], reverse=True)
    all_ranks = [c.rank for c in all_cards]

    rank_counts = Counter(all_ranks)
    hole_rank_set = set(hole_ranks)

    # --- メイドハンド (強い順に判定) ---

    if _has_flush(all_cards):
        return 20, "フラッシュ/SF"

    if _has_straight(all_ranks):
        return 18, "ストレート"

    # セット / トリップス
    for r, cnt in rank_counts.items():
        if cnt >= 3:
            label = "セット" if r in hole_rank_set else "トリップス"
            return 18, label

    # ペアのリスト (ホールカードが関与するもの)
    pairs = [r for r, cnt in rank_counts.items() if cnt == 2]
    hole_pairs = [r for r in pairs if r in hole_rank_set]

    # 2ペア
    if len(pairs) >= 2 and hole_pairs:
        return 15, "2ペア"

    # 1ペア (ホールカードが関与)
    if hole_pairs:
        paired_rank = hole_pairs[0]
        top_board = board_ranks[0] if board_ranks else 0
        second_board = board_ranks[1] if len(board_ranks) > 1 else 0

        other_hole = [r for r in hole_ranks if r != paired_rank]
        kicker = max(other_hole) if other_hole else 0

        fd = _flush_draw(all_cards)
        oesd_draw = _oesd(all_ranks)
        has_draw = fd or oesd_draw

        # オーバーペア
        if paired_rank > top_board:
            return 15, "オーバーペア"

        # トップペア
        if paired_rank == top_board:
            if kicker == 14:
                return 15, "TPTK"
            elif kicker >= 12:
                base, label = 12, "TP+強キッカー"
            elif kicker >= 8:
                base, label = 10, "TP+中キッカー"
            else:
                base, label = 10, "TP+弱キッカー"
            if has_draw and base < 15:
                return 12, f"コンボドロー({label})"
            return base, label

        # セカンドペア
        if paired_rank == second_board:
            if kicker >= 12:
                base, label = 8, "セカンドペア強"
            else:
                base, label = 5, "セカンドペア弱"
            if has_draw:
                return 12, f"コンボドロー({label})"
            return base, label

        # ボトムペア / アンダーペア
        base, label = 5, "弱ペア/ボトムペア"
        if has_draw:
            return 8, "ドロー+弱ペア"
        return base, label

    # --- ドローのみ ---

    fd = _flush_draw(all_cards)
    oesd_draw = _oesd(all_ranks)
    gs = _gutshot(all_ranks)
    bd_flush = _backdoor_flush(all_cards)
    bd_str = _backdoor_straight(all_ranks)

    if fd and oesd_draw:
        return 12, "コンボドロー(FD+OESD)"
    if fd:
        return 10, "フラッシュドロー"
    if oesd_draw:
        return 8, "OESD"
    if gs:
        return 5, "ガットショット"
    if bd_flush or bd_str:
        return 2, "バックドアドロー"

    return 2, "エア"


def bucket(score: int) -> str:
    """HandScore を H1/H2/H3 バケツに分類する."""
    if score >= 15:
        return "H3"
    elif score >= 8:
        return "H2"
    else:
        return "H1"


# ---------------------------------------------------------------------------
# 動作確認用テスト
# ---------------------------------------------------------------------------

def _run_tests() -> None:
    cases = [
        # (combo, board, expected_score, expected_bucket, note)
        ("KhKd", "Kc,7d,2s", 18, "H3", "セット"),
        ("AhKh", "Ks,7d,2c", 15, "H3", "TPTK"),
        ("KhQd", "Ks,7d,2c", 12, "H2", "TP+強キッカー"),
        ("Kh9d", "Ks,7d,2c", 10, "H2", "TP+中キッカー"),
        ("Kh3d", "Ks,7d,2c", 10, "H2", "TP+弱キッカー"),
        ("AhAs", "Ts,9d,8c", 15, "H3", "オーバーペア"),
        ("9h9d", "Ks,7d,2c", 5,  "H1", "アンダーペア"),
        ("7h6h", "Ks,7d,2c", 5,  "H1", "セカンドペア弱"),
        ("AhJh", "Ks,7h,2h", 10, "H2", "フラッシュドロー"),
        ("JhTh", "9h,8h,2s", 12, "H2", "コンボドロー(FD+OESD)"),  # 4h + J-T-9-8 OESD
        ("JsTd", "9h,8c,2d", 8,  "H2", "OESD"),                    # J-T-9-8 pure OESD
        ("AhQd", "Ks,7d,2c", 2,  "H1", "エア"),
        ("QhJh", "Ah,Kh,Th", 20, "H3", "フラッシュ (5枚ハート)"),
        ("QhJd", "Ah,Kc,Ts", 18, "H3", "ストレート(AKQJT)"),
        ("2h2d", "Ks,7d,2c", 18, "H3", "セット"),
        ("9h8h", "Ts,7d,2h", 8,  "H2", "OESD (ハートは3枚のみ)"),
        ("QhJh", "Ah,Kh,2c", 10, "H2", "FD のみ (J-Q-K-A は一端ふさがり)"),
        ("JsTd", "Qs,9h,8c", 18, "H3", "ストレート (8-9-T-J-Q)"),
        ("AhQh", "Kh,Jh,2c", 10, "H2", "FD のみ (A-K-Q-J 一端ふさがり)"),
        ("Ts9h", "8d,7c,2s", 8,  "H2", "OESD (7-8-9-T)"),
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
