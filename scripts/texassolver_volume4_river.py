#!/usr/bin/env python3
"""巻4 リバー検証タスク #103 / #105 / #106 / #108 の TexasSolver パイプライン.

5 枚ボード（リバー）専用で解き、各タスク固有の指標を集計する。

使用方法:
    python3 scripts/texassolver_volume4_river.py --task 106 [--limit N] [--dry-run]
    python3 scripts/texassolver_volume4_river.py --task all

タスク別:
    #103 リバー V:B 比     30 シナリオ × 3 ベットサイズ
    #105 ブロッカー論     20 シナリオ
    #106 リバー MDF       20 シナリオ
    #108 フック 6 論点    30 シナリオ

性能: 1 シナリオ約 30〜60 秒（リバーオンリーは tree 軽量）
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

TIMEOUT_PER_SCENARIO = 120

# プリセットレンジ（poker-gto/preset_ranges.rs と一致）
PRESET_RANGES = {
    "BtnOpen100bb": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
        "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
        "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
        "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
        "JTs,JTo,J9s,J8s,J7s,J6s,"
        "T9s,T8s,T7s,T6s,98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
    ),
    "BbDefendVsBtn": (
        "JJ,TT,99,88,77,66,55,44,33,22,"
        "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
        "AQo,AJo,ATo,A9o,A8o,A7o,A6o,A5o,A4o,A3o,A2o,"
        "K8s,K9s,KTs,KJs,KQs,KTo,KJo,KQo,"
        "Q2s,Q3s,Q4s,Q5s,Q6s,Q7s,Q8s,Q9s,QTs,QJs,Q8o,Q9o,QTo,QJo,"
        "J4s,J5s,J6s,J7s,J8s,J9s,JTs,J8o,J9o,JTo,"
        "T5s,T6s,T7s,T8s,T9s,T8o,T9o,"
        "95s,96s,97s,98s,98o,85s,86s,87s,87o,75s,76s,76o,64s,65s,65o,53s,54s,43s"
    ),
    "CoOpen100bb": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,A5o,A6o,A7o,A8o,A9o,"
        "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,"
        "QJs,QTs,Q9s,Q8s,QTo,QJo,"
        "JTs,JTo,J9s,J8s,T9s,T8s,98s,87s,76s,65s"
    ),
    "UtgOpen100bb": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AKo,AQs,AQo,AJs,AJo,ATs,KQs,KQo,KTs,KJs,QTs,QJs,JTs"
    ),
    "BbDefendVsCo": (
        "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
        "AKs,AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
        "AKo,AQo,AJo,ATo,A9o,A8o,A7o,"
        "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,"
        "QJs,QTs,Q9s,Q8s,Q7s,QJo,QTo,"
        "JTs,J9s,J8s,JTo,T9s,T8s,98s,97s,87s,76s,65s"
    ),
}


# リバーオンリー解析設定（5 枚ボード）
# bet_sizes_str: タスクごとに動的に決まる
CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,river,bet,{oop_river_sizes}
set_bet_sizes oop,river,allin
set_bet_sizes ip,river,bet,{ip_river_sizes}
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


def task_bet_sizes(task: str, scen: Dict[str, Any]) -> tuple[str, str]:
    """タスク別に IP/OOP river ベットサイズリスト（カンマ区切り %）を返す."""
    sizes = scen.get("bet_sizes_to_evaluate", [])
    if task == "103":
        # V:B 比: シナリオ指定の 25/43/55.5% を IP に与える
        pct_list = [str(int(round(s * 100))) for s in sizes] if sizes else ["25", "50", "75"]
        ip_sizes = ",".join(pct_list)
        oop_sizes = "50"
        return ip_sizes, oop_sizes
    if task == "106":
        # MDF: シナリオ指定の単一サイズを IP に与え、OOP の defense を見る
        pct_list = [str(int(round(s * 100))) for s in sizes] if sizes else ["75"]
        ip_sizes = ",".join(pct_list)
        oop_sizes = "75"
        return ip_sizes, oop_sizes
    # 105 / 108: 標準的な 33/75/150
    return "33,75,150", "50,100"


def build_config(scen: Dict[str, Any], task: str, dump_path: str) -> str:
    board_str = ",".join(scen["board"])
    pot = scen["pot_bb"]
    stack = scen["effective_stack_bb"]
    ip_range = resolve_range(scen["hero_range"])
    oop_range = resolve_range(scen["villain_range"])
    # hero が BB/SB の場合は IP/OOP を反転
    hero_pos = scen.get("hero_position", "BTN")
    if hero_pos in ("BB", "SB"):
        ip_range, oop_range = oop_range, ip_range
    ip_sizes, oop_sizes = task_bet_sizes(task, scen)
    return CONFIG_TEMPLATE.format(
        pot=pot, stack=stack, board=board_str,
        ip_range=ip_range, oop_range=oop_range,
        ip_river_sizes=ip_sizes, oop_river_sizes=oop_sizes,
        dump_path=dump_path,
    )


def run_solver(config_text: str, timeout: int = TIMEOUT_PER_SCENARIO) -> int:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_v4r_"
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


# ---------------------------------------------------------------------------
# 結果 JSON のパース
# ---------------------------------------------------------------------------

def aggregate_action_freq(node: Dict[str, Any]) -> Dict[str, float]:
    """ノードの strategy から action ごとの平均頻度を計算."""
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


def aggregate_for_task(result_json: Dict[str, Any], task: str) -> Dict[str, Any]:
    """root ノードから タスク別の指標を抽出."""
    summary: Dict[str, Any] = {}

    # Root の strategy（IP first-to-act on river）
    root_freqs = aggregate_action_freq(result_json)
    summary["ip_river_first_action_freq"] = root_freqs

    # bet サイズ別の OOP 反応（MDF 計算用）
    # root.childrens["BET XX"] → strategy が OOP の反応
    children = result_json.get("childrens", {})
    bet_responses: Dict[str, Dict[str, float]] = {}
    for child_key, child_node in children.items():
        if not child_key.startswith("BET"):
            continue
        oop_freqs = aggregate_action_freq(child_node)
        if oop_freqs:
            bet_responses[child_key] = oop_freqs
    summary["oop_response_to_bet"] = bet_responses

    # CHECK 後の OOP の挙動（OOP donk の頻度など）
    check_node = children.get("CHECK")
    if check_node:
        oop_after_check = aggregate_action_freq(check_node)
        summary["oop_after_ip_check"] = oop_after_check

    if task == "103":
        # V:B 比: bet ごとに OOP の fold 率を見る
        summary["alpha_implied"] = {
            k: round(v.get("FOLD", 0.0), 4)
            for k, v in bet_responses.items()
        }
    elif task == "106":
        # MDF: OOP の defense (1 - FOLD) を bet ごとに
        summary["mdf_measured"] = {
            k: round(1.0 - v.get("FOLD", 0.0), 4)
            for k, v in bet_responses.items()
        }
    return summary


# ---------------------------------------------------------------------------
# シナリオ実行
# ---------------------------------------------------------------------------

def solve_one(scen_path: Path, task: str, dry_run: bool = False) -> Dict[str, Any]:
    scen = json.loads(scen_path.read_text())
    sid = scen["scenario_id"]
    out_dir = RES_ROOT / task
    out_dir.mkdir(parents=True, exist_ok=True)
    dump_path = str(out_dir / f"{sid}_raw.json")

    config_text = build_config(scen, task, dump_path)
    if dry_run:
        return {"scenario_id": sid, "dry_run": True, "config": config_text}

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

    summary = aggregate_for_task(raw, task)
    return {
        "scenario_id": sid,
        "board": scen["board"],
        "pot_bb": scen["pot_bb"],
        "effective_stack_bb": scen["effective_stack_bb"],
        "elapsed_sec": round(elapsed, 1),
        "summary": summary,
    }


def run_task(task: str, limit: Optional[int] = None, dry_run: bool = False) -> None:
    scen_dir = SCEN_ROOT / task
    if not scen_dir.exists():
        print(f"❌ scenarios/{task}/ なし", file=sys.stderr)
        return
    out_dir = RES_ROOT / task
    out_dir.mkdir(parents=True, exist_ok=True)

    scen_files = sorted(scen_dir.glob("*.json"))
    scen_files = [p for p in scen_files if p.stem != "index"]
    if limit:
        scen_files = scen_files[:limit]

    print(f"\n=== Task #{task}: {len(scen_files)} シナリオ ===")
    summaries: List[Dict[str, Any]] = []
    total_elapsed = 0.0
    for i, scen_path in enumerate(scen_files, 1):
        print(f"  [{i}/{len(scen_files)}] {scen_path.stem}", end=" ... ", flush=True)
        result = solve_one(scen_path, task, dry_run=dry_run)
        if "error" in result:
            print(f"ERROR ({result.get('elapsed_sec', '?')}s): {result['error'][:60]}")
        elif "dry_run" in result:
            print("dry-run OK")
        else:
            elapsed = result.get("elapsed_sec", 0)
            total_elapsed += elapsed
            mdf = result["summary"].get("mdf_measured", {})
            alpha = result["summary"].get("alpha_implied", {})
            extra = ""
            if mdf:
                extra = "MDF=" + ",".join(f"{v:.2f}" for v in mdf.values())
            elif alpha:
                extra = "α=" + ",".join(f"{v:.2f}" for v in alpha.values())
            print(f"{elapsed:.1f}s {extra}")
        out_file = out_dir / f"{scen_path.stem}.json"
        out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        summaries.append(result)

    summary_path = out_dir / "summary.json"
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
    p.add_argument("--dry-run", action="store_true", help="solver を実行せず config 確認のみ")
    args = p.parse_args()

    if args.task == "all":
        for t in ["106", "103", "105", "108"]:
            run_task(t, args.limit, args.dry_run)
    else:
        run_task(args.task, args.limit, args.dry_run)


if __name__ == "__main__":
    main()
