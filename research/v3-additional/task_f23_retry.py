#!/usr/bin/env python3
"""task_f23_retry.py — 4-bet defense (F2) + 5-bet defense (F3) を別 sizing で再試行

R22 で 204 (No Content) だったため、R20 / R18 で試す。
"""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")
from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX
update_session()

# 標準 4-bet sizing は ~2.5x 3-bet = ~2.5 × 7 = ~17.5 → R17 or R18
# 100bb で 4-bet は普通 21-22BB だが、tree により異なる
SIZING_CANDIDATES = ["R17", "R18", "R20", "R21"]

VS_4BET_BASE = [
    ("HJ_3bet_vs_UTG_4bet",  "R2-R7-F-F-F-F-"),  # +sizing
    ("CO_3bet_vs_UTG_4bet",  "R2-F-R7-F-F-F-"),
    ("BTN_3bet_vs_UTG_4bet", "R2-F-F-R7-F-F-"),
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
    return {h: {"fold": round(fold[i],4), "call": round(call[i],4), "raise": round(bet[i],4)}
            for h, i in HAND_TO_INDEX.items()}


for label, pf_base in VS_4BET_BASE:
    out = OUT_DIR / f"task_f2_{label}.json"
    if out.exists():
        print(f"[skip] {label}"); continue

    # Try multiple sizings
    sols = None
    used_sizing = None
    for sz in SIZING_CANDIDATES:
        pf = pf_base + sz
        print(f"  trying {label} sz={sz} (pf={pf!r})...", flush=True)
        sols = api_get(board="", flop_actions="", pf=pf, depth=100)
        if sols:
            used_sizing = sz
            break
        time.sleep(0.3)

    if not sols:
        print(f"  [FAILED all sizings] {label}", file=sys.stderr); continue
    freqs = extract(sols)
    acts = sols.get('action_solutions', [])
    result = {"scenario": label, "preflop_actions": pf_base + used_sizing, "sizing": used_sizing, "depth": 100,
              "summary": {a['action']['code']: round(a.get('total_frequency',0),4) for a in acts},
              "hand_freqs": freqs}
    with open(out, "w") as f: json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  saved {out.name} (sz={used_sizing})")
    time.sleep(0.5)
print(f"\n=== タスク F2 retry 完了 ===")
