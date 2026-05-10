#!/usr/bin/env python3
"""
texassolver_v4_verify.py — ChatGPT v4 review で議論になった論点の追加検証.

検証対象:
  1) 3bd_001: 3BP IP defense (AA on K72r) — BTN(IP) facing BB CBet 33%
     → my claim: GTO mix 「レイズ60% / コール40%」
  2) 4b_001: 4BP CBet (AA on K72r) — IP open 4BP, OOP calls, IP CBets
     → my claim: H3 → ALL_IN
  3) 4bd_001: 4BP defense (AA on K72r) — IP facing OOP all-in CBet
     → my claim: コール（コミット）100%
  4) river_defense rd_001: AK on AK729 OOP facing IP 50% bet
     → my claim: borderline V — CR 可だが CALL 混合可

既存検証で対応済みの論点:
  ✓ 3bo_001: AA on K72r OOP CR/CALL split — scenario_a で 46.3/53.7 確認済
  ✓ K5o on K72r vs 50%: CALL 100% — /tmp/ts_chatgpt_review/K72r_50pct.json
  ✓ AJ on A95s vs 50%: CALL — A95ss_50pct.json
  ✓ A2 on T98w vs 50%: FOLD — T98w_50pct.json
"""

from __future__ import annotations
import json
import os
import subprocess
import tempfile
from pathlib import Path

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_CWD = "/home/cuzic/TexasSolver"
OUT_DIR = Path("/tmp/ts_v4_verify")
OUT_DIR.mkdir(exist_ok=True)

# 3BP ranges (BB 3-bet vs BTN, BTN call)
# AA を BTN range に含む拡張 (ChatGPT 仮説的なシナリオ)
BB_3BET_RANGE = "AA,KK,QQ,JJ,AKs,AKo,AQs,A5s,A4s,A3s,76s,65s,KQs"
BTN_CALL_RANGE_WITH_AA = (
    "AA,KK,QQ,JJ,TT,99,88,AQs,AQo,AJs,KQs,KJs,QJs,JTs,T9s,98s"
)

# SRP HU range (for river)
HU_BTN = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AKo,AQo,AJo,ATo,A9o,A8o,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "KQo,KJo,KTo,K9o,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,QJo,QTo,Q9o,"
    "JTs,J9s,J8s,J7s,J6s,JTo,J9o,"
    "T9s,T8s,T7s,T6s,T9o,T8o,"
    "98s,97s,96s,98o,87s,86s,85s,87o,76s,75s,74s,76o,65s,64s,65o,54s,53s"
)
HU_BB = HU_BTN  # symmetric for simplicity

CONFIG_3BD = """\
set_pot 19
set_effective_stack 91
set_board {board}
set_range_ip {ip}
set_range_oop {oop}
set_bet_sizes oop,flop,bet,33,50
set_bet_sizes ip,flop,raise,2.5,3
set_allin_threshold 0.67
build_tree
set_thread_num 4
set_accuracy 0.5
set_max_iteration 200
set_print_interval 100
set_dump_rounds 1
start_solve
dump_result {dump}
"""

CONFIG_4B = """\
set_pot 50
set_effective_stack 75
set_board {board}
set_range_ip {ip}
set_range_oop {oop}
set_bet_sizes ip,flop,bet,75
set_bet_sizes oop,flop,bet,75
set_bet_sizes oop,flop,raise,2.5
set_allin_threshold 0.5
build_tree
set_thread_num 4
set_accuracy 0.5
set_max_iteration 100
set_print_interval 50
set_dump_rounds 1
start_solve
dump_result {dump}
"""

# 4BP ranges (AA, KK, QQ, AK only — typical 4-bet calling/4-bet ranges)
BTN_4BET_RANGE = "AA,KK,QQ,AKs,AKo,AQs"
BB_5BET_CALL_RANGE = "AA,KK,QQ,JJ,AKs,AKo,AQs"


def run_solver(config: str, timeout: int = 240) -> tuple[str, int]:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_v4_"
    ) as f:
        f.write(config)
        cfg = f.name
    out = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_v4_out_"
    )
    out.close()
    try:
        with open(cfg, "r") as fin, open(out.name, "w") as fout:
            proc = subprocess.run(
                [SOLVER_BIN], stdin=fin, stdout=fout, stderr=subprocess.STDOUT,
                cwd=SOLVER_CWD, timeout=timeout,
            )
        return out.name, proc.returncode
    finally:
        os.unlink(cfg)


def _avg_actions(combos: dict, actions: list, hand_pat: str) -> tuple[int, dict]:
    matching = []
    for combo, probs in combos.items():
        if len(combo) >= 4 and combo[0] == hand_pat[0] and combo[2] == hand_pat[1]:
            if any(p > 0.001 for p in probs):
                matching.append(probs)
    if not matching:
        return 0, {}
    n = len(matching)
    avg = {actions[i]: sum(p[i] for p in matching) / n * 100 for i in range(len(actions))}
    return n, avg


