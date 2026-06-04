#!/usr/bin/env python3
"""task_s3_ip_defender.py — IP defender vs BB lead postflop

シナリオ: BTN/CO/HJ open → BB call → flop で BB lead (donk) → IP defender 反応
4 ボード × 3 IP positions × 2 betsize_levels = 24 spots
"""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")
from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX
update_session()

# IP open → BB call の preflop_actions
PF_BY_OPENER = {
    "BTN": "F-F-F-R2-F-C",  # BTN open, BB call
    "CO":  "F-F-R2-F-F-C",  # CO open, BB call
    "HJ":  "F-R2-F-F-F-C",  # HJ open, BB call
}

# Representative boards
BOARDS = [
    ("Ks7d2c", "dry_high"),
    ("9c8s6d", "dynamic"),
    ("As7h2c", "dry_high_A"),
    ("KsKd2c", "paired_high"),
]

# BB lead sizes to test
LEAD_SIZES = ["B33", "B50"]

OUT_DIR = Path(__file__).parent / "findings"


def extract_compact(sols):
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


for opener, pf in PF_BY_OPENER.items():
    for board, label in BOARDS:
        for lead_size in LEAD_SIZES:
            out_path = OUT_DIR / f"task_s3_{opener}_BB_{label}_BBlead{lead_size}.json"
            if out_path.exists():
                print(f"[skip] {opener} {label} {lead_size}"); continue
            print(f"  fetching {opener} vs BB lead {lead_size} on {label} ...", flush=True)
            flop_actions = lead_size  # BB が先手 bet
            sols = api_get(board=board, flop_actions=flop_actions, pf=pf, depth=100)
            if not sols:
                print(f"    [skip-no-data]"); continue
            result = {
                "scenario": f"{opener}_open_BB_lead_{label}_{lead_size}",
                "opener": opener, "phase": "flop", "board": board,
                "preflop_actions": pf, "flop_actions": flop_actions,
                **extract_compact(sols)
            }
            with open(out_path, "w") as f: json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"    saved {out_path.name}")
            time.sleep(0.3)
print(f"\n=== タスク S3 (IP defender vs BB lead) 完了 ===")
