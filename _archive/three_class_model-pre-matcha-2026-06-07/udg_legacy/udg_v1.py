#!/usr/bin/env python3
"""udg_v1.py — Universal Defense Grid (3-layer framework for postflop defense)

Reduces total memorization cost by ~70% vs the 11 separate formula approach.

Layer 1: SHARED CONCEPTS (3 tier functions, used by all scenarios)
  - board_polar_tier()    POLAR / MERGED / MID
  - hand_strength_tier()  NUT_MADE / STRONG / TWO_PAIR / PAIR / MID_PAIR / DRAW / AIR
  - bet_size_tier()       SMALL / MED / BIG / ALLIN

Layer 2: UNIVERSAL DEFENSE RULE (7 rules, applies to all scenarios)
  - apply_universal_rule(hand_tier, board_tier, bet_tier, street, dv)

Layer 3: SCENARIO MODIFIERS (small override layer per scenario type)
  - 3bp_modifier, 4bp_modifier
  - cr_defense_modifier, donk_defense_modifier
  - opener_co_hj_modifier
  - mtt_depth_modifier

Master function: udg_defense(row) applies all 3 layers.

Acc vs専用 v1 公式: trade-off は huge_loss で見るべき (acc は不本意な FOLD で下がる)。
"""
from __future__ import annotations

from typing import Literal

Action = Literal["FOLD", "CALL", "RAISE"]


# ════════════════════ Layer 1: SHARED CONCEPTS ════════════════════

POLAR_FAMILIES = {"dynamic", "dynamic_2tone", "monotone"}
MERGED_FAMILIES = {"dry_high", "low_dry", "paired"}

NUT_MADE_MV = {"fullhouse", "quads", "straight_flush"}
STRONG_MV = {"set", "trips", "straight", "flush"}
TWO_PAIR_MV = {"two_pair"}
PAIR_MV = {"top_pair", "overpair"}
MID_PAIR_MV = {"second_pair", "third_pair", "underpair", "low_pair"}
AIR_MV = {"no_made_hand", "ace_high", "king_high", "queen_high", "jack_high", "ten_high"}

STRONG_DRAW_DV = {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}
WEAK_DRAW_DV = {"twocards_bdfd", "onecard_bdfd", "gutshot"}


def board_polar_tier(board_family: str) -> str:
    """POLAR (相手に draw/nut 完成可能) / MERGED (相手大半 air) / MID."""
    if board_family in POLAR_FAMILIES:
        return "POLAR"
    if board_family in MERGED_FAMILIES:
        return "MERGED"
    return "MID"


def hand_strength_tier(mv: str) -> str:
    """6 階層に圧縮."""
    if mv in NUT_MADE_MV: return "NUT_MADE"
    if mv in STRONG_MV: return "STRONG"
    if mv in TWO_PAIR_MV: return "TWO_PAIR"
    if mv in PAIR_MV: return "PAIR"
    if mv in MID_PAIR_MV: return "MID_PAIR"
    if mv in AIR_MV: return "AIR"
    return "AIR"  # default unknown → AIR


def bet_size_tier(bet_size: str) -> str:
    """4 階層に圧縮."""
    if bet_size in {"allin"}: return "ALLIN"
    if bet_size in {"overbet", "overbet_185"}: return "BIG"
    if bet_size in {"med_75p", "med_100p"}: return "MED"
    if bet_size in {"small_33", "small_30p"}: return "SMALL"
    return "MED"  # default


def determine_street(board_str: str) -> str:
    """3 cards = flop, 4 = turn, 5 = river."""
    n = len(board_str) // 2 if board_str else 0
    if n == 5: return "river"
    if n == 4: return "turn"
    return "flop"


# ════════════════════ Layer 2: UNIVERSAL RULE (7 rules) ════════════════════

