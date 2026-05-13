#!/usr/bin/env python3
"""
analyze_river_sizes.py — [GTO-V5] リバー bet サイズのテクスチャ別検証
既存 river_results.json (162ボード) から ip_bet_50/75/100 の支配的サイズを集計。
"""
from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).parent / 'results' / 'river_results.json'

TEXTURE_ORDER = [
    'mono', 'paired_high', 'paired_low', '2tone_ak', '2tone',
    'rainbow_connected', 'rainbow_ak', 'rainbow_q',
    'rainbow', 'rainbow_lowconn', '2tone_conn',
]

def main() -> None:
    data = json.loads(RESULTS.read_text())

    # texture 別に集計
    by_tex: dict[str, list] = defaultdict(list)
    for r in data:
        if 'error' in r or r.get('ip_bet_pct') is None:
            continue
        tx = r.get('texture', 'unknown')
        by_tex[tx].append(r)

    print('=== リバー IP ファーストベット サイズ分布 ===\n')
    print(f'{"Texture":20s} {"n":4s} {"50% share":12s} {"75% share":12s} {"100% share":12s} {"推奨":10s} {"書籍":10s}')
    print('-' * 80)

    BOOK_SIZE = {
        'mono':              '50%',
        'paired_high':       '50%',
        'paired_low':        '50%',
        '2tone_ak':          '50%',
        '2tone':             '50%',
        'rainbow_connected': '50%',
        'rainbow_ak':        '50%',
        'rainbow_q':         '50%',
        'rainbow':           '50%',
        'rainbow_lowconn':   '50%',
        '2tone_conn':        '50%',
    }

    results_summary = []
    for tx in TEXTURE_ORDER:
        rows = by_tex.get(tx, [])
        if not rows:
            continue
        n = len(rows)

        # ip_bet_50/75/100 は「そのサイズを使った割合(%)」として格納
        s50  = sum(r.get('ip_bet_50',  0) for r in rows) / n
        s75  = sum(r.get('ip_bet_75',  0) for r in rows) / n
        s100 = sum(r.get('ip_bet_100', 0) for r in rows) / n

        best = max([('50%', s50), ('75%', s75), ('100%', s100)], key=lambda x: x[1])
        recommended = best[0]
        book = BOOK_SIZE.get(tx, '?')
        match = '✅' if recommended == book else '⚠️ '

        print(f'{tx:20s} {n:4d} {s50:12.1f} {s75:12.1f} {s100:12.1f} {recommended:10s} {book} {match}')
        results_summary.append({
            'texture': tx, 'n': n,
            'share_50': round(s50, 1), 'share_75': round(s75, 1), 'share_100': round(s100, 1),
            'recommended': recommended, 'book_current': book, 'match': recommended == book,
        })

    # 不一致サマリー
    mismatches = [r for r in results_summary if not r['match']]
    print(f'\n{"="*80}')
    print(f'検証: {len(results_summary)} テクスチャ / 不一致: {len(mismatches)}')
    if mismatches:
        print('\n⚠️  書籍修正が必要なテクスチャ:')
        for r in mismatches:
            print(f'  {r["texture"]:20s}: 書籍={r["book_current"]} → GTO推奨={r["recommended"]} '
                  f'(50%={r["share_50"]:.1f}% / 75%={r["share_75"]:.1f}% / 100%={r["share_100"]:.1f}%)')
    else:
        print('✅ 全テクスチャで書籍サイズと一致')

    out = Path(__file__).parent / 'results' / 'river_size_analysis.json'
    out.write_text(json.dumps(results_summary, ensure_ascii=False, indent=2))
    print(f'\n保存: {out}')


if __name__ == '__main__':
    main()
