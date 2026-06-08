"""eq 計算式 v3 — 既存 30 features + 15 interaction 項 = 45 features。

【追加 interaction 項】 (× で相互作用)

1. set_×_paired       : set on paired board (under-FH risk)
2. set_×_monotone     : set on mono (vs flush)
3. set_×_connected    : set on connected (vs straight)
4. overpair_×_paired  : overpair on paired (board crushed if quads)
5. overpair_×_connected: overpair on wet
6. overpair_×_b_high  : overpair value × board high
7. tp_×_paired        : TP on paired (vulnerable)
8. tp_×_kicker_rank   : TP × kicker quality
9. tp_×_monotone      : TP on mono
10. mid_match_×_overcards: mid pair × overcards
11. overcards_×_connected: overcards on wet (draw bonus)
12. overcards_×_paired : overcards on paired (no help)
13. high_K_×_ace      : KK vs A board
14. set_×_high_match  : set on top vs bottom paired
15. air_×_connected   : air on connected (FD/SD potential)
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_FORMULA_V3.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}


def extract_features(card_a: str, card_b: str, board: str):
    try:
        a_r = RANKS.index(card_a[0].upper()); a_s = card_a[1].lower()
        b_r = RANKS.index(card_b[0].upper()); b_s = card_b[1].lower()
        if a_r < b_r:
            a_r, b_r = b_r, a_r; a_s, b_s = b_s, a_s

        bc = [(RANKS.index(board[i*2:i*2+2][0].upper()), board[i*2:i*2+2][1].lower())
              for i in range(len(board) // 2)]
        b_ranks = sorted([r for r, _ in bc], reverse=True)
        b_suits = [s for _, s in bc]
        b_high = b_ranks[0]; b_mid = b_ranks[1] if len(b_ranks) > 1 else 0
        b_low = b_ranks[2] if len(b_ranks) > 2 else 0

        paired = 1 if (b_ranks[0] == b_ranks[1]) or (len(b_ranks)>2 and b_ranks[1] == b_ranks[2]) else 0
        monotone = 1 if len(set(b_suits)) == 1 else 0
        twotone = 1 if len(set(b_suits)) == 2 else 0
        gap_top = b_high - b_mid; gap_bot = b_mid - b_low
        total_gap = gap_top + gap_bot
        connected = 1 if (gap_top <= 2 and gap_bot <= 2 and not paired) else 0
        ace = 1 if b_high == 12 else 0
        broadway_count = sum(1 for r in b_ranks if r >= 8)

        hero_pair = 1 if a_r == b_r else 0
        hero_suited = 1 if a_s == b_s else 0
        hero_gap = a_r - b_r
        hero_high_A = 1 if a_r == 12 else 0
        hero_high_K = 1 if a_r == 11 else 0
        hero_broadway = 1 if (a_r >= 8 and b_r >= 8) else 0
        hero_low = 1 if (a_r <= 3 and b_r <= 3) else 0

        hero_top_match = 1 if (a_r == b_high or b_r == b_high) else 0
        hero_mid_match = 1 if (a_r == b_mid or b_r == b_mid) else 0
        hero_low_match = 1 if (a_r == b_low or b_r == b_low) else 0
        hero_overpair = 1 if (hero_pair and a_r > b_high) else 0
        hero_set = 1 if (hero_pair and a_r in (b_high, b_mid, b_low)) else 0
        hero_tp_kicker = (b_r if hero_top_match and a_r == b_high else 0)
        hero_overcards = sum(1 for r in (a_r, b_r) if r > b_high)
        hero_undercards = sum(1 for r in (a_r, b_r) if r < b_low)
        hero_suits_on_board = sum(1 for r, s in bc if s in (a_s, b_s))
        all_ranks = sorted({a_r, b_r} | set(b_ranks))
        straight_outs = 0
        for r in range(13):
            if r in all_ranks: continue
            test = sorted(all_ranks + [r])
            for i in range(len(test) - 4):
                if test[i+4] - test[i] == 4: straight_outs += 1; break

        # === INTERACTION TERMS ===
        # 1. set 系 × board
        i_set_paired = hero_set * paired
        i_set_mono = hero_set * monotone
        i_set_conn = hero_set * connected
        # 2. overpair × board
        i_op_paired = hero_overpair * paired
        i_op_conn = hero_overpair * connected
        i_op_bhigh = hero_overpair * b_high  # overpair の relative strength
        # 3. TP × board
        i_tp_paired = hero_top_match * paired
        i_tp_kicker = hero_top_match * (b_r if a_r == b_high else a_r)  # kicker rank
        i_tp_mono = hero_top_match * monotone
        # 4. mid/under × overcards
        i_mid_overcards = hero_mid_match * hero_overcards
        i_oc_conn = hero_overcards * connected
        i_oc_paired = hero_overcards * paired
        # 5. specific combos
        i_K_vs_A = hero_high_K * ace  # KK on A-board → demoted
        i_set_top_match = hero_set * hero_top_match  # top set
        i_air_conn = (1 - hero_pair) * (1 - hero_top_match) * connected  # air on wet
        # 6. flush potential
        i_fd_potential = max(0, hero_suits_on_board - 1) * (twotone + monotone)

        feats = [
            a_r, b_r, hero_pair, hero_suited, hero_gap, hero_high_A, hero_high_K, hero_broadway, hero_low,
            hero_top_match, hero_mid_match, hero_low_match, hero_overpair, hero_set, hero_tp_kicker,
            hero_overcards, hero_undercards, hero_suits_on_board, straight_outs,
            b_high, b_mid, b_low, max(gap_top, gap_bot), total_gap, paired, monotone, twotone, connected, ace, broadway_count,
            # interactions:
            i_set_paired, i_set_mono, i_set_conn,
            i_op_paired, i_op_conn, i_op_bhigh,
            i_tp_paired, i_tp_kicker, i_tp_mono,
            i_mid_overcards, i_oc_conn, i_oc_paired,
            i_K_vs_A, i_set_top_match, i_air_conn, i_fd_potential,
        ]
        return feats
    except (ValueError, IndexError):
        return None


FEATURE_NAMES = [
    "a_r","b_r","hero_pair","hero_suited","hero_gap","hero_high_A","hero_high_K","hero_broadway","hero_low",
    "hero_top_match","hero_mid_match","hero_low_match","hero_overpair","hero_set","hero_tp_kicker",
    "hero_overcards","hero_undercards","hero_suits_on_board","straight_outs",
    "b_high","b_mid","b_low","max_gap","total_gap","paired","monotone","twotone","connected","ace","broadway_count",
    "i_set_paired","i_set_mono","i_set_conn",
    "i_op_paired","i_op_conn","i_op_bhigh",
    "i_tp_paired","i_tp_kicker","i_tp_mono",
    "i_mid_overcards","i_oc_conn","i_oc_paired",
    "i_K_vs_A","i_set_top_match","i_air_conn","i_fd_potential",
]

print("Loading rows...")
X_list = []; y_list = []
n_read = 0; n_skipped = 0
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        n_read += 1
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        eq_b = r.get("equity_bucket", "")
        if not ca or not cb or eq_b not in EQ_LABEL_TO_IDX:
            n_skipped += 1; continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: n_skipped += 1; continue
        feats = extract_features(ca, cb, board)
        if feats is None: n_skipped += 1; continue
        X_list.append(feats)
        y_list.append(EQ_LABEL_TO_IDX[eq_b])

X = np.array(X_list, dtype=np.float32)
y = np.array(y_list, dtype=np.int8)
print(f"Loaded {len(X):,} rows, dim={X.shape[1]}")


def predict_eq(coeffs, intercept, X, t_weak, t_good, t_best):
    scores = X @ coeffs + intercept
    preds = np.zeros(len(scores), dtype=np.int8)
    preds = np.where(scores >= t_weak, 1, preds)
    preds = np.where(scores >= t_good, 2, preds)
    preds = np.where(scores >= t_best, 3, preds)
    return preds


def objective(trial):
    coeffs = np.array([trial.suggest_float(f"w_{name}", -3.0, 3.0) for name in FEATURE_NAMES], dtype=np.float32)
    intercept = trial.suggest_float("intercept", -15.0, 15.0)
    t_weak = trial.suggest_float("t_weak", -20.0, 10.0)
    t_good = trial.suggest_float("t_good", t_weak + 0.1, 15.0)
    t_best = trial.suggest_float("t_best", t_good + 0.1, 25.0)
    preds = predict_eq(coeffs, intercept, X, t_weak, t_good, t_best)
    return float((preds == y).mean() * 100)


print(f"\n=== Optuna 45-feature optimization (500 trials) ===")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=500, show_progress_bar=True)

best = study.best_params
print(f"\nBest accuracy: {study.best_value:.2f}%")
weighted = [(name, best[f"w_{name}"]) for name in FEATURE_NAMES]
weighted.sort(key=lambda x: -abs(x[1]))
print(f"\nTop 20 features by |weight|:")
for name, w in weighted[:20]:
    marker = " ★" if name.startswith("i_") else ""
    print(f"  {name:24} = {w:+.3f}{marker}")

# Integer version
int_coeffs = np.array([round(best[f"w_{name}"]) for name in FEATURE_NAMES], dtype=np.float32)
int_intercept = round(best["intercept"])
int_tw = round(best["t_weak"]); int_tg = max(int_tw+1, round(best["t_good"]))
int_tb = max(int_tg+1, round(best["t_best"]))
preds_int = predict_eq(int_coeffs, int_intercept, X, int_tw, int_tg, int_tb)
acc_int = float((preds_int == y).mean() * 100)
print(f"\nInteger: acc={acc_int:.2f}%, intercept={int_intercept}, t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")
print(f"Integer top |w|>=1:")
for name, w in zip(FEATURE_NAMES, int_coeffs):
    if abs(w) >= 1:
        marker = " ★" if name.startswith("i_") else ""
        print(f"  {name:24} = {int(w):+d}{marker}")

# Report
lines = []
lines.append("# eq 計算式 v3 — 45 特徴量 (interaction 15 含む)")
lines.append("")
lines.append("## 性能")
lines.append("")
lines.append(f"| variant | accuracy |")
lines.append(f"|---|---:|")
lines.append(f"| **45-feature 連続** | **{study.best_value:.2f}%** |")
lines.append(f"| 45-feature 整数 | {acc_int:.2f}% |")
lines.append(f"| (参考) 30-feature 線形 | 52.18% |")
lines.append(f"| (参考) 8-feature 線形 | 58.84% |")
lines.append(f"| (参考) 24-cell grid | 58.0% |")
lines.append("")

lines.append("## 上位特徴量 (連続係数 |w| 順)")
lines.append("")
lines.append("| 特徴量 | 連続 | 整数 | interaction? |")
lines.append("|---|---:|---:|---|")
for name, w in weighted[:25]:
    iw = round(w)
    is_interact = "★ inter" if name.startswith("i_") else "-"
    lines.append(f"| {name} | {w:+.3f} | {iw:+d} | {is_interact} |")
lines.append(f"| **intercept** | {best['intercept']:+.3f} | {int_intercept:+d} | - |")
lines.append("")
lines.append(f"閾値: t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
