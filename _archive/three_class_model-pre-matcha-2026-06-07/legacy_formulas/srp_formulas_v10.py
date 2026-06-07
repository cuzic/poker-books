#!/usr/bin/env python3
"""srp_formulas_v10.py — Cash SRP BB defense with opp range axis integration.

Domain: Cash 100bb SRP (single-raised pot), BB OOP defender.
Data source:
  - probe_priority_stats.json: B_flop (acc=71.7%, opp_pol=0.745),
    B_turn (acc=71.3%, opp_pol=0.794), B_river (acc=81.3%, opp_pol=0.959)
  - PROBE_PRIORITY_FINDINGS.md §6.1, §6.2, §6.4

Key findings integrated (PROBE_PRIORITY_FINDINGS.md §6.1–§6.2):
  - SRP flop: opp_polarization=0.745, opp_weak=0.606 — opener has ~60% air/weak on flop
  - SRP river: opp_polarization=0.959, opp_nut_pct=0.294 — river range is very polar
  - For AIR × dry_high × BDFD: opp_pol=0.745 baseline. If range is extra-polar (>0.95),
    more bluffs = can't profitably call. If merged (<0.70), fewer bluffs = CALL more.
  - top_pair × turn × overbet: opp_nut_pct drives call/fold decision
  - River bucket fallback: opp_polarization shifts bucket boundary thresholds

Design philosophy (暗算で回せる): simple if/elif/else, no ML, ~40 lines per function.
"""
from __future__ import annotations

from typing import Literal

Action = Literal["FOLD", "CALL", "RAISE"]

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}
DYNAMIC_RIVER = {"dynamic", "dynamic_2tone", "monotone"}
DRY_RIVER = {"dry_high", "low_dry"}
ABSOLUTELY_STRONG = {"straight", "flush", "trips"}


def flop_def_v9b_v10(
    mv: str,
    dv: str,
    board_family: str,
    bet_size: str,
    is_short: bool = False,
    opp_polarization: float = 0.745,
    opp_nut_pct: float = 0.031,
) -> Action:
    """Flop defense v9b + opp range axis (v10).

    Extends v9b with opp_polarization adjustment on the marginal AIR × dry × BDFD branch.

    Finding (PROBE_PRIORITY_FINDINGS §6.1): SRP flop opp_pol baseline=0.745.
      - opp_pol > 0.95 → opener range is very polar → bluff rate high → FOLD with air
      - opp_pol < 0.70 → opener range is merged/tight → fewer bluffs → CALL with BDFD
    """
    # --- AIR hands ---
    if mv in AIR:
        if dv == "no_draw":
            return "FOLD"
        if dv in WEAK_DRAW and board_family in DYNAMIC_BOARDS:
            return "FOLD"
        # Key opp_range axis branch (PROBE_PRIORITY_FINDINGS §6.1)
        if dv in WEAK_DRAW and board_family in DRY_BOARDS:
            if opp_polarization > 0.95:
                # Very polar → high bluff rate → too many bluffs → FOLD
                return "FOLD"
            if opp_polarization < 0.70:
                # Merged range → fewer bluffs → backdoor draw has implied odds → CALL
                return "CALL"
            # Default: deep stack FOLD (v9b rule 3)
            if not is_short:
                return "FOLD"

    # --- Weak pairs on dry/d2t boards ---
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and board_family in DRY_BOARDS | {"dynamic_2tone"}:
        if is_short:
            return "RAISE"
        return "FOLD"

    # --- Strong holdings ---
    if mv == "overpair":
        return "RAISE"

    return "CALL"


