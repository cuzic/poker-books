#!/usr/bin/env python3
"""pytest tests for bdm_v6 (BDM v6 = 巻③ 精密 HandScore、新スケール 0-100).

実行: pytest scripts/test_bdm_v6.py -v
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest

from bdm_v6 import (
    A_VALUES,
    C_VALUES,
    M_VALUES,
    bdm_v6,
    defender_action,
    defender_score,
    handscore_coarse,
    handscore_precise,
)


# ---------------------------------------------------------------------------
# 役スコア基本テスト (簡易版 = SPEC §2 のテーブル値)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "combo,board,expected_score,label_pattern",
    [
        # トップペア系
        ("AhKs", "Kc7d2c", 70, "TPTK"),
        ("KsQh", "Kc7d2c", 62, "TPGK"),
        ("KsTh", "Kc7d2c", 50, "TPMK"),
        ("Ks5h", "Kc7d2c", 45, "TPWK"),
        # オーバーペア
        ("JsJh", "8c7d2c", 72, "オーバーペア(中)"),
        ("9s9h", "8c7d2c", 68, "オーバーペア(低)"),
        # アンダーペア
        ("JsJh", "Kc7d2c", 40, "アンダーペア(中)"),
        ("8s8h", "Kc7d2c", 35, "アンダーペア(低)"),
        # セット / Mid set
        ("KhKd", "Kc7d2c", 92, "Top set"),
        ("7h7d", "Kc7d2c", 88, "Mid set"),
        ("2h2d", "Kc7d2c", 85, "Bottom set"),
        # セカンドペア
        ("AhQc", "KcQd7c", 42 + 2, "セカンドペア"),  # 強キッカー A → +2 in precise
        # ボトムペア
        ("Ah2c", "Kc7d2s", 32 + 2, "ボトムペア"),  # A kicker → +2
        # ハイカード
        ("AsQh", "Ks7d2c", 25, "Aハイ"),
        ("KsJh", "9c7d2c", 20, "Kハイ"),
        ("QsJh", "9c7d2c", 15, "Qハイ"),
    ],
)
def test_role_score_precise(combo, board, expected_score, label_pattern):
    """精密版で role_score 周辺の値が期待値に近いか。"""
    r = handscore_precise(combo, board, "flop")
    # 役スコア + ブロッカーで多少のズレあり、±5 以内を許容
    assert abs(r.score - expected_score) <= 5, (
        f"{combo} on {board}: got {r.score} ({r.label}), expected {expected_score}"
    )


@pytest.mark.parametrize(
    "combo,board,expected_score,label_pattern",
    [
        ("AhKs", "Kc7d2c", 70, "TPTK"),
        ("KsQh", "Kc7d2c", 62, "TPGK"),
        ("AsQh", "Ks7d2c", 25, "Aハイ"),
        ("KhKd", "Kc7d2c", 92, "Top set"),
    ],
)
def test_role_score_coarse(combo, board, expected_score, label_pattern):
    """簡易版で SPEC のテーブル値が出るか (ブロッカー +2 程度の誤差は許容)。"""
    r = handscore_coarse(combo, board, "flop")
    assert abs(r.score - expected_score) <= 5


# ---------------------------------------------------------------------------
# ドロー加点テスト (SPEC §3)
# ---------------------------------------------------------------------------
class TestDrawBonus:
    def test_flop_fd(self):
        """フロップ FD: 9 outs × 4 = 36 加点。"""
        # AhJh on Ks 7h 2h: 4 spades=2, hearts=3 → BDFD(ハートが 3枚)
        # 真の FD は 4 同スートが必要
        r = handscore_precise("AhJh", "Th7h2c", "flop")
        # AhJh + Th7h = 4 ハート → FD
        assert r.draw_bonus >= 30, f"FD bonus too low: {r.draw_bonus}"

    def test_flop_oesd(self):
        """フロップ OESD: 8 outs × 4 = 32 加点 (役なし)。"""
        # 9s8s on 7h6c2d: OESD T/5
        r = handscore_precise("9s8s", "7h6c2d", "flop")
        assert r.draw_bonus >= 28, f"OESD bonus too low: {r.draw_bonus}"

    def test_turn_fd_half(self):
        """ターン FD: 9 outs × 2 = 18 加点 (フロップの半分)。"""
        # AhJh on Th7h2c5c (turn): FD (4 ハート on flop, ターン 5c で継続)
        r_flop = handscore_precise("AhJh", "Th7h2c", "flop")
        r_turn = handscore_precise("AhJh", "Th7h2c5c", "turn")
        # ターンはフロップの約半分
        assert r_turn.draw_bonus < r_flop.draw_bonus, \
            "turn draw bonus should be smaller than flop"

    def test_river_zero(self):
        """リバー: ドロー加点 = 0。"""
        r = handscore_precise("AhJh", "Th7h2c5c8d", "river")
        assert r.draw_bonus == 0, f"river draw bonus should be 0, got {r.draw_bonus}"

    def test_combo_draw(self):
        """FD + OESD コンボ: 13 effective outs × 4 = 52 (重複 -2)。"""
        # 真のコンボドロー: JsTs on 9s8s2c など (両方スペードで 4 枚スペードかつ OESD)
        r = handscore_precise("JsTs", "9s8s2c", "flop")
        # コンボなのでかなり高い
        assert r.draw_bonus >= 40, f"combo draw too low: {r.draw_bonus}"


# ---------------------------------------------------------------------------
# ブロッカー加点テスト (SPEC §4)
# ---------------------------------------------------------------------------
class TestBlocker:
    def test_value_blocker_q(self):
        """Q ブロッカー: K-high 板で +2 (kicker 役以外で保有時)。"""
        # AhQs on Kc7d2c (Q は kicker でなく単独保有、TPx ではない場合)
        # KsQh で Q が kicker → blocker 加点なし
        r1 = handscore_precise("KsQh", "Kc7d2c", "flop")
        # AhQs では Q は kicker でない (A の方が kicker)、Q がブロッカー候補
        r2 = handscore_precise("AhQs", "Kc7d2c", "flop")
        # Q を kicker として使う KsQh より AhQs の方が Q ブロッカーがあって良い
        # ただし役は AhQs = Aハイ なので score は KsQh より低くなる
        assert r1.role_score > r2.role_score

    def test_blocker_max_only(self):
        """ブロッカーは最大値のみ (重複加算なし)。"""
        # 複数候補があっても 5 を超えない
        r = handscore_precise("AsKs", "Qs2s2h", "flop")
        # A♠ = ナッツ FD ブロッカー (+5)、K もある (+3 候補だが除外)
        assert r.blocker_bonus <= 5


# ---------------------------------------------------------------------------
# 簡易版 vs 精密版の整合性 (±5 以内)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "combo,board",
    [
        ("AhKs", "Kc7d2c"),
        ("KsQh", "Kc7d2c"),
        ("KsJh", "Kc7d2c"),
        ("KsTh", "Kc7d2c"),
        ("Ks5h", "Kc7d2c"),
        ("AhAs", "Kc7d2c"),
        ("JsJh", "Kc7d2c"),
        ("KhKd", "Kc7d2c"),
        ("7h7d", "Kc7d2c"),
        ("AhQc", "KcQd7c"),
        ("AhKc", "Kh8c2c"),
        ("AsKs", "Ks8c2c"),
        ("9s8s", "7h6c2d"),
        ("JsTs", "9s8c2h"),
        ("AsQh", "Ks7d2c"),
        ("9h9d", "Kh7c2d"),
        ("8h7h", "Kc8d2c"),
        ("Ad5d", "TsTd4d"),
        ("AsKs", "Qs2s2h"),
        ("JsTs", "9s8s2c"),
    ],
)
def test_consistency_coarse_vs_precise(combo, board):
    """主要 20 ハンドで簡易版と精密版の差が ±5 以内に収まるか。"""
    coarse = handscore_coarse(combo, board, "flop")
    precise = handscore_precise(combo, board, "flop")
    diff = abs(coarse.score - precise.score)
    assert diff <= 5, (
        f"{combo} on {board}: coarse={coarse.score}, precise={precise.score}, diff={diff}"
    )


# ---------------------------------------------------------------------------
# 後手スコア式 (SPEC_OTHER_FORMULAS.md §1)
# ---------------------------------------------------------------------------
class TestDefenderScore:
    def test_a_values(self):
        assert A_VALUES["dry"] == 12
        assert A_VALUES["semiwet"] == 6
        assert A_VALUES["wet"] == 0

    def test_c_values(self):
        assert C_VALUES[33] == 12
        assert C_VALUES[50] == 17
        assert C_VALUES[75] == 22
        assert C_VALUES[100] == 25
        assert C_VALUES[150] == 30

    def test_m_values(self):
        assert M_VALUES[2] == 0
        assert M_VALUES[3] == 12
        assert M_VALUES[4] == 22

    def test_tpgk_dry_50_hu(self):
        """TPGK on K72r dry vs 50% bet (HU) → 62 + 12 - 17 = 57 → CR。"""
        # SPEC §1.5 の例
        ds = defender_score(62, "dry", 50, 2)
        assert ds == 57
        assert defender_action(ds) == "CR"

    def test_tpmk_dry_75_hu(self):
        """TPMK on K72r dry vs 75% bet → 50 + 12 - 22 = 40 → 境界 CR。"""
        ds = defender_score(50, "dry", 75, 2)
        assert ds == 40
        assert defender_action(ds) == "CR"

    def test_aa_4way_wet(self):
        """AA on K-T-6 wet 4-way vs 75% → 75 + 0 - 22 - 22 = 31 → コール。"""
        ds = defender_score(75, "wet", 75, 4)
        assert ds == 31
        assert defender_action(ds) == "Call"

    def test_threshold_boundaries(self):
        assert defender_action(40) == "CR"
        assert defender_action(39) == "Call"
        assert defender_action(20) == "Call"
        assert defender_action(19) == "Fold"


# ---------------------------------------------------------------------------
# スケール検証 (新スケール 0-100 に収まる)
# ---------------------------------------------------------------------------
class TestScale:
    def test_score_clamped_0_100(self):
        """全ハンドが 0-100 に収まる。"""
        cases = [
            ("AhKs", "Kc7d2c", "flop"),
            ("AsKs", "Qs2s2h", "flop"),
            ("KhKd", "Kc7d2c", "flop"),
            ("JsTs", "9s8s2c", "flop"),
        ]
        for combo, board, street in cases:
            r = handscore_precise(combo, board, street)
            assert 0 <= r.score <= 100, f"{combo} on {board}: {r.score}"

    def test_quads_high(self):
        """クワッズは 95。"""
        # AKs on AAA: 4 of a kind ではない、これは Trips (board)
        # KK on KKK: クワッズ (board が KK でも hole が KK ならクワッズ)
        r = handscore_precise("KhKd", "KsKc7d", "flop")
        assert r.role_score >= 92  # クワッズ or full house

    def test_strongest_hand_capped(self):
        """ストレートフラッシュ + ナッツブロッカーで上限 100 でクランプ。"""
        r = handscore_precise("AhKh", "QhJhTh", "flop")
        # ロイヤルフラッシュ
        assert r.score <= 100


# ---------------------------------------------------------------------------
# bdm_v6 ショートカット
# ---------------------------------------------------------------------------
def test_bdm_v6_shortcut():
    """bdm_v6() は handscore_precise().score と同値。"""
    assert bdm_v6("AhKs", "Kc7d2c", "flop") == handscore_precise(
        "AhKs", "Kc7d2c", "flop"
    ).score


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
