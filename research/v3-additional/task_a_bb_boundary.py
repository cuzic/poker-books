#!/usr/bin/env python3
"""
task_a_bb_boundary.py — Vol1 BB defense 境界帯の混合戦略を全シナリオ取得

書籍 ch11 では BB vs BTN シナリオの 16 例外ハンド (A8o, A7o, K6s, ...) が
記載されているが、BB vs UTG/HJ/CO/SB の境界帯ハンドは推測。
GTO Wizard で 5 シナリオ × 169 ハンドの混合戦略を実測する。

仕様根拠: poker-books/vol1-preflop/chapters/04-cash-defense.md
"""
import os, sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent))
os.environ["GT"] = os.environ.get("GT_CASH_100BB", "Cash6mTest_6mNL100R2")

from gto_api import api_get, update_session
from hand_order import HANDS, HAND_TO_INDEX

update_session()

# 各 BB defense シナリオ
SCENARIOS = [
    ("BB_vs_UTG", "R2-F-F-F-F"),
    ("BB_vs_HJ",  "F-R2-F-F-F"),
    ("BB_vs_CO",  "F-F-R2-F-F"),
    ("BB_vs_BTN", "F-F-F-R2-F"),
    ("BB_vs_SB",  "F-F-F-F-R3"),
]

OUT_DIR = Path(__file__).parent / "findings"
OUT_DIR.mkdir(exist_ok=True)


def extract_hand_freqs(sols: dict) -> dict:
    """全 169 ハンドの fold/call/3-bet 頻度を辞書で返す。"""
    acts = sols.get('action_solutions', [])

    # 全 action を action 名でまとめる
    # F → fold, C → call, R系統 → 3-bet (合算)
    fold_strat = next((a['strategy'] for a in acts if a['action']['code'] == 'F'), [0.0]*169)
    call_strat = next((a['strategy'] for a in acts if a['action']['code'] == 'C'), [0.0]*169)
    bet_strat = [0.0] * 169
    for a in acts:
        code = a['action']['code']
        if code.startswith('R') and code != 'R0':
            for i, s in enumerate(a['strategy']):
                bet_strat[i] += s

    result = {}
    for hand, idx in HAND_TO_INDEX.items():
        result[hand] = {
            "fold": round(fold_strat[idx], 4),
            "call": round(call_strat[idx], 4),
            "3bet": round(bet_strat[idx], 4),
        }
    return result


def main():
    for label, pf in SCENARIOS:
        out_path = OUT_DIR / f"task_a_{label}.json"
        if out_path.exists():
            print(f"  [skip] {label} (already exists)")
            continue
        print(f"  fetching {label} (pf={pf!r}) ...", flush=True)
        sols = api_get(board="", flop_actions="", pf=pf, depth=100)
        if not sols:
            print(f"  [FAILED] {label}", file=sys.stderr)
            continue
        freqs = extract_hand_freqs(sols)
        # 集約値も保存
        all_acts = sols.get('action_solutions', [])
        summary = {
            "total_freq": {a['action']['code']: round(a.get('total_frequency', 0), 4) for a in all_acts}
        }
        result = {
            "scenario": label,
            "preflop_actions": pf,
            "depth": 100,
            "summary": summary,
            "hand_freqs": freqs,
        }
        with open(out_path, "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"  saved {out_path.name}")
        time.sleep(0.5)  # rate limit 配慮

    print()
    print("=== タスク A 完了 ===")
    # 全シナリオで EXCEPTIONS_BOUNDARY ハンド (BB vs BTN ベース 16 ハンド) の混合度を一覧表示
    target_hands = ["A8o", "A7o", "ATo", "K6s", "K9s", "KTo", "44",
                    "87s", "T7s", "J7s", "T9s", "22", "33", "54s", "65s", "76s"]
    print(f"\n書籍 EXCEPTIONS_BOUNDARY 16 ハンドの 5 シナリオ別 混合戦略:")
    print(f"{'hand':<6} | {'BB_vs_UTG':<18} | {'BB_vs_HJ':<18} | {'BB_vs_CO':<18} | {'BB_vs_BTN':<18} | {'BB_vs_SB':<18}")
    print("-" * 110)
    for h in target_hands:
        row = [h]
        for label, _ in SCENARIOS:
            p = OUT_DIR / f"task_a_{label}.json"
            if not p.exists():
                row.append("N/A")
                continue
            with open(p) as f:
                data = json.load(f)
            freq = data['hand_freqs'].get(h, {})
            fold, call, bet = freq.get('fold', 0), freq.get('call', 0), freq.get('3bet', 0)
            row.append(f"F{fold:.2f}/C{call:.2f}/3{bet:.2f}")
        print(" | ".join(f"{s:<18}" if i > 0 else f"{s:<6}" for i, s in enumerate(row)))


if __name__ == "__main__":
    main()
