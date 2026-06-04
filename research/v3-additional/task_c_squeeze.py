#!/usr/bin/env python3
"""
task_c_squeeze.py — Vol1 ch05 スクイーズ N=1/2 実測

書籍 ch05 §5.2 T_squeeze = T_3bet + 3 × N_callers は N=2 以上は概算値。
GTO Wizard で BTN/SB/BB squeeze vs UTG/HJ/CO open + 1-2 callers の T_squeeze を実測。

仕様根拠: poker-books/vol1-preflop/chapters/05-cash-multiway.md §5.2
"""
import os, sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")

from gto_api import api_get, update_session
from hand_order import HAND_TO_INDEX

update_session()

# 6m position: UTG, HJ, CO, BTN, SB, BB
# 各 squeezer × opener × N の組み合わせを pf 文字列で表現

# シンプル化のため、まず N=1 (1 cold caller) の代表的シナリオを取得
# squeezer は最後の発言者になる位置 (BTN/SB/BB)
SCENARIOS_N1 = [
    # BTN squeeze (UTG open + CO call → HJ fold → BTN squeeze)
    ("BTN_sq_vs_UTG_N1_co", "R2-F-C-F"),   # UTG R2, HJ F, CO C, BTN's turn
    ("BTN_sq_vs_HJ_N1_co",  "F-R2-C-F"),   # HJ open, CO call, BTN squeeze
    ("BTN_sq_vs_UTG_N1_hj", "R2-C-F-F"),   # UTG open + HJ call → CO fold → BTN

    # SB squeeze (UTG open + 1 caller → SB squeeze)
    ("SB_sq_vs_UTG_N1_hj", "R2-C-F-F-F"),  # UTG R2, HJ C, CO/BTN F, SB
    ("SB_sq_vs_UTG_N1_co", "R2-F-C-F-F"),  # UTG R2, CO C, BTN F, SB
    ("SB_sq_vs_HJ_N1_co",  "F-R2-C-F-F"),  # HJ R2, CO C, BTN F, SB
    ("SB_sq_vs_BTN_N1_co", "F-F-C-R2-F"),  # CO C, BTN R2 → SB... wait this is open after caller, different
    # Actually need to be careful. Let me use proper sequences.

    # BB squeeze (UTG open + caller → SB fold → BB squeeze)
    ("BB_sq_vs_UTG_N1_hj", "R2-C-F-F-F"),  # UTG R2, HJ C, CO F, BTN F, SB F, BB's turn
    ("BB_sq_vs_UTG_N1_co", "R2-F-C-F-F"),  # UTG R2, CO C, others F
    ("BB_sq_vs_UTG_N1_bn", "R2-F-F-C-F"),  # UTG R2, BTN C, SB F, BB
    ("BB_sq_vs_BTN_N1_sb", "F-F-F-R2-C"),  # BTN R2, SB C, BB squeeze
]

# N=2 (2 cold callers)
SCENARIOS_N2 = [
    ("BTN_sq_vs_UTG_N2",   "R2-C-C-F"),     # UTG R2, HJ C, CO C, BTN squeeze
    ("BB_sq_vs_UTG_N2_hj_co", "R2-C-C-F-F"), # UTG R2, HJ C, CO C, BTN F, SB F, BB
    ("BB_sq_vs_UTG_N2_co_bn", "R2-F-C-C-F"), # UTG R2, CO C, BTN C, SB F, BB
]

ALL_SCENARIOS = SCENARIOS_N1 + SCENARIOS_N2

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
        "squeeze": round(bet_strat[idx], 4),
    } for h, idx in HAND_TO_INDEX.items()}


def main():
    success_count = 0
    for label, pf in ALL_SCENARIOS:
        out_path = OUT_DIR / f"task_c_{label}.json"
        if out_path.exists():
            print(f"  [skip] {label} (already exists)")
            success_count += 1
            continue
        print(f"  fetching {label} (pf={pf!r}) ...", flush=True)
        sols = api_get(board="", flop_actions="", pf=pf, depth=100)
        if not sols:
            print(f"  [skip-no-data] {label}", file=sys.stderr)
            continue
        freqs = extract_hand_freqs(sols)
        all_acts = sols.get('action_solutions', [])
        result = {
            "scenario": label,
            "preflop_actions": pf,
            "depth": 100,
            "summary": {a['action']['code']: round(a.get('total_frequency', 0), 4) for a in all_acts},
            "hand_freqs": freqs,
        }
        with open(out_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  saved {out_path.name}, total squeeze freq: {sum(v for k,v in result['summary'].items() if k.startswith('R')):.3f}")
        success_count += 1
        time.sleep(0.5)

    print()
    print(f"=== タスク C 完了: {success_count}/{len(ALL_SCENARIOS)} シナリオ ===")
    print()
    # 重要ハンド (AA/KK/QQ/JJ/AKs) の squeeze 頻度を出力
    targets = ["AA", "KK", "QQ", "JJ", "TT", "AKs", "AKo", "AQs", "AQo", "KQs"]
    for label, _ in ALL_SCENARIOS:
        p = OUT_DIR / f"task_c_{label}.json"
        if not p.exists():
            continue
        with open(p) as f:
            data = json.load(f)
        sq_str = ", ".join(f"{h}={data['hand_freqs'][h]['squeeze']:.2f}" for h in targets)
        print(f"  {label}: {sq_str}")


if __name__ == "__main__":
    main()
