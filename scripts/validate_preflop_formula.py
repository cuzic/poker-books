"""
validate_preflop_formula.py — v7 プリフロップスコア式の全データ検証ツール

使い方:
  # 全シナリオ検証 (全データファイル)
  uv run scripts/validate_preflop_formula.py

  # フィルタ指定
  uv run scripts/validate_preflop_formula.py --game mtt --sbr 25 --icm chipev
  uv run scripts/validate_preflop_formula.py --ctx RFI BB
  uv run scripts/validate_preflop_formula.py --table 6 --icm pct25 pct50 ft

  # 係数カスタム指定
  uv run scripts/validate_preflop_formula.py --params suit_bonus=6 pair_bonus=14 low_pen=0

フィルタオプション:
  --game    cash | mtt (複数可)
  --table   6 | 9 (複数可)
  --sbr     スタック/ブラインド比 (複数可)
  --icm     chipev | chipev_mr | pct25 | pct37 | pct50 | ft | bubble (複数可)
  --ctx     RFI | BB | IP | OOP | SB_RFI | MW_BB | MW_SB | MW_IP (複数可)
  --exclude-partial   部分シナリオを除外 (デフォルト: 除外)
  --include-partial   部分シナリオを含む
  --include-push      push シナリオを含む (デフォルト: 除外)
  --top N             精度下位 N シナリオを詳細表示
"""
from __future__ import annotations
import json, argparse
from pathlib import Path

GTO_DIR = Path('/home/cuzic/poker-books/knowledges/preflop')
GTO_FILES = [
    GTO_DIR / 'gto-charts.json',
    GTO_DIR / 'gto-charts-mtt6.json',
    GTO_DIR / 'gto-charts-icm.json',
    GTO_DIR / 'gto-charts-mtt9m.json',
    GTO_DIR / 'gto-charts-ext.json',
]

# ===================================================================
# スコア計算 (v7)
# ===================================================================
_RANKS = '23456789TJQKA'
_RANK  = {r: v for v, r in enumerate(_RANKS, 2)}

def parse_hand(h: str):
    if len(h) == 2:
        r = _RANK[h[0]]
        return r, r, False, True
    a, b = _RANK[h[0]], _RANK[h[1]]
    return max(a, b), min(a, b), h.endswith('s'), False

ALL_169: list[str] = []
for r in _RANKS:
    ALL_169.append(f'{r}{r}')
for i in range(len(_RANKS) - 1, -1, -1):
    for j in range(i - 1, -1, -1):
        hi, lo = _RANKS[i], _RANKS[j]
        ALL_169 += [f'{hi}{lo}s', f'{hi}{lo}o']

def score_v7(hand: str, p: dict) -> float:
    H, L, suited, pair = parse_hand(hand)
    if pair:
        return H + L + p['pair_bonus']
    gap = H - L - 1
    ab  = p.get('a_blocker', 2) if H == 14 else 0.0
    kb  = p.get('k_blocker', 1) if H == 13 else 0.0
    if suited:
        if   H == 14: gc = min(gap, p.get('a_suited_gap_cap', 2))
        elif H == 13: gc = min(gap, 2)
        elif H == 12: gc = min(gap, 3)
        elif H == 11: gc = min(gap, 4)
        else:         gc = min(gap, p.get('low_high_cap', 7))
        sc = (p.get('suited_connector', 2)  if gap == 0 else
              p.get('suited_connector1', 4) if gap == 1 else 0)
        return H + L + p.get('suit_bonus', 7) - gc + ab + kb + sc
    if H == 14:
        gc = min(gap, p.get('a_gap_cap', 5)); lp = 0.0
    elif H == 13:
        gc = min(gap, p.get('k_gap_cap', 5)); lp = p.get('low_pen', 4) if L < 10 else 0.0
    else:
        gc = gap; lp = p.get('low_pen', 4) if L < 10 else 0.0
    return H + L - gc - lp + ab + kb

