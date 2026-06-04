#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""River attack v4 — include bluffs (no_made + king_high) and TP regardless of board."""
from __future__ import annotations

from pathlib import Path

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

    # ── v4: polarized rule (BET value + bluff, CHECK medium) ──
    VALUE = {"top_pair", "overpair", "two_pair", "set", "trips", "straight", "flush", "fullhouse", "quads"}
    BLUFF = {"no_made_hand", "king_high"}

    def pred_v4(r):
        mv = r["mv_cat"]
        if mv in VALUE: return "BET"
        if mv in BLUFF: return "BET"
        return "CHECK"
    df["pred_v4"] = df.apply(pred_v4, axis=1)

    # ── v5: avoid OP bet on paired (loses to trips) ──
    def pred_v5(r):
        mv = r["mv_cat"]
        bf = r["board_family"]
        if mv == "overpair" and bf == "paired": return "CHECK"
        if mv in VALUE: return "BET"
        if mv in BLUFF: return "BET"
        return "CHECK"
    df["pred_v5"] = df.apply(pred_v5, axis=1)

    # ── v6: also CHECK set on dynamic (slowplay) ──
    def pred_v6(r):
        mv = r["mv_cat"]
        bf = r["board_family"]
        if mv == "overpair" and bf == "paired": return "CHECK"
        if mv == "set" and bf in {"dry_high", "low_dry"}: return "CHECK"  # slowplay on dry
        if mv in VALUE: return "BET"
        if mv in BLUFF: return "BET"
        return "CHECK"
    df["pred_v6"] = df.apply(pred_v6, axis=1)

    print(f"=== Strategy comparison (river attack) ===")
    print(f"  baseline always_CHECK loss: {(df['best_ev']-df['ev_check']).mean():.4f} BB")
    print(f"  baseline always_BET   loss: {(df['best_ev']-df['ev_bet']).mean():.4f} BB")
    for col, name in [("pred_v4", "v4: BET if TP+ OR no_made/K-high"),
                       ("pred_v5", "v5: v4 - OP on paired"),
                       ("pred_v6", "v6: v5 - SET on dry")]:
        df["ev_pred"] = df.apply(lambda r: r["ev_bet"] if r[col] == "BET" else r["ev_check"], axis=1)
        df["loss"] = df["best_ev"] - df["ev_pred"]
        acc = (df[col] == df["modal"]).mean() * 100
        print(f"  {name:50s}  acc={acc:5.1f}%  loss={df['loss'].mean():.4f} BB")

    # ── Per mv_cat verbose for v4 ──
    df["ev_pred_v4"] = df.apply(lambda r: r["ev_bet"] if r["pred_v4"] == "BET" else r["ev_check"], axis=1)
    df["loss_v4"] = df["best_ev"] - df["ev_pred_v4"]
    print(f"\n=== Per mv_cat (v4) ===")
    for mv, sub in df.groupby("mv_cat"):
        if len(sub) < 200: continue
        acc = (sub["pred_v4"] == sub["modal"]).mean() * 100
        l = sub["loss_v4"].mean()
        l_chk = (sub["best_ev"] - sub["ev_check"]).mean()
        pred = sub["pred_v4"].iloc[0]
        save = l_chk - l
        marker = "✓" if save > 0.05 else (" " if abs(save) < 0.01 else "?")
        print(f"  {marker} {mv:15s} {pred:5s}  n={len(sub):6d} acc={acc:5.1f}% v4_loss={l:.4f} vs_CHECK_save={save:+.4f}BB")

    # ── ev_gap breakdown ──
    def gap(r):
        return abs(r["ev_bet"] - r["ev_check"])
    df["ev_gap"] = df.apply(gap, axis=1)
    df["gap_cat"] = pd.cut(df["ev_gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                            labels=["tiny", "small", "med", "large", "huge"])
    print(f"\n=== EV loss per ev_gap (v4) ===")
    for cat in df["gap_cat"].cat.categories:
        sub = df[df["gap_cat"] == cat]
        if len(sub) == 0: continue
        l_chk = (sub["best_ev"] - sub["ev_check"]).mean()
        l_v4 = sub["loss_v4"].mean()
        print(f"  {str(cat):8s} n={len(sub):6d} always_CHECK={l_chk:.4f}BB v4={l_v4:.4f}BB save={l_chk-l_v4:+.4f}BB")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
