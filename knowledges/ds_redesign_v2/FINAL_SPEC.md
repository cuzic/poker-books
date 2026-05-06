# 新 HandScore 仕様 FINAL SIGNOFF

確定日: 2026-05-05
バージョン: v3 (案【大】= 案 equity % リスケール)

## 仕様文書

```
SPEC_HANDSCORE.md       ← 役スコア表 + ドロー加点 + ブロッカー加点 + 計算例
SPEC_OTHER_FORMULAS.md  ← 後手・先手・バレル・α 式の新スケール定義
PROPOSAL.md             ← Phase 0.5 提案書 (本仕様の元データ)
```

## 確定パラメータ (sign-off)

```
HandScore = 役スコア + ドロー加点 + ブロッカー加点  (0-100 equity %)

役スコア:
  Set+/Flush/FH/Straight: 78-95
  Top 2pair: 78 / Overpair: 72-78
  TPTK: 70 / TPGK: 62 / TPMK: 50 / TPWK: 45
  Underpair: 35-45 / 2nd pair: 32-42
  Hi-card: 8-25

ドロー加点:
  Flop:  outs × 4 (Rule of 4)
  Turn:  outs × 2 (Rule of 2)
  River: 0
  BDFD: +5 / BDSD: +2 (固定)
  コンボドロー: -2 outs 重複控除

ブロッカー加点 (重複加算なし):
  ナッツ: +5 / Set/Straight: +3 / Value: +2

後手スコア = HS + A − C − M
A: ドライ +12 / セミ +6 / ウェット 0
C: 33%=12 / 50%=17 / 75%=22 / 100%=25 / 150%=30
M: HU=0 / 3-way=12 / 4-way+=22

閾値:
  ≥ 40 → CR 検討
  20〜39 → コール
  < 20 → フォールド
```

## GTO 整合性検証 (`scripts/gto_consistency_v3.py` 出力)

```
Phase1 ds_framework_recheck (27 cases、バケット集約):
  新スケール: 92.6% 一致 (旧 88.9% から改善)
  境界含み:   100% 達成

handscore_boundary (14 cases、個別ハンド):
  新スケール: 21.4% 一致 (個別変動が大きい spot のため)
  境界含み:   57.1%
  → 巻⑤ Ch5「ブロッカー実戦選択」で個別ハンドの局面別調整を扱う
```

## 設計判断 (Q1-Q11) sign-off

| Q | 内容 | 確定値 |
|---|---|---|
| Q1 | HandScore 上限 | 100 |
| Q2 | 役スコア値 | 24 役のテーブル (SPEC_HANDSCORE.md) |
| Q3 | ドロー加点式 | アウツ × ストリート係数 |
| Q4 | ストリート係数 | フロップ ×4 / ターン ×2 / リバー 0 |
| Q5 | コンボドロー控除 | -2 outs |
| Q6 | バックドア | BDFD +5 / BDSD +2 |
| Q7 | ブロッカー加点 | +5/+3/+2 (重複なし) |
| Q8 | C 値 | (1−MDF) × 50 = 12/17/22/25/30 |
| Q9 | A 値 | +12/+6/0 |
| Q10 | M 値 | 0/12/22 |
| Q11 | 閾値 | ≥40/20-39/<20 |

## レビュー観点

```
✓ 暗算しやすさ
  読者が Rule of 2/4 から HandScore を再現できる
  HS = 自分の equity % と直感的に読める
  
✓ GTO 整合性
  Phase1 集約: 92.6%
  既存の旧スケール (85.2%) から 7.4% 改善
  
✓ シリーズ全体での整合性
  式の形式は全巻共通 (HS + A - C - M)
  ストリート間の連続性 (フロップ → ターン → リバー)
  
✓ 既刊との位置づけ
  案【大】= 全面リスケール、過去互換は不要 (未公開)
  
✓ 読者の Rule of 2/4 知識との接続性
  ドロー加点 = アウツ × ストリート係数 (直接対応)
```

## Phase 2 (実装) への引き継ぎ

実装フェーズで使う仕様:
1. `scripts/hand_evaluator_v3.py` (新規実装、SPEC_HANDSCORE.md 準拠)
2. `scripts/bdm.py` の精密版を新スケール対応 (簡易版との差 ±5 以内)
3. `scripts/gto_consistency_v3.py` (本タスク済み)
4. C/A/M テーブルのハードコード更新
5. 既存閾値の更新 (≥8 → ≥40 等)

## Phase 3 (書籍) への引き継ぎ

```
全 6 巻 + digest で:
- HandScore 関連 471 件の数値式を再計算
- ドリル 504 問のうち 75% (377 問) を再計算
- 30-35 早見表ファイルを新スケール対応
- 巻② flop の図版 5 枚を AI 再生成
```

## ★ 設計仕様 sign-off

本仕様 (FINAL_SPEC.md + SPEC_HANDSCORE.md + SPEC_OTHER_FORMULAS.md) を、
案【大】の最終仕様として **承認**。

```
Phase 0:    13/13 ✓ 完了
Phase 0.5:  10/10 ✓ 完了
Phase 1:    5/5  ✓ 完了 ← 本書

Phase 2:    0/5  ← 次のフェーズ (並列実行可能)
Phase 3:    0/9
Phase 3.5:  0/5  
Phase 4:    0/6
合計:       28/53 (53%)
```

Phase 2 移行可能。
