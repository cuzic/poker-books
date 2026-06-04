#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""River attack formula — using mv_cat as primary axis (no bucket needed on river).

River logic: hand value IS the final value (no future cards). Polarization is severe.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    df = df[(df["street"] == "river") & (df["action_context"] == "attack") &
            (df["ev_bet"].notna()) & (df["ev_check"].notna()) &
            (df["mv_cat"].notna()) & (df["mv_cat"] != "")].copy()
    df["best_ev"] = df[["ev_bet", "ev_check"]].max(axis=1)
    df["modal"] = (df["bet_freq"] >= 0.5).map({True: "BET", False: "CHECK"})
    print(f"River attack rows: {len(df)}")
    print(f"BET modal rate: {(df['modal']=='BET').mean()*100:.1f}%")
    print(f"always_CHECK loss: {(df['best_ev']-df['ev_check']).mean():.4f} BB")
    print(f"always_BET   loss: {(df['best_ev']-df['ev_bet']).mean():.4f} BB")

    # mv_cat distribution + BET rate per mv
    print(f"\n=== BET modal rate per mv_cat ===")
    for mv, sub in df.groupby("mv_cat"):
        if len(sub) < 100: continue
        bet_rate = (sub["modal"] == "BET").mean() * 100
        bet_mean = sub["bet_freq"].mean() * 100
        l_chk = (sub["best_ev"] - sub["ev_check"]).mean()
        l_bet = (sub["best_ev"] - sub["ev_bet"]).mean()
        print(f"  {mv:15s} n={len(sub):5d} BET_modal={bet_rate:5.1f}% bet_mean={bet_mean:5.1f}% always_CHECK={l_chk:.4f} always_BET={l_bet:.4f}")

    # Strategy: 単純な MV ベース
    BET_MV = {"two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
    CHECK_MV = {"low_pair", "underpair", "third_pair", "second_pair", "no_made_hand", "ace_high", "king_high"}

    def pred_simple(mv):
        if mv in BET_MV: return "BET"
        return "CHECK"
    df["pred_simple"] = df["mv_cat"].apply(pred_simple)

    # Strategy: + overpair if not paired board
    def pred_v2(r):
        mv = r["mv_cat"]
        if mv in BET_MV: return "BET"
        if mv == "overpair" and r["board_family"] != "paired": return "BET"
        return "CHECK"
    df["pred_v2"] = df.apply(pred_v2, axis=1)

    # Strategy: + top_pair conditional (TPGK on dry)
    def pred_v3(r):
        mv = r["mv_cat"]
        bf = r["board_family"]
        if mv in BET_MV: return "BET"
        if mv == "overpair" and bf != "paired": return "BET"
        if mv == "top_pair" and bf in {"dry_high", "low_dry"}: return "BET"
        return "CHECK"
    df["pred_v3"] = df.apply(pred_v3, axis=1)

    print(f"\n=== Strategy comparison ===")
    for col, name in [("pred_simple", "v1: BET if 2P+ / set / straight+"),
                       ("pred_v2", "v2: v1 + OP on non-paired"),
                       ("pred_v3", "v3: v2 + TP on dry boards")]:
        df["ev_pred"] = df.apply(lambda r: r["ev_bet"] if r[col] == "BET" else r["ev_check"], axis=1)
        df["loss"] = df["best_ev"] - df["ev_pred"]
        acc = (df[col] == df["modal"]).mean() * 100
        print(f"  {name:50s}  acc={acc:5.1f}%  loss={df['loss'].mean():.4f} BB")

    # ── Per board_family ──
    print(f"\n=== Per board_family for v3 ===")
    df["ev_pred"] = df.apply(lambda r: r["ev_bet"] if r["pred_v3"] == "BET" else r["ev_check"], axis=1)
    df["loss"] = df["best_ev"] - df["ev_pred"]
    for bf, sub in df.groupby("board_family"):
        if len(sub) < 500: continue
        acc = (sub["pred_v3"] == sub["modal"]).mean() * 100
        print(f"  {bf:18s} n={len(sub):6d} acc={acc:5.1f}% loss={sub['loss'].mean():.4f}BB")

    # ── Per mv ──
    print(f"\n=== Per mv_cat for v3 ===")
    for mv, sub in df.groupby("mv_cat"):
        if len(sub) < 200: continue
        acc = (sub["pred_v3"] == sub["modal"]).mean() * 100
        l_chk = (sub["best_ev"] - sub["ev_check"]).mean()
        l_v3 = sub["loss"].mean()
        print(f"  {mv:15s} n={len(sub):6d} v3_acc={acc:5.1f}% v3_loss={l_v3:.4f} (always_CHECK loss={l_chk:.4f})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
