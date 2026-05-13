"""
calc.py — 『迷わないポーカー』シリーズ 共通計算式 (SSOT)

全巻 (Vol2–Vol5) の generator がここから式を参照する。
poker-drill の calc.py と仕様を同期させること。

フォーマット:
  ボード: "Kc,7d,2s" (カンマ区切り, ASCII スート)
  ハンド: "AKs", "77", "AKo"  (抽象) または "Ac,Kd" (具体)

2026-05-12 初版
"""
from __future__ import annotations
from collections import Counter
from itertools import combinations
from typing import Literal

# ── Rank / Suit constants ─────────────────────────────────────────────────────

RANK_MAP: dict[str, int] = {
    '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8,
    '9': 9, 'T': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14,
}
RANK_LABEL: dict[int, str] = {v: k for k, v in RANK_MAP.items()}

# ── Card parsing ──────────────────────────────────────────────────────────────

def parse_board(board_str: str) -> list[tuple[int, str]]:
    """
    Parse comma-separated ASCII board string.
    "Kc,7d,2s" → [(13,'c'), (7,'d'), (2,'s')]
    Also accepts 4/5-card boards for turn/river.
    """
    cards: list[tuple[int, str]] = []
    for token in board_str.replace(' ', '').split(','):
        token = token.strip()
        if len(token) >= 2:
            rank_ch = token[0].upper()
            suit_ch = token[1].lower()
            if rank_ch in RANK_MAP and suit_ch in 'shdcSHDC':
                cards.append((RANK_MAP[rank_ch], suit_ch.lower()))
    return cards


def parse_hand_abstract(hand_str: str) -> tuple[int, int, bool, bool]:
    """
    Parse abstract hand: "AKo" → (14, 13, False, False).
    Returns (h, l, is_pair, is_suited).  h >= l always.
    """
    s = hand_str.strip()
    if len(s) >= 2 and s[0].upper() == s[1].upper() and s[0].upper() in RANK_MAP:
        r = RANK_MAP[s[0].upper()]
        return r, r, True, False
    if len(s) >= 2 and s[0].upper() in RANK_MAP and s[1].upper() in RANK_MAP:
        h, l = RANK_MAP[s[0].upper()], RANK_MAP[s[1].upper()]
        if h < l:
            h, l = l, h
        suited = len(s) >= 3 and s[2].lower() == 's'
        return h, l, False, suited
    raise ValueError(f"Cannot parse hand: {hand_str!r}")


def parse_hand_specific(hand_str: str) -> tuple[tuple[int, str], tuple[int, str]]:
    """
    Parse specific hand: "Ac,Kd" → ((14,'c'), (13,'d')).
    """
    cards = parse_board(hand_str)
    if len(cards) < 2:
        raise ValueError(f"Cannot parse hand: {hand_str!r}")
    return cards[0], cards[1]


# ── Preflop formulas ──────────────────────────────────────────────────────────
#
# RFI Score = H + L [+ 10 if pair] [+ 6 if suited] [+ connector/gap bonus]
# T_open: UTG=24 / HJ=22 / CO=21 / BTN=18 / SB=22
#   (SB は OOP 補正のため BTN より tight; GTO 24% raise-only ≒ HJ T=22)
# T_3bet: BTN vs UTG=32/28, CO/HJ vs UTG=28, SB vs BTN=24
# T_4bet=33, T_5bet=39
# BB: Score_BB = Score + suited(+6) + diff1(+4) + diff2-3(+2), T_BB=20

RFI_THRESHOLDS: dict[str, int] = {
    "UTG": 24, "HJ": 22, "MP": 22, "CO": 21, "BTN": 18, "SB": 22,
}

def calc_rfi_score(h: int, l: int, is_pair: bool, is_suited: bool) -> float:
    """
    RFI score: H + L [+10 pair] [+3 suited] [+connector] [-gap_pen] [-low_pen].
    Pair short-circuits: score = h + l + 10 (no other bonuses/penalties).
    """
    if is_pair:
        return float(h + l + 10)
    score: float = h + l
    score += 3 if is_suited else 0
    gap = h - l
    if gap == 1:
        score += 1
    elif gap <= 3:
        score += 0.5
    if gap >= 5:
        score -= 1
    if h < 9 and l < 9:
        score -= 1
    return score


def calc_score_bb(h: int, l: int, is_pair: bool, is_suited: bool) -> float:
    """
    BB defence score: Score_BB = rfi_score + suited(+6) + diff_bonus - overlap_penalty.
    diff1: +4, diff2-3: +2.  T_BB = 20.
    """
    base = calc_rfi_score(h, l, is_pair, is_suited)
    if is_pair:
        return base
    bonus: float = 0
    if is_suited:
        bonus += 6
    gap = h - l
    if gap == 1:
        bonus += 4
    elif gap <= 3:
        bonus += 2
    return base + bonus


def rfi_decision(score: float, position: str) -> Literal["OPEN", "FOLD"]:
    t = RFI_THRESHOLDS.get(position, 22)
    return "OPEN" if score >= t else "FOLD"


