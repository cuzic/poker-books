#!/usr/bin/env python3
"""
extract_deck_boards.py — Extract all unique boards from poker-drill deck files.

Parses all flop/turn/river TypeScript deck files, extracts board strings,
converts Unicode suits to ASCII for TexasSolver, and outputs a structured JSON
with all scenarios to validate.

Output: deck_scenarios.json — all scenarios with board, hand, decision, deck info
        deck_boards_flop.json  — unique flop boards for TexasSolver
        deck_boards_turn.json  — unique turn (4-card) boards
        deck_boards_river.json — unique river (5-card) boards
"""
from __future__ import annotations
import json, re
from pathlib import Path
from collections import defaultdict

DRILL_DATA = Path('/home/cuzic/poker-drill/src/data')
OUT_DIR    = Path(__file__).parent

# ── Suit conversion ───────────────────────────────────────────────────────────
SUIT_MAP = {'♠': 's', '♥': 'h', '♦': 'd', '♣': 'c'}
RANK_ORDER = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

def unicode_to_ascii(card_token: str) -> str:
    """'K♠' → 'Ks'"""
    result = ''
    for ch in card_token:
        if ch in SUIT_MAP:
            result += SUIT_MAP[ch]
        else:
            result += ch
    return result


def parse_board(board_str: str) -> tuple[str, str, int]:
    """
    Parse board string → (flop_ascii, turn_ascii_or_empty, n_cards).
    Handles:
      'K♠7♦2♣'           → flop (3 cards)
      'K♠7♦2♣ → 7♥'      → flop + turn (4 cards)
      'A♠K♦7♣2♥9♠'       → river (5 cards, space-separated runs of 2)
    Returns (solver_str, turn_card, n_cards).
    solver_str: comma-separated ASCII e.g. 'Ks,7d,2c'
    turn_card: '' for flop, 'Xh' for turn/river
    """
    # Normalize: convert Unicode suits
    normalized = board_str
    for u, a in SUIT_MAP.items():
        normalized = normalized.replace(u, a)

    # Arrow notation (turn board: "Ks7d2c -> 7h" or "Ks7d2c → 7h")
    if '→' in normalized or '->' in normalized:
        parts = re.split(r'→|->|→', normalized)
        flop_part = parts[0].strip()
        turn_part = parts[1].strip() if len(parts) > 1 else ''
        flop_cards = re.findall(r'[AKQJTakqjt2-9]{1}[shdc]', flop_part)
        turn_cards = re.findall(r'[AKQJTakqjt2-9]{1}[shdc]', turn_part)
        all_cards = [c.upper()[0] + c[1].lower() for c in flop_cards + turn_cards]
        return ','.join(all_cards), (all_cards[3] if len(all_cards) > 3 else ''), len(all_cards)

    # Extract all card tokens: rank (1 char) + suit (1 char)
    cards_raw = re.findall(r'[AKQJTakqjt2-9]{1}[shdc]', normalized)
    cards = [c.upper()[0] + c[1].lower() for c in cards_raw]
    n = len(cards)
    return ','.join(cards), (cards[3] if n >= 4 else ''), n


def classify_board(solver_str: str) -> str:
    """Classify board by texture (9-type system)."""
    from collections import Counter
    cards = [(RANK_ORDER[c[0].upper()], c[1].lower())
             for c in solver_str.split(',')[:3]
             if len(c) >= 2 and c[0].upper() in RANK_ORDER]
    if not cards:
        return 'rainbow'
    ranks = [r for r,s in cards]
    suits = [s for r,s in cards]
    if len(set(suits)) == 1:
        return 'mono'
    cnt = Counter(ranks)
    pairs = [r for r,c in cnt.items() if c >= 2]
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
    return 'rainbow'


def b_score(texture: str) -> int:
    return {'mono':70,'paired_high':83,'paired_low':71,'2tone_ak':56,'2tone':50,
            'rainbow_connected':67,'rainbow_ak':62,'rainbow_q':58,'rainbow':55}.get(texture, 55)


