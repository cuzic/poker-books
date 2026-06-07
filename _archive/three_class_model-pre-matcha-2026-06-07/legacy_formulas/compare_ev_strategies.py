#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Compare EV loss across multiple attack strategies:

1. Oracle (per-combo max EV)
2. Always CHECK
3. Always BET
4. v6 framework (eq + bet_size + bluff_cand)
5. "Default CHECK + HIGH confidence BET" — new proposal

For each strategy, compute mean EV loss per decision.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "scripts" / "three_class_model" / "dataset_unified.csv"
BET_ATK = ROOT / "scripts" / "three_class_model" / "attack_bet_size.csv"

RANKS = "23456789TJQKA"


def size_bucket(s):
    if pd.isna(s): return "unknown"
    if s < 0.45: return "small"
    if s < 0.85: return "mid"
    return "big"


def has_strong_draw(dv): return dv in {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}
def has_bdfd(dv): return dv in {"twocards_bdfd", "onecard_bdfd"}


def has_high_blocker(card_a, card_b):
    ranks = (str(card_a)[0] if str(card_a) else "") + (str(card_b)[0] if str(card_b) else "")
    return "A" in ranks or "K" in ranks


def is_bluff_candidate(row):
    dv = row.get("dv_cat", "")
    if has_strong_draw(dv) or has_bdfd(dv) or dv == "gutshot":
        return True
    if has_high_blocker(row.get("card_a"), row.get("card_b")):
        return True
    return False


def predict_v6(eq, size_b, is_bluff_cand, dv_cat, mv_cat):
    """Return BET or CHECK (binary)."""
    if pd.isna(eq) or pd.isna(size_b) or size_b == "unknown":
        return "CHECK"
    if size_b == "small":
        if eq < 0.30 and is_bluff_cand:
            return "BET"  # selected bluff
        if eq >= 0.85:
            return "BET"  # value
        return "CHECK"
    # big bet
    if eq < 0.05 and is_bluff_cand:
        return "BET"
    if eq >= 0.90:
        return "BET"
    return "CHECK"


def predict_high_conf_only(row, high_cells):
    """Default CHECK, BET only on identified HIGH confidence value cells."""
    key = (row["size_bucket"], row["equity_bucket"], row["mv_cat"],
           row["board_family"], row["dv_cat"])
    if key in high_cells:
        return high_cells[key]
    return "CHECK"


