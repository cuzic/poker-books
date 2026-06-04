"""
v7_full_optuna.py — 全 GTO データを使った v7 係数の再最適化 (高速版)

最適化: スコアを169手分まとめて計算 → numpy で閾値スイープ (約60倍高速)

Cash:  56 シナリオ (SB_RFI/push/partial 除外)
MTT:   90 シナリオ (SBR25 ChipEV, SB_RFI/push/partial 除外)
"""
from __future__ import annotations
import json
import numpy as np
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_DIR = Path('/home/cuzic/poker-books/knowledges/preflop')
N_TRIALS = 2000

# ===================================================================
# ハンドリスト (固定順)
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

HAND_IDX = {h: i for i, h in enumerate(ALL_169)}
N = len(ALL_169)  # 169

# ===================================================================
# スコア関数 (169 手一括計算)
# ===================================================================
# ハンド属性を事前計算
_H    = np.zeros(N, dtype=np.float32)
_L    = np.zeros(N, dtype=np.float32)
_SUIT = np.zeros(N, dtype=bool)
_PAIR = np.zeros(N, dtype=bool)
_GAP  = np.zeros(N, dtype=np.float32)
_A    = np.zeros(N, dtype=bool)   # H == 14
_K    = np.zeros(N, dtype=bool)   # H == 13
_QHI  = np.zeros(N, dtype=bool)   # H == 12
_JHI  = np.zeros(N, dtype=bool)   # H == 11
_LOW  = np.zeros(N, dtype=bool)   # H <= 10  (suited gap cap = low_high_cap)
_LPEN = np.zeros(N, dtype=bool)   # L < 10 かつ H != A (low_pen 対象)
_GAP0 = np.zeros(N, dtype=bool)   # gap == 0 (suited_connector)
_GAP1 = np.zeros(N, dtype=bool)   # gap == 1 (suited_connector1)

for i, h in enumerate(ALL_169):
    if len(h) == 2:
        r = _RANK[h[0]]
        _H[i] = _L[i] = r
        _PAIR[i] = True
    else:
        a, b = _RANK[h[0]], _RANK[h[1]]
        H, L = max(a, b), min(a, b)
        _H[i] = H; _L[i] = L
        _SUIT[i] = h.endswith('s')
        gap = H - L - 1
        _GAP[i] = gap
        _A[i]   = (H == 14)
        _K[i]   = (H == 13)
        _QHI[i] = (H == 12)
        _JHI[i] = (H == 11)
        _LOW[i] = (H <= 10)
        _LPEN[i] = (L < 10 and H != 14)
        _GAP0[i] = (gap == 0)
        _GAP1[i] = (gap == 1)

def score_all(p: dict) -> np.ndarray:
    """169 手のスコアをまとめて計算"""
    s = np.zeros(N, dtype=np.float32)

    # ---- ペア ----
    s[_PAIR] = _H[_PAIR] + _L[_PAIR] + p['pair_bonus']

    # ---- スーテッド ----
    mask_s = _SUIT & ~_PAIR
    if mask_s.any():
        H  = _H[mask_s]
        L  = _L[mask_s]
        g  = _GAP[mask_s]
        ab = np.where(_A[mask_s], p['a_blocker'], 0.0)
        kb = np.where(_K[mask_s], p['k_blocker'], 0.0)
        gc = np.where(_A[mask_s],  np.minimum(g, p['a_suited_gap_cap']),
             np.where(_K[mask_s],  np.minimum(g, 2),
             np.where(_QHI[mask_s],np.minimum(g, 3),
             np.where(_JHI[mask_s],np.minimum(g, 4),
                                   np.minimum(g, p['low_high_cap'])))))
        sc = np.where(_GAP0[mask_s], p['suited_connector'],
             np.where(_GAP1[mask_s], p['suited_connector1'], 0.0))
        s[mask_s] = H + L + p['suit_bonus'] - gc + ab + kb + sc

    # ---- オフスーツ ----
    mask_o = ~_SUIT & ~_PAIR
    if mask_o.any():
        H  = _H[mask_o]
        L  = _L[mask_o]
        g  = _GAP[mask_o]
        ab = np.where(_A[mask_o], p['a_blocker'], 0.0)
        kb = np.where(_K[mask_o], p['k_blocker'], 0.0)
        lp = np.where(_LPEN[mask_o], p['low_pen'], 0.0)
        gc = np.where(_A[mask_o], np.minimum(g, p['a_gap_cap']),
             np.where(_K[mask_o], np.minimum(g, p['k_gap_cap']),
                                  g))
        s[mask_o] = H + L - gc - lp + ab + kb

    return s

