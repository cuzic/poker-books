"""eq_bucket 予測の non-linear モデル — Decision Tree / Random Forest / GBM。

【目的】 線形の限界 (60%) を非線形で超えられるか確認。
- DT depth 別 accuracy (3, 5, 7, 10, unlimited)
- Random Forest (100 trees)
- Gradient Boosting (100 estimators)

【特徴量】 既に作った 30 features + 15 interaction = 45
"""
from __future__ import annotations
import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_DECISION_TREE.md"

RANKS = "23456789TJQKA"
EQ_LABEL_TO_IDX = {"trash_hands":0, "weak_hands":1, "good_hands":2, "best_hands":3}

MV_TIER_MAP = {
    "fullhouse":0,"quads":0,"straight_flush":0,
    "set":1,"trips":1,"straight":1,"flush":1,
    "two_pair":2,
    "top_pair":3,"overpair":3,
    "second_pair":4,"third_pair":4,"underpair":4,"low_pair":4,
    "no_made_hand":5,"king_high":5,"ace_high":5,
}
DV_BASE = {"combo_draw":4,"nut_flush_draw":3,"flush_draw":3,"oesd":3,"gutshot":1,
           "twocards_bdfd":1,"onecard_bdfd":0,"no_draw":0}
OPP_R = {"SRP":0,"DEF":1,"3BP":2,"4BP":3}


def parse_pot(scn):
    s = scn.lower()
    return "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
           "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"