def turn_def_v10_v2(
    mv: str,
    dv: str,
    board_family: str,
    bet_size: str,
    opp_polarization: float = 0.794,
    opp_nut_pct: float = 0.058,
) -> Action:
    """Turn defense v10 + opp_nut_pct adjustment on top_pair × overbet branch.

    Finding (PROBE_PRIORITY_FINDINGS §6.2): SRP turn opp_pol=0.794, opp_nut_pct=0.058.
    For top_pair × overbet:
      - opp_nut_pct > 0.12 → heavy value → top_pair often dominated → FOLD
      - opp_nut_pct ≤ 0.12 → bluff-heavy overbet → CALL (standard v10 CALL)
    """
    if bet_size == "overbet_185":
        weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
        weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
        if weak_mv and weak_no_draw:
            return "FOLD"
        # opp_nut_pct axis on top_pair × dynamic × overbet (PROBE_PRIORITY_FINDINGS §6.2)
        if board_family in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw":
            if opp_nut_pct > 0.12:
                # Nut-heavy overbet → dominated → FOLD
                return "FOLD"
            # Low nut%, likely bluff-heavy → CALL
            return "CALL"
        if mv in AIR and dv in {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}:
            return "FOLD"
        return "CALL"

    # Non-overbet branches (unchanged from v10)
    if mv in AIR and board_family == "monotone":
        return "FOLD"
    if mv in AIR and dv in WEAK_DRAW and board_family != "low_dry":
        return "FOLD"
    if mv in AIR and dv == "no_draw":
        return "FOLD"
    if mv == "low_pair" and dv == "no_draw":
        return "FOLD"
    if mv == "third_pair" and dv == "no_draw" and board_family != "low_dry":
        return "FOLD"
    weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
    if board_family in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW:
        return "FOLD"
    if board_family in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p:
        return "FOLD"
    return "CALL"


def river_def_v15_v2(
    mv: str,
    dv: str,
    board_family: str,
    bet_size: str,
    equity_bucket: str,
    eq_percentile: float | None = None,
    opp_polarization: float = 0.959,
    opp_nut_pct: float = 0.294,
) -> Action:
    """River defense v15 + opp_polarization as bucket boundary weight.

    Finding (PROBE_PRIORITY_FINDINGS §6.1): SRP river opp_pol=0.959, opp_nut_pct=0.294.
    Bucket fallback: opp_polarization shifts the threshold for CALL vs FOLD on 'weak_hands'.
      - opp_pol > 0.95 → polar range → bluff rate ~50% → weak_hands CAN call small bets
      - opp_pol < 0.90 → merged → fewer bluffs → weak_hands should fold even small bets
    """
    is_dry = board_family in DRY_RIVER

    # allin: no raise option; quads/fullhouse must CALL (not RAISE)
    if bet_size == "allin":
        if mv in {"quads", "fullhouse"}:
            return "CALL"
        if mv in {"two_pair", "set", "trips", "straight", "flush"}:
            if equity_bucket in {"best_hands", "good_hands"}:
                return "CALL"
            if is_dry and mv in {"set", "trips", "straight", "flush"}:
                return "CALL"
            return "FOLD"
        if equity_bucket == "best_hands" and eq_percentile is not None and eq_percentile > 0.85:
            return "CALL"
        if board_family == "monotone" and mv == "flush":
            return "CALL"
        return "FOLD"

    # non-allin: quads/fullhouse can raise
    if mv in {"quads", "fullhouse"}:
        return "RAISE"

    if mv in ABSOLUTELY_STRONG:
        if equity_bucket == "trash_hands" and bet_size == "overbet":
            return "FOLD"
        return "CALL"

    if mv == "top_pair" and is_dry and bet_size in {"overbet", "med_100p"}:
        return "CALL"

    if equity_bucket == "best_hands":
        if eq_percentile is not None and eq_percentile > 0.96:
            return "RAISE"
        return "CALL"
    if equity_bucket == "good_hands":
        return "CALL"

    if equity_bucket == "weak_hands":
        if bet_size == "overbet":
            if board_family in DYNAMIC_RIVER and mv == "two_pair":
                return "CALL"
            return "FOLD"
        if bet_size == "med_100p":
            return "FOLD"
        # opp_polarization axis on small bet × weak_hands (PROBE_PRIORITY_FINDINGS §6.1)
        if opp_polarization < 0.90:
            # Merged range → fewer bluffs → weak hands can't profitably call
            return "FOLD"
        return "CALL"

    return "FOLD"
