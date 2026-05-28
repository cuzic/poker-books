#!/usr/bin/env python3
"""
CBS v2 — 4-axis CBet decision model for cash.

軸構成:
  HP (現在価値):  1-9 by hand type
  DP (将来価値):  0-3 by draw type
  Confidence:    HIGH/MID/LOW by |CBS - threshold| + board_type
  Size:          SMALL(33%) / OVERBET(116%) by polarize_class

出力:
  (Size, BetDirection, Frequency)
  Frequency = FREQ_TABLE[(Confidence, BetDirection)]

実装ポイント:
1. 既存 CBS (HP/DP/Confidence) の構造を温存
2. Size 軸を追加 — board features から派生
3. cash 用 polarize_class 判定を新規実装
4. パラメータは cash 専用に再校正
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

# ──── HP テーブル (cash-tuned) ─────────────────────────────────────────────
HP_TABLE = {
    "no_made_hand":  2,
    "ace_high":      2,
    "king_high":     2,
    "low_pair":      1,   # cash で低ペアはほぼ打たない → HP=1
    "underpair":     3,
    "third_pair":    3,
    "second_pair":   5,
    "top_pair":      7,
    "overpair":      7,
    "two_pair":      9,
    "flush":         9,
    "straight":      9,
    "set":           9,   # cash の set はほぼ常に打つ → HP=9
    "trips":         9,
    "fullhouse":     9,
    "quads":         9,
}

# ──── DP テーブル ─────────────────────────────────────────────────────────
DP_TABLE = {
    "no_draw":       0,
    "twocards_bdfd": 0,
    "gutshot":       1,
    "oesd":          2,
    "fd":            2,
    "combo_draw":    3,
}

# ──── 閾値 (cash-tuned) ──────────────────────────────────────────────────
THRESHOLD = {
    "BTN":  5,
    "CO":   5,
    "HJ":   5,
    "UTG":  5,
    "SB":   5,
}

# ──── FREQ_TABLE_SMALL (33% pot, range bet 想定) ──────────────────────────
FREQ_TABLE_SMALL = {
    ("HIGH", True):  0.75,   ("HIGH", False): 0.40,
    ("MID",  True):  0.55,   ("MID",  False): 0.40,
    ("LOW",  True):  0.45,   ("LOW",  False): 0.30,
}

# ──── FREQ_TABLE_OVERBET (116% pot, polarize 想定) ────────────────────────
FREQ_TABLE_OVERBET = {
    ("HIGH", True):  0.55,   ("HIGH", False): 0.15,
    ("MID",  True):  0.40,   ("MID",  False): 0.20,
    ("LOW",  True):  0.35,   ("LOW",  False): 0.25,
}


# ──── Size 軸: polarize_class 判定 ────────────────────────────────────────
def is_polarize_board(board_features: dict) -> bool:
    """
    Polarize board (116% overbet を使う) 判定。
    board_features dict:
      high: 'A','K','Q','J','T','9'-'2'
      mid:  middle card rank
      low:  lowest card rank
      gap:  high - low (int)
      suit_pattern: 'rainbow'/'2tone'/'mono'
      paired: bool
      connected: gap <= 4 and not paired
    """
    if board_features["paired"] or board_features["suit_pattern"] == "mono":
        return False

    h = board_features["high"]
    m = board_features["mid"]
    gap = board_features["gap"]
    order = "23456789TJQKA"
    h_idx = order.index(h)
    m_idx = order.index(m)
    suit = board_features["suit_pattern"]

    # 1. Super-connected low (876, 765, 975) → P-class
    if h_idx <= order.index("9") and gap <= 4:
        return True

    # 2. K-broadway-mid (KJ4, KQ7, KQJ系)
    if h == "K" and m_idx >= order.index("J") and gap >= 3:
        # KJT は OK だが KJ4 など mid が J 以上で gap 大なら polarize
        return True
    if h == "K" and m_idx >= order.index("9") and gap >= 5:
        return True

    # 3. A-mid-wet (AJ4, AT5, AT7, A87)
    if h == "A" and m_idx in range(order.index("8"), order.index("J")+1) and gap >= 4:
        return True

    # 4. Q-mid-wet (QT5, Q86, Q87, QJ6)
    if h == "Q" and m_idx in range(order.index("8"), order.index("J")+1):
        # Q + 8-J mid card → polarize 候補
        if gap >= 4:
            return True

    # 5. J/T mid-wet (J75, J85, T62, T87)
    if h in ("J", "T") and m_idx in range(order.index("6"), order.index("9")+1) and gap >= 3:
        return True

    return False


def calc_size(board_features: dict) -> int:
    """Returns 33 or 116."""
    if is_polarize_board(board_features):
        return 116
    return 33


# ──── Confidence (cash-tuned, board_type ベース) ──────────────────────────
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


# ──── 統合判定 ─────────────────────────────────────────────────────────────
@dataclass
class CBSDecision:
    cbs: int
    confidence: str
    bet_direction: bool
    frequency: float
    size: int  # 33 or 116


def cbs_v2_predict(
    hand_type: str,
    draw_type: str,
    board_type: int,
    board_features: dict,
    scenario: str,
) -> CBSDecision:
    """CBS v2 の中心関数。"""
    hp = HP_TABLE.get(hand_type, 0)
    dp = DP_TABLE.get(draw_type, 0)

    # Air paradox: no_made_hand + oesd → CBS = HP - 2
    if hand_type == "no_made_hand" and draw_type == "oesd":
        cbs = hp - 2
    else:
        cbs = hp + dp

    th = THRESHOLD.get(scenario, 5)
    direction = cbs >= th
    conf = calc_confidence(cbs, th, board_type)
    size = calc_size(board_features)

    # Size 別の周波数決定
    if size == 116:
        freq = FREQ_TABLE_OVERBET[(conf, direction)]
    else:
        freq = FREQ_TABLE_SMALL[(conf, direction)]

    return CBSDecision(cbs=cbs, confidence=conf, bet_direction=direction,
                       frequency=freq, size=size)


# ──── board features 抽出 ─────────────────────────────────────────────────
def extract_board_features(board_cards_str: str) -> dict:
    """
    board_cards_str: 'Kc,7d,2s' or 'Ks7d2c'
    """
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
    if suit_count == 1:
        suit_pattern = "mono"
    elif suit_count == 2:
        suit_pattern = "2tone"
    else:
        suit_pattern = "rainbow"
    return {
        "high": order[rvals[0]],
        "mid":  order[rvals[1]],
        "low":  order[rvals[2]],
        "gap":  rvals[0] - rvals[2],
        "suit_pattern": suit_pattern,
        "paired": paired,
        "connected": (rvals[0] - rvals[2] <= 4) and not paired,
    }


def parse_board_type(type_str: str) -> int:
    """型1〜型7 を抽出。"""
    if not type_str:
        return 1
    for i in range(1, 8):
        if f"型{i}" in type_str:
            return i
    return 1


# ──── 評価関数 ─────────────────────────────────────────────────────────────
def evaluate_on_cash_data(json_path: str, scenarios_fn=None):
    import json
    from collections import defaultdict

    if scenarios_fn is None:
        def scenarios_fn(pos):
            if pos in ("BTN_BB", "CO_BB", "BTN_SB"):
                return "BTN"
            if pos == "SB_BB":
                return "SB"
            return "HJ"

    with open(json_path) as f:
        data = json.load(f)

    records = []
    for pos, boards in data.items():
        for board_key, info in boards.items():
            hand_cats = info.get("hand_cats", {})
            board_type_str = info.get("type", "")
            board_type = parse_board_type(board_type_str)
            board_cards = info.get("board", board_key)
            features = extract_board_features(board_cards)

            for hand_type, vals in hand_cats.items():
                if hand_type not in HP_TABLE:
                    continue
                n = vals.get("combos", 0)
                if n < 5:
                    continue
                gto_pct = vals.get("bet_pct", 0) / 100.0

                scenario = scenarios_fn(pos)
                decision = cbs_v2_predict(
                    hand_type, "no_draw",  # hand_cats は draw 込み aggregated
                    board_type, features, scenario,
                )
                err = decision.frequency - gto_pct
                records.append({
                    "pos": pos, "board": board_key, "board_type": board_type,
                    "hand": hand_type, "n": n, "gto": gto_pct,
                    "size": decision.size, "freq": decision.frequency,
                    "cbs": decision.cbs, "conf": decision.confidence,
                    "direction": decision.bet_direction,
                    "err": err,
                })

    total_n = sum(r["n"] for r in records)
    wrmse = (sum(r["n"] * r["err"]**2 for r in records) / total_n) ** 0.5
    wmae = sum(r["n"] * abs(r["err"]) for r in records) / total_n

    # Per-hand bias
    by_hand = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in records:
        by_hand[r["hand"]][0] += r["n"] * r["err"]
        by_hand[r["hand"]][1] += r["n"]
        by_hand[r["hand"]][2] += r["n"] * r["err"]**2

    return {"wrmse": wrmse, "wmae": wmae, "records": records, "by_hand": dict(by_hand)}


def main():
    print("=" * 60)
    print("CBS v2 評価 — cash data 347 records")
    print("=" * 60)
    result = evaluate_on_cash_data("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json")
    print(f"\nWRMSE = {result['wrmse']*100:.2f}%")
    print(f"WMAE  = {result['wmae']*100:.2f}%")
    print(f"records = {len(result['records'])}, combos = {sum(r['n'] for r in result['records']):.0f}")

    print("\n手牌別バイアス:")
    print(f"{'hand':16s} {'HP':>3s} {'n':>6s} {'bias':>8s} {'wrmse':>8s}")
    for h, (esum, n, sse) in sorted(result['by_hand'].items(),
                                     key=lambda x: -x[1][1]):
        if n > 0:
            print(f"  {h:14s} {HP_TABLE[h]:>3d} {int(n):>6d}  "
                  f"{esum/n*100:+6.1f}%  {(sse/n)**0.5*100:>6.1f}%")

    # Size 分布チェック
    size_counts = {33: 0, 116: 0}
    for r in result['records']:
        size_counts[r['size']] += r['n']
    print(f"\nSize 分布: 33% small = {size_counts[33]:.0f} combos, "
          f"116% overbet = {size_counts[116]:.0f} combos")


if __name__ == "__main__":
    main()
