#!/usr/bin/env python3
"""recalculate_examples.py のユニットテスト。

実行:
    cd /home/cuzic/poker-books/scripts
    python3 -m pytest test_recalculate_examples.py -v
    # or
    python3 test_recalculate_examples.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from recalculate_examples import (
    process_line,
    recalc_back_score,
    infer_role_score,
    predict_new,
    predict_old,
    OLD_TO_NEW_C,
    OLD_TO_NEW_A,
    OLD_TO_NEW_M,
)


# ============================================================
# テストケース (10 件)
# ============================================================
def test_back_score_tpgk_call():
    """TPGK on dry vs 50% bet → 旧コール、新 CR (判定変化)."""
    line = "後手スコア = 15 + 3 − 3 − 5 = 10 → コール"
    matches = process_line(line, "TPGK相当")
    assert len(matches) >= 1
    m = matches[0]
    # 新: 62 + 12 − 17 = 57 → CR
    assert "62" in m.new and "12" in m.new and "17" in m.new
    assert "57" in m.new
    assert m.decision_change, "旧コール → 新 CR の判定変化を検出すべし"


def test_back_score_tptk_strong():
    """TPTK 18 + dry 3 - 3 - 7 = 11 → CR (旧 CR、新も CR)."""
    line = "後手スコア = 18 + 3 − 3 − 7 = 11 → CR"
    matches = process_line(line, "TPTK 強い2ペア")
    assert len(matches) >= 1
    m = matches[0]
    # 新: 70 (TPTK) + 12 − 22 = 60 → CR
    assert "70" in m.new
    assert "60" in m.new
    assert not m.decision_change, "旧 CR → 新 CR は変化なし"


def test_back_score_with_m():
    """M 値を含むケース: 0 + 3 − 3 − 7 − 0 = −7 → フォールド."""
    line = "後手スコア = 0 + 3 − 3 − 7 − 0 = −7 → フォールド"
    matches = process_line(line, "空振り フォールド")
    assert len(matches) >= 1
    m = matches[0]
    # 新: 8 + 12 − 22 − 0 = −2 → フォールド
    assert "12" in m.new and "22" in m.new
    assert "フォールド" in m.new


def test_back_score_pocket_air():
    """旧 6 + 3 − 3 − 5 − 0 = 1 → コール."""
    line = "後手スコア = 6 + 3 − 3 − 5 − 0 = 1 → コール"
    matches = process_line(line, "TPWK")
    assert len(matches) >= 1
    m = matches[0]
    # 新: 45 (TPWK) + 12 − 17 − 0 = 40 → CR (or 境界)
    # 45 + 12 - 17 = 40 → CR
    assert "45" in m.new


def test_alpha_unchanged():
    """α 値は新旧で変わらない."""
    line = "α = 5 ÷ (10 + 5) ≈ 0.33"
    matches = process_line(line, "")
    assert len(matches) >= 1
    m = matches[0]
    assert m.kind == "alpha"
    assert "α 値は不変" in m.note


def test_handscore_tpgk_alone():
    """単独 HandScore = 15 → 62."""
    line = "HandScore = 15（TPGK相当）"
    matches = process_line(line, "TPGK 相当")
    assert len(matches) >= 1
    m = matches[0]
    assert m.kind == "handscore"
    assert "62" in m.new


def test_handscore_tptk_alone():
    """HandScore = 18 + TPTK 文脈 → 70."""
    line = "HandScore = 18"
    matches = process_line(line, "TPTK A♠K♠")
    assert len(matches) >= 1
    m = matches[0]
    assert "70" in m.new


def test_handscore_already_new_skip():
    """既に新スケール (HandScore = 62) はスキップ."""
    line = "HandScore = 62"
    matches = process_line(line, "TPGK")
    # 62 は new_scale_values に含まれるのでスキップされる
    handscore_matches = [m for m in matches if m.kind == "handscore"]
    assert len(handscore_matches) == 0


def test_threshold_old_8_to_40():
    """CR 閾値 ≥8 → ≥40."""
    line = "CR閾値（≥8）を上回る"
    matches = process_line(line, "")
    thresh_matches = [m for m in matches if m.kind == "thresh"]
    assert len(thresh_matches) >= 1
    m = thresh_matches[0]
    assert "40" in m.new


def test_recalc_back_score_function():
    """recalc_back_score の基本動作."""
    # TPGK 文脈
    r = recalc_back_score(15, 3, 5, 0, "TPGK 相当")
    assert r["new_hs"] == 62
    assert r["new_a"] == 12
    assert r["new_c"] == 17
    assert r["new_m"] == 0
    assert r["new_score"] == 62 + 12 - 17 - 0  # 57
    assert r["new_decision"] == "CR"


def test_predict_thresholds():
    """新閾値の判定."""
    assert predict_new(40) == "CR"
    assert predict_new(39) == "コール"
    assert predict_new(20) == "コール"
    assert predict_new(19) == "フォールド"
    assert predict_new(-5) == "フォールド"


def test_old_thresholds():
    """旧閾値の判定."""
    assert predict_old(8) == "CR"
    assert predict_old(7) == "コール"
    assert predict_old(0) == "コール"
    assert predict_old(-1) == "フォールド"


def test_infer_role_score_with_hint():
    """文脈ヒントで役カテゴリを判定."""
    new_hs, _, _ = infer_role_score(15, "TPGK 相当のハンド")
    assert new_hs == 62

    new_hs, _, _ = infer_role_score(18, "TPTK A♠K♣")
    assert new_hs == 70

    new_hs, _, _ = infer_role_score(30, "トップセット")
    assert new_hs == 92


def test_conversion_tables():
    """変換テーブルの整合性."""
    # C 値
    assert OLD_TO_NEW_C[3] == 12   # 33%
    assert OLD_TO_NEW_C[5] == 17   # 50%
    assert OLD_TO_NEW_C[7] == 22   # 75%
    assert OLD_TO_NEW_C[9] == 25   # 100%
    assert OLD_TO_NEW_C[11] == 30  # 150%

    # A 値
    assert OLD_TO_NEW_A[3] == 12  # dry
    assert OLD_TO_NEW_A[2] == 6   # semi
    assert OLD_TO_NEW_A[1] == 0   # wet

    # M 値
    assert OLD_TO_NEW_M[0] == 0
    assert OLD_TO_NEW_M[3] == 12
    assert OLD_TO_NEW_M[6] == 22


def test_real_volume4_line():
    """実際の volume4 13 章のライン."""
    line = "後手スコア = 15 + 3 − 3 − 5 = 10 → コール"
    matches = process_line(line, "K♣J♣ TPGK相当 Jキッカー")
    assert len(matches) >= 1
    m = matches[0]
    # TPGK 文脈 → 新 HS=62, A=12, C=17, score=57, → CR
    assert m.decision_change
    assert "57" in m.new


# ============================================================
# 実行
# ============================================================
def _run_all() -> int:
    test_funcs = [v for k, v in globals().items() if k.startswith("test_")]
    passed = 0
    failed = 0
    for fn in test_funcs:
        try:
            fn()
            print(f"[OK] {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print()
    print(f"{passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(_run_all())
