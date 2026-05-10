#!/usr/bin/env python3
"""HandScore 評価関数 v3 (新スケール: 0-100 equity %).

仕様: knowledges/ds_redesign_v2/SPEC_HANDSCORE.md (確定日: 2026-05-05)

v2 (0-30 スケール) からの主な変更:
  - HS は equity % (0-100) として読める
  - ドロー加点は Rule of 2 / Rule of 4 を直接使用
  - フロップ: outs × 4 (上限 50)
  - ターン:  outs × 2 (上限 30)
  - リバー:  ドロー加点 = 0
  - バックドアは固定値 (BDFD +5, BDSD +2, ダブル +6)
  - ブロッカー加点は最大値のみ (重複不可)
  - 後手スコア閾値: ≥40 RAISE / 20-39 CALL / <20 FOLD
  - バケツ境界: H3 ≥ 65, H2 ≥ 35, H1 < 35

役スコア表は SPEC §2 に準拠。式と例は SPEC §5 を参照。
"""
from __future__ import annotations

from collections import Counter
from typing import NamedTuple

# v2 から helper を再利用
from hand_evaluator_v2 import (
    Card,
    RANK_MAP,
    RANK_STR,
    parse_card,
    parse_combo,
    _has_flush,
    _has_straight,
    _flush_draw,
    _oesd,
    _gutshot,
    _backdoor_flush,
    _backdoor_straight,
)


def parse_board(s: str) -> list[Card]:
    """ボード文字列をパース。

    "Kc7d2s" / "Kc,7d,2s" / "Ks7c2c,5d" / "Ks7c2c,5d,Qh" のような
    混在フォーマットに対応 (連続列とカンマ区切りの混在を許容)。
    """
    s = s.replace(" ", "")
    cards: list[Card] = []
    for token in s.split(","):
        if not token:
            continue
        # token は連続したカード列 (例: "Ks7c2c")
        for i in range(0, len(token), 2):
            cards.append(parse_card(token[i:i + 2]))
    return cards

# ============================================================
# 役スコア定数 (SPEC §2)
# ============================================================
NEW_ROLE_SCORE = {
    # 完成役
    "straight_flush": 95,
    "quads": 95,
    "full_house": 92,
    "flush_ace": 90,
    "flush_mid": 85,
    "straight_broadway": 85,
    "straight_high": 82,
    "straight_mid": 80,
    "straight_low": 78,
    # セット / トリップス
    "top_set": 92,
    "mid_set": 88,
    "bottom_set": 85,
    "trips": 85,
    # 2 ペア
    "two_pair_top": 78,
    "two_pair_top_mid": 75,
    "two_pair_top_bottom": 72,
    "two_pair_split": 68,
    # オーバーペア
    "overpair_high": 78,
    "overpair_mid": 72,
    "overpair_low": 68,
    # トップペア
    "tptk": 70,
    "tpgk": 62,
    "tpmk": 50,
    "tpwk": 45,
    # アンダーペア
    "underpair_high": 45,
    "underpair_mid": 40,
    "underpair_low": 35,
    # セカンドペア
    "second_pair_strong": 42,
    "second_pair_mid": 35,
    "second_pair_weak": 32,
    # ボトムペア
    "bottom_pair": 32,
    # ハイカード
    "ahigh": 25,
    "khigh": 20,
    "qhigh": 15,
    "jhigh": 10,
    "air": 8,
    # set_plus はペアボード等の汎用
    "set_plus": 88,
}


# ============================================================
# ドロー加点 (SPEC §3)
# ============================================================
def draw_bonus(outs: int, street: str, draw_type: str = "") -> int:
    """ドロー加点を返す。

    Args:
        outs: 完成までの effective outs
        street: "flop" / "turn" / "river"
        draw_type: "BDFD" / "BDSD" / "BDFD+BDSD" 等の補足タグ
    """
    if street == "river":
        return 0
    # バックドアは固定値 (ストリート問わず flop/turn でのみ意味あり)
    if "BDFD+BDSD" in draw_type or "DBL_BD" in draw_type:
        return 6
    if "BDFD" in draw_type:
        return 5
    if "BDSD" in draw_type:
        return 2
    if street == "flop":
        return min(outs * 4, 60)
    elif street == "turn":
        return min(outs * 2, 30)
    return 0


