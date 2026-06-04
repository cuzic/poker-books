"""
v7_mtt_compare.py — Cash vs MTT 係数比較

同じ Optuna フレームワークを Cash (gto-charts.json) と
MTT (mtt-gto-charts-SBR25.json) に対して走らせ、
係数が共通化できるかを検証する。

各データセットで最適化するカテゴリ:
  Cash: RFI(4) / BB(5) / IP(6) / OOP(4) / ALL(20)
  MTT:  RFI(6) / BB(6) / ALL(13)  ← IP/OOP はデータ不足
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

CASH_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json')
MTT_PATH  = Path('/home/cuzic/poker-books/knowledges/preflop/mtt-gto-charts-SBR25.json')
N_TRIALS  = 600

_RANKS = '23456789TJQKA'
_RANK  = {r: v for v, r in enumerate(_RANKS, 2)}

def all_169():
    hands = [f'{r}{r}' for r in _RANKS]
    for i in range(len(_RANKS)-1, -1, -1):
        for j in range(i-1, -1, -1):
            hi, lo = _RANKS[i], _RANKS[j]
            hands += [f'{hi}{lo}s', f'{hi}{lo}o']
    return hands

def parse(h):
    if len(h) == 2:
        r = _RANK[h[0]]
        return r, r, False, True
    a, b = _RANK[h[0]], _RANK[h[1]]
    return max(a,b), min(a,b), h.endswith('s'), False

HANDS = all_169()

def score(hand, p):
    H, L, suited, pair = parse(hand)
    if pair:
        return H + L + p['pair_bonus']
    gap = H - L - 1
    ab = p['a_blocker'] if H == 14 else 0.0
    kb = p['k_blocker'] if H == 13 else 0.0
    if suited:
        if H == 14:   gc = min(gap, p['a_suited_gap_cap'])
        elif H == 13: gc = min(gap, 2)
        elif H == 12: gc = min(gap, 3)
        elif H == 11: gc = min(gap, 4)
        else:         gc = min(gap, p['low_high_cap'])
        sc = p['suited_connector'] if gap == 0 else (p['suited_connector1'] if gap == 1 else 0)
        return H + L + p['suit_bonus'] - gc + ab + kb + sc
    if H == 14:
        gc = min(gap, p['a_gap_cap']); lp = 0.0
    elif H == 13:
        gc = min(gap, p['k_gap_cap']); lp = p['low_pen'] if L < 10 else 0.0
    else:
        gc = gap; lp = p['low_pen'] if L < 10 else 0.0
    return H + L - gc - lp + ab + kb

def best_acc(score_fn, gt):
    best = -1.0
    t = 10.0
    while t <= 44.0:
        correct = sum(1 for h in HANDS if (score_fn(h) >= t) == (h in gt))
        a = correct / len(HANDS)
        if a > best: best = a
        t += 0.5
    return best * 100

def category_acc(scenarios, p):
    fn = lambda h: score(h, p)
    return sum(best_acc(fn, s['play']) for s in scenarios) / len(scenarios)

# -----------------------------------------------------------------------
# GTO データ読み込み & シナリオ構築
# -----------------------------------------------------------------------
with open(CASH_PATH) as f: CASH = json.load(f)
with open(MTT_PATH)  as f: MTT  = json.load(f)

def gset_cash(key, *actions):
    s = set()
    for a in actions: s.update(CASH[key]['actions'].get(a, []))
    return s

def gset_mtt(key, *actions):
    s = set()
    for a in actions: s.update(MTT[key]['actions'].get(a, []))
    return s

CASH_CATS = {
    'RFI': [
        {'play': gset_cash('LJ_RFI','raise')},
        {'play': gset_cash('HJ_RFI','raise')},
        {'play': gset_cash('CO_RFI','raise')},
        {'play': gset_cash('BTN_RFI','raise')},
    ],
    'BB': [
        {'play': gset_cash('BB_vs_LJ','raise','limp')},
        {'play': gset_cash('BB_vs_HJ','raise','limp')},
        {'play': gset_cash('BB_vs_CO','raise','limp')},
        {'play': gset_cash('BB_vs_BTN','raise','limp')},
        {'play': gset_cash('BvB_BB_vs_SB_raise','raise','limp')},
    ],
    'IP': [
        {'play': gset_cash(k,'raise','limp')}
        for k in ['HJ_vs_LJ','CO_vs_LJ','CO_vs_HJ','BTN_vs_LJ','BTN_vs_HJ','BTN_vs_CO']
    ],
    'OOP': [
        {'play': gset_cash(k,'raise')}
        for k in ['SB_vs_LJ','SB_vs_HJ','SB_vs_CO','SB_vs_BTN']
    ],
}
CASH_CATS['ALL'] = [s for cat in CASH_CATS.values() for s in cat]

MTT_CATS = {
    'RFI': [
        {'play': gset_mtt(k,'raise')}
        for k in ['MTT25_UTG_RFI','MTT25_UTG1_RFI','MTT25_LJ_RFI',
                  'MTT25_HJ_RFI','MTT25_CO_RFI','MTT25_BTN_RFI']
    ],
    'BB': [
        {'play': gset_mtt(k,'raise','limp')}
        for k in ['MTT25_BB_vs_UTG','MTT25_BB_vs_UTG1','MTT25_BB_vs_LJ',
                  'MTT25_BB_vs_HJ','MTT25_BB_vs_CO','MTT25_BB_vs_BTN']
    ],
}
MTT_CATS['ALL'] = [s for cat in MTT_CATS.values() for s in cat]

# -----------------------------------------------------------------------
# Optuna 最適化
# -----------------------------------------------------------------------
PARAM_RANGES = {
    'suit_bonus':        (3, 8),
    'k_blocker':         (0, 2),
    'a_blocker':         (0, 4),
    'low_pen':           (0, 5),
    'a_gap_cap':         (0, 8),
    'k_gap_cap':         (0, 8),
    'pair_bonus':        (8, 16),
    'a_suited_gap_cap':  (0, 8),
    'suited_connector':  (0, 5),
    'suited_connector1': (0, 4),
    'low_high_cap':      (1, 8),
}

def make_objective(scenarios):
    def objective(trial):
        p = {k: trial.suggest_int(k, lo, hi) for k, (lo, hi) in PARAM_RANGES.items()}
        return category_acc(scenarios, p)
    return objective

def optimize(label, scenarios):
    sys.stdout.write(f'  {label} ({len(scenarios)} scenarios)... ')
    sys.stdout.flush()
    study = optuna.create_study(direction='maximize',
                                sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(make_objective(scenarios), n_trials=N_TRIALS, show_progress_bar=False)
    print(f'{study.best_value:.1f}%')
    return study.best_params, study.best_value

# -----------------------------------------------------------------------
# 実行
# -----------------------------------------------------------------------
print(f'Optuna n_trials={N_TRIALS} per category\n')

print('=== CASH ===')
cash_results = {}
for cat, scenarios in CASH_CATS.items():
    p, acc = optimize(f'Cash {cat}', scenarios)
    cash_results[cat] = (p, acc)

print()
print('=== MTT (SBR=25) ===')
mtt_results = {}
for cat, scenarios in MTT_CATS.items():
    p, acc = optimize(f'MTT  {cat}', scenarios)
    mtt_results[cat] = (p, acc)

# -----------------------------------------------------------------------
# 比較表
# -----------------------------------------------------------------------
PARAMS = list(PARAM_RANGES.keys())

def fmt(v, ref):
    d = v - ref
    return f'{v}({d:+d})' if d != 0 else str(v)

print('\n\n' + '='*90)
print('係数比較: Cash vs MTT (ALL 最適)')
print('='*90)
cash_all = cash_results['ALL'][0]
mtt_all  = mtt_results['ALL'][0]
print(f'{"係数":<22} {"Cash ALL":>10} {"MTT ALL":>10} {"差":>6}')
print('-'*50)
for pk in PARAMS:
    cv = cash_all[pk]
    mv = mtt_all[pk]
    d  = mv - cv
    marker = ' ★' if abs(d) >= 2 else (' △' if abs(d) == 1 else '')
    print(f'  {pk:<20} {cv:>10} {mv:>10} {d:>+6}{marker}')

print('\n\n' + '='*90)
print('カテゴリ別精度サマリー')
print('='*90)
print(f'{"カテゴリ":<16} {"シナリオ数":>8} {"精度":>8}')
print('-'*35)
print('  [Cash]')
for cat, (p, acc) in cash_results.items():
    n = len(CASH_CATS[cat])
    print(f'  {cat:<14} {n:>8}  {acc:>7.1f}%')
print('  [MTT SBR=25]')
for cat, (p, acc) in mtt_results.items():
    n = len(MTT_CATS[cat])
    print(f'  {cat:<14} {n:>8}  {acc:>7.1f}%')

print('\n\n' + '='*90)
print('RFI 係数比較 (Cash vs MTT)')
print('='*90)
cash_rfi = cash_results['RFI'][0]
mtt_rfi  = mtt_results['RFI'][0]
print(f'{"係数":<22} {"Cash RFI":>10} {"MTT RFI":>10} {"差":>6}')
print('-'*50)
for pk in PARAMS:
    cv = cash_rfi[pk]
    mv = mtt_rfi[pk]
    d  = mv - cv
    marker = ' ★' if abs(d) >= 2 else (' △' if abs(d) == 1 else '')
    print(f'  {pk:<20} {cv:>10} {mv:>10} {d:>+6}{marker}')

print('\n\n' + '='*90)
print('BB 係数比較 (Cash vs MTT)')
print('='*90)
cash_bb = cash_results['BB'][0]
mtt_bb  = mtt_results['BB'][0]
print(f'{"係数":<22} {"Cash BB":>10} {"MTT BB":>10} {"差":>6}')
print('-'*50)
for pk in PARAMS:
    cv = cash_bb[pk]
    mv = mtt_bb[pk]
    d  = mv - cv
    marker = ' ★' if abs(d) >= 2 else (' △' if abs(d) == 1 else '')
    print(f'  {pk:<20} {cv:>10} {mv:>10} {d:>+6}{marker}')

