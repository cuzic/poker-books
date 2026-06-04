#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas", "numpy"]
# ///
"""Verify the unified equity-bucket framework on real GTO data.

For each (spot, combo) record, the framework predicts an action category:
  Attack:   BET / CHECK
  Defense:  RAISE / CALL / FOLD

We compare to actual GTO action (the most-frequently-chosen action per combo).

Metrics:
  - Per-context accuracy
  - Confusion matrix
  - Failure modes (where the framework is wrong)
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from train_tree import add_features  # noqa: E402

ROOT = Path("/home/cuzic/poker-books")
DATA = ROOT / "knowledges" / "gto_wizard_full"
CSV = ROOT / "scripts" / "three_class_model" / "dataset_with_buckets.csv"

# ── Hand classification helpers ──
RANKS = "23456789TJQKA"
BROADWAY = set("TJQKA")


def hand_features(card_a: str, card_b: str) -> dict:
    """Return broadway / connector flags from 2 hole cards."""
    r1, r2 = card_a[0], card_b[0]
    i1, i2 = RANKS.index(r1), RANKS.index(r2)
    is_pair = r1 == r2
    is_suited = card_a[1] == card_b[1]
    is_broadway_both = r1 in BROADWAY and r2 in BROADWAY  # e.g., KJ
    is_broadway_one = (r1 in BROADWAY) ^ (r2 in BROADWAY)
    gap = abs(i1 - i2)
    is_connector = gap <= 1 and not is_pair  # 76, 87, 98 etc
    is_one_gap = gap == 2 and not is_pair    # 75, 86 etc
    # Pure garbage = no broadway, no connector, no pair
    is_pure_garbage = (not is_broadway_one and not is_broadway_both and not is_connector and not is_one_gap and not is_pair)
    return {
        "is_pair": is_pair,
        "is_suited": is_suited,
        "is_broadway_both": is_broadway_both,
        "is_broadway_one": is_broadway_one,
        "is_connector": is_connector,
        "is_one_gap": is_one_gap,
        "is_pure_garbage": is_pure_garbage,
        "rank_max": max(i1, i2),
        "rank_min": min(i1, i2),
    }


def has_any_draw(dv_cat: str) -> bool:
    return dv_cat in {
        "gutshot", "oesd", "flush_draw", "combo_draw",
        "onecard_bdfd", "twocards_bdfd", "nut_flush_draw",
    }


# ── Action context classification ──
def derive_action_context(row, all_actions: set[str]) -> str:
    """Decide if hero faces a bet (defense) or acts first (attack).

    We look at action codes available: if FOLD or CALL is in the available actions,
    hero is facing a bet → defense. Otherwise → attack.
    """
    if "F" in all_actions or "C" in all_actions:
        return "defense"
    return "attack"


# ── Unified framework prediction ──
def predict_action(
    bucket: str, mv_cat: str, dv_cat: str, board_family: str,
    hand_feats: dict, action_context: str,
) -> str:
    """Apply the unified framework. Returns one of:
      Attack:  BET / CHECK
      Defense: RAISE / CALL / FOLD
    """
    nut_or_2p = mv_cat in {"set", "trips", "two_pair", "straight", "flush", "fullhouse", "quads"}
    is_overpair = mv_cat == "overpair"
    is_top_pair = mv_cat == "top_pair"
    has_draw_flag = has_any_draw(dv_cat)
    # bluff-suitable trash: any draw, OR broadway both/one, OR connector
    is_bluff_trash = has_draw_flag or hand_feats["is_broadway_both"] or hand_feats["is_broadway_one"] or hand_feats["is_connector"]

    # Board adjustments
    paired_board = board_family == "paired"
    monotone_board = board_family == "monotone"
    dry_high_board = board_family == "dry_high"

    if action_context == "attack":
        # ── Attack ──
        if bucket == "best_hands":
            if nut_or_2p or is_overpair:
                return "BET"
            if is_top_pair:
                # TP on dry → slowplay; on wet/paired → bet
                if paired_board:
                    return "BET"
                if dry_high_board:
                    return "CHECK"
                return "BET"  # dynamic/etc default to BET
            return "BET"  # safety
        if bucket in {"good_hands", "weak_hands"}:
            if paired_board:
                return "BET"  # paired board adjustment
            return "CHECK"
        if bucket == "trash_hands":
            if paired_board:
                return "BET"
            if monotone_board:
                return "CHECK"
            if is_bluff_trash:
                return "BET"
            return "CHECK"
        return "CHECK"

    else:
        # ── Defense ──
        if bucket == "best_hands":
            if nut_or_2p or is_overpair:
                return "RAISE"
            if is_top_pair:
                # TP usually calls; raise on paired board (mixed game)
                return "CALL"
            return "CALL"
        if bucket in {"good_hands", "weak_hands"}:
            return "CALL"  # bluff-catch
        if bucket == "trash_hands":
            if monotone_board:
                return "FOLD"
            if is_bluff_trash:
                # CR bluff candidate but most often CALL; we say CALL as the safer default
                # Could be RAISE on paired board
                if paired_board:
                    return "RAISE"
                return "CALL"
            return "FOLD"
        return "FOLD"


# ── Per-spot action lookup ──
def load_spot_actions(spot_id: str) -> tuple[set[str], dict[int, dict[str, float]]]:
    """Return (available_action_codes, per-combo action freq map).
    per-combo map: combo_index → {action_code: freq}
    """
    for p in DATA.glob(f"**/{spot_id}.json"):
        d = json.loads(p.read_text())
        actions = d.get("action_solutions") or []
        codes = set()
        per_combo: dict[int, dict[str, float]] = defaultdict(dict)
        for a in actions:
            code = (a.get("action") or {}).get("code") or ""
            codes.add(code)
            strat = a.get("strategy") or []
            for i, f in enumerate(strat):
                if f > 0.001:
                    per_combo[i][code] = f
        return codes, per_combo
    return set(), {}


def actual_action(per_combo: dict[str, float], action_codes: set[str]) -> str:
    """Determine the actual most-likely action category for this combo.

    Returns one of: BET / CHECK / RAISE / CALL / FOLD
    """
    if not per_combo:
        return "UNKNOWN"
    # Build per-category aggregate
    cat_freq: dict[str, float] = {"BET": 0.0, "CHECK": 0.0, "RAISE": 0.0, "CALL": 0.0, "FOLD": 0.0}
    for code, f in per_combo.items():
        if code == "X":
            cat_freq["CHECK"] += f
        elif code == "F":
            cat_freq["FOLD"] += f
        elif code == "C":
            cat_freq["CALL"] += f
        elif code.startswith("R"):
            # If FOLD/CALL exists, this is a defense raise; else attack bet
            if "F" in action_codes or "C" in action_codes:
                cat_freq["RAISE"] += f
            else:
                cat_freq["BET"] += f
        else:
            pass
    return max(cat_freq.items(), key=lambda kv: kv[1])[0]


def main() -> int:
    df = pd.read_csv(CSV, low_memory=False)
    df = add_features(df)
    print(f"Loaded {len(df)} rows / {df['spot_id'].nunique()} spots")

    # Pre-compute per-spot action data
    print("Loading per-spot action codes & per-combo strategies...")
    spot_cache: dict[str, tuple[set[str], dict[int, dict[str, float]]]] = {}

    # Compute predictions
    print("Predicting + comparing...")
    pred_list = []
    actual_list = []
    ctx_list = []
    extra = []

    for _, row in df.iterrows():
        spot_id = row["spot_id"]
        if spot_id not in spot_cache:
            spot_cache[spot_id] = load_spot_actions(spot_id)
        codes, per_combo = spot_cache[spot_id]
        # We need per-combo index. The CSV row's order matches extract output, but we
        # don't preserve combo index. Skip if we can't find it.
        # Fallback: use card_a + card_b to reconstruct combo index.
        ca, cb = str(row.get("card_a") or ""), str(row.get("card_b") or "")
        if len(ca) != 2 or len(cb) != 2:
            continue
        # Compute combo index from cards
        def card_idx(c: str) -> int:
            return RANKS.index(c[0]) * 4 + "cdhs".index(c[1])
        i1, i2 = card_idx(ca), card_idx(cb)
        if i1 > i2:
            i1, i2 = i2, i1
        # combo i in [0..1325] enumeration: i = i1 * (51 - (i1-1)/2) + ... — use formula
        # Easier: pre-enumerate. But this is O(1326) per row; let's just compute analytically.
        # combo_index from (a,b) with a<b:
        #   sum_{k=0..a-1} (51 - k) + (b - a - 1)
        # That's: a*(101 - a)//2 + (b - a - 1)
        a, b = i1, i2
        combo_index = a * (101 - a) // 2 + (b - a - 1)
        per = per_combo.get(combo_index, {})
        if not per:
            continue
        act_ctx = derive_action_context(row, codes)
        bucket = row["equity_bucket"]
        feats = hand_features(ca, cb)
        pred = predict_action(
            bucket, str(row["mv_cat"]), str(row["dv_cat"]),
            str(row.get("board_family", "")),
            feats, act_ctx,
        )
        actual = actual_action(per, codes)
        pred_list.append(pred)
        actual_list.append(actual)
        ctx_list.append(act_ctx)
        extra.append((row["topic"], bucket, row["mv_cat"], row.get("board_family",""), row["street"], row["hero_rel"]))

    print(f"Evaluated {len(pred_list)} rows")

    # Combine into DataFrame for analysis
    result = pd.DataFrame({
        "pred": pred_list,
        "actual": actual_list,
        "ctx": ctx_list,
        "topic": [e[0] for e in extra],
        "bucket": [e[1] for e in extra],
        "mv": [e[2] for e in extra],
        "board_family": [e[3] for e in extra],
        "street": [e[4] for e in extra],
        "hero_rel": [e[5] for e in extra],
    })

    # ── Overall accuracy ──
    overall_acc = (result["pred"] == result["actual"]).mean()
    print(f"\n=== Overall accuracy: {overall_acc*100:.1f}% ===")

    # Per-context accuracy
    print(f"\n=== Accuracy by action context ===")
    for ctx, sub in result.groupby("ctx"):
        acc = (sub["pred"] == sub["actual"]).mean()
        print(f"  {ctx:10s}  n={len(sub):6d}  acc={acc*100:.1f}%")

    # Confusion matrix
    print(f"\n=== Confusion matrix (pred vs actual) ===")
    confusion = result.groupby(["pred", "actual"]).size().unstack(fill_value=0)
    print(confusion)

    # Per-bucket accuracy
    print(f"\n=== Accuracy by bucket × ctx ===")
    for (bk, ctx), sub in result.groupby(["bucket", "ctx"]):
        if len(sub) < 100:
            continue
        acc = (sub["pred"] == sub["actual"]).mean()
        print(f"  {bk:13s} {ctx:8s} n={len(sub):6d}  acc={acc*100:.1f}%")

    # Per-board-family accuracy
    print(f"\n=== Accuracy by board family ===")
    for bf, sub in result.groupby("board_family"):
        if len(sub) < 100:
            continue
        acc = (sub["pred"] == sub["actual"]).mean()
        print(f"  {bf:20s} n={len(sub):6d}  acc={acc*100:.1f}%")

    # Most frequent error patterns
    print(f"\n=== Top error patterns (bucket → wrong predicted action) ===")
    errors = result[result["pred"] != result["actual"]]
    err_groups = errors.groupby(["ctx", "bucket", "pred", "actual"]).size().sort_values(ascending=False).head(15)
    for (ctx, bk, pred, actual), n in err_groups.items():
        print(f"  {ctx:8s} {bk:13s} predicted={pred:5s} actual={actual:5s}  n={n}")

    # Save
    out_csv = ROOT / "scripts" / "three_class_model" / "verification_results.csv"
    result.to_csv(out_csv, index=False)
    print(f"\nSaved → {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
