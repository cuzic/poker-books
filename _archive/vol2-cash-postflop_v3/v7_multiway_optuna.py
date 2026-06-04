"""
v7_multiway_optuna.py — マルチウェイ対応コンテキスト統合最適化

コンテキスト (7種):
  RFI    : LJ/HJ/CO/BTN オープン (4)
  IP     : IP 3bet/call (6)
  OOP    : SB 3bet or fold (4)
  BB     : BB HU defense (5)
  MW_BB  : BB マルチウェイ (cold + squeeze) (4)
  MW_SB  : SB squeeze (5)
  MW_IP  : IP squeeze (3)
  ※ SB_RFI / BvB_limp は構造的限界のため除外

ベース係数 (11) + コンテキスト上書き (6ctx × 6係数 = 36)
合計 ~47 パラメータ → 1500 トライアル
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json')
N_TRIALS = 1500

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

with open(GTO_PATH) as f:
    GTO = json.load(f)

def gset(key, *actions):
    s = set()
    for a in actions:
        s.update(GTO[key]['actions'].get(a, []))
    return s

# ---------------------------------------------------------------
# シナリオ定義
# ---------------------------------------------------------------
SCENARIOS = {
    'RFI': [
        {'play': gset('LJ_RFI','raise')},
        {'play': gset('HJ_RFI','raise')},
        {'play': gset('CO_RFI','raise')},
        {'play': gset('BTN_RFI','raise')},
    ],
    'IP': [
        {'play': gset(k,'raise','limp')}
        for k in ['HJ_vs_LJ','CO_vs_LJ','CO_vs_HJ','BTN_vs_LJ','BTN_vs_HJ','BTN_vs_CO']
    ],
    'OOP': [
        {'play': gset(k,'raise')}
        for k in ['SB_vs_LJ','SB_vs_HJ','SB_vs_CO','SB_vs_BTN']
    ],
    'BB': [
        {'play': gset(k,'raise','limp')}
        for k in ['BB_vs_LJ','BB_vs_HJ','BB_vs_CO','BB_vs_BTN','BvB_BB_vs_SB_raise']
    ],
    'MW_BB': [
        {'play': gset('BB_vs_BTN_SB_cold','raise','limp')},
        {'play': gset('BB_vs_CO_BTN_cold','raise','limp')},
        {'play': gset('BB_squeeze_vs_HJ_BTN','raise','limp')},
        {'play': gset('BB_squeeze_vs_UTG_BTN','raise','limp')},
    ],
    'MW_SB': [
        {'play': gset(k,'raise','limp')}
        for k in ['SB_squeeze_vs_CO_BTN','SB_squeeze_vs_HJ_BTN',
                  'SB_squeeze_vs_UTG_BTN','SB_squeeze_vs_UTG_CO','SB_squeeze_vs_UTG_HJ']
    ],
    'MW_IP': [
        {'play': gset(k,'raise','limp')}
        for k in ['BTN_squeeze_vs_UTG_CO','BTN_squeeze_vs_UTG_HJ','CO_squeeze_vs_UTG_HJ']
    ],
}

ALL_SCENARIOS = [(ctx, s) for ctx, slist in SCENARIOS.items() for s in slist]

# ---------------------------------------------------------------
# 精度計算
# ---------------------------------------------------------------
def best_acc(score_fn, gt):
    best = -1.0
    t = 10.0
    while t <= 44.0:
        correct = sum(1 for h in HANDS if (score_fn(h) >= t) == (h in gt))
        a = correct / len(HANDS)
        if a > best: best = a
        t += 0.5
    return best * 100

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
CTX_PARAMS = ['suit_bonus','suited_connector','suited_connector1',
              'low_pen','pair_bonus','a_blocker']
CONTEXTS   = ['RFI','BB','IP','OOP','MW_BB','MW_SB','MW_IP']

def resolve(base, overrides, ctx):
    p = dict(base)
    p.update(overrides.get(ctx, {}))
    return p

def objective(trial):
    base = {k: trial.suggest_int(k, lo, hi) for k, (lo, hi) in PARAM_RANGES.items()}
    overrides = {}
    for ctx in CONTEXTS:
        ov = {}
        for pk in CTX_PARAMS:
            if trial.suggest_categorical(f'{ctx}_{pk}_use', [True, False]):
                lo, hi = {'suit_bonus':(3,8),'suited_connector':(0,5),
                          'suited_connector1':(0,4),'low_pen':(0,5),
                          'pair_bonus':(8,16),'a_blocker':(0,4)}[pk]
                ov[pk] = trial.suggest_int(f'{ctx}_{pk}', lo, hi)
        overrides[ctx] = ov

    total = 0.0
    for ctx, s in ALL_SCENARIOS:
        p = resolve(base, overrides, ctx)
        fn = lambda h, p=p: score(h, p)
        total += best_acc(fn, s['play'])
    return total / len(ALL_SCENARIOS)

# ---------------------------------------------------------------
# 実行
# ---------------------------------------------------------------
print(f'Optuna multiway context, n_trials={N_TRIALS}')
print(f'シナリオ数: {len(ALL_SCENARIOS)} ({", ".join(f"{k}={len(v)}" for k,v in SCENARIOS.items())})\n')

study = optuna.create_study(direction='maximize',
                            sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(objective, n_trials=N_TRIALS, show_progress_bar=False)

best  = study.best_params
bval  = study.best_value

# ---------------------------------------------------------------
# 結果整形
# ---------------------------------------------------------------
base_keys = list(PARAM_RANGES.keys())
base_p    = {k: best[k] for k in base_keys}

ctx_ov = {}
for ctx in CONTEXTS:
    ov = {}
    for pk in CTX_PARAMS:
        use_key = f'{ctx}_{pk}_use'
        val_key = f'{ctx}_{pk}'
        if best.get(use_key) and val_key in best:
            ov[pk] = best[val_key]
    ctx_ov[ctx] = ov

print(f'最良精度 (全{len(ALL_SCENARIOS)}シナリオ平均): {bval:.2f}%\n')

print('='*65)
print('ベース係数')
print('='*65)
for k, v in base_p.items():
    print(f'  {k:<22} = {v}')

print()
print('='*65)
print('コンテキスト上書き係数')
print('='*65)
for ctx in CONTEXTS:
    ov = ctx_ov[ctx]
    n  = len(SCENARIOS[ctx])
    if ov:
        print(f'\n  [{ctx}] ({n} scenarios)')
        for k, v in ov.items():
            bv   = base_p[k]
            diff = v - bv
            print(f'    {k:<22} = {v}  (base={bv}, Δ={diff:+d})')
    else:
        print(f'\n  [{ctx}] ({n} scenarios) — base 使用')

# コンテキスト別精度
print()
print('='*65)
print('コンテキスト別精度')
print('='*65)
for ctx, slist in SCENARIOS.items():
    p = resolve(base_p, ctx_ov, ctx)
    fn = lambda h, p=p: score(h, p)
    acc = sum(best_acc(fn, s['play']) for s in slist) / len(slist)
    print(f'  {ctx:<8} {len(slist):>2} scenarios:  {acc:.1f}%')

