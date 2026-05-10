#!/usr/bin/env python3
"""Final: F design with rounded user-friendly thresholds, plus per-position table."""
import json
from pathlib import Path

GTO = json.loads(Path('/home/cuzic/poker-books/knowledges/preflop/gto-charts.json').read_text())
RANK = {r: v for v, r in enumerate('23456789TJQKA', 2)}

def all_hands():
    hs, ranks = [], list('AKQJT98765432')
    for i, r1 in enumerate(ranks):
        for j, r2 in enumerate(ranks):
            if i == j: hs.append(r1 + r2)
            elif i < j: hs.append(r1 + r2 + 's')
            else: hs.append(r2 + r1 + 'o')
    return hs

def parse(h):
    if len(h) == 2: r = RANK[h[0]]; return r, r, False, True
    H, L = RANK[h[0]], RANK[h[1]]
    return max(H, L), min(H, L), h.endswith('s'), False

def score(h):
    """プリフロップスコア (3-bet vs call vs fold 用)"""
    H, L, suited, pair = parse(h)
    s = H + L
    if pair: s += 10
    if suited: s += 3
    if not pair:
        gap = H - L
        if gap == 1: s += 1
        elif gap in (2, 3): s += 0.5
    # ブロッカー
    if H == 14 and L == 13: s += 4
    elif H == 14: s += 3
    elif H == 13 or L == 13: s += 2
    # ペナルティ
    if not pair:
        gap = H - L
        if gap >= 4 and H != 14: s -= 1
        if H < 9: s -= 1
    return s

def predict(h, T3, Tc):
    s = score(h)
    if s >= T3: return '3bet'
    if s >= Tc: return 'call'
    return 'fold'

def truth(h, raise_set, call_set):
    if h in raise_set: return '3bet'
    if h in call_set: return 'call'
    return 'fold'

# 閾値案 (整数寄りに丸めた人手調整版)
THRESHOLDS = {
    'BTN_vs_LJ': (32, 28),  # vs UTG
    'BTN_vs_HJ': (32, 27),
    'BTN_vs_CO': (24, 24),  # CALL レンジ薄い
    'CO_vs_LJ':  (28, 28),  # CALL なし → T_3bet=T_call
    'CO_vs_HJ':  (28, 28),
    'HJ_vs_LJ':  (28, 28),
    'SB_vs_LJ':  (30, 30),
    'SB_vs_HJ':  (30, 30),
    'SB_vs_CO':  (28, 28),
    'SB_vs_BTN': (24, 24),
}

hands = all_hands()
total_hands = total_correct = 0
for pos, (T3, Tc) in THRESHOLDS.items():
    chart = GTO[pos]
    raise_set = set(chart['actions'].get('raise', []))
    call_set = set(chart['actions'].get('limp', []) + chart['actions'].get('call', []))
    truths = [truth(h, raise_set, call_set) for h in hands]
    preds = [predict(h, T3, Tc) for h in hands]
    correct = sum(1 for p, t in zip(preds, truths) if p == t)
    total_hands += len(hands)
    total_correct += correct
    print(f'{pos:<14} T_3bet={T3} T_call={Tc} acc={correct/len(hands):.3f}')

print(f'\n総合精度: {total_correct/total_hands:.3f}')

# Show what each opener looks like for BTN
print('\n=== BTN vs UTG (LJ) — 全ハンドの判定例 (主要のみ) ===')
T3, Tc = THRESHOLDS['BTN_vs_LJ']
chart = GTO['BTN_vs_LJ']
raise_set = set(chart['actions'].get('raise', []))
call_set = set(chart['actions'].get('limp', []) + chart['actions'].get('call', []))
key_hands = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', '77', '66', '55', '22',
             'AKs', 'AKo', 'AQs', 'AQo', 'AJs', 'AJo', 'ATs', 'ATo', 'A9s', 'A5s', 'A2s',
             'KQs', 'KQo', 'KJs', 'KJo', 'KTs', 'K9s',
             'QJs', 'QJo', 'QTs', 'JTs', 'T9s', '98s', '87s', '76s', '65s', '54s']
for h in key_hands:
    s = score(h)
    p = predict(h, T3, Tc)
    t = truth(h, raise_set, call_set)
    mark = '✓' if p == t else '✗'
    print(f'  {mark} {h:>4}: Score={s:>5.1f} GTO={t:>5} 予測={p:>5}')
