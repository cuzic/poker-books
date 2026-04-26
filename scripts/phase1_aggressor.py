#!/usr/bin/env python3
"""フロップ先手判断 AS 閾値検証スクリプト.

IP が OOP チェック後にベット vs チェックバックを選ぶ頻度を
HandScore バケツ別・ボードタイプ別に集計し、AS 閾値と 3×3 マトリックスを検証する。

検証目的:
  AS = H + A で ≥12 → ベット / <9 → チェック が正しいか
  3×3 マトリックス (H3/H2/H1 × dry/semi/wet) の各セルを実測

使用方法:
    python3 scripts/phase1_aggressor.py --board Kc,7d,2s --board-type dry
    python3 scripts/phase1_aggressor.py --board Kh,Jd,7s --board-type semi
    python3 scripts/phase1_aggressor.py --board Th,9d,8c --board-type wet

既存 JSON を再利用 (phase1_defender.py で生成済みの場合):
    python3 scripts/phase1_aggressor.py --board Kc,7d,2s --no-solve
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

BOARD_TYPE_A = {"dry": 3, "semi": 2, "wet": 1}

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


def run_solver(board: str, dump_path: str, timeout: int = 360) -> int:
    config = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board,
        ip_range=IP_RANGE, oop_range=OOP_RANGE, dump_path=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="ts_agg_") as f:
        f.write(config)
        cfg_path = f.name

    try:
        with open(cfg_path) as fin, open(os.devnull, "w") as devnull:
            proc = subprocess.Popen(
                [SOLVER_BIN], stdin=fin, stdout=devnull, stderr=devnull,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(); rc = -1
    finally:
        try: os.unlink(cfg_path)
        except OSError: pass

    return rc


def parse_ip_aggression(result: dict, board: str) -> dict:
    """IP の ベット vs チェックバック 頻度を HandScore バケツ別・サイズ別に集計する.

    JSON パス: root → CHECK → strategy
    actions: ['CHECK', 'BET X', 'BET Y', ...]
    """
    check_node = result.get("childrens", {}).get("CHECK", {})
    strat_wrapper = check_node.get("strategy", {})
    combo_strats = strat_wrapper.get("strategy", {})
    actions = strat_wrapper.get("actions", [])

    if not combo_strats:
        return {}

    check_idx = next((i for i, a in enumerate(actions) if a == "CHECK"), None)
    bet_idxs = {a: i for i, a in enumerate(actions) if a.startswith("BET")}

    # ベットサイズ → pot% のマッピング
    def chips_to_pct(chips_str: str) -> int:
        try:
            chips = float(chips_str.split()[1])
            return round(chips / POT * 100)
        except (IndexError, ValueError):
            return 0

    board_norm = ",".join(
        board.replace(",", "").replace(" ", "")[i:i+2]
        for i in range(0, len(board.replace(",", "").replace(" ", "")), 2)
    )

    bucket_stats: dict[str, dict] = defaultdict(
        lambda: {"check": [], "bet_33": [], "bet_50": [], "bet_75": [], "bet_other": []}
    )

    for combo, probs in combo_strats.items():
        try:
            score, _ = evaluate(combo, board_norm)
            b = bucket(score)
        except Exception:
            continue

        c_prob = probs[check_idx] if check_idx is not None and check_idx < len(probs) else 0.0
        bucket_stats[b]["check"].append(c_prob)

        for bet_action, bet_idx in bet_idxs.items():
            pct = chips_to_pct(bet_action)
            p = probs[bet_idx] if bet_idx < len(probs) else 0.0
            if 25 <= pct <= 40:
                bucket_stats[b]["bet_33"].append(p)
            elif 41 <= pct <= 60:
                bucket_stats[b]["bet_50"].append(p)
            elif 61 <= pct <= 90:
                bucket_stats[b]["bet_75"].append(p)
            else:
                bucket_stats[b]["bet_other"].append(p)

    result_rows = {}
    for b, stats in bucket_stats.items():
        n = len(stats["check"])
        if n == 0:
            continue

        def avg(lst: list) -> float:
            return round(sum(lst) / max(len(lst), 1) * 100, 1)

        result_rows[b] = {
            "n": n,
            "check_pct": avg(stats["check"]),
            "bet_33_pct": avg(stats["bet_33"]),
            "bet_50_pct": avg(stats["bet_50"]),
            "bet_75_pct": avg(stats["bet_75"]),
            "bet_total_pct": round(100 - avg(stats["check"]), 1),
        }
    return result_rows


def board_to_slug(board: str) -> str:
    return board.replace(",", "").replace(" ", "").lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="フロップ先手判断 AS 閾値検証")
    parser.add_argument("--board", default="Kc,7d,2s")
    parser.add_argument("--board-type", default="dry", choices=["dry", "semi", "wet"])
    parser.add_argument("--no-solve", action="store_true", help="既存 JSON を再利用")
    args = parser.parse_args()

    board = args.board
    board_type = args.board_type
    A = BOARD_TYPE_A[board_type]
    slug = board_to_slug(board)
    out_dir = os.path.join(RESULTS_DIR, slug)
    os.makedirs(out_dir, exist_ok=True)

    # phase1_defender.py と同じ JSON を共有する
    json_path = os.path.join(out_dir, "defender_result.json")

    if not args.no_solve or not os.path.exists(json_path):
        print(f"[Solving] board={board} ...", file=sys.stderr)
        rc = run_solver(board, json_path)
        if rc not in (0, -6) or not os.path.exists(json_path):
            print(f"ERROR: solver failed (rc={rc})", file=sys.stderr)
            sys.exit(1)
        print("[Done]", file=sys.stderr)
    else:
        print(f"[Reusing] {json_path}", file=sys.stderr)

    with open(json_path) as f:
        result = json.load(f)

    rows = parse_ip_aggression(result, board)

    print(f"\n=== IP 先手判断: {board} (BoardType={board_type}, A={A}) ===")
    print(f"{'バケツ':>4}  {'N':>5}  {'Check%':>7}  {'Bet(合計)%':>10}  "
          f"{'33%':>6}  {'50%':>6}  {'75%':>6}  AS閾値確認")
    print("-" * 80)

    h_center = {"H3": 17, "H2": 11, "H1": 4}
    for b in ["H3", "H2", "H1"]:
        if b not in rows:
            continue
        r = rows[b]
        H = h_center[b]
        AS = H + A
        expected_bet = AS >= 9
        actual_bet = r["bet_total_pct"] >= 50
        match = "✓" if expected_bet == actual_bet else "✗"
        print(
            f"  {b}  N={r['n']:4d}  "
            f"Check={r['check_pct']:5.1f}%  Bet={r['bet_total_pct']:5.1f}%  "
            f"33%={r['bet_33_pct']:4.1f}  50%={r['bet_50_pct']:4.1f}  75%={r['bet_75_pct']:4.1f}"
            f"  AS≈{AS} {'ベット推奨' if expected_bet else 'チェック推奨'} {match}"
        )

    # CSV 保存
    csv_path = os.path.join(out_dir, "aggressor_summary.csv")
    with open(csv_path, "w") as f:
        f.write("board,board_type,A,bucket,n,check_pct,bet_total_pct,bet_33_pct,bet_50_pct,bet_75_pct\n")
        for b, r in rows.items():
            f.write(f"{board},{board_type},{A},{b},{r['n']},{r['check_pct']},"
                    f"{r['bet_total_pct']},{r['bet_33_pct']},{r['bet_50_pct']},{r['bet_75_pct']}\n")
    print(f"\n結果を保存: {csv_path}")


if __name__ == "__main__":
    main()
