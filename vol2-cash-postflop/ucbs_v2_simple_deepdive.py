#!/usr/bin/env python3
"""
UCBS-v2 簡易版 (23 数値) の苦手領域 deep dive。

調査内容:
  (1) 詳細版 vs 簡易版の差分 — どこで丸めが効くか
  (2) Top 30 worst outlier records
  (3) ボード特徴 (paired / suit / connectedness) 別 bias
  (4) Position × Confidence の組合せ別 bias
  (5) 板高 (high card rank) 別 bias
  (6) Scenario × Hand category マトリクス
  (7) 残差の符号パターン (over/under predict の地理)
  (8) 簡易版で新たに悪化したケース
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
    calc_confidence, apply_confidence_exception, ucbs2_predict,
)
from ucbs_v2_simplify import predict_simple
from calc import classify_board_type7


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
            try:
                feats = extract_board_features(board_cards)
            except Exception:
                continue
            for h, vals in info.get("hand_cats", {}).items():
                if h not in HP_TABLE: continue
                n = vals.get("combos", 0)
                if n < 5: continue
                gto = vals["bet_pct"] / 100.0
                pred_v2 = ucbs2_predict(h, "no_draw", board_cards,
                                         bt_str, scen, "cash_100bb").frequency
                pred_s = predict_simple(h, "no_draw", board_cards,
                                        bt_str, scen, "cash_100bb")
                bt_num = parse_board_type(bt_str)
                conf = calc_confidence(HP_TABLE[h], 5, bt_num)
                conf = apply_confidence_exception(conf, bt_num)
                size = 116 if is_polarize_board(feats) else 33
                out.append({
                    "ctx": "cash_100bb", "src": "cash", "hand": h,
                    "board": board_cards, "bt_str": bt_str, "scenario": scen,
                    "n": n, "gto": gto, "pred_v2": pred_v2, "pred_simple": pred_s,
                    "err_v2": pred_v2 - gto, "err_s": pred_s - gto,
                    "board_type": bt_num, "conf": conf, "size": size,
                    "cbs": HP_TABLE[h],
                    "paired": feats["paired"],
                    "suit_pattern": feats["suit_pattern"],
                    "high_card": feats["high"],
                    "connected": feats["connected"],
                    "gap": feats["gap"],
                    "category": HAND_CATEGORY.get(h, "default"),
                })
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
                try:
                    bt_str = classify_board_type7(board)
                    feats = extract_board_features(board)
                except Exception:
                    continue
                bt_num = parse_board_type(bt_str)
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("total", 0)
                    if n < 3: continue
                    gto = vals["bet_pct"] / 100.0
                    pred_v2 = ucbs2_predict(h, "no_draw", board, bt_str,
                                             scen_pos, "mtt_25bb").frequency
                    pred_s = predict_simple(h, "no_draw", board, bt_str,
                                            scen_pos, "mtt_25bb")
                    conf = calc_confidence(HP_TABLE[h], 5, bt_num)
                    conf = apply_confidence_exception(conf, bt_num)
                    out.append({
                        "ctx": "mtt_25bb", "src": "mtt", "hand": h,
                        "board": board, "bt_str": bt_str, "scenario": scen_pos,
                        "n": n, "gto": gto, "pred_v2": pred_v2, "pred_simple": pred_s,
                        "err_v2": pred_v2 - gto, "err_s": pred_s - gto,
                        "board_type": bt_num, "conf": conf, "size": 33,
                        "cbs": HP_TABLE[h],
                        "paired": feats["paired"],
                        "suit_pattern": feats["suit_pattern"],
                        "high_card": feats["high"],
                        "connected": feats["connected"],
                        "gap": feats["gap"],
                        "category": HAND_CATEGORY.get(h, "default"),
                    })
    return out


def wrmse(records, key="err_s"):
    if not records: return 0.0
    n = sum(r["n"] for r in records)
    if n == 0: return 0.0
    return (sum(r["n"] * r[key]**2 for r in records) / n) ** 0.5


def breakdown(records, key_fn, label, min_n=300, max_rows=15):
    groups = defaultdict(list)
    for r in records:
        groups[key_fn(r)].append(r)
    rows = []
    for k, recs in groups.items():
        n = sum(r["n"] for r in recs)
        if n < min_n: continue
        rows.append((k, len(recs), n,
                     wrmse(recs, "err_v2"), wrmse(recs, "err_s"),
                     sum(r["n"] * r["err_s"] for r in recs) / n))
    rows.sort(key=lambda x: -x[2])
    print(f"\n[{label}]")
    print(f"  {'key':>25s}  {'recs':>5s}  {'combos':>7s}  {'v2-WR':>6s}  {'s-WR':>6s}  {'s-bias':>7s}")
    for k, nr, nc, w_v2, w_s, bias in rows[:max_rows]:
        diff = (w_s - w_v2) * 100
        marker = " ⚠" if diff > 0.5 else ""
        print(f"  {str(k):>25s}  {nr:>5d}  {int(nc):>7d}  "
              f"{w_v2*100:>5.2f}  {w_s*100:>5.2f}  {bias*100:>+6.2f}{marker}")


def main():
    records = gather()
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    mtt = [r for r in records if r["ctx"] == "mtt_25bb"]
    print(f"records: cash={len(cash)}, mtt={len(mtt)}, total combos={sum(r['n'] for r in records)}")

    # (1) v2 vs simple 全体差分
    print("\n" + "=" * 78)
    print("(1) 詳細版 vs 簡易版の WRMSE 比較")
    print("=" * 78)
    for label, recs in [("cash", cash), ("mtt", mtt), ("全体", records)]:
        wv = wrmse(recs, "err_v2")
        ws = wrmse(recs, "err_s")
        diff = (ws - wv) * 100
        print(f"  {label:>5s}  詳細 {wv*100:.3f}%  簡易 {ws*100:.3f}%  Δ {diff:+.3f}pt")

    # (2) Top 30 worst outliers (簡易版)
    print("\n" + "=" * 78)
    print("(2) Top 30 worst |error| records (簡易版)")
    print("=" * 78)
    sorted_by_err = sorted(records, key=lambda r: -r["n"] * abs(r["err_s"]))[:30]
    print(f"  {'src':>4s} {'hand':>14s} {'board':>9s} {'btype':>5s} {'pos':>4s} "
          f"{'n':>5s} {'gto':>5s} {'pred':>5s} {'|err|':>5s}")
    for r in sorted_by_err:
        print(f"  {r['src']:>4s} {r['hand']:>14s} {r['board'][:9]:>9s} "
              f"{r['board_type']:>5d} {r['scenario']:>4s} {int(r['n']):>5d} "
              f"{r['gto']*100:>4.1f}% {r['pred_simple']*100:>4.1f}% "
              f"{abs(r['err_s'])*100:>4.1f}%")

    # (3) Board feature 別 (paired, suit, connected)
    print("\n" + "=" * 78)
    print("(3) ボード特徴別")
    print("=" * 78)
    breakdown(records, lambda r: f"paired={r['paired']}", "Paired board")
    breakdown(records, lambda r: r["suit_pattern"], "Suit pattern")
    breakdown(records, lambda r: f"connected={r['connected']} gap={r['gap']}",
              "Connectedness", min_n=2000)

    # (4) Position × Confidence
    print("\n" + "=" * 78)
    print("(4) Scenario × Confidence")
    print("=" * 78)
    breakdown(records, lambda r: f"{r['scenario']:>3s}-{r['conf']}",
              "scenario-conf", min_n=500, max_rows=20)

    # (5) High card 別
    print("\n" + "=" * 78)
    print("(5) Board high card 別")
    print("=" * 78)
    breakdown(records, lambda r: f"high={r['high_card']}",
              "High card", min_n=500)

    # (6) Scenario × Hand category
    print("\n" + "=" * 78)
    print("(6) Scenario × Hand category")
    print("=" * 78)
    breakdown(records, lambda r: f"{r['scenario']:>3s}-{r['category']}",
              "scenario-category", min_n=500, max_rows=20)

    # (7) 残差符号パターン (over/under predict)
    print("\n" + "=" * 78)
    print("(7) Over-predict vs Under-predict (簡易版)")
    print("=" * 78)
    over_n = sum(r["n"] for r in records if r["err_s"] > 0.05)
    under_n = sum(r["n"] for r in records if r["err_s"] < -0.05)
    accurate_n = sum(r["n"] for r in records if abs(r["err_s"]) <= 0.05)
    total = sum(r["n"] for r in records)
    print(f"  over-predict > +5pt : {over_n} combos ({over_n/total*100:.1f}%)")
    print(f"  accurate ±5pt       : {accurate_n} combos ({accurate_n/total*100:.1f}%)")
    print(f"  under-predict < -5pt: {under_n} combos ({under_n/total*100:.1f}%)")

    # (8) 簡易版で詳細版より悪化した cases
    print("\n" + "=" * 78)
    print("(8) 簡易版で詳細版より >5pt 悪化した record (上位)")
    print("=" * 78)
    worse = sorted(records,
                   key=lambda r: -(abs(r["err_s"]) - abs(r["err_v2"])) * r["n"])[:20]
    print(f"  {'src':>4s} {'hand':>14s} {'board':>9s} {'pos':>4s} "
          f"{'n':>5s} {'gto':>5s} {'v2':>5s} {'simple':>6s} {'Δerr':>6s}")
    for r in worse:
        diff = (abs(r["err_s"]) - abs(r["err_v2"])) * 100
        if diff < 1.0: continue
        print(f"  {r['src']:>4s} {r['hand']:>14s} {r['board'][:9]:>9s} "
              f"{r['scenario']:>4s} {int(r['n']):>5d} "
              f"{r['gto']*100:>4.1f}% {r['pred_v2']*100:>4.1f}% "
              f"{r['pred_simple']*100:>5.1f}% {diff:>+5.2f}pt")

    # (9) 12-cell の v2 vs simple
    print("\n" + "=" * 78)
    print("(9) (Conf, Dir, Size) セル別の v2 vs simple")
    print("=" * 78)
    def cell_key(r):
        cbs = r["cbs"]
        T = 5
        direction = cbs >= T
        return f"{r['conf']:>4s}/{str(direction):>5s}/{r['size']}"
    breakdown(records, cell_key, "Cell-by-cell", min_n=0, max_rows=20)


if __name__ == "__main__":
    main()
