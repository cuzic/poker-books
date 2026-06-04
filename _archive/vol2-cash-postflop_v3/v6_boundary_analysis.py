"""
v6_boundary_analysis.py — v6 パラメータでの境界ハンド分析

v6 ALL最適係数で各シナリオの誤分類ハンドを調べ、
追加因子（Broadway bonus, 3-gap以上のペナルティ強化, etc.）の
効果を検討する。
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

GTO_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json')

_RANKS = '23456789TJQKA'
_RANK  = {r: v for v, r in enumerate(_RANKS, 2)}

def all_169():
    hands = [f'{r}{r}' for r in _RANKS]
    for i in range(len(_RANKS)-1, -1, -1):
        for j in range(i-1, -1, -1):
            hi, lo = _RANKS[i], _RANKS[j]
            hands += [f'{hi}{lo}s', f'{hi}{lo}o']
    return hands

def parse(h: str):
    if len(h) == 2:
        r = _RANK[h[0]]
        return r, r, False, True
    a, b = _RANK[h[0]], _RANK[h[1]]
    return max(a,b), min(a,b), h.endswith('s'), False

HANDS = all_169()

# v6 ALL最適パラメータ
V6 = dict(suit_bonus=5, k_blocker=0, a_blocker=2,
          low_pen=4, a_gap_cap=6, k_gap_cap=3, pair_bonus=14)

def score_v6(hand: str, p: dict = V6) -> float:
    H, L, suited, pair = parse(hand)
    if pair:
        return H + L + p['pair_bonus']
    gap = H - L - 1
    ab  = p['a_blocker'] if H == 14 else 0.0
    kb  = p['k_blocker'] if H == 13 else 0.0
    if suited:
        if H == 14:   gc = 0
        elif H == 13: gc = min(gap, 2)
        elif H == 12: gc = min(gap, 3)
        elif H == 11: gc = min(gap, 4)
        else:         gc = gap
        return H + L + p['suit_bonus'] - gc + ab + kb
    # offsuit
    if H == 14:
        gc = min(gap, p['a_gap_cap'])
        lp = 0.0
    elif H == 13:
        gc = min(gap, p['k_gap_cap'])
        lp = p['low_pen'] if L < 10 else 0.0
    else:
        gc = gap
        lp = p['low_pen'] if L < 10 else 0.0
    return H + L - gc - lp + ab + kb

with open(GTO_PATH) as f:
    GTO = json.load(f)

def gset(key, action):
    return set(GTO[key]['actions'].get(action, []))

def build_scenarios():
    s = {}
    for k in ['LJ_RFI','HJ_RFI','CO_RFI','BTN_RFI']:
        s[k] = {'play': gset(k,'raise'), 'label': 'RFI'}
    s['SB_RFI'] = {'play': gset('BvB_SB_strategy','raise')
                         | gset('BvB_SB_strategy','limp')
                         | gset('BvB_SB_strategy','mixed_limp'),
                   'label': 'SB_RFI'}
    for k in ['HJ_vs_LJ','CO_vs_LJ','CO_vs_HJ','BTN_vs_LJ','BTN_vs_HJ','BTN_vs_CO']:
        s[k] = {'play': gset(k,'raise') | gset(k,'limp'), 'label': 'DEF_IP'}
    for k in ['SB_vs_LJ','SB_vs_HJ','SB_vs_CO','SB_vs_BTN']:
        s[k] = {'play': gset(k,'raise'), 'label': 'DEF_OOP'}
    for k in ['BB_vs_LJ','BB_vs_HJ','BB_vs_CO','BB_vs_BTN','BvB_BB_vs_SB_raise']:
        s[k] = {'play': gset(k,'raise') | gset(k,'limp'), 'label': 'DEF_BB'}
    return s

ALL_SCENARIOS = build_scenarios()

# ============================================================
# 最適閾値を求める
# ============================================================
def find_best_threshold(scenario_key: str, p: dict = V6) -> tuple[float, float]:
    gt = ALL_SCENARIOS[scenario_key]['play']
    best_t, best_a = 10.0, 0.0
    t = 10.0
    while t <= 44.0:
        correct = sum(1 for h in HANDS if (score_v6(h, p) >= t) == (h in gt))
        a = correct / len(HANDS)
        if a > best_a:
            best_a, best_t = a, t
        t += 0.5
    return best_t, best_a * 100

# ============================================================
# 誤分類ハンドを取得
# ============================================================
def get_errors(scenario_key: str, p: dict = V6):
    gt = ALL_SCENARIOS[scenario_key]['play']
    t, acc = find_best_threshold(scenario_key, p)
    fp = []  # false positive: GTO fold だが score >= t
    fn = []  # false negative: GTO play だが score < t
    for h in HANDS:
        s = score_v6(h, p)
        in_gt = h in gt
        predicted = s >= t
        if predicted and not in_gt:
            fp.append((h, s))
        elif not predicted and in_gt:
            fn.append((h, s))
    return t, acc, fp, fn

print("=" * 70)
print("v6 ALL最適パラメータ での境界ハンド分析")
print("=" * 70)
print(f"パラメータ: {V6}\n")

# ============================================================
# シナリオ別誤分類
# ============================================================
# 全シナリオでの誤分類頻度をカウント
fp_count = defaultdict(int)
fn_count = defaultdict(int)
scenario_results = {}

for key, info in ALL_SCENARIOS.items():
    t, acc, fp, fn = get_errors(key)
    scenario_results[key] = (t, acc, fp, fn)
    for h, _ in fp:
        fp_count[h] += 1
    for h, _ in fn:
        fn_count[h] += 1

# 頻出誤分類ハンド
print("【False Positive (予測:play, GTO:fold) 頻出ハンド】")
fp_sorted = sorted(fp_count.items(), key=lambda x: -x[1])
for h, cnt in fp_sorted[:20]:
    s = score_v6(h)
    H, L, suited, pair = parse(h)
    gap = H - L - 1 if not pair else 0
    print(f"  {h:6s}  score={s:.0f}  cnt={cnt}/20  gap={gap}")

print()
print("【False Negative (予測:fold, GTO:play) 頻出ハンド】")
fn_sorted = sorted(fn_count.items(), key=lambda x: -x[1])
for h, cnt in fn_sorted[:20]:
    s = score_v6(h)
    H, L, suited, pair = parse(h)
    gap = H - L - 1 if not pair else 0
    print(f"  {h:6s}  score={s:.0f}  cnt={cnt}/20  gap={gap}")

# ============================================================
# RFI カテゴリ詳細
# ============================================================
print()
print("=" * 70)
print("【RFI カテゴリ詳細誤分類】")
rfi_keys = ['LJ_RFI','HJ_RFI','CO_RFI','BTN_RFI']
for key in rfi_keys:
    t, acc, fp, fn = scenario_results[key]
    print(f"\n  {key} (閾値={t}, 精度={acc:.1f}%)")
    if fn:
        print(f"    FN (GTOでplay→v6でfold): {[h for h,_ in fn]}")
    if fp:
        print(f"    FP (GTOでfold→v6でplay): {[h for h,_ in fp[:10]]}")

# ============================================================
# BB カテゴリ詳細
# ============================================================
print()
print("=" * 70)
print("【DEF_BB カテゴリ詳細誤分類】")
bb_keys = ['BB_vs_LJ','BB_vs_HJ','BB_vs_CO','BB_vs_BTN','BvB_BB_vs_SB_raise']
for key in bb_keys:
    t, acc, fp, fn = scenario_results[key]
    print(f"\n  {key} (閾値={t}, 精度={acc:.1f}%)")
    if fn:
        print(f"    FN (GTOでplay→v6でfold): {[h for h,_ in fn]}")
    if fp:
        print(f"    FP (GTOでfold→v6でplay): {[h for h,_ in fp[:10]]}")

# ============================================================
# SB 詳細（問題の多いカテゴリ）
# ============================================================
print()
print("=" * 70)
print("【SB_RFI 詳細誤分類】")
key = 'SB_RFI'
t, acc, fp, fn = scenario_results[key]
gt = ALL_SCENARIOS[key]['play']
print(f"  閾値={t}, 精度={acc:.1f}%")
print(f"  GTO play手数: {len(gt)}")
print(f"  FN数: {len(fn)}, FP数: {len(fp)}")
if fn:
    fn_by_score = sorted(fn, key=lambda x: -x[1])
    print(f"  FN上位 (GTOでplay→v6でfold): {[h for h,_ in fn_by_score[:15]]}")
if fp:
    fp_by_score = sorted(fp, key=lambda x: x[1])
    print(f"  FP下位 (GTOでfold→v6でplay): {[h for h,_ in fp_by_score[:15]]}")

# SBのlimp専用ハンドを特定
raise_hands = gset('BvB_SB_strategy', 'raise')
limp_hands  = gset('BvB_SB_strategy', 'limp') | gset('BvB_SB_strategy', 'mixed_limp')
limp_only   = limp_hands - raise_hands
print(f"\n  SB limp専用ハンド ({len(limp_only)}手): {sorted(limp_only)[:20]}")

# ============================================================
# ハンドカテゴリ別傾向
# ============================================================
print()
print("=" * 70)
print("【誤分類パターン分析】")

# offsuit FN ハンドのgap分布
fn_offsuit = [(h, fp_count[h]+fn_count[h]) for h in HANDS
              if not parse(h)[2] and not parse(h)[3] and fn_count[h] >= 3]
fn_offsuit.sort(key=lambda x: -x[1])
print("\n  FN多発 オフスーツハンド (3シナリオ以上でfold誤分類):")
for h, total in fn_offsuit[:15]:
    H, L, suited, pair = parse(h)
    gap = H-L-1
    s = score_v6(h)
    print(f"    {h:6s} gap={gap} score={s:.0f} fn_cnt={fn_count[h]}")

# suited FP ハンドのgap分布
fp_suited = [(h, fp_count[h]) for h in HANDS
             if parse(h)[2] and not parse(h)[3] and fp_count[h] >= 3]
fp_suited.sort(key=lambda x: -x[1])
print("\n  FP多発 スーツドハンド (3シナリオ以上でplay誤分類):")
for h, cnt in fp_suited[:15]:
    H, L, suited, pair = parse(h)
    gap = H-L-1
    s = score_v6(h)
    print(f"    {h:6s} gap={gap} score={s:.0f} fp_cnt={cnt}")