def features(card_a, card_b, board, mv_cat, dv_cat, opp_r):
    try:
        a_r = RANKS.index(card_a[0].upper()); a_s = card_a[1].lower()
        b_r = RANKS.index(card_b[0].upper()); b_s = card_b[1].lower()
        if a_r < b_r: a_r, b_r = b_r, a_r; a_s, b_s = b_s, a_s

        bc = [(RANKS.index(board[i*2:i*2+2][0].upper()), board[i*2:i*2+2][1].lower())
              for i in range(len(board) // 2)]
        b_ranks = sorted([r for r, _ in bc], reverse=True)
        b_suits = [s for _, s in bc]
        b_high = b_ranks[0]; b_mid = b_ranks[1] if len(b_ranks)>1 else 0
        b_low = b_ranks[2] if len(b_ranks)>2 else 0

        paired = 1 if (b_ranks[0]==b_ranks[1]) or (len(b_ranks)>2 and b_ranks[1]==b_ranks[2]) else 0
        monotone = 1 if len(set(b_suits))==1 else 0
        twotone = 1 if len(set(b_suits))==2 else 0
        connected = 1 if (b_high-b_mid <=2 and b_mid-b_low <=2 and not paired) else 0
        ace = 1 if b_high == 12 else 0
        broadway_count = sum(1 for r in b_ranks if r >= 8)

        hero_pair = 1 if a_r == b_r else 0
        hero_suited = 1 if a_s == b_s else 0
        hero_gap = a_r - b_r
        hero_high_A = 1 if a_r == 12 else 0
        hero_high_K = 1 if a_r == 11 else 0
        hero_top_match = 1 if (a_r == b_high or b_r == b_high) else 0
        hero_mid_match = 1 if (a_r == b_mid or b_r == b_mid) else 0
        hero_low_match = 1 if (a_r == b_low or b_r == b_low) else 0
        hero_overpair = 1 if (hero_pair and a_r > b_high) else 0
        hero_set = 1 if (hero_pair and a_r in (b_high, b_mid, b_low)) else 0
        hero_overcards = sum(1 for r in (a_r,b_r) if r > b_high)
        hero_undercards = sum(1 for r in (a_r,b_r) if r < b_low)
        hero_suits_on_board = sum(1 for r,s in bc if s in (a_s, b_s))

        mv_idx = MV_TIER_MAP.get(mv_cat, 5)
        dv_v = DV_BASE.get(dv_cat, 0)

        return [
            mv_idx, dv_v, opp_r,
            a_r, b_r, hero_pair, hero_suited, hero_gap,
            hero_high_A, hero_high_K,
            hero_top_match, hero_mid_match, hero_low_match,
            hero_overpair, hero_set, hero_overcards, hero_undercards,
            hero_suits_on_board,
            b_high, b_mid, b_low, paired, monotone, twotone, connected, ace, broadway_count,
        ]
    except (ValueError, IndexError):
        return None


print("Loading rows...")
X_list = []; y_list = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        mv = r.get("mv_cat", ""); dv = r.get("dv_cat", "no_draw")
        eq_b = r.get("equity_bucket", "")
        if eq_b not in EQ_LABEL_TO_IDX or mv not in MV_TIER_MAP: continue
        ca = r.get("card_a", ""); cb = r.get("card_b", "")
        if not ca or not cb: continue
        board = r.get("board_str", "")[:6].lower()
        if len(board) < 6: continue
        opp_r = OPP_R[parse_pot(r["scenario_id"])]
        feats = features(ca, cb, board, mv, dv, opp_r)
        if feats is None: continue
        X_list.append(feats)
        y_list.append(EQ_LABEL_TO_IDX[eq_b])

X = np.array(X_list, dtype=np.float32)
y = np.array(y_list, dtype=np.int8)
N = len(X)
print(f"Loaded {N:,} rows, dim={X.shape[1]}")


# Train/val split (80/20)
np.random.seed(42)
perm = np.random.permutation(N)
split = int(N * 0.8)
train_idx = perm[:split]; val_idx = perm[split:]
X_tr, y_tr = X[train_idx], y[train_idx]
X_va, y_va = X[val_idx], y[val_idx]
print(f"Train: {len(X_tr):,}, Val: {len(X_va):,}")


from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

results = []

print("\n=== Decision Tree (depth 別) ===")
for depth in [3, 5, 7, 10, 15, None]:
    dt = DecisionTreeClassifier(max_depth=depth, random_state=42)
    dt.fit(X_tr, y_tr)
    tr_acc = dt.score(X_tr, y_tr) * 100
    va_acc = dt.score(X_va, y_va) * 100
    print(f"  depth={str(depth):>5}: train={tr_acc:.2f}%, val={va_acc:.2f}%, n_leaves={dt.get_n_leaves()}")
    results.append((f"DT depth={depth}", tr_acc, va_acc, dt.get_n_leaves()))

print("\n=== Random Forest (100 trees) ===")
for max_depth in [5, 10, None]:
    rf = RandomForestClassifier(n_estimators=100, max_depth=max_depth, n_jobs=-1, random_state=42)
    rf.fit(X_tr, y_tr)
    tr_acc = rf.score(X_tr, y_tr) * 100
    va_acc = rf.score(X_va, y_va) * 100
    print(f"  depth={str(max_depth):>5}: train={tr_acc:.2f}%, val={va_acc:.2f}%")
    results.append((f"RF depth={max_depth}", tr_acc, va_acc, 100))

print("\n=== Gradient Boosting (100 estimators) ===")
gbm = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
gbm.fit(X_tr, y_tr)
tr_acc = gbm.score(X_tr, y_tr) * 100
va_acc = gbm.score(X_va, y_va) * 100
print(f"  depth=3, n_est=100: train={tr_acc:.2f}%, val={va_acc:.2f}%")
results.append(("GBM depth=3 n=100", tr_acc, va_acc, 100))

# Feature importance (RF)
print("\n=== Random Forest feature importance ===")
rf = RandomForestClassifier(n_estimators=100, max_depth=None, n_jobs=-1, random_state=42)
rf.fit(X_tr, y_tr)
FEATURE_NAMES = [
    "mv_idx","dv","opp_r",
    "a_r","b_r","hero_pair","hero_suited","hero_gap",
    "hero_high_A","hero_high_K",
    "hero_top_match","hero_mid_match","hero_low_match",
    "hero_overpair","hero_set","hero_overcards","hero_undercards",
    "hero_suits_on_board",
    "b_high","b_mid","b_low","paired","monotone","twotone","connected","ace","broadway_count",
]
importance = sorted(zip(FEATURE_NAMES, rf.feature_importances_), key=lambda x: -x[1])
for name, imp in importance[:15]:
    print(f"  {name:20} = {imp:.3f}")


# Report
lines = []
lines.append("# eq_bucket 予測 — Decision Tree / Random Forest / GBM")
lines.append("")
lines.append("線形モデル (60% 限界) を非線形で超えられるか検証。")
lines.append("")
lines.append("## 結果 (Train / Validation)")
lines.append("")
lines.append("| モデル | train | val | n_leaves/trees |")
lines.append("|--------|---:|---:|---:|")
for name, tr, va, n in results:
    lines.append(f"| {name} | {tr:.2f}% | {va:.2f}% | {n} |")
lines.append("")
lines.append("## 比較 (val accuracy)")
lines.append("")
lines.append("| 方式 | val accuracy |")
lines.append("|------|---:|")
linear_best = 60.42  # eq_grid_plus_linear
lines.append(f"| Decision Tree (depth 3) | {[r for r in results if 'depth=3' in r[0] and 'DT' in r[0]][0][2]:.2f}% |")
lines.append(f"| Decision Tree (depth 5) | {[r for r in results if 'depth=5' in r[0] and 'DT' in r[0]][0][2]:.2f}% |")
lines.append(f"| Decision Tree (depth 10) | {[r for r in results if 'depth=10' in r[0] and 'DT' in r[0]][0][2]:.2f}% |")
lines.append(f"| Decision Tree (unlimited) | {[r for r in results if 'depth=None' in r[0] and 'DT' in r[0]][0][2]:.2f}% |")
lines.append(f"| Random Forest (100 trees) | {[r for r in results if 'RF depth=None' in r[0]][0][2]:.2f}% |")
lines.append(f"| Gradient Boosting | {results[-1][2]:.2f}% |")
lines.append(f"| (参考) 線形最高 (grid+linear) | {linear_best:.2f}% |")
lines.append("")

lines.append("## Random Forest の feature importance (上位 15)")
lines.append("")
lines.append("| feature | importance |")
lines.append("|---------|---:|")
for name, imp in importance[:15]:
    lines.append(f"| {name} | {imp:.3f} |")
lines.append("")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
