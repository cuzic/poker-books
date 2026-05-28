#!/usr/bin/env python3
"""
UCBS-v2 — 式駆動の統一 CBet 頻度予測モデル

書籍コンセプト「式で精度と覚えやすさを両立」を体現:

  CBS = HP[hand] + DP[draw]
  conf = bucket(|CBS - T|, board_type)        # HIGH/MID/LOW
  dir = (CBS >= T)
  size = polarize_board(board) ? 116 : 33

  freq = base_freq[(conf, dir, size)]         ← 12 セル (cash 100bb data-driven)
       + α_ctx                                ← context uniform lift
       + β_ctx · I(CBS >= 7)                  ← strong/nut 帯 lift
       + offset_ctx[category]                 ← 役柄カテゴリ補正

  前段例外 (信頼度シフト):
    O4. 型6 ボード (mid 連結ウェット) では信頼度を 1 段上げる
        → 「mid-wet 板はレンジ全体が活きるので bet 候補が広がる」
    O5. mono ボード (3 同 suit) では信頼度を 1 段下げる (cash のみ)
        → 「mono 板はレンジが狭く絡むので bet 控えめ」

  後段補正:
    O7. position lift (cash/mtt 別):
          SB (OOP opener)  : cash -8, mtt -10
          BTN (IP opener)  : 0 (基準)
          CO/HJ/UTG (wide): cash +10, mtt +13
    O8. A-high paired/dry on mtt BTN/CO open → +30 (range bet 100% パターン)

  hand category:
    slowplay : set, trips, two_pair, fullhouse, flush, straight, quads
    trash    : low_pair
    premium  : overpair, underpair
    default  : それ以外 (offset = 0)

達成精度 (O4/O5/O7/O8 含む):
  cash_100bb: WRMSE 16.43% (UCBS-v1 の 21.43% から -5.00pt)
  mtt_25bb:    WRMSE 15.46%
  mtt_50bb:    WRMSE 12.96%
  mtt_100bb:   WRMSE 21.97%
  mtt_200bb:   WRMSE 14.10%  ★ Tier 1: MTT depth 25/50/100/200
  mtt_3bp_20bb:  WRMSE 23.08%
  mtt_3bp_25bb:  WRMSE 18.65%
  mtt_3bp_50bb:  WRMSE  8.62%
  mtt_3bp_100bb: WRMSE 13.37%  ★ Tier 3: 3BP IP depth series
  Tier 4: Turn cbet 2nd barrel (BTN IP after BB X)
  mtt_25bb_turn_btn:  WRMSE  7.02%
  mtt_50bb_turn_btn:  WRMSE 14.44%
  mtt_100bb_turn_btn: WRMSE 26.95%
  cash_100bb_turn_btn:WRMSE 16.11%

書籍読者の暗記対象 (合計 ~28 数値 + 3 例外ルール + 1 式):
  HP_TABLE: 6 バケット (共通)
  DP_TABLE: 4 段階 (共通)
  base_freq: 6 数値 (HIGH 70/45, MID 40/30, LOW 25/25) + overbet 例外 (HIGH +20, MID +15)
  カテゴリ 4 区分 + 共通 offset (trash -25, premium +15)
  context per: α, β, slowplay (cash=0/mtt=+5/+30/-30)
  position lift (4 数値): SB/wide × cash/mtt
  例外 3 ルール: 型6 up / mono down / A-x range bet (+30)
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


# ============================================================================
# 共通テーブル (全 context 共通)
# ============================================================================

HP_TABLE = {
    "no_made_hand":  2,
    "ace_high":      2,
    "king_high":     2,
    "low_pair":      2,
    "underpair":     3,
    "third_pair":    3,
    "second_pair":   5,
    "top_pair":      7,
    "overpair":      7,
    "two_pair":      9,
    "flush":         9,
    "straight":      9,
    "set":           8,
    "trips":         8,
    "fullhouse":     9,
    "quads":         9,
}

DP_TABLE = {
    "no_draw":       0,
    "twocards_bdfd": 0,
    "gutshot":       1,
    "oesd":          2,
    "fd":            2,
    "combo_draw":    3,
}

HAND_CATEGORY = {
    # slowplay 候補 (HP 8-9 だが GTO で slowplay されやすい役)
    "set":         "slowplay",
    "trips":       "slowplay",
    "two_pair":    "slowplay",
    "fullhouse":   "slowplay",
    "flush":       "slowplay",
    "straight":    "slowplay",
    "quads":       "slowplay",
    # trash (HP=2 だが bet 少)
    "low_pair":    "trash",
    # premium pair (slowplay 軽め)
    "overpair":    "premium",
    "underpair":   "premium",
    # default: ace_high, king_high, no_made_hand, third_pair, second_pair, top_pair
}


# ============================================================================
# Base frequency table (12 セル、cash 100bb data-driven、全 context 共通)
# ============================================================================

BASE_FREQ = {
    # (Confidence, Direction, Size) → freq
    ("HIGH", True,  33):  0.684,   # 強い手で確信、small 88 records
    ("HIGH", True,  116): 0.893,   # 強い手で確信、overbet 14
    ("HIGH", False, 33):  0.456,   # 弱い手で確信 (check 寄り)、small 84
    ("HIGH", False, 116): 0.437,   # 弱い手で確信、overbet 40
    ("MID",  True,  33):  0.400,   # 中程度、bet 寄り 36
    ("MID",  True,  116): 0.550,   # 中程度、overbet 30
    ("MID",  False, 33):  0.332,   # 中程度、check 寄り 29
    ("MID",  False, 116): 0.298,   # 中程度、overbet 24
    ("LOW",  True,  33):  0.254,   # ボード読み弱、bet 寄り 6
    ("LOW",  True,  116): 0.274,   # ボード読み弱、overbet 6
    # ("LOW",  False, 33):   ← cash データなし、フォールバック値
    # ("LOW",  False, 116):  ← cash データなし
}

# LOW False のフォールバック (HIGH/MID False の中央付近)
BASE_FREQ_FALLBACK = {
    ("LOW", False, 33):  0.30,
    ("LOW", False, 116): 0.28,
}


# ============================================================================
# Context 別パラメータ (WLS fit 結果)
# ============================================================================

CONTEXTS = {
    "cash_100bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": True,
        "alpha":    +0.00,
        "beta":     -0.02,
        "off_slowplay": +0.02,
        "off_trash":    -0.23,
        "off_premium":  +0.15,
        # Position lift (O7)
        "pos_lift": {
            "SB":  -0.08,
            "BTN": +0.00,
            "CO":  +0.10,
            "HJ":  +0.10,
            "UTG": +0.10,
        },
        # mono board conf shift (O5)
        "mono_conf_down": True,
        # A-high dry/paired range bet (O8): cash では効果なし
        "ax_range_bet": +0.00,
    },
    "mtt_25bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": False,
        "alpha":    +0.06,
        "beta":     +0.31,
        "off_slowplay": -0.28,
        "off_trash":    -0.23,
        "off_premium":  +0.15,
        # Position lift (O7)
        "pos_lift": {
            "SB":  -0.10,
            "BTN": +0.00,
            "CO":  +0.13,
            "HJ":  +0.13,
            "UTG": +0.13,
        },
        # mono board: mtt は効果薄、廃止
        "mono_conf_down": False,
        # A-high dry/paired range bet (O8): mtt BTN/CO で +30
        "ax_range_bet": +0.30,
    },
    # ─── MTT 50bb (MTT6mSimple、中盤 50bb) ────────────────────────────
    # データ: draw_study_MTT50BB.jsonl (120 spots, 5 positions × 24 boards)
    # WRMSE: 12.96% (mtt_25bb 流用 28.51% → -15.55pt、全 context 中最高精度)
    # 特徴: SB lift -29 (ICM 圧?)、wide lift ≈ 0、trash/premium 極端
    "mtt_50bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": False,
        "alpha":    -0.04,    # 50bb は cash 寄り (Simple tree でも overall 低め)
        "beta":     +0.19,    # CBS≥7 で middle lift
        "off_slowplay": -0.12,  # slowplay 軽め
        "off_trash":    -0.35,  # 50bb は low_pair 極端に控えめ
        "off_premium":  +0.20,  # overpair/underpair 強気
        "pos_lift": {
            "SB":  -0.29,    # SB は突出して控えめ (50bb の特殊性)
            "BTN": +0.00,
            "CO":  +0.00,    # position 効果薄
            "HJ":  +0.00,
            "UTG": +0.00,
        },
        "mono_conf_down": False,
        "ax_range_bet": +0.11,
    },
    # ═══ 3BP IP series (BTN cold-call vs BB 3bet → BTN IP cbet) ═══════
    # 全 depth で BTN_BB シナリオ、SPR は depth 依存:
    #   20bb=SPR2.5 / 25bb=SPR2.7 / 50bb=SPR5.5 / 100bb=SPR11

    # 3bp_20bb (低 SPR、linear range の middle hand bet 多)
    # WRMSE 23.08%
    "mtt_3bp_20bb": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    +0.02,
        "beta":     +0.14,
        "off_slowplay": -0.40,
        "off_trash":    -0.03,
        "off_premium":  -0.04,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False,
        "ax_range_bet": 0.0,
    },
    # 3bp_25bb (低 SPR、slowplay 極端、WRMSE 18.65%)
    "mtt_3bp_25bb": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    +0.09,
        "beta":     +0.19,
        "off_slowplay": -0.66,   # 25bb 3bp は set/trips が最も slowplay 集中
        "off_trash":    -0.44,
        "off_premium":  -0.09,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False,
        "ax_range_bet": 0.0,
    },
    # 3bp_50bb (深 SPR の標準、WRMSE 8.62% 最高精度)
    "mtt_3bp_50bb": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    +0.07,
        "beta":     +0.30,
        "off_slowplay": -0.40,
        "off_trash":    -0.45,
        "off_premium":  +0.14,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False,
        "ax_range_bet": 0.0,
    },
    # 3bp_100bb (deep polarize、WRMSE 13.37%)
    "mtt_3bp_100bb": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    +0.05,
        "beta":     +0.30,
        "off_slowplay": -0.33,
        "off_trash":    -0.48,
        "off_premium":  +0.20,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False,
        "ax_range_bet": 0.0,
    },
    # ═══ Turn cbet 2nd barrel series (BTN IP after BB X) ══════════════
    # 共通構造: α ≈ -0.35, β ≈ 0 (flop より低めの bet、強い役の追加 lift 不要)

    # turn_mtt25_btn (WRMSE 7.02%、最高精度)
    "mtt_25bb_turn_btn": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    -0.41, "beta": +0.01,
        "off_slowplay": -0.28, "off_trash": -0.01, "off_premium": +0.08,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False, "ax_range_bet": 0.0,
    },
    # turn_mtt50_btn (WRMSE 14.44%)
    "mtt_50bb_turn_btn": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    -0.37, "beta": -0.00,
        "off_slowplay": -0.25, "off_trash": -0.03, "off_premium": +0.10,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False, "ax_range_bet": 0.0,
    },
    # turn_mtt100_btn (WRMSE 26.95%、flop と同様 mtt_100bb は精度低)
    "mtt_100bb_turn_btn": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    -0.26, "beta": -0.00,
        "off_slowplay": -0.26, "off_trash": -0.14, "off_premium": +0.32,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False, "ax_range_bet": 0.0,
    },
    # turn_cash100_btn (WRMSE 16.11%)
    "cash_100bb_turn_btn": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    -0.37, "beta": +0.00,
        "off_slowplay": -0.27, "off_trash": -0.08, "off_premium": +0.22,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False, "ax_range_bet": 0.0,
    },
    # 後方互換: mtt_3bp_ip = mtt_3bp_20bb の alias
    "mtt_3bp_ip": {
        "thresholds": {"UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5},
        "polarize_enabled": False,
        "alpha":    +0.02,
        "beta":     +0.14,
        "off_slowplay": -0.40,
        "off_trash":    -0.03,
        "off_premium":  -0.04,
        "pos_lift": {"SB": 0, "BTN": 0, "CO": 0, "HJ": 0, "UTG": 0},
        "mono_conf_down": False,
        "ax_range_bet": 0.0,
    },
    # ─── MTT 200bb (MTT6mSimple、deep 200bb) ───────────────────────────
    # データ: draw_study_MTT200BB.jsonl (120 spots, 5 positions × 24 boards)
    # WRMSE: 14.10% (SB が 8.10% と特に高精度)
    # 構造: 50bb と類似 (SB lift 強く負、wide lift ≈ 0)
    "mtt_200bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": False,
        "alpha":    -0.04,
        "beta":     +0.11,
        "off_slowplay": -0.15,
        "off_trash":    -0.31,
        "off_premium":  +0.14,
        "pos_lift": {
            "SB":  -0.34,   # deep でも SB OOP は控えめ
            "BTN": +0.00,
            "CO":  +0.00,
            "HJ":  +0.00,
            "UTG": +0.00,
        },
        "mono_conf_down": False,
        "ax_range_bet": +0.09,
    },
    # ─── MTT 100bb (MTT6mSimple、序盤 100bb) ──────────────────────────
    # データ: draw_study_MTT100BB.jsonl (120 spots, 5 positions × 24 boards)
    # WRMSE: 21.97% (mtt_25bb 流用 24.37% → -2.40pt)
    "mtt_100bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": False,
        "alpha":    +0.15,    # mtt_25bb +0.06 より大 (Simple tree の wide cbet 傾向)
        "beta":     +0.09,    # mtt_25bb +0.31 より小 (slowplay 復活)
        "off_slowplay": -0.17,  # mtt_25bb -0.28 より緩 (100bb は slowplay 妙味復活)
        "off_trash":    -0.19,
        "off_premium":  +0.08,  # overpair の補正小さく
        "pos_lift": {
            "SB":  -0.11,
            "BTN": +0.00,
            "CO":  +0.17,    # mtt_25bb +0.13 より大
            "HJ":  +0.17,
            "UTG": +0.17,
        },
        "mono_conf_down": False,
        "ax_range_bet": +0.28,  # A-high range bet パターン継続
    },
}


# ============================================================================
# Board features & polarize 判定
# ============================================================================

def extract_board_features(board_cards_str: str) -> dict:
    """'Kc,7d,2s' or 'Ks7d2c' → features dict"""
    if "," in board_cards_str:
        cards = board_cards_str.split(",")[:3]
    else:
        cards = [board_cards_str[i*2:i*2+2] for i in range(3)]
    ranks = [c[0].upper() for c in cards]
    suits = [c[1].lower() for c in cards]
    order = "23456789TJQKA"
    rvals = sorted([order.index(r) for r in ranks], reverse=True)
    paired = len(set(ranks)) < 3
    suit_count = len(set(suits))
    suit_pattern = "mono" if suit_count == 1 else "2tone" if suit_count == 2 else "rainbow"
    return {
        "high": order[rvals[0]],
        "mid": order[rvals[1]],
        "low": order[rvals[2]],
        "gap": rvals[0] - rvals[2],
        "suit_pattern": suit_pattern,
        "paired": paired,
        "connected": (rvals[0] - rvals[2] <= 4) and not paired,
    }


def is_polarize_board(features: dict) -> bool:
    """Polarize board (cash overbet 適用) 判定 — UCBS v1 から継承"""
    if features["paired"] or features["suit_pattern"] == "mono":
        return False
    h = features["high"]; m = features["mid"]; gap = features["gap"]
    order = "23456789TJQKA"
    h_idx = order.index(h); m_idx = order.index(m)
    if h_idx <= order.index("9") and gap <= 4:
        return True
    if h == "K" and m_idx >= order.index("J") and gap >= 3:
        return True
    if h == "K" and m_idx >= order.index("9") and gap >= 5:
        return True
    if h == "A" and m_idx in range(order.index("8"), order.index("J") + 1) and gap >= 4:
        return True
    if h == "Q" and m_idx in range(order.index("8"), order.index("J") + 1) and gap >= 4:
        return True
    if h in ("J", "T") and m_idx in range(order.index("6"), order.index("9") + 1) and gap >= 3:
        return True
    return False


def parse_board_type(type_str: str) -> int:
    """型1〜型7 を抽出"""
    if not type_str:
        return 1
    for i in range(1, 8):
        if f"型{i}" in type_str:
            return i
    return 1


# ============================================================================
# Confidence 計算 (UCBS v1 から継承)
# ============================================================================

def calc_confidence(cbs: int, threshold: int, board_type: int) -> Literal["HIGH", "MID", "LOW"]:
    distance = abs(cbs - threshold)
    if distance >= 3:
        return "HIGH"
    if board_type == 1 and distance <= 2:
        return "HIGH"
    if board_type == 7 and distance == 0:
        return "HIGH"
    if board_type == 7 and distance == 1:
        return "LOW"
    if distance == 2:
        return "MID"
    if board_type == 5:
        return "MID"
    if board_type in (3, 4):
        return "LOW"
    return "MID"


def apply_confidence_exception(conf: str, board_type: int,
                                suit_pattern: str = "",
                                mono_down: bool = False) -> str:
    """前段例外: 信頼度シフト

    O4. 型6 (mid 連結ウェット) → 1 段上げる
    O5. mono board (cash のみ mono_down=True) → 1 段下げる
    """
    if board_type == 6:
        if conf == "LOW":
            conf = "MID"
        elif conf == "MID":
            conf = "HIGH"
    if mono_down and suit_pattern == "mono":
        if conf == "HIGH":
            conf = "MID"
        elif conf == "MID":
            conf = "LOW"
    return conf


def is_ax_dry_or_paired(features: dict) -> bool:
    """A-high で paired か gap >= 8 (dry/disconnected)。O8 用。"""
    if features["high"] != "A":
        return False
    return features["paired"] or features["gap"] >= 8


# ============================================================================
# UCBS-v2 統合判定
# ============================================================================

@dataclass
class UCBS2Decision:
    cbs: int
    hp: int
    dp: int
    confidence: str
    direction: bool
    size: int
    threshold: int
    base: float
    alpha: float
    beta_term: float
    offset: float
    frequency: float
    context: str
    category: str


def ucbs2_predict(
    hand_type: str,
    draw_type: str,
    board: str,                # "Kc,7d,2s" or "Ks7d2c"
    board_type_str: str,       # "型1..." or ""
    scenario: str,             # "UTG", "HJ", "CO", "BTN", "SB"
    context: str = "cash_100bb",
) -> UCBS2Decision:
    """UCBS-v2 中心関数: freq = base + α + β·I(CBS≥7) + offset[category]"""
    ctx = CONTEXTS[context]
    hp = HP_TABLE.get(hand_type, 0)
    dp = DP_TABLE.get(draw_type, 0)
    # Air paradox (UCBS v1 から継承)
    if hand_type == "no_made_hand" and draw_type == "oesd":
        cbs = hp - 2
    else:
        cbs = hp + dp

    threshold = ctx["thresholds"].get(scenario, 5)
    board_type = parse_board_type(board_type_str)
    features = extract_board_features(board)
    conf = calc_confidence(cbs, threshold, board_type)
    # 前段例外 O4/O5: 信頼度シフト
    conf = apply_confidence_exception(
        conf, board_type,
        suit_pattern=features["suit_pattern"],
        mono_down=ctx.get("mono_conf_down", False),
    )
    direction = cbs >= threshold

    # Size: polarize_enabled の context のみ overbet 候補
    if ctx["polarize_enabled"] and is_polarize_board(features):
        size = 116
    else:
        size = 33

    # Base frequency lookup
    key = (conf, direction, size)
    if key in BASE_FREQ:
        base = BASE_FREQ[key]
    elif key in BASE_FREQ_FALLBACK:
        base = BASE_FREQ_FALLBACK[key]
    else:
        base = 0.30

    # Context lift
    alpha = ctx["alpha"]
    beta_term = ctx["beta"] if cbs >= 7 else 0.0

    # Category offset
    category = HAND_CATEGORY.get(hand_type, "default")
    offset_key = f"off_{category}"
    offset = ctx.get(offset_key, 0.0)

    # O7. Position lift
    pos_lift = ctx.get("pos_lift", {}).get(scenario, 0.0)

    # O8. A-high paired/dry → range bet (mtt の BTN/CO で適用)
    ax_lift = 0.0
    if scenario in ("BTN", "CO") and is_ax_dry_or_paired(features):
        ax_lift = ctx.get("ax_range_bet", 0.0)

    freq = base + alpha + beta_term + offset + pos_lift + ax_lift
    freq = max(0.02, min(0.98, freq))

    return UCBS2Decision(
        cbs=cbs, hp=hp, dp=dp, confidence=conf, direction=direction,
        size=size, threshold=threshold,
        base=base, alpha=alpha, beta_term=beta_term, offset=offset,
        frequency=freq, context=context, category=category,
    )


# ============================================================================
# 評価関数
# ============================================================================

def evaluate_on_cash():
    import json
    from collections import defaultdict
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)
    scen_map = {"BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ",
                "UTG_BB": "UTG", "SB_BB": "SB", "BTN_SB": "BTN"}
    records = []
    for pos, boards in data.items():
        for board_key, info in boards.items():
            hand_cats = info.get("hand_cats", {})
            btype_str = info.get("type", "")
            board_cards = info.get("board", board_key)
            scen = scen_map.get(pos, "BTN")
            for h, vals in hand_cats.items():
                if h not in HP_TABLE:
                    continue
                n = vals.get("combos", 0)
                if n < 5:
                    continue
                gto = vals.get("bet_pct", 0) / 100.0
                d = ucbs2_predict(h, "no_draw", board_cards, btype_str, scen, "cash_100bb")
                records.append({"hand": h, "n": n, "gto": gto, "pred": d.frequency,
                                "err": d.frequency - gto, "cbs": d.cbs})
    total_n = sum(r["n"] for r in records)
    wrmse = (sum(r["n"] * r["err"]**2 for r in records) / total_n) ** 0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in records) / total_n
    print(f"\nUCBS-v2 cash_100bb: WRMSE={wrmse*100:.2f}%  WMAE={wmae*100:.2f}%  "
          f"records={len(records)}  combos={int(total_n)}")
    return wrmse, records


def _eval_mtt_depth_file(jsonl_file: str, context_name: str, label: str):
    """共通: draw_study_MTT*.jsonl を context で評価"""
    import json
    import sys
    sys.path.insert(0, "/home/cuzic/poker-books/scripts")
    from calc import classify_board_type7

    SCENARIO_POS = {
        "UTG_BB": "UTG", "HJ_BB": "HJ", "CO_BB": "CO",
        "BTN_BB": "BTN", "SB_BB": "SB",
    }
    records = []
    with open(jsonl_file) as f:
        for line in f:
            entry = json.loads(line)
            board = entry["board"]
            scen_pos = SCENARIO_POS.get(entry["scenario"], "BTN")
            try:
                bt_str = classify_board_type7(board)
            except Exception:
                bt_str = ""
            for h, vals in entry.get("hand_agg", {}).items():
                if h not in HP_TABLE:
                    continue
                n = vals.get("total", 0)
                if n < 3:
                    continue
                gto = vals.get("bet_pct", 0) / 100.0
                d = ucbs2_predict(h, "no_draw", board, bt_str, scen_pos, context_name)
                records.append({"hand": h, "n": n, "gto": gto, "pred": d.frequency,
                                "err": d.frequency - gto, "cbs": d.cbs})
    total_n = sum(r["n"] for r in records)
    wrmse = (sum(r["n"] * r["err"]**2 for r in records) / total_n) ** 0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in records) / total_n
    print(f"\nUCBS-v2 {label}: WRMSE={wrmse*100:.2f}%  WMAE={wmae*100:.2f}%  "
          f"records={len(records)}  combos={int(total_n)}")
    return wrmse, records


def evaluate_on_mtt_100bb():
    return _eval_mtt_depth_file(
        "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT100BB.jsonl",
        "mtt_100bb", "mtt_100bb")


def evaluate_on_mtt_50bb():
    return _eval_mtt_depth_file(
        "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT50BB.jsonl",
        "mtt_50bb", "mtt_50bb ")


def evaluate_on_mtt_200bb():
    return _eval_mtt_depth_file(
        "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT200BB.jsonl",
        "mtt_200bb", "mtt_200bb")


def evaluate_on_mtt():
    import json, glob
    from pathlib import Path
    from collections import defaultdict
    import sys
    sys.path.insert(0, "/home/cuzic/poker-books/scripts")
    from calc import classify_board_type7

    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    records = []
    for fp in files:
        name = Path(fp).stem.replace("draw_study_", "")
        if "3BP" in name:
            continue  # スコープ外
        if name in ("MTT100BB", "MTT50BB", "MTT200BB"):
            continue  # 別 context、別評価関数
        # ファイル名からシナリオ抽出
        if "_SB_cc" in name:
            scen_pos = "BTN"
        elif "_SB" in name:
            scen_pos = "SB"
        elif "_CO" in name:
            scen_pos = "CO"
        else:
            scen_pos = "BTN"
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry["board"]
                try:
                    bt_str = classify_board_type7(board)
                except Exception:
                    bt_str = ""
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE:
                        continue
                    n = vals.get("total", 0)
                    if n < 3:
                        continue
                    gto = vals.get("bet_pct", 0) / 100.0
                    d = ucbs2_predict(h, "no_draw", board, bt_str, scen_pos, "mtt_25bb")
                    records.append({"hand": h, "n": n, "gto": gto, "pred": d.frequency,
                                    "err": d.frequency - gto, "cbs": d.cbs})
    total_n = sum(r["n"] for r in records)
    wrmse = (sum(r["n"] * r["err"]**2 for r in records) / total_n) ** 0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in records) / total_n
    print(f"\nUCBS-v2 mtt_25bb:   WRMSE={wrmse*100:.2f}%  WMAE={wmae*100:.2f}%  "
          f"records={len(records)}  combos={int(total_n)}")
    return wrmse, records


def print_hand_bias(records, label):
    from collections import defaultdict
    print(f"\n[{label}] Hand 別 bias")
    by_hand = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in records:
        by_hand[r["hand"]][0] += r["n"] * r["err"]
        by_hand[r["hand"]][1] += r["n"]
        by_hand[r["hand"]][2] += r["n"] * r["err"]**2
    print(f"  {'hand':14s} {'HP':>3s} {'cat':>9s} {'combos':>7s} {'bias':>8s} {'wrmse':>8s}")
    for h in ["no_made_hand", "ace_high", "king_high", "low_pair", "underpair",
              "third_pair", "second_pair", "top_pair", "overpair",
              "two_pair", "straight", "flush", "set", "trips", "fullhouse"]:
        if h not in by_hand:
            continue
        esum, n, sse = by_hand[h]
        if n > 0:
            cat = HAND_CATEGORY.get(h, "default")
            print(f"  {h:14s} {HP_TABLE[h]:>3d}  {cat:>9s} {int(n):>6d}  "
                  f"{esum/n*100:+6.1f}%  {(sse/n)**0.5*100:>6.1f}%")


def demo():
    print("\n" + "=" * 70)
    print("UCBS-v2 デモ: 同じハンド × ボード を異なる context で予測")
    print("=" * 70)
    test_cases = [
        ("top_pair",     "no_draw", "Kc,7d,2s", "型1 ハイ×ドライ",  "BTN"),
        ("top_pair",     "no_draw", "Ah,Jd,4c", "型2 ハイ×ウェット", "BTN"),
        ("set",          "no_draw", "Kc,7d,2s", "型1",              "BTN"),
        ("low_pair",     "no_draw", "Kc,7d,2s", "型1",              "BTN"),
        ("overpair",     "no_draw", "9c,7d,2s", "型2",              "BTN"),
        ("no_made_hand", "oesd",    "Th,9s,8d", "型4",              "BTN"),
    ]
    for hand, draw, board, btype, sc in test_cases:
        print(f"\n[{hand} + {draw} on {board}]")
        for ctx in ["cash_100bb", "mtt_25bb"]:
            d = ucbs2_predict(hand, draw, board, btype, sc, ctx)
            print(f"  {ctx:12s} CBS={d.cbs:>2d} {d.confidence:>4s} "
                  f"dir={str(d.direction):>5s} size={d.size:>3d}% "
                  f"base={d.base*100:>4.1f}% α={d.alpha:+.2f} "
                  f"β={d.beta_term:+.2f} off={d.offset:+.2f} "
                  f"→ {d.frequency*100:>5.1f}%")


if __name__ == "__main__":
    print("=" * 70)
    print("UCBS-v2 検証 (5 context: cash + MTT 25/50/100/200)")
    print("=" * 70)
    cw, cash_recs = evaluate_on_cash()
    mw, mtt_recs = evaluate_on_mtt()
    m50w, mtt50_recs = evaluate_on_mtt_50bb()
    m100w, mtt100_recs = evaluate_on_mtt_100bb()
    m200w, mtt200_recs = evaluate_on_mtt_200bb()
    print(f"\n   UCBS-v2 全 context WRMSE:")
    print(f"     cash_100bb: {cw*100:.2f}%")
    print(f"     mtt_25bb:   {mw*100:.2f}%")
    print(f"     mtt_50bb:   {m50w*100:.2f}%")
    print(f"     mtt_100bb:  {m100w*100:.2f}%")
    print(f"     mtt_200bb:  {m200w*100:.2f}%")
