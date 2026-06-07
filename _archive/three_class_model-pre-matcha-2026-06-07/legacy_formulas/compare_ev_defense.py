#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Defense EV loss comparison.

Strategies:
  1. Oracle (per-combo max EV)
  2. Always FOLD
  3. Always CALL
  4. Always RAISE
  5. eq-based framework (FOLD if eq<40, else CALL)
  6. HIGH-only override (default CALL + identified HIGH cells)

Compute per-decision mean EV loss for each.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"


def main() -> int:
    df = pd.read_csv(DATA, low_memory=False)

    df = df[(df["action_context"] == "defense") &
            (df["eq_percentile"].notna()) &
            (df["ev_call"].notna()) &
            (df["ev_fold"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    print(f"Defense rows: {len(df)}")

    # Check what EV columns we have
    print(f"\nEV columns presence:")
    for col in ["ev_bet", "ev_check", "ev_fold", "ev_call", "ev_raise"]:
        if col in df.columns:
            avail = df[col].notna().mean() * 100
            print(f"  {col}: {avail:.1f}% available")

    # For defense, the relevant EVs are ev_fold, ev_call, ev_raise
    # Need to filter to rows where at least 2 of these are present
    available_actions = []
    if df["ev_fold"].notna().mean() > 0.5: available_actions.append("FOLD")
    if df["ev_call"].notna().mean() > 0.5: available_actions.append("CALL")
    if df["ev_raise"].notna().mean() > 0.5: available_actions.append("RAISE")
    print(f"\nUsable actions: {available_actions}")

    # Best EV per row
    ev_cols = []
    if "ev_fold" in df: ev_cols.append("ev_fold")
    if "ev_call" in df: ev_cols.append("ev_call")
    if "ev_raise" in df: ev_cols.append("ev_raise")
    df["best_ev"] = df[ev_cols].max(axis=1)

    # ── Per-strategy loss ──
    print(f"\n=== EV loss per strategy (mean BB per decision) ===")
    strategies = []
    for action_col, name in [("ev_fold", "Always FOLD"),
                              ("ev_call", "Always CALL"),
                              ("ev_raise", "Always RAISE")]:
        if action_col not in df:
            continue
        loss = (df["best_ev"] - df[action_col].fillna(-999))
        loss = loss[loss < 100]  # filter out -999 placeholder
        strategies.append((name, loss.mean(), loss.sum(), len(loss)))
        print(f"  {name:25s}  mean_loss={loss.mean():.4f}BB  total={loss.sum():9.1f}BB  n={len(loss)}")

    # ── eq-based framework: FOLD if eq<40, else CALL ──
    def eq_action(eq):
        if pd.isna(eq): return "CALL"
        if eq < 0.40: return "FOLD"
        return "CALL"
    df["pred_eq"] = df["eq_percentile"].apply(eq_action)
    df["ev_pred_eq"] = df.apply(
        lambda r: r["ev_fold"] if r["pred_eq"] == "FOLD" else r["ev_call"], axis=1
    )
    df["loss_eq"] = df["best_ev"] - df["ev_pred_eq"]
    print(f"  {'eq-based framework':25s}  mean_loss={df['loss_eq'].mean():.4f}BB  total={df['loss_eq'].sum():9.1f}BB")

    # ── Identify HIGH confidence cells per action ──
    keys = ["equity_bucket", "mv_cat", "board_family", "dv_cat"]
    cell = df.groupby(keys).agg(
        n=("eq_percentile", "count"),
        fold_iqr=("fold_freq", lambda x: x.quantile(0.75) - x.quantile(0.25)),
        call_iqr=("call_freq", lambda x: x.quantile(0.75) - x.quantile(0.25)),
        raise_iqr=("raise_freq", lambda x: x.quantile(0.75) - x.quantile(0.25)),
        fold_mean=("fold_freq", "mean"),
        call_mean=("call_freq", "mean"),
        raise_mean=("raise_freq", "mean"),
    ).reset_index()
    # HIGH conf where any IQR < 0.10
    cell["primary_iqr"] = cell[["fold_iqr", "call_iqr", "raise_iqr"]].min(axis=1)
    high_cells = cell[(cell["primary_iqr"] < 0.10) & (cell["n"] >= 30)].copy()
    # modal action
    def modal_of(row):
        d = {"FOLD": row["fold_mean"], "CALL": row["call_mean"], "RAISE": row["raise_mean"]}
        return max(d, key=lambda k: d[k])
    high_cells["modal"] = high_cells.apply(modal_of, axis=1)
    print(f"\nHIGH-conf cells: {len(high_cells)}")
    for mod in ["FOLD", "CALL", "RAISE"]:
        n = (high_cells["modal"] == mod).sum()
        print(f"  → {mod}: {n}")

    # ── HIGH-only override strategy: default CALL + use HIGH modal otherwise ──
    high_dict = {tuple(r[k] for k in keys): r["modal"] for _, r in high_cells.iterrows()}
    def hc_action(r):
        key = tuple(r[k] for k in keys)
        if key in high_dict:
            return high_dict[key]
        return "CALL"  # default
    df["pred_hc"] = df.apply(hc_action, axis=1)
    def ev_of(act, r):
        return r.get(f"ev_{act.lower()}")
    df["ev_pred_hc"] = df.apply(lambda r: ev_of(r["pred_hc"], r), axis=1)
    df["loss_hc"] = df["best_ev"] - df["ev_pred_hc"].fillna(df["ev_call"])
    print(f"  {'HIGH-only override':25s}  mean_loss={df['loss_hc'].mean():.4f}BB  total={df['loss_hc'].sum():9.1f}BB")

    # ── Try: default FOLD baseline ──
    def fc_action(r):
        key = tuple(r[k] for k in keys)
        if key in high_dict:
            return high_dict[key]
        return "FOLD"  # default
    df["pred_default_fold"] = df.apply(fc_action, axis=1)
    df["ev_pred_df"] = df.apply(lambda r: ev_of(r["pred_default_fold"], r), axis=1)
    df["loss_df"] = df["best_ev"] - df["ev_pred_df"].fillna(df["ev_fold"])
    print(f"  {'default FOLD + HIGH cells':25s}  mean_loss={df['loss_df'].mean():.4f}BB  total={df['loss_df'].sum():9.1f}BB")

    # ── EV loss per gap category ──
    # ev_gap for defense: max - 2nd best across fold/call/raise
    def ev_gap(r):
        evs = [r["ev_fold"], r["ev_call"], r["ev_raise"]]
        evs = sorted([e for e in evs if pd.notna(e)], reverse=True)
        if len(evs) < 2: return None
        return evs[0] - evs[1]
    df["ev_gap"] = df.apply(ev_gap, axis=1)
    df = df[df["ev_gap"].notna()].copy()
    df["gap_cat"] = pd.cut(df["ev_gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                            labels=["tiny", "small", "med", "large", "huge"])

    print(f"\n=== EV gap distribution ===")
    print(df["gap_cat"].value_counts(normalize=True).round(3) * 100)

    print(f"\n=== Per gap_cat: mean EV loss by strategy ===")
    print(f"  cat       call    fold    raise   eq     hc      df_FOLD")
    for cat in df["gap_cat"].cat.categories:
        sub = df[df["gap_cat"] == cat]
        if len(sub) == 0: continue
        loss_call = (sub["best_ev"] - sub["ev_call"]).mean()
        loss_fold = (sub["best_ev"] - sub["ev_fold"]).mean()
        loss_raise = (sub["best_ev"] - sub["ev_raise"]).mean() if "ev_raise" in df else float("nan")
        loss_eq = sub["loss_eq"].mean()
        loss_hc = sub["loss_hc"].mean()
        loss_df = sub["loss_df"].mean()
        print(f"  {str(cat):8s}  {loss_call:.4f}  {loss_fold:.4f}  {loss_raise:.4f}  {loss_eq:.4f}  {loss_hc:.4f}  {loss_df:.4f}  (n={len(sub)})")

    # ── Show HIGH-cell breakdown ──
    print(f"\n=== HIGH cells per modal action ===")
    for mod in ["FOLD", "CALL", "RAISE"]:
        sub = high_cells[high_cells["modal"] == mod]
        print(f"\n--- {mod} ({len(sub)} cells) ---")
        for _, r in sub.sort_values("n", ascending=False).head(15).iterrows():
            print(f"  {r['equity_bucket']:13s} × {r['mv_cat']:15s} × {r['board_family']:18s} × {r['dv_cat']:18s}  F:{r['fold_mean']*100:3.0f}% C:{r['call_mean']*100:3.0f}% R:{r['raise_mean']*100:3.0f}%  n={int(r['n'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
