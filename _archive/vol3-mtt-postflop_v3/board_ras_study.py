"""
ボード固有のRAS変動調査スクリプト
- draw_study JSONL から RAS（no_draw aggregate CBet%）を抽出
- ボード特徴量との相関を分析
- シナリオ別・ボードタイプ別の RAS 分布を可視化
"""
import json, glob, re
from collections import defaultdict

# === ボード特徴量抽出 ===
RANK_ORDER = "23456789TJQKA"
RANK_VAL = {r: i for i, r in enumerate(RANK_ORDER)}

def parse_board(board_str):
    """'Kd9s8c' → cards のリスト"""
    cards = []
    for i in range(0, len(board_str), 2):
        rank = board_str[i]
        suit = board_str[i+1]
        cards.append((rank, suit))
    return cards

def board_features(board_str):
    cards = parse_board(board_str)
    ranks = [c[0] for c in cards]
    suits = [c[1] for c in cards]
    vals  = sorted([RANK_VAL[r] for r in ranks], reverse=True)

    # 高カード
    high  = RANK_ORDER[vals[0]]
    mid   = RANK_ORDER[vals[1]]
    low   = RANK_ORDER[vals[2]]

    # スーツ
    suit_counts = {}
    for s in suits:
        suit_counts[s] = suit_counts.get(s, 0) + 1
    max_suit = max(suit_counts.values())
    monotone   = max_suit == 3
    two_tone   = max_suit == 2
    rainbow    = max_suit == 1

    # ペア判定
    rank_counts = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    paired = max(rank_counts.values()) >= 2
    trips_board = max(rank_counts.values()) == 3

    # コネクト度（最大スパン）
    gap = vals[0] - vals[2]  # 最大-最小
    connected = gap <= 4     # 5ランク幅以内

    # ストレートドロー可能性（3枚の最大スパン）
    oesd_possible = gap <= 3 and not paired  # 4連続以内
    gs_possible   = gap <= 4 and not paired

    # ハイカード分類
    if high == 'A': high_cat = 'A-high'
    elif high == 'K': high_cat = 'K-high'
    elif high == 'Q': high_cat = 'Q-high'
    elif high in ('J','T'): high_cat = 'JT-high'
    else: high_cat = 'low'

    # テクスチャー分類（簡易）
    if paired: texture = 'paired'
    elif monotone: texture = 'monotone'
    elif connected and two_tone: texture = 'wet-connected'
    elif connected and rainbow: texture = 'dry-connected'
    elif two_tone: texture = 'semi-wet'
    else: texture = 'dry'

    return {
        'high': high, 'mid': mid, 'low': low,
        'high_cat': high_cat, 'texture': texture,
        'monotone': monotone, 'two_tone': two_tone, 'rainbow': rainbow,
        'paired': paired, 'trips_board': trips_board,
        'connected': connected, 'oesd_possible': oesd_possible,
        'gap': gap, 'high_val': vals[0], 'mid_val': vals[1],
    }

# === データ読み込み ===
def sc_type(sc):
    if "LIMP" in sc: return "LIMP"
    if "3BP"  in sc: return "3BP"
    if "_SB"  in sc: return "SB"
    return "BTN"

ras_data = []  # (scenario, board, ras, features)
for path in sorted(glob.glob("mtt-postflop/findings/draw_study_*.jsonl")):
    with open(path) as f:
        for line in f:
            d = json.loads(line)
            sc   = sc_type(d.get("scenario",""))
            board = d.get("board","")
            if not board or len(board) < 6: continue
            draw_agg = d.get("draw_agg", {})
            nd = draw_agg.get("no_draw", {})
            ras = nd.get("bet_pct", None)
            if ras is None: continue
            ras /= 100.0
            feat = board_features(board)
            ras_data.append({"sc": sc, "board": board, "ras": ras, **feat})

print(f"総データ点数: {len(ras_data)}")
print(f"シナリオ内訳: { {s: sum(1 for r in ras_data if r['sc']==s) for s in ['BTN','SB','LIMP','3BP']} }")

# === 1. シナリオ × テクスチャー別 RAS 分布 ===
print("\n=== シナリオ × ボードテクスチャー別 平均RAS ===")
print(f"{'テクスチャー':16s}", end="")
for sc in ["BTN","SB","LIMP","3BP"]:
    print(f"  {sc:>8s}", end="")
print()
textures = ['dry','semi-wet','dry-connected','wet-connected','monotone','paired']
for tex in textures:
    print(f"  {tex:14s}", end="")
    for sc in ["BTN","SB","LIMP","3BP"]:
        recs = [r for r in ras_data if r['sc']==sc and r['texture']==tex]
        if recs:
            avg = sum(r['ras'] for r in recs)/len(recs)
            print(f"  {avg*100:7.1f}%", end="")
        else:
            print(f"  {'':7s}", end="")
    print()

