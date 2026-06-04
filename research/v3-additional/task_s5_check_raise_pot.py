#!/usr/bin/env python3
"""task_s5_check_raise_pot.py — Check-raise pot 後の対応

シナリオ: BTN open → BB call → flop で BTN B33 → BB raise R10 → BTN の対応
3 board × 2 raise size = 6 spots
"""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")
from gto_api import api_get, update_session
update_session()

PF_BTN_BB = "F-F-F-R2-F-C"
BOARDS = [
    ("Ks7d2c", "dry_high"),
    ("9c8s6d", "dynamic"),
    ("As7h2c", "dry_high_A"),
]
RAISE_SIZES = ["R8", "R10"]  # check-raise to 8 or 10 BB

OUT_DIR = Path(__file__).parent / "findings"


def extract(sols):
    acts = sols.get('action_solutions', [])
    return {
        "n_combos": len(acts[0].get('strategy', [])) if acts else 0,
        "n_actions": len(acts),
        "actions": [
            {
                "code": a.get('action', {}).get('code', ''),
                "freq": round(a.get('total_frequency', 0), 4),
                "position": a.get('action', {}).get('position', ''),
                "strategy": [round(s, 4) for s in a.get('strategy', [])][:50],
            }
            for a in acts
        ],
    }


for board, label in BOARDS:
    for raise_sz in RAISE_SIZES:
        # check-raise pot: BTN B33 → BB raise R8/R10 → BTN の defense
        out_path = OUT_DIR / f"task_s5_btn_vs_bb_xr_{label}_{raise_sz}.json"
        if out_path.exists():
            print(f"[skip] {label} {raise_sz}"); continue
        flop_actions = f"B33-{raise_sz}"
        print(f"  BTN vs BB check-raise on {label} ({raise_sz}) ...", flush=True)
        sols = api_get(board=board, flop_actions=flop_actions, pf=PF_BTN_BB, depth=100)
        if not sols:
            print(f"    [skip-no-data]")
            continue
        result = {
            "scenario": f"BTN_vs_BB_xr_{label}_{raise_sz}",
            "phase": "flop", "board": board,
            "preflop_actions": PF_BTN_BB, "flop_actions": flop_actions,
            **extract(sols)
        }
        with open(out_path, "w") as f: json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"    saved {out_path.name}")
        time.sleep(0.3)
print(f"\n=== タスク S5 (check-raise pot) 完了 ===")
