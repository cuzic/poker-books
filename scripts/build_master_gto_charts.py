"""
build_master_gto_charts.py — 全 GTO Wizard データを統一フォーマットに変換

対象データソース:
  1. raw_ranges/           — Cash 6m (action_solutions format)
  2. raw_ranges_3betv2/    — Cash 6m updated (action_solutions format)
  3. raw_ranges_multiway/  — Cash 6m MW (action_solutions format)
  4. raw_ranges_tournament/           — MTT 6m (meta+strategies format)
     sbr8-40, mronlygeneral_sbr*, squeeze_sbr*, mw_sbr*, threbet_sbr*
  5. raw_ranges_icm/                  — ICM 6m/8m/9m (meta+strategies format)
     6m_chipev, ICM6m200PTFT, ICM8m200PTBUBBLEMID, ICM8m200PTFT
     ICM9m200PTPCT25/37/50, ICM9m200PTFT
  6. raw_ranges_tournament_9m/        — MTT 9m (meta+strategies format)
     sbr8-40, mw_sbr*, threbet_sbr*

出力:
  knowledges/preflop/gto-charts.json          — 既存 Cash (変更なし)
  knowledges/preflop/gto-charts-mtt6.json     — MTT 6m 全 SBR 全フェーズ
  knowledges/preflop/gto-charts-icm.json      — ICM 全フェーズ全 SBR
  knowledges/preflop/gto-charts-mtt9m.json    — MTT 9m 全 SBR
  knowledges/preflop/gto-charts-cash-ext.json — Cash 追加 (vs_3bet 等 archive)

統一フォーマット:
  {
    "KEY": {
      "meta": {
        "game": "cash"|"mtt",
        "table": 6|9,
        "sbr": 25,
        "icm": "chipev"|"pct25"|"pct37"|"pct50"|"ft"|"bubble",
        "scenario": "BTN_RFI",
        "ctx": "RFI"|"BB"|"IP"|"OOP"|"SB_RFI"|"MW_BB"|"MW_SB"|"MW_IP"|"push",
        "partial": false
      },
      "actions": {"raise": [...], "call": [...], "fold": [...]}
    }
  }
"""
from __future__ import annotations
import json, os
from pathlib import Path

RAW        = Path('/home/cuzic/poker-drill/scripts/precompute')
ARCHIVE    = Path('/home/cuzic/poker-books/cash-postflop/_archive/findings')
MTT_DATA   = Path('/home/cuzic/poker-books/mtt-postflop/findings')
OUT        = Path('/home/cuzic/poker-books/knowledges/preflop')

# ===================================================================
# ハンド表記の正規化ユーティリティ
# ===================================================================
_RANKS = '23456789TJQKA'
_RANK  = {r: v for v, r in enumerate(_RANKS, 2)}
_RRANK = {v: r for r, v in _RANK.items()}

def normalize_hand(h: str) -> str:
    """GTO Wizard の手表記を標準化: '22' → '22', 'AhKs' 等は無視, 'AKs' そのまま"""
    h = h.strip()
    if len(h) == 2 and h[0] == h[1] and h[0] in _RANK:
        return h  # pair
    if len(h) == 3 and h[0] in _RANK and h[1] in _RANK and h[2] in ('s', 'o'):
        hi = max(_RANK[h[0]], _RANK[h[1]])
        lo = min(_RANK[h[0]], _RANK[h[1]])
        return _RRANK[hi] + _RRANK[lo] + h[2]
    return h

def dominant_from_freqs(freqs: dict[str, float]) -> str:
    """{'raise': 0.7, 'fold': 0.3} → 'raise'。push は raise 扱い"""
    r = freqs.get('raise', 0) + freqs.get('push', 0)
    c = freqs.get('call', 0)
    f = freqs.get('fold', 0)
    if r >= c and r >= f: return 'raise'
    if c >= f:            return 'call'
    return 'fold'

