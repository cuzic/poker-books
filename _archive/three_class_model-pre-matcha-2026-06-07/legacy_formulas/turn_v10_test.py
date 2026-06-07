#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""turn_v10_test.py — Turn defense v8 → v10 改良案。

turn_huge_explore の発見 (上位 5 集中地):
  1. no_made × gutshot × dry_high × other: 4150 BB total, GTO F=96%
  2. low_pair × no_draw × dynamic: 1126 BB total, GTO F=100%
  3. no_made × gutshot × monotone: 411 BB total, GTO F=100%
  4. low_pair × no_draw × small_33: GTO F=100%
  5. third_pair × no_draw × dry_high: GTO F=57%

新ルール:
  v10 = v8 + 以下追加:
    A. mv ∈ AIR ∧ board == monotone → FOLD (全 dv で fold が GTO)
    B. mv ∈ AIR ∧ dv ∈ WEAK_DRAW ∧ board != low_dry → FOLD (Turn では implied 弱)
    C. mv = low_pair ∧ dv = no_draw → FOLD (board 全部)
    D. mv = third_pair ∧ dv = no_draw ∧ board != low_dry → FOLD (拡張)

vs overbet_185 は v8 のまま (既に厳格)。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}


def turn_bet_size(s):
    if "_R4" in s or "_R5" in s or "_R6" in s: return "small_33"
    if "_R16" in s or "_R17" in s or "_R19" in s: return "overbet_185"
    return "other"


def turn_def_v8(r):
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
    weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
    if bs == "overbet_185":
        if weak_mv and weak_no_draw: return "FOLD"
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw": return "FOLD"
        if mv in AIR and dv in {"flush_draw", "nut_flush_draw"} and bf == "dry_high": return "FOLD"
        if mv in AIR and dv == "oesd" and bf in DYNAMIC_BOARDS: return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
        if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW: return "FOLD"
        if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p: return "FOLD"
        return "CALL"


def turn_def_v10(r):
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    if bs == "overbet_185":
        # v8 と同じ (既に厳格)
        weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
        weak_mv = mv in AIR | WEAK_PAIR_LOW | {"second_pair"}
        if weak_mv and weak_no_draw: return "FOLD"
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw": return "FOLD"
        if mv in AIR and dv in {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}: return "FOLD"
        return "CALL"
    else:
        # ── New v10 rules ──
        # A. AIR × monotone board → FOLD (全 dv で fold が GTO)
        if mv in AIR and bf == "monotone": return "FOLD"
        # B. AIR × weak_draw × board != low_dry → FOLD (low_dry のみ GTO は call)
        if mv in AIR and dv in WEAK_DRAW and bf != "low_dry": return "FOLD"
        # AIR × no_draw → FOLD (既存)
        if mv in AIR and dv == "no_draw": return "FOLD"
        # C. low_pair × no_draw → FOLD (board 全部)
        if mv == "low_pair" and dv == "no_draw": return "FOLD"
        # D. third_pair × no_draw × board != low_dry → FOLD
        if mv == "third_pair" and dv == "no_draw" and bf != "low_dry": return "FOLD"
        # 既存: dynamic + weak_mv_no2p + weak_draw → FOLD
        weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
        if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW: return "FOLD"
        if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p: return "FOLD"
        return "CALL"


# ── Eval ──
def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of_def(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    if p == "RAISE": return r["ev_raise"]


def ev_gap_row(r):
    evs = [e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)]
    if len(evs) < 2: return None
    s = sorted(evs, reverse=True)
    return s[0] - s[1]


def prep(df):
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
             df["ev_call"].notna() & df["ev_fold"].notna() & df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub["bet_size"] = sub["source_path"].apply(turn_bet_size)
    return sub[sub["ev_gap"].notna()]


def evaluate(sub, formula, label):
    sub_c = sub.copy()
    sub_c["pred"] = sub_c.apply(formula, axis=1)
    sub_c["ev_p"] = sub_c.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
    sub_c["loss"] = sub_c["best_ev"] - sub_c["ev_p"]
    acc = (sub_c["pred"] == sub_c["modal"]).mean() * 100
    mean_l = sub_c["loss"].mean()
    huge = sub_c[sub_c["ev_gap"] > 0.5]
    huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
    print(f"  {label:35s} n={len(sub_c):>6} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={len(huge)})={huge_l:.4f}BB")
    return sub_c


def main():
    df = pd.read_csv(DATA, low_memory=False)
    sub = prep(df)
    print(f"=== Turn defense — n={len(sub):,} rows ===\n")

    base = evaluate(sub, turn_def_v8, "v8 (現公式)")
    v10 = evaluate(sub, turn_def_v10, "v10 (board × dv × mv 拡張)")

    # AIR only
    print("\n=== AIR only ===")
    air = sub[sub["mv_cat"].isin(AIR)]
    evaluate(air, turn_def_v8, "v8 (AIR only)")
    evaluate(air, turn_def_v10, "v10 (AIR only)")

    # low_pair only
    print("\n=== low_pair only ===")
    lp = sub[sub["mv_cat"] == "low_pair"]
    evaluate(lp, turn_def_v8, "v8 (low_pair only)")
    evaluate(lp, turn_def_v10, "v10 (low_pair only)")

    # 全体 huge_loss 改善
    sub_c = sub.copy()
    sub_c["v8_loss"] = sub_c.apply(lambda r: best_ev_def(r) - ev_of_def(r, turn_def_v8(r)), axis=1)
    sub_c["v10_loss"] = sub_c.apply(lambda r: best_ev_def(r) - ev_of_def(r, turn_def_v10(r)), axis=1)
    huge = sub_c[sub_c["ev_gap"] > 0.5]
    print(f"\n=== 全体 huge_gap 改善 ===")
    print(f"  v8 huge_loss: {huge['v8_loss'].mean():.4f}BB (total {huge['v8_loss'].sum():.0f}BB)")
    print(f"  v10 huge_loss: {huge['v10_loss'].mean():.4f}BB (total {huge['v10_loss'].sum():.0f}BB)")
    print(f"  削減: {huge['v8_loss'].sum() - huge['v10_loss'].sum():.0f}BB ({(1 - huge['v10_loss'].mean()/huge['v8_loss'].mean())*100:.1f}% 改善)")


if __name__ == "__main__":
    raise SystemExit(main())