def apply_universal_rule(
    hand_tier: str,
    board_tier: str,
    bet_tier: str,
    street: str,
    mv: str,
    dv: str,
) -> Action:
    """7-rule core defense logic.

    Rules (top-down):
      1. NUT_MADE: river=CALL, else=RAISE
      2. STRONG: river=CALL, POLAR=slowdown CALL, else=RAISE
      3. TWO_PAIR: river=CALL, POLAR=slowdown CALL, else=RAISE
      4. PAIR: BIG/ALLIN × POLAR → FOLD (dominated), else CALL
      5. MID_PAIR: strong_draw=CALL, else=FOLD (modifiers may widen)
      6. DRAW (strong): CALL
      7. AIR: ace_high × MERGED=CALL (blocker), weak_draw × MERGED=CALL, else FOLD
    """
    is_river = street == "river"
    has_strong_draw = dv in STRONG_DRAW_DV
    has_weak_draw = dv in WEAK_DRAW_DV
    is_big_bet = bet_tier in {"BIG", "ALLIN"}

    # Rule 1: NUT_MADE
    if hand_tier == "NUT_MADE":
        return "CALL" if is_river else "RAISE"

    # Rule 2: STRONG made
    if hand_tier == "STRONG":
        if is_river:
            return "CALL"
        if board_tier == "POLAR":
            return "CALL"  # slowdown vs nut potential
        return "RAISE"

    # Rule 3: TWO_PAIR
    if hand_tier == "TWO_PAIR":
        if is_river:
            return "CALL"
        if board_tier == "POLAR":
            return "CALL"
        return "RAISE"

    # Rule 4: PAIR (TP/OP)
    if hand_tier == "PAIR":
        if is_big_bet and board_tier == "POLAR":
            return "FOLD"  # PAIR vs polar overbet → dominated
        return "CALL"

    # Rule 5: MID_PAIR
    if hand_tier == "MID_PAIR":
        if has_strong_draw:
            return "CALL"
        return "FOLD"  # default tight (modifiers widen for 4BP)

    # Rule 6/7: AIR + draws
    if has_strong_draw:
        return "CALL"
    if has_weak_draw and board_tier == "MERGED":
        return "CALL"

    # ace_high blocker on MERGED → CALL
    if mv == "ace_high" and board_tier == "MERGED":
        return "CALL"

    return "FOLD"


# ════════════════════ Layer 3: MODIFIERS ════════════════════

def apply_4bp_modifier(base: Action, hand_tier: str, board_tier: str, mv: str, dv: str,
                        street: str, board_family: str = "") -> Action:
    """4BP: widen MID_PAIR + AIR blocker rules + non-river RAISE for protection.

    4BP の特徴:
      - opp range tight (QQ+/AK)、flop/turn 40-60% air
      - SPR<1.5 → flop/turn は protection RAISE が GTO
      - mono board のみ slowdown CALL (flush 危険)

    Rules:
      1. MID_PAIR × river → CALL
      2. MID_PAIR × non-river × non-mono → RAISE (protection)
      3. MID_PAIR × monotone → CALL (slowdown)
      4. PAIR × non-river × non-mono → upgrade CALL→RAISE (protection)
      5. TWO_PAIR/STRONG × non-river × monotone → CALL (slowdown)
      6. ace_high × MERGED/MID → CALL (blocker)
    """
    is_river = street == "river"
    is_mono = board_family == "monotone"

    # MID_PAIR
    if hand_tier == "MID_PAIR":
        if is_river or is_mono:
            return "CALL"
        return "RAISE"

    # PAIR upgrade: non-river non-mono → RAISE
    if hand_tier == "PAIR" and not is_river and not is_mono and base == "CALL":
        return "RAISE"

    # TWO_PAIR/STRONG slowdown on monotone
    if hand_tier in {"TWO_PAIR", "STRONG"} and not is_river and is_mono:
        return "CALL"

    # ace_high blocker
    if mv == "ace_high" and board_tier in {"MERGED", "MID"}:
        return "CALL"

    return base


def apply_3bp_modifier(base: Action, hand_tier: str, board_tier: str, bet_tier: str,
                       equity_bucket: str, mv: str, dv: str, street: str) -> Action:
    """3BP: tighten MID_PAIR + river bucket fallback.

    1. 3BP river ALLIN: bucket-based decision
       - best/good_hands × STRONG/TWO_PAIR → CALL
       - else → FOLD (default)
    2. MID_PAIR × no_draw × dry → keep FOLD (base does this)
    3. PAIR × BIG bet × POLAR → keep FOLD (base does this)
    """
    is_river = street == "river"
    # 3BP river allin special: bucket override
    if is_river and bet_tier == "ALLIN":
        if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR"}:
            if equity_bucket in {"best_hands", "good_hands"}:
                return "CALL"
            if board_tier == "MERGED" and hand_tier == "STRONG":
                return "CALL"  # set on dry → CALL
            return "FOLD"
        if hand_tier == "PAIR" and board_tier == "MERGED":
            return "CALL"  # TP on dry → CALL allin (v15 finding)
    return base


