#!/usr/bin/env python3
"""cash_4bp_unified_v2.py — 4BP postflop 統一公式 (暗算可能版)

4BP flop/turn/river を「board polarization tier × hand strength tier」の 2 軸で
ロジカルに導出。Vol2 4BP 章を「暗記公式 + 例外少数」で書けるようにする。

中間概念 (他章と共通):
  - board_polar_tier: POLAR / MERGED / MID (4BP river 公式と同じ tier)
      * POLAR  = dynamic / dynamic_2tone / monotone  (相手に straight/flush 可能性)
      * MERGED = dry_high / low_dry / paired         (相手は大半 air、たまに set/full)
      * MID    = それ以外
  - hand strength tier: NUT_MADE / STRONG / PAIR / MID_PAIR / DRAW / AIR
  - street: 'flop' / 'turn' / 'river' で RAISE option 有無を分岐

統一原則 (Vol2 序文に書ける形):
  「4BP は opp range が tight (QQ+/AK) で flop/turn の 40-60% は air。
   よって defender は SRP より wide。POLAR board だけ AIR を fold」

期待 acc: 75-80% (専用 v1 と同等) を狙う。
"""
from __future__ import annotations

import pandas as pd

# ════════════════════ 中間概念 ════════════════════

POLAR_FAMILIES = {"dynamic", "dynamic_2tone", "monotone"}
MERGED_FAMILIES = {"dry_high", "low_dry", "paired"}

STRONG_DRAW = {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}

NUT_MADE = {"quads", "fullhouse", "straight_flush"}
STRONG_MADE = {"flush", "straight", "set", "trips"}
PAIR_TIER = {"overpair", "top_pair"}
TWO_PAIR_TIER = {"two_pair"}
MID_PAIR = {"second_pair", "third_pair", "low_pair", "underpair"}
AIR = {"no_made_hand", "ace_high", "king_high", "queen_high", "jack_high", "ten_high"}


def board_polar_tier(board_family: str) -> str:
    """Return POLAR / MERGED / MID for 4BP board context.

    POLAR = opp range can have straight/flush/full → strong made → slowdown.
    MERGED = opp range is mostly air or set+ → strong made bet for value.
    """
    if board_family in POLAR_FAMILIES:
        return "POLAR"
    if board_family in MERGED_FAMILIES:
        return "MERGED"
    return "MID"


# ════════════════════ 統一公式 ════════════════════

def cash_4bp_unified_v2(r) -> str:
    """4BP defense unified for flop/turn/river BB OOP.

    ロジック (暗算用):
      1) Strong made (TP+):
         - river → CALL (RAISE option なし)
         - non-river × POLAR → CALL (slowdown vs straight/flush)
         - non-river × MERGED/MID → RAISE
      2) Mid pair (2nd/3rd/UP/low): always CALL (4BP wide defense)
      3) Strong draw: always CALL
      4) AIR:
         - ace_high (blocker) → MERGED CALL, else FOLD
         - weak_draw × MERGED → CALL
         - その他 → FOLD
    """
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]
    # determine street: presence of board cards
    board_str = r.get("board_str", "")
    n_cards = len(board_str) // 2 if board_str else 0
    is_river = n_cards == 5
    # Some scenarios are river (5 cards), others flop (3) / turn (4)
    is_non_river = n_cards in (3, 4)

    tier = board_polar_tier(bf)

    # ── 1) Monsters ──
    if mv in NUT_MADE:
        return "CALL" if is_river else "RAISE"

    # ── 2) Strong made (set/trips/straight/flush) ──
    if mv in STRONG_MADE:
        if is_river:
            return "CALL"
        # non-river: slowdown on POLAR (vs possible nut)
        if tier == "POLAR" and mv in {"set"}:
            return "CALL"  # slowplay set on polar board
        return "CALL" if mv in {"straight", "flush"} else "RAISE"

    # ── 3) Two pair / overpair / top_pair ──
    if mv in TWO_PAIR_TIER | PAIR_TIER:
        if is_river:
            return "CALL"
        # non-river: slowdown on POLAR (flush/straight 警戒)
        if tier == "POLAR":
            return "CALL"
        return "RAISE"

    # ── 4) Mid pair (always CALL — 4BP defender wide) ──
    if mv in MID_PAIR:
        return "CALL"

    # ── 5) Strong draw → CALL ──
    if dv in STRONG_DRAW:
        return "CALL"

    # ── 6) AIR + weak draw ──
    if dv in WEAK_DRAW:
        # MERGED board (opp air heavy) → CALL with backdoor equity
        if tier == "MERGED":
            return "CALL"
        # POLAR board (opp has draws too) → equity 不足 → FOLD
        # MID → FOLD baseline
        return "FOLD"

    # ── 7) AIR + no draw ──
    if mv == "ace_high":
        # Ace_high has nut blocker → CALL on MERGED
        return "CALL" if tier == "MERGED" else "FOLD"
    # king_high / queen_high / jack_high / no_made_hand → FOLD
    return "FOLD"


# ════════════════════ Audit ════════════════════

def _evaluate(scenario_ids):
    """Run on dataset, compute acc / huge_loss per scenario."""
    df = pd.read_csv("scripts/three_class_model/dataset_unified_v2.csv", low_memory=False)
    for sid in scenario_ids:
        sub = df[df["scenario_id"] == sid].copy()
        if len(sub) == 0: continue
        sub["new_action"] = sub.apply(cash_4bp_unified_v2, axis=1)

        def loss(r):
            a = r["new_action"]
            ev = {"FOLD": r["ev_fold"], "CALL": r["ev_call"], "RAISE": r["ev_raise"]}.get(a)
            if pd.notna(ev): return r["best_ev"] - ev
            return r["ev_gap"]
        sub["new_loss"] = sub.apply(loss, axis=1)
        sub["new_correct"] = (sub["new_action"] == sub["best_action"])
        acc = sub["new_correct"].mean() * 100
        huge_rows = sub[sub["new_loss"] > 0.5]
        huge = huge_rows["new_loss"].mean() if len(huge_rows) > 0 else 0
        old_rows = sub[sub["formula_loss"] > 0.5]
        old_huge = old_rows["formula_loss"].mean() if len(old_rows) > 0 else 0
        print(f"{sid:30s}: acc={acc:.1f}%  huge_loss={huge:.2f}  (v1 baseline={old_huge:.2f})")


if __name__ == "__main__":
    print("=== Cash 4BP unified_v2 audit ===")
    _evaluate([
        "N_cash_4bp_flop", "A_cash_4bp_flop", "P6_A_mtt_4bp_flop",
        "N_cash_4bp_turn", "P6_A_mtt_4bp_turn",
        "N_cash_4bp_river", "P5_B_4bp_river_traj", "P6_A_mtt_4bp_river",
    ])
