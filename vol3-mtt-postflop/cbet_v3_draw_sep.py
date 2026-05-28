"""
CBet v3 — Draw Separation + Focused Factor Analysis
====================================================
Building on F17_ThreeGates (best: WMSE=0.02836, R²=0.576)

Key issue identified: semibluff gate (gate_B) bleeds into no-draw hands
because bb > 0 gives non-zero p_semi even when de=0.

F19: Separate draw gate with de as multiplicative gate
     p_semi = gate_B * de * sig(vb * de_nonlinear + bb)
F20: F19 + full hand-ace combined
F21: Polarized structure — explicit 2-mode model:
     high-RAS: p_hi = sigmoid(va*hand + ba) ← aggressive base
     low-RAS:  p_lo = sigmoid(vl*hand + bl) ← tight base
     p = gate*p_hi + (1-gate)*p_lo + draw_bonus

Usage:
  python3 mtt-postflop/cbet_v3_draw_sep.py
"""

from __future__ import annotations
import json, math, warnings
from pathlib import Path
from dataclasses import dataclass
import numpy as np
import optuna

optuna.logging.set_verbosity(optuna.logging.WARNING)
warnings.filterwarnings("ignore")

FINDINGS_DIR = Path(__file__).parent / "findings"

SCENARIO_FILES = [
    "draw_study_SRP25.jsonl", "draw_study_SRP20.jsonl",
    "draw_study_3BP20.jsonl", "draw_study_SRP25_SB.jsonl",
    "draw_study_SRP20_SB.jsonl", "draw_study_3BP25_SB.jsonl",
    "draw_study_SRP20_CO.jsonl", "draw_study_SRP25_SB_cc.jsonl",
    "draw_study_SRP20_SB_cc.jsonl", "draw_study_LIMP25_SB.jsonl",
    "draw_study_LIMP20_SB.jsonl",
]

SCENARIO_META = {
    "SRP25": (25.0, 0, 0), "SRP20": (20.0, 0, 0), "3BP20": (20.0, 1, 0),
    "SRP25_SB": (25.0, 0, 0), "SRP20_SB": (20.0, 0, 0), "3BP25_SB": (25.0, 1, 0),
    "SRP20_CO": (20.0, 0, 0), "SRP25_SB_cc": (25.0, 0, 0),
    "SRP20_SB_cc": (20.0, 0, 0), "LIMP25_SB": (25.0, 0, 1), "LIMP20_SB": (20.0, 0, 1),
}

BOARD_META = {
    "K98":(2,13,5),"T98":(3,10,2),"K72":(5,13,11),"Q83":(2,12,5),"J73":(5,11,8),
    "A94":(1,14,10),"765":(6,7,2),"KJT":(3,13,3),"T74":(5,10,6),
    "A72":(1,14,12),"742":(1,7,5),"KK8":(7,13,5),"AA7":(7,14,7),
}

HAND_NORM = {
    "no_made_hand":(0.00,0),"ace_high":(0.10,1),"king_high":(0.15,1),
    "underpair":(0.20,2),"low_pair":(0.25,2),"third_pair":(0.35,3),
    "second_pair":(0.45,5),"top_pair":(0.60,7),"overpair":(0.72,7),
    "two_pair":(0.82,8),"set":(0.90,8),"trips":(0.90,9),
    "flush":(0.88,9),"straight":(0.87,9),"fullhouse":(0.95,9),"quads":(0.97,9),
}

DRAW_EQUITY = {
    "no_draw":(0.00,0),"twocards_bdfd":(0.05,0),"onecard_bdfd":(0.08,1),
    "gutshot":(0.20,2),"oesd":(0.35,3),"fd":(0.30,3),"flush_draw":(0.30,3),
    "nut_flush_draw":(0.32,4),"fd_gutshot":(0.40,4),"fd_oesd":(0.50,5),
    "combo_draw":(0.50,5),
}


@dataclass
class DP:
    y:float; w:float; ras:float; de:float; hand:float
    sbr_n:float; p3bp:float; plimp:float; topR:float
    sp:float; scenario:str


