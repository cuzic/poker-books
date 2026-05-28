#!/usr/bin/env python3
"""
UCBS-v2 前段例外ルール 3 案の比較

A. Confidence shift: 型6 のとき conf を 1 段上げる (LOW→MID, MID→HIGH)
B. Threshold shift:  型6 のとき T を -1 する (cash) / +1 (mtt 試行)
C. Polarize 強制:    型6 のとき is_polarize_board=True を強制 (cash のみ)

それぞれ ucbs2_predict のラッパーとして実装し、WRMSE 測定。
"""
from __future__ import annotations
import json
import glob
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2 import (
    HP_TABLE, DP_TABLE, HAND_CATEGORY, BASE_FREQ, BASE_FREQ_FALLBACK, CONTEXTS,
    extract_board_features, is_polarize_board, parse_board_type, calc_confidence,
    UCBS2Decision,
)
from calc import classify_board_type7


def predict_with_exception(
    hand_type, draw_type, board, board_type_str, scenario, context,
    exception="none",
):
    """UCBS-v2 with front-end exception variants.

    exception:
      "none"           : 原版
      "conf_shift"     : 型6 で conf を 1 段 up
      "threshold_shift": 型6 で T -= 1 (cash) / T += 1 (mtt 不明だが試行)
      "polarize"       : 型6 で polarize 強制 (cash のみ意味あり)
    """
    ctx = CONTEXTS[context]
    hp = HP_TABLE.get(hand_type, 0)
    dp = DP_TABLE.get(draw_type, 0)
    if hand_type == "no_made_hand" and draw_type == "oesd":
        cbs = hp - 2
    else:
        cbs = hp + dp

    threshold = ctx["thresholds"].get(scenario, 5)
    board_type = parse_board_type(board_type_str)
    features = extract_board_features(board)

    # === 前段例外: threshold_shift ===
    if exception == "threshold_shift" and board_type == 6:
        if context == "cash_100bb":
            threshold -= 1
        elif context == "mtt_25bb":
            threshold -= 1

    # === 前段例外: polarize 強制 (cash のみ意味あり) ===
    if exception == "polarize" and board_type == 6:
        size = 116 if ctx["polarize_enabled"] else 33
    else:
        size = 116 if (ctx["polarize_enabled"] and is_polarize_board(features)) else 33

    conf = calc_confidence(cbs, threshold, board_type)

    # === 前段例外: conf_shift ===
    if exception == "conf_shift" and board_type == 6:
        if conf == "LOW": conf = "MID"
        elif conf == "MID": conf = "HIGH"
        # HIGH のまま

    direction = (cbs >= threshold)

    key = (conf, direction, size)
    if key in BASE_FREQ:
        base = BASE_FREQ[key]
    elif key in BASE_FREQ_FALLBACK:
        base = BASE_FREQ_FALLBACK[key]
    else:
        base = 0.30

    alpha = ctx["alpha"]
    beta_term = ctx["beta"] if cbs >= 7 else 0.0
    category = HAND_CATEGORY.get(hand_type, "default")
    offset = ctx.get(f"off_{category}", 0.0)

    freq = base + alpha + beta_term + offset
    return max(0.02, min(0.98, freq))


def gather_records():
    out = []
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)
    scen_map = {"BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ",
                "UTG_BB": "UTG", "SB_BB": "SB", "BTN_SB": "BTN"}
    for pos, boards in data.items():
        for board_key, info in boards.items():
            bt_str = info.get("type", "")
            board_cards = info.get("board", board_key)
            scen = scen_map.get(pos, "BTN")
            for h, vals in info.get("hand_cats", {}).items():
                if h not in HP_TABLE:
                    continue
                n = vals.get("combos", 0)
                if n < 5:
                    continue
                out.append({
                    "ctx": "cash_100bb", "hand": h, "board": board_cards,
                    "bt_str": bt_str, "scenario": scen,
                    "n": n, "gto": vals["bet_pct"] / 100.0,
                    "board_type": parse_board_type(bt_str),
                })
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    for fp in files:
        name = Path(fp).stem.replace("draw_study_", "")
        if "3BP" in name:
            continue
        scen_pos = "BTN" if "_SB_cc" in name or ("SB" not in name and "CO" not in name) \
                   else "SB" if "_SB" in name else "CO"
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
                    out.append({
                        "ctx": "mtt_25bb", "hand": h, "board": board,
                        "bt_str": bt_str, "scenario": scen_pos,
                        "n": n, "gto": vals["bet_pct"] / 100.0,
                        "board_type": parse_board_type(bt_str),
                    })
    return out


def wrmse(records, pred_fn):
    sse, total_n = 0.0, 0.0
    for r in records:
        pred = pred_fn(r)
        err = pred - r["gto"]
        sse += r["n"] * err * err
        total_n += r["n"]
    return (sse / total_n) ** 0.5 if total_n else 0.0


def main():
    records = gather_records()
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    mtt = [r for r in records if r["ctx"] == "mtt_25bb"]
    print(f"records: cash={len(cash)}, mtt={len(mtt)}")

    print("\n" + "=" * 76)
    print("前段例外 3 案 比較 (WRMSE)")
    print("=" * 76)

    def make_fn(exception):
        return lambda r: predict_with_exception(
            r["hand"], "no_draw", r["board"], r["bt_str"],
            r["scenario"], r["ctx"], exception,
        )

    print(f"{'exception':>22s}  {'cash':>8s}  {'mtt':>8s}  "
          f"{'cash型6':>10s}  {'mtt型6':>10s}")
    cash_t6 = [r for r in cash if r["board_type"] == 6]
    mtt_t6 = [r for r in mtt if r["board_type"] == 6]
    for excp in ["none", "conf_shift", "threshold_shift", "polarize"]:
        fn = make_fn(excp)
        cw = wrmse(cash, fn)
        mw = wrmse(mtt, fn)
        c6 = wrmse(cash_t6, fn)
        m6 = wrmse(mtt_t6, fn)
        print(f"{excp:>22s}  {cw*100:>6.2f}%  {mw*100:>6.2f}%  "
              f"{c6*100:>8.2f}%  {m6*100:>8.2f}%")

    # 型6 ボードでの hand 別 bias (conf_shift 案)
    print("\n[Cash 型6 ボードでの hand 別 bias]")
    for excp in ["none", "conf_shift", "threshold_shift"]:
        fn = make_fn(excp)
        print(f"\n-- exception = {excp} --")
        by_hand = defaultdict(lambda: [0.0, 0.0])
        for r in cash_t6:
            pred = fn(r)
            err = pred - r["gto"]
            by_hand[r["hand"]][0] += r["n"] * err
            by_hand[r["hand"]][1] += r["n"]
        print(f"  {'hand':14s} {'combos':>7s} {'bias':>8s}")
        for h in sorted(by_hand.keys()):
            esum, n = by_hand[h]
            if n > 0:
                print(f"  {h:14s} {int(n):>6d}  {esum/n*100:+6.1f}%")


if __name__ == "__main__":
    main()