# ── Board Score (B) ───────────────────────────────────────────────────────────
#
# B (0–100): 9-rule hierarchy (257-board GTO dataset).
# Rule 1: Mono      → 70
# Rule 2: Pair×top≥T → 83
# Rule 3: Pair×top<T → 71
# Rule 4: 2tone×A/K  → 56
# Rule 5: 2tone      → 50
# Rule 6: Rainbow×spread≤3×top≥J → 67
# Rule 7: Rainbow×top A/K → 62
# Rule 8: Rainbow×top Q  → 58
# Rule 9: Rainbow        → 55

def calc_board_score(board_str: str) -> tuple[int, str]:
    """
    Board Score B (0-100). Returns (score, texture_label).
    Input: "Kc,7d,2s"  (3-5 cards)
    """
    cards = parse_board(board_str)
    if not cards:
        return 55, "rainbow"
    ranks = [r for r, _ in cards]
    suits = [s for _, s in cards]

    if len(set(suits)) == 1:
        return 70, "mono"

    rank_counts = Counter(ranks)
    pair_ranks = [r for r, cnt in rank_counts.items() if cnt >= 2]
    if pair_ranks:
        top_pair_rank = max(pair_ranks)
        if top_pair_rank >= 10:
            return 83, "paired_high"
        return 71, "paired_low"

    n_suits = len(set(suits))
    two_tone = (n_suits == 2)
    top_rank = max(ranks)
    spread = max(ranks) - min(ranks)

    if two_tone:
        if top_rank >= 13:
            return 56, "2tone_ak"
        return 50, "2tone"

    # Rainbow
    if spread <= 3 and top_rank >= 11:
        return 67, "rainbow_connected"
    if top_rank >= 13:
        return 62, "rainbow_ak"
    if top_rank == 12:
        return 58, "rainbow_q"
    return 55, "rainbow"


# ── Hand Score (HS) on flop ───────────────────────────────────────────────────
#
# HS = role_score + draw_bonus + 2OC_bonus
#
# Role scores (new scale, equity %):
#   set_plus=85, overpair_high=80, overpair_mid=75, overpair_low=70,
#   two_pair=72, tptk=65, tpgk=60, tpmk=55, tpwk=50,
#   second_pair_strong=42, second_pair_weak=38, bottom_pair=30,
#   underpair_high=65, underpair_mid=60, underpair_low=40,
#   A-high=25, K-high=20, Q-high=15, other_air=10
#
# Draw bonus (flop): outs × 4
#   NFD=9outs → +36, FD(plain)=9outs → +32, OESD=8outs → +28, GS=4outs → +12
#   BDFD=+6, combo(FD+OESD)=15outs → +52
#
# 2OC bonus (flop): both hole cards > max(board) → +24
#   Applied AFTER role, only for air hands
#
# NOTE: calc_hand_score requires specific suits for draw detection.
#   For abstract ("AKs") on a board, partial detection is done.

_ROLE_SCORE: dict[str, int] = {
    "set_plus": 85,
    "overpair_high": 80, "overpair_mid": 75, "overpair_low": 70,
    "two_pair": 72,
    "tptk": 65, "tpgk": 60, "tpmk": 55, "tpwk": 50,
    "second_pair_strong": 42, "second_pair_weak": 38,
    "bottom_pair": 30,
    "underpair_high": 65, "underpair_mid": 60, "underpair_low": 40,
}

_MADE_QUADS    = 97
_MADE_NUT_FLUSH = 88
_MADE_FLUSH    = 84
_MADE_BROADWAY = 82
_MADE_STRAIGHT = 80


