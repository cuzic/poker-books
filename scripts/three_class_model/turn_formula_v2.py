#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Turn defense formula v2 — binary FOLD/CALL (no RAISE, slowplay everything)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    df = df[(df["street"] == "turn") & (df["action_context"] == "defense") &
            (df["ev_call"].notna()) & (df["ev_fold"].notna())].copy()
    for c in ["fold_freq", "call_freq", "raise_freq"]:
        df[c] = df[c].fillna(0)
    df["modal"] = df[["fold_freq", "call_freq", "raise_freq"]].idxmax(axis=1).str.replace("_freq", "").str.upper()
    df["best_ev"] = df[["ev_fold", "ev_call", "ev_raise"]].max(axis=1)
    print(f"Turn defense rows: {len(df)}")
    print(f"Modal distribution: {df['modal'].value_counts(normalize=True).round(3).to_dict()}")

    # Bet size context — what % pot was the turn bet?
    print(f"\n=== Per source (different bet sizes) ===")
    for sp, sub in df.groupby("source_path"):
        if len(sub) < 50: continue
        bn = Path(sp).name
        modal_dist = sub["modal"].value_counts(normalize=True).to_dict()
        f = modal_dist.get("FOLD", 0) * 100
        c = modal_dist.get("CALL", 0) * 100
        r = modal_dist.get("RAISE", 0) * 100
        print(f"  {bn:30s} n={len(sub):4d}  F:{f:5.1f}% C:{c:5.1f}% R:{r:4.1f}%")

    # Distinguish small vs large bet via filename pattern
    df["bet_size"] = df["source_path"].apply(lambda s:
        "small_25p" if "_R2." in s else
        "med_67p" if "_R6." in s else
        "overbet_185p" if "_R16" in s else "other"
    )
    print(f"\n=== By bet size ===")
    for bs, sub in df.groupby("bet_size"):
        modal_dist = sub["modal"].value_counts(normalize=True).round(3).to_dict()
        print(f"  {bs}: n={len(sub)} dist={modal_dist}")
        print(f"    always_FOLD loss: {(sub['best_ev']-sub['ev_fold']).mean():.4f}BB")
        print(f"    always_CALL loss: {(sub['best_ev']-sub['ev_call']).mean():.4f}BB")

    # ── Binary formulas ──
    # v1: just always CALL
    df["pred_call"] = "CALL"
    # v2: FOLD if mv=0 AND dv=0
    df["pred_v2"] = np.where((df["mv_cat"].isin({"no_made_hand", "ace_high", "king_high"})) &
                              (df["dv_cat"] == "no_draw"), "FOLD", "CALL")
    # v3: FOLD if (mv≤low_pair AND dv=0) — include weak pairs
    df["pred_v3"] = np.where((df["mv_cat"].isin({"no_made_hand", "ace_high", "king_high",
                                                  "low_pair", "underpair", "third_pair"})) &
                              (df["dv_cat"] == "no_draw"), "FOLD", "CALL")
    # v4: include bet_size — fold MORE on large bets
    def pred_v4(r):
        weak_mv = r["mv_cat"] in {"no_made_hand", "ace_high", "king_high", "low_pair", "underpair"}
        weakish = r["mv_cat"] in {"third_pair", "second_pair"}
        no_draw = r["dv_cat"] == "no_draw"
        if r["bet_size"] == "overbet_185p":
            # fold weak + weakish without draws against overbets
            if (weak_mv or weakish) and no_draw:
                return "FOLD"
        else:
            # vs smaller bets, only fold true trash
            if weak_mv and no_draw:
                return "FOLD"
        return "CALL"
    df["pred_v4"] = df.apply(pred_v4, axis=1)

    print(f"\n=== Strategy comparison ===")
    print(f"  always_FOLD loss: {(df['best_ev']-df['ev_fold']).mean():.4f}BB")
    print(f"  always_CALL loss: {(df['best_ev']-df['ev_call']).mean():.4f}BB")
    for col, name in [("pred_v2", "v2: FOLD if A/K-high/air + no_draw"),
                       ("pred_v3", "v3: v2 + weak pairs"),
                       ("pred_v4", "v4: v3 + overbet sensitivity")]:
        df["ev_pred"] = df.apply(lambda r: r["ev_fold"] if r[col] == "FOLD" else r["ev_call"], axis=1)
        df["loss"] = df["best_ev"] - df["ev_pred"]
        acc = (df[col] == df["modal"]).mean() * 100
        loss = df["loss"].mean()
        print(f"  {name:55s} acc={acc:5.1f}% loss={loss:.4f}BB")

    # ── Per ev_gap ──
    def gap(r):
        evs = sorted([e for e in [r["ev_fold"], r["ev_call"], r["ev_raise"]] if pd.notna(e)], reverse=True)
        return evs[0] - evs[1] if len(evs) >= 2 else None
    df["gap"] = df.apply(gap, axis=1)
    df["gap_cat"] = pd.cut(df["gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                            labels=["tiny", "small", "med", "large", "huge"])
    print(f"\n=== EV loss per gap (v4 vs always_CALL) ===")
    df["ev_v4"] = df.apply(lambda r: r["ev_fold"] if r["pred_v4"] == "FOLD" else r["ev_call"], axis=1)
    df["loss_v4"] = df["best_ev"] - df["ev_v4"]
    for cat in df["gap_cat"].cat.categories:
        sub = df[df["gap_cat"] == cat]
        if len(sub) == 0: continue
        l_call = (sub["best_ev"] - sub["ev_call"]).mean()
        l_v4 = sub["loss_v4"].mean()
        print(f"  {str(cat):8s} n={len(sub):4d} always_CALL={l_call:.4f}BB v4={l_v4:.4f}BB save={l_call-l_v4:+.4f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
