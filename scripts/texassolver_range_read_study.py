#!/usr/bin/env python3
"""
texassolver_range_read_study.py - range_read デッキ用 GTO データ収集

戦略:
  Stage A) フロップ 3 枚ボード × 8 テクスチャ を解析
           → CBet+Call 後の OOP フィルタリングレンジを抽出
  Stage B) ターン 4 枚ボード × 24 シナリオ (8 フロップ × 3 ターンカード) を解析
           → ターン開始時の両プレイヤーレンジ構成を抽出

使用方法:
    python3 scripts/texassolver_range_read_study.py [--stage A|B|all] [--dry-run] [--resume]

出力:
    knowledges/range_read/results/range_read_data.json
    knowledges/range_read/RESEARCH_UPDATED.md
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
from typing import Any

# ---------------------------------------------------------------------------
# パス定数
# ---------------------------------------------------------------------------
SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
SCRIPTS_DIR = Path("/home/cuzic/poker-books/scripts")
OUTPUT_DIR = Path("/home/cuzic/poker-books/knowledges/range_read/results")
OUTPUT_JSON = OUTPUT_DIR / "range_read_data.json"
OUTPUT_MD = Path("/home/cuzic/poker-books/knowledges/range_read/RESEARCH_UPDATED.md")

TIMEOUT = 300  # 秒

# ---------------------------------------------------------------------------
# プリフロップレンジ (BTN vs BB, 100BB SRP)
# ---------------------------------------------------------------------------
BTN_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
    "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,"
    "T9s,T8s,T7s,T6s,"
    "98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)

BB_RANGE = (
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

# ---------------------------------------------------------------------------
# シナリオ定義
# ---------------------------------------------------------------------------
# Stage A: フロップ 3 枚ボード
FLOP_SCENARIOS = [
    {
        "id": "K73r",
        "board": "Kc,7d,2s",
        "label": "K73r ドライ (K-high rainbow)",
        "nut_adv": "IP有利",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "A72r",
        "board": "Ac,7d,2s",
        "label": "A72r ドライ (A-high rainbow)",
        "nut_adv": "IP有利",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "JT5r",
        "board": "Jc,Td,5s",
        "label": "JT5r セミウェット broadway connected",
        "nut_adv": "中立",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "987r",
        "board": "9s,8d,7c",
        "label": "987r コネクテッド low 3-connected",
        "nut_adv": "OOP有利",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "K72fd",
        "board": "Ks,7s,2h",
        "label": "K72 フラッシュドロー (K-high + FD)",
        "nut_adv": "IP有利",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "JT5fd",
        "board": "Js,Ts,5h",
        "label": "JT5 フラッシュドロー (connected + FD)",
        "nut_adv": "中立",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "QQ4r",
        "board": "Qc,Qd,4s",
        "label": "QQ4r ペアボード high (IP有利)",
        "nut_adv": "IP有利",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "AKTr",
        "board": "Ac,Kd,Ts",
        "label": "AKTr broadway ドライ",
        "nut_adv": "IP有利",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "T86r",
        "board": "Tc,8d,6s",
        "label": "T86r コネクテッド middle",
        "nut_adv": "OOP有利",
        "pot": 7,
        "stack": 96,
    },
    {
        "id": "K75mono",
        "board": "Ks,7s,5s",
        "label": "K75s モノトーン (フラッシュ済み)",
        "nut_adv": "中立",
        "pot": 7,
        "stack": 96,
    },
]

# Stage B: ターン 4 枚ボード (フロップ × ターンカード)
TURN_SCENARIOS = [
    # K73r × 3 turn cards
    {"id": "K73r_As", "board": "Kc,7d,2s,Ah", "flop_id": "K73r",
     "turn_card": "Ah", "turn_type": "OC_ace", "label": "K73r + A♥ (オーバーカード Ace)",
     "pot": 14, "stack": 89},  # after 33% CBet + call
    {"id": "K73r_9d", "board": "Kc,7d,2s,9d", "flop_id": "K73r",
     "turn_card": "9d", "turn_type": "blank", "label": "K73r + 9♦ (ブランク)",
     "pot": 14, "stack": 89},
    {"id": "K73r_7h", "board": "Kc,7d,2s,7h", "flop_id": "K73r",
     "turn_card": "7h", "turn_type": "pair", "label": "K73r + 7♥ (ペア)",
     "pot": 14, "stack": 89},

    # A72r × 3 turn cards
    {"id": "A72r_Kh", "board": "Ac,7d,2s,Kh", "flop_id": "A72r",
     "turn_card": "Kh", "turn_type": "OC_king", "label": "A72r + K♥ (オーバーカード King)",
     "pot": 14, "stack": 89},
    {"id": "A72r_9d", "board": "Ac,7d,2s,9d", "flop_id": "A72r",
     "turn_card": "9d", "turn_type": "blank", "label": "A72r + 9♦ (ブランク)",
     "pot": 14, "stack": 89},
    {"id": "A72r_7h", "board": "Ac,7d,2s,7h", "flop_id": "A72r",
     "turn_card": "7h", "turn_type": "pair", "label": "A72r + 7♥ (ペア)",
     "pot": 14, "stack": 89},

    # JT5r × 3 turn cards
    {"id": "JT5r_Ah", "board": "Jc,Td,5s,Ah", "flop_id": "JT5r",
     "turn_card": "Ah", "turn_type": "OC_ace", "label": "JT5r + A♥ (オーバーカード Ace)",
     "pot": 14, "stack": 89},
    {"id": "JT5r_9d", "board": "Jc,Td,5s,9d", "flop_id": "JT5r",
     "turn_card": "9d", "turn_type": "straight", "label": "JT5r + 9♦ (ストレートコンプリート)",
     "pot": 14, "stack": 89},
    {"id": "JT5r_6h", "board": "Jc,Td,5s,6h", "flop_id": "JT5r",
     "turn_card": "6h", "turn_type": "blank_low", "label": "JT5r + 6♥ (ブランク low)",
     "pot": 14, "stack": 89},

    # 987r × 3 turn cards
    {"id": "987r_6s", "board": "9s,8d,7c,6h", "flop_id": "987r",
     "turn_card": "6h", "turn_type": "straight", "label": "987r + 6♥ (ストレートコンプリート)",
     "pot": 14, "stack": 89},
    {"id": "987r_Td", "board": "9s,8d,7c,Td", "flop_id": "987r",
     "turn_card": "Td", "turn_type": "OC_ten", "label": "987r + T♦ (オーバーカード Ten)",
     "pot": 14, "stack": 89},
    {"id": "987r_9h", "board": "9s,8d,7c,9h", "flop_id": "987r",
     "turn_card": "9h", "turn_type": "pair", "label": "987r + 9♥ (ペア)",
     "pot": 14, "stack": 89},

    # K72fd × 3 turn cards
    {"id": "K72fd_3s", "board": "Ks,7s,2h,3s", "flop_id": "K72fd",
     "turn_card": "3s", "turn_type": "flush_hit", "label": "K72fd + 3♠ (フラッシュ完成)",
     "pot": 14, "stack": 89},
    {"id": "K72fd_Ah", "board": "Ks,7s,2h,Ah", "flop_id": "K72fd",
     "turn_card": "Ah", "turn_type": "OC_ace", "label": "K72fd + A♥ (オーバーカード Ace)",
     "pot": 14, "stack": 89},
    {"id": "K72fd_7h", "board": "Ks,7s,2h,7h", "flop_id": "K72fd",
     "turn_card": "7h", "turn_type": "pair", "label": "K72fd + 7♥ (ペア)",
     "pot": 14, "stack": 89},

    # JT5fd × 3 turn cards
    {"id": "JT5fd_2s", "board": "Js,Ts,5h,2s", "flop_id": "JT5fd",
     "turn_card": "2s", "turn_type": "flush_hit", "label": "JT5fd + 2♠ (フラッシュ完成)",
     "pot": 14, "stack": 89},
    {"id": "JT5fd_Ah", "board": "Js,Ts,5h,Ah", "flop_id": "JT5fd",
     "turn_card": "Ah", "turn_type": "OC_ace", "label": "JT5fd + A♥ (オーバーカード Ace)",
     "pot": 14, "stack": 89},
    {"id": "JT5fd_9s", "board": "Js,Ts,5h,9s", "flop_id": "JT5fd",
     "turn_card": "9s", "turn_type": "straight_fd", "label": "JT5fd + 9♠ (ストレート + FD同時)",
     "pot": 14, "stack": 89},

    # QQ4r × 3 turn cards
    {"id": "QQ4r_Ah", "board": "Qc,Qd,4s,Ah", "flop_id": "QQ4r",
     "turn_card": "Ah", "turn_type": "OC_ace", "label": "QQ4r + A♥ (オーバーカード Ace)",
     "pot": 14, "stack": 89},
    {"id": "QQ4r_Kd", "board": "Qc,Qd,4s,Kd", "flop_id": "QQ4r",
     "turn_card": "Kd", "turn_type": "OC_king", "label": "QQ4r + K♦ (オーバーカード King)",
     "pot": 14, "stack": 89},
    {"id": "QQ4r_4h", "board": "Qc,Qd,4s,4h", "flop_id": "QQ4r",
     "turn_card": "4h", "turn_type": "pair", "label": "QQ4r + 4♥ (ペア)",
     "pot": 14, "stack": 89},

    # AKTr × 3 turn cards
    {"id": "AKTr_Qs", "board": "Ac,Kd,Ts,Qh", "flop_id": "AKTr",
     "turn_card": "Qh", "turn_type": "straight", "label": "AKTr + Q♥ (ブロードウェイストレート)",
     "pot": 14, "stack": 89},
    {"id": "AKTr_5d", "board": "Ac,Kd,Ts,5d", "flop_id": "AKTr",
     "turn_card": "5d", "turn_type": "blank", "label": "AKTr + 5♦ (ブランク)",
     "pot": 14, "stack": 89},
    {"id": "AKTr_As", "board": "Ac,Kd,Ts,As", "flop_id": "AKTr",
     "turn_card": "As", "turn_type": "pair", "label": "AKTr + A♠ (ペア Ace)",
     "pot": 14, "stack": 89},

    # T86r × 3 turn cards
    {"id": "T86r_7h", "board": "Tc,8d,6s,7h", "flop_id": "T86r",
     "turn_card": "7h", "turn_type": "straight", "label": "T86r + 7♥ (ストレートコンプリート)",
     "pot": 14, "stack": 89},
    {"id": "T86r_Ah", "board": "Tc,8d,6s,Ah", "flop_id": "T86r",
     "turn_card": "Ah", "turn_type": "OC_ace", "label": "T86r + A♥ (オーバーカード Ace)",
     "pot": 14, "stack": 89},
    {"id": "T86r_Td", "board": "Tc,8d,6s,Td", "flop_id": "T86r",
     "turn_card": "Td", "turn_type": "pair", "label": "T86r + T♦ (ペア)",
     "pot": 14, "stack": 89},

    # K75mono × 3 turn cards
    {"id": "K75m_3s", "board": "Ks,7s,5s,3h", "flop_id": "K75mono",
     "turn_card": "3h", "turn_type": "blank", "label": "K75s + 3♥ (ブランク off-suit)",
     "pot": 14, "stack": 89},
    {"id": "K75m_As", "board": "Ks,7s,5s,As", "flop_id": "K75mono",
     "turn_card": "As", "turn_type": "flush_hit", "label": "K75s + A♠ (フラッシュ 2枚目スート)",
     "pot": 14, "stack": 89},
    {"id": "K75m_7h", "board": "Ks,7s,5s,7h", "flop_id": "K75mono",
     "turn_card": "7h", "turn_type": "pair", "label": "K75s + 7♥ (ペア)",
     "pot": 14, "stack": 89},
]


# ---------------------------------------------------------------------------
# TexasSolver 実行関数
# ---------------------------------------------------------------------------

def build_flop_config(scenario: dict[str, Any], dump_path: str) -> str:
    """フロップ 3 枚ボード用 config を生成."""
    return f"""\
