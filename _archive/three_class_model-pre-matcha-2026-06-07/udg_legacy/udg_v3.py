#!/usr/bin/env python3
"""udg_v3.py — UDG v3: blocker_tier + hero_role + HIGH SPR aggression + mono slowdown

v2 からの変更 (Section A 既存データ分析の発見を反映):
  1. blocker_tier 新設 — Ace blocker on mono / trips-blocker on paired を捕捉
     (Section A3: mono × A blocker GTO CALL +27pp、paired × K blocker +42pp)
  2. hero_role tier 新設 — IP defender (R1 等) で wider call の傾向
     (Section A2: BTN IP river allin で weak_hands を FOLD すると 600+ row 誤判定)
  3. HIGH SPR + strong_made の aggression (Section A1: MTT200 で slowplay 取りこぼし 135 cases)
  4. monotone × non-river の slowdown rule (Section A4: mono_Qh huge 7.08 → 改善目標)

期待 v2 → v3:
  - overall huge_loss: 5.94 BB → ~4 BB (-32%)
  - blocker 関連の改善 (R1_past の 6.3 BB → 3 BB 目標)
  - 4BP mono の改善 (7 BB → 3 BB 目標)
"""
from __future__ import annotations
from collections import Counter
from typing import Literal

Action = Literal["FOLD", "CALL", "RAISE"]

# ════════════════════ Layer 1: 既存 tier 関数 (UDG v2 から流用) ════════════════════

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


def board_polar_tier(bf: str) -> str:
    if bf in POLAR_FAMILIES: return "POLAR"
    if bf in MERGED_FAMILIES: return "MERGED"
    return "MID"


def hand_strength_tier(mv: str) -> str:
    if mv in NUT_MADE_MV: return "NUT_MADE"
    if mv in STRONG_MV: return "STRONG"
    if mv in TWO_PAIR_MV: return "TWO_PAIR"
    if mv in PAIR_MV: return "PAIR"
    if mv in MID_PAIR_MV: return "MID_PAIR"
    return "AIR"


def bet_size_tier(bs: str) -> str:
    if bs == "allin": return "ALLIN"
    if bs in {"overbet", "overbet_185"}: return "BIG"
    if bs in {"med_75p", "med_100p"}: return "MED"
    if bs in {"small_33", "small_30p"}: return "SMALL"
    return "MED"


def determine_street(board_str: str) -> str:
    n = len(board_str) // 2 if board_str else 0
    if n == 5: return "river"
    if n == 4: return "turn"
    return "flop"


_SPR_TIER_BASE = {
    ("SRP", "flop"): "HIGH",
    ("SRP", "turn"): "MID",
    ("SRP", "river"): "MID",
    ("3BP", "flop"): "MID",
    ("3BP", "turn"): "LOW",
    ("3BP", "river"): "SHALLOW",
    ("4BP", "flop"): "LOW",
    ("4BP", "turn"): "SHALLOW",
    ("4BP", "river"): "SHALLOW",
}


def spr_tier(pot_type: str, street: str, depth_bb: int = 100) -> str:
    base = _SPR_TIER_BASE.get((pot_type, street), "MID")
    if depth_bb <= 25:
        return {"HIGH": "MID", "MID": "LOW", "LOW": "SHALLOW",
                 "SHALLOW": "SHALLOW"}.get(base, "SHALLOW")
    if depth_bb >= 200:
        return {"SHALLOW": "LOW", "LOW": "MID", "MID": "HIGH",
                 "HIGH": "HIGH"}.get(base, base)
    return base


def equity_aware_tier(hand_tier: str, eb: str) -> str:
    eb = eb or "good_hands"
    if eb == "best_hands": return "HIGH"
    if eb == "good_hands":
        return "HIGH" if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR", "PAIR"} else "MID"
    if eb == "weak_hands":
        if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR"}: return "MID"
        return "LOW"
    if eb == "trash_hands": return "VERY_LOW"
    if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR"}: return "HIGH"
    if hand_tier == "PAIR": return "MID"
    return "VERY_LOW" if hand_tier == "AIR" else "LOW"


