#!/usr/bin/env python3
"""audit_new_formulas.py — 新公式群の huge_loss を unified dataset で測定

scenario_id ごとに適切な新公式を適用 → formula_loss を計算 → huge_loss 集計。
既存 (v9b/v10/v15) baseline と比較。

Usage: python3 audit_new_formulas.py
出力: scripts/three_class_model/NEW_FORMULA_AUDIT.md
"""
import statistics
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# 新公式群を import
from srp_formulas_v10 import flop_def_v9b_v10, turn_def_v10_v2, river_def_v15_v2  # noqa: E402
from cash_3bp_flop_v1 import cash_3bp_flop_def_v1  # noqa: E402
from cash_3bp_turn_v1 import cash_3bp_turn_def_v1  # noqa: E402
from cash_3bp_river_v1 import cash_3bp_river_def_v1  # noqa: E402
from cash_4bp_flop_v1 import cash_4bp_flop_v1  # noqa: E402
from cash_4bp_turn_v1 import cash_4bp_turn_v1  # noqa: E402
from cash_4bp_river_v1 import cash_4bp_river_v1  # noqa: E402
from cr_donk_defense_v1 import (  # noqa: E402
    flop_cr_def_v1, flop_donk_def_v1,
    turn_donk_def_v1, turn_cr_def_v1, river_donk_def_v1,
)
from river_opener_correction import river_def_v15_with_opener  # noqa: E402


DATASET = ROOT / "dataset_unified_v2.csv"
REPORT = ROOT / "NEW_FORMULA_AUDIT.md"


# ════════════════════ Scenario → formula 振り分け ════════════════════

def safe_get(r, k, default=None):
    """row dict-like から取得、NaN は default に置換."""
    v = r.get(k, default) if hasattr(r, 'get') else getattr(r, k, default)
    if isinstance(v, float) and pd.isna(v):
        return default
    return v


def predict_new(row):
    """scenario_id に応じて新公式を選択 → (formula_name, predicted_action)."""
    sid = str(row.get("scenario_id", ""))
    mv = safe_get(row, "mv_cat", "no_made_hand")
    dv = safe_get(row, "dv_cat", "no_draw")
    bf = safe_get(row, "board_family", "dry_high")
    eb = safe_get(row, "equity_bucket", "trash_hands")
    eqp = safe_get(row, "eq_percentile")
    bs = safe_get(row, "ip_bet_size", "med_75p")
    pol = safe_get(row, "opp_polarization", 0.85)
    nut_pct = safe_get(row, "opp_nut_pct", 0.15)

    try:
        # Cash 4BP (r ベース signature)
        if sid in ("N_cash_4bp_flop", "A_cash_4bp_flop", "P6_A_mtt_4bp_flop"):
            return "cash_4bp_flop_v1", cash_4bp_flop_v1(row)
        if sid in ("N_cash_4bp_turn", "P6_A_mtt_4bp_turn"):
            return "cash_4bp_turn_v1", cash_4bp_turn_v1(row)
        if sid in ("N_cash_4bp_river", "P5_B_4bp_river_traj", "P6_A_mtt_4bp_river"):
            return "cash_4bp_river_v1", cash_4bp_river_v1(row)

        # Cash 3BP / MTT 100bb 3BP
        # signature: cash_3bp_flop_def_v1(mv, dv, board_family, bet_size, is_short, opp_polarization)
        if sid in ("N_cash_3bp_flop", "N_mtt_3bp_flop"):
            return "cash_3bp_flop_def_v1", cash_3bp_flop_def_v1(mv, dv, bf, bs, False, pol)
        # signature: cash_3bp_turn_def_v1(mv, dv, board_family, bet_size, opp_polarization, opp_weak)
        if sid in ("P5_A_cash_3bp_turn", "P5_A_mtt_3bp_turn"):
            return "cash_3bp_turn_def_v1", cash_3bp_turn_def_v1(mv, dv, bf, bs, pol)
        # signature: cash_3bp_river_def_v1(mv, dv, board_family, bet_size, equity_bucket, eq_percentile, opp_pol, opp_nut_pct)
        if sid in ("N_cash_3bp_river", "P5_A_mtt_3bp_river", "P5_B_3bp_river_extra"):
            return "cash_3bp_river_def_v1", cash_3bp_river_def_v1(mv, dv, bf, bs, eb, eqp, pol, nut_pct)

        # CR/donk
        if sid in ("N_cash_cr_def", "A_cash_cr_def_full"):
            return "flop_cr_def_v1", flop_cr_def_v1(mv, dv, bf, pol)
        if sid in ("N_cash_donk_def", "A_cash_donk_def_full"):
            return "flop_donk_def_v1", flop_donk_def_v1(mv, dv, bf, pol)
        if sid == "P5_D_turn_donk_def":
            return "turn_donk_def_v1", turn_donk_def_v1(mv, dv, bf, pol)
        if sid == "P5_D_turn_cr_def":
            return "turn_cr_def_v1", turn_cr_def_v1(mv, dv, bf, pol, bs)
        if sid == "P5_D_river_donk_def":
            return "river_donk_def_v1", river_donk_def_v1(mv, eb, bf, pol, bs)

        # opener split (CO/HJ open)
        if sid == "N_cash_hj_open_river":
            return "river_def_v15_with_opener", river_def_v15_with_opener(mv, eb, bf, bs, "HJ", eqp)
        if sid == "N_cash_co_open_river":
            return "river_def_v15_with_opener", river_def_v15_with_opener(mv, eb, bf, bs, "CO", eqp)

        # SRP baseline (v10/v15 拡張) — Cash SRP + BvB + BTN-SB
        if sid in ("B_flop",):
            return "flop_def_v9b_v10", flop_def_v9b_v10(mv, dv, bf, bs, opp_polarization=pol, opp_nut_pct=nut_pct)
        if sid in ("B_turn", "N_mtt200_turn"):
            return "turn_def_v10_v2", turn_def_v10_v2(mv, dv, bf, bs, opp_nut_pct=nut_pct)
        if sid in ("B_river", "N_bvb_srp_river", "N_btn_sb_river", "N_mtt100_river",
                   "N_mtt25_river", "N_mtt200_river"):
            return "river_def_v15_v2", river_def_v15_v2(mv, eb, bf, bs, eqp,
                                                          opp_polarization=pol)
    except Exception as e:
        return f"ERROR:{type(e).__name__}", None
    return "no_match", None