# ============================================================
# ブロッカー加点 (SPEC §4)
# ============================================================
def blocker_bonus(blocker_type: str) -> int:
    """ブロッカー加点 (重複加算なし、最大値のみ)。"""
    return {
        "nut": 5,
        "set": 3,
        "straight": 3,
        "value": 2,
        "backdoor": 1,
    }.get(blocker_type, 0)


# ============================================================
# アウツ計算 helpers
# ============================================================
def _count_flush_outs(hole: list[Card], board: list[Card]) -> int:
    """FD のアウツ数 (4 同スートで 9 outs が代表値)。"""
    suit_counts = Counter(c.suit for c in (hole + board))
    for suit, cnt in suit_counts.items():
        if cnt == 4:
            # 13 - 4 = 9 outs (該当スートの残カード)
            return 13 - cnt
    return 0


def _count_oesd_outs(all_ranks: list[int]) -> int:
    """OESD のアウツ (8 outs が代表値)。"""
    return 8 if _oesd(all_ranks) else 0


def _count_gutshot_outs(all_ranks: list[int]) -> int:
    """ガットショットのアウツ (4 outs)。"""
    return 4 if _gutshot(all_ranks) else 0


def _count_overcards(hole_ranks: list[int], board_ranks: list[int]) -> int:
    """ボード最高ランク超のホールカード数 (×3 outs)。"""
    if not board_ranks:
        return 0
    top_board = max(board_ranks)
    return sum(1 for r in hole_ranks if r > top_board)


def _is_monotone_or_3flush(board: list[Card]) -> bool:
    """モノトーン / 3-flush 板 (FD 補正対象)。"""
    suit_counts = Counter(c.suit for c in board)
    return any(v >= 3 for v in suit_counts.values())


