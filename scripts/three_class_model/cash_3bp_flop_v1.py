#!/usr/bin/env python3
"""cash_3bp_flop_v1.py — Cash 100bb 3BP flop, BB OOP defense (v1).

Domain: Cash 100bb 3BP (3-bet pot), BB OOP defender vs IP 3-bettor's cbet.
Data source:
  - probe_priority_stats.json: N_cash_3bp_flop acc=66.6%, opp_pol=0.726, opp_weak=0.591
  - probe_priority_stats.json: B_flop (SRP baseline) acc=71.7%, opp_pol=0.745
  - PROBE_PRIORITY_FINDINGS.md §5 (Tier D), §6.1

Key findings (PROBE_PRIORITY_FINDINGS §5, §6.1):
  - 3BP flop acc=66.6% vs SRP 71.7% — SRP v9b is a reasonable but imperfect proxy.
  - opp_pol=0.726 (3BP) vs 0.745 (SRP): 3BP range is slightly LESS polar → fewer bluffs.
  - opp_weak=0.591 (3BP) vs 0.606 (SRP): similar air % despite tighter preflop range.
  - Key 3BP structural difference: BB OOP 3-bettor (VALUE-HEAVY range) → flop hit rate
    is LOWER (preflop range is polar: AA/KK/AK + bluffs). Air combos MISS flop more.
  - Therefore: AIR × dry × no_draw → FOLD more aggressively than SRP.
  - Also: fewer middling hands (no 87s type) → second_pair FOLD more often.

Design: SRP v9b base + 3BP context correction.
  Correction 1: AIR × dry × BDFD → always FOLD (no is_short exception, pot already big)
  Correction 2: second_pair × no_draw × dry → FOLD (3BP range punishes medium pairs)
"""
from __future__ import annotations

from typing import Literal

Action = Literal["FOLD", "CALL", "RAISE"]

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}


def cash_3bp_flop_def_v1(
    mv: str,
    dv: str,
    board_family: str,
    bet_size: str = "other",
    is_short: bool = False,
    opp_polarization: float = 0.726,
) -> Action:
    """Cash 100bb 3BP flop BB OOP defense v1.

    Args:
        mv: made-value category (mv_cat).
        dv: draw-value category (dv_cat).
        board_family: board texture family.
        bet_size: "small_33" / "other" (3BP flop cbets are typically ~33%).
        is_short: not used in 3BP (pot too large for short-stack CR logic).
        opp_polarization: opener's range polarity (default from N_cash_3bp_flop probe).
    """
    # --- AIR hands: fold more aggressively vs 3BP (PROBE_PRIORITY_FINDINGS §5 Tier D) ---
    if mv in AIR:
        if dv == "no_draw":
            return "FOLD"
        if dv in WEAK_DRAW and board_family in DYNAMIC_BOARDS:
            return "FOLD"
        # 3BP correction: dry × BDFD → always FOLD (no is_short exception unlike SRP)
        # 3BP pot is 7-9 BB vs SRP 3-4 BB; overfold risk lower, fold equity higher
        if dv in WEAK_DRAW and board_family in DRY_BOARDS:
            return "FOLD"

    # --- Weak pairs: more aggressive fold in 3BP context ---
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and board_family in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"

    # 3BP correction: second_pair × no_draw × dry → FOLD
    # (opp 3BP range has AA/KK/AK that dominate top-pair → second_pair has little showdown value)
    if mv == "second_pair" and dv == "no_draw" and board_family in DRY_BOARDS:
        return "FOLD"

    # --- Strong holdings ---
    if mv == "overpair":
        return "RAISE"
    if mv in {"set", "two_pair", "top_pair"} and dv != "no_draw":
        return "RAISE"

    return "CALL"
