#!/usr/bin/env python3
"""
CBS パラメータの cash 適合性最適化

目的: MTT 用 CBS (HP/DP/threshold/FREQ_TABLE) を cash データ 347 点に対して
WRMSE 最小化する形でリチューニング。構造は CBS のまま、パラメータのみ変更。

最適化対象:
- HP テーブル (15 手牌種別)
- threshold (BTN/SB/LIMP の 3 シナリオ)
- FREQ_TABLE (6 セル: confidence × bet_direction)
"""
import json
import itertools
from collections import defaultdict
from copy import deepcopy

# ──── Initial CBS (MTT default) ─────────────────────────────────────────────
HP_INIT = {
    "no_made_hand": 2, "ace_high": 2, "king_high": 2,
    "low_pair": 3, "underpair": 3, "third_pair": 3,
    "second_pair": 5,
    "top_pair": 7, "overpair": 7,
    "two_pair": 9, "flush": 9, "straight": 9,
    "set": 7, "trips": 7,
    "fullhouse": 9, "quads": 9,
}

THRESHOLD_INIT = {"BTN": 5, "SB": 7, "LIMP": 7}

FREQ_INIT = {
    ("HIGH", True):  0.79, ("HIGH", False): 0.42,
    ("MID",  True):  0.67, ("MID",  False): 0.39,
    ("LOW",  True):  0.58, ("LOW",  False): 0.37,
}


def calc_confidence(cbs: int, threshold: int, board_type: int) -> str:
    distance = abs(cbs - threshold)
    if distance >= 3: return "HIGH"
    if board_type == 1 and distance <= 2: return "HIGH"
    if board_type == 7 and distance == 0: return "HIGH"
    if board_type == 7 and distance == 1: return "LOW"
    if distance == 2: return "MID"
    if board_type == 5: return "MID"
    if board_type in (3, 4): return "LOW"
    return "MID"


def scenario_from_position(pos):
    if pos in ("BTN_BB", "CO_BB", "BTN_SB"):
        return "BTN"
    if pos == "SB_BB":
        return "SB"
    return "LIMP"  # HJ_BB, UTG_BB


def cbs_predict(cbs, scenario, board_type, hp_table, threshold_table, freq_table):
    th = threshold_table[scenario]
    direction = (cbs >= th)
    conf = calc_confidence(cbs, th, board_type)
    return freq_table[(conf, direction)]


def parse_board_type(board_type_str):
    """型1〜型7 → 1-7。"型6 ペア高" などの prefix を扱う。"""
    if not board_type_str:
        return 1
    s = board_type_str.strip()
    for i in range(1, 8):
        if f"型{i}" in s:
            return i
    return 1


def load_records():
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)
    records = []
    for pos, boards in data.items():
        for board_key, info in boards.items():
            hand_cats = info.get("hand_cats", {})
            board_type_str = info.get("type", "")
            board_type = parse_board_type(board_type_str)
            for hand_type, vals in hand_cats.items():
                if hand_type not in HP_INIT:
                    continue
                n = vals.get("combos", 0)
                if n < 5:
                    continue
                gto = vals.get("bet_pct", 0) / 100.0
                records.append({
                    "pos": pos, "board": board_key, "board_type": board_type,
                    "hand": hand_type, "n": n, "gto": gto,
                    "scenario": scenario_from_position(pos),
                })
    return records


def evaluate(records, hp, threshold, freq):
    total_n = 0
    total_se = 0.0
    bias_by_hand = defaultdict(lambda: [0.0, 0.0])
    for r in records:
        cbs = hp[r["hand"]] + 0  # DP=0 (hand_cats has no draw data)
        pred = cbs_predict(cbs, r["scenario"], r["board_type"], hp, threshold, freq)
        err = pred - r["gto"]
        total_n += r["n"]
        total_se += r["n"] * err * err
        bias_by_hand[r["hand"]][0] += r["n"] * err
        bias_by_hand[r["hand"]][1] += r["n"]
    wrmse = (total_se / total_n) ** 0.5
    return wrmse, bias_by_hand, total_n


def show_eval(label, records, hp, threshold, freq):
    wrmse, bias, n_total = evaluate(records, hp, threshold, freq)
    print(f"\n=== {label} ===")
    print(f"WRMSE = {wrmse*100:.2f}%, total_n = {n_total}")
    print(f"{'hand':16s} {'HP':>3s} {'bias':>8s} {'n':>6s}")
    for h, (bsum, n) in sorted(bias.items()):
        if n > 0:
            print(f"  {h:14s} {hp[h]:>3d}  {bsum/n*100:+6.1f}%  {int(n):>6d}")
    return wrmse


