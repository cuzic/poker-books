#!/usr/bin/env python3
"""
HandScore 役スコア値 TexasSolver 整合確認 v3 (新スケール 0-100 equity %)

旧版 role_score_verify.py の新スケール対応。
旧版は残し、新規 v3 として作成。

新スケール役スコア (knowledges/ds_redesign_v2/SPEC_HANDSCORE.md):
  set_plus:           88-92 (Top set 92 / Mid set 88 / Bottom set 85)
  two_pair:           68-78 (top 2: 78, top+mid: 75, top+bottom: 72)
  overpair:           68-78
  TPTK:               70
  TPGK:               62
  TPMK:               50
  TPWK:               45
  underpair:          35-45
  second_pair_strong: 42 (Q+ kicker)
  second_pair_weak:   32 (J以下 kicker)
  bottom_pair:        32
  air:                8-25

検証方法:
  K72r SRP (BB vs BTN) の OOP 応答（CALL/RAISE/FOLD）から DS 予測と照合。
  DS = HS + A - C - M (新式)
  A=12 (dry), C=12 (33%), M=0 → DS = HS
  RAISE: DS >= 40 → HS >= 40
  CALL:  DS 20-39 → HS 20-39 (after A=12, C=12 cancel out)
  FOLD:  DS < 20  → HS < 20
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path("/home/cuzic/poker-books")
sys.path.insert(0, str(REPO / "scripts"))
from c_coefficients_v3 import (  # noqa: E402
    A_TABLE, C_TABLE, M_TABLE,
    DS_TH_RAISE, DS_TH_CALL,
    defender_score, predict_defender,
)

RAW = REPO / "knowledges/volume4/results/c_coef_srp/k72r_srp_raw.json"
OUT = REPO / "knowledges/volume4/results/role_score_verify"

RANK_MAP = {
    'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
    '9': 9, '8': 8, '7': 7, '6': 6, '5': 5, '4': 4, '3': 3, '2': 2,
}

# K72r ボード設定 (新スケール)
BOARD_TYPE = "dry"           # A=12
BOARD_A = A_TABLE[BOARD_TYPE]
BET_33_C = C_TABLE[33]       # 12
BET_75_C = C_TABLE[75]       # 22
M_HU = M_TABLE["HU"]         # 0

# 新スケール役スコア (SPEC_HANDSCORE.md)
CORRECT_SCORES_V3 = {
    "set_plus":           88,
    "two_pair":           75,   # top 2 ペア標準
    "overpair":           72,   # 中オーバーペア (JJ-TT)
    "tptk":               70,
    "tpgk":               62,
    "tpmk":               50,
    "tpwk":               45,
    "second_pair_strong": 42,
    "second_pair_weak":   32,
    "underpair":          40,   # 中アンダーペア
    "bottom_pair":        32,
    "air":                15,   # ハイカード平均
}


def parse_combo(c: str) -> list[int]:
    return sorted(
        [RANK_MAP.get(c[0].upper(), 0), RANK_MAP.get(c[2].upper(), 0)],
        reverse=True,
    )


def get_avg_actions(bet_node: dict, r1: int, r2: int) -> tuple[float, float, float, int]:
    """FOLD%, CALL%, RAISE% (averaged) for combos with the given ranks."""
    strat = bet_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})

    matches = [
        p for c, p in combos.items()
        if parse_combo(c) == sorted([r1, r2], reverse=True)
    ]
    if not matches:
        return 0.0, 0.0, 0.0, 0

    n_act = max(len(p) for p in matches)
    avg = [
        sum(p[i] if i < len(p) else 0 for p in matches) / len(matches)
        for i in range(n_act)
    ]

    fold_i = next((i for i, a in enumerate(actions) if "FOLD" in a), None)
    call_i = next((i for i, a in enumerate(actions) if "CALL" in a), None)
    raise_i = next((i for i, a in enumerate(actions) if "RAISE" in a), None)

    f = avg[fold_i] * 100 if fold_i is not None else 0.0
    ca = avg[call_i] * 100 if call_i is not None else 0.0
    r = avg[raise_i] * 100 if raise_i is not None else 0.0
    return f, ca, r, len(matches)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    if not RAW.exists():
        print(f"ERROR: {RAW} 未存在")
        return

    raw = json.loads(RAW.read_text())
    check_node = raw["childrens"]["CHECK"]
    bet_33 = check_node["childrens"].get("BET 2.000000")
    bet_75 = check_node["childrens"].get("BET 5.000000")

    if bet_33 is None:
        print("ERROR: BET 2.000000 ノード未存在")
        return

    print("=" * 80)
    print("HandScore 役スコア値 TexasSolver 整合確認 v3 (新スケール 0-100)")
    print("Board: K72r (Kc,7d,2s), SRP (BB vs BTN)")
    print(f"DS = HS + A - C - M  (A={BOARD_A} dry, M={M_HU} HU)")
    print(f"閾値: >={DS_TH_RAISE} RAISE / >={DS_TH_CALL} CALL / <{DS_TH_CALL} FOLD")
    print("=" * 80)

    cases = [
        # (ranks, hand_name, role, hs_book_v3, notes)
        ((13, 7),  "K7o",  "two_pair",            75, "K+7 both on board"),
        ((13, 12), "KQo",  "tpgk",                62, "top pair Q kicker"),
        ((13, 11), "KJo",  "tpmk",                50, "top pair J kicker"),
        ((13, 10), "KTo",  "tpmk",                50, "top pair T kicker"),
        ((13,  9), "K9o",  "tpmk",                50, "top pair 9 kicker"),
        ((13,  5), "K5o",  "tpwk",                45, "top pair 5 kicker"),
        ((14,  7), "A7o",  "second_pair_strong",  42, "7=2nd, A kicker"),
        ((14,  2), "A2o",  "bottom_pair",         32, "2=board, A kicker"),
    ]

    print(f"\n--- 33% CBet (C={BET_33_C}, bet=2bb) ---")
    print(
        f"{'Hand':<6} {'Role':<22} {'HS':>3} {'DS':>4} {'Predict':>7} | "
        f"{'F%':>6} {'C%':>6} {'R%':>6} {'n':>3} {'GTO判定':>8} {'OK?':>4}"
    )
    print("-" * 90)

    results_33 = []
    for (r1, r2), name, role, hs_book, notes in cases:
        f, ca, r, n = get_avg_actions(bet_33, r1, r2)
        ds = defender_score(hs_book, BOARD_A, BET_33_C, M_HU)
        pred = predict_defender(ds).upper()

        if n == 0:
            gto_action = "N/A"
            match = "N/A"
        else:
            gto_action = (
                "RAISE" if r > 50 else
                "FOLD" if f > 50 else
                "CALL"
            )
            match = "✓" if gto_action == pred else "✗"

        print(
            f"{name:<6} {role:<22} {hs_book:>3} {ds:>4} {pred:>7} | "
            f"{f:>6.1f} {ca:>6.1f} {r:>6.1f} {n:>3} {gto_action:>8} {match:>4}  {notes}"
        )

        results_33.append({
            "hand": name, "role": role, "hs": hs_book, "ds": ds,
            "predict": pred, "fold_pct": round(f, 1),
            "call_pct": round(ca, 1), "raise_pct": round(r, 1),
            "n": n, "gto_action": gto_action, "match": match,
            "bet_size": "33%",
        })

    # 75% CBet
    if bet_75 is not None:
        print(f"\n--- 75% CBet (C={BET_75_C}, bet=5bb) ---")
        print(
            f"{'Hand':<6} {'Role':<22} {'HS':>3} {'DS':>4} {'Predict':>7} | "
            f"{'F%':>6} {'C%':>6} {'R%':>6} {'n':>3} {'GTO判定':>8} {'OK?':>4}"
        )
        print("-" * 90)

        results_75 = []
        for (r1, r2), name, role, hs_book, notes in cases:
            f, ca, r, n = get_avg_actions(bet_75, r1, r2)
            ds = defender_score(hs_book, BOARD_A, BET_75_C, M_HU)
            pred = predict_defender(ds).upper()

            if n == 0:
                gto_action = "N/A"
                match = "N/A"
            else:
                gto_action = (
                    "RAISE" if r > 50 else
                    "FOLD" if f > 50 else
                    "CALL"
                )
                match = "✓" if gto_action == pred else "✗"

            print(
                f"{name:<6} {role:<22} {hs_book:>3} {ds:>4} {pred:>7} | "
                f"{f:>6.1f} {ca:>6.1f} {r:>6.1f} {n:>3} {gto_action:>8} {match:>4}  {notes}"
            )

            results_75.append({
                "hand": name, "role": role, "hs": hs_book, "ds": ds,
                "predict": pred, "fold_pct": round(f, 1),
                "call_pct": round(ca, 1), "raise_pct": round(r, 1),
                "n": n, "gto_action": gto_action, "match": match,
                "bet_size": "75%",
            })
    else:
        results_75 = []

    # サマリー
    print()
    print("=" * 80)
    print("役スコア値 (新スケール v3) 早見表")
    print("=" * 80)
    for role, score in CORRECT_SCORES_V3.items():
        print(f"  {role:<22}: {score:>3}")

    # JSON 保存
    out_data = {
        "scale": "v3 (new, 0-100 equity %)",
        "formula": "DS = HS + A - C - M",
        "thresholds": {
            "raise": f">= {DS_TH_RAISE}",
            "call":  f">= {DS_TH_CALL}",
            "fold":  f"< {DS_TH_CALL}",
        },
        "board": "K72r",
        "board_setup": {"A": BOARD_A, "type": BOARD_TYPE},
        "correct_role_scores": CORRECT_SCORES_V3,
        "cases_33pct": results_33,
        "cases_75pct": results_75,
    }
    out_json = OUT / "role_score_verify_v3_result.json"
    out_json.write_text(json.dumps(out_data, ensure_ascii=False, indent=2))
    print(f"\n保存: {out_json}")


if __name__ == "__main__":
    main()