# 閾値配列 (10.0 〜 44.0 を 0.5 刻み)
THRESHOLDS = np.arange(10.0, 44.5, 0.5, dtype=np.float32)  # shape (69,)

def best_acc_vec(scores: np.ndarray, play_arr: np.ndarray) -> float:
    """numpy ベクトル化で最適閾値精度を返す"""
    # predicted[i, j] = (scores[j] >= THRESHOLDS[i])  shape: (69, 169)
    predicted = scores[np.newaxis, :] >= THRESHOLDS[:, np.newaxis]
    # match[i] = number of correct predictions at threshold i
    match = (predicted == play_arr[np.newaxis, :]).sum(axis=1)
    return float(match.max()) / N * 100

# ===================================================================
# データ読み込み
# ===================================================================
EXCLUDE_CTX = {'push', 'SB_RFI'}

def _infer_ctx(key, meta=None):
    if meta and 'ctx' in meta:
        return meta['ctx']
    k = key.upper()
    if 'PUSH' in k:     return 'push'
    if any(x in k for x in ['SQ_','SQUEEZE','_SB_COLD','_BTN_SB','_CO_BTN','_O_','MW']):
        if k.startswith('BB'): return 'MW_BB'
        if k.startswith('SB'): return 'MW_SB'
        return 'MW_IP'
    if k.endswith('_RFI'):
        return 'SB_RFI' if 'SB_' in k else 'RFI'
    if k.startswith('BB_') or k.startswith('BVB_BB'): return 'BB'
    if k.startswith('SB_VS'):                          return 'OOP'
    if 'LIMP' in k:                                    return 'BB'
    return 'IP'

def load_scenarios(files, game_filter=None, sbr_filter=None, icm_filter=None):
    """(ctx, play_arr) のリストを返す (play_arr = numpy bool shape 169)"""
    scenarios = []
    for fpath in files:
        if not fpath.exists():
            continue
        with open(fpath) as f:
            d = json.load(f)
        for key, val in d.items():
            if isinstance(val, dict) and 'meta' in val:
                meta    = val['meta']
                partial = meta.get('partial', False)
                ctx     = meta.get('ctx', _infer_ctx(key))
                game    = meta.get('game', 'cash')
                sbr     = meta.get('sbr')
                icm     = meta.get('icm', 'chipev')
            elif isinstance(val, dict) and 'actions' in val:
                partial = val.get('partial', False)
                ctx     = _infer_ctx(key)
                game    = 'cash'; sbr = None; icm = 'chipev'
                meta    = {}
            else:
                continue

            if partial:            continue
            if ctx in EXCLUDE_CTX: continue
            if game_filter and game not in game_filter:  continue
            if sbr_filter  and sbr  not in sbr_filter:   continue
            if icm_filter  and icm  not in icm_filter:   continue

            acts = val.get('actions', {})
            play_hands = set(acts.get('raise', [])) | set(acts.get('call', []))
            if not play_hands:
                continue

            play_arr = np.array([h in play_hands for h in ALL_169], dtype=bool)
            scenarios.append((ctx, play_arr))
    return scenarios

# ===================================================================
# Optuna
# ===================================================================
PARAM_RANGES = {
    'suit_bonus':        (3, 9),
    'k_blocker':         (0, 3),
    'a_blocker':         (0, 5),
    'low_pen':           (0, 6),
    'a_gap_cap':         (0, 9),
    'k_gap_cap':         (0, 9),
    'pair_bonus':        (8, 18),
    'a_suited_gap_cap':  (0, 9),
    'suited_connector':  (0, 6),
    'suited_connector1': (0, 5),
    'low_high_cap':      (1, 9),
}
CTX_PARAMS = ['suit_bonus','suited_connector','suited_connector1',
              'low_pen','pair_bonus','a_blocker']
CONTEXTS   = ['RFI','BB','IP','OOP','MW_BB','MW_SB','MW_IP']

def make_objective(scenarios):
    def objective(trial):
        base = {k: trial.suggest_int(k, lo, hi) for k, (lo, hi) in PARAM_RANGES.items()}
        overrides = {}
        for ctx in CONTEXTS:
            ov = {}
            for pk in CTX_PARAMS:
                if trial.suggest_categorical(f'{ctx}_{pk}_use', [True, False]):
                    lo, hi = {'suit_bonus':(3,9),'suited_connector':(0,6),
                              'suited_connector1':(0,5),'low_pen':(0,6),
                              'pair_bonus':(8,18),'a_blocker':(0,5)}[pk]
                    ov[pk] = trial.suggest_int(f'{ctx}_{pk}', lo, hi)
            overrides[ctx] = ov

        total = 0.0
        for ctx, play_arr in scenarios:
            p      = {**base, **overrides.get(ctx, {})}
            scores = score_all(p)
            total += best_acc_vec(scores, play_arr)
        return total / len(scenarios)
    return objective

