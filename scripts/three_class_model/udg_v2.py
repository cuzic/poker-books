#!/usr/bin/env python3
"""udg_v2.py — UDG v2: 5 tier 概念に拡張 (A: SPR + C: Matchup + H: Equity bucket 統合)

v1 からの変更:
  - 新 tier 関数 3 つ追加 (spr_tier / equity_aware_tier / matchup_tier)
  - universal rule 7 → 3 ルール (AHEAD / TIE / BEHIND) に圧縮
  - 4BP / 3BP / MTT depth modifier は SPR tier に吸収
  - CR / donk / opener modifier は context shift で matchup を直接更新

期待: 暗記項目 30 → 20、huge_loss 同等以下、acc 改善 (matchup の方が GTO 整合)
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
    if board_family in POLAR_FAMILIES:
        return "POLAR"
    if board_family in MERGED_FAMILIES:
        return "MERGED"
    return "MID"


def hand_strength_tier(mv: str) -> str:
    if mv in NUT_MADE_MV: return "NUT_MADE"
    if mv in STRONG_MV: return "STRONG"
    if mv in TWO_PAIR_MV: return "TWO_PAIR"
    if mv in PAIR_MV: return "PAIR"
    if mv in MID_PAIR_MV: return "MID_PAIR"
    return "AIR"


def bet_size_tier(bet_size: str) -> str:
    if bet_size == "allin": return "ALLIN"
    if bet_size in {"overbet", "overbet_185"}: return "BIG"
    if bet_size in {"med_75p", "med_100p"}: return "MED"
    if bet_size in {"small_33", "small_30p"}: return "SMALL"
    return "MED"


def determine_street(board_str: str) -> str:
    n = len(board_str) // 2 if board_str else 0
    if n == 5: return "river"
    if n == 4: return "turn"
    return "flop"


# ════════════════════ NEW: SPR tier (A) ════════════════════
# Scenario × street で SPR を hardcode (実際の API データから計算済)

_SPR_TIER_BASE: dict[tuple[str, str], str] = {
    ("SRP", "flop"): "HIGH",     # ~10
    ("SRP", "turn"): "MID",      # ~5
    ("SRP", "river"): "MID",     # ~2 (Cash100), >5 for MTT200
    ("3BP", "flop"): "MID",      # ~6
    ("3BP", "turn"): "LOW",      # ~2-3
    ("3BP", "river"): "SHALLOW", # ~0.3 (allin)
    ("4BP", "flop"): "LOW",      # ~1.5
    ("4BP", "turn"): "SHALLOW",  # ~0.7
    ("4BP", "river"): "SHALLOW", # ~0.3
}


def spr_tier(pot_type: str, street: str, depth_bb: int = 100) -> str:
    """SPR tier: SHALLOW / LOW / MID / HIGH."""
    base = _SPR_TIER_BASE.get((pot_type, street), "MID")
    # depth 補正
    if depth_bb <= 25:
        # 短スタックは SHALLOW 寄り
        return {"HIGH": "MID", "MID": "LOW", "LOW": "SHALLOW",
                 "SHALLOW": "SHALLOW"}.get(base, "SHALLOW")
    if depth_bb >= 200:
        # 深スタックは HIGH 寄り
        return {"SHALLOW": "LOW", "LOW": "MID", "MID": "HIGH",
                 "HIGH": "HIGH"}.get(base, base)
    return base


# ════════════════════ NEW: Equity-aware hand tier (H) ════════════════════
# Equity bucket で hand_strength_tier を calibrate

def equity_aware_tier(hand_tier: str, equity_bucket: str) -> str:
    """Return effective hand tier: HIGH / MID / LOW / VERY_LOW.

    Equity bucket は relative strength (vs opp range) を表すので、
    hand_strength_tier の絶対強さを「実効強さ」に補正する。

    例: set on POLAR board × equity_bucket=weak_hands → MID (not HIGH)
        AIR + best_hands (mono board + nut blocker) → HIGH (not VERY_LOW)
    """
    eb = equity_bucket or "good_hands"

    if eb == "best_hands":
        return "HIGH"
    if eb == "good_hands":
        if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR", "PAIR"}:
            return "HIGH"
        return "MID"
    if eb == "weak_hands":
        if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR"}:
            return "MID"  # nominal strong but behind in equity
        if hand_tier == "PAIR":
            return "LOW"
        return "LOW"
    if eb == "trash_hands":
        return "VERY_LOW"
    # fallback (bucket missing)
    if hand_tier in {"NUT_MADE", "STRONG", "TWO_PAIR"}: return "HIGH"
    if hand_tier == "PAIR": return "MID"
    if hand_tier == "MID_PAIR": return "LOW"
    return "VERY_LOW"


# ════════════════════ NEW: Range matchup tier (C) ════════════════════
# 3-way classification: AHEAD / TIE / BEHIND

def matchup_tier(eq_aware: str, board_tier: str, bet_tier: str, dv: str) -> str:
    """hero vs opp range の相対位置を 3 段階で表現.

    Rules:
      - eq_aware HIGH: AHEAD always (best_hands or nominal strong + good_hands)
      - eq_aware MID: AHEAD on MERGED (opp mostly air), BEHIND on POLAR overbet, TIE else
      - eq_aware LOW: TIE if strong draw, BEHIND if big bet, else context-dependent
      - eq_aware VERY_LOW: BEHIND (rare bluff catch on MERGED)
    """
    has_strong_draw = dv in STRONG_DRAW_DV

    if eq_aware == "HIGH":
        return "AHEAD"

    if eq_aware == "MID":
        if board_tier == "MERGED":
            return "AHEAD"  # opp range mostly air
        if board_tier == "POLAR" and bet_tier in {"BIG", "ALLIN"}:
            return "BEHIND"  # polar overbet dominates
        return "TIE"

    if eq_aware == "LOW":
        if has_strong_draw:
            return "TIE"  # draw equity
        if bet_tier == "SMALL":
            return "TIE"  # cheap bluff catch
        if board_tier == "MERGED" and bet_tier == "MED":
            return "TIE"  # opp air-heavy on MERGED
        return "BEHIND"

    # VERY_LOW
    if has_strong_draw:
        return "TIE"
    return "BEHIND"


# ════════════════════ Layer 2: Universal Rule v2 (3 rules) ════════════════════

def apply_universal_rule_v2(
    matchup: str,
    spr: str,
    bet_tier: str,
    street: str,
    board_tier: str,
    hand_tier: str,
    mv: str,
    dv: str,
) -> Action:
    """3-rule defense logic.

      AHEAD: RAISE on non-river + non-POLAR; CALL on river or POLAR (slowdown)
      TIE:   CALL by default; FOLD on BIG bet × non-draw + non-blocker
      BEHIND: FOLD by default; CALL on SMALL bet × MERGED × blocker (rare)
    """
    is_river = street == "river"
    has_strong_draw = dv in STRONG_DRAW_DV
    has_blocker = mv == "ace_high"

    # ── Rule 1: AHEAD ──
    if matchup == "AHEAD":
        if hand_tier == "NUT_MADE":
            return "CALL" if is_river else "RAISE"
        if is_river:
            return "CALL"
        if board_tier == "POLAR":
            return "CALL"  # slowdown vs possible nut
        return "RAISE"

    # ── Rule 2: TIE ──
    if matchup == "TIE":
        # SHALLOW SPR + TIE = committed
        if spr == "SHALLOW":
            return "CALL"
        if has_strong_draw:
            return "CALL"
        # BIG/ALLIN × TIE without draw → cautious
        if bet_tier in {"BIG", "ALLIN"} and not has_blocker:
            # Only call with backdoor equity on MERGED
            if board_tier == "MERGED" and dv in WEAK_DRAW_DV:
                return "CALL"
            return "FOLD"
        return "CALL"

    # ── Rule 3: BEHIND ──
    if has_strong_draw:
        return "CALL"
    if bet_tier == "SMALL" and board_tier == "MERGED" and has_blocker:
        return "CALL"  # rare bluff catch
    if bet_tier == "SMALL" and dv in WEAK_DRAW_DV and board_tier == "MERGED":
        return "CALL"  # backdoor equity vs cheap bet
    return "FOLD"


# ════════════════════ Layer 3: Context modifiers (minimal) ════════════════════

def apply_context_modifier(matchup: str, action_context: str) -> str:
    """CR/donk context shifts matchup directly.

    CR after cbet: opp is VALUE-HEAVY (strong 45%) → shift matchup down 1 step
    donk: opp is AIR-HEAVY (weak 54-61%) → shift matchup up 1 step (BEHIND→TIE)
       (但し TIE→AHEAD は IP defender が RAISE しすぎになるので保留)
    """
    if action_context == "vs_CR":
        return {"AHEAD": "TIE", "TIE": "BEHIND", "BEHIND": "BEHIND"}[matchup]
    if action_context == "vs_donk":
        # BEHIND だけ TIE に格上げ (BTN IP は wider call OK)
        return {"AHEAD": "AHEAD", "TIE": "TIE", "BEHIND": "TIE"}[matchup]
    return matchup


def apply_donk_action_modifier(action: Action, action_context: str) -> Action:
    """donk defense では IP の RAISE が過剰になりがち、CALL に落とす.

    GTO 上 BTN IP が BB donk に対し raise するのは 5-10% 程度。
    RAISE → CALL に変換すれば acc 向上 (BIG bet 等 specific 場面は除外)。
    """
    if action_context == "vs_donk" and action == "RAISE":
        return "CALL"
    return action


def apply_opener_shift(matchup: str, opener: str, street: str) -> str:
    """CO/HJ open: opp value-heavier (tight range) → shift matchup down."""
    if opener not in {"CO", "HJ"}:
        return matchup
    if street == "river":
        # River: TIE→BEHIND (AHEAD stays AHEAD; river shove is different)
        return {"AHEAD": "AHEAD", "TIE": "BEHIND", "BEHIND": "BEHIND"}[matchup]
    if street == "turn":
        # Turn: AHEAD→TIE, TIE→BEHIND (overpair calls, second_pair folds)
        return {"AHEAD": "TIE", "TIE": "BEHIND", "BEHIND": "BEHIND"}[matchup]
    return matchup


# ════════════════════ Master function ════════════════════

def udg_defense_v2(r, scenario_meta: dict | None = None) -> Action:
    """5-tier UDG defense."""
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

    # scenario meta
    meta = scenario_meta or _infer_meta(r)
    pot_type = meta.get("pot_type", "SRP")
    action_context = meta.get("action_context", "vs_cbet")
    opener = meta.get("opener", "BTN")
    depth_bb = meta.get("depth_bb", 100)

    # NEW: SPR tier (A)
    spr = spr_tier(pot_type, street, depth_bb)

    # NEW: equity-aware hand tier (H)
    eq_aware = equity_aware_tier(hand_tier, eb)

    # NEW: range matchup tier (C)
    matchup = matchup_tier(eq_aware, board_tier, bet_tier, dv)

    # Layer 3: context modifiers (matchup-level shifts)
    matchup = apply_context_modifier(matchup, action_context)
    matchup = apply_opener_shift(matchup, opener, street)

    # ── 4BP flop: committed pot — entirely different game theory ──
    # SPR ~1.5: strong hands trap (CALL), pair-level commits (RAISE), air calls wide.
    # GTO data: top_pair 92%R / set 93%C / trips 99%C / air 51%C / trash 35%F.
    if pot_type == "4BP" and street == "flop":
        _SLOWPLAY_MV = {"trips", "set", "straight", "flush", "fullhouse", "quads", "straight_flush"}
        _COMMIT_MV = {"top_pair", "overpair", "second_pair", "underpair"}
        if mv in _SLOWPLAY_MV:
            return "CALL"
        if mv in _COMMIT_MV:
            return "RAISE"
        if hand_tier == "AIR" and eb == "trash_hands":
            return "FOLD"  # pure air with no equity folds even in committed pot
        return "CALL"  # third_pair, two_pair, ace_high, king_high (non-trash), low_pair, air (weak/good)

    # ── 4BP turn: near-commit (SPR ~0.7) — set now commits (RAISE), trips still traps (CALL) ──
    # GTO data: top_pair 80%R / set 64%R / trips 70%C / no_made_hand 81%F.
    if pot_type == "4BP" and street == "turn":
        _SLOWPLAY_T = {"trips", "straight", "flush", "fullhouse", "quads", "straight_flush"}
        _COMMIT_T = {"top_pair", "overpair", "second_pair", "underpair", "set", "two_pair"}
        if mv in _SLOWPLAY_T:
            return "CALL"
        if mv in _COMMIT_T:
            return "RAISE"
        if hand_tier == "AIR" and eb in {"trash_hands", "weak_hands"}:
            return "FOLD"  # air folds on turn (more often than flop)
        return "CALL"  # third_pair, low_pair, air (good_hands)

    # ── 3BP flop: opponent's 3-bet range is premium → medium hands call, not raise ──
    # GTO: overbet: weak_hands 80%F (cash), 67%F (MTT); small/med: weak_hands 82-93%C.
    # air weak_hands float vs MED/SMALL; fold trash always; fold weak vs BIG/ALLIN.
    if pot_type == "3BP" and street == "flop":
        _3BP_RAISE = {"overpair", "trips", "quads", "straight", "flush", "straight_flush"}
        if mv in _3BP_RAISE:
            return "RAISE"
        if mv == "low_pair" and eb in {"trash_hands", "weak_hands"}:
            return "FOLD"  # 92% FOLD in 3BP flop for low_pair
        if hand_tier == "AIR" and eb == "trash_hands":
            return "FOLD"  # trash air always folds in 3BP (no equity to realize)
        if hand_tier == "AIR" and eb == "weak_hands" and bet_tier in {"BIG", "ALLIN"}:
            return "FOLD"  # weak air folds vs overbet (80-93%F across cash+MTT)
        return "CALL"  # top_pair(76%C), second_pair(82%C), air weak vs MED/SMALL floats

    # ── 4BP river: SPR ~0.3, committed — almost every made hand calls ──
    # GTO data: top_pair 99%C / set 100%C / no_made_hand 91%F.
    if pot_type == "4BP" and street == "river":
        if mv in {"no_made_hand", "king_high"} and eb in {"trash_hands", "weak_hands"}:
            return "FOLD"
        if hand_tier == "AIR" and eb == "trash_hands":
            return "FOLD"
        return "CALL"  # everything else calls at SHALLOW SPR river

    # ── 3BP turn: SPR ~2-3, premium opp range — sets/trips raise, TP calls, air folds ──
    # GTO data: overpair 70%R / set 70%R / trips 71%R / top_pair 82%C / no_made_hand 88%F.
    if pot_type == "3BP" and street == "turn":
        _3BP_T_RAISE = {"overpair", "trips", "set"}  # ~70% RAISE each on turn (SPR < flop)
        if mv in _3BP_T_RAISE:
            return "RAISE"
        if hand_tier == "AIR" and eb in {"trash_hands", "weak_hands"}:
            return "FOLD"
        if mv == "low_pair" or (mv == "third_pair" and eb in {"trash_hands", "weak_hands"}):
            return "FOLD"
        return "CALL"  # top_pair(82%C), second_pair(68%C), flush(96%C), FH(94%C), underpair(68%C)

    # ── River donk defense: nuts RAISE for value, air FOLD, rest CALL ──
    # GTO data: flush/trips/quads/straight 89-100%R / no_made_hand 88%F / overpair 85%C.
    if action_context == "vs_donk" and street == "river":
        _RIVER_DONK_RAISE = {"flush", "trips", "quads", "straight", "set", "two_pair", "straight_flush"}
        if eb == "best_hands" and mv in _RIVER_DONK_RAISE:
            return "RAISE"
        if mv in {"no_made_hand", "king_high"} and eb in {"trash_hands", "weak_hands"}:
            return "FOLD"
        return "CALL"  # made hands (top_pair, second_pair, overpair, FH, etc.) call

    # Layer 2: universal rule
    action = apply_universal_rule_v2(matchup, spr, bet_tier, street, board_tier, hand_tier, mv, dv)
    # post-rule context tweak (donk RAISE → CALL, non-river only)
    action = apply_donk_action_modifier(action, action_context)

    # ── Donk defense: weak/trash equity → FOLD (flop/turn only, GTO: 67-96% fold rate) ──
    # River donk handled separately above. Flop/turn: trash/weak air over-calls.
    if action_context == "vs_donk" and action == "CALL" and street != "river":
        if eb == "trash_hands":
            return "FOLD"
        if eb == "weak_hands" and hand_tier in {"AIR", "MID_PAIR"}:
            return "FOLD"

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

    print("=== UDG v2 audit (5 tier 概念) ===\n")
    df = pd.read_csv("scripts/three_class_model/dataset_unified_v2.csv", low_memory=False)
    print(f"Loaded {len(df):,} rows\n")

    df["udg_action"] = df.apply(udg_defense_v2, axis=1)
    df["udg_correct"] = (df["udg_action"] == df["best_action"])

    def loss(r):
        a = r["udg_action"]
        ev = {"FOLD": r["ev_fold"], "CALL": r["ev_call"], "RAISE": r["ev_raise"]}.get(a)
        if pd.notna(ev): return r["best_ev"] - ev
        return r["ev_gap"]
    df["udg_loss"] = df.apply(loss, axis=1)

    print(f"{'scenario_id':30s}  {'n':>6s}  {'acc':>6s}  {'v2':>6s}  {'v1':>7s}  {'verdict':>10s}")
    print("-" * 80)
    for sid, sub in df.groupby("scenario_id"):
        acc = sub["udg_correct"].mean() * 100
        huge_rows = sub[sub["udg_loss"] > 0.5]
        huge = huge_rows["udg_loss"].mean() if len(huge_rows) > 0 else 0
        old_rows = sub[sub["formula_loss"] > 0.5]
        old_huge = old_rows["formula_loss"].mean() if len(old_rows) > 0 else 0
        verdict = "✓" if (huge <= old_huge * 1.1) else ("△" if huge <= old_huge * 1.3 else "✗")
        if old_huge == 0: verdict = "—"
        print(f"{sid:30s}  {len(sub):>6d}  {acc:>5.1f}%  {huge:>6.2f}  {old_huge:>7.2f}  {verdict:>10s}")

    print()
    huge_rows = df[df["udg_loss"] > 0.5]
    overall_huge = huge_rows["udg_loss"].mean()
    overall_acc = df["udg_correct"].mean() * 100
    valid_v1 = df[df["formula_loss"].notna() & (df["formula_loss"] > 0.5)]
    overall_v1_huge = valid_v1["formula_loss"].mean()
    print(f"OVERALL: acc={overall_acc:.1f}%  v2_huge={overall_huge:.2f}  v1_huge={overall_v1_huge:.2f}")
