"""optuna でスコアリング式の最適パラメータを探索 (連続値 + 高速)。

【目的】
grid search の整数係数 → 連続値、TPE sampler で 100-300 trials に圧縮。
高速かつ高精度な公式を発見。

【最適化変数】
- w_tier, w_eq, w_bs, w_pot: 連続値 [-5, 5]
- t_call, t_raise: 連続値 [score_min, score_max]

【目的関数 (multi-objective)】
- accuracy 最大化
- avg_loss 最小化
- → Pareto frontier から「バランス」選定
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/SCORE_OPTUNA_FORMULA.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_SCORE = {"ナッツメイド":5,"ストロング":4,"ツーペア":3,"トップペア以上":2,"ミドルペア":1,"エア":0}
EQ_SCORE = {"best_hands":3,"good_hands":2,"weak_hands":1,"trash_hands":0}
BS_PRESSURE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
POT_PRESSURE = {"SRP":0,"DEF":1,"3BP":1,"4BP":2}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


print("Loading rows into numpy arrays...")
tiers, eqs, bss, pots = [], [], [], []
ev_f, ev_c, ev_r, best_evs = [], [], [], []
best_actions = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        pot = parse_pot(r["scenario_id"])
        tier = MATCHA_TIER.get(r["mv_cat"], None)
        eq_b = r.get("equity_bucket", "")
        bs = r.get("ip_bet_size", "")
        if tier is None or eq_b not in EQ_SCORE or bs not in BS_PRESSURE: continue
        try:
            ba = r["best_action"].lower()
            efv = float(r["ev_fold"]); ecv = float(r["ev_call"]); erv = float(r["ev_raise"])
            be = float(r["best_ev"])
        except (KeyError, ValueError):
            continue
        tiers.append(TIER_SCORE[tier])
        eqs.append(EQ_SCORE[eq_b])
        bss.append(BS_PRESSURE[bs])
        pots.append(POT_PRESSURE[pot])
        best_actions.append({"fold":0,"call":1,"raise":2}[ba])
        ev_f.append(efv); ev_c.append(ecv); ev_r.append(erv); best_evs.append(be)

tiers = np.array(tiers, dtype=np.float32)
eqs = np.array(eqs, dtype=np.float32)
bss = np.array(bss, dtype=np.float32)
pots = np.array(pots, dtype=np.float32)
best_actions = np.array(best_actions, dtype=np.int8)
evs = np.stack([ev_f, ev_c, ev_r], axis=1).astype(np.float32)
best_evs = np.array(best_evs, dtype=np.float32)
N = len(tiers)
print(f"Loaded {N:,} rows")


def evaluate_continuous(w_tier, w_eq, w_bs, w_pot, t_call, t_raise):
    scores = w_tier * tiers + w_eq * eqs + w_bs * bss + w_pot * pots
    preds = np.where(scores >= t_raise, 2, np.where(scores >= t_call, 1, 0)).astype(np.int8)
    pred_evs = evs[np.arange(N), preds]
    losses = np.maximum(0, best_evs - pred_evs)
    acc = float((preds == best_actions).mean() * 100)
    avg = float(losses.mean())
    huge = float((losses > 5).mean() * 100)
    return acc, avg, huge


# === Optuna: minimize -accuracy + 10*avg_loss ===
def objective(trial: optuna.Trial) -> float:
    w_tier = trial.suggest_float("w_tier", 0, 5)
    w_eq = trial.suggest_float("w_eq", 0, 5)
    w_bs = trial.suggest_float("w_bs", -3, 1)
    w_pot = trial.suggest_float("w_pot", -3, 3)
    t_call = trial.suggest_float("t_call", -5, 20)
    t_raise = trial.suggest_float("t_raise", -5, 30)
    if t_raise <= t_call: return 100.0  # invalid
    acc, avg, huge = evaluate_continuous(w_tier, w_eq, w_bs, w_pot, t_call, t_raise)
    # Composite: minimize -acc + 10*avg_loss + 5*huge
    return -acc + 10 * avg + 5 * huge


print("\n=== Optuna (TPE, 500 trials) — balanced objective ===")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=500, show_progress_bar=True)

best = study.best_params
acc, avg, huge = evaluate_continuous(best["w_tier"], best["w_eq"], best["w_bs"], best["w_pot"],
                                     best["t_call"], best["t_raise"])
print(f"\nBest balanced:")
print(f"  w_tier={best['w_tier']:.3f}, w_eq={best['w_eq']:.3f}, w_bs={best['w_bs']:.3f}, w_pot={best['w_pot']:.3f}")
print(f"  t_call={best['t_call']:.3f}, t_raise={best['t_raise']:.3f}")
print(f"  acc={acc:.2f}%, avg loss={avg:.4f} BB, huge={huge:.2f}%")


# === Single-objective: maximize accuracy ===
print("\n=== Optuna — pure accuracy maximization ===")
def acc_obj(trial: optuna.Trial) -> float:
    w_tier = trial.suggest_float("w_tier", 0, 5)
    w_eq = trial.suggest_float("w_eq", 0, 5)
    w_bs = trial.suggest_float("w_bs", -3, 1)
    w_pot = trial.suggest_float("w_pot", -3, 3)
    t_call = trial.suggest_float("t_call", -5, 20)
    t_raise = trial.suggest_float("t_raise", -5, 30)
    if t_raise <= t_call: return 0.0
    acc, _, _ = evaluate_continuous(w_tier, w_eq, w_bs, w_pot, t_call, t_raise)
    return acc

study2 = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study2.optimize(acc_obj, n_trials=500, show_progress_bar=True)
best2 = study2.best_params
acc2, avg2, huge2 = evaluate_continuous(best2["w_tier"], best2["w_eq"], best2["w_bs"], best2["w_pot"],
                                       best2["t_call"], best2["t_raise"])
print(f"\nBest accuracy: acc={acc2:.2f}%, loss={avg2:.4f}BB, huge={huge2:.2f}%")
print(f"  weights: {best2}")


# === Single-objective: minimize loss ===
print("\n=== Optuna — pure loss minimization ===")
def loss_obj(trial: optuna.Trial) -> float:
    w_tier = trial.suggest_float("w_tier", 0, 5)
    w_eq = trial.suggest_float("w_eq", 0, 5)
    w_bs = trial.suggest_float("w_bs", -3, 1)
    w_pot = trial.suggest_float("w_pot", -3, 3)
    t_call = trial.suggest_float("t_call", -5, 20)
    t_raise = trial.suggest_float("t_raise", -5, 30)
    if t_raise <= t_call: return 100.0
    _, avg, _ = evaluate_continuous(w_tier, w_eq, w_bs, w_pot, t_call, t_raise)
    return avg

study3 = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study3.optimize(loss_obj, n_trials=500, show_progress_bar=True)
best3 = study3.best_params
acc3, avg3, huge3 = evaluate_continuous(best3["w_tier"], best3["w_eq"], best3["w_bs"], best3["w_pot"],
                                       best3["t_call"], best3["t_raise"])
print(f"\nBest loss: acc={acc3:.2f}%, loss={avg3:.4f}BB, huge={huge3:.2f}%")

# === Also try: integer rounded for book readability ===
print("\n=== Round to integer (book-friendly) ===")
def round_test(b):
    return (round(b["w_tier"]), round(b["w_eq"]), round(b["w_bs"]), round(b["w_pot"]),
            round(b["t_call"]), round(b["t_raise"]))
for name, b in [("balanced", best), ("acc-max", best2), ("loss-min", best3)]:
    wt, we, wbs, wp, tc, tr = round_test(b)
    if tr <= tc: tr = tc + 1
    acc, avg, huge = evaluate_continuous(wt, we, wbs, wp, tc, tr)
    print(f"  {name:10} rounded: w=({wt},{we},{wbs},{wp}) t=({tc},{tr}) → acc={acc:.2f}%, loss={avg:.4f}BB, huge={huge:.2f}%")


# === Report ===
lines = []
lines.append("# Optuna 最適スコアリング式 — 6 パラメータ MATCHA 公式")
lines.append("")
lines.append("optuna TPE sampler で 500 trials × 3 objective を探索。")
lines.append("実数係数の最適解 + 書籍向け整数版両方を提示。")
lines.append("")

lines.append("## 探索結果 (実数係数)")
lines.append("")
lines.append("| 基準 | w_tier | w_eq | w_bs | w_pot | T_call | T_raise | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for name, b in [("バランス (-acc+10loss+5huge)", best), ("acc max", best2), ("loss min", best3)]:
    a_, av_, hu_ = evaluate_continuous(b["w_tier"], b["w_eq"], b["w_bs"], b["w_pot"], b["t_call"], b["t_raise"])
    lines.append(f"| {name} | {b['w_tier']:.2f} | {b['w_eq']:.2f} | {b['w_bs']:.2f} | {b['w_pot']:.2f} | {b['t_call']:.2f} | {b['t_raise']:.2f} | {a_:.2f}% | {av_:.4f} BB | {hu_:.2f}% |")
lines.append("")

lines.append("## 整数係数版 (書籍向け、暗算可能)")
lines.append("")
lines.append("| 基準 | w_tier | w_eq | w_bs | w_pot | T_call | T_raise | accuracy | avg loss |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
for name, b in [("バランス", best), ("acc max", best2), ("loss min", best3)]:
    wt, we, wbs, wp, tc, tr = round_test(b)
    if tr <= tc: tr = tc + 1
    a_, av_, _ = evaluate_continuous(wt, we, wbs, wp, tc, tr)
    lines.append(f"| {name} | {wt} | {we} | {wbs} | {wp} | {tc} | {tr} | {a_:.2f}% | {av_:.4f} BB |")
lines.append("")

lines.append("## 全比較表")
lines.append("")
lines.append("| variant | パラメータ数 | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| **optuna 実数版 (バランス)** | 6 | **{acc:.2f}%** | **{avg:.4f} BB** | {huge:.2f}% |")
lines.append(f"| grid search 整数版 | 6 | 71.02% | 0.3413 BB | 1.22% |")
lines.append(f"| 41 マクロルール | 41 | 71.76% | 0.41 BB | 1.90% |")
lines.append(f"| CORE 113 + FB 535 | 652 | 75.62% | 0.32 BB | 1.47% |")
lines.append(f"| 既存公式 v9b/v10/v15 | ~50 | 59.46% | 1.86 BB | 9.65% |")
lines.append("")

lines.append("## 推奨 MATCHA 公式 (バランス、暗算可能整数版)")
lines.append("")
wt, we, wbs, wp, tc, tr = round_test(best)
if tr <= tc: tr = tc + 1
a_f, av_f, hu_f = evaluate_continuous(wt, we, wbs, wp, tc, tr)
lines.append("```")
lines.append(f"Score = {wt} × tier_value + {we} × eq_value + ({wbs}) × bs_pressure + ({wp}) × pot_pressure")
lines.append("")
lines.append("tier_value:    ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0")
lines.append("eq_value:      best=3, good=2, weak=1, trash=0")
lines.append("bs_pressure:   small_33=0, med_75p=1, med_100p=2, overbet=3, overbet_185=4, allin=5")
lines.append("pot_pressure:  SRP=0, DEF=1, 3BP=1, 4BP=2")
lines.append("")
lines.append(f"if Score >= {tr}: raise")
lines.append(f"elif Score >= {tc}: call")
lines.append(f"else: fold")
lines.append("```")
lines.append("")
lines.append(f"→ accuracy {a_f:.2f}%, avg loss {av_f:.3f} BB (per spot)")
lines.append("")
lines.append("## 結論")
lines.append("")
lines.append(f"- **6 パラメータの整数公式 1 本**で accuracy {a_f:.1f}%, loss {av_f:.3f} BB")
lines.append(f"- Chen Formula 系譜の「数値だけで判断」を達成")
lines.append(f"- 既存公式 (50+ パラメータ) より +{a_f-59.46:.1f}pp 精度向上")
lines.append(f"- 41 マクロルールとほぼ同等の精度 (パラメータ 1/7)")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
