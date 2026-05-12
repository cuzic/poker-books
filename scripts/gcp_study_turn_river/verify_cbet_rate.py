#!/usr/bin/env python3
"""
verify_cbet_rate.py — Validate flop CBet rate framework against 168-board GTO data.

Framework under test:
  T1 (HS≥65, overpair/top_pair):   always CBet
  T2 (HS≥20, two_overcards):       CBet if B≥58
  T3 (HS<20,  air):                 CBet if B≥70
  Size: mono→33%, paired→50%, B<58→75%, else→50%

GTO data: knowledges/flop/results/168board_study/*.json
Each file has: btn_cbet_pct, btn_cbet_33/50/75, cbet_overpair, cbet_two_overcards,
               cbet_top_pair, cbet_air, category, solver_str, ...

Outputs:
  1. Per-tier accuracy (T1/T2/T3 CBet decision)
  2. Size selection accuracy (mono/paired/etc.)
  3. Error table for mismatched boards
"""
from __future__ import annotations
import json
import glob
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent.parent / 'knowledges' / 'flop' / 'results' / '168board_study'

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

# ── Board score (9-rule) ──────────────────────────────────────────────────────

def board_score_ascii(board_str: str) -> tuple[int, str]:
    from collections import Counter
    cards = []
    for token in board_str.replace(' ', '').split(','):
        if len(token) >= 2 and token[0].upper() in RANK_VAL:
            cards.append((RANK_VAL[token[0].upper()], token[-1].lower()))
    if not cards:
        return 55, 'rainbow'
    ranks = [r for r, s in cards]
    suits = [s for r, s in cards]
    if len(set(suits)) == 1:
        return 70, 'mono'
    cnt = Counter(ranks)
    pairs = [r for r, c in cnt.items() if c >= 2]
    if pairs:
        top_pair = max(pairs)
        return (83, 'paired_high') if top_pair >= 10 else (71, 'paired_low')
    n_suits = len(set(suits))
    top_rank = max(ranks)
    spread = max(ranks) - min(ranks)
    if n_suits == 2:
        return (56, '2tone_ak') if top_rank >= 13 else (50, '2tone')
    if spread <= 3 and top_rank >= 11:
        return 67, 'rainbow_connected'
    if top_rank >= 13:
        return 62, 'rainbow_ak'
    if top_rank == 12:
        return 58, 'rainbow_q'
    return 55, 'rainbow'


def predict_cbet_size(b_score: int, texture: str) -> int:
    if texture == 'mono':
        return 33
    if texture in ('paired_high', 'paired_low'):
        return 50
    if b_score < 58:
        return 75
    return 50


def predict_tier_decision(tier: str, b_score: int) -> bool:
    if tier == 'T1':
        return True
    if tier == 'T2':
        return b_score >= 58
    return b_score >= 70  # T3


# ── Load data ─────────────────────────────────────────────────────────────────

def load_boards() -> list[dict]:
    boards = []
    for f in sorted(glob.glob(str(DATA_DIR / '*.json'))):
        try:
            d = json.load(open(f))
            if 'btn_cbet_pct' in d and 'cbet_overpair' in d:
                boards.append(d)
        except Exception:
            pass
    return boards


# ── Analysis ──────────────────────────────────────────────────────────────────

