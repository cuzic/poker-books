#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Cash 4BP Flop v1 — 4BP 専用ロジック (SRP 由来の v9b が破綻したため)

Domain
------
Cash 100bb, BB OOP defense vs IP overbet on flop in a 4-bet pot (4BP).
SPR ~1.5, range = QQ+/AK tight (high whiff rate).

Data source
-----------
- research/v4-postflop/probe_priority_stats.json [N_cash_4bp_flop]
  (n=7056 hand-level rows, 6 boards, formula_acc=43.9% with v9b baseline)
- research/v4-postflop/probe_priority_rows.csv (per-row best_action)
- MTT 100bb 4BP is structurally identical
  (P6_A_mtt_4bp_flop acc=40.3% with v9b → same formula 流用可)

Key findings (data)
-------------------
opp_polarization_mean = 0.65 (NOT polar — SRP flop is 0.95+)
opp_weak_pct_mean = 0.57 (opp range is 57% air — range tight で flop hit 率低い)
opp_strong_pct_mean = 0.086 (strong opp 9% のみ)
modal CALL = 57%, modal FOLD = 17%, modal RAISE = 26%

Per-mv_cat best_action distribution (across all 6 boards):
  top_pair      → RAISE 91.8%   (常 RAISE)
  overpair      → RAISE 73.7%   (常 RAISE)
  two_pair      → CALL 71.9%    (RAISE 28%; 4BP では 2P は slowplay 寄り)
  set           → CALL 93.3%    (4BP の set は call 流入)
  second_pair   → RAISE 60.5%   (4BP では sd_pair でも prot raise が GTO)
  underpair     → RAISE 65%     (QQ-JJ overpair-ish、prot raise)
  third_pair    → CALL 86.1%
  low_pair      → CALL 100%
  ace_high      → CALL 82.5%    (AK overcards、CHEAP)
  king_high     → CALL 68.1%, FOLD 22% (board K だと KQ で TP → 別判定)
  no_made_hand  → CALL 50.6%, FOLD 34.5%, RAISE 14.9% (board 別に分岐)

Per-board AIR (no_made/ace_high/king_high) × no_draw best_action:
  dry_K72       → mixed (F 40%, C 30%, R 29%) — board hit 率低、bluff raise mix
  d2t_T97       → FOLD 64% (危険板)
  dynamic_2tone → FOLD 84% (最も危険)
  low_dry       → CALL 73.7% (board 安全、call 安い)
  monotone      → FOLD 60.7% (flush 完成)
  paired        → CALL 66.4% (board KK2 → bluff catch 安い)

Design philosophy
-----------------
"In 4BP flop, FOLD is rarely correct because:
 (a) opp is 57% air (high whiff),
 (b) SPR<1.5 makes calling cheap (price ~3:1),
 (c) we have to defend MDF on opp's overbet.
 SRP の 'AIR × no_draw → FOLD' は **完全に逆方向**。"

The formula reduces to 4 tiers:
  1. value (TP+/overpair): RAISE for protection
  2. medium (second_pair/underpair/two_pair/set): CALL or RAISE by board
  3. marginal pair (third_pair/low_pair): CALL
  4. AIR: board-dependent (dry/paired/low_dry → CALL, monotone/dynamic → FOLD)

Target: acc > 60% (baseline v9b = 43.9%, +16 ppts improvement)
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

# ── Hand category sets ──
AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}
STRONG_DRAW = {"oesd", "flush_draw", "nut_flush_draw", "combo_draw"}

# ── Board family sets ──
DRY = {"dry_high", "low_dry"}           # K72, 853 等 — safe boards
DYNAMIC = {"dynamic", "dynamic_2tone"}  # T97 等 — opp の hit 率高い、危険
PAIRED = {"paired"}                     # KK2 — pair で bluff catch 安全
MONO = {"monotone"}                     # Js7s3s — flush 完成