# ===================================================================
# v7 コンテキスト別デフォルト係数
# ===================================================================
BASE_PARAMS = dict(
    suit_bonus=7, k_blocker=1, a_blocker=2, low_pen=4,
    a_gap_cap=5, k_gap_cap=5, pair_bonus=14,
    a_suited_gap_cap=2, suited_connector=2, suited_connector1=4, low_high_cap=7
)
CTX_OVERRIDES: dict[str, dict] = {
    'RFI':    dict(suit_bonus=3, suited_connector=3, suited_connector1=2),
    'BB':     dict(suited_connector=4, low_pen=2, pair_bonus=16),
    'IP':     dict(suit_bonus=5, suited_connector1=1, a_blocker=3),
    'OOP':    dict(suit_bonus=3, low_pen=3, pair_bonus=12),
    'MW_BB':  dict(suit_bonus=6, suited_connector=5, pair_bonus=16, a_blocker=2),
    'MW_SB':  dict(suited_connector1=2),
    'MW_IP':  dict(low_pen=0, a_blocker=4),
}

def get_params(ctx: str, overrides: dict | None = None) -> dict:
    p = {**BASE_PARAMS, **CTX_OVERRIDES.get(ctx, {})}
    if overrides:
        p.update(overrides)
    return p

# ===================================================================
# 精度計算
# ===================================================================
def best_accuracy(score_fn, play_set: set[str]) -> tuple[float, float]:
    """最適閾値での精度と閾値を返す"""
    best_acc, best_t = -1.0, 0.0
    t = 10.0
    while t <= 44.0:
        correct = sum(1 for h in ALL_169 if (score_fn(h) >= t) == (h in play_set))
        acc = correct / len(ALL_169)
        if acc > best_acc:
            best_acc, best_t = acc, t
        t += 0.5
    return best_acc * 100, best_t

# ===================================================================
# データ読み込み
# ===================================================================
def load_all(files: list[Path]) -> dict:
    all_data: dict = {}
    for fpath in files:
        if not fpath.exists():
            continue
        with open(fpath) as f:
            d = json.load(f)
        # 新フォーマット (meta + actions) か旧フォーマット (actions のみ) か判定
        for key, val in d.items():
            if isinstance(val, dict) and 'meta' in val:
                all_data[key] = val  # 新フォーマット
            elif isinstance(val, dict) and 'actions' in val:
                # 旧フォーマット (gto-charts.json)
                all_data[key] = {
                    'meta': {
                        'game': 'cash', 'table': 6, 'sbr': None,
                        'icm': 'chipev', 'scenario': key,
                        'ctx': _infer_ctx_from_key(key),
                        'partial': val.get('partial', False),
                    },
                    'actions': val['actions'],
                }
    return all_data

def _infer_ctx_from_key(key: str) -> str:
    k = key.upper()
    if 'PUSH' in k:       return 'push'
    if any(x in k for x in ['SQ_', 'SQUEEZE', '_SB_COLD', '_BTN_SB', '_CO_BTN']):
        if k.startswith('BB'): return 'MW_BB'
        if k.startswith('SB'): return 'MW_SB'
        return 'MW_IP'
    if k.endswith('_RFI'):
        return 'SB_RFI' if 'SB_' in k else 'RFI'
    if k.startswith('BB_') or k.startswith('BVB_BB'): return 'BB'
    if k.startswith('SB_VS'):                          return 'OOP'
    if 'LIMP' in k:                                    return 'BB'
    return 'IP'

# ===================================================================
# フィルタ
# ===================================================================
def apply_filters(data: dict, args) -> dict:
    filtered = {}
    for key, entry in data.items():
        m = entry['meta']

        # partial/push の除外
        if not args.include_partial and m.get('partial', False):
            continue
        if not args.include_push and m.get('ctx') == 'push':
            continue

        # game フィルタ
        if args.game and m.get('game') not in args.game:
            continue
        # table フィルタ
        if args.table and m.get('table') not in args.table:
            continue
        # sbr フィルタ
        if args.sbr and m.get('sbr') not in args.sbr:
            continue
        # icm フィルタ
        if args.icm and m.get('icm') not in args.icm:
            continue
        # ctx フィルタ
        if args.ctx and m.get('ctx') not in args.ctx:
            continue

        filtered[key] = entry
    return filtered

