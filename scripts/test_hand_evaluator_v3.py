#!/usr/bin/env python3
"""pytest テスト: hand_evaluator_v3.

SPEC §5 (計算例) と §10 (GTO 整合性検証境界例) を網羅。
"""
from __future__ import annotations

import os
import sys

# scripts ディレクトリを path に追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

from hand_evaluator_v3 import (
    NEW_ROLE_SCORE,
    back_score_v3,
    blocker_bonus,
    bucket_v3,
    draw_bonus,
    evaluate_v3,
    parse_board,
    predict_v3,
)


# ============================================================
# SPEC §5 計算例
# ============================================================
class TestSpecExamples:
    """SPEC §5 の計算例 1〜8 を再現。"""

    def test_example_1_tpgk_dry_flop(self):
        """例1: TPGK on K♣7♦2♠ → HS=62"""
        score, label = evaluate_v3("KhQh", "Kc7d2s", "flop")
        assert score == 62
        assert "TPGK" in label

    def test_example_2_tpgk_plus_fd(self):
        """例2: KhQc on Kc8c4c → TPGK+FD → 62 + 36 = 98"""
        score, label = evaluate_v3("KhQc", "Kc8c4c", "flop")
        assert 90 <= score <= 100
        assert "TPGK" in label

    def test_example_3_fd_on_monotone(self):
        """例3: As5h on Ts9s4s → ハイカード + 補正 FD + ブロッカー → ~48"""
        score, label = evaluate_v3("As5h", "Ts9s4s", "flop")
        assert 40 <= score <= 55
        # ナッツブロッカー A♠ がある
        assert "ブロッカー" in label

    def test_example_4_solo_oesd(self):
        """例4: 9s8s on 7h6c2d → 役なし + OESD → 8 + 32 = 40"""
        score, _ = evaluate_v3("9s8s", "7h6c2d", "flop")
        assert score == 40

    def test_example_5_combo_draw(self):
        """例5: JsTs on 9s8c2h → BDFD+OESD コンボドロー
        役なし(8) + BDFD+OESD (11 outs × 4 = 44) = 52
        """
        score, _ = evaluate_v3("JsTs", "9s8c2h", "flop")
        assert 50 <= score <= 65

    def test_example_6_tpgk_fd_turn(self):
        """例6: KcQc on Ks7c2c+5d → TPGK + FD ターン → 62 + 18 = 80"""
        score, label = evaluate_v3("KcQc", "Ks7c2c,5d", "turn")
        assert 75 <= score <= 85
        assert "TPGK" in label

    def test_example_7_two_pair_river(self):
        """例7: KcQc on Ks7c2c+5d+Qh → 2ペア (Kings & Queens)"""
        score, label = evaluate_v3("KcQc", "Ks7c2c,5d,Qh", "river")
        assert 70 <= score <= 80
        assert "2ペア" in label

    def test_example_8_tpgk_river_draw_missed(self):
        """例8: KcQc on Ks7c2c+5d+9h → TPGK ドロー失敗 → 62"""
        score, _ = evaluate_v3("KcQc", "Ks7c2c,5d,9h", "river")
        assert score == 62


# ============================================================
# 役スコア表 (SPEC §2)
# ============================================================
class TestRoleScores:
    def test_tptk(self):
        """TPTK on K72r"""
        score, label = evaluate_v3("AhKh", "Ks7d2c", "flop")
        assert score == NEW_ROLE_SCORE["tptk"]
        assert "TPTK" in label

    def test_overpair_high(self):
        """AA on K72r → アンダーペアではなくオーバーペアとして KK 以下を想定"""
        # AA は K より上 → オーバーペア(高)
        score, _ = evaluate_v3("AhAd", "Ks7d2c", "flop")
        assert score == NEW_ROLE_SCORE["overpair_high"]

    def test_set_top(self):
        """KK on K72r → トップセット"""
        score, label = evaluate_v3("KhKd", "Kc7d2s", "flop")
        assert score == NEW_ROLE_SCORE["top_set"]
        assert "セット" in label

    def test_bottom_pair(self):
        """22 on K72r → セット(ボトム), kicker 不問"""
        score, _ = evaluate_v3("2h2d", "Kc7d2s", "flop")
        # 22 がボードと刺さって 3 of a kind = bottom set
        assert score == NEW_ROLE_SCORE["bottom_set"]

    def test_air(self):
        """完全空振り"""
        score, _ = evaluate_v3("3h2d", "Kc8d5h", "flop")
        # 3 はボトムペアでなく Jハイ以下 → air
        assert score <= NEW_ROLE_SCORE["jhigh"]


# ============================================================
# bucket_v3 (新閾値)
# ============================================================
class TestBucket:
    def test_h3_threshold(self):
        assert bucket_v3(65) == "H3"
        assert bucket_v3(80) == "H3"
        assert bucket_v3(100) == "H3"

    def test_h2_threshold(self):
        assert bucket_v3(35) == "H2"
        assert bucket_v3(50) == "H2"
        assert bucket_v3(64) == "H2"

    def test_h1_threshold(self):
        assert bucket_v3(0) == "H1"
        assert bucket_v3(34) == "H1"


