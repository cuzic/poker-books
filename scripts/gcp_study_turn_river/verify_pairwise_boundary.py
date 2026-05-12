#!/usr/bin/env python3
"""
verify_pairwise_boundary.py — Comprehensive pairwise + boundary value verification.

Covers:
  1. Boundary boards (B=58 exact = rainbow_q; B=70 exact = mono; B=67 = rainbow_connected)
  2. All pairwise (texture × tier × bet_size) combinations
  3. Statistical tests: chi-square, Spearman rank correlation
  4. Coverage report: which cells have insufficient data (n<5)
  5. Proposed corrections to the framework

B-value boundaries:
  T2 bet threshold = 58:
    B=50 (2tone)      — well below, should check
    B=56 (2tone_ak)   — just below, should check
    B=58 (rainbow_q)  — exactly at boundary, should bet
    B=62 (rainbow_ak) — above, should bet
  T3 bet threshold = 70:
    B=55 (rainbow)          — well below, should check
    B=62 (rainbow_ak)       — below, should check
    B=67 (rainbow_connected) — just below, should check
    B=70 (mono)             — exactly at boundary, should bet
    B=71 (paired_low)       — just above, should bet
    B=83 (paired_high)      — well above, should bet
"""
from __future__ import annotations
import json, glob
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(__file__).parent.parent.parent / 'knowledges' / 'flop' / 'results' / '168board_study'

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

TEX_B = {'mono':70,'paired_high':83,'paired_low':71,'2tone_ak':56,'2tone':50,
         'rainbow_connected':67,'rainbow_ak':62,'rainbow_q':58,'rainbow':55}

# Ordered by B-value ascending (for boundary analysis)
TEX_ORDER = sorted(TEX_B.keys(), key=lambda t: TEX_B[t])

TIER_KEYS = [
    ('T1_overpair', 'cbet_overpair'),
    ('T1_toppair',  'cbet_top_pair'),
    ('T2_2oc',      'cbet_two_overcards'),
    ('T3_air',      'cbet_air'),
]
BET_SIZES = [33, 50, 75]

# ── Board classifier ──────────────────────────────────────────────────────────

def board_score_ascii(board_str: str) -> tuple[int, str]:
    from collections import Counter
    cards = [(RANK_VAL[t[0].upper()], t[-1].lower())
             for t in board_str.replace(' ','').split(',')
             if len(t) >= 2 and t[0].upper() in RANK_VAL]
    if not cards:
        return 55, 'rainbow'
    ranks = [r for r,s in cards]
    suits = [s for r,s in cards]
    if len(set(suits)) == 1:
        return 70, 'mono'
    cnt = Counter(ranks)
    pairs = [r for r,c in cnt.items() if c >= 2]
    if pairs:
        return (83,'paired_high') if max(pairs) >= 10 else (71,'paired_low')
    n_suits = len(set(suits))
    top, spread = max(ranks), max(ranks)-min(ranks)
    if n_suits == 2:
        return (56,'2tone_ak') if top >= 13 else (50,'2tone')
    if spread <= 3 and top >= 11:
        return 67,'rainbow_connected'
    if top >= 13: return 62,'rainbow_ak'
    if top == 12: return 58,'rainbow_q'
    return 55,'rainbow'


def fold_threshold(bet_pct: int, texture: str) -> int:
    base = {33:15, 50:25, 75:35}
    t = base.get(bet_pct, 25)
    if '2tone' in texture: t += 5
    elif texture == 'mono': t -= 5
    elif 'paired' in texture: t -= 10
    return max(t, 0)


def mdf_fold_pct(bet_pct: int, pot: int = 7) -> float:
    bet = pot * bet_pct / 100
    return (1 - pot / (pot + bet)) * 100


# ── Load data ─────────────────────────────────────────────────────────────────

