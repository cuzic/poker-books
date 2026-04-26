#!/usr/bin/env python3
"""巻4 タスク #102 ターン CBet 頻度 270 ケース — TexasSolver パイプライン.

scenarios/102/ 配下の 270 シナリオ JSON を読み込み、TexasSolver で
ターン CBet 頻度を計算して results/102/ に保存する。

使用方法:
    python3 scripts/texassolver_volume4_102.py [--dry-run] [--limit N]

オプション:
    --dry-run : TexasSolver を実行せず設定のみ確認
    --limit N : 先頭 N シナリオのみ実行 (テスト用)
    --resume  : 既存結果をスキップして未完了のみ実行 (デフォルト有効)

出力:
    knowledges/volume4/results/102/turn_cbet_102_<board>_<turn>.json

ツリー構造 (ターン+リバーツリー):
    - 4 枚ボード (フロップ3枚 + ターン1枚) を set_board に渡す
    - IP ターンベット: 33%, 50%, 75%, 150% + all-in
    - OOP ターンベット: 50%, 100% + all-in
    - リバーベット: 50% のみ + all-in (ツリーサイズ抑制)
    - 1 シナリオあたり ~45-60 秒で収束 (accuracy=0.5%)

性能特性:
    - ターンシナリオは完全ツリーのためフロップ完結ツリーの系統的バイアスなし
    - レンジは事前プリフロップ範囲を使用 (フロップ絞り込みなし)
    - 270 シナリオ × 50 秒 ≈ 3.75 時間 (1 プロセス)
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

SCENARIOS_DIR = Path("/home/cuzic/poker-books/knowledges/volume4/scenarios/102")
RESULTS_DIR = Path("/home/cuzic/poker-books/knowledges/volume4/results/102")
INDEX_FILE = SCENARIOS_DIR / "index.json"

TIMEOUT_PER_SCENARIO = 200  # 秒

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

# TexasSolver config template (ターン+リバーツリー)
# 4枚ボード (flop+turn) を set_board に渡す
# リバーは 50% のみでツリーサイズを抑制
CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,turn,bet,50,100
set_bet_sizes oop,turn,allin
set_bet_sizes ip,turn,bet,33,50,75,150
set_bet_sizes ip,turn,allin
set_bet_sizes oop,river,bet,50
set_bet_sizes oop,river,allin
set_bet_sizes ip,river,bet,50
set_bet_sizes ip,river,allin
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


# ---------------------------------------------------------------------------
# シナリオ読み込み
# ---------------------------------------------------------------------------


def load_scenarios() -> list[dict]:
    """index.json からシナリオ一覧を読み込む."""
    with open(INDEX_FILE) as f:
        index = json.load(f)
    scenarios = []
    for entry in index["scenarios"]:
        scenario_file = SCENARIOS_DIR / entry["file"]
        with open(scenario_file) as f:
            scenario = json.load(f)
        scenario["_board_label"] = entry["board_label"]
        scenario["_category"] = entry["category"]
        scenarios.append(scenario)
    return scenarios


# ---------------------------------------------------------------------------
# ソルバー実行
# ---------------------------------------------------------------------------


def build_config(board: list[str], pot: int, stack: int, dump_path: str) -> str:
    """TexasSolver 設定ファイルのテキストを生成する."""
    board_str = ",".join(board)  # ["Kc","7d","2s","As"] → "Kc,7d,2s,As"
    return CONFIG_TEMPLATE.format(
        pot=pot,
        stack=stack,
        board=board_str,
        ip_range=IP_RANGE,
        oop_range=OOP_RANGE,
        dump_path=dump_path,
    )


def run_solver(
    config_text: str, timeout: int = TIMEOUT_PER_SCENARIO
) -> tuple[float | None, int]:
    """TexasSolver を実行し (exploitability, returncode) を返す."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_v4_cfg_"
    ) as f:
        f.write(config_text)
        cfg_path = f.name

    stdout_file = cfg_path.replace("ts_v4_cfg_", "ts_v4_stdout_")

    try:
        with open(cfg_path) as fin, open(stdout_file, "w") as fout:
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
                rc = -1
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass

    exploitability = _parse_exploitability(stdout_file)

    try:
        os.unlink(stdout_file)
    except OSError:
        pass

    return exploitability, rc


