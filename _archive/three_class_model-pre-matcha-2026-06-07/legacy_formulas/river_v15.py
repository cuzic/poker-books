#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""River v15 — v14 のバグ修正版。

v14 から修正:
1. **fullhouse × overbet → CALL を削除**、全 fullhouse は RAISE (実測 raise_freq 96%)
2. **broad `is_dyn AND TP × weak/good → CALL` を削除**
   - monotone × TP × allin × weak は FOLD 94% が GTO (v14 は誤 CALL)
   - dynamic × TP × allin/med は FOLD 主流 (v14 が huge_loss 大)
3. **dry_high の TP/2P × overbet/med → CALL** は維持 (bluffcatcher)
4. **straight × overbet × dynamic** で trash bucket は FOLD (細分化)

実測 (mtt_formula_audit.py):
- v14 Cash100: huge_loss 0.388 BB / acc 82.3%
- v15 目標: huge_loss < 0.20 BB / acc > 88%
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"

DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
ABSOLUTELY_STRONG = {"straight", "flush", "trips"}


def river_v15(r):
    """River defense v15.

    優先順:
    1. fullhouse/quads → 常 RAISE (どんな bet size でも)
    2. allin spot: bucket + 板で個別判定
    3. ABSOLUTELY_STRONG (straight/flush/trips) bucket-best/good → CALL、trash → FOLD
    4. TP × dry × overbet/med → CALL (bluffcatcher)
    5. bucket logic で fallback
    """
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dry = bf in DRY

    # ── 1) Nuts / fullhouse は常 RAISE ────────────────
    if mv in {"quads", "fullhouse"}:
        return "RAISE"

    # ── 2) vs allin ─────────────────────────────────
    if bs == "allin":
        # 強メイドハンドは bucket good/best なら call、それ以外 fold
        # 2P を追加 (MTT50 dynamic × 2P × good_hands で modal CALL 100% / ev +31 BB)
        if mv in {"two_pair", "set", "trips", "straight", "flush"}:
            if eb in {"best_hands", "good_hands"}:
                return "CALL"
            if is_dry and mv in {"set", "trips", "straight", "flush"}:
                return "CALL"  # dry 板は強メイドが negative blocker 少なく call 安全
            return "FOLD"
        # best_hands × 高 eqp → call
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85:
            return "CALL"
        # monotone × flush は常 call (上のルールに含まれるが念のため)
        if bf == "monotone" and mv == "flush":
            return "CALL"
        # それ以外は FOLD (TP も含む — v14 のバグ修正)
        return "FOLD"

    # ── 3) ABSOLUTELY_STRONG (non-allin) ─────────────
    if mv in ABSOLUTELY_STRONG:
        # trash bucket は overbet で FOLD (dominated straight 等)
        if eb == "trash_hands" and bs == "overbet":
            return "FOLD"
        return "CALL"

    # ── 4) TP × dry × overbet/med → CALL (bluffcatcher) ─
    if mv == "top_pair" and is_dry and bs in {"overbet", "med_100p"}:
        return "CALL"

    # ── 5) bucket logic fallback ─────────────────────
    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96:
            return "RAISE"
        return "CALL"
    if eb == "good_hands":
        return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            # dynamic × 2P は overbet でも CALL (showdown value)
            if bf in DYNAMIC and mv == "two_pair":
                return "CALL"
            return "FOLD"
        if bs == "med_100p":
            return "FOLD"
        return "CALL"
    # trash_hands
    return "FOLD"


def river_v14(r):
    """v14 (比較用)."""
    eb = r["equity_bucket"]; bs = r["bet_size"]; mv = r["mv_cat"]
    eqp = r.get("eq_percentile"); bf = r["board_family"]
    is_dyn = bf in DYNAMIC
    if mv == "quads": return "RAISE"
    if mv == "fullhouse" and bs != "overbet": return "RAISE"
    if mv == "fullhouse" and bs == "overbet": return "CALL"
    if bs == "allin":
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85: return "CALL"
        if bf in DRY and mv in {"set", "trips", "straight", "flush"}: return "CALL"
        if eb == "good_hands" and mv in {"straight", "flush", "trips"}: return "CALL"
        if bf == "monotone" and mv == "flush": return "CALL"
        if is_dyn and mv == "top_pair" and eb in {"weak_hands", "good_hands"}: return "CALL"
        return "FOLD"
    if mv in ABSOLUTELY_STRONG: return "CALL"
    if mv == "top_pair" and bf in DRY and bs in {"overbet", "med_100p"}: return "CALL"
    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96: return "RAISE"
        return "CALL"
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if is_dyn and mv == "two_pair": return "CALL"
            return "FOLD"
        if bs == "med_100p": return "FOLD"
        return "CALL"
    return "FOLD"


