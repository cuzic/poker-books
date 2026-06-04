#!/usr/bin/env python3
"""
Vol2/Vol3 統一構造候補の fit + 評価

Opus ブレストの推奨 3 案を実装し WLS で fit + WRMSE 測定。

候補:
  I) 差分表 δ: Vol2 25 cell base + Vol3 13×5 補正 (Δ)
  H) HP×ctx 直接: 13 ctx × 6 HP base + DP bonus + cat offset + pos lift
  A) 階層型: Vol2 25 cell base + α/β·I(CBS≥7) per 13 ctx + offset
"""
from __future__ import annotations
import json, sys
from pathlib import Path
from collections import defaultdict
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/home/cuzic/poker-books/scripts")

from ucbs_v2 import HP_TABLE, DP_TABLE, HAND_CATEGORY, extract_board_features
from calc import classify_board_type7


# Vol2 contexts (5 categories)
CTX5 = ["cash", "mtt_short", "mtt_deep", "3bp", "turn"]
# Vol3 contexts (13 categories)
CTX13 = ["cash_100bb",
         "mtt_25bb", "mtt_50bb", "mtt_100bb", "mtt_200bb",
         "mtt_3bp_20bb", "mtt_3bp_25bb", "mtt_3bp_50bb", "mtt_3bp_100bb",
         "mtt_25bb_turn_btn", "mtt_50bb_turn_btn",
         "mtt_100bb_turn_btn", "cash_100bb_turn_btn"]

# 13 ctx → 5 ctx グループ map (Vol2 → Vol3 階層)
CTX13_TO_5 = {
    "cash_100bb": "cash",
    "mtt_25bb": "mtt_short", "mtt_50bb": "mtt_short",
    "mtt_100bb": "mtt_deep", "mtt_200bb": "mtt_deep",
    "mtt_3bp_20bb": "3bp", "mtt_3bp_25bb": "3bp",
    "mtt_3bp_50bb": "3bp", "mtt_3bp_100bb": "3bp",
    "mtt_25bb_turn_btn": "turn", "mtt_50bb_turn_btn": "turn",
    "mtt_100bb_turn_btn": "turn", "cash_100bb_turn_btn": "turn",
}

BANDS = ["air", "weak", "mid", "strong", "nut"]


def cbs_band(cbs: int) -> str:
    if cbs <= 2: return "air"
    if cbs <= 4: return "weak"
    if cbs <= 6: return "mid"
    if cbs <= 8: return "strong"
    return "nut"


