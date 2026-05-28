"""
v7_context_optuna.py — コンテキスト別係数の統合最適化

設計:
  - ベース係数 (全コンテキスト共通)
  - コンテキスト上書き係数 (RFI / BB / DEF_IP / DEF_OOP)
  - 最終スコアは: context係数優先 → なければ base係数

探索パラメータ (合計 ~35):
  base (11): suit_bonus, k_blocker, a_blocker, low_pen,
             a_gap_cap, k_gap_cap, pair_bonus,
             a_suited_gap_cap, suited_connector, suited_connector1, low_high_cap
  各コンテキスト (5×4=20):
    suit_bonus, suited_connector, suited_connector1,
    low_pen, pair_bonus  (a_blocker は base 固定で試す)
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json')
N_TRIALS  = 1200   # パラメータ数が多いので増やす

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

# -------------------------------------------------------------------------
# スコア関数 — p はコンテキスト解決済み係数辞書
# -------------------------------------------------------------------------
def score(hand: str, p: dict) -> float:
    H, L, suited, pair = parse(hand)
    if pair:
        return H + L + p['pair_bonus']
    gap = H - L - 1
    ab  = p['a_blocker'] if H == 14 else 0.0
    kb  = p['k_blocker'] if H == 13 else 0.0

    if suited:
        if H == 14:   gc = min(gap, p['a_suited_gap_cap'])
        elif H == 13: gc = min(gap, 2)
        elif H == 12: gc = min(gap, 3)
        elif H == 11: gc = min(gap, 4)
        else:         gc = min(gap, p['low_high_cap'])
        sc = p['suited_connector'] if gap == 0 else (p['suited_connector1'] if gap == 1 else 0)
        return H + L + p['suit_bonus'] - gc + ab + kb + sc

    # offsuit
    if H == 14:
        gc = min(gap, p['a_gap_cap']); lp = 0.0
    elif H == 13:
        gc = min(gap, p['k_gap_cap']); lp = p['low_pen'] if L < 10 else 0.0
    else:
        gc = gap; lp = p['low_pen'] if L < 10 else 0.0
    return H + L - gc - lp + ab + kb

# -------------------------------------------------------------------------
# GTO データ
# -------------------------------------------------------------------------
with open(GTO_PATH) as f:
    GTO = json.load(f)

def gset(key, action):
    return set(GTO[key]['actions'].get(action, []))

def build_scenarios():
    s = {}
    for k in ['LJ_RFI','HJ_RFI','CO_RFI','BTN_RFI']:
        s[k] = {'play': gset(k,'raise'), 'ctx': 'RFI'}
    s['SB_RFI'] = {'play': gset('BvB_SB_strategy','raise')
                         | gset('BvB_SB_strategy','limp')
                         | gset('BvB_SB_strategy','mixed_limp'),
                   'ctx': 'SB'}
    for k in ['HJ_vs_LJ','CO_vs_LJ','CO_vs_HJ','BTN_vs_LJ','BTN_vs_HJ','BTN_vs_CO']:
        s[k] = {'play': gset(k,'raise') | gset(k,'limp'), 'ctx': 'IP'}
    for k in ['SB_vs_LJ','SB_vs_HJ','SB_vs_CO','SB_vs_BTN']:
        s[k] = {'play': gset(k,'raise'), 'ctx': 'OOP'}
    for k in ['BB_vs_LJ','BB_vs_HJ','BB_vs_CO','BB_vs_BTN','BvB_BB_vs_SB_raise']:
        s[k] = {'play': gset(k,'raise') | gset(k,'limp'), 'ctx': 'BB'}
    return s

ALL_SCENARIOS = build_scenarios()
CONTEXTS = ['RFI', 'SB', 'IP', 'OOP', 'BB']

# コンテキスト別のシナリオキー
CTX_KEYS = {c: [k for k,v in ALL_SCENARIOS.items() if v['ctx']==c] for c in CONTEXTS}

# -------------------------------------------------------------------------
# 精度計算
# -------------------------------------------------------------------------
def best_acc(score_fn, gt):
    best = -1.0
    t = 10.0
    while t <= 44.0:
        correct = sum(1 for h in HANDS if (score_fn(h) >= t) == (h in gt))
        a = correct / len(HANDS)
        if a > best: best = a
        t += 0.5
    return best * 100

def all_acc(base_p: dict, ctx_overrides: dict[str, dict]) -> float:
    total = 0.0
    for key, info in ALL_SCENARIOS.items():
        ctx = info['ctx']
        # コンテキスト係数優先、なければ base
        p = {**base_p, **ctx_overrides.get(ctx, {})}
        fn = lambda h, p=p: score(h, p)
        total += best_acc(fn, info['play'])
    return total / len(ALL_SCENARIOS)

# -------------------------------------------------------------------------
# Optuna objective
# -------------------------------------------------------------------------
# コンテキスト別に上書きする係数キー
CTX_OVERRIDE_PARAMS = ['suit_bonus', 'suited_connector', 'suited_connector1',
                       'low_pen', 'pair_bonus', 'a_blocker']

def make_objective():
    def objective(trial: optuna.Trial) -> float:
        # ベース係数
        base = {
            'suit_bonus':        trial.suggest_int('suit_bonus',        3, 8),
            'k_blocker':         trial.suggest_int('k_blocker',         0, 2),
            'a_blocker':         trial.suggest_int('a_blocker',         0, 4),
            'low_pen':           trial.suggest_int('low_pen',           0, 5),
            'a_gap_cap':         trial.suggest_int('a_gap_cap',         0, 8),
            'k_gap_cap':         trial.suggest_int('k_gap_cap',         0, 8),
            'pair_bonus':        trial.suggest_int('pair_bonus',        8, 16),
            'a_suited_gap_cap':  trial.suggest_int('a_suited_gap_cap',  0, 8),
            'suited_connector':  trial.suggest_int('suited_connector',  0, 5),
            'suited_connector1': trial.suggest_int('suited_connector1', 0, 4),
            'low_high_cap':      trial.suggest_int('low_high_cap',      1, 8),
        }
        # コンテキスト別上書き係数 (base と同じ範囲、None = base を使う)
        ctx_overrides = {}
        for ctx in ['RFI', 'BB', 'IP', 'OOP']:
            overrides = {}
            for pk in CTX_OVERRIDE_PARAMS:
                # None (= base使用) か override値か を選択
                use_override = trial.suggest_categorical(f'{ctx}_{pk}_use', [True, False])
                if use_override:
                    lo, hi = {'suit_bonus':(3,8), 'suited_connector':(0,5),
                               'suited_connector1':(0,4), 'low_pen':(0,5),
                               'pair_bonus':(8,16), 'a_blocker':(0,4)}[pk]
                    overrides[pk] = trial.suggest_int(f'{ctx}_{pk}', lo, hi)
            ctx_overrides[ctx] = overrides
        return all_acc(base, ctx_overrides)
    return objective

print(f'Optuna context-specific, n_trials={N_TRIALS}\n')
study = optuna.create_study(direction='maximize',
                            sampler=optuna.samplers.TPESampler(seed=42))
study.optimize(make_objective(), n_trials=N_TRIALS, show_progress_bar=False,
               n_jobs=1)

best = study.best_params
best_val = study.best_value

# -------------------------------------------------------------------------
# 結果整形
# -------------------------------------------------------------------------
def extract_params(best: dict) -> tuple[dict, dict[str, dict]]:
    base = {}
    ctx_ov = {c: {} for c in ['RFI', 'BB', 'IP', 'OOP']}
    for k, v in best.items():
        if '_use' in k or '_' not in k:
            continue
        parts = k.split('_', 1)
        if parts[0] in ['RFI', 'BB', 'IP', 'OOP']:
            ctx, param = parts[0], parts[1]
            if f'{ctx}_{param}_use' in best and best[f'{ctx}_{param}_use']:
                ctx_ov[ctx][param] = v
    base_keys = ['suit_bonus','k_blocker','a_blocker','low_pen','a_gap_cap',
                 'k_gap_cap','pair_bonus','a_suited_gap_cap','suited_connector',
                 'suited_connector1','low_high_cap']
    base = {k: best[k] for k in base_keys}
    return base, ctx_ov

base_p, ctx_ov = extract_params(best)

print(f'最良精度 (全20シナリオ平均): {best_val:.2f}%\n')

print('='*70)
print('ベース係数')
print('='*70)
for k, v in base_p.items():
    print(f'  {k:<22} = {v}')

print()
print('='*70)
print('コンテキスト上書き係数')
print('='*70)
for ctx in ['RFI', 'BB', 'IP', 'OOP']:
    ov = ctx_ov[ctx]
    if ov:
        print(f'\n  [{ctx}]')
        for k, v in ov.items():
            base_v = base_p.get(k, '?')
            diff = v - base_v if isinstance(base_v, int) else 0
            print(f'    {k:<22} = {v}  (base={base_v}, Δ={diff:+d})')
    else:
        print(f'\n  [{ctx}] — 上書きなし (base 使用)')

# カテゴリ別精度
print()
print('='*70)
print('コンテキスト別精度')
print('='*70)
for ctx in CONTEXTS:
    keys = CTX_KEYS[ctx]
    total = 0.0
    for k in keys:
        p = {**base_p, **ctx_ov.get(ctx, {})}
        fn = lambda h, p=p: score(h, p)
        total += best_acc(fn, ALL_SCENARIOS[k]['play'])
    avg = total / len(keys)
    print(f'  {ctx:<8} {len(keys)} scenarios:  {avg:.1f}%')

