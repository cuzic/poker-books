#!/usr/bin/env python3
"""
UCBS-v2 特殊役 offset を WLS (重み付き最小二乗) で確定

モデル:
  freq = base_freq[(conf, dir, size)] + α + β·I(CBS≥7)
                                       + off_slowplay·I(slowplay)
                                       + off_trash·I(trash)
                                       + off_premium·I(premium)

これは θ = (α, β, off_sp, off_tr, off_pr) の 5 次元線形回帰。
y_i = gto_i - base[k_i] とすれば、

  minimize Σ n_i (θ·x_i - y_i)²
       x_i = (1, I_β, I_sp, I_tr, I_pr)

WLS 解: θ = (X'WX)⁻¹ X'Wy
"""
from __future__ import annotations
from collections import defaultdict
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

from ucbs_v2_fit import load_records, fit_base_freq, SCOPE_CTX


HAND_CATEGORY = {
    "set":         "slowplay",
    "trips":       "slowplay",
    "two_pair":    "slowplay",
    "fullhouse":   "slowplay",
    "flush":       "slowplay",
    "straight":    "slowplay",
    "quads":       "slowplay",
    "low_pair":    "trash",
    "overpair":    "premium",
    "underpair":   "premium",
}


def get_base(r, base_freq):
    k = (r["conf"], r["dir"], r["size"])
    if k in base_freq:
        return base_freq[k]
    # fallback
    candidates = [v for kk, v in base_freq.items()
                  if kk[0] == r["conf"] and kk[2] == r["size"]]
    return sum(candidates) / len(candidates) if candidates else 0.30


def build_feature_matrix(records, base_freq):
    """各 record の (X, y, w) を構築"""
    n_records = len(records)
    X = np.zeros((n_records, 5))  # [const(α), β, slowplay, trash, premium]
    y = np.zeros(n_records)
    w = np.zeros(n_records)
    for i, r in enumerate(records):
        base = get_base(r, base_freq)
        beta_ind = 1.0 if r["cbs"] >= 7 else 0.0
        cat = HAND_CATEGORY.get(r["hand"], "default")
        X[i] = [
            1.0,
            beta_ind,
            1.0 if cat == "slowplay" else 0.0,
            1.0 if cat == "trash" else 0.0,
            1.0 if cat == "premium" else 0.0,
        ]
        y[i] = r["gto"] - base
        w[i] = r["n"]
    return X, y, w


def wls_fit(X, y, w):
    """WLS: minimize Σ w_i (X_i θ - y_i)² → θ = (X'WX)⁻¹ X'Wy"""
    W = np.diag(w)
    XtW = X.T @ W
    theta = np.linalg.solve(XtW @ X, XtW @ y)
    return theta


def predict(r, base_freq, theta_dict):
    base = get_base(r, base_freq)
    beta_ind = 1.0 if r["cbs"] >= 7 else 0.0
    cat = HAND_CATEGORY.get(r["hand"], "default")
    freq = (base + theta_dict["alpha"]
            + theta_dict["beta"] * beta_ind
            + theta_dict["slowplay"] * (cat == "slowplay")
            + theta_dict["trash"] * (cat == "trash")
            + theta_dict["premium"] * (cat == "premium"))
    return max(0.02, min(0.98, freq))


def wrmse(records, base_freq, theta_dict):
    sse, total_n = 0.0, 0.0
    for r in records:
        pred = predict(r, base_freq, theta_dict)
        err = pred - r["gto"]
        sse += r["n"] * err * err
        total_n += r["n"]
    return (sse / total_n) ** 0.5


