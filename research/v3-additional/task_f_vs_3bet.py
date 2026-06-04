#!/usr/bin/env python3
"""task_f_vs_3bet.py — Vol1 ch04 §4.4-§4.6 vs 3-bet/4-bet/5-bet defense hand-level

オープナー vs 3-bet 12 シナリオ + 4-bet defense 5 + 5-bet defense 1 = 18 spots
"""
import os, sys, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")
from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX
update_session()

# §4.4 オープナー vs 3-bet (12 シナリオ)
# IP 3-bet sizing は ~3x (R7-R8)、BB の 3-bet も R7-R10、SB R10+
# とりあえず R7 を仮定
VS_3BET = [
    # UTG opens, 各 caller が 3-bet → UTG turn
    ("UTG_vs_HJ_3bet",  "R2-R7-F-F-F-F"),
    ("UTG_vs_CO_3bet",  "R2-F-R7-F-F-F"),
    ("UTG_vs_BTN_3bet", "R2-F-F-R7-F-F"),
    ("UTG_vs_SB_3bet",  "R2-F-F-F-R10-F"),
    ("UTG_vs_BB_3bet",  "R2-F-F-F-F-R10"),
    # HJ opens
    ("HJ_vs_CO_3bet",   "F-R2-R7-F-F-F"),
    ("HJ_vs_BTN_3bet",  "F-R2-F-R7-F-F"),
    ("HJ_vs_BB_3bet",   "F-R2-F-F-F-R10"),
    # CO opens
    ("CO_vs_BTN_3bet",  "F-F-R2-R7-F-F"),
    ("CO_vs_BB_3bet",   "F-F-R2-F-F-R10"),
    # BTN opens
    ("BTN_vs_SB_3bet",  "F-F-F-R2-R10-F"),
    ("BTN_vs_BB_3bet",  "F-F-F-R2-F-R10"),
]

# §4.5 4-bet defense (5 シナリオ): 3-bettor が 4-bet を受ける
# 標準: 2.5 → 9 → 22 (4-bet)
VS_4BET = [
    ("HJ_3bet_vs_UTG_4bet",  "R2-R7-F-F-F-F-R22"),  # UTG 4-bet → HJ defense
    ("CO_3bet_vs_UTG_4bet",  "R2-F-R7-F-F-F-R22"),
    ("BTN_3bet_vs_UTG_4bet", "R2-F-F-R7-F-F-R22"),
    ("BTN_3bet_vs_HJ_4bet",  "F-R2-F-R7-F-F-R22"),
    ("BTN_3bet_vs_CO_4bet",  "F-F-R2-R7-F-F-R22"),
]

# §4.6 5-bet defense (1 シナリオ代表): 4-bettor が 5-bet を受ける
VS_5BET = [
    ("UTG_4bet_vs_HJ_5bet", "R2-R7-F-F-F-F-R22-RAI"),
]

OUT_DIR = Path(__file__).parent / "findings"
OUT_DIR.mkdir(exist_ok=True)


def extract(sols):
    acts = sols.get('action_solutions', [])
    fold = next((a['strategy'] for a in acts if a['action']['code'] == 'F'), [0.0]*169)
    call = next((a['strategy'] for a in acts if a['action']['code'] == 'C'), [0.0]*169)
    bet = [0.0]*169
    allin = next((a['strategy'] for a in acts if a['action']['code'] == 'RAI'), None)
    for a in acts:
        c = a['action']['code']
        if c.startswith('R') and c != 'R0' and c != 'RAI':
            for i, s in enumerate(a['strategy']): bet[i] += s
    out = {}
    for h, i in HAND_TO_INDEX.items():
        d = {"fold": round(fold[i],4), "call": round(call[i],4), "raise": round(bet[i],4)}
        if allin:
            d["allin"] = round(allin[i],4)
        out[h] = d
    return out


def run(scenarios, prefix):
    success = 0
    for label, pf in scenarios:
        out = OUT_DIR / f"task_{prefix}_{label}.json"
        if out.exists():
            print(f"[skip] {label}"); success += 1; continue
        print(f"fetching {label} (pf={pf!r}) ...", flush=True)
        sols = api_get(board="", flop_actions="", pf=pf, depth=100)
        if not sols:
            print(f"[skip-no-data] {label}", file=sys.stderr); continue
        freqs = extract(sols)
        acts = sols.get('action_solutions', [])
        result = {"scenario": label, "preflop_actions": pf, "depth": 100,
                  "summary": {a['action']['code']: round(a.get('total_frequency',0),4) for a in acts},
                  "hand_freqs": freqs}
        with open(out, "w") as f: json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"saved {out.name}"); success += 1
        time.sleep(0.5)
    return success


print("=== F1: vs 3-bet (12 scenarios) ===")
n1 = run(VS_3BET, "f1")
print(f"\n=== F2: 4-bet defense (5 scenarios) ===")
n2 = run(VS_4BET, "f2")
print(f"\n=== F3: 5-bet defense (1 scenario) ===")
n3 = run(VS_5BET, "f3")
print(f"\n=== タスク F 完了: F1={n1}, F2={n2}, F3={n3} ===")
