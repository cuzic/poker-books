#!/usr/bin/env python3
"""validate_book_vs_gto.py — 書籍 Score 式 vs GTO 実測の精度検証

各シナリオで:
  - 書籍式 (Score ≥ T → PLAY、Score < T → FOLD) の予測
  - GTO 実測 (50%+ frequency の主アクション)
  - 一致率 (accuracy)
  - 不一致ハンドの一覧
  - huge_gap loss 候補 (実測 100% PLAY なのに書籍が FOLD 予測する等)

出力:
  - findings/validation_report.md
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "poker-drill"))
sys.path.insert(0, str(Path(__file__).parent))

from scripts.generate._common.score import score_cash, score_mtt
from hand_order import HANDS

FINDINGS = Path(__file__).parent / "findings"

# ────────────────────────────────────────────────────────────
# 書籍値 (ch03/ch04 確定値)
# ────────────────────────────────────────────────────────────

# Cash RFI T_open (ch03 §3.1)
T_OPEN_CASH = {
    "UTG": 25, "HJ": 23, "CO": 21, "BTN": 18, "SB": 22,
}

# BB defense (ch04 §4.1): (opener) → (T_3bet, T_call)
BB_DEFENSE = {
    "UTG": (36, 23), "HJ": (34, 22), "CO": (30, 20),
    "BTN": (28, 18), "SB": (30, 18),
}

# IP defense (ch04 §4.2): (hero, opener) → (T_3bet, T_call or None for 3bet-or-fold)
IP_DEFENSE = {
    ("BTN", "UTG"): (36, 29), ("BTN", "HJ"): (36, 28), ("BTN", "CO"): (26, None),
    ("CO",  "UTG"): (32, 30), ("CO",  "HJ"): (28, None),
    ("HJ",  "UTG"): (30, None),
}

# SB OOP defense (ch04 §4.3): (opener) → (T_3bet, T_call)
SB_DEFENSE = {
    "UTG": (34, 30), "HJ": (32, 29), "CO": (30, 27), "BTN": (25, 25),
}

# vs 3-bet (ch04 §4.4): (T_4bet, T_call)
VS_3BET = (37, 31)


def gto_action(freqs: dict[str, float], two_step: bool) -> str:
    """GTO 実測アクション (50%+ の主アクション)。

    two_step=True: fold/call/3-bet の 3 アクション
    two_step=False: fold/raise のみ (RFI 等)
    """
    f = freqs.get("fold", 0)
    c = freqs.get("call", 0)
    b = freqs.get("3bet", 0) or freqs.get("raise", 0) or freqs.get("squeeze", 0)
    if two_step:
        if f >= 0.50: return "FOLD"
        if b >= 0.50: return "3BET"
        if c >= 0.50: return "CALL"
        # 混合: 最大値
        return max([("FOLD", f), ("CALL", c), ("3BET", b)], key=lambda x: x[1])[0]
    else:
        # RFI: fold vs raise
        if f >= 0.50: return "FOLD"
        return "RAISE"


def book_predict_two_step(score: int, t_3bet: int, t_call) -> str:
    """書籍式の予測 (3-bet/call/fold)。"""
    if score >= t_3bet: return "3BET"
    if t_call is None: return "FOLD"
    if score >= t_call: return "CALL"
    return "FOLD"


def book_predict_one_step(score: int, t: int) -> str:
    if score >= t: return "RAISE"
    return "FOLD"


def validate_scenario(label: str, freqs_data: dict, predict_fn, score_fn=score_cash, two_step: bool = True) -> dict:
    """1 シナリオの精度検証。"""
    total = 0
    correct = 0
    mismatches = []
    for hand in HANDS:
        if hand not in freqs_data:
            continue
        total += 1
        score = score_fn(hand)
        predicted = predict_fn(score)
        actual = gto_action(freqs_data[hand], two_step)
        if predicted == actual:
            correct += 1
        else:
            mismatches.append({
                "hand": hand, "score": score,
                "predicted": predicted, "actual": actual,
                "freqs": freqs_data[hand],
            })
    return {
        "label": label,
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0,
        "mismatches": mismatches,
    }


def main():
    print("# 書籍 Score 式 vs GTO 実測の精度検証")
    print()
    print("各シナリオで書籍式 (Score ≥ T → PLAY) の予測と GTO 主アクション (50%+) を比較。")
    print()

    all_results = []

    # ── Cash RFI (5 オープナー) ──
    print("## 1. Cash RFI (ch03 §3.1)")
    print()
    print(f"書籍 T_open: {T_OPEN_CASH}")
    print()
    print("| Pos | T_open | 一致 | 整合率 |")
    print("|-----|--------|------|--------|")
    for pos, t in T_OPEN_CASH.items():
        path = FINDINGS / f"task_l_{pos}_RFI.json"
        if not path.exists():
            print(f"| {pos} | {t} | (no data) | - |")
            continue
        data = json.load(open(path))["hand_freqs"]
        r = validate_scenario(f"RFI_{pos}", data,
                              lambda s, t=t: book_predict_one_step(s, t),
                              two_step=False)
        all_results.append(("RFI", pos, r))
        print(f"| {pos} | {t} | {r['correct']}/{r['total']} | {r['accuracy']:.1%} |")
    print()

    # ── BB defense (5 オープナー) ──
    print("## 2. BB defense (ch04 §4.1)")
    print()
    print("| Opener | T_3bet/T_call | 一致 | 整合率 |")
    print("|--------|---------------|------|--------|")
    for opener, (t3, tc) in BB_DEFENSE.items():
        path = FINDINGS / f"task_a_BB_vs_{opener}.json"
        if not path.exists():
            continue
        data = json.load(open(path))["hand_freqs"]
        r = validate_scenario(f"BB_vs_{opener}", data,
                              lambda s, t3=t3, tc=tc: book_predict_two_step(s, t3, tc))
        all_results.append(("BB_defense", opener, r))
        print(f"| {opener} | {t3}/{tc} | {r['correct']}/{r['total']} | {r['accuracy']:.1%} |")
    print()

    # ── IP defense (6 セル) ──
    print("## 3. IP defense (ch04 §4.2)")
    print()
    print("| Hero | Opener | T_3bet/T_call | 一致 | 整合率 |")
    print("|------|--------|---------------|------|--------|")
    for (hero, opener), (t3, tc) in IP_DEFENSE.items():
        path = FINDINGS / f"task_d_{hero}_vs_{opener}.json"
        if not path.exists():
            continue
        data = json.load(open(path))["hand_freqs"]
        r = validate_scenario(f"{hero}_vs_{opener}", data,
                              lambda s, t3=t3, tc=tc: book_predict_two_step(s, t3, tc))
        all_results.append(("IP_defense", f"{hero}_vs_{opener}", r))
        tc_str = str(tc) if tc is not None else "—"
        print(f"| {hero} | {opener} | {t3}/{tc_str} | {r['correct']}/{r['total']} | {r['accuracy']:.1%} |")
    print()

    # ── SB OOP defense (4 オープナー) ──
    print("## 4. SB OOP defense (ch04 §4.3)")
    print()
    print("| Opener | T_3bet/T_call | 一致 | 整合率 |")
    print("|--------|---------------|------|--------|")
    for opener, (t3, tc) in SB_DEFENSE.items():
        path = FINDINGS / f"task_e_SB_vs_{opener}.json"
        if not path.exists():
            continue
        data = json.load(open(path))["hand_freqs"]
        r = validate_scenario(f"SB_vs_{opener}", data,
                              lambda s, t3=t3, tc=tc: book_predict_two_step(s, t3, tc if t3 != tc else None))
        all_results.append(("SB_defense", opener, r))
        print(f"| {opener} | {t3}/{tc} | {r['correct']}/{r['total']} | {r['accuracy']:.1%} |")
    print()

    # ── vs 3-bet (12 シナリオ) ──
    print("## 5. vs 3-bet (ch04 §4.4)")
    print()
    print(f"書籍: T_4bet={VS_3BET[0]}, T_call={VS_3BET[1]}")
    print()
    print("| Scenario | 一致 | 整合率 |")
    print("|----------|------|--------|")
    for path in sorted(FINDINGS.glob("task_f1_*.json")):
        sc = path.stem.replace("task_f1_", "")
        data = json.load(open(path))["hand_freqs"]
        # data has fold/call/raise (instead of 3bet)
        # 書籍 predict: 4-bet / call / fold
        # GTO actual: same structure, but extracting differs
        # → adapt: book_predict_two_step works since structure matches
        # but key in freqs is 'raise' not '3bet'
        r = validate_scenario(sc, data,
                              lambda s, t4=VS_3BET[0], tc=VS_3BET[1]:
                                  "3BET" if s >= t4 else ("CALL" if s >= tc else "FOLD"))
        all_results.append(("vs_3bet", sc, r))
        print(f"| {sc} | {r['correct']}/{r['total']} | {r['accuracy']:.1%} |")
    print()

    # ── 不一致が多いシナリオの top mismatches ──
    print("## 6. 不一致ハンド TOP (Score 順)")
    print()
    print("整合率が低い 5 シナリオの代表 mismatches を抽出。")
    print()
    low_accuracy = sorted(all_results, key=lambda x: x[2]["accuracy"])[:5]
    for cat, name, r in low_accuracy:
        print(f"### {cat}: {name} (整合率 {r['accuracy']:.1%})")
        print()
        print("| Hand | Score | 書籍予測 | GTO 主 | F% | C% | R% |")
        print("|------|-------|---------|--------|-----|-----|-----|")
        for m in r["mismatches"][:10]:
            freqs = m["freqs"]
            f = freqs.get("fold", 0)
            c = freqs.get("call", 0)
            b = freqs.get("3bet", 0) or freqs.get("raise", 0) or 0
            print(f"| {m['hand']} | {m['score']} | {m['predicted']} | {m['actual']} | {f:.0%} | {c:.0%} | {b:.0%} |")
        print()

    # ── 全体サマリ ──
    print("## 7. 全体サマリ")
    print()
    total_correct = sum(r[2]["correct"] for r in all_results)
    total = sum(r[2]["total"] for r in all_results)
    print(f"**全シナリオ合計**: {total_correct}/{total} = **{total_correct/total:.1%}**")
    print()
    by_cat = {}
    for cat, _, r in all_results:
        if cat not in by_cat:
            by_cat[cat] = {"correct": 0, "total": 0}
        by_cat[cat]["correct"] += r["correct"]
        by_cat[cat]["total"] += r["total"]
    print("| カテゴリ | 一致 | 整合率 |")
    print("|----------|------|--------|")
    for cat, d in by_cat.items():
        print(f"| {cat} | {d['correct']}/{d['total']} | {d['correct']/d['total']:.1%} |")


if __name__ == "__main__":
    main()
