#!/usr/bin/env python3
"""フロップ後手判断 DS 閾値検証スクリプト.

OOP が IP のフロップ CBet に直面したときの fold/call/raise% を
HandScore バケツ別・ベットサイズ別に集計し、DS 閾値を検証する。

検証目的:
  DS = H − C で fold < 7 / call 7-11 / raise ≥ 12 が正しいか
  BetCost の値 (33%=3, 50%=5, 75%=7) が妥当か

使用方法:
    python3 scripts/phase1_defender.py --board Kc,7d,2s
    python3 scripts/phase1_defender.py --board Kh,Jd,7s
    python3 scripts/phase1_defender.py --board Th,9d,8c
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from hand_evaluator import evaluate, bucket

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
RESULTS_DIR = "/home/cuzic/poker-books/knowledges/volume4/results/phase1"

IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
    "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,"
    "T9s,T8s,T7s,T6s,"
    "98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)

OOP_RANGE = (
    "JJ,TT,99,88,77,66,55,44,33,22,"
    "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AQo,AJo,ATo,A9o,A8o,A7o,A6o,A5o,A4o,A3o,A2o,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "KQo,KJo,KTo,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,Q3s,Q2s,"
    "QJo,QTo,Q9o,Q8o,"
    "JTs,J9s,J8s,J7s,J6s,J5s,J4s,JTo,J9o,J8o,"
    "T9s,T8s,T7s,T6s,T5s,T9o,T8o,"
    "98s,97s,96s,95s,98o,"
    "87s,86s,85s,87o,"
    "76s,75s,74s,76o,"
    "65s,64s,65o,"
    "54s,53s,43s"
)

POT = 7
STACK = 97

# IP ベットサイズ (pot の %)
BET_SIZES_PCT = [33, 50, 75]

# TexasSolver のベット額 = PCT/100 * POT (小数点以下2桁)
def pct_to_chips(pct: int) -> float:
    return round(pct / 100 * POT, 2)

CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,raise,60,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes ip,flop,raise,100,200
set_bet_sizes ip,flop,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 300
set_print_interval 100
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""


def run_solver(board: str, dump_path: str, timeout: int = 360) -> tuple[str, int]:
    config = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board,
        ip_range=IP_RANGE, oop_range=OOP_RANGE, dump_path=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="ts_def_") as f:
        f.write(config)
        cfg_path = f.name

    stdout_file = cfg_path.replace("ts_def_", "ts_def_out_")
    try:
        with open(cfg_path) as fin, open(stdout_file, "w") as fout:
            proc = subprocess.Popen(
                [SOLVER_BIN], stdin=fin, stdout=fout, stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(); rc = -1
    finally:
        try: os.unlink(cfg_path)
        except OSError: pass

    return stdout_file, rc


def parse_oop_defense(result: dict, board: str, bet_size_chips: float) -> dict:
    """OOP の fold/call/raise 率を HandScore バケツ別に集計する.

    JSON パス: root → CHECK → BET {amount} → strategy
    actions: ['FOLD', 'CALL', 'RAISE ...']
    """
    check_node = result.get("childrens", {}).get("CHECK", {})

    # 最近傍 BET キーを選ぶ
    best_key, best_diff = None, float("inf")
    for k in check_node.get("childrens", {}):
        if not k.startswith("BET"):
            continue
        try:
            val = float(k.split()[1])
            diff = abs(val - bet_size_chips)
            if diff < best_diff:
                best_diff, best_key = diff, k
        except (ValueError, IndexError):
            continue

    if best_key is None or best_diff > 2.0:
        return {}

    bet_node = check_node["childrens"][best_key]

    strat_wrapper = bet_node.get("strategy", {})
    combo_strats = strat_wrapper.get("strategy", {})
    actions = strat_wrapper.get("actions", [])

    if not combo_strats or not actions:
        return {}

    # action インデックス
    fold_idx = next((i for i, a in enumerate(actions) if a == "FOLD"), None)
    call_idx = next((i for i, a in enumerate(actions) if a == "CALL"), None)
    raise_idxs = [i for i, a in enumerate(actions) if "RAISE" in a or "ALLIN" in a]

    # バケツ別集計
    bucket_stats: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"fold": [], "call": [], "raise": []}
    )

    board_str = board.replace(",", "").replace(" ", "")
    # board は "Kc,7d,2s" 形式でも "Kc7d2s" 形式でも OK
    board_norm = ",".join(board_str[i:i+2] for i in range(0, len(board_str), 2))

    for combo, probs in combo_strats.items():
        try:
            score, _ = evaluate(combo, board_norm)
            b = bucket(score)
        except Exception:
            continue

        f_prob = probs[fold_idx] if fold_idx is not None and fold_idx < len(probs) else 0.0
        c_prob = probs[call_idx] if call_idx is not None and call_idx < len(probs) else 0.0
        r_prob = sum(probs[i] for i in raise_idxs if i < len(probs))

        bucket_stats[b]["fold"].append(f_prob)
        bucket_stats[b]["call"].append(c_prob)
        bucket_stats[b]["raise"].append(r_prob)

    result_rows = {}
    for b, stats in bucket_stats.items():
        n = len(stats["fold"])
        if n == 0:
            continue
        result_rows[b] = {
            "n": n,
            "fold_pct": round(sum(stats["fold"]) / n * 100, 1),
            "call_pct": round(sum(stats["call"]) / n * 100, 1),
            "raise_pct": round(sum(stats["raise"]) / n * 100, 1),
        }
    return result_rows


def board_to_slug(board: str) -> str:
    return board.replace(",", "").replace(" ", "").lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="フロップ後手判断 DS 閾値検証")
    parser.add_argument("--board", default="Kc,7d,2s", help="ボード (例: Kc,7d,2s)")
    parser.add_argument("--no-solve", action="store_true", help="既存 JSON を再利用")
    args = parser.parse_args()

    board = args.board
    slug = board_to_slug(board)
    out_dir = os.path.join(RESULTS_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "defender_result.json")

    if not args.no_solve or not os.path.exists(json_path):
        print(f"[Solving] board={board} ...", file=sys.stderr)
        _, rc = run_solver(board, json_path)
        if rc not in (0, -6) or not os.path.exists(json_path):
            print(f"ERROR: solver failed (rc={rc})", file=sys.stderr)
            sys.exit(1)
        print("[Done]", file=sys.stderr)
    else:
        print(f"[Reusing] {json_path}", file=sys.stderr)

    with open(json_path) as f:
        result = json.load(f)

    print(f"\n=== OOP 後手判断: {board} ===")
    print(f"{'サイズ':>6}  {'バケツ':>4}  {'N':>5}  {'Fold%':>6}  {'Call%':>6}  {'Raise%':>7}  DS閾値確認")
    print("-" * 70)

    bet_cost_map = {33: 3, 50: 5, 75: 7}

    for pct in BET_SIZES_PCT:
        chips = pct_to_chips(pct)
        rows = parse_oop_defense(result, board, chips)
        if not rows:
            print(f"  {pct}%: BET キーが見つかりません (利用可能: ...)")
            continue

        cost: int = bet_cost_map.get(pct, 0)
        for b in ["H3", "H2", "H1"]:
            if b not in rows:
                continue
            r = rows[b]
            h_center = {"H3": 17, "H2": 11, "H1": 4}[b]
            ds = h_center - cost
            expected = "raise" if ds >= 12 else ("call" if ds >= 7 else "fold")
            actual_max = max(r["fold_pct"], r["call_pct"], r["raise_pct"])
            actual_action = (
                "raise" if r["raise_pct"] == actual_max else
                ("call" if r["call_pct"] == actual_max else "fold")
            )
            match = "✓" if expected == actual_action else "✗"
            print(
                f"  {pct}%  {b}  N={r['n']:4d}  "
                f"Fold={r['fold_pct']:5.1f}%  Call={r['call_pct']:5.1f}%  Raise={r['raise_pct']:5.1f}%"
                f"  DS≈{ds} expect={expected} {match}"
            )

    # 結果を CSV 保存
    csv_path = os.path.join(out_dir, "defender_summary.csv")
    with open(csv_path, "w") as f:
        f.write("board,bet_pct,bucket,n,fold_pct,call_pct,raise_pct\n")
        for pct in BET_SIZES_PCT:
            chips = pct_to_chips(pct)
            rows = parse_oop_defense(result, board, chips)
            for b, r in rows.items():
                f.write(f"{board},{pct},{b},{r['n']},{r['fold_pct']},{r['call_pct']},{r['raise_pct']}\n")
    print(f"\n結果を保存: {csv_path}")


if __name__ == "__main__":
    main()