def load_data():
    data = []
    for fname in SCENARIO_FILES:
        fp = FINDINGS_DIR / fname
        if not fp.exists(): continue
        with open(fp) as f:
            for line in f:
                rec = json.loads(line.strip())
                if not rec: continue
                sc = rec["scenario"]
                if sc not in SCENARIO_META: continue
                sbr, p3, pl = SCENARIO_META[sc]
                sbr_n = (sbr - 20.0) / 10.0
                gp = rec["group"]
                if gp not in BOARD_META: continue
                _, top_rank, _ = BOARD_META[gp]
                topR = (top_rank - 2) / 12.0
                nd = rec.get("draw_agg", {}).get("no_draw", {})
                ras = nd.get("bet_pct", 50.0) / 100.0
                for key, cell in rec.get("cross", {}).items():
                    n = cell.get("n", 0)
                    if n == 0: continue
                    parts = key.split("|")
                    if len(parts) != 2: continue
                    hs, ds = parts
                    hi = HAND_NORM.get(hs); di = DRAW_EQUITY.get(ds)
                    if hi is None or di is None: continue
                    hand_n, _ = hi; de, _ = di
                    sp = 1.0 if hs in ("set","fullhouse","quads","trips") else 0.0
                    y = max(0.0, min(1.0, cell.get("avg", 0.0) / 100.0))
                    data.append(DP(y=y, w=float(n), ras=ras, de=de, hand=hand_n,
                                   sbr_n=sbr_n, p3bp=float(p3), plimp=float(pl),
                                   topR=topR, sp=sp, scenario=sc))
    print(f"Loaded {len(data)} data points")
    return data


def arrays(data):
    r  = np.array([d.ras   for d in data])
    de = np.array([d.de    for d in data])
    h  = np.array([d.hand  for d in data])
    sn = np.array([d.sbr_n for d in data])
    p3 = np.array([d.p3bp  for d in data])
    pl = np.array([d.plimp for d in data])
    tr = np.array([d.topR  for d in data])
    sp = np.array([d.sp    for d in data])
    y  = np.array([d.y     for d in data])
    w  = np.array([d.w     for d in data])
    w  = w / w.sum()
    return r, de, h, sn, p3, pl, tr, sp, y, w


def sig(x): return 1.0 / (1.0 + np.exp(-np.clip(x, -15, 15)))
def wmse(p, y, w): return float(np.sum(w * (p - y)**2))
def wrmse_pct(p, y, w): return math.sqrt(wmse(p, y, w)) * 100


# ---------------------------------------------------------------------------
# F17 reference (best from v2)
# ---------------------------------------------------------------------------
def f17(trial, r, de, h, sn, p3, pl, tr, sp):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_p=p("sp_p",0,0.5)

    ta_eff = ta + w_adj * (1.0 - h)
    gA = sig(ka*(r - ta_eff)); gB = sig(kb*(r - tb)); gC = sig(kc*(r - tc))
    is_air = (h < 0.2).astype(float) * (de < 0.1).astype(float)

    pv = gA * sig(va*h + ba + cs*sn + cp*p3)
    ps = gB * sig(vb*de + bb)
    pb = gC * sig(vc*is_air + bc) * is_air

    base = np.maximum(np.maximum(pv, ps), pb)
    return np.clip(base - sp_p*sp, 0, 1)


# ---------------------------------------------------------------------------
# F19: Draw-separation fix
# p_semi only contributes when de > 0 (de acts as multiplicative factor)
# ---------------------------------------------------------------------------
def f19(trial, r, de, h, sn, p3, pl, tr, sp):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.2,0.7)
    kc=p("kc",1,20); tc=p("tc",0.4,0.95)
    va=p("va",0,6); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-3,5)  # no-draw floor can be positive but de=0 kills it
    vc=p("vc",0,8);  bc=p("bc",-3,5)
    sp_p=p("sp_p",0,0.5)
    at=p("at",0,0.3)  # ace-board loosening

    ta_eff = ta + w_adj * (1.0 - h) - at * tr
    gA = sig(ka*(r - ta_eff))
    gB = sig(kb*(r - tb))
    gC = sig(kc*(r - tc))
    is_air = (h < 0.2).astype(float) * (de < 0.1).astype(float)

    pv = gA * sig(va*h + ba + cs*sn + cp*p3)
    # KEY FIX: multiply by de so no-draw hands get p_semi=0
    ps = gB * de * sig(vb*de + bb)
    pb = gC * sig(vc*is_air + bc) * is_air

    base = np.maximum(np.maximum(pv, ps), pb)
    return np.clip(base - sp_p*sp, 0, 1)


