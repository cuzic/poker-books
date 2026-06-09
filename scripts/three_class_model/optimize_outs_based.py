"""outs ベース DV + tier+draw 統合 grid の組合せ最適化。

【DV 変更】 outs を直接使う (連続値)
- combo_draw: 15 outs (FD+OESD)
- nut_flush_draw: 9
- flush_draw: 9
- oesd: 8
- gutshot: 4
- twocards_bdfd: 1.5
- onecard_bdfd: 0.5
- no_draw: 0

【街考慮】 rule of 4 and 2
- flop (2 streets): outs × 4 = % equity
- turn (1 street): outs × 2 = % equity
- river: outs × 0 = 0 (draw 完成不可)

【grid】 td4 × b4 = 16 cells (前回最強)

【期待】 0.44 → 0.40 BB
"""
from __future__ import annotations
import csv
import re
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/OUTS_BASED_FORMULA.md"

RANKS = "23456789TJQKA"
MV_TIER_MAP = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_6 = {"エア":0,"ミドルペア":1,"トップペア以上":2,"ツーペア":3,"ストロング":4,"ナッツメイド":5}
OUTS = {
    "combo_draw": 15,
    "nut_flush_draw": 9,
    "flush_draw": 9,
    "oesd": 8,
    "gutshot": 4,
    "twocards_bdfd": 1.5,
    "onecard_bdfd": 0.5,
    "no_draw": 0,
}
DV_HAS = {"combo_draw","nut_flush_draw","flush_draw","oesd","gutshot","twocards_bdfd"}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def parse_street(scn):
    s = scn.lower()
    if "river" in s: return 2
    if "turn" in s: return 1
    return 0  # flop


def board_4(board):
    if len(board) < 6: return 0
    cards = [board[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return 0
    suits = [c[1].lower() for c in cards]
    if rvals[0]==rvals[1] or rvals[1]==rvals[2]: return 1
    if len(set(suits))==1: return 3
    if rvals[0]-rvals[1] <=2 and rvals[1]-rvals[2] <=2: return 2
    return 0


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_h = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_h)
    except (ValueError, IndexError):
        return 0


def tier_draw_4(tier_idx, has_draw):
    if tier_idx >= 3: return 0  # 強メイド
    if tier_idx >= 1: return 1  # 中メイド
    if has_draw: return 2  # draw
    return 3  # trash


print("Loading...")
records = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", "")
        bs_str = r.get("ip_bet_size", "")
        if mv not in MV_TIER_MAP or bs_str not in BS_BASE: continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb: continue
        try:
            ba = r["best_action"].lower()
            efv = float(r["ev_fold"]); ecv = float(r["ev_call"]); erv = float(r["ev_raise"])
            be = float(r["best_ev"])
        except (KeyError, ValueError):
            continue
        tier_idx = TIER_6[MV_TIER_MAP[mv]]
        dv_cat = r.get("dv_cat", "no_draw")
        outs = OUTS.get(dv_cat, 0)
        has_draw = 1 if dv_cat in DV_HAS else 0
        street = parse_street(r["scenario_id"])
        # outs × multiplier (rule of 4 and 2)
        # flop: 2 streets → x4 (一気に turn & river ある場合)、x2 (1 street の場合)
        # turn: 1 street → x2
        # river: 0 (draw 完成不可)
        if street == 0: multiplier = 4   # flop, full 2 streets
        elif street == 1: multiplier = 2  # turn, 1 street
        else: multiplier = 0             # river
        outs_eq = outs * multiplier  # 0-60 %eq 概算
        records.append({
            "tier_orig": tier_idx,
            "td_4": tier_draw_4(tier_idx, has_draw),
            "b4": board_4(board),
            "outs_eq": outs_eq,
            "raw_outs": outs,
            "street": street,
            "opp_r": OPP_R[parse_pot(r["scenario_id"])],
            "bs": BS_BASE[bs_str],
            "oc": hero_oc(ca, cb, board),
            "best_action": {"fold":0,"call":1,"raise":2}[ba],
            "ev_fold": efv, "ev_call": ecv, "ev_raise": erv, "best_ev": be,
        })

N = len(records)
print(f"Loaded {N:,} rows")

tier_orig = np.array([r["tier_orig"] for r in records], dtype=np.int8)
td_4 = np.array([r["td_4"] for r in records], dtype=np.int8)
b4 = np.array([r["b4"] for r in records], dtype=np.int8)
outs_eq = np.array([r["outs_eq"] for r in records], dtype=np.float32)
raw_outs = np.array([r["raw_outs"] for r in records], dtype=np.float32)
street_arr = np.array([r["street"] for r in records], dtype=np.int8)
opp = np.array([r["opp_r"] for r in records], dtype=np.float32)
bs = np.array([r["bs"] for r in records], dtype=np.float32)
oc = np.array([r["oc"] for r in records], dtype=np.float32)
ba_arr = np.array([r["best_action"] for r in records], dtype=np.int8)
ev_arr = np.stack([[r["ev_fold"], r["ev_call"], r["ev_raise"]] for r in records]).astype(np.float32)
be_arr = np.array([r["best_ev"] for r in records], dtype=np.float32)
g_idx = td_4.astype(np.int32) * 4 + b4.astype(np.int32)  # 4×4 = 16


def run_config(name, dv_source):
    """dv_source: 'outs_eq' (rule of 4/2) or 'raw_outs' (直接)"""
    dv = outs_eq if dv_source == "outs_eq" else raw_outs

    def evaluate(params):
        grid = np.array([params[f"g_{i}"] for i in range(16)], dtype=np.float32)
        score = (params["w_tier"] * tier_orig.astype(np.float32)
                 + grid[g_idx]
                 + params["w_dv"] * dv
                 + params["w_oc"] * oc
                 + params["w_pot"] * opp - params["w_bs"] * bs
                 + params["intercept"])
        preds = np.where(score >= params["t_raise"], 2,
                         np.where(score >= params["t_call"], 1, 0)).astype(np.int8)
        pred_evs = ev_arr[np.arange(N), preds]
        losses = np.maximum(0, be_arr - pred_evs)
        return (float((preds == ba_arr).mean()*100),
                float(losses.mean()), float((losses>5).mean()*100))

    def objective(trial):
        params = {}
        for i in range(16): params[f"g_{i}"] = trial.suggest_float(f"g_{i}", -10, 20)
        params["w_tier"] = trial.suggest_float("w_tier", 0, 5)
        params["w_dv"] = trial.suggest_float("w_dv", 0, 1.0)
        params["w_oc"] = trial.suggest_float("w_oc", -2, 3)
        params["w_pot"] = trial.suggest_float("w_pot", 0, 3)
        params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
        params["intercept"] = trial.suggest_float("intercept", -15, 15)
        t_call = trial.suggest_float("t_call", -15, 15)
        t_raise = trial.suggest_float("t_raise", t_call + 0.5, 60)
        params["t_call"] = t_call; params["t_raise"] = t_raise
        _, avg_loss, _ = evaluate(params)
        return avg_loss

    print(f"\n=== {name} (16 cells, 2000 trials) ===")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=2000)
    best = study.best_params
    acc, avg, huge = evaluate(best)
    # Integer (w_dv は float 維持)
    int_p = {}
    for k, v in best.items():
        if k.startswith("g_") or k == "intercept" or k in ("w_tier","w_oc","w_pot","w_bs"):
            int_p[k] = round(v)
        elif k == "w_dv":
            # round to 0.5 increments
            int_p[k] = round(v * 2) / 2
    int_p["t_call"] = round(best["t_call"])
    int_p["t_raise"] = max(int_p["t_call"]+1, round(best["t_raise"]))
    acc_i, avg_i, huge_i = evaluate(int_p)
    print(f"  連続: acc={acc:.2f}%, loss={avg:.4f} BB, huge={huge:.2f}%")
    print(f"  整数 (w_dv は 0.5 刻み): acc={acc_i:.2f}%, loss={avg_i:.4f} BB, huge={huge_i:.2f}%")
    print(f"  weights: w_tier={best['w_tier']:.2f}, w_dv={best['w_dv']:.3f}, w_oc={best['w_oc']:.2f}, w_pot={best['w_pot']:.2f}, w_bs={best['w_bs']:.2f}, intercept={best['intercept']:.2f}")
    return {"name": name, "acc": acc, "avg": avg, "huge": huge,
            "acc_i": acc_i, "avg_i": avg_i, "huge_i": huge_i,
            "best": best, "int": int_p, "dv_source": dv_source}