def main():
    records = load_records()
    print(f"Total records: {len(records)}, total combos: {sum(r['n'] for r in records)}")

    # Baseline
    print("\n" + "="*60)
    print("Baseline (MTT CBS default)")
    print("="*60)
    base_wrmse = show_eval("Default", records, HP_INIT, THRESHOLD_INIT, FREQ_INIT)

    # Hypothesis-based tuning
    # H1: set HP 7 → 9 (cash set is bet-everywhere)
    # H2: low_pair HP 3 → 1 (cash low_pair almost never bet)
    # H3: trips HP 7 → 9
    # H4: no_made_hand HP 2 → 3 (slightly higher)
    HP_TUNED = dict(HP_INIT)
    HP_TUNED["set"] = 9
    HP_TUNED["trips"] = 9
    HP_TUNED["low_pair"] = 1
    HP_TUNED["no_made_hand"] = 3
    HP_TUNED["fullhouse"] = 7  # cash fullhouse: lower for slowplay
    HP_TUNED["quads"] = 7

    print("\n" + "="*60)
    print("Hypothesis 1: HP adjustments (set/trips +2, low_pair -2, etc.)")
    print("="*60)
    h1_wrmse = show_eval("H1", records, HP_TUNED, THRESHOLD_INIT, FREQ_INIT)

    # H2: also lower FREQ_TABLE for cash
    FREQ_TUNED = {
        ("HIGH", True):  0.75, ("HIGH", False): 0.25,
        ("MID",  True):  0.60, ("MID",  False): 0.35,
        ("LOW",  True):  0.50, ("LOW",  False): 0.35,
    }
    print("\n" + "="*60)
    print("Hypothesis 2: HP tuned + FREQ_TABLE recalibrated")
    print("="*60)
    h2_wrmse = show_eval("H2", records, HP_TUNED, THRESHOLD_INIT, FREQ_TUNED)

    # H3: also adjust thresholds
    THRESHOLD_TUNED = {"BTN": 5, "SB": 5, "LIMP": 7}
    print("\n" + "="*60)
    print("Hypothesis 3: H2 + SB threshold 7 → 5")
    print("="*60)
    h3_wrmse = show_eval("H3", records, HP_TUNED, THRESHOLD_TUNED, FREQ_TUNED)

    # ──── Grid search on FREQ_TABLE ─────────────────────────────────────────
    print("\n" + "="*60)
    print("Grid search: FREQ_TABLE optimization (HP_TUNED, THRESHOLD_TUNED fixed)")
    print("="*60)
    best_wrmse = h3_wrmse
    best_freq = FREQ_TUNED
    for h_t in [0.65, 0.70, 0.75, 0.80, 0.85]:
        for h_f in [0.15, 0.20, 0.25, 0.30, 0.35]:
            for m_t in [0.50, 0.55, 0.60, 0.65, 0.70]:
                for m_f in [0.25, 0.30, 0.35, 0.40]:
                    for l_t in [0.40, 0.45, 0.50, 0.55]:
                        for l_f in [0.25, 0.30, 0.35, 0.40]:
                            f = {
                                ("HIGH", True): h_t,  ("HIGH", False): h_f,
                                ("MID",  True): m_t,  ("MID",  False): m_f,
                                ("LOW",  True): l_t,  ("LOW",  False): l_f,
                            }
                            w, _, _ = evaluate(records, HP_TUNED, THRESHOLD_TUNED, f)
                            if w < best_wrmse:
                                best_wrmse = w
                                best_freq = f
    print(f"Best FREQ:")
    for k, v in best_freq.items():
        print(f"  {k}: {v*100:.0f}%")
    print(f"Best WRMSE = {best_wrmse*100:.2f}%")
    show_eval("Best (after grid)", records, HP_TUNED, THRESHOLD_TUNED, best_freq)

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Baseline (MTT defaults):     WRMSE = {base_wrmse*100:.2f}%")
    print(f"  H1 (HP tuned):                WRMSE = {h1_wrmse*100:.2f}%")
    print(f"  H2 (HP + FREQ):               WRMSE = {h2_wrmse*100:.2f}%")
    print(f"  H3 (H2 + threshold):          WRMSE = {h3_wrmse*100:.2f}%")
    print(f"  Best (grid on FREQ):          WRMSE = {best_wrmse*100:.2f}%")
    print(f"  改善: {(base_wrmse - best_wrmse)*100:.1f}pt")


if __name__ == "__main__":
    main()
