#!/usr/bin/env python3
"""
GTO 整合性検証スクリプト v3 (新スケール HandScore 0-100 equity %)

新仕様 (knowledges/ds_redesign_v2/SPEC_HANDSCORE.md) の予測精度を、
既存 GTO 実測データで検証する。

Usage:
    python3 scripts/gto_consistency_v3.py [--source phase1|boundary|all]

入力:
    knowledges/volume4/results/ds_framework_recheck/result.json
    knowledges/flop/results/handscore_boundary/summary_v2.json

出力:
    knowledges/ds_redesign_v2/gto_consistency_v3_report.json
    一致率レポート (旧スケール vs 新スケール)
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

REPO = Path("/home/cuzic/poker-books")

# ─── 新スケール仕様 (SPEC_HANDSCORE.md より) ─────────────────────

# 役カテゴリ → 新 HS マッピング (代表値)
NEW_HS_BY_BUCKET = {
    "H1": 28,   # 弱
    "H2": 47,   # 中
    "H3": 70,   # 強
}

# A 値 (ボード補正)
NEW_A = {
    "K72r": 12, "kc7d2s": 12,
    "KJ7r": 6, "khjd7s": 6,
    "T98r": 0, "th9d8c": 0,
    "Adry": 12, "Ks,7c,2c": 12, "Ad,7c,2s": 12,
    "Tc,8d,4s": 6,
}

# C 値 (ベット圧、新スケール)
NEW_C = {
    33: 12, 50: 17, 75: 22, 100: 25, 150: 30,
}

# 旧スケール対応 (比較用)
OLD_HS_BY_BUCKET = {"H1": 4, "H2": 11, "H3": 17}
OLD_A = {"K72r": 3, "KJ7r": 2, "T98r": 1}
OLD_C = {33: 3, 50: 5, 75: 7, 100: 9, 150: 11}

# 閾値
NEW_TH_R = 40
NEW_TH_F = 20
OLD_TH_R = 8
OLD_TH_F = 0


def predict_new(hs: int, A: int, C: int, M: int = 0) -> str:
    """新スケール後手スコア → 予測アクション."""
    DS = hs + A - C - M
    if DS >= NEW_TH_R:
        return "RAISE"
    elif DS >= NEW_TH_F:
        return "CALL"
    return "FOLD"


def predict_old(hs: int, A: int, C: int, M: int = 0) -> str:
    """旧スケール後手スコア → 予測アクション."""
    DS = hs + A - 3 - C - M
    if DS >= OLD_TH_R:
        return "RAISE"
    elif DS >= OLD_TH_F:
        return "CALL"
    return "FOLD"


def actual_action(F: float, C: float, R: float) -> str:
    """実測の三択判定 (≥50% で確定、それ以外は最大値)."""
    if R >= 50:
        return "RAISE"
    elif F >= 50:
        return "FOLD"
    elif C >= 50:
        return "CALL"
    # 全て < 50 の境界域
    if R > C and R > F:
        return "RAISE"
    elif F > C:
        return "FOLD"
    return "CALL"


def evaluate_phase1():
    """ds_framework_recheck (27 cases) で旧 vs 新スケールの一致率を比較."""
    f = REPO / "knowledges/volume4/results/ds_framework_recheck/result.json"
    data = json.load(open(f))

    new_correct = 0
    new_boundary = 0
    old_correct = 0
    old_boundary = 0
    total = 0
    rows = []

    for row in data["rows"]:
        board = row["board"]
        bet_pct = int(row["size"].rstrip("%"))
        bucket = row["bucket"]

        new_hs = NEW_HS_BY_BUCKET[bucket]
        new_a = NEW_A.get(board, 0)
        new_c = NEW_C[bet_pct]
        new_pred = predict_new(new_hs, new_a, new_c)

        old_hs = OLD_HS_BY_BUCKET[bucket]
        old_a = OLD_A.get(board, 0)
        old_c = OLD_C[bet_pct]
        old_pred = predict_old(old_hs, old_a, old_c)

        actual = actual_action(row["fold_pct"], row["call_pct"], row["raise_pct"])

        new_match = new_pred == actual
        old_match = old_pred == actual

        new_DS = new_hs + new_a - new_c
        new_is_boundary = abs(new_DS - NEW_TH_R) <= 5 or abs(new_DS - NEW_TH_F) <= 5
        old_DS = old_hs + old_a - 3 - old_c
        old_is_boundary = abs(old_DS - OLD_TH_R) <= 2 or abs(old_DS - OLD_TH_F) <= 2

        if new_match:
            new_correct += 1
        elif new_is_boundary:
            new_boundary += 1
        if old_match:
            old_correct += 1
        elif old_is_boundary:
            old_boundary += 1
        total += 1

        rows.append({
            "board": board,
            "bet_pct": bet_pct,
            "bucket": bucket,
            "actual": actual,
            "new_pred": new_pred,
            "new_DS": new_DS,
            "new_match": new_match,
            "old_pred": old_pred,
            "old_DS": old_DS,
            "old_match": old_match,
        })

    return {
        "test_set": "Phase1 ds_framework_recheck",
        "total": total,
        "new_scale": {
            "match_rate": new_correct / total * 100,
            "match_inc_boundary": (new_correct + new_boundary) / total * 100,
            "correct": new_correct,
            "boundary": new_boundary,
        },
        "old_scale": {
            "match_rate": old_correct / total * 100,
            "match_inc_boundary": (old_correct + old_boundary) / total * 100,
            "correct": old_correct,
            "boundary": old_boundary,
        },
        "rows": rows,
    }


def evaluate_boundary():
    """handscore_boundary (14 cases) で個別ハンドの精度を確認."""
    f = REPO / "knowledges/flop/results/handscore_boundary/summary_v2.json"
    data = json.load(open(f))

    # 個別ハンドラベル → 推定 HS
    def estimate_new_hs(label: str) -> int:
        """SPEC_HANDSCORE.md に基づくラベル → 新 HS マッピング."""
        ll = label.lower()
        role = 0
        if "tpgk" in ll:
            role = 62
        elif "tptk" in ll:
            role = 70
        elif "tpmk" in ll:
            role = 50
        elif "tpwk" in ll:
            role = 45
        elif "2nd" in ll or "セカンド" in ll:
            role = 32

        draw = 0
        # "no FD" を判定
        if "no fd" in ll or "no_fd" in ll:
            pass  # FD なし
        elif "nut fd" in ll or "ナッツfd" in ll:
            draw = 36
        elif "fd" in ll and "bdfd" not in ll:
            # tpwk+FD など
            draw = 36
        elif "oesd" in ll:
            draw = 32
        elif "gut" in ll:
            draw = 16
        elif "bdfd" in ll:
            draw = 5

        blocker = 0
        if "nut fd" in ll or "ナッツfd" in ll:
            blocker = 5

        return min(100, role + draw + blocker)

    correct = 0
    boundary = 0
    total = 0
    rows = []

    for x in data:
        board = x["board"]
        label = x["label"].split("[")[0].strip()
        new_hs = estimate_new_hs(label)
        new_a = NEW_A.get(board, 6)
        new_c = NEW_C[33]  # oop33 のみ
        new_DS = new_hs + new_a - new_c
        new_pred = predict_new(new_hs, new_a, new_c)

        F = x["oop33"]["F"]
        C = x["oop33"]["C"]
        R = x["oop33"]["R"]
        actual = actual_action(F, C, R)

        is_match = new_pred == actual
        is_boundary = abs(new_DS - NEW_TH_R) <= 5 or abs(new_DS - NEW_TH_F) <= 5

        if is_match:
            correct += 1
        elif is_boundary:
            boundary += 1
        total += 1

        rows.append({
            "board": board,
            "label": label,
            "new_hs": new_hs,
            "new_DS": new_DS,
            "new_pred": new_pred,
            "actual": actual,
            "match": is_match,
        })

    return {
        "test_set": "handscore_boundary individual hands",
        "total": total,
        "new_scale": {
            "match_rate": correct / total * 100,
            "match_inc_boundary": (correct + boundary) / total * 100,
            "correct": correct,
            "boundary": boundary,
        },
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all", choices=["phase1", "boundary", "all"])
    parser.add_argument("--out", default="knowledges/ds_redesign_v2/gto_consistency_v3_report.json")
    args = parser.parse_args()

    results = {}

    if args.source in ("phase1", "all"):
        r = evaluate_phase1()
        results["phase1"] = r
        print(f"=== {r['test_set']} ({r['total']} cases) ===")
        print(f"  新スケール: {r['new_scale']['match_rate']:.1f}% (境界含み {r['new_scale']['match_inc_boundary']:.1f}%)")
        print(f"  旧スケール: {r['old_scale']['match_rate']:.1f}% (境界含み {r['old_scale']['match_inc_boundary']:.1f}%)")
        print()

    if args.source in ("boundary", "all"):
        r = evaluate_boundary()
        results["boundary"] = r
        print(f"=== {r['test_set']} ({r['total']} cases) ===")
        print(f"  新スケール: {r['new_scale']['match_rate']:.1f}% (境界含み {r['new_scale']['match_inc_boundary']:.1f}%)")
        print()

    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"レポート出力: {out_path}")


if __name__ == "__main__":
    main()