# ============================================================
# back_score_v3 / predict_v3
# ============================================================
class TestBackScore:
    def test_dry_50bet_hu(self):
        """TPGK (62) + dry (12) - 50% (17) = 57 → RAISE"""
        ds = back_score_v3(62, 12, 17, 0)
        assert ds == 57
        assert predict_v3(ds) == "RAISE"

    def test_ahigh_75bet_fold(self):
        """Ahigh (25) + dry (12) - 75% (22) = 15 → FOLD"""
        ds = back_score_v3(25, 12, 22, 0)
        assert ds == 15
        assert predict_v3(ds) == "FOLD"

    def test_4way_aa_call(self):
        """AA (75) + wet (6) - 75% (22) - 4way (22) = 37 → CALL"""
        ds = back_score_v3(75, 6, 22, 22)
        assert ds == 37
        assert predict_v3(ds) == "CALL"


# ============================================================
# predict_v3 閾値
# ============================================================
class TestPredict:
    def test_raise_threshold(self):
        assert predict_v3(40) == "RAISE"
        assert predict_v3(100) == "RAISE"

    def test_call_range(self):
        assert predict_v3(20) == "CALL"
        assert predict_v3(39) == "CALL"

    def test_fold_below_20(self):
        assert predict_v3(19) == "FOLD"
        assert predict_v3(0) == "FOLD"
        assert predict_v3(-10) == "FOLD"


# ============================================================
# draw_bonus (SPEC §3)
# ============================================================
class TestDrawBonus:
    def test_flop_fd(self):
        """フロップ FD: 9 outs × 4 = 36"""
        assert draw_bonus(9, "flop") == 36

    def test_flop_oesd(self):
        """フロップ OESD: 8 outs × 4 = 32"""
        assert draw_bonus(8, "flop") == 32

    def test_flop_gs(self):
        """フロップ GS: 4 outs × 4 = 16"""
        assert draw_bonus(4, "flop") == 16

    def test_flop_combo_cap(self):
        """フロップ outs × 4 は 60 で上限クランプ (FD+OESD 13 outs = 52 を許容)"""
        assert draw_bonus(13, "flop") == 52  # FD+OESD 重複控除後
        assert draw_bonus(15, "flop") == 60  # キャップ到達
        assert draw_bonus(20, "flop") == 60  # キャップ維持

    def test_turn_fd(self):
        """ターン FD: 9 × 2 = 18"""
        assert draw_bonus(9, "turn") == 18

    def test_turn_cap(self):
        """ターン上限 30"""
        assert draw_bonus(20, "turn") == 30

    def test_river_zero(self):
        """リバーは常に 0"""
        assert draw_bonus(9, "river") == 0
        assert draw_bonus(20, "river") == 0

    def test_bdfd_fixed(self):
        """BDFD は固定 +5"""
        assert draw_bonus(0, "flop", "BDFD") == 5

    def test_bdsd_fixed(self):
        """BDSD は固定 +2"""
        assert draw_bonus(0, "flop", "BDSD") == 2

    def test_double_backdoor(self):
        """ダブルバックドアは +6"""
        assert draw_bonus(0, "flop", "BDFD+BDSD") == 6


# ============================================================
# blocker_bonus (SPEC §4)
# ============================================================
class TestBlockerBonus:
    def test_nut(self):
        assert blocker_bonus("nut") == 5

    def test_set(self):
        assert blocker_bonus("set") == 3

    def test_straight(self):
        assert blocker_bonus("straight") == 3

    def test_value(self):
        assert blocker_bonus("value") == 2

    def test_unknown(self):
        assert blocker_bonus("unknown") == 0


# ============================================================
# parse_board (新形式)
# ============================================================
class TestParseBoard:
    def test_continuous(self):
        cards = parse_board("Kc7d2s")
        assert len(cards) == 3

    def test_comma_separated(self):
        cards = parse_board("Kc,7d,2s")
        assert len(cards) == 3

    def test_mixed_turn(self):
        """フロップ連続 + ターンカードのカンマ"""
        cards = parse_board("Ks7c2c,5d")
        assert len(cards) == 4

    def test_mixed_river(self):
        cards = parse_board("Ks7c2c,5d,Qh")
        assert len(cards) == 5


# ============================================================
# クランプ
# ============================================================
class TestClamping:
    def test_score_capped_at_100(self):
        """役+ドロー+ブロッカーが 100 を超えても 100 で止める"""
        # KhQc on Kc8c4c は TPGK(62) + FD(36) = 98 で 100 未満
        # 強制的に超えるケース: TPTK + FD on 4c-board → 70+36+? = 100+
        score, _ = evaluate_v3("AcKc", "Kc8c4c", "flop")
        # TPTK + FD = 70 + 36 = 106 → 100 にクランプ
        assert score <= 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
