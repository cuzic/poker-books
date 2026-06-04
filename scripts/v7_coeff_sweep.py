"""
v7_coeff_sweep.py — 4/5/6 係数の組み合わせ精度調査

4係数ベースから1つずつ追加したとき、何が最も効くかを測定する。

候補追加係数:
  sc_bonus  : suited gap=0 への追加ボーナス (connector)
  sc1_bonus : suited gap=1 への追加ボーナス
  low_pen   : offsuit 低カード (L<10, H≠A) へのペナルティ
  k_bonus   : K-high への追加ボーナス
  suit_off_split: suited と offsuit で gap_cap を分ける (suit_gap_cap / off_gap_cap)
  a_suit_gap: A-suited 専用 gap_cap (他と分離)
"""
from __future__ import annotations
import json, itertools
import numpy as np
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_DIR = Path('/home/cuzic/poker-books/knowledges/preflop')
N_TRIALS = 1500

# ===================================================================
# ハンドリスト + 属性配列
# ===================================================================
_RANKS = '23456789TJQKA'
_RANK  = {r: v for v, r in enumerate(_RANKS, 2)}
ALL_169: list[str] = []
for r in _RANKS:
    ALL_169.append(f'{r}{r}')
for i in range(len(_RANKS)-1,-1,-1):
    for j in range(i-1,-1,-1):
        hi,lo=_RANKS[i],_RANKS[j]; ALL_169+=[f'{hi}{lo}s',f'{hi}{lo}o']
N=len(ALL_169)

_H=np.zeros(N,dtype=np.float32); _L=np.zeros(N,dtype=np.float32)
_SUIT=np.zeros(N,dtype=bool);    _PAIR=np.zeros(N,dtype=bool)
_GAP=np.zeros(N,dtype=np.float32)
_A=np.zeros(N,dtype=bool); _K=np.zeros(N,dtype=bool)
_LPEN=np.zeros(N,dtype=bool)
_GAP0=np.zeros(N,dtype=bool); _GAP1=np.zeros(N,dtype=bool)
_QHI=np.zeros(N,dtype=bool); _JHI=np.zeros(N,dtype=bool)

for i,h in enumerate(ALL_169):
    if len(h)==2:
        r=_RANK[h[0]]; _H[i]=_L[i]=r; _PAIR[i]=True
    else:
        a,b=_RANK[h[0]],_RANK[h[1]]; H,L=max(a,b),min(a,b)
        _H[i]=H; _L[i]=L; _SUIT[i]=h.endswith('s')
        gap=H-L-1; _GAP[i]=gap
        _A[i]=(H==14); _K[i]=(H==13); _QHI[i]=(H==12); _JHI[i]=(H==11)
        _LPEN[i]=(L<10 and H!=14); _GAP0[i]=(gap==0); _GAP1[i]=(gap==1)

THRESHOLDS=np.arange(10.0,44.5,0.5,dtype=np.float32)

def best_acc(scores,play_arr):
    pred=scores[np.newaxis,:]>=THRESHOLDS[:,np.newaxis]
    return float((pred==play_arr[np.newaxis,:]).sum(axis=1).max())/N*100

# ===================================================================
# 係数セット別スコア関数
# ===================================================================
def score_v(p: dict) -> np.ndarray:
    """
    汎用スコア関数。p に含まれるキーに応じて機能を有効化。
    必須: pair_bonus, suit_bonus, gap_cap, a_bonus
    任意: sc_bonus, sc1_bonus, low_pen, k_bonus,
          suit_gap_cap (suited用gap_cap。なければgap_capを使用),
          off_gap_cap  (offsuit用gap_cap。なければgap_capを使用),
          a_suit_gap   (A-suited専用gap_cap。なければsuit_gap_capを使用)
    """
    s=np.zeros(N,dtype=np.float32)
    s[_PAIR]=_H[_PAIR]+_L[_PAIR]+p['pair_bonus']

    mask_s=_SUIT&~_PAIR
    if mask_s.any():
        H=_H[mask_s]; L=_L[mask_s]; g=_GAP[mask_s]
        # gap_cap (suited): suit_gap_cap → gap_cap → 4 の順でフォールバック
        s_gcap = p.get('suit_gap_cap', p.get('gap_cap', 4))
        a_gcap = p.get('a_suit_gap', s_gcap)
        gc = np.where(_A[mask_s], np.minimum(g, float(a_gcap)), np.minimum(g, float(s_gcap)))
        ab = np.where(_A[mask_s], p['a_bonus'], 0.0)
        kb = np.where(_K[mask_s], p.get('k_bonus',0), 0.0)
        sc = np.where(_GAP0[mask_s], p.get('sc_bonus',0),
             np.where(_GAP1[mask_s], p.get('sc1_bonus',0), 0.0))
        s[mask_s]=H+L+p['suit_bonus']-gc+ab+kb+sc

    mask_o=~_SUIT&~_PAIR
    if mask_o.any():
        H=_H[mask_o]; L=_L[mask_o]; g=_GAP[mask_o]
        o_gcap = p.get('off_gap_cap', p.get('gap_cap', 4))
        gc = np.minimum(g, o_gcap)
        ab = np.where(_A[mask_o], p['a_bonus'], 0.0)
        kb = np.where(_K[mask_o], p.get('k_bonus',0), 0.0)
        lp = np.where(_LPEN[mask_o], p.get('low_pen',0), 0.0)
        s[mask_o]=H+L-gc-lp+ab+kb
    return s