def calc_hand_score(hand_str: str, board_str: str) -> int:
    """
    Hand Score HS (0-100) on flop/turn.
    hand_str: abstract "AKs"/"77" or specific "Ac,Kd"
    board_str: "Kc,7d,2s" or "Kc,7d,2s,Ah" (turn)

    Returns integer HS.  Use calc_flop_tier(hs) to classify T1/T2/T3.
    """
    board_cards = parse_board(board_str)
    board_ranks = [r for r, _ in board_cards]
    board_suits = [s for _, s in board_cards]
    rank_counter = Counter(board_ranks)
    n_board = len(board_cards)
    street = "flop" if n_board == 3 else ("turn" if n_board == 4 else "river")

    # Parse hand
    is_specific = (',' in hand_str or (len(hand_str) >= 4 and hand_str[1].lower() in 'shdc'))
    if is_specific:
        c1, c2 = parse_hand_specific(hand_str)
        h_rank, h_suit = c1
        l_rank, l_suit = c2
        if h_rank < l_rank:
            h_rank, h_suit, l_rank, l_suit = l_rank, l_suit, h_rank, h_suit
        is_pair_hand = (h_rank == l_rank)
        is_suited_hand = (h_suit == l_suit)
        hand_suits: list[str] | None = [h_suit, l_suit]
    else:
        h_rank, l_rank, is_pair_hand, is_suited_hand = parse_hand_abstract(hand_str)
        if h_rank < l_rank:
            h_rank, l_rank = l_rank, h_rank
        h_suit = l_suit = ''
        hand_suits = None

    # ── Check made hands first (non-pair hands only for flush/straight) ────────
    # Quads
    if rank_counter.get(h_rank, 0) + (1 if is_pair_hand else 0) >= 4:
        return _MADE_QUADS
    if rank_counter.get(l_rank, 0) >= 3:
        return _MADE_QUADS

    # Full house / flush / straight: approximate (detail omitted for brevity)
    # Straight check
    all_ranks = sorted({h_rank, l_rank} | set(board_ranks))
    for combo in combinations(all_ranks, 5):
        if combo[4] - combo[0] == 4 and len(set(combo)) == 5:
            if h_rank in combo or l_rank in combo:
                made = _MADE_BROADWAY if combo[4] == 14 and combo[0] == 10 else _MADE_STRAIGHT
                return made

    # Flush (specific only)
    if hand_suits:
        for suit in set(hand_suits):
            total = hand_suits.count(suit) + board_suits.count(suit)
            if total >= 5:
                has_ace = (h_rank == 14 and h_suit == suit) or (l_rank == 14 and l_suit == suit)
                return _MADE_NUT_FLUSH if has_ace else _MADE_FLUSH

    # ── Role classification ────────────────────────────────────────────────────
    role = _classify_role(h_rank, l_rank, is_pair_hand, rank_counter, board_ranks)

    if role in _ROLE_SCORE:
        score = _ROLE_SCORE[role]
    elif role == "air":
        # Hi-card scores
        top = max(h_rank, l_rank)
        if top == 14:
            score = 25
        elif top == 13:
            score = 20
        elif top == 12:
            score = 15
        else:
            score = 10
    else:
        score = 30

    # ── Draw bonus ─────────────────────────────────────────────────────────────
    if street == "river":
        draw_mult = 0
    elif street == "turn":
        draw_mult = 2
    else:
        draw_mult = 4

    draw_bonus = 0
    if draw_mult > 0:
        has_fd, has_bdfd, is_nut_fd = _detect_fd(h_rank, l_rank, h_suit, l_suit, board_suits, hand_suits, is_suited_hand)
        has_oesd, has_gutshot = _detect_straights(h_rank, l_rank, board_ranks)

        if has_fd and has_oesd:
            draw_bonus = 15 * draw_mult  # combo draw: 15 outs
        elif has_fd:
            outs = 9
            draw_bonus = outs * draw_mult + (4 if is_nut_fd else 0)
        elif has_oesd:
            draw_bonus = 8 * draw_mult
        elif has_gutshot:
            draw_bonus = 4 * draw_mult
        elif has_bdfd and street == "flop":
            draw_bonus = 6  # flat bonus (flop only — BDFD has no value at turn)

    # ── 2OC bonus (flop, air hands only) ─────────────────────────────────────
    oc2_bonus = 0
    if street == "flop" and role == "air" and not is_pair_hand:
        max_board = max(board_ranks) if board_ranks else 0
        if h_rank > max_board and l_rank > max_board:
            oc2_bonus = 24

    return min(100, score + draw_bonus + oc2_bonus)


def _classify_role(h_rank: int, l_rank: int, is_pair: bool,
                   rank_counter: Counter, board_ranks: list[int]) -> str:
    """Classify hand role vs board."""
    if not board_ranks:
        return "air"
    top_board = max(board_ranks)

    if is_pair:
        if h_rank in rank_counter:
            return "set_plus"
        if h_rank > top_board:
            if h_rank >= 12:
                return "overpair_high"
            if h_rank >= 10:
                return "overpair_mid"
            return "overpair_low"
        # Underpair
        if h_rank >= 12:
            return "underpair_high"
        if h_rank >= 10:
            return "underpair_mid"
        return "underpair_low"

    h_on = h_rank in rank_counter
    l_on = l_rank in rank_counter

    if h_on and l_on:
        return "two_pair"

    if h_on:
        return _top_pair_role(h_rank, l_rank, board_ranks)
    if l_on:
        return _top_pair_role(l_rank, h_rank, board_ranks)

    return "air"


def _top_pair_role(pair_rank: int, kicker: int, board_ranks: list[int]) -> str:
    sorted_board = sorted(board_ranks, reverse=True)
    if pair_rank == sorted_board[0]:
        if kicker >= 13:
            return "tptk"
        if kicker >= 12:
            return "tpgk"
        if kicker >= 8:
            return "tpmk"
        return "tpwk"
    if len(sorted_board) > 1 and pair_rank == sorted_board[1]:
        return "second_pair_strong" if kicker >= 12 else "second_pair_weak"
    return "bottom_pair"


