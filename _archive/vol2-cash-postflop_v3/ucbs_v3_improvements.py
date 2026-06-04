#!/usr/bin/env python3
"""
UCBS-v3 階層型の改善案 (B1 + B3 + B6) を実装して fit + 評価

ベース: 候補 A 階層型 (Vol2 base + α/β layer)

改善:
  B1: Position lift per (ctx_group, pos) — +12 params, +1 step
  B3: 二段 β (band 別: strong vs nut)    — +13 params, +0 step
  B6: 残差ピンポイント修正 (top-N 局所)   — +5-8 params, +0.5 step
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")
from ucbs_candidates_fit import (
    HP_TABLE, DP_TABLE, HAND_CATEGORY, CTX13, CTX13_TO_5, BANDS,
    cbs_band, load_all, evaluate,
)


# ─── B1 + B3 + B6 を含む改善モデル ────────────────────────
class CandidateA_Improved:
    """階層型 + B1 (pos_lift) + B3 (二段 β) + B6 (残差 fix)"""

    def fit(self, records):
        # ── Stage 1: Vol2 base (combos 加重平均) ──
        base_agg = defaultdict(lambda: [0.0, 0.0])
        for r in records:
            ctx5 = CTX13_TO_5[r["ctx"]]
            base_agg[(ctx5, r["band"])][0] += r["n"] * r["gto"]
            base_agg[(ctx5, r["band"])][1] += r["n"]
        self.base = {(c, b): v[0]/v[1] for (c, b), v in base_agg.items() if v[1] > 0}

        # ── Stage 2: 全 layer を線形 WLS で同時 fit ──
        cat_keys = ["slowplay", "trash", "premium"]
        # ctx_group for position (3 groups: cash, mtt_srp, 3bp+turn)
        ctx_group_keys = ["cash_group", "mtt_srp_group", "other_group"]
        def ctx_group(ctx):
            if ctx == "cash_100bb" or ctx == "cash_100bb_turn_btn":
                return "cash_group"
            if ctx in ("mtt_25bb", "mtt_50bb", "mtt_100bb", "mtt_200bb"):
                return "mtt_srp_group"
            return "other_group"
        pos_keys = ["SB", "wide"]   # BTN baseline

        # parameter layout
        n_alpha = len(CTX13)
        n_beta_s = len(CTX13)  # B3: strong band β
        n_beta_n = len(CTX13)  # B3: nut band β
        n_cat = len(cat_keys)
        n_pos = len(ctx_group_keys) * len(pos_keys)  # B1: pos_lift

        idx_alpha = {c: i for i, c in enumerate(CTX13)}
        idx_beta_s = {c: n_alpha + i for i, c in enumerate(CTX13)}
        idx_beta_n = {c: n_alpha + n_beta_s + i for i, c in enumerate(CTX13)}
        idx_cat = {c: n_alpha + n_beta_s + n_beta_n + i for i, c in enumerate(cat_keys)}
        pos_offset = n_alpha + n_beta_s + n_beta_n + n_cat
        idx_pos = {(g, p): pos_offset + gi*len(pos_keys) + pi
                   for gi, g in enumerate(ctx_group_keys)
                   for pi, p in enumerate(pos_keys)}

        n_params = pos_offset + n_pos
        X = np.zeros((len(records), n_params))
        y = np.zeros(len(records))
        w = np.zeros(len(records))

        for i, r in enumerate(records):
            ctx5 = CTX13_TO_5[r["ctx"]]
            b = self.base.get((ctx5, r["band"]), 0.5)
            # alpha
            X[i, idx_alpha[r["ctx"]]] = 1.0
            # B3: two-stage beta (strong / nut)
            if r["band"] == "strong":
                X[i, idx_beta_s[r["ctx"]]] = 1.0
            elif r["band"] == "nut":
                X[i, idx_beta_n[r["ctx"]]] = 1.0
            # cat offset
            if r["cat"] in idx_cat:
                X[i, idx_cat[r["cat"]]] = 1.0
            # B1: pos_lift
            g = ctx_group(r["ctx"])
            scen = r["scenario"]
            if scen == "SB":
                X[i, idx_pos[(g, "SB")]] = 1.0
            elif scen in ("CO", "HJ", "UTG"):
                X[i, idx_pos[(g, "wide")]] = 1.0
            y[i] = r["gto"] - b
            w[i] = r["n"]

        # Ridge 正則化 (lambda=0.001 弱め)
        sqrtw = np.sqrt(w)
        Xw = X * sqrtw[:, None]
        yw = y * sqrtw
        reg = 0.001 * np.eye(n_params)
        theta = np.linalg.solve(Xw.T @ Xw + reg, Xw.T @ yw)

        self.alpha = {c: theta[idx_alpha[c]] for c in CTX13}
        self.beta_s = {c: theta[idx_beta_s[c]] for c in CTX13}
        self.beta_n = {c: theta[idx_beta_n[c]] for c in CTX13}
        self.cat_offset = {"default": 0.0}
        for c in cat_keys:
            self.cat_offset[c] = theta[idx_cat[c]]
        self.pos_lift = {}
        for g in ctx_group_keys:
            for p in pos_keys:
                self.pos_lift[(g, p)] = theta[idx_pos[(g, p)]]
        self.ctx_group = ctx_group
        self.n_p1 = n_params

        # ── Stage 3: B6 残差 top-N 局所 fix ──
        # Stage 1+2 で fit した上で残差を確認、|残差| > 5% かつ combos > 1000 の cell に対して
        # ctx × band 別の追加 offset を計算
        residuals = defaultdict(lambda: [0.0, 0.0])
        for r in records:
            pred = self._predict_no_local(r)
            res = r["gto"] - pred
            residuals[(r["ctx"], r["band"])][0] += r["n"] * res
            residuals[(r["ctx"], r["band"])][1] += r["n"]
        # 残差絶対値で sort、top-N を抽出
        ranked = sorted(
            ((key, (s/n if n > 0 else 0), n) for key, (s, n) in residuals.items() if n >= 500),
            key=lambda x: -abs(x[1])
        )
        self.local_fix = {}
        n_local = 0
        for key, mean_res, n in ranked:
            if abs(mean_res) >= 0.05 and n_local < 8:  # top 8 のみ採用
                self.local_fix[key] = mean_res
                n_local += 1
        self.n_local = n_local

    def _predict_no_local(self, r):
        ctx5 = CTX13_TO_5[r["ctx"]]
        b = self.base.get((ctx5, r["band"]), 0.5)
        a = self.alpha.get(r["ctx"], 0.0)
        # B3: band-specific β
        if r["band"] == "strong":
            bt = self.beta_s.get(r["ctx"], 0.0)
        elif r["band"] == "nut":
            bt = self.beta_n.get(r["ctx"], 0.0)
        else:
            bt = 0.0
        co = self.cat_offset.get(r["cat"], 0.0)
        # B1: pos_lift
        g = self.ctx_group(r["ctx"])
        scen = r["scenario"]
        if scen == "SB":
            pl = self.pos_lift.get((g, "SB"), 0.0)
        elif scen in ("CO", "HJ", "UTG"):
            pl = self.pos_lift.get((g, "wide"), 0.0)
        else:
            pl = 0.0
        return max(0.02, min(0.98, b + a + bt + co + pl))

    def predict(self, r):
        # B6: 局所 fix を加算
        base_pred = self._predict_no_local(r)
        local = self.local_fix.get((r["ctx"], r["band"]), 0.0)
        return max(0.02, min(0.98, base_pred + local))

    def n_params(self):
        return len(self.base) + self.n_p1 + self.n_local


# ─── 既存 A (改善前) と並列比較用 ───────────────────────
class CandidateA_Original:
    def fit(self, records):
        base_agg = defaultdict(lambda: [0.0, 0.0])
        for r in records:
            ctx5 = CTX13_TO_5[r["ctx"]]
            base_agg[(ctx5, r["band"])][0] += r["n"] * r["gto"]
            base_agg[(ctx5, r["band"])][1] += r["n"]
        self.base = {(c, b): v[0]/v[1] for (c, b), v in base_agg.items() if v[1] > 0}

        cat_keys = ["slowplay", "trash", "premium"]
        n_params = len(CTX13)*2 + len(cat_keys)
        idx_a = {c: i for i, c in enumerate(CTX13)}
        idx_b = {c: len(CTX13) + i for i, c in enumerate(CTX13)}
        idx_c = {c: 2*len(CTX13) + i for i, c in enumerate(cat_keys)}
        X = np.zeros((len(records), n_params))
        y = np.zeros(len(records))
        w = np.zeros(len(records))
        for i, r in enumerate(records):
            ctx5 = CTX13_TO_5[r["ctx"]]
            b = self.base.get((ctx5, r["band"]), 0.5)
            X[i, idx_a[r["ctx"]]] = 1.0
            if r["cbs"] >= 7:
                X[i, idx_b[r["ctx"]]] = 1.0
            if r["cat"] in idx_c:
                X[i, idx_c[r["cat"]]] = 1.0
            y[i] = r["gto"] - b
            w[i] = r["n"]
        sw = np.sqrt(w)
        theta, *_ = np.linalg.lstsq(X*sw[:,None], y*sw, rcond=None)
        self.alpha = {c: theta[idx_a[c]] for c in CTX13}
        self.beta = {c: theta[idx_b[c]] for c in CTX13}
        self.cat_offset = {"default": 0.0}
        for c in cat_keys:
            self.cat_offset[c] = theta[idx_c[c]]
        self.n_p = len(self.base) + n_params

    def predict(self, r):
        ctx5 = CTX13_TO_5[r["ctx"]]
        b = self.base.get((ctx5, r["band"]), 0.5)
        a = self.alpha.get(r["ctx"], 0.0)
        bt = self.beta.get(r["ctx"], 0.0) if r["cbs"] >= 7 else 0.0
        co = self.cat_offset.get(r["cat"], 0.0)
        return max(0.02, min(0.98, b + a + bt + co))

    def n_params(self):
        return self.n_p


def main():
    print("Loading data...")
    records = load_all()
    print(f"Loaded {len(records)} records, {sum(r['n'] for r in records):.0f} combos")

    for cls, name in [(CandidateA_Original, "A (現状): base + α + β·I(CBS≥7) + cat"),
                       (CandidateA_Improved, "A' 改善: + B1(pos) + B3(二段β) + B6(局所fix)")]:
        m = cls()
        m.fit(records)
        evaluate(m, records, name)
        if hasattr(m, 'local_fix'):
            print(f"\n  B6 局所 fix ({m.n_local} 個):")
            for (ctx, band), v in sorted(m.local_fix.items(),
                                          key=lambda x: -abs(x[1])):
                print(f"    {ctx:>20s} × {band:>6s}: {v*100:>+5.1f}pt")


if __name__ == "__main__":
    main()