# ===================================================================
# Format A: meta + strategies dict
#   raw_ranges_tournament, raw_ranges_icm, tournament_9m
# ===================================================================
def load_strategies_format(path: Path) -> dict[str, list[str]]:
    """strategies dict → {'raise': [...], 'call': [...], 'fold': [...]}"""
    with open(path) as f:
        d = json.load(f)
    strats = d['strategies']
    buckets: dict[str, list[str]] = {'raise': [], 'call': [], 'fold': []}
    for hand_raw, freqs in strats.items():
        hand = normalize_hand(hand_raw)
        act  = dominant_from_freqs(freqs)
        buckets[act].append(hand)
    return buckets

# ===================================================================
# Format B: action_solutions + players_info
#   raw_ranges, raw_ranges_3betv2, raw_ranges_multiway
# ===================================================================
def load_action_solutions_format(path: Path) -> dict[str, list[str]]:
    """action_solutions → {'raise': [...], 'call': [...], 'fold': [...]}"""
    with open(path) as f:
        d = json.load(f)

    pi    = d['players_info'][0]
    hands = list(pi['simple_hand_counters'].keys())
    n     = len(hands)

    fold_s  = [0.0] * n
    call_s  = [0.0] * n
    raise_s = [0.0] * n

    for sol in d['action_solutions']:
        code  = sol['action']['code']
        strat = sol.get('strategy', [0.0] * n)
        if code == 'F':
            for i, v in enumerate(strat): fold_s[i]  += v
        elif code in ('C', 'X'):
            for i, v in enumerate(strat): call_s[i]  += v
        else:  # R* / RAI / push
            for i, v in enumerate(strat): raise_s[i] += v

    buckets: dict[str, list[str]] = {'raise': [], 'call': [], 'fold': []}
    for i, hand_raw in enumerate(hands):
        hand = normalize_hand(hand_raw)
        act  = dominant_from_freqs({'raise': raise_s[i], 'call': call_s[i], 'fold': fold_s[i]})
        buckets[act].append(hand)
    return buckets

# ===================================================================
# Format C: results.phase.scenario.rows (mtt_preflop_gto JSON)
# ===================================================================
def load_mtt_rows_format(rows: list[dict]) -> dict[str, list[str]]:
    """rows形式 → buckets"""
    buckets: dict[str, list[str]] = {'raise': [], 'call': [], 'fold': []}
    for row in rows:
        hand = normalize_hand(row['hc'])
        act  = dominant_from_freqs({
            'raise': row.get('raise', 0),
            'call':  row.get('call',  0),
            'fold':  row.get('fold',  0),
        })
        buckets[act].append(hand)
    return buckets

# ===================================================================
# コンテキスト判定
# ===================================================================
def infer_ctx(scenario: str, is_mw: bool = False) -> str:
    s = scenario.upper()
    if 'PUSH' in s:                            return 'push'
    if is_mw or 'MW' in s or '_O_' in s or 'SQ' in s or 'SQUEEZE' in s:
        if s.startswith('BB'):                 return 'MW_BB'
        if s.startswith('SB'):                 return 'MW_SB'
        return 'MW_IP'
    if s.endswith('RFI'):
        if s.startswith('SB'):                 return 'SB_RFI'
        return 'RFI'
    if s.startswith('BB_VS') or s.startswith('BVB_BB'):
        return 'BB'
    if s.startswith('SB_VS'):                  return 'OOP'
    return 'IP'

def is_partial(buckets: dict, scenario: str) -> bool:
    """169手未満 (push/3bet等は部分レンジ) の判定"""
    total = sum(len(v) for v in buckets.values())
    return total < 169

# ===================================================================
# エントリ構築
# ===================================================================
def make_entry(buckets: dict, meta: dict) -> dict:
    partial = is_partial(buckets, meta.get('scenario', ''))
    return {
        'meta': {**meta, 'partial': partial},
        'actions': buckets,
    }

# ===================================================================
# ビルダー 1: MTT 6m (raw_ranges_tournament)
# ===================================================================
TOURNAMENT_DIR = RAW / 'raw_ranges_tournament'

