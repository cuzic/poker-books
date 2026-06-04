"""
compare_formulas.py — v5final vs Score_R の MTT 精度比較

2 つの計算式を比較し、GTO への精度（正解率）を測定する。

  1. v5final  — 現行 MTT 式（MTT 専用設計、精度 93.6% と主張）
  2. Score_R  — キャッシュゲーム式（ポーカードリルで使用中）

シナリオ A: キャッシュ 6-max GTO（gto-charts.json）
シナリオ B: MTT GTO（toc.md の T_open テーブルを Ground Truth として使用）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# poker-drill 側の score_r を再利用するため import path を通す
sys.path.insert(0, '/home/cuzic/poker-drill/scripts/generate')
from core.preflop_score import score_r as _score_r_poker_drill  # type: ignore  # noqa: E402

REPO_ROOT = Path('/home/cuzic/poker-books')
GTO_CHARTS_PATH = REPO_ROOT / 'knowledges' / 'preflop' / 'gto-charts.json'


# ---------------------------------------------------------------------------
# 全 169 ハンドを列挙
# ---------------------------------------------------------------------------
_RANKS = '23456789TJQKA'  # 低→高


def all_169_hands() -> list[str]:
    hands: list[str] = []
    # ペア 13
    for r in _RANKS:
        hands.append(f'{r}{r}')
    # スーテッド / オフスーツ
    for i in range(len(_RANKS) - 1, -1, -1):
        for j in range(i - 1, -1, -1):
            hi, lo = _RANKS[i], _RANKS[j]
            hands.append(f'{hi}{lo}s')
            hands.append(f'{hi}{lo}o')
    assert len(hands) == 169, f'expected 169, got {len(hands)}'
    return hands


# ---------------------------------------------------------------------------
# ランク parsing
# ---------------------------------------------------------------------------
_RANK = {r: v for v, r in enumerate('23456789TJQKA', 2)}


def parse(hand: str) -> tuple[int, int, bool, bool]:
    """hand → (H, L, suited, is_pair)。"""
    if len(hand) == 2:
        r = _RANK[hand[0]]
        return r, r, False, True
    a, b = _RANK[hand[0]], _RANK[hand[1]]
    return max(a, b), min(a, b), hand.endswith('s'), False


# ---------------------------------------------------------------------------
# Score_R: poker-drill の実装をそのまま使用
# ---------------------------------------------------------------------------
def score_r(hand: str) -> int:
    return _score_r_poker_drill(hand)


# ---------------------------------------------------------------------------
# v5final 実装
# ---------------------------------------------------------------------------
def score_v5final(hand: str) -> int:
    """v5final: MTT 専用スコア。

    ペア:    H + L + 12
    suited:  H + L + 5 - gap_cap + Aブロッカー(+3)
       gap_cap: A→0, K→min(gap,2), Q→min(gap,3), J→min(gap,4), T以下→gap全額
    offsuit: H + L - (L<10 なら -3) - gap + Aブロッカー(+3)
    """
    H, L, suited, pair = parse(hand)
    if pair:
        return H + L + 12

    gap = H - L - 1  # 隣接=0
    a_blocker = 3 if H == 14 else 0

    if suited:
        if H == 14:
            gap_cap = 0
        elif H == 13:
            gap_cap = min(gap, 2)
        elif H == 12:
            gap_cap = min(gap, 3)
        elif H == 11:
            gap_cap = min(gap, 4)
        else:  # H <= 10
            gap_cap = gap
        return H + L + 5 - gap_cap + a_blocker

    # offsuit
    penalty_l = 3 if L < 10 else 0
    return H + L - penalty_l - gap + a_blocker


# ---------------------------------------------------------------------------
# シナリオ A: キャッシュ 6-max GTO データ
# ---------------------------------------------------------------------------
POS_MAP_CASH = {
    'LJ_RFI': 'UTG',  # LJ in 6-max == UTG
    'HJ_RFI': 'HJ',
    'CO_RFI': 'CO',
    'BTN_RFI': 'BTN',
    'SB_RFI': 'SB',
}


def load_cash_gto() -> dict[str, set[str]]:
    """各ポジションの 'raise' ハンド集合を返す。"""
    with open(GTO_CHARTS_PATH, encoding='utf-8') as f:
        data = json.load(f)
    out: dict[str, set[str]] = {}
    for key, pos in POS_MAP_CASH.items():
        raise_hands = set(data[key]['actions']['raise'])
        out[pos] = raise_hands
    return out


def best_threshold(score_fn, raise_set: set[str], hands: list[str]) -> tuple[float, float]:
    """しきい値を 14〜30 で 0.5 刻みに探索し、最も精度が高い (T, acc%) を返す。"""
    best = (-1.0, -1.0)
    t = 14.0
    while t <= 30.0 + 1e-9:
        correct = 0
        for h in hands:
            predicted_open = score_fn(h) >= t
            actual_open = h in raise_set
            if predicted_open == actual_open:
                correct += 1
        acc = correct * 100.0 / len(hands)
        if acc > best[1]:
            best = (t, acc)
        t += 0.5
    return best


def scenario_a() -> dict[str, dict[str, tuple[float, float]]]:
    """シナリオ A: キャッシュ 6-max GTO への精度。

    返り値: {pos: {'score_r': (T, acc), 'v5final': (T, acc)}}
    """
    hands = all_169_hands()
    cash_gto = load_cash_gto()

    result: dict[str, dict[str, tuple[float, float]]] = {}
    for pos in ['UTG', 'HJ', 'CO', 'BTN', 'SB']:
        raise_set = cash_gto[pos]
        sr_best = best_threshold(score_r, raise_set, hands)
        v5_best = best_threshold(score_v5final, raise_set, hands)
        result[pos] = {'score_r': sr_best, 'v5final': v5_best}
    return result


# ---------------------------------------------------------------------------
# シナリオ B: MTT GTO（toc.md の T_open テーブル）
# ---------------------------------------------------------------------------
# 9-max MTT、SBR ごとの v5final T_open
T_OPEN_V5_9MAX: dict[int, dict[str, int]] = {
    8:  {'UTG': 24, 'UTG1': 23, 'UTG2': 23, 'LJ': 22, 'HJ': 21, 'CO': 20, 'BTN': 18},
    10: {'UTG': 25, 'UTG1': 24, 'UTG2': 23, 'LJ': 23, 'HJ': 21, 'CO': 21, 'BTN': 18},
    12: {'UTG': 25, 'UTG1': 25, 'UTG2': 23, 'LJ': 23, 'HJ': 23, 'CO': 21, 'BTN': 19, 'SB': 40},
    14: {'UTG': 25, 'UTG1': 25, 'UTG2': 23, 'LJ': 23, 'HJ': 23, 'CO': 21, 'BTN': 19, 'SB': 40},
    17: {'UTG': 24, 'UTG1': 24, 'UTG2': 23, 'LJ': 22, 'HJ': 21, 'CO': 21, 'BTN': 17, 'SB': 34},
    20: {'UTG': 24, 'UTG1': 24, 'UTG2': 22, 'LJ': 22, 'HJ': 21, 'CO': 19, 'BTN': 17, 'SB': 30},
    25: {'UTG': 24, 'UTG1': 23, 'UTG2': 22, 'LJ': 22, 'HJ': 20, 'CO': 19, 'BTN': 16, 'SB': 29},
    40: {'UTG': 24, 'UTG1': 24, 'UTG2': 22, 'LJ': 22, 'HJ': 20, 'CO': 18, 'BTN': 14, 'SB': 29},
}

# タスク仕様で指定された比較対象 SBR
TARGET_SBRS = [25, 20, 17, 12]
# タスク仕様の比較対象ポジション（UTG, LJ, HJ, CO, BTN）
TARGET_POSITIONS = ['UTG', 'LJ', 'HJ', 'CO', 'BTN']


def mtt_ground_truth(sbr: int, pos: str) -> set[str]:
    """v5final + T_open テーブルから定義する MTT GT (open するハンド集合)。"""
    t = T_OPEN_V5_9MAX[sbr][pos]
    hands = all_169_hands()
    return {h for h in hands if score_v5final(h) >= t}


def scenario_b() -> dict[int, dict[str, dict[str, tuple[float, float]]]]:
    """シナリオ B: MTT GTO ground truth に対する各式の精度。

    返り値: {sbr: {pos: {'score_r': (T_best, acc), 'v5final': (T_v5, acc)}}}
    """
    hands = all_169_hands()
    out: dict[int, dict[str, dict[str, tuple[float, float]]]] = {}
    for sbr in TARGET_SBRS:
        out[sbr] = {}
        for pos in TARGET_POSITIONS:
            gt = mtt_ground_truth(sbr, pos)
            # v5final は自身の T_open をそのまま使う（自己整合 = 100%）
            t_v5 = T_OPEN_V5_9MAX[sbr][pos]
            correct_v5 = sum(1 for h in hands if (score_v5final(h) >= t_v5) == (h in gt))
            v5_acc = correct_v5 * 100.0 / len(hands)
            # Score_R は閾値を最適化
            sr_best = best_threshold(score_r, gt, hands)
            out[sbr][pos] = {'score_r': sr_best, 'v5final': (float(t_v5), v5_acc)}
    return out


# ---------------------------------------------------------------------------
# 境界ハンド分析
# ---------------------------------------------------------------------------
def disagreement_hands(sbr: int, pos: str) -> list[str]:
    """同じ MTT GT に対して 2 式の判定が分かれるハンドを列挙。

    各式の閾値は『その式での最適閾値（SR）／T_open テーブル（v5）』。
    """
    gt = mtt_ground_truth(sbr, pos)
    hands = all_169_hands()
    t_v5 = T_OPEN_V5_9MAX[sbr][pos]
    t_sr, _ = best_threshold(score_r, gt, hands)
    disagree = []
    for h in hands:
        pred_sr = score_r(h) >= t_sr
        pred_v5 = score_v5final(h) >= t_v5
        if pred_sr != pred_v5:
            disagree.append(h)
    return disagree


# ---------------------------------------------------------------------------
# 出力ヘルパ
# ---------------------------------------------------------------------------
def fmt_pair(t: float, acc: float) -> str:
    t_str = f'{t:g}'
    return f'{acc:5.1f}% (T={t_str})'


def print_scenario_a(res: dict[str, dict[str, tuple[float, float]]]) -> None:
    print('=== シナリオ A: キャッシュ 6-max GTO ===')
    print(f'{"Pos":<6} {"Score_R":<22} {"v5final (best T)":<22}')
    sr_total, v5_total, n = 0.0, 0.0, 0
    for pos in ['UTG', 'HJ', 'CO', 'BTN', 'SB']:
        sr_t, sr_a = res[pos]['score_r']
        v5_t, v5_a = res[pos]['v5final']
        print(f'{pos:<6} {fmt_pair(sr_t, sr_a):<22} {fmt_pair(v5_t, v5_a):<22}')
        sr_total += sr_a
        v5_total += v5_a
        n += 1
    print(f'{"AVG":<6} {sr_total/n:5.1f}%                {v5_total/n:5.1f}%')
    print()


def print_scenario_b(res: dict[int, dict[str, dict[str, tuple[float, float]]]]) -> None:
    print('=== シナリオ B: MTT GTO (v5final T_open ground truth) ===')
    for sbr in TARGET_SBRS:
        print(f'\nSBR={sbr}:')
        print(f'  {"Pos":<6} {"Score_R (best T)":<22} {"v5final (own T)":<22}')
        sr_sum = v5_sum = 0.0
        n = 0
        for pos in TARGET_POSITIONS:
            if pos not in T_OPEN_V5_9MAX[sbr]:
                continue
            sr_t, sr_a = res[sbr][pos]['score_r']
            v5_t, v5_a = res[sbr][pos]['v5final']
            print(f'  {pos:<6} {fmt_pair(sr_t, sr_a):<22} {fmt_pair(v5_t, v5_a):<22}')
            sr_sum += sr_a
            v5_sum += v5_a
            n += 1
        print(f'  {"AVG":<6} {sr_sum/n:5.1f}%                {v5_sum/n:5.1f}%')


def print_disagreement(sbr: int = 25) -> None:
    print()
    print(f'=== 境界ハンド一覧 (SBR={sbr}、Score_R 最適閾値 vs v5final) ===')
    hands_169 = all_169_hands()
    for pos in TARGET_POSITIONS:
        gt = mtt_ground_truth(sbr, pos)
        t_v5 = T_OPEN_V5_9MAX[sbr][pos]
        t_sr, _ = best_threshold(score_r, gt, hands_169)
        diff = disagreement_hands(sbr, pos)
        # 各ハンドが「GT で open か」「SR 予測」「v5 予測」を表示
        lines = []
        for h in diff:
            in_gt = '○' if h in gt else '×'
            pred_sr = '○' if score_r(h) >= t_sr else '×'
            pred_v5 = '○' if score_v5final(h) >= t_v5 else '×'
            lines.append(f'{h}(SR={score_r(h)}, V5={score_v5final(h)}, GT={in_gt}, SR予測={pred_sr}, V5予測={pred_v5})')
        print(f'\n  {pos} (T_SR={t_sr:g}, T_V5={t_v5}, GT={len(gt)}, 不一致={len(diff)}):')
        if lines:
            for ln in lines:
                print(f'    {ln}')
        else:
            print('    (なし)')


# ---------------------------------------------------------------------------
# 全体平均と推奨
# ---------------------------------------------------------------------------
def overall_summary(
    res_a: dict[str, dict[str, tuple[float, float]]],
    res_b: dict[int, dict[str, dict[str, tuple[float, float]]]],
) -> None:
    print('=== 全体まとめ ===')
    # A 平均
    sr_a = sum(res_a[p]['score_r'][1] for p in res_a) / len(res_a)
    v5_a = sum(res_a[p]['v5final'][1] for p in res_a) / len(res_a)
    print(f'シナリオ A 平均: Score_R={sr_a:.1f}%  v5final={v5_a:.1f}%')

    # B 平均（全 SBR × ポジション）
    sr_b_vals = []
    v5_b_vals = []
    for sbr in res_b:
        for pos in res_b[sbr]:
            sr_b_vals.append(res_b[sbr][pos]['score_r'][1])
            v5_b_vals.append(res_b[sbr][pos]['v5final'][1])
    sr_b = sum(sr_b_vals) / len(sr_b_vals)
    v5_b = sum(v5_b_vals) / len(v5_b_vals)
    print(f'シナリオ B 平均: Score_R={sr_b:.1f}%  v5final={v5_b:.1f}%')

    print()
    print('--- 推奨 ---')
    if v5_b > sr_b + 1.0:
        print(f'MTT には v5final を推奨（B 平均で +{v5_b - sr_b:.1f} ポイント優位）。')
    elif sr_b > v5_b + 1.0:
        print(f'MTT に Score_R が +{sr_b - v5_b:.1f} ポイント優位（B 平均）。')
    else:
        print(f'MTT 平均では両式が拮抗（差 {abs(v5_b - sr_b):.1f}pt 以内）。')


def main() -> None:
    print(f'GTO charts: {GTO_CHARTS_PATH}')
    print(f'Score_R 出典: poker-drill/scripts/generate/core/preflop_score.py')
    print()

    res_a = scenario_a()
    print_scenario_a(res_a)

    res_b = scenario_b()
    print_scenario_b(res_b)

    print_disagreement(sbr=25)

    print()
    overall_summary(res_a, res_b)


if __name__ == '__main__':
    main()
