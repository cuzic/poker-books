#!/usr/bin/env python3
"""
texassolver_chatgpt_review_verify.py — ChatGPT レビューで論点となった
HU シナリオを TexasSolver で検証する。

対象:
  1. K72r + 50% CBet 受け側 (K5o=TPWK の CALL or FOLD)
  2. A95s + 50% CBet 受け側 (AJ=TPGK の CR or CALL)
  3. T98w + 50% CBet 受け側 (A2 の CALL or FOLD)

使い方:
  python3 scripts/texassolver_chatgpt_review_verify.py
"""

from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_CWD = "/home/cuzic/TexasSolver"

# BTN open range, BB call range (100BB, 6-max)
IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AKo,AQo,AJo,ATo,A9o,A8o,A7o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,"
    "T9s,T8s,T7s,T6s,"
    "98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)
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

# Scenarios to verify
SCENARIOS = [
    {
        "name": "K72r_50pct",
        "board": "Kc,7d,2s",
        "pot": 7,
        "stack": 97,
        "target_combos": ["KsKh", "K5o = K5/K4/K3/K2"],  # K5o = TPWK
        "target_descr": "K5o (TPWK) on K72r vs 50% CBet (HU)",
        "review_question": "TPWK は CALL or FOLD?",
    },
    {
        "name": "A95ss_50pct",
        "board": "As,9d,5c",
        "pot": 7,
        "stack": 97,
        "target_combos": ["AJ", "AT", "AQ"],
        "target_descr": "AJ (TPGK) on A95s vs 50% CBet (HU)",
        "review_question": "TPGK は CR or CALL?",
    },
    {
        "name": "T98w_50pct",
        "board": "Ts,9s,8d",
        "pot": 7,
        "stack": 97,
        "target_combos": ["A2"],
        "target_descr": "A2 (Air on wet) on T98 vs 50% CBet",
        "review_question": "弱いハンドは CALL or FOLD?",
    },
]

# config: OOP defends after IP CBets 50%
# Note: IP already CBet 50% means pot=7→pot=10.5 after CBet, OOP facing 3.5 bet into 7
# For the solver, we model the post-CBet state:
#   - pot_after_cbet = pot + 2*cbet = 7 + 7 = 14 (50% pot bet)
# But TexasSolver expects "starting pot, current decision tree". Let's run from
# pre-CBet but with OOP's defending stance.
CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes oop,flop,raise,2.5,3
set_allin_threshold 0.67
build_tree
set_thread_num 4
set_accuracy 0.5
set_max_iteration 200
set_print_interval 50
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""


def run_solver(config_text: str, timeout: int = 600) -> tuple[str, int]:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_cfg_"
    ) as f:
        f.write(config_text)
        cfg_path = f.name

    stdout_file = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_out_"
    )
    stdout_file.close()

    try:
        with open(cfg_path, "r") as fin, open(stdout_file.name, "w") as fout:
            proc = subprocess.run(
                [SOLVER_BIN],
                stdin=fin,
                stdout=fout,
                stderr=subprocess.STDOUT,
                cwd=SOLVER_CWD,
                timeout=timeout,
            )
        return stdout_file.name, proc.returncode
    finally:
        os.unlink(cfg_path)


def analyze_oop_response(result_json: dict, target_hand_pattern: str = ""):
    """OOP の CBet 受け応答を分析。
    Tree 構造:
      root: OOP first action (CHECK or DONK)
      └ CHECK: OOP checked
          └ BET XX: IP CBets
              └ OOP response (CALL/FOLD/RAISE)
    """
    if "childrens" not in result_json:
        return None

    # Step 1: OOP CHECK ノードへ進む
    if "CHECK" not in result_json["childrens"]:
        return None
    check_node = result_json["childrens"]["CHECK"]

    # Step 2: IP の BET ノード一覧
    if "childrens" not in check_node:
        return None
    bet_nodes = [k for k in check_node["childrens"].keys() if "BET" in k.upper()]
    if not bet_nodes:
        return None

    # 50% pot bet (= 3.5) に最も近いものを選ぶ (pot=7 で 50% = 3.5)
    target_bet = 3.5
    best_node_key = None
    best_diff = 1e9
    for k in bet_nodes:
        try:
            bet_amt = float(k.replace("BET", "").strip())
            if abs(bet_amt - target_bet) < best_diff:
                best_diff = abs(bet_amt - target_bet)
                best_node_key = k
        except ValueError:
            continue
    if best_node_key is None:
        best_node_key = bet_nodes[0]

    bet_node = check_node["childrens"][best_node_key]
    print(f"  Selected IP bet node: {best_node_key}")

    # OOP がここで応答 → strategy
    if "strategy" not in bet_node:
        return None

    strat = bet_node["strategy"]
    actions = strat.get("actions", [])
    combo_strats = strat.get("strategy", {})

    return {
        "actions": actions,
        "combo_count": len(combo_strats),
        "combos": combo_strats,
    }