def _detect_fd(h_rank: int, l_rank: int, h_suit: str, l_suit: str,
               board_suits: list[str], hand_suits: list[str] | None,
               is_suited_hand: bool) -> tuple[bool, bool, bool]:
    """Returns (has_fd, has_bdfd, is_nut_fd)."""
    if hand_suits:
        for suit in {h_suit, l_suit}:
            if not suit:
                continue
            total = hand_suits.count(suit) + board_suits.count(suit)
            if total >= 4:
                is_nut = (h_rank == 14 and h_suit == suit) or (l_rank == 14 and l_suit == suit)
                return True, False, is_nut
            if total >= 3:
                return False, True, False
    elif is_suited_hand:
        suit_counts = Counter(board_suits)
        max_board = max(suit_counts.values(), default=0)
        if max_board >= 2:
            return True, False, h_rank == 14
        if max_board >= 1:
            return False, True, False
    return False, False, False


def _detect_straights(h_rank: int, l_rank: int,
                      board_ranks: list[int]) -> tuple[bool, bool]:
    """Returns (has_oesd, has_gutshot)."""
    hole_set = frozenset([h_rank, l_rank])
    unique_r = sorted({h_rank, l_rank} | set(board_ranks))
    has_oesd = False
    has_gutshot = False
    for combo in combinations(unique_r, 4):
        if not (frozenset(combo) & hole_set):
            continue
        span = combo[3] - combo[0]
        gaps = [combo[i + 1] - combo[i] for i in range(3)]
        if span == 3 and max(gaps) == 1:
            if combo[3] == 14 or combo[0] == 2:
                has_gutshot = True
            else:
                has_oesd = True
        elif span == 4 and sorted(gaps) == [1, 1, 2]:
            has_gutshot = True
    return has_oesd, has_gutshot


# ── Flop tier / CBet decision ─────────────────────────────────────────────────
#
# T1 ≥ 65: always CBet (strong made hands)
# T2 ≥ 20: CBet if B ≥ 58 (includes 2OC hands)
# T3 < 20: CBet if B ≥ 67 (dry boards only, air/weak hands)
#
# CBet size (GTO 168board):
#   paired_high / mono → 50%
#   others             → 75%

def calc_flop_tier(hand_score: int) -> Literal["T1", "T2", "T3"]:
    """T1≥65 / T2≥20 / T3<20. T2 lower bound = 20 to include 2OC (+24 bonus)."""
    if hand_score >= 65:
        return "T1"
    if hand_score >= 20:
        return "T2"
    return "T3"


def calc_flop_cbet_decision(hand_score: int, board_score: int) -> bool:
    """IP CBet decision: T1→always, T2→B≥58, T3→B≥62.
    T3 threshold updated from 67 to 62: pot10 data shows K/A-high rainbow (B=62)
    has fold_vs33=29-46% > α=25% → T3 bluff is +EV on these boards.
    """
    if hand_score >= 65:
        return True
    if hand_score >= 20:
        return board_score >= 58
    return board_score >= 62


def calc_cbet_size(texture_label: str) -> int:
    """
    CBet size (% of pot).
    GTO (pot=10 44 scenarios): 33% used 78% of the time on dry rainbow boards.
    mono               → 75%  (charge draws)
    2tone / connected  → 50%  (semi-wet)
    paired_high        → 50%  (medium size)
    dry rainbow        → 33%  (range bet: GTO default)
    """
    if texture_label == "mono":
        return 75
    if "2tone" in texture_label or "paired" in texture_label or "connected" in texture_label:
        return 50
    return 33  # dry rainbow (rainbow / rainbow_ak / rainbow_q): GTO equilibrium


# ── Fold threshold (OOP defence) ─────────────────────────────────────────────
#
# Base: vs33%→15, vs50%→25, vs75%→35
# Correction: 2tone+5, mono-5, paired-10
# → Fold if HS < threshold

def calc_fold_threshold(bet_size_pct: int, texture_label: str) -> int:
    """
    OOP fold threshold: fold if HS < returned value.
    Base: vs33%→15, vs50%→25, vs75%→35.
    Board correction: 2tone+5, mono-5, paired-10.
    """
    base: dict[int, int] = {33: 15, 50: 25, 75: 35}
    threshold = base.get(bet_size_pct, 25)
    if "2tone" in texture_label:
        threshold += 5
    elif texture_label == "mono":
        threshold -= 5
    elif "paired" in texture_label:
        threshold -= 10
    return max(threshold, 0)


def calc_fold_decision(hand_score: int, bet_size_pct: int,
                       texture_label: str) -> Literal["CALL", "FOLD"]:
    """Fold if HS < threshold."""
    return "FOLD" if hand_score < calc_fold_threshold(bet_size_pct, texture_label) else "CALL"


# ── Turn barrel ───────────────────────────────────────────────────────────────
#
# GTO 233board: T1/T2 → always barrel (78%+ bet rate), size=33%
# T3 → bet only B≥67
# Turn tier threshold same as flop (T1≥65, T2≥20)

def calc_turn_cbet_decision(hand_score: int, board_score: int) -> tuple[bool, int]:
    """
    Turn barrel: Returns (should_bet, size_pct).
    T1/T2 → always, size=33%.  T3 → B≥67, size=33%.
    """
    size = 33
    tier = calc_flop_tier(hand_score)  # same thresholds
    if tier in ("T1", "T2"):
        return True, size
    return board_score >= 67, size


