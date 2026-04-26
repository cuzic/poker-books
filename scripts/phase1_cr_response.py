#!/usr/bin/env python3
"""チェックレイズ応答 IP 判断検証スクリプト.

OOP チェックレイズに対する IP の fold/call/reraise 頻度を
HandScore バケツ別に集計し、CR 応答閾値を検証する。

検証目的:
  H ≥ 18 → リレイズ/オールイン
  H 15-17 → コール
  H < 15  → フォールド
  の閾値が正しいか

使用方法:
    python3 scripts/phase1_cr_response.py --board Kc,7d,2s
    python3 scripts/phase1_cr_response.py --board Kh,Jd,7s --no-solve
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(__file__))
from hand_evaluator import evaluate, bucket

RESULTS_DIR = "/home/cuzic/poker-books/knowledges/volume4/results/phase1"
POT = 7


def find_bet_node(childrens: dict, target_pct: int) -> tuple[str, dict] | tuple[None, None]:
    """指定 % に最も近い BET ノードを返す."""
    target_chips = target_pct / 100 * POT
    best_key, best_node, best_diff = None, None, float("inf")
    for k, v in childrens.items():
        if not k.startswith("BET"):
            continue
        try:
            chips = float(k.split()[1])
            diff = abs(chips - target_chips)
            if diff < best_diff:
                best_diff = diff
                best_key, best_node = k, v
        except (IndexError, ValueError):
            continue
    return best_key, best_node


def parse_ip_cr_response(result: dict, board: str, cbet_pct: int = 33, cr_pct: int = 100) -> dict:
    """IP のチェックレイズ応答 fold/call/reraise を HandScore バケツ別に集計する.

    JSON パス: root → CHECK → BET {cbet} → RAISE {cr} → strategy
    actions: ['FOLD', 'CALL', 'RAISE ...', 'ALLIN']
    """
    check_node = result.get("childrens", {}).get("CHECK", {})

    # IP CBet ノード
    cbet_key, cbet_node = find_bet_node(check_node.get("childrens", {}), cbet_pct)
    if cbet_node is None:
        return {}

    # OOP チェックレイズノード
    cr_key, cr_node = find_bet_node(cbet_node.get("childrens", {}), cr_pct * 3)
    if cr_node is None:
        # フォールバック: RAISE キーを探す
        for k, v in cbet_node.get("childrens", {}).items():
            if "RAISE" in k or "ALLIN" in k:
                cr_key, cr_node = k, v
                break
    if cr_node is None:
        return {}

    strat_wrapper = cr_node.get("strategy", {})
    combo_strats = strat_wrapper.get("strategy", {})
    actions = strat_wrapper.get("actions", [])

    if not combo_strats:
        return {}

    fold_idx = next((i for i, a in enumerate(actions) if a == "FOLD"), None)
    call_idx = next((i for i, a in enumerate(actions) if a == "CALL"), None)
    reraise_idxs = [i for i, a in enumerate(actions) if "RAISE" in a or "ALLIN" in a]

    board_norm = ",".join(
        board.replace(",", "").replace(" ", "")[i:i+2]
        for i in range(0, len(board.replace(",", "").replace(" ", "")), 2)
    )

    bucket_stats: dict[str, dict] = defaultdict(
        lambda: {"fold": [], "call": [], "reraise": []}
    )

    for combo, probs in combo_strats.items():
        try:
            score, _ = evaluate(combo, board_norm)
            b = bucket(score)
            h = score
        except Exception:
            continue

        f_prob = probs[fold_idx] if fold_idx is not None and fold_idx < len(probs) else 0.0
        c_prob = probs[call_idx] if call_idx is not None and call_idx < len(probs) else 0.0
        r_prob = sum(probs[i] for i in reraise_idxs if i < len(probs))

        # H スコア別で記録 (バケツだけでなく詳細も)
        bucket_stats[b]["fold"].append(f_prob)
        bucket_stats[b]["call"].append(c_prob)
        bucket_stats[b]["reraise"].append(r_prob)

    result_rows = {}
    for b, stats in bucket_stats.items():
        n = len(stats["fold"])
        if n == 0:
            continue
        result_rows[b] = {
            "n": n,
            "fold_pct": round(sum(stats["fold"]) / n * 100, 1),
            "call_pct": round(sum(stats["call"]) / n * 100, 1),
            "reraise_pct": round(sum(stats["reraise"]) / n * 100, 1),
        }
    return result_rows


def board_to_slug(board: str) -> str:
    return board.replace(",", "").replace(" ", "").lower()


def main() -> None:
    parser = argparse.ArgumentParser(description="チェックレイズ応答 IP 判断検証")
    parser.add_argument("--board", default="Kc,7d,2s")
    parser.add_argument("--cbet-pct", type=int, default=33, help="IP CBet サイズ (%)")
    parser.add_argument("--no-solve", action="store_true", help="既存 JSON を再利用")
    args = parser.parse_args()

    board = args.board
    slug = board_to_slug(board)
    out_dir = os.path.join(RESULTS_DIR, slug)
    json_path = os.path.join(out_dir, "defender_result.json")

    if not os.path.exists(json_path):
        print(f"ERROR: {json_path} が存在しません。先に phase1_defender.py を実行してください。",
              file=sys.stderr)
        sys.exit(1)

    with open(json_path) as f:
        result = json.load(f)

    rows = parse_ip_cr_response(result, board, cbet_pct=args.cbet_pct)

    if not rows:
        print(f"WARNING: チェックレイズノードが見つかりませんでした。", file=sys.stderr)
        print("ツリーに IP の re-raise サイズが含まれているか確認してください。", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== IP のチェックレイズ応答: {board} (IP CBet {args.cbet_pct}%) ===")
    print(f"{'バケツ':>4}  {'N':>5}  {'Fold%':>6}  {'Call%':>6}  {'Reraise%':>9}  閾値確認")
    print("-" * 65)

    for b in ["H3", "H2", "H1"]:
        if b not in rows:
            continue
        r = rows[b]
        H_center = {"H3": 17, "H2": 11, "H1": 4}[b]
        if H_center >= 18:
            expected = "reraise"
        elif H_center >= 15:
            expected = "call"
        else:
            expected = "fold"
        actual_max = max(r["fold_pct"], r["call_pct"], r["reraise_pct"])
        actual = (
            "reraise" if r["reraise_pct"] == actual_max else
            ("call" if r["call_pct"] == actual_max else "fold")
        )
        match = "✓" if expected == actual else "✗"
        print(
            f"  {b}  N={r['n']:4d}  "
            f"Fold={r['fold_pct']:5.1f}%  Call={r['call_pct']:5.1f}%  Reraise={r['reraise_pct']:5.1f}%"
            f"  expect={expected} {match}"
        )

    # CSV 保存
    csv_path = os.path.join(out_dir, "cr_response_summary.csv")
    with open(csv_path, "w") as f:
        f.write("board,cbet_pct,bucket,n,fold_pct,call_pct,reraise_pct\n")
        for b, r in rows.items():
            f.write(f"{board},{args.cbet_pct},{b},{r['n']},{r['fold_pct']},{r['call_pct']},{r['reraise_pct']}\n")
    print(f"\n結果を保存: {csv_path}")


if __name__ == "__main__":
    main()