def matchup_tier(eq_aware: str, board_tier: str, bet_tier: str, dv: str) -> str:
    has_strong_draw = dv in STRONG_DRAW_DV
    if eq_aware == "HIGH": return "AHEAD"
    if eq_aware == "MID":
        if board_tier == "MERGED": return "AHEAD"
        if board_tier == "POLAR" and bet_tier in {"BIG", "ALLIN"}: return "BEHIND"
        return "TIE"
    if eq_aware == "LOW":
        if has_strong_draw: return "TIE"
        if bet_tier == "SMALL": return "TIE"
        if board_tier == "MERGED" and bet_tier == "MED": return "TIE"
        return "BEHIND"
    if has_strong_draw: return "TIE"
    return "BEHIND"


# ════════════════════ NEW Layer 1: blocker_tier ════════════════════

def blocker_tier(card_a: str, card_b: str, board_str: str, board_family: str) -> str:
    """Return blocker strength: STRONG_BLOCKER / MED_BLOCKER / NONE.

    Section A3 finding (既存データ実測):
      - Monotone × Ax of board suit: GTO CALL +27pp
      - Paired KK × Kx (trips block): GTO CALL +42pp
    """
    if not card_a or not card_b or not board_str or len(board_str) < 6:
        return "NONE"

    # Monotone: Ace of board suit = STRONG_BLOCKER
    if board_family == "monotone":
        # board の最初の card のスート (mono flop は全部同じスート)
        suit = board_str[1]
        if (card_a.startswith("A") and card_a[1:2] == suit) or \
           (card_b.startswith("A") and card_b[1:2] == suit):
            return "STRONG_BLOCKER"
        # K of suit = MED_BLOCKER
        if (card_a.startswith("K") and card_a[1:2] == suit) or \
           (card_b.startswith("K") and card_b[1:2] == suit):
            return "MED_BLOCKER"

    # Paired: hero に paired rank の card → trips block (STRONG)
    if board_family == "paired":
        ranks = [board_str[i] for i in range(0, len(board_str), 2)]
        rc = Counter(ranks)
        paired_rank = next((r for r, c in rc.items() if c >= 2), None)
        if paired_rank:
            if card_a[0] == paired_rank or card_b[0] == paired_rank:
                return "STRONG_BLOCKER"

    # dynamic_2tone / dynamic で nut suit/straight blocker は今回 skip (effect 小)
    return "NONE"


# ════════════════════ NEW Layer 1: hero_role ════════════════════

def infer_hero_role(scenario_id: str, hero_pos: str = "", target: str = "") -> str:
    """IP vs OOP defender. Section A2 で IP は wider call が必要と判明."""
    sid = str(scenario_id).lower()
    # IP defender scenarios
    if "r1_past" in sid: return "IP"
    if "cr_def" in sid or "donk_def" in sid: return "IP"
    if "turn_cr" in sid or "turn_donk" in sid: return "IP"
    if "river_donk" in sid: return "IP"
    return "OOP"


# ════════════════════ Layer 2: Universal rule v3 (blocker-aware + role-aware) ════════════════════

def apply_universal_rule_v3(
    matchup: str, spr: str, bet_tier: str, street: str,
    board_tier: str, board_family: str, hand_tier: str,
    blocker: str, mv: str, dv: str,
) -> Action:
    """3-rule + blocker/role aware defense logic."""
    is_river = street == "river"
    has_strong_draw = dv in STRONG_DRAW_DV
    has_weak_draw = dv in WEAK_DRAW_DV

    # ── Rule 1: AHEAD ──
    if matchup == "AHEAD":
        # NEW: monotone non-river slowdown for marginal value (Section A4)
        if board_family == "monotone" and not is_river:
            if hand_tier in {"PAIR", "TWO_PAIR"}:
                return "CALL"
        # NEW: HIGH SPR でも nut_made / strong は RAISE 維持 (Section A1)
        if hand_tier == "NUT_MADE":
            return "CALL" if is_river else "RAISE"
        if hand_tier in {"STRONG", "TWO_PAIR"} and spr == "HIGH" and not is_river:
            return "RAISE"  # MTT200 で slowplay 取りこぼし対策
        if is_river: return "CALL"
        if board_tier == "POLAR": return "CALL"  # slowdown vs nut possibility
        return "RAISE"

    # ── Rule 2: TIE ──
    if matchup == "TIE":
        if spr == "SHALLOW": return "CALL"
        if has_strong_draw: return "CALL"
        # NEW: blocker boost (Section A3)
        if blocker == "STRONG_BLOCKER" and bet_tier in {"MED", "BIG"}:
            return "CALL"
        if bet_tier in {"BIG", "ALLIN"}:
            if board_tier == "MERGED" and has_weak_draw: return "CALL"
            if blocker in {"STRONG_BLOCKER", "MED_BLOCKER"}: return "CALL"
            return "FOLD"
        return "CALL"

    # ── Rule 3: BEHIND ──
    if has_strong_draw: return "CALL"
    # NEW: blocker on BEHIND × {SMALL, MED} bet → CALL (bluff catch)
    if blocker == "STRONG_BLOCKER" and bet_tier in {"SMALL", "MED"}:
        return "CALL"
    if bet_tier == "SMALL":
        if mv == "ace_high" and board_tier == "MERGED": return "CALL"
        if has_weak_draw and board_tier == "MERGED": return "CALL"
        return "FOLD"
    return "FOLD"