def run_cbet_verification() -> None:
    boards = load_boards()
    print(f'Loaded {len(boards)} boards with hand-category CBet data\n')

    # Per-tier validation
    tier_results: dict[str, dict] = {
        'T1_overpair': {'correct': 0, 'wrong': 0, 'gto_vals': []},
        'T1_toppair':  {'correct': 0, 'wrong': 0, 'gto_vals': []},
        'T2_2oc':      {'correct': 0, 'wrong': 0, 'gto_vals': [], 'b_right': [], 'b_wrong': []},
        'T3_air':      {'correct': 0, 'wrong': 0, 'gto_vals': [], 'b_right': [], 'b_wrong': []},
    }

    size_results: dict[str, dict] = {}
    errors: list[dict] = []

    for b in boards:
        b_score, texture = board_score_ascii(b['solver_str'])

        # T1: overpair — should always bet (≥80% is "correct")
        op = b.get('cbet_overpair')
        if op is not None:
            pred = True
            gto_bet = op >= 80
            tier_results['T1_overpair']['gto_vals'].append(op)
            if gto_bet:
                tier_results['T1_overpair']['correct'] += 1
            else:
                tier_results['T1_overpair']['wrong'] += 1
                errors.append({'board': b['solver_str'], 'b_score': b_score, 'texture': texture,
                                'tier': 'T1_overpair', 'prediction': 'always_bet',
                                'gto_cbet': op})

        # T1: top_pair — should always bet (≥75%)
        tp = b.get('cbet_top_pair')
        if tp is not None:
            gto_bet = tp >= 75
            tier_results['T1_toppair']['gto_vals'].append(tp)
            if gto_bet:
                tier_results['T1_toppair']['correct'] += 1
            else:
                tier_results['T1_toppair']['wrong'] += 1
                errors.append({'board': b['solver_str'], 'b_score': b_score, 'texture': texture,
                                'tier': 'T1_toppair', 'prediction': 'always_bet',
                                'gto_cbet': tp})

        # T2: two_overcards — should bet if B≥58
        t2 = b.get('cbet_two_overcards')
        if t2 is not None:
            pred_bet = b_score >= 58
            gto_bet = t2 >= 50  # threshold: majority action
            tier_results['T2_2oc']['gto_vals'].append(t2)
            if pred_bet == gto_bet:
                tier_results['T2_2oc']['correct'] += 1
                tier_results['T2_2oc']['b_right'].append(b_score)
            else:
                tier_results['T2_2oc']['wrong'] += 1
                tier_results['T2_2oc']['b_wrong'].append(b_score)
                errors.append({'board': b['solver_str'], 'b_score': b_score, 'texture': texture,
                                'tier': 'T2_2oc',
                                'prediction': f'bet(B={b_score}≥58)' if pred_bet else f'check(B={b_score}<58)',
                                'gto_cbet': t2})

        # T3: air — should bet if B≥70
        t3 = b.get('cbet_air')
        if t3 is not None:
            pred_bet = b_score >= 70
            gto_bet = t3 >= 50
            tier_results['T3_air']['gto_vals'].append(t3)
            if pred_bet == gto_bet:
                tier_results['T3_air']['correct'] += 1
                tier_results['T3_air']['b_right'].append(b_score)
            else:
                tier_results['T3_air']['wrong'] += 1
                tier_results['T3_air']['b_wrong'].append(b_score)
                errors.append({'board': b['solver_str'], 'b_score': b_score, 'texture': texture,
                                'tier': 'T3_air',
                                'prediction': f'bet(B={b_score}≥70)' if pred_bet else f'check(B={b_score}<70)',
                                'gto_cbet': t3})

        # Size selection
        pred_size = predict_cbet_size(b_score, texture)
        # Dominant size from GTO data
        size_map = {33: b.get('btn_cbet_33', 0),
                    50: b.get('btn_cbet_50', 0),
                    75: b.get('btn_cbet_75', 0)}
        if any(v is not None for v in size_map.values()):
            gto_dominant = max(size_map, key=lambda k: size_map[k] or 0)
            if texture not in size_results:
                size_results[texture] = {'correct': 0, 'total': 0, 'preds': defaultdict(int), 'gtos': defaultdict(int)}
            size_results[texture]['total'] += 1
            size_results[texture]['preds'][pred_size] += 1
            size_results[texture]['gtos'][gto_dominant] += 1
            if pred_size == gto_dominant:
                size_results[texture]['correct'] += 1

    # ── Report ────────────────────────────────────────────────────────────────
    print('=' * 70)
    print('SECTION 1: CBet Decision Accuracy by Tier')
    print('=' * 70)
    print(f'{"Tier":15s}  {"n":>4}  {"correct%":>9}  {"avg_GTO_CBet%":>14}  {"Notes"}')
    print('-' * 70)
    for tier_name, r in tier_results.items():
        total = r['correct'] + r['wrong']
        if total == 0:
            continue
        pct = r['correct'] / total * 100
        avg_gto = sum(r['gto_vals']) / len(r['gto_vals']) if r['gto_vals'] else 0
        if tier_name in ('T1_overpair', 'T1_toppair'):
            notes = f'threshold: GTO≥80%' if tier_name == 'T1_overpair' else 'threshold: GTO≥75%'
        elif tier_name == 'T2_2oc':
            notes = f'threshold: B≥58 → bet; avg_b_right={sum(r["b_right"])/len(r["b_right"]):.0f} avg_b_wrong={sum(r["b_wrong"])/len(r["b_wrong"]):.0f}' if r['b_right'] and r['b_wrong'] else ''
        else:
            notes = f'threshold: B≥70 → bet; avg_b_right={sum(r["b_right"])/len(r["b_right"]):.0f} avg_b_wrong={sum(r["b_wrong"])/len(r["b_wrong"]):.0f}' if r['b_right'] and r['b_wrong'] else ''
        print(f'{tier_name:15s}  {total:4d}  {pct:8.1f}%  {avg_gto:13.1f}%  {notes}')

    print()
    print('=' * 70)
    print('SECTION 2: Average GTO CBet % by Texture × Tier')
    print('=' * 70)
    # Group by texture
    by_texture: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for b in boards:
        b_score, texture = board_score_ascii(b['solver_str'])
        for tier, key in [('T1_op', 'cbet_overpair'), ('T1_tp', 'cbet_top_pair'),
                          ('T2_2oc', 'cbet_two_overcards'), ('T3_air', 'cbet_air')]:
            v = b.get(key)
            if v is not None:
                by_texture[texture][tier].append(v)

    print(f'{"texture":22s}  {"B":3s}  {"T1_op":6s}  {"T1_tp":6s}  {"T2_2oc":7s}  {"T3_air":7s}  {"pred_T2":7s}  {"pred_T3":7s}')
    print('-' * 75)

    # B-score for display
    tex_b = {'mono':70,'paired_high':83,'paired_low':71,'2tone_ak':56,'2tone':50,
             'rainbow_connected':67,'rainbow_ak':62,'rainbow_q':58,'rainbow':55}

    for tex in sorted(tex_b.keys()):
        b_score = tex_b[tex]
        row = by_texture.get(tex, {})
        def avg(lst): return f'{sum(lst)/len(lst):.0f}%' if lst else '   -'
        pred_t2 = 'BET' if b_score >= 58 else 'check'
        pred_t3 = 'BET' if b_score >= 70 else 'check'
        print(f'{tex:22s}  {b_score:3d}  {avg(row.get("T1_op",[]))} {avg(row.get("T1_tp",[]))}   '
              f'{avg(row.get("T2_2oc",[]))}    {avg(row.get("T3_air",[]))}  '
              f'{pred_t2:7s}  {pred_t3:7s}')

    print()
    print('=' * 70)
    print('SECTION 3: CBet Size Selection Accuracy')
    print('=' * 70)
    print(f'{"texture":22s}  {"pred_size":9s}  {"correct%":9s}  {"n":>4}  {"GTO dominant"}')
    print('-' * 70)
    for tex in sorted(size_results.keys()):
        r = size_results[tex]
        pct = r['correct'] / r['total'] * 100 if r['total'] > 0 else 0
        pred = max(r['preds'], key=r['preds'].get)
        gto_dom = max(r['gtos'], key=r['gtos'].get)
        print(f'{tex:22s}  {pred:9d}%  {pct:8.1f}%  {r["total"]:4d}  '
              f'GTO≈{gto_dom}% (counts: 33={r["gtos"][33]} 50={r["gtos"][50]} 75={r["gtos"][75]})')

    print()
    print('=' * 70)
    print('SECTION 4: T2/T3 Error Analysis (Prediction Mismatch)')
    print('=' * 70)
    t2_errors = [e for e in errors if e['tier'] == 'T2_2oc']
    t3_errors = [e for e in errors if e['tier'] == 'T3_air']

    print(f'T2 (2OC) errors: {len(t2_errors)}')
    for e in sorted(t2_errors, key=lambda x: x['gto_cbet'], reverse=True)[:10]:
        print(f'  {e["board"]:14s}  B={e["b_score"]:3d} ({e["texture"]})  '
              f'pred={e["prediction"]}  GTO_CBet={e["gto_cbet"]:.0f}%')

    print(f'\nT3 (air) errors: {len(t3_errors)}')
    for e in sorted(t3_errors, key=lambda x: x['gto_cbet'], reverse=True)[:10]:
        print(f'  {e["board"]:14s}  B={e["b_score"]:3d} ({e["texture"]})  '
              f'pred={e["prediction"]}  GTO_CBet={e["gto_cbet"]:.0f}%')

    # Overall accuracy
    total_correct = sum(r['correct'] for r in tier_results.values())
    total_all = sum(r['correct'] + r['wrong'] for r in tier_results.values())
    print(f'\n{"=" * 70}')
    print(f'OVERALL CBet Decision Accuracy: {total_correct}/{total_all} = {total_correct/total_all*100:.1f}%')
    print('=' * 70)


if __name__ == '__main__':
    run_cbet_verification()