def apply_cr_defense_modifier(base: Action, hand_tier: str, board_tier: str, mv: str, dv: str) -> Action:
    """CR defense: opp is VALUE-HEAVY (opp_strong 46-65%). Tighten fold threshold.

    1. PAIR on POLAR/MID × any bet → FOLD (opp likely has 2P+ in CR range)
    2. MID_PAIR × any → FOLD
    3. AIR + weak_draw on POLAR → FOLD
    """
    if hand_tier == "PAIR" and board_tier in {"POLAR"}:
        return "FOLD"
    if hand_tier == "MID_PAIR":
        return "FOLD"  # tighter than base for CR
    return base


def apply_donk_defense_modifier(base: Action, hand_tier: str, board_tier: str, mv: str, dv: str) -> Action:
    """Donk defense: opp is AIR-HEAVY (opp_weak 54-61%). Widen call threshold.

    1. PAIR → CALL always (donker has lots of air)
    2. MID_PAIR + any_draw → CALL
    3. AIR + weak_draw × any board → CALL (donker bluffs widely)
    """
    if hand_tier == "PAIR":
        return "CALL"
    if hand_tier == "MID_PAIR" and (dv in STRONG_DRAW_DV or dv in WEAK_DRAW_DV):
        return "CALL"
    if hand_tier == "AIR" and dv in WEAK_DRAW_DV:
        return "CALL"
    return base


def apply_opener_co_hj_modifier(base: Action, hand_tier: str, bet_tier: str, board_tier: str, street: str) -> Action:
    """CO/HJ open river: tighten bluff catchers (opp_nut_pct 22% vs BTN 29%).

    Only river-specific. CO/HJ value-heavier than BTN → fold more PAIR vs BIG bet.
    """
    if street != "river": return base
    if hand_tier == "PAIR" and bet_tier in {"BIG", "ALLIN"} and board_tier == "POLAR":
        return "FOLD"
    return base


def apply_mtt_depth_modifier(base: Action, hand_tier: str, board_tier: str, bet_tier: str,
                              street: str, depth_bb: int) -> Action:
    """MTT depth: short=shove/fold, deep=wider call.

    Short (≤25bb): pair → CALL (committed), AIR → FOLD (no implied)
    Deep (≥200bb): widen MID_PAIR on flop/turn (more implied odds)
    """
    if depth_bb <= 25:
        if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR", "PAIR"}:
            return "CALL"
    elif depth_bb >= 200:
        if hand_tier == "MID_PAIR" and street in {"flop", "turn"}:
            return "CALL"
    return base


# ════════════════════ Master function: UDG defense ════════════════════

def udg_defense(r, scenario_meta: dict | None = None) -> Action:
    """Master defense function: applies all 3 layers.

    scenario_meta: optional dict to override scenario detection. Keys:
        - pot_type: "SRP" / "3BP" / "4BP"
        - action_context: "vs_cbet" (default) / "vs_CR" / "vs_donk"
        - opener: "BTN" (default) / "CO" / "HJ"
        - depth_bb: int (default 100)
    """
    # Extract row fields
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]
    bs = r.get("ip_bet_size", "med_75p")
    eb = r.get("equity_bucket", "trash_hands")
    board_str = r.get("board_str", "")

    # Layer 1: classify
    hand_tier = hand_strength_tier(mv)
    board_tier = board_polar_tier(bf)
    bet_tier = bet_size_tier(bs)
    street = determine_street(board_str)

    # Layer 2: universal rule
    action = apply_universal_rule(hand_tier, board_tier, bet_tier, street, mv, dv)

    # Layer 3: apply modifiers based on scenario
    meta = scenario_meta or _infer_meta(r)
    pot_type = meta.get("pot_type", "SRP")
    action_context = meta.get("action_context", "vs_cbet")
    opener = meta.get("opener", "BTN")
    depth_bb = meta.get("depth_bb", 100)

    if pot_type == "4BP":
        action = apply_4bp_modifier(action, hand_tier, board_tier, mv, dv, street, bf)
    elif pot_type == "3BP":
        action = apply_3bp_modifier(action, hand_tier, board_tier, bet_tier, eb, mv, dv, street)

    if action_context == "vs_CR":
        action = apply_cr_defense_modifier(action, hand_tier, board_tier, mv, dv)
    elif action_context == "vs_donk":
        action = apply_donk_defense_modifier(action, hand_tier, board_tier, mv, dv)

    if opener in {"CO", "HJ"}:
        action = apply_opener_co_hj_modifier(action, hand_tier, bet_tier, board_tier, street)

    if depth_bb != 100:
        action = apply_mtt_depth_modifier(action, hand_tier, board_tier, bet_tier, street, depth_bb)

    return action