def _parse_exploitability(stdout_path: str) -> float | None:
    last_val = None
    try:
        with open(stdout_path, "rb") as f:
            content = f.read()
        for line in content.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if "Total exploitability" in line and "precent" in line:
                try:
                    parts = line.split()
                    idx = parts.index("exploitability") + 1
                    last_val = float(parts[idx])
                except (IndexError, ValueError):
                    pass
    except OSError:
        pass
    return last_val


def parse_ip_cbet(result_json: dict) -> float:
    """result JSON からターン OOP check 後の IP CBet 頻度 (0-100) を計算する."""
    check_node = result_json.get("childrens", {}).get("CHECK")
    if check_node is None:
        raise ValueError(
            f"No CHECK node in root. Keys: {list(result_json.get('childrens', {}).keys())}"
        )

    strat_wrapper = check_node.get("strategy", {})
    combo_strats = strat_wrapper.get("strategy", {})
    actions = strat_wrapper.get("actions", [])

    if not combo_strats:
        raise ValueError("Empty strategy in CHECK node")

    check_idx: int | None
    try:
        check_idx = actions.index("CHECK")
    except ValueError:
        check_idx = None

    total = 0.0
    n = 0
    for probs in combo_strats.values():
        if check_idx is not None and check_idx < len(probs):
            total += 1.0 - probs[check_idx]
        else:
            total += 1.0
        n += 1

    if n == 0:
        raise ValueError("No combos found")

    return (total / n) * 100.0


# ---------------------------------------------------------------------------
# シナリオ実行
# ---------------------------------------------------------------------------


def solve_scenario(scenario: dict, dry_run: bool = False) -> dict:
    """1 シナリオを解いて結果辞書を返す."""
    sid = scenario["scenario_id"]
    board = scenario["board"]
    pot = scenario.get("pot_bb", 10)
    stack = scenario.get("effective_stack_bb", 92)
    category = scenario.get("_category", "unknown")
    board_label = scenario.get("_board_label", "?")
    turn_card = board[3] if len(board) >= 4 else "?"

    t0 = time.time()

    base_result = {
        "scenario_id": sid,
        "board_label": board_label,
        "board": board,
        "turn_card": turn_card,
        "category": category,
        "pot_bb": pot,
        "effective_stack_bb": stack,
        "turn_cbet_pct": None,
        "exploitability_pct": None,
        "elapsed_sec": None,
        "status": "unknown",
    }

    if dry_run:
        base_result["elapsed_sec"] = 0.0
        base_result["status"] = "dry_run"
        print(f"  [DRY RUN] {sid}", file=sys.stderr)
        return base_result

    with tempfile.TemporaryDirectory() as tmpdir:
        dump_path = os.path.join(tmpdir, "result.json")
        config = build_config(board, pot, stack, dump_path)

        exploitability, rc = run_solver(config, timeout=TIMEOUT_PER_SCENARIO)
        elapsed = time.time() - t0
        base_result["elapsed_sec"] = round(elapsed, 1)

        if rc == -1:
            base_result["status"] = "timeout"
            print(f"  [{sid}] TIMEOUT {elapsed:.0f}s", file=sys.stderr)
            return base_result

        if rc != 0:
            base_result["status"] = f"error_rc_{rc}"
            print(f"  [{sid}] ERROR rc={rc}", file=sys.stderr)
            return base_result

        if not os.path.exists(dump_path):
            base_result["status"] = "no_dump"
            print(f"  [{sid}] no dump file", file=sys.stderr)
            return base_result

        try:
            with open(dump_path) as f:
                result_json = json.load(f)
            cbet_pct = parse_ip_cbet(result_json)
        except Exception as e:
            base_result["status"] = f"parse_error: {e}"
            print(f"  [{sid}] parse error: {e}", file=sys.stderr)
            return base_result

    base_result.update(
        {
            "turn_cbet_pct": round(cbet_pct, 1),
            "exploitability_pct": round(exploitability, 3) if exploitability is not None else None,
            "status": "ok",
        }
    )
    exploit_str = f"{exploitability:.3f}" if exploitability is not None else "N/A"
    print(
        f"  [{sid}] cbet={cbet_pct:.1f}% cat={category} exploit={exploit_str}% {elapsed:.0f}s",
        file=sys.stderr,
    )
    return base_result


