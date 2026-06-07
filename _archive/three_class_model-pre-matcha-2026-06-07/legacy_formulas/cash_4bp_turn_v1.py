#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Cash 4BP Turn v1 — 4BP turn 専用ロジック

Domain
------
Cash 100bb, BB OOP defense vs IP turn overbet_185 in a 4-bet pot (4BP).
SPR ~1.0, range = QQ+/AK tight.

Data source
-----------
- research/v4-postflop/probe_phase4_stats.json [N_cash_4bp_turn]
  (n=6768 hand-level rows, 6 boards, formula_acc=49.4% with v10 baseline)
- research/v4-postflop/probe_phase4_rows.csv (per-row best_action)
- MTT 100bb 4BP turn (P6_A_mtt_4bp_turn) — acc 48.5%、Cash と同構造

Key findings (data)
-------------------
opp_polarization_mean = 0.54 (SRP turn 0.79 と質的に異なる)
opp_strong_pct_mean = 0.14
opp_weak_pct_mean = 0.41
modal F/C/R = 38.6 / 37.4 / 24.0% (3-way 殆ど均等!)

Per-mv_cat best_action distribution:
  top_pair      → RAISE 79.9%      (常 RAISE — value で commit)
  overpair      → RAISE 68.4%
  underpair     → RAISE 76.3%      (4BP では QQ underpair も RAISE!)
  two_pair      → RAISE 68.5%      (slowplay やめて value)
  set           → RAISE 63.9%
  second_pair   → RAISE 61.0%      (4BP 特有 — 板別)
  trips         → CALL 70%, R 30%  (slowplay)
  fullhouse     → CALL 100%        (slowplay 確定)
  straight      → CALL 100%
  third_pair    → CALL 68.5%
  low_pair      → CALL 89.1%       (overbet vs low pair: CALL 主流)
  ace_high      → FOLD 36, CALL 57 (board 依存)
  king_high     → FOLD 57.8%       (board K でなければ FOLD)
  no_made_hand  → FOLD 81.3%       (overbet × air → FOLD)

Per-board × top_pair:
  dry_K72   → R 88%, d2t_T97 → R 97%, low_853 → R 100%, dyn_T97 → R 98%
  mono_Js   → C 77% (monotone は board 危険、TP slowplay)
  pair_KK2  → no data (TP on KK2 is rare; underpair becomes effectively TP)

Per-board × ace_high × no_draw:
  dry_K72   → CALL 85%, low_853 → CALL 69%, pair_KK2 → CALL 67%
  d2t_T97   → CALL 41%, FOLD 59%
  mono_Js   → FOLD 60%
  dyn_T97   → FOLD 53%, CALL 47% (mixed)

AIR × dv_cat:
  no_made × no_draw         → FOLD 93.8%
  no_made × gutshot         → FOLD 83.7%
  no_made × oesd            → mixed (F 51, C 34, R 14)
  no_made × flush_draw      → mixed (F 50, C 39, R 11)
  no_made × combo_draw      → CALL 46, R 39, F 14 (実質 continue)

Design philosophy
-----------------
APPROACH (b) — Decisive cut.
理由: 暗算式として書籍に載せるには deterministic な F/C/R 必要。
ただし limitations を docstring で正直に提示:
  - opp_polarization 0.54 で 3 択ほぼ均等という事実上、誤差 ~25% は不可避
  - 確率分布 tier mapping を本書付録に併記する設計を推奨

Decision logic:
  1. value made (TP+, op/up, 2P, set): RAISE (over multi-board)
       Exception: mono_Js × TP → CALL (flush 危険、slowplay)
  2. nut made (str/flush/full): CALL (slowplay vs committed opp)
  3. trips: CALL ≈ R mix → CALL baseline
  4. second_pair: board × board family で RAISE or CALL
  5. third/low pair: CALL (overbet vs marginal pair で fold は EV 取り過ぎ)
  6. AIR + strong draw (combo/flush/oesd): CALL (equity 30%+)
  7. AIR + weak (gutshot/bdfd/no_draw): FOLD
  8. ace_high: board safe (dry_K72/low_853/pair_KK2) → CALL、それ以外 → FOLD
  9. king_high: 全 FOLD (overbet には足りない)

Target: acc > 55% (baseline v10 = 49.4%, +5+ ppts improvement; realistic)

Limitations (honest)
--------------------
4BP turn の F/C/R が 38/37/24% で 3-way 均等のため、deterministic 公式の
理論上 ceiling は ~60-65%。これ以上は確率混合 (tier mapping) でしか達成不可。
書籍では「公式で 6 割、残り 4 割は GTO mix を暗記」として伝える設計を推奨。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
STRONG_DRAW = {"oesd", "flush_draw", "nut_flush_draw", "combo_draw"}
WEAK_DRAW = {"gutshot", "twocards_bdfd", "onecard_bdfd"}
DRY = {"dry_high", "low_dry"}
DYNAMIC = {"dynamic", "dynamic_2tone"}


