"""
append_multiway_to_gto_charts.py
raw_ranges_multiway/ の 14 シナリオを gto-charts.json に追記する。

変換ルール:
  - 支配的アクション (最高頻度) で 169 手を排他的に割り当て
  - F → fold
  - C / X (check) → limp
  - R* / RAI → raise
  - total=169 を保証
"""
from __future__ import annotations
import json
from pathlib import Path

RAW_DIR  = Path('/home/cuzic/poker-drill/scripts/precompute/raw_ranges_multiway')
GTO_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json')

# ファイル名 → シナリオキーのマッピング
SCENARIO_MAP = {
    # BB defense (multiway)
    'BB_vs_BTN_SB_cold':     'BB_vs_BTN_SB_cold',
    'BB_vs_CO_BTN_cold':     'BB_vs_CO_BTN_cold',
    # BB squeeze
    'squeeze_BB_vs_HJ_BTN':  'BB_squeeze_vs_HJ_BTN',
    'squeeze_BB_vs_UTG_BTN': 'BB_squeeze_vs_UTG_BTN',
    # SB squeeze
    'squeeze_SB_vs_CO_BTN':  'SB_squeeze_vs_CO_BTN',
    'squeeze_SB_vs_HJ_BTN':  'SB_squeeze_vs_HJ_BTN',
    'squeeze_SB_vs_UTG_BTN': 'SB_squeeze_vs_UTG_BTN',
    'squeeze_SB_vs_UTG_CO':  'SB_squeeze_vs_UTG_CO',
    'squeeze_SB_vs_UTG_HJ':  'SB_squeeze_vs_UTG_HJ',
    # IP squeeze
    'squeeze_BTN_vs_UTG_CO': 'BTN_squeeze_vs_UTG_CO',
    'squeeze_BTN_vs_UTG_HJ': 'BTN_squeeze_vs_UTG_HJ',
    'squeeze_CO_vs_UTG_HJ':  'CO_squeeze_vs_UTG_HJ',
    # BvB limp
    'limp_BB_vs_SB':         'BvB_BB_vs_SB_limp_defense',
    'limp_BB_vs_SB_only':    'BvB_BB_vs_SB_limp_only',
}

def extract_dominant(data: dict) -> dict[str, list[str]]:
    """169手を支配的アクションで fold / limp / raise に振り分ける"""
    pi = data['players_info'][0]
    hands = list(pi['simple_hand_counters'].keys())

    # アクション別戦略ベクトルを集約
    fold_s  = [0.0] * 169
    limp_s  = [0.0] * 169
    raise_s = [0.0] * 169

    for sol in data['action_solutions']:
        code  = sol['action']['code']
        strat = sol.get('strategy', [0.0] * 169)
        if code == 'F':
            for i, v in enumerate(strat): fold_s[i]  += v
        elif code in ('C', 'X'):
            for i, v in enumerate(strat): limp_s[i]  += v
        else:  # R* / RAI
            for i, v in enumerate(strat): raise_s[i] += v

    buckets: dict[str, list[str]] = {'raise': [], 'limp': [], 'fold': []}
    for i, hand in enumerate(hands):
        vals = {'raise': raise_s[i], 'limp': limp_s[i], 'fold': fold_s[i]}
        dominant = max(vals, key=lambda k: vals[k])
        buckets[dominant].append(hand)

    return buckets

# 既存 gto-charts.json を読み込み
with open(GTO_PATH) as f:
    gto = json.load(f)

print(f'既存シナリオ数: {len(gto)}')

added = []
for fname_stem, scenario_key in SCENARIO_MAP.items():
    fpath = RAW_DIR / f'{fname_stem}.json'
    if not fpath.exists():
        print(f'  SKIP (file not found): {fpath.name}')
        continue
    if scenario_key in gto:
        print(f'  SKIP (already exists): {scenario_key}')
        continue

    with open(fpath) as f:
        raw = json.load(f)

    buckets = extract_dominant(raw)
    total = sum(len(v) for v in buckets.values())

    # limp が空なら actions から除外
    actions = {k: v for k, v in buckets.items() if v}
    gto[scenario_key] = {'actions': actions}
    added.append(scenario_key)
    print(f'  ADD {scenario_key}: raise={len(buckets["raise"])}, limp={len(buckets["limp"])}, fold={len(buckets["fold"])}, total={total}')

# 保存
with open(GTO_PATH, 'w', encoding='utf-8') as f:
    json.dump(gto, f, ensure_ascii=False, indent=2)

print(f'\n完了: {len(added)} シナリオを追加 → 合計 {len(gto)} シナリオ')
