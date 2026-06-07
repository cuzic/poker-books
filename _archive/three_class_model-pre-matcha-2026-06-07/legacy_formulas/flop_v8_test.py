#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""flop_v8_test.py — Flop defense v7 → v8 改良案の検証。

仮説 (huge_gap_subdivide.py の発見より):
  AIR × weak_draw は board_family で挙動が逆になる:
    - dry_high / low_dry: GTO は CALL 多 (63%, 66%) — implied odds 良
    - dynamic / dynamic_2tone: GTO は FOLD 多 (60-79%) — equity 薄

v7 の単純 "AIR × no_draw → FOLD" を board 依存 v8 に拡張する。
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
STRONG = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}


# ── Flop defense v7 (現公式) ──
def flop_def_v7(r):
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    if mv in AIR and dv == "no_draw":
        return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair":
        return "RAISE"
    return "CALL"


# ── Flop defense v8 候補 1: AIR×weak_draw を board で分岐 ──
def flop_def_v8_a(r):
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    # AIR の処理 (新)
    if mv in AIR:
        if dv == "no_draw":
            return "FOLD"  # v7 と同じ
        if dv in WEAK_DRAW:
            if bf in DYNAMIC_BOARDS:
                return "FOLD"  # NEW: dynamic では弱ドロー air も fold
            else:
                return "CALL"  # NEW: dry/low_dry では弱ドロー air は call (default)
        # FD/OESD/combo はそのまま CALL (default)
    # 既存ルール継続
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair":
        return "RAISE"
    return "CALL"


# ── Flop defense v8 候補 2: さらに細かく twocards_bdfd だけ別扱い ──
def flop_def_v8_b(r):
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    if mv in AIR:
        if dv == "no_draw":
            return "FOLD"
        if dv == "gutshot":
            # gutshot は dry で CALL、dynamic で FOLD (huge_gap 解析より)
            return "FOLD" if bf in DYNAMIC_BOARDS else "CALL"
        if dv in {"twocards_bdfd", "onecard_bdfd"}:
            # BDFD は dry のみ CALL
            if bf in DRY_BOARDS:
                return "CALL"
            else:
                return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair":
        return "RAISE"
    return "CALL"


# ── Evaluation utilities ──
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
    sub = df[(df["street"] == "flop") & (df["action_context"] == "defense") &
             df["ev_call"].notna() & df["ev_fold"].notna() &
             df["mv_cat"].notna() & (df["mv_cat"] != "")].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev_def, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    return sub[sub["ev_gap"].notna()]


def evaluate(sub, formula, label, focus_air=False):
    sub_c = sub.copy()
    sub_c["pred"] = sub_c.apply(formula, axis=1)
    sub_c["ev_p"] = sub_c.apply(lambda r: ev_of_def(r, r["pred"]), axis=1)
    sub_c["loss"] = sub_c["best_ev"] - sub_c["ev_p"]
    acc = (sub_c["pred"] == sub_c["modal"]).mean() * 100
    mean_l = sub_c["loss"].mean()
    huge = sub_c[sub_c["ev_gap"] > 0.5]
    huge_l = huge["loss"].mean() if len(huge) > 0 else float("nan")
    n_huge = len(huge)
    print(f"  {label:35s} n={len(sub_c):>6} acc={acc:5.1f}% mean={mean_l:.4f}BB huge(n={n_huge})={huge_l:.4f}BB")
    if focus_air:
        air_only = sub_c[sub_c["mv_cat"].isin(AIR)]
        air_h = air_only[air_only["ev_gap"] > 0.5]
        if len(air_only):
            print(f"    └─ AIR only: n={len(air_only):>6} acc={(air_only['pred']==air_only['modal']).mean()*100:.1f}% huge(n={len(air_h)})={air_h['loss'].mean() if len(air_h) else 0:.4f}BB")
    return sub_c


def main():
    df = pd.read_csv(DATA, low_memory=False)
    sub = prep(df)
    print(f"=== Flop defense — n={len(sub):,} rows ===\n")

    base_v7 = evaluate(sub, flop_def_v7, "v7 (現公式)", focus_air=True)
    print()
    v8a = evaluate(sub, flop_def_v8_a, "v8a (AIR×weak_draw board分岐)", focus_air=True)
    print()
    v8b = evaluate(sub, flop_def_v8_b, "v8b (gutshot/BDFD 別扱い)", focus_air=True)

    # 詳細: AIR × weak_draw × board 別の v7 vs v8a 比較
    print(f"\n=== AIR × weak_draw × board の cell-level 比較 ===")
    air_wd = sub[sub["mv_cat"].isin(AIR) & sub["dv_cat"].isin(WEAK_DRAW)]
    print(f"対象 rows: {len(air_wd):,}")
    print(f"\n{'dv_cat':15s} {'board':18s} {'n':>5s} {'gto_call%':>10s} {'v7_pred':>8s} {'v8a_pred':>9s} {'v7_huge':>9s} {'v8a_huge':>9s}")
    for (dv, bf), g in air_wd.groupby(["dv_cat", "board_family"]):
        gto_c = g["call_freq"].mean() * 100
        v7_p = flop_def_v7(g.iloc[0])
        v8a_p = flop_def_v8_a(g.iloc[0])
        # huge loss
        huge_v7 = g.copy()
        huge_v7["loss"] = huge_v7.apply(lambda r: best_ev_def(r) - ev_of_def(r, flop_def_v7(r)), axis=1)
        huge_v8a = g.copy()
        huge_v8a["loss"] = huge_v8a.apply(lambda r: best_ev_def(r) - ev_of_def(r, flop_def_v8_a(r)), axis=1)
        h7 = huge_v7[huge_v7["ev_gap"] > 0.5]
        h8 = huge_v8a[huge_v8a["ev_gap"] > 0.5]
        h7_l = h7["loss"].mean() if len(h7) else 0
        h8_l = h8["loss"].mean() if len(h8) else 0
        print(f"{dv:15s} {bf:18s} {len(g):>5} {gto_c:>9.0f}% {v7_p:>8s} {v8a_p:>9s} {h7_l:>8.3f} {h8_l:>8.3f}")

    # AIR × weak_draw 領域での総改善
    print(f"\n=== AIR × weak_draw 領域での v7 → v8a 改善量 ===")
    air_wd_c = air_wd.copy()
    air_wd_c["v7_loss"] = air_wd_c.apply(lambda r: best_ev_def(r) - ev_of_def(r, flop_def_v7(r)), axis=1)
    air_wd_c["v8a_loss"] = air_wd_c.apply(lambda r: best_ev_def(r) - ev_of_def(r, flop_def_v8_a(r)), axis=1)
    print(f"  mean loss: v7={air_wd_c['v7_loss'].mean():.4f}BB, v8a={air_wd_c['v8a_loss'].mean():.4f}BB")
    huge = air_wd_c[air_wd_c["ev_gap"] > 0.5]
    if len(huge):
        print(f"  huge_gap loss: v7={huge['v7_loss'].mean():.4f}BB, v8a={huge['v8a_loss'].mean():.4f}BB  (n={len(huge):,})")
        print(f"  改善: {(huge['v7_loss'].mean() - huge['v8a_loss'].mean()):.4f}BB ({(1 - huge['v8a_loss'].mean()/huge['v7_loss'].mean())*100:.1f}% 削減)")


if __name__ == "__main__":
    raise SystemExit(main())
