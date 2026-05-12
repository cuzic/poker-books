#!/usr/bin/env python3
"""
boards_comprehensive.py — Generate comprehensive turn+river scenario list.

Design goals:
  1. All 9 flop textures × 3+ boards × 4 turn types = pairwise coverage
  2. Boundary boards: rainbow_connected(B=67) / mono(B=70) / paired_low(B=71)
  3. Connected anomaly boards: low rainbow/2tone spread<=3 top<J
  4. Additional boards per texture for statistical reliability (n>=5 per cell)

Pairwise coverage targets:
  - (texture, turn_card_type): 9 × 4 = 36 cells, min 3 boards each → 108 scenarios
  - (boundary_texture, turn_card_type): 6 × 4 = 24 additional boundary scenarios
  - Total turn: ~132 scenarios
  - River: 33 canonical flop+turn pairs × 3 river types = 99 river scenarios
  - Grand total: ~231 scenarios

Outputs:
  boards_turn_v2.json   — turn (4-card) scenarios
  boards_river_v2.json  — river (5-card) scenarios
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import Counter, defaultdict

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}
RANK_STR = {v: k for k, v in RANK_VAL.items()}

# ── Flop catalog ──────────────────────────────────────────────────────────────
# 9 main textures × 4 boards + boundary cases × 4 each
FLOPS = [
    # ── Monotone (B=70) — 4 boards ────────────────────────────────────────────
    ('mono', 70, 'K95cc', 'Kc,9c,5c'),
    ('mono', 70, 'J84cc', 'Jc,8c,4c'),
    ('mono', 70, '963cc', '9c,6c,3c'),
    ('mono', 70, 'A52cc', 'Ac,5c,2c'),

    # ── Paired_high (B=83) — 4 boards ─────────────────────────────────────────
    ('paired_high', 83, 'KK7r',  'Kc,Kd,7s'),
    ('paired_high', 83, 'QQ8r',  'Qc,Qd,8s'),
    ('paired_high', 83, 'JJ5r',  'Jc,Jd,5s'),
    ('paired_high', 83, 'TT6r',  'Tc,Td,6s'),

    # ── Paired_low (B=71) — 4 boards ──────────────────────────────────────────
    ('paired_low', 71, 'A99r',   'Ac,9d,9s'),
    ('paired_low', 71, 'K88r',   'Kc,8d,8s'),
    ('paired_low', 71, 'Q77r',   'Qc,7d,7s'),
    ('paired_low', 71, 'J66r',   'Jc,6d,6s'),

    # ── 2tone_AK (B=56) — 4 boards ────────────────────────────────────────────
    ('2tone_ak', 56, 'A83t',    'Ac,8d,3c'),
    ('2tone_ak', 56, 'K94t',    'Kc,9d,4c'),
    ('2tone_ak', 56, 'A72t',    'Ac,7d,2c'),
    ('2tone_ak', 56, 'K86t',    'Kc,8d,6c'),

    # ── 2tone (B=50) — 4 boards ───────────────────────────────────────────────
    ('2tone', 50, 'J95t',   'Jc,9d,5c'),
    ('2tone', 50, 'T74t',   'Tc,7d,4c'),
    ('2tone', 50, '963t',   '9c,6d,3c'),
    ('2tone', 50, '852t',   '8c,5d,2c'),

    # ── Rainbow_connected (B=67) — 6 boards (boundary category) ───────────────
    ('rainbow_connected', 67, 'KQJr',   'Kc,Qd,Jh'),
    ('rainbow_connected', 67, 'QJTr',   'Qc,Jd,Th'),
    ('rainbow_connected', 67, 'JT9r',   'Jc,Td,9h'),
    ('rainbow_connected', 67, 'KJTr',   'Kc,Jd,Th'),
    ('rainbow_connected', 67, 'QT9r',   'Qc,Td,9h'),
    ('rainbow_connected', 67, 'KQTr',   'Kc,Qd,Th'),

    # ── Rainbow_AK (B=62) — 4 boards ──────────────────────────────────────────
    ('rainbow_ak', 62, 'A83r',    'Ac,8d,3s'),
    ('rainbow_ak', 62, 'K72r',    'Kc,7d,2s'),
    ('rainbow_ak', 62, 'A94r',    'Ac,9d,4s'),
    ('rainbow_ak', 62, 'K63r',    'Kc,6d,3s'),

    # ── Rainbow_Q (B=58) — 5 boards (boundary category) ───────────────────────
    ('rainbow_q', 58, 'Q83r',    'Qc,8d,3s'),
    ('rainbow_q', 58, 'Q72r',    'Qc,7d,2s'),
    ('rainbow_q', 58, 'Q94r',    'Qc,9d,4s'),
    ('rainbow_q', 58, 'QT7r',    'Qc,Td,7s'),
    ('rainbow_q', 58, 'Q86r',    'Qc,8d,6s'),

    # ── Rainbow (B=55) — 4 boards ─────────────────────────────────────────────
    ('rainbow', 55, 'T72r',    'Tc,7d,2s'),
    ('rainbow', 55, '963r',    '9c,6d,3s'),
    ('rainbow', 55, '852r',    '8c,5d,2s'),
    ('rainbow', 55, 'J63r',    'Jc,6d,3s'),

    # ── Low connected rainbow (B=55, anomaly) — 6 boards ──────────────────────
    # These are classified B=55 but have high connectivity (spread<=3, top<J)
    ('rainbow_lowconn', 55, 'T98r',   'Tc,9d,8h'),
    ('rainbow_lowconn', 55, 'T87r',   'Tc,8d,7h'),
    ('rainbow_lowconn', 55, '987r',   '9c,8d,7h'),
    ('rainbow_lowconn', 55, '876r',   '8c,7d,6h'),
    ('rainbow_lowconn', 55, 'T97r',   'Tc,9d,7h'),
    ('rainbow_lowconn', 55, '986r',   '9c,8d,6h'),

    # ── 2tone connected (B=50, anomaly) — 4 boards ────────────────────────────
    # Connected 2-tone boards: spread<=3
    ('2tone_conn', 50, 'QJT2t',  'Qc,Jd,Tc'),
    ('2tone_conn', 50, 'JT9_2t', 'Jc,Td,9c'),
    ('2tone_conn', 50, 'T98_2t', 'Tc,9d,8c'),
    ('2tone_conn', 50, '987_2t', '9c,8d,7c'),
]


# ── Turn card generation ───────────────────────────────────────────────────────

def _ranks(solver_str: str) -> list[int]:
    return sorted([RANK_VAL[c[0].upper()] for c in solver_str.split(',')], reverse=True)

def _suits_list(solver_str: str) -> list[str]:
    return [c[-1].lower() for c in solver_str.split(',')]

def _make_turn_cards(flop: str) -> dict[str, str]:
    """Return dict {turn_type: card_token} for all applicable turn card types."""
    ranks = _ranks(flop)
    suits = _suits_list(flop)
    r_hi, r_mid, r_lo = ranks[0], ranks[1], ranks[2]

    used_ranks = set(ranks)
    used_suits = set(suits)
    all_suits = {'c','d','h','s'}
    new_suits = list(all_suits - used_suits) or ['c']

    result = {}

    # Pair: pair the highest card (use a different suit)
    pair_suit = next(s for s in ('c','d','h','s') if s != suits[0])
    result['pair'] = f'{RANK_STR[r_hi]}{pair_suit}'

    # Overcard: rank strictly above highest flop card
    oc_rank = None
    for r in range(r_hi + 1, 15):
        if r not in used_ranks:
            oc_rank = r
            break
    if oc_rank is None:
        # No overcard possible (A on board already) — use next best
        oc_rank = r_hi + 1 if r_hi < 14 else 14
        if oc_rank > 14: oc_rank = 14
    oc_suit = new_suits[0] if new_suits else 'c'
    result['overcard'] = f'{RANK_STR[oc_rank]}{oc_suit}'

    # Blank: lowest rank not on board, avoiding suit completion
    blank_suit = next((s for s in ('c','d','h','s') if suits.count(s) < 2), 'c')
    for br in range(2, r_lo):
        if br not in used_ranks:
            result['blank'] = f'{RANK_STR[br]}{blank_suit}'
            break
    else:
        # All lower ranks used — use r_hi+2 if possible
        result['blank'] = f'{RANK_STR[max(2, r_lo-1)]}{blank_suit}'

    # Connector: adds straight draw, rank within 3 of r_lo going down
    conn_rank = None
    for r in range(r_lo - 1, max(2, r_lo - 4), -1):
        if r not in used_ranks and r >= 2:
            conn_rank = r
            break
    if conn_rank is None:
        # Try going up
        for r in range(r_hi + 1, r_hi + 4):
            if r not in used_ranks and r <= 14:
                conn_rank = r
                break
    if conn_rank is None:
        conn_rank = max(2, r_lo - 1)
    conn_suit = blank_suit
    result['connector'] = f'{RANK_STR[conn_rank]}{conn_suit}'

    # Flush: only for 2-tone boards (3rd card of the same suit)
    suit_cnt = Counter(suits)
    flush_suit, cnt = suit_cnt.most_common(1)[0]
    if cnt == 2:
        for fr in range(14, 1, -1):
            if fr not in used_ranks:
                result['flush'] = f'{RANK_STR[fr]}{flush_suit}'
                break

    return result


# ── River card generation ──────────────────────────────────────────────────────

def _make_river_cards(flop: str, turn_card: str) -> dict[str, str]:
    all_cards = flop.split(',') + [turn_card]
    used_ranks = set(RANK_VAL[c[0].upper()] for c in all_cards)
    used_suits = [c[-1].lower() for c in all_cards]
    suit_cnt = Counter(used_suits)

    # Blank: low disconnected, no flush
    blank_suit = next((s for s in ('c','d','h','s') if suit_cnt[s] < 2), 'c')
    for br in range(2, 15):
        if br not in used_ranks:
            blank_card = f'{RANK_STR[br]}{blank_suit}'
            break
    else:
        blank_card = f'2{blank_suit}'

    # Pair: pairs the turn card
    turn_rank = RANK_VAL[turn_card[0].upper()]
    turn_suit = turn_card[-1].lower()
    pair_suit = next(s for s in ('c','d','h','s') if s != turn_suit and suit_cnt[s] < 2)
    pair_card = f'{RANK_STR[turn_rank]}{pair_suit}'

    # Flush completer: completes the most common suit (if >= 2 on board)
    flush_suit, flush_cnt = suit_cnt.most_common(1)[0]
    if flush_cnt >= 2:
        for fr in range(14, 1, -1):
            if fr not in used_ranks:
                flush_card = f'{RANK_STR[fr]}{flush_suit}'
                break
        else:
            flush_card = blank_card
    else:
        flush_card = blank_card

    return {'blank': blank_card, 'pair': pair_card, 'flush': flush_card}


# ── Build scenario lists ──────────────────────────────────────────────────────

def build_turn_scenarios() -> list[dict]:
    scenarios = []
    seen = set()
    for texture, b_score, flop_id, flop_str in FLOPS:
        turn_cards = _make_turn_cards(flop_str)
        for turn_type, turn_card in sorted(turn_cards.items()):
            board_4card = flop_str + ',' + turn_card
            scenario_id = f'tr_{flop_id}_{turn_type[:4]}'
            if scenario_id in seen:
                continue
            seen.add(scenario_id)
            scenarios.append({
                'scenario_id': scenario_id,
                'street': 'turn',
                'texture': texture,
                'b_score': b_score,
                'flop_id': flop_id,
                'flop_str': flop_str,
                'turn_type': turn_type,
                'turn_card': turn_card,
                'board': board_4card,
                'pot_bb': 10,
                'effective_stack_bb': 92,
            })
    return scenarios


def build_river_scenarios(turn_scenarios: list[dict]) -> list[dict]:
    """For each texture, pick the 'blank' turn scenario and add 3 river types."""
    # One canonical turn per flop (blank turn)
    canonical: dict[str, dict] = {}
    for s in turn_scenarios:
        if s['turn_type'] == 'blank' and s['flop_id'] not in canonical:
            canonical[s['flop_id']] = s

    scenarios = []
    for flop_id, ts in sorted(canonical.items()):
        river_cards = _make_river_cards(ts['flop_str'], ts['turn_card'])
        for river_type, river_card in sorted(river_cards.items()):
            board_5card = ts['board'] + ',' + river_card
            scenario_id = f'rv_{ts["flop_id"]}_{river_type[:4]}'
            scenarios.append({
                'scenario_id': scenario_id,
                'street': 'river',
                'texture': ts['texture'],
                'b_score': ts['b_score'],
                'flop_id': ts['flop_id'],
                'flop_str': ts['flop_str'],
                'turn_card': ts['turn_card'],
                'turn_type': ts['turn_type'],
                'river_type': river_type,
                'river_card': river_card,
                'board': board_5card,
                'pot_bb': 20,
                'effective_stack_bb': 80,
            })
    return scenarios


if __name__ == '__main__':
    turn_scens = build_turn_scenarios()
    river_scens = build_river_scenarios(turn_scens)

    out_dir = Path(__file__).parent
    (out_dir / 'boards_turn_v2.json').write_text(
        json.dumps(turn_scens, ensure_ascii=False, indent=2))
    (out_dir / 'boards_river_v2.json').write_text(
        json.dumps(river_scens, ensure_ascii=False, indent=2))

    # Stats
    tex_cnt = Counter(s['texture'] for s in turn_scens)
    tc_cnt  = Counter((s['texture'], s['turn_type']) for s in turn_scens)
    min_cell = min(tc_cnt.values())
    max_cell = max(tc_cnt.values())

    print(f'Turn scenarios:  {len(turn_scens)}')
    print(f'River scenarios: {len(river_scens)}')
    print(f'Total:           {len(turn_scens) + len(river_scens)}')
    print(f'\nPairwise cell coverage (texture × turn_type):')
    print(f'  min={min_cell}  max={max_cell}  cells={len(tc_cnt)}')
    print(f'\nTurn by texture:')
    for tex, cnt in sorted(tex_cnt.items(), key=lambda x: x[1]):
        print(f'  {tex:22s}: {cnt:3d} scenarios')

    # Check pairwise completeness
    all_textures = set(s['texture'] for s in turn_scens)
    all_turn_types = set(s['turn_type'] for s in turn_scens)
    print(f'\nAll textures: {sorted(all_textures)}')
    print(f'All turn types: {sorted(all_turn_types)}')

    missing = []
    for tex in all_textures:
        for tt in ['pair', 'overcard', 'blank', 'connector']:
            if tc_cnt.get((tex, tt), 0) == 0:
                missing.append((tex, tt))
    if missing:
        print(f'\nMissing cells: {missing}')
    else:
        print('\nAll core pairwise cells covered ✓')
