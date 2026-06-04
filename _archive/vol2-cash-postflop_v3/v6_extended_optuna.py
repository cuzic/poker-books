"""
v6_extended_optuna.py — 追加ファクターの効果検証

現行 v6 の問題点:
  1. A-suited 大ギャップ (A2s-A8s) が FP 多発
     → A-suited にも gap cap を追加
  2. 小スーツドコネクター (43s-76s) が FN 多発
     → connected bonus (gap=0,1 の suited に +N) を追加

新パラメータ:
  a_suited_gap_cap : A スーツドの gap キャップ (0=現行 = 無制限)
  conn_bonus       : gap=0 スーツドコネクターへのボーナス
  conn1_bonus      : gap=1 スーツドコネクターへのボーナス
  low_high_cap     : H<=9 のスーツドで gc=min(gap, N) (現行=full gap)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json')
N_TRIALS = 600

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

def score_ext(hand: str, p: dict) -> float:
    H, L, suited, pair = parse(hand)
    if pair:
        return H + L + p['pair_bonus']
    gap = H - L - 1
    ab  = p['a_blocker'] if H == 14 else 0.0
    kb  = p['k_blocker'] if H == 13 else 0.0

    if suited:
        # A suited: cap at a_suited_gap_cap
        if H == 14:
            gc = min(gap, p['a_suited_gap_cap'])
        elif H == 13:
            gc = min(gap, 2)
        elif H == 12:
            gc = min(gap, 3)
        elif H == 11:
            gc = min(gap, 4)
        else:
            # 小カード (H<=10): low_high_cap でキャップ
            gc = min(gap, p['low_high_cap'])
        # connector bonus
        cb = p['conn_bonus'] if gap == 0 else (p['conn1_bonus'] if gap == 1 else 0)
        return H + L + p['suit_bonus'] - gc + ab + kb + cb

    # offsuit (既存ロジック維持)
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
ALL_KEYS = list(ALL_SCENARIOS.keys())

CATEGORY_KEYS = {
    'RFI':     [k for k,v in ALL_SCENARIOS.items() if v['label']=='RFI'],
    'DEF_IP':  [k for k,v in ALL_SCENARIOS.items() if v['label']=='DEF_IP'],
    'DEF_OOP': [k for k,v in ALL_SCENARIOS.items() if v['label']=='DEF_OOP'],
    'DEF_BB':  [k for k,v in ALL_SCENARIOS.items() if v['label']=='DEF_BB'],
    'ALL':     ALL_KEYS,
}

def best_acc_fn(score_fn, gt: set) -> float:
    best = -1.0
    t = 10.0
    while t <= 44.0:
        correct = sum(1 for h in HANDS if (score_fn(h) >= t) == (h in gt))
        a = correct / len(HANDS)
        if a > best: best = a
        t += 0.5
    return best * 100

def category_acc(keys, p):
    fn = lambda h: score_ext(h, p)
    return sum(best_acc_fn(fn, ALL_SCENARIOS[k]['play']) for k in keys) / len(keys)

# v6 ベースライン
V6 = dict(suit_bonus=5, k_blocker=0, a_blocker=2,
          low_pen=4, a_gap_cap=6, k_gap_cap=3, pair_bonus=14,
          a_suited_gap_cap=0, conn_bonus=0, conn1_bonus=0, low_high_cap=99)

def make_objective_ext(keys):
    def objective(trial):
        p = {
            'suit_bonus':        trial.suggest_int('suit_bonus', 3, 8),
            'k_blocker':         trial.suggest_int('k_blocker',  0, 2),
            'a_blocker':         trial.suggest_int('a_blocker',  1, 4),
            'low_pen':           trial.suggest_int('low_pen',    0, 5),
            'a_gap_cap':         trial.suggest_int('a_gap_cap',  0, 8),
            'k_gap_cap':         trial.suggest_int('k_gap_cap',  0, 8),
            'pair_bonus':        trial.suggest_int('pair_bonus', 8, 16),
            # 新パラメータ
            'a_suited_gap_cap':  trial.suggest_int('a_suited_gap_cap', 0, 8),
            'conn_bonus':        trial.suggest_int('conn_bonus',       0, 4),
            'conn1_bonus':       trial.suggest_int('conn1_bonus',      0, 3),
            'low_high_cap':      trial.suggest_int('low_high_cap',     1, 6),
        }
        return category_acc(keys, p)
    return objective

def optimize_ext(cat_name, keys):
    study = optuna.create_study(direction='maximize',
                                sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(make_objective_ext(keys), n_trials=N_TRIALS, show_progress_bar=False)
    return study.best_params, study.best_value

print(f"Optuna extended, n_trials={N_TRIALS} per category\n")
print(f"v6 baseline ALL: {category_acc(ALL_KEYS, V6):.1f}%\n")

results = {}
for cat, keys in CATEGORY_KEYS.items():
    if cat == 'SB_RFI': continue  # skip — structural limit
    sys.stdout.write(f'  最適化中: {cat} ({len(keys)} scenarios)... ')
    sys.stdout.flush()
    best_p, best_a = optimize_ext(cat, keys)
    v6_a = category_acc(keys, V6)
    results[cat] = (best_p, best_a, v6_a)
    delta = best_a - v6_a
    print(f'v6={v6_a:.1f}%  best={best_a:.1f}%  Δ={delta:+.1f}%')

# 全カテゴリ結果表示
print('\n' + '='*80)
print('カテゴリ別 改善')
print('='*80)
for cat, (best_p, best_a, v6_a) in results.items():
    print(f'\n{cat} ({v6_a:.1f}% → {best_a:.1f}%, Δ={best_a-v6_a:+.1f}%)')
    # 新パラメータのみ表示
    for pk in ['a_suited_gap_cap','conn_bonus','conn1_bonus','low_high_cap',
               'suit_bonus','pair_bonus','a_blocker','low_pen','a_gap_cap','k_gap_cap']:
        v = best_p.get(pk, V6.get(pk, 'N/A'))
        v6v = V6.get(pk, '?')
        diff = v - v6v if isinstance(v6v, int) else 0
        new_flag = ' ★NEW★' if pk in ['a_suited_gap_cap','conn_bonus','conn1_bonus','low_high_cap'] else ''
        d_str = f'({diff:+d})' if diff != 0 else '     '
        print(f'  {pk:<20} = {v:3d} {d_str}{new_flag}')

# ALL 推奨
all_p = results['ALL'][0]
print('\n\n推奨 v6+ パラメータ (ALL 最適):')
for pk in ['suit_bonus','k_blocker','a_blocker','low_pen','a_gap_cap','k_gap_cap','pair_bonus',
           'a_suited_gap_cap','conn_bonus','conn1_bonus','low_high_cap']:
    v = all_p[pk]
    v6v = V6[pk]
    d = v - v6v
    note = f'  (v6から{d:+d})' if d != 0 else '  (変化なし)'
    marker = ' ← NEW' if pk in ['a_suited_gap_cap','conn_bonus','conn1_bonus','low_high_cap'] else ''
    print(f'  {pk:<22} = {v}{note}{marker}')

