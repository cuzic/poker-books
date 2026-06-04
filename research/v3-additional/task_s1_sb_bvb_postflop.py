#!/usr/bin/env python3
"""task_s1_sb_bvb_postflop.py — SB-BB BvB SRP の Turn/River postflop hand-level

SB open R3 → BB call → flop (SB X → BB X) → turn (SB のターン)
代表ボード 4 つ × turn card 3 種 = 12 spots (SB turn の defense)
+ flop で SB cbet → BB call の後 turn のシナリオ

書籍 Vol3 ch02-03 (Turn/River MTT) の SB 補強。SB defender も含む。
"""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")
from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX
update_session()

# SB-BB BvB SRP: pf = "F-F-F-F-R3-C" (SB R3, BB C)
PF_SB_BB = "F-F-F-F-R3-C"

# Representative boards (Vol2 と同じ 4 family の代表)
BOARDS = [
    ("Ks7d2c", "dry_high"),      # K-high dry
    ("9c8s6d", "dynamic"),        # connected dynamic
    ("As7h2c", "dry_high_A"),    # A-high dry
    ("KsKd2c", "paired_high"),   # paired
]

# Turn cards for postflop sequences:
TURN_CARDS = ["3c", "Kh", "Ah"]  # blank, board-pair, OC

OUT_DIR = Path(__file__).parent / "findings"


def extract(sols, mode="postflop"):
    """postflop は raw response の action_solutions + strategy[N] (N != 169)"""
    acts = sols.get('action_solutions', [])
    n_combos = len(acts[0].get('strategy', [])) if acts else 0
    return {
        "n_combos": n_combos,
        "actions": [
            {
                "code": a.get('action', {}).get('code', ''),
                "freq": round(a.get('total_frequency', 0), 4),
                "position": a.get('action', {}).get('position', ''),
                "strategy": [round(s, 4) for s in a.get('strategy', [])][:50],  # 最初の 50 だけ保存
            }
            for a in acts
        ],
        "hand_categories_range": sols.get('hand_categories_range', []),
        "n_actions": len(acts),
    }


# ── 1. Flop spot (SB X → BB X や SB cbet 後 BB の番) ──
# Multiple flop_action variants:
for board, label in BOARDS:
    # 1a. Flop で SB の番 (X-X or X-bet)
    out_path = OUT_DIR / f"task_s1_flop_{label}_sb_xx.json"
    if out_path.exists():
        print(f"[skip] flop {label} SB X/X"); continue
    print(f"  fetching flop {label} SB action (board={board}) ...", flush=True)
    sols = api_get(board=board, flop_actions="", pf=PF_SB_BB, depth=100)
    if not sols:
        print(f"  [skip] {label}"); continue
    result = {"scenario": f"SB_BB_BvB_flop_{label}", "board": board, "phase": "flop",
              "preflop_actions": PF_SB_BB,
              **extract(sols)}
    with open(out_path, "w") as f: json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  saved {out_path.name}")
    time.sleep(0.3)

# ── 2. Turn spot (SB cbet 33% → BB call → turn) ──
for board, label in BOARDS:
    for turn in TURN_CARDS:
        out_path = OUT_DIR / f"task_s1_turn_{label}_{turn}_sb.json"
        if out_path.exists():
            print(f"[skip] turn {label}+{turn}"); continue
        # flop_actions: "B33-C" (SB bet 33%, BB call) → turn SB の番
        flop_actions = "B33-C"
        full_board = board + turn
        print(f"  fetching turn {label}+{turn} SB action ...", flush=True)
        sols = api_get(board=full_board, flop_actions=flop_actions, pf=PF_SB_BB, depth=100)
        if not sols:
            # try X-X-X (check through flop)
            flop_actions = "X-X"
            print(f"    retry with X-X...", flush=True)
            sols = api_get(board=full_board, flop_actions=flop_actions, pf=PF_SB_BB, depth=100)
        if not sols:
            print(f"  [skip] turn {label}+{turn}"); continue
        result = {"scenario": f"SB_BB_BvB_turn_{label}_{turn}", "board": full_board, "phase": "turn",
                  "preflop_actions": PF_SB_BB, "flop_actions": flop_actions,
                  **extract(sols)}
        with open(out_path, "w") as f: json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  saved {out_path.name}")
        time.sleep(0.3)

print(f"\n=== タスク S1 (SB BvB postflop) 完了 ===")