# ════════════════════ Layer 3: context modifiers ════════════════════

def apply_context_modifier(matchup: str, action_context: str) -> str:
    if action_context == "vs_CR":
        return {"AHEAD": "TIE", "TIE": "BEHIND", "BEHIND": "BEHIND"}[matchup]
    if action_context == "vs_donk":
        return {"AHEAD": "AHEAD", "TIE": "TIE", "BEHIND": "TIE"}[matchup]
    return matchup


def apply_opener_shift(matchup: str, opener: str, street: str) -> str:
    if street == "river" and opener in {"CO", "HJ"}:
        return {"AHEAD": "AHEAD", "TIE": "BEHIND", "BEHIND": "BEHIND"}[matchup]
    return matchup


def apply_donk_action_modifier(action: Action, action_context: str) -> Action:
    if action_context == "vs_donk" and action == "RAISE":
        return "CALL"
    return action


# ════════════════════ NEW Layer 3: IP defender modifier (Section A2) ════════════════════

def apply_ip_defender_modifier(
    action: Action, hero_role: str, bet_tier: str,
    hand_tier: str, mv: str, eb: str, dv: str, blocker: str,
    board_family: str,
) -> Action:
    """BTN IP river allin defender: 限定的に Section A2 patterns だけ FOLD → CALL.

    Section A2 で見つかった TOP mismatches:
      flush × weak/trash × FOLD → CALL (192 + 23 cases)
      top_pair × weak/trash × FOLD → CALL (145 + 125 cases、MERGED board が多い)
      second_pair × weak × FOLD → CALL (112 cases)

    NOTE: trips × weak × CALL → FOLD (58 cases) や両 pair × weak × CALL → FOLD (26)
    は UDG が over-CALL してる場面、IP modifier では触らない (root cause は別)。
    """
    if hero_role != "IP" or bet_tier != "ALLIN": return action
    if action != "FOLD": return action  # CALL/RAISE は touch しない

    # 限定 pattern のみ FOLD → CALL
    # flush × weak/trash (192+23 cases)
    if mv == "flush" and eb in {"weak_hands", "trash_hands"}:
        return "CALL"
    # top_pair × weak/trash on MERGED board (145+125 cases、大半が MERGED)
    if mv == "top_pair" and eb in {"weak_hands", "trash_hands"} and board_family in MERGED_FAMILIES:
        return "CALL"
    # second_pair × weak on MERGED (112 cases、大半が MERGED)
    if mv == "second_pair" and eb == "weak_hands" and board_family in MERGED_FAMILIES:
        return "CALL"
    return action


# ════════════════════ Master function ════════════════════

def udg_defense_v3(r, scenario_meta: dict | None = None) -> Action:
    """5+2 tier UDG v3 defense."""
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]
    bs = r.get("ip_bet_size", "med_75p")
    eb = r.get("equity_bucket", "trash_hands")
    board_str = r.get("board_str", "")
    card_a = str(r.get("card_a", ""))
    card_b = str(r.get("card_b", ""))

    # Layer 1: classify
    hand_tier = hand_strength_tier(mv)
    board_tier = board_polar_tier(bf)
    bet_tier = bet_size_tier(bs)
    street = determine_street(board_str)
    blocker = blocker_tier(card_a, card_b, board_str, bf)  # NEW

    meta = scenario_meta or _infer_meta(r)
    pot_type = meta.get("pot_type", "SRP")
    action_context = meta.get("action_context", "vs_cbet")
    opener = meta.get("opener", "BTN")
    depth_bb = meta.get("depth_bb", 100)
    hero_role = infer_hero_role(str(r.get("scenario_id", "")))  # NEW

    spr = spr_tier(pot_type, street, depth_bb)
    eq_aware = equity_aware_tier(hand_tier, eb)
    matchup = matchup_tier(eq_aware, board_tier, bet_tier, dv)

    # NEW: blocker boost matchup if strong_blocker on BEHIND with reasonable bet
    if blocker == "STRONG_BLOCKER" and matchup == "BEHIND" and bet_tier in {"SMALL", "MED"}:
        matchup = "TIE"

    matchup = apply_context_modifier(matchup, action_context)
    matchup = apply_opener_shift(matchup, opener, street)

    action = apply_universal_rule_v3(
        matchup, spr, bet_tier, street, board_tier, bf, hand_tier, blocker, mv, dv
    )
    action = apply_donk_action_modifier(action, action_context)
    # NOTE: apply_ip_defender_modifier was net negative on R1
    # (converted too many FOLDs that were actually correct).
    # Removed; R1 needs deeper analysis (Section A2 showed only mismatch breakdown,
    # not the underlying GTO distribution).
    return action