# ── Deck files configuration ──────────────────────────────────────────────────
DECK_FILES = [
    # (filename, street, situation)
    ('flop-cbet-cards.ts',           'flop',  'cbet_srp'),
    ('flop-vs-cbet-cards.ts',        'flop',  'defense_srp'),
    ('flop-cbet-3bp-cards.ts',       'flop',  'cbet_3bp'),
    ('flop-vs-cbet-3bp-cards.ts',    'flop',  'defense_3bp'),
    ('flop-cbet-4bp-cards.ts',       'flop',  'cbet_4bp'),
    ('flop-vs-cbet-4bp-cards.ts',    'flop',  'defense_4bp'),
    ('flop-cbet-multiway-cards.ts',  'flop',  'cbet_multiway'),
    ('flop-multiway-cards.ts',       'flop',  'defense_multiway'),
    ('flop-donk-cards.ts',           'flop',  'donk'),
    ('turn-cbet-cards.ts',           'turn',  'cbet_srp'),
    ('turn-defense-cards.ts',        'turn',  'defense_srp'),
    ('turn-cbet-3bp-cards.ts',       'turn',  'cbet_3bp'),
    ('river-first-cards.ts',         'river', 'first_bet'),
    ('river-defense-cards.ts',       'river', 'defense'),
    ('river-alpha-cards.ts',         'river', 'alpha'),
]


def extract_from_ts(filepath: Path) -> list[dict]:
    """Extract card data from TypeScript deck file (nested front/back structure)."""
    text = filepath.read_text(encoding='utf-8')

    # Split into per-card blocks using "id": pattern
    card_blocks = re.split(r'(?=\{\s*\n\s*"id":\s*")', text)
    cards = []

    for block in card_blocks:
        # Extract id
        id_m = re.search(r'"id":\s*"([^"]+)"', block)
        if not id_m:
            continue
        card_id = id_m.group(1)

        # Extract from "front" section: board, hand
        front_m = re.search(r'"front"\s*:\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', block, re.DOTALL)
        board_raw = ''
        hand_raw  = ''
        if front_m:
            front_text = front_m.group(1)
            b_m = re.search(r'"board":\s*"([^"]+)"', front_text)
            h_m = re.search(r'"hand":\s*"([^"]+)"', front_text)
            if b_m: board_raw = b_m.group(1)
            if h_m: hand_raw  = h_m.group(1)

        # Extract from "back" section: decision, answer
        back_m = re.search(r'"back"\s*:\s*\{(.+?)(?=\n\s*\},\s*\n\s*\{|\n\s*\}\s*\])', block, re.DOTALL)
        decision = ''
        answer   = ''
        if back_m:
            back_text = back_m.group(1)
            d_m = re.search(r'"decision":\s*"([^"]+)"', back_text)
            a_m = re.search(r'"answer":\s*"([^"]+)"', back_text)
            if d_m: decision = d_m.group(1)
            if a_m: answer   = a_m.group(1)

        # Skip concept/memory/quiz cards without meaningful board
        if not board_raw or len(board_raw) < 4:
            continue
        # Skip if board looks like a label (no suit symbols or rank chars)
        has_suits = any(s in board_raw for s in ('♠','♥','♦','♣'))
        if not has_suits:
            continue

        solver_str, turn_card, n_cards = parse_board(board_raw)
        if not solver_str or n_cards < 3:
            continue

        texture = classify_board(solver_str)
        cards.append({
            'card_id':   card_id,
            'board_raw': board_raw,
            'board':     solver_str,
            'turn_card': turn_card,
            'n_cards':   n_cards,
            'hand_raw':  hand_raw,
            'decision':  decision,
            'answer':    answer,
            'texture':   texture,
            'b_score':   b_score(texture),
        })
    return cards


# ── Main extraction ────────────────────────────────────────────────────────────

