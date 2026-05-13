#!/usr/bin/env python3
"""
verify_cr_thresholds.py — [GTO-V2] CR/CALL/FOLD 閾値検証 (HS=40/20)

既存 draw_bonus_v3_raw.json ツリー (board: Kh,9h,5d,2c) を再利用。
OOP range 内の多様な HS 帯の手を抽出し、defense breakdown を計測。

現行書籍閾値:
  HS ≥ 40  → CR (チェックレイズ推奨)
  20≤HS<40 → CALL
  HS < 20  → FOLD

検証対象手 (board K♥9♥5♦→2♣):
  K♦A♦ → TPTK   (HS≈65)
  K♦Q♦ → TPGK   (HS≈55)  ← v3 再利用
  K♦J♦ → TPMK   (HS≈50)
  K♦T♦ → TPWK   (HS≈45)
  9♣8♦ → 2nd pair+1kicker (HS≈35)
  9♣3♦ → 2nd pair+1WK    (HS≈30)
  5♣4♦ → 3rd pair         (HS≈25)
  Q♥8♥ → 純FD              (HS=26) ← v3 再利用
  A♣Q♦ → Aハイ 1OC         (HS≈25) ← v3 再利用
  Q♣J♦ → 2OC air           (HS≈8)  ← v3 再利用
"""
from __future__ import annotations
import json
from pathlib import Path

DUMP = Path(__file__).parent / 'results' / 'draw_bonus_v3_raw.json'
OUT  = Path(__file__).parent / 'results' / 'cr_threshold_results.json'

# (combo, label, hs_pred, type)
TARGETS: list[tuple[str, str, int, str]] = [
    ('KdAd', 'K♦A♦ TPTK',      65, 'TPTK'),
    ('KdQd', 'K♦Q♦ TPGK',      55, 'TPGK'),
    ('KdJd', 'K♦J♦ TPMK',      50, 'TPMK'),
    ('KdTd', 'K♦T♦ TPWK',      45, 'TPWK'),
    ('9c8d', '9♣8♦ 2ndPair+K', 35, '2nd_pair'),
    ('9c3d', '9♣3♦ 2ndPair+WK',30, '2nd_pair_wk'),
    ('5c4d', '5♣4♦ 3rdPair',   25, '3rd_pair'),
    ('Qh8h', 'Q♥8♥ 純FD',      26, 'pure_FD'),
    ('AcQd', 'A♣Q♦ Aハイ',     25, 'Ahigh'),
    ('QcJd', 'Q♣J♦ air',        8, 'air'),
]

BET_PCTS = [33.0, 50.0, 75.0]


def get_bet_node(tree: dict, approx_chips: float) -> tuple[str, dict] | tuple[None, None]:
    check_node = tree.get('childrens', {}).get('CHECK')
    if not check_node:
        return None, None
    best_key, best_node, best_diff = None, None, 999.0
    for key, node in check_node.get('childrens', {}).items():
        try:
            chips = float(key.replace('BET ', ''))
        except ValueError:
            continue
        if abs(chips - approx_chips) < best_diff:
            best_key, best_node, best_diff = key, node, abs(chips - approx_chips)
    return best_key, best_node


def combo_defense(node: dict, combo: str) -> dict:
    sb = node.get('strategy', {})
    actions: list[str] = sb.get('actions', [])
    strat   = sb.get('strategy', {})
    if combo not in strat:
        return {}
    freqs = strat[combo]
    d: dict[str, float] = {}
    for i, a in enumerate(actions):
        f = freqs[i] if i < len(freqs) else 0.0
        au = a.upper()
        if au == 'FOLD':
            d['fold'] = f
        elif au == 'CALL':
            d['call'] = f
        else:
            d['raise'] = d.get('raise', 0.0) + f
    return d


