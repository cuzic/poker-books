"""
build_mtt_gto_charts.py — MTT GTO データを gto-charts.json 互換フォーマットへ変換

入力:
  mtt-postflop/findings/mtt_preflop_gto_SBR25_rfi.json     → RFI (LJ/HJ/CO/BTN + UTG)
  mtt-postflop/findings/mtt_preflop_gto_SBR25_vs_open.json → BB defense
  mtt-postflop/findings/mtt_preflop_gto_SBR25_vs_3bet.json → IP call/4bet
  mtt-postflop/findings/mtt_preflop_gto_SBR40_all.json     → SB RFI (SBR40 のみ存在)

出力:
  knowledges/preflop/mtt-gto-charts-SBR25.json

フォーマット (gto-charts.json と同一):
  {
    "scenario_key": {
      "actions": {
        "raise": [...],   // 3bet or RFI raise
        "limp":  [...],   // call
        "fold":  [...]
      }
    }
  }

混合戦略の処理: 支配的アクション（最高頻度）で排他的に振り分ける → 常に total=169
"""
from __future__ import annotations
import json
from pathlib import Path

BASE     = Path('/home/cuzic/poker-books/mtt-postflop/findings')
OUT_PATH = Path('/home/cuzic/poker-books/knowledges/preflop/mtt-gto-charts-SBR25.json')

def dominant_action(row: dict, action_keys: list[str]) -> str:
    """混合戦略ハンドを最高頻度アクションに割り当てる"""
    best_act = action_keys[0]
    best_val = row.get(action_keys[0], 0)
    for act in action_keys[1:]:
        v = row.get(act, 0)
        if v > best_val:
            best_val, best_act = v, act
    return best_act

def split_by_dominant(rows: list[dict], action_keys: list[str]) -> dict[str, list[str]]:
    """全169手を支配的アクションで排他的に振り分ける (total=169 保証)"""
    buckets: dict[str, list[str]] = {a: [] for a in action_keys}
    for r in rows:
        act = dominant_action(r, action_keys)
        buckets[act].append(r['hc'])
    return buckets

result: dict[str, dict] = {}

# ============================================================
# 1. RFI (SBR=25): UTG / UTG1 / LJ / HJ / CO / BTN
# ============================================================
with open(BASE / 'mtt_preflop_gto_SBR25_rfi.json') as f:
    rfi25 = json.load(f)['results']['rfi']

RFI_MAP = {
    'UTG RFI':  'MTT25_UTG_RFI',
    'UTG1 RFI': 'MTT25_UTG1_RFI',
    'LJ RFI':   'MTT25_LJ_RFI',
    'HJ RFI':   'MTT25_HJ_RFI',
    'CO RFI':   'MTT25_CO_RFI',
    'BTN RFI':  'MTT25_BTN_RFI',
}
for src, dst in RFI_MAP.items():
    rows = rfi25[src]['rows']
    buckets = split_by_dominant(rows, ['raise', 'fold'])
    result[dst] = {'actions': {'raise': buckets['raise'], 'fold': buckets['fold']}}
    total = sum(len(v) for v in buckets.values())
    print(f'{dst}: raise={len(buckets["raise"])}, fold={len(buckets["fold"])}, total={total}')

# ============================================================
# 2. BB defense vs open (SBR=25): BB vs UTG/UTG1/LJ/HJ/CO/BTN
# ============================================================
with open(BASE / 'mtt_preflop_gto_SBR25_vs_open.json') as f:
    vs_open25 = json.load(f)['results']['vs_open']

