#!/usr/bin/env python3
"""
analyze_turn_river.py — Analyze GCP turn+river study results.

Produces:
  1. CBet rate by texture × turn_type (pairwise heatmap)
  2. Bet size distribution by texture (dominant size)
  3. OOP fold threshold by texture × bet_size
  4. River bet/bluff rates by texture
  5. Framework update recommendations

Input: results/turn_results.json, results/river_results.json
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median, stdev

OUT_DIR = Path(__file__).parent
RES_DIR = OUT_DIR / 'results'

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

TEXTURES = ['mono','paired_high','paired_low','2tone_ak','2tone',
            'rainbow_connected','rainbow_ak','rainbow_q','rainbow',
            'rainbow_lowconn','2tone_conn']
B_SCORE  = {'mono':70,'paired_high':83,'paired_low':71,'2tone_ak':56,'2tone':50,
            'rainbow_connected':67,'rainbow_ak':62,'rainbow_q':58,'rainbow':55,
            'rainbow_lowconn':55,'2tone_conn':50}


def fmt(v: float | None, pct: bool = True) -> str:
    if v is None: return '  -  '
    if pct: return f'{v:5.1f}%'
    return f'{v:5.1f}'


def cell_stats(vals: list[float]) -> str:
    if not vals: return '  -  '
    if len(vals) == 1: return f'{vals[0]:5.1f}%'
    return f'{mean(vals):5.1f}% ±{stdev(vals):4.1f}'


# ── Load results ──────────────────────────────────────────────────────────────

def load(path: Path) -> list[dict]:
    if not path.exists():
        print(f'WARN: {path} not found')
        return []
    return json.loads(path.read_text())


def main() -> None:
    turn_results  = load(RES_DIR / 'turn_results.json')
    river_results = load(RES_DIR / 'river_results.json')

    if not turn_results and not river_results:
        print('No results found. Run collect_turn_river.sh first.')
        sys.exit(1)

    print(f'Loaded: {len(turn_results)} turn, {len(river_results)} river results')
    errors_t = sum(1 for r in turn_results if r.get('error'))
    errors_r = sum(1 for r in river_results if r.get('error'))
    if errors_t or errors_r:
        print(f'Errors: {errors_t} turn, {errors_r} river')
    print()

    # ── TURN ANALYSIS ─────────────────────────────────────────────────────────

    print('=' * 70)
    print('TURN CBet RATES  (IP bet after OOP check, 4-card board)')
    print('=' * 70)

    # Group by texture × turn_type
    turn_cell: dict[tuple, list[float]] = defaultdict(list)
    turn_tex: dict[str, list[float]] = defaultdict(list)
    turn_raw = [r for r in turn_results if 'ip_cbet_pct' in r and not r.get('error')]

    for r in turn_raw:
        tex  = r.get('texture', '?')
        tt   = r.get('turn_type', '?')
        pct  = r['ip_cbet_pct']
        turn_cell[(tex, tt)].append(pct)
        turn_tex[tex].append(pct)

    # Pairwise heatmap
    turn_types = ['blank', 'overcard', 'connector', 'pair', 'flush', 'deck']
    header = f'{"Texture":22s}'
    for tt in turn_types:
        header += f'  {tt[:7]:>7s}'
    print(header)
    print('-' * (22 + 9 * len(turn_types)))
    for tex in TEXTURES:
        vals_all = turn_tex.get(tex, [])
        row = f'{tex:22s}'
        for tt in turn_types:
            vals = turn_cell.get((tex, tt), [])
            if vals:
                row += f'  {mean(vals):5.1f}%'
            else:
                row += '    -  '
        avg = mean(vals_all) if vals_all else None
        row += f'  avg={avg:.1f}%' if avg else ''
        print(row)

    # ── CBet size distribution ─────────────────────────────────────────────────
    print()
    print('TURN CBet SIZE DISTRIBUTION  (which size dominates per texture)')
    print('-' * 60)
    print(f'{"Texture":22s}  {"33%":>7s}  {"50%":>7s}  {"75%":>7s}  dominant')
    for tex in TEXTURES:
        rows = [r for r in turn_raw if r.get('texture') == tex]
        if not rows:
            continue
        s33 = mean(r.get('ip_cbet_33', 0) for r in rows)
        s50 = mean(r.get('ip_cbet_50', 0) for r in rows)
        s75 = mean(r.get('ip_cbet_75', 0) for r in rows)
        dominant = max([('33%', s33), ('50%', s50), ('75%', s75)], key=lambda x: x[1])[0]
        print(f'{tex:22s}  {s33:5.1f}%  {s50:5.1f}%  {s75:5.1f}%  → {dominant}')

    # ── OOP fold threshold ─────────────────────────────────────────────────────
    print()
    print('OOP FOLD RATES (defense fold % vs each bet size)')
    print('-' * 65)
    print(f'{"Texture":22s}  {"vs33%":>7s}  {"vs50%":>7s}  {"vs75%":>7s}  B-score')
    for tex in sorted(TEXTURES, key=lambda t: B_SCORE.get(t, 55)):
        rows = [r for r in turn_raw if r.get('texture') == tex]
        if not rows:
            continue
        f33 = mean(r['oop_fold_vs33'] for r in rows if 'oop_fold_vs33' in r) if any('oop_fold_vs33' in r for r in rows) else None
        f50 = mean(r['oop_fold_vs50'] for r in rows if 'oop_fold_vs50' in r) if any('oop_fold_vs50' in r for r in rows) else None
        f75 = mean(r['oop_fold_vs75'] for r in rows if 'oop_fold_vs75' in r) if any('oop_fold_vs75' in r for r in rows) else None
        bs  = B_SCORE.get(tex, 55)
        print(f'{tex:22s}  {fmt(f33):>7s}  {fmt(f50):>7s}  {fmt(f75):>7s}  B={bs}')

    # ── CBet by hand tier ──────────────────────────────────────────────────────
    print()
    print('TURN CBet BY HAND TIER  (avg % betting by hand category)')
    print('-' * 75)
    cats = ['overpair', 'top_pair', 'two_overcards', 'air']
    print(f'{"Texture":22s}  ' + '  '.join(f'{c[:9]:>9s}' for c in cats) + '  B')
    for tex in TEXTURES:
        rows = [r for r in turn_raw if r.get('texture') == tex]
        if not rows:
            continue
        bs = B_SCORE.get(tex, 55)
        row = f'{tex:22s}'
        for cat in cats:
            key = f'cbet_{cat}'
            vals = [r[key] for r in rows if key in r]
            row += f'  {mean(vals):7.1f}%' if vals else '      -  '
        row += f'  B={bs}'
        print(row)

    # ── Framework check vs current rules ──────────────────────────────────────
    print()
    print('FRAMEWORK VALIDATION  (GTO vs current turn rules)')
    print('-' * 70)
    print('Current rules:')
    print('  T1 (overpair/top_pair): always bet')
    print('  T2 (2OC):  bet if B ≥ 58')
    print('  T3 (air):  bet if B ≥ 70')
    print()

    thresh_t2 = 58
    thresh_t3 = 70

    t2_correct, t2_total = 0, 0
    t3_correct, t3_total = 0, 0

    for tex in TEXTURES:
        rows = [r for r in turn_raw if r.get('texture') == tex]
        if not rows:
            continue
        bs = B_SCORE.get(tex, 55)
        t2_vals = [r['cbet_two_overcards'] for r in rows if 'cbet_two_overcards' in r]
        t3_vals = [r['cbet_air'] for r in rows if 'cbet_air' in r]
        t2_bet = bs >= thresh_t2
        t3_bet = bs >= thresh_t3

        if t2_vals:
            gto_t2 = mean(t2_vals)
            gto_t2_bet = gto_t2 >= 50
            match_t2 = (t2_bet == gto_t2_bet)
            t2_correct += int(match_t2)
            t2_total   += 1
            flag = '✓' if match_t2 else '✗'
            pred = 'bet' if t2_bet else 'chk'
            act  = 'bet' if gto_t2_bet else 'chk'
            print(f'  T2 {tex:22s} B={bs:2d}  GTO={gto_t2:4.0f}%  pred={pred}  actual={act}  {flag}')

        if t3_vals:
            gto_t3 = mean(t3_vals)
            gto_t3_bet = gto_t3 >= 50
            match_t3 = (t3_bet == gto_t3_bet)
            t3_correct += int(match_t3)
            t3_total   += 1
            flag = '✓' if match_t3 else '✗'
            pred = 'bet' if t3_bet else 'chk'
            act  = 'bet' if gto_t3_bet else 'chk'
            print(f'  T3 {tex:22s} B={bs:2d}  GTO={gto_t3:4.0f}%  pred={pred}  actual={act}  {flag}')

    print()
    if t2_total > 0:
        print(f'T2 accuracy: {t2_correct}/{t2_total} = {t2_correct/t2_total*100:.0f}%')
    if t3_total > 0:
        print(f'T3 accuracy: {t3_correct}/{t3_total} = {t3_correct/t3_total*100:.0f}%')

    # ── RIVER ANALYSIS ────────────────────────────────────────────────────────
    print()
    print('=' * 70)
    print('RIVER BET RATES  (IP first-bet after OOP check, 5-card board)')
    print('=' * 70)

    river_tex: dict[str, list[float]] = defaultdict(list)
    river_raw = [r for r in river_results if 'ip_bet_pct' in r and not r.get('error')]

    for r in river_raw:
        tex = r.get('texture', '?')
        river_tex[tex].append(r['ip_bet_pct'])

    print(f'{"Texture":22s}  {"bet%":>7s}  {"made_hand":>9s}  {"air(bluff)":>10s}  B')
    for tex in TEXTURES:
        rows = [r for r in river_raw if r.get('texture') == tex]
        if not rows:
            continue
        bet_pct = mean(r['ip_bet_pct'] for r in rows)
        made_h  = mean(r['bet_overpair'] for r in rows if 'bet_overpair' in r) if any('bet_overpair' in r for r in rows) else None
        air_h   = mean(r['bet_air'] for r in rows if 'bet_air' in r) if any('bet_air' in r for r in rows) else None
        bs = B_SCORE.get(tex, 55)
        print(f'{tex:22s}  {bet_pct:5.1f}%  {fmt(made_h):>9s}  {fmt(air_h):>10s}  B={bs}')

    # ── Save analysis ──────────────────────────────────────────────────────────
    summary = {
        'n_turn': len(turn_raw),
        'n_river': len(river_raw),
        'turn_cbet_by_texture': {
            tex: round(mean(vs), 2)
            for tex, vs in turn_tex.items() if vs
        },
        'turn_cbet_by_cell': {
            f'{tex}_{tt}': round(mean(vs), 2)
            for (tex, tt), vs in turn_cell.items() if vs
        },
        'river_bet_by_texture': {
            tex: round(mean(vs), 2)
            for tex, vs in river_tex.items() if vs
        },
    }
    (RES_DIR / 'analysis_summary.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2))
    print(f'\nSaved: results/analysis_summary.json')


if __name__ == '__main__':
    main()
