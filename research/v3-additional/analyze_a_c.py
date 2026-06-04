#!/usr/bin/env python3
"""
analyze_a_c.py — タスク A + C の結果を集計、書籍値との差分レポート作成
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from hand_order import HAND_TO_INDEX

OUT_DIR = Path(__file__).parent / "findings"

# ========== タスク A: BB defense 境界帯 ==========

BB_SCENARIOS = ["BB_vs_UTG", "BB_vs_HJ", "BB_vs_CO", "BB_vs_BTN", "BB_vs_SB"]

# 書籍 EXCEPTIONS_BOUNDARY (BB vs BTN ベース、ch11)
BOOK_EXCEPTIONS = {
    "A8o": "CALL 60%", "A7o": "FOLD 60%", "ATo": "CALL or 3BET 30%",
    "K6s": "CALL 60%", "K9s": "CALL or 3BET", "KTo": "FOLD 60%",
    "44": "CALL 70%", "87s": "CALL 60%", "T7s": "CALL 60%",
    "J7s": "CALL 60%", "T9s": "CALL or 3BET",
    "22": "CALL if deep", "33": "CALL if deep",
    "54s": "CALL if IP", "65s": "CALL if IP", "76s": "CALL if IP",
}


def load_scenario(name: str) -> dict | None:
    p = OUT_DIR / f"task_a_{name}.json"
    if not p.exists():
        return None
    with open(p) as f:
        return json.load(f)


def classify_action(freq: dict) -> str:
    """fold/call/3-bet 頻度から代表アクションを返す。"""
    if freq['fold'] >= 0.98:
        return "FOLD"
    if freq['call'] >= 0.98:
        return "CALL"
    if freq['3bet'] >= 0.98:
        return "3BET"
    # 混合戦略
    parts = []
    if freq['fold'] >= 0.05:
        parts.append(f"F{int(freq['fold']*100)}")
    if freq['call'] >= 0.05:
        parts.append(f"C{int(freq['call']*100)}")
    if freq['3bet'] >= 0.05:
        parts.append(f"3{int(freq['3bet']*100)}")
    return "/".join(parts)


def report_task_a():
    print("=" * 100)
    print("## タスク A: 書籍 EXCEPTIONS_BOUNDARY 16 ハンド × 5 シナリオ実測")
    print("=" * 100)
    print()

    # 書籍記述と全シナリオの実測を比較
    print(f"| {'ハンド':<5} | {'書籍 (BB vs BTN ベース)':<30} | {'BB vs UTG':<14} | {'BB vs HJ':<14} | {'BB vs CO':<14} | {'BB vs BTN':<14} | {'BB vs SB':<14} |")
    print("|" + "-"*7 + "|" + "-"*32 + "|" + ("-"*16 + "|") * 5)

    scenarios_data = {s: load_scenario(s) for s in BB_SCENARIOS}

    for hand, book_desc in BOOK_EXCEPTIONS.items():
        row = [hand, book_desc]
        for s in BB_SCENARIOS:
            data = scenarios_data.get(s)
            if not data or hand not in data['hand_freqs']:
                row.append("N/A")
                continue
            freq = data['hand_freqs'][hand]
            row.append(classify_action(freq))
        print(f"| {row[0]:<5} | {row[1]:<30} | " + " | ".join(f"{c:<14}" for c in row[2:]) + " |")

    print()
    print("## 主要発見")
    print()
    print("### 書籍記述と乖離があるハンド (BB vs BTN シナリオで比較)")
    for hand, book_desc in BOOK_EXCEPTIONS.items():
        btn_data = scenarios_data.get("BB_vs_BTN")
        if not btn_data:
            continue
        freq = btn_data['hand_freqs'].get(hand, {})
        actual = classify_action(freq)
        # 書籍が「FOLD 60%」と言っているのに実測 CALL/3BET、または逆のケース
        if "FOLD" in book_desc and ("CALL" in actual or "3BET" in actual) and freq['fold'] < 0.5:
            print(f"  - {hand}: 書籍「{book_desc}」 → 実測「{actual}」 (大幅乖離)")
        elif "CALL 60%" in book_desc and freq['call'] >= 0.98:
            print(f"  - {hand}: 書籍「{book_desc}」 → 実測「{actual}」 (混合ではなく純粋 CALL)")
        elif "CALL or 3BET" in book_desc and freq['call'] >= 0.98:
            print(f"  - {hand}: 書籍「{book_desc}」 → 実測「{actual}」 (3BET なし、純粋 CALL)")

    print()
    print("### オープナー位置で大きく変動するハンド (FOLD 比率の幅)")
    for hand in BOOK_EXCEPTIONS:
        folds = []
        for s in BB_SCENARIOS:
            data = scenarios_data.get(s)
            if data:
                folds.append(data['hand_freqs'][hand]['fold'])
        if folds:
            spread = max(folds) - min(folds)
            if spread >= 0.3:
                folds_str = " / ".join(f"{f:.0%}" for f in folds)
                print(f"  - {hand}: fold% = {folds_str} (range {spread:.0%})")


# ========== タスク C: スクイーズ ==========

def report_task_c():
    print()
    print("=" * 100)
    print("## タスク C: スクイーズ N=1/2 実測 (書籍 T_squeeze 公式の検証)")
    print("=" * 100)
    print()

    # 書籍 §5.2: T_squeeze = T_3bet + 3N
    T_3BET = {
        ("BTN", "UTG"): 36, ("BTN", "HJ"): 36, ("BTN", "CO"): 26,
        ("SB",  "UTG"): 34, ("SB",  "HJ"): 32, ("SB",  "CO"): 30, ("SB",  "BTN"): 25,
        ("BB",  "UTG"): 36, ("BB",  "HJ"): 34, ("BB",  "CO"): 30, ("BB",  "BTN"): 28,
    }
    # 主要ハンドの Score (Cash)
    SCORES = {"AA":41,"KK":39,"QQ":37,"JJ":35,"TT":33,"99":31,"AKs":38,"AKo":31,"AQs":36,"AQo":29,"KQs":32}

    # 各シナリオで「書籍式の T_squeeze」と「実測の squeeze 100% 最低ハンド」を比較
    scenarios = []
    for p in sorted(OUT_DIR.glob("task_c_*.json")):
        with open(p) as f:
            scenarios.append(json.load(f))

    print(f"| シナリオ | N | 書籍 T_squeeze | 実測 (主要ハンド squeeze%) |")
    print("|" + "-"*30 + "|---|" + "-"*14 + "|" + "-"*80 + "|")
    for data in scenarios:
        sc = data['scenario']
        # parse: e.g., "BTN_sq_vs_UTG_N1_co"
        parts = sc.split("_")
        if len(parts) < 4 or parts[1] != "sq" or parts[2] != "vs":
            continue
        squeezer, opener = parts[0], parts[3]
        n = int(parts[4][1])  # N1 → 1
        t3 = T_3BET.get((squeezer, opener))
        t_sq = t3 + 3 * n if t3 else None

        # 主要ハンドの squeeze 頻度
        freqs = data['hand_freqs']
        targets = ["JJ", "TT", "99", "AQs", "AQo", "KQs"]
        actual = ", ".join(f"{h}={freqs[h]['squeeze']:.0%}" for h in targets if h in freqs)
        t_sq_str = str(t_sq) if t_sq else "?"
        print(f"| {sc:<28} | {n} | {t_sq_str:<14} | {actual} |")


if __name__ == "__main__":
    report_task_a()
    report_task_c()
