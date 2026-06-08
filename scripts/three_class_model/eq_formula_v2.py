"""eq 計算式 v2 — 30+ 派生特徴量 + optuna 最適化。

【新特徴量】(card_a, card_b, board_str から計算)

A. Hero hand 特徴 (15+):
 1. hero_rank_high      (0-12) 最高 rank
 2. hero_rank_low       (0-12) 最低 rank
 3. hero_pair           (0/1) pocket pair
 4. hero_suited         (0/1) suited
 5. hero_gap            rank_high - rank_low
 6. hero_high_is_A      1 if A 含む
 7. hero_high_is_K      1 if K 含む
 8. hero_broadway       1 if both T+
 9. hero_low            1 if both ≤5

B. Hero vs board overlap (10+):
10. hero_top_overlap   pair が board top と一致 (TP)
11. hero_mid_overlap   pair が board mid と一致 (2nd P)
12. hero_low_overlap   pair が board low と一致 (3rd P)
13. hero_overpair      pocket pair > board high
14. hero_set_match     pocket pair が board のいずれかと一致 (set)
15. hero_tp_kicker     TP のときの kicker rank (0-12)
16. hero_overcards_count   board より高い hero card 数
17. hero_undercards_count  board より低い hero card 数
18. hero_FD_potential  hero と board の同 suit カード数 (3=flush, 2=FD)
19. hero_straight_outs  straight 完成までの outs (簡易)

C. Board feat (10+):
20. board_high_rank    (0-12)
21. board_mid_rank
22. board_low_rank
23. board_max_gap
24. board_total_gap    gap1 + gap2
25. board_paired       0/1
26. board_monotone     0/1
27. board_twotone      0/1
28. board_connected    0/1
29. board_ace          A 含む
30. board_broadway_count   T+ 数

【ターゲット】eq_bucket (best=3, good=2, weak=1, trash=0)
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np
import optuna

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_FORMULA_V2.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}


def rank_idx(c: str) -> int:
    return RANKS.index(c[0].upper())


def suit_of(c: str) -> str:
    return c[1].lower()


def extract_features(card_a: str, card_b: str, board: str) -> list:
    """Return 30+ features. card_a, card_b like '7s', board like 'Ks7d2c'."""
    try:
        a_r = rank_idx(card_a); a_s = suit_of(card_a)
        b_r = rank_idx(card_b); b_s = suit_of(card_b)
        # ensure a_r >= b_r
        if a_r < b_r:
            a_r, b_r = b_r, a_r
            a_s, b_s = b_s, a_s

        # Board: 3 cards (flop) or more
        bc = [(rank_idx(board[i*2:i*2+2]), suit_of(board[i*2:i*2+2])) for i in range(len(board) // 2)]
        b_ranks = sorted([r for r, _ in bc], reverse=True)
        b_suits = [s for _, s in bc]
        b_high = b_ranks[0]
        b_mid = b_ranks[1] if len(b_ranks) > 1 else 0
        b_low = b_ranks[2] if len(b_ranks) > 2 else 0

        paired = 1 if (len(b_ranks) > 1 and b_ranks[0] == b_ranks[1]) or \
                       (len(b_ranks) > 2 and b_ranks[1] == b_ranks[2]) else 0
        monotone = 1 if len(set(b_suits)) == 1 else 0
        twotone = 1 if len(set(b_suits)) == 2 else 0
        gap_top = b_high - b_mid; gap_bot = b_mid - b_low
        max_gap = max(gap_top, gap_bot)
        total_gap = gap_top + gap_bot
        connected = 1 if (gap_top <= 2 and gap_bot <= 2 and not paired) else 0
        ace = 1 if b_high == 12 else 0
        broadway_count = sum(1 for r in b_ranks if r >= 8)

        # Hero features
        hero_pair = 1 if a_r == b_r else 0
        hero_suited = 1 if a_s == b_s else 0
        hero_gap = a_r - b_r
        hero_high_A = 1 if a_r == 12 else 0
        hero_high_K = 1 if a_r == 11 else 0
        hero_broadway = 1 if (a_r >= 8 and b_r >= 8) else 0
        hero_low = 1 if (a_r <= 3 and b_r <= 3) else 0  # both ≤5

        # Overlap with board
        hero_top_match = 1 if (a_r == b_high or b_r == b_high) else 0
        hero_mid_match = 1 if (a_r == b_mid or b_r == b_mid) else 0
        hero_low_match = 1 if (a_r == b_low or b_r == b_low) else 0
        hero_overpair = 1 if (hero_pair and a_r > b_high) else 0
        hero_set = 1 if (hero_pair and a_r in (b_high, b_mid, b_low)) else 0
        hero_tp_kicker = (b_r if hero_top_match and a_r == b_high else 0)
        # overcards count
        hero_overcards = sum(1 for r in (a_r, b_r) if r > b_high)
        hero_undercards = sum(1 for r in (a_r, b_r) if r < b_low)
        # FD potential
        hero_suits_on_board = sum(1 for r, s in bc if s in (a_s, b_s))
        # straight outs approx (simplified)
        all_ranks = sorted({a_r, b_r} | set(b_ranks))
        straight_outs = 0
        for r in range(13):
            if r in all_ranks: continue
            test = sorted(all_ranks + [r])
            # check any 5 consecutive
            for i in range(len(test) - 4):
                if test[i+4] - test[i] == 4: straight_outs += 1; break

        return [
            a_r, b_r, hero_pair, hero_suited, hero_gap, hero_high_A, hero_high_K, hero_broadway, hero_low,
            hero_top_match, hero_mid_match, hero_low_match, hero_overpair, hero_set, hero_tp_kicker,
            hero_overcards, hero_undercards, hero_suits_on_board, straight_outs,
            b_high, b_mid, b_low, max_gap, total_gap, paired, monotone, twotone, connected, ace, broadway_count,
        ]
    except (ValueError, IndexError):
        return None


FEATURE_NAMES = [
    "a_r", "b_r", "hero_pair", "hero_suited", "hero_gap",
    "hero_high_A", "hero_high_K", "hero_broadway", "hero_low",
    "hero_top_match", "hero_mid_match", "hero_low_match", "hero_overpair", "hero_set", "hero_tp_kicker",
    "hero_overcards", "hero_undercards", "hero_suits_on_board", "straight_outs",
    "b_high", "b_mid", "b_low", "max_gap", "total_gap", "paired", "monotone", "twotone", "connected", "ace", "broadway_count",
]

print("Loading rows and computing features...")
X_list = []
y_list = []
n_read = 0
n_skipped = 0
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        n_read += 1
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        eq_b = r.get("equity_bucket", "")
        if not ca or not cb or eq_b not in EQ_LABEL_TO_IDX:
            n_skipped += 1; continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6:
            n_skipped += 1; continue
        feats = extract_features(ca, cb, board)
        if feats is None:
            n_skipped += 1; continue
        X_list.append(feats)
        y_list.append(EQ_LABEL_TO_IDX[eq_b])

X = np.array(X_list, dtype=np.float32)
y = np.array(y_list, dtype=np.int8)
print(f"Loaded {len(X):,} rows ({n_skipped} skipped of {n_read} total)")
print(f"Feature dim: {X.shape[1]}")


# === Logistic-style scoring with optuna ===
def predict_eq(coeffs, intercept, X, t_weak, t_good, t_best):
    scores = X @ coeffs + intercept
    preds = np.zeros(len(scores), dtype=np.int8)
    preds = np.where(scores >= t_weak, 1, preds)
    preds = np.where(scores >= t_good, 2, preds)
    preds = np.where(scores >= t_best, 3, preds)
    return preds


def objective(trial):
    coeffs = np.array([trial.suggest_float(f"w_{name}", -3.0, 3.0) for name in FEATURE_NAMES], dtype=np.float32)
    intercept = trial.suggest_float("intercept", -10.0, 10.0)
    t_weak = trial.suggest_float("t_weak", -10.0, 5.0)
    t_good = trial.suggest_float("t_good", t_weak + 0.1, 10.0)
    t_best = trial.suggest_float("t_best", t_good + 0.1, 15.0)
    preds = predict_eq(coeffs, intercept, X, t_weak, t_good, t_best)
    acc = float((preds == y).mean() * 100)
    return acc


print("\n=== Optuna 30-feature optimization (300 trials) ===")
optuna.logging.set_verbosity(optuna.logging.WARNING)
study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=300, show_progress_bar=True)

best = study.best_params
print(f"\nBest accuracy: {study.best_value:.2f}%")
print(f"\nTop features by |weight|:")
weighted = [(name, best[f"w_{name}"]) for name in FEATURE_NAMES]
weighted.sort(key=lambda x: -abs(x[1]))
for name, w in weighted[:15]:
    print(f"  {name:22} = {w:+.3f}")
print(f"intercept = {best['intercept']:+.3f}")
print(f"t_weak={best['t_weak']:.2f}, t_good={best['t_good']:.2f}, t_best={best['t_best']:.2f}")


# === Integer version ===
print(f"\n=== Integer rounded ===")
int_coeffs = np.array([round(best[f"w_{name}"]) for name in FEATURE_NAMES], dtype=np.float32)
int_intercept = round(best["intercept"])
int_tw = round(best["t_weak"])
int_tg = max(int_tw + 1, round(best["t_good"]))
int_tb = max(int_tg + 1, round(best["t_best"]))
preds_int = predict_eq(int_coeffs, int_intercept, X, int_tw, int_tg, int_tb)
acc_int = float((preds_int == y).mean() * 100)
print(f"Integer accuracy: {acc_int:.2f}%")
print(f"Top integer features (|w|>=1):")
for name, w in zip(FEATURE_NAMES, int_coeffs):
    if abs(w) >= 1:
        print(f"  {name:22} = {int(w):+d}")
print(f"intercept = {int_intercept:+d}")
print(f"t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")


# Report
lines = []
lines.append("# eq 計算式 v2 — 30 特徴量 + optuna")
lines.append("")
lines.append(f"## 性能")
lines.append("")
lines.append(f"- 連続係数版: **{study.best_value:.2f}%**")
lines.append(f"- 整数係数版: **{acc_int:.2f}%**")
lines.append(f"- 参考: 8-feature 版 (前回): 58.84%")
lines.append(f"- 参考: 24-cell grid: 58.0%")
lines.append("")

lines.append("## 重要特徴量 (|weight| 上位)")
lines.append("")
lines.append("| 特徴量 | 連続係数 | 整数 |")
lines.append("|--------|---:|---:|")
for name, w in weighted[:20]:
    iw = round(w)
    lines.append(f"| {name} | {w:+.3f} | {iw:+d} |")
lines.append(f"| **intercept** | {best['intercept']:+.3f} | {int_intercept:+d} |")
lines.append("")
lines.append(f"閾値: t_weak={int_tw}, t_good={int_tg}, t_best={int_tb}")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