def extract_result(best_params):
    base_p = {k: best_params[k] for k in PARAM_RANGES}
    ctx_ov = {}
    for ctx in CONTEXTS:
        ov = {}
        for pk in CTX_PARAMS:
            if best_params.get(f'{ctx}_{pk}_use') and f'{ctx}_{pk}' in best_params:
                ov[pk] = best_params[f'{ctx}_{pk}']
        ctx_ov[ctx] = ov
    return base_p, ctx_ov

def print_result(label, n_scen, best_val, base_p, ctx_ov, scenarios):
    print(f'\n{"="*70}')
    print(f'{label}  ({n_scen} scenarios, 最良精度: {best_val:.2f}%)')
    print(f'{"="*70}')
    print('\nベース係数:')
    for k, v in base_p.items():
        print(f'  {k:<22} = {v}')
    print('\nコンテキスト上書き係数:')
    for ctx in CONTEXTS:
        ov  = ctx_ov.get(ctx, {})
        cnt = sum(1 for c, _ in scenarios if c == ctx)
        if cnt == 0:
            continue
        if ov:
            print(f'\n  [{ctx}] ({cnt} scenarios)')
            for k, v in ov.items():
                diff = v - base_p[k]
                print(f'    {k:<22} = {v}  (base={base_p[k]}, Δ={diff:+d})')
        else:
            print(f'\n  [{ctx}] ({cnt} scenarios) — base 使用')

    print('\nコンテキスト別精度:')
    ctx_acc: dict[str, list] = {}
    for ctx, play_arr in scenarios:
        p      = {**base_p, **ctx_ov.get(ctx, {})}
        scores = score_all(p)
        ctx_acc.setdefault(ctx, []).append(best_acc_vec(scores, play_arr))
    for ctx, accs in sorted(ctx_acc.items()):
        print(f'  {ctx:<10} {len(accs):>3} scenarios:  {sum(accs)/len(accs):.1f}%')

# ===================================================================
# メイン
# ===================================================================
all_files = [
    GTO_DIR / 'gto-charts.json',
    GTO_DIR / 'gto-charts-mtt6.json',
    GTO_DIR / 'gto-charts-icm.json',
    GTO_DIR / 'gto-charts-mtt9m.json',
    GTO_DIR / 'gto-charts-ext.json',
]

print(f'Optuna v7 full (vectorized), n_trials={N_TRIALS}\n')

# ---- Cash ----
cash_s = load_scenarios(all_files, game_filter={'cash'})
print(f'=== CASH ({len(cash_s)} scenarios) ===')

study_cash = optuna.create_study(
    direction='maximize', sampler=optuna.samplers.TPESampler(seed=42))
study_cash.optimize(make_objective(cash_s), n_trials=N_TRIALS, n_jobs=1)

base_c, ov_c = extract_result(study_cash.best_params)
print_result('CASH', len(cash_s), study_cash.best_value, base_c, ov_c, cash_s)

# ---- MTT 6m SBR25 ChipEV ----
mtt_s = load_scenarios(all_files, game_filter={'mtt'}, sbr_filter={25}, icm_filter={'chipev'})
print(f'\n\n=== MTT 6m SBR25 ChipEV ({len(mtt_s)} scenarios) ===')

study_mtt = optuna.create_study(
    direction='maximize', sampler=optuna.samplers.TPESampler(seed=42))
study_mtt.optimize(make_objective(mtt_s), n_trials=N_TRIALS, n_jobs=1)

base_m, ov_m = extract_result(study_mtt.best_params)
print_result('MTT 6m SBR25', len(mtt_s), study_mtt.best_value, base_m, ov_m, mtt_s)

# ---- Cash vs MTT 差分 ----
print(f'\n\n{"="*70}')
print('Cash vs MTT ベース係数差分')
print(f'{"="*70}')
print(f'  {"係数":<22} {"Cash":>6} {"MTT":>6} {"差":>5}')
print('-'*46)
for k in PARAM_RANGES:
    cv, mv = base_c[k], base_m[k]
    diff   = mv - cv
    flag   = ' ★' if abs(diff) >= 2 else (' △' if diff else '')
    print(f'  {k:<22} {cv:>6} {mv:>6} {diff:>+5}{flag}')