# ===================================================================
# メイン検証
# ===================================================================
def validate(data: dict, param_overrides: dict | None = None,
             top_n: int = 0, verbose: bool = False):
    if not data:
        print('該当シナリオなし')
        return

    results = []
    ctx_totals: dict[str, list] = {}
    icm_totals: dict[str, list] = {}

    for key, entry in data.items():
        m    = entry['meta']
        acts = entry['actions']
        ctx  = m.get('ctx', 'RFI')

        # play set: raise + call
        play = set(acts.get('raise', [])) | set(acts.get('call', []))

        p       = get_params(ctx, param_overrides)
        fn      = lambda h, p=p: score_v7(h, p)
        acc, t  = best_accuracy(fn, play)

        results.append({'key': key, 'ctx': ctx, 'acc': acc, 't': t, 'meta': m})
        ctx_totals.setdefault(ctx, []).append(acc)
        icm_totals.setdefault(m.get('icm', '?'), []).append(acc)

    # 全体集計
    all_acc = [r['acc'] for r in results]
    avg     = sum(all_acc) / len(all_acc)

    print(f'\n{"="*70}')
    print(f'検証シナリオ数: {len(results)}  /  全体平均精度: {avg:.2f}%')
    print(f'{"="*70}')

    # コンテキスト別
    print('\n【コンテキスト別精度】')
    for ctx, accs in sorted(ctx_totals.items()):
        print(f'  {ctx:<12} {len(accs):>4} scenarios  avg={sum(accs)/len(accs):.1f}%  '
              f'min={min(accs):.1f}%  max={max(accs):.1f}%')

    # ICM フェーズ別
    print('\n【ICM フェーズ別精度】')
    for icm, accs in sorted(icm_totals.items()):
        print(f'  {icm:<14} {len(accs):>4} scenarios  avg={sum(accs)/len(accs):.1f}%  '
              f'min={min(accs):.1f}%  max={max(accs):.1f}%')

    # SBR 別 (MTT のみ)
    sbr_totals: dict = {}
    for r in results:
        sbr = r['meta'].get('sbr')
        if sbr is not None:
            sbr_totals.setdefault(sbr, []).append(r['acc'])
    if sbr_totals:
        print('\n【SBR 別精度 (MTT)】')
        for sbr, accs in sorted(sbr_totals.items()):
            print(f'  SBR={sbr:<4} {len(accs):>4} scenarios  avg={sum(accs)/len(accs):.1f}%')

    # 精度ワーストN
    if top_n > 0:
        worst = sorted(results, key=lambda r: r['acc'])[:top_n]
        print(f'\n【精度ワースト {top_n}】')
        for r in worst:
            m = r['meta']
            print(f'  {r["acc"]:5.1f}%  T={r["t"]:4.1f}  [{r["ctx"]:8}]  {r["key"][:60]}')

    return avg

# ===================================================================
# CLI
# ===================================================================
def main():
    parser = argparse.ArgumentParser(description='v7 プリフロップ式 全データ検証')
    parser.add_argument('--game',   nargs='+', choices=['cash','mtt'])
    parser.add_argument('--table',  nargs='+', type=int, choices=[6, 9])
    parser.add_argument('--sbr',    nargs='+', type=int)
    parser.add_argument('--icm',    nargs='+')
    parser.add_argument('--ctx',    nargs='+',
                        choices=['RFI','BB','IP','OOP','SB_RFI','MW_BB','MW_SB','MW_IP'])
    parser.add_argument('--include-partial', action='store_true')
    parser.add_argument('--include-push',    action='store_true')
    parser.add_argument('--top', type=int, default=10, dest='top_n')
    parser.add_argument('--params', nargs='+',
                        help='係数上書き: key=value 形式 e.g. suit_bonus=6')
    args = parser.parse_args()

    # 係数パース
    param_overrides = {}
    if args.params:
        for p in args.params:
            k, v = p.split('=')
            param_overrides[k] = int(v)

    print('GTO データ読み込み中...')
    all_data = load_all(GTO_FILES)
    print(f'  総シナリオ数: {len(all_data)}')

    filtered = apply_filters(all_data, args)
    print(f'  フィルタ後:   {len(filtered)} シナリオ')

    validate(filtered, param_overrides or None, top_n=args.top_n)

if __name__ == '__main__':
    main()