# ── River ─────────────────────────────────────────────────────────────────────
#
# VMB bucket: V≥70 / M≥35 / B<35
# River CBet (GTO 162board): T1 always, T2 IP only, T3 check
# River size: B≥83(paired_high) → 100%, others → 50%

def calc_river_vmb_bucket(hand_score: int) -> Literal["V", "M", "B"]:
    """River VMB: V≥70 / M≥35 / B<35."""
    if hand_score >= 70:
        return "V"
    if hand_score >= 35:
        return "M"
    return "B"


def calc_river_cbet_decision(hand_score: int, board_score: int,
                              position: str) -> tuple[bool, int]:
    """
    River bet decision. Returns (should_bet, size_pct).
    T1→always, T2→IP only, T3→check.
    Size: paired_high(B≥83)→100%, others→50%.
    """
    tier = calc_river_vmb_bucket(hand_score)  # V=T1, M=T2, B=T3
    size = 100 if board_score >= 83 else 50
    if tier == "V":
        return True, size
    if tier == "M":
        return position == "IP", size
    return False, size


# ── River / Turn runout tag ────────────────────────────────────────────────────
#
# 新カードがボード構造に与える影響を5タグで分類する (Vol4/Vol5 共通)。
#
# Tags (優先順: PB > SC > FC > OC > blank):
#   PB    : 既存カードとランクが重なる（ボードペア）
#   SC    : 新カードでストレート成立の可能性が初めて生まれる
#   FC    : 新カードで同スーツが4枚以上 → 1枚持ちでフラッシュ成立
#   OC    : 既存カード全てより高いランク（オーバーカード）
#   blank : 上記なし（構造変化なし）
#
# IP リバーベット閾値 (by river_tag) — GTO 12ボード実測:
#   blank: HS ≥ 55  (M+: TPTK 62-99% → bet)
#   OC   : HS ≥ 60  (M+: TPTK 42% → borderline)
#   SC   : HS ≥ 70  (V only: TPTK 0% → check)
#   FC   : HS ≥ 70  (V only)
#   PB   : HS ≥ 80  (強V only: TPTK 0%, set/trips bet)
#
# OOP lead (ドンク) 条件: SC or FC + HS ≥ 70
#   SC donk rate: 46-53%, FC donk rate: 28% (GTO)

def _count_straight_windows(board_ranks: list[int], max_hole: int = 2) -> int:
    """
    ボードランク集合から、max_hole 枚以下のホールカードで完成できる
    ストレートウィンドウの数を返す。
    max_hole=2: 通常の判定（2枚ホールカードで完成）
    max_hole=1: 1枚で完成する「イージーストレート」のみ
    """
    expanded = set(board_ranks)
    if 14 in expanded:
        expanded.add(1)   # A-low ホイール対応 (A がボードにある場合のみ)
    count = 0
    for low in range(1, 11):
        window = {low, low + 1, low + 2, low + 3, low + 4}
        missing = len(window - expanded)
        if missing <= max_hole:
            count += 1
    return count


def _new_sc_card(prior_ranks: list[int], new_rank: int) -> bool:
    """
    new_rank を追加することで「1枚ホールカードで完成するストレート窓」が
    新たに生まれるか（SC カード判定）。
    JT59→Q: True（8-9-T-J-Q、9-T-J-Q-K 窓が新生）
    JT59→2: False（新しいイージー窓なし）
    """
    before = _count_straight_windows(prior_ranks, max_hole=1)
    after  = _count_straight_windows(prior_ranks + [new_rank], max_hole=1)
    return after > before


def _tag_new_card(
    prior_ranks: list[int], prior_suits: list[str],
    new_rank: int, new_suit: str,
) -> Literal["blank", "OC", "SC", "FC", "PB"]:
    """
    新カードをタグ付けするコア実装。優先: PB > SC > FC > OC > blank。
    SC: 1枚ホールカードで完成するイージーストレート窓が新生
    FC: prior に3枚同スーツ + new で4枚（1枚持ちでフラッシュ成立）
    OC: new が prior の最高ランクを超える
    """
    if new_rank in prior_ranks:
        return "PB"
    if _new_sc_card(prior_ranks, new_rank):
        return "SC"
    suit_ctr = Counter(prior_suits)
    if suit_ctr.get(new_suit, 0) >= 3:   # prior に3枚 + new で4枚同スーツ
        return "FC"
    if prior_ranks and new_rank > max(prior_ranks):
        return "OC"
    return "blank"


def classify_turn_card(
    flop_board_str: str, turn_card_str: str
) -> Literal["blank", "OC", "SC", "FC", "PB"]:
    """
    ターンカードのフロップへの影響を分類。
    flop_board_str: "Jc,Td,5s"  (3枚)
    turn_card_str:  "9d"
    """
    flop = parse_board(flop_board_str)
    turn = parse_board(turn_card_str)
    if not flop or not turn:
        return "blank"
    t_rank, t_suit = turn[0]
    return _tag_new_card([r for r, _ in flop], [s for _, s in flop], t_rank, t_suit)


