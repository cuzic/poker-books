#!/usr/bin/env python3
"""
boards_full_study.py — Generate the full comprehensive board study list.

Merges:
  1. boards_turn_v2.json / boards_river_v2.json  (pairwise + boundary coverage)
  2. deck_boards_turn.json / deck_boards_river.json  (actual poker-drill scenarios)

Outputs:
  study_boards_turn.json   — all unique turn (4-card) boards to run on GCP
  study_boards_river.json  — all unique river (5-card) boards to run on GCP
  study_boards_all.json    — combined list for launch script
"""
from __future__ import annotations
import json, re
from pathlib import Path
from collections import Counter

OUT_DIR = Path(__file__).parent
RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

# ── Texture from solver_str (first 3 cards) ───────────────────────────────────

def classify_board(solver_str: str) -> str:
    cards = [c for c in solver_str.split(',')[:3] if len(c) >= 2]
    if not cards:
        return 'rainbow'
    ranks = [RANK_VAL.get(c[0].upper(), 0) for c in cards]
    suits = [c[-1].lower() for c in cards]
    if len(set(suits)) == 1:
        return 'mono'
    cnt = Counter(ranks)
    pairs = [r for r, c in cnt.items() if c >= 2]
    if pairs:
        return 'paired_high' if max(pairs) >= 10 else 'paired_low'
    n_suits = len(set(suits))
    top, spread = max(ranks), max(ranks) - min(ranks)
    if n_suits == 2:
        return '2tone_ak' if top >= 13 else '2tone'
    if spread <= 3 and top >= 11:
        return 'rainbow_connected'
    if top >= 13: return 'rainbow_ak'
    if top == 12: return 'rainbow_q'
    # Low connected check (rainbow, spread<=3, top<J)
    if spread <= 3 and top < 11:
        return 'rainbow_lowconn'
    return 'rainbow'


def b_score(texture: str) -> int:
    return {'mono':70,'paired_high':83,'paired_low':71,'2tone_ak':56,'2tone':50,
            'rainbow_connected':67,'rainbow_ak':62,'rainbow_q':58,'rainbow':55,
            'rainbow_lowconn':55,'2tone_conn':50}.get(texture, 55)


def make_board_entry(solver_str: str, source: str, street: str,
                     scenario_id: str | None = None,
                     extra: dict | None = None) -> dict:
    cards = solver_str.split(',')
    n = len(cards)
    ranks_raw = [RANK_VAL.get(c[0].upper(), 0) for c in cards]
    ranks = sorted(ranks_raw, reverse=True)
    texture = classify_board(solver_str)

    entry: dict = {
        'scenario_id': scenario_id or f'{street[:2]}_{solver_str.replace(",","").replace(" ","_")}',
        'street': street,
        'solver_str': solver_str,
        'n_cards': n,
        'texture': texture,
        'b_score': b_score(texture),
        'r_hi': ranks[0] if ranks else 0,
        'r_mid': ranks[1] if len(ranks) > 1 else 0,
        'r_lo': ranks[2] if len(ranks) > 2 else 0,
        'source': source,
    }
    if extra:
        entry.update(extra)
    return entry


