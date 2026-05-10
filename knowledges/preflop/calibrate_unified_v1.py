#!/usr/bin/env python3
"""統合 Score を RFI / 3-bet / SB-vs-RFI / BB defense でキャリブレーション."""
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
    """プリフロップスコア."""
    H, L, suited, pair = parse(h)
    s = H + L
    if pair: s += 10
    if suited: s += 3
    if not pair:
        gap = H - L
        if gap == 1: s += 1
        elif gap in (2, 3): s += 0.5
    if H == 14 and L == 13: s += 4
    elif H == 14: s += 3
    elif H == 13 or L == 13: s += 2
    if not pair:
        gap = H - L
        if gap >= 4 and H != 14: s -= 1
        if H < 9: s -= 1
    return s

hands = all_hands()

def calibrate_binary(chart, play_keys=('raise',), fold_keys=('fold',)):
    """Best single threshold T where Score ≥ T → play, else fold."""
    play_set = set()
    for k in play_keys:
        play_set.update(chart['actions'].get(k, []))
    truths = ['play' if h in play_set else 'fold' for h in hands]
    best = (0, 0)
    for T in [x * 0.5 for x in range(0, 90)]:
        preds = ['play' if score(h) >= T else 'fold' for h in hands]
        acc = sum(p == t for p, t in zip(preds, truths)) / len(hands)
        if acc > best[1]: best = (T, acc)
    return best


def calibrate_3way(chart, raise_keys=('raise',), call_keys=('limp', 'call')):
    """Best (T_3bet, T_call) where Score ≥ T_3bet → 3bet, T_call ≤ ... → call, else fold."""
    raise_set = set()
    call_set = set()
    for k in raise_keys: raise_set.update(chart['actions'].get(k, []))
    for k in call_keys: call_set.update(chart['actions'].get(k, []))
    def truth(h):
        if h in raise_set: return '3bet'
        if h in call_set: return 'call'
        return 'fold'
    truths = [truth(h) for h in hands]
    best = (0, 0, 0)
    for T3 in [x * 0.5 for x in range(0, 90)]:
        for Tc in [x * 0.5 for x in range(0, 90)]:
            if Tc > T3: continue
            preds = []
            for h in hands:
                s = score(h)
                if s >= T3: preds.append('3bet')
                elif s >= Tc: preds.append('call')
                else: preds.append('fold')
            acc = sum(p == t for p, t in zip(preds, truths)) / len(hands)
            if acc > best[2]: best = (T3, Tc, acc)
    return best


# ===== 1. RFI (open raise) =====
print('=== RFI (オープンレイズ) — 単一閾値 T_open ===')
rfi_results = {}
for pos in ['LJ_RFI', 'HJ_RFI', 'CO_RFI', 'BTN_RFI']:
    T, acc = calibrate_binary(GTO[pos])
    rfi_results[pos] = (T, acc)
    print(f'  {pos:<10} T_open={T:>5.1f}  acc={acc:.3f}')

# SB は raise + limp を「play」として扱う
T, acc = calibrate_binary(GTO['SB_RFI'], play_keys=('raise', 'limp'))
print(f'  SB_RFI     T_open={T:>5.1f}  acc={acc:.3f} (raise+limp 合算)')

# ===== 2. 3-bet (vs RFI) =====
print('\n=== 3-bet (vs RFI) — 二段閾値 ===')
for pos in ['HJ_vs_LJ', 'CO_vs_LJ', 'CO_vs_HJ', 'BTN_vs_LJ', 'BTN_vs_HJ', 'BTN_vs_CO',
            'SB_vs_LJ', 'SB_vs_HJ', 'SB_vs_CO', 'SB_vs_BTN']:
    T3, Tc, acc = calibrate_3way(GTO[pos])
    print(f'  {pos:<14} T_3bet={T3:>5.1f}  T_call={Tc:>5.1f}  acc={acc:.3f}')

# ===== 3. BB defense =====
print('\n=== BB defense (vs RFI) — 二段閾値 (raise=3bet, limp=call) ===')
for pos in ['BB_vs_LJ', 'BB_vs_HJ', 'BB_vs_CO', 'BB_vs_BTN']:
    T3, Tc, acc = calibrate_3way(GTO[pos])
    print(f'  {pos:<14} T_3bet={T3:>5.1f}  T_call={Tc:>5.1f}  acc={acc:.3f}')

# ===== 4. BvB =====
print('\n=== BvB ===')
T, acc = calibrate_binary(GTO['BvB_SB_strategy'], play_keys=('raise', 'limp', 'mixed_limp'))
print(f'  BvB_SB strategy: T_play={T:>5.1f}  acc={acc:.3f}')

# squeeze 用 charts はないが、3-bet と同じロジックが流用可能
