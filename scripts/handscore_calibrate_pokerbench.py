#!/usr/bin/env python3
"""HandScore を PokerBench (Apache 2.0) で キャリブレーション.

PokerBench は per-(board, holding) → GTO action を提供する。
個別決定なので balanced sampling の影響を受けない（count 分布のみ歪み）。

本スクリプトは:
1. PokerBench の BTN-vs-BB SRP IP-CBet 1456 サンプルを読む
2. 各 (board, holding) に対して現行 HandScore を計算
3. HandScore vs GTO action (Bet/Check) の関係を分析
4. 最適 threshold と HandScore の予測精度を出す
5. 不一致パターン (HandScore は高いが Check 等) をリスト

使い方:
    python3 scripts/handscore_calibrate_pokerbench.py
"""
from __future__ import annotations
import sys
from pathlib import Path
from collections import defaultdict, Counter

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from hand_evaluator import evaluate  # noqa: E402

POKERBENCH_CSV = REPO / "data/pokerbench/postflop_500k_train.csv"
OUTPUT_DIR = REPO / "knowledges/flop-advanced/handscore_calibration"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def normalize_board(board_flop: str) -> str:
    """PokerBench 'Ks7h2d' → ',' 区切り 'Ks,7h,2d' に変換 (hand_evaluator 用)."""
    cards = [board_flop[i:i + 2] for i in range(0, len(board_flop), 2)]
    return ",".join(cards)


def main():
    print(f"Loading PokerBench dataset...")
    df = pd.read_csv(POKERBENCH_CSV, low_memory=False)

    target = df[
        (df['evaluation_at'] == 'Flop') &
        (df['preflop_action'] == 'BTN/2.5bb/BB/call') &
        (df['hero_position'] == 'IP') &
        (df['postflop_action'] == 'OOP_CHECK')
    ].copy()
    print(f"BTN-vs-BB SRP IP-CBet sample: {len(target):,} rows, {target['board_flop'].nunique()} boards")

    # HandScore を計算
    records = []
    for _, row in target.iterrows():
        board = normalize_board(row['board_flop'])
        try:
            score, label = evaluate(row['holding'], board)
        except Exception as e:
            continue
        action = str(row['correct_decision']).strip().lower()
        is_bet = action.startswith('bet')
        records.append({
            'board': row['board_flop'],
            'holding': row['holding'],
            'hand_score': score,
            'category': label,
            'action': 'bet' if is_bet else ('check' if action.startswith('check') else 'other'),
            'correct_decision': row['correct_decision'],
            'pot_size': row.get('pot_size'),
        })
    pdf = pd.DataFrame(records)
    pdf = pdf[pdf['action'].isin(['bet', 'check'])]
    print(f"Valid (HandScore evaluated, action=bet/check): {len(pdf):,}")
    print()

    # 分布
    print("=== HandScore 値別の bet 確率 ===")
    print(f"{'HandScore':<10} {'N':>5} {'P(Bet)':>8} {'代表カテゴリ'}")
    print('-' * 60)
    for score in sorted(pdf['hand_score'].unique()):
        sub = pdf[pdf['hand_score'] == score]
        p_bet = (sub['action'] == 'bet').mean()
        cat_counter = Counter(sub['category'])
        top_cats = ', '.join(f"{c}({n})" for c, n in cat_counter.most_common(2))
        print(f"{score:<10} {len(sub):>5} {p_bet:>8.1%} {top_cats}")

    print()
    print("=== カテゴリ別の bet 確率 ===")
    print(f"{'Category':<25} {'Score':>5} {'N':>5} {'P(Bet)':>8}")
    print('-' * 55)
    for cat in pdf['category'].unique():
        sub = pdf[pdf['category'] == cat]
        if len(sub) < 3:
            continue
        score = sub['hand_score'].iloc[0]
        p_bet = (sub['action'] == 'bet').mean()
        print(f"{cat:<25} {score:>5} {len(sub):>5} {p_bet:>8.1%}")

    print()
    print("=== threshold 別の予測精度 ===")
    print(f"{'Threshold':<12} {'Acc':>7} {'P(Bet|HS≥t)':>13} {'P(Check|HS<t)':>15}")
    print('-' * 55)
    for t in range(2, 21):
        pdf_pred = pdf['hand_score'] >= t
        pdf_actual = pdf['action'] == 'bet'
        acc = (pdf_pred == pdf_actual).mean()
        if (pdf['hand_score'] >= t).any():
            p_bet_high = (pdf[pdf['hand_score'] >= t]['action'] == 'bet').mean()
        else:
            p_bet_high = float('nan')
        if (pdf['hand_score'] < t).any():
            p_check_low = (pdf[pdf['hand_score'] < t]['action'] == 'check').mean()
        else:
            p_check_low = float('nan')
        print(f"{t:<12} {acc:>7.1%} {p_bet_high:>13.1%} {p_check_low:>15.1%}")

    # 不一致 (高 HandScore で check / 低 HandScore で bet) のパターン
    print()
    print("=== 不一致サンプル: 高 HandScore (≥15) で Check ===")
    high_check = pdf[(pdf['hand_score'] >= 15) & (pdf['action'] == 'check')]
    print(f"件数: {len(high_check)} / 高HS全体 {len(pdf[pdf['hand_score'] >= 15])} = "
          f"{len(high_check)/max(1,len(pdf[pdf['hand_score'] >= 15])):.1%}")
    print()
    print("板別 高HS-Check 件数 上位 10:")
    print(high_check.groupby('board').size().sort_values(ascending=False).head(10))

    print()
    print("=== 不一致サンプル: 低 HandScore (≤5) で Bet ===")
    low_bet = pdf[(pdf['hand_score'] <= 5) & (pdf['action'] == 'bet')]
    print(f"件数: {len(low_bet)} / 低HS全体 {len(pdf[pdf['hand_score'] <= 5])} = "
          f"{len(low_bet)/max(1,len(pdf[pdf['hand_score'] <= 5])):.1%}")
    print()
    print("板別 低HS-Bet 件数 上位 10:")
    print(low_bet.groupby('board').size().sort_values(ascending=False).head(10))

    # 保存
    pdf.to_csv(OUTPUT_DIR / "handscore_vs_pokerbench.csv", index=False)
    high_check.to_csv(OUTPUT_DIR / "high_handscore_check.csv", index=False)
    low_bet.to_csv(OUTPUT_DIR / "low_handscore_bet.csv", index=False)
    print()
    print(f"Saved: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
