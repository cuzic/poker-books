"""Single grid の size 別比較 — 9 / 12 / 16 / 24 cells で loss/accuracy 推移。

【目的】 v1 (24 cells single) と圧縮版 (9/12/16) の精度比較。
補正項なし、純粋に grid size を変える。

【グリッド構成】
- 9 cells:  3 tier × 3 board
- 12a cells: 4 tier × 3 board
- 12b cells: 3 tier × 4 board
- 16 cells: 4 tier × 4 board
- 18 cells: 6 tier × 3 board
- 24 cells: 6 tier × 4 board (= v1)

【tier 圧縮】
- 3 tier: 強(ナッツ/ストロング) / 中(2P/TP+) / 弱(MP/エア)
- 4 tier: 強 / 2P / TP+ / 弱
- 6 tier: そのまま

【board 圧縮】
- 3 board: dry / paired / wet
- 4 board: そのまま
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/GRID_SIZE_COMPARISON.md"

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
TIER_4 = {"エア":0,"ミドルペア":0,"トップペア以上":1,"ツーペア":2,"ストロング":3,"ナッツメイド":3}
TIER_3 = {"エア":0,"ミドルペア":0,"トップペア以上":1,"ツーペア":1,"ストロング":2,"ナッツメイド":2}
DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


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


def board_3(b4):
    if b4 == 0: return 0  # dry
    if b4 == 1: return 1  # paired
    return 2  # wet


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_h = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_h)
    except (ValueError, IndexError):
        return 0


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
        tier = MV_TIER_MAP[mv]
        b4 = board_4(board)
        records.append({
            "tier6": TIER_6[tier], "tier4": TIER_4[tier], "tier3": TIER_3[tier],
            "b4": b4, "b3": board_3(b4),
            "dv": DV_BASE.get(r.get("dv_cat", "no_draw"), 0),
            "opp_r": OPP_R[parse_pot(r["scenario_id"])],
            "bs": BS_BASE[bs_str],
            "oc": hero_oc(ca, cb, board),
            "tier_orig": TIER_6[tier],  # for w_tier
            "best_action": {"fold":0,"call":1,"raise":2}[ba],
            "ev_fold": efv, "ev_call": ecv, "ev_raise": erv, "best_ev": be,
        })

N = len(records)
print(f"Loaded {N:,} rows")

tier_orig = np.array([r["tier_orig"] for r in records], dtype=np.int8)
dv_arr = np.array([r["dv"] for r in records], dtype=np.float32)
opp_arr = np.array([r["opp_r"] for r in records], dtype=np.float32)
bs_arr = np.array([r["bs"] for r in records], dtype=np.float32)
oc_arr = np.array([r["oc"] for r in records], dtype=np.float32)
best_actions_arr = np.array([r["best_action"] for r in records], dtype=np.int8)
ev_arr = np.stack([[r["ev_fold"], r["ev_call"], r["ev_raise"]] for r in records]).astype(np.float32)
best_evs_arr = np.array([r["best_ev"] for r in records], dtype=np.float32)


def run_optuna(name, tier_key, board_key, n_tier, n_board, n_trials=1500):
    tier_arr = np.array([r[tier_key] for r in records], dtype=np.int8)
    bl_arr = np.array([r[board_key] for r in records], dtype=np.int8)
    g_idx = tier_arr.astype(np.int32) * n_board + bl_arr.astype(np.int32)
    n_cells = n_tier * n_board

    def evaluate(params):
        grid = np.array([params[f"g_{i}"] for i in range(n_cells)], dtype=np.float32)
        score = (params["w_tier"] * tier_orig.astype(np.float32)
                 + grid[g_idx]
                 + params["w_dv"] * dv_arr + params["w_oc"] * oc_arr
                 + params["w_pot"] * opp_arr - params["w_bs"] * bs_arr
                 + params["intercept"])
        preds = np.where(score >= params["t_raise"], 2,
                         np.where(score >= params["t_call"], 1, 0)).astype(np.int8)
        pred_evs = ev_arr[np.arange(N), preds]
        losses = np.maximum(0, best_evs_arr - pred_evs)
        return (float((preds == best_actions_arr).mean()*100),
                float(losses.mean()), float((losses>5).mean()*100))

    def objective(trial):
        params = {}
        for i in range(n_cells): params[f"g_{i}"] = trial.suggest_float(f"g_{i}", -5, 15)
        params["w_tier"] = trial.suggest_float("w_tier", 0, 4)
        params["w_dv"] = trial.suggest_float("w_dv", 0, 3)
        params["w_oc"] = trial.suggest_float("w_oc", -2, 3)
        params["w_pot"] = trial.suggest_float("w_pot", 0, 3)
        params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
        params["intercept"] = trial.suggest_float("intercept", -10, 10)
        t_call = trial.suggest_float("t_call", -10, 15)
        t_raise = trial.suggest_float("t_raise", t_call + 0.5, 40)
        params["t_call"] = t_call; params["t_raise"] = t_raise
        _, avg_loss, _ = evaluate(params)
        return avg_loss

    print(f"\n=== {name} ({n_tier}×{n_board}={n_cells} cells, {n_trials} trials) ===")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
    best = study.best_params
    acc, avg, huge = evaluate(best)
    # Integer
    int_p = {k: round(v) for k, v in best.items() if k.startswith("g_") or k.startswith("w_") or k=="intercept"}
    int_p["t_call"] = round(best["t_call"])
    int_p["t_raise"] = max(int_p["t_call"]+1, round(best["t_raise"]))
    acc_i, avg_i, huge_i = evaluate(int_p)
    print(f"  連続: acc={acc:.2f}%, loss={avg:.4f} BB, huge={huge:.2f}%")
    print(f"  整数: acc={acc_i:.2f}%, loss={avg_i:.4f} BB, huge={huge_i:.2f}%")
    # Print grid
    print(f"  Grid (連続):")
    for ti in range(n_tier):
        row = [f"{best[f'g_{ti*n_board+bi}']:>7.2f}" for bi in range(n_board)]
        print(f"    {row}")
    return {"name": name, "n_cells": n_cells, "n_tier": n_tier, "n_board": n_board,
            "acc": acc, "avg": avg, "huge": huge,
            "acc_i": acc_i, "avg_i": avg_i, "huge_i": huge_i,
            "best": best, "int": int_p}


configs = [
    ("9 cells (3×3)",  "tier3", "b3", 3, 3),
    ("12a cells (4×3)", "tier4", "b3", 4, 3),
    ("12b cells (3×4)", "tier3", "b4", 3, 4),
    ("16 cells (4×4)", "tier4", "b4", 4, 4),
    ("18 cells (6×3)", "tier6", "b3", 6, 3),
    ("24 cells (6×4)", "tier6", "b4", 6, 4),
]

results = []
for name, tk, bk, nt, nb in configs:
    results.append(run_optuna(name, tk, bk, nt, nb, n_trials=1500))


# Report
lines = []
lines.append("# Single Grid サイズ別 比較")
lines.append("")
lines.append("補正項なしの single grid で size を 9 → 24 cells で比較。")
lines.append("各 size で 1500 trials × optuna で action loss を minimize。")
lines.append("")

lines.append("## 性能比較")
lines.append("")
lines.append("| variant | cells | 連続 acc | 連続 loss | 連続 huge% | 整数 acc | 整数 loss | 整数 huge% |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
for r in results:
    lines.append(f"| {r['name']} | {r['n_cells']} | {r['acc']:.2f}% | {r['avg']:.4f} | {r['huge']:.2f}% | {r['acc_i']:.2f}% | {r['avg_i']:.4f} | {r['huge_i']:.2f}% |")
lines.append("")

lines.append("## まとめ — Pareto frontier")
lines.append("")
lines.append("| cells | 連続 loss (BB) | 整数 loss (BB) | 整数暗記項目 |")
lines.append("|---:|---:|---:|---:|")
for r in results:
    base_items = 6  # w_tier, w_dv, w_oc, w_pot, w_bs, intercept
    total = r["n_cells"] + base_items + 2  # +2 thresholds
    lines.append(f"| {r['n_cells']} | {r['avg']:.4f} | {r['avg_i']:.4f} | {total} |")
lines.append("")

# Best grids
lines.append("## 各サイズの整数 Grid")
lines.append("")
for r in results:
    lines.append(f"### {r['name']} (整数版、loss {r['avg_i']:.4f} BB)")
    lines.append("")
    n_t = r["n_tier"]; n_b = r["n_board"]
    for ti in range(n_t):
        row = " ".join(f"{r['int'][f'g_{ti*n_b+bi}']:>4d}" for bi in range(n_b))
        lines.append(f"`{row}`")
    lines.append("")
    lines.append(f"weights: w_tier={r['int']['w_tier']}, w_dv={r['int']['w_dv']}, w_oc={r['int']['w_oc']}, w_pot={r['int']['w_pot']}, w_bs={r['int']['w_bs']}, intercept={r['int']['intercept']}")
    lines.append(f"thresholds: call={r['int']['t_call']}, raise={r['int']['t_raise']}")
    lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
