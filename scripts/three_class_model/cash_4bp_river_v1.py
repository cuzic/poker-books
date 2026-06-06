#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Cash 4BP River v1 — 4BP river 専用ロジック (polarization × bucket × mv)

Domain
------
Cash 100bb, BB OOP defense vs IP river overbet (≈ allin given SPR <1) in 4BP.

Data source
-----------
- research/v4-postflop/probe_phase4_stats.json [N_cash_4bp_river]
  (n=6486 hand-level rows, 6 boards, formula_acc=60.7% with v15 baseline)
- research/v4-postflop/probe_phase5_stats.json [P5_B_4bp_river_traj]
  (16 trajectories × 4 boards = additional 17k rows of trajectory variance)
- research/v4-postflop/probe_phase4_rows.csv

Key findings (data)
-------------------
opp_polarization_mean = 0.69 (NOT polar like SRP 0.95+)
opp_strong_pct_mean = 0.44 (strong opp 44%)
opp_weak_pct_mean = 0.25 (mid 31% !)
modal F/C = 42.6 / 57.4%, RAISE = 0% (allin spot)

Per-board polarization is the KEY structural axis:
  dyn_T97      polarization=1.00  strong=76% → POLAR (bucket logic)
  d2t_T97      polarization=1.00  strong=76% → POLAR
  low_853      polarization=0.69  strong=43% → MID-POLAR
  mono_Js      polarization=0.59  strong=34% → MID
  pair_KK2     polarization=0.45  strong=20% → MERGED (mv-based decisions)
  dry_K72      polarization=0.41  strong=16% → MERGED

Per-board × mv on POLAR boards (dyn_T97 / d2t_T97):
  dyn_T97 × second_pair → F 38%, C 62%  (まだ CALL 多い)
  dyn_T97 × third_pair → F 49, C 51 (almost split)
  dyn_T97 × low_pair → F 73, C 27 (fold)
  dyn_T97 × ace_high → F 100% (FOLD 確定)
  d2t_T97 × second_pair → F 33, C 67 (call lean)
  d2t_T97 × low_pair → F 70, C 30 (fold)

Per-board × mv on MERGED boards (dry_K72 / pair_KK2):
  dry_K72 × low_pair → C 58.6%, F 41 (lean call)
  dry_K72 × ace_high → C 94.6% (almost always call)
  pair_KK2 × low_pair → CALL 100%
  pair_KK2 × ace_high → 50/50
  pair_KK2 × second_pair/third_pair → CALL 100%

Per-board × mv on MID boards (mono_Js / low_853):
  mono_Js × low_pair → F 62.5%, C 37 (lean fold)
  mono_Js × ace_high → F 62.5%, C 37 (lean fold)
  mono_Js × second_pair → C 72%, F 28 (call)
  low_853 × ace_high → C 71.5%, F 28
  low_853 × king_high → F 87.5%
  low_853 × second_pair → CALL 100%

GLOBAL mv distribution (all boards):
  top_pair      → CALL 99.2%  (常 CALL)
  overpair      → CALL 76.5%
  underpair     → CALL 95.8%
  two_pair/set/trips/straight/flush/full → CALL 100% (no RAISE in allin)
  second_pair   → CALL 86.4%
  third_pair    → CALL 80.8%
  low_pair      → F 50.3%, C 49.7%  (★ board 依存 mixed)
  ace_high      → F 49.7%, C 50.3%  (★ board 依存 mixed)
  no_made_hand  → FOLD 90.9%
  king_high     → FOLD 87.3%

Design philosophy
-----------------
"4BP river は polarization × mv の 2軸 hybrid:
  - POLAR board (>=0.85): bucket fallback ── 強メイドのみ CALL、bluff catcher 思考が機能
  - MERGED board (<0.55): mv-based ── 中位ペアでも CALL、相手 range が merged
  - MID board (0.55-0.85): mv + ace_high の board 別判定"

Polarization thresholds (data-driven):
  HIGH polar ≥ 0.85 → bucket logic (mv tier に厳しい)
  LOW polar < 0.55  → mv logic (mv tier に寛容、中位ペアまで CALL)
  MID 0.55-0.85    → mv logic but ace_high/low_pair FOLD