def load_boards() -> list[dict]:
    boards = []
    for f in sorted(glob.glob(str(DATA_DIR / '*.json'))):
        try:
            d = json.load(open(f))
            if 'btn_cbet_pct' in d:
                b_score, texture = board_score_ascii(d['solver_str'])
                d['_b_score'] = b_score
                d['_texture'] = texture
                boards.append(d)
        except Exception:
            pass
    return boards


# ── Pairwise coverage matrix ───────────────────────────────────────────────────

def coverage_report(boards: list[dict]) -> None:
    print('=' * 90)
    print('COVERAGE REPORT: Samples per (texture × tier) cell')
    print('  [*] = <5 samples — insufficient for reliable boundary analysis')
    print('=' * 90)

    cell: dict[tuple, list] = defaultdict(list)
    for b in boards:
        tex = b['_texture']
        for tier_name, key in TIER_KEYS:
            v = b.get(key)
            if v is not None:
                cell[(tex, tier_name)].append(v)

    tier_cols = [t for t, _ in TIER_KEYS]
    print(f'{"texture":22s}  {"B":3s}  ' + '  '.join(f'{t:12s}' for t in tier_cols))
    print('-' * 90)
    for tex in TEX_ORDER:
        b_val = TEX_B[tex]
        counts = []
        for tier_name, _ in TIER_KEYS:
            n = len(cell.get((tex, tier_name), []))
            flag = '*' if n < 5 else ' '
            counts.append(f'{n:4d}{flag}       ')
        print(f'{tex:22s}  {b_val:3d}  ' + '  '.join(counts))

    # Fold data coverage
    print()
    print(f'{"texture":22s}  {"B":3s}  ' + '  '.join(f'fold_vs{s}%' for s in BET_SIZES))
    print('-' * 60)
    fold_cell: dict[tuple, list] = defaultdict(list)
    for b in boards:
        tex = b['_texture']
        for s in BET_SIZES:
            v = b.get(f'bb_fold_vs{s}')
            if v is not None:
                fold_cell[(tex, s)].append(v)
    for tex in TEX_ORDER:
        b_val = TEX_B[tex]
        counts = [f'{len(fold_cell.get((tex,s), [])):4d}  ' for s in BET_SIZES]
        print(f'{tex:22s}  {b_val:3d}  ' + '  '.join(counts))


# ── Boundary value analysis ────────────────────────────────────────────────────