def main():
    print("=" * 76)
    print("UCBS-v2 + 特殊役 offset (WLS fit)")
    print("=" * 76)
    records = load_records()
    cash = [r for r in records if r["ctx"] == "cash_100bb"]
    mtt = [r for r in records if r["ctx"] == "mtt_25bb"]
    base_freq = fit_base_freq(cash)
    print(f"records: cash={len(cash)}, mtt_25bb={len(mtt)}")

    # === Approach 1: per-context independent fit ===
    print("\n[Approach 1] context 別に α, β, offset×3 を WLS で確定")
    print("=" * 76)
    results = {}
    for ctx in SCOPE_CTX:
        recs = [r for r in records if r["ctx"] == ctx]
        X, y, w = build_feature_matrix(recs, base_freq)
        theta = wls_fit(X, y, w)
        td = {
            "alpha":    theta[0],
            "beta":     theta[1],
            "slowplay": theta[2],
            "trash":    theta[3],
            "premium":  theta[4],
        }
        wr = wrmse(recs, base_freq, td)
        results[ctx] = (td, wr)
        print(f"\n--- {ctx} (WRMSE = {wr*100:.2f}%) ---")
        print(f"  α        = {td['alpha']:+.3f}")
        print(f"  β        = {td['beta']:+.3f}   (CBS ≥ 7 で加算)")
        print(f"  slowplay = {td['slowplay']:+.3f}   (set, two_pair, flush, fullhouse, straight, trips, quads)")
        print(f"  trash    = {td['trash']:+.3f}   (low_pair)")
        print(f"  premium  = {td['premium']:+.3f}   (overpair, underpair)")

    # === Approach 2: shared trash/premium、slowplay は context 別 ===
    print("\n[Approach 2] slowplay のみ context 別、trash/premium は共通")
    print("=" * 76)
    # モデル: theta = (α_cash, β_cash, α_mtt, β_mtt,
    #                  sp_cash, sp_mtt, trash, premium)
    n_all = len(records)
    X = np.zeros((n_all, 8))
    y = np.zeros(n_all)
    w = np.zeros(n_all)
    for i, r in enumerate(records):
        base = get_base(r, base_freq)
        beta_ind = 1.0 if r["cbs"] >= 7 else 0.0
        cat = HAND_CATEGORY.get(r["hand"], "default")
        is_cash = 1.0 if r["ctx"] == "cash_100bb" else 0.0
        is_mtt = 1.0 if r["ctx"] == "mtt_25bb" else 0.0
        is_sp = 1.0 if cat == "slowplay" else 0.0
        X[i] = [
            is_cash,                    # α_cash
            is_cash * beta_ind,         # β_cash
            is_mtt,                     # α_mtt
            is_mtt * beta_ind,          # β_mtt
            is_cash * is_sp,            # slowplay_cash
            is_mtt * is_sp,             # slowplay_mtt
            1.0 if cat == "trash" else 0.0,
            1.0 if cat == "premium" else 0.0,
        ]
        y[i] = r["gto"] - base
        w[i] = r["n"]
    theta = wls_fit(X, y, w)
    print(f"\n  α_cash         = {theta[0]:+.3f}")
    print(f"  β_cash         = {theta[1]:+.3f}")
    print(f"  α_mtt          = {theta[2]:+.3f}")
    print(f"  β_mtt          = {theta[3]:+.3f}")
    print(f"  slowplay_cash  = {theta[4]:+.3f}")
    print(f"  slowplay_mtt   = {theta[5]:+.3f}")
    print(f"  trash          = {theta[6]:+.3f}   (共通)")
    print(f"  premium        = {theta[7]:+.3f}   (共通)")

    # 個別 WRMSE
    td_cash = {"alpha": theta[0], "beta": theta[1],
               "slowplay": theta[4], "trash": theta[6], "premium": theta[7]}
    td_mtt = {"alpha": theta[2], "beta": theta[3],
              "slowplay": theta[5], "trash": theta[6], "premium": theta[7]}
    cash_w = wrmse(cash, base_freq, td_cash)
    mtt_w = wrmse(mtt, base_freq, td_mtt)
    print(f"\n  cash WRMSE = {cash_w*100:.2f}%  (現状 21.43%, Approach1 {results['cash_100bb'][1]*100:.2f}%)")
    print(f"  mtt  WRMSE = {mtt_w*100:.2f}%  (現状 20.79%, Approach1 {results['mtt_25bb'][1]*100:.2f}%)")

    # === Hand 別 bias を出力 (Approach 2) ===
    print("\n[Hand 別 bias after Approach 2]")
    for ctx, td in [("cash_100bb", td_cash), ("mtt_25bb", td_mtt)]:
        print(f"\n--- {ctx} ---")
        recs = [r for r in records if r["ctx"] == ctx]
        by_hand = defaultdict(lambda: [0.0, 0.0])
        for r in recs:
            pred = predict(r, base_freq, td)
            err = pred - r["gto"]
            by_hand[r["hand"]][0] += r["n"] * err
            by_hand[r["hand"]][1] += r["n"]
        print(f"  {'hand':14s} {'category':>9s} {'bias':>8s}")
        for h in sorted(by_hand.keys()):
            esum, n = by_hand[h]
            cat = HAND_CATEGORY.get(h, "default")
            if n > 0:
                bias = esum / n * 100
                marker = " ★" if abs(bias) > 10 else ""
                print(f"  {h:14s} {cat:>9s} {bias:+6.1f}%{marker}")


if __name__ == "__main__":
    main()
