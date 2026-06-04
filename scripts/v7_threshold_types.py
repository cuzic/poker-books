"""
v7_threshold_types.py — 4係数で各閾値タイプの精度を評価

閾値タイプ:
  T_play  : raise+call vs fold        (今まで評価していたもの)
  T_raise : raise vs call+fold        (3-bet/4-bet判断の上限閾値)
  T_3way  : raise / call / fold の3分類精度

同じ4係数でT_raiseも捌けるか？
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
_GAP=np.zeros(N,dtype=np.float32)
_A=np.zeros(N,dtype=bool)

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

def best_acc_play(scores, play_arr):
    """T_play: play(raise+call) vs fold"""
    pred=scores[np.newaxis,:]>=THRESHOLDS[:,np.newaxis]
    match=(pred==play_arr[np.newaxis,:]).sum(axis=1)
    idx=match.argmax()
    return float(match[idx])/N*100, float(THRESHOLDS[idx])

def best_acc_raise(scores, raise_arr):
    """T_raise: raise vs (call+fold)"""
    pred=scores[np.newaxis,:]>=THRESHOLDS[:,np.newaxis]
    match=(pred==raise_arr[np.newaxis,:]).sum(axis=1)
    idx=match.argmax()
    return float(match[idx])/N*100, float(THRESHOLDS[idx])

def acc_3way(scores, raise_arr, call_arr):
    """
    T_raise と T_call の2閾値で3分類精度を評価
    T_raise > T_call と仮定: score>=T_raise→raise, T_call<=score<T_raise→call, else fold
    """
    best=0.0; best_tr=0.0; best_tc=0.0
    fold_arr = ~raise_arr & ~call_arr
    for ti_r,tr in enumerate(THRESHOLDS):
        for ti_c,tc in enumerate(THRESHOLDS):
            if tc >= tr: continue
            pred_raise = scores>=tr
            pred_call  = (scores>=tc) & (scores<tr)
            pred_fold  = scores<tc
            match=(pred_raise==raise_arr).sum()+(pred_call==call_arr).sum()+(pred_fold==fold_arr).sum()
            # 重複カウントを避けるため正しく計算
            correct = ((pred_raise & raise_arr) | (pred_call & call_arr) | (pred_fold & fold_arr)).sum()
            acc=float(correct)/N*100
            if acc>best:
                best=acc; best_tr=tr; best_tc=tc
    return best, best_tr, best_tc

# ===================================================================
# データ読み込み — raise/call/fold を別々に保持
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

def load_3way(files, game_filter=None, sbr_filter=None, icm_filter=None):
    """(ctx, raise_arr, call_arr, fold_arr) を返す"""
    rows=[]
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
            raise_h=set(acts.get('raise',[])); call_h=set(acts.get('call',[]))
            # raise も call もないシナリオはスキップ
            if not raise_h and not call_h: continue
            # raise のみ (RFI など) も含む
            ra=np.array([h in raise_h for h in ALL_169],dtype=bool)
            ca=np.array([h in call_h  for h in ALL_169],dtype=bool)
            rows.append((ctx,ra,ca))
    return rows

all_files=[
    GTO_DIR/'gto-charts.json', GTO_DIR/'gto-charts-mtt6.json',
    GTO_DIR/'gto-charts-icm.json', GTO_DIR/'gto-charts-mtt9m.json',
    GTO_DIR/'gto-charts-ext.json',
]

# 確定済み4係数
CASH_P=dict(pair_bonus=13,suit_bonus=7,gap_cap=4,a_bonus=4)
MTT_P =dict(pair_bonus=19,suit_bonus=9,gap_cap=5,a_bonus=4)

cash_rows =load_3way(all_files,game_filter={'cash'})
mtt25_rows=load_3way(all_files,game_filter={'mtt'},sbr_filter={25},icm_filter={'chipev'})

print(f'Cash:{len(cash_rows)} MTT25:{len(mtt25_rows)}\n')

# ===================================================================
# コンテキスト別に raise/call の分布を確認
# ===================================================================
def analyze(rows, params, label):
    print(f'\n{"="*70}')
    print(f'{label}')
    print(f'{"="*70}')
    sc=score4(params)

    # RFI 系 (raise only, call=0) と defense 系 (raise+call) を分けて表示
    rfi_ctxs={'RFI'}
    print(f'\n{"ctx":<10} {"N":>4}  {"T_play%":>8} {"T_play_th":>10}  {"T_raise%":>9} {"T_raise_th":>11}  {"T_3way%":>8}  {"raise_n":>8} {"call_n":>8}')
    print('-'*100)

    ctx_groups: dict[str,list]={}
    for ctx,ra,ca in rows:
        ctx_groups.setdefault(ctx,[]).append((ra,ca))

    totals={'play':[],'raise':[],'3way':[]}
    for ctx in sorted(ctx_groups.keys()):
        items=ctx_groups[ctx]
        play_accs=[]; raise_accs=[]; way3_accs=[]
        r_counts=[]; c_counts=[]
        for ra,ca in items:
            play_arr=ra|ca
            # T_play
            pa,_=best_acc_play(sc,play_arr)
            play_accs.append(pa)
            # T_raise (raise vs call+fold)
            ra_acc,_=best_acc_raise(sc,ra)
            raise_accs.append(ra_acc)
            r_counts.append(ra.sum()); c_counts.append(ca.sum())
            # T_3way (only if call_hands exist)
            if ca.any():
                w3,_,_=acc_3way(sc,ra,ca)
                way3_accs.append(w3)

        ap=sum(play_accs)/len(play_accs)
        ar=sum(raise_accs)/len(raise_accs)
        aw=sum(way3_accs)/len(way3_accs) if way3_accs else float('nan')
        avgr=sum(r_counts)/len(r_counts)
        avgc=sum(c_counts)/len(c_counts)

        # 代表シナリオの閾値
        rep_ra,rep_ca=items[len(items)//2]
        _,th_play=best_acc_play(sc,rep_ra|rep_ca)
        _,th_raise=best_acc_raise(sc,rep_ra)

        aw_str=f'{aw:8.2f}%' if not np.isnan(aw) else '       N/A'
        print(f'  {ctx:<10} {len(items):>4}  {ap:>7.2f}% {th_play:>10.1f}  {ar:>8.2f}% {th_raise:>11.1f}  {aw_str}  {avgr:>8.1f} {avgc:>8.1f}')
        totals['play']+=play_accs; totals['raise']+=raise_accs
        if way3_accs: totals['3way']+=way3_accs

    print('-'*100)
    tp=sum(totals['play'])/len(totals['play'])
    tr=sum(totals['raise'])/len(totals['raise'])
    tw=sum(totals['3way'])/len(totals['3way']) if totals['3way'] else float('nan')
    tw_s=f'{tw:8.2f}%' if not np.isnan(tw) else '       N/A'
    print(f'  {"TOTAL":<10} {len(rows):>4}  {tp:>7.2f}%             {tr:>8.2f}%             {tw_s}')

    # T_raise の分布をさらに詳しく: BB/IP/OOP に注目
    print(f'\n--- T_raise の詳細 (raise vs call+fold): {label} ---')
    print('raise が少ないシナリオは T_raise が低精度になりやすい')
    low_raise=[(ctx,ra,ca) for ctx,ra,ca in rows if (ra|ca).any() and ra.sum()<20]
    if low_raise:
        print(f'  raise_hands < 20 のシナリオ数: {len(low_raise)}')
        accs=[best_acc_raise(sc,ra)[0] for _,ra,ca in low_raise]
        print(f'  T_raise 精度 (avg): {sum(accs)/len(accs):.2f}%')

analyze(cash_rows, CASH_P, 'CASH 4係数')
analyze(mtt25_rows, MTT_P, 'MTT SBR=25 4係数')

# ===================================================================
# 代表的シナリオのスコア分布を可視化 (BB defense)
# ===================================================================
print('\n\n=== BB defense: raise/call/fold スコア分布 ===')
print('(スコアが raise > call > fold の順になっているか確認)')
print('Cash 4係数で代表的なBBシナリオを表示\n')

sc=score4(CASH_P)
bb_rows=[(ra,ca) for ctx,ra,ca in cash_rows if ctx=='BB']
if bb_rows:
    ra,ca=bb_rows[0]
    fa=~ra&~ca
    r_scores=sorted(sc[ra],reverse=True)[:5]
    c_scores=sorted(sc[ca],reverse=True)[:5]
    f_scores=sorted(sc[fa],reverse=True)[:5]
    print(f'  raise top5 スコア: {[f"{x:.1f}" for x in r_scores]}')
    print(f'  call  top5 スコア: {[f"{x:.1f}" for x in c_scores]}')
    print(f'  fold  top5 スコア: {[f"{x:.1f}" for x in f_scores]}')
    r_mean=sc[ra].mean(); c_mean=sc[ca].mean() if ca.any() else float('nan')
    f_mean=sc[fa].mean()
    print(f'  raise avg={r_mean:.1f}, call avg={c_mean:.1f}, fold avg={f_mean:.1f}')
    print(f'  → raise_avg > call_avg: {r_mean > c_mean}')
    print(f'  → call_avg  > fold_avg: {c_mean > f_mean}')

    # Cash BB の全シナリオで確認
    print('\nCash BB 全シナリオの raise/call 平均スコア:')
    for i,(ra,ca) in enumerate(bb_rows):
        if not ca.any(): continue
        rm=sc[ra].mean() if ra.any() else 0
        cm=sc[ca].mean()
        print(f'  scenario{i+1}: raise_avg={rm:.1f}, call_avg={cm:.1f}, 順序OK={rm>cm}')