# サブディレクトリ → (icm, game, table)
_SUBDIR_META = {
    # sbr{N}: MTT ChipEV, 6m
    'sbr':              ('chipev', 'mtt', 6),
    # mronlygeneral_sbr{N}: MTT ChipEV min-raise only
    'mronlygeneral_sbr':('chipev_mr', 'mtt', 6),
    # squeeze_sbr{N}: MTT squeeze scenarios
    'squeeze_sbr':      ('chipev', 'mtt', 6),
    # mw_sbr{N}: MTT multiway
    'mw_sbr':           ('chipev', 'mtt', 6),
    # threbet_sbr{N}: MTT vs_3bet
    'threbet_sbr':      ('chipev', 'mtt', 6),
}

def sbr_from_dirname(name: str) -> int:
    parts = name.split('sbr')
    return int(parts[-1]) if parts[-1].isdigit() else 0

def build_mtt6(out: dict) -> int:
    count = 0
    for subdir in sorted(TOURNAMENT_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        name = subdir.name
        # match prefix
        prefix = None
        for p in _SUBDIR_META:
            if name.startswith(p):
                prefix = p
                break
        if prefix is None:
            continue
        icm, game, table = _SUBDIR_META[prefix]
        sbr = sbr_from_dirname(name)
        is_mw = 'mw' in name or 'squeeze' in name

        for fpath in sorted(subdir.glob('*.json')):
            scenario = fpath.stem  # e.g., 'BTN_RFI'
            try:
                buckets = load_strategies_format(fpath)
            except Exception as e:
                print(f'  ERROR {fpath}: {e}')
                continue

            ctx = infer_ctx(scenario, is_mw=is_mw)
            key = f'MTT6_{sbr}_{name.replace("sbr"+str(sbr), "").strip("_") or "std"}_{scenario}'
            # クリーンアップ
            key = key.replace('__', '_').rstrip('_')

            meta = dict(game=game, table=table, sbr=sbr, icm=icm,
                        scenario=scenario, ctx=ctx, subtype=name)
            out[key] = make_entry(buckets, meta)
            count += 1
    return count

# ===================================================================
# ビルダー 2: ICM (raw_ranges_icm)
# ===================================================================
ICM_DIR = RAW / 'raw_ranges_icm'

_ICM_META = {
    '6m_chipev':           ('chipev', 6),
    'ICM6m200PTFT':        ('ft',     6),
    'ICM8m200PTBUBBLEMID': ('bubble', 8),
    'ICM8m200PTFT':        ('ft',     8),
    'ICM9m200PTFT':        ('ft',     9),
    'ICM9m200PTPCT25':     ('pct25',  9),
    'ICM9m200PTPCT37':     ('pct37',  9),
    'ICM9m200PTPCT50':     ('pct50',  9),
}

def build_icm(out: dict) -> int:
    count = 0
    for icm_type, (icm_label, table) in _ICM_META.items():
        type_dir = ICM_DIR / icm_type
        if not type_dir.exists():
            continue
        for sbr_dir in sorted(type_dir.iterdir()):
            if not sbr_dir.is_dir():
                continue
            sbr = sbr_from_dirname(sbr_dir.name)
            for fpath in sorted(sbr_dir.glob('*.json')):
                scenario = fpath.stem
                try:
                    buckets = load_strategies_format(fpath)
                except Exception as e:
                    print(f'  ERROR {fpath}: {e}')
                    continue
                is_mw   = 'mw' in scenario.lower() or '_o_' in scenario.lower()
                ctx     = infer_ctx(scenario, is_mw=is_mw)
                key     = f'ICM_{icm_type}_{sbr}_{scenario}'
                meta    = dict(game='mtt', table=table, sbr=sbr, icm=icm_label,
                               scenario=scenario, ctx=ctx, icm_type=icm_type)
                out[key] = make_entry(buckets, meta)
                count += 1
    return count

# ===================================================================
# ビルダー 3: MTT 9m (raw_ranges_tournament_9m)
# ===================================================================
TOURNAMENT_9M_DIR = RAW / 'raw_ranges_tournament_9m'

def build_mtt9m(out: dict) -> int:
    count = 0
    for subdir in sorted(TOURNAMENT_9M_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        name = subdir.name
        sbr  = sbr_from_dirname(name)
        is_mw = 'mw' in name or 'squeeze' in name or 'threbet' in name

        for fpath in sorted(subdir.glob('*.json')):
            scenario = fpath.stem
            try:
                buckets = load_strategies_format(fpath)
            except Exception as e:
                print(f'  ERROR {fpath}: {e}')
                continue
            ctx = infer_ctx(scenario, is_mw=is_mw)
            key = f'MTT9_{sbr}_{name.replace("sbr"+str(sbr),"").strip("_") or "std"}_{scenario}'
            key = key.replace('__', '_').rstrip('_')
            meta = dict(game='mtt', table=9, sbr=sbr, icm='chipev',
                        scenario=scenario, ctx=ctx, subtype=name)
            out[key] = make_entry(buckets, meta)
            count += 1
    return count

# ===================================================================
# ビルダー 4: Cash 追加 (archive: vs_3bet, vs_5bet, multiway)
# ===================================================================
def build_cash_ext(out: dict) -> int:
    count = 0
    archive_files = {
        'preflop_gto_rfi.json':      ('rfi',    'RFI'),
        'preflop_gto_vs_open.json':  ('vs_open','BB'),
        'preflop_gto_vs_3bet.json':  ('vs_3bet','IP'),
        'preflop_gto_vs_4bet.json':  ('vs_4bet','IP'),
        'preflop_gto_multiway.json': ('multiway','MW_IP'),
    }
    for fname, (phase_key, default_ctx) in archive_files.items():
        fpath = ARCHIVE / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            d = json.load(f)
        results = d.get('results', {})
        phase_data = results.get(phase_key, {})
        for scenario_name, info in phase_data.items():
            rows = info.get('rows', [])
            if not rows:
                continue
            buckets = load_mtt_rows_format(rows)
            # scenario name → key
            sc_key = scenario_name.replace(' ', '_').replace('+', 'p')
            key    = f'CASH_EXT_{sc_key}'
            ctx    = infer_ctx(sc_key)
            meta   = dict(game='cash', table=6, sbr=None, icm='chipev',
                          scenario=scenario_name, ctx=ctx, phase=phase_key)
            out[key] = make_entry(buckets, meta)
            count += 1
    return count

# ===================================================================
# ビルダー 5: MTT mtt_preflop_gto JSON (mtt-postflop/findings)
# ===================================================================
_MTT_GTO_FILES = [
    ('mtt_preflop_gto_SBR20_rfi.json',      20, 'rfi',      'chipev'),
    ('mtt_preflop_gto_SBR20_vs_open.json',  20, 'vs_open',  'chipev'),
    ('mtt_preflop_gto_SBR20_vs_3bet.json',  20, 'vs_3bet',  'chipev'),
    ('mtt_preflop_gto_SBR20_multiway.json', 20, 'multiway', 'chipev'),
    ('mtt_preflop_gto_SBR25_rfi.json',      25, 'rfi',      'chipev'),
    ('mtt_preflop_gto_SBR25_vs_open.json',  25, 'vs_open',  'chipev'),
    ('mtt_preflop_gto_SBR25_vs_3bet.json',  25, 'vs_3bet',  'chipev'),
    ('mtt_preflop_gto_SBR25_multiway.json', 25, 'multiway', 'chipev'),
    ('mtt_preflop_gto_SBR40_all.json',      40, 'rfi',      'chipev'),
    ('mtt_preflop_gto_SBR40_vs_open.json',  40, 'vs_open',  'chipev'),
    ('mtt_preflop_gto_SBR40_vs_3bet.json',  40, 'vs_3bet',  'chipev'),
    ('mtt_preflop_gto_SBR40_multiway.json', 40, 'multiway', 'chipev'),
]

def build_mtt_gto_files(out: dict) -> int:
    count = 0
    for fname, sbr, phase_key, icm in _MTT_GTO_FILES:
        fpath = MTT_DATA / fname
        if not fpath.exists():
            continue
        with open(fpath) as f:
            d = json.load(f)
        results = d.get('results', {})
        # rfi/vs_open/vs_3bet は直接キー、multiway は nested
        phase_data = results.get(phase_key, results.get('rfi', {}))
        is_mw = phase_key == 'multiway'

        for scenario_name, info in phase_data.items():
            rows = info.get('rows', [])
            if not rows:
                continue
            buckets = load_mtt_rows_format(rows)
            sc_key  = scenario_name.replace(' ', '_').replace('+', 'p').replace('/', '_')
            key     = f'MTTGTO6_{sbr}_{phase_key}_{sc_key}'
            ctx     = infer_ctx(sc_key, is_mw=is_mw)
            meta    = dict(game='mtt', table=6, sbr=sbr, icm=icm,
                           scenario=scenario_name, ctx=ctx, phase=phase_key)
            out[key] = make_entry(buckets, meta)
            count += 1
    return count

# ===================================================================
# メイン
# ===================================================================
if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)

    print('=== GTO Master Charts Builder ===\n')

    # ---- MTT 6m ----
    mtt6: dict = {}
    n = build_mtt6(mtt6)
    print(f'MTT 6m (raw_ranges_tournament): {n} scenarios')
    out_mtt6 = OUT / 'gto-charts-mtt6.json'
    with open(out_mtt6, 'w') as f:
        json.dump(mtt6, f, ensure_ascii=False, indent=2)
    print(f'  → {out_mtt6}')

    # ---- ICM ----
    icm: dict = {}
    n = build_icm(icm)
    print(f'\nICM (raw_ranges_icm): {n} scenarios')
    out_icm = OUT / 'gto-charts-icm.json'
    with open(out_icm, 'w') as f:
        json.dump(icm, f, ensure_ascii=False, indent=2)
    print(f'  → {out_icm}')

    # ---- MTT 9m ----
    mtt9: dict = {}
    n = build_mtt9m(mtt9)
    print(f'\nMTT 9m (raw_ranges_tournament_9m): {n} scenarios')
    out_mtt9 = OUT / 'gto-charts-mtt9m.json'
    with open(out_mtt9, 'w') as f:
        json.dump(mtt9, f, ensure_ascii=False, indent=2)
    print(f'  → {out_mtt9}')

    # ---- Cash extended ----
    cash_ext: dict = {}
    n = build_cash_ext(cash_ext)
    print(f'\nCash extended (archive): {n} scenarios')
    n2 = build_mtt_gto_files(cash_ext)
    print(f'MTT GTO files (mtt-postflop/findings): {n2} scenarios')
    out_ext = OUT / 'gto-charts-ext.json'
    with open(out_ext, 'w') as f:
        json.dump(cash_ext, f, ensure_ascii=False, indent=2)
    print(f'  → {out_ext}')

    # ---- サマリー ----
    print('\n=== Summary ===')
    totals = {
        'gto-charts.json (Cash existing)': None,
        'gto-charts-mtt6.json': len(mtt6),
        'gto-charts-icm.json':  len(icm),
        'gto-charts-mtt9m.json': len(mtt9),
        'gto-charts-ext.json':  len(cash_ext),
    }
    grand_total = 0
    for fname, n in totals.items():
        if n is None:
            # count existing
            existing = OUT / 'gto-charts.json'
            if existing.exists():
                with open(existing) as f:
                    n = len(json.load(f))
            else:
                n = 0
        grand_total += n
        print(f'  {fname:<40} {n:>5} scenarios')
    print(f'  {"TOTAL":<40} {grand_total:>5} scenarios')

    # ---- コンテキスト別集計 ----
    print('\n=== Context breakdown (all files) ===')
    ctx_counts: dict[str, int] = {}
    partial_count = 0
    for d in [mtt6, icm, mtt9, cash_ext]:
        for v in d.values():
            ctx = v['meta'].get('ctx', '?')
            ctx_counts[ctx] = ctx_counts.get(ctx, 0) + 1
            if v['meta'].get('partial'):
                partial_count += 1
    for ctx, n in sorted(ctx_counts.items()):
        print(f'  {ctx:<12} {n:>5}')
    print(f'  (partial: {partial_count})')
