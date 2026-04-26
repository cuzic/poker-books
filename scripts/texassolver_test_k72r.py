#!/usr/bin/env python3
"""TexasSolver K72r 単ボードテスト.

K72r フロップで IP CBet 頻度と exploitability を計測する。
期待値: CBet ~75-91% (フロップ限定ツリーでは ~78%, 参考値 GTO Wizard 91%)

使用方法:
    python3 scripts/texassolver_test_k72r.py

実装メモ:
  - TexasSolver はプロセスのカレントディレクトリから relative path でファイルを
    探すため、cwd=SOLVER_DIR が必要。
  - stdout/stderr を PIPE で capture すると大量の progress bar 出力が
    パイプバッファを埋めてデッドロックを起こすため、ファイルにリダイレクトする。
  - exploitability は stdout に "Total exploitability X precent" として出力される。
  - ターン/リバーのベットサイズを省略すると「フロップ完結ツリー」になり、
    1ボードあたり ~2分で 0.5% exploitability まで収束する。
    フロップCBet頻度は GTO Wizard 参照値より ~10-13% 低めに出る傾向あり
    (ターン/リバーの positional advantage が反映されないため)。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"

# BTN open range (100BB, 6-max cash)
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

# BB defend range (vs BTN 2.5x, 100BB)
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
BOARD = "Kc,7d,2s"  # K72r
REF_CBET_PCT = 91  # GTO Wizard reference

# TexasSolver config template (フロップ完結ツリー)
# ターン/リバーのベットサイズを省略することで、ツリーをフロップ完結にする。
# これにより 1 ボードあたり ~2-3 分で収束する。
# GTO Wizard との系統的な乖離: フロップ CBet 頻度が ~10-13% 低めに出る
# (ターン/リバーの positional advantage が反映されないため)。
CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,flop,bet,33,50,75,150
set_bet_sizes ip,flop,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.3
set_max_iteration 500
set_print_interval 50
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""


def build_config(board: str, dump_path: str) -> str:
    return CONFIG_TEMPLATE.format(
        pot=POT,
        stack=STACK,
        board=board,
        ip_range=IP_RANGE,
        oop_range=OOP_RANGE,
        dump_path=dump_path,
    )


def run_solver(config_text: str, timeout: int = 300) -> tuple[str, str, int]:
    """TexasSolver をサブプロセスで実行し (stdout_path, returncode) を返す.

    stdout/stderr を一時ファイルにリダイレクトする (PIPE バッファ問題を回避)。
    config は一時ファイル経由で stdin に渡す。
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_cfg_"
    ) as f:
        f.write(config_text)
        cfg_path = f.name

    stdout_file = cfg_path.replace("ts_cfg_", "ts_stdout_")
    stderr_file = cfg_path.replace("ts_cfg_", "ts_stderr_")

    try:
        with open(cfg_path, "r") as fin, open(stdout_file, "w") as fout, open(
            stderr_file, "w"
        ) as ferr:
            proc = subprocess.Popen(
                [SOLVER_BIN],
                stdin=fin,
                stdout=fout,
                stderr=ferr,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                rc = -1  # timeout
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass

    return stdout_file, stderr_file, rc


def parse_exploitability(stdout_path: str) -> float | None:
    """stdout ファイルから最終 exploitability % を取得する.

    TexasSolver は以下の形式で出力する:
        Total exploitability X precent
    最後の値を返す。
    """
    last_val = None
    try:
        with open(stdout_path, "rb") as f:
            content = f.read()
        # バイナリから文字列に変換 (progress bar の制御文字を無視)
        lines = content.decode("utf-8", errors="replace").splitlines()
        for line in lines:
            line = line.strip()
            if "Total exploitability" in line and "precent" in line:
                try:
                    # "Total exploitability X precent"
                    parts = line.split()
                    idx = parts.index("exploitability") + 1
                    val = float(parts[idx])
                    last_val = val
                except (IndexError, ValueError):
                    pass
    except OSError:
        pass
    return last_val


def parse_ip_cbet(result_json: dict) -> float:
    """result JSON から OOP check 後の IP CBet 頻度 (0-100) を計算する.

    root node: player=1 (OOP), actions include CHECK
    childrens['CHECK']: player=0 (IP)
      strategy['strategy']: {combo: [prob_action0, prob_action1, ...]}
      strategy['actions']: [action_name, ...]

    IP CBet = 1 - CHECK probability, averaged over all combos.
    """
    root = result_json
    check_node = root.get("childrens", {}).get("CHECK")
    if check_node is None:
        raise ValueError("No CHECK node found in root childrens")

    strat_wrapper = check_node.get("strategy", {})
    combo_strats = strat_wrapper.get("strategy", {})
    actions = strat_wrapper.get("actions", [])

    if not combo_strats:
        raise ValueError("Empty strategy in CHECK node")

    # find CHECK index
    try:
        check_idx = actions.index("CHECK")
    except ValueError:
        check_idx = None

    total_cbet_prob = 0.0
    n = 0
    for probs in combo_strats.values():
        if check_idx is not None and check_idx < len(probs):
            cbet_prob = 1.0 - probs[check_idx]
        else:
            cbet_prob = 1.0
        total_cbet_prob += cbet_prob
        n += 1

    if n == 0:
        raise ValueError("No combos found in strategy")

    return (total_cbet_prob / n) * 100.0


def main() -> None:
    print("TexasSolver K72r テスト", file=sys.stderr)
    print(f"Solver: {SOLVER_BIN}", file=sys.stderr)
    print(f"Board: {BOARD}", file=sys.stderr)
    print(f"Pot: {POT} BB, Stack: {STACK} BB", file=sys.stderr)
    print(f"Tree: フロップ完結 (ターン/リバー省略)", file=sys.stderr)
    print("--- Solving (may take 2-3 min) ---", file=sys.stderr)

    with tempfile.TemporaryDirectory() as tmpdir:
        dump_path = os.path.join(tmpdir, "result.json")
        config = build_config(BOARD, dump_path)

        try:
            stdout_file, stderr_file, rc = run_solver(config, timeout=300)
        except Exception as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        if rc == -1:
            print("ERROR: solver timed out after 300s", file=sys.stderr)
            sys.exit(1)

        if rc not in (0, -6):  # -6 = SIGABRT can still produce dump
            print(f"ERROR: solver returned code {rc}", file=sys.stderr)
            # Read stdout for diagnosis
            try:
                with open(stdout_file) as f:
                    print("stdout:", f.read()[-500:], file=sys.stderr)
            except OSError:
                pass
            sys.exit(1)

        # exploitability
        exploitability = parse_exploitability(stdout_file)

        # Read result JSON
        if not os.path.exists(dump_path):
            print("ERROR: dump file not created", file=sys.stderr)
            try:
                with open(stdout_file) as f:
                    content = f.read()
                # show last part
                import re
                lines = [l for l in re.sub(r'\r', '\n', content).splitlines() if l.strip() and '[' not in l]
                print("stdout:", '\n'.join(lines[-20:]), file=sys.stderr)
            except OSError:
                pass
            sys.exit(1)

        with open(dump_path) as f:
            result = json.load(f)

        cbet_pct = parse_ip_cbet(result)

    # Cleanup temp files
    for p in (stdout_file, stderr_file):
        try:
            os.unlink(p)
        except OSError:
            pass

    # Results
    error = cbet_pct - REF_CBET_PCT
    abs_error = abs(error)

    print("\n=== K72r Result ===")
    print(f"Board:            {BOARD}")
    print(f"IP CBet (solver): {cbet_pct:.1f}%")
    print(f"GTO Wizard ref:   {REF_CBET_PCT}%")
    print(f"Error:            {error:+.1f}%")
    print(f"Abs error:        {abs_error:.1f}%")
    print(f"Exploitability:   {exploitability}%")

    if abs_error <= 20:
        print(f"\nPASS: within 20% of reference (typical for flop-only tree)")
    else:
        print(f"\nWARN: {cbet_pct:.1f}% is far from reference {REF_CBET_PCT}%")
        print("Note: フロップ完結ツリーでは ~10-13% の系統的な低め推定が生じる。")


if __name__ == "__main__":
    main()
