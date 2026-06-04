#!/usr/bin/env python3
"""task_c2_squeeze_n3.py — Squeeze N=3 (3 cold callers) hand-level"""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")
from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX
update_session()

# N=3: UTG open + HJ + CO + BTN all call → SB/BB squeeze
SCENARIOS_N3 = [
    ("BB_sq_vs_UTG_N3_hj_co_bn", "R2-C-C-C-F"),  # UTG, HJ, CO, BTN all C, SB F, BB
    ("SB_sq_vs_UTG_N3_hj_co_bn", "R2-C-C-C"),    # UTG, HJ, CO, BTN all C, SB
]

OUT_DIR = Path(__file__).parent / "findings"


def extract(sols):
    acts = sols.get('action_solutions', [])
    fold = next((a['strategy'] for a in acts if a['action']['code'] == 'F'), [0.0]*169)
    call = next((a['strategy'] for a in acts if a['action']['code'] == 'C'), [0.0]*169)
    bet = [0.0]*169
    for a in acts:
        c = a['action']['code']
        if c.startswith('R') and c != 'R0':
            for i, s in enumerate(a['strategy']): bet[i] += s
    return {h: {"fold": round(fold[i],4), "call": round(call[i],4), "squeeze": round(bet[i],4)}
            for h, i in HAND_TO_INDEX.items()}


for label, pf in SCENARIOS_N3:
    out = OUT_DIR / f"task_c2_{label}.json"
    if out.exists():
        print(f"[skip] {label}"); continue
    print(f"fetching {label} (pf={pf!r}) ...", flush=True)
    sols = api_get(board="", flop_actions="", pf=pf, depth=100)
    if not sols:
        print(f"[FAILED] {label}", file=sys.stderr); continue
    freqs = extract(sols)
    acts = sols.get('action_solutions', [])
    result = {"scenario": label, "preflop_actions": pf, "depth": 100,
              "summary": {a['action']['code']: round(a.get('total_frequency',0),4) for a in acts},
              "hand_freqs": freqs}
    with open(out, "w") as f: json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"saved {out.name}, sq freq: {sum(v for k,v in result['summary'].items() if k.startswith('R')):.3f}")
    time.sleep(0.5)
print(f"\n=== タスク C2 (Squeeze N=3) 完了 ===")
