#!/usr/bin/env python3
"""
study_5cat.py — 5類型フロップ調査 (TexasSolver, BTN_BB)

各ボード型ごとに 3 ボードを実行し、役スコア + ドロー種別で 5 類型に分類して
CBet% を集計する。

実行:
    python3 cash-postflop/study_5cat.py
    python3 cash-postflop/study_5cat.py --dry-run   # 設定確認のみ

出力:
    cash-postflop/findings/5cat_study.json
    cash-postflop/findings/5cat_summary.md
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
FINDINGS_DIR = Path(__file__).parent / "findings"
SCRIPT_DIR = Path(__file__).parent.parent / "scripts"

# ─── レンジ ───────────────────────────────────────────────────────────────────
IP_RANGE = (  # BTN open 100BB
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
    "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,T9s,T8s,T7s,T6s,"
    "98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)
OOP_RANGE = (  # BB defend vs BTN 2.5x 100BB
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
    "65s,64s,65o,54s,53s,43s"
)

POT = 7
STACK = 97

# ─── 調査ボード（3×7型） ──────────────────────────────────────────────────────
BOARDS = [
    # 型1 ハイドライ (K/A/Q 高, レインボー/ドライ)
    ("型1_ハイドライ", "Ks,7d,2c", "K高・レインボー"),
    ("型1_ハイドライ", "As,9d,3c", "A高・レインボー"),
    ("型1_ハイドライ", "Qs,7d,3c", "Q高・レインボー"),

    # 型2 ハイウェット (K/A/Q 高, 2トーン/コネクト)
    ("型2_ハイウェット", "Qh,8d,3s", "Q高・2トーン"),
    ("型2_ハイウェット", "Kh,9d,5s", "K高・2トーン"),
    ("型2_ハイウェット", "Ah,8s,5d", "A高・2トーン"),

    # 型3 ロードライ (ミドル以下, レインボー)
    ("型3_ロードライ", "Jd,7s,5c", "J中・レインボー"),
    ("型3_ロードライ", "9s,6d,2c", "9中・レインボー"),
    ("型3_ロードライ", "8d,5s,2c", "8低・レインボー"),

    # 型4 ローウェット (コネクト+2トーン)
    ("型4_ローウェット", "Th,9s,8d", "低連携・2トーン"),
    ("型4_ローウェット", "9h,8d,7s", "9連続・レインボー"),
    ("型4_ローウェット", "Jd,9s,8h", "J連携・2トーン"),

    # 型5 モノトーン (同スーツ3枚)
    ("型5_モノトーン", "Ah,9h,5h", "A高モノトーン"),
    ("型5_モノトーン", "Kd,7d,3d", "K高モノトーン"),
    ("型5_モノトーン", "Qh,8h,4h", "Q中モノトーン"),

    # 型6 ペア高 (高いペア)
    ("型6_ペア高", "As,Ac,Kd", "AAKペア"),
    ("型6_ペア高", "Kh,Kd,8c", "KK8ペア"),
    ("型6_ペア高", "Ah,Ad,Qs", "AAQペア"),

    # 型7 ペア低 (低いペア)
    ("型7_ペア低", "7s,7d,2c", "77低ペア"),
    ("型7_ペア低", "4s,4d,9c", "44中ペア"),
    ("型7_ペア低", "5h,5c,2d", "55低ペア"),
]

# ─── TexasSolver 設定 ─────────────────────────────────────────────────────────
CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,flop,bet,33,75
set_bet_sizes ip,flop,allin
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,allin
set_allin_threshold 0.67
build_tree
set_thread_num 2
set_accuracy 0.8
set_max_iteration 200
start_solve
dump_result {dump_path}
"""