# ---------------------------------------------------------------------------
# F20: F19 + LIMP-specific tightening
# plimp acts as additional gate raising threshold
# ---------------------------------------------------------------------------
def f20(trial, r, de, h, sn, p3, pl, tr, sp):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    lp=p("lp",0,0.3)  # LIMP raises gate threshold
    kb=p("kb",1,20); tb=p("tb",0.2,0.7)
    kc=p("kc",1,20); tc=p("tc",0.4,0.95)
    va=p("va",0,6); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-3,5)
    vc=p("vc",0,8);  bc=p("bc",-3,5)
    sp_p=p("sp_p",0,0.5)
    at=p("at",0,0.3)

    ta_eff = ta + w_adj*(1.0 - h) - at*tr + lp*pl  # LIMP tightens gate
    gA = sig(ka*(r - ta_eff))
    gB = sig(kb*(r - tb + lp*pl))  # also tightens draw gate
    gC = sig(kc*(r - tc))
    is_air = (h < 0.2).astype(float) * (de < 0.1).astype(float)

    pv = gA * sig(va*h + ba + cs*sn + cp*p3)
    ps = gB * de * sig(vb*de + bb)
    pb = gC * sig(vc*is_air + bc) * is_air

    base = np.maximum(np.maximum(pv, ps), pb)
    return np.clip(base - sp_p*sp, 0, 1)


# ---------------------------------------------------------------------------
# F21: Polarized-2mode model
# High-RAS: aggressive base + air OK
# Low-RAS: tight base, only strong hands bet
# ---------------------------------------------------------------------------
def f21(trial, r, de, h, sn, p3, pl, tr, sp):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    kg=p("kg",2,15); tg=p("tg",0.3,0.7)  # soft mode switch
    # High-RAS regime (gate=1): air OK, polarized
    va_h=p("va_h",0,5); ba_h=p("ba_h",-5,5); ve_h=p("ve_h",0,8)
    # Low-RAS regime (gate=0): tight value only
    va_l=p("va_l",0,10); ba_l=p("ba_l",-8,0)
    # Draw component (separate)
    kb=p("kb",1,20); tb=p("tb",0.2,0.7); vd=p("vd",0,10)
    # Modifiers
    cs=p("cs",-3,3); cp=p("cp",-5,0); at=p("at",0,0.3); lp=p("lp",0,0.3)
    sp_p=p("sp_p",0,0.5)

    gate = sig(kg*(r - tg))   # gate=1 → high RAS, gate=0 → low RAS

    p_hi = sig(va_h*h + ba_h + ve_h*(h - 0.5)**2 * np.sign(h - 0.5))
    p_lo = sig(va_l*h + ba_l + cs*sn + cp*p3 - at*tr - lp*pl)

    p_value = gate * p_hi + (1 - gate) * p_lo

    tb_eff = tb - at*tr + lp*pl
    gB = sig(kb*(r - tb_eff))
    p_draw = gB * de * sig(vd*de)

    base = np.maximum(p_value, p_draw)
    return np.clip(base - sp_p*sp, 0, 1)


# ---------------------------------------------------------------------------
# F22: Hand-segmented gates (separate params for weak/strong)
# ---------------------------------------------------------------------------
def f22(trial, r, de, h, sn, p3, pl, tr, sp):
    """Separate gate params for weak (h<0.5) vs strong (h≥0.5) hands."""
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    # Strong hand value gate (top_pair+)
    ka_s=p("ka_s",1,20); ta_s=p("ta_s",0.05,0.5)
    va_s=p("va_s",0,5);  ba_s=p("ba_s",-5,3)
    # Weak hand value gate (pair- , requires higher RAS)
    ka_w=p("ka_w",1,20); ta_w=p("ta_w",0.2,0.8)
    va_w=p("va_w",0,5);  ba_w=p("ba_w",-8,0)   # negative bias → tight
    # Draw gate
    kb=p("kb",1,20); tb=p("tb",0.2,0.7)
    vb=p("vb",0,10)
    # Pure bluff gate
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    # Modifiers
    cs=p("cs",-3,3); cp=p("cp",-5,0); at=p("at",0,0.3); lp=p("lp",0,0.3)
    sp_p=p("sp_p",0,0.5)

    strong = (h >= 0.5).astype(float)
    weak   = 1.0 - strong

    ta_eff_s = ta_s - at*tr
    ta_eff_w = ta_w + lp*pl - at*tr

    gA_s = sig(ka_s*(r - ta_eff_s))
    gA_w = sig(ka_w*(r - ta_eff_w))

    pv_s = gA_s * sig(va_s*h + ba_s + cs*sn + cp*p3) * strong
    pv_w = gA_w * sig(va_w*h + ba_w + cs*sn + cp*p3) * weak

    tb_eff = tb + lp*pl
    gB = sig(kb*(r - tb_eff))
    ps = gB * de * sig(vb*de)

    is_air = (h < 0.2).astype(float) * (de < 0.1).astype(float)
    gC = sig(kc*(r - tc))
    pb = gC * is_air

    base = np.maximum(np.maximum(pv_s + pv_w, ps), pb)
    return np.clip(base - sp_p*sp, 0, 1)


