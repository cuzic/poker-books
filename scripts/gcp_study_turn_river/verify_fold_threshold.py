#!/usr/bin/env python3
"""
verify_fold_threshold.py — Validate defense fold threshold formula against GTO data.

Formula under test:
  Base: vs33%→15, vs50%→25, vs75%→35
  Board corrections: 2tone+5, mono-5, paired-10

Validation method:
  1. GTO data has bb_fold_vs33/50/75: actual % of OOP range that folds
  2. The threshold formula predicts a HandScore cutoff.
  3. Estimate the "predicted fold rate" by computing:
       what fraction of a typical OOP range has HS < threshold on each board?
  4. Compare predicted vs actual fold rates; check direction of corrections.

Also validates:
  - MDF compliance: GTO fold rate vs 1-MDF
  - Correction direction: mono should fold less than rainbow; 2tone more
"""
from __future__ import annotations
import json
import glob
from pathlib import Path
from collections import defaultdict
import statistics

DATA_DIR = Path(__file__).parent.parent.parent / 'knowledges' / 'flop' / 'results' / '168board_study'

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

# ── Board score ───────────────────────────────────────────────────────────────

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
    from collections import Counter
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


def fold_threshold(bet_pct: int, texture: str) -> int:
    """New fold threshold formula."""
    base = {33: 15, 50: 25, 75: 35}
    t = base.get(bet_pct, 25)
    if '2tone' in texture:
        t += 5
    elif texture == 'mono':
        t -= 5
    elif 'paired' in texture:
        t -= 10
    return max(t, 0)


def mdf(bet_pct: int, pot: int = 7) -> float:
    """Minimum Defense Frequency (fold less than 1-MDF = exploit)."""
    bet = pot * bet_pct / 100
    return pot / (pot + bet)   # fraction that must call to make bluff 0EV


# ── OOP range HS distribution estimate ───────────────────────────────────────
# Approximate fraction of OOP range with HS < threshold on a given board.
# Based on BbDefendVsBtn range with typical hand distributions.
# We use a piecewise linear approximation of the cumulative HS distribution.
# This is a simplification; actual distribution depends on board.
#
# Approximate OOP range HS CDF (fraction of range with HS ≤ x):
#   HS = 0     → 0% (no hands with HS=0 typically, unless all board-unrelated air)
#   HS = 5     → ~15% (pure air, backdoor draws only)
#   HS = 10    → ~25%
#   HS = 15    → ~35% (threshold for vs33% rainbow)
#   HS = 20    → ~45%
#   HS = 25    → ~52% (threshold for vs50% rainbow)
#   HS = 35    → ~62% (threshold for vs75% rainbow)
#   HS = 65    → ~85% (T1 begins)
#   HS = 100   → ~100%
# NOTE: This CDF is board-independent; board-specific version would require
# computing per-hand equity, which is complex. The verification focuses on
# directional accuracy and rank correlation.

_CDF_POINTS = [(0, 0.0), (5, 0.12), (10, 0.22), (15, 0.33), (20, 0.43),
               (25, 0.50), (30, 0.56), (35, 0.62), (45, 0.70), (65, 0.84),
               (80, 0.92), (100, 1.0)]

def estimated_fold_rate(threshold: int) -> float:
    """Estimate fraction of OOP range that folds (HS < threshold)."""
    if threshold <= 0:
        return 0.0
    for i in range(len(_CDF_POINTS) - 1):
        x0, y0 = _CDF_POINTS[i]
        x1, y1 = _CDF_POINTS[i + 1]
        if x0 <= threshold <= x1:
            frac = (threshold - x0) / (x1 - x0)
            return y0 + frac * (y1 - y0)
    return 1.0


# ── Load and validate ─────────────────────────────────────────────────────────

def load_boards() -> list[dict]:
    boards = []
    for f in sorted(glob.glob(str(DATA_DIR / '*.json'))):
        try:
            d = json.load(open(f))
            if 'bb_fold_vs33' in d and 'bb_fold_vs50' in d and 'bb_fold_vs75' in d:
                boards.append(d)
        except Exception:
            pass
    return boards