# ===================================================================
# データ読み込み
# ===================================================================
EXCLUDE_CTX={'push','SB_RFI'}

def _infer_ctx(key,meta=None):
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

def load_scenarios(files,game_filter=None,sbr_filter=None,icm_filter=None):
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

all_files=[
    GTO_DIR/'gto-charts.json', GTO_DIR/'gto-charts-mtt6.json',
    GTO_DIR/'gto-charts-icm.json', GTO_DIR/'gto-charts-mtt9m.json',
    GTO_DIR/'gto-charts-ext.json',
]
cash_s=load_scenarios(all_files,game_filter={'cash'})
mtt_s =load_scenarios(all_files,game_filter={'mtt'},sbr_filter={25},icm_filter={'chipev'})
print(f'Cash:{len(cash_s)} MTT:{len(mtt_s)}\n')

# ===================================================================
# 係数セット定義
# ===================================================================
# ranges: {param_name: (lo, hi)}
RANGES_BASE = dict(pair_bonus=(8,18), suit_bonus=(2,8), gap_cap=(2,8), a_bonus=(0,6))

RANGES_SPLIT = {k:v for k,v in RANGES_BASE.items() if k!='gap_cap'}

VARIANTS = {
    # --- 4係数 ---
    '4A base':
        dict(params=RANGES_BASE),

    # --- 5係数 (1つ追加) ---
    '5A +sc_bonus':
        dict(params={**RANGES_BASE, 'sc_bonus':(0,6)}),
    '5B +low_pen':
        dict(params={**RANGES_BASE, 'low_pen':(0,6)}),
    '5C +k_bonus':
        dict(params={**RANGES_BASE, 'k_bonus':(0,4)}),
    '5D +sc1_bonus':
        dict(params={**RANGES_BASE, 'sc1_bonus':(0,5)}),
    '5E +split_gap(suit/off)':
        dict(params={**RANGES_SPLIT, 'suit_gap_cap':(1,8), 'off_gap_cap':(1,8)}),

    # --- 6係数 (2つ追加) ---
    '6A +sc+low_pen':
        dict(params={**RANGES_BASE, 'sc_bonus':(0,6), 'low_pen':(0,6)}),
    '6B +sc+k_bonus':
        dict(params={**RANGES_BASE, 'sc_bonus':(0,6), 'k_bonus':(0,4)}),
    '6C +sc+sc1':
        dict(params={**RANGES_BASE, 'sc_bonus':(0,6), 'sc1_bonus':(0,5)}),
    '6D +low_pen+k_bonus':
        dict(params={**RANGES_BASE, 'low_pen':(0,6), 'k_bonus':(0,4)}),
    '6E +split_gap+sc':
        dict(params={**RANGES_SPLIT, 'suit_gap_cap':(1,8), 'off_gap_cap':(1,8), 'sc_bonus':(0,6)}),
    '6F +split_gap+low_pen':
        dict(params={**RANGES_SPLIT, 'suit_gap_cap':(1,8), 'off_gap_cap':(1,8), 'low_pen':(0,6)}),
}

