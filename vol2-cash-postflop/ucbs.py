#!/usr/bin/env python3
"""
UCBS (Universal CBS) — cash と MTT の両方で使える統一 CBet 判定モデル。

設計原則:
1. 構造は CBS v1 (MTT) を維持: HP + DP + Confidence
2. Size 軸を追加 (CBS v2 cash の貢献): SMALL / MID / OVERBET / HUGE
3. Context をパラメータ化: cash100bb / mtt200bb / mtt100bb / mtt50bb / mtt25bb
4. HP/DP テーブルは原則共通、context 別に微調整
5. THRESHOLD / FREQ_TABLE / SIZE_RULES は context 別

これで:
  - 1 つの式で cash も MTT も予測できる
  - context を切り替えるだけで game type 対応
  - 書籍では「UCBS = HP + DP, +context 表」と説明できる
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal


# ============================================================================
# 共通テーブル (cash/MTT 同じ)
# ============================================================================

HP_TABLE = {
    "no_made_hand":  2,
    "ace_high":      2,
    "king_high":     2,
    "low_pair":      2,   # 統一値: ACASH では HP=1 だったが妥協で 2
    "underpair":     3,
    "third_pair":    3,
    "second_pair":   5,
    "top_pair":      7,
    "overpair":      7,
    "two_pair":      9,
    "flush":         9,
    "straight":      9,
    "set":           8,   # 統一値: cash=9, mtt=7 の中間
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


# ============================================================================
# Context 別パラメータ
# ============================================================================

CONTEXTS = {
    # ─── Cash 100bb ──────────────────────────────────────────────────────
    "cash_100bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        # Cash 専用 HP オーバーライド (bias 解消)
        "hp_overrides": {
            "low_pair":   1,
            "set":        9,
            "trips":      9,
            "flush":      7,
            "two_pair":   8,
            "king_high":  3,
            "no_made_hand": 3,
        },
        # Hand-type frequency modifier (CBS スコアの粗さを補正)
        # base_freq + offset を最終予測値とする
        "hand_freq_mod": {
            "low_pair":   -0.25,  # cash で low_pair の予測を -25pt
            "no_made_hand": +0.10,
            "ace_high":   +0.10,
            "king_high":  +0.10,
            "second_pair": -0.10,
            "third_pair":  +0.05,
            "underpair":  +0.08,
            "overpair":   +0.10,
            "two_pair":   -0.10,
            "set":        +0.10,
            "flush":      -0.05,
            "fullhouse":  +0.05,
        },
        "polarize_enabled": True,
        "freq_small": {
            ("HIGH", True):  0.75,  ("HIGH", False): 0.40,
            ("MID",  True):  0.55,  ("MID",  False): 0.40,
            ("LOW",  True):  0.45,  ("LOW",  False): 0.30,
        },
        "freq_overbet": {
            ("HIGH", True):  0.55,  ("HIGH", False): 0.15,
            ("MID",  True):  0.40,  ("MID",  False): 0.20,
            ("LOW",  True):  0.35,  ("LOW",  False): 0.25,
        },
    },

    # ─── MTT 200bb (full deep) ───────────────────────────────────────────
    "mtt_200bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 7,
        },
        "polarize_enabled": False,  # MTT 200bb は flop で polarize 少ない
        "freq_small": {
            # MTT 200bb は cbet 多用、freq 高め
            ("HIGH", True):  0.92,  ("HIGH", False): 0.50,
            ("MID",  True):  0.78,  ("MID",  False): 0.45,
            ("LOW",  True):  0.65,  ("LOW",  False): 0.35,
        },
        "freq_overbet": {
            # MTT 200bb のターン overbet は別ロジック、ここでは flop 用に低 freq
            ("HIGH", True):  0.60,  ("HIGH", False): 0.15,
            ("MID",  True):  0.45,  ("MID",  False): 0.20,
            ("LOW",  True):  0.40,  ("LOW",  False): 0.25,
        },
    },

    # ─── MTT 100bb (cash 相当) ───────────────────────────────────────────
    "mtt_100bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": True,
        # 既存 MTT 100bb 28 spots から派生 (cash より少し高め)
        "freq_small": {
            ("HIGH", True):  0.85,  ("HIGH", False): 0.45,
            ("MID",  True):  0.65,  ("MID",  False): 0.40,
            ("LOW",  True):  0.50,  ("LOW",  False): 0.30,
        },
        "freq_overbet": {
            ("HIGH", True):  0.55,  ("HIGH", False): 0.15,
            ("MID",  True):  0.40,  ("MID",  False): 0.20,
            ("LOW",  True):  0.35,  ("LOW",  False): 0.25,
        },
    },

    # ─── MTT 50bb (shallow) ──────────────────────────────────────────────
    "mtt_50bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": True,
        "freq_small": {
            ("HIGH", True):  0.80,  ("HIGH", False): 0.40,
            ("MID",  True):  0.55,  ("MID",  False): 0.35,
            ("LOW",  True):  0.40,  ("LOW",  False): 0.25,
        },
        "freq_overbet": {
            ("HIGH", True):  0.50,  ("HIGH", False): 0.10,
            ("MID",  True):  0.35,  ("MID",  False): 0.15,
            ("LOW",  True):  0.30,  ("LOW",  False): 0.20,
        },
    },

    # ─── MTT 3BP IP (BTN が 3bet コール側、SPR~3) ───────────────────────
    "mtt_3bp_ip": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": False,  # 3BP は linear range (slowplay 少ない)
        "simple_confidence": True,  # board_type 修飾を無効化 (3BP は SPR で支配)
        "freq_small": {
            ("HIGH", True):  0.95,  ("HIGH", False): 0.55,
            ("MID",  True):  0.80,  ("MID",  False): 0.50,
            ("LOW",  True):  0.65,  ("LOW",  False): 0.45,
        },
        "freq_overbet": {
            ("HIGH", True):  0.60,  ("HIGH", False): 0.15,
            ("MID",  True):  0.40,  ("MID",  False): 0.20,
            ("LOW",  True):  0.35,  ("LOW",  False): 0.20,
        },
        "hp_overrides": {
            # 3BP IP は linear: trip/set は普通に打つ (slowplay 軽め)
            "low_pair":  3,   # 53% target (default 2 では低すぎる)
            "set":       7,   # 27% target (slowplay 軽め)
            "trips":     7,
            "two_pair":  9,
            "fullhouse": 7,
        },
        "hand_freq_mod": {
            "no_made_hand": -0.05,
            "set":          -0.35,    # 27%
            "trips":        -0.30,    # 49%
            "fullhouse":    -0.40,    # slowplay 残
            "third_pair":   +0.15,    # 67%
            "second_pair":  +0.05,
        },
    },

    # NOTE: mtt_3bp_oop は OCBS (cash-postflop/ocbs.py) に分離。
    # OOP の U 字型分布は CBS の monotonic 構造と相性が悪く、別モデル。

    # ─── MTT 25bb (very short, MTT 中後半) ──────────────────────────────
    "mtt_25bb": {
        "thresholds": {
            "UTG": 5, "HJ": 5, "CO": 5, "BTN": 5, "SB": 5,
        },
        "polarize_enabled": False,
        # MTT 短スタックは air も中程度に打つ (FE 重視)
        "freq_small": {
            ("HIGH", True):  0.80,  ("HIGH", False): 0.45,
            ("MID",  True):  0.60,  ("MID",  False): 0.42,
            ("LOW",  True):  0.50,  ("LOW",  False): 0.35,
        },
        "freq_overbet": {
            ("HIGH", True):  0.50,  ("HIGH", False): 0.12,
            ("MID",  True):  0.32,  ("MID",  False): 0.18,
            ("LOW",  True):  0.28,  ("LOW",  False): 0.15,
        },
        # MTT 25bb 用 hand_freq_mod
        "hand_freq_mod": {
            "no_made_hand": +0.05,
            "ace_high":     +0.05,
            "king_high":    +0.05,
            "underpair":    +0.10,
            "second_pair":  -0.15,    # bias +27% を解消
            "set":          -0.10,
            "fullhouse":    -0.20,    # bias +38% を解消
            "trips":        +0.05,
        },
    },
}


# ============================================================================
# Board features 抽出
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


def parse_board_type(type_str: str) -> int:
    """型1〜型7 を抽出"""
    if not type_str:
        return 1
    for i in range(1, 8):
        if f"型{i}" in type_str:
            return i
    return 1


# ============================================================================
# Confidence 計算 (cash/MTT 共通だが board_type 修飾子で挙動変化)
# ============================================================================

def calc_confidence(cbs: int, threshold: int, board_type: int,
                     simple_mode: bool = False) -> Literal["HIGH", "MID", "LOW"]:
    """
    Confidence 計算。simple_mode=True で board_type 修飾を無効化。
    3BP のような特殊 context で使う。
    """
    distance = abs(cbs - threshold)
    if distance >= 3:
        return "HIGH"
    if simple_mode:
        # distance-only judgment
        return "MID" if distance == 2 else "HIGH" if distance == 0 else "LOW"
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


# ============================================================================
# Size 計算 (context 依存)
# ============================================================================

def is_polarize_board(features: dict) -> bool:
    """Polarize board 判定 (cash 用、187 spots から派生)"""
    if features["paired"] or features["suit_pattern"] == "mono":
        return False
    h = features["high"]
    m = features["mid"]
    gap = features["gap"]
    order = "23456789TJQKA"
    h_idx = order.index(h)
    m_idx = order.index(m)

    # 1. Super-connected low (876, 765, 975)
    if h_idx <= order.index("9") and gap <= 4:
        return True
    # 2. K-broadway-mid (KJ4, KQ7, KQJ系)
    if h == "K" and m_idx >= order.index("J") and gap >= 3:
        return True
    if h == "K" and m_idx >= order.index("9") and gap >= 5:
        return True
    # 3. A-mid-wet (AJ4, AT5, A87)
    if h == "A" and m_idx in range(order.index("8"), order.index("J") + 1) and gap >= 4:
        return True
    # 4. Q-mid-wet (QT5, Q86, QJ6)
    if h == "Q" and m_idx in range(order.index("8"), order.index("J") + 1) and gap >= 4:
        return True
    # 5. J/T mid-wet (J75, J85, T62, T87)
    if h in ("J", "T") and m_idx in range(order.index("6"), order.index("9") + 1) and gap >= 3:
        return True
    return False


def calc_size(features: dict, context: str) -> int:
    """Returns size as % of pot."""
    ctx = CONTEXTS[context]
    if ctx["polarize_enabled"] and is_polarize_board(features):
        return 116
    return 33


# ============================================================================
# UCBS 統合判定
# ============================================================================

@dataclass
class UCBSDecision:
    cbs: int
    hp: int
    dp: int
    confidence: str
    bet_direction: bool
    frequency: float
    size: int
    threshold: int
    context: str


def ucbs_predict(
    hand_type: str,
    draw_type: str,
    board: str,                # "Kc,7d,2s" or "Ks7d2c"
    board_type_str: str,       # "型1..." or ""
    scenario: str,             # "UTG", "HJ", "CO", "BTN", "SB"
    context: str = "cash_100bb",
) -> UCBSDecision:
    """UCBS の中心関数。context で cash/MTT 切替。"""
    ctx_params = CONTEXTS[context]
    # HP は共通テーブル + context-specific オーバーライド
    hp_overrides = ctx_params.get("hp_overrides", {})
    hp = hp_overrides.get(hand_type, HP_TABLE.get(hand_type, 0))
    dp = DP_TABLE.get(draw_type, 0)

    # Air paradox: no_made_hand + oesd → CBS = HP - 2
    if hand_type == "no_made_hand" and draw_type == "oesd":
        cbs = hp - 2
    else:
        cbs = hp + dp

    threshold = ctx_params["thresholds"].get(scenario, 5)
    board_type = parse_board_type(board_type_str)
    features = extract_board_features(board)
    size = calc_size(features, context)

    direction = cbs >= threshold
    simple_conf = ctx_params.get("simple_confidence", False)
    conf = calc_confidence(cbs, threshold, board_type, simple_mode=simple_conf)

    if size >= 100:
        freq = ctx_params["freq_overbet"][(conf, direction)]
    else:
        freq = ctx_params["freq_small"][(conf, direction)]

    # Hand-type frequency modifier (CBS スコアの粒度限界を補正)
    hand_mod = ctx_params.get("hand_freq_mod", {})
    freq = max(0.02, min(0.98, freq + hand_mod.get(hand_type, 0.0)))

    return UCBSDecision(
        cbs=cbs, hp=hp, dp=dp, confidence=conf,
        bet_direction=direction, frequency=freq,
        size=size, threshold=threshold, context=context,
    )


# ============================================================================
# 評価関数 (cash データに対する WRMSE)
# ============================================================================

def evaluate_on_cash():
    import json
    from collections import defaultdict

    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)

    scenarios_from_pos = {
        "BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ", "UTG_BB": "UTG",
        "SB_BB": "SB", "BTN_SB": "BTN",
    }

    records = []
    for pos, boards in data.items():
        for board_key, info in boards.items():
            hand_cats = info.get("hand_cats", {})
            board_type_str = info.get("type", "")
            board_cards = info.get("board", board_key)
            scenario = scenarios_from_pos.get(pos, "BTN")

            for hand_type, vals in hand_cats.items():
                if hand_type not in HP_TABLE:
                    continue
                n = vals.get("combos", 0)
                if n < 5:
                    continue
                gto_pct = vals.get("bet_pct", 0) / 100.0

                decision = ucbs_predict(
                    hand_type, "no_draw",
                    board_cards, board_type_str,
                    scenario, "cash_100bb",
                )
                err = decision.frequency - gto_pct
                records.append({
                    "pos": pos, "board": board_key, "hand": hand_type,
                    "n": n, "gto": gto_pct, "pred": decision.frequency,
                    "size": decision.size, "cbs": decision.cbs,
                    "conf": decision.confidence, "err": err,
                })

    total_n = sum(r["n"] for r in records)
    wrmse = (sum(r["n"] * r["err"]**2 for r in records) / total_n) ** 0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in records) / total_n

    print("=" * 70)
    print(f"UCBS cash_100bb 評価: WRMSE={wrmse*100:.2f}%  WMAE={wmae*100:.2f}%  n={len(records)}")
    print("=" * 70)

    # By hand
    by_hand = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in records:
        by_hand[r["hand"]][0] += r["n"] * r["err"]
        by_hand[r["hand"]][1] += r["n"]
        by_hand[r["hand"]][2] += r["n"] * r["err"]**2
    print(f"\n{'hand':16s} {'HP':>3s} {'n':>6s} {'bias':>8s} {'wrmse':>8s}")
    for h in ["no_made_hand", "ace_high", "king_high", "low_pair", "underpair",
              "third_pair", "second_pair", "top_pair", "overpair",
              "two_pair", "straight", "flush", "set", "trips", "fullhouse"]:
        if h not in by_hand: continue
        esum, n, sse = by_hand[h]
        if n > 0:
            print(f"  {h:14s} {HP_TABLE[h]:>3d}  {int(n):>6d}  "
                  f"{esum/n*100:+6.1f}%  {(sse/n)**0.5*100:>6.1f}%")
    return wrmse


def demo_unified():
    print("\n" + "=" * 70)
    print("UCBS デモ: 同じハンド × ボード を異なる context で予測")
    print("=" * 70)
    print(f"{'context':14s} {'CBS':>4s} {'conf':>6s} {'dir':>5s} {'size':>5s} {'freq':>6s}")
    print("-" * 50)

    test_cases = [
        # (hand_type, draw_type, board, board_type_str, scenario)
        ("top_pair", "no_draw", "Kc,7d,2s", "型1 ハイ×ドライ", "BTN"),
        ("top_pair", "no_draw", "Ah,Jd,4c", "型2 ハイ×ウェット", "BTN"),
        ("no_made_hand", "oesd", "Th,9s,8d", "型4 ロー×ウェット", "BTN"),
        ("set", "no_draw", "Kc,7d,2s", "型1 ハイ×ドライ", "BTN"),
    ]
    for case in test_cases:
        hand, draw, board, btype, sc = case
        print(f"\n[{hand} + {draw} on {board}]")
        for ctx in ["cash_100bb", "mtt_200bb", "mtt_100bb", "mtt_50bb", "mtt_25bb"]:
            d = ucbs_predict(hand, draw, board, btype, sc, ctx)
            print(f"  {ctx:14s} {d.cbs:>4d}  {d.confidence:>6s} {str(d.bet_direction):>5s} "
                  f"{d.size:>4d}% {d.frequency*100:>5.1f}%")


if __name__ == "__main__":
    evaluate_on_cash()
    demo_unified()
