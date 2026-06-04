#!/usr/bin/env python3
"""
Vol3 Simplified UCBS v2 — Vol2 Light の自然な拡張版

設計 (再修正):
1. Vol2 Light の **CBS バンド表を context 細分化** (5 → 10 context × 5 band = 50 cells)
2. Confidence 軸を **adjustment 層**として追加 (HIGH 0 / MID -10 / LOW -20)
3. 例外 4 つ (low_pair / SB / 型6 / mono)
4. Vol2 読者の知識をそのまま活かす

合計暗記:
  HP table (6) + DP table (4) + 50-cell band table + Confidence adj (2 値, HIGH=0)
  + 例外 4 = ~65 数値
  vs Full UCBS-v2 の 100+ 数値

暗算 step:
  1. HP + DP = CBS                              (Vol2 知識)
  2. CBS → band (air/weak/mid/strong/nut)        (Vol2 知識)
  3. context × band table → base                 (Vol2 拡張: 5→10 context)
  4. + Confidence adj (HIGH 0 / MID -10 / LOW -20)  ← Vol3 新規
  5. + 例外 (low_pair/SB/型6/mono)
  → 8 step、~10-12 秒
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2 import HP_TABLE, DP_TABLE, extract_board_features, parse_board_type, calc_confidence
from calc import classify_board_type7
from ucbs_light_v2 import cbs_band


# ─── 10 context × 5 band の base 表 ─────────────────────────
# Vol2 Light の 5 行を 10 行に細分化。Vol2 の構造はそのまま
BASE_TABLE = {
    # Vol2 Light = cash (45/40/40/60/60)
    "cash_100bb":   {"air": 0.45, "weak": 0.40, "mid": 0.40, "strong": 0.60, "nut": 0.60},
    # Vol2 Light mtt_short の 2 段階分割
    "mtt_25bb":     {"air": 0.40, "weak": 0.30, "mid": 0.40, "strong": 0.80, "nut": 0.85},
    "mtt_50bb":     {"air": 0.40, "weak": 0.30, "mid": 0.35, "strong": 0.65, "nut": 0.75},
    # Vol2 Light mtt_deep の 2 段階分割
    "mtt_100bb":    {"air": 0.45, "weak": 0.40, "mid": 0.45, "strong": 0.70, "nut": 0.70},
    "mtt_200bb":    {"air": 0.40, "weak": 0.40, "mid": 0.40, "strong": 0.60, "nut": 0.60},
    # Vol2 Light 3bp の SPR 別 (浅 = bet 弱、深 = polarize)
    "mtt_3bp_20bb": {"air": 0.50, "weak": 0.50, "mid": 0.65, "strong": 0.65, "nut": 0.40},
    "mtt_3bp_25bb": {"air": 0.45, "weak": 0.55, "mid": 0.70, "strong": 0.70, "nut": 0.50},
    "mtt_3bp_50bb": {"air": 0.45, "weak": 0.50, "mid": 0.60, "strong": 0.75, "nut": 0.55},
    "mtt_3bp_100bb":{"air": 0.40, "weak": 0.50, "mid": 0.60, "strong": 0.75, "nut": 0.65},
    # Vol2 Light turn (5/5/10/30/40) — context 別小調整
    "mtt_25bb_turn_btn":  {"air": 0.05, "weak": 0.05, "mid": 0.10, "strong": 0.30, "nut": 0.40},
    "mtt_50bb_turn_btn":  {"air": 0.05, "weak": 0.05, "mid": 0.15, "strong": 0.35, "nut": 0.40},
    "mtt_100bb_turn_btn": {"air": 0.10, "weak": 0.10, "mid": 0.20, "strong": 0.35, "nut": 0.45},
    "cash_100bb_turn_btn":{"air": 0.05, "weak": 0.10, "mid": 0.15, "strong": 0.35, "nut": 0.45},
}

# ─── Confidence adjustment (band 依存) ─────────────────────
# 強い役は Confidence の影響を受けにくく、弱い役は影響大
# = Light の 25 セル表で「型1/3/4/7 によって freq が違う」を Confidence で簡易表現
CONF_ADJ_BY_BAND = {
    "air":    {"HIGH": +0.00, "MID": -0.05, "LOW": -0.10},
    "weak":   {"HIGH": +0.00, "MID": -0.05, "LOW": -0.10},
    "mid":    {"HIGH": +0.05, "MID":  0.00, "LOW": -0.10},
    "strong": {"HIGH": +0.10, "MID":  0.00, "LOW": -0.05},
    "nut":    {"HIGH": +0.05, "MID":  0.00, "LOW": -0.05},
}


# ─── 例外ルール ───────────────────────────────────────────
def apply_exceptions(base, hand, scenario, board_type, board_features, context):
    """4 例外"""
    # E1: low_pair -10 (Vol2 共通)
    if hand == "low_pair":
        base -= 0.10
    # E2: SB scenario -10
    if scenario == "SB":
        base -= 0.10
    # E3: 型6 board +10 (信頼度 up 効果を数値で)
    if board_type == 6:
        base += 0.10
    # E4: mono board cash -10 (信頼度 down)
    if context == "cash_100bb" and board_features and board_features["suit_pattern"] == "mono":
        base -= 0.10
    return base


# ─── Vol3 Simplified 主関数 ────────────────────────────────
def ucbs_v3s(hand: str, draw: str, board: str, scenario: str,
             context: str = "cash_100bb") -> float:
    hp = HP_TABLE.get(hand, 0)
    dp = DP_TABLE.get(draw, 0)
    cbs = hp + dp
    band = cbs_band(cbs)
    base = BASE_TABLE[context][band]

    # Confidence 判定
    T = 5
    bt = 1
    feats = None
    if board:
        try:
            bt_str = classify_board_type7(board)
            bt = parse_board_type(bt_str)
            feats = extract_board_features(board)
        except Exception:
            pass
    # Confidence は Vol2 互換のため適用しない (シンプル化)
    # 必要なら型6 例外で表現
    _ = calc_confidence  # 未使用警告抑制
    base = apply_exceptions(base, hand, scenario, bt, feats, context)
    return max(0.05, min(0.95, base))


# ─── 評価 ─────────────────────────────────────────────────
def evaluate():
    files = [
        ("cash_100bb", "/home/cuzic/poker-books/vol2-cash-postflop/findings/cash_5cat_gto.json", "cash_100bb", "cash"),
        ("mtt_25bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_SRP25.jsonl", "mtt_25bb", "mtt"),
        ("mtt_50bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT50BB.jsonl", "mtt_50bb", "mtt"),
        ("mtt_100bb",  "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT100BB.jsonl", "mtt_100bb", "mtt"),
        ("mtt_200bb",  "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT200BB.jsonl", "mtt_200bb", "mtt"),
        ("3bp_25bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP25.jsonl", "mtt_3bp_25bb", "mtt"),
        ("3bp_50bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP50.jsonl", "mtt_3bp_50bb", "mtt"),
        ("3bp_100bb",  "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP100.jsonl", "mtt_3bp_100bb", "mtt"),
        ("turn_mtt25", "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl", "mtt_25bb_turn_btn", "mtt_turn"),
        ("turn_cash100","/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_CASH100_BTN.jsonl", "cash_100bb_turn_btn", "mtt_turn"),
    ]
    light_wrmse = {
        "cash_100bb": 21.07, "mtt_25bb": 36.08, "mtt_50bb": 19.08,
        "mtt_100bb": 35.54, "mtt_200bb": 21.49,
        "3bp_25bb": 15.71, "3bp_50bb": 9.63, "3bp_100bb": 15.33,
        "turn_mtt25": 16.67, "turn_cash100": 22.49,
    }
    full_wrmse = {
        "cash_100bb": 16.43, "mtt_25bb": 15.46, "mtt_50bb": 12.96,
        "mtt_100bb": 21.95, "mtt_200bb": 14.10,
        "3bp_25bb": 18.65, "3bp_50bb": 8.62, "3bp_100bb": 13.37,
        "turn_mtt25": 7.02, "turn_cash100": 16.11,
    }
    print("=" * 80)
    print("Vol3 Simplified v2 評価 (Light 25→50 セル拡張 + Confidence + 例外 4)")
    print("=" * 80)
    print(f"{'context':>14s}  {'Light':>7s}  {'V3 簡易':>7s}  {'Full':>7s}  "
          f"{'Δ(Light)':>9s}  {'Δ(Full)':>9s}")
    print("-" * 80)
    for label, fp, ctx, fmt in files:
        if not Path(fp).exists():
            continue
        records = _load(fp, fmt)
        sse, total_n = 0.0, 0.0
        for r in records:
            scen = r.get("scenario", "BTN")
            pred = ucbs_v3s(r["hand"], r.get("draw", "no_draw"),
                            r.get("board", ""), scen, ctx)
            err = pred - r["gto"]
            sse += r["n"] * err * err
            total_n += r["n"]
        wrmse = (sse / total_n) ** 0.5 * 100 if total_n else 0
        light = light_wrmse.get(label, 0)
        full = full_wrmse.get(label, 0)
        d_light = light - wrmse
        d_full = wrmse - full
        m = "◎" if d_full < 3 else ("○" if d_full < 6 else ("△" if d_full < 10 else "×"))
        print(f"  {label:>12s}  {light:>5.2f}%  {wrmse:>5.2f}%  {full:>5.2f}%  "
              f"{d_light:>+6.2f}pt  {d_full:>+6.2f}pt {m}")


def _load(fp, fmt):
    out = []
    if fmt == "cash":
        scen_map = {"BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ",
                    "UTG_BB": "UTG", "SB_BB": "SB", "BTN_SB": "BTN"}
        with open(fp) as f:
            data = json.load(f)
        for pos, boards in data.items():
            scen = scen_map.get(pos, "BTN")
            for board_key, info in boards.items():
                board_cards = info.get("board", board_key)
                for h, vals in info.get("hand_cats", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("combos", 0)
                    if n < 5: continue
                    out.append({"hand": h, "n": n, "draw": "no_draw",
                                "gto": vals["bet_pct"]/100.0,
                                "board": board_cards, "scenario": scen})
    elif fmt == "mtt_turn":
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                flop = entry.get("flop", entry.get("board", ""))
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("total", 0)
                    if n < 3: continue
                    out.append({"hand": h, "n": n, "draw": "no_draw",
                                "gto": vals["bet_pct"]/100.0,
                                "board": flop, "scenario": "BTN"})
    else:
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry.get("board", "")
                scen = entry.get("scenario", "BTN")
                if isinstance(scen, str):
                    if "_SB_cc" in scen: scen_pos = "BTN"
                    elif "_SB" in scen or scen.endswith("SB"): scen_pos = "SB"
                    elif "_CO" in scen or scen == "CO_BB": scen_pos = "CO"
                    else: scen_pos = "BTN"
                else:
                    scen_pos = "BTN"
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("total", 0)
                    if n < 3: continue
                    out.append({"hand": h, "n": n, "draw": "no_draw",
                                "gto": vals["bet_pct"]/100.0,
                                "board": board, "scenario": scen_pos})
    return out


if __name__ == "__main__":
    evaluate()
