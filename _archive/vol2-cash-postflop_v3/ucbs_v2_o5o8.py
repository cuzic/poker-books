#!/usr/bin/env python3
"""
UCBS-v2 + O5-O8 例外ルール 4 つ追加

O5. mono board (3 同 suit)        → 信頼度 1 段 down
O6. paired board (ボードペア)     → 信頼度 1 段 up
O7. position lift (cash, mtt 別):
      SB (OOP opener)  : -0.05
      BTN (IP opener)  : ±0 (基準)
      CO/HJ/UTG (wide) : +0.15 (cash)
O8. A-high paired/dry (mtt BTN/CO) → freq +0.30 (range bet 100%)

WLS で 4 例外の offset を fit して、最適値を見つける。
"""
from __future__ import annotations
import json, glob, sys
from pathlib import Path
from collections import defaultdict

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2 import (
    HP_TABLE, DP_TABLE, HAND_CATEGORY, CONTEXTS,
    extract_board_features, is_polarize_board, parse_board_type,
    calc_confidence, apply_confidence_exception,
)
from ucbs_v2_simplify import (
    predict_simple, BASE_FREQ_SIMPLE, OVERBET_LIFT,
)
from calc import classify_board_type7


WIDE_OPEN_POS = {"CO", "HJ", "UTG"}


def is_ax_dry_or_paired(features):
    """A-high で paired か gap >= 8 (dry/disconnected) か"""
    if features["high"] != "A":
        return False
    return features["paired"] or features["gap"] >= 8


def predict_with_overrides(
    hand_type, draw_type, board, board_type_str, scenario, context,
    enabled=None,
    offset_mono=0.0, offset_paired=0.0,
    offset_sb=0.0, offset_btn=0.0, offset_wide=0.0,
    offset_ahigh=0.0,
):
    """簡易版 + O5-O8 override 適用"""
    if enabled is None:
        enabled = {"O5", "O6", "O7", "O8"}

    ctx = CONTEXTS[context]
    hp = HP_TABLE.get(hand_type, 0)
    dp = DP_TABLE.get(draw_type, 0)
    if hand_type == "no_made_hand" and draw_type == "oesd":
        cbs = hp - 2
    else:
        cbs = hp + dp
    threshold = ctx["thresholds"].get(scenario, 5)
    board_type = parse_board_type(board_type_str)
    features = extract_board_features(board)
    size = 116 if (ctx["polarize_enabled"] and is_polarize_board(features)) else 33

    conf = calc_confidence(cbs, threshold, board_type)
    conf = apply_confidence_exception(conf, board_type)

    # O5. mono board → conf down 1
    if "O5" in enabled and features["suit_pattern"] == "mono":
        if conf == "HIGH": conf = "MID"
        elif conf == "MID": conf = "LOW"

    # O6. paired board → conf up 1
    if "O6" in enabled and features["paired"]:
        if conf == "LOW": conf = "MID"
        elif conf == "MID": conf = "HIGH"

    direction = (cbs >= threshold)
    base = BASE_FREQ_SIMPLE[(conf, direction)]
    if size == 116:
        base += OVERBET_LIFT[(conf, direction)]

    alpha = ctx["alpha"]
    beta_term = ctx["beta"] if cbs >= 7 else 0.0
    category = HAND_CATEGORY.get(hand_type, "default")
    offset = ctx.get(f"off_{category}", 0.0)

    # O7. Position lift
    pos_lift = 0.0
    if "O7" in enabled:
        if scenario == "SB":
            pos_lift = offset_sb
        elif scenario == "BTN":
            pos_lift = offset_btn
        elif scenario in WIDE_OPEN_POS:
            pos_lift = offset_wide

    # O8. A-high dry/paired range bet (mtt BTN/CO 用)
    ax_lift = 0.0
    if ("O8" in enabled and context == "mtt_25bb"
        and scenario in ("BTN", "CO") and is_ax_dry_or_paired(features)):
        ax_lift = offset_ahigh

    freq = base + alpha + beta_term + offset + pos_lift + ax_lift
    return max(0.02, min(0.98, freq))


