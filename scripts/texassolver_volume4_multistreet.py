#!/usr/bin/env python3
"""巻4 検証タスク（街別対応版）— TexasSolver パイプライン.

scripts/texassolver_volume4_river.py が river 専用 bet sizes のみ設定するため、
3 枚ボード（flop）や 4 枚ボード（turn）のシナリオでは tree の bet 枝が無く
全 100% CHECK 縮退する不具合があった。本スクリプトは街別 bet sizes を設定し、
任意の board 長で正しく解析する。

使用例:
    python3 scripts/texassolver_volume4_multistreet.py --task 108 --limit 5
    python3 scripts/texassolver_volume4_multistreet.py --task 108 --rerun-flop
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"

REPO = Path("/home/cuzic/poker-books")
SCEN_ROOT = REPO / "knowledges" / "volume4" / "scenarios"
RES_ROOT = REPO / "knowledges" / "volume4" / "results"

TIMEOUT_PER_SCENARIO = 180

# プリセットレンジ
PRESET_RANGES = {
    "BtnOpen100bb": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
        "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
        "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
        "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
        "JTs,JTo,J9s,J8s,J7s,J6s,T9s,T8s,T7s,T6s,98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
    ),
    "BbDefendVsBtn": (
        "JJ,TT,99,88,77,66,55,44,33,22,"
        "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
        "AQo,AJo,ATo,A9o,A8o,A7o,A6o,A5o,A4o,A3o,A2o,"
        "K8s,K9s,KTs,KJs,KQs,KTo,KJo,KQo,"
        "Q2s,Q3s,Q4s,Q5s,Q6s,Q7s,Q8s,Q9s,QTs,QJs,Q8o,Q9o,QTo,QJo,"
        "J4s,J5s,J6s,J7s,J8s,J9s,JTs,J8o,J9o,JTo,T5s,T6s,T7s,T8s,T9s,T8o,T9o,"
        "95s,96s,97s,98s,98o,85s,86s,87s,87o,75s,76s,76o,64s,65s,65o,53s,54s,43s"
    ),
    "CoOpen100bb": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,A5o,A6o,A7o,A8o,A9o,"
        "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,QJs,QTs,Q9s,Q8s,QTo,QJo,"
        "JTs,JTo,J9s,J8s,T9s,T8s,98s,87s,76s,65s"
    ),
    "UtgOpen100bb": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AKo,AQs,AQo,AJs,AJo,ATs,KQs,KQo,KTs,KJs,QTs,QJs,JTs"
    ),
    "BbDefendVsCo": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,AKo,AQo,AJo,ATo,A9o,A8o,A7o,"
        "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,QJs,QTs,Q9s,Q8s,Q7s,QJo,QTo,"
        "JTs,J9s,J8s,JTo,T9s,T8s,98s,97s,87s,76s,65s"
    ),
}


def build_config_for_street(scen: Dict[str, Any], dump_path: str) -> str:
    """街別の bet sizes を含む設定を生成."""
    board = scen["board"]
    n_board = len(board)
    pot = scen["pot_bb"]
    stack = scen["effective_stack_bb"]
    ip_range = resolve_range(scen["hero_range"])
    oop_range = resolve_range(scen["villain_range"])
    if scen.get("hero_position") in ("BB", "SB"):
        ip_range, oop_range = oop_range, ip_range

    sizes = scen.get("bet_sizes_to_evaluate", [])
    pct_list = [str(int(round(s * 100))) for s in sizes] if sizes else [33, 75]
    bet_sizes_str = ",".join(str(s) for s in pct_list) if pct_list else "33,75"

    lines = [
        f"set_pot {pot}",
        f"set_effective_stack {stack}",
        f"set_board {','.join(board)}",
        f"set_range_ip {ip_range}",
        f"set_range_oop {oop_range}",
    ]

    # 街別に bet sizes を設定（board 長に応じて必要な街のみ）
    if n_board == 3:
        # flop シナリオ: flop / turn / river の 3 街
        lines += [
            f"set_bet_sizes ip,flop,bet,{bet_sizes_str}",
            "set_bet_sizes ip,flop,allin",
            f"set_bet_sizes oop,flop,bet,{bet_sizes_str}",
            "set_bet_sizes oop,flop,allin",
            "set_bet_sizes ip,turn,bet,50,75",
            "set_bet_sizes ip,turn,allin",
            "set_bet_sizes oop,turn,bet,50,75",
            "set_bet_sizes oop,turn,allin",
            "set_bet_sizes ip,river,bet,75",
            "set_bet_sizes ip,river,allin",
            "set_bet_sizes oop,river,bet,75",
            "set_bet_sizes oop,river,allin",
        ]
    elif n_board == 4:
        # turn シナリオ: turn / river の 2 街
        lines += [
            f"set_bet_sizes ip,turn,bet,{bet_sizes_str}",
            "set_bet_sizes ip,turn,allin",
            f"set_bet_sizes oop,turn,bet,{bet_sizes_str}",
            "set_bet_sizes oop,turn,allin",
            "set_bet_sizes ip,river,bet,75",
            "set_bet_sizes ip,river,allin",
            "set_bet_sizes oop,river,bet,75",
            "set_bet_sizes oop,river,allin",
        ]
    else:
        # river シナリオ: river のみ
        lines += [
            f"set_bet_sizes ip,river,bet,{bet_sizes_str}",
            "set_bet_sizes ip,river,allin",
            f"set_bet_sizes oop,river,bet,{bet_sizes_str}",
            "set_bet_sizes oop,river,allin",
        ]

    # ツリー構築・解析
    lines += [
        "set_allin_threshold 0.67",
        "build_tree",
        "set_thread_num 8",
        "set_accuracy 0.5",
        "set_max_iteration 200",
        "set_print_interval 50",
        "set_dump_rounds 1",
        "start_solve",
        f"dump_result {dump_path}",
    ]
    return "\n".join(lines) + "\n"


def resolve_range(range_obj: Any) -> str:
    if isinstance(range_obj, str):
        return range_obj
    if isinstance(range_obj, dict):
        if "preset" in range_obj:
            preset = range_obj["preset"]
            if preset not in PRESET_RANGES:
                raise ValueError(f"未知の preset: {preset}")
            return PRESET_RANGES[preset]
        if "expr" in range_obj:
            return range_obj["expr"]
    raise ValueError(f"未対応の range 形式: {range_obj!r}")


def run_solver(config_text: str, timeout: int = TIMEOUT_PER_SCENARIO) -> int:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_v4ms_"
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


def aggregate_action_freq(node: Dict[str, Any]) -> Dict[str, float]:
    strat = node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})
    if not actions or not combos:
        return {}
    sums = [0.0] * len(actions)
    n = 0
    for probs in combos.values():
        if len(probs) != len(actions):
            continue
        for i, p in enumerate(probs):
            sums[i] += p
        n += 1
    if n == 0:
        return {}
    return {a: round(sums[i] / n, 4) for i, a in enumerate(actions)}


def aggregate(result_json: Dict[str, Any]) -> Dict[str, Any]:
    summary: Dict[str, Any] = {}
    summary["root_action_freq"] = aggregate_action_freq(result_json)

    children = result_json.get("childrens", {})
    bet_responses: Dict[str, Dict[str, float]] = {}
    for child_key, child_node in children.items():
        if not child_key.startswith("BET"):
            continue
        bet_responses[child_key] = aggregate_action_freq(child_node)
    summary["villain_response_to_bet"] = bet_responses

    check_node = children.get("CHECK")
    if check_node:
        summary["villain_after_hero_check"] = aggregate_action_freq(check_node)

    return summary


def solve_one(scen_path: Path, task: str) -> Dict[str, Any]:
    scen = json.loads(scen_path.read_text())
    sid = scen["scenario_id"]
    out_dir = RES_ROOT / task
    out_dir.mkdir(parents=True, exist_ok=True)
    dump_path = str(out_dir / f"{sid}_raw.json")

    config_text = build_config_for_street(scen, dump_path)

    t0 = time.time()
    rc = run_solver(config_text)
    elapsed = time.time() - t0

    if rc != 0 or not Path(dump_path).exists():
        return {
            "scenario_id": sid, "error": f"solver rc={rc}",
            "elapsed_sec": round(elapsed, 1),
        }

    try:
        raw = json.loads(Path(dump_path).read_text())
    except Exception as e:
        return {"scenario_id": sid, "error": f"parse failed: {e}"}

    return {
        "scenario_id": sid,
        "board": scen["board"],
        "n_board": len(scen["board"]),
        "pot_bb": scen["pot_bb"],
        "effective_stack_bb": scen["effective_stack_bb"],
        "elapsed_sec": round(elapsed, 1),
        "summary": aggregate(raw),
    }


def run_task(task: str, limit: Optional[int] = None,
             street_filter: Optional[int] = None) -> None:
    scen_dir = SCEN_ROOT / task
    if not scen_dir.exists():
        print(f"❌ scenarios/{task}/ なし", file=sys.stderr)
        return
    out_dir = RES_ROOT / task
    out_dir.mkdir(parents=True, exist_ok=True)

    scen_files = sorted(scen_dir.glob("*.json"))
    scen_files = [p for p in scen_files if p.stem != "index"]

    if street_filter is not None:
        # board 長で絞る
        filtered = []
        for p in scen_files:
            scen = json.loads(p.read_text())
            if len(scen["board"]) == street_filter:
                filtered.append(p)
        scen_files = filtered

    if limit:
        scen_files = scen_files[:limit]

    print(f"\n=== Task #{task}: {len(scen_files)} シナリオ "
          f"(street_filter={street_filter}) ===")
    summaries: List[Dict[str, Any]] = []
    total_elapsed = 0.0
    for i, scen_path in enumerate(scen_files, 1):
        print(f"  [{i}/{len(scen_files)}] {scen_path.stem}", end=" ... ", flush=True)
        result = solve_one(scen_path, task)
        if "error" in result:
            print(f"ERROR ({result.get('elapsed_sec', '?')}s): {result['error'][:60]}")
        else:
            elapsed = result.get("elapsed_sec", 0)
            total_elapsed += elapsed
            root = result["summary"].get("root_action_freq", {})
            check = root.get("CHECK", 0)
            bet_total = sum(v for k, v in root.items() if k.startswith("BET"))
            print(f"{elapsed:.1f}s n={result['n_board']} CHECK={check:.2f} BET={bet_total:.2f}")
        out_file = out_dir / f"{scen_path.stem}.json"
        out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        summaries.append(result)

    summary_path = out_dir / "summary_multistreet.json"
    summary_path.write_text(json.dumps({
        "task": task,
        "n_scenarios": len(summaries),
        "total_elapsed_sec": round(total_elapsed, 1),
        "scenarios": summaries,
    }, ensure_ascii=False, indent=2))
    print(f"\n  → {out_dir}/ に {len(summaries)} ファイル出力 (total {total_elapsed:.0f}s)")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task", required=True, help="103 / 105 / 106 / 108 / all")
    p.add_argument("--limit", type=int, help="先頭 N シナリオのみ実行")
    p.add_argument("--street", type=int, choices=[3, 4, 5],
                   help="board 長で絞る（3=flop, 4=turn, 5=river）")
    args = p.parse_args()

    if args.task == "all":
        for t in ["106", "103", "105", "108"]:
            run_task(t, args.limit, args.street)
    else:
        run_task(args.task, args.limit, args.street)


if __name__ == "__main__":
    main()