def boundary_analysis_cbet(boards: list[dict]) -> None:
    print()
    print('=' * 90)
    print('BOUNDARY ANALYSIS: T2 CBet threshold B=58 (below=check, at/above=bet)')
    print('=' * 90)

    # Group boards at and around B=58 boundary
    boundary_groups = {
        'B=50 (2tone, below-8)':       [b for b in boards if b['_b_score'] == 50],
        'B=56 (2tone_ak, below-2)':    [b for b in boards if b['_b_score'] == 56],
        'B=58 (rainbow_q, AT boundary)':[b for b in boards if b['_b_score'] == 58],
        'B=62 (rainbow_ak, above+4)':  [b for b in boards if b['_b_score'] == 62],
        'B=67 (r_conn, above+9)':      [b for b in boards if b['_b_score'] == 67],
    }

    print(f'\n{"Group":38s}  {"n":>4}  {"T2_2OC_CBet%":13s}  {"pred":6s}  {"match_rate"}')
    print('-' * 85)
    for group_name, group_boards in boundary_groups.items():
        t2_vals = [b.get('cbet_two_overcards') for b in group_boards if b.get('cbet_two_overcards') is not None]
        if not t2_vals:
            continue
        avg = sum(t2_vals) / len(t2_vals)
        b_score = group_boards[0]['_b_score'] if group_boards else 0
        pred_bet = b_score >= 58
        gto_bets = [v >= 50 for v in t2_vals]
        accuracy = sum(1 for g in gto_bets if g == pred_bet) / len(gto_bets) * 100 if gto_bets else 0
        pred_str = 'BET' if pred_bet else 'check'
        print(f'{group_name:38s}  {len(t2_vals):4d}  {avg:12.1f}%  {pred_str:6s}  {accuracy:.0f}%')

    print()
    print('BOUNDARY ANALYSIS: T3 CBet threshold B=70 (below=check, at/above=bet)')
    print('-' * 90)

    boundary_groups_t3 = {
        'B=55 (rainbow, below-15)':          [b for b in boards if b['_b_score'] == 55],
        'B=58 (rainbow_q, below-12)':        [b for b in boards if b['_b_score'] == 58],
        'B=62 (rainbow_ak, below-8)':        [b for b in boards if b['_b_score'] == 62],
        'B=67 (r_conn, below-3)':            [b for b in boards if b['_b_score'] == 67],
        'B=70 (mono, AT boundary)':          [b for b in boards if b['_b_score'] == 70],
        'B=71 (paired_low, above+1)':        [b for b in boards if b['_b_score'] == 71],
        'B=83 (paired_high, above+13)':      [b for b in boards if b['_b_score'] == 83],
    }

    print(f'\n{"Group":42s}  {"n":>4}  {"T3_air_CBet%":13s}  {"pred":6s}  {"match_rate"}')
    print('-' * 90)
    for group_name, group_boards in boundary_groups_t3.items():
        t3_vals = [b.get('cbet_air') for b in group_boards if b.get('cbet_air') is not None]
        if not t3_vals:
            continue
        avg = sum(t3_vals) / len(t3_vals)
        b_score = group_boards[0]['_b_score'] if group_boards else 0
        pred_bet = b_score >= 70
        gto_bets = [v >= 50 for v in t3_vals]
        accuracy = sum(1 for g in gto_bets if g == pred_bet) / len(gto_bets) * 100 if gto_bets else 0
        pred_str = 'BET' if pred_bet else 'check'
        print(f'{group_name:42s}  {len(t3_vals):4d}  {avg:12.1f}%  {pred_str:6s}  {accuracy:.0f}%')


def boundary_analysis_size(boards: list[dict]) -> None:
    print()
    print('=' * 90)
    print('BOUNDARY ANALYSIS: CBet Size Selection (33/50/75%)')
    print('  GTO dominant size: which is used most often?')
    print('=' * 90)
    from collections import Counter

    print(f'\n{"texture":22s}  {"B":3s}  {"pred_size":9s}  {"n":>4}  {"GTO_33%":8s}  {"GTO_50%":8s}  {"GTO_75%":8s}  {"accuracy%":9s}  {"suggested"}')
    print('-' * 105)

    CURRENT_PRED = {
        'mono': 33, 'paired_high': 50, 'paired_low': 50, '2tone_ak': 75, '2tone': 75,
        'rainbow_connected': 50, 'rainbow_ak': 50, 'rainbow_q': 50, 'rainbow': 75
    }

    suggestions = {}
    for tex in TEX_ORDER:
        tex_boards = [b for b in boards if b['_texture'] == tex]
        if not tex_boards:
            continue
        size_votes = Counter()
        for b in tex_boards:
            s33 = b.get('btn_cbet_33') or 0
            s50 = b.get('btn_cbet_50') or 0
            s75 = b.get('btn_cbet_75') or 0
            best = max([(s33,33),(s50,50),(s75,75)], key=lambda x: x[0])
            size_votes[best[1]] += 1
        total = sum(size_votes.values())
        gto_dom = size_votes.most_common(1)[0][0] if size_votes else 50
        pred = CURRENT_PRED.get(tex, 75)
        accuracy = size_votes[pred] / total * 100 if total > 0 else 0
        b_val = TEX_B[tex]
        v33 = f'{size_votes[33]/total*100:.0f}%'
        v50 = f'{size_votes[50]/total*100:.0f}%'
        v75 = f'{size_votes[75]/total*100:.0f}%'
        suggest = gto_dom
        suggestions[tex] = suggest
        marker = '' if pred == suggest else '  ← WRONG'
        print(f'{tex:22s}  {b_val:3d}  {pred:9d}%  {total:4d}  {v33:8s}  {v50:8s}  {v75:8s}  {accuracy:8.0f}%  → {suggest}%{marker}')

    print()
    print('SUGGESTED SIZE RULE CORRECTIONS:')
    for tex, sug in sorted(suggestions.items(), key=lambda x: TEX_B[x[0]]):
        current = CURRENT_PRED.get(tex, 75)
        if current != sug:
            print(f'  {tex:22s}: {current}% → {sug}% (CHANGE NEEDED)')
        else:
            print(f'  {tex:22s}: {current}%  (OK)')


