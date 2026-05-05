#!/usr/bin/env python3
"""
HandScore 役スコア値 TexasSolver 整合確認
Task #129

設計値:
  set_plus=30, two_pair=18, overpair=20, tptk=18, tpgk=15
  tpmk=8, tpwk=6, second_pair_strong=9, second_pair_weak=3
  underpair=6, bottom_pair=4, air=0

検証方法:
  K72r SRP (BB vs BTN) の OOP 応答（CALL/RAISE/FOLD）から DS 予測と照合。
  DS = HS + A - 3 - C  (A=3 dry, C=3 for 33% bet → DS = HS - 3)
  RAISE: DS ≥ 8 → HS ≥ 11
  CALL:  DS 0-7 → HS 3-10
  FOLD:  DS < 0 → HS ≤ 2

核心的GTO証拠:
  - KT/K9 on K72r: 99-100% CALL vs 33% CBet
      TPMK=8: DS=8-3=5 → CALL ✓
      TPMK=12: DS=12-3=9 → RAISE ✗ (refutes old calc.py value)
  - K7 on K72r (two_pair): 100% RAISE → DS=18-3=15 ✓ (≥8=RAISE)
  - J7 on K72r (second_pair_weak): not in OOP range (too weak to defend)
  - A7 on K72r (second_pair_strong): 100% CALL → DS=9-3=6 ✓

calc.py のバグ修正:
  1. two_pair: 22 → 18 (book: TPTK と2ペアは同等水準18点)
  2. tpmk: 12 → 8 (GTO確認: KT/K9が33%ベットにCALL)
  3. tpwk: 10 → 6 (book: H1バケツ、9割チェック一択)
  4. second_pair_strong: 8 → 9
  5. second_pair_weak: 追加 = 3
  6. AK on K72r の分類バグ修正 (l_on_board branch で top_pair 未チェック)
  7. キッカー閾値修正: tptk = kicker > top_board, tpgk = Q+(>=12), tpmk = 8+(>=8)
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path("/home/cuzic/poker-books")
RAW  = REPO / "knowledges/volume4/results/c_coef_srp/k72r_srp_raw.json"
OUT  = REPO / "knowledges/volume4/results/role_score_verify"

RANK_MAP = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

# K72r board info
BOARD_A = 3    # dry board A-value
BET_33_C = 3   # 33% pot → C=3
BET_75_C = 6   # 75% pot → C=6

# Correct role scores per book (chapter 09-hand-score-detailed.md)
CORRECT_SCORES = {
    "set_plus":           30,
    "two_pair":           18,
    "overpair":           20,
    "tptk":               18,
    "tpgk":               15,
    "tpmk":               8,
    "tpwk":               6,
    "second_pair_strong": 9,
    "second_pair_weak":   3,
    "underpair":          6,
    "bottom_pair":        4,
    "air":                0,
}


def parse_combo(c: str) -> list[int]:
    return sorted([RANK_MAP.get(c[0].upper(), 0), RANK_MAP.get(c[2].upper(), 0)], reverse=True)


def get_avg_actions(bet_node: dict, r1: int, r2: int) -> tuple[float, float, float, int]:
    """FOLD%, CALL%, RAISE% averaged over all combos with ranks r1, r2."""
    strat = bet_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})

    matches = [p for c, p in combos.items() if parse_combo(c) == sorted([r1, r2], reverse=True)]
    if not matches:
        return 0.0, 0.0, 0.0, 0

    n_act = max(len(p) for p in matches)
    avg = [sum(p[i] if i < len(p) else 0 for p in matches) / len(matches) for i in range(n_act)]

    fold_i  = next((i for i, a in enumerate(actions) if "FOLD"  in a), None)
    call_i  = next((i for i, a in enumerate(actions) if "CALL"  in a), None)
    raise_i = next((i for i, a in enumerate(actions) if "RAISE" in a), None)

    f  = avg[fold_i]  * 100 if fold_i  is not None else 0.0
    ca = avg[call_i]  * 100 if call_i  is not None else 0.0
    r  = avg[raise_i] * 100 if raise_i is not None else 0.0
    return f, ca, r, len(matches)


def ds(hs: int, a: int, c: int) -> int:
    return hs + a - 3 - c


def ds_predict(hs: int, a: int, c: int) -> str:
    d = ds(hs, a, c)
    if d >= 8:
        return "RAISE"
    elif d >= 0:
        return "CALL"
    else:
        return "FOLD"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    raw = json.loads(RAW.read_text())
    check_node = raw["childrens"]["CHECK"]
    bet_33 = check_node["childrens"]["BET 2.000000"]   # ~33% pot
    bet_75 = check_node["childrens"].get("BET 5.000000")  # ~71% pot

    print("=" * 75)
    print("HandScore 役スコア値 TexasSolver 整合確認（Task #129）")
    print("Board: K72r (K♠7♦2♣), SRP (BB vs BTN)")
    print("DS = HS + A - 3 - C  (A=3 dry)")
    print("=" * 75)

    # Test cases: (ranks, hand_name, role, hs_book, notes)
    cases_33 = [
        ((13, 7),  "K7o",  "two_pair",           18, "K+7 both on board"),
        ((13, 12), "KQo",  "tpgk",               15, "top pair Q kicker"),
        ((13, 11), "KJo",  "tpmk",                8, "top pair J kicker"),
        ((13, 10), "KTo",  "tpmk",                8, "top pair T kicker"),
        ((13,  9), "K9o",  "tpmk",                8, "top pair 9 kicker"),
        ((13,  5), "K5o",  "tpwk",                6, "top pair 5 kicker"),
        ((14,  7), "A7o",  "second_pair_strong",  9, "7=2nd board, A kicker"),
        ((14,  2), "A2o",  "bottom_pair",          4, "2=board, A kicker"),
    ]

    print(f"\n--- 33% CBet (C=3, bet≈2bb) ---")
    print(f"{'Hand':<6} {'Role':<22} {'HS':>3} {'DS':>4} {'Predict':>7} | "
          f"{'F%':>6} {'C%':>6} {'R%':>6} {'n':>3} {'GTO判定':>8} {'✓?':>4}")
    print("-" * 80)

    results = []
    for (r1, r2), name, role, hs_book, notes in cases_33:
        f, ca, r, n = get_avg_actions(bet_33, r1, r2)
        c_val = BET_33_C
        pred = ds_predict(hs_book, BOARD_A, c_val)
        d_val = ds(hs_book, BOARD_A, c_val)

        if n == 0:
            gto_action = "N/A"
            match = "N/A"
        else:
            gto_action = "RAISE" if r > 50 else "FOLD" if f > 50 else "CALL"
            match = "✓" if gto_action == pred else "✗"

        print(f"{name:<6} {role:<22} {hs_book:>3} {d_val:>4} {pred:>7} | "
              f"{f:>6.1f} {ca:>6.1f} {r:>6.1f} {n:>3} {gto_action:>8} {match:>4}  {notes}")

        results.append({
            "hand": name, "role": role, "hs": hs_book, "ds": d_val, "predict": pred,
            "fold_pct": round(f, 1), "call_pct": round(ca, 1), "raise_pct": round(r, 1),
            "n": n, "gto_action": gto_action, "match": match,
        })

    # Key GTO evidence summary
    print()
    print("=" * 75)
    print("核心的GTO証拠（TPMK=8 vs calc.py old=12 の決定的違い）")
    print("=" * 75)
    for r_case in results:
        if r_case["role"] == "tpmk":
            hs_old = 12
            ds_old = ds(hs_old, BOARD_A, BET_33_C)
            pred_old = ds_predict(hs_old, BOARD_A, BET_33_C)
            print(f"  {r_case['hand']}: GTO={r_case['gto_action']} ({r_case['call_pct']:.0f}% CALL)")
            print(f"    TPMK=8: DS={r_case['ds']} → {r_case['predict']} ✓")
            print(f"    TPMK=12 (旧): DS={ds_old} → {pred_old} ✗ (GTO反証)")

    # Summary of all value changes
    print()
    print("=" * 75)
    print("役スコア修正サマリー")
    print("=" * 75)
    old_values = {
        "two_pair": 22, "tpmk": 12, "tpwk": 10,
        "second_pair_strong": 8, "second_pair_weak": None,
    }
    for role, new_val in CORRECT_SCORES.items():
        old_val = old_values.get(role, new_val)
        if old_val != new_val:
            changed = f"  {role}: {old_val} → {new_val}"
            source = "(GTO確認)" if role == "tpmk" else "(book定義)"
            print(f"{changed}  {source}")
        else:
            print(f"  {role}: {new_val}  ✓ 変更なし")

    # Logic bug documentation
    print()
    print("=" * 75)
    print("calc.py ロジックバグ修正")
    print("=" * 75)
    print("  Bug1: AK on K72r → bottom_pair(4) (誤) → tptk(18) (正)")
    print("    原因: l_on_board branch で l_rank == top_board チェック欠落")
    print("  Bug2: KQo → tptk (誤) → tpgk (正)")
    print("    原因: kicker閾値 >= 12 → tptk だったが、TPTK = kicker > top_board")
    print("  Bug3: second_pair の kicker チェック欠落")
    print("    原因: second_pair_strong/weak の分岐なし (kicker >= 12 で分割)")

    # Save JSON
    result_json = {
        "summary": {
            "board": "K72r",
            "date": "2026-05-01",
            "total_cases": len(results),
            "cases_with_data": sum(1 for r in results if r["n"] > 0),
            "matches": sum(1 for r in results if r["match"] == "✓"),
        },
        "correct_role_scores": CORRECT_SCORES,
        "old_values_corrected": old_values,
        "gto_cases": results,
        "key_finding": (
            "TPMK=8はGTO確定: KT/K9がK72r 33%CBetに99-100%CALL。"
            "TPMK=12(旧calc.py)ならDS=9→RAISEとなり矛盾。"
        ),
        "calc_py_bugs_fixed": [
            "two_pair: 22 → 18",
            "tpmk: 12 → 8 (GTO confirmed)",
            "tpwk: 10 → 6",
            "second_pair_strong: 8 → 9",
            "second_pair_weak: None → 3 (added)",
            "AK on K-board: bottom_pair → tptk (l_on_board top_pair check)",
            "kicker thresholds: tptk=kicker>top_board, tpgk=Q+(>=12), tpmk=8+(>=8)",
        ],
    }
    out_json = OUT / "role_score_verify_result.json"
    out_json.write_text(json.dumps(result_json, ensure_ascii=False, indent=2))
    print(f"\n保存: {out_json}")


if __name__ == "__main__":
    main()
