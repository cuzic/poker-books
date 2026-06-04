"""
v7_4coeff_mtt.py — 4係数式を MTT SBR別 / ICMフェーズ別で検証

検証する軸:
  1. SBR別 (8/10/13/15/20/25/30/40) — 係数が変わるか？閾値だけか？
  2. ICMフェーズ別 (chipev/pct25/pct37/pct50/ft) — 係数が変わるか？
  3. Cash vs MTT 4係数比較
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_DIR = Path('/home/cuzic/poker-books/knowledges/preflop')
N_TRIALS = 800  # SBR/ICM 別なので各グループが小さい→少ないtrials で十分

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

for i,h in enumerate(ALL_169):
    if len(h)==2:
        r=_RANK[h[0]]; _H[i]=_L[i]=r; _PAIR[i]=True
    else:
        a,b=_RANK[h[0]],_RANK[h[1]]; H,L=max(a,b),min(a,b)
        _H[i]=H; _L[i]=L; _SUIT[i]=h.endswith('s')
        gap=H-L-1; _GAP[i]=gap
        _A[i]=(H==14); _K[i]=(H==13)
        _LPEN[i]=(L<10 and H!=14); _GAP0[i]=(gap==0); _GAP1[i]=(gap==1)

THRESHOLDS=np.arange(8.0,46.0,0.5,dtype=np.float32)

def best_acc(scores,play_arr):
    pred=scores[np.newaxis,:]>=THRESHOLDS[:,np.newaxis]
    return float((pred==play_arr[np.newaxis,:]).sum(axis=1).max())/N*100

def best_threshold(scores,play_arr):
    pred=scores[np.newaxis,:]>=THRESHOLDS[:,np.newaxis]
    idx=(pred==play_arr[np.newaxis,:]).sum(axis=1).argmax()
    return float(THRESHOLDS[idx])

# ===================================================================
# 4係数スコア関数
# ===================================================================
def score4(p):
    """pair_bonus, suit_bonus, gap_cap, a_bonus"""
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

RANGES4=dict(pair_bonus=(8,20),suit_bonus=(2,10),gap_cap=(2,8),a_bonus=(0,7))

def optuna4(scenarios, n_trials=N_TRIALS, seed=42):
    if not scenarios: return None, None, 0
    def obj(trial):
        p={k:trial.suggest_int(k,lo,hi) for k,(lo,hi) in RANGES4.items()}
        return sum(best_acc(score4(p),pa) for _,pa in scenarios)/len(scenarios)
    study=optuna.create_study(direction='maximize',
                              sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(obj,n_trials=n_trials,n_jobs=1)
    bp=study.best_params
    # 最良係数で各シナリオの best_threshold を記録
    s=score4(bp)
    thresholds=[best_threshold(s,pa) for _,pa in scenarios]
    return bp, thresholds, study.best_value

# ===================================================================
# データ読み込み (全フィールド返す)
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
    """全シナリオを (ctx, play_arr, game, sbr, icm, table) で返す"""
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
                game='cash'; sbr=None; icm='chipev'; table=6; meta={}
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
all_rows=load_all(all_files)
print(f'全シナリオ: {len(all_rows)}\n')

# ===================================================================
# 1. Cash vs MTT SBR25 基本比較 (再確認)
# ===================================================================
cash_s=[(r['ctx'],r['pa']) for r in all_rows if r['game']=='cash']
mtt25_s=[(r['ctx'],r['pa']) for r in all_rows
          if r['game']=='mtt' and r['sbr']==25 and r['icm']=='chipev']

print('=== Cash vs MTT SBR=25 ChipEV ===')
cash_p,_,cash_acc=optuna4(cash_s,n_trials=1000)
mtt25_p,_,mtt25_acc=optuna4(mtt25_s,n_trials=1000)
print(f'Cash  ({len(cash_s):3d}シナリオ): {cash_acc:.2f}%  係数={cash_p}')
print(f'MTT25 ({len(mtt25_s):3d}シナリオ): {mtt25_acc:.2f}%  係数={mtt25_p}')

# ===================================================================
# 2. MTT SBR別 (6m chipev)
# ===================================================================
print('\n=== MTT 6m ChipEV: SBR別 ===')
sbr_values=sorted(set(r['sbr'] for r in all_rows
                       if r['game']=='mtt' and r['icm']=='chipev' and r['sbr']))
print(f'{"SBR":>5} {"N":>4}  {"精度":>7}  pair suit gap  a_b')
sbr_params={}
for sbr in sbr_values:
    s=[(r['ctx'],r['pa']) for r in all_rows
       if r['game']=='mtt' and r['sbr']==sbr and r['icm']=='chipev']
    if len(s)<5: continue
    p,ths,acc=optuna4(s,n_trials=N_TRIALS)
    sbr_params[sbr]=(p,acc,len(s))
    pb=p['pair_bonus']; sb=p['suit_bonus']; gc=p['gap_cap']; ab=p['a_bonus']
    print(f'  {sbr:>3}  {len(s):>4}  {acc:>6.2f}%  {pb:>4} {sb:>4} {gc:>3} {ab:>4}')

# ===================================================================
# 3. ICM フェーズ別 (MTT 6m SBR=25)
# ===================================================================
print('\n=== MTT 6m SBR=25: ICMフェーズ別 ===')
icm_phases=sorted(set(r['icm'] for r in all_rows
                       if r['game']=='mtt' and r['sbr']==25))
print(f'{"フェーズ":>10} {"N":>4}  {"精度":>7}  pair suit gap  a_b  最良閾値(avg)')
icm_params={}
for icm in icm_phases:
    s=[(r['ctx'],r['pa']) for r in all_rows
       if r['game']=='mtt' and r['sbr']==25 and r['icm']==icm]
    if len(s)<3: continue
    p,ths,acc=optuna4(s,n_trials=N_TRIALS)
    icm_params[icm]=(p,acc,len(s),ths)
    pb=p['pair_bonus']; sb=p['suit_bonus']; gc=p['gap_cap']; ab=p['a_bonus']
    avg_th=sum(ths)/len(ths) if ths else 0
    print(f'  {icm:>10}  {len(s):>4}  {acc:>6.2f}%  {pb:>4} {sb:>4} {gc:>3} {ab:>4}  {avg_th:>6.1f}')

# ===================================================================
# 4. ICM フェーズ別: RFIシナリオの閾値変化に注目
# ===================================================================
print('\n=== MTT RFI シナリオの閾値変化 (SBR=25, 4係数固定=mtt25_p) ===')
print('フェーズごとに同じ係数で閾値がどう変わるか')
rfi_ctxs={'RFI'}
print(f'{"フェーズ":>10}  {"RFI閾値(avg)":>12}  {"全体閾値(avg)":>12}  N(RFI)')
for icm in icm_phases:
    s_all=[(r['ctx'],r['pa']) for r in all_rows
            if r['game']=='mtt' and r['sbr']==25 and r['icm']==icm]
    if len(s_all)<3: continue
    sc=score4(mtt25_p)
    rfi_ths=[best_threshold(sc,pa) for ctx,pa in s_all if ctx in rfi_ctxs]
    all_ths=[best_threshold(sc,pa) for _,pa in s_all]
    avg_rfi=sum(rfi_ths)/len(rfi_ths) if rfi_ths else float('nan')
    avg_all=sum(all_ths)/len(all_ths)
    print(f'  {icm:>10}  {avg_rfi:>12.1f}  {avg_all:>12.1f}  {len(rfi_ths):>5}')

# ===================================================================
# 5. SBR別の係数安定性まとめ
# ===================================================================
print('\n=== SBR別係数まとめ: 係数は安定しているか？ ===')
if sbr_params:
    print(f'{"SBR":>5}  {"pair":>5} {"suit":>5} {"gap":>4} {"a_b":>4}  {"精度":>7}')
    for sbr,(p,acc,n) in sorted(sbr_params.items()):
        print(f'  {sbr:>3}  {p["pair_bonus"]:>5} {p["suit_bonus"]:>5} {p["gap_cap"]:>4} {p["a_bonus"]:>4}  {acc:>6.2f}%')

# ===================================================================
# 6. Cash と MTT で係数がどう違うか (集約)
# ===================================================================
print('\n=== Cash vs MTT 4係数差分まとめ ===')
print(f'{"係数":<14}  {"Cash":>6}  {"MTT25":>6}  {"差":>5}')
print('-'*38)
for k in ['pair_bonus','suit_bonus','gap_cap','a_bonus']:
    cv=cash_p[k]; mv=mtt25_p[k]; diff=mv-cv
    flag=' ★' if abs(diff)>=2 else (' △' if diff else '')
    print(f'  {k:<14}  {cv:>6}  {mv:>6}  {diff:>+5}{flag}')

print('\n完了')