def _infer_meta(r) -> dict:
    sid = str(r.get("scenario_id", ""))
    meta: dict = {"pot_type": "SRP", "action_context": "vs_cbet", "opener": "BTN", "depth_bb": 100}
    if "4bp" in sid.lower(): meta["pot_type"] = "4BP"
    elif "3bp" in sid.lower(): meta["pot_type"] = "3BP"
    if "cr_def" in sid.lower(): meta["action_context"] = "vs_CR"
    elif "donk_def" in sid.lower(): meta["action_context"] = "vs_donk"
    elif "turn_cr" in sid.lower(): meta["action_context"] = "vs_CR"
    elif "turn_donk" in sid.lower(): meta["action_context"] = "vs_donk"
    elif "river_donk" in sid.lower(): meta["action_context"] = "vs_donk"
    if "hj_open" in sid.lower(): meta["opener"] = "HJ"
    elif "co_open" in sid.lower(): meta["opener"] = "CO"
    if "mtt25" in sid.lower(): meta["depth_bb"] = 25
    elif "mtt200" in sid.lower(): meta["depth_bb"] = 200
    return meta


# ════════════════════ Audit ════════════════════

if __name__ == "__main__":
    import pandas as pd

    print("=== UDG v3 audit (blocker + IP defender + HIGH SPR + mono slowdown) ===\n")
    df = pd.read_csv("scripts/three_class_model/dataset_unified_v2.csv", low_memory=False)
    print(f"Loaded {len(df):,} rows\n")

    df["udg_action"] = df.apply(udg_defense_v3, axis=1)
    df["udg_correct"] = (df["udg_action"] == df["best_action"])

    def loss(r):
        a = r["udg_action"]
        ev = {"FOLD": r["ev_fold"], "CALL": r["ev_call"], "RAISE": r["ev_raise"]}.get(a)
        if pd.notna(ev): return r["best_ev"] - ev
        return r["ev_gap"]
    df["udg_loss"] = df.apply(loss, axis=1)

    print(f"{'scenario_id':30s}  {'n':>6s}  {'acc':>6s}  {'v3':>6s}  {'v2_proxy':>9s}  {'verdict':>10s}")
    print("-" * 85)
    for sid, sub in df.groupby("scenario_id"):
        acc = sub["udg_correct"].mean() * 100
        huge_rows = sub[sub["udg_loss"] > 0.5]
        huge = huge_rows["udg_loss"].mean() if len(huge_rows) > 0 else 0
        old_rows = sub[sub["formula_loss"] > 0.5]
        old_huge = old_rows["formula_loss"].mean() if len(old_rows) > 0 else 0
        verdict = "✓" if (huge <= old_huge * 1.1) else ("△" if huge <= old_huge * 1.3 else "✗")
        if old_huge == 0: verdict = "—"
        print(f"{sid:30s}  {len(sub):>6d}  {acc:>5.1f}%  {huge:>6.2f}  {old_huge:>9.2f}  {verdict:>10s}")

    print()
    huge_rows = df[df["udg_loss"] > 0.5]
    overall_huge = huge_rows["udg_loss"].mean()
    overall_acc = df["udg_correct"].mean() * 100
    valid_v1 = df[df["formula_loss"].notna() & (df["formula_loss"] > 0.5)]
    overall_v1_huge = valid_v1["formula_loss"].mean()
    print(f"OVERALL: acc={overall_acc:.1f}%  v3_huge={overall_huge:.2f}  v1_huge={overall_v1_huge:.2f}")