def gather():
    out = []
    with open("/home/cuzic/poker-books/cash-postflop/findings/cash_5cat_gto.json") as f:
        data = json.load(f)
    scen_map = {"BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ",
                "UTG_BB": "UTG", "SB_BB": "SB", "BTN_SB": "BTN"}
    for pos, boards in data.items():
        for board_key, info in boards.items():
            bt_str = info.get("type", "")
            board_cards = info.get("board", board_key)
            scen = scen_map.get(pos, "BTN")
            for h, vals in info.get("hand_cats", {}).items():
                if h not in HP_TABLE: continue
                n = vals.get("combos", 0)
                if n < 5: continue
                out.append({"ctx": "cash_100bb", "hand": h, "board": board_cards,
                            "bt_str": bt_str, "scenario": scen,
                            "n": n, "gto": vals["bet_pct"]/100.0})
    files = sorted(glob.glob("/home/cuzic/poker-books/mtt-postflop/findings/draw_study_*.jsonl"))
    for fp in files:
        name = Path(fp).stem.replace("draw_study_", "")
        if "3BP" in name: continue
        scen_pos = "BTN" if "_SB_cc" in name or ("SB" not in name and "CO" not in name) \
                   else "SB" if "_SB" in name else "CO"
        with open(fp) as f:
            for line in f:
                entry = json.loads(line)
                board = entry["board"]
                try: bt_str = classify_board_type7(board)
                except Exception: bt_str = ""
                for h, vals in entry.get("hand_agg", {}).items():
                    if h not in HP_TABLE: continue
                    n = vals.get("total", 0)
                    if n < 3: continue
                    out.append({"ctx": "mtt_25bb", "hand": h, "board": board,
                                "bt_str": bt_str, "scenario": scen_pos,
                                "n": n, "gto": vals["bet_pct"]/100.0})
    return out


def wrmse_eval(records, pred_fn):
    sse, total_n = 0.0, 0.0
    for r in records:
        pred = pred_fn(r)
        err = pred - r["gto"]
        sse += r["n"] * err * err
        total_n += r["n"]
    return (sse / total_n) ** 0.5 if total_n else 0.0


def fit_offsets_wls(records, ctx_filter=None):
    """O5-O8 の offset を WLS で fit。

    ベース: 簡易版 predict_simple(O5-O8 適用なし、ただし conf shift 型6 は有効)
    Features:
      x0 = 1 (constant)
      x1 = I(scenario == "SB")
      x2 = I(scenario in WIDE_OPEN_POS)   # BTN は default
      x3 = I(mono board)
      x4 = I(paired board)
      x5 = I(A-high dry/paired & mtt & scenario in {BTN, CO})
    """
    if ctx_filter:
        records = [r for r in records if r["ctx"] == ctx_filter]
    n = len(records)
    X = np.zeros((n, 6))
    y = np.zeros(n)
    w = np.zeros(n)
    for i, r in enumerate(records):
        feats = extract_board_features(r["board"])
        X[i, 0] = 1.0
        X[i, 1] = 1.0 if r["scenario"] == "SB" else 0.0
        X[i, 2] = 1.0 if r["scenario"] in WIDE_OPEN_POS else 0.0
        X[i, 3] = 1.0 if feats["suit_pattern"] == "mono" else 0.0
        X[i, 4] = 1.0 if feats["paired"] else 0.0
        X[i, 5] = 1.0 if (r["ctx"] == "mtt_25bb"
                          and r["scenario"] in ("BTN", "CO")
                          and is_ax_dry_or_paired(feats)) else 0.0
        pred = predict_simple(r["hand"], "no_draw", r["board"],
                              r["bt_str"], r["scenario"], r["ctx"])
        y[i] = r["gto"] - pred
        w[i] = r["n"]
    # Drop zero columns
    valid = [j for j in range(X.shape[1]) if np.any(X[:, j] != 0)]
    Xv = X[:, valid]
    W = np.diag(w)
    XtW = Xv.T @ W
    theta_v, *_ = np.linalg.lstsq(Xv * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)
    theta = np.zeros(X.shape[1])
    for k, j in enumerate(valid):
        theta[j] = theta_v[k]
    return theta


