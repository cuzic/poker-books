#!/usr/bin/env python3
"""UCBS-v2 mtt_3bp_ip context fit (低 SPR 3-bet pot IP cbet)

データ: draw_study_3BP20.jsonl (BTN cold-call vs BB 3bet → BTN IP cbet 想定)
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
    calc_confidence, apply_confidence_exception, is_ax_dry_or_paired,
)
from ucbs_v2_simplify import BASE_FREQ_SIMPLE
from calc import classify_board_type7


def load():
    fp = "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_3BP20.jsonl"
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
                    "scenario": "BTN",  # BTN IP cbet
                    "board": board, "bt_str": bt_str, "bt": bt,
                    "hand": h, "n": vals["total"],
                    "gto": vals["bet_pct"] / 100.0, "feats": feats,
                })
    return out


def predict(r, alpha=0, beta=0, off_slowplay=0, off_trash=0, off_premium=0,
            pos_lifts=None, ax_lift=0, T=5):
    if pos_lifts is None:
        pos_lifts = {}
    hp = HP_TABLE[r["hand"]]
    cbs = hp
    conf = calc_confidence(cbs, T, r["bt"])
    conf = apply_confidence_exception(conf, r["bt"])
    direction = (cbs >= T)
    base = BASE_FREQ_SIMPLE[(conf, direction)]
    cat = HAND_CATEGORY.get(r["hand"], "default")
    offset = {"slowplay": off_slowplay, "trash": off_trash, "premium": off_premium}.get(cat, 0.0)
    beta_term = beta if cbs >= 7 else 0.0
    pos_lift = pos_lifts.get(r["scenario"], 0.0)
    ax = ax_lift if (r["scenario"] in ("BTN", "CO") and is_ax_dry_or_paired(r["feats"])) else 0.0
    return max(0.02, min(0.98, base + alpha + beta_term + offset + pos_lift + ax))


def build_X(records):
    n = len(records)
    # 3BP は単一 scenario なので position 軸不要 (or BTN only)
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
        base = BASE_FREQ_SIMPLE[(conf, direction)]
        y[i] = r["gto"] - base
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
    records = load()
    print(f"3BP IP records: {len(records)} (combos {sum(r['n'] for r in records)})")

    print("\n[Baseline] mtt_25bb / mtt_50bb を流用")
    base_25 = wrmse(records,
        alpha=+0.06, beta=+0.31, off_slowplay=-0.28,
        off_trash=-0.23, off_premium=+0.15,
        pos_lifts={"BTN": 0}, ax_lift=0)
    base_50 = wrmse(records,
        alpha=-0.04, beta=+0.19, off_slowplay=-0.12,
        off_trash=-0.35, off_premium=+0.20,
        pos_lifts={"BTN": 0}, ax_lift=+0.11)
    print(f"  mtt_25bb 流用: WRMSE = {base_25*100:.2f}%")
    print(f"  mtt_50bb 流用: WRMSE = {base_50*100:.2f}%")

    print("\n[WLS fit] mtt_3bp_ip 専用")
    X, y, w = build_X(records)
    theta = solve(X, y, w)
    fit_w = wrmse(records,
        alpha=theta[0], beta=theta[1],
        off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4],
        pos_lifts={"BTN": 0}, ax_lift=0)
    print(f"  α        = {theta[0]:+.3f}")
    print(f"  β        = {theta[1]:+.3f}  (CBS ≥ 7)")
    print(f"  slowplay = {theta[2]:+.3f}")
    print(f"  trash    = {theta[3]:+.3f}")
    print(f"  premium  = {theta[4]:+.3f}")
    print(f"  WRMSE    = {fit_w*100:.2f}%")

    print("\n[Hand 別 bias]")
    by_hand = defaultdict(lambda: [0.0, 0.0])
    for r in records:
        err = predict(r,
            alpha=theta[0], beta=theta[1],
            off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4],
            pos_lifts={"BTN": 0}, ax_lift=0) - r["gto"]
        by_hand[r["hand"]][0] += r["n"] * err
        by_hand[r["hand"]][1] += r["n"]
    for h, (esum, n) in sorted(by_hand.items(), key=lambda x: -x[1][1]):
        if n > 0:
            mark = " ★" if abs(esum/n) > 0.10 else ""
            print(f"  {h:14s} combos={int(n):>5d}  bias={esum/n*100:+6.1f}%{mark}")


if __name__ == "__main__":
    main()
