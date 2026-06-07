#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Attack v6: eq + bet_size + bluff-candidate-flag.

Adds a "bluff candidate" indicator:
- has BDFD (one or two card backdoor)
- has top-rank blocker (matches board top)
- has A or K blocker

For low-eq combos, only bluff candidates bet.
For high-eq combos, value bet.
For middle-eq combos, mostly check unless strong draw.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path("/home/cuzic/poker-books")
RANKS = "23456789TJQKA"


def size_bucket(s):
    if pd.isna(s):
        return "unknown"
    if s < 0.45:
        return "small"
    if s < 0.85:
        return "mid"
    return "big"


def freq_to_3band(f):
    if f < 0.25: return "LOW"
    if f < 0.75: return "MIX"
    return "HIGH"


def has_strong_draw(dv: str) -> bool:
    return dv in {"oesd", "flush_draw", "combo_draw", "nut_flush_draw"}


def has_bdfd(dv: str) -> bool:
    return dv in {"twocards_bdfd", "onecard_bdfd"}


def has_gutshot(dv: str) -> bool:
    return dv == "gutshot"


def has_high_blocker(card_a: str, card_b: str) -> bool:
    """Has A or K blocker."""
    ranks = (card_a[0] if len(card_a) > 0 else "") + (card_b[0] if len(card_b) > 0 else "")
    return "A" in ranks or "K" in ranks


def has_top_blocker(card_a: str, card_b: str, board_flop: str) -> bool:
    """Hand contains a card matching board top rank."""
    if len(board_flop) < 6:
        return False
    board_ranks = [board_flop[0], board_flop[2], board_flop[4]]
    top = max(board_ranks, key=lambda r: RANKS.index(r) if r in RANKS else -1)
    hand_ranks = (card_a[0] if len(card_a) > 0 else "") + (card_b[0] if len(card_b) > 0 else "")
    return top in hand_ranks


def is_bluff_candidate(row) -> bool:
    """Returns True if this combo is a viable bluff candidate."""
    dv = row.get("dv_cat", "")
    if has_strong_draw(dv) or has_bdfd(dv) or has_gutshot(dv):
        return True
    ca = str(row.get("card_a", ""))
    cb = str(row.get("card_b", ""))
    bf = str(row.get("board_flop", ""))
    if has_high_blocker(ca, cb) or has_top_blocker(ca, cb, bf):
        return True
    return False


def predict_attack_v6(eq, size_b, is_bluff_cand, dv_cat, mv_cat):
    """v6 prediction with bluff candidate flag."""
    if pd.isna(eq) or pd.isna(size_b) or size_b == "unknown":
        return "MIX"

    # Stage 1: low eq
    if eq < 0.20:
        if is_bluff_cand and size_b == "small":
            return "MIX"  # mixed bluff at small size
        if is_bluff_cand and size_b == "big":
            return "LOW"  # bluff is rare at big size
        return "LOW"  # not bluff candidate → CHECK

    # Stage 2: mid-low (20-50)
    if eq < 0.50:
        # With strong made/draw → bet
        if has_strong_draw(dv_cat):
            return "MIX"  # semi-bluff
        return "LOW"

    # Stage 3: middle (50-70)
    if eq < 0.70:
        if size_b == "big":
            return "LOW"  # pot control vs big
        # small: thin value bets exist
        if mv_cat in {"top_pair", "overpair"}:
            return "MIX"
        return "LOW"

    # Stage 4: high (70-90)
    if eq < 0.90:
        if size_b == "big":
            return "LOW"  # slowplay vs big
        return "MIX"

    # Stage 5: very high (90-100)
    return "MIX"


