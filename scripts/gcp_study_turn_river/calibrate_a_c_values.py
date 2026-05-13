#!/usr/bin/env python3
"""
calibrate_a_c_values.py — [GTO-V3] A値・C値キャリブレーション
既存 turn_results.json (233ボード) の OOP fold 率から A値・C値を逆算する。

理論式:
  後手スコア = HS + A - C - M
  FOLD 基準:  後手スコア < 20  ⟺  HS < 20 - A + C + M
  FOLD 閾値 HS_fold = C - A + 20  (HU: M=0)

  実測 fold 率 → OOP range の HandScore 分布と突き合わせて A を推定。
"""
from __future__ import annotations
import json, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'poker-drill' / 'scripts' / 'generate' / 'core'))

RESULTS_TURN = Path(__file__).parent / 'results' / 'turn_results.json'

# OOP range (BB SRP call range) の代表的 HandScore 分布
# TexasSolver で使った OOP range を基に calc.py で事前計算
# board K♠7♦2♣ (dry) を代表ボードとして使用
# 各 bucket の大まかなHS分布（累積分布関数的に使う）
#実際は board ごとに異なるが texture 代表値として使用

# texture → A値の GTO実測推定に使う観測 fold 率
# fold 率 f から: HS_fold = (1 - f) * MAX_HS で近似
# より正確には: f = P(HS < HS_fold) で OOP range のHS分布を使う

# OOP range の HandScore 中央値（各 texture の代表ボードで概算）
# GCP 研究の aggregate fold 率から逆算する近似法:
#   fold% = (OOP hands with HS < HS_fold) / (total OOP hands)
#   OOP range では HS が uniform(0,100) に近い分布を仮定すると:
#   fold% ≈ HS_fold / 100
#   → HS_fold ≈ fold% × 100
#   → C - A + 20 ≈ fold% × 100
#   → A ≈ C + 20 - fold% × 100

TEXTURE_A_EXPECTED = {
    'dry':       ('dry_boards',   8, 12),   # (name, flop_A, expected_turn_A)
    'semi':      ('semi_boards',  6,  6),
    'suited':    ('suited',       4,  4),
    'connected': ('connected',    3,  0),
    'wet':       ('wet',          0,  0),
}

# texture → A値マッピング（書籍現行値）
BOOK_A = {
    'rainbow':           12,   # dry ≈
    'rainbow_ak':        12,
    'paired_high':        8,
    'paired_low':         8,
    'rainbow_q':          6,
    '2tone_ak':           6,
    '2tone':              4,
    'mono':               4,
    'rainbow_connected':  0,
    'rainbow_lowconn':    0,
    '2tone_conn':         0,
}

# C値（現行書籍値）
BOOK_C = {33: 12, 50: 17, 75: 22, 100: 25}


def main() -> None:
    data = json.loads(RESULTS_TURN.read_text())

    by_tex: dict[str, list] = defaultdict(list)
    for r in data:
        if 'error' in r:
            continue
        tx = r.get('texture', 'unknown')
        by_tex[tx].append(r)

    print('=== A値・C値 GTO キャリブレーション ===\n')
    print('【理論式】 fold 閾値 HS_fold = C - A + 20')
    print('【逆算式】 A ≈ C + 20 - fold% × 100  (OOP range HS 均一分布仮定)\n')

    print('--- C値 検証（vs bet size） ---')
    print(f'{"Bet%":8s} {"書籍C":8s} {"観測fold%":12s} {"逆算HS_fold":12s} {"逆算A(dry)":12s} {"整合?":8s}')
    print('-'*65)

    # dry texture 代表（rainbow, rainbow_ak）で C値を検証
    dry_textures = ['rainbow', 'rainbow_ak', 'paired_high']
    c_estimates = {}
    for bet_pct, c_book in BOOK_C.items():
        fold_key = f'oop_fold_vs{bet_pct}'
        folds = []
        for tx in dry_textures:
            for r in by_tex.get(tx, []):
                v = r.get(fold_key)
                if v is not None:
                    folds.append(v / 100)
        if not folds:
            continue
        avg_fold = sum(folds) / len(folds)
        # A(dry) = 12 と仮定して C を逆算
        # fold% ≈ HS_fold / 100 → HS_fold ≈ fold% * 100
        # C = HS_fold + A - 20 = fold%*100 + 12 - 20
        c_est = avg_fold * 100 + 12 - 20
        hs_fold_est = avg_fold * 100
        match = '✅' if abs(c_est - c_book) <= 3 else '⚠️ '
        print(f'{bet_pct:8d} {c_book:8d} {avg_fold*100:12.1f} {hs_fold_est:12.1f} {c_est:12.1f} {match} (書籍C={c_book}, 逆算C≈{c_est:.0f})')
        c_estimates[bet_pct] = c_est

    print('\n--- A値 検証（vs 33% ベット） ---')
    print(f'{"Texture":20s} {"n":4s} {"fold_vs33%":12s} {"HS_fold推定":12s} {"逆算A":10s} {"書籍A":10s} {"差":6s} {"整合?"}')
    print('-'*80)

    # C=12(33%ベット) を使って A を逆算
    c_33 = c_estimates.get(33, 12)
    a_results = []
    TEXTURE_ORDER = [
        'paired_high', 'rainbow_ak', 'rainbow', 'rainbow_q',
        'mono', '2tone_ak', 'paired_low', 'rainbow_connected',
        '2tone', 'rainbow_lowconn', '2tone_conn',
    ]
    for tx in TEXTURE_ORDER:
        rows = by_tex.get(tx, [])
        if not rows:
            continue
        folds = [r['oop_fold_vs33'] / 100 for r in rows if r.get('oop_fold_vs33') is not None]
        if not folds:
            continue
        avg_fold = sum(folds) / len(folds)
        hs_fold = avg_fold * 100
        # A = C + 20 - hs_fold
        a_est = c_33 + 20 - hs_fold
        a_book = BOOK_A.get(tx, '?')
        if isinstance(a_book, int):
            diff = a_est - a_book
            match = '✅' if abs(diff) <= 4 else '⚠️ '
        else:
            diff = 0; match = '?'
        print(f'{tx:20s} {len(rows):4d} {avg_fold*100:12.1f} {hs_fold:12.1f} {a_est:10.1f} {str(a_book):10s} {diff:+6.1f} {match}')
        a_results.append({'texture': tx, 'a_book': a_book, 'a_estimated': round(a_est, 1),
                           'fold_vs33': round(avg_fold*100, 1), 'match': abs(diff) <= 4 if isinstance(a_book, int) else None})

    # サマリー
    valid = [r for r in a_results if r['match'] is not None]
    ok = sum(1 for r in valid if r['match'])
    print(f'\n整合: {ok}/{len(valid)} テクスチャ')

    # 推奨修正値
    print('\n■ 推奨修正（差 > 4 のテクスチャ）:')
    for r in a_results:
        if r['match'] is False:
            print(f'  {r["texture"]:20s}: 書籍A={r["a_book"]} → GTO推奨≈{r["a_estimated"]}')

    out = Path(__file__).parent / 'results' / 'a_c_calibration.json'
    out.write_text(json.dumps({'c_estimates': c_estimates, 'a_results': a_results},
                              ensure_ascii=False, indent=2))
    print(f'\n保存: {out}')


if __name__ == '__main__':
    main()