def already_done(scenario_id: str) -> bool:
    """結果ファイルが既に存在するか確認する."""
    out_file = RESULTS_DIR / f"{scenario_id}.json"
    if not out_file.exists():
        return False
    try:
        with open(out_file) as f:
            data = json.load(f)
        return data.get("status") == "ok"
    except Exception:
        return False


def save_scenario_result(result: dict) -> None:
    """シナリオ結果を個別 JSON ファイルに保存する."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RESULTS_DIR / f"{result['scenario_id']}.json"
    with open(out_file, "w") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# 集計
# ---------------------------------------------------------------------------


def build_summary() -> dict:
    """results/102/ の全 JSON を集計してサマリを返す."""
    results = []
    for f in sorted(RESULTS_DIR.glob("turn_cbet_102_*.json")):
        try:
            with open(f) as fh:
                results.append(json.load(fh))
        except Exception:
            pass

    done = [r for r in results if r.get("status") == "ok"]
    cats: dict[str, list[float]] = {}
    for r in done:
        cat = r.get("category", "unknown")
        pct = r.get("turn_cbet_pct")
        if pct is not None:
            cats.setdefault(cat, []).append(pct)

    cat_avg = {c: round(sum(v) / len(v), 1) for c, v in cats.items()}

    return {
        "count_total": len(results),
        "count_ok": len(done),
        "category_avg_cbet_pct": cat_avg,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="巻4 #102 ターン CBet 270 ケース")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="先頭 N シナリオのみ")
    parser.add_argument(
        "--no-resume", action="store_true", help="既存結果を無視して再実行"
    )
    args = parser.parse_args()

    if not os.path.exists(SOLVER_BIN):
        print(f"ERROR: solver not found: {SOLVER_BIN}", file=sys.stderr)
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    scenarios = load_scenarios()
    if args.limit > 0:
        scenarios = scenarios[: args.limit]

    total = len(scenarios)
    skip = 0
    if not args.no_resume:
        todo = [s for s in scenarios if not already_done(s["scenario_id"])]
        skip = total - len(todo)
        if skip > 0:
            print(f"Resume: {skip}/{total} 済み → {len(todo)} 残", file=sys.stderr)
        scenarios = todo
    else:
        todo = scenarios

    print(
        f"=== 巻4 #102 ターン CBet ===\n"
        f"Solver: {SOLVER_BIN}\n"
        f"Scenarios: {len(scenarios)} (skip={skip})\n"
        f"Timeout: {TIMEOUT_PER_SCENARIO}s/scenario\n"
        f"DryRun: {args.dry_run}",
        file=sys.stderr,
    )

    t_start = time.time()
    ok = 0
    error = 0

    for i, scenario in enumerate(scenarios, 1):
        sid = scenario["scenario_id"]
        print(f"\n[{i+skip}/{total}] {sid} ...", file=sys.stderr)

        result = solve_scenario(scenario, dry_run=args.dry_run)
        save_scenario_result(result)

        if result["status"] == "ok":
            ok += 1
        else:
            error += 1

    total_elapsed = time.time() - t_start
    summary = build_summary()

    print(
        f"\n=== 完了 ===\n"
        f"OK: {ok}, Error: {error}\n"
        f"Category avg CBet: {summary['category_avg_cbet_pct']}\n"
        f"Elapsed: {total_elapsed:.0f}s\n"
        f"Output: {RESULTS_DIR}",
        file=sys.stderr,
    )

    # サマリ JSON を保存
    summary_file = RESULTS_DIR / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"Summary: {summary_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
