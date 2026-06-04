#!/usr/bin/env python3
"""
order_probe.py — strategy[169] のハンド順序を確定する

UTG RFI (最タイトなオープンレンジ ~17.5%) を取得し、raise するハンドの index を
取得。標準順序の仮説と照合して GTO Wizard の preflop hand order を確定する。

使い方:
  source .env && uv run --with requests python3 order_probe.py
"""
import os, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")

from gto_api import api_get, update_session

update_session()

# Step 1: UTG RFI (オープンレンジ)
print("=== Step 1: UTG RFI ===")
sols_rfi = api_get(board="", flop_actions="", pf="", depth=100)
if not sols_rfi:
    print("UTG RFI failed", file=sys.stderr)
    sys.exit(1)

# raise action の合算 strategy
acts = sols_rfi['action_solutions']
raise_strat = [0.0] * 169
for a in acts:
    code = a['action']['code']
    if code.startswith('R') and code != 'R0':
        for i, s in enumerate(a['strategy']):
            raise_strat[i] += s

# raise > 0.01 の index リスト
utg_open_indices = sorted([(i, freq) for i, freq in enumerate(raise_strat) if freq > 0.01], key=lambda x: -x[1])
print(f"UTG オープンする index 数: {len(utg_open_indices)}")
print()

# 100% open (確実な強ハンド)
sure_open = [i for i, f in utg_open_indices if f >= 0.99]
print(f"100% open index 数: {len(sure_open)}")
print(f"100% open index: {sorted(sure_open)}")
print()

# Step 2: BB vs SB 3.5BB open (最 tight 場面、AA だけ 3-bet)
print("=== Step 2: BB vs SB open (最タイトな 3-bet シナリオ) ===")
sols_bb_sb = api_get(board="", flop_actions="", pf="F-F-F-F-R3", depth=100)
if sols_bb_sb:
    acts = sols_bb_sb['action_solutions']
    print(f"action codes: {[a['action']['code'] for a in acts]}")
    # 3-bet strategy
    bet_strat = [0.0] * 169
    for a in acts:
        code = a['action']['code']
        if code.startswith('R') and code != 'R0':
            for i, s in enumerate(a['strategy']):
                bet_strat[i] += s
    top_3bet = sorted(enumerate(bet_strat), key=lambda x: -x[1])[:5]
    print(f"BB vs SB 3-bet TOP 5: {top_3bet}")

print()

# Step 3: 順序仮説のテスト
# 仮説: index = row*13 + col、rank 順序は A→2 (高い順)
# (0,0) = AA (index 0), (1,1) = KK (index 14), (12,12) = 22 (index 168)
RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

def index_to_hand_v1(idx: int) -> str:
    """仮説 1: 13x13 grid, A=row 0, 2=row 12, 上三角=suited, 下三角=offsuit"""
    row, col = divmod(idx, 13)
    if row == col:
        return f"{RANKS[row]}{RANKS[col]}"  # pair
    elif row < col:
        return f"{RANKS[row]}{RANKS[col]}s"  # suited (high rank first)
    else:
        return f"{RANKS[col]}{RANKS[row]}o"  # offsuit (high rank first)

def index_to_hand_v2(idx: int) -> str:
    """仮説 2: 上三角=offsuit, 下三角=suited (逆)"""
    row, col = divmod(idx, 13)
    if row == col:
        return f"{RANKS[row]}{RANKS[col]}"
    elif row < col:
        return f"{RANKS[row]}{RANKS[col]}o"
    else:
        return f"{RANKS[col]}{RANKS[row]}s"


def all_hands_alpha_low_first() -> list[str]:
    """仮説 3: アルファベット順 (low rank first)、例: 22, 23o, 23s, 24o, 24s, ..., 2A, 33, 34o, ..., AA"""
    # 2,3,4,...,A の順
    LOW = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    hands = []
    for i, lo in enumerate(LOW):
        # pair
        hands.append(f"{lo}{lo}")
        # higher than lo: offsuit, suited
        for hi in LOW[i+1:]:
            hands.append(f"{hi}{lo}o")
            hands.append(f"{hi}{lo}s")
    return hands

def all_hands_alpha_high_first() -> list[str]:
    """仮説 4: アルファベット順 (high rank first)、例: AA, A2o, A2s, A3o, ..., AKs, KK, K2o, ..."""
    HIGH = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
    hands = []
    for i, hi in enumerate(HIGH):
        # pair
        hands.append(f"{hi}{hi}")
        # lower than hi
        for lo in HIGH[i+1:]:
            hands.append(f"{hi}{lo}o")
            hands.append(f"{hi}{lo}s")
    return hands

HANDS_V3 = all_hands_alpha_low_first()
HANDS_V4 = all_hands_alpha_high_first()
print(f"\n仮説 3 (low first): len={len(HANDS_V3)}, first 5={HANDS_V3[:5]}, last 3={HANDS_V3[-3:]}")
print(f"仮説 4 (high first): len={len(HANDS_V4)}, first 5={HANDS_V4[:5]}, last 3={HANDS_V4[-3:]}")

print("\n=== UTG オープン 100% ハンド の 4 仮説テスト ===")
print(f"{'index':>5}  {'v1 grid 上三角=s':<10}  {'v2 grid 上三角=o':<10}  {'v3 alpha low':<10}  {'v4 alpha high':<10}")
for i in sorted(sure_open):
    h1 = index_to_hand_v1(i)
    h2 = index_to_hand_v2(i)
    h3 = HANDS_V3[i] if i < len(HANDS_V3) else "-"
    h4 = HANDS_V4[i] if i < len(HANDS_V4) else "-"
    print(f"{i:>5}  {h1:<14}  {h2:<14}  {h3:<14}  {h4:<14}")
