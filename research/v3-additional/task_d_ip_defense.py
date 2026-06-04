#!/usr/bin/env python3
"""
task_d_ip_defense.py — Vol1 ch04 §4.2 IP defense 実測

BTN vs UTG/HJ/CO + CO vs UTG/HJ + HJ vs UTG = 6 シナリオ × 169 ハンド。
書籍 ch04 §4.2 のテーブル (T_3bet/T_call) を GTO 実測で検証。

使い方:
  source .env && python3 task_d_ip_defense.py
"""
import os, sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")

from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX

update_session()

# 6m position order: UTG, HJ, CO, BTN, SB, BB
# IP defense: BTN/CO/HJ がオープナーの後ろから defense
SCENARIOS = [
    # (label, pf: actions before hero's turn)
    ("HJ_vs_UTG",  "R2"),               # UTG R2 → HJ's turn
    ("CO_vs_UTG",  "R2-F"),             # UTG R2, HJ F → CO's turn
    ("CO_vs_HJ",   "F-R2"),             # UTG F, HJ R2 → CO's turn
    ("BTN_vs_UTG", "R2-F-F"),           # UTG R2, HJ/CO F → BTN's turn
    ("BTN_vs_HJ",  "F-R2-F"),           # HJ R2, CO F → BTN's turn
    ("BTN_vs_CO",  "F-F-R2"),           # CO R2 → BTN's turn
]

OUT_DIR = Path(__file__).parent / "findings"
OUT_DIR.mkdir(exist_ok=True)


def extract_hand_freqs(sols: dict) -> dict:
    acts = sols.get('action_solutions', [])
    fold_strat = next((a['strategy'] for a in acts if a['action']['code'] == 'F'), [0.0]*169)
    call_strat = next((a['strategy'] for a in acts if a['action']['code'] == 'C'), [0.0]*169)
    bet_strat = [0.0] * 169
    for a in acts:
        code = a['action']['code']
        if code.startswith('R') and code != 'R0':
            for i, s in enumerate(a['strategy']):
                bet_strat[i] += s
    return {h: {
        "fold": round(fold_strat[idx], 4),
        "call": round(call_strat[idx], 4),
        "3bet": round(bet_strat[idx], 4),
    } for h, idx in HAND_TO_INDEX.items()}


def main():
    for label, pf in SCENARIOS:
        out_path = OUT_DIR / f"task_d_{label}.json"
        if out_path.exists():
            print(f"  [skip] {label}")
            continue
        print(f"  fetching {label} (pf={pf!r}) ...", flush=True)
        sols = api_get(board="", flop_actions="", pf=pf, depth=100)
        if not sols:
            print(f"  [FAILED] {label}", file=sys.stderr)
            continue
        freqs = extract_hand_freqs(sols)
        acts = sols.get('action_solutions', [])
        result = {
            "scenario": label,
            "preflop_actions": pf,
            "depth": 100,
            "summary": {a['action']['code']: round(a.get('total_frequency', 0), 4) for a in acts},
            "hand_freqs": freqs,
        }
        with open(out_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  saved {out_path.name}")
        time.sleep(0.5)
    print(f"\n=== タスク D 完了 ({len(SCENARIOS)} シナリオ) ===")


if __name__ == "__main__":
    main()