# ============================================================
# 役判定 (新スケール用)
# ============================================================
def _classify_role(hole: list[Card], board: list[Card]) -> tuple[int, str]:
    """役の種別を判定し、(役スコア, ラベル) を返す。

    ドロー加点・ブロッカー加点はここでは付与しない。
    """
    all_cards = hole + board
    hole_ranks = [c.rank for c in hole]
    board_ranks = sorted([c.rank for c in board], reverse=True)
    all_ranks = [c.rank for c in all_cards]

    rank_counts = Counter(all_ranks)
    hole_rank_set = set(hole_ranks)

    # ストレートフラッシュ判定 (簡略: フラッシュ + ストレート)
    if _has_flush(all_cards) and _has_straight(all_ranks):
        # 厳密にはフラッシュスートでストレートが必要だが、
        # 本評価器は近似のため SF とみなす
        return NEW_ROLE_SCORE["straight_flush"], "ストレートフラッシュ"

    # クワッズ
    for r, cnt in rank_counts.items():
        if cnt == 4:
            return NEW_ROLE_SCORE["quads"], "クワッズ"

    # フルハウス
    has_three = any(cnt >= 3 for cnt in rank_counts.values())
    pair_count = sum(1 for cnt in rank_counts.values() if cnt >= 2)
    if has_three and pair_count >= 2:
        return NEW_ROLE_SCORE["full_house"], "フルハウス"

    # フラッシュ
    if _has_flush(all_cards):
        # Ace 持ちフラッシュなら "Aハイフラッシュ"
        suit_counts = Counter(c.suit for c in all_cards)
        flush_suit = next(s for s, v in suit_counts.items() if v >= 5)
        flush_ranks = sorted(
            [c.rank for c in all_cards if c.suit == flush_suit], reverse=True
        )
        top_flush = flush_ranks[0]
        # ナッツ判定: ボードに無く、自分が持つ最高カード
        my_flush_ranks = [c.rank for c in hole if c.suit == flush_suit]
        if my_flush_ranks and max(my_flush_ranks) == 14:
            return NEW_ROLE_SCORE["flush_ace"], "Aハイフラッシュ"
        return NEW_ROLE_SCORE["flush_mid"], "フラッシュ"

    # ストレート
    if _has_straight(all_ranks):
        # 上端カードで分類
        unique = sorted(set(all_ranks))
        if 14 in unique:
            unique_with_low_a = [1] + unique
        else:
            unique_with_low_a = unique
        # ストレートの最高ランクを探す
        best_high = 0
        for i in range(len(unique_with_low_a) - 4):
            window = unique_with_low_a[i:i + 5]
            if window[-1] - window[0] == 4 and len(set(window)) == 5:
                best_high = max(best_high, window[-1])
        if best_high == 14:
            return NEW_ROLE_SCORE["straight_broadway"], "Aハイストレート"
        elif best_high >= 11:
            return NEW_ROLE_SCORE["straight_high"], "ストレート(high)"
        elif best_high >= 8:
            return NEW_ROLE_SCORE["straight_mid"], "ストレート(mid)"
        else:
            return NEW_ROLE_SCORE["straight_low"], "ストレート(low)"

    # セット / トリップス
    for r, cnt in rank_counts.items():
        if cnt == 3:
            if r in hole_rank_set and hole_ranks.count(r) == 2:
                # ポケットペアと一致 → セット
                top_board = board_ranks[0] if board_ranks else 0
                second_board = board_ranks[1] if len(board_ranks) > 1 else 0
                if r == top_board:
                    return NEW_ROLE_SCORE["top_set"], "トップセット"
                elif r == second_board:
                    return NEW_ROLE_SCORE["mid_set"], "ミドルセット"
                else:
                    return NEW_ROLE_SCORE["bottom_set"], "ボトムセット"
            else:
                # ボードペアと自分のホールが一致 → トリップス
                return NEW_ROLE_SCORE["trips"], "トリップス"

    # 2 ペア
    pairs = [r for r, cnt in rank_counts.items() if cnt == 2]
    hole_pairs = [r for r in pairs if r in hole_rank_set]

    if len(pairs) >= 2 and hole_pairs:
        # 2 ペアの構成判定
        # ホールペア (ポケペア由来) 1 つ + ボードペア 1 つ等もある
        # ここでは「自分の関与する 2 ペア」を分類
        sorted_pairs = sorted(pairs, reverse=True)
        top_pair = sorted_pairs[0]
        second_pair = sorted_pairs[1] if len(sorted_pairs) > 1 else 0
        top_board = board_ranks[0] if board_ranks else 0
        # 両ホールカードがボードと一致した "2 ペア (top + ?)"
        if top_pair == top_board:
            if second_pair == (board_ranks[1] if len(board_ranks) > 1 else 0):
                return NEW_ROLE_SCORE["two_pair_top"], "2ペア(top2)"
            elif len(board_ranks) > 2 and second_pair >= board_ranks[2]:
                return NEW_ROLE_SCORE["two_pair_top_mid"], "2ペア(top+mid)"
            else:
                return NEW_ROLE_SCORE["two_pair_top_bottom"], "2ペア(top+bot)"
        return NEW_ROLE_SCORE["two_pair_split"], "2ペア(split)"

    # 1 ペア (ホール関与)
    if hole_pairs:
        paired_rank = hole_pairs[0]
        top_board = board_ranks[0] if board_ranks else 0
        second_board = board_ranks[1] if len(board_ranks) > 1 else 0

        other_hole = [r for r in hole_ranks if r != paired_rank]
        kicker = max(other_hole) if other_hole else 0

        # ポケットペアが盤上どこにも刺さらない場合 → オーバー or アンダーペア
        is_pocket_pair = (
            len(hole_ranks) == 2
            and hole_ranks[0] == hole_ranks[1]
            and paired_rank == hole_ranks[0]
            and paired_rank not in [c.rank for c in board]
        )

        if is_pocket_pair:
            if paired_rank > top_board:
                # オーバーペア
                if paired_rank >= 12:  # AA / KK / QQ
                    return NEW_ROLE_SCORE["overpair_high"], "オーバーペア(高)"
                elif paired_rank >= 10:  # JJ / TT
                    return NEW_ROLE_SCORE["overpair_mid"], "オーバーペア(中)"
                else:
                    return NEW_ROLE_SCORE["overpair_low"], "オーバーペア(低)"
            else:
                # アンダーペア
                if paired_rank >= 12:
                    return NEW_ROLE_SCORE["underpair_high"], "アンダーペア(高)"
                elif paired_rank >= 10:
                    return NEW_ROLE_SCORE["underpair_mid"], "アンダーペア(中)"
                else:
                    return NEW_ROLE_SCORE["underpair_low"], "アンダーペア(低)"

        # トップペア
        if paired_rank == top_board:
            if kicker == 14 or kicker == 13:  # A or K キッカー
                return NEW_ROLE_SCORE["tptk"], "TPTK"
            elif kicker >= 12:
                return NEW_ROLE_SCORE["tpgk"], "TPGK"
            elif kicker >= 8:
                return NEW_ROLE_SCORE["tpmk"], "TPMK"
            else:
                return NEW_ROLE_SCORE["tpwk"], "TPWK"

        # セカンドペア
        if paired_rank == second_board:
            if kicker >= 12:
                return NEW_ROLE_SCORE["second_pair_strong"], "セカンドペア(強)"
            elif kicker >= 8:
                return NEW_ROLE_SCORE["second_pair_mid"], "セカンドペア(中)"
            else:
                return NEW_ROLE_SCORE["second_pair_weak"], "セカンドペア(弱)"

        # ボトムペア
        return NEW_ROLE_SCORE["bottom_pair"], "ボトムペア"

    # ハイカード
    max_hole = max(hole_ranks) if hole_ranks else 0
    if max_hole == 14:
        return NEW_ROLE_SCORE["ahigh"], "Aハイ"
    elif max_hole == 13:
        return NEW_ROLE_SCORE["khigh"], "Kハイ"
    elif max_hole == 12:
        return NEW_ROLE_SCORE["qhigh"], "Qハイ"
    elif max_hole == 11:
        return NEW_ROLE_SCORE["jhigh"], "Jハイ"
    return NEW_ROLE_SCORE["air"], "空振り"