def classify_river_runout(
    turn_board_str: str, river_card_str: str
) -> Literal["blank", "OC", "SC", "FC", "PB"]:
    """
    リバーカードのターンボードへの影響を分類。
    turn_board_str: "Jc,Td,5s,9d"  (4枚)
    river_card_str: "Qh"
    """
    turn = parse_board(turn_board_str)
    river = parse_board(river_card_str)
    if not turn or not river:
        return "blank"
    r_rank, r_suit = river[0]
    return _tag_new_card([r for r, _ in turn], [s for _, s in turn], r_rank, r_suit)


# ── River M+/M- bucket (4分類) ─────────────────────────────────────────────────
#
# 旧 VMB 3分類を M+/M- に細分化。
#
# V   ≥70 : バリュー (セット/ストレート/フラッシュ/ツーペア+/オーバーペア)
# M+  55-69: 薄いバリュー候補 (TPTK=65, TPGK=60, TPMK=55)
# M-  35-54: ショーダウンバリュー (TPWK=50, セカンドペア=38-42)
# B   <35  : エア (ボトムペア=30, Aハイ=25, ...)
#
# M+ は「ブランクボードではバリュー、完成ランアウトではSDV」に振る舞う。
# M- はほぼ常にチェック（ブラフキャッチャーとして機能）。

def calc_river_bucket(hand_score: int) -> Literal["V", "M+", "M-", "B"]:
    """
    リバー4分類バケット。
    V≥70 / M+(55-69) / M-(35-54) / B<35
    """
    if hand_score >= 70:
        return "V"
    if hand_score >= 55:
        return "M+"
    if hand_score >= 35:
        return "M-"
    return "B"


_RIVER_IP_BET_THRESHOLD: dict[str, int] = {
    "blank": 55,   # M+ bets: TPMK(55)/TPGK(60)/TPTK(65) → 62-99%
    "OC":    60,   # M+ cautious: TPTK=42%、TPMK → check
    "SC":    70,   # V only: TPTK=0% → check
    "FC":    70,   # V only
    "PB":    80,   # 強V only: TPTK=0%, トリップス(85)/FH+ → bet
}


def calc_river_ip_bet(hand_score: int, river_tag: str) -> bool:
    """
    IP リバーベット判断。True = bet。
    river_tag: "blank" | "OC" | "SC" | "FC" | "PB"
    """
    return hand_score >= _RIVER_IP_BET_THRESHOLD.get(river_tag, 55)


def classify_river_board(river_board_str: str) -> Literal["PB", "SC", "FC", "blank"]:
    """
    5枚リバーボード全体の構造タイプ分類。OOP リード判断に使用。
    （classify_river_runout はリバーカードの寄与を見る; こちらは全体構造を見る）

    PB : ボードにペアあり → FH/トリップス可能性
    FC : 4枚以上同スーツ → 1枚ホールカードでフラッシュ成立
    SC : ≥3 ストレート窓 (2枚以下ホールカードで完成) → OOP ストレートが豊富
    blank: 上記なし
    """
    cards = parse_board(river_board_str)
    if not cards:
        return "blank"
    ranks = [r for r, _ in cards]
    suits = [s for _, s in cards]

    if max(Counter(ranks).values()) >= 2:
        return "PB"
    if max(Counter(suits).values()) >= 4:
        return "FC"
    if _count_straight_windows(ranks, max_hole=2) >= 3:
        return "SC"
    return "blank"


def calc_river_oop_lead(hand_score: int, river_board_type: str) -> bool:
    """
    OOP リバーリード（ドンク）条件。
    SC or FC ボードタイプ + V バケット(HS≥70) → lead。
    GTO: SC=46-53%, FC=28%。
    river_board_type: classify_river_board() の戻り値を使用。
    """
    return hand_score >= 70 and river_board_type in ("SC", "FC")


def calc_river_action_v2(
    hand_score: int,
    turn_board_str: str,
    river_card_str: str,
    position: str,
    board_score: int,
) -> dict:
    """
    リバーアクション統合判断 (v2: runout_tag + board_type 対応)。

    IP bet: classify_river_runout() タグ使用（リバーカードの寄与で閾値決定）
    OOP lead: classify_river_board() タイプ使用（ボード全体構造で OOP ドンク決定）

    Returns: {action, size_pct, bucket, river_tag, board_type}
    action: "BET" | "LEAD" | "CHECK"
    """
    river_tag = classify_river_runout(turn_board_str, river_card_str)
    full_board = turn_board_str + "," + river_card_str.split(",")[0]
    board_type = classify_river_board(full_board)
    bucket = calc_river_bucket(hand_score)
    size = 100 if board_score >= 83 else 50

    if position == "IP":
        bet = calc_river_ip_bet(hand_score, river_tag)
        return {"action": "BET" if bet else "CHECK",
                "size_pct": size if bet else 0,
                "bucket": bucket, "river_tag": river_tag, "board_type": board_type}
    else:
        lead = calc_river_oop_lead(hand_score, board_type)
        return {"action": "LEAD" if lead else "CHECK",
                "size_pct": size if lead else 0,
                "bucket": bucket, "river_tag": river_tag, "board_type": board_type}