BB_MAP = {
    'BB vs UTG':  'MTT25_BB_vs_UTG',
    'BB vs UTG1': 'MTT25_BB_vs_UTG1',
    'BB vs LJ':   'MTT25_BB_vs_LJ',
    'BB vs HJ':   'MTT25_BB_vs_HJ',
    'BB vs CO':   'MTT25_BB_vs_CO',
    'BB vs BTN':  'MTT25_BB_vs_BTN',
}
for src, dst in BB_MAP.items():
    rows = vs_open25[src]['rows']
    buckets = split_by_dominant(rows, ['raise', 'call', 'fold'])
    result[dst] = {'actions': {
        'raise': buckets['raise'],   # 3-bet
        'limp':  buckets['call'],    # call (limp に相当)
        'fold':  buckets['fold'],
    }}
    total = sum(len(v) for v in buckets.values())
    print(f'{dst}: 3bet={len(buckets["raise"])}, call={len(buckets["call"])}, fold={len(buckets["fold"])}, total={total}')

# ============================================================
# 3. IP vs 3-bet (SBR=25): CO/BTN vs 3bet → call=defend, raise=4bet
# ============================================================
with open(BASE / 'mtt_preflop_gto_SBR25_vs_3bet.json') as f:
    vs3b25 = json.load(f)['results']['vs_3bet']

VS3_MAP = {
    'CO vs BTN 3bet':  'MTT25_CO_vs_BTN_3bet',
    'BTN vs SB 3bet':  'MTT25_BTN_vs_SB_3bet',
    'BTN vs BB 3bet':  'MTT25_BTN_vs_BB_3bet',
}
for src, dst in VS3_MAP.items():
    rows = vs3b25[src]['rows']
    buckets = split_by_dominant(rows, ['raise', 'call', 'fold'])
    # vs_3bet はオープンレンジ内のハンドのみ (169手完全ではない)
    # partial=true を付けて Optuna 比較からは除外
    result[dst] = {
        'actions': {
            'raise': buckets['raise'],
            'limp':  buckets['call'],
            'fold':  buckets['fold'],
        },
        'partial': True,  # 169手未満: Optuna accuracy 計算に使用不可
    }
    total = sum(len(v) for v in buckets.values())
    print(f'{dst}: 4bet={len(buckets["raise"])}, call={len(buckets["call"])}, fold={len(buckets["fold"])}, total={total} [partial]')

# ============================================================
# 4. SB RFI (SBR=40, SBR=25 データなし)
# ============================================================
with open(BASE / 'mtt_preflop_gto_SBR40_all.json') as f:
    all40 = json.load(f)['results']['rfi']

sb_rows = all40['SB RFI']['rows']
# SBR40 SB: raise=大きいレイズ、call=リンプ相当
sb_buckets = split_by_dominant(sb_rows, ['raise', 'call', 'fold'])
result['MTT40_SB_RFI'] = {'actions': {
    'raise': sb_buckets['raise'],
    'limp':  sb_buckets['call'],
    'fold':  sb_buckets['fold'],
}}
total = sum(len(v) for v in sb_buckets.values())
print(f'MTT40_SB_RFI: raise={len(sb_buckets["raise"])}, limp={len(sb_buckets["call"])}, fold={len(sb_buckets["fold"])}, total={total}')

# ============================================================
# 5. 検証: 完全シナリオ (partial=False) は total=169 チェック
# ============================================================
print()
errors = []
for k, v in result.items():
    if v.get('partial'):
        continue
    total = sum(len(hands) for hands in v['actions'].values())
    if total != 169:
        errors.append(f'  ERROR {k}: total={total}')
if errors:
    print('バリデーションエラー:')
    for e in errors: print(e)
else:
    complete = [k for k, v in result.items() if not v.get('partial')]
    partial  = [k for k, v in result.items() if v.get('partial')]
    print(f'バリデーション OK: 完全シナリオ {len(complete)} 件 (total=169), 部分シナリオ {len(partial)} 件')

# ============================================================
# 6. 出力
# ============================================================
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'\n→ {OUT_PATH} に {len(result)} シナリオを保存')
print('\nシナリオ一覧:')
for k in result:
    acts = result[k]['actions']
    counts = {a: len(v) for a, v in acts.items()}
    print(f'  {k:<30} {counts}')
