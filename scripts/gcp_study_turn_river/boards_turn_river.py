#!/usr/bin/env python3
"""
boards_turn_river.py — Generate turn+river scenario list for GTO study.

Covers 9 flop textures × 3 representative boards × 4 turn types = 108 turn scenarios.
Selects 27 canonical flop+turn combos × 3 river types = 81 river scenarios.
Total: 189 scenarios.

Output:
  boards_turn.json   — 108 turn (4-card) scenarios
  boards_river.json  — 81 river (5-card) scenarios
"""
from __future__ import annotations
import json
from pathlib import Path

RANK_VAL = {'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
            '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2}
RANK_STR = {v: k for k, v in RANK_VAL.items()}

# ── 9 flop textures × 3 representative boards each ───────────────────────────
# Format: (texture_key, b_value, board_id_prefix, solver_str)
FLOPS: list[tuple[str, int, str, str]] = [
    # Monotone (B=70)
    ('mono',             70, 'K95cc',  'Kc,9c,5c'),
    ('mono',             70, 'J84cc',  'Jc,8c,4c'),
    ('mono',             70, '963cc',  '9c,6c,3c'),
    # Paired high — pair rank ≥ T (B=83)
    ('paired_high',      83, 'KK7r',   'Kc,Kd,7s'),
    ('paired_high',      83, 'QQ8r',   'Qc,Qd,8s'),
    ('paired_high',      83, 'JJ5r',   'Jc,Jd,5s'),
    # Paired low — pair rank < T (B=71)
    ('paired_low',       71, 'A99r',   'Ac,9d,9s'),
    ('paired_low',       71, 'K88r',   'Kc,8d,8s'),
    ('paired_low',       71, 'Q77r',   'Qc,7d,7s'),
    # 2-tone × A/K top (B=56)
    ('2tone_ak',         56, 'A83t',   'Ac,8d,3c'),
    ('2tone_ak',         56, 'K94t',   'Kc,9d,4c'),
    ('2tone_ak',         56, 'AT7t',   'Ac,Td,7c'),
    # 2-tone other (B=50)
    ('2tone',            50, 'J95t',   'Jc,9d,5c'),
    ('2tone',            50, 'T74t',   'Tc,7d,4c'),
    ('2tone',            50, '963t',   '9c,6d,3c'),
    # Rainbow × connected (spread≤3, top≥J) (B=67)
    ('rainbow_connected',67, 'KQJr',   'Kc,Qd,Jh'),
    ('rainbow_connected',67, 'QJTr',   'Qc,Jd,Th'),
    ('rainbow_connected',67, 'JT9r',   'Jc,Td,9h'),
    # Rainbow × A/K top (B=62)
    ('rainbow_ak',       62, 'A83r',   'Ac,8d,3s'),
    ('rainbow_ak',       62, 'K72r',   'Kc,7d,2s'),
    ('rainbow_ak',       62, 'A94r',   'Ac,9d,4s'),
    # Rainbow × Q top (B=58)
    ('rainbow_q',        58, 'Q83r',   'Qc,8d,3s'),
    ('rainbow_q',        58, 'Q72r',   'Qc,7d,2s'),
    ('rainbow_q',        58, 'Q94r',   'Qc,9d,4s'),
    # Rainbow other (B=55)
    ('rainbow',          55, 'T72r',   'Tc,7d,2s'),
    ('rainbow',          55, '963r',   '9c,6d,3s'),
    ('rainbow',          55, '852r',   '8c,5d,2s'),
]

# ── Turn card definitions ──────────────────────────────────────────────────────
# For each flop, define 4 representative turn cards:
#   pair     = same rank as one flop card (pairs the board)
#   overcard = rank higher than all flop cards
#   blank    = low card, no draw, no pair
#   connector = rank that adds straight draw potential

def _ranks(solver_str: str) -> list[int]:
    cards = solver_str.split(',')
    return sorted([RANK_VAL[c[0].upper()] for c in cards], reverse=True)

def _suits(solver_str: str) -> list[str]:
    return [c[-1].lower() for c in solver_str.split(',')]

def _available_suits(flop: str) -> set[str]:
    used = set(_suits(flop))
    return {'c', 'd', 'h', 's'} - used

def _make_turn_cards(flop: str) -> dict[str, str]:
    """Return {category: 'Xs'} turn card tokens for the given flop."""
    ranks = _ranks(flop)
    r_hi, r_mid, r_lo = ranks[0], ranks[1], ranks[2]
    suits_on_board = _suits(flop)

    # Pair: pair the top card (use a different suit)
    pair_suit = next(s for s in ('c', 'd', 'h', 's') if s != suits_on_board[0])
    pair_card = f"{RANK_STR[r_hi]}{pair_suit}"

    # Overcard: rank above top card (or ace if no room; use K if top=A)
    oc_rank = r_hi + 1 if r_hi < 14 else 13
    # Avoid using same rank as existing card
    while oc_rank in ranks and oc_rank < 14:
        oc_rank += 1
    if oc_rank > 14:
        oc_rank = 14
    if oc_rank == r_hi or oc_rank in ranks:
        oc_rank = 14 if 14 not in ranks else (13 if 13 not in ranks else 12)
    oc_suit = next(s for s in ('c', 'd', 'h', 's') if s != suits_on_board[0])
    oc_card = f"{RANK_STR[oc_rank]}{oc_suit}"

    # Blank: lowest possible unmatched rank (2 unless already on board)
    for blank_rank in range(2, r_lo):
        if blank_rank not in ranks:
            break
    else:
        blank_rank = 2
    blank_suit = next(s for s in ('c', 'd', 'h', 's') if s not in suits_on_board[:2])
    blank_card = f"{RANK_STR[blank_rank]}{blank_suit}"

    # Connector: rank within 2 of low card (adds OESD/gutshot potential)
    conn_rank = r_lo - 1 if r_lo > 3 else r_lo + 2
    while conn_rank in ranks and conn_rank >= 2:
        conn_rank -= 1
    if conn_rank < 2:
        conn_rank = r_lo + 1 if r_lo + 1 <= 14 and r_lo + 1 not in ranks else r_lo - 2
    if conn_rank < 2:
        conn_rank = 4
    conn_suit = next(s for s in ('c', 'd', 'h', 's') if s not in suits_on_board[:2])
    conn_card = f"{RANK_STR[conn_rank]}{conn_suit}"

    return {
        'pair': pair_card,
        'overcard': oc_card,
        'blank': blank_card,
        'connector': conn_card,
    }

# ── River card definitions ──────────────────────────────────────────────────────
def _make_river_cards(flop: str, turn_card: str) -> dict[str, str]:
    """Return {category: 'Xs'} river card tokens for given flop+turn."""
    all_cards = flop.split(',') + [turn_card]
    ranks_on_board = [RANK_VAL[c[0].upper()] for c in all_cards]
    suits_on_board = [c[-1].lower() for c in all_cards]

    # Blank: lowest rank not on board, suit not completing flush
    for blank_rank in range(2, 15):
        if blank_rank not in ranks_on_board:
            break
    blank_suit = next(s for s in ('c', 'd', 'h', 's') if suits_on_board.count(s) < 2)
    blank_card = f"{RANK_STR[blank_rank]}{blank_suit}"

    # Pair: pairs the turn card
    pair_rank = RANK_VAL[turn_card[0].upper()]
    pair_suit = next(s for s in ('c', 'd', 'h', 's') if s != turn_card[-1].lower() and s != suits_on_board[0])
    pair_card = f"{RANK_STR[pair_rank]}{pair_suit}"

    # Flush completer: 3rd card of the most-present suit
    from collections import Counter
    suit_counts = Counter(suits_on_board)
    flush_suit, cnt = suit_counts.most_common(1)[0]
    if cnt >= 2:
        # Find a rank not on board using the flush suit
        for flush_rank in range(14, 1, -1):
            if flush_rank not in ranks_on_board:
                flush_card = f"{RANK_STR[flush_rank]}{flush_suit}"
                break
        else:
            flush_card = blank_card  # fallback
    else:
        flush_card = blank_card  # no flush draw possible

    return {
        'blank': blank_card,
        'pair': pair_card,
        'flush': flush_card,
    }


# ── Build scenario lists ──────────────────────────────────────────────────────

def build_turn_scenarios() -> list[dict]:
    scenarios = []
    for texture, b_score, flop_id, flop_str in FLOPS:
        turn_cards = _make_turn_cards(flop_str)
        for turn_type, turn_card in turn_cards.items():
            board_4card = flop_str + ',' + turn_card
            scenario_id = f'tr_{flop_id}_{turn_type[:4]}'
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
    """Pick 1 canonical turn scenario per flop (blank turn) and add 3 river cards."""
    # Use "blank" turn for river study (most neutral continuation)
    canonical_turns = {s['flop_id']: s for s in turn_scenarios if s['turn_type'] == 'blank'}

    scenarios = []
    for flop_id, ts in canonical_turns.items():
        river_cards = _make_river_cards(ts['flop_str'], ts['turn_card'])
        for river_type, river_card in river_cards.items():
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
                'pot_bb': 20,       # after turn 50% CBet call
                'effective_stack_bb': 80,
            })
    return scenarios


if __name__ == '__main__':
    turn_scens = build_turn_scenarios()
    river_scens = build_river_scenarios(turn_scens)

    out_dir = Path(__file__).parent
    (out_dir / 'boards_turn.json').write_text(
        json.dumps(turn_scens, ensure_ascii=False, indent=2))
    (out_dir / 'boards_river.json').write_text(
        json.dumps(river_scens, ensure_ascii=False, indent=2))

    print(f'Turn scenarios:  {len(turn_scens)}')
    print(f'River scenarios: {len(river_scens)}')
    print(f'Total:           {len(turn_scens) + len(river_scens)}')

    # Quick sanity check
    from collections import Counter
    tex_counts = Counter(s['texture'] for s in turn_scens)
    print('\nTurn by texture:')
    for tex, cnt in sorted(tex_counts.items()):
        print(f'  {tex:22s}: {cnt}')
