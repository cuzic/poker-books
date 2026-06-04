#!/usr/bin/env python3
"""
A 階層型に「もう 1 軸」を追加した 3 候補を fit + 比較

ベース: A = base[ctx5][band] + α[ctx13] + β[ctx13]·I(CBS≥7) + cat_offset
        (54 params, WRMSE 18.88%)

新軸:
  C1 Confidence = HP - DP の符号 (made / balanced / draw)
     baseline=balanced。γ_made[ctx13], γ_draw[ctx13] (26 params)
  C2 Range advantage = scenario group (late / SB)
     baseline=BTN。δ_late[ctx13], δ_SB[ctx13] (26 params)
  C3 Board family = dry_high / paired / dynamic / low_dry
     baseline=dry_high。ε[family][ctx_group] (9 params, 軽量版)
  ALL: C1+C2+C3 全乗せ
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ucbs_candidates_fit import CTX13, CTX13_TO_5, load_all, evaluate


# ─── Board family 分類 ────────────────────────────────────
RANK_TO_NUM = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
                "T":10,"J":11,"Q":12,"K":13,"A":14}

def parse_cards(board: str):
    """'AsKd7c' → [(14,'s'),(13,'d'),(7,'c')]、Turn 4枚も処理"""
    cards = []
    i = 0
    while i < len(board) - 1:
        r, s = board[i], board[i+1]
        if r in RANK_TO_NUM:
            cards.append((RANK_TO_NUM[r], s))
        i += 2
    return cards[:3]  # flop の 3 枚のみ

def board_family(board: str) -> str:
    cards = parse_cards(board)
    if len(cards) < 3:
        return "dry_high"
    ranks = sorted([c[0] for c in cards], reverse=True)
    suits = [c[1] for c in cards]
    is_paired = len(set(ranks)) < 3
    is_monotone = len(set(suits)) == 1
    is_two_tone = len(set(suits)) == 2
    high = ranks[0]
    # gap = 最大ランク - 最小ランク
    gap = ranks[0] - ranks[2]
    is_connected = gap <= 4
    if is_paired:
        return "paired"
    if is_monotone or (is_connected and is_two_tone):
        return "dynamic"
    if high >= 11:  # J or higher
        return "dry_high"
    return "low_dry"


def confidence(hp: int, dp: int) -> str:
    diff = hp - dp
    if diff >= 2: return "made"
    if diff <= -2: return "draw"
    return "balanced"


def ctx_group(ctx: str) -> str:
    if ctx in ("cash_100bb", "cash_100bb_turn_btn"):
        return "cash"
    if ctx in ("mtt_25bb", "mtt_50bb", "mtt_100bb", "mtt_200bb",
                "mtt_25bb_turn_btn", "mtt_50bb_turn_btn", "mtt_100bb_turn_btn"):
        return "mtt_srp"
    return "3bp"


def scen_group(scen: str) -> str:
    if scen == "SB": return "SB"
    if scen in ("CO", "HJ", "UTG"): return "late"
    return "BTN"


# ─── 共通: A 階層型 + 任意の追加軸 ───────────────────────
class AxisModel:
    """A 階層型 + 任意の追加軸を WLS で同時 fit"""

    def __init__(self, axes: list[str]):
        """axes: ['C1', 'C2', 'C3'] のサブセット"""
        self.axes = axes

    def fit(self, records):
        # Stage 1: Vol2 base (combos 加重平均)
        base_agg = defaultdict(lambda: [0.0, 0.0])
        for r in records:
            ctx5 = CTX13_TO_5[r["ctx"]]
            base_agg[(ctx5, r["band"])][0] += r["n"] * r["gto"]
            base_agg[(ctx5, r["band"])][1] += r["n"]
        self.base = {(c, b): v[0]/v[1] for (c, b), v in base_agg.items() if v[1] > 0}

        # records に派生 field を付与
        for r in records:
            r["conf"] = confidence(r["hp"], r["dp"])
            r["scen_g"] = scen_group(r["scenario"])
            r["board_fam"] = board_family(r["board"])
            r["ctx_g"] = ctx_group(r["ctx"])

        # Stage 2: 全 layer を WLS で同時 fit
        cat_keys = ["slowplay", "trash", "premium"]

        # parameter layout
        slots = []  # (key, name) のリスト
        # base layer (α, β)
        for c in CTX13:
            slots.append(("alpha", c))
        for c in CTX13:
            slots.append(("beta", c))
        for c in cat_keys:
            slots.append(("cat", c))

        if "C1" in self.axes:
            # C1: γ_made[ctx13], γ_draw[ctx13]
            for c in CTX13:
                slots.append(("c1_made", c))
            for c in CTX13:
                slots.append(("c1_draw", c))
        if "C2" in self.axes:
            # C2: δ_late[ctx13], δ_SB[ctx13]
            for c in CTX13:
                slots.append(("c2_late", c))
            for c in CTX13:
                slots.append(("c2_SB", c))
        if "C3" in self.axes:
            # C3: ε[family][ctx_group] (dry_high baseline)
            for fam in ("paired", "dynamic", "low_dry"):
                for cg in ("cash", "mtt_srp", "3bp"):
                    slots.append(("c3", (fam, cg)))

        idx = {s: i for i, s in enumerate(slots)}
        n_params = len(slots)

        X = np.zeros((len(records), n_params))
        y = np.zeros(len(records))
        w = np.zeros(len(records))

        for i, r in enumerate(records):
            ctx5 = CTX13_TO_5[r["ctx"]]
            b = self.base.get((ctx5, r["band"]), 0.5)
            X[i, idx[("alpha", r["ctx"])]] = 1.0
            if r["cbs"] >= 7:
                X[i, idx[("beta", r["ctx"])]] = 1.0
            if r["cat"] in cat_keys:
                X[i, idx[("cat", r["cat"])]] = 1.0
            if "C1" in self.axes:
                if r["conf"] == "made":
                    X[i, idx[("c1_made", r["ctx"])]] = 1.0
                elif r["conf"] == "draw":
                    X[i, idx[("c1_draw", r["ctx"])]] = 1.0
            if "C2" in self.axes:
                if r["scen_g"] == "late":
                    X[i, idx[("c2_late", r["ctx"])]] = 1.0
                elif r["scen_g"] == "SB":
                    X[i, idx[("c2_SB", r["ctx"])]] = 1.0
            if "C3" in self.axes:
                fam = r["board_fam"]
                if fam in ("paired", "dynamic", "low_dry"):
                    X[i, idx[("c3", (fam, r["ctx_g"]))]] = 1.0
            y[i] = r["gto"] - b
            w[i] = r["n"]

        # Ridge regularization for stability
        sqrtw = np.sqrt(w)
        Xw = X * sqrtw[:, None]
        yw = y * sqrtw
        reg = 0.001 * np.eye(n_params)
        theta = np.linalg.solve(Xw.T @ Xw + reg, Xw.T @ yw)

        self.theta = theta
        self.idx = idx
        self.cat_keys = cat_keys
        self.n_p = len(self.base) + n_params

    def predict(self, r):
        ctx5 = CTX13_TO_5[r["ctx"]]
        b = self.base.get((ctx5, r["band"]), 0.5)
        v = b
        v += self.theta[self.idx[("alpha", r["ctx"])]]
        if r["cbs"] >= 7:
            v += self.theta[self.idx[("beta", r["ctx"])]]
        if r["cat"] in self.cat_keys:
            v += self.theta[self.idx[("cat", r["cat"])]]
        if "C1" in self.axes:
            conf = confidence(r["hp"], r["dp"])
            if conf == "made":
                v += self.theta[self.idx[("c1_made", r["ctx"])]]
            elif conf == "draw":
                v += self.theta[self.idx[("c1_draw", r["ctx"])]]
        if "C2" in self.axes:
            sg = scen_group(r["scenario"])
            if sg == "late":
                v += self.theta[self.idx[("c2_late", r["ctx"])]]
            elif sg == "SB":
                v += self.theta[self.idx[("c2_SB", r["ctx"])]]
        if "C3" in self.axes:
            fam = board_family(r["board"])
            cg = ctx_group(r["ctx"])
            if fam in ("paired", "dynamic", "low_dry"):
                v += self.theta[self.idx[("c3", (fam, cg))]]
        return max(0.02, min(0.98, v))

    def n_params(self):
        return self.n_p

    def dump_axis_summary(self):
        out = {}
        for axis in self.axes:
            entries = []
            for slot, i in self.idx.items():
                if slot[0].startswith(("c1_", "c2_", "c3")) and slot[0].startswith(
                        f"c{axis[1]}"):
                    entries.append((slot, self.theta[i]))
            out[axis] = entries
        return out


def main():
    print("Loading data...")
    records = load_all()
    print(f"Loaded {len(records)} records, {sum(r['n'] for r in records):.0f} combos")

    cfgs = [
        ([], "A 階層型 (ベース)"),
        (["C1"], "A + C1 (Confidence)"),
        (["C2"], "A + C2 (Range adv = scenario)"),
        (["C3"], "A + C3 (Board family)"),
        (["C1", "C2"], "A + C1 + C2"),
        (["C1", "C3"], "A + C1 + C3"),
        (["C2", "C3"], "A + C2 + C3"),
        (["C1", "C2", "C3"], "A + 全軸 (C1+C2+C3)"),
    ]
    for axes, name in cfgs:
        m = AxisModel(axes)
        m.fit(records)
        evaluate(m, records, name)


if __name__ == "__main__":
    main()
