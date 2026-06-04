#!/usr/bin/env python3
"""
order_probe2.py — 仮説確定のための追加実験

BB vs UTG (タイトな defense) で 100% fold する index を取得。
これは確実に弱ハンド (72o, 32o 等) のはず。仮説と照合。

さらに UTG vs BB 4-bet (3-bet 受けた UTG の 4-bet レンジ ~4%) は AA/KK/QQ/AKs のみ。
"""
import os, sys, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")

from gto_api import api_get, update_session

update_session()

# Step 1: BB vs UTG open (タイト defense)
# UTG open R2 → HJ/CO/BTN/SB fold → BB's turn
print("=== BB vs UTG open ===")
sols = api_get(board="", flop_actions="", pf="R2-F-F-F-F", depth=100)
if not sols:
    print("BB vs UTG failed", file=sys.stderr)
    sys.exit(1)

acts = sols['action_solutions']
fold_strat = next(a['strategy'] for a in acts if a['action']['code'] == 'F')
sure_fold = [i for i, f in enumerate(fold_strat) if f >= 0.99]
print(f"BB vs UTG: 100% fold index 数 = {len(sure_fold)}")
print(f"100% fold index: {sorted(sure_fold)}")

# 3-bet 系
bet_strat = [0.0] * 169
for a in acts:
    code = a['action']['code']
    if code.startswith('R') and code != 'R0':
        for i, s in enumerate(a['strategy']):
            bet_strat[i] += s

sure_3bet = [i for i, f in enumerate(bet_strat) if f >= 0.99]
print()
print(f"BB vs UTG: 100% 3-bet index 数 = {len(sure_3bet)}")
print(f"100% 3-bet index: {sorted(sure_3bet)}")

# Step 2: 全 169 hand を 4 仮説に展開して "100% fold" の整合性を見る
LOW = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
HIGH = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']

def hands_alpha_low_first() -> list[str]:
    """22, 32o, 32s, 42o, ..., 2A, 33, 43o, ..., AA"""
    out = []
    for i, lo in enumerate(LOW):
        out.append(f"{lo}{lo}")
        for hi in LOW[i+1:]:
            out.append(f"{hi}{lo}o")
            out.append(f"{hi}{lo}s")
    return out

def hands_alpha_low_first_pair_at_top() -> list[str]:
    """全ペアを先頭にまとめてから non-pair: 22,33,...,AA,32o,32s,...,A2o,A2s,...,AKo,AKs"""
    out = [f"{r}{r}" for r in LOW]  # 13 pairs
    for i, lo in enumerate(LOW):
        for hi in LOW[i+1:]:
            out.append(f"{hi}{lo}o")
            out.append(f"{hi}{lo}s")
    return out

def hands_v3_correct_offsuit_low_high() -> list[str]:
    """v3 だが offsuit/suited の対だけ調整 — 構造はvariety:
    まず i (low) を固定し、その上にある各 high で (high+low+o, high+low+s) を交互に、
    だが pair も間に挟む別バリアントを試す。
    """
    # 実は最も自然な「アルファベット順」は単純な文字列sort:
    # ['22','23o','23s','24o',...,'AKs','AKo','AQs',...,'AA']
    # ただし JTo vs JTs vs TJo の表記が問題。実用的には high rank first で書く。
    out = []
    # 全 169 hand を canonical な high-first 表記で生成、文字列 sort
    all_hands = []
    for i, hi in enumerate(HIGH):
        all_hands.append(f"{hi}{hi}")
        for lo in HIGH[i+1:]:
            all_hands.append(f"{hi}{lo}o")
            all_hands.append(f"{hi}{lo}s")
    return sorted(all_hands)


HANDS_V3 = hands_alpha_low_first()           # 仮説 3 (orderprobe.py と同じ)
HANDS_V6 = hands_alpha_low_first_pair_at_top()  # 仮説 6: pairs まとめ
HANDS_V7 = hands_v3_correct_offsuit_low_high()  # 仮説 7: アルファベットソート

print(f"\n--- 仮説 3 (low first, pair に混ぜる) ---")
print(f"  index 168 = {HANDS_V3[168]}")  # expected AA
print(f"\n--- 仮説 6 (pairs まとめ) ---")
print(f"  index 168 = {HANDS_V6[168]}")
print(f"  index 12 = {HANDS_V6[12]}")  # AA in 仮説 6
print(f"\n--- 仮説 7 (全 high-first 表記の単純 sort) ---")
print(f"  index 168 = {HANDS_V7[168]}")
print(f"  AA index in v7: {HANDS_V7.index('AA') if 'AA' in HANDS_V7 else 'N/A'}")
print()

print("=== BB vs UTG 100% fold の仮説テスト ===")
for h_idx, hypo in [("v3", HANDS_V3), ("v6", HANDS_V6), ("v7", HANDS_V7)]:
    folds = [hypo[i] for i in sure_fold if i < len(hypo)]
    weak = sum(1 for h in folds if h[0] in ['2','3','4'] or (len(h)==3 and h[2]=='o' and int(h[1] if h[1].isdigit() else 9) <= 7))
    print(f"  {h_idx}: 弱ハンド (2-4 始まりや 7o 以下) = {weak}/{len(folds)}")

print()
print("=== BB vs UTG 100% 3-bet ハンド ===")
for h_idx, hypo in [("v3", HANDS_V3), ("v6", HANDS_V6), ("v7", HANDS_V7)]:
    threes = sorted([hypo[i] for i in sure_3bet if i < len(hypo)])
    print(f"  {h_idx}: {threes[:15]}")

# Step 3: 結果 JSON 保存
out = Path(__file__).parent / "findings" / "order_probe2_bb_vs_utg.json"
with open(out, "w") as f:
    json.dump(sols, f, ensure_ascii=False, indent=2)
print(f"\nSaved → {out}")
