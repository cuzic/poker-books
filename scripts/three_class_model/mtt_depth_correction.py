#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas"]
# ///
"""mtt_depth_correction.py — Vol3 用 depth-aware 補正レイヤ (Task #11)

公式 v9b (flop) / v10 (turn) / v15 (river) は MTT50 / Cash100 で fit されているが、
MTT25 (短) / MTT100 (中) / MTT200 (深) では per-miss bleed が大きい。
本ファイルは v9b/v10/v15 をベースに、stack depth に応じた **少数の override** を
追加することで huge_loss を削減する SURGICAL CORRECTION モジュール。

主要設計方針 (新公式ではない、override レイヤ):
  - base 公式は引き続き workhorse (v9b/v10/v15)
  - depth_bb に応じて少数条件 (5-10) のみ override
  - SPR ベース: Cash100 SPR(flop)≈10 / turn≈7 / river≈2
                MTT25 SPR(flop)≈5  / turn≈3 / river≈1 (short stack)
                MTT200 SPR(flop)≈20 / turn≈14 / river≈5 (very deep)
  - 既存 memory `project_c_value_table_split` の SPR 閾値: ≥6→40, 3-5→60, <3→75

実測 (probe_priority_stats.json):
  - N_mtt100_river: acc=86.0%, formula_huge_loss=19.6 BB → 目標 15 BB
  - N_mtt25_river:  acc=79.6%, formula_huge_loss= 8.8 BB → 目標  6 BB
  - N_mtt200_turn:  acc=65.8%, formula_huge_loss= 2.7 BB → 目標  2 BB
  - N_mtt200_river: acc=76.1%, formula_huge_loss= 4.0 BB → 目標  3 BB

Vol3 章設計への影響:
  1. SRP postflop 章: 共通公式 v9b/v10/v15 で説明
  2. **depth 別補正章**: 25bb / 100bb / 200bb で挙動が変わる cell を明示
  3. 短 stack (25bb) は **shove/fold 軸** が支配的 → made-hand call wider、air/marginal fold tighter
  4. 深 stack (200bb) は **multi-street implication** が増える → top_pair が IP からの med-overbet で wider call (deeper bluff freq up)
"""
from __future__ import annotations

import sys
from pathlib import Path

# 同ディレクトリの mtt_formula_audit から base 公式と category 定数を import
sys.path.insert(0, str(Path(__file__).parent))

from mtt_formula_audit import (  # noqa: E402
    AIR,
    DRY_BOARDS,
    DRY_RIVER,
    DYNAMIC_BOARDS,
    DYNAMIC_RIVER,
    WEAK_DRAW,
    WEAK_PAIR_LOW,
    flop_def_v9b,
    river_def_v15,
    turn_def_v10,
)

# ════════════════════════════ Depth 閾値 ═══════════════════════
SHORT_DEPTH_BB = 25  # MTT25 以下 = "短 stack" (SPR river ≈ 1)
DEEP_DEPTH_BB = 200  # MTT200 以上 = "深 stack" (SPR river ≈ 5)


# ════════════════════════════ Helper: row-style dict ═══════════
def _make_row(mv, dv, bf, bs=None, eb=None, eqp=None):
    """base 公式は dict-like row を受ける。最小 row を組み立てる。"""
    return {
        "mv_cat": mv,
        "dv_cat": dv,
        "board_family": bf,
        "bet_size": bs if bs is not None else "—",
        "equity_bucket": eb if eb is not None else "good_hands",
        "eq_percentile": eqp,
    }


# ════════════════════════════ Flop ═══════════════════════════════
def depth_aware_flop_def(mv, dv, bf, depth_bb):
    """Flop defense (BB OOP vs IP cbet) の depth-aware 補正。

    v9b は既に `_is_short_stack` で 50bb 以下を short 判定済み。
    本補正は MTT200 (very deep, SPR(flop)≈20) で追加 override を入れる。

    深 stack override (5-10 条件):
      - third_pair/low_pair × dynamic board × no_draw: deep では fold ではなく CALL
        理由: SPR 高い → 後街で turn/river bluff が増える → 弱メイドの defense value 上がる
      - underpair × dry board: deep でも CALL (overpair 化のチャンスはないが pot odds 有利)
    """
    row = _make_row(mv, dv, bf)
    base = flop_def_v9b(row)

    if depth_bb >= DEEP_DEPTH_BB:
        # Deep stack: SPR 高、後街 bluff threat が defender 側を ease する
        if mv in {"third_pair", "low_pair"} and dv == "no_draw" and bf in DYNAMIC_BOARDS:
            return "CALL"
        if mv == "underpair" and dv == "no_draw" and bf in DRY_BOARDS:
            return "CALL"
        # Deep stack で AIR + bdfd combo は flush eq の implication 大 → CALL
        if mv in AIR and dv == "twocards_bdfd" and bf in DYNAMIC_BOARDS:
            return "CALL"

    # depth 25bb 以下は v9b の `_is_short_stack` が既に処理しているので追加 override なし
    return base


