#!/usr/bin/env python3
"""cash_3bp_turn_v1.py — Cash 100bb 3BP turn, BB OOP defense (v2、data-driven 修正版).

Domain: Cash 100bb (and MTT 100bb) 3BP, BB OOP defender vs IP 3-bettor's turn barrel.

Data source:
  - probe_phase5_stats.json: P5_A_cash_3bp_turn acc=66.3%, opp_pol=0.711, opp_weak=0.424
  - probe_phase5_stats.json: P5_A_mtt_3bp_turn acc=66.5%, opp_pol=0.714 (≈ Cash)
  - PROBE_PRIORITY_FINDINGS.md §5 (Tier B)、§6.1

Key findings (revised 2026-06-06 audit):
  - bet_size 分布: overbet_185 (5640) + med_75p (1128)。
    "overbet_185" は実は barrel R24 で、true overbet ではない。
  - 3BP turn の OOP は SRP より wide に call できる:
      * top_pair × overbet_185 → CALL 多数 (formula は v1 で FOLD していた、acc 上)
      * ace_high × monotone × overbet_185 → CALL (nut blocker)
      * second_pair × weak_draw → CALL (3BP 3-bettor は bluff も持つ)

Design (v2):
  - 強い made hand (set+) は CALL/RAISE
  - **top_pair, overpair は基本 CALL** (v1 のように bet_size で FOLD しない)
  - middle pair × draw → CALL
  - AIR × strong draw → CALL
  - AIR × ace_high/king_high × monotone → CALL (blocker)
  - 上記以外の AIR → FOLD
"""
from __future__ import annotations

from typing import Literal

Action = Literal["FOLD", "CALL", "RAISE"]

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}
STRONG_DRAW = {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}
STRONG_MADE = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}

# 3BP turn bet sizes — probe's classify_bet_size() vocabulary
SMALL_BETS = {"small_33", "small_30p"}
BARRELS = {"med_75p", "med_100p"}
OVERBETS = {"overbet", "overbet_185", "allin"}  # NOTE: overbet_185 は barrel R24


def cash_3bp_turn_def_v1(
    mv: str,
    dv: str,
    board_family: str,
    bet_size: str = "med_75p",
    opp_polarization: float = 0.711,
) -> Action:
    """Cash/MTT 100bb 3BP turn BB OOP defense v2.

    Args:
        mv: made-value category.
        dv: draw-value category.
        board_family: board texture family.
        bet_size: probe classify_bet_size 出力 (small_33 / med_75p / overbet_185 等)。
        opp_polarization: 3-bettor's turn range polarity (default from N_cash_3bp_turn).
    """
    has_strong_draw = dv in STRONG_DRAW
    has_any_draw = dv in STRONG_DRAW or dv in WEAK_DRAW

    # --- Monsters: always RAISE ---
    if mv in {"quads", "fullhouse"}:
        return "RAISE"
    if mv == "set" and has_strong_draw:
        return "RAISE"

    # --- Strong made hands (2P+): CALL ---
    if mv in {"two_pair", "set", "trips", "straight", "flush"}:
        return "CALL"

    # --- Top pair / overpair: CALL (data driven、v1 FOLD ルール削除) ---
    if mv in {"top_pair", "overpair"}:
        # exception: overpair × strong draw → RAISE for protection
        if mv == "overpair" and has_strong_draw:
            return "RAISE"
        return "CALL"

    # --- Second pair ---
    if mv == "second_pair":
        if has_any_draw:
            return "CALL"
        # opp_pol < 0.75 = merged → second_pair behind → FOLD
        if opp_polarization < 0.75:
            return "FOLD"
        return "CALL"

    # --- Weak pairs (underpair / third / low) ---
    if mv in WEAK_PAIR_LOW:
        if has_strong_draw:
            return "CALL"
        if bet_size in SMALL_BETS and board_family in DRY_BOARDS:
            return "CALL"
        return "FOLD"

    # --- AIR (no_made_hand, ace_high, king_high) ---
    if mv in AIR:
        # Strong draw → CALL anywhere
        if has_strong_draw:
            return "CALL"
        # Nut blocker on monotone → CALL (data: ace_high/king_high × monotone GTO calls)
        if board_family == "monotone" and mv in {"ace_high", "king_high"}:
            return "CALL"
        # Weak draw on dynamic dry → marginal call
        if dv in WEAK_DRAW and board_family in DRY_BOARDS and bet_size in SMALL_BETS:
            return "CALL"
        return "FOLD"

    # default: CALL (mv unknown)
    return "CALL"


if __name__ == "__main__":
    # quick smoke test
    tests = [
        ("top_pair", "no_draw", "dry_high", "overbet_185", "CALL"),
        ("top_pair", "no_draw", "low_dry", "overbet_185", "CALL"),
        ("ace_high", "no_draw", "monotone", "overbet_185", "CALL"),
        ("no_made_hand", "no_draw", "dry_high", "med_75p", "FOLD"),
        ("set", "no_draw", "dry_high", "med_75p", "CALL"),
        ("overpair", "flush_draw", "dynamic_2tone", "med_75p", "RAISE"),
        ("second_pair", "no_draw", "dynamic", "med_75p", "CALL"),  # opp_pol=0.711 → close
    ]
    for mv, dv, bf, bs, expected in tests:
        got = cash_3bp_turn_def_v1(mv, dv, bf, bs)
        flag = "✓" if got == expected else "✗"
        print(f"  {flag} ({mv},{dv},{bf},{bs}) → {got} (expected {expected})")
