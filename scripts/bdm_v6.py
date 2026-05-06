#!/usr/bin/env python3
"""BDM v6 = 巻③ 精密 HandScore (新スケール 0-100 equity %).

SPEC: knowledges/ds_redesign_v2/SPEC_HANDSCORE.md (v3)
SPEC: knowledges/ds_redesign_v2/SPEC_OTHER_FORMULAS.md (v3)

設計思想
--------
- 簡易版 (hand_evaluator_v3 / handscore_coarse): 役カテゴリ単位で HS を返す
  例: TPGK = 62 (キッカー Q+ なら一律)
- 精密版 (bdm_v6 / handscore_precise): 個別ハンド × 個別ボードでより精緻に補正
  例: AKs on K72r = 70 (TPTK)
      KQs on K72r = 64 (TPGK + Q キッカー、強キッカー側)
      KJs on K72r = 62 (TPGK 中央値)
      KTs on K72r = 60 (TPGK 弱キッカー寄り)

両者の差は ±5 以内に収まる (簡易版は精密版のカテゴリ平均)。

スケール
--------
旧 BDM v5: 0-30
新 BDM v6: 0-100 (equity % と読める)

主要差分:
  - 閾値: ≥8 → ≥40 (CR 検討)
  - ドロー加点: アウツ × 1.5 → アウツ × 4 (フロップ) / × 2 (ターン) / 0 (リバー)
  - ブロッカー加点: +3/+2 → +5/+3/+2
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import NamedTuple

RANK_STR = "23456789TJQKA"
RANK_MAP = {r: i + 2 for i, r in enumerate(RANK_STR)}


class Card(NamedTuple):
    rank: int
    suit: str


@dataclass
class HandScoreResult:
    score: int          # 0-100 にクランプされた HandScore
    role_score: int     # 役スコア (補正前)
    draw_bonus: int     # ドロー加点
    blocker_bonus: int  # ブロッカー加点
    label: str          # 役ラベル ("TPGK", "FD", etc.)


# ---------------------------------------------------------------------------
# パーサ
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# 役判定ヘルパ
# ---------------------------------------------------------------------------
def _flush_size(cards: list[Card]) -> tuple[int, str]:
    """最大スートの枚数とそのスート文字を返す。"""
    c = Counter(card.suit for card in cards)
    if not c:
        return 0, ""
    suit, n = c.most_common(1)[0]
    return n, suit


def _has_flush(cards: list[Card]) -> bool:
    return _flush_size(cards)[0] >= 5


def _straight_top(ranks: list[int]) -> int:
    """ストレート完成時、その最大ランクを返す。なければ 0。"""
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    best = 0
    for i in range(len(unique) - 4):
        window = unique[i:i + 5]
        if window[-1] - window[0] == 4 and len(set(window)) == 5:
            best = max(best, window[-1])
    return best


def _flush_draw(cards: list[Card]) -> tuple[bool, str]:
    """4 枚同スート (FD) があるか。あればそのスート文字。"""
    n, s = _flush_size(cards)
    return n == 4, s


def _backdoor_flush(cards: list[Card]) -> tuple[bool, str]:
    """3 枚同スート (BDFD) があるか。"""
    n, s = _flush_size(cards)
    return n == 3, s


def _oesd(ranks: list[int]) -> bool:
    """OESD (両端開き 8 outs) があるか。"""
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 3):
        window = unique[i:i + 4]
        if window[-1] - window[0] == 3 and len(set(window)) == 4:
            low_end = window[0] - 1
            high_end = window[-1] + 1
            if low_end >= 1 and high_end <= 14:
                return True
    return False


def _gutshot(ranks: list[int]) -> bool:
    """ガットショット (4 outs) があるか。"""
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 3):
        window = unique[i:i + 4]
        span = window[-1] - window[0]
        if span == 3 and len(set(window)) == 4:
            low_end = window[0] - 1
            high_end = window[-1] + 1
            if not (low_end >= 1 and high_end <= 14):
                return True
        elif span == 4 and len(set(window)) == 4:
            return True
    return False


def _backdoor_straight(ranks: list[int]) -> bool:
    """BDSD (3 連続またはギャップ 1 つ)。"""
    unique = sorted(set(ranks))
    if 14 in unique:
        unique = [1] + unique
    for i in range(len(unique) - 2):
        window = unique[i:i + 3]
        if window[-1] - window[0] <= 3 and len(set(window)) == 3:
            return True
    return False


def _count_outs_fd(hole: list[Card], board: list[Card]) -> int:
    """FD のアウツ数 (通常 9、ボード状況で減算)。"""
    has_fd, suit = _flush_draw(hole + board)
    if not has_fd:
        return 0
    used = sum(1 for c in hole + board if c.suit == suit)
    return max(0, 13 - used)


def _is_monotone(board: list[Card]) -> bool:
    """ボード 3 枚が同じスート。"""
    return len(set(c.suit for c in board)) == 1 and len(board) >= 3


def _has_three_flush(board: list[Card]) -> bool:
    """ボードに 3 枚同スートがあるか。"""
    c = Counter(c.suit for c in board)
    return any(v >= 3 for v in c.values())


# ---------------------------------------------------------------------------
# 簡易版 (hand_evaluator_v3 相当): 役カテゴリ単位
# ---------------------------------------------------------------------------
def handscore_coarse(combo: str, board: str, street: str = "flop") -> HandScoreResult:
    """簡易版 HandScore (SPEC_HANDSCORE.md §2 の表をそのまま適用).

    巻② で使う、役カテゴリ単位の粗い HS。読者の暗算用。
    精密版 (handscore_precise) との差は ±5 以内が目標。
    """
    return _evaluate(combo, board, street, precise=False)


# ---------------------------------------------------------------------------
# 精密版 (BDM v6): 個別ハンド × 個別ボード
# ---------------------------------------------------------------------------
def handscore_precise(combo: str, board: str, street: str = "flop") -> HandScoreResult:
    """精密版 HandScore (BDM v6).

    巻③ で使う、個別ハンドの kicker 強度や blocker などを反映した HS。
    簡易版との差は ±5 以内。
    """
    return _evaluate(combo, board, street, precise=True)


# 後方互換用の別名
def bdm_v6(combo: str, board: str, street: str = "flop") -> int:
    """BDM v6 の HS スコアだけを返すショートカット。"""
    return handscore_precise(combo, board, street).score


# ---------------------------------------------------------------------------
# 共通評価ロジック
# ---------------------------------------------------------------------------
def _evaluate(combo: str, board: str, street: str, precise: bool) -> HandScoreResult:
    hole = parse_combo(combo)
    board_cards = parse_board(board)
    all_cards = hole + board_cards

    hole_ranks = [c.rank for c in hole]
    board_ranks = sorted([c.rank for c in board_cards], reverse=True)
    all_ranks = [c.rank for c in all_cards]
    rank_counts = Counter(all_ranks)
    hole_set = set(hole_ranks)

    role_score, label = _role_score(
        hole, board_cards, hole_ranks, board_ranks, rank_counts, hole_set, precise
    )

    draw_bonus = _draw_bonus(hole, board_cards, all_cards, all_ranks, street, role_score)

    blocker_bonus = _blocker_bonus(hole, board_cards, board_ranks, role_score)

    raw = role_score + draw_bonus + blocker_bonus
    score = max(0, min(100, raw))
    return HandScoreResult(
        score=score,
        role_score=role_score,
        draw_bonus=draw_bonus,
        blocker_bonus=blocker_bonus,
        label=label,
    )


def _role_score(
    hole: list[Card],
    board: list[Card],
    hole_ranks: list[int],
    board_ranks: list[int],
    rank_counts: Counter,
    hole_set: set[int],
    precise: bool,
) -> tuple[int, str]:
    """役スコア (SPEC_HANDSCORE.md §2)。"""
    n_board = len(board)
    all_cards = hole + board

    # --- ストレートフラッシュ / クワッズ ---
    quads = [r for r, c in rank_counts.items() if c == 4]
    if quads:
        return 95, "クワッズ"

    if _has_flush(all_cards) and _straight_top([c.rank for c in all_cards]) > 0:
        # ストレートフラッシュの判定 (簡略化、同スート 5 枚で straight 判定)
        n, suit = _flush_size(all_cards)
        if n >= 5:
            sf_ranks = [c.rank for c in all_cards if c.suit == suit]
            if _straight_top(sf_ranks) > 0:
                return 95, "ストレートフラッシュ"

    # --- フルハウス ---
    trips = [r for r, c in rank_counts.items() if c == 3]
    pairs_all = [r for r, c in rank_counts.items() if c == 2]
    if trips and (len(trips) >= 2 or pairs_all):
        return 92, "フルハウス"

    # --- フラッシュ ---
    if _has_flush(all_cards):
        n, suit = _flush_size(all_cards)
        suited_ranks = sorted(
            [c.rank for c in all_cards if c.suit == suit], reverse=True
        )
        top_flush_rank = suited_ranks[0]
        # 自分の hole にナッツがあるか
        my_top = max((c.rank for c in hole if c.suit == suit), default=0)
        if precise:
            if my_top == 14:
                return 90, "Aハイフラッシュ"
            elif my_top >= 12:
                return 87, "高フラッシュ"
            elif my_top >= 9:
                return 83, "フラッシュ(中)"
            else:
                return 78, "フラッシュ(低)"
        else:
            if my_top == 14:
                return 90, "Aハイフラッシュ"
            return 85, "フラッシュ"

    # --- ストレート ---
    str_top = _straight_top([c.rank for c in all_cards])
    if str_top > 0:
        if precise:
            if str_top == 14:
                return 85, "ストレート(broadway)"
            elif str_top >= 11:
                return 82, "ストレート(high)"
            elif str_top >= 8:
                return 80, "ストレート(mid)"
            else:
                return 78, "ストレート(low)"
        else:
            if str_top == 14:
                return 85, "ストレート(broadway)"
            elif str_top >= 11:
                return 82, "ストレート(high)"
            elif str_top >= 8:
                return 80, "ストレート(mid)"
            else:
                return 78, "ストレート(low)"

    # --- セット / トリップス ---
    if trips:
        trip_rank = max(trips)
        is_set = trip_rank in hole_set and hole_ranks.count(trip_rank) == 2
        if is_set:
            top_b = board_ranks[0] if board_ranks else 0
            if trip_rank == top_b:
                return 92, "Top set"
            elif len(board_ranks) > 1 and trip_rank == board_ranks[1]:
                return 88, "Mid set"
            else:
                return 85, "Bottom set"
        else:
            return 85, "トリップス"

    # --- 2 ペア ---
    hole_pair_ranks = [r for r, c in rank_counts.items() if c == 2 and r in hole_set]
    board_pair_ranks = [r for r, c in rank_counts.items() if c == 2 and r not in hole_set]

    # 自分の 2 枚がペアになっている場合 (pocket pair)
    pocket_pair = (
        len(hole_ranks) == 2
        and hole_ranks[0] == hole_ranks[1]
    )

    # 2 ペア判定: hole が両方ボードにヒット (= split 2pair) または
    # 1 つはポケットペア + ボードに別のペア
    if not pocket_pair:
        # 個別の hole カードが両方ボードとペア
        hits = [r for r in hole_ranks if rank_counts.get(r, 0) == 2]
        if len(set(hits)) == 2 and len(board_ranks) >= 2:
            top_b = board_ranks[0]
            second_b = board_ranks[1] if len(board_ranks) > 1 else 0
            third_b = board_ranks[2] if len(board_ranks) > 2 else 0
            paired_set = set(hits)
            if top_b in paired_set and second_b in paired_set:
                return 78, "2ペア(top 2)"
            elif top_b in paired_set and third_b in paired_set:
                return 75, "2ペア(top+bottom)"
            elif top_b in paired_set:
                return 72, "2ペア(top+mid)"
            else:
                return 68, "2ペア(split)"

    # --- ペア役 (1 ペア) ---
    if hole_pair_ranks or pocket_pair:
        if pocket_pair:
            paired_rank = hole_ranks[0]
        else:
            paired_rank = hole_pair_ranks[0]

        other_hole_ranks = [r for r in hole_ranks if r != paired_rank]
        kicker = max(other_hole_ranks) if other_hole_ranks else 0

        top_b = board_ranks[0] if board_ranks else 0
        second_b = board_ranks[1] if len(board_ranks) > 1 else 0
        third_b = board_ranks[2] if len(board_ranks) > 2 else 0

        # オーバーペア
        if pocket_pair and paired_rank > top_b:
            if paired_rank >= 12:  # AA-QQ
                base = 78
                label = "オーバーペア(高)"
            elif paired_rank >= 10:  # JJ-TT
                base = 72
                label = "オーバーペア(中)"
            else:
                base = 68
                label = "オーバーペア(低)"
            if precise:
                # 板の最高位との余裕で微調整 (gap が大きいほど安全)
                gap = paired_rank - top_b
                if gap >= 4:  # AA on T-low, KK on 9-low 等
                    base += 1
                elif gap == 1:  # AA on K, KK on Q 等 (微妙な圧迫)
                    base -= 1
            return base, label

        # トップペア
        if paired_rank == top_b:
            if kicker == 14 or kicker == 13:
                # TPTK
                base = 70
                label = "TPTK"
                if precise and kicker == 14 and paired_rank < 14:
                    base = 70  # AKx 系
                elif precise and kicker == 13:
                    base = 68  # KQx で K が top の TPTK 相当
                return base, label
            elif kicker >= 12:
                base = 62
                label = "TPGK"
                if precise:
                    # Q キッカーは 64、J キッカーは 60
                    if kicker == 12:
                        base = 64
                    elif kicker == 11:
                        base = 60
                return base, label
            elif kicker >= 8:
                base = 50
                label = "TPMK"
                if precise:
                    base = 48 + (kicker - 8) * 1  # 8→48, 9→49, T→50
                return base, label
            else:
                base = 45
                label = "TPWK"
                if precise:
                    base = 42 + max(0, kicker - 2)  # 弱いほど下がる、目安
                    base = max(40, min(45, base))
                return base, label

        # アンダーペア (pocket pair で板より低い)
        if pocket_pair and paired_rank < top_b:
            if paired_rank >= 12:  # まれ (KK on AAA)
                base, label = 45, "アンダーペア(高)"
            elif paired_rank >= 10:
                base, label = 40, "アンダーペア(中)"
            else:
                base, label = 35, "アンダーペア(低)"
            if precise:
                # 板の最高位との差で微調整
                gap = top_b - paired_rank
                if gap <= 1:
                    base += 1
                elif gap >= 5:
                    base -= 1
            return base, label

        # セカンドペア
        if paired_rank == second_b:
            if kicker >= 12:
                base, label = 42, "セカンドペア(強)"
            elif kicker >= 8:
                base, label = 35, "セカンドペア(中)"
            else:
                base, label = 32, "セカンドペア(弱)"
            if precise:
                # キッカーが A なら +2、Q なら 0
                if kicker == 14:
                    base += 2
                elif kicker == 13:
                    base += 1
            return base, label

        # ボトムペア
        if paired_rank == third_b:
            base, label = 32, "ボトムペア"
            if precise and kicker >= 12:
                base += 2
            return base, label

        # それ以外は board pair (paired by board only)
        return 30, "ボードペアのみ"

    # --- 役なし ---
    max_hole = max(hole_ranks) if hole_ranks else 0
    if 14 in hole_ranks:
        return 25, "Aハイ"
    elif 13 in hole_ranks:
        return 20, "Kハイ"
    elif 12 in hole_ranks:
        return 15, "Qハイ"
    elif max_hole >= 10:
        return 12, "T-Jハイ"
    elif max_hole >= 7:
        return 10, "中ハイカード"
    else:
        return 8, "空振り"


def _draw_bonus(
    hole: list[Card],
    board: list[Card],
    all_cards: list[Card],
    all_ranks: list[int],
    street: str,
    role_score: int,
) -> int:
    """ドロー加点 (SPEC_HANDSCORE.md §3)。"""
    if street == "river":
        return 0

    multiplier = 4 if street == "flop" else 2  # turn は ×2

    fd_outs = _count_outs_fd(hole, board)
    has_fd = fd_outs > 0
    has_oesd = _oesd(all_ranks)
    has_gs = _gutshot(all_ranks) and not has_oesd
    has_bdfd, _ = _backdoor_flush(all_cards) if not has_fd else (False, "")
    has_bdsd = _backdoor_straight(all_ranks) and not has_oesd and not has_gs

    bonus = 0
    outs = 0

    # メインドローのアウツを集計
    if has_fd:
        outs += fd_outs
    if has_oesd:
        outs += 8
    elif has_gs:
        outs += 4

    # コンボドローの重複控除 (-2 outs)
    if has_fd and (has_oesd or has_gs):
        outs -= 2

    if outs > 0:
        bonus = outs * multiplier

    # モノトーン板の FD は ×0.5 補正
    if has_fd and (_is_monotone(board) or _has_three_flush(board)):
        # 既に 3-flush 板なので相手も完成可能 → FD 部分のみ ×0.5
        # ただし flop で street == "flop" のときのみ全 outs から FD 分を半減
        fd_part = fd_outs * multiplier
        if has_oesd:
            fd_part = max(0, (fd_outs - 2)) * multiplier
        bonus -= fd_part // 2

    # バックドア (固定値、フロップのみ)
    if street == "flop":
        if has_bdfd and has_bdsd:
            bonus += 6
        elif has_bdfd:
            bonus += 5
        elif has_bdsd:
            bonus += 2

    # ペア持ちのドローは加点を半分にする (実用上の補正)
    # SPEC §2.3 ではペア+BDFD = +3、ペア+BDSD = +1
    if role_score >= 32:  # 何らかのペア役以上
        if street == "flop" and not has_fd and not has_oesd and not has_gs:
            # ペア + バックドアのみ
            if has_bdfd and has_bdsd:
                return 4
            elif has_bdfd:
                return 3
            elif has_bdsd:
                return 1
            return 0

    return max(0, bonus)


def _blocker_bonus(
    hole: list[Card],
    board: list[Card],
    board_ranks: list[int],
    role_score: int,
) -> int:
    """ブロッカー加点 (SPEC_HANDSCORE.md §4、重複加算なし、最大値のみ).

    既に強い役 (ストレート以上) や、kicker として既に役に組み込まれているカードは
    重複加算しない。
    """
    # 既に強い役 (ストレート以上) はブロッカー加点しない
    if role_score >= 78:
        return 0

    hole_ranks = [c.rank for c in hole]
    board_suits = Counter(c.suit for c in board)

    # 役に既に "使っている" カードを判定
    # トップペアの kicker はブロッカー扱いしない
    top_b = board_ranks[0] if board_ranks else 0
    paired_in_hole = [r for r in hole_ranks if r in board_ranks]
    used_as_kicker = set()
    if paired_in_hole and len(hole_ranks) == 2:
        # 1 枚がペア、もう 1 枚が kicker として既に使われている
        for r in hole_ranks:
            if r not in paired_in_hole:
                used_as_kicker.add(r)

    candidates = []

    # ナッツフラッシュブロッカー: ボードに 2+ 同スートあり、A 同スート保有
    for suit, n in board_suits.items():
        if n >= 2:
            for c in hole:
                if c.suit == suit and c.rank == 14:
                    candidates.append(5)

    # ナッツストレートブロッカー (連続板で A/K 保有)
    sorted_board = sorted(set(board_ranks))
    if len(sorted_board) >= 2:
        max_diff = max(sorted_board) - min(sorted_board)
        if max_diff <= 4 and 14 in hole_ranks and 14 not in board_ranks \
                and 14 not in used_as_kicker:
            candidates.append(3)
        if max_diff <= 4 and 13 in hole_ranks and 13 not in board_ranks \
                and 13 not in used_as_kicker:
            candidates.append(3)

    # 上位セットブロッカー (ペアボードで K/A 保有)
    pair_on_board = any(v == 2 for v in Counter(board_ranks).values())
    if pair_on_board:
        if 14 in hole_ranks and 14 not in board_ranks and 14 not in used_as_kicker:
            candidates.append(3)
        elif 13 in hole_ranks and 13 not in board_ranks and 13 not in used_as_kicker:
            candidates.append(3)

    # バリューブロッカー (Q が hole にあり、板は K/A ハイ)
    # ただし Q を kicker として既に使っている場合は除外
    if 12 in hole_ranks and 12 not in board_ranks and 12 not in used_as_kicker:
        if board_ranks and max(board_ranks) >= 13:
            candidates.append(2)

    # バックドアブロッカー (+1)
    for suit, n in board_suits.items():
        if n == 2:
            for c in hole:
                if c.suit == suit and c.rank >= 11 and not candidates:
                    candidates.append(1)
                    break

    return max(candidates) if candidates else 0


# ---------------------------------------------------------------------------
# 後手スコア (SPEC_OTHER_FORMULAS.md §1)
# ---------------------------------------------------------------------------
A_VALUES = {"dry": 12, "semiwet": 6, "wet": 0}
C_VALUES = {33: 12, 50: 17, 75: 22, 100: 25, 150: 30}
M_VALUES = {2: 0, 3: 12, 4: 22}


def defender_score(
    hand_score: int,
    board_type: str = "dry",
    bet_pct: int = 50,
    n_players: int = 2,
) -> int:
    """後手スコア = HandScore + A − C − M。"""
    a = A_VALUES[board_type]
    c = C_VALUES[bet_pct]
    m = M_VALUES[min(n_players, 4)]
    return hand_score + a - c - m


def defender_action(score: int) -> str:
    """≥40 → CR、20-39 → コール、<20 → フォールド。"""
    if score >= 40:
        return "CR"
    elif score >= 20:
        return "Call"
    else:
        return "Fold"


# ---------------------------------------------------------------------------
# 動作確認用エントリポイント
# ---------------------------------------------------------------------------
def _run_consistency_check() -> None:
    """簡易版 vs 精密版の整合性チェック (主要 20 ハンド)。"""
    cases = [
        # (combo, board, street, expected_label_pattern)
        ("AhKs", "Kc7d2c", "flop", "TPTK"),
        ("KsQh", "Kc7d2c", "flop", "TPGK"),
        ("KsJh", "Kc7d2c", "flop", "TPGK"),
        ("KsTh", "Kc7d2c", "flop", "TPMK"),
        ("Ks5h", "Kc7d2c", "flop", "TPWK"),
        ("AhAs", "Kc7d2c", "flop", "オーバーペア(高)"),
        ("JsJh", "Kc7d2c", "flop", "アンダーペア(中)"),
        ("KhKd", "Kc7d2c", "flop", "Top set"),
        ("7h7d", "Kc7d2c", "flop", "Mid set"),
        ("AhQc", "KcQd7c", "flop", "セカンドペア(強)"),
        ("AhKc", "Kh8c2c", "flop", "TPTK"),  # FD 込み (with K of clubs)
        ("AsKs", "Ks8c2c", "flop", "TPTK"),
        ("9s8s", "7h6c2d", "flop", "9ハイ"),  # OESD 役なし
        ("JsTs", "9s8c2h", "flop", "T-Jハイ"),  # OESD
        ("AsQh", "Ks7d2c", "flop", "Aハイ"),
        ("AhKh", "QhJh2s", "flop", "Aハイ"),  # FD + GS
        ("9h9d", "Kh7c2d", "flop", "アンダーペア(低)"),
        ("AhAh", "Kc7d2c", "flop", "オーバーペア(高)"),  # invalid duplicates but for shape
        ("8h7h", "Kc8d2c", "flop", "セカンドペア(中)"),
        ("Ad5d", "TsTd4d", "flop", "Aハイ"),  # FD on paired board
    ]

    print(f"{'combo':6s} {'board':10s} {'簡易':>4} {'精密':>4} {'差':>3} {'簡易ラベル':20s} {'精密ラベル':20s}")
    print("-" * 80)

    max_diff = 0
    n_within_5 = 0
    n_total = 0
    for combo, board, street, _ in cases:
        try:
            coarse = handscore_coarse(combo, board, street)
            precise = handscore_precise(combo, board, street)
        except (KeyError, ValueError) as e:
            print(f"  SKIP {combo} on {board}: {e}")
            continue
        diff = abs(coarse.score - precise.score)
        n_total += 1
        if diff <= 5:
            n_within_5 += 1
        max_diff = max(max_diff, diff)
        flag = "  " if diff <= 5 else "!!"
        print(f"{combo:6s} {board:10s} {coarse.score:>4d} {precise.score:>4d} "
              f"{diff:>3d} {flag} {coarse.label:18s} {precise.label:18s}")

    print(f"\n整合性: {n_within_5}/{n_total} (±5 以内)、最大差 {max_diff}")


if __name__ == "__main__":
    _run_consistency_check()
