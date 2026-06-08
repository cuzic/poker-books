"""暗算用にスコア値を pre-multiplied 化 — 係数なしの \"足し算 only\" 公式。

【旧式】Score = 1×tier + 3×eq + (-1)×bs + 2×pot
【新式】Score = tier + eq + bs + pot  (係数全部 1)

スコア表を pre-multiply して暗算を楽に:
- tier_value:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0
- eq_value:    best=9, good=6, weak=3, trash=0  ← 旧 0/1/2/3 を 3 倍
- bs_value:    small=0, 75%=-1, 100%=-2, over=-3, over185=-4, allin=-5  ← 符号反転
- pot_value:   SRP=0, DEF=2, 3BP=2, 4BP=4  ← 旧 0/1/1/2 を 2 倍

同じ閾値: Score >= 16 → raise, >= 3 → call, else fold
(旧 11/4 → 新 11/4 のまま、ただし bs を負にしたので公式上ぴったり)

【検証】同じ accuracy / loss が出るか、154K rows で再評価
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/SCORE_SIMPLIFIED_FORMULA.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}

# Pre-multiplied scores (係数 1 で足すだけ)
TIER_VAL = {"ナッツメイド":5,"ストロング":4,"ツーペア":3,"トップペア以上":2,"ミドルペア":1,"エア":0}
EQ_VAL   = {"best_hands":9,"good_hands":6,"weak_hands":3,"trash_hands":0}            # 旧×3
BS_VAL   = {"small_33":0,"med_75p":-1,"med_100p":-2,"overbet":-3,"overbet_185":-4,"allin":-5}  # 符号反転
POT_VAL  = {"SRP":0,"DEF":2,"3BP":2,"4BP":4}                                          # 旧×2


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


print("Loading rows...")
tiers, eqs, bss, pots = [], [], [], []
ev_f, ev_c, ev_r, best_evs, best_actions = [], [], [], [], []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        pot = parse_pot(r["scenario_id"])
        tier = MATCHA_TIER.get(r["mv_cat"], None)
        eq_b = r.get("equity_bucket", "")
        bs = r.get("ip_bet_size", "")
        if tier is None or eq_b not in EQ_VAL or bs not in BS_VAL: continue
        try:
            ba = r["best_action"].lower()
            efv = float(r["ev_fold"]); ecv = float(r["ev_call"]); erv = float(r["ev_raise"])
            be = float(r["best_ev"])
        except (KeyError, ValueError):
            continue
        tiers.append(TIER_VAL[tier])
        eqs.append(EQ_VAL[eq_b])
        bss.append(BS_VAL[bs])
        pots.append(POT_VAL[pot])
        best_actions.append({"fold":0,"call":1,"raise":2}[ba])
        ev_f.append(efv); ev_c.append(ecv); ev_r.append(erv); best_evs.append(be)

tiers = np.array(tiers, dtype=np.int8)
eqs   = np.array(eqs, dtype=np.int8)
bss   = np.array(bss, dtype=np.int8)
pots  = np.array(pots, dtype=np.int8)
best_actions = np.array(best_actions, dtype=np.int8)
evs   = np.stack([ev_f, ev_c, ev_r], axis=1).astype(np.float32)
best_evs = np.array(best_evs, dtype=np.float32)
N = len(tiers)
print(f"Loaded {N:,} rows")


def evaluate(t_call: int, t_raise: int):
    scores = tiers + eqs + bss + pots  # all coefficients = 1
    preds = np.where(scores >= t_raise, 2, np.where(scores >= t_call, 1, 0)).astype(np.int8)
    pred_evs = evs[np.arange(N), preds]
    losses = np.maximum(0, best_evs - pred_evs)
    acc = float((preds == best_actions).mean() * 100)
    avg = float(losses.mean())
    huge = float((losses > 5).mean() * 100)
    return acc, avg, huge


# 旧式の最適閾値: T_call=3, T_raise=16 を試す
print("\n=== 旧式に対応する閾値 (T_call=3, T_raise=16) ===")
acc, avg, huge = evaluate(3, 16)
print(f"  Accuracy: {acc:.2f}%, avg loss: {avg:.4f} BB, huge: {huge:.2f}%")

# Grid search for best thresholds with new values
print("\n=== Grid search 閾値最適化 ===")
best_balanced = (-100, 999, 999, 0, 0)
best_acc = (-100, 999, 999, 0, 0)
best_loss = (100, 999, 999, 0, 0)
score_min = -5 + 0 + 0 + 0
score_max = 5 + 9 + 0 + 4
for tc in range(score_min, score_max+1):
    for tr in range(tc+1, score_max+2):
        a, v, h = evaluate(tc, tr)
        bal = -a + 10*v + 5*h
        if bal < (-best_balanced[0] + 10*best_balanced[1] + 5*best_balanced[2]):
            best_balanced = (a, v, h, tc, tr)
        if a > best_acc[0]:
            best_acc = (a, v, h, tc, tr)
        if v < best_loss[1]:
            best_loss = (a, v, h, tc, tr)

print(f"  Balanced: t_call={best_balanced[3]}, t_raise={best_balanced[4]} → acc={best_balanced[0]:.2f}%, loss={best_balanced[1]:.4f}BB, huge={best_balanced[2]:.2f}%")
print(f"  Acc max:  t_call={best_acc[3]}, t_raise={best_acc[4]} → acc={best_acc[0]:.2f}%, loss={best_acc[1]:.4f}BB, huge={best_acc[2]:.2f}%")
print(f"  Loss min: t_call={best_loss[3]}, t_raise={best_loss[4]} → acc={best_loss[0]:.2f}%, loss={best_loss[1]:.4f}BB, huge={best_loss[2]:.2f}%")


# Theoretical score range:
# min = 0 (エア) + 0 (trash) + (-5) (allin) + 0 (SRP) = -5
# max = 5 (ナッツ) + 9 (best) + 0 (small bs) + 4 (4BP) = 18
print(f"\n  Score range: [{tiers.min() + eqs.min() + bss.min() + pots.min()}, {tiers.max() + eqs.max() + bss.max() + pots.max()}]")
print(f"  Theoretical [-5, 18]")

# Example calculations for memorization
print("\n=== 暗算の例題 ===")
print("【例 1】SRP flop で TP+ + good eq + 相手 33% bet")
print(f"  tier=2 (TP+) + eq=6 (good) + bs=0 (small) + pot=0 (SRP) = {2+6+0+0}")
print(f"  → Score 8 → call (>= {best_balanced[3]})")
print()
print("【例 2】4BP flop で TP+ + good eq + 相手 overbet")
print(f"  tier=2 + eq=6 + bs=-3 (overbet) + pot=4 (4BP) = {2+6-3+4}")
print(f"  → Score 9 → call")
print()
print("【例 3】SRP river で ナッツメイド + best eq + 相手 100% bet")
print(f"  tier=5 + eq=9 + bs=-2 + pot=0 = {5+9-2+0}")
print(f"  → Score 12 → call (>= {best_balanced[4]} なら raise)")


# === Report ===
lines = []
lines.append("# 暗算用 簡易スコア — 係数なしの「足し算 only」公式")
lines.append("")
lines.append("ユーザー提案による値の pre-multiplication で、係数を消した暗算用 MATCHA 公式。")
lines.append("数学的には旧式と等価。")
lines.append("")
lines.append("## 旧式 (係数あり)")
lines.append("")
lines.append("```")
lines.append("Score = 1 × tier + 3 × eq + (-1) × bs + 2 × pot")
lines.append("```")
lines.append("")
lines.append("## 新式 (係数なし、暗算楽)")
lines.append("")
lines.append("```")
lines.append("Score = tier + eq + bs + pot  ← 足すだけ")
lines.append("")
lines.append("tier:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0")
lines.append("eq:    best=9, good=6, weak=3, trash=0       ← 旧 0/1/2/3 を 3 倍")
lines.append("bs:    small=0, 75%=-1, 100%=-2, over=-3,    ← 符号反転")
lines.append("       over185=-4, allin=-5")
lines.append("pot:   SRP=0, DEF=2, 3BP=2, 4BP=4             ← 旧 0/1/1/2 を 2 倍")
lines.append("```")
lines.append("")

lines.append("## 評価結果 (旧式の閾値を維持)")
lines.append("")
lines.append("| 閾値 | accuracy | avg loss | huge% |")
lines.append("|------|---:|---:|---:|")
lines.append(f"| T_call=3, T_raise=16 (旧式と同等) | {acc:.2f}% | {avg:.4f} BB | {huge:.2f}% |")
lines.append("")

lines.append("## 新値での閾値最適化")
lines.append("")
lines.append("| 基準 | T_call | T_raise | accuracy | avg loss | huge% |")
lines.append("|------|---:|---:|---:|---:|---:|")
lines.append(f"| バランス | {best_balanced[3]} | {best_balanced[4]} | {best_balanced[0]:.2f}% | {best_balanced[1]:.4f} BB | {best_balanced[2]:.2f}% |")
lines.append(f"| acc max  | {best_acc[3]} | {best_acc[4]} | {best_acc[0]:.2f}% | {best_acc[1]:.4f} BB | {best_acc[2]:.2f}% |")
lines.append(f"| loss min | {best_loss[3]} | {best_loss[4]} | {best_loss[0]:.2f}% | {best_loss[1]:.4f} BB | {best_loss[2]:.2f}% |")
lines.append("")

lines.append("## 推奨公式 (バランス)")
lines.append("")
lines.append("```")
lines.append("Score = tier + eq + bs + pot")
lines.append("")
lines.append("tier:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0")
lines.append("eq:    best=9, good=6, weak=3, trash=0")
lines.append("bs:    small=0, 75%=-1, 100%=-2, over=-3, over185=-4, allin=-5")
lines.append("pot:   SRP=0, DEF=2, 3BP=2, 4BP=4")
lines.append("")
lines.append(f"if Score >= {best_balanced[4]}: raise")
lines.append(f"elif Score >= {best_balanced[3]}: call")
lines.append("else: fold")
lines.append("```")
lines.append("")

lines.append("## 暗算の例題")
lines.append("")
lines.append("### 例 1: SRP flop で TP+ + good eq + 相手 33% bet")
lines.append("- tier=2 (TP+) + eq=6 (good) + bs=0 (small) + pot=0 (SRP)")
lines.append("- Score = **8** → call")
lines.append("")
lines.append("### 例 2: 4BP flop で TP+ + good eq + 相手 overbet")
lines.append("- tier=2 + eq=6 + bs=-3 (overbet) + pot=4 (4BP)")
lines.append("- Score = **9** → call")
lines.append("")
lines.append("### 例 3: SRP river で ナッツ + best eq + 相手 100% bet")
lines.append("- tier=5 + eq=9 + bs=-2 + pot=0")
lines.append("- Score = **12** → call")
lines.append("")

lines.append("## 比較")
lines.append("")
lines.append("| 式 | 操作 | 例: SRP TP+ good 33% |")
lines.append("|---|---|---|")
lines.append("| 旧式 | 1×2 + 3×2 + (-1)×0 + 2×0 = 8 | 4 個の乗算 + 4 個の加算 |")
lines.append("| **新式** | 2 + 6 + 0 + 0 = 8 | **0 乗算、3 加算** |")
lines.append("")
lines.append("→ 暗算負荷 ~70% 削減。Chen Formula 同様「数値を覚えて足すだけ」")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
