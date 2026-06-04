"""
v7_tiers.py — 3段階精度検証 + Optuna最適化

Tier1 (シンプル): 係数4個、コンテキストなし
  Score = H+L + pair_bonus[pair] + suit_bonus[suited] - min(gap, gap_cap) + a_bonus[A-high]

Tier2 (ミドル): 係数11個、コンテキストなし (base only, no overrides)

Tier3 (詳細): 現行v7 (base + 7コンテキスト上書き)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_DIR = Path('/home/cuzic/poker-books/knowledges/preflop')
N_TRIALS_T1 = 1000
N_TRIALS_T2 = 2000

# ===================================================================
# ハンドリスト
# ===================================================================
_RANKS = '23456789TJQKA'
_RANK  = {r: v for v, r in enumerate(_RANKS, 2)}
ALL_169: list[str] = []
for r in _RANKS:
    ALL_169.append(f'{r}{r}')
for i in range(len(_RANKS) - 1, -1, -1):
    for j in range(i - 1, -1, -1):
        hi, lo = _RANKS[i], _RANKS[j]
        ALL_169 += [f'{hi}{lo}s', f'{hi}{lo}o']
N = len(ALL_169)

_H = np.zeros(N, dtype=np.float32); _L = np.zeros(N, dtype=np.float32)
_SUIT = np.zeros(N, dtype=bool);    _PAIR = np.zeros(N, dtype=bool)
_GAP  = np.zeros(N, dtype=np.float32)
_A    = np.zeros(N, dtype=bool); _K = np.zeros(N, dtype=bool)
_QHI  = np.zeros(N, dtype=bool); _JHI = np.zeros(N, dtype=bool)
_LPEN = np.zeros(N, dtype=bool)
_GAP0 = np.zeros(N, dtype=bool); _GAP1 = np.zeros(N, dtype=bool)

for i, h in enumerate(ALL_169):
    if len(h) == 2:
        r = _RANK[h[0]]; _H[i] = _L[i] = r; _PAIR[i] = True
    else:
        a, b = _RANK[h[0]], _RANK[h[1]]; H, L = max(a,b), min(a,b)
        _H[i]=H; _L[i]=L; _SUIT[i]=h.endswith('s')
        gap=H-L-1; _GAP[i]=gap
        _A[i]=(H==14); _K[i]=(H==13); _QHI[i]=(H==12); _JHI[i]=(H==11)
        _LPEN[i]=(L<10 and H!=14); _GAP0[i]=(gap==0); _GAP1[i]=(gap==1)

THRESHOLDS = np.arange(10.0, 44.5, 0.5, dtype=np.float32)

def best_acc(scores, play_arr):
    predicted = scores[np.newaxis,:] >= THRESHOLDS[:,np.newaxis]
    return float((predicted == play_arr[np.newaxis,:]).sum(axis=1).max()) / N * 100

# ===================================================================
# スコア関数
# ===================================================================
def score_simple(p: dict) -> np.ndarray:
    """Tier1: 係数4個 (pair_bonus, suit_bonus, gap_cap, a_bonus)"""
    s = np.zeros(N, dtype=np.float32)
    s[_PAIR] = _H[_PAIR] + _L[_PAIR] + p['pair_bonus']
    mask_s = _SUIT & ~_PAIR
    if mask_s.any():
        gc = np.minimum(_GAP[mask_s], p['gap_cap'])
        ab = np.where(_A[mask_s], p['a_bonus'], 0.0)
        s[mask_s] = _H[mask_s] + _L[mask_s] + p['suit_bonus'] - gc + ab
    mask_o = ~_SUIT & ~_PAIR
    if mask_o.any():
        gc = np.minimum(_GAP[mask_o], p['gap_cap'])
        ab = np.where(_A[mask_o], p['a_bonus'], 0.0)
        s[mask_o] = _H[mask_o] + _L[mask_o] - gc + ab
    return s

def score_full(p: dict) -> np.ndarray:
    """Tier2/3: 係数11個"""
    s = np.zeros(N, dtype=np.float32)
    s[_PAIR] = _H[_PAIR] + _L[_PAIR] + p['pair_bonus']
    mask_s = _SUIT & ~_PAIR
    if mask_s.any():
        H=_H[mask_s]; L=_L[mask_s]; g=_GAP[mask_s]
        ab=np.where(_A[mask_s],p['a_blocker'],0.0)
        kb=np.where(_K[mask_s],p['k_blocker'],0.0)
        gc=np.where(_A[mask_s], np.minimum(g,p['a_suited_gap_cap']),
           np.where(_K[mask_s], np.minimum(g,2),
           np.where(_QHI[mask_s],np.minimum(g,3),
           np.where(_JHI[mask_s],np.minimum(g,4),
                                  np.minimum(g,p['low_high_cap'])))))
        sc=np.where(_GAP0[mask_s],p['suited_connector'],
           np.where(_GAP1[mask_s],p['suited_connector1'],0.0))
        s[mask_s]=H+L+p['suit_bonus']-gc+ab+kb+sc
    mask_o = ~_SUIT & ~_PAIR
    if mask_o.any():
        H=_H[mask_o]; L=_L[mask_o]; g=_GAP[mask_o]
        ab=np.where(_A[mask_o],p['a_blocker'],0.0)
        kb=np.where(_K[mask_o],p['k_blocker'],0.0)
        lp=np.where(_LPEN[mask_o],p['low_pen'],0.0)
        gc=np.where(_A[mask_o],np.minimum(g,p['a_gap_cap']),
           np.where(_K[mask_o],np.minimum(g,p['k_gap_cap']),g))
        s[mask_o]=H+L-gc-lp+ab+kb
    return s

# ===================================================================
# データ読み込み
# ===================================================================
EXCLUDE_CTX = {'push','SB_RFI'}

def _infer_ctx(key, meta=None):
    if meta and 'ctx' in meta: return meta['ctx']
    k=key.upper()
    if 'PUSH' in k: return 'push'
    if any(x in k for x in ['SQ_','SQUEEZE','_SB_COLD','_BTN_SB','_CO_BTN','_O_','MW']):
        if k.startswith('BB'): return 'MW_BB'
        if k.startswith('SB'): return 'MW_SB'
        return 'MW_IP'
    if k.endswith('_RFI'): return 'SB_RFI' if 'SB_' in k else 'RFI'
    if k.startswith('BB_') or k.startswith('BVB_BB'): return 'BB'
    if k.startswith('SB_VS'): return 'OOP'
    if 'LIMP' in k: return 'BB'
    return 'IP'

def load_scenarios(files, game_filter=None, sbr_filter=None, icm_filter=None):
    scenarios=[]
    for fpath in files:
        if not fpath.exists(): continue
        with open(fpath) as f: d=json.load(f)
        for key,val in d.items():
            if isinstance(val,dict) and 'meta' in val:
                meta=val['meta']; partial=meta.get('partial',False)
                ctx=meta.get('ctx',_infer_ctx(key)); game=meta.get('game','cash')
                sbr=meta.get('sbr'); icm=meta.get('icm','chipev')
            elif isinstance(val,dict) and 'actions' in val:
                partial=val.get('partial',False); ctx=_infer_ctx(key)
                game='cash'; sbr=None; icm='chipev'; meta={}
            else: continue
            if partial: continue
            if ctx in EXCLUDE_CTX: continue
            if game_filter and game not in game_filter: continue
            if sbr_filter  and sbr  not in sbr_filter:  continue
            if icm_filter  and icm  not in icm_filter:  continue
            acts=val.get('actions',{})
            play_hands=set(acts.get('raise',[]))|set(acts.get('call',[]))
            if not play_hands: continue
            play_arr=np.array([h in play_hands for h in ALL_169],dtype=bool)
            scenarios.append((ctx,play_arr))
    return scenarios

all_files = [
    GTO_DIR/'gto-charts.json', GTO_DIR/'gto-charts-mtt6.json',
    GTO_DIR/'gto-charts-icm.json', GTO_DIR/'gto-charts-mtt9m.json',
    GTO_DIR/'gto-charts-ext.json',
]

cash_s = load_scenarios(all_files, game_filter={'cash'})
mtt_s  = load_scenarios(all_files, game_filter={'mtt'}, sbr_filter={25}, icm_filter={'chipev'})
print(f'Cash: {len(cash_s)} scenarios, MTT SBR25: {len(mtt_s)} scenarios\n')

# ===================================================================
# Tier3 係数（確定済み）
# ===================================================================
CASH_BASE = dict(suit_bonus=4,k_blocker=3,a_blocker=5,low_pen=2,a_gap_cap=5,
                 k_gap_cap=7,pair_bonus=16,a_suited_gap_cap=4,
                 suited_connector=1,suited_connector1=0,low_high_cap=5)
CASH_CTX = {
    'RFI':   {'low_pen':3,'pair_bonus':11,'a_blocker':4},
    'BB':    {'suit_bonus':6,'suited_connector':6,'suited_connector1':4},
    'IP':    {'suited_connector1':2,'pair_bonus':12},
    'OOP':   {'suited_connector1':4,'pair_bonus':12},
    'MW_BB': {'suited_connector1':5,'low_pen':6,'pair_bonus':11},
    'MW_SB': {'suited_connector':6,'suited_connector1':5},
    'MW_IP': {'suit_bonus':8,'suited_connector':6,'pair_bonus':14,'a_blocker':2},
}
MTT_BASE = dict(suit_bonus=6,k_blocker=0,a_blocker=5,low_pen=0,a_gap_cap=5,
                k_gap_cap=2,pair_bonus=18,a_suited_gap_cap=4,
                suited_connector=4,suited_connector1=3,low_high_cap=5)
MTT_CTX = {
    'RFI':   {'suit_bonus':5,'low_pen':1},
    'BB':    {'suit_bonus':9,'pair_bonus':10,'a_blocker':3},
    'IP':    {'low_pen':6},
    'OOP':   {'suited_connector1':2,'low_pen':5},
    'MW_BB': {'suit_bonus':9,'suited_connector':5,'suited_connector1':5,'low_pen':5,'a_blocker':1},
    'MW_SB': {'suited_connector1':2,'a_blocker':4},
    'MW_IP': {'suit_bonus':3,'suited_connector1':1,'low_pen':6,'a_blocker':4},
}

def eval_no_ctx(scenarios, base, fn=score_full):
    return sum(best_acc(fn(base),pa) for _,pa in scenarios)/len(scenarios)

def eval_with_ctx(scenarios, base, ctx_ov):
    return sum(best_acc(score_full({**base,**ctx_ov.get(ctx,{})}),pa)
               for ctx,pa in scenarios)/len(scenarios)

print('=== Tier3 (詳細, 現行v7) ===')
t3_cash = eval_with_ctx(cash_s, CASH_BASE, CASH_CTX)
t3_mtt  = eval_with_ctx(mtt_s,  MTT_BASE,  MTT_CTX)
print(f'  Cash: {t3_cash:.2f}%  MTT: {t3_mtt:.2f}%')

# ===================================================================
# Tier2: ミドル — Optuna で base only (no ctx) を再最適化
# ===================================================================
print('\n=== Tier2 (ミドル) Optuna 最適化中 ... ===')
FULL_RANGES = dict(suit_bonus=(3,9),k_blocker=(0,3),a_blocker=(0,5),
                   low_pen=(0,6),a_gap_cap=(0,9),k_gap_cap=(0,9),
                   pair_bonus=(8,18),a_suited_gap_cap=(0,9),
                   suited_connector=(0,6),suited_connector1=(0,5),low_high_cap=(1,9))

def make_full_obj(scenarios):
    def obj(trial):
        p={k:trial.suggest_int(k,lo,hi) for k,(lo,hi) in FULL_RANGES.items()}
        return sum(best_acc(score_full(p),pa) for _,pa in scenarios)/len(scenarios)
    return obj

study_t2_cash=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=42))
study_t2_cash.optimize(make_full_obj(cash_s),n_trials=N_TRIALS_T2,n_jobs=1)
t2_cash_params=study_t2_cash.best_params
t2_cash=study_t2_cash.best_value

study_t2_mtt=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=42))
study_t2_mtt.optimize(make_full_obj(mtt_s),n_trials=N_TRIALS_T2,n_jobs=1)
t2_mtt_params=study_t2_mtt.best_params
t2_mtt=study_t2_mtt.best_value

print(f'  Cash: {t2_cash:.2f}%  MTT: {t2_mtt:.2f}%')

# ===================================================================
# Tier1: シンプル — Optuna で 4係数最適化
# ===================================================================
print('\n=== Tier1 (シンプル) Optuna 最適化中 ... ===')
SIMPLE_RANGES = dict(pair_bonus=(8,18), suit_bonus=(2,8),
                     gap_cap=(2,8), a_bonus=(0,6))

def make_simple_obj(scenarios):
    def obj(trial):
        p={k:trial.suggest_int(k,lo,hi) for k,(lo,hi) in SIMPLE_RANGES.items()}
        return sum(best_acc(score_simple(p),pa) for _,pa in scenarios)/len(scenarios)
    return obj

study_t1_cash=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=42))
study_t1_cash.optimize(make_simple_obj(cash_s),n_trials=N_TRIALS_T1,n_jobs=1)
t1_cash_params=study_t1_cash.best_params
t1_cash=study_t1_cash.best_value

study_t1_mtt=optuna.create_study(direction='maximize',sampler=optuna.samplers.TPESampler(seed=42))
study_t1_mtt.optimize(make_simple_obj(mtt_s),n_trials=N_TRIALS_T1,n_jobs=1)
t1_mtt_params=study_t1_mtt.best_params
t1_mtt=study_t1_mtt.best_value

print(f'  Cash: {t1_cash:.2f}%  MTT: {t1_mtt:.2f}%')

# ===================================================================
# 結果まとめ
# ===================================================================
print('\n' + '='*70)
print('3段階精度サマリー')
print('='*70)
print(f'{"Tier":<12} {"Cash":>8} {"MTT SBR25":>12} {"覚える量":>20}')
print('-'*60)
print(f'{"Tier1 シンプル":<12} {t1_cash:>7.1f}% {t1_mtt:>11.1f}%  {"係数4個・コンテキストなし":>20}')
print(f'{"Tier2 ミドル":<12} {t2_cash:>7.1f}% {t2_mtt:>11.1f}%  {"係数11個・コンテキストなし":>20}')
print(f'{"Tier3 詳細":<12} {t3_cash:>7.1f}% {t3_mtt:>11.1f}%  {"係数11個+7コンテキスト上書き":>20}')

print('\n--- Tier1 係数 ---')
print('Cash: ', {k:v for k,v in t1_cash_params.items()})
print('MTT:  ', {k:v for k,v in t1_mtt_params.items()})

print('\n--- Tier2 係数 (Cash, no ctx) ---')
for k,v in t2_cash_params.items():
    base_v=CASH_BASE[k]; diff=v-base_v
    flag=' ★' if abs(diff)>=2 else (' △' if diff else '')
    print(f'  {k:<22} = {v}  (Tier3base={base_v}, Δ={diff:+d}){flag}')

print('\n--- Tier2 係数 (MTT, no ctx) ---')
for k,v in t2_mtt_params.items():
    base_v=MTT_BASE[k]; diff=v-base_v
    flag=' ★' if abs(diff)>=2 else (' △' if diff else '')
    print(f'  {k:<22} = {v}  (Tier3base={base_v}, Δ={diff:+d}){flag}')

# コンテキスト別精度breakdown (Tier1 vs Tier2 vs Tier3)
print('\n--- コンテキスト別精度: Cash ---')
ctx_data: dict[str, list] = {}
for ctx, pa in cash_s:
    t1 = best_acc(score_simple(t1_cash_params), pa)
    t2 = best_acc(score_full(t2_cash_params), pa)
    t3 = best_acc(score_full({**CASH_BASE, **CASH_CTX.get(ctx,{})}), pa)
    ctx_data.setdefault(ctx, []).append((t1,t2,t3))
print(f'  {"ctx":<10} {"N":>4}  {"Tier1":>7} {"Tier2":>7} {"Tier3":>7}')
for ctx, vals in sorted(ctx_data.items()):
    a1=sum(v[0] for v in vals)/len(vals)
    a2=sum(v[1] for v in vals)/len(vals)
    a3=sum(v[2] for v in vals)/len(vals)
    print(f'  {ctx:<10} {len(vals):>4}  {a1:>6.1f}% {a2:>6.1f}% {a3:>6.1f}%')

print('\n--- コンテキスト別精度: MTT ---')
ctx_data2: dict[str, list] = {}
for ctx, pa in mtt_s:
    t1 = best_acc(score_simple(t1_mtt_params), pa)
    t2 = best_acc(score_full(t2_mtt_params), pa)
    t3 = best_acc(score_full({**MTT_BASE, **MTT_CTX.get(ctx,{})}), pa)
    ctx_data2.setdefault(ctx, []).append((t1,t2,t3))
print(f'  {"ctx":<10} {"N":>4}  {"Tier1":>7} {"Tier2":>7} {"Tier3":>7}')
for ctx, vals in sorted(ctx_data2.items()):
    a1=sum(v[0] for v in vals)/len(vals)
    a2=sum(v[1] for v in vals)/len(vals)
    a3=sum(v[2] for v in vals)/len(vals)
    print(f'  {ctx:<10} {len(vals):>4}  {a1:>6.1f}% {a2:>6.1f}% {a3:>6.1f}%')
