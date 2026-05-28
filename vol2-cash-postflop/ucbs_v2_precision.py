#!/usr/bin/env python3
"""
UCBS-v2 包括的精度調査:

(1) ファイル別 WRMSE
(2) シナリオ (position) 別 WRMSE
(3) ボード型 (型1-7) 別 WRMSE
(4) Hand カテゴリ別 WRMSE
(5) Confidence × Direction × Size セル別 WRMSE
(6) 3BP IP がスコープ外として UCBS-v2 を当てた場合の参考値
(7) ベースライン比較 (平均値で常に予測した場合の WRMSE)
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
    HP_TABLE, HAND_CATEGORY, BASE_FREQ,
    ucbs2_predict, parse_board_type,
)
from calc import classify_board_type7


def gather_cash_records():
    """cash_5cat_gto.json から records 構築"""
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)
    scen_map = {"BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ",
                "UTG_BB": "UTG", "SB_BB": "SB", "BTN_SB": "BTN"}
    out = []
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
                d = ucbs2_predict(h, "no_draw", board_cards, bt_str, scen, "cash_100bb")
                gto = vals["bet_pct"] / 100.0
                out.append({
                    "src": "cash",
                    "file": "cash_5cat_gto",
                    "scenario": scen,
                    "board": board_cards,
                    "board_type": parse_board_type(bt_str),
                    "hand": h,
                    "category": HAND_CATEGORY.get(h, "default"),
                    "conf": d.confidence,
                    "dir": d.direction,
                    "size": d.size,
                    "cbs": d.cbs,
                    "n": n,
                    "gto": gto,
                    "pred": d.frequency,
                    "err": d.frequency - gto,
                })
    return out


def gather_mtt_records(include_3bp_ip=False):
    """draw_study_*.jsonl から records 構築"""
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    out = []
    for fp in files:
        name = Path(fp).stem.replace("draw_study_", "")
        # シナリオと scope 判定
        if "3BP" in name and "_SB" in name:
            continue  # OCBS スコープ
        if "3BP" in name:
            ctx = "mtt_25bb"  # UCBS-v2 で参考までに 3BP IP も評価
            if not include_3bp_ip:
                continue
            scen_pos = "BTN"
            tag = "3BP_IP"
        else:
            ctx = "mtt_25bb"
            tag = name
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
                    d = ucbs2_predict(h, "no_draw", board, bt_str, scen_pos, ctx)
                    gto = vals["bet_pct"] / 100.0
                    out.append({
                        "src": "mtt_3bp_ip" if "3BP" in name else "mtt_25bb",
                        "file": tag,
                        "scenario": scen_pos,
                        "board": board,
                        "board_type": parse_board_type(bt_str),
                        "hand": h,
                        "category": HAND_CATEGORY.get(h, "default"),
                        "conf": d.confidence,
                        "dir": d.direction,
                        "size": d.size,
                        "cbs": d.cbs,
                        "n": n,
                        "gto": gto,
                        "pred": d.frequency,
                        "err": d.frequency - gto,
                    })
    return out


def wrmse(records):
    if not records:
        return 0.0
    n = sum(r["n"] for r in records)
    if n == 0:
        return 0.0
    return (sum(r["n"] * r["err"]**2 for r in records) / n) ** 0.5


def wmae(records):
    if not records:
        return 0.0
    n = sum(r["n"] for r in records)
    if n == 0:
        return 0.0
    return sum(r["n"] * abs(r["err"]) for r in records) / n


def baseline_constant_wrmse(records, constant=None):
    """常に同じ値で予測した場合の WRMSE (baseline)"""
    if not records:
        return 0.0, 0.0
    n = sum(r["n"] for r in records)
    if constant is None:
        # combos 加重平均 GTO freq
        constant = sum(r["n"] * r["gto"] for r in records) / n
    sse = sum(r["n"] * (constant - r["gto"])**2 for r in records)
    return (sse / n) ** 0.5, constant


def breakdown_by(records, key_fn, label, min_n=1000):
    """key_fn ごとに WRMSE を出力"""
    groups = defaultdict(list)
    for r in records:
        groups[key_fn(r)].append(r)
    print(f"\n[{label}]")
    rows = []
    for k, recs in groups.items():
        n = sum(r["n"] for r in recs)
        if n < min_n:
            continue
        rows.append((k, len(recs), n, wrmse(recs), wmae(recs)))
    rows.sort(key=lambda x: -x[2])  # combos 降順
    print(f"  {'key':>24s}  {'records':>7s}  {'combos':>7s}  {'WRMSE':>8s}  {'WMAE':>8s}")
    for k, nrec, nc, wr, wm in rows:
        print(f"  {str(k):>24s}  {nrec:>7d}  {int(nc):>7d}  {wr*100:>6.2f}%  {wm*100:>6.2f}%")


def main():
    print("=" * 78)
    print("UCBS-v2 包括的精度調査")
    print("=" * 78)

    cash_recs = gather_cash_records()
    mtt_recs = gather_mtt_records(include_3bp_ip=False)
    mtt_3bp_recs = gather_mtt_records(include_3bp_ip=True)
    mtt_3bp_only = [r for r in mtt_3bp_recs if r["src"] == "mtt_3bp_ip"]

    # (1) 全体サマリ
    print("\n[1] 全体サマリ")
    print(f"  {'context':>20s}  {'records':>7s}  {'combos':>7s}  {'WRMSE':>8s}  {'WMAE':>8s}  {'baseline':>9s}")
    for label, recs in [
        ("cash_100bb (in-scope)", cash_recs),
        ("mtt_25bb (in-scope)",   mtt_recs),
        ("mtt_3bp_ip (out-of-scope ref)", mtt_3bp_only),
    ]:
        n = sum(r["n"] for r in recs)
        wr = wrmse(recs)
        wm = wmae(recs)
        bw, mean = baseline_constant_wrmse(recs)
        print(f"  {label:>34s}  {len(recs):>7d}  {int(n):>7d}  {wr*100:>6.2f}%  {wm*100:>6.2f}%  "
              f"{bw*100:>6.2f}% (μ={mean*100:.1f}%)")

    # (2) ファイル別
    print("\n[2] MTT ファイル別 WRMSE (in-scope のみ)")
    breakdown_by(mtt_recs, lambda r: r["file"], "MTT file")

    # (3) ボード型別
    all_recs = cash_recs + mtt_recs
    print("\n[3] ボード型別 (cash + mtt)")
    breakdown_by(all_recs, lambda r: f"型{r['board_type']}", "Board type")

    # (4) Hand カテゴリ別
    print("\n[4] Hand カテゴリ別 (cash + mtt)")
    breakdown_by(all_recs, lambda r: r["category"], "Category", min_n=0)

    # (5) Confidence セル別
    print("\n[5] (Confidence, Direction, Size) セル別 WRMSE")
    breakdown_by(all_recs, lambda r: f"{r['conf']}/{r['dir']}/{r['size']}",
                 "Cell", min_n=0)

    # (6) Confidence 単独
    print("\n[6] Confidence 単独")
    breakdown_by(all_recs, lambda r: r["conf"], "Confidence", min_n=0)

    # (7) シナリオ別 (cash)
    print("\n[7] cash シナリオ別")
    breakdown_by(cash_recs, lambda r: r["scenario"], "Cash scenario", min_n=0)

    # (8) hand 別 (cash + mtt 別々)
    print("\n[8] hand 別 (cash)")
    breakdown_by(cash_recs, lambda r: r["hand"], "Cash hand", min_n=50)
    print("\n[8b] hand 別 (mtt_25bb)")
    breakdown_by(mtt_recs, lambda r: r["hand"], "MTT hand", min_n=500)

    # (9) CBS 帯別
    def cbs_band(r):
        c = r["cbs"]
        if c <= 2: return "0-2 air"
        if c <= 4: return "3-4 weak"
        if c <= 6: return "5-6 mid"
        if c <= 8: return "7-8 strong"
        return "9+ nut"
    print("\n[9] CBS 帯別 (cash + mtt)")
    breakdown_by(all_recs, cbs_band, "CBS band", min_n=0)

    # (10) 予測誤差の分布
    print("\n[10] 誤差分布 (cash + mtt 統合)")
    n_total = sum(r["n"] for r in all_recs)
    bands = [(-1.0, -0.30), (-0.30, -0.15), (-0.15, -0.05), (-0.05, +0.05),
             (+0.05, +0.15), (+0.15, +0.30), (+0.30, +1.0)]
    print(f"  {'err range':>16s}  {'records':>7s}  {'combos':>7s}  {'fraction':>9s}")
    for lo, hi in bands:
        recs = [r for r in all_recs if lo <= r["err"] < hi]
        n = sum(r["n"] for r in recs)
        frac = n / n_total * 100
        print(f"  {f'{lo:+.2f} ~ {hi:+.2f}':>16s}  {len(recs):>7d}  {int(n):>7d}  {frac:>7.1f}%")

    # (11) サマリと評価
    print("\n" + "=" * 78)
    print("[サマリ] UCBS-v2 精度評価")
    print("=" * 78)
    cash_wr = wrmse(cash_recs)
    mtt_wr = wrmse(mtt_recs)
    cash_bl, _ = baseline_constant_wrmse(cash_recs)
    mtt_bl, _ = baseline_constant_wrmse(mtt_recs)
    print(f"  cash_100bb:  WRMSE {cash_wr*100:5.2f}% (baseline {cash_bl*100:.2f}%, "
          f"説明力 {(1 - cash_wr**2/cash_bl**2)*100:.1f}%)")
    print(f"  mtt_25bb:    WRMSE {mtt_wr*100:5.2f}% (baseline {mtt_bl*100:.2f}%, "
          f"説明力 {(1 - mtt_wr**2/mtt_bl**2)*100:.1f}%)")
    bp_wr = wrmse(mtt_3bp_only)
    bp_bl, _ = baseline_constant_wrmse(mtt_3bp_only)
    print(f"  mtt_3bp_ip:  WRMSE {bp_wr*100:5.2f}% (baseline {bp_bl*100:.2f}%, "
          f"説明力 {(1 - bp_wr**2/bp_bl**2)*100:.1f}%) ※スコープ外、参考値")


if __name__ == "__main__":
    main()
