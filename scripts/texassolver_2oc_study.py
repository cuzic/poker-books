#!/usr/bin/env python3
"""2OC（2オーバーカード）加点+24の妥当性 GTO 検証スクリプト.

研究設問:
  ドライ低ボード (7♣4♦2♠) で OOP(BB) が IP(BTN) の CBet を受けるとき、
  「純粋2OC」手牌（AKo, AQo, KQo 等）の GTO fold 率はどのくらいか？
  → HandScore 式: HS_air≈10-20 + 2OC=+24 → 合計34-44 が妥当か検証。

ボード選択: 7♣4♦2♠
  - rainbow, max=7 → A/K/Q/J/T/9/8 すべてが OC
  - BB レンジに AKo, AQo, KQo, QJo = 純2OC が多数含まれる
  - 7/4/2 でセット勢も分散、ボードが空振りしやすい理想的な検証板

検証指標:
  各 CBet サイズ (33%, 50%, 75%) に対して：
  1. 純2OC 手牌群 (AKo, AQo, AJs, KQo, QJo) の avg_fold%
  2. 純air  手牌群 (T8o, 96o 等 overcard なし) の avg_fold%
  3. ΔEV ≒ fold 率差 → 2OC 加点 +24 の妥当性を評価

期待仮説:
  「一時的ペア化」の価値 ≈ 6 outs × 2 (ターン1枚期待) ≈ 12 が正味価値
  +24 (Rule-of-4) は2ストリート分で過大評価の可能性あり
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/flop/results/2oc_study")

BOARD = "7c,4d,2s"  # dry rainbow, max=7
POT = 7             # BTN 2.5x open → BB call
STACK = 97

# BTN open range (IP)
IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
    "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,T9s,T8s,T7s,T6s,98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)

# BB defend range (OOP)
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


def run_solver(dump_path: str, timeout: int = 360) -> int:
    config = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=BOARD,
        ip_range=IP_RANGE, oop_range=OOP_RANGE, dump_path=dump_path,
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
        try: os.unlink(cfg)
        except OSError: pass


def get_oop_response_node(raw: dict, bet_pct: int) -> dict | None:
    """OOP check → IP bet X → OOP response ノード."""
    check_node = raw.get("childrens", {}).get("CHECK")
    if not check_node:
        return None
    expected = POT * bet_pct / 100.0
    for key, node in check_node.get("childrens", {}).items():
        if not key.startswith("BET"):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        if abs(amt - expected) < 1.5:
            return node
    return None


def board_ranks(board: str) -> set[int]:
    """ボードカードのランク集合 (A=14, K=13, ...)"""
    rank_map = {"A":14,"K":13,"Q":12,"J":11,"T":10,"9":9,"8":8,"7":7,"6":6,"5":5,"4":4,"3":3,"2":2}
    return {rank_map[c[0].upper()] for c in board.split(",")}


def combo_is_2oc(combo: str, board_rank_set: set[int]) -> bool:
    """コンボが純粋2OC（両カードともボード最大より高い、ポケットペア除外）か判定."""
    rank_map = {"A":14,"K":13,"Q":12,"J":11,"T":10,"9":9,"8":8,"7":7,"6":6,"5":5,"4":4,"3":3,"2":2}
    max_board = max(board_rank_set)
    r0 = rank_map.get(combo[0].upper(), 0)
    r1 = rank_map.get(combo[2].upper(), 0)
    # ポケットペアを除外（オーバーペアは別カテゴリ）
    if r0 == r1:
        return False
    # 両カードともボード最大より高く、かつボード上のカードとペアにならない
    return r0 > max_board and r1 > max_board and r0 not in board_rank_set and r1 not in board_rank_set


def combo_is_pure_air(combo: str, board_rank_set: set[int]) -> bool:
    """純粋air: ボード最大(=7)未満の両カード、かつペアなし."""
    rank_map = {"A":14,"K":13,"Q":12,"J":11,"T":10,"9":9,"8":8,"7":7,"6":6,"5":5,"4":4,"3":3,"2":2}
    max_board = max(board_rank_set)
    r0 = rank_map.get(combo[0].upper(), 0)
    r1 = rank_map.get(combo[2].upper(), 0)
    # 両カードともボード内のどのカードともペアにならず、かつ8以下（OC なし）
    if r0 in board_rank_set or r1 in board_rank_set:
        return False
    return r0 <= max_board and r1 <= max_board


def extract_fold_stats(response_node: dict, board_rank_set: set[int], category: str) -> dict:
    """カテゴリに合致するコンボの fold 率を集計."""
    strat = response_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        fold_idx = actions.index("FOLD")
    except ValueError:
        return {"error": f"FOLD not in {actions}"}

    matched_folds = []
    matched_combos = []
    for combo, probs in combos.items():
        if category == "2OC" and combo_is_2oc(combo, board_rank_set):
            matched_combos.append(combo)
            matched_folds.append(probs[fold_idx] if fold_idx < len(probs) else 0.0)
        elif category == "air" and combo_is_pure_air(combo, board_rank_set):
            matched_combos.append(combo)
            matched_folds.append(probs[fold_idx] if fold_idx < len(probs) else 0.0)

    if not matched_folds:
        return {"error": f"no combos for {category}", "n": 0}

    avg_fold = sum(matched_folds) / len(matched_folds)
    return {
        "n": len(matched_combos),
        "avg_fold_pct": round(avg_fold * 100, 1),
        "combos_sample": matched_combos[:8],
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dump_path = str(OUT_DIR / "742r_oop_study.json")

    if Path(dump_path).exists():
        print(f"キャッシュ済み結果を利用: {dump_path}")
    else:
        print(f"TexasSolver 実行中 (Board: {BOARD}, CBet 33/50/75%) ...")
        t0 = time.time()
        rc = run_solver(dump_path)
        elapsed = time.time() - t0
        if rc != 0 or not Path(dump_path).exists():
            print(f"ERROR: solver rc={rc}")
            return
        print(f"完了: {elapsed:.0f}s")

    raw: Any = json.loads(Path(dump_path).read_text())
    board_rank_set = board_ranks(BOARD)
    max_board = max(board_rank_set)
    print(f"\nBoard: {BOARD}  (max rank={max_board}: {[c for c in '234567'][max_board-2] if max_board<=7 else max_board})")
    print(f"OOP (BB) が IP (BTN) の CBet を受けるシナリオ")
    print(f"\n{'CBet':>8} | {'2OC fold%':>12} | {'air fold%':>12} | {'fold Δ':>8} | {'2OC n':>6} | {'air n':>6}")
    print("-" * 65)

    cbet_sizes = [33, 50, 75]
    results = {}

    for pct in cbet_sizes:
        node = get_oop_response_node(raw, pct)
        if node is None:
            print(f"  {pct:>5}% | ノードなし")
            continue

        stats_2oc = extract_fold_stats(node, board_rank_set, "2OC")
        stats_air = extract_fold_stats(node, board_rank_set, "air")

        fold_2oc = stats_2oc.get("avg_fold_pct", float("nan"))
        fold_air = stats_air.get("avg_fold_pct", float("nan"))
        delta = fold_air - fold_2oc if isinstance(fold_2oc, float) and isinstance(fold_air, float) else float("nan")

        print(f"  {pct:>5}% | {fold_2oc:>11.1f}% | {fold_air:>11.1f}% | {delta:>+7.1f}% | {stats_2oc.get('n',0):>6} | {stats_air.get('n',0):>6}")
        results[pct] = {"2oc": stats_2oc, "air": stats_air}

    # ── サンプルコンボ詳細 (50% CBet) ──────────────────────────────────────────
    print("\n=== 50% CBet 詳細: 2OC サンプルコンボ ===")
    node50 = get_oop_response_node(raw, 50)
    if node50:
        strat = node50.get("strategy", {})
        actions = strat.get("actions", [])
        combos = strat.get("strategy", {})
        try:
            fold_idx = actions.index("FOLD")
            call_idx = actions.index("CALL")
        except ValueError:
            fold_idx = call_idx = -1

        print(f"{'combo':>8} | {'fold%':>8} | {'call%':>8} | {'raise%':>8}")
        print("-" * 40)
        shown = 0
        for combo, probs in sorted(combos.items()):
            if not combo_is_2oc(combo, board_rank_set):
                continue
            fold_p = probs[fold_idx] * 100 if fold_idx >= 0 and fold_idx < len(probs) else 0
            call_p = probs[call_idx] * 100 if call_idx >= 0 and call_idx < len(probs) else 0
            raise_p = 100 - fold_p - call_p
            print(f"  {combo:>6} | {fold_p:>7.1f}% | {call_p:>7.1f}% | {raise_p:>7.1f}%")
            shown += 1
            if shown >= 20:
                break

    # ── HandScore 評価 ────────────────────────────────────────────────────────
    print("\n=== HandScore 式との照合 ===")
    print("2OC の HandScore: air_base(10~20) + 2OC(+24) = 34~44")
    print("C 閾値: 33%=11 / 50%=17 / 75%=22")
    print("→ 式の予測: 2OC は 33%/50%/75% すべて CALL (HS≥C)")
    print()

    node50 = get_oop_response_node(raw, 50)
    if node50:
        s2oc = extract_fold_stats(node50, board_rank_set, "2OC")
        fold_pct = s2oc.get("avg_fold_pct", 0)
        print(f"GTO実測 (50% CBet): 2OC fold {fold_pct:.1f}% / call {100-fold_pct:.1f}%")
        if fold_pct > 30:
            print("→ GTO は 2OC を多くフォールド → +24 は過大評価の可能性大")
        elif fold_pct > 10:
            print("→ GTO は 2OC を部分的にフォールド → +24 はやや過大の可能性")
        else:
            print("→ GTO は 2OC をほぼコール → +24 は概ね妥当")


if __name__ == "__main__":
    main()
