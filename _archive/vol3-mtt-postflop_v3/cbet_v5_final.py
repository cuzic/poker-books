"""
CBet v5 — Final Refinement
===========================
Starting from F23_WPpen (WMSE=0.02714, R²=0.594)

Remaining issues:
  underpair: +12.4% under-predicted (iwp classification too broad)
  fullhouse:  -39.5% over-predicted (sp_p too small for extreme slowplay)

F27: Narrow iwp to (0.25 <= h <= 0.45) — exclude underpair from penalty
F28: F27 + separate FH/quads penalty (heavier sp_p_heavy)
F29: F28 + underpair bonus (explicit +bias for underpair)
F30: Ablation — test if w_adj alone captures most of the gain (no iwp)

Usage:
  python3 mtt-postflop/cbet_v5_final.py
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
    "draw_study_SRP25.jsonl","draw_study_SRP20.jsonl","draw_study_3BP20.jsonl",
    "draw_study_SRP25_SB.jsonl","draw_study_SRP20_SB.jsonl","draw_study_3BP25_SB.jsonl",
    "draw_study_SRP20_CO.jsonl","draw_study_SRP25_SB_cc.jsonl","draw_study_SRP20_SB_cc.jsonl",
    "draw_study_LIMP25_SB.jsonl","draw_study_LIMP20_SB.jsonl",
]

SCENARIO_META = {
    "SRP25":(25,0,0),"SRP20":(20,0,0),"3BP20":(20,1,0),"SRP25_SB":(25,0,0),
    "SRP20_SB":(20,0,0),"3BP25_SB":(25,1,0),"SRP20_CO":(20,0,0),
    "SRP25_SB_cc":(25,0,0),"SRP20_SB_cc":(20,0,0),"LIMP25_SB":(25,0,1),"LIMP20_SB":(20,0,1),
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
    "nut_flush_draw":(0.32,4),"fd_gutshot":(0.40,4),"fd_oesd":(0.50,5),"combo_draw":(0.50,5),
}


@dataclass
class DP:
    y:float; w:float; ras:float; de:float; hand:float
    sbr_n:float; p3bp:float; plimp:float; topR:float
    sp_light:float  # set/trips only
    sp_heavy:float  # fullhouse/quads only
    iwp_narrow:float  # (0.25 <= h <= 0.45) no draw — exclude underpair
    iair:float
    is_underpair:float  # h exactly 0.20
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
                    sp_light = 1.0 if hs in ("set","trips") else 0.0
                    sp_heavy = 1.0 if hs in ("fullhouse","quads") else 0.0
                    # Narrow weak pair: only low_pair(0.25) + third_pair(0.35) + second_pair(0.45)
                    iwp = 1.0 if (0.24 <= hand_n <= 0.46) and de < 0.05 else 0.0
                    iair = 1.0 if hand_n < 0.15 and de < 0.05 else 0.0
                    is_up = 1.0 if abs(hand_n - 0.20) < 0.01 else 0.0
                    y = max(0.0, min(1.0, cell.get("avg",0.0)/100.0))
                    data.append(DP(
                        y=y, w=float(n), ras=ras, de=de, hand=hand_n,
                        sbr_n=sbr_n, p3bp=float(p3), plimp=float(pl),
                        topR=topR, sp_light=sp_light, sp_heavy=sp_heavy,
                        iwp_narrow=iwp, iair=iair, is_underpair=is_up, scenario=sc,
                    ))
    print(f"Loaded {len(data)} data points")
    return data


def to_arr(data):
    feat_keys = ["ras","de","hand","sbr_n","p3bp","plimp","topR",
                 "sp_light","sp_heavy","iwp_narrow","iair","is_underpair"]
    arrs = [np.array([getattr(d, k) for d in data]) for k in feat_keys]
    y = np.array([d.y for d in data])
    w = np.array([d.w for d in data]); w /= w.sum()
    return tuple(arrs) + (y, w)


sig  = lambda x: 1.0/(1.0+np.exp(-np.clip(x,-15,15)))
wmse = lambda p,y,w: float(np.sum(w*(p-y)**2))


# F23 reference (broad iwp including underpair)
def f23(trial, r, de, h, sn, p3, pl, tr, spl, sph, iwp, iair, iup):
    def p(n,lo,hi): return trial.suggest_float(n,lo,hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_p=p("sp_p",0,0.5); wp_pen=p("wp_pen",0,0.5)

    # broad iwp (includes underpair h=0.20)
    iwp_broad = ((h > 0.15) & (h < 0.50) & (de < 0.05)).astype(float)

    ta_eff = ta + w_adj*(1.0 - h)
    gA = sig(ka*(r-ta_eff)); gB = sig(kb*(r-tb)); gC = sig(kc*(r-tc))
    pv = gA*sig(va*h+ba+cs*sn+cp*p3)
    ps = gB*sig(vb*de+bb)
    pb = gC*sig(vc*iair+bc)*iair
    base = np.maximum(np.maximum(pv,ps),pb) - sp_p*(spl+sph) - wp_pen*iwp_broad
    return np.clip(base, 0, 1)


# F27: Narrow iwp (exclude underpair)
def f27(trial, r, de, h, sn, p3, pl, tr, spl, sph, iwp, iair, iup):
    def p(n,lo,hi): return trial.suggest_float(n,lo,hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_p=p("sp_p",0,0.5); wp_pen=p("wp_pen",0,0.5)

    ta_eff = ta + w_adj*(1.0 - h)
    gA = sig(ka*(r-ta_eff)); gB = sig(kb*(r-tb)); gC = sig(kc*(r-tc))
    pv = gA*sig(va*h+ba+cs*sn+cp*p3)
    ps = gB*sig(vb*de+bb)
    pb = gC*sig(vc*iair+bc)*iair
    # Use pre-computed narrow iwp (0.25-0.45 only)
    base = np.maximum(np.maximum(pv,ps),pb) - sp_p*(spl+sph) - wp_pen*iwp
    return np.clip(base, 0, 1)


# F28: Narrow iwp + separate FH/quads heavy slowplay
def f28(trial, r, de, h, sn, p3, pl, tr, spl, sph, iwp, iair, iup):
    def p(n,lo,hi): return trial.suggest_float(n,lo,hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_l=p("sp_l",0,0.3)   # light slowplay: set/trips
    sp_h=p("sp_h",0,0.6)   # heavy slowplay: fullhouse/quads
    wp_pen=p("wp_pen",0,0.5)

    ta_eff = ta + w_adj*(1.0 - h)
    gA = sig(ka*(r-ta_eff)); gB = sig(kb*(r-tb)); gC = sig(kc*(r-tc))
    pv = gA*sig(va*h+ba+cs*sn+cp*p3)
    ps = gB*sig(vb*de+bb)
    pb = gC*sig(vc*iair+bc)*iair
    base = np.maximum(np.maximum(pv,ps),pb) - sp_l*spl - sp_h*sph - wp_pen*iwp
    return np.clip(base, 0, 1)


# F29: F28 + underpair bonus
def f29(trial, r, de, h, sn, p3, pl, tr, spl, sph, iwp, iair, iup):
    def p(n,lo,hi): return trial.suggest_float(n,lo,hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_l=p("sp_l",0,0.3); sp_h=p("sp_h",0,0.6)
    wp_pen=p("wp_pen",0,0.5)
    up_bon=p("up_bon",0,0.3)  # underpair bonus (bets more than other weak pairs)

    ta_eff = ta + w_adj*(1.0 - h)
    gA = sig(ka*(r-ta_eff)); gB = sig(kb*(r-tb)); gC = sig(kc*(r-tc))
    pv = gA*sig(va*h+ba+cs*sn+cp*p3)
    ps = gB*sig(vb*de+bb)
    pb = gC*sig(vc*iair+bc)*iair
    base = np.maximum(np.maximum(pv,ps),pb) - sp_l*spl - sp_h*sph - wp_pen*iwp + up_bon*iup
    return np.clip(base, 0, 1)


# F30: Ablation — only w_adj, no iwp (test if w_adj alone is enough)
def f30(trial, r, de, h, sn, p3, pl, tr, spl, sph, iwp, iair, iup):
    def p(n,lo,hi): return trial.suggest_float(n,lo,hi)
    ka=p("ka",1,20); ta=p("ta",0.05,0.5); w_adj=p("w_adj",0,0.6)
    kb=p("kb",1,20); tb=p("tb",0.3,0.8)
    kc=p("kc",1,20); tc=p("tc",0.5,0.95)
    va=p("va",0,5); ba=p("ba",-5,3); cs=p("cs",-3,3); cp=p("cp",-5,0)
    vb=p("vb",0,10); bb=p("bb",-5,3)
    vc=p("vc",-5,5); bc=p("bc",-5,3)
    sp_l=p("sp_l",0,0.3); sp_h=p("sp_h",0,0.6)

    ta_eff = ta + w_adj*(1.0 - h)
    gA = sig(ka*(r-ta_eff)); gB = sig(kb*(r-tb)); gC = sig(kc*(r-tc))
    pv = gA*sig(va*h+ba+cs*sn+cp*p3)
    ps = gB*sig(vb*de+bb)
    pb = gC*sig(vc*iair+bc)*iair
    base = np.maximum(np.maximum(pv,ps),pb) - sp_l*spl - sp_h*sph
    return np.clip(base, 0, 1)


FORMULAS = {
    "F23_broad_iwp": f23,
    "F27_narrow_iwp": f27,
    "F28_sp_sep":     f28,
    "F29_underpair+": f29,
    "F30_ablation":   f30,
}


def residuals(data, pred, y, label):
    hmap = {
        0.00:"no_made",0.10:"ace_h",0.15:"king_h",0.20:"underpair",
        0.25:"low_pair",0.35:"3rd_pair",0.45:"2nd_pair",0.60:"top_pair",
        0.72:"overpair",0.82:"two_pair",0.87:"straight",0.88:"flush",
        0.90:"set/trips",0.95:"fullhouse",0.97:"quads",
    }
    from collections import defaultdict
    by_h = defaultdict(lambda:{"e":[],"w":[]})
    for i, dp in enumerate(data):
        err = (y[i]-pred[i])*100
        hl = hmap.get(round(dp.hand,2), f"{dp.hand:.2f}")
        by_h[hl]["e"].append(err); by_h[hl]["w"].append(dp.w)
    def st(d):
        e=np.array(d["e"]); wt=np.array(d["w"]); wn=wt/wt.sum()
        return np.average(e,weights=wn), math.sqrt(np.average(e**2,weights=wn))
    print(f"\n=== {label} 残差 ===")
    for k,d in sorted(by_h.items(),key=lambda x:st(x[1])[0]):
        me,rm = st(d); n=len(d["e"])
        flag = "OK" if abs(me)<10 else ("OVER" if me<0 else "UNDER")
        print(f"  {k:<12} {me:>+7.1f}% {rm:>6.1f}%  [{flag}] n={n}")


def main():
    print("=" * 58)
    print("CBet v5 — Final Refinement")
    print("=" * 58)
    data = load_data()
    arrs = to_arr(data)
    r,de,h,sn,p3,pl,tr,spl,sph,iwp,iair,iup,y,w = arrs
    bm = float(np.sum(w*(y-np.average(y,weights=w))**2))
    print(f"Baseline WMSE: {bm:.5f}  ({math.sqrt(bm)*100:.1f}%)\n")

    N = 1000
    results = {}
    print(f"最適化中 ({N}試行)...")

    for name, fn in FORMULAS.items():
        study = optuna.create_study(direction="minimize",
                                    sampler=optuna.samplers.TPESampler(seed=42))
        def obj(trial, fn=fn):
            try:
                pred = fn(trial, r,de,h,sn,p3,pl,tr,spl,sph,iwp,iair,iup)
                return wmse(np.clip(pred,0,1), y, w)
            except: return 1.0
        study.optimize(obj, n_trials=N, show_progress_bar=False)
        best = study.best_value
        pct  = math.sqrt(best)*100
        rv   = 1.0 - best/bm
        results[name] = {"wmse":best,"pct":pct,"r2":rv,"params":study.best_params}
        print(f"  {name:<20} WMSE={best:.5f}  WRMSE={pct:.1f}%  R²={rv:.3f}")

    print("\n" + "=" * 58)
    f23b = results.get("F23_broad_iwp",{}).get("wmse", bm)
    for n_,r_ in sorted(results.items(), key=lambda x:x[1]["wmse"]):
        imp = (f23b - r_["wmse"]) / f23b * 100
        print(f"  {n_:<20} R²={r_['r2']:.3f}  WRMSE={r_['pct']:.1f}%  改善vs F23={imp:+.1f}%")

    best_name = min(results, key=lambda k:results[k]["wmse"])
    best_r = results[best_name]
    print(f"\n最良式: {best_name}  (WMSE={best_r['wmse']:.5f}  R²={best_r['r2']:.3f})")
    for k,v in sorted(best_r["params"].items()):
        print(f"  {k:8s} = {v:+.4f}")

    class MT:
        def __init__(self,p): self._p=p
        def suggest_float(self,n,lo,hi): return self._p[n]

    fn_best = FORMULAS[best_name]
    mock = MT(best_r["params"])
    pred_b = np.clip(fn_best(mock,r,de,h,sn,p3,pl,tr,spl,sph,iwp,iair,iup),0,1)
    residuals(data, pred_b, y, best_name)

    # Boundary table
    print(f"\n=== 境界値表（ドローなし）===")
    hvs = np.array([0.00,0.10,0.15,0.20,0.25,0.35,0.45,0.60,0.72,0.82,0.90,0.95])
    hls = ["noMade","aceH","kingH","undP","lowP","3rdP","2ndP","topP","over","2pair","set","FH"]
    de0  = np.zeros(len(hvs))
    spl0 = np.where(hvs==0.90, 1.0, 0.0)
    sph0 = np.where(hvs>=0.95, 1.0, 0.0)
    iwp0 = np.where((hvs>=0.24)&(hvs<=0.46), 1.0, 0.0)
    iair0= np.where(hvs<0.15, 1.0, 0.0)
    iup0 = np.where(np.abs(hvs-0.20)<0.01, 1.0, 0.0)

    scenes = [
        ("BTN SRP25",0.77,0,0,0.5),("BTN SRP20",0.70,0,0,0.5),
        ("3BP20",    0.55,1,0,0.5),("3BP25_SB",0.65,1,0,0.5),
        ("SRP25_SB", 0.44,0,0,0.5),("SRP20_SB",0.50,0,0,0.5),
        ("LIMP25",   0.39,0,1,0.5),("LIMP20",  0.41,0,1,0.5),
    ]
    print(f"\n{'シナリオ':<13} RAS  noM  aceH kngH undP lowP 3rdP 2ndP topP over 2pr  set  FH")
    print("-" * 86)
    for sc,rv,i3,ilmp,itr in scenes:
        ra_=np.full_like(hvs,rv); sn_=np.zeros_like(hvs)
        p3_=np.full_like(hvs,float(i3)); pl_=np.full_like(hvs,float(ilmp)); tr_=np.full_like(hvs,itr)
        preds=np.clip(fn_best(mock,ra_,de0,hvs,sn_,p3_,pl_,tr_,spl0,sph0,iwp0,iair0,iup0),0,1)
        vals="  ".join(f"{int(v*100):3d}%" for v in preds)
        print(f"  {sc:<11} {rv:.2f}  {vals}")

    print("\n=== ドローボーナス確認（SRP20_SB, lowPair） ===")
    de_types = [("no_draw",0.0),("BDFD",0.05),("gutshot",0.20),("FD",0.30),("OESD",0.35),("combo",0.50)]
    sc2, ras2, i3b2, ilmp2, tr2 = "SRP20_SB", 0.50, 0, 0, 0.5
    h_lp = 0.25; sp_lp = 0.0; iwp_lp = 1.0; iair_lp = 0.0; iup_lp = 0.0
    print(f"{'ドロー':<12} {'DE':>5} {'予測CBet%':>10}")
    for dn, de_v in de_types:
        ra_=np.array([ras2]); de_=np.array([de_v]); h_=np.array([h_lp])
        sn_=np.array([0.0]); p3_=np.array([float(i3b2)]); pl_=np.array([float(ilmp2)])
        tr_=np.array([tr2]); spl_=np.array([0.0]); sph_=np.array([0.0])
        iwp_=np.array([iwp_lp if de_v<0.05 else 0.0])  # iwp only triggers when de<0.05
        iair_=np.array([0.0]); iup_=np.array([0.0])
        pred_v = fn_best(mock,ra_,de_,h_,sn_,p3_,pl_,tr_,spl_,sph_,iwp_,iair_,iup_)
        print(f"  {dn:<10} {de_v:>5.2f} {float(np.clip(pred_v,0,1)[0])*100:>9.1f}%")

    print("\n完了。")


if __name__ == "__main__":
    main()
