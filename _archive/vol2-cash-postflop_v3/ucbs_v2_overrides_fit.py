#!/usr/bin/env python3
"""
UCBS-v2 override の offset を WLS で fit。

各 override は「条件 → 補正値 (offset)」の形。offset を WLS で fit:

  residual_i = gto_i - pred_v2_i
  features (列): [O1_nutted, O2_trash, O3_wide_polarize, O4_type6_high, O5_mid_false_air]
  各 cell に対し I(条件) を 1/0 で立てる
  解: θ = (X'WX)⁻¹ X'Wy (W は combos)

これで「override の存在価値」を客観的に判定できる。
- |offset| が大きいなら override は有効
- |offset| が小さいなら不要

Context 別に fit する案と、同じ条件で context 共通 fit する案の両方を試す。
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2_overrides import (
    gather_all_records, NUTTED_HANDS, WIDE_OPEN_POS,
)
from ucbs_v2 import BASE_FREQ


def build_features(records, ctx_filter=None):
    """各 record に対する override feature vector を構築。

    Features:
      x0 = 1 (constant)                                  ← 全体 bias
      x1 = I(hand ∈ nutted = set/trips/fullhouse/quads)
      x2 = I(hand = low_pair)
      x3 = I(scenario ∈ wide & size = 116)               ← cash polarize 板での wide open
      x4 = I(board_type = 6)
      x5 = I(conf = MID & not dir & cbs ≤ 2)
    """
    if ctx_filter:
        records = [r for r in records if r["ctx"] == ctx_filter]
    n = len(records)
    X = np.zeros((n, 6))
    y = np.zeros(n)
    w = np.zeros(n)
    for i, r in enumerate(records):
        d = r["decision"]
        X[i, 0] = 1.0
        X[i, 1] = 1.0 if r["hand"] in NUTTED_HANDS else 0.0
        X[i, 2] = 1.0 if r["hand"] == "low_pair" else 0.0
        X[i, 3] = 1.0 if (r["scenario"] in WIDE_OPEN_POS and d.size == 116) else 0.0
        X[i, 4] = 1.0 if r["board_type"] == 6 else 0.0
        X[i, 5] = 1.0 if (d.confidence == "MID" and not d.direction and d.cbs <= 2) else 0.0
        y[i] = r["gto"] - r["pred_v2"]
        w[i] = r["n"]
    return X, y, w, records


def wls_solve(X, y, w):
    # 全 0 列を検出して除外 (zero-count feature → singular)
    valid_cols = [j for j in range(X.shape[1]) if np.any(X[:, j] != 0)]
    Xv = X[:, valid_cols]
    W = np.diag(w)
    XtW = Xv.T @ W
    try:
        theta_v = np.linalg.solve(XtW @ Xv, XtW @ y)
    except np.linalg.LinAlgError:
        theta_v, *_ = np.linalg.lstsq(Xv * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)
    theta = np.zeros(X.shape[1])
    for k, j in enumerate(valid_cols):
        theta[j] = theta_v[k]
    return theta


def wrmse_with_offsets(records, theta, override_idx_fn):
    """theta を適用したときの WRMSE"""
    sse, total_n = 0.0, 0.0
    for r in records:
        d = r["decision"]
        # 各 override 適用
        delta = theta[0]  # constant
        if r["hand"] in NUTTED_HANDS:
            delta += theta[1]
        if r["hand"] == "low_pair":
            delta += theta[2]
        if r["scenario"] in WIDE_OPEN_POS and d.size == 116:
            delta += theta[3]
        if r["board_type"] == 6:
            delta += theta[4]
        if d.confidence == "MID" and not d.direction and d.cbs <= 2:
            delta += theta[5]
        new_freq = max(0.02, min(0.98, r["pred_v2"] + delta))
        err = new_freq - r["gto"]
        sse += r["n"] * err * err
        total_n += r["n"]
    return (sse / total_n) ** 0.5


def main():
    records = gather_all_records()
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    mtt = [r for r in records if r["ctx"] == "mtt_25bb"]
    print(f"records: cash={len(cash)}, mtt={len(mtt)}")

    print("\n" + "=" * 76)
    print("[Approach 1] Context 別に override offset を WLS fit")
    print("=" * 76)
    for ctx in ["cash_100bb", "mtt_25bb"]:
        X, y, w, recs = build_features(records, ctx)
        theta = wls_solve(X, y, w)
        w_before = (sum(r["n"] * (r["pred_v2"] - r["gto"])**2 for r in recs) /
                    sum(r["n"] for r in recs)) ** 0.5
        w_after = wrmse_with_offsets(recs, theta, None)
        print(f"\n{ctx}:")
        print(f"  base (constant)  = {theta[0]:+.3f}")
        print(f"  O1 nutted        = {theta[1]:+.3f}  ({sum(r['n'] for r in recs if r['hand'] in NUTTED_HANDS)} combos affected)")
        print(f"  O2 low_pair      = {theta[2]:+.3f}  ({sum(r['n'] for r in recs if r['hand'] == 'low_pair')} combos)")
        print(f"  O3 wide+polariz  = {theta[3]:+.3f}  ({sum(r['n'] for r in recs if r['scenario'] in WIDE_OPEN_POS and r['decision'].size == 116)} combos)")
        print(f"  O4 type-6        = {theta[4]:+.3f}  ({sum(r['n'] for r in recs if r['board_type'] == 6)} combos)")
        print(f"  O5 MID-False-air = {theta[5]:+.3f}  ({sum(r['n'] for r in recs if r['decision'].confidence == 'MID' and not r['decision'].direction and r['decision'].cbs <= 2)} combos)")
        print(f"  WRMSE: {w_before*100:.2f}% → {w_after*100:.2f}% (Δ {(w_after-w_before)*100:+.2f}pt)")

    print("\n" + "=" * 76)
    print("[Approach 2] Context 共通 (全 record で同じ override offset)")
    print("=" * 76)
    X, y, w, recs = build_features(records, None)
    theta = wls_solve(X, y, w)
    w_after = wrmse_with_offsets(recs, theta, None)
    w_before = (sum(r["n"] * (r["pred_v2"] - r["gto"])**2 for r in recs) /
                sum(r["n"] for r in recs)) ** 0.5
    print(f"\n  base (constant)  = {theta[0]:+.3f}")
    print(f"  O1 nutted        = {theta[1]:+.3f}")
    print(f"  O2 low_pair      = {theta[2]:+.3f}")
    print(f"  O3 wide+polariz  = {theta[3]:+.3f}")
    print(f"  O4 type-6        = {theta[4]:+.3f}")
    print(f"  O5 MID-False-air = {theta[5]:+.3f}")
    print(f"  全体 WRMSE: {w_before*100:.2f}% → {w_after*100:.2f}% (Δ {(w_after-w_before)*100:+.2f}pt)")

    # 個別 ctx の WRMSE 内訳
    cash_w_before = (sum(r["n"] * (r["pred_v2"] - r["gto"])**2 for r in cash) /
                     sum(r["n"] for r in cash)) ** 0.5
    cash_w_after = wrmse_with_offsets(cash, theta, None)
    mtt_w_before = (sum(r["n"] * (r["pred_v2"] - r["gto"])**2 for r in mtt) /
                    sum(r["n"] for r in mtt)) ** 0.5
    mtt_w_after = wrmse_with_offsets(mtt, theta, None)
    print(f"  cash WRMSE: {cash_w_before*100:.2f}% → {cash_w_after*100:.2f}% (Δ {(cash_w_after-cash_w_before)*100:+.2f}pt)")
    print(f"  mtt  WRMSE: {mtt_w_before*100:.2f}% → {mtt_w_after*100:.2f}% (Δ {(mtt_w_after-mtt_w_before)*100:+.2f}pt)")

    # Ablation: 各 override を 1 つずつ落とす
    print("\n" + "=" * 76)
    print("[Ablation] Approach 1 で override を 1 つずつ落とした WRMSE")
    print("=" * 76)
    override_names = ["constant", "O1 nutted", "O2 low_pair", "O3 wide_polarize",
                      "O4 type-6", "O5 MID-False-air"]
    for ctx in ["cash_100bb", "mtt_25bb"]:
        X, y, w, recs = build_features(records, ctx)
        full_theta = wls_solve(X, y, w)
        full_wrmse = wrmse_with_offsets(recs, full_theta, None)
        print(f"\n{ctx} (full WRMSE = {full_wrmse*100:.2f}%):")
        for i in range(1, 6):  # 1-5 はそれぞれの override
            dropped_theta = full_theta.copy()
            dropped_theta[i] = 0.0
            dropped_wrmse = wrmse_with_offsets(recs, dropped_theta, None)
            cost = (dropped_wrmse - full_wrmse) * 100
            print(f"  drop {override_names[i]:>20s}: {dropped_wrmse*100:.2f}% "
                  f"(cost {cost:+.3f}pt {'✓' if cost > 0.05 else ' '})")


if __name__ == "__main__":
    main()