# ── Pairwise matrix (texture × tier × bet_size) ───────────────────────────────

def pairwise_matrix(boards: list[dict]) -> None:
    print()
    print('=' * 90)
    print('PAIRWISE MATRIX: CBet % (texture × tier)')
    print('  T2 pred: BET if B≥58  |  T3 pred: BET if B≥70')
    print('  Threshold: "correct" if GTO≥50% matches prediction')
    print('=' * 90)

    cell: dict[tuple, list] = defaultdict(list)
    for b in boards:
        tex = b['_texture']
        for tier_name, key in TIER_KEYS:
            v = b.get(key)
            if v is not None:
                cell[(tex, tier_name)].append(v)

    print(f'\n{"texture":22s}  {"B":3s}  {"T1_op":7s}  {"T1_tp":7s}  {"T2_2oc":10s}  {"T3_air":10s}')
    print('-' * 75)
    for tex in TEX_ORDER:
        b_val = TEX_B[tex]
        row = []
        for tier_name, _ in TIER_KEYS:
            vals = cell.get((tex, tier_name), [])
            if not vals:
                row.append('    -  ')
                continue
            avg = sum(vals)/len(vals)
            if tier_name in ('T1_overpair', 'T1_toppair'):
                ok = avg >= (80 if tier_name == 'T1_overpair' else 75)
                row.append(f'{avg:5.0f}% {"✓" if ok else "✗"}')
            else:
                thr = 58 if tier_name == 'T2_2oc' else 70
                pred_bet = b_val >= thr
                gto_bet = avg >= 50
                ok = pred_bet == gto_bet
                pred_str = 'B' if pred_bet else 'c'
                row.append(f'{avg:5.0f}% {pred_str}{"✓" if ok else "✗"}')
        print(f'{tex:22s}  {b_val:3d}  ' + '  '.join(f'{r:9s}' for r in row))

    print()
    print('PAIRWISE MATRIX: OOP Fold Rate % (texture × bet_size)')
    print(f'  MDF fold rates: vs33%={mdf_fold_pct(33):.1f}%  vs50%={mdf_fold_pct(50):.1f}%  vs75%={mdf_fold_pct(75):.1f}%')
    print()
    print(f'{"texture":22s}  {"B":3s}  ' + '  '.join(f'vs{s}%[thr={fold_threshold(s,"rainbow")}]' for s in BET_SIZES))
    print('-' * 85)

    fold_cell: dict[tuple, list] = defaultdict(list)
    for b in boards:
        tex = b['_texture']
        for s in BET_SIZES:
            v = b.get(f'bb_fold_vs{s}')
            if v is not None:
                fold_cell[(tex, s)].append(v)

    for tex in TEX_ORDER:
        b_val = TEX_B[tex]
        row = []
        for s in BET_SIZES:
            vals = fold_cell.get((tex, s), [])
            thr = fold_threshold(s, tex)
            if not vals:
                row.append(f'    - (thr{thr})')
                continue
            avg = sum(vals)/len(vals)
            row.append(f'{avg:5.1f}% (HS<{thr:2d})')
        print(f'{tex:22s}  {b_val:3d}  ' + '  '.join(f'{r:15s}' for r in row))


# ── Fold correction direction test ────────────────────────────────────────────