# ── Turn barrel v2 (turn_tag 対応) ────────────────────────────────────────────
#
# GTO 233ボード実測:
#   全体 IP barrel: 85.6%
#   ペアターン barrel: 96.1% → IP ほぼ全ハンドでバレル
#   SC/FC ターン: V のみバレル（M は保護のためチェック）
#
# ターンバレル閾値 by turn_tag:
#   blank / OC: T1/T2 → always barrel; T3 → B ≥ 62
#   PB        : HS ≥ 20 (T2+T1 全てバレル — ペアターンは IP レンジ優位)
#   SC / FC   : HS ≥ 65 (T1 のみ — 完成系は V に任せる)
#
# OOP ターンフォールド閾値補正 by turn_tag:
#   PB  : base - 10 (IP ブラフ増加 → OOP はより守りやすい)
#   SC/FC: base + 5 (IP バリュー増加 → OOP は降りやすい)

def calc_turn_barrel_v2(
    hand_score: int, board_score: int, turn_tag: str
) -> tuple[bool, int]:
    """
    ターンバレル判断 v2 (turn_tag 対応)。Returns (should_bet, size_pct).
    """
    size = 33
    if turn_tag == "PB":
        return hand_score >= 20, size
    if turn_tag in ("SC", "FC"):
        return hand_score >= 65, size
    # blank / OC: 標準ロジック
    tier = calc_flop_tier(hand_score)
    if tier in ("T1", "T2"):
        return True, size
    return board_score >= 62, size


def calc_turn_oop_fold_threshold_v2(bet_size_pct: int, turn_tag: str) -> int:
    """
    OOP ターンフォールド閾値 (turn_tag 補正付き)。
    Base: vs33%=20, vs50%=30, vs75%=40。
    PB: -10、SC/FC: +5。
    """
    base: dict[int, int] = {33: 20, 50: 30, 75: 40}
    threshold = base.get(bet_size_pct, 20)
    if turn_tag == "PB":
        threshold -= 10
    elif turn_tag in ("SC", "FC"):
        threshold += 5
    return max(threshold, 0)


# ── Utility ───────────────────────────────────────────────────────────────────

def calc_spr(stack_bb: float, pot_bb: float) -> float:
    """Stack-to-Pot Ratio = effective_stack / pot."""
    return stack_bb / pot_bb if pot_bb > 0 else float('inf')


def calc_alpha(bet_bb: float, pot_before_bet_bb: float) -> float:
    """α = bet / (pot_before_bet + bet). Required equity to break even."""
    total = pot_before_bet_bb + bet_bb
    return bet_bb / total if total > 0 else 0.0


def calc_min_defense_freq(alpha: float) -> float:
    """MDF = 1 - α. Minimum fraction of range OOP must defend."""
    return 1.0 - alpha


def calc_vb_ratio(alpha: float) -> tuple[int, int]:
    """
    Optimal V:B ratio at river equilibrium.
    α=25%→V:B=3:1, 33%→2:1, 43%→4:3, 50%→1:1, 60%→3:2.
    """
    table: dict[int, tuple[int, int]] = {
        25: (3, 1), 33: (2, 1), 43: (4, 3), 50: (1, 1), 60: (3, 2),
    }
    alpha_pct = round(alpha * 100)
    best = min(table, key=lambda k: abs(k - alpha_pct))
    return table[best]


# ── C-coefficient (board aggression factor) ───────────────────────────────────
#
# C = (1 - MDF) × 50  where MDF = 1 - α
# Or simply: C = α × 50
# C values for common bet sizes:
#   33% bet → α = 0.25 → C = 12
#   50% bet → α = 0.33 → C = 17
#   75% bet → α = 0.43 → C = 22
#  100% bet → α = 0.50 → C = 25
#  150% bet → α = 0.60 → C = 30

def calc_c_coeff(bet_size_pct: int) -> float:
    """
    C coefficient = α × 50.
    bet_size_pct: 33 / 50 / 75 / 100 / 150
    """
    alpha = bet_size_pct / (100 + bet_size_pct)
    return alpha * 50


# ── Board texture helpers (used by generators) ────────────────────────────────

def board_has_flush_draw(board_str: str) -> bool:
    """True if 2+ cards of same suit on board (flush draw possible)."""
    cards = parse_board(board_str)
    suits = [s for _, s in cards]
    return max(Counter(suits).values(), default=0) >= 2


def board_is_paired(board_str: str) -> bool:
    """True if board has a pair."""
    cards = parse_board(board_str)
    ranks = [r for r, _ in cards]
    return max(Counter(ranks).values(), default=0) >= 2


