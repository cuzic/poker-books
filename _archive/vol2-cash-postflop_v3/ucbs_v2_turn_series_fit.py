#!/usr/bin/env python3
"""UCBS-v2 turn cbet series fit (4 contexts)"""
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
    files = {
        "turn_mtt25_btn": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl",
        "turn_mtt50_btn": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT50_BTN.jsonl",
        "turn_mtt100_btn": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_MTT100_BTN.jsonl",
        "turn_cash100_btn": "/home/cuzic/poker-books/mtt-postflop/findings/draw_study_TURN_CASH100_BTN.jsonl",
    }
    print(f"{'profile':22s}  {'records':>7s}  {'combos':>7s}  "
          f"{'α':>6s}  {'β':>6s}  {'slowp':>6s}  {'trash':>6s}  {'prem':>6s}  "
          f"{'WRMSE':>7s}")
    print("-" * 110)
    for label, fp in files.items():
        try:
            recs = load(fp)
        except FileNotFoundError:
            continue
        if not recs:
            continue
        X, y, w = build_X(recs)
        theta = solve(X, y, w)
        wf = wrmse(recs,
            alpha=theta[0], beta=theta[1],
            off_slowplay=theta[2], off_trash=theta[3], off_premium=theta[4])
        total_n = sum(r["n"] for r in recs)
        print(f"{label:22s}  {len(recs):>7d}  {int(total_n):>7d}  "
              f"{theta[0]:>+5.2f}  {theta[1]:>+5.2f}  "
              f"{theta[2]:>+5.2f}  {theta[3]:>+5.2f}  {theta[4]:>+5.2f}  "
              f"{wf*100:>6.2f}%")


if __name__ == "__main__":
    main()
