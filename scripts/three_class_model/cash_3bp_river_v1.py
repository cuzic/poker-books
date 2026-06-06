#!/usr/bin/env python3
"""cash_3bp_river_v1.py — Cash 100bb 3BP river, BB OOP defense (v1).

Domain: Cash 100bb 3BP (3-bet pot), BB OOP defender on river.
Data source:
  - probe_priority_stats.json:  N_cash_3bp_river acc=79.7%, opp_pol=0.914, opp_nut=0.194
  - probe_phase5_stats.json:    P5_B_3bp_river_extra acc=78.0%, opp_pol=0.900, opp_nut=0.159
  - probe_phase5_stats.json:    P5_A_mtt_3bp_river  acc=77.1%, opp_pol=0.870, opp_nut=0.181
  - PROBE_PRIORITY_FINDINGS.md §5 Tier B, §6.1

Key findings (PROBE_PRIORITY_FINDINGS §5, §6.1):
  - 3BP river opp_pol=0.86-0.91, opp_nut_pct=0.14-0.19 (SRP: 0.96, 0.29).
    → 3BP river is LESS polar than SRP river. 3-bettor has more medium-strength hands.
  - Per-family nut concentration is board-specific:
    * dyn_T97 opp_straight=70% (straight complete → 70% of opp range IS straight)
    * mono_Js opp_flush=28% (3BP: lower than SRP 44% — 3BP range has fewer flush combos)
    * pair_KK2 opp_fullhouse=0% in 3BP (vs SRP 16%) — 3BP tightens out full house combos
  - bet_size R58 (near-allin): 3BP river allin is structurally shove-or-fold.
    → only premium hands call shoves.
  - acc 77-80%: similar accuracy to SRP river (81.3%) — v15 logic works with nut_class tweak.

Design: bucket × bet_size + per-board nut_class correction.
  Core: inherit v15 bucket logic.
  Correction 1: nut_class-based threshold — if you beat opp nut class, CALL; else FOLD.
  Correction 2: near-allin (R58) → shove-or-fold: only strong_made vs nut_class survive.
  Correction 3: 3BP-specific overfold: opp_nut_pct < 0.20 on non-dynamic boards → fold more.
"""
from __future__ import annotations

from typing import Literal

Action = Literal["FOLD", "CALL", "RAISE"]

# Board families where river is draw-complete (completed straight / flush heavily in range)
DRY_RIVER = {"dry_high", "low_dry"}
DYNAMIC_RIVER = {"dynamic", "dynamic_2tone", "monotone"}
ABSOLUTELY_STRONG = {"straight", "flush", "trips", "set", "two_pair"}

# Per-family nut class and opp nut % from probe (PROBE_PRIORITY_FINDINGS §6.1)
# Used to determine whether hero hand beats opp nut class.
# Format: {board_family: (nut_class_name, opp_nut_pct_3bp)}
FAMILY_NUT_MAP: dict[str, tuple[str, float]] = {
    "dyn_T97":   ("straight", 0.705),   # dyn_T97 → straight heavy; 3BP 70.5%
    "dynamic":   ("straight", 0.187),   # generic dynamic → straight possible
    "dynamic_2tone": ("flush", 0.000),  # d2t → flush draw boards; 3BP flush % low
    "mono_Js":   ("flush",    0.275),   # mono → flush nut; 3BP 27.5% (SRP 44%)
    "dry_high":  ("set",      0.064),   # dry high → set/trips nut; 3BP 6.4%
    "low_dry":   ("set",      0.000),   # low dry → set nut; low nut concentration
    "pair_KK2":  ("fullhouse",0.122),   # paired → FH nut; 3BP 12.2% (SRP 16%)
}

# Hand categories that beat each nut class
BEATS_NUT: dict[str, frozenset[str]] = {
    "straight": frozenset({"flush", "fullhouse", "quads", "straight"}),
    "flush":    frozenset({"fullhouse", "quads", "flush"}),
    "set":      frozenset({"fullhouse", "quads", "straight", "flush", "set", "two_pair"}),
    "fullhouse": frozenset({"quads", "fullhouse"}),
    "trips":    frozenset({"fullhouse", "quads", "straight", "flush", "set", "trips", "two_pair"}),
}