def compute_loss(row, action):
    """action に対する EV を見つけて formula_loss = best_ev - ev_action."""
    if action is None: return None
    best_ev = safe_get(row, "best_ev")
    ev_f = safe_get(row, "ev_fold")
    ev_c = safe_get(row, "ev_call")
    ev_r = safe_get(row, "ev_raise")
    if best_ev is None: return None
    if action == "FOLD" and ev_f is not None:
        return best_ev - ev_f
    if action == "CALL" and ev_c is not None:
        return best_ev - ev_c
    if action == "RAISE" and ev_r is not None:
        return best_ev - ev_r
    # action が tree に無い → worst-case (ev_gap)
    ev_gap = safe_get(row, "ev_gap")
    return ev_gap if ev_gap is not None else None


# ════════════════════ Main ════════════════════

def main():
    print(f"Loading {DATASET}...")
    df = pd.read_csv(DATASET, low_memory=False)
    print(f"  {len(df)} rows / {len(df.columns)} cols")

    # filter rows where best_ev exists
    mask = df["best_ev"].notna()
    df = df[mask].copy()
    print(f"  {len(df)} rows with best_ev")

    # apply new formulas
    print("Applying new formulas...")
    df[["new_formula", "new_action"]] = df.apply(
        lambda r: pd.Series(predict_new(r)), axis=1
    )

    # compute formula_loss for new formulas
    df["new_formula_loss"] = df.apply(lambda r: compute_loss(r, r["new_action"]), axis=1)
    df["new_correct"] = (df["new_action"] == df["best_action"])

    # group by scenario_id × new_formula
    scenario_stats = []
    for sid, sub in df.groupby("scenario_id"):
        sub = sub[sub["new_formula"] != "no_match"]
        if len(sub) == 0: continue
        formula_used = sub["new_formula"].mode().iloc[0] if len(sub) > 0 else "none"
        n = len(sub)
        # new metrics
        valid = sub[sub["new_formula_loss"].notna()]
        new_acc = (valid["new_correct"].sum() / len(valid) * 100) if len(valid) > 0 else None
        new_mean_loss = valid["new_formula_loss"].mean() if len(valid) > 0 else None
        new_huge = valid[valid["new_formula_loss"] > 0.5]
        new_huge_loss = new_huge["new_formula_loss"].mean() if len(new_huge) > 0 else 0
        new_huge_pct = (len(new_huge) / len(valid) * 100) if len(valid) > 0 else None
        # baseline (from CSV)
        old_valid = sub[sub["formula_loss"].notna()]
        old_acc = (old_valid["formula_correct"].sum() / len(old_valid) * 100) if len(old_valid) > 0 else None
        old_mean_loss = old_valid["formula_loss"].mean() if len(old_valid) > 0 else None
        old_huge = old_valid[old_valid["formula_loss"] > 0.5]
        old_huge_loss = old_huge["formula_loss"].mean() if len(old_huge) > 0 else 0
        old_huge_pct = (len(old_huge) / len(old_valid) * 100) if len(old_valid) > 0 else None

        scenario_stats.append({
            "scenario_id": sid, "formula": formula_used, "n": n,
            "old_acc": round(old_acc, 1) if old_acc is not None else None,
            "new_acc": round(new_acc, 1) if new_acc is not None else None,
            "old_mean_loss": round(old_mean_loss, 3) if old_mean_loss is not None else None,
            "new_mean_loss": round(new_mean_loss, 3) if new_mean_loss is not None else None,
            "old_huge_loss": round(old_huge_loss, 3) if old_huge_loss is not None else None,
            "new_huge_loss": round(new_huge_loss, 3) if new_huge_loss is not None else None,
            "old_huge_pct": round(old_huge_pct, 1) if old_huge_pct is not None else None,
            "new_huge_pct": round(new_huge_pct, 1) if new_huge_pct is not None else None,
        })

    # sort by formula then by improvement (old_huge_loss - new_huge_loss)
    scenario_stats.sort(key=lambda s: (
        s["formula"],
        -(s.get("old_huge_loss") or 0) + (s.get("new_huge_loss") or 0)
    ))

    # write report
    with open(REPORT, "w") as f:
        f.write("# New Formula Audit Report\n\n")
        f.write(f"Dataset: dataset_unified_v2.csv ({len(df):,} rows with best_ev)\n\n")
        f.write("各 scenario_id に新公式を適用、formula_loss (best_ev − ev_action) を計算。\n")
        f.write("baseline (v9b/v10/v15) との直接比較。\n\n")

        f.write("## Summary (formula → average huge_loss reduction)\n\n")
        f.write("| Formula | n scenarios | avg old huge_loss | avg new huge_loss | reduction |\n")
        f.write("|---|---:|---:|---:|---:|\n")
        formulas = {}
        for s in scenario_stats:
            fname = s["formula"]
            if fname not in formulas: formulas[fname] = []
            formulas[fname].append(s)
        for fname, ss in formulas.items():
            old_h = [s["old_huge_loss"] for s in ss if s["old_huge_loss"] is not None]
            new_h = [s["new_huge_loss"] for s in ss if s["new_huge_loss"] is not None]
            old_avg = statistics.mean(old_h) if old_h else 0
            new_avg = statistics.mean(new_h) if new_h else 0
            red = old_avg - new_avg
            red_pct = f" ({red/old_avg*100:+.1f}%)" if old_avg else ""
            f.write(f"| **{fname}** | {len(ss)} | {old_avg:.3f} | {new_avg:.3f} | "
                    f"**{red:+.3f}**{red_pct} |\n")

        f.write("\n## Per-scenario detail\n\n")
        f.write("| scenario | formula | n | old_acc → new_acc | old_huge_loss → new_huge_loss | old_huge% → new_huge% |\n")
        f.write("|---|---|---:|---|---|---|\n")
        for s in scenario_stats:
            def diff(old, new, suffix=""):
                if old is None or new is None: return f"{old} → {new}"
                d = new - old
                sign = "+" if d > 0 else ""
                return f"{old}{suffix} → **{new}**{suffix} ({sign}{d:.2f})"
            f.write(f"| {s['scenario_id']} | {s['formula']} | {s['n']} | "
                    f"{diff(s['old_acc'], s['new_acc'], '%')} | "
                    f"{diff(s['old_huge_loss'], s['new_huge_loss'])} | "
                    f"{diff(s['old_huge_pct'], s['new_huge_pct'], '%')} |\n")

    print(f"\nReport: {REPORT}")
    # quick console summary
    print("\n=== Summary ===")
    for fname, ss in formulas.items():
        old_h = [s["old_huge_loss"] for s in ss if s["old_huge_loss"] is not None]
        new_h = [s["new_huge_loss"] for s in ss if s["new_huge_loss"] is not None]
        if old_h and new_h:
            old_avg = statistics.mean(old_h)
            new_avg = statistics.mean(new_h)
            print(f"  {fname:30s}: huge_loss {old_avg:.3f} → {new_avg:.3f} "
                  f"({(new_avg-old_avg)/old_avg*100:+.1f}%)")


if __name__ == "__main__":
    main()
