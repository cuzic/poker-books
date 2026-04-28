#!/usr/bin/env python3
"""ボード文字列から特徴量と 17 型分類を得るユーティリティ.

巻③ 第4章の 17 型分類に従ってボードを判別する。
"""
from __future__ import annotations
import re
from dataclasses import dataclass

RANK_VALUE = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5,
    "4": 4, "3": 3, "2": 2,
}


@dataclass
class BoardFeatures:
    """フロップ 3 枚の構造特徴."""
    ranks: list[int]            # 降順 (top, mid, low)
    rank_chars: list[str]
    suits: list[str]            # 例: ['s', 's', 'd']
    is_paired: bool
    is_trips: bool
    is_monotone: bool
    is_2tone: bool
    is_rainbow: bool
    top: int
    middle: int
    low: int
    max_diff: int
    is_broadway: bool           # 全 3 枚 ≥ T
    is_high_top: bool           # top ∈ {A, K, Q}
    is_connected3: bool         # max_diff ≤ 2
    is_high_connected: bool     # max_diff ≤ 4 かつ top ≥ T
    type_code: str              # 例: '1a', '2c', '4d'
    type_name: str

    def to_dict(self) -> dict:
        return {
            "ranks": self.ranks,
            "rank_chars": self.rank_chars,
            "suits": self.suits,
            "top": self.top,
            "middle": self.middle,
            "low": self.low,
            "max_diff": self.max_diff,
            "is_paired": self.is_paired,
            "is_trips": self.is_trips,
            "is_monotone": self.is_monotone,
            "is_2tone": self.is_2tone,
            "is_rainbow": self.is_rainbow,
            "is_broadway": self.is_broadway,
            "is_high_top": self.is_high_top,
            "is_connected3": self.is_connected3,
            "is_high_connected": self.is_high_connected,
            "type_code": self.type_code,
            "type_name": self.type_name,
        }


def parse_board(board: str) -> tuple[list[str], list[str]]:
    """ボード表記をパースして (ranks, suits) を返す.

    対応形式:
      - 'Kc7d2s' (3 枚連結、suit 付き)
      - 'K72r' (3 ランク + suit_pattern: r=rainbow, ss=2tone, mono=monotone)
      - 'KQTss' (broadway + 2tone)
      - 'AAK' (ペア、suit 不明 → r 仮定)
    """
    s = board.strip()

    # フォーマット1: ランク+suit ペアが 3 つ (Kc7d2s)
    m = re.fullmatch(r"([2-9TJQKA])([cdhs])([2-9TJQKA])([cdhs])([2-9TJQKA])([cdhs])", s)
    if m:
        return ([m.group(1), m.group(3), m.group(5)],
                [m.group(2), m.group(4), m.group(6)])

    # フォーマット2: ランク 3 つ + suit pattern
    m = re.fullmatch(r"([2-9TJQKA])([2-9TJQKA])([2-9TJQKA])(r|ss|mono|tt)?", s)
    if m:
        ranks = [m.group(1), m.group(2), m.group(3)]
        pat = m.group(4) or ""
        if pat == "mono":
            suits = ["s", "s", "s"]
        elif pat in ("ss", "tt"):
            suits = ["s", "s", "d"]
        else:  # r か無指定
            suits = ["s", "d", "c"]
        return ranks, suits

    raise ValueError(f"Unrecognized board format: {board!r}")