# ════════════════════════════ Turn ═══════════════════════════════
def depth_aware_turn_def(mv, dv, bf, bet_size, depth_bb):
    """Turn defense の depth-aware 補正。

    実測: N_mtt200_turn は huge_loss 2.7 BB と他より目立つ。
    主因: deep stack では IP の overbet/large bet 範囲に top_pair-class が混ざる
          (pure polar じゃない) → top_pair で fold すると bleed。

    Deep override (3 条件):
      - top_pair × dry × med_75p: deep では CALL (v10 だと CALL のはずだが念のため明示)
      - top_pair × DYNAMIC × overbet_185: deep では FOLD → CALL (deep の bluff combo 増)
      - second_pair × dry × med_75p: deep では CALL

    Short override (MTT25, 2 条件):
      - SPR 約 3 → shove or fold 軸。med_75p に対する weak メイドは
        実質 "shove 受け" になる → 中途半端な mv は FOLD。
    """
    row = _make_row(mv, dv, bf, bs=bet_size)
    base = turn_def_v10(row)

    if depth_bb >= DEEP_DEPTH_BB:
        # Deep stack: opp の overbet range に top_pair/value が混ざる比率増、
        # かつ后街での implied odds で marginal made が CALL profitable に
        if mv == "top_pair" and bf in DYNAMIC_BOARDS and bet_size == "overbet_185":
            return "CALL"
        if mv == "second_pair" and bf in DRY_BOARDS and bet_size in {"small_33", "other"}:
            return "CALL"
        if mv in {"top_pair", "overpair"} and bet_size == "small_33":
            return "CALL"

    if depth_bb <= SHORT_DEPTH_BB:
        # Short stack: med-large bet は実質 shove 同等 → weak メイドは諦め
        if mv in WEAK_PAIR_LOW and dv == "no_draw" and bet_size in {"overbet_185"}:
            return "FOLD"
        # Short stack + draw は equity ベースで CALL (pot odds 有利)
        if dv in {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"} and bet_size in {"small_33", "other"}:
            return "CALL"

    return base


# ════════════════════════════ River ═══════════════════════════════
def depth_aware_river_def(mv, eb, bf, bet_size, depth_bb, eqp=None, dv="no_draw"):
    """River defense の depth-aware 補正。

    実測 (probe):
      - MTT25 river huge_loss=8.8 BB  → 目標 6 BB
      - MTT100 river huge_loss=19.6 BB → 目標 15 BB
      - MTT200 river huge_loss=4.0 BB  → 目標 3 BB

    Short (MTT25) override (3 条件): SPR≈1, shove/fold 軸
      - {two_pair, set, trips} × どんな bet_size: CALL (短 stack call wider)
      - {weak_hands, trash_hands} × allin: FOLD (短 stack の allin 受けは tighter)
      - top_pair × allin × DYNAMIC: FOLD (short ではこの combo は通常 dominated)

    Deep (MTT200) override (3 条件): SPR≈5, multi-street depth
      - top_pair × {dry_high, low_dry} × {med_75p, med_100p}: CALL
        (deep では IP の large bet range に bluff 混ざる)
      - good_hands × overbet × DRY: CALL (deep の overbet polar 度がやや下がる)
      - 2P × DYNAMIC × {med_100p, overbet}: CALL を強制 (v15 は eb 経由で fold する場合がある)
    """
    row = _make_row(mv, dv, bf, bs=bet_size, eb=eb, eqp=eqp)
    base = river_def_v15(row)

    # ─── Short stack (≤25bb): shove/fold 軸 ─────────────────────
    if depth_bb <= SHORT_DEPTH_BB:
        # Short での made hand は wider call
        if mv in {"two_pair", "set", "trips", "straight", "flush"}:
            return "CALL"
        # 短 stack の allin 受けは tighter (実 eq vs all-in range で marginal は -)
        if eb in {"weak_hands", "trash_hands"} and bet_size == "allin":
            return "FOLD"
        # top_pair × allin × dynamic は short では dominated 多い
        if mv == "top_pair" and bet_size == "allin" and bf in DYNAMIC_RIVER:
            return "FOLD"
        return base

    # ─── Deep stack (≥200bb): multi-street implication ───────────
    if depth_bb >= DEEP_DEPTH_BB:
        # Deep の IP large-bet range に bluff 混ざる → top_pair wider call
        if mv == "top_pair" and bf in DRY_RIVER and bet_size in {"med_75p", "med_100p"}:
            return "CALL"
        # Deep の overbet polarization は短/中より緩い (mid 比率増)
        if eb == "good_hands" and bet_size == "overbet" and bf in DRY_RIVER:
            return "CALL"
        # Dynamic river × 2P は overbet/med_100p で CALL (v15 の eb 分岐で fold する穴を埋める)
        if mv == "two_pair" and bf in DYNAMIC_RIVER and bet_size in {"med_100p", "overbet"}:
            return "CALL"
        return base

    # MTT100 / Cash100 は v15 そのまま (in-domain)
    return base


# ════════════════════════════ Tests ═══════════════════════════
if __name__ == "__main__":
    print("=" * 70)
    print("MTT Depth Correction — Same hand × different depth")
    print("=" * 70)

    # ─── Case 1: River top_pair × dry_high × med_100p, eb=good ──
    args = dict(mv="top_pair", eb="good_hands", bf="dry_high", bet_size="med_100p", eqp=0.72)
    print("\n[River] top_pair good_hands × dry_high × med_100p:")
    for d in (25, 100, 200):
        a = depth_aware_river_def(depth_bb=d, **args)
        print(f"  depth={d:3d}bb → {a}")

    # ─── Case 2: River two_pair × dynamic × med_100p, eb=weak ──
    args = dict(mv="two_pair", eb="weak_hands", bf="dynamic", bet_size="med_100p", eqp=0.55)
    print("\n[River] two_pair weak_hands × dynamic × med_100p:")
    for d in (25, 100, 200):
        a = depth_aware_river_def(depth_bb=d, **args)
        print(f"  depth={d:3d}bb → {a}")

    # ─── Case 3: River set × allin × low_dry, eb=weak ──────────
    args = dict(mv="set", eb="weak_hands", bf="low_dry", bet_size="allin", eqp=0.70)
    print("\n[River] set weak_hands × low_dry × allin:")
    for d in (25, 100, 200):
        a = depth_aware_river_def(depth_bb=d, **args)
        print(f"  depth={d:3d}bb → {a}  (short: call wider)")

    # ─── Case 4: River top_pair × allin × dynamic, eb=good ────
    args = dict(mv="top_pair", eb="good_hands", bf="dynamic", bet_size="allin", eqp=0.50)
    print("\n[River] top_pair good_hands × dynamic × allin:")
    for d in (25, 100, 200):
        a = depth_aware_river_def(depth_bb=d, **args)
        print(f"  depth={d:3d}bb → {a}  (short: fold tighter)")

    # ─── Case 5: Turn top_pair × dynamic × overbet_185 ─────────
    print("\n[Turn] top_pair × dynamic × overbet_185:")
    for d in (25, 100, 200):
        a = depth_aware_turn_def(mv="top_pair", dv="no_draw", bf="dynamic", bet_size="overbet_185", depth_bb=d)
        print(f"  depth={d:3d}bb → {a}")

    # ─── Case 6: Flop third_pair × dynamic × no_draw ──────────
    print("\n[Flop] third_pair × dynamic × no_draw:")
    for d in (25, 100, 200):
        a = depth_aware_flop_def(mv="third_pair", dv="no_draw", bf="dynamic", depth_bb=d)
        print(f"  depth={d:3d}bb → {a}")

    # ─── Case 7: Flop AIR × twocards_bdfd × dynamic ────────────
    print("\n[Flop] AIR (ace_high) × twocards_bdfd × dynamic_2tone:")
    for d in (25, 100, 200):
        a = depth_aware_flop_def(mv="ace_high", dv="twocards_bdfd", bf="dynamic_2tone", depth_bb=d)
        print(f"  depth={d:3d}bb → {a}")

    print("\n" + "=" * 70)
    print("Target huge_loss reductions:")
    print("  MTT25  river: 8.8  → 6.0 BB")
    print("  MTT100 river: 19.6 → 15.0 BB")
    print("  MTT200 turn:  2.7  → 2.0 BB")
    print("  MTT200 river: 4.0  → 3.0 BB")
    print("=" * 70)