def main():
    records = gather()
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    mtt = [r for r in records if r["ctx"] == "mtt_25bb"]
    print(f"records: cash={len(cash)}, mtt={len(mtt)}")

    # ベースライン (簡易版、O5-O8 なし)
    base_fn = lambda r: predict_simple(
        r["hand"], "no_draw", r["board"], r["bt_str"],
        r["scenario"], r["ctx"])
    cash_base = wrmse_eval(cash, base_fn)
    mtt_base = wrmse_eval(mtt, base_fn)
    print(f"\n[ベースライン (簡易版)]  cash={cash_base*100:.2f}%  mtt={mtt_base*100:.2f}%")

    # ─── WLS fit: per-context ────────────────────────────────
    print("\n[WLS fit: context 別]")
    fits = {}
    for ctx in ["cash_100bb", "mtt_25bb"]:
        theta = fit_offsets_wls(records, ctx)
        fits[ctx] = theta
        print(f"\n{ctx}:")
        print(f"  base const = {theta[0]:+.3f}")
        print(f"  SB lift    = {theta[1]:+.3f}")
        print(f"  wide lift  = {theta[2]:+.3f}")
        print(f"  mono shift = {theta[3]:+.3f}")
        print(f"  pair shift = {theta[4]:+.3f}")
        print(f"  A-x lift   = {theta[5]:+.3f}")

    # ─── Apply fitted offsets ────────────────────────────────
    print("\n[fit 値を適用した WRMSE (conf shift は O5-O6 ロジカルに適用、O7/O8 は数値 lift)]")
    def make_fn(ctx_name):
        theta = fits[ctx_name]
        def fn(r):
            if r["ctx"] != ctx_name:
                return predict_simple(r["hand"], "no_draw", r["board"],
                                       r["bt_str"], r["scenario"], r["ctx"])
            # ベース予測に WLS fit 値を加算 (構造非対応)
            return predict_with_overrides(
                r["hand"], "no_draw", r["board"], r["bt_str"],
                r["scenario"], r["ctx"],
                enabled={"O5", "O6", "O7", "O8"},
                offset_mono=0.0, offset_paired=0.0,  # O5/O6 はロジカル shift
                offset_sb=theta[1], offset_btn=0.0, offset_wide=theta[2],
                offset_ahigh=theta[5],
            )
        return fn

    cash_fn = make_fn("cash_100bb")
    mtt_fn = make_fn("mtt_25bb")
    cash_w = wrmse_eval(cash, cash_fn)
    mtt_w = wrmse_eval(mtt, mtt_fn)
    print(f"  cash WRMSE: {cash_base*100:.2f}% → {cash_w*100:.2f}% (Δ {(cash_w-cash_base)*100:+.2f}pt)")
    print(f"  mtt  WRMSE: {mtt_base*100:.2f}% → {mtt_w*100:.2f}% (Δ {(mtt_w-mtt_base)*100:+.2f}pt)")

    # ─── Ablation (各 override を 1 つずつ落とす) ────────────
    print("\n[Ablation: 各 override を落としたときの WRMSE 増加コスト]")
    for ctx, recs in [("cash_100bb", cash), ("mtt_25bb", mtt)]:
        print(f"\n{ctx}:")
        # 全 override
        full_fn = cash_fn if ctx == "cash_100bb" else mtt_fn
        full_w = wrmse_eval(recs, full_fn)
        print(f"  Full WRMSE = {full_w*100:.2f}%")
        for drop in ["O5", "O6", "O7", "O8"]:
            theta = fits[ctx]
            def fn(r, drop=drop, theta=theta):
                if r["ctx"] != ctx:
                    return predict_simple(r["hand"], "no_draw", r["board"],
                                           r["bt_str"], r["scenario"], r["ctx"])
                enabled = {"O5", "O6", "O7", "O8"} - {drop}
                return predict_with_overrides(
                    r["hand"], "no_draw", r["board"], r["bt_str"],
                    r["scenario"], r["ctx"],
                    enabled=enabled,
                    offset_sb=theta[1] if drop != "O7" else 0,
                    offset_btn=0.0,
                    offset_wide=theta[2] if drop != "O7" else 0,
                    offset_ahigh=theta[5] if drop != "O8" else 0,
                )
            dropped_w = wrmse_eval(recs, fn)
            cost = (dropped_w - full_w) * 100
            marker = " ✓" if cost > 0.1 else "  "
            print(f"  drop {drop}: {dropped_w*100:.2f}% (cost {cost:+.2f}pt){marker}")


if __name__ == "__main__":
    main()