def main() -> int:
    main_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "dataset_unified.csv", low_memory=False)
    bet_df = pd.read_csv(ROOT / "scripts" / "three_class_model" / "attack_bet_size.csv")
    bet_df = bet_df[["spot_id", "primary_size_pot"]].drop_duplicates(subset=["spot_id"])
    df = main_df.merge(bet_df, on="spot_id", how="left")

    df = df[(df["action_context"] == "attack") &
            (df["eq_percentile"].notna()) &
            (df["primary_size_pot"].notna()) &
            (df["equity_bucket"].notna()) & (df["equity_bucket"] != "")].copy()
    df["size_bucket"] = df["primary_size_pot"].apply(size_bucket)
    df["actual_band"] = df["bet_freq"].apply(freq_to_3band)
    df["is_bluff_cand"] = df.apply(is_bluff_candidate, axis=1)

    print(f"Attack rows: {len(df)} / spots: {df['spot_id'].nunique()}")
    print(f"\nBluff candidate share: {df['is_bluff_cand'].mean()*100:.1f}%")

    # Check assumption: at low eq, bluff candidates have higher bet_freq
    print(f"\n=== Verify: low-eq bet_freq, bluff cand vs not ===")
    low = df[df["eq_percentile"] < 0.20]
    bc_low = low[low["is_bluff_cand"]]
    nbc_low = low[~low["is_bluff_cand"]]
    print(f"  bluff candidate (n={len(bc_low)}): mean bet_freq={bc_low['bet_freq'].mean()*100:.1f}%")
    print(f"  not bluff cand  (n={len(nbc_low)}): mean bet_freq={nbc_low['bet_freq'].mean()*100:.1f}%")

    df["pred_band"] = df.apply(
        lambda r: predict_attack_v6(r["eq_percentile"], r["size_bucket"], r["is_bluff_cand"], r["dv_cat"], r["mv_cat"]),
        axis=1,
    )
    df["correct"] = df["pred_band"] == df["actual_band"]
    print(f"\n=== v6 overall accuracy: {df['correct'].mean()*100:.1f}% ===")
    print(pd.crosstab(df["pred_band"], df["actual_band"]))
    print()
    print("Normalized (row %):")
    print(pd.crosstab(df["pred_band"], df["actual_band"], normalize="index").round(2))

    print(f"\n=== Per (size × bucket) ===")
    for sz in ["small", "big"]:
        for bk in ["best_hands", "good_hands", "weak_hands", "trash_hands"]:
            sub = df[(df["size_bucket"] == sz) & (df["equity_bucket"] == bk)]
            if len(sub) < 100:
                continue
            acc = sub["correct"].mean() * 100
            print(f"  size={sz:5s} bucket={bk:13s} n={len(sub):6d}  acc={acc:5.1f}%")

    print(f"\n=== Per board_family ===")
    for bf, sub in df.groupby("board_family"):
        if len(sub) < 500:
            continue
        acc = sub["correct"].mean() * 100
        print(f"  {bf:18s} n={len(sub):6d}  acc={acc:5.1f}%")

    # Confidence tier
    keys = ["size_bucket", "equity_bucket", "mv_cat", "board_family", "dv_cat"]
    cell_iqr = df.groupby(keys)["bet_freq"].agg([
        ("q25", lambda x: x.quantile(0.25)),
        ("q75", lambda x: x.quantile(0.75)),
        "count",
    ]).reset_index()
    cell_iqr["iqr"] = cell_iqr["q75"] - cell_iqr["q25"]
    cell_iqr = cell_iqr[cell_iqr["count"] >= 30]
    cell_iqr["confidence"] = cell_iqr["iqr"].apply(
        lambda x: "HIGH" if x < 0.10 else ("MED" if x < 0.30 else "LOW")
    )
    conf_dict = {tuple(r[k] for k in keys): r["confidence"] for _, r in cell_iqr.iterrows()}
    df["conf"] = df.apply(lambda r: conf_dict.get(tuple(r[k] for k in keys), "LOW"), axis=1)
    print(f"\n=== Accuracy by confidence tier (v6) ===")
    for tier in ["HIGH", "MED", "LOW"]:
        sub = df[df["conf"] == tier]
        if len(sub) < 100:
            continue
        cov = len(sub) / len(df) * 100
        acc = sub["correct"].mean() * 100
        print(f"  {tier}: n={len(sub):6d} ({cov:.0f}%)  acc={acc:5.1f}%")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