def run_solver(config_text: str, timeout: int = 300) -> tuple[str, str, int]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as cf:
        cf.write(config_text)
        config_path = cf.name
    stdout_file = config_path + ".stdout"
    stderr_file = config_path + ".stderr"
    try:
        with open(stdout_file, "w") as fout, open(stderr_file, "w") as ferr:
            proc = subprocess.Popen(
                [SOLVER_BIN, "--input_file", config_path],
                stdout=fout,
                stderr=ferr,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = -1
    finally:
        os.unlink(config_path)
    return stdout_file, stderr_file, rc


def parse_combo_strategies(result_json: dict) -> dict[str, dict[str, float]]:
    """コンボ別アクション確率を返す: {combo: {action: prob}}"""
    root = result_json
    check_node = root.get("childrens", {}).get("CHECK")
    if check_node is None:
        return {}
    strat_wrapper = check_node.get("strategy", {})
    combo_strats = strat_wrapper.get("strategy", {})
    actions = strat_wrapper.get("actions", [])
    result: dict[str, dict[str, float]] = {}
    for combo, probs in combo_strats.items():
        result[combo] = {a: p for a, p in zip(actions, probs)}
    return result


def classify_5cat(role_score: int, _role_label: str, draw_label: str) -> str:
    """役スコア + ドロー種別で 5 類型に分類"""
    # "FD" check must NOT match "BDFD" (BDFD contains "FD" as substring)
    has_fd = draw_label in ("FD", "FD+GS") or "フラッシュ" in draw_label
    has_oesd = "OESD" in draw_label
    has_gs = "GS" in draw_label and "BDFD" not in draw_label  # pure gutshot
    has_bdfd = "BDFD" in draw_label

    if role_score >= 65:
        return "バリュー"
    if has_fd or has_oesd:
        return "ドロー"
    if role_score >= 35:
        return "ブラフキャッチャー"
    if has_gs or has_bdfd:
        return "ウィークドロー"
    return "エアー"


def analyze_board(board_str: str, result_json: dict) -> dict:
    """TexasSolver 結果から 5 類型別 CBet% を計算"""
    sys.path.insert(0, str(SCRIPT_DIR))
    from hand_evaluator_v3 import _classify_role, _calc_draw_bonus
    from hand_evaluator_v2 import parse_board, parse_combo

    board_cards = parse_board(board_str.replace(",", ""))
    combo_strats = parse_combo_strategies(result_json)

    categories = {
        "バリュー": {"bet_prob_sum": 0.0, "n": 0},
        "ドロー": {"bet_prob_sum": 0.0, "n": 0},
        "ブラフキャッチャー": {"bet_prob_sum": 0.0, "n": 0},
        "ウィークドロー": {"bet_prob_sum": 0.0, "n": 0},
        "エアー": {"bet_prob_sum": 0.0, "n": 0},
    }

    for combo_str, action_probs in combo_strats.items():
        try:
            combo = parse_combo(combo_str)
        except Exception:
            continue
        role_score, _ = _classify_role(combo, board_cards)
        has_made = role_score > 0
        _, draw_label = _calc_draw_bonus(combo, board_cards, "flop", has_made)
        cat = classify_5cat(role_score, "", draw_label)

        bet_prob = sum(v for k, v in action_probs.items() if k != "CHECK")
        categories[cat]["bet_prob_sum"] += bet_prob
        categories[cat]["n"] += 1

    return {
        cat: {
            "cbet_pct": round(v["bet_prob_sum"] / v["n"] * 100, 1) if v["n"] > 0 else 0.0,
            "n": v["n"],
        }
        for cat, v in categories.items()
    }


def run_one_board(args: tuple) -> dict:
    board_type, board_str, desc = args
    print(f"  [{board_type}] {board_str} ({desc}) 開始…", flush=True)
    t0 = time.time()

    with tempfile.TemporaryDirectory() as tmpdir:
        dump_path = os.path.join(tmpdir, "result.json")
        config = CONFIG_TEMPLATE.format(
            pot=POT,
            stack=STACK,
            board=board_str,
            ip_range=IP_RANGE,
            oop_range=OOP_RANGE,
            dump_path=dump_path,
        )
        stdout_f, stderr_f, rc = run_solver(config, timeout=360)

        elapsed = time.time() - t0
        status = "OK" if rc in (0, -6) else f"ERR({rc})"

        result_data = None
        analysis = None
        if os.path.exists(dump_path):
            with open(dump_path) as f:
                result_data = json.load(f)
            analysis = analyze_board(board_str, result_data)

        # cleanup temp stdout/stderr
        for p in (stdout_f, stderr_f):
            try:
                os.unlink(p)
            except OSError:
                pass

    print(f"  [{board_type}] {board_str} → {status} ({elapsed:.0f}s)", flush=True)
    return {
        "board_type": board_type,
        "board": board_str,
        "desc": desc,
        "status": status,
        "elapsed_s": round(elapsed, 1),
        "analysis": analysis,
    }


def build_markdown(results: list[dict]) -> str:
    lines = ["# 5類型 CBet% 調査結果（BTN_BB, TexasSolver）\n"]
    lines.append(f"実行日: {time.strftime('%Y-%m-%d')}\n")

    cat_order = ["バリュー", "ドロー", "ブラフキャッチャー", "ウィークドロー", "エアー"]
    header = "| ボード型 | ボード | " + " | ".join(cat_order) + " |\n"
    sep = "|" + "---|" * (2 + len(cat_order)) + "\n"

    # Group by type
    from collections import defaultdict
    by_type: dict[str, list] = defaultdict(list)
    for r in results:
        by_type[r["board_type"]].append(r)

    for btype, rows in sorted(by_type.items()):
        lines.append(f"\n## {btype}\n")
        lines.append(header)
        lines.append(sep)
        for r in rows:
            if not r.get("analysis"):
                lines.append(f"| {btype} | {r['board']} ({r['desc']}) | エラー |\n")
                continue
            a = r["analysis"]
            vals = [f"{a[c]['cbet_pct']}% (n={a[c]['n']})" for c in cat_order]
            lines.append(f"| {btype} | `{r['board']}` ({r['desc']}) | " + " | ".join(vals) + " |\n")

    lines.append("\n## 5類型の定義\n\n")
    lines.append("| 類型 | HS基準 | ドロー条件 |\n")
    lines.append("|------|--------|----------|\n")
    lines.append("| バリュー | role ≥ 65 | — |\n")
    lines.append("| ドロー | any | OESD / FD |\n")
    lines.append("| ブラフキャッチャー | 35 ≤ role < 65 | OESD/FD なし |\n")
    lines.append("| ウィークドロー | role < 35 | GS / BDFD |\n")
    lines.append("| エアー | role < 35 | ドローなし |\n")

    return "".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--type", default="", help="特定の型のみ実行 (例: 型1_ハイドライ)")
    args = parser.parse_args()

    boards = BOARDS
    if args.type:
        boards = [b for b in boards if b[0] == args.type]
    if not boards:
        print("マッチするボードなし")
        return

    print(f"=== 5類型調査 ===  {len(boards)} ボード, workers={args.workers}")
    for b in boards:
        print(f"  {b[0]:20s} {b[1]:15s} {b[2]}")

    if args.dry_run:
        print("\n--dry-run: 実行せずに終了")
        return

    FINDINGS_DIR.mkdir(exist_ok=True)

    results: list[dict] = []
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(run_one_board, b): b for b in boards}
        for fut in as_completed(futures):
            try:
                results.append(fut.result())
            except Exception as e:
                b = futures[fut]
                print(f"  ERROR {b[1]}: {e}")
                results.append({
                    "board_type": b[0], "board": b[1], "desc": b[2],
                    "status": f"EXCEPTION: {e}", "analysis": None
                })

    # Sort by board order
    order = {b[1]: i for i, b in enumerate(BOARDS)}
    results.sort(key=lambda r: order.get(r["board"], 99))

    out_json = FINDINGS_DIR / "5cat_study.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    out_md = FINDINGS_DIR / "5cat_summary.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(build_markdown(results))

    print(f"\n完了: {out_json}")
    print(f"     {out_md}")
    ok = sum(1 for r in results if r.get("analysis"))
    print(f"成功: {ok}/{len(results)} ボード")


if __name__ == "__main__":
    main()
