"""18 cells grid + outs を直接 score に加算 (DV テーブル廃止)。

【設計】
Score = w_tier × tier + Grid[tier][board_3]
      + w_outs × outs (DV 5段階 → outs 直接)
      + w_oc × overcards + w_pot × pot - w_bs × bs + intercept

【outs lookup (読者の前提知識)】
- combo_draw: 15
- nut_flush_draw: 9
- flush_draw: 9
- oesd: 8
- gutshot: 4
- twocards_bdfd: 2
- onecard_bdfd: 1
- no_draw: 0

→ 読者は「FD = 9 outs、OESD = 8 outs」を覚えている前提
→ 公式: outs × 係数 だけで draw 価値が決まる
→ 暗記表が 1 つ減る

【期待】
- 連続: 0.39 BB 維持
- 整数: 0.42 BB を維持しつつ、DV テーブル削除
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/OUTS_DIRECT_FORMULA.md"

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
TIER_NAMES = ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]
BL_3_NAMES = ["dry","paired","wet"]

OUTS_TABLE = {
    "combo_draw": 15,
    "nut_flush_draw": 9,
    "flush_draw": 9,
    "oesd": 8,
    "gutshot": 4,
    "twocards_bdfd": 2,
    "onecard_bdfd": 1,
    "no_draw": 0,
}
BS_BASE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
OPP_R = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def board_3(board):
    if len(board) < 6: return 0
    cards = [board[i*2:i*2+2] for i in range(3)]
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return 0
    suits = [c[1].lower() for c in cards]
    if rvals[0]==rvals[1] or rvals[1]==rvals[2]: return 1  # paired
    if len(set(suits))==1: return 2  # monotone → wet
    if rvals[0]-rvals[1] <=2 and rvals[1]-rvals[2] <=2: return 2  # connected → wet
    return 0  # dry


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
        records.append({
            "tier_idx": TIER_6[MV_TIER_MAP[mv]],
            "b3": board_3(board),
            "outs": OUTS_TABLE.get(r.get("dv_cat", "no_draw"), 0),
            "opp_r": OPP_R[parse_pot(r["scenario_id"])],
            "bs": BS_BASE[bs_str],
            "oc": hero_oc(ca, cb, board),
            "best_action": {"fold":0,"call":1,"raise":2}[ba],
            "ev_fold": efv, "ev_call": ecv, "ev_raise": erv, "best_ev": be,
        })

N = len(records)
print(f"Loaded {N:,} rows")

tier_idx = np.array([r["tier_idx"] for r in records], dtype=np.int8)
b3 = np.array([r["b3"] for r in records], dtype=np.int8)
outs = np.array([r["outs"] for r in records], dtype=np.float32)
opp = np.array([r["opp_r"] for r in records], dtype=np.float32)
bs = np.array([r["bs"] for r in records], dtype=np.float32)
oc = np.array([r["oc"] for r in records], dtype=np.float32)
ba_arr = np.array([r["best_action"] for r in records], dtype=np.int8)
ev_arr = np.stack([[r["ev_fold"], r["ev_call"], r["ev_raise"]] for r in records]).astype(np.float32)
be_arr = np.array([r["best_ev"] for r in records], dtype=np.float32)
g_idx = tier_idx.astype(np.int32) * 3 + b3.astype(np.int32)


def evaluate(params):
    grid = np.array([params[f"g_{i}"] for i in range(18)], dtype=np.float32)
    score = (params["w_tier"] * tier_idx.astype(np.float32)
             + grid[g_idx]
             + params["w_outs"] * outs
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
    for i in range(18): params[f"g_{i}"] = trial.suggest_float(f"g_{i}", -10, 20)
    params["w_tier"] = trial.suggest_float("w_tier", 0, 5)
    params["w_outs"] = trial.suggest_float("w_outs", 0, 2)  # outs × 0~2
    params["w_oc"] = trial.suggest_float("w_oc", -2, 3)
    params["w_pot"] = trial.suggest_float("w_pot", 0, 4)
    params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
    params["intercept"] = trial.suggest_float("intercept", -15, 15)
    t_call = trial.suggest_float("t_call", -15, 15)
    t_raise = trial.suggest_float("t_raise", t_call + 0.5, 60)
    params["t_call"] = t_call; params["t_raise"] = t_raise
    _, avg_loss, _ = evaluate(params)
    return avg_loss


optuna.logging.set_verbosity(optuna.logging.WARNING)
print(f"\n=== Optuna 18 cells + outs direct (2500 trials) ===")
study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=2500, show_progress_bar=True)
best = study.best_params
acc, avg, huge = evaluate(best)
print(f"\n連続: acc={acc:.2f}%, loss={avg:.4f} BB, huge={huge:.2f}%")

# Integer (w_outs は 0.5 刻みで)
int_p = {}
for k, v in best.items():
    if k.startswith("g_") or k == "intercept" or k in ("w_tier","w_oc","w_pot","w_bs"):
        int_p[k] = round(v)
    elif k == "w_outs":
        int_p[k] = round(v * 2) / 2  # 0.5 刻み
int_p["t_call"] = round(best["t_call"])
int_p["t_raise"] = max(int_p["t_call"]+1, round(best["t_raise"]))
acc_i, avg_i, huge_i = evaluate(int_p)
print(f"整数 (w_outs は 0.5 刻み): acc={acc_i:.2f}%, loss={avg_i:.4f} BB, huge={huge_i:.2f}%")

# Try w_outs=1 fixed (もっとも素朴な「outs そのまま」)
print(f"\n=== w_outs=1 固定 (outs そのまま加算) ===")
def objective_w1(trial):
    params = {}
    for i in range(18): params[f"g_{i}"] = trial.suggest_float(f"g_{i}", -10, 20)
    params["w_tier"] = trial.suggest_float("w_tier", 0, 5)
    params["w_outs"] = 1.0  # fixed
    params["w_oc"] = trial.suggest_float("w_oc", -2, 3)
    params["w_pot"] = trial.suggest_float("w_pot", 0, 4)
    params["w_bs"] = trial.suggest_float("w_bs", 0, 3)
    params["intercept"] = trial.suggest_float("intercept", -15, 15)
    t_call = trial.suggest_float("t_call", -15, 30)
    t_raise = trial.suggest_float("t_raise", t_call + 0.5, 80)
    params["t_call"] = t_call; params["t_raise"] = t_raise
    _, avg_loss, _ = evaluate(params)
    return avg_loss

study_w1 = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study_w1.optimize(objective_w1, n_trials=2000, show_progress_bar=False)
best_w1 = study_w1.best_params
best_w1["w_outs"] = 1.0
acc_w1, avg_w1, huge_w1 = evaluate(best_w1)
print(f"w_outs=1 連続: acc={acc_w1:.2f}%, loss={avg_w1:.4f} BB, huge={huge_w1:.2f}%")

# Integer w_outs=1
int_p_w1 = {k: round(v) for k, v in best_w1.items()
            if k.startswith("g_") or k == "intercept" or k in ("w_tier","w_oc","w_pot","w_bs")}
int_p_w1["w_outs"] = 1.0
int_p_w1["t_call"] = round(best_w1["t_call"])
int_p_w1["t_raise"] = max(int_p_w1["t_call"]+1, round(best_w1["t_raise"]))
acc_w1_i, avg_w1_i, huge_w1_i = evaluate(int_p_w1)
print(f"w_outs=1 整数: acc={acc_w1_i:.2f}%, loss={avg_w1_i:.4f} BB, huge={huge_w1_i:.2f}%")


lines = []
lines.append("# Outs Direct Formula (DV テーブル廃止)")
lines.append("")
lines.append("読者は outs を知っている前提で、outs を直接 score に加算。")
lines.append("DV テーブル (combo=4, FD=3, etc) を覚える必要なし。")
lines.append("")
lines.append("## 性能比較")
lines.append("")
lines.append("| variant | 連続 acc | 連続 loss | huge% | 整数 acc | 整数 loss | huge% |")
lines.append("|---|---:|---:|---:|---:|---:|---:|")
lines.append(f"| w_outs 自由 (18 cells) | {acc:.2f}% | {avg:.4f} | {huge:.2f}% | {acc_i:.2f}% | {avg_i:.4f} | {huge_i:.2f}% |")
lines.append(f"| **w_outs=1 固定 (18 cells)** | {acc_w1:.2f}% | **{avg_w1:.4f}** | {huge_w1:.2f}% | {acc_w1_i:.2f}% | **{avg_w1_i:.4f}** | {huge_w1_i:.2f}% |")
lines.append(f"| (参考) 18 cells + DV 5段階 | — | — | — | 69.44% | **0.4165** | 1.77% |")
lines.append(f"| (参考) v1 (24 cells + DV) | — | — | — | 66.5% | 0.4789 | 2.28% |")
lines.append("")

lines.append("## w_outs=1 公式 (整数版)")
lines.append("")
lines.append("```")
lines.append(f"Score = {int_p_w1['w_tier']} × tier + Grid[tier][board]")
lines.append(f"      + 1 × outs (読者が計算)")
lines.append(f"      + {int_p_w1['w_oc']} × overcards")
lines.append(f"      + {int_p_w1['w_pot']} × pot - {int_p_w1['w_bs']} × bs + ({int_p_w1['intercept']})")
lines.append("")
lines.append("outs lookup (読者が暗算):")
lines.append("  combo draw (FD+OESD): 15")
lines.append("  flush draw / NFD:     9")
lines.append("  OESD:                 8")
lines.append("  gutshot:              4")
lines.append("  BDFD (2 cards):       2")
lines.append("  no draw:              0")
lines.append("")
lines.append(f"if Score >= {int_p_w1['t_raise']}: raise")
lines.append(f"elif Score >= {int_p_w1['t_call']}: call")
lines.append("else: fold")
lines.append("```")
lines.append("")

lines.append("## Grid (w_outs=1 整数版)")
lines.append("")
lines.append("| tier | dry | paired | wet |")
lines.append("|------|---:|---:|---:|")
for ti in range(6):
    row = f"| {TIER_NAMES[ti]} |"
    for bi in range(3):
        row += f" {int_p_w1[f'g_{ti*3+bi}']} |"
    lines.append(row)
lines.append("")

lines.append("## 暗記項目")
lines.append("")
lines.append("| version | 軸の値 | grid | weights | 合計項目 |")
lines.append("|---|---:|---:|---:|---:|")
lines.append("| 旧 (DV 5段階) | tier 6 + DV 5 + bs 6 + pot 4 = 21 | 18 | 5 | **44** |")
lines.append("| **新 (outs 直接)** | tier 6 + bs 6 + pot 4 = 16 | 18 | 5 | **39** ← 5 項目減 |")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