def board_connectivity(board_str: str) -> Literal["connected", "semi", "dry"]:
    """
    Rough connectivity label.
    connected: spread ≤ 4
    semi: spread 5-6
    dry: spread ≥ 7
    """
    cards = parse_board(board_str)
    if len(cards) < 2:
        return "dry"
    ranks = [r for r, _ in cards]
    spread = max(ranks) - min(ranks)
    if spread <= 4:
        return "connected"
    if spread <= 6:
        return "semi"
    return "dry"


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # ── Flop / Turn 基本テスト ─────────────────────────────────────────────────
    tests = [
        ("AKs", "Kc,7d,2s"),   # TPTK on K72r
        ("77",  "Kc,7d,2s"),   # Set on K72r
        ("AQo", "Kc,7d,2s"),   # 2OC on K72r (should get +24)
        ("T9s", "Kc,7d,2s"),   # Air + OESD (gutshot only here)
        ("JTs", "Kc,7d,2s"),   # Air
        ("AKs", "Jc,Td,5s"),   # OC ace on JT5r
        ("AQo", "9s,8d,7c"),   # 2OC on 987r
    ]
    print("Hand        Board        HS   Tier  CBet?  BS   Texture")
    print("-" * 70)
    for hand, board in tests:
        bs, tex = calc_board_score(board)
        hs = calc_hand_score(hand, board)
        tier = calc_flop_tier(hs)
        cbet = calc_flop_cbet_decision(hs, bs)
        print(f"{hand:10s}  {board:14s}  {hs:3d}  {tier}   {'Y' if cbet else 'N'}     {bs:3d}  {tex}")

    # ── River runout tag テスト ────────────────────────────────────────────────
    print("\n--- River runout tag ---")
    runout_cases = [
        ("Jc,Td,5s,9d", "Qh",  "SC expected"),   # Q completes J-T-Q (needs Q,9,8... actually Q-J-T-9 needs 8 or K? Let's check)
        ("Kc,7d,2s,Ah", "2h",  "PB expected"),   # 2 pairs the board
        ("Jc,Td,5s,9d", "8h",  "SC expected"),   # 8 completes 8-9-T-J straight
        ("Ks,7s,5s,3s", "8h",  "OC expected"),   # 8 > 3,5,7... wait 8<K, so not OC. blank?
        ("Kc,7d,2s,Ah", "Jd",  "OC expected"),   # J < A, not OC. blank? A is max, J < A. Hmm
        ("Kc,7s,5s,3s", "9s",  "FC expected"),   # 3 spades on turn + 9s = 4 spades
        ("Kc,7d,2s,4h", "9c",  "OC expected"),   # 9 > 4 (but not > K, so blank!)
        ("Kc,7d,2s,4h", "Ah",  "OC expected"),   # A > K = OC
    ]
    for turn_b, river_c, note in runout_cases:
        tag = classify_river_runout(turn_b, river_c)
        print(f"  {turn_b} | {river_c} → {tag:6s}  ({note})")

    # ── River action v2 テスト ─────────────────────────────────────────────────
    print("\n--- River action v2 (IP) ---")
    river_action_cases = [
        # (hand, turn_board, river_card, expected_tag)
        ("AKs", "Kc,7d,2s,Ah", "Jd",  "blank: TPTK bet"),
        ("AKs", "Jc,Td,5s,9d", "8h",  "SC: TPTK check"),
        ("AKs", "Kc,7d,2s,Ah", "2h",  "PB: TPTK check"),
        ("77",  "Kc,7d,2s,Ah", "2h",  "PB: Set → if HS≥80, bet"),
        ("77",  "Jc,Td,5s,9d", "8h",  "SC: Set bet"),
    ]
    for hand, turn_b, river_c, note in river_action_cases:
        bs, _ = calc_board_score(turn_b + "," + river_c)
        hs = calc_hand_score(hand, turn_b + "," + river_c)
        result = calc_river_action_v2(hs, turn_b, river_c, "IP", bs)
        bucket = calc_river_bucket(hs)
        print(f"  {hand} | {river_c} on {turn_b[-4:]} | HS={hs:3d} {bucket:3s} | tag={result['river_tag']:6s} → {result['action']}  ({note})")

    # ── Turn barrel v2 テスト ──────────────────────────────────────────────────
    print("\n--- Turn barrel v2 ---")
    turn_cases = [
        ("Jc,Td,5s", "9d", "AKs",  "SC turn: only T1 barrels"),
        ("Kc,7d,2s", "7h", "AKs",  "PB turn: T2+ barrels (TPTK HS≥20)"),
        ("Kc,7d,2s", "Ah", "JTs",  "OC turn: standard T1/T2"),
    ]
    for flop, turn_c, hand, note in turn_cases:
        turn_board = flop + "," + turn_c
        hs = calc_hand_score(hand, turn_board)
        bs, _ = calc_board_score(turn_board)
        tag = classify_turn_card(flop, turn_c)
        bet, sz = calc_turn_barrel_v2(hs, bs, tag)
        print(f"  {hand} | turn={turn_c} ({tag:6s}) | HS={hs:3d} → {'BET' if bet else 'CHK'} {sz}%  ({note})")