def main() -> int:
    main_df = pd.read_csv(DATA, low_memory=False)
    bet_df = pd.read_csv(BET_ATK)[["spot_id", "primary_size_pot"]].drop_duplicates(subset=["spot_id"])
    df = main_df.merge(bet_df, on="spot_id", how="left")

    df = df[(df["action_context"] == "attack") &
            (df["eq_percentile"].notna()) &
            (df["primary_size_pot"].notna()) &
            (df["ev_bet"].notna()) & (df["ev_check"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    df["size_bucket"] = df["primary_size_pot"].apply(size_bucket)
    df["best_ev"] = df[["ev_bet", "ev_check"]].max(axis=1)
    print(f"Attack rows: {len(df)}")

    # ── Identify HIGH confidence value-bet cells ──
    keys_hc = ["size_bucket", "equity_bucket", "mv_cat", "board_family", "dv_cat"]
    cell_stats = df.groupby(keys_hc).agg(
        median_bet=("bet_freq", "median"),
        q25=("bet_freq", lambda x: x.quantile(0.25)),
        q75=("bet_freq", lambda x: x.quantile(0.75)),
        count=("bet_freq", "count"),
    ).reset_index()
    cell_stats["iqr"] = cell_stats["q75"] - cell_stats["q25"]
    # HIGH confidence + BET-modal cell
    high_bet_cells = cell_stats[
        (cell_stats["iqr"] < 0.10) &
        (cell_stats["count"] >= 30) &
        (cell_stats["median_bet"] >= 0.75)
    ]
    # HIGH confidence + CHECK-modal cells (for reference)
    high_check_cells = cell_stats[
        (cell_stats["iqr"] < 0.10) &
        (cell_stats["count"] >= 30) &
        (cell_stats["median_bet"] < 0.25)
    ]
    print(f"\nHIGH-conf BET cells: {len(high_bet_cells)}")
    print(f"HIGH-conf CHECK cells: {len(high_check_cells)}")

    high_bet_set = set(tuple(r[k] for k in keys_hc) for _, r in high_bet_cells.iterrows())
    high_check_set = set(tuple(r[k] for k in keys_hc) for _, r in high_check_cells.iterrows())

    # ── Apply v6 ──
    df["is_bluff_cand"] = df.apply(is_bluff_candidate, axis=1)
    df["pred_v6"] = df.apply(
        lambda r: predict_v6(r["eq_percentile"], r["size_bucket"], r["is_bluff_cand"], r["dv_cat"], r["mv_cat"]),
        axis=1,
    )

    # ── Apply "high-conf-only" strategy ──
    def hc_pred(r):
        key = tuple(r[k] for k in keys_hc)
        if key in high_bet_set:
            return "BET"
        return "CHECK"
    df["pred_hc"] = df.apply(hc_pred, axis=1)

    # ── Compute EV for each strategy ──
    def ev_of(pred_col):
        return df.apply(lambda r: r["ev_bet"] if r[pred_col] == "BET" else r["ev_check"], axis=1)

    df["ev_v6"] = ev_of("pred_v6")
    df["ev_hc"] = ev_of("pred_hc")
    df["ev_always_check"] = df["ev_check"]
    df["ev_always_bet"] = df["ev_bet"]

    df["loss_v6"] = df["best_ev"] - df["ev_v6"]
    df["loss_hc"] = df["best_ev"] - df["ev_hc"]
    df["loss_check"] = df["best_ev"] - df["ev_always_check"]
    df["loss_bet"] = df["best_ev"] - df["ev_always_bet"]

    print(f"\n=== EV loss comparison (mean per decision, total BB) ===")
    print(f"  Strategy                       mean_loss    total_loss   BET_freq")
    for col, name in [("loss_check", "Always CHECK"),
                       ("loss_bet", "Always BET"),
                       ("loss_v6", "v6 framework"),
                       ("loss_hc", "HIGH-only override (NEW)")]:
        mean = df[col].mean()
        total = df[col].sum()
        bet_freq = (df[f"pred_{name.lower().split()[0]}" if name == "v6 framework" or name == "HIGH-only override (NEW)" else "pred_v6"] == "BET").mean() if "pred" in col else None
        print(f"  {name:32s}  {mean:7.4f}BB    {total:9.1f}     -")

    print(f"\n=== Modal accuracy of each strategy ===")
    df["actual_mod"] = (df["bet_freq"] >= 0.5).map({True: "BET", False: "CHECK"})
    for col, name in [("pred_v6", "v6"), ("pred_hc", "HIGH-only")]:
        acc = (df[col] == df["actual_mod"]).mean() * 100
        bet_rate_pred = (df[col] == "BET").mean() * 100
        print(f"  {name:18s}  accuracy={acc:5.1f}%  pred_BET={bet_rate_pred:5.1f}% (actual_BET={(df['actual_mod']=='BET').mean()*100:.1f}%)")

    # ── Per ev_gap category, EV loss breakdown ──
    df["ev_gap"] = (df["ev_bet"] - df["ev_check"]).abs()
    df["gap_cat"] = pd.cut(df["ev_gap"], bins=[-0.001, 0.01, 0.05, 0.15, 0.50, 100],
                            labels=["tiny", "small", "med", "large", "huge"])
    print(f"\n=== EV loss per gap category (mean BB) ===")
    print(f"  gap_cat       check    bet    v6     hc")
    for cat in df["gap_cat"].cat.categories:
        sub = df[df["gap_cat"] == cat]
        if len(sub) == 0:
            continue
        print(f"  {str(cat):10s}  {sub['loss_check'].mean():.4f}  {sub['loss_bet'].mean():.4f}  {sub['loss_v6'].mean():.4f}  {sub['loss_hc'].mean():.4f}  (n={len(sub)})")

    # ── Show HIGH BET cells for book inclusion ──
    print(f"\n=== HIGH-CONFIDENCE BET cells (override conditions) ===")
    for _, r in high_bet_cells.sort_values("count", ascending=False).head(30).iterrows():
        print(f"  {r['size_bucket']:12s} × {r['equity_bucket']:13s} × {r['mv_cat']:15s} × {r['board_family']:18s} × {r['dv_cat']:18s}  med_bet={r['median_bet']*100:.0f}%  n={int(r['count'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