# ---------------------------------------------------------------------------
# Optimization + Analysis
# ---------------------------------------------------------------------------

FORMULAS = {
    "F17_ref":        f17,
    "F19_DrawSep":    f19,
    "F20_DrawLimp":   f20,
    "F21_Polarized":  f21,
    "F22_SegGates":   f22,
}


def residual_summary(data, pred, y, tag):
    from collections import defaultdict
    by_hand = defaultdict(lambda: {"e":[], "w":[]})
    by_scene = defaultdict(lambda: {"e":[], "w":[]})
    hand_map = {
        0.00:"no_made", 0.10:"ace_h", 0.15:"king_h", 0.20:"underpair",
        0.25:"low_pair", 0.35:"3rd_pair", 0.45:"2nd_pair",
        0.60:"top_pair", 0.72:"overpair", 0.82:"two_pair",
        0.87:"straight", 0.88:"flush", 0.90:"set/trips",
        0.95:"fullhouse", 0.97:"quads"
    }
    w_raw = np.array([d.w for d in data])
    for i, dp in enumerate(data):
        err = (y[i] - pred[i]) * 100
        wt = w_raw[i]
        hl = hand_map.get(round(dp.hand, 2), f"{dp.hand:.2f}")
        by_hand[hl]["e"].append(err); by_hand[hl]["w"].append(wt)
        by_scene[dp.scenario]["e"].append(err); by_scene[dp.scenario]["w"].append(wt)

    def stats(d):
        e = np.array(d["e"]); wt = np.array(d["w"]); wn = wt/wt.sum()
        return np.average(e, weights=wn), math.sqrt(np.average(e**2, weights=wn))

    print(f"\n=== {tag}: ハンドタイプ別残差 ===")
    for k, d in sorted(by_hand.items(), key=lambda x: stats(x[1])[0]):
        me, rm = stats(d)
        n = len(d["e"])
        print(f"  {k:<14} {me:>+8.1f}%  WRMSE={rm:.1f}%  n={n}")

    print(f"\n=== {tag}: シナリオ別残差 ===")
    for k, d in sorted(by_scene.items(), key=lambda x: stats(x[1])[0]):
        me, rm = stats(d)
        print(f"  {k:<18} {me:>+8.1f}%  WRMSE={rm:.1f}%")


