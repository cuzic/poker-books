#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy", "scikit-learn"]
# ///
"""Per-street attack formula derivation.

For flop / turn / river attack:
  1. Show default-CHECK baseline EV loss
  2. Find HIGH-confidence BET cells per street
  3. Derive simple "default CHECK + N exceptions" rule
  4. Compare structure across streets
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def analyze_street(df: pd.DataFrame, street: str) -> None:
    print(f"\n{'='*70}")
    print(f"=== {street.upper()} ATTACK ===")
    print(f"{'='*70}")
    sub = df[(df["street"] == street) & (df["action_context"] == "attack") &
              (df["ev_bet"].notna()) & (df["ev_check"].notna()) &
              (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    print(f"Rows: {len(sub)}")
    if len(sub) == 0:
        return
    sub["best_ev"] = sub[["ev_bet", "ev_check"]].max(axis=1)
    sub["modal"] = (sub["bet_freq"] >= 0.5).map({True: "BET", False: "CHECK"})

    # Baselines
    print(f"\n--- Baselines ---")
    print(f"  BET_modal rate: {(sub['modal'] == 'BET').mean()*100:.1f}%")
    print(f"  always_CHECK loss: {(sub['best_ev'] - sub['ev_check']).mean():.4f} BB")
    print(f"  always_BET   loss: {(sub['best_ev'] - sub['ev_bet']).mean():.4f} BB")

    # HIGH-conf cells (default-CHECK + override)
    keys = ["equity_bucket", "mv_cat", "board_family", "dv_cat"]
    stats = sub.groupby(keys).agg(
        n=("bet_freq", "count"),
        bet_median=("bet_freq", "median"),
        bet_iqr=("bet_freq", lambda x: x.quantile(0.75) - x.quantile(0.25)),
        bet_mean=("bet_freq", "mean"),
    ).reset_index()
    high_bet = stats[(stats["bet_iqr"] < 0.10) & (stats["n"] >= 30) & (stats["bet_median"] >= 0.75)]
    high_check = stats[(stats["bet_iqr"] < 0.10) & (stats["n"] >= 30) & (stats["bet_median"] < 0.25)]
    print(f"\n--- HIGH-conf cells ---")
    print(f"  BET cells:   {len(high_bet)}")
    print(f"  CHECK cells: {len(high_check)}")

    if len(high_bet) > 0:
        print(f"\n  Top BET cells:")
        for _, r in high_bet.sort_values("n", ascending=False).head(15).iterrows():
            print(f"    {r['equity_bucket']:13s} × {r['mv_cat']:15s} × {r['board_family']:15s} × {r['dv_cat']:18s}  bet={r['bet_median']*100:3.0f}% n={int(r['n'])}")

    # Apply default-CHECK + HIGH BET override
    high_set = set(tuple(r[k] for k in keys) for _, r in high_bet.iterrows())
    def pred_hc(r):
        if tuple(r[k] for k in keys) in high_set: return "BET"
        return "CHECK"
    sub["pred_hc"] = sub.apply(pred_hc, axis=1)
    def ev_of(r):
        return r["ev_bet"] if r["pred_hc"] == "BET" else r["ev_check"]
    sub["ev_pred_hc"] = sub.apply(ev_of, axis=1)
    sub["loss_hc"] = sub["best_ev"] - sub["ev_pred_hc"]
    print(f"\n  default CHECK + {len(high_bet)} BET cells: loss={sub['loss_hc'].mean():.4f} BB  acc={(sub['pred_hc']==sub['modal']).mean()*100:.1f}%")

    # Simple eq-based: BET if bucket=best AND board ∈ low_dry/dry_high
    def pred_simple(r):
        if r["equity_bucket"] == "best_hands" and r["board_family"] in {"low_dry", "dry_high"}:
            return "BET"
        return "CHECK"
    sub["pred_simple"] = sub.apply(pred_simple, axis=1)
    sub["ev_pred_simple"] = sub.apply(lambda r: r["ev_bet"] if r["pred_simple"]=="BET" else r["ev_check"], axis=1)
    sub["loss_simple"] = sub["best_ev"] - sub["ev_pred_simple"]
    print(f"  simple rule (best × dry board): loss={sub['loss_simple'].mean():.4f} BB  acc={(sub['pred_simple']==sub['modal']).mean()*100:.1f}%")

    # By board family
    print(f"\n--- Per board_family (BET modal rate) ---")
    for bf, ss in sub.groupby("board_family"):
        if len(ss) < 500: continue
        br = (ss["modal"] == "BET").mean() * 100
        cl = (ss["best_ev"] - ss["ev_check"]).mean()
        bl = (ss["best_ev"] - ss["ev_bet"]).mean()
        print(f"  {bf:18s} n={len(ss):6d} BET_modal={br:5.1f}% always_CHECK={cl:.4f} always_BET={bl:.4f}")


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)
    for st in ["flop", "turn", "river"]:
        analyze_street(df, st)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