# ─── 全 records ロード ─────────────────────────────────────
def load_all():
    files = {
        "cash_100bb":  ("/home/cuzic/poker-books/vol2-cash-postflop/findings/cash_5cat_gto.json", "cash"),
        "mtt_25bb":    ("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_SRP25.jsonl", "mtt"),
        "mtt_50bb":    ("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT50BB.jsonl", "mtt"),
        "mtt_100bb":   ("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT100BB.jsonl", "mtt"),
        "mtt_200bb":   ("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_MTT200BB.jsonl", "mtt"),
        "mtt_3bp_20bb":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP20.jsonl", "mtt"),
        "mtt_3bp_25bb":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP25.jsonl", "mtt"),
        "mtt_3bp_50bb":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP50.jsonl", "mtt"),
        "mtt_3bp_100bb":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_3BP100.jsonl", "mtt"),
        "mtt_25bb_turn_btn":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_MTT25_BTN.jsonl", "turn"),
        "mtt_50bb_turn_btn":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_MTT50_BTN.jsonl", "turn"),
        "mtt_100bb_turn_btn":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_MTT100_BTN.jsonl", "turn"),
        "cash_100bb_turn_btn":("/home/cuzic/poker-books/vol3-mtt-postflop/findings/draw_study_TURN_CASH100_BTN.jsonl", "turn"),
    }
    all_records = []
    for ctx, (fp, fmt) in files.items():
        if not Path(fp).exists():
            continue
        if fmt == "cash":
            scen_map = {"BTN_BB": "BTN", "CO_BB": "CO", "HJ_BB": "HJ",
                        "UTG_BB": "UTG", "SB_BB": "SB", "BTN_SB": "BTN"}
            with open(fp) as f:
                data = json.load(f)
            for pos, boards in data.items():
                scen = scen_map.get(pos, "BTN")
                for board_key, info in boards.items():
                    board = info.get("board", board_key)
                    for h, vals in info.get("hand_cats", {}).items():
                        if h not in HP_TABLE: continue
                        n = vals.get("combos", 0)
                        if n < 5: continue
                        all_records.append({
                            "ctx": ctx, "hand": h, "draw": "no_draw", "n": n,
                            "gto": vals["bet_pct"]/100.0,
                            "board": board, "scenario": scen,
                        })
        else:
            with open(fp) as f:
                for line in f:
                    entry = json.loads(line)
                    board = entry.get("board", entry.get("flop", ""))
                    if fmt == "turn":
                        scen_pos = "BTN"
                    else:
                        scn_raw = entry.get("scenario", "BTN")
                        if isinstance(scn_raw, str):
                            if "_SB_cc" in scn_raw: scen_pos = "BTN"
                            elif "_SB" in scn_raw or scn_raw.endswith("SB"): scen_pos = "SB"
                            elif "_CO" in scn_raw or scn_raw == "CO_BB": scen_pos = "CO"
                            else: scen_pos = "BTN"
                        else:
                            scen_pos = "BTN"
                    for h, vals in entry.get("hand_agg", {}).items():
                        if h not in HP_TABLE: continue
                        n = vals.get("total", 0)
                        if n < 3: continue
                        all_records.append({
                            "ctx": ctx, "hand": h, "draw": "no_draw", "n": n,
                            "gto": vals["bet_pct"]/100.0,
                            "board": board, "scenario": scen_pos,
                        })
    # CBS, band などを computed fields に
    for r in all_records:
        hp = HP_TABLE.get(r["hand"], 0)
        dp = DP_TABLE.get(r["draw"], 0)
        r["hp"] = hp
        r["dp"] = dp
        r["cbs"] = hp + dp
        r["band"] = cbs_band(r["cbs"])
        r["cat"] = HAND_CATEGORY.get(r["hand"], "default")
    return all_records


# ─── 候補 I: 差分表 δ ────────────────────────────────────
class CandidateI:
    """Vol2 base[ctx5][band] + Vol3 補正 δ[ctx13][band]
    parameters: 25 (Vol2 base) + 13×5 (δ) = 90 params
    暗算: Vol2 = 4 step, Vol3 = 5 step (Vol2 結果に δ を加算)
    """
    def fit(self, records):
        # Vol2 base: combos 加重平均 per (ctx5, band)
        base_agg = defaultdict(lambda: [0.0, 0.0])  # [sum_n_gto, sum_n]
        for r in records:
            ctx5 = CTX13_TO_5[r["ctx"]]
            base_agg[(ctx5, r["band"])][0] += r["n"] * r["gto"]
            base_agg[(ctx5, r["band"])][1] += r["n"]
        self.base = {(c, b): v[0]/v[1] for (c, b), v in base_agg.items() if v[1] > 0}

        # δ: 13 ctx 別の残差を combos 加重平均
        delta_agg = defaultdict(lambda: [0.0, 0.0])
        for r in records:
            ctx5 = CTX13_TO_5[r["ctx"]]
            b = self.base.get((ctx5, r["band"]), 0.5)
            res = r["gto"] - b
            delta_agg[(r["ctx"], r["band"])][0] += r["n"] * res
            delta_agg[(r["ctx"], r["band"])][1] += r["n"]
        self.delta = {(c, b): v[0]/v[1] for (c, b), v in delta_agg.items() if v[1] > 0}

    def predict(self, r):
        ctx5 = CTX13_TO_5[r["ctx"]]
        base = self.base.get((ctx5, r["band"]), 0.5)
        delta = self.delta.get((r["ctx"], r["band"]), 0.0)
        return max(0.02, min(0.98, base + delta))

    def n_params(self):
        return len(self.base) + len(self.delta)


