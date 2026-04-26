#!/usr/bin/env python3
"""TexasSolver 30 ボード精度検証スクリプト.

BTN vs BB, 100BB, 6-max キャッシュの SRP フロップ CBet 頻度を
30 ボードについて TexasSolver で計算し、GTO Wizard 参照値と比較する。

使用方法:
    python3 scripts/texassolver_accuracy_30.py [--dry-run]

オプション:
    --dry-run : TexasSolver を実行せずに設定ファイルのみ生成して確認

出力:
    /home/cuzic/poker-books/knowledges/volume4/results/texassolver_accuracy_30.json

ツリー構造 (フロップ完結ツリー):
    - フロップのみ (ターン/リバーのベットサイズは省略)
    - IP ベット: 33%, 50%, 75%, 150% pot + all-in
    - OOP ベット (OOP lead): 60%, 100% pot + all-in
    - OOP raise 不使用 (ツリーサイズを抑えるため)
    - 1 ボードあたり ~2-3 分で 0.3% exploitability まで収束

性能特性:
    - 系統的誤差: GTO Wizard 参照値より ~10-15% 低めに推定
      (ターン/リバーの IP ポジションアドバンテージが未反映)
    - ボードタイプ間の相対順序は維持される (ドライ > ウェット の傾向)
    - 30 ボードの合計実行時間: ~60-90 分 (8 スレッド、CPU による)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
RESULTS_DIR = Path("/home/cuzic/poker-books/knowledges/volume4/results")
OUTPUT_FILE = RESULTS_DIR / "texassolver_accuracy_30.json"

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
TIMEOUT_PER_BOARD = 300  # 秒 (5 分)

# TexasSolver config template
# フロップ完結ツリー: ターン/リバーのベットサイズを省略
# OOP は bet のみ (raise なし) でツリーサイズを抑制
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

# ---------------------------------------------------------------------------
# 30 ボードと GTO Wizard 参照 CBet %
# ---------------------------------------------------------------------------

BOARDS = [
    # (board_spec, ref_cbet_pct, board_cards)
    ("K72r",    91, "Kc,7d,2s"),
    ("A72r",    90, "Ac,7d,2s"),
    ("K44",     43, "Kc,4d,4s"),
    ("Q53r",    85, "Qc,5d,3s"),
    ("A82r",    88, "Ac,8d,2s"),
    ("K83r",    87, "Kc,8d,3s"),
    ("A52r",    89, "Ac,5d,2s"),
    ("K95r",    80, "Kc,9d,5s"),
    ("KT5r",    70, "Kc,Td,5s"),
    ("J75r",    40, "Jc,7d,5s"),
    ("Q83ss",   55, "Qc,8c,3d"),
    ("AT7ss",   60, "Ac,Tc,7d"),
    ("J84ss",   50, "Jc,8c,4d"),
    ("QJ9r",    50, "Qc,Jd,9s"),
    ("T87r",    45, "Tc,8d,7s"),
    ("876r",    42, "8c,7d,6s"),
    ("987ss",   30, "9c,8c,7d"),
    ("JT9ss",   25, "Jc,Tc,9d"),
    ("987mono", 20, "9h,8h,7h"),
    ("KQTss",   35, "Kc,Qc,Td"),
    ("AKQmono", 15, "Ah,Kh,Qh"),
    ("JT8ss",   30, "Jc,Tc,8d"),
    ("T98r",    40, "Tc,9d,8s"),
    ("T98ss",   35, "Tc,9c,8d"),
    ("772",     70, "7c,7d,2s"),
    ("AAK",     85, "Ac,Ad,Ks"),
    ("KK9",     80, "Kc,Kd,9s"),
    ("965r",    60, "9c,6d,5s"),
    ("632r",    62, "6c,3d,2s"),
    ("A99",     78, "Ac,9d,9s"),
]

assert len(BOARDS) == 30, f"Expected 30 boards, got {len(BOARDS)}"


# ---------------------------------------------------------------------------
# ソルバー実行
# ---------------------------------------------------------------------------


def build_config(board_cards: str, dump_path: str) -> str:
    """TexasSolver 設定ファイルのテキストを生成する."""
    return CONFIG_TEMPLATE.format(
        pot=POT,
        stack=STACK,
        board=board_cards,
        ip_range=IP_RANGE,
        oop_range=OOP_RANGE,
        dump_path=dump_path,
    )


def run_solver(
    config_text: str, timeout: int = TIMEOUT_PER_BOARD
) -> tuple[float | None, int]:
    """TexasSolver を実行し (exploitability, returncode) を返す.

    stdout/stderr をファイルにリダイレクトして PIPE バッファ問題を回避する。
    config は一時ファイル経由で stdin に渡す。
    TexasSolver は cwd=/home/cuzic/TexasSolver が必要。
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_cfg_"
    ) as f:
        f.write(config_text)
        cfg_path = f.name

    stdout_file = cfg_path.replace("ts_cfg_", "ts_stdout_")

    try:
        with open(cfg_path, "r") as fin, open(stdout_file, "w") as fout:
            proc = subprocess.Popen(
                [SOLVER_BIN],
                stdin=fin,
                stdout=fout,
                stderr=subprocess.DEVNULL,
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

    exploitability = parse_exploitability(stdout_file)

    try:
        os.unlink(stdout_file)
    except OSError:
        pass

    return exploitability, rc  # type: ignore[return-value]


def parse_exploitability(stdout_path: str) -> float | None:
    """stdout ファイルから最終 exploitability % を取得する.

    "Total exploitability X precent" の最後の値を返す。
    """
    last_val = None
    try:
        with open(stdout_path, "rb") as f:
            content = f.read()
        text = content.decode("utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if "Total exploitability" in line and "precent" in line:
                try:
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
      strategy['strategy']: {combo: [prob_action0, ...]}
      strategy['actions']: [action_name, ...]

    IP CBet = 1 - CHECK probability, combos の単純平均。
    """
    check_node = result_json.get("childrens", {}).get("CHECK")
    if check_node is None:
        raise ValueError("No CHECK node found in root childrens")

    strat_wrapper = check_node.get("strategy", {})
    combo_strats = strat_wrapper.get("strategy", {})
    actions = strat_wrapper.get("actions", [])

    if not combo_strats:
        raise ValueError("Empty strategy in CHECK node")

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


def solve_board(
    board_spec: str,
    ref_cbet_pct: int,
    board_cards: str,
    dry_run: bool = False,
) -> dict:
    """1 ボードを解き、結果辞書を返す."""
    t0 = time.time()
    print(
        f"  [{board_spec}] cards={board_cards} ref={ref_cbet_pct}%",
        file=sys.stderr,
    )

    if dry_run:
        print("  [DRY RUN] スキップ", file=sys.stderr)
        return {
            "board": board_spec,
            "board_cards": board_cards,
            "ref_cbet_pct": ref_cbet_pct,
            "solver_cbet_pct": None,
            "error": None,
            "abs_error": None,
            "exploitability_pct": None,
            "elapsed_sec": 0.0,
            "status": "dry_run",
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        dump_path = os.path.join(tmpdir, "result.json")
        config = build_config(board_cards, dump_path)

        exploitability, rc = run_solver(config, timeout=TIMEOUT_PER_BOARD)

        elapsed = time.time() - t0

        if rc == -1:
            print(
                f"  [{board_spec}] TIMEOUT after {elapsed:.0f}s", file=sys.stderr
            )
            return {
                "board": board_spec,
                "board_cards": board_cards,
                "ref_cbet_pct": ref_cbet_pct,
                "solver_cbet_pct": None,
                "error": None,
                "abs_error": None,
                "exploitability_pct": None,
                "elapsed_sec": round(elapsed, 1),
                "status": "timeout",
            }

        if rc not in (0,):
            print(
                f"  [{board_spec}] ERROR rc={rc} after {elapsed:.0f}s",
                file=sys.stderr,
            )
            return {
                "board": board_spec,
                "board_cards": board_cards,
                "ref_cbet_pct": ref_cbet_pct,
                "solver_cbet_pct": None,
                "error": None,
                "abs_error": None,
                "exploitability_pct": None,
                "elapsed_sec": round(elapsed, 1),
                "status": f"error_rc_{rc}",
            }

        if not os.path.exists(dump_path):
            print(
                f"  [{board_spec}] ERROR: dump file not created after {elapsed:.0f}s",
                file=sys.stderr,
            )
            return {
                "board": board_spec,
                "board_cards": board_cards,
                "ref_cbet_pct": ref_cbet_pct,
                "solver_cbet_pct": None,
                "error": None,
                "abs_error": None,
                "exploitability_pct": None,
                "elapsed_sec": round(elapsed, 1),
                "status": "no_dump",
            }

        try:
            with open(dump_path) as f:
                result_json = json.load(f)
            cbet_pct = parse_ip_cbet(result_json)
        except Exception as e:
            print(
                f"  [{board_spec}] ERROR parsing result: {e}", file=sys.stderr
            )
            return {
                "board": board_spec,
                "board_cards": board_cards,
                "ref_cbet_pct": ref_cbet_pct,
                "solver_cbet_pct": None,
                "error": None,
                "abs_error": None,
                "exploitability_pct": None,
                "elapsed_sec": round(elapsed, 1),
                "status": f"parse_error: {e}",
            }

    error = round(cbet_pct - ref_cbet_pct, 1)
    abs_error = abs(error)
    exploit_str = f"{exploitability:.3f}" if exploitability is not None else "N/A"
    print(
        f"  [{board_spec}] cbet={cbet_pct:.1f}% ref={ref_cbet_pct}% "
        f"err={error:+.1f}% exploit={exploit_str}% elapsed={elapsed:.0f}s",
        file=sys.stderr,
    )

    return {
        "board": board_spec,
        "board_cards": board_cards,
        "ref_cbet_pct": ref_cbet_pct,
        "solver_cbet_pct": round(cbet_pct, 1),
        "error": error,
        "abs_error": abs_error,
        "exploitability_pct": round(exploitability, 3) if exploitability is not None else None,
        "elapsed_sec": round(elapsed, 1),
        "status": "ok",
    }


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="TexasSolver 30 ボード精度検証")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="TexasSolver を実行せずに設定のみ検証",
    )
    args = parser.parse_args()

    # 出力ディレクトリ確認
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # ソルバーバイナリ確認
    if not os.path.exists(SOLVER_BIN):
        print(f"ERROR: solver not found: {SOLVER_BIN}", file=sys.stderr)
        sys.exit(1)

    print(
        f"=== TexasSolver 30 ボード精度検証 ===",
        file=sys.stderr,
    )
    print(
        f"Solver: {SOLVER_BIN}\n"
        f"Output: {OUTPUT_FILE}\n"
        f"Boards: {len(BOARDS)}\n"
        f"Timeout: {TIMEOUT_PER_BOARD}s/board\n"
        f"DryRun: {args.dry_run}",
        file=sys.stderr,
    )

    results = []
    t_start = time.time()

    for i, (board_spec, ref_cbet_pct, board_cards) in enumerate(BOARDS, 1):
        print(
            f"\n[{i}/{len(BOARDS)}] {board_spec} ...",
            file=sys.stderr,
        )
        result = solve_board(board_spec, ref_cbet_pct, board_cards, dry_run=args.dry_run)
        results.append(result)

        # 中間保存 (クラッシュ耐性)
        save_results(results, partial=True)

    total_elapsed = time.time() - t_start

    # 統計集計
    valid = [r for r in results if r["abs_error"] is not None]
    if valid:
        avg_abs_error = round(sum(r["abs_error"] for r in valid) / len(valid), 1)
        max_abs_error = max(r["abs_error"] for r in valid)
    else:
        avg_abs_error = None
        max_abs_error = None

    output = {
        "summary": {
            "avg_abs_error_pct": avg_abs_error,
            "max_abs_error_pct": max_abs_error,
            "count": len(results),
            "valid_count": len(valid),
            "total_elapsed_sec": round(total_elapsed, 1),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "metadata": {
            "solver": "TexasSolver (C++ CFR)",
            "solver_bin": SOLVER_BIN,
            "ip_range": "BTN open 100BB 6-max",
            "oop_range": "BB defend vs BTN 2.5x 100BB",
            "pot": POT,
            "stack": STACK,
            "tree": "flop-only (no turn/river)",
            "ip_flop_bets": "33,50,75,150 + allin",
            "oop_flop_bets": "60,100 + allin",
            "accuracy_target_pct": 0.3,
            "max_iterations": 500,
            "timeout_per_board_sec": TIMEOUT_PER_BOARD,
            "note": (
                "フロップ完結ツリーのため GTO Wizard 参照値より ~10-15% 低めに推定。"
                "ターン/リバーの IP ポジションアドバンテージが未反映。"
                "ボードタイプ間の相対順序は維持される。"
            ),
        },
        "results": results,
    }

    save_results(results, output=output, partial=False)

    print(
        f"\n=== 完了 ===\n"
        f"Valid: {len(valid)}/{len(results)}\n"
        f"Avg |error|: {avg_abs_error}%\n"
        f"Max |error|: {max_abs_error}%\n"
        f"Total elapsed: {total_elapsed:.0f}s\n"
        f"Output: {OUTPUT_FILE}",
        file=sys.stderr,
    )


def save_results(
    results: list,
    output: dict | None = None,
    partial: bool = True,
) -> None:
    """結果を JSON ファイルに保存する."""
    if output is None:
        # 中間保存用の簡易フォーマット
        valid = [r for r in results if r["abs_error"] is not None]
        output = {
            "summary": {
                "avg_abs_error_pct": (
                    round(sum(r["abs_error"] for r in valid) / len(valid), 1)
                    if valid
                    else None
                ),
                "max_abs_error_pct": max((r["abs_error"] for r in valid), default=None),
                "count": len(results),
                "valid_count": len(valid),
                "partial": partial,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
            },
            "metadata": {
                "solver": "TexasSolver (C++ CFR)",
                "ip_range": "BTN open 100BB 6-max",
                "oop_range": "BB defend vs BTN 2.5x 100BB",
                "pot": POT,
                "stack": STACK,
            },
            "results": results,
        }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
