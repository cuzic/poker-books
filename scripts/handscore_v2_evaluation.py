#!/usr/bin/env python3
"""HandScore v1 vs v2 を PokerBench で精度比較.

各 (board, holding, GTO_action) に対して v1 と v2 の HandScore を計算し:
  - 単調性 (高 score → 高 P(Bet))
  - 最適 threshold での予測精度
  - スピアマン相関 (HandScore vs GTO bet rate)
を比較する。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import hand_evaluator as v1
import hand_evaluator_v2 as v2

POKERBENCH_CSV = REPO / "data/pokerbench/postflop_500k_train.csv"
OUTPUT = REPO / "knowledges/flop-advanced/handscore_calibration/v1_vs_v2.json"


def normalize_board(b):
    return ",".join(b[i:i + 2] for i in range(0, len(b), 2))


def main():
    df = pd.read_csv(POKERBENCH_CSV, low_memory=False)
    target = df[
        (df['evaluation_at'] == 'Flop') &
        (df['preflop_action'] == 'BTN/2.5bb/BB/call') &
        (df['hero_position'] == 'IP') &
        (df['postflop_action'] == 'OOP_CHECK')
    ].copy()

    records = []
    for _, row in target.iterrows():
        board = normalize_board(row['board_flop'])
        try:
            s1, l1 = v1.evaluate(row['holding'], board)
            s2, l2 = v2.evaluate(row['holding'], board)
        except Exception:
            continue
        action = str(row['correct_decision']).strip().lower()
        if not (action.startswith('bet') or action.startswith('check')):
            continue
        is_bet = action.startswith('bet')
        records.append({
            'board': row['board_flop'],
            'holding': row['holding'],
            'v1_score': s1, 'v1_label': l1,
            'v2_score': s2, 'v2_label': l2,
            'is_bet': is_bet,
        })
    pdf = pd.DataFrame(records)
    print(f"Total samples: {len(pdf):,}")

    # スコア別 P(Bet) の単調性比較
    def monotonic_check(score_col, name):
        agg = pdf.groupby(score_col).agg(
            n=('is_bet', 'count'),
            p_bet=('is_bet', 'mean')
        ).reset_index()
        print(f"\n=== {name} スコア別 P(Bet) ===")
        print(agg.to_string(index=False))
        # 単調性: 連続するスコア間で P(Bet) が下がる回数
        prev = None
        violations = 0
        for _, r in agg.iterrows():
            if prev is not None and r['p_bet'] < prev:
                violations += 1
            prev = r['p_bet']
        print(f"単調性違反 (前スコアより P(Bet) が下がる箇所): {violations}")
        return agg, violations

    v1_agg, v1_viol = monotonic_check('v1_score', 'v1')
    v2_agg, v2_viol = monotonic_check('v2_score', 'v2')

    # 最適 threshold の予測精度
    def best_threshold(score_col, name):
        best_acc = 0
        best_t = 0
        for t in range(2, 21):
            pred = pdf[score_col] >= t
            acc = (pred == pdf['is_bet']).mean()
            if acc > best_acc:
                best_acc = acc
                best_t = t
        return best_t, best_acc

    v1_t, v1_acc = best_threshold('v1_score', 'v1')
    v2_t, v2_acc = best_threshold('v2_score', 'v2')

    # スピアマン相関 (各サンプルの score と action の相関)
    from scipy.stats import spearmanr
    v1_corr, _ = spearmanr(pdf['v1_score'], pdf['is_bet'].astype(int))
    v2_corr, _ = spearmanr(pdf['v2_score'], pdf['is_bet'].astype(int))

    # H3/H2/H1 バケツの bet 率
    pdf['v1_bucket'] = pdf['v1_score'].apply(v1.bucket)
    pdf['v2_bucket'] = pdf['v2_score'].apply(v2.bucket)
    print("\n=== バケツ別 P(Bet) v1 ===")
    print(pdf.groupby('v1_bucket')['is_bet'].agg(['count', 'mean']))
    print("\n=== バケツ別 P(Bet) v2 ===")
    print(pdf.groupby('v2_bucket')['is_bet'].agg(['count', 'mean']))

    # サマリー
    print("\n=== 比較サマリー ===")
    print(f"{'指標':<30} {'v1':>10} {'v2':>10} {'改善':>10}")
    print('-' * 65)
    print(f"{'単調性違反 (低いほど良)':<30} {v1_viol:>10} {v2_viol:>10} "
          f"{v1_viol - v2_viol:>+10}")
    print(f"{'最適 threshold':<30} {v1_t:>10} {v2_t:>10}")
    print(f"{'最適 threshold 精度':<30} {v1_acc:>10.1%} {v2_acc:>10.1%} "
          f"{v2_acc - v1_acc:>+10.1%}")
    print(f"{'スピアマン相関':<30} {v1_corr:>10.3f} {v2_corr:>10.3f} "
          f"{v2_corr - v1_corr:>+10.3f}")

    # 保存
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "n_samples": len(pdf),
        "v1": {
            "monotonicity_violations": v1_viol,
            "best_threshold": v1_t, "best_accuracy": round(v1_acc, 4),
            "spearman_correlation": round(v1_corr, 4),
            "score_distribution": v1_agg.to_dict('records'),
        },
        "v2": {
            "monotonicity_violations": v2_viol,
            "best_threshold": v2_t, "best_accuracy": round(v2_acc, 4),
            "spearman_correlation": round(v2_corr, 4),
            "score_distribution": v2_agg.to_dict('records'),
        },
        "improvement": {
            "monotonicity_reduction": v1_viol - v2_viol,
            "accuracy_gain": round(v2_acc - v1_acc, 4),
            "correlation_gain": round(v2_corr - v1_corr, 4),
        }
    }
    OUTPUT.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