def classify(board: str) -> BoardFeatures:
    """ボードを 17 型に分類して特徴量を返す."""
    rank_chars_raw, suits_raw = parse_board(board)
    # ランクを数値化して降順ソート
    paired = list(zip(rank_chars_raw, suits_raw))
    paired.sort(key=lambda x: -RANK_VALUE[x[0]])
    rank_chars = [p[0] for p in paired]
    suits = [p[1] for p in paired]
    ranks = [RANK_VALUE[c] for c in rank_chars]

    is_trips = ranks[0] == ranks[1] == ranks[2]
    is_paired = (ranks[0] == ranks[1] or ranks[1] == ranks[2]) and not is_trips
    suit_set = set(suits)
    is_monotone = len(suit_set) == 1
    is_2tone = len(suit_set) == 2
    is_rainbow = len(suit_set) == 3
    top, middle, low = ranks
    max_diff = top - low
    is_broadway = all(r >= 10 for r in ranks)
    is_high_top = top >= 12  # Q, K, A
    is_connected3 = max_diff <= 2
    is_high_connected = max_diff <= 4 and top >= 10

    # 17 型分類 (巻③ 第4章準拠)
    if is_trips:
        type_code, type_name = "trips", "trips"
    elif is_paired:
        # Pair の高さ
        pair_rank = ranks[0] if ranks[0] == ranks[1] else ranks[1]
        if pair_rank == 14:
            type_code, type_name = "6a", "paired-AA"
        elif pair_rank == 13:
            type_code, type_name = "6b", "paired-KK"
        elif pair_rank == 12:
            type_code, type_name = "6c", "paired-QQ"
        elif top >= 13:
            # A/K トップ + 低/中ペア (ペアは Q 以下)
            if pair_rank <= 7:
                type_code, type_name = "7a", "AK-high-lowpair"
            elif 8 <= pair_rank <= 10:
                type_code, type_name = "7b", "AK-high-midpair"
            else:
                type_code, type_name = "7c", "AK-high-Jpair"
        elif 2 <= pair_rank <= 7:
            type_code, type_name = "6d", "paired-low"
        else:
            type_code, type_name = "7x", "paired-other"
    elif is_monotone:
        if is_broadway:
            type_code, type_name = "5a", "mono-broadway"
        else:
            type_code, type_name = "5b", "mono-low"
    else:
        # 非ペア・非モノトーン
        if is_high_top:
            if is_2tone:
                if is_broadway:
                    type_code, type_name = "2c", "high-broadway-2tone"
                elif max_diff <= 4:
                    type_code, type_name = "2c2", "high-close-2tone"
                elif 5 <= max_diff <= 7:
                    type_code, type_name = "2a", "high-mid-2tone"
                else:
                    type_code, type_name = "1a", "high-dry-2tone"
            else:  # rainbow
                if middle == 10:  # mid=T
                    type_code, type_name = "2e", "high-midT-rainbow"
                elif max_diff <= 4:
                    type_code, type_name = "2f", "high-close-rainbow"
                elif 5 <= max_diff <= 7:
                    type_code, type_name = "1c", "high-mid-rainbow"
                else:
                    type_code, type_name = "1b", "high-dry-rainbow"
        else:  # ロー (top ≤ J)
            if top == 10:  # T トップ
                if is_2tone:
                    type_code, type_name = "4a", "low-T-2tone"
                else:
                    type_code, type_name = "4c", "low-T-rainbow"
            elif top == 11:  # J トップ
                if is_2tone:
                    type_code, type_name = "4a", "low-J-2tone"
                else:
                    if max_diff <= 4:
                        type_code, type_name = "4c", "low-J-close-rainbow"
                    else:
                        type_code, type_name = "3d", "low-J-mid-rainbow"
            else:  # 9 以下トップ
                if is_2tone:
                    if 5 <= max_diff <= 7:
                        type_code, type_name = "3c", "low-mid-2tone"
                    else:
                        type_code, type_name = "4b", "low-sub9-2tone"
                else:  # rainbow
                    if 5 <= max_diff <= 7:
                        type_code, type_name = "3d", "low-mid-rainbow"
                    elif max_diff <= 4:
                        type_code, type_name = "4d", "low-sub9-rainbow"
                    else:
                        type_code, type_name = "3e", "low-other-rainbow"

    return BoardFeatures(
        ranks=ranks, rank_chars=rank_chars, suits=suits,
        is_paired=is_paired, is_trips=is_trips,
        is_monotone=is_monotone, is_2tone=is_2tone, is_rainbow=is_rainbow,
        top=top, middle=middle, low=low, max_diff=max_diff,
        is_broadway=is_broadway, is_high_top=is_high_top,
        is_connected3=is_connected3, is_high_connected=is_high_connected,
        type_code=type_code, type_name=type_name,
    )


# --- 簡易動作確認 ---
if __name__ == "__main__":
    import sys
    boards = sys.argv[1:] or [
        "K72r", "A82r", "Q53r", "K95r", "KT5r",
        "KQTss", "QJ9r", "T98ss", "987ss", "JT9ss",
        "AKQmono", "987mono", "K44", "AAK", "772",
        "965r", "632r", "876r", "A99",
    ]
    print(f'{"Board":<10} {"Type":<8} {"Name":<24} {"top":>3} {"max_diff":>8}')
    print("-" * 60)
    for b in boards:
        try:
            f = classify(b)
            print(f"{b:<10} {f.type_code:<8} {f.type_name:<24} {f.top:>3} {f.max_diff:>8}")
        except Exception as e:
            print(f"{b:<10} ERROR: {e}")
