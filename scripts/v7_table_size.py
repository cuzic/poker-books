"""
v7_table_size.py — 6max / 8max / 9max の4係数比較

同じ係数で全テーブルサイズをカバーできるか？
閾値だけ違うのか、係数も変わるのか？
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_DIR = Path('/home/cuzic/poker-books/knowledges/preflop')
N_TRIALS = 1000

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
_GAP=np.zeros(N,dtype=np.float32); _A=np.zeros(N,dtype=bool)

for i,h in enumerate(ALL_169):
    if len(h)==2:
        r=_RANK[h[0]]; _H[i]=_L[i]=r; _PAIR[i]=True
    else:
        a,b=_RANK[h[0]],_RANK[h[1]]; H,L=max(a,b),min(a,b)
        _H[i]=H; _L[i]=L; _SUIT[i]=h.endswith('s')
        _GAP[i]=H-L-1; _A[i]=(H==14)

THRESHOLDS=np.arange(8.0,50.0,0.5,dtype=np.float32)

def score4(p):
    s=np.zeros(N,dtype=np.float32)
    s[_PAIR]=_H[_PAIR]+_L[_PAIR]+p['pair_bonus']
    mask_s=_SUIT&~_PAIR
    if mask_s.any():
        gc=np.minimum(_GAP[mask_s],p['gap_cap'])
        ab=np.where(_A[mask_s],p['a_bonus'],0.0)
        s[mask_s]=_H[mask_s]+_L[mask_s]+p['suit_bonus']-gc+ab
    mask_o=~_SUIT&~_PAIR
    if mask_o.any():
        gc=np.minimum(_GAP[mask_o],p['gap_cap'])
        ab=np.where(_A[mask_o],p['a_bonus'],0.0)
        s[mask_o]=_H[mask_o]+_L[mask_o]-gc+ab
    return s

def best_acc(scores,play_arr):
    pred=scores[np.newaxis,:]>=THRESHOLDS[:,np.newaxis]
    match=(pred==play_arr[np.newaxis,:]).sum(axis=1)
    idx=match.argmax()
    return float(match[idx])/N*100, float(THRESHOLDS[idx])

RANGES4=dict(pair_bonus=(8,22),suit_bonus=(2,10),gap_cap=(2,8),a_bonus=(0,8))

def optuna4(scenarios, n_trials=N_TRIALS, seed=42):
    if not scenarios: return None, 0
    def obj(trial):
        p={k:trial.suggest_int(k,lo,hi) for k,(lo,hi) in RANGES4.items()}
        return sum(best_acc(score4(p),pa)[0] for _,pa in scenarios)/len(scenarios)
    study=optuna.create_study(direction='maximize',
                              sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(obj,n_trials=n_trials,n_jobs=1)
    return study.best_params, study.best_value

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

def load_all(files):
    rows=[]
    for fpath in files:
        if not fpath.exists(): continue
        with open(fpath) as f: d=json.load(f)
        for key,val in d.items():
            if isinstance(val,dict) and 'meta' in val:
                meta=val['meta']; partial=meta.get('partial',False)
                ctx=meta.get('ctx',_infer_ctx(key)); game=meta.get('game','cash')
                sbr=meta.get('sbr'); icm=meta.get('icm','chipev')
                table=meta.get('table',6)
            elif isinstance(val,dict) and 'actions' in val:
                partial=val.get('partial',False); ctx=_infer_ctx(key)
                game='cash'; sbr=None; icm='chipev'; table=6
            else: continue
            if partial: continue
            if ctx in EXCLUDE_CTX: continue
            acts=val.get('actions',{})
            play_hands=set(acts.get('raise',[]))|set(acts.get('call',[]))
            if not play_hands: continue
            pa=np.array([h in play_hands for h in ALL_169],dtype=bool)
            rows.append(dict(ctx=ctx,pa=pa,game=game,sbr=sbr,icm=icm,table=table))
    return rows

all_files=[
    GTO_DIR/'gto-charts.json', GTO_DIR/'gto-charts-mtt6.json',
    GTO_DIR/'gto-charts-icm.json', GTO_DIR/'gto-charts-mtt9m.json',
    GTO_DIR/'gto-charts-ext.json',
]
rows=load_all(all_files)

# テーブルサイズ別のシナリオ数確認
from collections import Counter
tbl_cnt=Counter(r['table'] for r in rows if r['game']=='mtt')
print('MTT テーブルサイズ別シナリオ数:')
for t,n in sorted(tbl_cnt.items()):
    print(f'  {t}max: {n}')

# ===================================================================
# 1. テーブルサイズ別: chipev, SBR=25 前後 (SBR20-30)
# ===================================================================
print('\n=== テーブルサイズ別: ChipEV, SBR20-30 ===')
for table in [6,8,9]:
    s=[(r['ctx'],r['pa']) for r in rows
       if r['game']=='mtt' and r['icm']=='chipev'
       and r['sbr'] and 20<=r['sbr']<=30 and r['table']==table]
    if not s:
        print(f'  {table}max: データなし')
        continue
    p,acc=optuna4(s)
    print(f'  {table}max ({len(s):3d}シナリオ): {acc:.2f}%  {p}')

# ===================================================================
# 2. テーブルサイズ別: chipev, 全SBR
# ===================================================================
print('\n=== テーブルサイズ別: ChipEV 全SBR ===')
params_by_table={}
for table in [6,8,9]:
    s=[(r['ctx'],r['pa']) for r in rows
       if r['game']=='mtt' and r['icm']=='chipev' and r['table']==table]
    if len(s)<5:
        print(f'  {table}max: データ不足 ({len(s)})')
        continue
    p,acc=optuna4(s)
    params_by_table[table]=(p,acc,len(s))
    print(f'  {table}max ({len(s):3d}シナリオ): {acc:.2f}%  {p}')

# ===================================================================
# 3. コンテキスト別精度: 6max vs 9max (確定係数で)
# ===================================================================
print('\n=== コンテキスト別精度: 6max vs 9max (ChipEV 全SBR) ===')
P6=params_by_table.get(6,(None,0,0))[0]
P9=params_by_table.get(9,(None,0,0))[0]
if P6 and P9:
    sc6=score4(P6); sc9=score4(P9)
    ctxs=sorted(set(r['ctx'] for r in rows if r['game']=='mtt'))
    print(f'  {"ctx":<10} {"N6":>4} {"6max%":>8}  {"N9":>4} {"9max%":>8}')
    print('-'*50)
    for ctx in ctxs:
        s6=[(r['ctx'],r['pa']) for r in rows
            if r['game']=='mtt' and r['icm']=='chipev' and r['table']==6 and r['ctx']==ctx]
        s9=[(r['ctx'],r['pa']) for r in rows
            if r['game']=='mtt' and r['icm']=='chipev' and r['table']==9 and r['ctx']==ctx]
        if not s6 and not s9: continue
        a6=sum(best_acc(sc6,pa)[0] for _,pa in s6)/len(s6) if s6 else float('nan')
        a9=sum(best_acc(sc9,pa)[0] for _,pa in s9)/len(s9) if s9 else float('nan')
        n6=len(s6); n9=len(s9)
        a6s=f'{a6:7.2f}%' if not np.isnan(a6) else '     N/A'
        a9s=f'{a9:7.2f}%' if not np.isnan(a9) else '     N/A'
        print(f'  {ctx:<10} {n6:>4} {a6s}  {n9:>4} {a9s}')

# ===================================================================
# 4. 9max で 6max 係数を使ったらどうなるか
# ===================================================================
print('\n=== 6max 係数を 9max に適用したときの精度 ===')
if P6:
    sc6=score4(P6)
    for table in [8,9]:
        s=[(r['ctx'],r['pa']) for r in rows
           if r['game']=='mtt' and r['icm']=='chipev' and r['table']==table]
        if not s: continue
        acc=sum(best_acc(sc6,pa)[0] for _,pa in s)/len(s)
        p_own,acc_own=optuna4(s)
        print(f'  {table}max: 6max係数適用={acc:.2f}%  専用係数={acc_own:.2f}%  差={acc_own-acc:+.2f}%')
        print(f'         専用係数: {p_own}')

# ===================================================================
# 5. SBR 別 閾値シフト: 9max vs 6max (同じ係数)
# ===================================================================
print('\n=== SBR別 RFI 閾値: 6max vs 9max (共通係数 pair=19,suit=9,gap=5,a=4) ===')
COMMON=dict(pair_bonus=19,suit_bonus=9,gap_cap=5,a_bonus=4)
sc=score4(COMMON)
sbr_vals=sorted(set(r['sbr'] for r in rows if r['game']=='mtt' and r['sbr']))
print(f'  {"SBR":>5}  {"6max_RFI_th":>12} {"9max_RFI_th":>12}  {"差":>5}')
print('-'*45)
for sbr in sbr_vals:
    ths6=[best_acc(sc,pa)[1] for r in rows
          if r['game']=='mtt' and r['sbr']==sbr and r['icm']=='chipev'
          and r['table']==6 and r['ctx']=='RFI'
          for pa in [r['pa']]]
    ths9=[best_acc(sc,pa)[1] for r in rows
          if r['game']=='mtt' and r['sbr']==sbr and r['icm']=='chipev'
          and r['table']==9 and r['ctx']=='RFI'
          for pa in [r['pa']]]
    if not ths6 and not ths9: continue
    t6=sum(ths6)/len(ths6) if ths6 else float('nan')
    t9=sum(ths9)/len(ths9) if ths9 else float('nan')
    diff=t9-t6 if not (np.isnan(t6) or np.isnan(t9)) else float('nan')
    t6s=f'{t6:11.1f}' if not np.isnan(t6) else '        N/A'
    t9s=f'{t9:11.1f}' if not np.isnan(t9) else '        N/A'
    ds=f'{diff:+5.1f}' if not np.isnan(diff) else '  N/A'
    print(f'  {sbr:>5}  {t6s} {t9s}  {ds}')

# ===================================================================
# 6. Cash vs 6max vs 9max: 係数差分まとめ
# ===================================================================
print('\n=== Cash / 6max / 9max 係数差分まとめ ===')
CASH_P=dict(pair_bonus=13,suit_bonus=7,gap_cap=4,a_bonus=4)
print(f'  {"係数":<14}  {"Cash":>6}  {"6max":>6}  {"9max":>6}  {"6→9差":>7}')
print('-'*48)
P9_=params_by_table.get(9,(None,0,0))[0] or {}
P6_=params_by_table.get(6,(None,0,0))[0] or {}
for k in ['pair_bonus','suit_bonus','gap_cap','a_bonus']:
    cv=CASH_P[k]; v6=P6_.get(k,'?'); v9=P9_.get(k,'?')
    diff=v9-v6 if isinstance(v9,int) and isinstance(v6,int) else '?'
    flag=' ★' if isinstance(diff,int) and abs(diff)>=2 else ''
    print(f'  {k:<14}  {cv:>6}  {v6:>6}  {v9:>6}  {diff:>+6}{flag}')