# ─── 候補 H: HP×ctx 直接 ─────────────────────────────────
class CandidateH:
    """T[ctx][HP] + DP_bonus[DP] + cat_offset[cat] + pos_lift[pos]
    parameters: 13×6 + 4 + 3 + 2 = 87 params
    暗算: 4 step (HP/DP/cat/pos すべて整数加算)
    """
    def fit(self, records):
        # WLS で線形回帰
        # features: [I(ctx,hp) × 78] + [I(dp=1), I(dp=2), I(dp=3)] +
        #           [I(cat=slowplay), I(cat=trash), I(cat=premium)] +
        #           [I(SB), I(CO|HJ|UTG)]
        hp_levels = [2, 3, 5, 7, 8, 9]
        ctx_hp_keys = [(c, hp) for c in CTX13 for hp in hp_levels]
        n_ctx_hp = len(ctx_hp_keys)
        dp_keys = [1, 2, 3]
        cat_keys = ["slowplay", "trash", "premium"]
        pos_keys = ["SB", "wide"]
        n_params = n_ctx_hp + len(dp_keys) + len(cat_keys) + len(pos_keys)

        X = np.zeros((len(records), n_params))
        y = np.zeros(len(records))
        w = np.zeros(len(records))

        idx_ctx_hp = {k: i for i, k in enumerate(ctx_hp_keys)}
        for i, r in enumerate(records):
            key = (r["ctx"], r["hp"])
            if key in idx_ctx_hp:
                X[i, idx_ctx_hp[key]] = 1.0
            for j, dp in enumerate(dp_keys):
                if r["dp"] == dp:
                    X[i, n_ctx_hp + j] = 1.0
            for j, c in enumerate(cat_keys):
                if r["cat"] == c:
                    X[i, n_ctx_hp + len(dp_keys) + j] = 1.0
            scen = r["scenario"]
            if scen == "SB":
                X[i, n_ctx_hp + len(dp_keys) + len(cat_keys)] = 1.0
            elif scen in ("CO", "HJ", "UTG"):
                X[i, n_ctx_hp + len(dp_keys) + len(cat_keys) + 1] = 1.0
            y[i] = r["gto"]
            w[i] = r["n"]

        sqrtw = np.sqrt(w)
        theta, *_ = np.linalg.lstsq(X * sqrtw[:, None], y * sqrtw, rcond=None)

        self.T = {k: theta[idx_ctx_hp[k]] for k in ctx_hp_keys}
        self.DP_bonus = {0: 0.0}
        for j, dp in enumerate(dp_keys):
            self.DP_bonus[dp] = theta[n_ctx_hp + j]
        self.cat_offset = {"default": 0.0}
        for j, c in enumerate(cat_keys):
            self.cat_offset[c] = theta[n_ctx_hp + len(dp_keys) + j]
        self.pos_lift = {"BTN": 0.0, "SB": theta[n_ctx_hp + len(dp_keys) + len(cat_keys)],
                         "CO": theta[n_ctx_hp + len(dp_keys) + len(cat_keys) + 1],
                         "HJ": theta[n_ctx_hp + len(dp_keys) + len(cat_keys) + 1],
                         "UTG": theta[n_ctx_hp + len(dp_keys) + len(cat_keys) + 1]}
        self.n_p = n_params

    def predict(self, r):
        t = self.T.get((r["ctx"], r["hp"]), 0.5)
        dp_b = self.DP_bonus.get(r["dp"], 0.0)
        co = self.cat_offset.get(r["cat"], 0.0)
        pl = self.pos_lift.get(r["scenario"], 0.0)
        return max(0.02, min(0.98, t + dp_b + co + pl))

    def n_params(self):
        return self.n_p