# ============================================================
# ドロー検出 (役なし時のみ加点を追加)
# ============================================================
def _calc_draw_bonus(
    hole: list[Card], board: list[Card], street: str, has_made_pair: bool
) -> tuple[int, str]:
    """役以外のドロー加点を計算。(加点, タグ) を返す。"""
    all_cards = hole + board
    all_ranks = [c.rank for c in all_cards]
    hole_ranks = [c.rank for c in hole]
    board_ranks = [c.rank for c in board]

    if street == "river":
        return 0, ""

    fd = _flush_draw(all_cards)
    oesd = _oesd(all_ranks)
    gs = _gutshot(all_ranks)
    bd_flush = _backdoor_flush(all_cards) and not fd
    bd_str = _backdoor_straight(all_ranks) and not (oesd or gs)

    # 2 同スートのホール + ボード 1 同スート (= 3-flush 構成) + OESD/GS は
    # SPEC §5 例5 に従い「強化コンボドロー」として扱う
    suited_hole = len(hole) == 2 and hole[0].suit == hole[1].suit
    suit_match_board = (
        suited_hole
        and any(c.suit == hole[0].suit for c in board)
    )
    enhanced_bd_combo = (
        suited_hole
        and suit_match_board
        and not fd
        and (oesd or gs)
        and street == "flop"
    )

    # FD + OESD コンボ
    if fd and oesd:
        outs = 13  # 重複 -2 控除済み (15 - 2)
        bonus = draw_bonus(outs, street)
        return bonus, "FD+OESD"
    if enhanced_bd_combo and oesd:
        # SPEC 例5: BDFD (3 outs相当) + OESD (8 outs) ≒ 11 effective outs (重複考慮)
        # FD+OESD (13 outs = +52) より下、OESD単独 (+32) より上
        outs = 11
        bonus = draw_bonus(outs, street)
        return bonus, "BDFD+OESD"
    if enhanced_bd_combo and gs:
        outs = 12
        bonus = draw_bonus(outs, street)
        return bonus, "BDFD+GS"
    if fd and gs:
        outs = 12  # 9 + 4 - 1 重複
        bonus = draw_bonus(outs, street)
        # モノトーン / 3-flush 板補正 (役なし時のみ; メイドハンドは相手と分けて評価)
        if _is_monotone_or_3flush(board) and not has_made_pair:
            bonus = bonus // 2
        return bonus, "FD+GS"
    if fd:
        outs = 9
        bonus = draw_bonus(outs, street)
        # モノトーン板補正は役なしの裸 FD のみ (例3 参照)
        if _is_monotone_or_3flush(board) and not has_made_pair:
            bonus = bonus // 2
        return bonus, "FD"
    if oesd:
        outs = 8
        return draw_bonus(outs, street), "OESD"
    if gs:
        outs = 4
        return draw_bonus(outs, street), "GS"

    # オーバーカード加点 (役なし時のみ)
    if not has_made_pair:
        oc = _count_overcards(hole_ranks, board_ranks)
        if oc >= 2:
            outs = oc * 3
            return draw_bonus(outs, street), f"{oc}OC"

    # バックドア
    if bd_flush and bd_str:
        return draw_bonus(0, street, "BDFD+BDSD"), "BDFD+BDSD"
    if bd_flush:
        return draw_bonus(0, street, "BDFD"), "BDFD"
    if bd_str:
        return draw_bonus(0, street, "BDSD"), "BDSD"

    return 0, ""


