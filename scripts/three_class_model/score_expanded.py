"""シナリオ軸を細分化して 6 → 8 パラメータ式を試す。

【追加軸】
- street: flop=0, turn=1, river=2  (3 値)
- role: attacker (open-raise side), defender (caller side)  (2 値)
  - SRP/3BP/4BP は attacker
  - DEF は defender (CR/donk defense)

【公式拡張】
Score = w_tier × tier + w_eq × eq + w_bs × bs + w_pot × pot
      + w_street × street + w_role × role

【目的】attack/defense + street を含めて精度向上、何 pp の改善か測定
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/SCORE_EXPANDED_FORMULA.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"アンダーペア","third_pair":"アンダーペア","underpair":"アンダーペア","low_pair":"アンダーペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_SCORE = {"ナッツメイド":5,"ストロング":4,"ツーペア":3,"トップペア以上":2,"アンダーペア":1,"エア":0}
EQ_SCORE = {"best_hands":3,"good_hands":2,"weak_hands":1,"trash_hands":0}
BS_PRESSURE = {"small_33":0,"med_75p":1,"med_100p":2,"overbet":3,"overbet_185":4,"allin":5}
POT_PRESSURE = {"SRP":0,"DEF":1,"3BP":1,"4BP":2}
STREET_VAL = {"flop":0,"turn":1,"river":2}


def parse_scn(scn):
    s = scn.lower()
    pot = "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
          "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"
    street = "river" if "river" in s else "turn" if "turn" in s else "flop"
    role = "defender" if pot == "DEF" else "attacker"
    cr_type = "cr" if "cr_def" in s else "donk" if "donk_def" in s else "none"
    return pot, street, role, cr_type


# === Load ===
print("Loading rows...")
tiers, eqs, bss, pots, streets, roles = [], [], [], [], [], []
ev_f, ev_c, ev_r, best_evs, best_actions = [], [], [], [], []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        pot, street, role, cr_type = parse_scn(r["scenario_id"])
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
        streets.append(STREET_VAL[street])
        roles.append(0 if role == "attacker" else 1)
        best_actions.append({"fold":0,"call":1,"raise":2}[ba])
        ev_f.append(efv); ev_c.append(ecv); ev_r.append(erv); best_evs.append(be)

tiers = np.array(tiers, dtype=np.float32)
eqs = np.array(eqs, dtype=np.float32)
bss = np.array(bss, dtype=np.float32)
pots = np.array(pots, dtype=np.float32)
streets = np.array(streets, dtype=np.float32)
roles = np.array(roles, dtype=np.float32)
best_actions = np.array(best_actions, dtype=np.int8)
evs = np.stack([ev_f, ev_c, ev_r], axis=1).astype(np.float32)
best_evs = np.array(best_evs, dtype=np.float32)
N = len(tiers)
print(f"Loaded {N:,} rows")
print(f"  attackers: {(roles==0).sum():,} / defenders: {(roles==1).sum():,}")
print(f"  flop: {(streets==0).sum():,} / turn: {(streets==1).sum():,} / river: {(streets==2).sum():,}")


def evaluate(coeffs):
    """coeffs = (w_tier, w_eq, w_bs, w_pot, w_street, w_role, t_call, t_raise)"""
    wt, we, wb, wp, ws, wr, tc, tr = coeffs
    scores = wt*tiers + we*eqs + wb*bss + wp*pots + ws*streets + wr*roles
    preds = np.where(scores >= tr, 2, np.where(scores >= tc, 1, 0)).astype(np.int8)
    pred_evs = evs[np.arange(N), preds]
    losses = np.maximum(0, best_evs - pred_evs)
    acc = float((preds == best_actions).mean() * 100)
    avg = float(losses.mean())
    huge = float((losses > 5).mean() * 100)
    return acc, avg, huge


# === Optuna: balanced objective ===
print("\n=== Optuna 8-param balanced (500 trials) ===")
def obj_balanced(trial: optuna.Trial) -> float:
    wt = trial.suggest_float("w_tier", 0, 5)
    we = trial.suggest_float("w_eq", 0, 5)
    wb = trial.suggest_float("w_bs", -3, 1)
    wp = trial.suggest_float("w_pot", -3, 3)
    ws = trial.suggest_float("w_street", -3, 3)
    wr = trial.suggest_float("w_role", -3, 3)
    tc = trial.suggest_float("t_call", -5, 20)
    tr = trial.suggest_float("t_raise", -5, 30)
    if tr <= tc: return 100.0
    acc, avg, huge = evaluate((wt, we, wb, wp, ws, wr, tc, tr))
    return -acc + 10*avg + 5*huge

optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="minimize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(obj_balanced, n_trials=500)
best_bal = study.best_params

# Also accuracy and loss objectives
print("=== Optuna 8-param acc max (500 trials) ===")
def obj_acc(trial):
    wt = trial.suggest_float("w_tier", 0, 5)
    we = trial.suggest_float("w_eq", 0, 5)
    wb = trial.suggest_float("w_bs", -3, 1)
    wp = trial.suggest_float("w_pot", -3, 3)
    ws = trial.suggest_float("w_street", -3, 3)
    wr = trial.suggest_float("w_role", -3, 3)
    tc = trial.suggest_float("t_call", -5, 20)
    tr = trial.suggest_float("t_raise", -5, 30)
    if tr <= tc: return 0.0
    a, _, _ = evaluate((wt,we,wb,wp,ws,wr,tc,tr))
    return a

study2 = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study2.optimize(obj_acc, n_trials=500)
best_acc = study2.best_params


def report(params):
    coeffs = (params["w_tier"],params["w_eq"],params["w_bs"],params["w_pot"],
              params["w_street"],params["w_role"],params["t_call"],params["t_raise"])
    return evaluate(coeffs)


a_bal, l_bal, h_bal = report(best_bal)
a_acc, l_acc, h_acc = report(best_acc)
print(f"\nBalanced: acc={a_bal:.2f}%, loss={l_bal:.4f}BB, huge={h_bal:.2f}%")
print(f"  weights: tier={best_bal['w_tier']:.2f}, eq={best_bal['w_eq']:.2f}, bs={best_bal['w_bs']:.2f}, pot={best_bal['w_pot']:.2f}, street={best_bal['w_street']:.2f}, role={best_bal['w_role']:.2f}")
print(f"  thresholds: t_call={best_bal['t_call']:.2f}, t_raise={best_bal['t_raise']:.2f}")
print(f"\nAcc max: acc={a_acc:.2f}%, loss={l_acc:.4f}BB, huge={h_acc:.2f}%")


# Rounded version
def round_p(b):
    return (round(b["w_tier"]), round(b["w_eq"]), round(b["w_bs"]), round(b["w_pot"]),
            round(b["w_street"]), round(b["w_role"]),
            round(b["t_call"]), round(b["t_raise"]))

print(f"\n=== Rounded (integer, book-friendly) ===")
for name, b in [("balanced", best_bal), ("acc-max", best_acc)]:
    wt, we, wb, wp, ws, wr, tc, tr = round_p(b)
    if tr <= tc: tr = tc + 1
    a, l, h = evaluate((wt,we,wb,wp,ws,wr,tc,tr))
    print(f"  {name:10} w=({wt},{we},{wb},{wp},{ws},{wr}) t=({tc},{tr}) → acc={a:.2f}%, loss={l:.4f}BB, huge={h:.2f}%")


# === Per-scenario breakdown ===
print("\n=== Per-scenario breakdown (8-param balanced) ===")
wt, we, wb, wp, ws, wr, tc, tr = (best_bal["w_tier"],best_bal["w_eq"],best_bal["w_bs"],
                                  best_bal["w_pot"],best_bal["w_street"],best_bal["w_role"],
                                  best_bal["t_call"],best_bal["t_raise"])
scores = wt*tiers + we*eqs + wb*bss + wp*pots + ws*streets + wr*roles
preds = np.where(scores >= tr, 2, np.where(scores >= tc, 1, 0)).astype(np.int8)
losses = np.maximum(0, best_evs - evs[np.arange(N), preds])
correct = (preds == best_actions)

# By (role, street)
print(f"{'scenario':25} {'n':>10} {'acc':>7} {'loss':>9}")
for role_v, role_name in [(0, "attacker"), (1, "defender")]:
    for st_v, st_name in [(0, "flop"), (1, "turn"), (2, "river")]:
        mask = (roles == role_v) & (streets == st_v)
        n = int(mask.sum())
        if n == 0: continue
        a = correct[mask].mean() * 100
        l = losses[mask].mean()
        print(f"  {role_name:10} {st_name:8} {n:>10,} {a:>6.1f}% {l:>8.4f}BB")

# By pot type
print(f"\n{'pot':10} {'n':>10} {'acc':>7} {'loss':>9}")
pot_names = ["SRP", "DEF", "3BP", "4BP"]  # by POT_PRESSURE values 0,1,1,2 — duplicate
pot_idx = pots
for p_val, p_name in [(0, "SRP"), (1, "DEF/3BP"), (2, "4BP")]:
    mask = (pots == p_val)
    n = int(mask.sum())
    if n == 0: continue
    a = correct[mask].mean()*100
    l = losses[mask].mean()
    print(f"  {p_name:8} {n:>10,} {a:>6.1f}% {l:>8.4f}BB")

# === Report ===
lines = []
lines.append("# 8 パラメータ式 — street/role 軸を追加")
lines.append("")
lines.append("MATCHA 6 パラメータ式に **street** (flop/turn/river) と **role** (attacker/defender) を追加。")
lines.append("「あらゆるシナリオ (attack/defense × 3 streets) でも使えるか」を検証。")
lines.append("")
lines.append("## 式")
lines.append("")
lines.append("```")
lines.append("Score = w_tier × tier + w_eq × eq + w_bs × bs + w_pot × pot + w_street × street + w_role × role")
lines.append("")
lines.append("street: flop=0, turn=1, river=2")
lines.append("role:   attacker=0, defender=1")
lines.append("```")
lines.append("")

lines.append("## 結果")
lines.append("")
lines.append("| variant | params | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| **8-param 連続 (バランス)** | 8 | **{a_bal:.2f}%** | **{l_bal:.4f} BB** | {h_bal:.2f}% |")
lines.append(f"| 8-param 連続 (acc max) | 8 | **{a_acc:.2f}%** | {l_acc:.4f} BB | {h_acc:.2f}% |")
wt, we, wb, wp, ws, wr, tc, tr = round_p(best_bal)
if tr <= tc: tr = tc+1
a_int, l_int, h_int = evaluate((wt,we,wb,wp,ws,wr,tc,tr))
lines.append(f"| **8-param 整数 (バランス)** | 8 | {a_int:.2f}% | {l_int:.4f} BB | {h_int:.2f}% |")
lines.append(f"| 6-param 整数 (前回 推奨) | 6 | 70.76% | 0.3220 BB | 1.15% |")
lines.append(f"| 41 マクロルール | 41 | 71.76% | 0.41 BB | 1.90% |")
lines.append(f"| 既存公式 v9b/v10/v15 | ~50 | 59.46% | 1.86 BB | 9.65% |")
lines.append("")

lines.append("## 最適 8 パラメータ (バランス、整数版)")
lines.append("")
lines.append("```")
lines.append(f"Score = {wt} × tier + {we} × eq + ({wb}) × bs + ({wp}) × pot + ({ws}) × street + ({wr}) × role")
lines.append("")
lines.append("tier:   ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0")
lines.append("eq:     best=3, good=2, weak=1, trash=0")
lines.append("bs:     small=0, 75%=1, 100%=2, over=3, over185=4, allin=5")
lines.append("pot:    SRP=0, DEF=1, 3BP=1, 4BP=2")
lines.append("street: flop=0, turn=1, river=2")
lines.append("role:   attacker=0, defender=1")
lines.append("")
lines.append(f"if Score >= {tr}: raise")
lines.append(f"elif Score >= {tc}: call")
lines.append("else: fold")
lines.append("```")
lines.append("")

# Per-scenario stats from balanced
print("\nFilling per-scenario stats in report...")
lines.append("## シナリオ別 精度 (8-param バランス)")
lines.append("")
lines.append("| role | street | n | accuracy | avg loss |")
lines.append("|---|---|---:|---:|---:|")
for role_v, role_name in [(0, "attacker"), (1, "defender")]:
    for st_v, st_name in [(0, "flop"), (1, "turn"), (2, "river")]:
        mask = (roles == role_v) & (streets == st_v)
        n = int(mask.sum())
        if n == 0: continue
        a = float(correct[mask].mean() * 100)
        l = float(losses[mask].mean())
        lines.append(f"| {role_name} | {st_name} | {n:,} | {a:.2f}% | {l:.4f} BB |")
lines.append("")

lines.append("## 解釈")
lines.append("")
diff = a_int - 70.76
loss_diff = (0.3220 - l_int) / 0.3220 * 100
lines.append(f"- 8-param 整数 vs 6-param 整数: accuracy {diff:+.2f}pp, loss {loss_diff:+.1f}%")
lines.append(f"- street/role を入れることでシナリオ別 spot に追従可能に")
lines.append(f"- attacker と defender, flop と river で行動が違う部分を式で捕捉")
lines.append(f"- パラメータ +2 個のコストで精度大幅向上 (or 小幅)")
lines.append("")
lines.append("## 結論")
lines.append("")
if a_int > 73:
    lines.append(f"- **8-param 式は \"あらゆるシナリオ\" で機能** (accuracy {a_int:.1f}%)")
    lines.append(f"- attack/defense × flop/turn/river の差を完全捕捉")
else:
    lines.append(f"- 8-param 式は accuracy {a_int:.1f}% で 6-param とほぼ同等")
    lines.append(f"- → MATCHA の本質は **tier + eq + bs + pot** の 4 軸で十分")
    lines.append(f"- street/role は副次的、書籍向け公式には不要")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