results = []
results.append(run_config("outs × multiplier (rule of 4/2)", "outs_eq"))
results.append(run_config("raw outs (no street scaling)", "raw_outs"))


lines = []
lines.append("# Outs ベース DV 公式")
lines.append("")
lines.append("## 性能比較")
lines.append("")
lines.append("| variant | 連続 acc | 連続 loss | 連続 huge% | 整数 acc | 整数 loss | 整数 huge% |")
lines.append("|---|---:|---:|---:|---:|---:|---:|")
for r in results:
    lines.append(f"| {r['name']} | {r['acc']:.2f}% | {r['avg']:.4f} | {r['huge']:.2f}% | {r['acc_i']:.2f}% | {r['avg_i']:.4f} | {r['huge_i']:.2f}% |")
lines.append("")
lines.append("| baseline | acc | loss |")
lines.append("|---|---:|---:|")
lines.append("| td4 × b4 +DV (dv_cat 5段階) | 68.81% | 0.4441 BB |")
lines.append("| v1 (24 single grid) | 66.5% | 0.48 BB |")
lines.append("")

TD_NAMES = ["強メイド","中メイド","draw","trash"]
BL_NAMES = ["dry","paired","connected","monotone"]
for r in results:
    lines.append(f"## {r['name']} 整数 Grid")
    lines.append("")
    lines.append("| | " + " | ".join(BL_NAMES) + " |")
    lines.append("|---" * 5 + "|")
    for ti in range(4):
        row = [TD_NAMES[ti]] + [str(r['int'][f'g_{ti*4+bi}']) for bi in range(4)]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    lines.append(f"weights: " + ", ".join([f"{k}={v}" for k, v in r['int'].items() if k.startswith("w_") or k == "intercept"]))
    lines.append(f"thresholds: t_call={r['int']['t_call']}, t_raise={r['int']['t_raise']}")
    lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
