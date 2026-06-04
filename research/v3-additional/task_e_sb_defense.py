#!/usr/bin/env python3
"""task_e_sb_defense.py — Vol1 ch04 §4.3 SB OOP defense hand-level (4 spots)"""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")
from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX
update_session()

SCENARIOS = [
    ("SB_vs_UTG", "R2-F-F-F"),
    ("SB_vs_HJ",  "F-R2-F-F"),
    ("SB_vs_CO",  "F-F-R2-F"),
    ("SB_vs_BTN", "F-F-F-R2"),
]

OUT_DIR = Path(__file__).parent / "findings"
OUT_DIR.mkdir(exist_ok=True)


def extract(sols):
    acts = sols.get('action_solutions', [])
    fold = next((a['strategy'] for a in acts if a['action']['code'] == 'F'), [0.0]*169)
    call = next((a['strategy'] for a in acts if a['action']['code'] == 'C'), [0.0]*169)
    bet = [0.0]*169
    for a in acts:
        c = a['action']['code']
        if c.startswith('R') and c != 'R0':
            for i, s in enumerate(a['strategy']): bet[i] += s
    return {h: {"fold": round(fold[i],4), "call": round(call[i],4), "3bet": round(bet[i],4)}
            for h, i in HAND_TO_INDEX.items()}


for label, pf in SCENARIOS:
    out = OUT_DIR / f"task_e_{label}.json"
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
    print(f"saved {out.name}")
    time.sleep(0.5)
print(f"\n=== タスク E 完了 ({len(SCENARIOS)} シナリオ) ===")
