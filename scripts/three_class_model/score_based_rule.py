"""数式スコアリングでルール数を最小化 (numpy 版、高速)。

【設計】
Score = w_tier * tier + w_eq * eq + w_bs * bs + w_pot * pot
判定: Score ≥ T_raise → raise, ≥ T_call → call, else fold

【目標】重み 4 個 + 閾値 2 個 = 6 パラメータで spot 判定。
Chen Formula 規模の暗算可能性。
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/SCORE_BASED_FORMULA.md"

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


def parse_scenario(scn):
    s = scn.lower()
    pot = "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
          "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"
    return pot


# === Load & vectorize ===
print("Loading rows into numpy arrays...")
tiers, eqs, bss, pots = [], [], [], []
ev_f, ev_c, ev_r, best_evs = [], [], [], []
best_actions = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        pot = parse_scenario(r["scenario_id"])
        tier = MATCHA_TIER.get(r["mv_cat"], None)
        eq_b = r.get("equity_bucket", "")
        bs = r.get("ip_bet_size", "")
        if tier is None or eq_b not in EQ_SCORE or bs not in BS_PRESSURE:
            continue
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

tiers = np.array(tiers, dtype=np.int8)
eqs = np.array(eqs, dtype=np.int8)
bss = np.array(bss, dtype=np.int8)
pots = np.array(pots, dtype=np.int8)
best_actions = np.array(best_actions, dtype=np.int8)
evs = np.stack([ev_f, ev_c, ev_r], axis=1).astype(np.float32)
best_evs = np.array(best_evs, dtype=np.float32)
print(f"Loaded {len(tiers):,} rows")


def evaluate(w_tier, w_eq, w_bs, w_pot, t_call, t_raise):
    scores = w_tier * tiers + w_eq * eqs + w_bs * bss + w_pot * pots
    preds = np.where(scores >= t_raise, 2, np.where(scores >= t_call, 1, 0))
    pred_evs = evs[np.arange(len(preds)), preds]
    losses = np.maximum(0, best_evs - pred_evs)
    acc = float((preds == best_actions).mean() * 100)
    avg = float(losses.mean())
    huge = float((losses > 5).mean() * 100)
    return acc, avg, huge


# === Grid search ===
print("\nGrid search...")
results = []
for w_tier in [1, 2, 3]:
    for w_eq in [1, 2, 3, 4]:
        for w_bs in [-3, -2, -1, 0]:
            for w_pot in [-2, -1, 0, 1, 2]:
                # only sensible score ranges
                max_score = w_tier*5 + w_eq*3 + max(0,w_bs)*5 + max(0,w_pot)*2
                min_score = min(0,w_bs)*5 + min(0,w_pot)*2
                for t_call in range(min_score, max_score+1):
                    for t_raise in range(t_call+1, max_score+2):
                        acc, avg, huge = evaluate(w_tier, w_eq, w_bs, w_pot, t_call, t_raise)
                        results.append({
                            "w": (w_tier, w_eq, w_bs, w_pot),
                            "t": (t_call, t_raise),
                            "acc": acc, "avg": avg, "huge": huge,
                        })

print(f"Evaluated {len(results):,} param combinations")

# Top by accuracy
results.sort(key=lambda x: -x["acc"])
print(f"\nTop 10 by accuracy:")
for c in results[:10]:
    print(f"  w={c['w']} t={c['t']}  acc={c['acc']:.2f}% loss={c['avg']:.4f}BB huge={c['huge']:.2f}%")
best_acc = results[0]

# Top by avg loss
results.sort(key=lambda x: x["avg"])
print(f"\nTop 5 by avg loss:")
for c in results[:5]:
    print(f"  w={c['w']} t={c['t']}  acc={c['acc']:.2f}% loss={c['avg']:.4f}BB huge={c['huge']:.2f}%")
best_loss = results[0]

# Balanced: acc - 10*loss
results.sort(key=lambda x: -(x["acc"] - 10*x["avg"]))
balanced = results[0]
print(f"\nBalanced: w={balanced['w']} t={balanced['t']}  acc={balanced['acc']:.2f}% loss={balanced['avg']:.4f}BB huge={balanced['huge']:.2f}%")

# Formula baseline
print(f"\n=== Formula baseline ===")
print("(See previous reports: v9b/v10/v15 accuracy 59.46%, loss 1.86 BB)")

# === Report ===
lines = []
lines.append("# 数式スコアリング — 6 パラメータの公式")
lines.append("")
lines.append("MATCHA 5 軸を線形結合 → 閾値判定で fold/call/raise。")
lines.append("Chen Formula 規模の暗算可能性を達成。")
lines.append("")
lines.append("## スコア計算")
lines.append("")
lines.append("```")
lines.append("Score = w_tier × tier + w_eq × eq + w_bs × bs + w_pot × pot")
lines.append("")
lines.append("tier:  ナッツ=5, ストロング=4, ツーペア=3, TP+=2, MP=1, エア=0")
lines.append("eq:    best=3, good=2, weak=1, trash=0")
lines.append("bs:    small_33=0, med_75p=1, med_100p=2, overbet=3, overbet_185=4, allin=5")
lines.append("pot:   SRP=0, DEF=1, 3BP=1, 4BP=2")
lines.append("")
lines.append("if Score >= T_raise: raise")
lines.append("elif Score >= T_call: call")
lines.append("else: fold")
lines.append("```")
lines.append("")

lines.append("## grid search 結果")
lines.append("")
lines.append("| 基準 | w_tier | w_eq | w_bs | w_pot | T_call | T_raise | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
for label, c in [("最高 accuracy", best_acc), ("最小 avg loss", best_loss), ("バランス (acc-10×loss)", balanced)]:
    lines.append(f"| **{label}** | {c['w'][0]} | {c['w'][1]} | {c['w'][2]} | {c['w'][3]} | {c['t'][0]} | {c['t'][1]} | {c['acc']:.2f}% | {c['avg']:.4f} BB | {c['huge']:.2f}% |")
lines.append("")

lines.append("## 比較表")
lines.append("")
lines.append("| variant | パラメータ数 | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| **数式 (バランス)** | **6** | **{balanced['acc']:.2f}%** | **{balanced['avg']:.4f} BB** | **{balanced['huge']:.2f}%** |")
lines.append(f"| 41 マクロルール | 41 | 71.76% | 0.41 BB | 1.90% |")
lines.append(f"| CORE 113 + FB 535 | 652 | 75.62% | 0.32 BB | 1.47% |")
lines.append(f"| 既存公式 v9b/v10/v15 | ~50 | 59.46% | 1.86 BB | 9.65% |")
lines.append("")

lines.append("## バランス選定の公式 (推奨)")
lines.append("")
lines.append("```")
lines.append(f"Score = {balanced['w'][0]} × tier + {balanced['w'][1]} × eq + ({balanced['w'][2]}) × bs + ({balanced['w'][3]}) × pot")
lines.append("")
lines.append(f"if Score >= {balanced['t'][1]}: raise")
lines.append(f"elif Score >= {balanced['t'][0]}: call")
lines.append(f"else: fold")
lines.append("```")
lines.append("")

lines.append("## 結論")
lines.append("")
lines.append(f"- **6 パラメータの式 1 本**で accuracy **{balanced['acc']:.2f}%**, loss **{balanced['avg']:.3f} BB**")
lines.append(f"- 既存公式と比べ accuracy +{balanced['acc']-59.46:.1f}pp、loss {(balanced['avg']-1.86)/1.86*100:+.1f}%")
lines.append(f"- 41 マクロルールと比べ paramters 1/7、accuracy {balanced['acc']-71.76:+.2f}pp")
lines.append("")
lines.append("**MATCHA Framework の真の暗算公式**: Chen Formula と同様、")
lines.append("数値だけ覚えれば spot 判定可能。")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
