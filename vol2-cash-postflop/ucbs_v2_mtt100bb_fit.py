#!/usr/bin/env python3
"""
UCBS-v2 mtt_100bb context の α/β/offset を WLS で fit。

データ: mtt-postflop/findings/draw_study_MTT100BB.jsonl
構造: 既存 cash_100bb / mtt_25bb と同じ式に新規パラメータを fit。

ステップ:
  1. mtt_100bb の record を読み込み (scenario × board × hand)
  2. 既存 base_freq, HP_TABLE, DP_TABLE, exception ロジックを流用
  3. WLS で α, β, off_slowplay, off_trash, off_premium, position lift を fit
  4. WRMSE 測定
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import defaultdict

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2 import (
    HP_TABLE, HAND_CATEGORY, BASE_FREQ, BASE_FREQ_FALLBACK,
    extract_board_features, is_polarize_board, parse_board_type,
    calc_confidence, apply_confidence_exception, is_ax_dry_or_paired,
)
from ucbs_v2_simplify import BASE_FREQ_SIMPLE, OVERBET_LIFT
from calc import classify_board_type7


SCENARIO_POS = {
    "UTG_BB": "UTG", "HJ_BB": "HJ", "CO_BB": "CO",
    "BTN_BB": "BTN", "SB_BB": "SB",
}


def load_mtt100bb():
    """draw_study_MTT100BB.jsonl から records を構築"""
    fp = "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_MTT100BB.jsonl"
    out = []
    with open(fp) as f:
        for line in f:
            entry = json.loads(line)
            board = entry["board"]
            scen = SCENARIO_POS.get(entry["scenario"], "BTN")
            try:
                bt_str = classify_board_type7(board)
                feats = extract_board_features(board)
            except Exception:
                continue
            bt = parse_board_type(bt_str)
            for h, vals in entry.get("hand_agg", {}).items():
                if h not in HP_TABLE:
                    continue
                n = vals.get("total", 0)
                if n < 3:
                    continue
                out.append({
                    "scenario": scen, "board": board,
                    "bt_str": bt_str, "bt": bt,
                    "hand": h, "n": n,
                    "gto": vals["bet_pct"] / 100.0,
                    "feats": feats,
                })
    return out


def predict_base(r, alpha=0.0, beta=0.0, off_slowplay=0.0, off_trash=0.0,
                 off_premium=0.0, pos_lifts=None, ax_lift=0.0,
                 mono_down=False, T=5):
    """UCBS-v2 構造を直接実装 (mtt_100bb 用)"""
    if pos_lifts is None:
        pos_lifts = {}
    hp = HP_TABLE[r["hand"]]
    cbs = hp  # draw=no_draw
    conf = calc_confidence(cbs, T, r["bt"])
    conf = apply_confidence_exception(conf, r["bt"],
                                        suit_pattern=r["feats"]["suit_pattern"],
                                        mono_down=mono_down)
    direction = (cbs >= T)
    base = BASE_FREQ_SIMPLE[(conf, direction)]
    # mtt は polarize_enabled=False
    cat = HAND_CATEGORY.get(r["hand"], "default")
    offset = {"slowplay": off_slowplay, "trash": off_trash, "premium": off_premium}.get(cat, 0.0)
    beta_term = beta if cbs >= 7 else 0.0
    pos_lift = pos_lifts.get(r["scenario"], 0.0)
    # A-x lift (BTN/CO で a-high dry/paired)
    ax = ax_lift if (r["scenario"] in ("BTN", "CO") and is_ax_dry_or_paired(r["feats"])) else 0.0
    return max(0.02, min(0.98, base + alpha + beta_term + offset + pos_lift + ax))


def build_feature_matrix(records):
    """WLS 用の feature matrix"""
    n = len(records)
    # Features: alpha, beta·I(CBS≥7), slowplay, trash, premium, SB_lift, wide_lift, ax_lift
    X = np.zeros((n, 8))
    y = np.zeros(n)
    w = np.zeros(n)
    for i, r in enumerate(records):
        hp = HP_TABLE[r["hand"]]
        cbs = hp
        T = 5
        beta_ind = 1.0 if cbs >= 7 else 0.0
        cat = HAND_CATEGORY.get(r["hand"], "default")
        is_sb = 1.0 if r["scenario"] == "SB" else 0.0
        is_wide = 1.0 if r["scenario"] in ("CO", "HJ", "UTG") else 0.0
        is_ax = 1.0 if (r["scenario"] in ("BTN", "CO") and is_ax_dry_or_paired(r["feats"])) else 0.0
        X[i] = [
            1.0,                                       # alpha
            beta_ind,                                  # beta · I(CBS≥7)
            1.0 if cat == "slowplay" else 0.0,
            1.0 if cat == "trash" else 0.0,
            1.0 if cat == "premium" else 0.0,
            is_sb,
            is_wide,
            is_ax,
        ]
        # Base = simple_base[(conf, dir)] (mono shift は試行的、まず off)
        conf = calc_confidence(cbs, T, r["bt"])
        conf = apply_confidence_exception(conf, r["bt"])  # 型6 only
        direction = (cbs >= T)
        base = BASE_FREQ_SIMPLE[(conf, direction)]
        y[i] = r["gto"] - base
        w[i] = r["n"]
    return X, y, w


def wls_solve(X, y, w):
    valid_cols = [j for j in range(X.shape[1]) if np.any(X[:, j] != 0)]
    Xv = X[:, valid_cols]
    theta_v, *_ = np.linalg.lstsq(Xv * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)
    theta = np.zeros(X.shape[1])
    for k, j in enumerate(valid_cols):
        theta[j] = theta_v[k]
    return theta


def wrmse(records, **kwargs):
    sse, total_n = 0.0, 0.0
    for r in records:
        pred = predict_base(r, **kwargs)
        err = pred - r["gto"]
        sse += r["n"] * err * err
        total_n += r["n"]
    return (sse / total_n) ** 0.5 if total_n else 0.0


def main():
    records = load_mtt100bb()
    print(f"mtt_100bb records: {len(records)} (combos {sum(r['n'] for r in records)})")
    if not records:
        print("No data. Run mtt100bb_draw_study.py --collect first.")
        return

    # ベースライン: 既存 mtt_25bb パラメータを mtt_100bb に流用した場合
    print("\n[Baseline] 既存 mtt_25bb パラメータをそのまま当てた場合")
    base_w = wrmse(records,
        alpha=+0.06, beta=+0.31,
        off_slowplay=-0.28, off_trash=-0.23, off_premium=+0.15,
        pos_lifts={"SB": -0.10, "BTN": 0, "CO": +0.13, "HJ": +0.13, "UTG": +0.13},
        ax_lift=+0.30)
    print(f"  WRMSE = {base_w*100:.2f}%")

    # WLS fit (mtt_100bb 専用)
    print("\n[WLS fit] mtt_100bb 専用パラメータ")
    X, y, w = build_feature_matrix(records)
    theta = wls_solve(X, y, w)
    fit_w = wrmse(records,
        alpha=theta[0], beta=theta[1],
        off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4],
        pos_lifts={"SB": theta[5], "BTN": 0, "CO": theta[6], "HJ": theta[6], "UTG": theta[6]},
        ax_lift=theta[7])
    print(f"  α        = {theta[0]:+.3f}")
    print(f"  β        = {theta[1]:+.3f}  (CBS ≥ 7)")
    print(f"  slowplay = {theta[2]:+.3f}")
    print(f"  trash    = {theta[3]:+.3f}")
    print(f"  premium  = {theta[4]:+.3f}")
    print(f"  SB lift  = {theta[5]:+.3f}")
    print(f"  wide lift= {theta[6]:+.3f}")
    print(f"  ax lift  = {theta[7]:+.3f}")
    print(f"  WRMSE    = {fit_w*100:.2f}%")
    print(f"  改善: {(base_w - fit_w)*100:+.2f}pt vs 流用ベースライン")

    # ファイル別 WRMSE
    print("\n[シナリオ別 WRMSE]")
    by_scen = defaultdict(list)
    for r in records:
        by_scen[r["scenario"]].append(r)
    for scen, recs in by_scen.items():
        wf = wrmse(recs,
            alpha=theta[0], beta=theta[1],
            off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4],
            pos_lifts={"SB": theta[5], "BTN": 0, "CO": theta[6], "HJ": theta[6], "UTG": theta[6]},
            ax_lift=theta[7])
        n = sum(r["n"] for r in recs)
        print(f"  {scen}: WRMSE={wf*100:.2f}%, n={len(recs)}, combos={int(n)}")

    # Hand 別 bias
    print("\n[Hand 別 bias]")
    by_hand = defaultdict(lambda: [0.0, 0.0])
    for r in records:
        pred = predict_base(r,
            alpha=theta[0], beta=theta[1],
            off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4],
            pos_lifts={"SB": theta[5], "BTN": 0, "CO": theta[6], "HJ": theta[6], "UTG": theta[6]},
            ax_lift=theta[7])
        err = pred - r["gto"]
        by_hand[r["hand"]][0] += r["n"] * err
        by_hand[r["hand"]][1] += r["n"]
    for h, (esum, n) in sorted(by_hand.items(), key=lambda x: -x[1][1]):
        if n > 0:
            print(f"  {h:14s} combos={int(n):>5d}  bias={esum/n*100:+6.1f}%")


if __name__ == "__main__":
    main()