# ============================================================
# メイン関数
# ============================================================
def evaluate_v3(combo: str, board: str, street: str = "flop") -> tuple[int, str]:
    """新スケール HandScore (0-100 equity %)。

    Args:
        combo: ハンド ("AhKh" 等)
        board: ボード ("Kc7d2s" 等)
        street: "flop" / "turn" / "river"

    Returns:
        (hand_score, role_label)
    """
    hole = parse_combo(combo)
    board_cards = parse_board(board)

    # 役スコア
    role_score, role_label = _classify_role(hole, board_cards)

    # ペア役以上か (ドロー加点は役なし時のみ追加だが、ペア+ドローの補正もある)
    # SPEC §2.3 によれば「ペア+BDFD: +3 / ペア+BDSD: +1」
    has_pair_or_better = role_score >= NEW_ROLE_SCORE["bottom_pair"]
    has_made_pair = has_pair_or_better

    # ドロー加点
    bonus, draw_tag = _calc_draw_bonus(hole, board_cards, street, has_made_pair)

    # ペア時のドロー扱い:
    #  - 強ドロー (FD/OESD/GS) があれば加点 (役を持ちながらドロー継続)
    #  - 弱バックドアは固定値 (+3 BDFD / +1 BDSD)
    if has_made_pair and street != "river":
        if "BDFD+BDSD" in draw_tag:
            bonus = 3 + 1  # 4
        elif "BDFD" in draw_tag and "FD" not in draw_tag:
            bonus = 3
        elif "BDSD" in draw_tag and "OESD" not in draw_tag and "GS" not in draw_tag:
            bonus = 1
        elif draw_tag.endswith("OC"):
            # ペア持ちでオーバーカードは加点しない
            bonus = 0

    # ブロッカー加点 (簡易: ナッツフラッシュブロッカー / ストレートブロッカー)
    blocker = _calc_blocker_bonus(hole, board_cards)

    score = role_score + bonus + blocker
    score = max(0, min(100, score))  # クランプ

    label = role_label
    if draw_tag and bonus > 0:
        label = f"{role_label}+{draw_tag}"
    if blocker > 0:
        label = f"{label}+ブロッカー"

    return score, label


def _calc_blocker_bonus(hole: list[Card], board: list[Card]) -> int:
    """簡易ブロッカー判定。

    ナッツフラッシュブロッカー (3-flush 板で A♠ 等) を主に検出。
    """
    suit_counts = Counter(c.suit for c in board)
    for suit, cnt in suit_counts.items():
        if cnt >= 3:
            # 3-flush 以上の板で、自分がそのスートの A を持つ
            for c in hole:
                if c.suit == suit and c.rank == 14:
                    return blocker_bonus("nut")
    return 0


# ============================================================
# バケツ / 後手スコア / 判定
# ============================================================
def bucket_v3(score: int) -> str:
    """HS → H1/H2/H3 (新閾値)."""
    if score >= 65:
        return "H3"
    if score >= 35:
        return "H2"
    return "H1"