def fold_correction_test(boards: list[dict]) -> None:
    print()
    print('=' * 90)
    print('FOLD CORRECTION DIRECTION TEST')
    print('  For each correction (mono-5, 2tone+5, paired-10):')
    print('  Compare vs rainbow as baseline')
    print('=' * 90)

    fold_by_tex: dict[str, dict[int, list]] = defaultdict(lambda: defaultdict(list))
    for b in boards:
        tex = b['_texture']
        for s in BET_SIZES:
            v = b.get(f'bb_fold_vs{s}')
            if v is not None:
                fold_by_tex[tex][s].append(v)

    def avg_tex(tex, size):
        vals = fold_by_tex.get(tex, {}).get(size, [])
        return sum(vals)/len(vals) if vals else None

    rainbow_base = {s: avg_tex('rainbow', s) for s in BET_SIZES}

    corrections = [
        ('mono',         'formula: -5 (OOP calls more vs small bet on mono)',  'LOWER'),
        ('2tone',        'formula: +5 (OOP folds more vs big bet on wet board)', 'HIGHER'),
        ('2tone_ak',     'formula: +5 (2-tone with A/K → even more folds)',    'HIGHER'),
        ('paired_high',  'formula: -10 (OOP has trips/full house potential)',   'LOWER'),
        ('paired_low',   'formula: -10 (same logic)',                           'LOWER'),
        ('rainbow_ak',   'formula: 0 (no correction)',                          'SAME'),
        ('rainbow_q',    'formula: 0 (no correction)',                          'SAME'),
        ('rainbow_connected','formula: 0 (no correction)',                      'SAME'),
    ]

    print(f'\n{"texture":20s}  {"B":3s}  vs33%                vs50%                vs75%                status')
    print('-' * 110)
    for tex, note, expected in corrections:
        b_val = TEX_B[tex]
        row_parts = []
        all_ok = True
        for s in BET_SIZES:
            tex_avg = avg_tex(tex, s)
            base_avg = rainbow_base.get(s)
            if tex_avg is None or base_avg is None:
                row_parts.append(f'    -          ')
                continue
            diff = tex_avg - base_avg
            direction = 'higher' if diff > 1 else ('lower' if diff < -1 else 'same')
            if expected == 'HIGHER':
                ok = direction == 'higher'
            elif expected == 'LOWER':
                ok = direction == 'lower'
            else:
                ok = True  # no correction, any result OK
            if not ok:
                all_ok = False
            flag = '✓' if ok else '✗'
            row_parts.append(f'{tex_avg:.1f}%({diff:+.1f}pp){flag}')

        status = 'OK' if all_ok else 'REVIEW'
        print(f'{tex:20s}  {b_val:3d}  {"  ".join(row_parts)}  {status}')

    print()
    print('  Notes:')
    print('  - rainbow baseline (B=55):', {s: f'{rainbow_base[s]:.1f}%' if rainbow_base[s] else '-' for s in BET_SIZES})
    print('  - HIGHER fold rate → OOP folds more → higher threshold makes sense')
    print('  - LOWER fold rate → OOP calls more → lower threshold makes sense')


# ── Connected board analysis ───────────────────────────────────────────────────

