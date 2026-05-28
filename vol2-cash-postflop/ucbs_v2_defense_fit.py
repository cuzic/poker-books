#!/usr/bin/env python3
"""UCBS-v2 BB defense fit (continue freq = 1 - fold freq)

予測対象は cbet ではなく defense の continue freq (call + raise)。
UCBS-v2 構造を流用、target を continue freq に置換。
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2 import (
    HP_TABLE, HAND_CATEGORY,
    extract_board_features, parse_board_type,
    calc_confidence, apply_confidence_exception,
)
from ucbs_v2_simplify import BASE_FREQ_SIMPLE
from calc import classify_board_type7


def load(fp):
    out = []
    with open(fp) as f:
        for line in f:
            entry = json.loads(line)
            board = entry["board"]
            try:
                bt_str = classify_board_type7(board)
                feats = extract_board_features(board)
            except Exception:
                continue
            bt = parse_board_type(bt_str)
            for h, vals in entry.get("hand_agg", {}).items():
                if h not in HP_TABLE or vals.get("total", 0) < 3:
                    continue
                out.append({
                    "scenario": "BTN",  # BB defending vs BTN cbet
                    "board": board, "bt_str": bt_str, "bt": bt,
                    "hand": h, "n": vals["total"],
                    "gto": vals["cont_pct"] / 100.0,  # continue freq
                    "feats": feats,
                })
    return out


def predict(r, alpha, beta, off_slowplay, off_trash, off_premium, T=5):
    hp = HP_TABLE[r["hand"]]
    cbs = hp
    conf = calc_confidence(cbs, T, r["bt"])
    conf = apply_confidence_exception(conf, r["bt"])
    direction = (cbs >= T)
    base = BASE_FREQ_SIMPLE[(conf, direction)]
    cat = HAND_CATEGORY.get(r["hand"], "default")
    offset = {"slowplay": off_slowplay, "trash": off_trash, "premium": off_premium}.get(cat, 0.0)
    beta_term = beta if cbs >= 7 else 0.0
    return max(0.02, min(0.98, base + alpha + beta_term + offset))


def build_X(records):
    n = len(records)
    X = np.zeros((n, 5))
    y = np.zeros(n)
    w = np.zeros(n)
    for i, r in enumerate(records):
        hp = HP_TABLE[r["hand"]]
        cbs = hp
        beta_ind = 1.0 if cbs >= 7 else 0.0
        cat = HAND_CATEGORY.get(r["hand"], "default")
        X[i] = [1.0, beta_ind,
                1.0 if cat == "slowplay" else 0.0,
                1.0 if cat == "trash" else 0.0,
                1.0 if cat == "premium" else 0.0]
        conf = calc_confidence(cbs, 5, r["bt"])
        conf = apply_confidence_exception(conf, r["bt"])
        direction = (cbs >= 5)
        y[i] = r["gto"] - BASE_FREQ_SIMPLE[(conf, direction)]
        w[i] = r["n"]
    return X, y, w


def solve(X, y, w):
    valid = [j for j in range(X.shape[1]) if np.any(X[:, j] != 0)]
    Xv = X[:, valid]
    theta_v, *_ = np.linalg.lstsq(Xv * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)
    theta = np.zeros(X.shape[1])
    for k, j in enumerate(valid):
        theta[j] = theta_v[k]
    return theta


def wrmse(records, **kw):
    sse, n = 0.0, 0.0
    for r in records:
        err = predict(r, **kw) - r["gto"]
        sse += r["n"] * err * err
        n += r["n"]
    return (sse / n) ** 0.5 if n else 0.0


def main():
    fp = "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_DEF_MTT25_BB.jsonl"
    records = load(fp)
    print(f"BB defense records: {len(records)} (combos {sum(r['n'] for r in records)})")

    X, y, w = build_X(records)
    theta = solve(X, y, w)
    fit_w = wrmse(records,
        alpha=theta[0], beta=theta[1],
        off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4])
    print(f"\n[WLS fit] BB defense (continue freq)")
    print(f"  α        = {theta[0]:+.3f}")
    print(f"  β        = {theta[1]:+.3f}  (CBS ≥ 7)")
    print(f"  slowplay = {theta[2]:+.3f}")
    print(f"  trash    = {theta[3]:+.3f}")
    print(f"  premium  = {theta[4]:+.3f}")
    print(f"  WRMSE    = {fit_w*100:.2f}%")

    # GTO continue 平均
    avg_cont = sum(r["n"] * r["gto"] for r in records) / sum(r["n"] for r in records)
    print(f"\n  GTO continue 平均: {avg_cont*100:.2f}% (= 1 - fold rate)")

    print("\n[Hand 別 bias]")
    by_hand = defaultdict(lambda: [0.0, 0.0, 0.0])
    for r in records:
        pred = predict(r,
            alpha=theta[0], beta=theta[1],
            off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4])
        err = pred - r["gto"]
        by_hand[r["hand"]][0] += r["n"] * err
        by_hand[r["hand"]][1] += r["n"]
        by_hand[r["hand"]][2] += r["n"] * r["gto"]
    for h, (esum, n, gsum) in sorted(by_hand.items(), key=lambda x: -x[1][1]):
        if n > 0:
            m = " ★" if abs(esum/n) > 0.10 else ""
            print(f"  {h:14s} combos={int(n):>5d}  GTO_avg={gsum/n*100:5.1f}%  bias={esum/n*100:+6.1f}%{m}")


if __name__ == "__main__":
    main()