# ===================================================================
# Optuna 実行
# ===================================================================
def run_optuna(scenarios, ranges, n_trials=N_TRIALS):
    def obj(trial):
        p={k:trial.suggest_int(k,lo,hi) for k,(lo,hi) in ranges.items()}
        return sum(best_acc(score_v(p),pa) for _,pa in scenarios)/len(scenarios)
    study=optuna.create_study(direction='maximize',
                              sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(obj,n_trials=n_trials,n_jobs=1)
    return study.best_value, study.best_params

# ===================================================================
# 全バリアント実行
# ===================================================================
results_cash={}; results_mtt={}
for name, cfg in VARIANTS.items():
    print(f'  {name} ...',end=' ',flush=True)
    ac, pc = run_optuna(cash_s, cfg['params'])
    am, pm = run_optuna(mtt_s,  cfg['params'])
    results_cash[name]=(ac,pc)
    results_mtt[name]=(am,pm)
    print(f'Cash={ac:.2f}%  MTT={am:.2f}%')

# ===================================================================
# サマリー表示
# ===================================================================
print('\n'+'='*72)
print(f'{"バリアント":<26} {"係数数":>5} {"Cash":>8} {"MTT":>8}')
print('-'*55)

groups = {'4': [], '5': [], '6': []}
for name in VARIANTS:
    tier = name[0]
    if tier in groups:
        ac, _ = results_cash[name]
        am, _ = results_mtt[name]
        n_params = len(VARIANTS[name]['params'])
        groups[tier].append((name, n_params, ac, am))

for tier in ['4','5','6']:
    items = sorted(groups[tier], key=lambda x: -(x[2]+x[3]))
    for name, np_, ac, am in items:
        print(f'  {name:<26} {np_:>5}  {ac:>7.2f}%  {am:>7.2f}%')
    # 最良を太字で
    best = items[0]
    print(f'  {"→ 最良":>26}  {best[2]:>7.2f}%  {best[3]:>7.2f}%')
    print()

# ===================================================================
# 最良バリアントのコンテキスト別精度
# ===================================================================
def ctx_breakdown(scenarios, params):
    ctx_acc={}
    for ctx,pa in scenarios:
        ctx_acc.setdefault(ctx,[]).append(best_acc(score_v(params),pa))
    return {c:sum(v)/len(v) for c,v in ctx_acc.items()}

print('='*72)
print('コンテキスト別精度: 4A / 5最良 / 6最良 vs Tier3(v7full)')
print('='*72)

# 4A
best4c_p = results_cash['4A base'][1]
best4m_p = results_mtt['4A base'][1]

# 5系 最良
best5_c = max((n for n in VARIANTS if n.startswith('5')),
              key=lambda n: results_cash[n][0]+results_mtt[n][0])
best5c_p = results_cash[best5_c][1]
best5m_p = results_mtt[best5_c][1]

# 6系 最良
best6_c = max((n for n in VARIANTS if n.startswith('6')),
              key=lambda n: results_cash[n][0]+results_mtt[n][0])
best6c_p = results_cash[best6_c][1]
best6m_p = results_mtt[best6_c][1]

# Tier3 (v7 full)
CASH_BASE=dict(suit_bonus=4,k_blocker=3,a_blocker=5,low_pen=2,a_gap_cap=5,
               k_gap_cap=7,pair_bonus=16,a_suited_gap_cap=4,
               suited_connector=1,suited_connector1=0,low_high_cap=5)
CASH_CTX={'RFI':{'low_pen':3,'pair_bonus':11,'a_blocker':4},
          'BB':{'suit_bonus':6,'suited_connector':6,'suited_connector1':4},
          'IP':{'suited_connector1':2,'pair_bonus':12},
          'OOP':{'suited_connector1':4,'pair_bonus':12},
          'MW_BB':{'suited_connector1':5,'low_pen':6,'pair_bonus':11},
          'MW_SB':{'suited_connector':6,'suited_connector1':5},
          'MW_IP':{'suit_bonus':8,'suited_connector':6,'pair_bonus':14,'a_blocker':2}}
MTT_BASE=dict(suit_bonus=6,k_blocker=0,a_blocker=5,low_pen=0,a_gap_cap=5,
              k_gap_cap=2,pair_bonus=18,a_suited_gap_cap=4,
              suited_connector=4,suited_connector1=3,low_high_cap=5)
MTT_CTX={'RFI':{'suit_bonus':5,'low_pen':1},
         'BB':{'suit_bonus':9,'pair_bonus':10,'a_blocker':3},
         'IP':{'low_pen':6},
         'OOP':{'suited_connector1':2,'low_pen':5},
         'MW_BB':{'suit_bonus':9,'suited_connector':5,'suited_connector1':5,'low_pen':5,'a_blocker':1},
         'MW_SB':{'suited_connector1':2,'a_blocker':4},
         'MW_IP':{'suit_bonus':3,'suited_connector1':1,'low_pen':6,'a_blocker':4}}

from pathlib import Path as _P
# Tier3 full v7 scores (full formula)
def score_full(p):
    s=np.zeros(N,dtype=np.float32)
    s[_PAIR]=_H[_PAIR]+_L[_PAIR]+p['pair_bonus']
    mask_s=_SUIT&~_PAIR
    if mask_s.any():
        H=_H[mask_s];L=_L[mask_s];g=_GAP[mask_s]
        ab=np.where(_A[mask_s],p['a_blocker'],0.0)
        kb=np.where(_K[mask_s],p['k_blocker'],0.0)
        gc=np.where(_A[mask_s],np.minimum(g,p['a_suited_gap_cap']),
           np.where(_K[mask_s],np.minimum(g,2),
           np.where(_QHI[mask_s],np.minimum(g,3),
           np.where(_JHI[mask_s],np.minimum(g,4),np.minimum(g,p['low_high_cap'])))))
        sc=np.where(_GAP0[mask_s],p['suited_connector'],
           np.where(_GAP1[mask_s],p['suited_connector1'],0.0))
        s[mask_s]=H+L+p['suit_bonus']-gc+ab+kb+sc
    mask_o=~_SUIT&~_PAIR
    if mask_o.any():
        H=_H[mask_o];L=_L[mask_o];g=_GAP[mask_o]
        ab=np.where(_A[mask_o],p['a_blocker'],0.0)
        kb=np.where(_K[mask_o],p['k_blocker'],0.0)
        lp=np.where(_LPEN[mask_o],p['low_pen'],0.0)
        gc=np.where(_A[mask_o],np.minimum(g,p['a_gap_cap']),
           np.where(_K[mask_o],np.minimum(g,p['k_gap_cap']),g))
        s[mask_o]=H+L-gc-lp+ab+kb
    return s

print(f'\n  Cash  ctx  |  4A   |  5: {best5_c:<18}|  6: {best6_c:<18}|  v7full')
print('-'*90)
ctxs=sorted(set(ctx for ctx,_ in cash_s))
for ctx in ctxs:
    pairs=[(pa) for c,pa in cash_s if c==ctx]
    a4=sum(best_acc(score_v(best4c_p),pa) for pa in pairs)/len(pairs)
    a5=sum(best_acc(score_v(best5c_p),pa) for pa in pairs)/len(pairs)
    a6=sum(best_acc(score_v(best6c_p),pa) for pa in pairs)/len(pairs)
    at=sum(best_acc(score_full({**CASH_BASE,**CASH_CTX.get(ctx,{})}),pa) for pa in pairs)/len(pairs)
    print(f'  {ctx:<10}  {len(pairs):>3}  | {a4:>5.1f}% | {a5:>5.1f}%  | {a6:>5.1f}%  | {at:>5.1f}%')

print(f'\n  MTT   ctx  |  4A   |  5: {best5_c:<18}|  6: {best6_c:<18}|  v7full')
print('-'*90)
ctxs=sorted(set(ctx for ctx,_ in mtt_s))
for ctx in ctxs:
    pairs=[(pa) for c,pa in mtt_s if c==ctx]
    a4=sum(best_acc(score_v(best4m_p),pa) for pa in pairs)/len(pairs)
    a5=sum(best_acc(score_v(best5m_p),pa) for pa in pairs)/len(pairs)
    a6=sum(best_acc(score_v(best6m_p),pa) for pa in pairs)/len(pairs)
    at=sum(best_acc(score_full({**MTT_BASE,**MTT_CTX.get(ctx,{})}),pa) for pa in pairs)/len(pairs)
    print(f'  {ctx:<10}  {len(pairs):>3}  | {a4:>5.1f}% | {a5:>5.1f}%  | {a6:>5.1f}%  | {at:>5.1f}%')

print('\n=== 最良バリアント係数 ===')
print(f'4A  Cash: {best4c_p}')
print(f'4A  MTT:  {best4m_p}')
print(f'{best5_c}  Cash: {best5c_p}')
print(f'{best5_c}  MTT:  {best5m_p}')
print(f'{best6_c}  Cash: {best6c_p}')
print(f'{best6_c}  MTT:  {best6m_p}')