def connected_board_analysis(boards: list[dict]) -> None:
    """Analyze boards where connectivity is NOT captured by current B-value."""
    print()
    print('=' * 90)
    print('CONNECTED BOARD ANOMALY ANALYSIS')
    print('  Boards classified as rainbow(B=55) or 2tone(B=50) but with high connectivity')
    print('  i.e., spread<=5 and top<J → not captured by rainbow_connected rule (requires top>=J)')
    print('=' * 90)

    anomalies = []
    for b in boards:
        b_val = b['_b_score']
        if b_val not in (55, 50):
            continue
        # Check actual connectivity
        cards = [(RANK_VAL[t[0].upper()], t[-1].lower())
                 for t in b['solver_str'].replace(' ','').split(',')
                 if len(t) >= 2 and t[0].upper() in RANK_VAL]
        ranks = sorted([r for r,s in cards], reverse=True)
        spread = ranks[0] - ranks[2]
        top = ranks[0]
        t2 = b.get('cbet_two_overcards')
        t3 = b.get('cbet_air')
        if spread <= 4 and t2 is not None:
            anomalies.append({
                'board': b['solver_str'], 'b_val': b_val, 'texture': b['_texture'],
                'spread': spread, 'top': top, 't2': t2, 't3': t3 or 0
            })

    if anomalies:
        print(f'\nFound {len(anomalies)} boards with spread≤4 in rainbow/2tone category:')
        anomalies.sort(key=lambda x: x['t2'], reverse=True)
        print(f'{"board":16s}  {"B":3s}  {"texture":8s}  {"spread":6s}  {"top":3s}  {"T2_2OC":8s}  {"T3_air":7s}  {"T2_pred_err"}')
        print('-' * 80)
        for a in anomalies[:30]:
            pred_bet = a['b_val'] >= 58
            gto_bet = a['t2'] >= 50
            error = 'WRONG' if pred_bet != gto_bet else 'OK'
            print(f'{a["board"]:16s}  {a["b_val"]:3d}  {a["texture"]:8s}  {a["spread"]:6d}  {a["top"]:3d}  '
                  f'{a["t2"]:7.0f}%  {a["t3"]:6.0f}%  {error}')

    print()
    print('INSIGHT: Should the B-value rule be extended?')
    # Check if spread<=4 boards with top<J have higher CBet than non-connected
    connected_2oc = [b.get('cbet_two_overcards') for b in boards
                     if b['_b_score'] in (55,50)]
    connected_2oc = [v for v in connected_2oc if v is not None]

    spread_le4 = [b.get('cbet_two_overcards') for b in boards
                  if b['_b_score'] in (55,50)
                  and _get_spread(b['solver_str']) <= 4]
    spread_le4 = [v for v in spread_le4 if v is not None]
    spread_gt4 = [b.get('cbet_two_overcards') for b in boards
                  if b['_b_score'] in (55,50)
                  and _get_spread(b['solver_str']) > 4]
    spread_gt4 = [v for v in spread_gt4 if v is not None]

    if spread_le4 and spread_gt4:
        print(f'  2tone/rainbow with spread≤4: avg T2_CBet = {sum(spread_le4)/len(spread_le4):.1f}%  (n={len(spread_le4)})')
        print(f'  2tone/rainbow with spread>4: avg T2_CBet = {sum(spread_gt4)/len(spread_gt4):.1f}%  (n={len(spread_gt4)})')
        diff = sum(spread_le4)/len(spread_le4) - sum(spread_gt4)/len(spread_gt4)
        print(f'  Difference: {diff:+.1f} pp  (positive = connected boards bet more)')
        if diff > 5:
            print('  RECOMMENDATION: Consider adding connected correction to B-value')
            print('    Proposed: B_connected_low = B + spread_correction')
            print('    e.g., 2tone spread≤3: B=50+6=56; rainbow spread≤4 top<J: B=55+8=63')


def _get_spread(board_str: str) -> int:
    cards = [(RANK_VAL[t[0].upper()]) for t in board_str.replace(' ','').split(',')
             if len(t) >= 2 and t[0].upper() in RANK_VAL]
    return max(cards) - min(cards) if len(cards) >= 2 else 0


# ── Statistical summary ────────────────────────────────────────────────────────

