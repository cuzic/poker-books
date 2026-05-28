"""
v6_context_analysis.py — Optuna によるコンテキスト別係数最適化

カテゴリ別に suited_bonus / offsuit_penalty / pair_bonus 等を最適化し、
RFI → defense で係数がどう変わるかを検証する。

カテゴリ:
  1. RFI       : LJ/HJ/CO/BTN オープン
  2. SB RFI    : SB (raise+limp を "play" として扱う)
  3. DEF IP    : IP が vs オープンで 3bet/call/fold
                 (HJ_vs_LJ / CO_vs_LJ / CO_vs_HJ /
                  BTN_vs_LJ / BTN_vs_HJ / BTN_vs_CO)
  4. DEF OOP   : SB が vs オープンで 3bet/fold
  5. DEF BB    : BB が vs オープンで 3bet/call/fold
  6. ALL       : 全シナリオ共通の最適係数

Usage:
  uv run --with optuna cash-postflop/v6_context_analysis.py
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

GTO_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json')
N_TRIALS  = 400   # カテゴリごとのトライアル数

# ---------------------------------------------------------------------------
# ハンドユーティリティ
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# スコア関数 (パラメータ辞書を受け取る)
# ---------------------------------------------------------------------------
def score(hand: str, p: dict) -> float:
    H, L, suited, pair = parse(hand)
    if pair:
        return H + L + p['pair_bonus']

    gap = H - L - 1
    ab  = p['a_blocker'] if H == 14 else 0.0
    kb  = p['k_blocker'] if H == 13 else 0.0  # AK は ab のみ (二重加算なし)

    if suited:
        if H == 14:   gc = 0
        elif H == 13: gc = min(gap, 2)
        elif H == 12: gc = min(gap, 3)
        elif H == 11: gc = min(gap, 4)
        else:         gc = gap
        return H + L + p['suit_bonus'] - gc + ab + kb

    # offsuit
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

# ---------------------------------------------------------------------------
# GTO データ
# ---------------------------------------------------------------------------
with open(GTO_PATH) as f:
    GTO = json.load(f)

def gset(key, action):
    return set(GTO[key]['actions'].get(action, []))

# シナリオ定義: {name: gt_set}
# gt_set は「play (参加) するハンド集合」
def build_scenarios() -> dict[str, dict[str, set]]:
    s = {}
    # 1. RFI
    for k in ['LJ_RFI','HJ_RFI','CO_RFI','BTN_RFI']:
        s[k] = {'play': gset(k,'raise'), 'label': 'RFI'}

    # 2. SB RFI (raise + limp = play)
    s['SB_RFI'] = {'play': gset('BvB_SB_strategy','raise')
                         | gset('BvB_SB_strategy','limp')
                         | gset('BvB_SB_strategy','mixed_limp'),
                   'label': 'SB_RFI'}

    # 3. DEF IP: raise=3bet, limp=call
    for k in ['HJ_vs_LJ','CO_vs_LJ','CO_vs_HJ','BTN_vs_LJ','BTN_vs_HJ','BTN_vs_CO']:
        s[k] = {'play': gset(k,'raise') | gset(k,'limp'), 'label': 'DEF_IP'}

    # 4. DEF OOP: SB 3bet-or-fold
    for k in ['SB_vs_LJ','SB_vs_HJ','SB_vs_CO','SB_vs_BTN']:
        s[k] = {'play': gset(k,'raise'), 'label': 'DEF_OOP'}

    # 5. DEF BB: raise=3bet, limp=call
    for k in ['BB_vs_LJ','BB_vs_HJ','BB_vs_CO','BB_vs_BTN','BvB_BB_vs_SB_raise']:
        s[k] = {'play': gset(k,'raise') | gset(k,'limp'), 'label': 'DEF_BB'}

    return s

ALL_SCENARIOS = build_scenarios()

CATEGORY_KEYS = {
    'RFI':     [k for k,v in ALL_SCENARIOS.items() if v['label']=='RFI'],
    'SB_RFI':  ['SB_RFI'],
    'DEF_IP':  [k for k,v in ALL_SCENARIOS.items() if v['label']=='DEF_IP'],
    'DEF_OOP': [k for k,v in ALL_SCENARIOS.items() if v['label']=='DEF_OOP'],
    'DEF_BB':  [k for k,v in ALL_SCENARIOS.items() if v['label']=='DEF_BB'],
    'ALL':     list(ALL_SCENARIOS.keys()),
}

# ---------------------------------------------------------------------------
# 精度計算: 最適閾値を探索して正答率を返す
# ---------------------------------------------------------------------------
def best_acc(score_fn, gt: set) -> float:
    best = -1.0
    t = 10.0
    while t <= 44.0:
        correct = sum(1 for h in HANDS if (score_fn(h) >= t) == (h in gt))
        a = correct / len(HANDS)
        if a > best:
            best = a
        t += 0.5
    return best * 100

def category_acc(keys: list[str], p: dict) -> float:
    fn = lambda h: score(h, p)
    return sum(best_acc(fn, ALL_SCENARIOS[k]['play']) for k in keys) / len(keys)

# ---------------------------------------------------------------------------
# v5final ベースライン
# ---------------------------------------------------------------------------
V5 = dict(suit_bonus=5, k_blocker=0, a_blocker=3,
          low_pen=3, a_gap_cap=100, k_gap_cap=100, pair_bonus=12)

# ---------------------------------------------------------------------------
# Optuna 最適化
# ---------------------------------------------------------------------------
def make_objective(keys: list[str]):
    def objective(trial: optuna.Trial) -> float:
        p = {
            'suit_bonus':  trial.suggest_int('suit_bonus', 3, 8),
            'k_blocker':   trial.suggest_int('k_blocker',  0, 2),
            'a_blocker':   trial.suggest_int('a_blocker',  1, 4),
            'low_pen':     trial.suggest_int('low_pen',    0, 4),
            'a_gap_cap':   trial.suggest_int('a_gap_cap',  0, 8),
            'k_gap_cap':   trial.suggest_int('k_gap_cap',  0, 8),
            'pair_bonus':  trial.suggest_int('pair_bonus', 8, 14),
        }
        return category_acc(keys, p)
    return objective

def optimize(cat_name: str, keys: list[str]) -> tuple[dict, float]:
    study = optuna.create_study(direction='maximize',
                                sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(make_objective(keys), n_trials=N_TRIALS, show_progress_bar=False)
    return study.best_params, study.best_value

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f'Optuna TPE, n_trials={N_TRIALS} per category\n')

    results: dict[str, tuple[dict, float]] = {}

    for cat, keys in CATEGORY_KEYS.items():
        sys.stdout.write(f'  最適化中: {cat} ({len(keys)} scenarios)... ')
        sys.stdout.flush()
        best_p, best_a = optimize(cat, keys)
        v5_a = category_acc(keys, V5)
        results[cat] = (best_p, best_a, v5_a)
        delta = best_a - v5_a
        print(f'v5={v5_a:.1f}%  best={best_a:.1f}%  Δ={delta:+.1f}%')

    # =========================================================
    # 係数比較表
    # =========================================================
    print('\n\n' + '='*100)
    print('カテゴリ別 最適係数 (v5final との差分)')
    print('='*100)
    params_keys = ['suit_bonus','k_blocker','a_blocker','low_pen','a_gap_cap','k_gap_cap','pair_bonus']
    v5_vals     = [V5[k] for k in params_keys]

    header = f'{"係数":<18} {"v5final":>8}'
    for cat in CATEGORY_KEYS:
        header += f'  {cat:>10}'
    print(header)
    print('-'*100)

    for i, pk in enumerate(params_keys):
        row = f'{pk:<18} {v5_vals[i]:>8}'
        for cat in CATEGORY_KEYS:
            best_p, _, _ = results[cat]
            v = best_p[pk]
            diff = v - v5_vals[i]
            cell = f'{v}({diff:+d})' if diff != 0 else f'{v}'
            row += f'  {cell:>10}'
        print(row)

    # =========================================================
    # 精度サマリー
    # =========================================================
    print('\n\n' + '='*80)
    print('精度サマリー')
    print('='*80)
    print(f'{"カテゴリ":<14} {"シナリオ数":>8} {"v5final":>10} {"最適":>10} {"Δ":>8}')
    print('-'*80)
    for cat, keys in CATEGORY_KEYS.items():
        best_p, best_a, v5_a = results[cat]
        delta = best_a - v5_a
        marker = '↑' if delta > 0.5 else ('↓' if delta < -0.5 else '→')
        print(f'{cat:<14} {len(keys):>8}     {v5_a:>7.1f}%    {best_a:>7.1f}%  {marker}{abs(delta):>5.1f}%')

    # =========================================================
    # コンテキスト差分のポイント
    # =========================================================
    rfi_p  = results['RFI'][0]
    ip_p   = results['DEF_IP'][0]
    oop_p  = results['DEF_OOP'][0]
    bb_p   = results['DEF_BB'][0]
    all_p  = results['ALL'][0]

    print('\n\n' + '='*80)
    print('コンテキストで変化する係数 (変化あり = ★)')
    print('='*80)
    print(f'{"係数":<18} {"RFI":>8} {"DEF_IP":>8} {"DEF_OOP":>8} {"DEF_BB":>8} {"ALL":>8}')
    print('-'*80)
    for pk in params_keys:
        vals = [rfi_p[pk], ip_p[pk], oop_p[pk], bb_p[pk], all_p[pk]]
        mark = ' ★' if len(set(vals)) > 1 else ''
        row = f'{pk:<18}'
        for v, ref in zip(vals, [V5[pk]]*5):
            diff = v - rfi_p[pk]
            cell = f'{v}({diff:+d})' if diff != 0 else str(v)
            row += f'  {cell:>8}'
        print(row + mark)

    print('\n推奨 v6 パラメータ (ALL 最適):')
    for pk in params_keys:
        v = all_p[pk]
        d = v - V5[pk]
        note = f'  (v5final から{d:+d})' if d != 0 else ''
        print(f'  {pk:<18} = {v}{note}')

if __name__ == '__main__':
    main()
