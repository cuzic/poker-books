#!/usr/bin/env python3
"""BoardScore PokerBench 検証 v3 (新スケール 0-100 equity %)

旧版 boardscore_pokerbench.py の新スケール対応。
旧版は残し、新規 v3 として作成。

PokerBench (Apache 2.0) の per-(board, holding) → GTO action から、
新スケール HandScore で:
  - strong_bet_rate: HandScore >= 65 (H3) のハンドが bet される率
  - weak_bet_rate:   HandScore < 35  (H1) のハンドが bet される率
  - tp_plus_bet_rate: TPTK / 2 ペア / オーバーペア bet 率

を 17 型で集約する。

旧版閾値:
  HS >= 14 (H3 旧) → 新 HS >= 65
  HS <=  4 (H1 旧) → 新 HS < 35

依存:
  - hand_evaluator_v3 が存在する場合はそれを使用 (新スケール直接)
  - 存在しない場合は hand_evaluator_v2 (旧スケール) で計算 → 新スケールに変換
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from c_coefficients_v3 import HS_TH_H3, HS_TH_H2  # noqa: E402

# hand_evaluator_v3 が無い場合は v2 (旧スケール 0-30) で計算してマップ
try:
    import hand_evaluator_v3 as _v3  # noqa: E402
    # v3 は evaluate_v3 という名前
    _evaluate_fn = _v3.evaluate_v3
    HS_SCALE = "new"
except (ImportError, AttributeError):
    import hand_evaluator_v2 as _v2  # noqa: E402
    _evaluate_fn = _v2.evaluate
    HS_SCALE = "old"

from board_classifier import classify  # noqa: E402

POKERBENCH_CSV = REPO / "data/pokerbench/postflop_500k_train.csv"
OUTPUT = REPO / "knowledges/flop-advanced/handscore_calibration/boardscore_v3.json"


def normalize_board(b):
    return ",".join(b[i:i + 2] for i in range(0, len(b), 2))


def map_old_hs_to_new(score: int) -> int:
    """旧スケール 0-30 を新スケール 0-100 に近似変換 (粗い、検証用のみ)."""
    # 旧 H3 >= 14 → 新 H3 >= 65, 旧 H2 7-13 → 新 35-64, 旧 H1 < 7 → 新 < 35
    if score >= 14:
        # 14→65, 15→70, 16→75, 17→80, 18→82, 20→88, 25→92, 30→95
        return min(95, 65 + (score - 14) * 5)
    if score >= 7:
        # 7→35, 8→40, 9→45, 10→48, 11→52, 12→56, 13→60
        return 35 + (score - 7) * 4
    # < 7
    if score >= 4:
        return 25 + (score - 4) * 3   # 4→25, 5→28, 6→31
    return max(8, score * 4)          # 0→8, 1→12, 2→16, 3→20


def get_score_new(holding: str, board: str) -> tuple[int | None, str | None]:
    """holding+board から新スケール HS を返す."""
    try:
        score, label = _evaluate_fn(holding, board)
    except Exception:
        return None, None
    if HS_SCALE == "old":
        score = map_old_hs_to_new(score)
    return score, label


def main():
    if not POKERBENCH_CSV.exists():
        print(f"ERROR: {POKERBENCH_CSV} 未存在")
        return

    print(f"PokerBench データ読込中... (スケール: {HS_SCALE})")
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
        score, label = get_score_new(row['holding'], board)
        if score is None:
            continue
        action = str(row['correct_decision']).strip().lower()
        if not (action.startswith('bet') or action.startswith('check')):
            continue
        is_bet = action.startswith('bet')

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

    # === per-board metrics (新スケール HS_TH_H3 = 65 / weak < 35) ===
    print(f"\n=== per-board derived BoardScore (新スケール) ===")
    print(f"strong_bet_rate: HS >= {HS_TH_H3} のハンドの bet 率")
    print(f"weak_bet_rate:   HS <  {HS_TH_H2} のハンドの bet 率")
    board_metrics = []
    for board, sub in pdf.groupby('board'):
        strong = sub[sub['hand_score'] >= HS_TH_H3]
        weak = sub[sub['hand_score'] < HS_TH_H2]
        tp_or_better = sub[sub['category'].isin([
            'TPTK', '2ペア', 'オーバーペア', 'セット', 'トリップス',
            'ストレート', 'フラッシュ/SF',
        ])]
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
            'strong_bet_rate': (
                round(strong['is_bet'].mean(), 3) if len(strong) > 0 else None
            ),
            'weak_n': len(weak),
            'weak_bet_rate': (
                round(weak['is_bet'].mean(), 3) if len(weak) > 0 else None
            ),
            'tp_plus_n': len(tp_or_better),
            'tp_plus_bet_rate': (
                round(tp_or_better['is_bet'].mean(), 3)
                if len(tp_or_better) > 0 else None
            ),
            'overall_cbet': round(sub['is_bet'].mean(), 3),
        })

    bm = pd.DataFrame(board_metrics).sort_values(
        'strong_bet_rate', ascending=False, na_position='last',
    )
    print(bm.to_string(index=False))

    # === per-type aggregation ===
    print(f"\n=== per-type BoardScore (17 型集約, 新スケール) ===")
    type_metrics = []
    for type_code, sub in pdf.groupby('type_code'):
        strong = sub[sub['hand_score'] >= HS_TH_H3]
        weak = sub[sub['hand_score'] < HS_TH_H2]
        n_boards = sub['board'].nunique()
        type_metrics.append({
            'type_code': type_code,
            'n_boards': n_boards,
            'n_holdings': len(sub),
            'strong_n': len(strong),
            'strong_bet_rate': (
                round(strong['is_bet'].mean(), 3) if len(strong) > 0 else None
            ),
            'weak_n': len(weak),
            'weak_bet_rate': (
                round(weak['is_bet'].mean(), 3) if len(weak) > 0 else None
            ),
        })
    tm = pd.DataFrame(type_metrics).sort_values('type_code')
    print(tm.to_string(index=False))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps({
        "scale": "v3 (new, 0-100 equity %)",
        "hs_source_scale": HS_SCALE,
        "thresholds": {"H3": HS_TH_H3, "H2": HS_TH_H2},
        "per_board": board_metrics,
        "per_type": type_metrics,
    }, indent=2, ensure_ascii=False))
    print(f"\nSaved: {OUTPUT}")


if __name__ == "__main__":
    main()
