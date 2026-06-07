#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""turn_v9_test.py — Turn defense v8 → v9 改良案 (board × dv × bet_size 細分化)。

Flop v8a で「AIR × weak_draw × board」の交互作用が huge_loss 46% 削減を達成。
同様の方針で Turn defense v8 を v9 に改良する。

仮説: Turn defender でも:
  - AIR × weak_draw × dynamic では FOLD (v8 で既に部分実装)
  - AIR × weak_draw × dry/low_dry × small/medium bet では CALL (現公式の検証)
  - AIR × {FD, OESD, combo} × board × bet_size で細分化
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
WEAK_PAIR_MID = {"second_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}
STRONG_DRAW = {"flush_draw", "nut_flush_draw", "oesd", "combo_draw"}


def turn_bet_size(s):
    if "_R4" in s or "_R5" in s or "_R6" in s: return "small_33"
    if "_R7" in s or "_R8" in s or "_R9" in s: return "med_67"
    if "_R13" in s or "_R14" in s: return "big_100"
    if "_R16" in s or "_R17" in s or "_R19" in s: return "overbet_185"
    return "other"


# ── Turn defense v8 (現公式 combined R1+R2+R3) ──
def turn_def_v8(r):
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID

    if bs == "overbet_185":
        if weak_mv and weak_no_draw: return "FOLD"
        # v8 R1: dynamic + TP + no_draw → FOLD
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw": return "FOLD"
        # v8 (existing): AIR + FD on dry_high → FOLD
        if mv in AIR and dv in {"flush_draw", "nut_flush_draw"} and bf == "dry_high": return "FOLD"
        # AIR + OESD on dynamic → FOLD
        if mv in AIR and dv == "oesd" and bf in DYNAMIC_BOARDS: return "FOLD"
        return "CALL"
    else:
        # medium / small / big
        # AIR + no_draw → FOLD
        if mv in AIR and dv == "no_draw": return "FOLD"
        # v8 R2: dynamic + 弱メイド(exc 2nd_pair) + 弱ドロー → FOLD
        weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
        if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW: return "FOLD"
        # v8 R3: dynamic + OESD + 弱メイド(exc 2nd_pair) → FOLD
        if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p: return "FOLD"
        return "CALL"


# ── Turn defense v9 候補: Flop v8a と同様の AIR × weak_draw × board 拡張 ──
def turn_def_v9_a(r):
    """v8 + AIR × weak_draw × DYNAMIC × medium/small → FOLD を全 bet_size 追加。"""
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID

    if bs == "overbet_185":
        # NEW: AIR × any draw weakness × any board (overbet kills all draws on Turn)
        if mv in AIR and dv != "combo_draw": return "FOLD"
        if weak_mv and weak_no_draw: return "FOLD"
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw": return "FOLD"
        # weak pair + strong draw でも overbet では混合戦略 (mid/under pair)
        if mv in WEAK_PAIR_LOW and dv in {"oesd", "gutshot"} and bf in DYNAMIC_BOARDS: return "FOLD"
        return "CALL"
    else:
        # NEW: AIR × no_draw × all boards → FOLD (既存)
        if mv in AIR and dv == "no_draw": return "FOLD"
        # NEW: AIR × weak_draw × DYNAMIC* → FOLD (Flop v8a と同方向)
        if mv in AIR and dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
        # 弱メイド + 弱ドロー × dynamic → FOLD (v8 R2)
        weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
        if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW: return "FOLD"
        if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p: return "FOLD"
        return "CALL"


# ── Turn defense v9 候補 b: さらに細粒度 — overbet で AIR×FD on dynamic 追加 ──
def turn_def_v9_b(r):
    mv, dv, bf, bs = r["mv_cat"], r["dv_cat"], r["board_family"], r["bet_size"]
    weak_no_draw = dv in {"no_draw"} | WEAK_DRAW
    weak_mv = mv in AIR | WEAK_PAIR_LOW | WEAK_PAIR_MID

    if bs == "overbet_185":
        # AIR×non-combo はすべて FOLD (combo_draw だけ continue)
        if mv in AIR and dv != "combo_draw": return "FOLD"
        if weak_mv and weak_no_draw: return "FOLD"
        if bf in DYNAMIC_BOARDS and mv == "top_pair" and dv == "no_draw": return "FOLD"
        if mv in WEAK_PAIR_LOW and dv in {"oesd", "gutshot"} and bf in DYNAMIC_BOARDS: return "FOLD"
        # 2nd_pair も overbet では FOLD (mid-low pair line)
        if mv == "second_pair" and dv == "no_draw" and bf in DYNAMIC_BOARDS: return "FOLD"
        return "CALL"
    else:
        if mv in AIR and dv == "no_draw": return "FOLD"
        if mv in AIR and dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
        # NEW: AIR + WEAK_DRAW + monotone/paired → FOLD (low equity for non-flush hands)
        if mv in AIR and dv in WEAK_DRAW and bf in {"monotone", "paired"}: return "FOLD"
        weak_mv_no2p = mv in AIR | WEAK_PAIR_LOW
        if bf in DYNAMIC_BOARDS and weak_mv_no2p and dv in WEAK_DRAW: return "FOLD"
        if bf in DYNAMIC_BOARDS and dv == "oesd" and weak_mv_no2p: return "FOLD"
        return "CALL"


# ── Eval utilities ──
def best_ev_def(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of_def(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    if p == "RAISE": return r["ev_raise"]
    return None


def ev_gap_row(r):
    evs = [r["ev_fold"], r["ev_call"], r["ev_raise"]]
    evs = [e for e in evs if pd.notna(e)]
    if len(evs) < 2: return None
    s = sorted(evs, reverse=True)
    return s[0] - s[1]


def prep(df):
    sub = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
             df["ev_call"].notna() & df["ev_fold"].notna() &
             df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
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
    print(f"bet_size dist: {sub['bet_size'].value_counts().to_dict()}\n")

    base = evaluate(sub, turn_def_v8, "v8 (現公式)")
    v9a = evaluate(sub, turn_def_v9_a, "v9a (AIR×weak_draw×dynamic 拡張)")
    v9b = evaluate(sub, turn_def_v9_b, "v9b (+ monotone/paired/2nd_pair)")

    # AIR ハンドだけ
    print("\n=== AIR ハンドのみ (mv ∈ {no_made/ace_high/king_high}) ===")
    air = sub[sub["mv_cat"].isin(AIR)]
    print(f"AIR rows: {len(air):,}")
    evaluate(air, turn_def_v8, "v8 (AIR only)")
    evaluate(air, turn_def_v9_a, "v9a (AIR only)")
    evaluate(air, turn_def_v9_b, "v9b (AIR only)")

    # cell-level diff: v8 vs v9a
    print("\n=== AIR × dv × board × bet_size の v8 → v9a 差分 ===")
    air_c = air.copy()
    air_c["v8_pred"] = air_c.apply(turn_def_v8, axis=1)
    air_c["v9a_pred"] = air_c.apply(turn_def_v9_a, axis=1)
    diff = air_c[air_c["v8_pred"] != air_c["v9a_pred"]]
    print(f"差分 rows: {len(diff):,}")
    print(f"\n{'dv_cat':14s} {'board':18s} {'bet_size':14s} {'n':>5s} {'gto_F%':>7s} {'gto_C%':>7s} {'v8':>5s} {'v9a':>5s}")
    for (dv, bf, bs), g in diff.groupby(["dv_cat", "board_family", "bet_size"]):
        gf = g["fold_freq"].mean() * 100
        gc = g["call_freq"].mean() * 100
        v8p = g["v8_pred"].iloc[0]
        v9p = g["v9a_pred"].iloc[0]
        print(f"{dv:14s} {bf:18s} {bs:14s} {len(g):>5} {gf:>6.0f}% {gc:>6.0f}% {v8p:>5s} {v9p:>5s}")

    # v8 vs v9 改善量
    print("\n=== 全体改善量 ===")
    air_c["v8_loss"] = air_c.apply(lambda r: best_ev_def(r) - ev_of_def(r, turn_def_v8(r)), axis=1)
    air_c["v9a_loss"] = air_c.apply(lambda r: best_ev_def(r) - ev_of_def(r, turn_def_v9_a(r)), axis=1)
    air_c["v9b_loss"] = air_c.apply(lambda r: best_ev_def(r) - ev_of_def(r, turn_def_v9_b(r)), axis=1)
    huge = air_c[air_c["ev_gap"] > 0.5]
    if len(huge):
        print(f"  AIR-only huge_gap: v8={huge['v8_loss'].mean():.4f}BB, v9a={huge['v9a_loss'].mean():.4f}BB, v9b={huge['v9b_loss'].mean():.4f}BB  (n={len(huge):,})")
        print(f"  v9a 削減: {(1 - huge['v9a_loss'].mean()/huge['v8_loss'].mean())*100:.1f}%")


if __name__ == "__main__":
    raise SystemExit(main())