def cash_4bp_flop_v1(r) -> str:
    """4BP flop defense for BB OOP, vs IP overbet (SPR ~1.5).

    Decision tree (top-down):
      1. Strong made hands (TP+, overpair, set, 2P): RAISE/CALL by hand class
      2. Medium pairs (sd_pair / underpair): RAISE for protection (4BP-specific!)
      3. Weak pairs (3rd/low): CALL (board cheap)
      4. AIR + strong draw: CALL/RAISE (equity warrants continuation)
      5. AIR + weak draw or no draw: board-dependent (DEFAULT NOT FOLD)
    """
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]

    # ── 1) Top tier value: RAISE always (data: 73-92% RAISE) ──
    if mv in {"top_pair", "overpair"}:
        return "RAISE"

    # ── 2) Mid value: 4BP の 2P/set は call (slowplay; data 72-93% CALL) ──
    if mv in {"two_pair", "set"}:
        return "CALL"
    if mv in {"trips", "straight", "flush", "fullhouse", "quads"}:
        return "CALL"  # very rare on flop; slowplay against committed opp

    # ── 3) Second pair / underpair: RAISE for protection
    #     (data: second_pair RAISE 60%, underpair RAISE 65%; 4BP 特有) ──
    if mv in {"second_pair", "underpair"}:
        # Exception: monotone board with second_pair → CALL (flush 危険)
        if bf == "monotone":
            return "CALL"
        return "RAISE"

    # ── 4) Weak pairs: cheap CALL ──
    if mv in {"third_pair", "low_pair"}:
        return "CALL"

    # ── 5) AIR + strong draw → CALL (equity ~30%+ vs polarized) ──
    if mv in AIR and dv in STRONG_DRAW:
        return "CALL"

    # ── 6) AIR + gutshot/bdfd (weak draw) → board-dependent
    #      gutshot は dynamic/monotone でも CALL (data: 65-100% CALL across boards) ──
    if mv in AIR and dv in WEAK_DRAW:
        if bf == "monotone" and dv != "twocards_bdfd":
            return "CALL"
        if bf in DYNAMIC:
            return "CALL"          # gutshot × dynamic は CALL (equity あり)
        if bf in PAIRED | {"low_dry"}:
            return "CALL"
        if bf == "dry_high":
            return "CALL"          # bdfd/gutshot × dry_high → CALL or RAISE
        return "FOLD"

    # ── 7) AIR + no_draw → board-dependent ──
    if mv in AIR and dv == "no_draw":
        # ace_high は overcards 価値あり → CALL ベース (FOLD は king_high/no_made のみ)
        if mv == "ace_high":
            if bf == "dynamic_2tone":
                return "FOLD"      # data: F=59%、最も危険
            return "CALL"
        # paired board: bluff catch 安全 → CALL
        if bf == "paired":
            return "CALL"
        # low_dry (853): 絶対安全 → CALL
        if bf == "low_dry":
            return "CALL"
        # dry_high (K72): no_made_hand は mix(F41/C30/R36) → FOLD baseline、king_high は FOLD 43%
        if bf == "dry_high":
            return "FOLD"
        # dynamic / dynamic_2tone / monotone: 板危険 → FOLD
        return "FOLD"

    # Default fallback (should not reach)
    return "CALL"


def best_ev(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


# ── Per-board prediction test (CORE_BOARDS) ──
def _test_predictions():
    """Show formula predictions on representative cells per board."""
    print("=== cash_4bp_flop_v1 per-board predictions ===\n")
    boards = ["dry_K72", "d2t_T97", "mono_Js", "low_853", "dyn_T97", "pair_KK2"]
    families = ["dry_high", "dynamic_2tone", "monotone", "low_dry", "dynamic", "paired"]
    test_cells = [
        ("top_pair", "no_draw"),
        ("overpair", "no_draw"),
        ("second_pair", "no_draw"),
        ("third_pair", "no_draw"),
        ("low_pair", "no_draw"),
        ("no_made_hand", "no_draw"),
        ("no_made_hand", "gutshot"),
        ("no_made_hand", "flush_draw"),
        ("ace_high", "no_draw"),
        ("king_high", "no_draw"),
    ]
    header = f"{'mv':<14} {'dv':<13}" + "".join(f"{b:>10}" for b in boards)
    print(header)
    print("-" * len(header))
    for mv, dv in test_cells:
        row = f"{mv:<14} {dv:<13}"
        for bf in families:
            r = {"mv_cat": mv, "dv_cat": dv, "board_family": bf}
            row += f"{cash_4bp_flop_v1(r):>10}"
        print(row)
    print()


def main():
    """Run formula against actual N_cash_4bp_flop data and report acc."""
    import csv
    rows_path = ROOT / "research" / "v4-postflop" / "probe_priority_rows.csv"
    if not rows_path.exists():
        print(f"NOTE: {rows_path} not found; running prediction test only.")
        _test_predictions()
        return

    correct = 0
    n = 0
    per_board = {}
    with open(rows_path) as f:
        for row in csv.DictReader(f):
            if row["scenario_id"] != "N_cash_4bp_flop":
                continue
            n += 1
            pred = cash_4bp_flop_v1(row)
            ok = (pred == row["best_action"])
            if ok:
                correct += 1
            bf = row["board_label"]
            per_board.setdefault(bf, [0, 0])
            per_board[bf][0] += 1
            if ok:
                per_board[bf][1] += 1

    acc = correct / n * 100 if n else 0.0
    print(f"=== cash_4bp_flop_v1 vs N_cash_4bp_flop ===")
    print(f"n={n:,} acc={acc:.1f}%  (baseline v9b = 43.9%)")
    print(f"\nPer-board:")
    for bf, (tot, hit) in sorted(per_board.items()):
        print(f"  {bf:<12} n={tot:>5} acc={hit/tot*100:>5.1f}%")
    print()
    _test_predictions()


if __name__ == "__main__":
    raise SystemExit(main())
