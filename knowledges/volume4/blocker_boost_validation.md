# ナッツブロッカー補正の TexasSolver 検証結果

**検証日**: 2026-05-05
**ソルバー**: TexasSolver (CFR+, accuracy=0.5%, 200 iter)
**シナリオ数**: 5 (tc_006, tc_010 を含む)

---

## 1. 検証シナリオと結果

### S1: J♥8♥5♣ → 4♥（tc_006、suited+flush, barrel=5）

| ハンド | 説明 | 実 GTO CBet |
|---|---|---|
| AhKd | Ah NFD (4-flush に Ah blocker) | 76.3% |
| AhKc | Ah NFD | 77.7% |
| AhKs | Ah NFD | 76.4% |
| AdKh | Kh sub-NFD（K-flush 候補） | 86.0% |
| AcKh | Kh sub-NFD | 85.8% |
| AsKh | Kh sub-NFD | 86.1% |

**全体 CBet: 75.3%** (barrel=5 予測「依存」より +5pp 上振れ)

### S2: K♣Q♣7♦ → J♣（suited+flush, barrel=5）

| ハンド | 説明 | 実 GTO CBet |
|---|---|---|
| AcKs | Ac NFD blocker | 81.1% |
| AdKh | AKo no club | 69.5% |
| Ts9s | air, gutshot | 100.0% |

**全体 CBet: 69.9%** (barrel=5 予測「依存」と概ね整合)

### S3: T♣9♦8♥ → 7♠（connected+connector, barrel=3）

| ハンド | 説明 | 実 GTO CBet |
|---|---|---|
| AhKh | air, gutshot to J | 46.4% |
| AsJh | J straight blocker + 完成 | 100.0% |
| KsQc | KQ blocker + gutshot | 71.0% |
| Js6s | J straight blocker | 67.9% |

**全体 CBet: 68.4%** (barrel=3 予測「依存」と整合)

### S4: K♥9♥4♣ → A♥（suited+OC, barrel=7）

| ハンド | 説明 | 実 GTO CBet |
|---|---|---|
| Qs6s | air | 68.7% |
| 8d7d | air | 94.7% |

**全体 CBet: 80.2%** (barrel=7 予測「全レンジ」と整合 ✓)

注: A♥ ターンは OC かつ flush card。spec 優先順位（OC > flush）で coeff=3。

### S5: 8♦7♦6♣ → A♥（tc_010、suited+OC, barrel=7）

A3 (TP) 各 suit combo: 69-83% CBet（spec 予測「全レンジCBet」と整合 ✓）
全体 CBet: 66.7%（barrel=7 予測より -3pp 下振れ）

---

## 2. 主要発見

### 2.1 提案修正: 「H2 → H3 promotion」が正しい補正の方向

当初提案した「ナッツブロッカー補正 (Ah=+3, K straight blocker=+2)」は **方向性は正しいが対象が狭すぎる**。

実際の GTO データから、以下の補正が必要と判明:

```
NFD (FD + Ace blocker):
  HandScore +3 追加（既に spec 既定: NutsFD = +16 vs FD = +13）
  → DESIGN.md line 138 で「未実装」と明記、本提案は実装の促進

Sub-NFD (FD + K blocker on flush board):
  HandScore +2 追加 (新提案)
  実 GTO で 86% CBet（NFD と同等以上）

ストレート blocker + gutshot:
  HandScore +2 追加 (新提案)
  例: T98r+7 で KQ blocker + gutshot → 71% CBet
```

### 2.2 補正値の根拠

実 GTO CBet と現 formula 予測の乖離:

| ハンド | 現 HS | 現 bucket | 実 CBet | 期待 bucket |
|---|---|---|---|---|
| AhKd on J85hh+4h | 13 | H2 | 76% | H3 |
| AcKs on KQ7c+Jc | 13 | H2 | 81% | H3 |
| KsQc on T98+7 | ~10 | H2 | 71% | H3 |

これらすべてに「+3」または「+2」の追加補正で実効 HS を 14-16 に押し上げ、H3 扱い→ CBet 候補にする。

### 2.3 実装の難易度

- `calc_hand_score()` に NutsFD 検出ロジック（spade/heart/diamond/club の Ace 保有チェック）を追加: **小**
- Sub-NFD と straight blocker の検出ロジック: **中**（ボードテクスチャ判定が必要）
- 既存テスト 314 件への影響: **要検証**

### 2.4 教育的価値

巻④ 第7章 7-5-a 節として「ブロッカー込みの実効 HandScore」を 100 文字程度で説明可能:

> ターン以降のフラッシュ完成ボードでは、ナッツフラッシュブロッカー（A♠/♥/♦/♣）保有時に
> HandScore +3 を加算します。AKo on 4-flush turn の AhKd は形式上 H2 (HS=13) ですが、
> ブロッカー込みで実効 HS=16 → H3 として CBet 候補に格上げ。サブナッツフラッシュ
> ブロッカー (Kh on heart-flush turn) も同様に +2 加算します。

---

## 3. 結論と次のアクション

**結論**: 提案は有効。ただし対象を「ナッツ」に限定せず「強いブロッカー全般」に拡張が必要。

**次のアクション** (実装する場合):

1. `calc_hand_score()` に NFD detection を追加（DESIGN.md の未実装 spec 機能）
2. Sub-NFD / ストレート blocker detection を追加
3. 巻④ 第7章に 7-5-a 節を加筆
4. 既存 314 テストへの影響確認 + tc_006 等の card 再生成
5. CHANGELOG または変更履歴に記録

**実装しない選択肢** (現状維持):

- 現 formula は教育的に簡素で十分機能している
- ±10% の境界誤差は既知（barrel_score_verify_table.md で 87.5% セル一致）
- 細かいブロッカー補正は実戦経験で習得すべき暗黙知として残す
- 本ドキュメントは将来的な v2 設計時の参考資料として保管

優先度: **中**（巻4 v2 改訂時に検討）

---

## 4. 実装完了履歴 (2026-05-05 追記)

**全 5 項目実装完了**。本提案は spec 拡張として正式採用された:

| # | アクション | コミット | 状態 |
|---|----------|---------|------|
| 1 | `calc_hand_score()` に NFD detection (+3) | `15287ec` (poker-drill) | ✓ |
| 2a | Sub-NFD detection (+2) | `4c927a6` (poker-drill) | ✓ |
| 2b | ナッツストレート blocker detection (+2) | `3834a21` (poker-drill) | ✓ |
| 3 | 巻④ 第7章 7-5-a 節を加筆 | `d2cad33` (poker-books) | ✓ |
| 4 | 314 テスト影響確認 + 再生成 | `15287ec` 等 | ✓ 全テスト合格 |
| 5 | CHANGELOG 記録 | `148fabe` (poker-drill) | ✓ |

**関連改訂**:
- 巻⑤ 第5章への参照追加: `4f55daa`
- digest 第14章への参照追加: `fccf8f2`
- 巻間整合性メモ: `knowledges/spec_extension_volume_alignment.md` (commit `f1e6407`)

**実装後の挙動 (確認済み)**:
- AhKd on J♥8♥5♣ → 4♥: HS 13 → **16** (NFD 適用、H3 promotion)
- KhQc on J♥8♥5♣ → 4♥: HS 13 → **15** (Sub-NFD 適用、H3 promotion)
- K♥2♦ on J♣T♦9♠8♥: gutshot 6 → **8** (ナッツストレート blocker 適用)

これで spec → 書籍 → 実装 → CHANGELOG の参照チェーンが完成。本ドキュメントは
歴史的記録として保管。