def case_3bd_001():
    """3bd_001: AA on K72r in 3BP, IP facing OOP CBet 33%."""
    print("\n=== Case 1: 3bd_001 — AA on K72r 3BP IP facing OOP CBet 33% ===")
    dump = OUT_DIR / "3bd_001.json"
    cfg = CONFIG_3BD.format(
        board="Kc,7d,2s",
        ip=BTN_CALL_RANGE_WITH_AA,
        oop=BB_3BET_RANGE,
        dump=str(dump),
    )
    stdout_f, rc = run_solver(cfg, timeout=300)
    if rc != 0 or not dump.exists():
        with open(stdout_f) as f:
            print(f.read()[-600:])
        return None

    data = json.loads(dump.read_text())
    # Tree: root = OOP first action. OOP CHECK or OOP BET.
    # We want: OOP BET 33% → IP response (CALL/RAISE/FOLD)
    children = data.get("childrens", {})
    bet_keys = [k for k in children if k.startswith("BET")]
    if not bet_keys:
        # Maybe OOP-first means OOP CHECK is option, then IP can bet
        # Try CHECK → IP BET
        if "CHECK" in children:
            ip_under_check = children["CHECK"].get("childrens", {})
            bet_keys = [k for k in ip_under_check if k.startswith("BET")]
            target_dict = ip_under_check
        else:
            print("  No OOP BET found")
            return None
    else:
        target_dict = children

    # Pick BET ~33% (= 6.27 of 19 pot)
    target = 6.27
    best = min(bet_keys, key=lambda k: abs(float(k.replace("BET", "").strip()) - target))
    print(f"  Picked: {best}")
    bet_node = target_dict[best]
    strat = bet_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})
    print(f"  Actions: {actions}, total combos: {len(combos)}")

    for hand in ["AA", "KK", "QQ", "AKs", "AKo"]:
        n, avg = _avg_actions(combos, actions, hand)
        if n:
            summary = ", ".join(f"{a}={f:.1f}%" for a, f in avg.items())
            print(f"  {hand} ({n} combos): {summary}")
    return data


def case_4b_001():
    """4b_001: AA on K72r in 4BP, IP CBet."""
    print("\n=== Case 2: 4b_001 — AA on K72r 4BP IP CBet ===")
    print("  4BP SPR≈1.5 → expect ALL_IN or 75% commit")
    dump = OUT_DIR / "4b_001.json"
    cfg = CONFIG_4B.format(
        board="Kc,7d,2s",
        ip=BTN_4BET_RANGE,
        oop=BB_5BET_CALL_RANGE,
        dump=str(dump),
    )
    stdout_f, rc = run_solver(cfg, timeout=180)
    if rc != 0 or not dump.exists():
        with open(stdout_f) as f:
            print(f.read()[-500:])
        return None

    data = json.loads(dump.read_text())
    # Tree: OOP first → OOP CHECK or BET
    # Then IP CHECK or BET 33/75/allin
    if "CHECK" in data.get("childrens", {}):
        ip_actions = data["childrens"]["CHECK"]
        ip_strat = ip_actions.get("strategy", {})
        actions = ip_strat.get("actions", [])
        combos = ip_strat.get("strategy", {})
        print(f"  IP actions after OOP check: {actions}")
        print(f"  IP combos: {len(combos)}")
        for hand in ["AA", "KK", "QQ", "AKs"]:
            n, avg = _avg_actions(combos, actions, hand)
            if n:
                summary = ", ".join(f"{a}={f:.1f}%" for a, f in avg.items())
                print(f"  {hand} ({n} combos): {summary}")
    return data


def case_4b_wet():
    """4BP wet/semi board H3 verification.
    AA on T98ss (wet, 5 cards: T9 close, two spades flush draw possible)
    QQ on J85 (semi: 8-5 connector)
    """
    print("\n=== Case 3: 4BP wet/semi H3 verification ===")
    scenarios = [
        ("AA on T98w (wet)", "Ts,9s,8d", "AA"),
        ("QQ on J85 (semi)", "Jh,8d,5c", "QQ"),
        ("AKs on T98w (wet)", "Ts,9s,8d", "AKs"),
    ]
    results = {}
    for name, board, target_hand in scenarios:
        print(f"\n--- {name}")
        dump = OUT_DIR / f"4b_wet_{board.replace(',','_')}_{target_hand}.json"
        cfg = CONFIG_4B.format(
            board=board,
            ip=BTN_4BET_RANGE,
            oop=BB_5BET_CALL_RANGE,
            dump=str(dump),
        )
        stdout_f, rc = run_solver(cfg, timeout=180)
        if rc != 0 or not dump.exists():
            print("  ✗ failed")
            continue
        data = json.loads(dump.read_text())
        if "CHECK" in data.get("childrens", {}):
            ip_strat = data["childrens"]["CHECK"].get("strategy", {})
            actions = ip_strat.get("actions", [])
            combos = ip_strat.get("strategy", {})
            for hand in [target_hand, "AA", "KK", "QQ", "AKs"]:
                n, avg = _avg_actions(combos, actions, hand)
                if n:
                    summary = ", ".join(f"{a}={f:.1f}%" for a, f in avg.items())
                    print(f"  {hand} ({n} combos): {summary}")
                    results[(name, hand)] = avg
    return results


def main():
    case_3bd_001()
    case_4b_001()
    case_4b_wet()
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
