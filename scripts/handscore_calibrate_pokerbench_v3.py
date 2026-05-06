#!/usr/bin/env python3
"""HandScore PokerBench キャリブレーション v3 (新スケール 0-100 equity %).

旧版 handscore_calibrate_pokerbench.py の新スケール対応。
旧版は残し、新規 v3 として作成。

PokerBench (Apache 2.0) は per-(board, holding) → GTO action を提供する。
本スクリプトは:
1. PokerBench の BTN-vs-BB SRP IP-CBet サンプルを読む
2. 各 (board, holding) に対して新スケール HandScore を計算
3. HandScore vs GTO action (Bet/Check) の関係を分析
4. 最適 threshold と 予測精度を出す（新スケール: 35 / 65 を中心に）
5. 不一致パターンをリスト

新スケール閾値:
  H1 < 35 / H2 35-64 / H3 >= 65
  threshold sweep: 25, 30, 35, 40, ..., 95

旧版との主な違い:
  - HS スケール: 0-30 → 0-100 (equity %)
  - threshold range: 2-20 → 25-95
  - 高 HS 不一致: >= 15 → >= 70
  - 低 HS 不一致: <= 5 → <= 25
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import Counter

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

# v3 evaluator (新スケール直接)
try:
    import hand_evaluator_v3 as _v3  # noqa: E402
    _evaluate_fn = _v3.evaluate_v3
    HS_SCALE = "new"
except (ImportError, AttributeError):
    print("WARN: hand_evaluator_v3 未存在 → v1 + 旧→新マップで代替")
    from hand_evaluator import evaluate as _evaluate_fn  # noqa: E402
    HS_SCALE = "old"

from c_coefficients_v3 import HS_TH_H3, HS_TH_H2  # noqa: E402

POKERBENCH_CSV = REPO / "data/pokerbench/postflop_500k_train.csv"
OUTPUT_DIR = REPO / "knowledges/flop-advanced/handscore_calibration"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 新スケールにおける「高 HS」と「低 HS」 (旧 >= 15 / <= 5 相当)
HIGH_HS_THRESHOLD = HS_TH_H3      # 65 (旧 14-15 相当)
LOW_HS_THRESHOLD = 25             # 旧 5 相当 (BDFD/BDSD 以下)


def map_old_to_new(score: int) -> int:
    """旧スケール 0-30 → 新スケール 0-100 近似."""
    if score >= 14:
        return min(95, 65 + (score - 14) * 5)
    if score >= 7:
        return 35 + (score - 7) * 4
    if score >= 4:
        return 25 + (score - 4) * 3
    return max(8, score * 4)


def normalize_board(board_flop: str) -> str:
    """PokerBench 'Ks7h2d' → ',' 区切り 'Ks,7h,2d'."""
    cards = [board_flop[i:i + 2] for i in range(0, len(board_flop), 2)]
    return ",".join(cards)


def evaluate(holding: str, board: str) -> tuple[int, str]:
    score, label = _evaluate_fn(holding, board)
    if HS_SCALE == "old":
        score = map_old_to_new(score)
    return score, label


def main():
    print(f"PokerBench データ読込中... (HS スケール: {HS_SCALE})")
    df = pd.read_csv(POKERBENCH_CSV, low_memory=False)

    target = df[
        (df['evaluation_at'] == 'Flop') &
        (df['preflop_action'] == 'BTN/2.5bb/BB/call') &
        (df['hero_position'] == 'IP') &
        (df['postflop_action'] == 'OOP_CHECK')
    ].copy()
    print(f"BTN-vs-BB SRP IP-CBet: {len(target):,} 行 / {target['board_flop'].nunique()} ボード")

    # HandScore を計算
    records = []
    for _, row in target.iterrows():
        board = normalize_board(row['board_flop'])
        try:
            score, label = evaluate(row['holding'], board)
        except Exception:
            continue
        action = str(row['correct_decision']).strip().lower()
        is_bet = action.startswith('bet')
        records.append({
            'board': row['board_flop'],
            'holding': row['holding'],
            'hand_score': score,
            'category': label,
            'action': 'bet' if is_bet else (
                'check' if action.startswith('check') else 'other'
            ),
            'correct_decision': row['correct_decision'],
            'pot_size': row.get('pot_size'),
        })
    pdf = pd.DataFrame(records)
    pdf = pdf[pdf['action'].isin(['bet', 'check'])]
    print(f"有効サンプル: {len(pdf):,}")
    print()

    # === HS バケット別の bet 確率 ===
    # 新スケール: 5 刻み bin
    print("=== HandScore バケット別 bet 確率 (新スケール) ===")
    print(f"{'HS bin':<12} {'N':>6} {'P(Bet)':>8} {'代表カテゴリ'}")
    print('-' * 70)
    bin_edges = list(range(0, 105, 5))
    pdf['hs_bin'] = pd.cut(pdf['hand_score'], bins=bin_edges, right=False)
    for bin_label, sub in pdf.groupby('hs_bin', observed=True):
        if len(sub) == 0:
            continue
        p_bet = (sub['action'] == 'bet').mean()
        cat_counter = Counter(sub['category'])
        top_cats = ', '.join(
            f"{c}({n})" for c, n in cat_counter.most_common(2)
        )
        print(f"{str(bin_label):<12} {len(sub):>6} {p_bet:>8.1%} {top_cats}")

    print()
    print("=== カテゴリ別 bet 確率 ===")
    print(f"{'Category':<25} {'平均HS':>7} {'N':>6} {'P(Bet)':>8}")
    print('-' * 60)
    for cat, sub in pdf.groupby('category'):
        if len(sub) < 3:
            continue
        avg_hs = sub['hand_score'].mean()
        p_bet = (sub['action'] == 'bet').mean()
        print(f"{cat:<25} {avg_hs:>7.1f} {len(sub):>6} {p_bet:>8.1%}")

    print()
    print("=== threshold 別 予測精度 (新スケール) ===")
    print(
        f"{'Threshold':<12} {'Acc':>7} "
        f"{'P(Bet|HS>=t)':>13} {'P(Check|HS<t)':>15}"
    )
    print('-' * 60)
    # 新スケール: 25-95 を 5 刻みで sweep
    for t in range(25, 100, 5):
        pdf_pred = pdf['hand_score'] >= t
        pdf_actual = pdf['action'] == 'bet'
        acc = (pdf_pred == pdf_actual).mean()
        if (pdf['hand_score'] >= t).any():
            p_bet_high = (
                pdf[pdf['hand_score'] >= t]['action'] == 'bet'
            ).mean()
        else:
            p_bet_high = float('nan')
        if (pdf['hand_score'] < t).any():
            p_check_low = (
                pdf[pdf['hand_score'] < t]['action'] == 'check'
            ).mean()
        else:
            p_check_low = float('nan')
        print(f"{t:<12} {acc:>7.1%} {p_bet_high:>13.1%} {p_check_low:>15.1%}")

    # 不一致パターン
    print()
    print(f"=== 不一致: 高 HS (>= {HIGH_HS_THRESHOLD}) で Check ===")
    high_pool = pdf[pdf['hand_score'] >= HIGH_HS_THRESHOLD]
    high_check = high_pool[high_pool['action'] == 'check']
    rate_str = (
        f"{len(high_check) / max(1, len(high_pool)):.1%}"
        if len(high_pool) > 0 else "N/A"
    )
    print(f"件数: {len(high_check)} / 高HS {len(high_pool)} = {rate_str}")
    print()
    print("板別 高HS-Check 件数 上位 10:")
    if len(high_check) > 0:
        print(high_check.groupby('board').size()
              .sort_values(ascending=False).head(10))

    print()
    print(f"=== 不一致: 低 HS (<= {LOW_HS_THRESHOLD}) で Bet ===")
    low_pool = pdf[pdf['hand_score'] <= LOW_HS_THRESHOLD]
    low_bet = low_pool[low_pool['action'] == 'bet']
    rate_str = (
        f"{len(low_bet) / max(1, len(low_pool)):.1%}"
        if len(low_pool) > 0 else "N/A"
    )
    print(f"件数: {len(low_bet)} / 低HS {len(low_pool)} = {rate_str}")
    print()
    print("板別 低HS-Bet 件数 上位 10:")
    if len(low_bet) > 0:
        print(low_bet.groupby('board').size()
              .sort_values(ascending=False).head(10))

    # 保存
    pdf.drop(columns=['hs_bin'], errors='ignore').to_csv(
        OUTPUT_DIR / "handscore_v3_vs_pokerbench.csv", index=False,
    )
    high_check.to_csv(OUTPUT_DIR / "high_handscore_v3_check.csv", index=False)
    low_bet.to_csv(OUTPUT_DIR / "low_handscore_v3_bet.csv", index=False)
    print()
    print(f"保存先: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