Decision logic (top-down):
  1. Strong made (2P/set/trips/str/flush/full/quads): CALL 確定
  2. Pair tier (TP, OP, UP): CALL 確定
  3. second_pair/third_pair: CALL on all but dynamic POLAR boards (where 50/50)
  4. low_pair: board polarization で分岐
       - merged (dry_K72, pair_KK2): CALL
       - polar (dyn_T97, d2t_T97): FOLD
       - mid (mono_Js, low_853): FOLD (data lean)
  5. ace_high: board polarization で分岐
       - merged + paired (dry_K72, pair_KK2): CALL/MIX (default CALL)
       - polar (dyn_T97, d2t_T97): FOLD
       - mid: FOLD (data lean fold)
  6. king_high / no_made_hand: FOLD 確定

Bet size: 4BP river は SPR <1 で R47/overbet ≈ allin equivalent.

Target: acc > 65% (baseline v15 = 60.7%, +5+ ppts improvement)
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

# ── Board polarization classification (data-driven from probe_phase4) ──
# polarization ≥ 0.85 → POLAR (opp range は value + air、middling 少)
# polarization < 0.55 → MERGED (opp range に middle 多)
# 0.55-0.85          → MID-POLAR
POLAR_BOARDS = {"dyn_T97", "d2t_T97"}            # polarization ~1.00
MERGED_BOARDS = {"dry_K72", "pair_KK2"}          # polarization 0.41-0.45
# MID = {"mono_Js" (0.59), "low_853" (0.69)} — handled via family fallback

# ── Board family fallback (when board_label is not in our 6 CORE_BOARDS) ──
POLAR_FAMILIES = {"dynamic", "dynamic_2tone"}     # high polar
MERGED_FAMILIES = {"dry_high", "paired"}          # low polar
# {"low_dry", "monotone"} → mid-polar

# Strong made categories (always CALL in allin spot)
NUT_MADE = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
PAIR_TIER = {"top_pair", "overpair", "underpair"}


def _board_polarization_tier(r) -> str:
    """Return 'POLAR' / 'MERGED' / 'MID' for a board.

    Prefers board_label (exact match for 6 CORE_BOARDS), falls back to board_family.
    """
    bl = r.get("board_label", "")
    if bl in POLAR_BOARDS:
        return "POLAR"
    if bl in MERGED_BOARDS:
        return "MERGED"
    bf = r.get("board_family", "")
    if bf in POLAR_FAMILIES:
        return "POLAR"
    if bf in MERGED_FAMILIES:
        return "MERGED"
    return "MID"


def cash_4bp_river_v1(r) -> str:
    """4BP river defense vs IP overbet/allin (SPR <1).

    Decision (top-down):
      1. Strong made (2P+): CALL
      2. Pair tier (TP/OP/UP): CALL
      3. second_pair, third_pair: CALL (data 80-100% C across boards)
      4. low_pair: polarization-tiered (MERGED → CALL, POLAR/MID → FOLD)
      5. ace_high: polarization-tiered (MERGED → CALL, POLAR/MID → FOLD)
      6. king_high, no_made_hand: FOLD
    """
    mv = r["mv_cat"]
    tier = _board_polarization_tier(r)

    # ── 1) Strong made hands → CALL ──
    if mv in NUT_MADE:
        return "CALL"

    # ── 2) Pair tier (TP/OP/UP) → CALL (>=76% across all data) ──
    if mv in PAIR_TIER:
        return "CALL"

    # ── 3) Mid pairs → CALL (data 80-100%) ──
    #     2nd_pair: 86% C global; 3rd_pair: 81% C global
    #     ただし POLAR board × 3rd_pair は 50/50 → CALL maintain (vol損益少)
    if mv in {"second_pair", "third_pair"}:
        return "CALL"

    # ── 4) low_pair: board polarization で分岐 ──
    #     MERGED → CALL (dry_K72 59%, pair_KK2 100%)
    #     POLAR  → FOLD (dyn_T97 73%, d2t_T97 70%)
    #     MID    → FOLD (mono_Js 62%)
    if mv == "low_pair":
        if tier == "MERGED":
            return "CALL"
        return "FOLD"

    # ── 5) ace_high: 同じく polarization で分岐 ──
    #     MERGED → CALL (dry_K72 94%, pair_KK2 50/50 → lean CALL)
    #     POLAR  → FOLD (dyn_T97 100%, d2t_T97 80%)
    #     MID    → FOLD (mono_Js 62% F, low_853 28% F は exception; default FOLD)
    if mv == "ace_high":
        if tier == "MERGED":
            return "CALL"
        if tier == "MID":
            # low_853 (low_dry family) は CALL lean — bf check
            if r.get("board_family") == "low_dry":
                return "CALL"
            return "FOLD"
        return "FOLD"

    # ── 6) king_high / no_made_hand: FOLD ──
    return "FOLD"


