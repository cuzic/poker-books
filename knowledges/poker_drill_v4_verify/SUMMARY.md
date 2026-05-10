# ChatGPT v4 review 論点の TexasSolver 検証 (2026-05-06)

このディレクトリには、ChatGPT v4 review で議論になった poker-drill の戦略判断を
TexasSolver (HU) で検証した結果を保存。

## 既存検証で確認済みの項目

| 論点 | 主張 | 検証元 | 結果 |
|---|---|---|---|
| 3bo_001 AA on K72r OOP CBet→受け | AA→CR46%/CALL54% | knowledges/volume4/results/3bp_verify/scenario_a.json | ✓ 53.7/46.3 で一致 |
| K5o on K72r vs IP 50% CBet | CALL 100% | /tmp/ts_chatgpt_review/K72r_50pct.json | ✓ 確認済 |
| AJ on A95s vs IP 50% CBet | CALL 100% | /tmp/ts_chatgpt_review/A95ss_50pct.json | ✓ 確認済 |
| A2 on T98w vs IP 50% CBet | FOLD 94% | /tmp/ts_chatgpt_review/T98w_50pct.json | ✓ 確認済 |

## 今回追加した検証 (2026-05-06)

### 1. 3bd_001: AA on K72r 3BP IP defense

- 設定: BB 3-bet, BTN call, OOP CBet 33% on K72r
- 結果 (3bd_001.json):
  - **AA → RAISE 100%** (混合戦略ではない)
  - KK → RAISE 100%
  - QQ → RAISE 100%
- 私の以前の note「AA→レイズ60%/コール40%」は **誤り**
- 修正: 「IP範囲は強いので overpair は基本レイズ純。混合は OOP (3-bettor) 側で発生」に変更

### 2. 4b_001 / 4b_004: AA, AK on K72r 4BP IP CBet

- 設定: 4BP SPR≈1.5, BTN open 4-bet, BB call, BTN CBet
- 結果 (4b_001.json, BET75% = 純粋なオールイン):
  - **AA → BET 75% = 98.5%** (auto-commit 確認) ✓
  - **KK → BET 75% = 100%** (auto-commit 確認) ✓
  - **QQ → CHECK 100%** (K-high で QQ はチェック！)
  - **AKs → CHECK 67% / BET 33%** ← TPTK は auto-commit ではない！
- 重要発見: **TPTK in 4BP は CHECK 寄りの混合戦略**
- 修正: flop_cbet_4bp.py で is_overpair 判定を追加。TPTK は「チェック多め (TPTK: 混合戦略)」に変更

## 追加検証 2 (4BP wet/semi)

| ハンド × 板 | TexasSolver 結果 | 私の deck 出力 |
|---|---|---|
| AA on T98w (wet) | BET 100% | オールイン ✓ |
| QQ on J85 (semi) | **CHECK 69% / BET 31%** | チェック多め (混合) ✓ |
| KK on T98w (wet) | CHECK 23% / BET 77% | オールイン (多数派) ✓ |
| AKs on T98w (wet) | CHECK 84% / BET 16% | チェック多め (TPTK) ✓ |
| AKs on K72r (dry) | CHECK 67% / BET 33% | チェック多め (TPTK) ✓ |

これにより、`flop_cbet_4bp.py` の H3 分岐を 4 段階に細分化:
1. `is_AA or is_top_set` → 純戦略 ALL_IN
2. `overpair × wet` → 多数派 ALL_IN
3. `overpair × dry/semi` (KK/QQ) → CHECK 寄り混合
4. `TPTK` (any board) → CHECK 寄り混合

## まだ未検証の懸念

- **multiway (mw_001) IP有利+CR封印**: TexasSolver は HU only のため直接検証不可

## 関連ファイル

- 検証スクリプト: `scripts/texassolver_v4_verify.py`
- generator 修正: `scripts/generate/flop_defense_3bp.py`, `scripts/generate/flop_cbet_4bp.py`
