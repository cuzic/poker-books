#!/usr/bin/env python3
"""cash_3bp_turn_v1.py — Cash 100bb 3BP turn, BB OOP defense (v1).

Domain: Cash/MTT 100bb 3BP (3-bet pot), BB OOP defender on turn.
Data source:
  - probe_phase5_stats.json: P5_A_cash_3bp_turn acc=66.3%, opp_pol=0.711, opp_weak=0.424
  - probe_phase5_stats.json: P5_A_mtt_3bp_turn  acc=66.5%, opp_pol=0.714, opp_weak=0.444
  - PROBE_PRIORITY_FINDINGS.md §5 Tier B, §6.1

Key findings (PROBE_PRIORITY_FINDINGS §5 Tier B, §6.1):
  - Cash and MTT 100bb 3BP turn are virtually identical (acc 66.3% vs 66.5%,
    opp_pol 0.711 vs 0.714). This formula serves BOTH.
  - opp_pol=0.711 on turn: LOWER than SRP turn (0.794). 3BP range has more mid-strength
    hands (TT, JJ, QQ, AQ-type) that didn't fold to 3-bet → merged feel on turn.
  - opp_weak=0.424: much lower than SRP flop (0.606). 3-bettor's range survived the flop;
    more showdown-worthy holdings. → BB should fold more liberally.
  - bet_size context: cbet ~R10 (small), barrel ~R24 (2/3 pot).
    Small cbet → IP protected strong range → CALL wider on draws/medium hands.
    Barrel R24 → commitment pressure → fold weak hands.

Design: mv-based + opp_polarization correction, bet_size aware.
  Rule 1: AIR → always FOLD (turn range merged, fewer bluffs than SRP)
  Rule 2: Weak pairs + no draw → FOLD
  Rule 3: opp_pol < 0.75 (merged) + medium hand + no draw → FOLD more
  Rule 4: Strong hands / combo draws → CALL (or RAISE with nuts)
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

# 3BP turn bet sizes (approximate from probe: cbet=R10, barrel=R24)
SMALL_BET = "small_cbet"   # ~R10, ~33%
BARREL = "barrel"          # ~R24, ~65%
OVERBET = "overbet"        # R40+


def cash_3bp_turn_def_v1(
    mv: str,
    dv: str,
    board_family: str,
    bet_size: str = "barrel",
    opp_polarization: float = 0.711,
    opp_weak: float = 0.424,
) -> Action:
    """Cash/MTT 100bb 3BP turn BB OOP defense v1.

    Args:
        mv: made-value category.
        dv: draw-value category.
        board_family: board texture family.
        bet_size: "small_cbet" (~R10/33%) / "barrel" (~R24/65%) / "overbet" (R40+).
        opp_polarization: 3-bettor's turn range polarity (default N_cash_3bp_turn probe).
        opp_weak: fraction of 3-bettor's range that is weak/air (default from probe).
    """
    # --- Nuts: always raise ---
    if mv in {"quads", "fullhouse"}:
        return "RAISE"
    if mv == "set" and dv != "no_draw":
        return "RAISE"

    # --- AIR: always fold on turn (finding: opp_weak=0.424 → fewer bluffs → no call) ---
    if mv in AIR:
        if dv in STRONG_DRAW and board_family in DYNAMIC_BOARDS:
            return "CALL"
        return "FOLD"

    # --- Overbet: only very strong hands survive ---
    if bet_size == OVERBET:
        if mv in STRONG_MADE or dv in STRONG_DRAW:
            return "CALL"
        return "FOLD"

    # --- Weak pairs: fold unless draw or vs small cbet ---
    if mv in WEAK_PAIR_LOW:
        if dv in STRONG_DRAW:
            return "CALL"
        if bet_size == SMALL_BET and board_family in DRY_BOARDS:
            return "CALL"  # small cbet on dry board → often protection, not value
        return "FOLD"

    # --- Second pair ---
    if mv == "second_pair":
        if dv in STRONG_DRAW:
            return "CALL"
        if dv in WEAK_DRAW and board_family in DYNAMIC_BOARDS:
            return "CALL"
        # opp_pol < 0.75 = merged 3BP range → second pair often behind → FOLD
        if opp_polarization < 0.75:
            return "FOLD"
        return "CALL"

    # --- Top pair ---
    if mv == "top_pair":
        if dv in STRONG_DRAW:
            return "RAISE"
        if bet_size == OVERBET and dv == "no_draw":
            return "FOLD"  # overbet + top pair + no redraw → dominated
        return "CALL"

    # --- Overpair ---
    if mv == "overpair":
        if dv in STRONG_DRAW:
            return "RAISE"
        return "CALL"

    # --- Strong made / combo draw ---
    if mv in STRONG_MADE or dv in STRONG_DRAW:
        return "CALL"

    return "FOLD"