def _infer_meta(r) -> dict:
    """scenario_id から pot_type / context / opener / depth を推測."""
    sid = str(r.get("scenario_id", ""))
    meta: dict = {"pot_type": "SRP", "action_context": "vs_cbet", "opener": "BTN", "depth_bb": 100}

    # pot type
    if "4bp" in sid.lower(): meta["pot_type"] = "4BP"
    elif "3bp" in sid.lower(): meta["pot_type"] = "3BP"

    # action context
    if "cr_def" in sid.lower(): meta["action_context"] = "vs_CR"
    elif "donk_def" in sid.lower(): meta["action_context"] = "vs_donk"
    elif "turn_cr" in sid.lower(): meta["action_context"] = "vs_CR"
    elif "turn_donk" in sid.lower(): meta["action_context"] = "vs_donk"
    elif "river_donk" in sid.lower(): meta["action_context"] = "vs_donk"

    # opener
    if "hj_open" in sid.lower(): meta["opener"] = "HJ"
    elif "co_open" in sid.lower(): meta["opener"] = "CO"

    # depth
    if "mtt25" in sid.lower(): meta["depth_bb"] = 25
    elif "mtt200" in sid.lower(): meta["depth_bb"] = 200

    return meta


# ════════════════════ Audit ════════════════════

if __name__ == "__main__":
    import pandas as pd
    import statistics

    print("=== UDG v1 audit ===\n")
    df = pd.read_csv("scripts/three_class_model/dataset_unified_v2.csv", low_memory=False)
    print(f"Loaded {len(df):,} rows\n")

    df["udg_action"] = df.apply(udg_defense, axis=1)
    df["udg_correct"] = (df["udg_action"] == df["best_action"])

    def loss(r):
        a = r["udg_action"]
        ev = {"FOLD": r["ev_fold"], "CALL": r["ev_call"], "RAISE": r["ev_raise"]}.get(a)
        if pd.notna(ev): return r["best_ev"] - ev
        return r["ev_gap"]
    df["udg_loss"] = df.apply(loss, axis=1)

    # Per-scenario
    print(f"{'scenario_id':30s}  {'n':>6s}  {'acc':>6s}  {'huge':>6s}  {'v1_huge':>7s}  {'verdict':>10s}")
    print("-" * 85)
    scenario_summary = []
    for sid, sub in df.groupby("scenario_id"):
        acc = sub["udg_correct"].mean() * 100
        huge_rows = sub[sub["udg_loss"] > 0.5]
        huge = huge_rows["udg_loss"].mean() if len(huge_rows) > 0 else 0
        old_rows = sub[sub["formula_loss"] > 0.5]
        old_huge = old_rows["formula_loss"].mean() if len(old_rows) > 0 else 0
        verdict = "✓" if huge <= old_huge * 1.1 else ("△" if huge <= old_huge * 1.3 else "✗")
        if old_huge == 0: verdict = "—"
        print(f"{sid:30s}  {len(sub):>6d}  {acc:>5.1f}%  {huge:>6.2f}  {old_huge:>7.2f}  {verdict:>10s}")
        scenario_summary.append({
            "sid": sid, "n": len(sub), "acc": acc,
            "udg_huge": huge, "v1_huge": old_huge
        })

    # Overall
    print()
    huge_rows = df[df["udg_loss"] > 0.5]
    overall_huge = huge_rows["udg_loss"].mean()
    overall_acc = df["udg_correct"].mean() * 100
    valid_v1 = df[df["formula_loss"].notna() & (df["formula_loss"] > 0.5)]
    overall_v1_huge = valid_v1["formula_loss"].mean()
    print(f"OVERALL: acc={overall_acc:.1f}%  udg_huge={overall_huge:.2f}  v1_huge={overall_v1_huge:.2f}")
