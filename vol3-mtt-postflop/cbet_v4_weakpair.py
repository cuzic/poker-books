"""
CBet v4 — Weak-Pair Explicit Suppression
=========================================
Root cause found: bb=+1.65 in p_semi creates a constant 34% floor
for all no-draw hands via gB × sig(bb), including weak pairs.

Key insight: On medium-RAS boards, GTO bets:
  air (h=0.00):      40-50% (random bluff range)
  low_pair (h=0.25): 15-25% ← LOWER than air
  top_pair (h=0.60): 70-80% ← higher

The U-shape cannot be captured monotonically.

Fix approaches:
  F23: F17 + explicit weak-pair × no-draw penalty (additive)
  F24: F17 + weak-pair gate (separate gating for pair zone)
  F25: Non-monotone hand curve (piecewise: air=bluff, pair=tight, made=value)

Usage:
  python3 mtt-postflop/cbet_v4_weakpair.py
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
    "SRP25":(25.0,0,0), "SRP20":(20.0,0,0), "3BP20":(20.0,1,0),
    "SRP25_SB":(25.0,0,0), "SRP20_SB":(20.0,0,0), "3BP25_SB":(25.0,1,0),
    "SRP20_CO":(20.0,0,0), "SRP25_SB_cc":(25.0,0,0),
    "SRP20_SB_cc":(20.0,0,0), "LIMP25_SB":(25.0,0,1), "LIMP20_SB":(20.0,0,1),
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
    sbr_n:float; p3bp:float; plimp:float; topR:float; sp:float
    is_weak_pair:float  # 0.15 < h < 0.50
    is_air:float        # h < 0.15 and de < 0.05
    scenario:str


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
                    iwp = 1.0 if (0.15 < hand_n < 0.50) and de < 0.05 else 0.0
                    iair = 1.0 if hand_n < 0.15 and de < 0.05 else 0.0
                    y = max(0.0, min(1.0, cell.get("avg", 0.0) / 100.0))
                    data.append(DP(
                        y=y, w=float(n), ras=ras, de=de, hand=hand_n,
                        sbr_n=sbr_n, p3bp=float(p3), plimp=float(pl),
                        topR=topR, sp=sp, is_weak_pair=iwp, is_air=iair,
                        scenario=sc,
                    ))
    print(f"Loaded {len(data)} data points")
    return data


def to_arr(data):
    return (
        np.array([d.ras for d in data]),
        np.array([d.de  for d in data]),
        np.array([d.hand for d in data]),
        np.array([d.sbr_n for d in data]),
        np.array([d.p3bp for d in data]),
        np.array([d.plimp for d in data]),
        np.array([d.topR for d in data]),
        np.array([d.sp  for d in data]),
        np.array([d.is_weak_pair for d in data]),
        np.array([d.is_air for d in data]),
        np.array([d.y for d in data]),
        np.array([d.w for d in data]) / sum(d.w for d in data),
    )


sig  = lambda x: 1.0 / (1.0 + np.exp(-np.clip(x, -15, 15)))
wmse = lambda p, y, w: float(np.sum(w * (p - y)**2))


# ---------------------------------------------------------------------------
# F17 baseline
# ---------------------------------------------------------------------------
def f17(trial, r, de, h, sn, p3, pl, tr, sp, iwp, iair):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_p=p("sp_p",0,0.5)

    ta_eff = ta + w_adj*(1.0 - h)
    gA = sig(ka*(r - ta_eff)); gB = sig(kb*(r - tb)); gC = sig(kc*(r - tc))
    pv = gA * sig(va*h + ba + cs*sn + cp*p3)
    ps = gB * sig(vb*de + bb)
    pb = gC * sig(vc*iair + bc) * iair
    return np.clip(np.maximum(np.maximum(pv, ps), pb) - sp_p*sp, 0, 1)


# ---------------------------------------------------------------------------
# F23: F17 + explicit weak-pair × no-draw penalty
# Subtracts a learned penalty for the pair zone without draws
# ---------------------------------------------------------------------------
def f23(trial, r, de, h, sn, p3, pl, tr, sp, iwp, iair):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_p=p("sp_p",0,0.5)
    wp_pen=p("wp_pen",0,0.5)  # penalty for weak pair + no draw

    ta_eff = ta + w_adj*(1.0 - h)
    gA = sig(ka*(r - ta_eff)); gB = sig(kb*(r - tb)); gC = sig(kc*(r - tc))
    pv = gA * sig(va*h + ba + cs*sn + cp*p3)
    ps = gB * sig(vb*de + bb)
    pb = gC * sig(vc*iair + bc) * iair
    base = np.maximum(np.maximum(pv, ps), pb) - sp_p*sp - wp_pen*iwp
    return np.clip(base, 0, 1)


# ---------------------------------------------------------------------------
# F24: Separate weak-pair gate (even tighter threshold)
# iwp hands require higher RAS to pass the semibluff gate
# ---------------------------------------------------------------------------
def f24(trial, r, de, h, sn, p3, pl, tr, sp, iwp, iair):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_p=p("sp_p",0,0.5)
    wp_raise=p("wp_raise",0,0.4)  # how much higher RAS weak pairs need

    ta_eff = ta + w_adj*(1.0 - h)
    # Weak pairs need tb + wp_raise to activate semibluff
    tb_eff = tb + wp_raise * iwp
    gA = sig(ka*(r - ta_eff)); gB = sig(kb*(r - tb_eff)); gC = sig(kc*(r - tc))

    pv = gA * sig(va*h + ba + cs*sn + cp*p3)
    ps = gB * sig(vb*de + bb)
    pb = gC * sig(vc*iair + bc) * iair
    return np.clip(np.maximum(np.maximum(pv, ps), pb) - sp_p*sp, 0, 1)


# ---------------------------------------------------------------------------
# F25: Non-monotone hand function — piecewise model
# Separates air (bluff range), pair zone (tight), made hand (value)
# value = max(p_bluff, p_pair, p_value, p_draw)
# p_bluff: air through high-RAS gate
# p_pair: weak pairs through pair-specific gate (tight)
# p_value: strong hands (h≥0.50) through value gate
# p_draw: draws through draw gate
# ---------------------------------------------------------------------------
def f25(trial, r, de, h, sn, p3, pl, tr, sp, iwp, iair):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    # Value gate: strong hands
    ka=p("ka",1,20); ta_s=p("ta_s",0.1,0.6)
    va=p("va",0,8);  ba=p("ba",-5,3)
    # Pair gate: weak pairs (tight)
    kp=p("kp",1,20); ta_w=p("ta_w",0.3,0.9)
    vwp=p("vwp",0,5); bwp=p("bwp",-8,-0.5)  # force negative bias
    # Bluff gate: air
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    # Draw gate
    kb=p("kb",1,20); tb=p("tb",0.2,0.7)
    vb=p("vb",0,10); bb_d=p("bb_d",-5,3)
    # Modifiers
    cs=p("cs",-3,3); cp=p("cp",-5,0); sp_p=p("sp_p",0,0.5)

    strong = (h >= 0.50).astype(float)
    pair_z = ((h >= 0.15) & (h < 0.50)).astype(float)  # pair zone

    gA = sig(ka*(r - ta_s))
    gP = sig(kp*(r - ta_w))
    gC = sig(kc*(r - tc))
    gB = sig(kb*(r - tb))

    pv = strong * gA * sig(va*(h-0.5) + ba + cs*sn + cp*p3)
    pp = pair_z * gP * sig(vwp*h + bwp + cs*sn + cp*p3)
    pb = iair  * gC
    pd = gB * de * sig(vb*de + bb_d)  # draw requires de > 0 to be non-trivial

    base = np.maximum(np.maximum(np.maximum(pv, pp), pb), pd) - sp_p*sp
    return np.clip(base, 0, 1)


# ---------------------------------------------------------------------------
# F26: F25 variant — draw can help any hand (combined max)
# Same structure but draw can elevate any hand tier
# ---------------------------------------------------------------------------
def f26(trial, r, de, h, sn, p3, pl, tr, sp, iwp, iair):
    def p(n, lo, hi): return trial.suggest_float(n, lo, hi)
    ka=p("ka",1,20); ta_s=p("ta_s",0.1,0.6)
    va=p("va",0,8);  ba=p("ba",-5,3)
    kp=p("kp",1,20); ta_w=p("ta_w",0.3,0.9)
    vwp=p("vwp",0,5); bwp=p("bwp",-8,-0.5)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    kb=p("kb",1,20); tb=p("tb",0.2,0.7)
    vb=p("vb",0,10)
    cs=p("cs",-3,3); cp=p("cp",-5,0); at=p("at",0,0.3); sp_p=p("sp_p",0,0.5)

    strong = (h >= 0.50).astype(float)
    pair_z = ((h >= 0.15) & (h < 0.50)).astype(float)

    ta_s_eff = ta_s - at*tr  # ace boards loosen strong-hand threshold
    ta_w_eff = ta_w - at*tr  # ace boards also loosen pair zone slightly
    gA = sig(ka*(r - ta_s_eff))
    gP = sig(kp*(r - ta_w_eff))
    gC = sig(kc*(r - tc))
    gB = sig(kb*(r - tb))

    pv = strong * gA * sig(va*(h-0.5) + ba + cs*sn + cp*p3)
    pp = pair_z * gP * sig(vwp*h + bwp + cs*sn + cp*p3)
    pb = iair  * gC
    pd = gB * sig(vb * de - 3.0) * (de > 0.05)  # draw gate with threshold ≈0.05

    base = np.maximum(np.maximum(np.maximum(pv, pp), pb), pd) - sp_p*sp
    return np.clip(base, 0, 1)


FORMULAS = {
    "F17_base":    f17,
    "F23_WPpen":   f23,
    "F24_WPgate":  f24,
    "F25_PWB":     f25,   # Piecewise: Pair/Value/Bluff zones
    "F26_PWB_v2":  f26,
}


def run_analysis(data, pred, y, label):
    hmap = {
        0.00:"no_made", 0.10:"ace_h", 0.15:"king_h", 0.20:"underpair",
        0.25:"low_pair", 0.35:"3rd_pair", 0.45:"2nd_pair",
        0.60:"top_pair", 0.72:"overpair", 0.82:"two_pair",
        0.87:"straight", 0.88:"flush", 0.90:"set/trips",
        0.95:"fullhouse", 0.97:"quads"
    }
    from collections import defaultdict
    by_h = defaultdict(lambda:{"e":[],"w":[]})
    for i, dp in enumerate(data):
        err = (y[i] - pred[i]) * 100
        hl = hmap.get(round(dp.hand, 2), f"{dp.hand:.2f}")
        by_h[hl]["e"].append(err); by_h[hl]["w"].append(dp.w)

    def stats(d):
        e=np.array(d["e"]); wt=np.array(d["w"]); wn=wt/wt.sum()
        return np.average(e,weights=wn), math.sqrt(np.average(e**2,weights=wn))

    print(f"\n=== {label}: 残差 ===")
    print(f"{'ハンド':<14} {'残差':>8} {'WRMSE':>7}  {'判定':>6}")
    for k, d in sorted(by_h.items(), key=lambda x:stats(x[1])[0]):
        me, rm = stats(d)
        flag = "OK" if abs(me) < 10 else ("OVER" if me < 0 else "UNDER")
        print(f"  {k:<12} {me:>+7.1f}% {rm:>6.1f}%  {flag}")


def main():
    print("=" * 60)
    print("CBet v4 — Weak Pair Suppression")
    print("=" * 60)

    data = load_data()
    arrs = to_arr(data)
    r, de, h, sn, p3, pl, tr, sp, iwp, iair, y, w = arrs
    w_raw = np.array([d.w for d in data])

    bm = float(np.sum(w * (y - np.average(y, weights=w))**2))
    print(f"Baseline WMSE: {bm:.5f}  ({math.sqrt(bm)*100:.1f}%)\n")

    N = 1000
    results = {}
    print(f"最適化中 (各{N}試行)...")

    for name, fn in FORMULAS.items():
        study = optuna.create_study(direction="minimize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        def obj(trial, fn=fn):
            try:
                pred = fn(trial, r, de, h, sn, p3, pl, tr, sp, iwp, iair)
                return wmse(np.clip(pred,0,1), y, w)
            except: return 1.0
        study.optimize(obj, n_trials=N, show_progress_bar=False)
        best = study.best_value
        pct  = math.sqrt(best)*100
        rv   = 1.0 - best/bm
        results[name] = {"wmse":best,"pct":pct,"r2":rv,"params":study.best_params}
        print(f"  {name:<16} WMSE={best:.5f}  WRMSE={pct:.1f}%  R²={rv:.3f}")

    print("\n" + "=" * 60)
    print("結果比較")
    print("=" * 60)
    print(f"{'式':<18} {'WMSE':>8} {'WRMSE':>7} {'R²':>7}")
    for n_, r_ in sorted(results.items(), key=lambda x:x[1]["wmse"]):
        print(f"  {n_:<16} {r_['wmse']:.5f}  {r_['pct']:>5.1f}%  {r_['r2']:.3f}")

    best_name = min(results, key=lambda k:results[k]["wmse"])
    best_r = results[best_name]
    print(f"\n最良式: {best_name}  (R²={best_r['r2']:.3f})")
    for k, v in sorted(best_r["params"].items()):
        print(f"  {k:8s} = {v:+.4f}")

    class MT:
        def __init__(self,p): self._p=p
        def suggest_float(self,n,lo,hi): return self._p[n]

    fn_best = FORMULAS[best_name]
    mock = MT(best_r["params"])
    pred_b = np.clip(fn_best(mock, r, de, h, sn, p3, pl, tr, sp, iwp, iair), 0, 1)
    run_analysis(data, pred_b, y, best_name)

    # Boundary table for best formula
    print(f"\n=== {best_name}: 境界値表（ドローなし）===")
    hand_vals = np.array([0.00,0.10,0.15,0.20,0.25,0.35,0.45,0.60,0.72,0.82,0.90,0.95])
    hlabels   = ["noMade","aceH","kingH","underpair","lowP","3rdP","2ndP","topP","over","2pair","set","FH"]
    de0   = np.zeros(len(hand_vals))
    sp0   = np.where(hand_vals>=0.88, 1.0, 0.0)
    iwp0  = np.where((hand_vals>0.15)&(hand_vals<0.50), 1.0, 0.0)
    iair0 = np.where(hand_vals<0.15, 1.0, 0.0)

    scenarios = [
        ("SRP25(BTN)",  0.77, 0, 0, 0.5),
        ("SRP20(BTN)",  0.70, 0, 0, 0.5),
        ("3BP20",       0.55, 1, 0, 0.5),
        ("3BP25_SB",    0.65, 1, 0, 0.5),
        ("SRP25_SB",    0.44, 0, 0, 0.5),
        ("SRP20_SB",    0.50, 0, 0, 0.5),
        ("LIMP25_SB",   0.39, 0, 1, 0.5),
        ("LIMP20_SB",   0.41, 0, 1, 0.5),
    ]

    print(f"\n{'シナリオ':<14} {'RAS':>5}  noM   aceH  kingH  undP  lowP  3rdP  2ndP  topP  over  2pr   set")
    print("-" * 95)
    for sc, rv, i3b, ilmp, itr in scenarios:
        ra = np.full_like(hand_vals, rv)
        sn_ = np.zeros_like(hand_vals)
        p3_ = np.full_like(hand_vals, float(i3b))
        pl_ = np.full_like(hand_vals, float(ilmp))
        tr_ = np.full_like(hand_vals, itr)

        preds = np.clip(fn_best(mock, ra, de0, hand_vals, sn_, p3_, pl_, tr_, sp0, iwp0, iair0), 0, 1)
        vals = "  ".join(f"{int(v*100):3d}%" for v in preds[:11])
        print(f"  {sc:<12} {rv:.2f}   {vals}")

    print("\n完了。")


if __name__ == "__main__":
    main()
