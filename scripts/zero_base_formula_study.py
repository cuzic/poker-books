#!/usr/bin/env python3
"""ゼロベースフロップ戦略回帰分析スクリプト.

30ボードをTexasSolverで解析し、既存16ボードのキャッシュと合わせて
合計46ボードに対して回帰分析を行い、CBet率・BBフォールド率の予測式を導出する。

Usage:
    python3 scripts/zero_base_formula_study.py

出力:
    knowledges/flop/results/zero_base_study/ に各ボードのJSONを保存
    最終レポートをコンソールに出力
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# ─── 設定 ──────────────────────────────────────────────────────────────────
SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
OUT_DIR     = Path("/home/cuzic/poker-books/knowledges/flop/results/zero_base_study")
CACHE_DIR1  = Path("/home/cuzic/poker-books/knowledges/flop/results/boundary_analysis")
CACHE_DIR2  = Path("/home/cuzic/poker-books/knowledges/flop/results/boundary_analysis2")

POT   = 7
STACK = 97

IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,"
    "JTs,JTo,J9s,J8s,J7s,"
    "T9s,T8s,T7s,"
    "98s,97s,"
    "87s,86s,"
    "76s,75s,"
    "65s,54s"
)

OOP_RANGE = (
    "JJ,TT,99,88,77,66,55,44,33,22,"
    "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AQo,AJo,ATo,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "KQo,KJo,KTo,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,"
    "QJo,QTo,"
    "JTs,J9s,J8s,"
    "JTo,"
    "T9s,T8s,T7s,"
    "T9o,"
    "98s,97s,96s,"
    "87s,86s,"
    "76s,75s,"
    "65s,54s,43s"
)

CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes ip,flop,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 400
set_print_interval 100
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""

IP_BET_SIZES = {
    "33": 2.0,
    "50": 4.0,
    "75": 5.0,
}

RANK_MAP = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
}

# ─── 新規30ボード ────────────────────────────────────────────────────────────
NEW_BOARDS = [
    # Group 1: top card series（2nd=7, 3rd=2, topだけ変化）
    ("Ac,7d,2h", "A72r"),
    ("Tc,7d,2h", "T72r"),
    ("9c,7d,2h", "972r"),
    ("8c,7d,2h", "872r"),

    # Group 2: A topでspread変化
    ("Ac,Kd,Qh", "AKQr"),
    ("Ac,Kd,9h", "AK9r"),
    ("Ac,9d,2h", "A92r"),
    ("Ac,8d,2h", "A82r"),

    # Group 3: K topで2nd card変化
    ("Kc,Qd,2h", "KQ2r"),
    ("Kc,Qd,Jh", "KQJr"),
    ("Kc,7d,2h", "K72r"),

    # Group 4: J/T topでlow board
    ("Jc,6d,2h", "J62r"),
    ("Tc,9d,8h", "T98r"),
    ("9c,6d,2h", "962r"),
    ("8c,5d,2h", "852r"),
    ("7c,5d,3h", "753r"),
    ("6c,4d,2h", "642r"),

    # Group 5: 2-tone
    ("Kc,7d,2c", "K72t"),
    ("Jc,7d,2c", "J72t"),
    ("9c,6d,2c", "962t"),
    ("Ac,9d,2c", "A92t"),

    # Group 6: monotone
    ("Ac,9c,3c", "A93m"),
    ("Kc,7c,2c", "K72m"),
    ("9c,6c,2c", "962m"),

    # Group 7: paired
    ("Jc,Jd,9h", "JJ9r"),
    ("Jc,Jd,2h", "JJ2r"),
    ("9c,9d,2h", "992r"),
    ("7c,7d,2h", "772r"),
    ("Ac,5d,5h", "A55r"),
    ("Kc,5d,5h", "K55r"),
]

# ─── 既存16ボードのキャッシュ情報 ─────────────────────────────────────────────
# boundary_analysis (6ボード)
CACHE1_SLUGS = {
    "j72r": (CACHE_DIR1, "Jc,7d,2h"),
    "k83r": (CACHE_DIR1, "Kc,8d,3h"),
    "k93r": (CACHE_DIR1, "Kc,9d,3h"),
    "q72r": (CACHE_DIR1, "Qc,7d,2h"),
    "qq7r": (CACHE_DIR1, "Qc,Qd,7h"),
    "qq8r": (CACHE_DIR1, "Qc,Qd,8h"),
}
# boundary_analysis2 (10ボード)
CACHE2_SLUGS = {
    "a93":  (CACHE_DIR2, "Ac,9d,3h"),
    "aa2":  (CACHE_DIR2, "Ac,Ad,2h"),
    "aak":  (CACHE_DIR2, "Ac,Ad,Kh"),
    "at3":  (CACHE_DIR2, "Ac,Td,3h"),
    "j52":  (CACHE_DIR2, "Jc,5d,2h"),
    "kk4":  (CACHE_DIR2, "Kc,Kd,4h"),
    "kkt":  (CACHE_DIR2, "Kc,Kd,Th"),
    "q52":  (CACHE_DIR2, "Qc,5d,2h"),
    "t52":  (CACHE_DIR2, "Tc,5d,2h"),
    "t62":  (CACHE_DIR2, "Tc,6d,2h"),
}


# ─── ソルバー実行 ────────────────────────────────────────────────────────────
def run_solver(board: str, dump_path: str, timeout: int = 600) -> int:
    config = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board,
        ip_range=IP_RANGE, oop_range=OOP_RANGE,
        dump_path=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(config)
        cfg = f.name
    try:
        with open(cfg) as fin:
            proc = subprocess.Popen(
                [SOLVER_BIN], stdin=fin,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
            )
            try:
                return proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(); return -1
    finally:
        try:
            os.unlink(cfg)
        except OSError:
            pass


# ─── ボード情報 ──────────────────────────────────────────────────────────────
def board_ranks(board: str) -> list[int]:
    return sorted([RANK_MAP[c[0].upper()] for c in board.split(",")], reverse=True)


def board_suits(board: str) -> list[str]:
    return [c[1].lower() for c in board.split(",")]


def board_rank_set(board: str) -> set[int]:
    return set(RANK_MAP[c[0].upper()] for c in board.split(","))


def is_paired_board(board: str) -> bool:
    ranks = board_ranks(board)
    return len(set(ranks)) < len(ranks)


# ─── ノード取得ヘルパー ─────────────────────────────────────────────────────
def get_ip_cbet_node(raw: dict) -> dict | None:
    return raw.get("childrens", {}).get("CHECK")


def find_best_bet_node(children: dict, target_amt: float, tolerance: float = 1.5) -> tuple[str | None, dict | None]:
    best_key = None
    best_node = None
    best_diff = float("inf")
    for key, node in children.items():
        if not key.startswith("BET"):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        diff = abs(amt - target_amt)
        if diff < tolerance and diff < best_diff:
            best_diff = diff
            best_key = key
            best_node = node
    return best_key, best_node


# ─── IP CBet 率の計算 ────────────────────────────────────────────────────────
def compute_ip_cbet_total(raw: dict) -> dict:
    ip_node = get_ip_cbet_node(raw)
    if ip_node is None:
        return {"error": "CHECK node not found"}

    strat = ip_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        chk_idx = actions.index("CHECK")
    except ValueError:
        return {"error": "CHECK not in actions"}

    action_totals = [0.0] * len(actions)
    n_combos = 0
    for combo, probs in combos.items():
        n_combos += 1
        for i, p in enumerate(probs):
            if i < len(action_totals):
                action_totals[i] += p

    if n_combos == 0:
        return {"error": "no combos"}

    avg_probs = [t / n_combos for t in action_totals]
    check_pct = avg_probs[chk_idx] * 100

    bet_probs: dict[str, float] = {}
    for i, act in enumerate(actions):
        if act.startswith("BET"):
            bet_probs[act] = avg_probs[i] * 100

    total_cbet = sum(bet_probs.values())
    top_bet = max(bet_probs, key=bet_probs.get) if bet_probs else None

    top_size_label = "?"
    if top_bet:
        try:
            amt = float(top_bet.split()[1])
            if amt >= STACK * 0.9:
                top_size_label = "allin"
            elif abs(amt - IP_BET_SIZES["33"]) <= 0.5:
                top_size_label = "33%(BET2)"
            elif abs(amt - IP_BET_SIZES["50"]) <= 0.5:
                top_size_label = "50%(BET4)"
            elif abs(amt - IP_BET_SIZES["75"]) <= 0.5:
                top_size_label = "75%(BET5)"
            else:
                approx_pct = round(amt / POT * 100)
                top_size_label = f"{approx_pct}%pot"
        except (IndexError, ValueError):
            pass

    return {
        "total_cbet_pct": round(total_cbet, 1),
        "check_pct": round(check_pct, 1),
        "bet_breakdown": {k: round(v, 1) for k, v in bet_probs.items()},
        "top_bet_key": top_bet,
        "top_bet_label": top_size_label,
        "n_combos": n_combos,
    }


# ─── BB フォールド率の計算 ───────────────────────────────────────────────────
def compute_bb_fold_vs_cbet(raw: dict, config_pct: int) -> dict:
    ip_node = get_ip_cbet_node(raw)
    if ip_node is None:
        return {"error": "CHECK node not found"}

    target_amt = IP_BET_SIZES.get(str(config_pct), POT * config_pct / 100.0)
    key, bet_node = find_best_bet_node(ip_node.get("childrens", {}), target_amt)

    if bet_node is None:
        all_bet_keys = [k for k in ip_node.get("childrens", {}) if k.startswith("BET")]
        if not all_bet_keys:
            return {"error": f"no BET nodes under CHECK", "config_pct": config_pct}
        all_bet_keys.sort(key=lambda k: abs(float(k.split()[1]) - target_amt))
        key = all_bet_keys[0]
        bet_node = ip_node["childrens"][key]

    strat = bet_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        fold_idx = actions.index("FOLD")
    except ValueError:
        return {"error": f"FOLD not in {actions}", "key_used": key}

    folds = []
    for combo, probs in combos.items():
        if fold_idx < len(probs):
            folds.append(probs[fold_idx])

    if not folds:
        return {"error": "no combos", "key_used": key}

    avg_fold = sum(folds) / len(folds)
    return {
        "key_used": key,
        "actual_bet_amt": float(key.split()[1]),
        "avg_fold_pct": round(avg_fold * 100, 1),
        "n_combos": len(folds),
    }


# ─── ハンド強度別 CBet 率 ─────────────────────────────────────────────────────
def classify_combo(combo: str, board: str) -> str:
    b_ranks = board_ranks(board)
    b_rank_set = board_rank_set(board)
    b_is_paired = is_paired_board(board)

    r0 = RANK_MAP.get(combo[0].upper(), 0)
    r1 = RANK_MAP.get(combo[2].upper(), 0)
    is_pocket_pair = (r0 == r1)
    top_board = b_ranks[0]
    mid_board = b_ranks[1] if len(b_ranks) > 1 else 0

    if b_is_paired:
        pair_rank = next(r for r in b_ranks if b_ranks.count(r) >= 2)
        if r0 == pair_rank or r1 == pair_rank:
            return "trips"
        if is_pocket_pair and r0 > pair_rank:
            return "overpair"
        if is_pocket_pair and r0 == pair_rank:
            return "top_set"
        if is_pocket_pair and r0 < pair_rank:
            return "underpair"
        non_pair_ranks = [r for r in b_ranks if r != pair_rank]
        if non_pair_ranks:
            top_non_pair = non_pair_ranks[0]
            if r0 == top_non_pair or r1 == top_non_pair:
                return "top_pair"
        return "air"

    if is_pocket_pair and r0 in b_rank_set:
        return "set"
    if is_pocket_pair and r0 > top_board:
        return "overpair"
    if is_pocket_pair and r0 < top_board and r0 not in b_rank_set:
        return "underpair"

    hits_top = (r0 == top_board or r1 == top_board)
    if hits_top:
        top_kicker = max(r for r in [r0, r1] if r != top_board) if r0 != r1 else top_board
        if top_kicker >= 10:
            return "tptk"
        return "top_pair"

    hits_mid = (r0 == mid_board or r1 == mid_board)
    if hits_mid:
        return "middle_pair"

    if r0 > top_board and r1 > top_board and not is_pocket_pair:
        return "2oc"

    return "air"


def compute_cbet_by_category(raw: dict, board: str) -> dict[str, dict]:
    ip_node = get_ip_cbet_node(raw)
    if ip_node is None:
        return {}
    strat = ip_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        chk_idx = actions.index("CHECK")
    except ValueError:
        return {}

    categories: dict[str, list[float]] = {}
    for combo, probs in combos.items():
        cat = classify_combo(combo, board)
        cbet = 1.0 - probs[chk_idx] if chk_idx < len(probs) else 1.0
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(cbet)

    result: dict[str, dict] = {}
    for cat, vals in categories.items():
        result[cat] = {
            "avg_cbet_pct": round(sum(vals) / len(vals) * 100, 1),
            "n": len(vals),
        }
    return result


# ─── ボード解析 ──────────────────────────────────────────────────────────────
def analyze_board_from_raw(raw: Any, board: str, slug: str) -> dict:
    cbet_info = compute_ip_cbet_total(raw)
    bb_fold_33 = compute_bb_fold_vs_cbet(raw, 33)
    bb_fold_75 = compute_bb_fold_vs_cbet(raw, 75)
    cat_cbet   = compute_cbet_by_category(raw, board)

    return {
        "board": board,
        "slug": slug,
        "cbet": cbet_info,
        "bb_fold_vs_33pct": bb_fold_33,
        "bb_fold_vs_75pct": bb_fold_75,
        "cbet_by_category": cat_cbet,
    }


def analyze_board(board: str, slug: str) -> dict:
    dump_path = OUT_DIR / f"{slug}.json"
    analysis_path = OUT_DIR / f"{slug}_analysis.json"

    if analysis_path.exists():
        print(f"  キャッシュ済み (分析): {analysis_path}")
        return json.loads(analysis_path.read_text())

    if dump_path.exists():
        print(f"  キャッシュ済み (raw): {dump_path}")
    else:
        print(f"  TexasSolver 実行中 (Board: {board}) ...")
        t0 = time.time()
        rc = run_solver(board, str(dump_path))
        elapsed = time.time() - t0
        if rc != 0 or not dump_path.exists():
            print(f"  ERROR: solver rc={rc}")
            return {}
        print(f"  完了: {elapsed:.0f}s")

    raw = json.loads(dump_path.read_text())
    result = analyze_board_from_raw(raw, board, slug)
    analysis_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result


# ─── 既存キャッシュ読み込み ──────────────────────────────────────────────────
def load_cached_boards() -> list[dict]:
    """既存16ボードのanalysis JSONを読み込む."""
    results = []
    all_caches = {**CACHE1_SLUGS, **CACHE2_SLUGS}
    for slug, (cache_dir, board) in all_caches.items():
        analysis_file = cache_dir / f"{slug}_analysis.json"
        if analysis_file.exists():
            d = json.loads(analysis_file.read_text())
            results.append(d)
            print(f"  既存キャッシュ読み込み: {slug} ({board})")
        else:
            print(f"  WARNING: キャッシュ不在: {analysis_file}")
    return results


# ─── 特徴量抽出 ──────────────────────────────────────────────────────────────
def extract_features(board: str, slug: str) -> dict:
    """ボードの特徴量を抽出する."""
    ranks = board_ranks(board)
    suits = board_suits(board)
    top_rank = ranks[0]
    mid_rank = ranks[1] if len(ranks) > 1 else 0
    low_rank  = ranks[2] if len(ranks) > 2 else 0

    spread   = top_rank - low_rank
    top_diff = top_rank - mid_rank
    mid_diff = mid_rank - low_rank

    # スーツ情報
    suit_counts: dict[str, int] = {}
    for s in suits:
        suit_counts[s] = suit_counts.get(s, 0) + 1
    max_suit = max(suit_counts.values())
    is_monotone = (max_suit == 3)
    is_2tone    = (max_suit == 2)

    # ペアボード
    rank_counts: dict[int, int] = {}
    for r in ranks:
        rank_counts[r] = rank_counts.get(r, 0) + 1
    is_paired = any(v >= 2 for v in rank_counts.values())
    pair_rank   = 0
    kicker_rank = 0
    if is_paired:
        pair_rank = max(r for r, cnt in rank_counts.items() if cnt >= 2)
        non_pair_ranks = [r for r in ranks if r != pair_rank]
        kicker_rank = non_pair_ranks[0] if non_pair_ranks else 0

    # 派生特徴量
    density_wet   = 1 if spread <= 2 else 0
    high_connected = 1 if (top_rank >= 10 and top_diff <= 4) else 0
    top_is_high   = 1 if top_rank >= 12 else 0
    top_ge_T      = 1 if top_rank >= 10 else 0

    return {
        "slug":        slug,
        "board":       board,
        "top_rank":    top_rank,
        "mid_rank":    mid_rank,
        "low_rank":    low_rank,
        "spread":      spread,
        "top_diff":    top_diff,
        "mid_diff":    mid_diff,
        "is_2tone":    1 if is_2tone else 0,
        "is_monotone": 1 if is_monotone else 0,
        "is_paired":   1 if is_paired else 0,
        "pair_rank":   pair_rank,
        "kicker_rank": kicker_rank,
        "density_wet":    density_wet,
        "high_connected":  high_connected,
        "top_is_high":    top_is_high,
        "top_ge_T":       top_ge_T,
    }


def build_board_stats(analysis: dict, features: dict) -> dict:
    """解析結果と特徴量を統合する."""
    cbet = analysis.get("cbet", {})
    fold33 = analysis.get("bb_fold_vs_33pct", {})
    fold75 = analysis.get("bb_fold_vs_75pct", {})
    cat    = analysis.get("cbet_by_category", {})

    breakdown = cbet.get("bet_breakdown", {})
    btn_cbet_33 = 0.0
    btn_cbet_50 = 0.0
    btn_cbet_75 = 0.0
    for key, val in breakdown.items():
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        if abs(amt - 2.0) <= 0.5:
            btn_cbet_33 += val
        elif abs(amt - 4.0) <= 0.5:
            btn_cbet_50 += val
        elif abs(amt - 5.0) <= 0.5:
            btn_cbet_75 += val

    stats = {**features}
    stats["btn_cbet_pct"]       = cbet.get("total_cbet_pct", float("nan"))
    stats["btn_cbet_33"]        = round(btn_cbet_33, 1)
    stats["btn_cbet_50"]        = round(btn_cbet_50, 1)
    stats["btn_cbet_75"]        = round(btn_cbet_75, 1)
    stats["btn_check"]          = cbet.get("check_pct", float("nan"))
    stats["bb_fold_vs33"]       = fold33.get("avg_fold_pct", float("nan"))
    stats["bb_fold_vs75"]       = fold75.get("avg_fold_pct", float("nan"))
    stats["air_cbet_pct"]       = cat.get("air",      {}).get("avg_cbet_pct", float("nan"))
    stats["overpair_cbet_pct"]  = cat.get("overpair", {}).get("avg_cbet_pct", float("nan"))
    stats["underpair_cbet_pct"] = cat.get("underpair",{}).get("avg_cbet_pct", float("nan"))
    return stats


# ─── 回帰分析 ────────────────────────────────────────────────────────────────
def pearson_r(x: list[float], y: list[float]) -> float:
    n = len(x)
    if n < 2:
        return float("nan")
    mx = sum(x) / n
    my = sum(y) / n
    num   = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den_x = sum((xi - mx) ** 2 for xi in x) ** 0.5
    den_y = sum((yi - my) ** 2 for yi in y) ** 0.5
    if den_x == 0 or den_y == 0:
        return float("nan")
    return num / (den_x * den_y)


def t_statistic(r: float, n: int) -> float:
    if abs(r) >= 1.0 or n <= 2:
        return float("nan")
    return r * ((n - 2) ** 0.5) / ((1 - r * r) ** 0.5)


def multiple_regression(X_rows: list[list[float]], y: list[float]) -> tuple[list[float], float]:
    """OLS回帰. numpy.linalg.lstsq を使用. 戻り値: (coeffs_with_intercept, R2)"""
    import numpy as np
    n = len(y)
    # バイアス項を追加
    A = [[1.0] + row for row in X_rows]
    A_arr = np.array(A)
    y_arr = np.array(y)
    coeffs, residuals, rank, sv = np.linalg.lstsq(A_arr, y_arr, rcond=None)
    y_pred = A_arr @ coeffs
    ss_res = float(np.sum((y_arr - y_pred) ** 2))
    ss_tot = float(np.sum((y_arr - y_arr.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    rmse = (ss_res / n) ** 0.5
    return list(coeffs), r2, rmse


# ─── レポート出力 ────────────────────────────────────────────────────────────
FEATURE_NAMES = [
    "top_rank", "spread", "top_diff", "mid_diff",
    "is_2tone", "is_monotone", "is_paired",
    "density_wet", "high_connected", "top_is_high", "top_ge_T",
    "kicker_rank",
]


def run_regression(all_stats: list[dict], target_key: str, label: str) -> None:
    # NaN を除外
    valid = [s for s in all_stats if not (s[target_key] != s[target_key])]
    n = len(valid)
    y = [s[target_key] for s in valid]

    print(f"\n{'='*65}")
    print(f"=== {label} (n={n}) ===")
    print(f"{'='*65}")

    # 単変量相関
    print("\n【単変量Pearson相関係数】")
    corr_list = []
    for feat in FEATURE_NAMES:
        x = [s.get(feat, 0.0) for s in valid]
        r = pearson_r(x, y)
        t = t_statistic(r, n)
        sig = ""
        if abs(t) > 2.0:
            sig = " *"
        if abs(t) > 3.0:
            sig = " **"
        print(f"  {feat:<20}: r = {r:+.3f}  (t={t:+.2f}){sig}")
        corr_list.append((feat, r, t))

    # 重回帰
    X_rows = [[s.get(f, 0.0) for f in FEATURE_NAMES] for s in valid]
    try:
        coeffs, r2, rmse = multiple_regression(X_rows, y)
        print(f"\n【重回帰モデル】")
        print(f"  {target_key} ≈ {coeffs[0]:.2f}")
        for i, feat in enumerate(FEATURE_NAMES):
            c = coeffs[i + 1]
            if abs(c) > 0.01:
                print(f"    + ({c:+.3f}) × {feat}")
        print(f"  R² = {r2:.3f},  RMSE = {rmse:.2f}%")

        # 寄与度ランキング（係数の絶対値 × 標準偏差）
        import numpy as np
        arr = np.array([[s.get(f, 0.0) for f in FEATURE_NAMES] for s in valid])
        stds = arr.std(axis=0)
        impact = [abs(coeffs[i + 1]) * stds[i] for i in range(len(FEATURE_NAMES))]
        ranked = sorted(zip(FEATURE_NAMES, impact, coeffs[1:]), key=lambda x: x[1], reverse=True)
        print(f"\n【寄与度ランキング (|coeff| × std)】")
        for rank_i, (feat, imp, coef) in enumerate(ranked[:8], 1):
            print(f"  #{rank_i:d}  {feat:<20}  impact={imp:.2f}  coeff={coef:+.3f}")

    except Exception as e:
        print(f"  重回帰エラー: {e}")


# ─── CSV出力 ─────────────────────────────────────────────────────────────────
def print_csv_table(all_stats: list[dict]) -> None:
    print("\n\n" + "="*120)
    print("【表1: 全ボードデータ一覧 (CSV形式)】")
    print("="*120)
    cols = ["slug", "board", "top_rank", "mid_rank", "low_rank", "spread",
            "top_diff", "mid_diff", "is_2tone", "is_monotone", "is_paired",
            "pair_rank", "kicker_rank", "density_wet", "high_connected",
            "top_is_high", "top_ge_T",
            "btn_cbet_pct", "btn_cbet_33", "btn_cbet_50", "btn_cbet_75", "btn_check",
            "bb_fold_vs33", "bb_fold_vs75",
            "air_cbet_pct", "overpair_cbet_pct", "underpair_cbet_pct"]
    print(",".join(cols))
    for s in sorted(all_stats, key=lambda x: x["slug"]):
        row = []
        for c in cols:
            v = s.get(c, "")
            if isinstance(v, float) and v != v:  # NaN
                row.append("")
            elif isinstance(v, float):
                row.append(f"{v:.1f}")
            else:
                row.append(str(v))
        print(",".join(row))


# ─── メイン ─────────────────────────────────────────────────────────────────
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"ゼロベースフロップ戦略回帰分析")
    print(f"pot={POT}, stack={STACK}, accuracy=0.5, max_iter=400")
    print(f"出力先: {OUT_DIR}")
    print()

    # ─── 既存16ボードを読み込む ─────────────────────────────────
    print("[Step 1] 既存キャッシュ読み込み")
    cached = load_cached_boards()
    cached_slugs = {d["slug"] for d in cached}
    print(f"  既存ボード数: {len(cached)}")
    print()

    # ─── 新規30ボードを解析 ─────────────────────────────────────
    print("[Step 2] 新規30ボード解析")
    new_results = []
    for board, slug in NEW_BOARDS:
        if slug.lower() in cached_slugs:
            print(f"  スキップ(既存): {slug}")
            continue
        print(f"[{slug}] {board}")
        r = analyze_board(board, slug)
        if r:
            new_results.append(r)
    print(f"  新規解析完了: {len(new_results)} ボード")
    print()

    # ─── 全ボードを統合 ─────────────────────────────────────────
    all_analyses = cached + new_results
    print(f"[Step 3] 合計 {len(all_analyses)} ボードを回帰分析")

    all_stats = []
    for analysis in all_analyses:
        board = analysis["board"]
        slug  = analysis["slug"]
        feats = extract_features(board, slug)
        stats = build_board_stats(analysis, feats)
        all_stats.append(stats)

    # ─── CSV出力 ──────────────────────────────────────────────
    print_csv_table(all_stats)

    # ─── 回帰分析 ─────────────────────────────────────────────
    run_regression(all_stats, "btn_cbet_pct",  "BTN CBet率の予測")
    run_regression(all_stats, "bb_fold_vs75",  "BB Fold率（vs75%CBet）の予測")
    run_regression(all_stats, "air_cbet_pct",  "エアハンドCBet率の予測")

    # ─── サマリーJSON保存 ─────────────────────────────────────
    summary_path = OUT_DIR / "regression_summary.json"
    summary_path.write_text(json.dumps(all_stats, indent=2, ensure_ascii=False))
    print(f"\n\n集計JSON: {summary_path}")
    print(f"合計ボード数: {len(all_stats)}")


if __name__ == "__main__":
    main()