def summarize_action_freq(combos: dict, actions: list, hand_pattern: str = "") -> dict:
    """指定パターンマッチするコンボのアクション頻度を集計"""
    matching = {}
    for combo, probs in combos.items():
        if hand_pattern:
            # Simple pattern match: e.g., "K5" matches Ks5h, K5o etc
            # combo format e.g. "KsKh"
            match = False
            for hp in hand_pattern.split(","):
                hp = hp.strip()
                if len(hp) >= 2 and combo[0] == hp[0] and combo[2] == hp[1]:
                    match = True
                    break
            if not match:
                continue
        matching[combo] = probs

    if not matching:
        return {}

    # Average action frequencies
    action_sums = [0.0] * len(actions)
    for probs in matching.values():
        for i, p in enumerate(probs):
            action_sums[i] += p
    n = len(matching)
    avg = {actions[i]: action_sums[i] / n for i in range(len(actions))}
    return {"matching_combos": n, "avg_freq": avg}


def main():
    out_dir = Path("/tmp/ts_chatgpt_review")
    out_dir.mkdir(exist_ok=True)

    results = []
    for sc in SCENARIOS:
        print(f"\n=== {sc['name']}: {sc['target_descr']} ===")
        print(f"質問: {sc['review_question']}")

        dump_path = str(out_dir / f"{sc['name']}.json")
        config_text = CONFIG_TEMPLATE.format(
            pot=sc["pot"],
            stack=sc["stack"],
            board=sc["board"],
            ip_range=IP_RANGE,
            oop_range=OOP_RANGE,
            dump_path=dump_path,
        )
        stdout_file, rc = run_solver(config_text, timeout=300)
        print(f"  exit={rc}, dump={dump_path}")

        if rc != 0 or not Path(dump_path).exists():
            print("  ✗ Solver failed")
            with open(stdout_file) as f:
                print(f.read()[-500:])
            continue

        with open(dump_path) as f:
            data = json.load(f)

        oop = analyze_oop_response(data)
        if not oop:
            print("  ✗ Could not extract OOP strategy")
            continue

        print(f"  Actions: {oop['actions']}")
        print(f"  Total OOP combos: {oop['combo_count']}")

        # Pattern match for review hand
        if sc["name"] == "K72r_50pct":
            for pattern in ["K5", "K4", "K3", "K2"]:
                summary = summarize_action_freq(oop["combos"], oop["actions"], pattern)
                if summary:
                    print(f"  {pattern} ({summary['matching_combos']} combos):")
                    for action, freq in summary["avg_freq"].items():
                        print(f"    {action}: {freq*100:.1f}%")
        elif sc["name"] == "A95ss_50pct":
            for pattern in ["AJ", "AT", "AQ"]:
                summary = summarize_action_freq(oop["combos"], oop["actions"], pattern)
                if summary:
                    print(f"  {pattern} ({summary['matching_combos']} combos):")
                    for action, freq in summary["avg_freq"].items():
                        print(f"    {action}: {freq*100:.1f}%")
        elif sc["name"] == "T98w_50pct":
            for pattern in ["A2"]:
                summary = summarize_action_freq(oop["combos"], oop["actions"], pattern)
                if summary:
                    print(f"  {pattern} ({summary['matching_combos']} combos):")
                    for action, freq in summary["avg_freq"].items():
                        print(f"    {action}: {freq*100:.1f}%")

        results.append({"scenario": sc["name"], "result": "ok"})

    print(f"\n=== Done: {len(results)}/{len(SCENARIOS)} scenarios ===")


if __name__ == "__main__":
    main()