def main():
    print("=" * 60)
    print("CBet v3 — Draw Separation & Polarized Models")
    print("=" * 60)

    data = load_data()
    r, de, h, sn, p3, pl, tr, sp, y, w = arrays(data)
    w_raw = np.array([d.w for d in data])

    bm = float(np.sum(w * (y - np.average(y, weights=w))**2))
    print(f"Baseline WMSE: {bm:.5f}  ({math.sqrt(bm)*100:.1f}%)")

    N = 1000
    results = {}
    print(f"\n最適化中 (各{N}試行)...")

    for name, fn in FORMULAS.items():
        study = optuna.create_study(direction="minimize",
                                    sampler=optuna.samplers.TPESampler(seed=42))

        def obj(trial, fn=fn):
            try:
                pred = fn(trial, r, de, h, sn, p3, pl, tr, sp)
                return wmse(np.clip(pred,0,1), y, w)
            except: return 1.0

        study.optimize(obj, n_trials=N, show_progress_bar=False)
        best = study.best_value
        pct = math.sqrt(best)*100
        rv = 1.0 - best/bm
        results[name] = {"wmse":best, "pct":pct, "r2":rv, "params":study.best_params}
        print(f"  {name:<18} WMSE={best:.5f}  WRMSE={pct:.1f}%  R²={rv:.3f}")

    print("\n" + "=" * 60)
    print("結果比較")
    print("=" * 60)
    print(f"{'式':<20} {'WMSE':>8} {'WRMSE':>7} {'R²':>7}")
    print("-" * 47)
    for n, r_ in sorted(results.items(), key=lambda x: x[1]["wmse"]):
        print(f"{n:<20} {r_['wmse']:.5f}  {r_['pct']:>5.1f}%  {r_['r2']:.3f}")

    # Best residuals
    best_name = min(results, key=lambda k: results[k]["wmse"])
    best_r = results[best_name]
    print(f"\n最良式: {best_name}  (R²={best_r['r2']:.3f})")
    for k, v in sorted(best_r["params"].items()):
        print(f"  {k:8s} = {v:+.4f}")

    class MT:
        def __init__(self, p): self._p = p
        def suggest_float(self, n, lo, hi): return self._p[n]
        def suggest_int(self, n, lo, hi): return int(self._p[n])

    fn_best = FORMULAS[best_name]
    mock = MT(best_r["params"])
    pred_best = np.clip(fn_best(mock, r, de, h, sn, p3, pl, tr, sp), 0, 1)
    residual_summary(data, pred_best, y, best_name)

    # Boundary analysis
    print(f"\n=== {best_name}: シナリオ別CBet境界 (ドローなし) ===")
    hand_vals = np.array([0.00,0.10,0.15,0.25,0.35,0.45,0.60,0.72,0.82,0.90,0.95])
    hlabels   = ["noMade","aceH","kingH","lowP","3rdP","2ndP","topP","over","2pair","set","FH"]
    de0  = np.zeros(len(hand_vals))
    sp0  = np.where(hand_vals >= 0.88, 1.0, 0.0)

    scenarios = [
        ("SRP25",    0.77, 0, 0, 0.5),
        ("SRP20",    0.70, 0, 0, 0.5),
        ("SRP20_CO", 0.79, 0, 0, 0.5),
        ("3BP20",    0.55, 1, 0, 0.5),
        ("3BP25_SB", 0.65, 1, 0, 0.5),
        ("SRP25_SB", 0.44, 0, 0, 0.5),
        ("SRP20_SB", 0.50, 0, 0, 0.5),
        ("cc_SRP20", 0.55, 0, 0, 0.5),
        ("LIMP25_SB",0.39, 0, 1, 0.5),
        ("LIMP20_SB",0.41, 0, 1, 0.5),
    ]

    print(f"{'シナリオ':<16} {'RAS':>5}  ", end="")
    for hl in hlabels[:8]:
        print(f"{hl:>7}", end="")
    print("  T_check  T_bet")
    print("-" * 100)

    for sc, ras_v, i3b, ilmp, itr in scenarios:
        ras_a = np.full_like(hand_vals, ras_v)
        sn_a  = np.zeros_like(hand_vals)
        p3_a  = np.full_like(hand_vals, float(i3b))
        pl_a  = np.full_like(hand_vals, float(ilmp))
        tr_a  = np.full_like(hand_vals, itr)

        preds = np.clip(fn_best(mock, ras_a, de0, hand_vals, sn_a, p3_a, pl_a, tr_a, sp0), 0, 1)

        t_check = "なし"
        t_bet   = "なし"
        for idx in range(len(hand_vals)-1):
            if preds[idx] < 0.20 and preds[idx+1] >= 0.20 and t_check=="なし":
                t_check = hlabels[idx+1]
            if preds[idx] < 0.80 and preds[idx+1] >= 0.80 and t_bet=="なし":
                t_bet = hlabels[idx+1]

        print(f"{sc:<16} {ras_v:>5.2f}  ", end="")
        for pv in preds[:8]:
            print(f"{pv*100:>6.0f}%", end="")
        print(f"  {t_check:>7}  {t_bet:>5}")

    print("\n完了。")


if __name__ == "__main__":
    main()
