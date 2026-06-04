#!/usr/bin/env python3
"""
UCBS-v2 base_freq を丸めて圧縮するシミュレーション。

現状 base_freq (12 cells, 小数 1 桁):
  HIGH True  33   68.4%        HIGH True  116  89.3%
  HIGH False 33   45.6%        HIGH False 116  43.7%
  MID  True  33   40.0%        MID  True  116  55.0%
  MID  False 33   33.2%        MID  False 116  29.8%
  LOW  True  33   25.4%        LOW  True  116  27.4%

観察:
  - bet 方向 (True) と check 方向 (False) の差は HIGH で 25pt、MID で 10pt、LOW で 0pt
  - overbet (116) は HIGH-True で +21pt、MID-True で +15pt、他は無視できる差

提案: 「6 数値 + 1 ルール」に圧縮
  base_freq_simple = {
    HIGH: True 70 / False 45,
    MID:  True 40 / False 30,
    LOW:  True 25 / False 25,
  }
  overbet 例外: size = 116 のとき、True 側に
    HIGH: +20 (→ 90)
    MID:  +15 (→ 55)
    LOW:  +0
"""
from __future__ import annotations
import json, glob, sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2 import (
    HP_TABLE, DP_TABLE, HAND_CATEGORY, CONTEXTS,
    extract_board_features, is_polarize_board, parse_board_type,
    calc_confidence, apply_confidence_exception,
)
from calc import classify_board_type7


# 圧縮 base_freq (6 数値 + overbet 例外)
BASE_FREQ_SIMPLE = {
    ("HIGH", True):  0.70,
    ("HIGH", False): 0.45,
    ("MID",  True):  0.40,
    ("MID",  False): 0.30,
    ("LOW",  True):  0.25,
    ("LOW",  False): 0.25,
}

OVERBET_LIFT = {
    ("HIGH", True):  0.20,
    ("MID",  True):  0.15,
    ("LOW",  True):  0.00,
    ("HIGH", False): 0.00,
    ("MID",  False): 0.00,
    ("LOW",  False): 0.00,
}


def predict_simple(hand_type, draw_type, board, board_type_str, scenario, context):
    """6 数値 base_freq + 1 overbet ルール版"""
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
    size = 116 if (ctx["polarize_enabled"] and is_polarize_board(features)) else 33

    conf = calc_confidence(cbs, threshold, board_type)
    conf = apply_confidence_exception(conf, board_type)
    direction = (cbs >= threshold)

    base = BASE_FREQ_SIMPLE[(conf, direction)]
    if size == 116:
        base += OVERBET_LIFT[(conf, direction)]

    alpha = ctx["alpha"]
    beta_term = ctx["beta"] if cbs >= 7 else 0.0
    category = HAND_CATEGORY.get(hand_type, "default")
    offset = ctx.get(f"off_{category}", 0.0)

    return max(0.02, min(0.98, base + alpha + beta_term + offset))


def gather():
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
                if h not in HP_TABLE: continue
                n = vals.get("combos", 0)
                if n < 5: continue
                out.append({"ctx": "cash_100bb", "hand": h, "board": board_cards,
                            "bt_str": bt_str, "scenario": scen,
                            "n": n, "gto": vals["bet_pct"]/100.0})
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    for fp in files:
        name = Path(fp).stem.replace("draw_study_", "")
        if "3BP" in name: continue
        scen_pos = "BTN" if "_SB_cc" in name or ("SB" not in name and "CO" not in name) \
                   else "SB" if "_SB" in name else "CO"
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry["board"]
                try: bt_str = classify_board_type7(board)
                except Exception: bt_str = ""
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("total", 0)
                    if n < 3: continue
                    out.append({"ctx": "mtt_25bb", "hand": h, "board": board,
                                "bt_str": bt_str, "scenario": scen_pos,
                                "n": n, "gto": vals["bet_pct"]/100.0})
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
    records = gather()
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    mtt = [r for r in records if r["ctx"] == "mtt_25bb"]
    print(f"records: cash={len(cash)}, mtt={len(mtt)}")

    from ucbs_v2 import ucbs2_predict
    def fn_v2(r):
        return ucbs2_predict(r["hand"], "no_draw", r["board"],
                             r["bt_str"], r["scenario"], r["ctx"]).frequency
    def fn_simple(r):
        return predict_simple(r["hand"], "no_draw", r["board"],
                              r["bt_str"], r["scenario"], r["ctx"])

    print("\n比較:")
    print(f"  {'モデル':30s}  {'cash':>8s}  {'mtt':>8s}")
    print(f"  {'UCBS-v2 (12 セル詳細)':30s}  {wrmse(cash, fn_v2)*100:>6.2f}%  {wrmse(mtt, fn_v2)*100:>6.2f}%")
    print(f"  {'UCBS-v2 簡易 (6 数値+overbet)':30s}  {wrmse(cash, fn_simple)*100:>6.2f}%  {wrmse(mtt, fn_simple)*100:>6.2f}%")


if __name__ == "__main__":
    main()