# ─── 候補 A: 階層型 (Vol2 base + α/β layer) ───────────────
class CandidateA:
    """B[ctx5][band] + α[ctx13] + β[ctx13]·I(CBS≥7) + cat_offset[cat]
    parameters: 25 + 13 + 13 + 3 = 54 params
    暗算: Vol2 = 4 step, Vol3 = 6 step
    """
    def fit(self, records):
        # Stage 1: Vol2 base = combos 加重平均
        base_agg = defaultdict(lambda: [0.0, 0.0])
        for r in records:
            ctx5 = CTX13_TO_5[r["ctx"]]
            base_agg[(ctx5, r["band"])][0] += r["n"] * r["gto"]
            base_agg[(ctx5, r["band"])][1] += r["n"]
        self.base = {(c, b): v[0]/v[1] for (c, b), v in base_agg.items() if v[1] > 0}

        # Stage 2: α/β per ctx13, cat_offset を WLS で fit
        cat_keys = ["slowplay", "trash", "premium"]
        n_params = len(CTX13) + len(CTX13) + len(cat_keys)
        idx_alpha = {c: i for i, c in enumerate(CTX13)}
        idx_beta = {c: len(CTX13) + i for i, c in enumerate(CTX13)}
        idx_cat = {c: 2*len(CTX13) + i for i, c in enumerate(cat_keys)}

        X = np.zeros((len(records), n_params))
        y = np.zeros(len(records))
        w = np.zeros(len(records))
        for i, r in enumerate(records):
            ctx5 = CTX13_TO_5[r["ctx"]]
            b = self.base.get((ctx5, r["band"]), 0.5)
            X[i, idx_alpha[r["ctx"]]] = 1.0
            if r["cbs"] >= 7:
                X[i, idx_beta[r["ctx"]]] = 1.0
            if r["cat"] in idx_cat:
                X[i, idx_cat[r["cat"]]] = 1.0
            y[i] = r["gto"] - b
            w[i] = r["n"]

        sqrtw = np.sqrt(w)
        theta, *_ = np.linalg.lstsq(X * sqrtw[:, None], y * sqrtw, rcond=None)

        self.alpha = {c: theta[idx_alpha[c]] for c in CTX13}
        self.beta = {c: theta[idx_beta[c]] for c in CTX13}
        self.cat_offset = {"default": 0.0}
        for c in cat_keys:
            self.cat_offset[c] = theta[idx_cat[c]]
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


# ─── 評価 ─────────────────────────────────────────────────
def evaluate(model, records, name):
    """ctx 別 WRMSE と max abs error"""
    by_ctx = defaultdict(list)
    for r in records:
        by_ctx[r["ctx"]].append(r)
    print(f"\n=== {name} (params: {model.n_params()}) ===")
    print(f"{'ctx':>20s}  {'records':>7s}  {'WRMSE':>8s}  {'max|err|':>9s}")
    overall_sse, overall_n = 0.0, 0.0
    overall_max = 0.0
    for ctx in CTX13:
        recs = by_ctx.get(ctx, [])
        if not recs:
            continue
        sse, total_n = 0.0, 0.0
        max_err = 0.0
        for r in recs:
            pred = model.predict(r)
            err = pred - r["gto"]
            sse += r["n"] * err * err
            total_n += r["n"]
            max_err = max(max_err, abs(err))
        wrmse = (sse / total_n) ** 0.5 * 100 if total_n else 0
        overall_sse += sse
        overall_n += total_n
        overall_max = max(overall_max, max_err)
        print(f"  {ctx:>18s}  {len(recs):>7d}  {wrmse:>6.2f}%  {max_err*100:>7.1f}%")
    overall = (overall_sse / overall_n) ** 0.5 * 100 if overall_n else 0
    print(f"  {'OVERALL':>18s}  {sum(len(by_ctx[c]) for c in CTX13):>7d}  "
          f"{overall:>6.2f}%  {overall_max*100:>7.1f}%")
    return overall


def main():
    print("Loading data...")
    records = load_all()
    print(f"Loaded {len(records)} records across {len(set(r['ctx'] for r in records))} contexts")
    print(f"Total combos: {sum(r['n'] for r in records):.0f}")

    for cls, name in [(CandidateI, "候補 I: 差分表 δ"),
                       (CandidateH, "候補 H: HP×ctx 直接"),
                       (CandidateA, "候補 A: 階層型")]:
        model = cls()
        model.fit(records)
        evaluate(model, records, name)

    print("\n" + "=" * 60)
    print("参考: 既存 Full UCBS-v2 平均 WRMSE ~16%, Light ~21%")


if __name__ == "__main__":
    main()
