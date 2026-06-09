"""tier + draw を統合した 1 軸 (4 分類) × board grid 比較。

【tier+draw 統合 4 分類】(実プレイ感覚に近い)
  A "強メイド" : ナッツ / ストロング / ツーペア (絶対強い made)
  B "中メイド" : TP+ / MP (中程度 made)
  C "draw"    : エア + draw あり (FD/OESD/combo)
  D "trash"   : エア + no_draw (完全ゴミ) + MP-w/o-draw

【grid 構成】
- 4 × 3 = 12 cells (board: dry/paired/wet)
- 4 × 4 = 16 cells (board: dry/paired/connected/monotone)

【別構成】tier-3 (強/中/弱) × {draw有/draw無} = 6 セル × board(3) = 18 セル
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/GRID_TIER_DRAW.md"

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
DV_HAS = {"flush_draw","nut_flush_draw","oesd","gutshot","combo_draw","twocards_bdfd"}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}
DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}


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
    if b4 == 0: return 0
    if b4 == 1: return 1
    return 2


def hero_oc(card_a, card_b, board):
    try:
        a_r = RANKS.index(card_a[0].upper()); b_r = RANKS.index(card_b[0].upper())
        cards = [board[i*2:i*2+2] for i in range(3)]
        b_h = max([RANKS.index(c[0].upper()) for c in cards])
        return sum(1 for r in (a_r, b_r) if r > b_h)
    except (ValueError, IndexError):
        return 0


def tier_draw_4(tier_idx, has_draw):
    """4 分類: 強メイド / 中メイド / draw / trash"""
    # 強メイド: ナッツ(5)/ストロング(4)/2P(3)
    if tier_idx >= 3: return 0  # 強メイド
    # 中メイド: TP+(2)/MP(1)
    if tier_idx >= 1: return 1  # 中メイド
    # エア(0) → draw あれば draw、なければ trash
    if has_draw: return 2
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
        has_draw = 1 if dv_cat in DV_HAS else 0
        b4 = board_4(board)
        records.append({
            "tier_orig": tier_idx,
            "td_4": tier_draw_4(tier_idx, has_draw),
            "b3": board_3(b4),
            "b4": b4,
            "dv_v": DV_BASE.get(dv_cat, 0),
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
b3 = np.array([r["b3"] for r in records], dtype=np.int8)
b4 = np.array([r["b4"] for r in records], dtype=np.int8)
dv_v = np.array([r["dv_v"] for r in records], dtype=np.float32)
opp = np.array([r["opp_r"] for r in records], dtype=np.float32)
bs = np.array([r["bs"] for r in records], dtype=np.float32)
oc = np.array([r["oc"] for r in records], dtype=np.float32)
ba_arr = np.array([r["best_action"] for r in records], dtype=np.int8)
ev_arr = np.stack([[r["ev_fold"], r["ev_call"], r["ev_raise"]] for r in records]).astype(np.float32)
be_arr = np.array([r["best_ev"] for r in records], dtype=np.float32)


def run_config(name, td_axis, board_axis, n_td, n_board, n_trials=1500, use_dv=False):
    g_idx = td_axis.astype(np.int32) * n_board + board_axis.astype(np.int32)
    n_cells = n_td * n_board

    def evaluate(params):
        grid = np.array([params[f"g_{i}"] for i in range(n_cells)], dtype=np.float32)
        score = (params["w_tier"] * tier_orig.astype(np.float32)
                 + grid[g_idx]
                 + params["w_oc"] * oc
                 + params["w_pot"] * opp - params["w_bs"] * bs
                 + params["intercept"])
        if use_dv:
            score = score + params["w_dv"] * dv_v
        preds = np.where(score >= params["t_raise"], 2,
                         np.where(score >= params["t_call"], 1, 0)).astype(np.int8)
        pred_evs = ev_arr[np.arange(N), preds]
        losses = np.maximum(0, be_arr - pred_evs)
        return (float((preds == ba_arr).mean()*100),
                float(losses.mean()), float((losses>5).mean()*100))

    def objective(trial):
        params = {}
        for i in range(n_cells): params[f"g_{i}"] = trial.suggest_float(f"g_{i}", -5, 15)
        params["w_tier"] = trial.suggest_float("w_tier", 0, 4)
        params["w_oc"] = trial.suggest_float("w_oc", -2, 3)
        params["w_pot"] = trial.suggest_float("w_pot", 0, 3)
        params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
        params["intercept"] = trial.suggest_float("intercept", -10, 10)
        if use_dv: params["w_dv"] = trial.suggest_float("w_dv", 0, 3)
        t_call = trial.suggest_float("t_call", -10, 15)
        t_raise = trial.suggest_float("t_raise", t_call + 0.5, 40)
        params["t_call"] = t_call; params["t_raise"] = t_raise
        _, avg_loss, _ = evaluate(params)
        return avg_loss

    print(f"\n=== {name} ({n_td}×{n_board}={n_cells} cells, {n_trials} trials) ===")
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials)
    best = study.best_params
    acc, avg, huge = evaluate(best)
    int_p = {k: round(v) for k, v in best.items() if k.startswith("g_") or k.startswith("w_") or k=="intercept"}
    int_p["t_call"] = round(best["t_call"])
    int_p["t_raise"] = max(int_p["t_call"]+1, round(best["t_raise"]))
    acc_i, avg_i, huge_i = evaluate(int_p)
    print(f"  連続: acc={acc:.2f}%, loss={avg:.4f} BB, huge={huge:.2f}%")
    print(f"  整数: acc={acc_i:.2f}%, loss={avg_i:.4f} BB, huge={huge_i:.2f}%")
    print(f"  Grid (連続):")
    for ti in range(n_td):
        row = " ".join(f"{best[f'g_{ti*n_board+bi}']:>6.2f}" for bi in range(n_board))
        print(f"    {row}")
    return {"name": name, "n_cells": n_cells, "n_td": n_td, "n_board": n_board,
            "acc": acc, "avg": avg, "huge": huge,
            "acc_i": acc_i, "avg_i": avg_i, "huge_i": huge_i,
            "best": best, "int": int_p, "use_dv": use_dv}


results = []
# tier_draw_4 軸 × board
results.append(run_config("td4 × b3 (12 cells, no DV)", td_4, b3, 4, 3, n_trials=1500, use_dv=False))
results.append(run_config("td4 × b3 (12 cells, +DV)", td_4, b3, 4, 3, n_trials=1500, use_dv=True))
results.append(run_config("td4 × b4 (16 cells, no DV)", td_4, b4, 4, 4, n_trials=1500, use_dv=False))
results.append(run_config("td4 × b4 (16 cells, +DV)", td_4, b4, 4, 4, n_trials=1500, use_dv=True))


# Report
lines = []
lines.append("# tier + draw 統合の 4 分類 × board grid")
lines.append("")
lines.append("## 4 分類 (tier_draw)")
lines.append("")
lines.append("- A 強メイド: ナッツ / ストロング / ツーペア")
lines.append("- B 中メイド: TP+ / MP")
lines.append("- C draw: エア + draw あり")
lines.append("- D trash: エア + no draw")
lines.append("")
lines.append("## 結果")
lines.append("")
lines.append("| variant | cells | 連続 acc | 連続 loss | 連続 huge% | 整数 acc | 整数 loss | 整数 huge% |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
for r in results:
    lines.append(f"| {r['name']} | {r['n_cells']} | {r['acc']:.2f}% | {r['avg']:.4f} | {r['huge']:.2f}% | {r['acc_i']:.2f}% | {r['avg_i']:.4f} | {r['huge_i']:.2f}% |")
lines.append("")
lines.append("## 比較")
lines.append("")
lines.append("| baseline | acc | loss |")
lines.append("|---|---:|---:|")
lines.append("| v1 (24 single grid) | 66.5% | 0.48 BB |")
lines.append("| v3 (9 + 4 補正) | 63.6% | 0.61 BB |")
lines.append("")

# Detail per config
TD_NAMES = ["強メイド","中メイド","draw","trash"]
for r in results:
    lines.append(f"## {r['name']} (整数版)")
    lines.append("")
    n_t = r["n_td"]; n_b = r["n_board"]
    board_names = ["dry","paired","wet"] if n_b == 3 else ["dry","paired","connected","monotone"]
    lines.append(f"| | {' | '.join(board_names)} |")
    lines.append(f"|---" * (n_b+1) + "|")
    for ti in range(n_t):
        row = [TD_NAMES[ti]] + [f"{r['int'][f'g_{ti*n_b+bi}']}" for bi in range(n_b)]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    weights = ", ".join([f"{k}={v}" for k, v in r['int'].items() if k.startswith("w_") or k == "intercept"])
    lines.append(f"weights: {weights}")
    lines.append(f"t_call={r['int']['t_call']}, t_raise={r['int']['t_raise']}")
    lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
