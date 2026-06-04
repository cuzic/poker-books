#!/usr/bin/env python3
"""
Medium UCBS — Light UCBS v2 + 境界例外ルール

Light の 25 セル表に **5 つの例外ルール** を加えて Full UCBS-v2 に近い精度を狙う。
暗算ステップは Light の 6 sec → Medium の 8-10 sec 程度に増えるが、Full の 15-20 sec より速い。

例外ルール (Full UCBS-v2 の主要効果を簡素化):
  E1. **mtt_short + CBS≥7**: +25pt (Full の β=+31 効果近似)
  E2. **mtt_100bb + CBS≥5**: +15pt (Full の α=+15 wide cbet 近似)
  E3. **mono board + cash**: -10pt (Full の mono conf down)
  E4. **A-high dry/paired + MTT BTN/CO**: +30pt (Full の ax_range_bet)
  E5. **SB scenario**: -10pt (Full の SB lift 近似)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_light_v2 import LIGHT_V2_BASE, LIGHT_V2_OFFSET, cbs_band
from ucbs_v2 import HP_TABLE, DP_TABLE, extract_board_features
from calc import classify_board_type7


# ─── 例外ルール ──────────────────────────────────────
def medium_ucbs(hand: str, draw: str, context: str,
                board: str = "", scenario: str = "BTN") -> float:
    """Light + 5 例外ルール"""
    hp = HP_TABLE.get(hand, 0)
    dp = DP_TABLE.get(draw, 0)
    cbs = hp + dp
    band = cbs_band(cbs)
    base = LIGHT_V2_BASE[context][band]
    base += LIGHT_V2_OFFSET.get(hand, 0.0)

    # board features
    feats = None
    bt = ""
    if board:
        try:
            feats = extract_board_features(board)
            bt = classify_board_type7(board)
        except Exception:
            pass

    # ── E1: mtt_short で強い役 (CBS≥7) は +15pt (穏当補正) ──
    # Note: +25 だと mtt_50 で over-correction、+15 が mtt_25/50 のバランス
    if context == "mtt_short" and cbs >= 7:
        base += 0.15

    # ── E2: mtt_deep で「nut 帯のみ」+10pt ──
    # Note: 全 CBS≥5 だと mtt_200 で過剰、nut 帯のみで mtt_100 wide cbet を捕捉
    if context == "mtt_deep" and cbs >= 9:
        base += 0.10

    # ── E3: mono board で cash は -10pt ──
    if context == "cash" and feats and feats["suit_pattern"] == "mono":
        base -= 0.10

    # ── E4: A-high dry/paired で MTT BTN/CO は +30pt ──
    if context in ("mtt_short", "mtt_deep") and scenario in ("BTN", "CO") and feats:
        if feats["high"] == "A" and (feats["paired"] or feats["gap"] >= 8):
            base += 0.30

    # ── E5: SB scenario なら -10pt ──
    if scenario == "SB":
        base -= 0.10

    return max(0.05, min(0.95, base))


# ─── 評価関数 ───────────────────────────────────────
def evaluate():
    files = [
        ("cash_100bb", "/home/cuzic/poker-books/vol2-cash-postflop/findings/cash_5cat_gto.json", "cash", "cash"),
        ("mtt_25bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_SRP25.jsonl", "mtt_short", "mtt"),
        ("mtt_50bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT50BB.jsonl", "mtt_short", "mtt"),
        ("mtt_100bb",  "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT100BB.jsonl", "mtt_deep", "mtt"),
        ("mtt_200bb",  "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT200BB.jsonl", "mtt_deep", "mtt"),
        ("3bp_25bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP25.jsonl", "3bp", "mtt"),
        ("3bp_50bb",   "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP50.jsonl", "3bp", "mtt"),
        ("3bp_100bb",  "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP100.jsonl", "3bp", "mtt"),
        ("turn_mtt25", "/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl", "turn", "mtt"),
        ("turn_cash100","/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_CASH100_BTN.jsonl", "turn", "mtt"),
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

    print("=" * 78)
    print("Medium UCBS 評価 (Light + 5 例外)")
    print("=" * 78)
    print(f"{'context':>14s}  {'Light':>7s}  {'Medium':>7s}  {'Full':>7s}  "
          f"{'Δvs Light':>10s}  {'Δvs Full':>9s}")
    print("-" * 78)
    for label, fp, ctx, fmt in files:
        if not Path(fp).exists():
            continue
        records = _load(fp, fmt)
        sse, total_n = 0.0, 0.0
        for r in records:
            scen = r.get("scenario", "BTN")
            pred = medium_ucbs(r["hand"], r.get("draw", "no_draw"), ctx,
                               r.get("board", ""), scen)
            err = pred - r["gto"]
            sse += r["n"] * err * err
            total_n += r["n"]
        wrmse = (sse / total_n) ** 0.5 * 100 if total_n else 0
        light = light_wrmse.get(label, 0)
        full = full_wrmse.get(label, 0)
        d_light = light - wrmse
        d_full = wrmse - full
        marker = "◎" if d_full < 3 else ("○" if d_full < 6 else ("△" if d_full < 10 else "×"))
        print(f"  {label:>12s}  {light:>5.2f}%  {wrmse:>5.2f}%  {full:>5.2f}%  "
              f"{d_light:>+6.2f}pt  {d_full:>+6.2f}pt {marker}")


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
    else:
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry.get("board", entry.get("flop", ""))
                # scenario: 3BP/turn/depth による
                scen = entry.get("scenario", "BTN")
                if isinstance(scen, str):
                    if "SB" in scen and "cc" not in scen:
                        scen_pos = "SB"
                    elif "CO" in scen:
                        scen_pos = "CO"
                    else:
                        scen_pos = "BTN"
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