def best_ev(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def _test_predictions():
    print("=== cash_4bp_river_v1 per-board predictions ===\n")
    # CORE_BOARDS in display order
    boards = [
        ("dry_K72", "dry_high"),
        ("d2t_T97", "dynamic_2tone"),
        ("mono_Js", "monotone"),
        ("low_853", "low_dry"),
        ("dyn_T97", "dynamic"),
        ("pair_KK2", "paired"),
    ]
    test_cells = [
        ("top_pair", "no_draw"),
        ("overpair", "no_draw"),
        ("underpair", "no_draw"),
        ("two_pair", "no_draw"),
        ("set", "no_draw"),
        ("straight", "no_draw"),
        ("second_pair", "no_draw"),
        ("third_pair", "no_draw"),
        ("low_pair", "no_draw"),
        ("ace_high", "no_draw"),
        ("king_high", "no_draw"),
        ("no_made_hand", "no_draw"),
    ]
    header = f"{'mv':<14} {'dv':<10}" + "".join(f"{b[0]:>10}" for b in boards)
    print(header)
    print("-" * len(header))
    for mv, dv in test_cells:
        row = f"{mv:<14} {dv:<10}"
        for bl, bf in boards:
            r = {"mv_cat": mv, "dv_cat": dv, "board_label": bl, "board_family": bf}
            row += f"{cash_4bp_river_v1(r):>10}"
        print(row)
    print()
    print("Polarization tiers:")
    for bl, bf in boards:
        r = {"board_label": bl, "board_family": bf}
        tier = _board_polarization_tier(r)
        print(f"  {bl:<10} (family={bf:<14}) → {tier}")
    print()


def main():
    import csv
    rows_path = ROOT / "research" / "v4-postflop" / "probe_phase4_rows.csv"
    if not rows_path.exists():
        print(f"NOTE: {rows_path} not found; running prediction test only.")
        _test_predictions()
        return

    correct = 0
    n = 0
    per_board = {}
    per_mv = {}
    with open(rows_path) as f:
        for row in csv.DictReader(f):
            if row["scenario_id"] != "N_cash_4bp_river":
                continue
            n += 1
            pred = cash_4bp_river_v1(row)
            ok = (pred == row["best_action"])
            if ok:
                correct += 1
            bl = row["board_label"]
            per_board.setdefault(bl, [0, 0])
            per_board[bl][0] += 1
            if ok:
                per_board[bl][1] += 1
            mv = row["mv_cat"]
            per_mv.setdefault(mv, [0, 0])
            per_mv[mv][0] += 1
            if ok:
                per_mv[mv][1] += 1

    acc = correct / n * 100 if n else 0.0
    print(f"=== cash_4bp_river_v1 vs N_cash_4bp_river ===")
    print(f"n={n:,} acc={acc:.1f}%  (baseline v15 = 60.7%)")
    print(f"\nPer-board:")
    for bl, (tot, hit) in sorted(per_board.items()):
        print(f"  {bl:<12} n={tot:>5} acc={hit/tot*100:>5.1f}%")
    print(f"\nPer-mv_cat:")
    for mv, (tot, hit) in sorted(per_mv.items(), key=lambda x: -x[1][0]):
        print(f"  {mv:<14} n={tot:>5} acc={hit/tot*100:>5.1f}%")
    print()
    _test_predictions()


if __name__ == "__main__":
    raise SystemExit(main())
