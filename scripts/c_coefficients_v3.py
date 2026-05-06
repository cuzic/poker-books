#!/usr/bin/env python3
"""
新スケール (0-100 equity %) における C / A / M 係数および閾値の単純定義モジュール。

定義元: knowledges/ds_redesign_v2/SPEC_OTHER_FORMULAS.md (確定日: 2026-05-05)

他の v3 検証スクリプト (ds_framework_recheck_v3.py 等) はここから import する。

旧スケール → 新スケール対応:
  C: {33:3, 50:5, 75:7, 100:9, 150:11} → {33:12, 50:17, 75:22, 100:25, 150:30}
  A: {dry:3, semi:2, wet:1}              → {dry:12, semi:6, wet:0}
  M: なし                                  → {HU:0, 3-way:12, 4-way+:22}
  閾値 (DS): >=8 CR / >=0 call / <0 fold → >=40 CR / >=20 call / <20 fold
  バケツ (HS): H3>=14, H2>=7, H1<7         → H3>=65, H2>=35, H1<35

旧式は HS + A - 3 - C (ベースライン補正 -3) だったが、
新式では -3 を A 値に吸収しているため、後手スコア = HS + A - C - M。
"""
from __future__ import annotations

# ─── 後手スコア係数 ──────────────────────────────────

# C: ベット圧力（ベットサイズ別）
C_TABLE = {
    33:  12,
    50:  17,
    75:  22,
    100: 25,
    150: 30,
}

# A: ボード補正
A_TABLE = {
    "dry":  12,
    "semi":  6,
    "wet":   0,
}

# M: マルチウェイ補正
M_TABLE = {
    "HU":      0,
    "3-way":  12,
    "4-way+": 22,
}

# ─── 閾値 ─────────────────────────────────────────────

# 後手スコア (DS) 閾値
DS_TH_RAISE = 40    # >= 40 → CR (チェックレイズ) 検討
DS_TH_CALL  = 20    # >= 20 → コール
# < 20 → フォールド

# 先手スコア閾値
ATTACK_TH_BIG    = 60   # >= 60 → 75-150% pot
ATTACK_TH_MID    = 40   # >= 40 → 50-75% pot
ATTACK_TH_SMALL  = 20   # >= 20 → 33% pot or check
# < 20 → check

# 役スコア (HandScore) バケツ閾値
HS_TH_H3 = 65   # >= 65 → 強 (H3)
HS_TH_H2 = 35   # >= 35 → 中 (H2)
# < 35 → 弱 (H1)

# 旧スケール (比較用)
OLD_C_TABLE  = {33: 3, 50: 5, 75: 7, 100: 9, 150: 11}
OLD_A_TABLE  = {"dry": 3, "semi": 2, "wet": 1}
OLD_DS_TH_RAISE = 8
OLD_DS_TH_CALL  = 0
OLD_HS_TH_H3 = 14
OLD_HS_TH_H2 = 7

# ─── バケツ代表 HS（ds_framework_recheck.py 互換用） ──────

# 新スケール:
#   H3 = 70 (TPTK 標準), H2 = 50 (TPMK / FD など中堅), H1 = 28 (BDFD / 弱)
HS_REP = {
    "H3": 70,
    "H2": 50,
    "H1": 28,
}

# 旧スケール:
OLD_HS_REP = {"H3": 17, "H2": 11, "H1": 4}


# ─── 計算ヘルパー ─────────────────────────────────────

def defender_score(hs: int, A: int, C: int, M: int = 0) -> int:
    """新スケール 後手スコア = HS + A - C - M (ベースライン補正は A に吸収)."""
    return hs + A - C - M


def attacker_score(hs: int, A: int, M: int = 0) -> int:
    """新スケール 先手スコア = HS + A - M (C 値なし)."""
    return hs + A - M


def predict_defender(ds: int) -> str:
    """後手スコア → 予測アクション."""
    if ds >= DS_TH_RAISE:
        return "raise"
    if ds >= DS_TH_CALL:
        return "call"
    return "fold"


def predict_attacker(score: int) -> str:
    """先手スコア → 予測ベットサイズ。"""
    if score >= ATTACK_TH_BIG:
        return "75-150%pot"
    if score >= ATTACK_TH_MID:
        return "50-75%pot"
    if score >= ATTACK_TH_SMALL:
        return "33%pot"
    return "check"


def bucket(hs: int) -> str:
    """HandScore バケツ判定 (新スケール)."""
    if hs >= HS_TH_H3:
        return "H3"
    if hs >= HS_TH_H2:
        return "H2"
    return "H1"


def main() -> None:
    """整合性チェック: 仕様書の例と一致するか確認."""
    print("=" * 60)
    print("c_coefficients_v3.py 自己検証")
    print("=" * 60)

    # 仕様書の例 1: TPGK on K72r dry vs 50% bet (HU)
    #   HS=62, A=12, C=17, M=0 → DS=57 → CR
    hs, A, C, M = 62, A_TABLE["dry"], C_TABLE[50], M_TABLE["HU"]
    ds = defender_score(hs, A, C, M)
    pred = predict_defender(ds)
    expected = ("raise", 57)
    print(f"例1 TPGK on K72r vs 50% (HU):")
    print(f"  HS={hs} A={A} C={C} M={M} → DS={ds} → {pred}")
    print(f"  期待: DS={expected[1]}, action={expected[0]}")
    assert ds == 57, f"DS mismatch: {ds} vs 57"
    assert pred == "raise", f"action mismatch: {pred}"
    print("  → OK")

    # 仕様書の例 2: TPTK on K72r dry HU 先手
    #   HS=70, A=12, M=0 → 攻撃=82 → 75-150%
    hs, A, M = 70, A_TABLE["dry"], M_TABLE["HU"]
    score = attacker_score(hs, A, M)
    pred = predict_attacker(score)
    print(f"\n例2 TPTK on K72r 先手 (HU):")
    print(f"  HS={hs} A={A} M={M} → 攻撃={score} → {pred}")
    assert score == 82, f"先手スコア mismatch: {score} vs 82"
    assert pred == "75-150%pot"
    print("  → OK")

    # バケツ判定
    print(f"\nバケツ判定:")
    for hs in [10, 28, 35, 50, 65, 70, 90]:
        print(f"  HS={hs:3d} → {bucket(hs)}")
    assert bucket(34) == "H1"
    assert bucket(35) == "H2"
    assert bucket(64) == "H2"
    assert bucket(65) == "H3"

    # C 表エントリ
    print(f"\nC 表 (新スケール):")
    for size, c in C_TABLE.items():
        print(f"  {size:>3}% pot → C={c}")

    # 旧 → 新 C 値の比率（参考: 約 4 倍）
    print(f"\n旧 → 新 C 値の比率:")
    for size in OLD_C_TABLE:
        if size in C_TABLE:
            ratio = C_TABLE[size] / OLD_C_TABLE[size]
            print(f"  {size:>3}% : 旧 {OLD_C_TABLE[size]:>2} → 新 {C_TABLE[size]:>2}  (×{ratio:.2f})")

    print("\n全テスト OK")


if __name__ == "__main__":
    main()
