#!/usr/bin/env python3
"""BoardScore (per-board IP CBet 頻度) を PokerBench で再導出する.

PokerBench の per-board 全体 cbet_ratio は balanced sampling で歪むが、
**per-(board, holding) の (HandScore, action) ペア** は正確。

そこで以下の派生指標を計算:
  - strong_bet_rate: HandScore≥14 のハンドが bet される率 (PFA-favorability)
  - weak_bet_rate:   HandScore≤4  のハンドが bet される率 (board のブラフ可能性)
  - top_pair_bet_rate: TPTK / 2 ペア / オーバーペアの bet 率 (バリュー bet の積極性)

これらを 17 型で集約し、現行の補正テーブル / 17 型代表値と比較する。

balanced sampling の影響を最小化するため、各カテゴリ内 (HandScore=15 など)
での bet 比率を取る → category-conditional な比率なら歪みが軽減される。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from collections import defaultdict

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import hand_evaluator_v2 as v2  # noqa: E402
from board_classifier import classify  # noqa: E402

POKERBENCH_CSV = REPO / "data/pokerbench/postflop_500k_train.csv"
OUTPUT = REPO / "knowledges/flop-advanced/handscore_calibration/boardscore_v2.json"


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
            score, label = v2.evaluate(row['holding'], board)
        except Exception:
            continue
        action = str(row['correct_decision']).strip().lower()
        if not (action.startswith('bet') or action.startswith('check')):
            continue
        is_bet = action.startswith('bet')

        # Get 17-type (use original board representation)
        try:
            feat = classify(row['board_flop'])
            type_code = feat.type_code
            type_name = feat.type_name
        except Exception:
            type_code = "?"
            type_name = "?"

        records.append({
            'board': row['board_flop'],
            'holding': row['holding'],
            'hand_score': score,
            'category': label,
            'is_bet': is_bet,
            'type_code': type_code,
            'type_name': type_name,
        })
    pdf = pd.DataFrame(records)
    print(f"Total samples: {len(pdf):,}")

    # === per-board metrics ===
    print(f"\n=== per-board derived BoardScore ===")
    board_metrics = []
    for board, sub in pdf.groupby('board'):
        strong = sub[sub['hand_score'] >= 14]
        weak = sub[sub['hand_score'] <= 4]
        tp_or_better = sub[sub['category'].isin([
            'TPTK', '2ペア', 'オーバーペア', 'セット', 'トリップス',
            'ストレート', 'フラッシュ/SF'])]
        bdfd_air = sub[sub['hand_score'] <= 4]

        # Type を取得 (hold ignore, board のみ)
        try:
            feat = classify(board)
            type_code = feat.type_code
        except Exception:
            type_code = "?"

        board_metrics.append({
            'board': board,
            'type_code': type_code,
            'n_holdings': len(sub),
            'strong_n': len(strong),
            'strong_bet_rate': round(strong['is_bet'].mean(), 3) if len(strong) > 0 else None,
            'weak_n': len(weak),
            'weak_bet_rate': round(weak['is_bet'].mean(), 3) if len(weak) > 0 else None,
            'tp_plus_n': len(tp_or_better),
            'tp_plus_bet_rate': round(tp_or_better['is_bet'].mean(), 3) if len(tp_or_better) > 0 else None,
            'overall_cbet': round(sub['is_bet'].mean(), 3),
        })

    bm = pd.DataFrame(board_metrics).sort_values('strong_bet_rate', ascending=False, na_position='last')
    print(bm.to_string(index=False))

    # === per-type aggregation ===
    print(f"\n=== per-type BoardScore (17 型集約) ===")

    # type_code を直接集計 (カテゴリ内なら balanced sampling 影響を受けにくい)
    type_metrics = []
    for type_code, sub in pdf.groupby('type_code'):
        strong = sub[sub['hand_score'] >= 14]
        weak = sub[sub['hand_score'] <= 4]
        n_boards = sub['board'].nunique()
        type_metrics.append({
            'type_code': type_code,
            'n_boards': n_boards,
            'n_holdings': len(sub),
            'strong_n': len(strong),
            'strong_bet_rate': round(strong['is_bet'].mean(), 3) if len(strong) > 0 else None,
            'weak_n': len(weak),
            'weak_bet_rate': round(weak['is_bet'].mean(), 3) if len(weak) > 0 else None,
        })
    tm = pd.DataFrame(type_metrics).sort_values('type_code')
    print(tm.to_string(index=False))

    # === 30-board ref とのクロスチェック ===
    print(f"\n=== ボード別: 30B ref CBet% vs PokerBench strong_bet_rate ===")
    with open(REPO / 'knowledges/volume4/results/texassolver_accuracy_30.json') as f:
        ref30 = json.load(f)
    import re
    rank_value = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}
    def tex(b):
        cards = re.findall(r'[2-9TJQKA][cdhs]', b)
        cards.sort(key=lambda c: -rank_value[c[0]])
        ranks = ''.join(c[0] for c in cards)
        suits = [c[1] for c in cards]
        if len(set(suits)) == 1:
            return f"{ranks}-mono"
        elif len(set(suits)) == 2:
            return f"{ranks}-tt"
        else:
            return f"{ranks}-r"

    ref_by_tex = {}
    for r in ref30['results']:
        if r.get('status') == 'ok':
            cards = ''.join(r['board_cards'].split(','))
            ref_by_tex[tex(cards)] = (r['board'], r['ref_cbet_pct'])

    matches = []
    for _, row in bm.iterrows():
        t = tex(row['board'])
        if t in ref_by_tex:
            ref_name, ref_pct = ref_by_tex[t]
            matches.append({
                'pb_board': row['board'],
                'ref_board': ref_name,
                'ref_pct': ref_pct,
                'pb_strong_bet': row['strong_bet_rate'],
                'pb_overall': row['overall_cbet'],
                'tex': t,
            })

    if matches:
        mdf = pd.DataFrame(matches)
        print(mdf.to_string(index=False))
        from scipy.stats import spearmanr
        if len(mdf) >= 3:
            corr, _ = spearmanr(mdf['ref_pct'], mdf['pb_strong_bet'])
            corr_overall, _ = spearmanr(mdf['ref_pct'], mdf['pb_overall'])
            print(f"\nSpearman corr (ref vs PB strong_bet): {corr:.3f}")
            print(f"Spearman corr (ref vs PB overall):    {corr_overall:.3f}")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "per_board": board_metrics,
        "per_type": type_metrics,
        "matches_with_ref30": matches,
    }, indent=2, ensure_ascii=False))
    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