def river_bet_size(s):
    # _R89/_R35 を先に判定 (_R8 substring match を回避)
    if "_R89" in s or "_R35" in s: return "allin"
    if "_R16" in s: return "overbet"
    if "_R13" in s: return "med_100p"
    if "_R7" in s or "_R8" in s: return "med_75p"
    if "_R4" in s: return "small_30p"
    return "other"


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
    mean_l = sub["loss"].mean()
    return {
        "formula": label, "n": len(sub),
        "acc%": round(acc, 1),
        "mean_loss": round(mean_l, 3),
        "huge_loss": round(huge_loss, 3),
        "n_huge": int(huge_mask.sum()),
    }


def main():
    df = pd.read_csv(DATA, low_memory=False)
    sub = df[
        (df["street"] == "river") & (df["action_context"] == "defense")
        & df["ev_call"].notna() & df["ev_fold"].notna()
        & df["mv_cat"].notna() & (df["mv_cat"] != "") & (df["mv_cat"] != "unknown")
    ].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        sub[c] = sub[c].fillna(0)
    sub["modal"] = sub[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    sub["best_ev"] = sub.apply(best_ev, axis=1)
    sub["ev_gap"] = sub.apply(ev_gap_row, axis=1)
    sub["bet_size"] = sub["source_path"].apply(river_bet_size)
    sub["pot_type"] = sub["source_path"].apply(detect_pot_type)
    sub = sub[sub["ev_gap"].notna()]

    print("=== River v14 vs v15 (全データ) ===")
    for fm, label in [(river_v14, "v14"), (river_v15, "v15")]:
        r = evaluate(sub, fm, label)
        print(f"  {r['formula']:5s}  n={r['n']:6,}  acc={r['acc%']}%  mean={r['mean_loss']}BB  huge={r['huge_loss']}BB  n_huge={r['n_huge']:,}")
    print()

    print("=== pot_type 別 ===")
    print(f"{'pot':10s} {'公式':5s} {'n':>6s} {'acc%':>7s} {'mean':>9s} {'huge':>9s}")
    for pt in ["Cash100", "MTT50"]:
        sp = sub[sub["pot_type"] == pt]
        if len(sp) < 200: continue
        for fm, label in [(river_v14, "v14"), (river_v15, "v15")]:
            r = evaluate(sp, fm, label)
            print(f"  {pt:8s}  {label}  {r['n']:>6,}  {r['acc%']:>6.1f}% {r['mean_loss']:>6.3f}BB {r['huge_loss']:>6.3f}BB")
    print()

    print("=== 旧 v14 境界 cell が v15 でどう変わったか (top 10 huge_loss) ===")
    boundary_cells = [
        ("dry_high", "fullhouse", "no_draw", "overbet"),
        ("monotone", "top_pair", "no_draw", "allin"),
        ("dynamic", "fullhouse", "no_draw", "overbet"),
        ("dynamic", "top_pair", "no_draw", "allin"),
        ("dynamic", "straight", "no_draw", "overbet"),
        ("dynamic", "two_pair", "no_draw", "med_100p"),
        ("dry_high", "second_pair", "no_draw", "overbet"),
        ("dynamic", "two_pair", "no_draw", "small_30p"),
        ("dynamic", "set", "no_draw", "allin"),
        ("dynamic", "trips", "no_draw", "overbet"),
    ]
    print(f"{'bf':14s} {'mv':14s} {'dv':10s} {'bs':10s} {'n':>5s} {'v14_huge':>9s} {'v15_huge':>9s} {'v14_acc':>8s} {'v15_acc':>8s}")
    for bf, mv, dv, bs in boundary_cells:
        cell = sub[(sub["board_family"] == bf) & (sub["mv_cat"] == mv)
                   & (sub["dv_cat"] == dv) & (sub["bet_size"] == bs)]
        if len(cell) < 30: continue
        r14 = evaluate(cell, river_v14, "v14")
        r15 = evaluate(cell, river_v15, "v15")
        print(f"  {bf:12s} {mv:14s} {dv:10s} {bs:10s} {r14['n']:>4,}  {r14['huge_loss']:>6.2f}BB  {r15['huge_loss']:>6.2f}BB  {r14['acc%']:>6.1f}%  {r15['acc%']:>6.1f}%")


if __name__ == "__main__":
    raise SystemExit(main())
