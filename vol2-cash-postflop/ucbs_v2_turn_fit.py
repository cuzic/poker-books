#!/usr/bin/env python3
"""UCBS-v2 turn cbet 2nd barrel fit (mtt 25bb BTN)"""
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


def load():
    fp = "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl"
    out = []
    with open(fp) as f:
        for line in f:
            entry = json.loads(line)
            # ターン card 込みの 4-card board → 3-card flop で UCBS-v2 評価
            flop = entry["flop"]
            try:
                bt_str = classify_board_type7(flop)
                feats = extract_board_features(flop)
            except Exception:
                continue
            bt = parse_board_type(bt_str)
            for h, vals in entry.get("hand_agg", {}).items():
                if h not in HP_TABLE or vals.get("total", 0) < 3:
                    continue
                out.append({
                    "scenario": "BTN", "flop": flop, "turn": entry["turn"],
                    "bt_str": bt_str, "bt": bt,
                    "hand": h, "n": vals["total"],
                    "gto": vals["bet_pct"] / 100.0, "feats": feats,
                    "spot_id": entry["spot_id"],
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
    records = load()
    print(f"turn records: {len(records)} (combos {sum(r['n'] for r in records)})")

    # ─── Baseline: mtt_25bb 流用 ───
    print("\n[Baseline] mtt_25bb パラメータ流用")
    base_w = wrmse(records,
        alpha=+0.06, beta=+0.31, off_slowplay=-0.28,
        off_trash=-0.23, off_premium=+0.15)
    print(f"  WRMSE = {base_w*100:.2f}%")

    # ─── WLS fit: turn 専用 ───
    print("\n[WLS fit] turn cbet (mtt_25bb BTN) 専用")
    X, y, w = build_X(records)
    theta = solve(X, y, w)
    fit_w = wrmse(records,
        alpha=theta[0], beta=theta[1],
        off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4])
    print(f"  α        = {theta[0]:+.3f}")
    print(f"  β        = {theta[1]:+.3f}  (CBS ≥ 7)")
    print(f"  slowplay = {theta[2]:+.3f}")
    print(f"  trash    = {theta[3]:+.3f}")
    print(f"  premium  = {theta[4]:+.3f}")
    print(f"  WRMSE    = {fit_w*100:.2f}%")
    print(f"  改善: {(base_w - fit_w)*100:+.2f}pt")

    # ─── Spot 別 WRMSE ───
    print("\n[Spot 別 (flop+turn)]")
    by_spot = defaultdict(list)
    for r in records:
        by_spot[r["spot_id"]].append(r)
    for spot_id, recs in sorted(by_spot.items()):
        if not recs: continue
        wf = wrmse(recs,
            alpha=theta[0], beta=theta[1],
            off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4])
        n = sum(r["n"] for r in recs)
        print(f"  {spot_id:14s} (flop {recs[0]['flop']} + {recs[0]['turn']}): "
              f"WRMSE={wf*100:.2f}%, n={len(recs)}, combos={int(n)}")

    # ─── Hand 別 bias ───
    print("\n[Hand 別 bias]")
    by_hand = defaultdict(lambda: [0.0, 0.0])
    for r in records:
        err = predict(r,
            alpha=theta[0], beta=theta[1],
            off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4]) - r["gto"]
        by_hand[r["hand"]][0] += r["n"] * err
        by_hand[r["hand"]][1] += r["n"]
    for h, (esum, n) in sorted(by_hand.items(), key=lambda x: -x[1][1]):
        if n > 0:
            m = " ★" if abs(esum/n) > 0.10 else ""
            print(f"  {h:14s} combos={int(n):>5d}  bias={esum/n*100:+6.1f}%{m}")


if __name__ == "__main__":
    main()