set_pot {scenario['pot']}
set_effective_stack {scenario['stack']}
set_board {scenario['board']}
set_range_ip {BTN_RANGE}
set_range_oop {BB_RANGE}
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes ip,flop,allin
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,turn,bet,33,75
set_bet_sizes ip,turn,allin
set_bet_sizes oop,turn,bet,50,100
set_bet_sizes oop,turn,allin
set_bet_sizes ip,river,bet,50
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,50
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 300
start_solve
dump_result {dump_path}
"""


def build_turn_config(scenario: dict[str, Any], dump_path: str) -> str:
    """ターン 4 枚ボード用 config を生成."""
    return f"""\
set_pot {scenario['pot']}
set_effective_stack {scenario['stack']}
set_board {scenario['board']}
set_range_ip {BTN_RANGE}
set_range_oop {BB_RANGE}
set_bet_sizes ip,turn,bet,33,75
set_bet_sizes ip,turn,allin
set_bet_sizes oop,turn,bet,50,100
set_bet_sizes oop,turn,allin
set_bet_sizes ip,river,bet,50
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,50
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 200
start_solve
dump_result {dump_path}
"""


def run_solver(config_str: str, scenario_id: str, dry_run: bool = False) -> dict[str, Any] | None:
    """TexasSolver を実行して結果 JSON を返す."""
    dump_path = str(OUTPUT_DIR / f"{scenario_id}_raw.json")

    if dry_run:
        print(f"  [dry-run] {scenario_id}: config generated, skipping solve")
        return None

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(config_str)
        config_file = f.name

    stdout_log = str(OUTPUT_DIR / f"{scenario_id}_stdout.log")
    proc = None
    try:
        t0 = time.time()
        proc = subprocess.Popen(
            [SOLVER_BIN],
            stdin=open(config_file),
            stdout=open(stdout_log, "w"),
            stderr=subprocess.STDOUT,
            cwd=SOLVER_DIR,
        )
        proc.wait(timeout=TIMEOUT)
        elapsed = time.time() - t0
        print(f"  [{scenario_id}] {elapsed:.0f}s", end="")

        if proc.returncode != 0:
            print(f" FAILED (returncode={proc.returncode})")
            return None

        # exploitability を stdout から読む
        try:
            with open(stdout_log) as lg:
                content = lg.read()
            expl_line = [l for l in content.splitlines() if "exploitability" in l.lower()]
            if expl_line:
                print(f" | expl: {expl_line[-1].split()[-2][:6]}%", end="")
        except Exception:
            pass
        print()

        if not Path(dump_path).exists():
            print(f"  [{scenario_id}] dump file not found: {dump_path}")
            return None

        with open(dump_path) as f:
            return json.load(f)

    except subprocess.TimeoutExpired:
        if proc is not None:
            proc.kill()
        print(f" TIMEOUT")
        return None
    except Exception as e:
        print(f" ERROR: {e}")
        return None
    finally:
        os.unlink(config_file)


# ---------------------------------------------------------------------------
# レンジ解析関数
# ---------------------------------------------------------------------------

def find_action_node(node: dict, action_fragment: str) -> dict | None:
    """ノードの children から action_fragment を含むキーを探す."""
    children = node.get("childrens") or {}
    for key, child in children.items():
        if action_fragment.upper() in key.upper():
            return child
    return None


def get_strategy_dict(node: dict) -> tuple[list[str], dict[str, list[float]]]:
    """ノードの strategy を (actions, {combo: [probs]}) として返す."""
    strat = node.get("strategy") or {}
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})
    return actions, combos


def parse_bet_amount(action: str) -> float | None:
    """'BET 5.000000' → 5.0, それ以外 → None."""
    parts = action.strip().split()
    if len(parts) == 2 and parts[0].upper() == "BET":
        try:
            return float(parts[1])
        except ValueError:
            pass
    return None


def find_idx_by_ratio(actions: list[str], pot_bb: float, ratio: float, tol: float = 0.20) -> int | None:
    """アクションリストから pot_bb * ratio に最も近いベットのインデックスを返す."""
    target = pot_bb * ratio
    best_idx, best_diff = None, float("inf")
    for i, a in enumerate(actions):
        bb = parse_bet_amount(a)
        if bb is None:
            continue
        diff = abs(bb - target) / (pot_bb + 1e-9)
        if diff < tol and diff < best_diff:
            best_idx, best_diff = i, diff
    return best_idx


def find_child_by_ratio(node: dict, pot_bb: float, ratio: float, tol: float = 0.20) -> tuple[str, dict] | None:
    """children から pot_bb * ratio に最も近いベットの (key, child) を返す."""
    target = pot_bb * ratio
    best_key, best_child, best_diff = None, None, float("inf")
    for key, child in (node.get("childrens") or {}).items():
        bb = parse_bet_amount(key)
        if bb is None:
            continue
        diff = abs(bb - target) / (pot_bb + 1e-9)
        if diff < tol and diff < best_diff:
            best_key, best_child, best_diff = key, child, diff
    if best_key is None or best_child is None:
        return None
    return best_key, best_child


def extract_cbet_frequencies(flop_result: dict, pot_bb: float = 7.0) -> dict[str, Any]:
    """
    フロップ結果から CBet 関連頻度を抽出。

    Returns:
        {
            "cbet33_freq": float,           # IP の 33% CBet 平均頻度
            "cbet50_freq": float,           # IP の 50% CBet 平均頻度
            "xc_freq": float,               # IP のチェックバック平均頻度
            "oop_call_vs_33": float,        # OOP が 33% CBet に対してコールする平均頻度
            "oop_fold_vs_33": float,        # OOP が 33% CBet に対してフォールドする平均頻度
            "oop_call_vs_50": float,        # OOP が 50% CBet に対してコールする平均頻度
            "oop_fold_vs_50": float,
            "oop_cbet_call_combos_33": {combo: call_prob}, # フィルタリングレンジ用
        }
    """
    result = {}

    # root は OOP (player=1) が最初にアクションする
    root = flop_result

    # OOP の CHECK ノードを取得
    oop_check = find_action_node(root, "CHECK")
    if oop_check is None:
        return result

    # IP の CBet ノード群 (player=0, OOP check 後)
    ip_actions, ip_combos = get_strategy_dict(oop_check)
    if not ip_combos:
        return result

    # IP の各アクションのインデックス (BB 額から比率で分類)
    check_idx = next((i for i, a in enumerate(ip_actions) if "CHECK" in a.upper()), None)
    bet33_idx = find_idx_by_ratio(ip_actions, pot_bb, 0.33)
    bet50_idx = find_idx_by_ratio(ip_actions, pot_bb, 0.50)
    bet75_idx = find_idx_by_ratio(ip_actions, pot_bb, 0.75)
    # 33% と 50% が同じアクションに解決されたら 50% 側をクリア
    if bet33_idx is not None and bet33_idx == bet50_idx:
        bet50_idx = None

    if ip_combos:
        n = len(ip_combos)
        if check_idx is not None:
            result["xc_freq"] = round(sum(p[check_idx] for p in ip_combos.values()) / n * 100, 1)
        if bet33_idx is not None:
            result["cbet33_freq"] = round(sum(p[bet33_idx] for p in ip_combos.values()) / n * 100, 1)
        if bet50_idx is not None:
            result["cbet50_freq"] = round(sum(p[bet50_idx] for p in ip_combos.values()) / n * 100, 1)
        if bet75_idx is not None:
            result["cbet75_freq"] = round(sum(p[bet75_idx] for p in ip_combos.values()) / n * 100, 1)

    # OOP の CBet コール/フォールド頻度 (vs 33% CBet)
    if bet33_idx is not None:
        pair33 = find_child_by_ratio(oop_check, pot_bb, 0.33)
        if pair33:
            bet33_node = pair33[1]
            oop_actions, oop_combos = get_strategy_dict(bet33_node)
            if oop_combos:
                call_idx = next((i for i, a in enumerate(oop_actions) if "CALL" in a.upper()), None)
                fold_idx = next((i for i, a in enumerate(oop_actions) if "FOLD" in a.upper()), None)
                n = len(oop_combos)
                if call_idx is not None:
                    result["oop_call_vs_33"] = round(
                        sum(p[call_idx] for p in oop_combos.values()) / n * 100, 1)
                    # フィルタリングレンジ保存
                    result["oop_cbet_call_combos_33"] = {
                        combo: round(probs[call_idx], 3)
                        for combo, probs in oop_combos.items()
                    }
                if fold_idx is not None:
                    result["oop_fold_vs_33"] = round(
                        sum(p[fold_idx] for p in oop_combos.values()) / n * 100, 1)

    # OOP の CBet コール/フォールド頻度 (vs 50% CBet)
    if bet50_idx is not None:
        pair50 = find_child_by_ratio(oop_check, pot_bb, 0.50)
        if pair50:
            bet50_node = pair50[1]
            oop_actions, oop_combos = get_strategy_dict(bet50_node)
            if oop_combos:
                call_idx = next((i for i, a in enumerate(oop_actions) if "CALL" in a.upper()), None)
                fold_idx = next((i for i, a in enumerate(oop_actions) if "FOLD" in a.upper()), None)
                n = len(oop_combos)
                if call_idx is not None:
                    result["oop_call_vs_50"] = round(
                        sum(p[call_idx] for p in oop_combos.values()) / n * 100, 1)
                if fold_idx is not None:
                    result["oop_fold_vs_50"] = round(
                        sum(p[fold_idx] for p in oop_combos.values()) / n * 100, 1)

    return result


def extract_turn_strategies(turn_result: dict, pot_bb: float = 14.0) -> dict[str, Any]:
    """
    ターン 4 枚ボード結果からターン戦略を抽出。

    Returns:
        {
            "ip_bet33_freq": float,   # IP の 33% ターンベット平均頻度
            "ip_bet75_freq": float,   # IP の 75% ターンベット平均頻度
            "ip_check_freq": float,   # IP のチェック平均頻度
            "oop_bet50_freq": float,  # OOP の 50% プローブ平均頻度
            "oop_check_freq": float,  # OOP のチェック平均頻度
            "oop_call_vs_ip33": float, # OOP が IP 33% ベットに対してコール
            "oop_fold_vs_ip33": float,
        }
    """
    result = {}
    root = turn_result

    # OOP が先にアクション (player=1 = OOP)
    oop_actions, oop_combos = get_strategy_dict(root)
    if not oop_combos:
        return result

    check_idx = next((i for i, a in enumerate(oop_actions) if "CHECK" in a.upper()), None)
    bet50_idx = find_idx_by_ratio(oop_actions, pot_bb, 0.50)
    bet100_idx = find_idx_by_ratio(oop_actions, pot_bb, 1.00)
    if bet50_idx is not None and bet50_idx == bet100_idx:
        bet100_idx = None

    n = len(oop_combos)
    if check_idx is not None:
        result["oop_check_freq"] = round(sum(p[check_idx] for p in oop_combos.values()) / n * 100, 1)
    if bet50_idx is not None:
        result["oop_bet50_freq"] = round(sum(p[bet50_idx] for p in oop_combos.values()) / n * 100, 1)
    if bet100_idx is not None:
        result["oop_bet100_freq"] = round(sum(p[bet100_idx] for p in oop_combos.values()) / n * 100, 1)

    # IP のターンアクション (OOP チェック後)
    oop_check_node = find_action_node(root, "CHECK")
    if oop_check_node:
        ip_actions, ip_combos = get_strategy_dict(oop_check_node)
        if ip_combos:
            ip_check_idx = next((i for i, a in enumerate(ip_actions) if "CHECK" in a.upper()), None)
            ip_bet33_idx = find_idx_by_ratio(ip_actions, pot_bb, 0.33)
            ip_bet75_idx = find_idx_by_ratio(ip_actions, pot_bb, 0.75)
            if ip_bet33_idx is not None and ip_bet33_idx == ip_bet75_idx:
                ip_bet75_idx = None

            n2 = len(ip_combos)
            if ip_check_idx is not None:
                result["ip_check_freq"] = round(sum(p[ip_check_idx] for p in ip_combos.values()) / n2 * 100, 1)
            if ip_bet33_idx is not None:
                result["ip_bet33_freq"] = round(sum(p[ip_bet33_idx] for p in ip_combos.values()) / n2 * 100, 1)
            if ip_bet75_idx is not None:
                result["ip_bet75_freq"] = round(sum(p[ip_bet75_idx] for p in ip_combos.values()) / n2 * 100, 1)

            # IP ベット 33% に対する OOP レスポンス
            pair33 = find_child_by_ratio(oop_check_node, pot_bb, 0.33)
            if pair33:
                bet33_node = pair33[1]
                oop_resp_actions, oop_resp_combos = get_strategy_dict(bet33_node)
                if oop_resp_combos:
                    call_idx = next((i for i, a in enumerate(oop_resp_actions) if "CALL" in a.upper()), None)
                    fold_idx = next((i for i, a in enumerate(oop_resp_actions) if "FOLD" in a.upper()), None)
                    n3 = len(oop_resp_combos)
                    if call_idx is not None:
                        result["oop_call_vs_ip33"] = round(
                            sum(p[call_idx] for p in oop_resp_combos.values()) / n3 * 100, 1)
                    if fold_idx is not None:
                        result["oop_fold_vs_ip33"] = round(
                            sum(p[fold_idx] for p in oop_resp_combos.values()) / n3 * 100, 1)

    return result


def classify_combos(combo_probs: dict[str, float], board_str: str) -> dict[str, Any]:
    """
    コンボをハンド強度カテゴリに分類する（簡易版）。
    board_str: "Kc,7d,2s" 形式

    Returns:
        {
            "weighted_total": float,   # 加重合計コンボ数
            "top_10": [(combo, weight)],  # 上位 10 コンボ
            "category_pct": {
                "sets_plus": float,    # セット以上 (%)
                "two_pair": float,     # ツーペア
                "top_pair": float,     # トップペア
                "middle_pair": float,  # ミドルペア
                "draws": float,        # ドロー（FD/OESD）
                "weak": float,         # 弱い手
            }
        }
    """
    board_cards = [c.strip() for c in board_str.replace(",", " ").split() if c.strip()]
    board_ranks = {c[0] for c in board_cards}
    board_suits = [c[1] for c in board_cards]
    flush_suit = None
    if len(board_suits) >= 3:
        from collections import Counter
        suit_counts = Counter(board_suits)
        # モノトーンかフラッシュドロー
        flush_suit = suit_counts.most_common(1)[0][0] if suit_counts.most_common(1)[0][1] >= 2 else None

    rank_order = "23456789TJQKA"

    def rank_val(r: str) -> int:
        return rank_order.index(r)

    # ボードの最高ランク、2番目のランク
    board_rank_vals = sorted([rank_val(c[0]) for c in board_cards], reverse=True)

    def classify(combo: str) -> str:
        # combo = "AhKh" など 4 文字
        if len(combo) < 4:
            return "weak"
        c1, c2 = combo[:2], combo[2:]
        r1, s1 = c1[0], c1[1]
        r2, s2 = c2[0], c2[1]
        hand_ranks = [rank_val(r1), rank_val(r2)]
        hand_ranks_sorted = sorted(hand_ranks, reverse=True)

        # ボード上の役確認
        all_cards_rank = [rank_val(c[0]) for c in board_cards] + hand_ranks
        all_ranks_sorted = sorted(all_cards_rank, reverse=True)

        # ペア判定
        from collections import Counter
        rank_counter = Counter([rank_val(c[0]) for c in board_cards] + hand_ranks)
        max_count = max(rank_counter.values())

        # セット以上: 3枚以上同ランク、またはフルハウス、フォーカーズ
        if max_count >= 4:
            return "sets_plus"
        if max_count == 3:
            return "sets_plus"
        # ツーペア
        pairs = [r for r, c in rank_counter.items() if c >= 2]
        if len(pairs) >= 2:
            return "two_pair"
        # ワンペア
        if pairs:
            pair_rank = pairs[0]
            if pair_rank == board_rank_vals[0]:
                return "top_pair"
            elif board_rank_vals and pair_rank > board_rank_vals[-1]:
                return "middle_pair"
            else:
                return "weak"

        # ドロー判定 (フラッシュドロー: スーツ一致 2枚+)
        if flush_suit:
            hand_flush_count = sum(1 for s in [s1, s2] if s == flush_suit)
            board_flush_count = sum(1 for c in board_cards if c[1] == flush_suit)
            if hand_flush_count + board_flush_count >= 4:
                return "draws"

        # OESD/ガッシュショット判定 (簡易: ランク近接 4 枚でストレートドロー)
        all_unique_ranks = sorted(set(all_cards_rank))
        # 4 連続または 1 欠けで 4 連続
        for start in range(len(all_unique_ranks) - 2):
            span = all_unique_ranks[start:start + 5]
            if len(span) == 5 and span[-1] - span[0] <= 4:
                return "draws"
        for start in range(len(all_unique_ranks) - 3):
            span = all_unique_ranks[start:start + 4]
            if len(span) == 4 and span[-1] - span[0] <= 4:
                return "draws"

        return "weak"

    if not combo_probs:
        return {"weighted_total": 0, "top_10": [], "category_pct": {}}

    categories = {"sets_plus": 0.0, "two_pair": 0.0, "top_pair": 0.0,
                  "middle_pair": 0.0, "draws": 0.0, "weak": 0.0}
    total_weight = sum(combo_probs.values())

    for combo, weight in combo_probs.items():
        cat = classify(combo)
        categories[cat] += weight

    sorted_combos = sorted(combo_probs.items(), key=lambda x: -x[1])

    return {
        "weighted_total": round(total_weight, 1),
        "top_10": [(c, round(w, 3)) for c, w in sorted_combos[:10]],
        "category_pct": {k: round(v / total_weight * 100, 1) if total_weight > 0 else 0.0
                         for k, v in categories.items()},
    }


# ---------------------------------------------------------------------------
# メイン実行
# ---------------------------------------------------------------------------

def run_stage_a(dry_run: bool, resume: bool) -> dict[str, Any]:
    """Stage A: フロップ解析 (10 シナリオ)."""
    print("\n=== Stage A: フロップ解析 ===")
    results: dict[str, Any] = {}

    for scen in FLOP_SCENARIOS:
        sid = scen["id"]
        result_path = OUTPUT_DIR / f"{sid}_raw.json"

        if resume and result_path.exists():
            print(f"  [{sid}] resume: loading existing result")
            with open(result_path) as f:
                raw = json.load(f)
        else:
            print(f"  [{sid}] running flop solve ({scen['board']})...")
            config = build_flop_config(scen, str(result_path))
            raw = run_solver(config, sid, dry_run=dry_run)

        if raw is None and not dry_run:
            print(f"  [{sid}] SKIP (no result)")
            continue

        if raw is not None:
            freqs = extract_cbet_frequencies(raw, pot_bb=float(scen["pot"]))
            results[sid] = {
                "id": sid,
                "board": scen["board"],
                "label": scen["label"],
                "nut_adv": scen["nut_adv"],
                "cbet_frequencies": freqs,
            }
            print(f"  [{sid}] xc={freqs.get('xc_freq','?')}% "
                  f"cbet33={freqs.get('cbet33_freq','?')}% "
                  f"oop_call_vs33={freqs.get('oop_call_vs_33','?')}%")
        elif dry_run:
            results[sid] = {"id": sid, "board": scen["board"], "label": scen["label"],
                            "nut_adv": scen["nut_adv"], "cbet_frequencies": {}}

    return results


def run_stage_b(dry_run: bool, resume: bool, flop_results: dict[str, Any]) -> dict[str, Any]:
    """Stage B: ターン解析 (30 シナリオ)."""
    print("\n=== Stage B: ターン解析 ===")
    results: dict[str, Any] = {}

    for scen in TURN_SCENARIOS:
        sid = scen["id"]
        result_path = OUTPUT_DIR / f"{sid}_raw.json"

        if resume and result_path.exists():
            print(f"  [{sid}] resume: loading existing result")
            with open(result_path) as f:
                raw = json.load(f)
        else:
            print(f"  [{sid}] running turn solve ({scen['board']})...")
            config = build_turn_config(scen, str(result_path))
            raw = run_solver(config, sid, dry_run=dry_run)

        if raw is None and not dry_run:
            print(f"  [{sid}] SKIP (no result)")
            continue

        if raw is not None:
            strats = extract_turn_strategies(raw, pot_bb=float(scen["pot"]))
            results[sid] = {
                "id": sid,
                "board": scen["board"],
                "flop_id": scen["flop_id"],
                "turn_card": scen["turn_card"],
                "turn_type": scen["turn_type"],
                "label": scen["label"],
                "turn_strategies": strats,
            }

            # フロップでのフィルタリングレンジ情報を付加
            fid = scen["flop_id"]
            if fid in flop_results:
                call_combos = flop_results[fid].get("cbet_frequencies", {}).get(
                    "oop_cbet_call_combos_33", {})
                if call_combos:
                    board_for_classify = ",".join(scen["board"].split(",")[:3])
                    oop_range_analysis = classify_combos(call_combos, board_for_classify)
                    results[sid]["oop_postflop_range"] = oop_range_analysis

            print(f"  [{sid}] ip_bet33={strats.get('ip_bet33_freq','?')}% "
                  f"ip_xc={strats.get('ip_check_freq','?')}% "
                  f"oop_call_vs33={strats.get('oop_call_vs_ip33','?')}%")
        elif dry_run:
            results[sid] = {"id": sid, "board": scen["board"], "label": scen["label"],
                            "turn_strategies": {}}

    return results


def generate_research_doc(flop_results: dict, turn_results: dict) -> str:
    """研究ドキュメントを生成する."""
    lines = [
        "# レンジリーディング GTO 研究（TexasSolver 実測データ版）",
        "",
        f"生成日時: 2026-05-12 | シナリオ数: フロップ {len(flop_results)} + ターン {len(turn_results)}",
        "",
        "## 解析設定",
        "",
        "- BTN vs BB, 100BB, 6-max SRP",
        "- BTN open range: ~40% (852 combos)",
        "- BB defend range: ~40% (850 combos)",
        "- Pot: 7bb (CBet後ターンは 14bb), Stack: 96bb",
        "- Accuracy: 0.5%, Max iterations: 200-300",
        "",
    ]

    # Stage A: フロップ解析結果
    lines += ["## Stage A: フロップテクスチャ別 CBet 頻度", ""]
    lines += ["| ボード | テクスチャ | IP xc% | IP cbet33% | OOP call33% | OOP fold33% |"]
    lines += ["|--------|-----------|--------|-----------|------------|------------|"]

    for sid, data in flop_results.items():
        board = data.get("board", "?")
        label = data.get("label", "?")
        freqs = data.get("cbet_frequencies", {})
        xc = freqs.get("xc_freq", "?")
        cbet33 = freqs.get("cbet33_freq", "?")
        call33 = freqs.get("oop_call_vs_33", "?")
        fold33 = freqs.get("oop_fold_vs_33", "?")
        lines.append(f"| {board} | {label[:30]} | {xc}% | {cbet33}% | {call33}% | {fold33}% |")

    lines += ["", "## Stage B: ターンシナリオ別戦略", ""]

    # フロップ別にグループ化
    from collections import defaultdict
    by_flop: dict[str, list[dict]] = defaultdict(list)
    for data in turn_results.values():
        by_flop[data.get("flop_id", "?")].append(data)

    for flop_id, turn_list in sorted(by_flop.items()):
        flop_data = flop_results.get(flop_id, {})
        flop_label = flop_data.get("label", flop_id)
        flop_board = flop_data.get("board", "?")
        flop_freqs = flop_data.get("cbet_frequencies", {})

        lines += [f"### {flop_label} ({flop_board})", ""]

        # フロップ CBet 情報
        if flop_freqs:
            cbet33 = flop_freqs.get("cbet33_freq", "?")
            call33 = flop_freqs.get("oop_call_vs_33", "?")
            fold33 = flop_freqs.get("oop_fold_vs_33", "?")
            lines += [
                f"**フロップ CBet 33%:** IP bet={cbet33}% | OOP call={call33}% | OOP fold={fold33}%",
                "",
            ]

        # ターンカード別戦略
        lines += ["| ターンカード | タイプ | IP bet33% | IP xc% | OOP call vs33% |"]
        lines += ["|------------|------|----------|-------|----------------|"]

        for tdata in sorted(turn_list, key=lambda x: x.get("turn_type", "")):
            tc = tdata.get("turn_card", "?")
            ttype = tdata.get("turn_type", "?")
            strats = tdata.get("turn_strategies", {})
            ip_b33 = strats.get("ip_bet33_freq", "?")
            ip_xc = strats.get("ip_check_freq", "?")
            oop_call = strats.get("oop_call_vs_ip33", "?")
            lines.append(f"| {tc} | {ttype} | {ip_b33}% | {ip_xc}% | {oop_call}% |")

        lines.append("")

        # OOP のポストフロップレンジ分析
        oop_range_data = None
        for tdata in turn_list:
            if "oop_postflop_range" in tdata:
                oop_range_data = tdata["oop_postflop_range"]
                break

        if oop_range_data:
            cat = oop_range_data.get("category_pct", {})
            total = oop_range_data.get("weighted_total", 0)
            top10 = oop_range_data.get("top_10", [])
            lines += [
                f"**OOP CBet+Call レンジ ({flop_board}):** 計 {total:.0f} combos",
                f"- セット+: {cat.get('sets_plus', '?')}% | ツーペア: {cat.get('two_pair', '?')}%",
                f"- トップペア: {cat.get('top_pair', '?')}% | ミドルペア: {cat.get('middle_pair', '?')}%",
                f"- ドロー: {cat.get('draws', '?')}% | 弱手: {cat.get('weak', '?')}%",
                f"- 上位コンボ: {', '.join(f'{c}({w:.2f})' for c, w in top10[:5])}",
                "",
            ]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Range Read GTO Study")
    parser.add_argument("--stage", choices=["A", "B", "all"], default="all")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--resume", action="store_true", default=True)
    parser.add_argument("--no-resume", dest="resume", action="store_false")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_data: dict[str, Any] = {"flop": {}, "turn": {}}

    # 既存データのロード
    if OUTPUT_JSON.exists():
        with open(OUTPUT_JSON) as f:
            all_data = json.load(f)

    # Stage A
    if args.stage in ("A", "all"):
        flop_results = run_stage_a(dry_run=args.dry_run, resume=args.resume)
        all_data["flop"].update(flop_results)

    # Stage B
    if args.stage in ("B", "all"):
        turn_results = run_stage_b(
            dry_run=args.dry_run,
            resume=args.resume,
            flop_results=all_data["flop"],
        )
        all_data["turn"].update(turn_results)

    # 結果保存
    if not args.dry_run:
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f"\n✓ JSON 保存: {OUTPUT_JSON}")

        # 研究ドキュメント生成
        doc = generate_research_doc(all_data["flop"], all_data["turn"])
        with open(OUTPUT_MD, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"✓ MD 保存: {OUTPUT_MD}")

    print(f"\n完了: Stage A={len(all_data['flop'])} / Stage B={len(all_data['turn'])} シナリオ")


if __name__ == "__main__":
    main()