# === 2. シナリオ × ハイカード別 RAS 分布 ===
print("\n=== シナリオ × ハイカード別 平均RAS ===")
print(f"{'ハイカード':12s}", end="")
for sc in ["BTN","SB","LIMP","3BP"]:
    print(f"  {sc:>8s}", end="")
print()
for hcat in ['A-high','K-high','Q-high','JT-high','low']:
    print(f"  {hcat:12s}", end="")
    for sc in ["BTN","SB","LIMP","3BP"]:
        recs = [r for r in ras_data if r['sc']==sc and r['high_cat']==hcat]
        if recs:
            avg = sum(r['ras'] for r in recs)/len(recs)
            print(f"  {avg*100:7.1f}%", end="")
        else:
            print(f"  {'':7s}", end="")
    print()

# === 3. ハイカード × テクスチャー の交差（SBシナリオ詳細）===
print("\n=== SBシナリオ: ハイカード × テクスチャー 平均RAS ===")
print(f"{'':14s}", end="")
for tex in textures:
    print(f"  {tex[:10]:>10s}", end="")
print()
for hcat in ['A-high','K-high','Q-high','JT-high','low']:
    print(f"  {hcat:12s}", end="")
    for tex in textures:
        recs = [r for r in ras_data if r['sc']=='SB' and r['high_cat']==hcat and r['texture']==tex]
        if recs:
            avg = sum(r['ras'] for r in recs)/len(recs)
            print(f"  {avg*100:9.1f}%", end="")
        else:
            print(f"  {'—':>9s}", end="")
    print()

# === 4. RAS 予測ルールの精度テスト ===
print("\n=== 簡易RAS分類ルール（暗算用）の精度 ===")

def ras_rule(r):
    """ボード特徴からRASクラスを推定: HIGH(>65%) / MID(40-65%) / LOW(<40%)"""
    hcat = r['high_cat']; tex = r['texture']; sc = r['sc']

    # BTN/CO: 常に高RAS
    if sc == 'BTN':
        if tex in ('dry','semi-wet') and hcat in ('A-high','K-high'): return 'HIGH'
        if tex == 'paired': return 'HIGH'
        if tex == 'monotone': return 'MID'
        if tex in ('wet-connected','dry-connected'): return 'MID'
        return 'MID'

    # SB SRP
    if sc == 'SB':
        if hcat == 'A-high' and tex in ('dry','semi-wet'): return 'HIGH'
        if hcat == 'K-high' and tex == 'dry': return 'HIGH'
        if tex == 'monotone': return 'LOW'
        if tex == 'wet-connected': return 'LOW'
        if hcat in ('JT-high','low') and tex in ('dry-connected','wet-connected'): return 'LOW'
        return 'MID'

    # LIMP
    if sc == 'LIMP':
        if hcat == 'A-high' and tex in ('dry','semi-wet'): return 'MID'
        if tex in ('wet-connected','dry-connected','monotone'): return 'LOW'
        return 'LOW'

    return 'MID'  # 3BP

def actual_ras_class(ras):
    if ras >= 0.65: return 'HIGH'
    if ras >= 0.40: return 'MID'
    return 'LOW'

correct = sum(1 for r in ras_data if ras_rule(r) == actual_ras_class(r['ras']))
total   = len(ras_data)
print(f"  全体正答率: {correct}/{total} = {correct/total*100:.1f}%")
for sc in ['BTN','SB','LIMP','3BP']:
    recs = [r for r in ras_data if r['sc']==sc]
    c = sum(1 for r in recs if ras_rule(r)==actual_ras_class(r['ras']))
    print(f"  {sc:5s}: {c}/{len(recs)} = {c/len(recs)*100:.1f}%")

# 誤分類ケースを表示
print("\n  誤分類ケース（SB）:")
for r in ras_data:
    if r['sc']!='SB': continue
    pred = ras_rule(r); actual = actual_ras_class(r['ras'])
    if pred != actual:
        print(f"    {r['board']:8s}  {r['high_cat']:8s} {r['texture']:14s}  RAS={r['ras']*100:.0f}%  予測={pred}→実={actual}")

# === 5. 各シナリオのRAS分布ヒストグラム ===
print("\n=== RAS分布ヒストグラム ===")
for sc in ['BTN','SB','LIMP']:
    recs = [r for r in ras_data if r['sc']==sc]
    if not recs: continue
    vals = [r['ras'] for r in recs]
    avg = sum(vals)/len(vals)
    buckets = [0]*5  # 0-20,20-40,40-60,60-80,80-100
    for v in vals:
        buckets[min(4, int(v*5))] += 1
    labels = ["0-20%","20-40%","40-60%","60-80%","80+%"]
    print(f"  {sc} (avg={avg*100:.0f}%, n={len(recs)}):")
    for l, c in zip(labels, buckets):
        bar = "█"*c
        print(f"    {l}: {bar} ({c})")
