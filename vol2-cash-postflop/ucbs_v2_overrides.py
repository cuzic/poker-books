#!/usr/bin/env python3
"""
UCBS-v2 苦手領域 override ロジック

UCBS-v2 の base prediction に後段で適用する補正ルール。
書籍では「特殊ケース 5 個」として箇条書きで覚えられる形を目指す。

Override rules:
  O1. Nutted slowplay: set/trips/fullhouse/quads は context 別 offset
      (cash で +0.10、mtt で -0.20 を追加)
  O2. Trash context-split: low_pair の trash offset を context 別に
      (cash で -0.20 追加、mtt は現状維持)
  O3. Wide opener size: UTG/HJ/CO open vs BB は size=33 強制
      (polarize でも overbet しない、cash 専用)
  O4. Type-6 board confidence shift: 型6 のとき HIGH → MID にダウンシフト
  O5. MID-False bluff boost: 信頼度 MID + check 方向 + CBS ≤ 2 のとき +0.05

各 override は独立に on/off 可能。ablation で効果を測定する。
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
    HP_TABLE, HAND_CATEGORY, BASE_FREQ, CONTEXTS,
    ucbs2_predict, parse_board_type, calc_confidence,
    extract_board_features, is_polarize_board,
)
from calc import classify_board_type7


# Override 適用辞書
NUTTED_HANDS = {"set", "trips", "fullhouse", "quads"}
WIDE_OPEN_POS = {"UTG", "HJ", "CO"}


# ============================================================================
# Override パラメータ (Lock-in WLS 等で fit 可能)
# ============================================================================

OVERRIDES = {
    "cash_100bb": {
        "O1_nutted_slowplay": +0.10,
        "O2_trash":           -0.17,   # 既存 trash=-0.23 に追加
        "O3_wide_open_size":  True,    # boolean flag
        "O3_wide_open_mid_cut": -0.05, # CBS 5-6 で wide pos のとき
        "O4_type6_conf_shift": True,
        "O5_mid_false_bluff": +0.05,
    },
    "mtt_25bb": {
        "O1_nutted_slowplay": -0.20,   # mtt は slowplay 強
        "O2_trash":           +0.00,
        "O3_wide_open_size":  False,   # mtt は size=33 一律で関係なし
        "O3_wide_open_mid_cut": 0.0,
        "O4_type6_conf_shift": True,
        "O5_mid_false_bluff": +0.00,
    },
}


# ============================================================================
# Override 適用関数 (UCBS-v2 base prediction の後段)
# ============================================================================

def apply_overrides(decision, hand_type, board, board_type_str, scenario,
                    context, enabled=None):
    """UCBS-v2 decision に override を適用し、修正後 freq を返す。

    enabled: set of rule names to apply, e.g. {"O1", "O2"}.
             None なら全 override 適用。
    """
    if enabled is None:
        enabled = {"O1", "O2", "O3", "O4", "O5"}

    ov = OVERRIDES[context]
    base_freq = decision.frequency
    bt = parse_board_type(board_type_str)

    # O1. Nutted slowplay
    delta_o1 = 0.0
    if "O1" in enabled and hand_type in NUTTED_HANDS:
        delta_o1 = ov["O1_nutted_slowplay"]

    # O2. Trash context-split
    delta_o2 = 0.0
    if "O2" in enabled and hand_type == "low_pair":
        delta_o2 = ov["O2_trash"]

    # O3. Wide opener size shift (cash 専用)
    delta_o3 = 0.0
    if "O3" in enabled and context == "cash_100bb" and ov["O3_wide_open_size"]:
        if scenario in WIDE_OPEN_POS:
            # size 116 適用されていた場合は 33 に戻したい
            # ここでは freq 補正で擬似的に: polarize → small への差分を -0.15 で吸収
            if decision.size == 116:
                # base_freq[(conf, dir, 33)] - base_freq[(conf, dir, 116)] で計算
                small_key = (decision.confidence, decision.direction, 33)
                big_key = (decision.confidence, decision.direction, 116)
                if small_key in BASE_FREQ and big_key in BASE_FREQ:
                    delta_o3 = BASE_FREQ[small_key] - BASE_FREQ[big_key]
            # CBS 5-6 帯で追加 cut
            if 5 <= decision.cbs <= 6:
                delta_o3 += ov["O3_wide_open_mid_cut"]

    # O4. Type-6 board confidence shift
    delta_o4 = 0.0
    if "O4" in enabled and ov["O4_type6_conf_shift"] and bt == 6:
        # HIGH → MID のシフトを擬似的に freq 差分で実現
        if decision.confidence == "HIGH":
            mid_key = ("MID", decision.direction, decision.size)
            cur_key = ("HIGH", decision.direction, decision.size)
            if mid_key in BASE_FREQ and cur_key in BASE_FREQ:
                delta_o4 = BASE_FREQ[mid_key] - BASE_FREQ[cur_key]

    # O5. MID-False bluff boost
    delta_o5 = 0.0
    if ("O5" in enabled and decision.confidence == "MID"
        and not decision.direction and decision.cbs <= 2):
        delta_o5 = ov["O5_mid_false_bluff"]

    new_freq = base_freq + delta_o1 + delta_o2 + delta_o3 + delta_o4 + delta_o5
    new_freq = max(0.02, min(0.98, new_freq))
    return new_freq, {
        "O1": delta_o1, "O2": delta_o2, "O3": delta_o3,
        "O4": delta_o4, "O5": delta_o5,
    }


# ============================================================================
# 評価関数
# ============================================================================

def gather_all_records():
    """cash + mtt の records を構築"""
    out = []
    # Cash
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
                d = ucbs2_predict(h, "no_draw", board_cards, bt_str, scen, "cash_100bb")
                out.append({
                    "ctx": "cash_100bb", "hand": h, "board": board_cards,
                    "bt_str": bt_str, "scenario": scen,
                    "n": n, "gto": vals["bet_pct"] / 100.0,
                    "pred_v2": d.frequency, "decision": d,
                    "board_type": parse_board_type(bt_str),
                })
    # MTT (3BP IP 含めない)
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    for fp in files:
        name = Path(fp).stem.replace("draw_study_", "")
        if "3BP" in name:
            continue
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
                    d = ucbs2_predict(h, "no_draw", board, bt_str, scen_pos, "mtt_25bb")
                    out.append({
                        "ctx": "mtt_25bb", "hand": h, "board": board,
                        "bt_str": bt_str, "scenario": scen_pos,
                        "n": n, "gto": vals["bet_pct"] / 100.0,
                        "pred_v2": d.frequency, "decision": d,
                        "board_type": parse_board_type(bt_str),
                    })
    return out


def wrmse(records, pred_key="pred_v2"):
    if not records:
        return 0.0
    n = sum(r["n"] for r in records)
    if n == 0:
        return 0.0
    return (sum(r["n"] * (r[pred_key] - r["gto"])**2 for r in records) / n) ** 0.5


def apply_and_measure(records, enabled):
    """enabled override セットを適用し、修正後 WRMSE を計算"""
    n = sum(r["n"] for r in records)
    if n == 0:
        return 0.0
    sse = 0.0
    for r in records:
        new_freq, _ = apply_overrides(
            r["decision"], r["hand"], r["board"], r["bt_str"],
            r["scenario"], r["ctx"], enabled,
        )
        err = new_freq - r["gto"]
        sse += r["n"] * err * err
    return (sse / n) ** 0.5


def main():
    print("=" * 78)
    print("UCBS-v2 + Override 効果測定 (ablation)")
    print("=" * 78)

    records = gather_all_records()
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    mtt = [r for r in records if r["ctx"] == "mtt_25bb"]
    print(f"records: cash={len(cash)}, mtt={len(mtt)}")

    # Baseline (override なし)
    cash_v2 = wrmse(cash)
    mtt_v2 = wrmse(mtt)
    print(f"\n[Baseline UCBS-v2]")
    print(f"  cash WRMSE = {cash_v2*100:.2f}%")
    print(f"  mtt  WRMSE = {mtt_v2*100:.2f}%")

    # Ablation: 各 override を独立に追加
    print(f"\n[Ablation] 各 override 単独効果")
    print(f"  {'override':>30s}  {'cash':>7s}  {'Δcash':>7s}  {'mtt':>7s}  {'Δmtt':>7s}")
    rules = {
        "O1 (nutted slowplay)": {"O1"},
        "O2 (trash context-split)": {"O2"},
        "O3 (wide opener size, cash)": {"O3"},
        "O4 (type-6 conf shift)": {"O4"},
        "O5 (MID-False bluff boost)": {"O5"},
    }
    for label, en in rules.items():
        cw = apply_and_measure(cash, en)
        mw = apply_and_measure(mtt, en)
        dc = (cw - cash_v2) * 100
        dm = (mw - mtt_v2) * 100
        marker_c = " ✓" if dc < -0.1 else (" ✗" if dc > 0.1 else "")
        marker_m = " ✓" if dm < -0.1 else (" ✗" if dm > 0.1 else "")
        print(f"  {label:>30s}  {cw*100:>5.2f}%  {dc:>+5.2f}{marker_c}  "
              f"{mw*100:>5.2f}%  {dm:>+5.2f}{marker_m}")

    # 全 override 適用
    print(f"\n[All overrides applied]")
    cw = apply_and_measure(cash, {"O1", "O2", "O3", "O4", "O5"})
    mw = apply_and_measure(mtt, {"O1", "O2", "O3", "O4", "O5"})
    print(f"  cash WRMSE = {cw*100:.2f}%  (Δ {(cw-cash_v2)*100:+.2f}pt)")
    print(f"  mtt  WRMSE = {mw*100:.2f}%  (Δ {(mw-mtt_v2)*100:+.2f}pt)")

    # 良い組合せを greedy で探す
    print(f"\n[Greedy forward selection] 改善する override のみ追加")
    enabled = set()
    remaining = {"O1", "O2", "O3", "O4", "O5"}
    while remaining:
        best_gain = 0.0
        best_rule = None
        for r in remaining:
            test_en = enabled | {r}
            cw = apply_and_measure(cash, test_en)
            mw = apply_and_measure(mtt, test_en)
            # combos 加重で総合 WRMSE
            nc = sum(rec["n"] for rec in cash)
            nm = sum(rec["n"] for rec in mtt)
            total_wr = ((cw**2 * nc + mw**2 * nm) / (nc + nm)) ** 0.5
            # current
            cw_cur = apply_and_measure(cash, enabled) if enabled else cash_v2
            mw_cur = apply_and_measure(mtt, enabled) if enabled else mtt_v2
            cur_wr = ((cw_cur**2 * nc + mw_cur**2 * nm) / (nc + nm)) ** 0.5
            gain = cur_wr - total_wr
            if gain > best_gain:
                best_gain = gain
                best_rule = r
        if best_rule is None or best_gain < 0.0001:
            break
        enabled.add(best_rule)
        remaining.remove(best_rule)
        cw = apply_and_measure(cash, enabled)
        mw = apply_and_measure(mtt, enabled)
        print(f"  + {best_rule}: cash={cw*100:.2f}%, mtt={mw*100:.2f}% "
              f"(joint gain {best_gain*100:+.3f}pt)")
    print(f"\n  Final enabled: {sorted(enabled)}")

    # 詳細: 苦手領域別の改善
    print(f"\n[苦手領域別の改善] override 全適用後")
    full_en = enabled

    # set 役 (mtt)
    mtt_set = [r for r in mtt if r["hand"] in NUTTED_HANDS]
    w_before = wrmse(mtt_set)
    w_after = apply_and_measure(mtt_set, full_en)
    print(f"  mtt nutted_slowplay (set/trips/fullhouse): "
          f"{w_before*100:.2f}% → {w_after*100:.2f}%  ({(w_after-w_before)*100:+.2f}pt)")

    # low_pair (cash)
    cash_low = [r for r in cash if r["hand"] == "low_pair"]
    w_before = wrmse(cash_low)
    w_after = apply_and_measure(cash_low, full_en)
    print(f"  cash low_pair: {w_before*100:.2f}% → {w_after*100:.2f}%  "
          f"({(w_after-w_before)*100:+.2f}pt)")

    # UTG/HJ/CO open (cash)
    cash_wide = [r for r in cash if r["scenario"] in WIDE_OPEN_POS]
    w_before = wrmse(cash_wide)
    w_after = apply_and_measure(cash_wide, full_en)
    print(f"  cash UTG/HJ/CO open: {w_before*100:.2f}% → {w_after*100:.2f}%  "
          f"({(w_after-w_before)*100:+.2f}pt)")

    # Type-6 board (cash + mtt)
    type6 = [r for r in records if r["board_type"] == 6]
    w_before = wrmse(type6)
    w_after = apply_and_measure(type6, full_en)
    print(f"  Type-6 board: {w_before*100:.2f}% → {w_after*100:.2f}%  "
          f"({(w_after-w_before)*100:+.2f}pt)")


if __name__ == "__main__":
    main()