def main() -> None:
    # ── Load pairwise+boundary comprehensive boards ───────────────────────────
    comp_turn  = json.loads((OUT_DIR / 'boards_turn_v2.json').read_text())
    comp_river = json.loads((OUT_DIR / 'boards_river_v2.json').read_text())

    # Add source tag and pot/stack
    for s in comp_turn:
        s['source'] = 'comprehensive'
        s.setdefault('pot_bb', 10)
        s.setdefault('effective_stack_bb', 92)
    for s in comp_river:
        s['source'] = 'comprehensive'
        s.setdefault('pot_bb', 20)
        s.setdefault('effective_stack_bb', 80)

    # ── Load deck boards ───────────────────────────────────────────────────────
    deck_turn_raw  = json.loads((OUT_DIR / 'deck_boards_turn.json').read_text())
    deck_river_raw = json.loads((OUT_DIR / 'deck_boards_river.json').read_text())

    # ── Merge: add deck boards not already in comprehensive ────────────────────
    comp_turn_boards  = {s['board'] for s in comp_turn}
    comp_river_boards = {s['board'] for s in comp_river}

    added_turn = 0
    for db in deck_turn_raw:
        solver_str = db['solver_str']
        if solver_str in comp_turn_boards:
            continue
        comp_turn_boards.add(solver_str)
        added_turn += 1
        source_decks = db.get('source_decks', [])
        entry = make_board_entry(
            solver_str, 'deck', 'turn',
            scenario_id=f'tr_deck_{solver_str.replace(",","_")[:20]}',
            extra={
                'board': solver_str,
                'pot_bb': 10,
                'effective_stack_bb': 92,
                'source_decks': source_decks,
            }
        )
        # Extract flop (first 3 cards) and turn card (4th)
        cards_list = solver_str.split(',')
        entry['flop_str'] = ','.join(cards_list[:3])
        entry['turn_card'] = cards_list[3] if len(cards_list) > 3 else ''
        entry['turn_type'] = 'deck'
        comp_turn.append(entry)

    added_river = 0
    for db in deck_river_raw:
        solver_str = db['solver_str']
        if solver_str in comp_river_boards:
            continue
        comp_river_boards.add(solver_str)
        added_river += 1
        source_decks = db.get('source_decks', [])
        entry = make_board_entry(
            solver_str, 'deck', 'river',
            scenario_id=f'rv_deck_{solver_str.replace(",","_")[:20]}',
            extra={
                'board': solver_str,
                'pot_bb': 20,
                'effective_stack_bb': 80,
                'source_decks': source_decks,
            }
        )
        cards_list = solver_str.split(',')
        entry['flop_str'] = ','.join(cards_list[:3])
        entry['turn_card'] = cards_list[3] if len(cards_list) > 3 else ''
        entry['river_card'] = cards_list[4] if len(cards_list) > 4 else ''
        entry['turn_type'] = 'deck'
        entry['river_type'] = 'deck'
        comp_river.append(entry)

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f'Turn scenarios:  {len(comp_turn)} ({len(comp_turn)-added_turn} comprehensive + {added_turn} deck-only)')
    print(f'River scenarios: {len(comp_river)} ({len(comp_river)-added_river} comprehensive + {added_river} deck-only)')
    print(f'Total:           {len(comp_turn) + len(comp_river)}')

    # Texture breakdown
    tex_turn = Counter(s['texture'] for s in comp_turn)
    print(f'\nTurn by texture:')
    for tex, cnt in sorted(tex_turn.items(), key=lambda x: -x[1]):
        print(f'  {tex:22s}: {cnt:3d}  B={b_score(tex)}')

    # Pairwise cell check
    tt_cnt = Counter((s['texture'], s.get('turn_type','')) for s in comp_turn)
    print(f'\nPairwise cells (texture × turn_type): {len(tt_cnt)}')
    for k, v in sorted(tt_cnt.items()):
        tex, tt = k
        if tt in ['pair','overcard','blank','connector','flush']:
            print(f'  {tex:22s} × {tt:12s}: {v}')

    # ── Save outputs ───────────────────────────────────────────────────────────
    (OUT_DIR / 'study_boards_turn.json').write_text(
        json.dumps(comp_turn, ensure_ascii=False, indent=2))
    (OUT_DIR / 'study_boards_river.json').write_text(
        json.dumps(comp_river, ensure_ascii=False, indent=2))

    all_scenarios = comp_turn + comp_river
    (OUT_DIR / 'study_boards_all.json').write_text(
        json.dumps(all_scenarios, ensure_ascii=False, indent=2))

    print(f'\nSaved:')
    print(f'  study_boards_turn.json  ({len(comp_turn)} scenarios)')
    print(f'  study_boards_river.json ({len(comp_river)} scenarios)')
    print(f'  study_boards_all.json   ({len(all_scenarios)} scenarios)')


if __name__ == '__main__':
    main()