def cash_4bp_turn_v1(r) -> str:
    """4BP turn defense vs IP overbet_185 (SPR ~1).

    Decision tree:
      1. Nut made (str/flush/full/quads): CALL (slowplay)
      2. Trips: CALL (slowplay; data: C 70%)
      3. Top tier value (TP, OP, 2P, set): RAISE — exception monotone × TP → CALL
      4. Mid value (UP, second_pair): RAISE on most boards; CALL on monotone & pair
      5. Marginal pair (third/low): CALL (overbet vs marginal は EV loss 抑制)
      6. AIR + strong draw: CALL (equity保持)
      7. AIR + weak/no_draw: FOLD (但し ace_high は board 別 CALL/FOLD)
    """
    mv = r["mv_cat"]
    dv = r["dv_cat"]
    bf = r["board_family"]

    # ── 1) Nut made: slowplay ──
    if mv in {"fullhouse", "quads", "straight", "flush"}:
        return "CALL"

    # ── 2) Trips: slowplay-ish (data 70% C / 30% R) ──
    if mv == "trips":
        return "CALL"

    # ── 3) Top tier value: RAISE (data 79-98% R), exception monotone × TP ──
    if mv == "top_pair":
        if bf == "monotone":
            return "CALL"      # mono_Js × TP は CALL 77% (flush 危険)
        return "RAISE"
    if mv == "overpair":
        if bf == "monotone":
            return "CALL"      # 同上
        return "RAISE"
    if mv in {"two_pair", "set"}:
        if bf == "monotone":
            return "CALL"      # 2P/set on mono: slowplay vs flush 危険
        return "RAISE"

    # ── 4) Mid value ──
    if mv == "underpair":
        # data: UP RAISE 76% global, mono_Js は CALL 50/R 50
        if bf == "monotone":
            return "CALL"
        if bf == "paired":
            return "RAISE"     # KK2 × UP(QQ): RAISE 67%
        if bf in DRY:
            return "RAISE"
        return "RAISE"
    if mv == "second_pair":
        # board 別:
        #   dry_K72/low_853 → RAISE 85-92%
        #   dyn_T97/d2t_T97 → C 63-67% (危険板 — slowdown)
        #   mono_Js → CALL 87%
        #   pair_KK2 → RAISE 100% (TP-equivalent)
        if bf == "paired":
            return "RAISE"
        if bf in DRY:
            return "RAISE"
        if bf == "monotone":
            return "CALL"
        if bf in DYNAMIC:
            return "CALL"     # 危険板では CALL
        return "CALL"

    # ── 5) Marginal pair: CALL ──
    if mv in {"third_pair", "low_pair"}:
        return "CALL"

    # ── 6) AIR + strong draw: CALL ──
    if mv in AIR and dv in STRONG_DRAW:
        return "CALL"

    # ── 7) AIR + weak/no_draw: ace_high は board 別、それ以外 FOLD ──
    if mv == "ace_high":
        # ace_high: 板絶対安全 → CALL、それ以外 FOLD
        # data: dry_K72 C85, low_853 C69, pair_KK2 C67 → CALL
        #       d2t_T97 F59, mono_Js F60, dyn_T97 F53 → FOLD
        if bf in {"dry_high", "low_dry", "paired"}:
            return "CALL"
        return "FOLD"
    # king_high / no_made_hand: 殆ど常に FOLD
    return "FOLD"


def best_ev(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def _test_predictions():
    print("=== cash_4bp_turn_v1 per-board predictions ===\n")
    boards = ["dry_K72", "d2t_T97", "mono_Js", "low_853", "dyn_T97", "pair_KK2"]
    families = ["dry_high", "dynamic_2tone", "monotone", "low_dry", "dynamic", "paired"]
    test_cells = [
        ("top_pair", "no_draw"),
        ("overpair", "no_draw"),
        ("two_pair", "no_draw"),
        ("set", "no_draw"),
        ("second_pair", "no_draw"),
        ("third_pair", "no_draw"),
        ("low_pair", "no_draw"),
        ("underpair", "no_draw"),
        ("no_made_hand", "no_draw"),
        ("no_made_hand", "oesd"),
        ("no_made_hand", "flush_draw"),
        ("ace_high", "no_draw"),
        ("king_high", "no_draw"),
        ("straight", "no_draw"),
    ]
    header = f"{'mv':<14} {'dv':<13}" + "".join(f"{b:>10}" for b in boards)
    print(header)
    print("-" * len(header))
    for mv, dv in test_cells:
        row = f"{mv:<14} {dv:<13}"
        for bf in families:
            r = {"mv_cat": mv, "dv_cat": dv, "board_family": bf}
            row += f"{cash_4bp_turn_v1(r):>10}"
        print(row)
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
            if row["scenario_id"] != "N_cash_4bp_turn":
                continue
            n += 1
            pred = cash_4bp_turn_v1(row)
            ok = (pred == row["best_action"])
            if ok:
                correct += 1
            bf = row["board_label"]
            per_board.setdefault(bf, [0, 0])
            per_board[bf][0] += 1
            if ok:
                per_board[bf][1] += 1
            mv = row["mv_cat"]
            per_mv.setdefault(mv, [0, 0])
            per_mv[mv][0] += 1
            if ok:
                per_mv[mv][1] += 1

    acc = correct / n * 100 if n else 0.0
    print(f"=== cash_4bp_turn_v1 vs N_cash_4bp_turn ===")
    print(f"n={n:,} acc={acc:.1f}%  (baseline v10 = 49.4%)")
    print(f"\nPer-board:")
    for bf, (tot, hit) in sorted(per_board.items()):
        print(f"  {bf:<12} n={tot:>5} acc={hit/tot*100:>5.1f}%")
    print(f"\nPer-mv_cat:")
    for mv, (tot, hit) in sorted(per_mv.items(), key=lambda x: -x[1][0]):
        print(f"  {mv:<14} n={tot:>5} acc={hit/tot*100:>5.1f}%")
    print()
    _test_predictions()


if __name__ == "__main__":
    raise SystemExit(main())