def run_fold_threshold_verification() -> None:
    boards = load_boards()
    print(f'Loaded {len(boards)} boards with fold data\n')

    # ── Fold rate by texture (direction check) ────────────────────────────────
    by_texture: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    rows: list[dict] = []

    tex_b = {'mono':70,'paired_high':83,'paired_low':71,'2tone_ak':56,'2tone':50,
             'rainbow_connected':67,'rainbow_ak':62,'rainbow_q':58,'rainbow':55}

    for b in boards:
        b_score, texture = board_score_ascii(b['solver_str'])
        for size in [33, 50, 75]:
            key = f'bb_fold_vs{size}'
            gto_fold = b.get(key)
            if gto_fold is None:
                continue
            thr = fold_threshold(size, texture)
            pred_fold_rate = estimated_fold_rate(thr) * 100  # %
            mdf_fold = (1 - mdf(size)) * 100  # equilibrium fold %

            by_texture[texture][f'fold{size}'].append(gto_fold)
            rows.append({
                'board': b['solver_str'], 'texture': texture, 'b_score': b_score,
                'size': size, 'threshold': thr,
                'gto_fold': gto_fold, 'pred_fold': pred_fold_rate, 'mdf_fold': mdf_fold,
                'error': gto_fold - pred_fold_rate,
            })

    # ── Section 1: Average fold rate by texture ───────────────────────────────
    print('=' * 80)
    print('SECTION 1: Average GTO Fold Rate by Texture × Bet Size')
    print('  Formula correction direction: mono=-5, 2tone=+5, paired=-10')
    print('=' * 80)
    print(f'{"texture":22s}  {"B":3s}  {"vs33%":7s}  {"vs50%":7s}  {"vs75%":7s}  '
          f'{"thr33":6s}  {"thr50":6s}  {"thr75":6s}  {"n":>4}')
    print('-' * 80)

    # MDF baseline
    mdf_folds = {33: (1-mdf(33))*100, 50: (1-mdf(50))*100, 75: (1-mdf(75))*100}
    print(f'{"[MDF baseline]":22s}  {"---":3s}  {mdf_folds[33]:6.1f}%  {mdf_folds[50]:6.1f}%  '
          f'{mdf_folds[75]:6.1f}%  {"---":6s}  {"---":6s}  {"---":6s}')
    print()

    for tex in sorted(tex_b.keys()):
        b_score = tex_b[tex]
        row = by_texture.get(tex, {})
        n = len(row.get('fold33', []))
        def avg(lst): return f'{sum(lst)/len(lst):.1f}%' if lst else '   -'
        thr33 = fold_threshold(33, tex)
        thr50 = fold_threshold(50, tex)
        thr75 = fold_threshold(75, tex)
        print(f'{tex:22s}  {b_score:3d}  {avg(row.get("fold33",[]))}  '
              f'{avg(row.get("fold50",[]))}  {avg(row.get("fold75",[]))}  '
              f'HS<{thr33:2d}  HS<{thr50:2d}  HS<{thr75:2d}  {n:4d}')

    # ── Section 2: Correction direction validation ────────────────────────────
    print()
    print('=' * 80)
    print('SECTION 2: Correction Direction Validation')
    print('  mono vs rainbow (same size): does mono have LOWER fold rate? (threshold-5)')
    print('  2tone vs rainbow (same size): does 2tone have HIGHER fold rate? (threshold+5)')
    print('  paired vs rainbow (same size): does paired have LOWER fold rate? (threshold-10)')
    print('=' * 80)

    for size in [33, 50, 75]:
        fold_key = f'fold{size}'
        r_rainbow = by_texture.get('rainbow', {}).get(fold_key, [])
        r_mono    = by_texture.get('mono', {}).get(fold_key, [])
        r_2tone   = by_texture.get('2tone', {}).get(fold_key, [])
        r_2ak     = by_texture.get('2tone_ak', {}).get(fold_key, [])
        r_paired_h = by_texture.get('paired_high', {}).get(fold_key, [])
        r_paired_l = by_texture.get('paired_low', {}).get(fold_key, [])

        def avg_r(lst): return sum(lst)/len(lst) if lst else None

        rainbow_avg = avg_r(r_rainbow)
        mono_avg = avg_r(r_mono)
        t2_avg = avg_r(r_2tone)
        t2ak_avg = avg_r(r_2ak)
        ph_avg = avg_r(r_paired_h)
        pl_avg = avg_r(r_paired_l)

        print(f'\nvs {size}% CBet:')
        if rainbow_avg is not None:
            print(f'  rainbow (baseline): {rainbow_avg:.1f}%  [threshold={fold_threshold(size,"rainbow")}]')
            if mono_avg is not None:
                direction = 'OK ✓' if mono_avg < rainbow_avg else 'WRONG ✗'
                print(f'  mono               : {mono_avg:.1f}%  [threshold={fold_threshold(size,"mono")}]  '
                      f'diff={mono_avg-rainbow_avg:+.1f}%  formula_says_lower  → {direction}')
            if t2_avg is not None:
                direction = 'OK ✓' if t2_avg > rainbow_avg else 'WRONG ✗'
                print(f'  2tone              : {t2_avg:.1f}%  [threshold={fold_threshold(size,"2tone")}]  '
                      f'diff={t2_avg-rainbow_avg:+.1f}%  formula_says_higher → {direction}')
            if t2ak_avg is not None:
                direction = 'OK ✓' if t2ak_avg > rainbow_avg else 'WRONG ✗'
                print(f'  2tone_ak           : {t2ak_avg:.1f}%  [threshold={fold_threshold(size,"2tone_ak")}]  '
                      f'diff={t2ak_avg-rainbow_avg:+.1f}%  formula_says_higher → {direction}')
            if ph_avg is not None:
                direction = 'OK ✓' if ph_avg < rainbow_avg else 'WRONG ✗'
                print(f'  paired_high        : {ph_avg:.1f}%  [threshold={fold_threshold(size,"paired_high")}]  '
                      f'diff={ph_avg-rainbow_avg:+.1f}%  formula_says_lower  → {direction}')
            if pl_avg is not None:
                direction = 'OK ✓' if pl_avg < rainbow_avg else 'WRONG ✗'
                print(f'  paired_low         : {pl_avg:.1f}%  [threshold={fold_threshold(size,"paired_low")}]  '
                      f'diff={pl_avg-rainbow_avg:+.1f}%  formula_says_lower  → {direction}')

    # ── Section 3: Calibration check (predicted vs actual fold rates) ─────────
    print()
    print('=' * 80)
    print('SECTION 3: Calibration — Predicted vs Actual Fold Rate')
    print('  predicted_fold_rate = estimated fraction of OOP range with HS < threshold')
    print('=' * 80)

    for size in [33, 50, 75]:
        size_rows = [r for r in rows if r['size'] == size]
        if not size_rows:
            continue
        errors = [r['error'] for r in size_rows]
        abs_errors = [abs(e) for e in errors]
        pred_folds = [r['pred_fold'] for r in size_rows]
        gto_folds  = [r['gto_fold'] for r in size_rows]

        # Pearson correlation
        n = len(errors)
        mean_pred = sum(pred_folds) / n
        mean_gto  = sum(gto_folds)  / n
        cov = sum((p - mean_pred) * (g - mean_gto) for p, g in zip(pred_folds, gto_folds)) / n
        std_pred = (sum((p - mean_pred)**2 for p in pred_folds) / n) ** 0.5
        std_gto  = (sum((g - mean_gto)**2 for g in gto_folds)  / n) ** 0.5
        corr = cov / (std_pred * std_gto) if std_pred * std_gto > 0 else 0

        print(f'\nvs {size}% CBet (n={n}):')
        print(f'  Mean GTO fold rate : {mean_gto:.1f}%   MDF-fold: {(1-mdf(size))*100:.1f}%')
        print(f'  Mean pred fold rate: {mean_pred:.1f}%')
        print(f'  Mean abs error     : {sum(abs_errors)/n:.1f} pp')
        print(f'  Pearson r          : {corr:.3f}')

        # Over/under-fold by texture
        print(f'  Over/under-fold by texture:')
        tex_err: dict[str, list[float]] = defaultdict(list)
        for r in size_rows:
            tex_err[r['texture']].append(r['error'])
        for tex in sorted(tex_b.keys()):
            errs = tex_err.get(tex, [])
            if errs:
                avg_err = sum(errs)/len(errs)
                direction = 'over-folds' if avg_err > 5 else ('under-folds' if avg_err < -5 else 'calibrated')
                print(f'    {tex:22s}: pred-GTO = {avg_err:+.1f} pp  ({direction})')

    # ── Section 4: Rank correlation ───────────────────────────────────────────
    print()
    print('=' * 80)
    print('SECTION 4: Threshold Rank Correlation with GTO Fold Rate')
    print('  Spearman rank correlation: higher threshold → more folds')
    print('=' * 80)
    for size in [33, 50, 75]:
        size_rows = [r for r in rows if r['size'] == size]
        if not size_rows:
            continue
        # Sort by threshold; check if GTO fold rate also increases
        grouped: dict[int, list[float]] = defaultdict(list)
        for r in size_rows:
            grouped[r['threshold']].append(r['gto_fold'])
        thresholds = sorted(grouped.keys())
        avg_folds = [sum(grouped[t])/len(grouped[t]) for t in thresholds]
        print(f'\nvs {size}% (grouped by threshold):')
        for t, avg_f in zip(thresholds, avg_folds):
            print(f'  threshold={t:2d}: avg_GTO_fold={avg_f:.1f}%')


if __name__ == '__main__':
    run_fold_threshold_verification()