def _hero_beats_opp_nut(mv: str, board_family: str) -> bool:
    """True if hero's made-hand class beats (or ties) the board's nut class."""
    nut_class = FAMILY_NUT_MAP.get(board_family, ("set", 0.10))[0]
    return mv in BEATS_NUT.get(nut_class, frozenset())


def cash_3bp_river_def_v1(
    mv: str,
    dv: str,
    board_family: str,
    bet_size: str,
    equity_bucket: str,
    eq_percentile: float | None = None,
    opp_polarization: float = 0.900,
    opp_nut_pct: float = 0.180,
) -> Action:
    """Cash 100bb 3BP river BB OOP defense v1.

    Args:
        mv: made-value category (mv_cat).
        dv: draw-value category (dv_cat; river has no live draws, but may still inform).
        board_family: board texture family.
        bet_size: "allin"/"near_allin" (R58) / "overbet" (R16) / "med_100p" (R13) /
                  "med_75p" (R7-R8) / "small_30p" (R4).
        equity_bucket: "best_hands" / "good_hands" / "weak_hands" / "trash_hands".
        eq_percentile: hero equity percentile vs entire range (0-1); None if unavailable.
        opp_polarization: 3-bettor's river range polarity (default from 3BP probe mean).
        opp_nut_pct: fraction of 3-bettor's range at nut class (default from 3BP probe mean).
    """
    is_dry = board_family in DRY_RIVER
    hero_beats_nut = _hero_beats_opp_nut(mv, board_family)

    # --- Absolute monsters: always raise (PROBE_PRIORITY_FINDINGS §6.1: paired_KK2 FH 0% in 3BP) ---
    if mv in {"quads", "fullhouse"}:
        return "RAISE"

    # --- Near-allin / allin bet: shove-or-fold structure ---
    if bet_size in {"allin", "near_allin"}:
        # Hero beats opp nut class → call shove (PROBE_PRIORITY_FINDINGS §6.1)
        if hero_beats_nut:
            return "CALL"
        # strong made hand + good equity position → call
        if mv in {"set", "trips", "straight", "flush"} and equity_bucket in {"best_hands", "good_hands"}:
            return "CALL"
        # two_pair: only call if high equity percentile (3BP nut_pct 14-19% is significant)
        if mv == "two_pair" and equity_bucket == "best_hands":
            return "CALL"
        return "FOLD"

    # --- Strong made hands (non-allin): always call ---
    if mv in ABSOLUTELY_STRONG:
        if equity_bucket == "trash_hands" and bet_size == "overbet":
            return "FOLD"  # worst straight/flush on board (e.g., board shows AKQJT)
        return "CALL"

    # --- Top pair on dry board vs large bet: call (same as v15) ---
    if mv == "top_pair" and is_dry and bet_size in {"overbet", "med_100p"}:
        return "CALL"

    # --- Bucket-based fallback (3BP adjusted) ---
    if equity_bucket == "best_hands":
        if eq_percentile is not None and eq_percentile > 0.96:
            return "RAISE"
        return "CALL"

    if equity_bucket == "good_hands":
        return "CALL"

    if equity_bucket == "weak_hands":
        if bet_size == "overbet":
            # 3BP correction: opp_nut_pct < 0.20 on dry → fewer bluffs → fold more
            if is_dry and opp_nut_pct < 0.20 and mv not in {"two_pair"}:
                return "FOLD"
            if board_family in DYNAMIC_RIVER and mv == "two_pair":
                return "CALL"
            return "FOLD"
        if bet_size == "med_100p":
            return "FOLD"
        # Small/medium bet: 3BP opp_pol=0.90 (lower than SRP 0.96) → fewer bluffs → fold more
        if opp_polarization < 0.90:
            return "FOLD"
        return "CALL"

    # trash_hands: always fold
    return "FOLD"
