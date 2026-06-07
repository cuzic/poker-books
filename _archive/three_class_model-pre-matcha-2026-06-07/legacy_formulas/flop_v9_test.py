#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Flop v9 — v8a の境界 cell 修正版

修正対象:
1. **AIR × BDFD × dry/low_dry**: Cash100/MTT100 で modal FOLD だが v8a CALL → 1.4-2.7 BB loss
   - 単純解 (v9a): 全 depth で FOLD
   - depth-aware (v9b): depth ≥ 60 で FOLD、それ未満は CALL (short stack implied odds)
2. **MTT 短スタック CR (third_pair × dry × no_draw)**: modal RAISE 91-93%
   - v8a は FOLD → loss 2.06 BB
   - v9: depth ≤ 50 のとき third_pair × dry × no_draw → RAISE
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

AIR = {"no_made_hand", "ace_high", "king_high"}
WEAK_PAIR_LOW = {"low_pair", "underpair", "third_pair"}
DRY_BOARDS = {"dry_high", "low_dry"}
DYNAMIC_BOARDS = {"dynamic", "dynamic_2tone"}
WEAK_DRAW = {"twocards_bdfd", "onecard_bdfd", "gutshot"}


def flop_def_v8a(r):
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    if mv in AIR:
        if dv == "no_draw": return "FOLD"
        if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair": return "RAISE"
    return "CALL"


def flop_def_v9a(r):
    """v9a: AIR × WEAK_DRAW → FOLD を全 board に拡張 (depth 無視)。"""
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    if mv in AIR:
        if dv == "no_draw": return "FOLD"
        if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
        if dv in WEAK_DRAW and bf in DRY_BOARDS: return "FOLD"  # NEW
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        return "FOLD"
    if mv == "overpair": return "RAISE"
    return "CALL"


def _is_short_stack(r):
    """source_path から short stack (≤50bb) か判定。depth 列は preprocessing で欠損するため。"""
    p = str(r.get("source_path", "")).lower()
    if "mtt25" in p or "mtt50" in p: return True
    if "cash100" in p or "mtt100" in p or "mtt200" in p: return False
    # その他: depth 列が使えるなら使う
    depth_raw = r.get("depth", 100)
    try:
        depth = float(depth_raw) if pd.notna(depth_raw) else 100.0
    except (ValueError, TypeError):
        depth = 100.0
    return depth > 0 and depth <= 50


def flop_def_v9b(r):
    """v9b: stack-depth aware。
    - deep (≥60bb / Cash100, MTT100/200): AIR × WEAK_DRAW × dry → FOLD
    - short (≤50bb / MTT25, MTT50): AIR × WEAK_DRAW × dry → CALL (implied odds で v8a 維持)
    - short: third_pair × dry × no_draw → RAISE (MTT 短スタック CR、modal RAISE 91%+)
    """
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    is_short = _is_short_stack(r)

    if mv in AIR:
        if dv == "no_draw": return "FOLD"
        if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
        if dv in WEAK_DRAW and bf in DRY_BOARDS and not is_short: return "FOLD"  # NEW (deep only)

    # MTT 短スタックの CR: third_pair/low_pair × dry × no_draw
    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        if is_short:
            return "RAISE"  # MTT 短スタック CR
        return "FOLD"

    if mv == "overpair": return "RAISE"
    return "CALL"


def best_ev(r):
    return max(e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e))


def ev_of(r, p):
    if p == "FOLD": return r["ev_fold"]
    if p == "CALL": return r["ev_call"]
    return r["ev_raise"] if pd.notna(r["ev_raise"]) else r["ev_call"]


def ev_gap_row(r):
    evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
    return evs[0] - evs[1] if len(evs) >= 2 else None


def detect_pot_type(p):
    p = str(p).lower()
    if "mtt25" in p: return "MTT25"
    if "mtt50" in p: return "MTT50"
    if "mtt100" in p: return "MTT100"
    if "cash100" in p: return "Cash100"
    return "other"