def back_score_v3(hs: int, A: int, C: int, M: int = 0) -> int:
    """後手スコア (新スケール)。

    Args:
        hs: HandScore (0-100)
        A: ボード補正 (+12 dry / +6 semi / 0 wet)
        C: ベット圧力 (33%=12 / 50%=17 / 75%=22 / 100%=25 / 150%=30)
        M: マルチウェイ補正 (HU=0 / 3-way=12 / 4-way+=22)

    Returns:
        後手スコア
    """
    return hs + A - C - M


def predict_v3(back_score: int) -> str:
    """新閾値 (≥40 RAISE / 20-39 CALL / <20 FOLD)."""
    if back_score >= 40:
        return "RAISE"
    if back_score >= 20:
        return "CALL"
    return "FOLD"


# ============================================================
# 動作確認 (SPEC §5 の例 1〜8)
# ============================================================
def _run_examples() -> None:
    """SPEC §5 の計算例を再現。"""
    cases = [
        # (combo, board, street, expected_min, expected_max, note)
        ("KhQh", "Kc7d2s", "flop", 60, 65, "例1: TPGK on K72r → 62"),
        ("KhQc", "Kc8c4c", "flop", 90, 100, "例2: TPGK + FD → ~98"),
        ("As5h", "Ts9s4s", "flop", 40, 60, "例3: 単独 FD on モノトーン (補正+ナッツ)"),
        ("9s8s", "7h6c2d", "flop", 35, 45, "例4: 単独 OESD → 40"),
        ("JsTs", "9s8c2h", "flop", 55, 70, "例5: コンボドロー FD+OESD → 60 (上限後)"),
        ("KcQc", "Ks7c2c,5d", "turn", 75, 85, "例6: TPGK + FD on turn → 80"),
        ("KcQc", "Ks7c2c,5d,Qh", "river", 70, 80, "例7: 2ペア on river → 75"),
        ("KcQc", "Ks7c2c,5d,9h", "river", 60, 65, "例8: TPGK ドロー失敗 river → 62"),
    ]

    passed = 0
    failed = 0
    print("=" * 72)
    print("SPEC §5 計算例の検証")
    print("=" * 72)
    for combo, board, street, exp_min, exp_max, note in cases:
        score, label = evaluate_v3(combo, board, street)
        ok = exp_min <= score <= exp_max
        status = "OK" if ok else "NG"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"[{status}] {note}")
        print(f"     {combo} on {board} ({street}) → HS={score} ({label})")
        if not ok:
            print(f"     期待範囲 [{exp_min}, {exp_max}] / 実測 {score}")

    print("=" * 72)
    print(f"{passed} passed, {failed} failed")
    print()

    # bucket / back_score / predict の動作確認
    print("=" * 72)
    print("bucket_v3 / back_score_v3 / predict_v3 の動作確認")
    print("=" * 72)
    print(f"bucket_v3(80) = {bucket_v3(80)}  (期待: H3)")
    print(f"bucket_v3(50) = {bucket_v3(50)}  (期待: H2)")
    print(f"bucket_v3(15) = {bucket_v3(15)}  (期待: H1)")

    # SPEC §10 の検証境界例
    # TPGK on K72r dry vs 50% bet: HS=62, A=12, C=17 → DS=57 (RAISE)
    ds = back_score_v3(62, 12, 17, 0)
    print(f"\nTPGK on K72r dry vs 50%: DS={ds} → {predict_v3(ds)} (期待: RAISE)")

    # ハイカード on K72r dry vs 75%: HS=25, A=12, C=22 → DS=15 (FOLD)
    ds = back_score_v3(25, 12, 22, 0)
    print(f"Ahigh on K72r dry vs 75%: DS={ds} → {predict_v3(ds)} (期待: FOLD)")

    # AA on K-T-6 wet 4-way vs 75%: HS=75, A=6, C=22, M=22 → DS=37 (CALL)
    ds = back_score_v3(75, 6, 22, 22)
    print(f"AA on KT6 wet 4-way vs 75%: DS={ds} → {predict_v3(ds)} (期待: CALL)")


if __name__ == "__main__":
    _run_examples()
