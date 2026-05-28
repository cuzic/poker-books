#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = []
# ///
"""
CBS System Validation against GTO Wizard data.
Validates direction accuracy, confidence calibration, and FREQ_TABLE accuracy.
"""

import json
import glob
import math
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path(__file__).parent
FINDINGS_DIR = BASE_DIR / "findings"

# ─── CBS Tables (must match generator.py) ────────────────────────────────────
HP_TABLE = {
    'no_made_hand': 5,
    'ace_high':     5,
    'king_high':    5,
    'low_pair':     2,
    'third_pair':   3,
    'underpair':    5,
    'second_pair':  5,
    'top_pair':     7,
    'overpair':     7,
    'two_pair':     9,
    'straight':     9,
    'set':          5,
    'trips':        9,
    'fullhouse':    2,
    'quads':        3,
}

DP_TABLE = {
    'no_draw':        0,
    'onecard_bdfd':   0,
    'twocards_bdfd':  0,
    'gutshot':        1,
    'flush_draw':     2,
    'nut_flush_draw': 2,
    'oesd':           2,
    'combo_draw':     3,
}

THRESHOLDS = {'BTN': 5, 'SB': 7, 'LIMP': 7, '3BP': 5, 'CO': 5}

FREQ_TABLE = {
    ('HIGH', True):  79,
    ('HIGH', False): 42,
    ('MID',  True):  67,
    ('MID',  False): 39,
    ('LOW',  True):  58,
    ('LOW',  False): 37,
}

# ─── Board Classification ─────────────────────────────────────────────────────
def classify_board(board_id: str) -> int:
    b = board_id.split('_')[0]
    if len(b) >= 2 and b[0] == b[1]:
        return 7
    rank_vals = []
    for x in b[:3]:
        if x == 'A':   rank_vals.append(14)
        elif x == 'K': rank_vals.append(13)
        elif x == 'Q': rank_vals.append(12)
        elif x == 'J': rank_vals.append(11)
        elif x == 'T': rank_vals.append(10)
        else:
            try:   rank_vals.append(int(x))
            except: continue
    if len(rank_vals) < 3:
        return 0
    rank_vals = sorted(rank_vals, reverse=True)
    top, mid, bot = rank_vals
    if top == mid or mid == bot:
        return 7
    total_gap = top - bot
    if total_gap <= 4:
        return 3 if top >= 9 else 4
    if top == 14 and total_gap >= 8:
        return 1
    if top >= 10 and total_gap >= 5:
        return 5
    if top <= 9:
        return 4 if total_gap <= 5 else 6
    return 2

def calc_cbs(hand_type: str, draw_type: str) -> int:
    hp = HP_TABLE.get(hand_type, 0)
    dp = DP_TABLE.get(draw_type, 0)
    if hand_type == 'no_made_hand' and draw_type == 'oesd':
        return hp - 2
    return hp + dp

def calc_confidence(cbs: int, threshold: int, board_type: int) -> str:
    distance = abs(cbs - threshold)
    if distance >= 3:
        return 'HIGH'
    if board_type == 1 and distance <= 2:
        return 'HIGH'
    if board_type == 7 and distance == 0:
        return 'HIGH'
    if board_type == 7 and distance == 1:
        return 'LOW'
    if distance == 2:
        return 'MID'
    if board_type == 5:
        return 'MID'
    if board_type in (3, 4):
        return 'LOW'
    return 'MID'

# ─── Data Loading ─────────────────────────────────────────────────────────────
def get_scenario_cat(fname: str) -> str:
    name = Path(fname).stem.replace('draw_study_', '')
    if 'SBR25' in name:
        return 'EXCLUDE'
    if 'SB_cc' in name:
        return 'BTN'
    if 'LIMP' in name:
        return 'LIMP'
    if '3BP' in name:
        return '3BP'
    if 'SB' in name:
        return 'SB'
    if 'CO' in name:
        return 'CO'
    return 'BTN'

def load_records():
    """
    Returns list of dicts:
      {scenario, board_id, board_type, hand_type, draw_type,
       cbs, threshold, distance, is_bet_cbs, is_bet_gto, gto_pct,
       confidence, freq_pred}
    """
    records = []
    files = glob.glob(str(FINDINGS_DIR / "draw_study_*.jsonl"))

    for fpath in sorted(files):
        cat = get_scenario_cat(fpath)
        if cat == 'EXCLUDE':
            continue
        threshold = THRESHOLDS.get(cat, 5)

        with open(fpath) as fh:
            for line in fh:
                try:
                    board = json.loads(line)
                    board_id = board['board_id']
                    board_type = classify_board(board_id)
                    for key, val in board['cross'].items():
                        gto_pct = val['avg']
                        hand_type, draw_type = key.split('|')
                        if hand_type not in HP_TABLE or draw_type not in DP_TABLE:
                            continue
                        cbs = calc_cbs(hand_type, draw_type)
                        distance = abs(cbs - threshold)
                        is_bet_cbs = cbs >= threshold
                        is_bet_gto = gto_pct >= 50.0
                        conf = calc_confidence(cbs, threshold, board_type)
                        freq_pred = FREQ_TABLE.get((conf, is_bet_cbs), 50)
                        records.append({
                            'scenario': cat,
                            'board_id': board_id,
                            'board_type': board_type,
                            'hand_type': hand_type,
                            'draw_type': draw_type,
                            'cbs': cbs,
                            'threshold': threshold,
                            'distance': distance,
                            'is_bet_cbs': is_bet_cbs,
                            'is_bet_gto': is_bet_gto,
                            'gto_pct': gto_pct,
                            'confidence': conf,
                            'freq_pred': freq_pred,
                        })
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

    return records