def evaluate(sub, formula, label):
    sub = sub.copy()
    sub["pred"] = sub.apply(formula, axis=1)
    sub["ev_p"] = sub.apply(lambda r: ev_of(r, r["pred"]), axis=1)
    sub["loss"] = sub["best_ev"] - sub["ev_p"]
    huge_mask = sub["ev_gap"] > 0.5
    huge_loss = sub.loc[huge_mask, "loss"].mean() if huge_mask.sum() > 0 else 0.0
    acc = (sub["pred"] == sub["modal"]).mean() * 100
    return {
        "formula": label, "n": len(sub),
        "acc%": round(acc, 1),
        "mean_loss": round(sub["loss"].mean(), 3),
        "huge_loss": round(float(huge_loss), 3),
        "n_huge": int(huge_mask.sum()),
    }


def main():
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[
        (df["street"] == "flop") & (df["action_context"] == "defense")
        & df["ev_call"].notna() & df["ev_fold"].notna()
        & df["mv_cat"].notna() & (df["mv_cat"] != "") & (df["mv_cat"] != "unknown")
    ].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub["pot_type"] = sub["source_path"].apply(detect_pot_type)
    sub = sub[sub["ev_gap"].notna()]

    print("=== Flop v8a vs v9a vs v9b (全データ) ===")
    for fm, label in [(flop_def_v8a, "v8a"), (flop_def_v9a, "v9a"), (flop_def_v9b, "v9b")]:
        r = evaluate(sub, fm, label)
        print(f"  {r['formula']:4s}  n={r['n']:6,}  acc={r['acc%']}%  mean={r['mean_loss']}BB  huge={r['huge_loss']}BB  n_huge={r['n_huge']:,}")
    print()

    print("=== pot_type 別 ===")
    print(f"{'pot':10s} {'公式':5s} {'n':>6s} {'acc%':>7s} {'mean':>9s} {'huge':>9s}")
    for pt in ["Cash100", "MTT100", "MTT50", "MTT25"]:
        sp = sub[sub["pot_type"] == pt]
        if len(sp) < 200: continue
        for fm, label in [(flop_def_v8a, "v8a"), (flop_def_v9a, "v9a"), (flop_def_v9b, "v9b")]:
            r = evaluate(sp, fm, label)
            print(f"  {pt:8s}  {label}  {r['n']:>6,}  {r['acc%']:>6.1f}% {r['mean_loss']:>6.3f}BB {r['huge_loss']:>6.3f}BB")
    print()

    print("=== 主要境界 cell の変化 ===")
    cells = [
        ("Cash100", "dry_high", "no_made_hand", "twocards_bdfd"),
        ("Cash100", "low_dry", "no_made_hand", "twocards_bdfd"),
        ("Cash100", "dry_high", "ace_high", "onecard_bdfd"),
        ("MTT100",  "dry_high", "no_made_hand", "onecard_bdfd"),
        ("MTT100",  "dry_high", "no_made_hand", "twocards_bdfd"),
        ("MTT100",  "low_dry",  "no_made_hand", "twocards_bdfd"),
        ("MTT25",   "dry_high", "third_pair",   "no_draw"),
        ("MTT50",   "dry_high", "third_pair",   "no_draw"),
        ("MTT25",   "low_dry",  "low_pair",     "no_draw"),
    ]
    print(f"{'pot':8s} {'bf':10s} {'mv':14s} {'dv':14s} {'n':>5s} {'v8a':>9s} {'v9a':>9s} {'v9b':>9s}")
    for pot, bf, mv, dv in cells:
        cell = sub[(sub["pot_type"] == pot) & (sub["board_family"] == bf) & (sub["mv_cat"] == mv) & (sub["dv_cat"] == dv)]
        if len(cell) < 30: continue
        r1 = evaluate(cell, flop_def_v8a, "v8a")
        r2 = evaluate(cell, flop_def_v9a, "v9a")
        r3 = evaluate(cell, flop_def_v9b, "v9b")
        print(f"  {pot:6s} {bf:10s} {mv:14s} {dv:14s} {r1['n']:>4,}  {r1['huge_loss']:>6.2f}BB  {r2['huge_loss']:>6.2f}BB  {r3['huge_loss']:>6.2f}BB")


if __name__ == "__main__":
    raise SystemExit(main())