def main() -> None:
    all_scenarios: list[dict] = []
    by_file: dict[str, list[dict]] = {}

    print('Extracting scenarios from deck files...\n')
    print(f'{"File":40s}  {"Cards":5s}  {"Boards (unique)"}')
    print('-' * 80)

    for filename, street, situation in DECK_FILES:
        filepath = DRILL_DATA / filename
        if not filepath.exists():
            print(f'{filename:40s}  [MISSING]')
            continue

        cards = extract_from_ts(filepath)
        for c in cards:
            c['deck_file'] = filename
            c['street']    = street
            c['situation'] = situation
        by_file[filename] = cards
        all_scenarios.extend(cards)

        unique_boards = len(set(c['board'][:11] for c in cards))  # first 11 chars as key
        print(f'{filename:40s}  {len(cards):5d}  {unique_boards:4d} unique boards')

    print(f'\nTotal scenarios: {len(all_scenarios)}')

    # ── Unique board lists by street ──────────────────────────────────────────
    seen_boards: set[str] = set()
    flop_boards: list[dict] = []
    turn_boards: list[dict] = []
    river_boards: list[dict] = []

    for s in all_scenarios:
        board_key = s['board']
        n = s['n_cards']
        if board_key in seen_boards:
            continue
        seen_boards.add(board_key)
        texture = classify_board(board_key)

        # Board ranks for metric extraction
        cards_ascii = board_key.split(',')
        ranks = sorted([RANK_ORDER.get(c[0].upper(), 0) for c in cards_ascii], reverse=True)

        board_entry = {
            'board_id':   board_key.replace(',', '').replace(' ', '_')[:15],
            'solver_str': board_key,
            'n_cards':    n,
            'texture':    texture,
            'b_score':    b_score(texture),
            'r_hi':       ranks[0] if ranks else 0,
            'r_mid':      ranks[1] if len(ranks) > 1 else 0,
            'r_lo':       ranks[2] if len(ranks) > 2 else 0,
            'source_decks': list({s2['deck_file'] for s2 in all_scenarios
                                   if s2['board'] == board_key}),
        }

        if n == 3 and s['street'] == 'flop':
            board_entry['pot_bb']   = 7
            board_entry['stack_bb'] = 97
            flop_boards.append(board_entry)
        elif n == 4 or (n >= 4 and s['street'] == 'turn'):
            board_entry['pot_bb']   = 10
            board_entry['stack_bb'] = 92
            turn_boards.append(board_entry)
        elif n >= 5 or s['street'] == 'river':
            board_entry['pot_bb']   = 20
            board_entry['stack_bb'] = 80
            river_boards.append(board_entry)

    print(f'\nUnique boards:')
    print(f'  Flop:  {len(flop_boards)}')
    print(f'  Turn:  {len(turn_boards)}')
    print(f'  River: {len(river_boards)}')
    print(f'  Total: {len(flop_boards) + len(turn_boards) + len(river_boards)}')

    # ── Texture coverage ──────────────────────────────────────────────────────
    print(f'\nFlop board texture coverage:')
    tex_cnt = defaultdict(int)
    for b in flop_boards:
        tex_cnt[b['texture']] += 1
    for tex, cnt in sorted(tex_cnt.items(), key=lambda x: -x[1]):
        print(f'  {tex:22s}: {cnt:3d}  B={b_score(tex)}')

    # ── Save outputs ──────────────────────────────────────────────────────────
    OUT_DIR.joinpath('deck_scenarios.json').write_text(
        json.dumps(all_scenarios, ensure_ascii=False, indent=2))
    OUT_DIR.joinpath('deck_boards_flop.json').write_text(
        json.dumps(flop_boards, ensure_ascii=False, indent=2))
    OUT_DIR.joinpath('deck_boards_turn.json').write_text(
        json.dumps(turn_boards, ensure_ascii=False, indent=2))
    OUT_DIR.joinpath('deck_boards_river.json').write_text(
        json.dumps(river_boards, ensure_ascii=False, indent=2))

    print(f'\nSaved:')
    print(f'  deck_scenarios.json ({len(all_scenarios)} scenarios)')
    print(f'  deck_boards_flop.json ({len(flop_boards)} boards)')
    print(f'  deck_boards_turn.json ({len(turn_boards)} boards)')
    print(f'  deck_boards_river.json ({len(river_boards)} boards)')

    # ── Pairwise decision coverage ─────────────────────────────────────────────
    print(f'\nDecision coverage by deck:')
    print(f'{"Deck file":40s}  {"n":>4}  {"Decisions"}')
    for filename in [f for f, _, _ in DECK_FILES]:
        cards = by_file.get(filename, [])
        if not cards:
            continue
        dec_cnt = defaultdict(int)
        for c in cards:
            dec_cnt[c['decision']] += 1
        dec_str = ', '.join(f'{d}={n}' for d, n in sorted(dec_cnt.items()))
        print(f'{filename:40s}  {len(cards):4d}  {dec_str}')

    # ── Missing texture coverage ───────────────────────────────────────────────
    all_textures = {'mono','paired_high','paired_low','2tone_ak','2tone',
                    'rainbow_connected','rainbow_ak','rainbow_q','rainbow'}
    covered = set(tex_cnt.keys())
    missing = all_textures - covered
    if missing:
        print(f'\nFlop textures NOT covered in any deck: {sorted(missing)}')
        print('  → Consider adding boards for these textures to GCP study')
    else:
        print(f'\nAll 9 flop textures covered in deck boards ✓')


if __name__ == '__main__':
    main()