# ─── Analysis Functions ───────────────────────────────────────────────────────
def pct(n, total):
    return f"{100*n/total:.1f}%" if total else "—"

def rmse(records, pred_key='freq_pred'):
    if not records:
        return float('nan')
    ss = sum((r['gto_pct'] - r[pred_key]) ** 2 for r in records)
    return math.sqrt(ss / len(records))

def mean_gto(records):
    if not records: return float('nan')
    return sum(r['gto_pct'] for r in records) / len(records)

def direction_accuracy(records):
    correct = sum(1 for r in records if r['is_bet_cbs'] == r['is_bet_gto'])
    return correct, len(records)

# ─── Report ───────────────────────────────────────────────────────────────────
def main():
    print("Loading GTO data...")
    records = load_records()
    print(f"  Total records: {len(records)}")
    print()

    # ── 1. Direction Accuracy by Scenario ──
    print("=" * 60)
    print("1. 方向判定精度（ベット vs チェック, 50%閾値）")
    print("=" * 60)
    print(f"{'シナリオ':<10} {'正解数':>6} {'全件':>6} {'正解率':>8}")
    print("-" * 36)
    scenarios = sorted(set(r['scenario'] for r in records))
    total_c, total_n = 0, 0
    for sc in scenarios:
        recs = [r for r in records if r['scenario'] == sc]
        c, n = direction_accuracy(recs)
        total_c += c; total_n += n
        print(f"{sc:<10} {c:>6} {n:>6} {pct(c,n):>8}")
    print("-" * 36)
    print(f"{'全体':<10} {total_c:>6} {total_n:>6} {pct(total_c,total_n):>8}")
    print()

    # ── 2. Direction Accuracy by Confidence Level ──
    print("=" * 60)
    print("2. 確信度別 方向判定精度")
    print("=" * 60)
    print(f"{'確信度':<8} {'正解数':>6} {'全件':>6} {'正解率':>8} {'平均GTO%':>10}")
    print("-" * 44)
    for conf in ['HIGH', 'MID', 'LOW']:
        recs = [r for r in records if r['confidence'] == conf]
        c, n = direction_accuracy(recs)
        mg = mean_gto(recs)
        print(f"{conf:<8} {c:>6} {n:>6} {pct(c,n):>8} {mg:>9.1f}%")
    print()

    # ── 3. Validated GTO averages vs FREQ_TABLE ──
    print("=" * 60)
    print("3. FREQ_TABLE検証（確信度×方向 → 実測GTO平均%）")
    print("=" * 60)
    print(f"{'確信度':<8} {'方向':<8} {'予測%':>7} {'実測%':>7} {'誤差':>7} {'件数':>6}")
    print("-" * 46)
    for conf in ['HIGH', 'MID', 'LOW']:
        for is_bet, dir_label in [(True, 'ベット'), (False, 'チェック')]:
            recs = [r for r in records if r['confidence'] == conf and r['is_bet_cbs'] == is_bet]
            mg = mean_gto(recs)
            pred = FREQ_TABLE.get((conf, is_bet), 50)
            err = mg - pred
            print(f"{conf:<8} {dir_label:<8} {pred:>6}% {mg:>6.1f}% {err:>+6.1f}% {len(recs):>6}")
    print()

    # ── 4. RMSE Analysis ──
    print("=" * 60)
    print("4. RMSE 精度分析")
    print("=" * 60)
    baseline_mean = mean_gto(records)
    for r in records:
        r['_baseline'] = baseline_mean
    rmse_baseline = rmse(records, '_baseline')
    rmse_freq = rmse(records, 'freq_pred')
    improvement = (rmse_baseline - rmse_freq) / rmse_baseline * 100

    print(f"  ベースライン RMSE（定数={baseline_mean:.1f}%）: {rmse_baseline:.1f}%")
    print(f"  CBS二系統 RMSE:                        {rmse_freq:.1f}%")
    print(f"  改善率:                                {improvement:.1f}%")
    print()

    # ── 5. Direction Accuracy by CBS Distance ──
    print("=" * 60)
    print("5. CBS距離別 方向判定精度（全シナリオ合計）")
    print("=" * 60)
    print(f"{'距離':<6} {'正解数':>6} {'全件':>6} {'正解率':>8} {'平均GTO%':>10}")
    print("-" * 40)
    for dist in range(6):
        recs = [r for r in records if r['distance'] == dist]
        if not recs: continue
        c, n = direction_accuracy(recs)
        mg = mean_gto(recs)
        print(f"{dist:<6} {c:>6} {n:>6} {pct(c,n):>8} {mg:>9.1f}%")
    recs3p = [r for r in records if r['distance'] >= 3]
    c, n = direction_accuracy(recs3p)
    mg = mean_gto(recs3p)
    print(f"{'≥3':<6} {c:>6} {n:>6} {pct(c,n):>8} {mg:>9.1f}%")
    print()

    # ── 6. Board Type × Direction Accuracy ──
    print("=" * 60)
    print("6. ボード型別 方向判定精度（距離0-2, BTN）")
    print("=" * 60)
    print(f"{'ボード型':<8} {'距離0-1':>8} {'距離2':>8} {'距離≥3':>8}")
    print("-" * 36)
    btn_recs = [r for r in records if r['scenario'] == 'BTN']
    for bt in [1, 3, 4, 5, 7]:
        row = []
        for dist_range in [(0, 1), (2, 2), (3, 99)]:
            recs = [r for r in btn_recs
                    if r['board_type'] == bt
                    and dist_range[0] <= r['distance'] <= dist_range[1]]
            if recs:
                c, n = direction_accuracy(recs)
                row.append(f"{pct(c,n):>7} ({n})")
            else:
                row.append("     — ")
        print(f"型{bt:<7} {row[0]:>14} {row[1]:>14} {row[2]:>14}")
    print()

    # ── 7. Per-hand accuracy (worst offenders) ──
    print("=" * 60)
    print("7. 手牌別 平均GTO% vs CBS予測（BTN, ドローなし）")
    print("=" * 60)
    print(f"{'手牌':<20} {'HP':>4} {'CBS':>4} {'方向':>8} {'GTO平均%':>9} {'正解率':>8} {'件数':>5}")
    print("-" * 62)
    hand_types = sorted(HP_TABLE.keys())
    for ht in hand_types:
        recs = [r for r in records
                if r['scenario'] == 'BTN' and r['hand_type'] == ht and r['draw_type'] == 'no_draw']
        if not recs: continue
        hp = HP_TABLE[ht]
        cbs = calc_cbs(ht, 'no_draw')
        direction = "ベット" if cbs >= 5 else "チェック"
        mg = mean_gto(recs)
        c, n = direction_accuracy(recs)
        acc = f"{pct(c,n)}"
        print(f"{ht:<20} {hp:>4} {cbs:>4} {direction:>8} {mg:>8.1f}% {acc:>8} {n:>5}")
    print()

    # ── 8. Air paradox verification ──
    print("=" * 60)
    print("8. エアー逆説検証（BTN, no_made_hand）")
    print("=" * 60)
    print(f"{'ドロー':<20} {'CBS':>4} {'GTO平均%':>9} {'方向予測':>10} {'件数':>5}")
    print("-" * 52)
    draw_order = ['no_draw', 'onecard_bdfd', 'twocards_bdfd', 'gutshot',
                  'flush_draw', 'nut_flush_draw', 'oesd', 'combo_draw']
    for dt in draw_order:
        recs = [r for r in records
                if r['scenario'] == 'BTN'
                and r['hand_type'] == 'no_made_hand'
                and r['draw_type'] == dt]
        if not recs: continue
        cbs = calc_cbs('no_made_hand', dt)
        mg = mean_gto(recs)
        direction = "ベット" if cbs >= 5 else "チェック"
        print(f"{dt:<20} {cbs:>4} {mg:>8.1f}% {direction:>10} {len(recs):>5}")
    print()

    # ── 9. Scenario comparison: BTN vs CO ──
    print("=" * 60)
    print("9. BTN vs CO 比較（ドローなし、主要手牌）")
    print("=" * 60)
    print(f"{'手牌':<18} {'BTN平均%':>9} {'CO平均%':>9} {'差':>7}")
    print("-" * 46)
    key_hands = ['ace_high', 'second_pair', 'top_pair', 'two_pair', 'no_made_hand']
    for ht in key_hands:
        btn = [r for r in records if r['scenario']=='BTN' and r['hand_type']==ht and r['draw_type']=='no_draw']
        co  = [r for r in records if r['scenario']=='CO'  and r['hand_type']==ht and r['draw_type']=='no_draw']
        if btn and co:
            mb = mean_gto(btn)
            mc = mean_gto(co)
            print(f"{ht:<18} {mb:>8.1f}% {mc:>8.1f}% {mc-mb:>+6.1f}%")
    print()

    print("=" * 60)
    print("検証完了")
    print("=" * 60)

if __name__ == '__main__':
    main()
