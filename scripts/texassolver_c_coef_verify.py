#!/usr/bin/env python3
"""C 係数（100% / 150% pot bet）の MDF を実測し、巻④ 第11章の理論値と比較する.

巻④ ch11 の C 値設計:
  100% bet → 後手下限確率 = 0.50 → C=9
  150% bet → 後手下限確率 = 0.40 → C=11

scenarios/106/ の 10 ボードを再利用し、bet size 100% と 150% で MDF を実測。
balanced レンジ（BB defend）のみを対象に、tight レンジは省略（時間節約）。

使用方法:
    python3 scripts/texassolver_c_coef_verify.py
"""
from __future__ import annotations

import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
REPO = Path("/home/cuzic/poker-books")
OUT_DIR = REPO / "knowledges" / "volume4" / "results" / "c_coef_verify"

# 巻④ ch11 の代表 10 ボード（#106 の balanced と同じ）
BOARDS = [
    ("Adry", ["As", "Kh", "7d", "4c", "2s"]),
    ("Kdry", ["Kc", "9h", "5d", "3s", "2c"]),
    ("BoardTrips", ["7s", "7d", "7c", "Kh", "2s"]),
    ("TwoPair", ["Ks", "Qd", "Kh", "Qc", "3s"]),
    ("FlushDone", ["Kh", "9h", "5h", "3h", "2c"]),
    ("FullHouseable", ["8s", "8d", "Kh", "Qc", "Kd"]),
    ("FourStraight", ["9s", "8d", "7c", "6h", "2s"]),
    ("LowStraight", ["5s", "4d", "3c", "2h", "Ah"]),
    ("StraightDone", ["Js", "Td", "9c", "8h", "7s"]),
    ("Monotone", ["Kh", "9h", "5h", "3h", "2h"]),
]

IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
    "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,T9s,T8s,T7s,T6s,98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)

OOP_RANGE_BALANCED = (
    "JJ,TT,99,88,77,66,55,44,33,22,"
    "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AQo,AJo,ATo,A9o,A8o,A7o,A6o,A5o,A4o,A3o,A2o,"
    "K8s,K9s,KTs,KJs,KQs,KTo,KJo,KQo,"
    "Q2s,Q3s,Q4s,Q5s,Q6s,Q7s,Q8s,Q9s,QTs,QJs,Q8o,Q9o,QTo,QJo,"
    "J4s,J5s,J6s,J7s,J8s,J9s,JTs,J8o,J9o,JTo,T5s,T6s,T7s,T8s,T9s,T8o,T9o,"
    "95s,96s,97s,98s,98o,85s,86s,87s,87o,75s,76s,76o,64s,65s,65o,53s,54s,43s"
)

CONFIG_TEMPLATE = """\
set_pot 27
set_effective_stack 80
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,river,bet,{bet_pct}
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,{bet_pct}
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 200
set_print_interval 50
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""


def run_solver(config_text: str, timeout: int = 90) -> int:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_ccoef_"
    ) as f:
        f.write(config_text)
        cfg_path = f.name
    try:
        with open(cfg_path) as fin:
            proc = subprocess.Popen(
                [SOLVER_BIN], stdin=fin,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                rc = -1
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass
    return rc


def aggregate_fold(node):
    strat = node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})
    if not actions or not combos:
        return None
    try:
        fold_idx = actions.index("FOLD")
    except ValueError:
        return None
    sums = 0.0
    n = 0
    for probs in combos.values():
        if len(probs) > fold_idx:
            sums += probs[fold_idx]
            n += 1
    return sums / n if n else None


def measure(board_label, board, bet_pct):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dump_path = str(OUT_DIR / f"{board_label}_{bet_pct}pct_raw.json")
    config = CONFIG_TEMPLATE.format(
        board=",".join(board),
        ip_range=IP_RANGE,
        oop_range=OOP_RANGE_BALANCED,
        bet_pct=bet_pct,
        dump_path=dump_path,
    )
    t0 = time.time()
    rc = run_solver(config)
    elapsed = time.time() - t0
    if rc != 0 or not Path(dump_path).exists():
        return {"error": f"rc={rc}", "elapsed": elapsed}

    raw = json.loads(Path(dump_path).read_text())
    children = raw.get("childrens", {})
    bet_node = None
    for k, v in children.items():
        if k.startswith("BET"):
            try:
                bet_amount = float(k.split()[1])
                expected = 27 * bet_pct / 100
                if abs(bet_amount - expected) < 0.5:
                    bet_node = v
                    break
            except (IndexError, ValueError):
                pass
            if bet_node is None:
                bet_node = v

    if bet_node is None:
        return {"error": "no BET node", "elapsed": elapsed}

    fold_freq = aggregate_fold(bet_node)
    if fold_freq is None:
        return {"error": "no FOLD aggregate", "elapsed": elapsed}

    mdf = 1.0 - fold_freq
    return {"mdf": round(mdf, 4), "fold": round(fold_freq, 4), "elapsed": round(elapsed, 1)}


def main():
    results = {}
    for bet_pct in [100, 150]:
        theory_alpha = bet_pct / (100 + bet_pct)
        theory_mdf = 1 - theory_alpha
        print(f"\n=== bet={bet_pct}% / 理論 α={theory_alpha:.3f} → MDF={theory_mdf:.3f} ===")
        results[bet_pct] = []
        for label, board in BOARDS:
            print(f"  {label:18s} ({''.join(board)}) ...", end=" ", flush=True)
            r = measure(label, board, bet_pct)
            if "error" in r:
                print(f"ERROR ({r['elapsed']:.0f}s): {r['error']}")
            else:
                diff = r["mdf"] - theory_mdf
                print(f"{r['elapsed']:.0f}s  MDF={r['mdf']:.3f}  (理論差 {diff:+.3f})")
                results[bet_pct].append((label, r["mdf"]))

        if results[bet_pct]:
            mdfs = [m for _, m in results[bet_pct]]
            avg = statistics.mean(mdfs)
            print(f"  → 平均 MDF = {avg:.3f}  (理論 {theory_mdf:.3f}, 差 {avg-theory_mdf:+.3f})")

    summary_path = OUT_DIR / "c_coef_summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nWritten: {summary_path}")


if __name__ == "__main__":
    main()