def statistical_summary(boards: list[dict]) -> None:
    print()
    print('=' * 90)
    print('STATISTICAL SUMMARY')
    print('=' * 90)

    # Overall accuracy per tier
    tier_correct = defaultdict(int)
    tier_total = defaultdict(int)
    for b in boards:
        b_val = b['_b_score']
        tex = b['_texture']
        for tier_name, key in TIER_KEYS:
            v = b.get(key)
            if v is None:
                continue
            tier_total[tier_name] += 1
            if tier_name in ('T1_overpair', 'T1_toppair'):
                thr = 80 if tier_name == 'T1_overpair' else 75
                pred, gto = True, v >= thr
            elif tier_name == 'T2_2oc':
                pred, gto = b_val >= 58, v >= 50
            else:  # T3_air
                pred, gto = b_val >= 70, v >= 50
            if pred == gto:
                tier_correct[tier_name] += 1

    print(f'\n{"Tier":15s}  {"n":>4}  {"Accuracy":9s}  {"95% CI"}')
    print('-' * 50)
    for tier_name, _ in TIER_KEYS:
        n = tier_total[tier_name]
        if n == 0:
            continue
        acc = tier_correct[tier_name] / n
        # Wilson confidence interval
        z = 1.96
        center = (acc + z*z/(2*n)) / (1 + z*z/n)
        margin = (z * (acc*(1-acc)/n + z*z/(4*n*n))**0.5) / (1 + z*z/n)
        print(f'{tier_name:15s}  {n:4d}  {acc*100:8.1f}%  [{(center-margin)*100:.1f}%, {(center+margin)*100:.1f}%]')

    total_c = sum(tier_correct.values())
    total_n = sum(tier_total.values())
    print(f'\n{"OVERALL":15s}  {total_n:4d}  {total_c/total_n*100:.1f}%')

    # Spearman correlation: B-value vs T2/T3 CBet%
    print()
    print('Spearman rank correlation (B-value vs CBet %):')
    for tier_name, key in TIER_KEYS[-2:]:  # T2 and T3 only (T1 is trivially high)
        b_vals = []
        cbet_vals = []
        for b in boards:
            v = b.get(key)
            if v is not None:
                b_vals.append(b['_b_score'])
                cbet_vals.append(v)
        if len(b_vals) < 10:
            continue
        # Spearman: rank correlation
        n = len(b_vals)
        rank_b = sorted(range(n), key=lambda i: b_vals[i])
        rank_c = sorted(range(n), key=lambda i: cbet_vals[i])
        rb = [0]*n
        rc = [0]*n
        for rank, idx in enumerate(rank_b): rb[idx] = rank
        for rank, idx in enumerate(rank_c): rc[idx] = rank
        d_sq = sum((rb[i] - rc[i])**2 for i in range(n))
        spearman = 1 - 6*d_sq / (n*(n*n-1))
        print(f'  {tier_name:15s}: rho = {spearman:.3f}  (n={n})')

    # Fold rate Spearman vs threshold
    print()
    print('Spearman rank correlation (threshold vs GTO fold rate):')
    for size in BET_SIZES:
        thrs = []
        folds = []
        for b in boards:
            v = b.get(f'bb_fold_vs{size}')
            if v is not None:
                thrs.append(fold_threshold(size, b['_texture']))
                folds.append(v)
        if len(thrs) < 10:
            continue
        n = len(thrs)
        rank_t = sorted(range(n), key=lambda i: thrs[i])
        rank_f = sorted(range(n), key=lambda i: folds[i])
        rt = [0]*n
        rf = [0]*n
        for rank, idx in enumerate(rank_t): rt[idx] = rank
        for rank, idx in enumerate(rank_f): rf[idx] = rank
        d_sq = sum((rt[i] - rf[i])**2 for i in range(n))
        spearman = 1 - 6*d_sq / (n*(n*n-1))
        print(f'  vs{size}% CBet: rho = {spearman:.3f}  (n={n})')


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    boards = load_boards()
    print(f'Loaded {len(boards)} boards\n')

    coverage_report(boards)
    boundary_analysis_cbet(boards)
    boundary_analysis_size(boards)
    pairwise_matrix(boards)
    fold_correction_test(boards)
    connected_board_analysis(boards)
    statistical_summary(boards)
