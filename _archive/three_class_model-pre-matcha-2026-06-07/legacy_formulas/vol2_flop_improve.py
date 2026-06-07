#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Vol2 Flop 公式の改善案を検証.

現状 (Vol2 ch04 + ch05 補正):
  W (= A-high/K-high/low_pair) × m → CALL
  + Flop 補正: low_pair/3rd_pair × no_draw × dry → FOLD

改善案 (4 候補):
  v2: + A-high/K-high × no_draw × m → FOLD (AIR 扱い拡張)
  v3: + overpair × m → RAISE (value raise の追加)
  v4: v2 + v3 統合
  v5: v4 + 3rd_pair × no_draw × dynamic → FOLD (extra correction)
"""
from __future__ import annotations

from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

S_HANDS = {"two_pair", "set", "trips", "straight", "flush",
           "fullhouse", "quads", "overpair", "straight_flush"}
M_HANDS = {"top_pair", "second_pair", "third_pair", "underpair"}
STRONG_DRAWS = {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}


def vol2_current(r):
    """現状: 純粋 Vol2 + 街補正 (本書 ch05)."""
    mv, dv = r["mv_cat"], r["dv_cat"]
    bf = r["board_family"]
    # 分類
    if mv in S_HANDS: cat = "S"
    elif mv in M_HANDS: cat = "M"
    elif mv == "low_pair": cat = "W"
    elif dv in STRONG_DRAWS and mv in {"no_made_hand", "ace_high", "king_high"}:
        cat = "D"
    elif mv in {"ace_high", "king_high"}: cat = "W"
    else: cat = "A"

    # m サイズ (Flop)
    base = {"S": "CALL", "M": "CALL", "W": "CALL", "A": "FOLD", "D": "CALL"}[cat]

    # Flop ch05 補正: low_pair/3rd_pair × no_draw × dry → FOLD
    if mv in {"low_pair", "third_pair"} and dv == "no_draw":
        if bf in {"dry_high", "low_dry", "dynamic_2tone"}:
            return "FOLD"
    return base


def vol2_v2_AKair(r):
    """改善 v2: A-high/K-high × no_draw を AIR 扱い (FOLD on m+)."""
    base = vol2_current(r)
    mv, dv = r["mv_cat"], r["dv_cat"]
    # 追加補正: A-high/K-high × no_draw on Flop → FOLD
    if mv in {"ace_high", "king_high"} and dv == "no_draw":
        return "FOLD"
    return base


def vol2_v3_overpairRAISE(r):
    """改善 v3: overpair → RAISE."""
    base = vol2_current(r)
    mv = r["mv_cat"]
    if mv == "overpair":
        return "RAISE"
    return base


def vol2_v4_combined(r):
    """改善 v4: v2 + v3 統合."""
    mv, dv = r["mv_cat"], r["dv_cat"]
    if mv == "overpair": return "RAISE"
    if mv in {"ace_high", "king_high"} and dv == "no_draw": return "FOLD"
    return vol2_current(r)


def vol2_v5_extra(r):
    """改善 v5: v4 + 3rd_pair × no_draw × dynamic → FOLD."""
    mv, dv = r["mv_cat"], r["dv_cat"]
    bf = r["board_family"]
    if mv == "overpair": return "RAISE"
    if mv in {"ace_high", "king_high"} and dv == "no_draw": return "FOLD"
    if mv == "third_pair" and dv == "no_draw" and bf in {"dynamic", "monotone"}:
        return "FOLD"
    return vol2_current(r)


def vol3_v7(r):
    """Vol3 詳細 (参考、上限)."""
    mv, dv = r["mv_cat"], r["dv_cat"]
    bf = r["board_family"]
    AIR = {"no_made_hand", "ace_high", "king_high"}
    if mv in AIR and dv == "no_draw": return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in {"dry_high", "low_dry", "dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair": return "RAISE"
    return "CALL"


def best_ev(r):
    evs = [e for e in [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise")] if pd.notna(e)]
    return max(evs) if evs else float("nan")


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_gap(r):
    evs = sorted([e for e in [r.get("ev_fold"), r.get("ev_call"), r.get("ev_raise")] if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[(df["street"] == "flop") & (df["action_context"] == "defense") &
              df["source_path"].str.contains("def_cash100_bb_raw") &
              df["ev_call"].notna() & df["ev_fold"].notna()].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap, axis=1)
    sub = sub[sub["ev_gap"].notna()].copy()

    # baseline
    baseline_huge = sub[sub["ev_gap"] > 0.5]
    always_call_loss = (baseline_huge["best_ev"] - baseline_huge["ev_call"]).mean()

    print(f"\n=== Cash 100bb Flop defense — 改善検証 ===")
    print(f"n={len(sub)}, huge_gap n={len(baseline_huge)}")
    print(f"always_CALL huge_loss baseline: {always_call_loss:.4f} BB\n")

    print(f"{'公式':40s} {'acc':>7s} {'mean':>10s} {'huge':>10s} {'削減率':>10s}")
    print("-" * 80)
    for name, f in [
        ("Vol2 現状 (ch04 + ch05 補正)", vol2_current),
        ("Vol2 + v2 (A/K-high → A)", vol2_v2_AKair),
        ("Vol2 + v3 (overpair RAISE)", vol2_v3_overpairRAISE),
        ("Vol2 + v4 (v2+v3 統合)", vol2_v4_combined),
        ("Vol2 + v5 (+ 3rd dynamic FOLD)", vol2_v5_extra),
        ("Vol3 v7 (詳細、上限参考)", vol3_v7),
    ]:
        s = sub.copy()
        s["pred"] = s.apply(f, axis=1)
        s["ev_p"] = s.apply(lambda r: ev_of(r, r["pred"]), axis=1)
        s["loss"] = s["best_ev"] - s["ev_p"]
        acc = (s["pred"] == s["modal"]).mean() * 100
        mean_l = s["loss"].mean()
        huge = s[s["ev_gap"] > 0.5]
        huge_l = huge["loss"].mean()
        reduction = (always_call_loss - huge_l) / always_call_loss * 100
        print(f"  {name:40s} {acc:6.1f}% {mean_l:9.4f}BB {huge_l:9.4f}BB {reduction:8.1f}%")

    print(f"\n=== huge_gap セル別の改善要因分析 ===")
    s = sub.copy()
    s["pred_v4"] = s.apply(vol2_v4_combined, axis=1)
    s["ev_v4"] = s.apply(lambda r: ev_of(r, r["pred_v4"]), axis=1)
    s["loss_v4"] = s["best_ev"] - s["ev_v4"]
    s["pred_curr"] = s.apply(vol2_current, axis=1)
    s["ev_curr"] = s.apply(lambda r: ev_of(r, r["pred_curr"]), axis=1)
    s["loss_curr"] = s["best_ev"] - s["ev_curr"]
    s["improvement"] = s["loss_curr"] - s["loss_v4"]
    huge_s = s[s["ev_gap"] > 0.5].copy()
    big_improve = huge_s[huge_s["improvement"] > 0.5].copy()
    print(f"\nv4 で改善した huge_gap セル (loss 0.5+ 削減)：")
    print(f"  n={len(big_improve)} (出 huge_gap {len(huge_s)} 中 {len(big_improve)/len(huge_s)*100:.1f}%)")
    if len(big_improve) > 0:
        agg = big_improve.groupby(["mv_cat", "dv_cat", "board_family"]).agg(
            n=("improvement", "count"),
            avg_improve=("improvement", "mean"),
        ).reset_index().sort_values("avg_improve", ascending=False).head(10)
        for _, r in agg.iterrows():
            print(f"    mv={r['mv_cat']:14s} × dv={r['dv_cat']:15s} × bf={r['board_family']:18s} n={int(r['n']):3d} avg_improve={r['avg_improve']:.3f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
