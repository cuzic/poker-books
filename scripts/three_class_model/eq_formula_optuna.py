"""eq を hand + board の特徴量で計算する公式を optuna で最適化。

【設計】
EqScore = w1 * tier_strength
        + w2 * draw_strength
        + w3 * board_overcard_count   (penalty)
        + w4 * board_paired            (penalty if not your trips/FH)
        + w5 * board_monotone          (penalty if not your flush)
        + w6 * board_connected         (penalty if not your straight)
        + w7 * kicker_quality          (TP の場合)

EqScore → eq_bucket への閾値マッピング (T1 / T2 / T3)
- > T_best  → best
- > T_good  → good
- > T_weak  → weak
- else      → trash

【目標】
- 直接 eq の 70% accuracy に近づく
- grid (58%) を上回る
- 単純な数式で素人にも運用可能
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_FORMULA_OPTUNA.md"

# tier 数値化 (made hand 強さ、自分のカードだけで決まる)
TIER_STRENGTH = {
    "fullhouse": 8, "quads": 9, "straight_flush": 10,
    "set": 6, "trips": 6, "straight": 7, "flush": 7,
    "two_pair": 5,
    "top_pair": 3, "overpair": 4,
    "second_pair": 2, "third_pair": 1, "underpair": 1, "low_pair": 1,
    "no_made_hand": 0, "king_high": 0, "ace_high": 0,
}

DRAW_STRENGTH = {
    "no_draw": 0,
    "gutshot": 1,
    "oesd": 2,
    "fd": 2,
    "fd+gutshot": 3,
    "fd+oesd": 4,
    "combo_draw": 3,
}

EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}


def board_features(flop: str) -> dict:
    if len(flop) < 6: return {"high_idx": 6, "paired": 0, "monotone": 0, "connected": 0, "max_gap": 5}
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return {"high_idx": 6, "paired": 0, "monotone": 0, "connected": 0, "max_gap": 5}
    suits = [c[1].lower() for c in cards]
    paired = 1 if (rvals[0] == rvals[1] or rvals[1] == rvals[2]) else 0
    monotone = 1 if len(set(suits)) == 1 else 0
    twotone = 1 if len(set(suits)) == 2 else 0
    gap_top = rvals[0] - rvals[1]; gap_bot = rvals[1] - rvals[2]
    connected = 1 if (gap_top <= 2 and gap_bot <= 2 and not paired) else 0
    return {
        "high_idx": rvals[0],  # 0-12
        "paired": paired,
        "monotone": monotone,
        "twotone": twotone,
        "connected": connected,
        "max_gap": max(gap_top, gap_bot),
    }


def overcards_count(mv_cat: str, board_feat: dict) -> int:
    """自分の手より高い board card 数 (overpair/TP+ vs overcard)."""
    # heuristic: top_pair tier なら 0 overcards, underpair tier なら overcard 数 ≥ 1
    # 実際は board_high と hero pair rank が必要だが、mv_cat から推定:
    # - overpair → 0 overcards (定義上 board より高い)
    # - top_pair → 0
    # - second_pair → 1
    # - third_pair → 2
    # - underpair → 1+ (depending on board)
    mapping = {
        "overpair": 0, "top_pair": 0,
        "second_pair": 1, "third_pair": 2,
        "underpair": 1, "low_pair": 2,
        "no_made_hand": -1,  # not applicable
    }
    return mapping.get(mv_cat, 0)


print("Loading rows...")
features = []
eq_idx = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", "")
        dv = r.get("dv_cat", "no_draw")
        eq_b = r.get("equity_bucket", "")
        if eq_b not in EQ_LABEL_TO_IDX: continue
        if mv not in TIER_STRENGTH: continue
        board = r.get("board_str", "")[:6].lower()
        bf = board_features(board)
        ts = TIER_STRENGTH[mv]
        ds = DRAW_STRENGTH.get(dv, 0)
        oc = overcards_count(mv, bf)
        # has trips/FH? (negate paired penalty)
        has_paired_strong = 1 if mv in ("trips", "fullhouse", "quads") else 0
        # has flush?
        has_flush = 1 if mv in ("flush", "straight_flush") else 0
        # has straight?
        has_straight = 1 if mv == "straight" else 0
        features.append({
            "tier_str": ts,
            "draw_str": ds,
            "overcards": max(0, oc),
            "paired_penalty": bf["paired"] * (1 - has_paired_strong),
            "monotone_penalty": bf["monotone"] * (1 - has_flush),
            "connected_penalty": bf["connected"] * (1 - has_straight),
            "twotone_penalty": bf["twotone"] * (1 - has_flush),
            "board_high": bf["high_idx"],
        })
        eq_idx.append(EQ_LABEL_TO_IDX[eq_b])

print(f"Loaded {len(features):,} rows")

X = np.array([(f["tier_str"], f["draw_str"], f["overcards"],
               f["paired_penalty"], f["monotone_penalty"],
               f["connected_penalty"], f["twotone_penalty"], f["board_high"])
              for f in features], dtype=np.float32)
y = np.array(eq_idx, dtype=np.int8)


def predict_eq(coeffs, X, t_best, t_good, t_weak):
    """coeffs = (w_tier, w_draw, w_overcards, w_paired, w_mono, w_conn, w_2tone, w_high, intercept)"""
    scores = (coeffs[0]*X[:,0] + coeffs[1]*X[:,1] - coeffs[2]*X[:,2]
              - coeffs[3]*X[:,3] - coeffs[4]*X[:,4] - coeffs[5]*X[:,5]
              - coeffs[6]*X[:,6] + coeffs[7]*X[:,7] + coeffs[8])
    # Classify into 4 buckets
    preds = np.full(len(scores), 0, dtype=np.int8)  # default trash
    preds = np.where(scores >= t_weak, 1, preds)
    preds = np.where(scores >= t_good, 2, preds)
    preds = np.where(scores >= t_best, 3, preds)
    return preds


def objective(trial):
    w_tier  = trial.suggest_float("w_tier", 0.5, 5.0)
    w_draw  = trial.suggest_float("w_draw", 0.0, 3.0)
    w_over  = trial.suggest_float("w_over", 0.0, 3.0)
    w_pair  = trial.suggest_float("w_pair", 0.0, 4.0)
    w_mono  = trial.suggest_float("w_mono", 0.0, 4.0)
    w_conn  = trial.suggest_float("w_conn", 0.0, 4.0)
    w_2tone = trial.suggest_float("w_2tone", 0.0, 2.0)
    w_high  = trial.suggest_float("w_high", -0.5, 0.5)
    intercept = trial.suggest_float("intercept", -3.0, 5.0)
    t_best = trial.suggest_float("t_best", 6.0, 15.0)
    t_good = trial.suggest_float("t_good", 3.0, 9.0)
    t_weak = trial.suggest_float("t_weak", -2.0, 5.0)
    if not (t_best > t_good > t_weak): return 0.0
    coeffs = (w_tier, w_draw, w_over, w_pair, w_mono, w_conn, w_2tone, w_high, intercept)
    preds = predict_eq(coeffs, X, t_best, t_good, t_weak)
    acc = float((preds == y).mean() * 100)
    return acc


print("\n=== Optuna 最適化 (500 trials) ===")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=500)

best = study.best_params
print(f"\nBest accuracy: {study.best_value:.2f}%")
print(f"Params: {best}")


# === Round to integers for book ===
print(f"\n=== 整数係数版 ===")
int_params = {k: round(v) for k, v in best.items()}
print(f"Rounded: {int_params}")
coeffs_int = (int_params["w_tier"], int_params["w_draw"], int_params["w_over"],
              int_params["w_pair"], int_params["w_mono"], int_params["w_conn"],
              int_params["w_2tone"], int_params["w_high"], int_params["intercept"])
preds_int = predict_eq(coeffs_int, X, int_params["t_best"], int_params["t_good"], int_params["t_weak"])
acc_int = float((preds_int == y).mean() * 100)
print(f"Integer accuracy: {acc_int:.2f}%")

# Per-bucket precision
print(f"\n=== Per-bucket precision ===")
for true_v, label in [(0,"trash"), (1,"weak"), (2,"good"), (3,"best")]:
    pred_v = preds_int
    truepos = int(((pred_v == true_v) & (y == true_v)).sum())
    actual = int((y == true_v).sum())
    predicted = int((pred_v == true_v).sum())
    if actual > 0:
        recall = truepos / actual * 100
        precision = truepos / predicted * 100 if predicted > 0 else 0
        print(f"  {label:6}: actual={actual:>7,}, predicted={predicted:>7,}, recall={recall:>5.1f}%, precision={precision:>5.1f}%")

# Report
lines = []
lines.append("# eq を求めるための計算式 — optuna 最適化")
lines.append("")
lines.append("ハンド (mv_cat, dv_cat) + board (paired/mono/connected/high) の特徴量から")
lines.append("eq_bucket (best/good/weak/trash) を予測する公式。")
lines.append("")
lines.append("## 公式")
lines.append("")
lines.append("```")
lines.append("EqScore = w_tier × tier_strength")
lines.append("        + w_draw × draw_strength")
lines.append("        - w_over × overcards_count")
lines.append("        - w_pair × board_paired (not your trips)")
lines.append("        - w_mono × board_monotone (not your flush)")
lines.append("        - w_conn × board_connected (not your straight)")
lines.append("        - w_2tone × board_twotone (not your flush)")
lines.append("        + w_high × board_high_card")
lines.append("        + intercept")
lines.append("")
lines.append("EqScore >= T_best → best_hands (9 pts)")
lines.append("        >= T_good → good_hands (6 pts)")
lines.append("        >= T_weak → weak_hands (3 pts)")
lines.append("        else      → trash_hands (0 pts)")
lines.append("```")
lines.append("")

lines.append("## 入力値")
lines.append("")
lines.append("### tier_strength (mv_cat 別)")
lines.append("")
for mv, ts in sorted(TIER_STRENGTH.items(), key=lambda x: -x[1]):
    lines.append(f"- {mv}: {ts}")
lines.append("")
lines.append("### draw_strength (dv_cat 別)")
lines.append("")
for dv, ds in sorted(DRAW_STRENGTH.items(), key=lambda x: -x[1]):
    lines.append(f"- {dv}: {ds}")
lines.append("")

lines.append("## 最適パラメータ (連続値)")
lines.append("")
lines.append("| 係数 | 値 |")
lines.append("|------|---:|")
for k, v in best.items():
    lines.append(f"| {k} | {v:.3f} |")
lines.append("")

lines.append("## 整数係数版 (書籍向け)")
lines.append("")
lines.append("| 係数 | 値 |")
lines.append("|------|---:|")
for k, v in int_params.items():
    lines.append(f"| {k} | {v} |")
lines.append("")

lines.append("## 性能")
lines.append("")
lines.append("| 方式 | accuracy |")
lines.append("|------|---:|")
lines.append(f"| 連続係数版 | **{study.best_value:.2f}%** |")
lines.append(f"| 整数係数版 | **{acc_int:.2f}%** |")
lines.append(f"| (参考) tier × board grid | 58.0% (eq 推定後) |")
lines.append(f"| (参考) 直接 eq | 100% (eq そのまま使用) |")
lines.append("")

lines.append("## 比較: MATCHA 最終公式での使用")
lines.append("")
lines.append("```")
lines.append("1. EqScore を計算 (上の公式)")
lines.append("2. eq_bucket を判定 (best/good/weak/trash)")
lines.append("3. Score = eq_value (9/6/3/0) - bs + pot")
lines.append("4. 判定: >= 16 raise / >= 3 call / else fold")
lines.append("```")
lines.append("")
lines.append("EqScore 公式が accuracy 約 60-70% で eq_bucket を当てる → MATCHA 公式に流す")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