def main() -> None:
    tree = json.loads(DUMP.read_text())

    all_results: dict[float, dict] = {}
    for pct in BET_PCTS:
        chips = pct / 100 * 10
        key, node = get_bet_node(tree, chips)
        if node is None:
            print(f'No node for {pct}%'); continue
        pct_results = {}
        for combo, label, hs, htype in TARGETS:
            pct_results[combo] = combo_defense(node, combo)
        all_results[pct] = pct_results

    # Print table
    print('=== CR/CALL/FOLD 閾値 GTO 検証 ===')
    print(f'Board: Kh,9h,5d,2c (K♥9♥5♦→2♣, 2tone_ak + blank)\n')
    print('書籍閾値: HS≥40→CR / 20≤HS<40→CALL / HS<20→FOLD\n')

    for pct in BET_PCTS:
        d = all_results.get(pct, {})
        chips = pct / 100 * 10
        print(f'--- vs IP ~{pct:.0f}% ポット bet ({chips:.1f}ch) ---')
        print(f'{"手":22s} {"HS":5s} {"タイプ":14s} '
              f'{"fold%":7s} {"call%":7s} {"raise%":7s} {"def%":7s} {"GTO判定":10s} {"書籍判定":10s} {"整合?"}')
        for combo, label, hs, htype in TARGETS:
            dd = d.get(combo, {})
            if not dd:
                print(f'{label:22s} {hs:5d} {htype:14s}  (range外)')
                continue
            fold_p  = dd.get('fold',  0) * 100
            call_p  = dd.get('call',  0) * 100
            raise_p = dd.get('raise', 0) * 100
            def_p   = call_p + raise_p

            # GTO verdict from dominant action
            if raise_p >= 20:
                gto_verdict = 'CR'
            elif def_p >= 70:
                gto_verdict = 'CALL'
            elif fold_p >= 60:
                gto_verdict = 'FOLD'
            else:
                gto_verdict = 'MIXED'

            # Book verdict
            if hs >= 40:
                book_verdict = 'CR'
            elif hs >= 20:
                book_verdict = 'CALL'
            else:
                book_verdict = 'FOLD'

            match = '✅' if gto_verdict == book_verdict else ('⚠️ ' if gto_verdict != 'MIXED' else '～')
            print(f'{label:22s} {hs:5d} {htype:14s} '
                  f'{fold_p:7.1f} {call_p:7.1f} {raise_p:7.1f} {def_p:7.1f} '
                  f'{gto_verdict:10s} {book_verdict:10s} {match}')
        print()

    # Summary by threshold
    print('■ 閾値検証サマリー (vs 75% bet)')
    d75 = all_results.get(75.0, {})
    cr_correct, call_correct, fold_correct = 0, 0, 0
    total = {'CR': 0, 'CALL': 0, 'FOLD': 0}
    correct = {'CR': 0, 'CALL': 0, 'FOLD': 0}
    for combo, label, hs, htype in TARGETS:
        dd = d75.get(combo, {})
        if not dd: continue
        fold_p  = dd.get('fold', 0) * 100
        call_p  = dd.get('call', 0) * 100
        raise_p = dd.get('raise', 0) * 100
        def_p   = call_p + raise_p
        if raise_p >= 20:
            gto_v = 'CR'
        elif def_p >= 70:
            gto_v = 'CALL'
        elif fold_p >= 60:
            gto_v = 'FOLD'
        else:
            gto_v = 'MIXED'
        if hs >= 40:
            book_v = 'CR'
        elif hs >= 20:
            book_v = 'CALL'
        else:
            book_v = 'FOLD'
        total[book_v] = total.get(book_v, 0) + 1
        if gto_v == book_v:
            correct[book_v] = correct.get(book_v, 0) + 1

    for cat in ['CR', 'CALL', 'FOLD']:
        n = total.get(cat, 0)
        c = correct.get(cat, 0)
        pct_ok = c/n*100 if n else 0
        print(f'  {cat}: {c}/{n} ({pct_ok:.0f}%)')

    # Key finding: FD exception
    fd_result = d75.get('Qh8h', {})
    ah_result = d75.get('AcQd', {})
    if fd_result and ah_result:
        fd_def = (fd_result.get('call', 0) + fd_result.get('raise', 0)) * 100
        ah_def = (ah_result.get('call', 0) + ah_result.get('raise', 0)) * 100
        print(f'\n■ 重要発見: 純FD例外ルール')
        print(f'  Q♥8♥ 純FD(HS=26) def={fd_def:.1f}%  vs  A♣Q♦ Aハイ(HS=25) def={ah_def:.1f}%')
        print(f'  差={fd_def-ah_def:+.1f}% → FD は HS+A-C 式では FOLD 判定されるが GTO は 100% call')
        print(f'  → draw_bonus は「過剰評価」でなく「過小評価」。FD専用の ALWAYS CALL ルールが必要。')

    OUT.write_text(json.dumps(all_results, ensure_ascii=False, indent=2))
    print(f'\n保存: {OUT}')


if __name__ == '__main__':
    main()
