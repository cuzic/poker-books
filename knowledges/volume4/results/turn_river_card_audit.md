# ターン・リバー裏面 検証レポート (poker-drill カード)

**検証日**: 2026-05-04（初版）／2026-05-04（追記: river-defense 検証 + 全 deck 機械監査）
**対象**: poker-drill の全 deck カード計 342枚
**手法**: 既存 TexasSolver 検証データ (102/, c_coef_verify/, role_score_verify/, action_framework_coefficients.md) との突き合わせ + 書籍ロジック整合性チェック + answer↔formula 機械的整合チェック

## 修正完了サマリ（2026-05-04 追記）

| Deck | 修正内容 | コミット |
|------|---------|---------|
| turn-cbet | suited 優先ルール違反 7枚修正 + impossible 4枚削除 (25→21枚) | 195d6cf |
| river-first | rf_010/016 を Broadway straight に修正 + TPMK 薄バリュー分岐追加 | 85bcb26 |
| river-defense | rd_005 (TPMK CALL) の formula↔answer 不整合を修正、後手スコア narrative 導入 | 62e43e2 |
| テスト | 旧仕様アサーション修正、全 314 テスト合格 | 56b2713 |

## 機械監査の最終結果（2026-05-04）

全 23 deck × 342 cards の answer↔formula 整合チェック → 残存「不整合」24件は全て false positive または design choice:

- **preflop-4bet (20件)**: 「ポーラー4betルール」の決定木 (★QQ以上 / JJ-TT / 99以下) を 3 分岐すべて表示するデザイン。answer は ★ 印の分岐から導かれる（formula 末尾は最終分岐 "99以下→FOLD" の表示）。整合の判定にはミスマッチ検出ロジックでは捕捉不可。design 上の選択。
- **flop-vs-cbet, flop-vs-cbet-3bp-oop (3件)**: answer="チェックレイズ" や "チェックレイズまたはコール" が "チェック" を含むため検出ロジックの false positive。実際は formula と一致。

---

## 結論サマリ

| カテゴリ | 枚数 | 重大エラー | 軽微エラー | 整合性 OK |
|---------|----|----|----|----|
| turn-cbet (tc_*) | 25 | 2 | 5 | 18 |
| turn-defense (td_*) | 15 | 0 | 0 | 15 |
| river-alpha (ra_*) | 17 | 0 | 0 | 17 (大筋整合) |
| river-defense (rd_*) | 12 | 0 | 0 | 12 (大筋整合) |
| river-first (rf_*) | 18 | 5 | 0 | 13 |
| **合計** | **87** | **7** | **5** | **75** |

重大エラー = 推奨アクションが反転する可能性があるもの。
軽微エラー = 推奨アクションは維持されるが説明テキストが誤っているもの。

---

## 重大エラー詳細

### A. turn-cbet: FlopType 誤分類により推奨が反転 (2件)

書籍 `volume4/chapters/08-barrel-score.md:87` の優先順位ルール「**同スート 2 枚以上あれば「スーテッド」を優先**」に違反。

#### tc_006: A♥K♦ on J♥8♥5♣ → 4♥
- **現状**: FlopType=セミウェット(6) + フラッシュ(1) = 7 → 「全レンジCBet」 → AK ベット
- **正しい分類**: J♥+8♥ で 2♥ → スーテッド(4) + フラッシュ(1) = **5** → 「依存（H3のみ）」
- **正しい推奨**: AK は HandScore 13 (H2) なので **チェック** すべき
- **TexasSolver 裏付け**: J84ss + Ts(フラッシュ) で IP CBet頻度 68.0% (102/turn_cbet_102_J84ss_Ts.json) — barrel=5 の「依存」ゾーンと整合。J85ss も同等ゾーン。
- 判定根拠テキスト「① 同スート2枚以上? NO」も事実誤認

#### tc_010: A♦3♥ on 8♦7♦6♣ → A♥
- **現状**: FlopType=コネクテッド(3) + OC(3) = 6 → 「依存（H3のみ）」 → A3(TP, HS=10, H2) は **チェック**
- **正しい分類**: 8♦+7♦ で 2♦ → スーテッド(4) + OC(3) = **7** → 「全レンジCBet」
- **正しい推奨**: A3(TP) は **CBet（バレル）** すべき
- 推奨アクションが完全に反転する境界ケース
- 判定根拠テキストもステップ① (スーテッド判定) を欠落

### B. river-first: formula と answer の不整合 (5件)

formula.steps の最終ステップ判断と answer/conclusion が矛盾。

| ID | ハンド | board | 役 | formula 最終判断 | answer | 備考 |
|----|--------|-------|----|------|------|------|
| rf_010 | K♥Q♦ | A♠K♦T♣2♥J♠ | ストレート(V≥18) | **BET 50%** | チェック | 4ブロードウェイ板でブロッカー戦略の意図不明 |
| rf_013 | A♥J♦ | A♠K♦7♣2♥9♠ | TPMK(B<10) | **CHECK** | ベット 33% | 薄バリュー override か |
| rf_016 | K♥Q♦ | J♠T♦9♣5♥2♠ | ストレート(V≥18) | **BET 50%** | チェック | ナッツ抑え戦略の意図不明 |
| rf_017 | K♥T♦ | K♠Q♦7♣2♥9♠ | TPGK(B<10? ←要確認) | **CHECK** | ベット 33% | TPMK の薄バリュー override |
| rf_018 | A♥9♦ | A♠K♦8♣2♥5♠ | TPMK(B<10) | **CHECK** | ベット 33% | 薄バリュー override |

**問題**: formula 表示が判断ロジックを反映せず、後付けで answer が決まっている。読者は formula の最終ステップを読んで間違った理解をする。

**処理方針**:
- rf_010, rf_016: 答えとロジックを「ナッツ抑えチェック（ブロッカー意図）」に揃えるか、ベット 50% に修正
- rf_013, rf_017, rf_018: 「TPMK薄バリュー → 33%ベット」の分岐を formula に追加

---

## 軽微エラー詳細 (turn-cbet)

FlopType 誤分類だが推奨アクション帯（全レンジCBet/依存）は変わらないもの。説明テキスト修正のみ。

| ID | 板 | 現分類 | 正分類 | barrel 変化 | 推奨 |
|----|----|------|------|----|----|
| tc_011 | 8♦7♦6♣ → 2♠ | コネクテッド+ブランク=5 | スーテッド+ブランク=**6** | 依存→依存 | 同 |
| tc_012 | J♥T♥9♣ → 8♥ | コネクテッド+フラッシュ=4 | スーテッド+フラッシュ=**5** | 依存→依存 | 同 |
| tc_019 | J♥T♥9♣ → T♦ | コネクテッド+ペア=7 | スーテッド+ペア=**8** | 全レンジ→全レンジ | 同 |
| tc_020 | J♥T♥9♣ → 8♦ | コネクテッド+コネクター=3 | スーテッド+コネクター=**4** | 依存→依存 | 同 |
| tc_022 | J♥T♥9♣ → 8♥ | コネクテッド+フラッシュ=4 | スーテッド+フラッシュ=**5** | 依存→依存 | 同 |

---

## 既知の境界ケース（裏面で要警告）

`barrel_score_verify_table.md` の 2 不一致セルが裏面カードに含まれる:

| ID | 板 | 分類 | barrel | 裏面推奨 | GTO 実測 | リスク |
|----|----|------|----|----|----|----|
| tc_005 | J85r → A | semi×OC | 9 | 全レンジCBet | 70.0% | 境界（TPTKは問題なし） |
| tc_017 | J83r → 2 | semi×blank | 8 | 全レンジCBet | 67.0% | 境界（TPTK問題なし） |
| **tc_021** | J83r → 2 | semi×blank | 8 | **全レンジCBet** | 67.0% | **K9airがCBet推奨は危険** |

tc_021 は K♥9♦ (HandScore 0, 弱H1) で「全レンジCBet」を推奨しているが、実際の GTO では 67% のみがベット。K-high air は残り 33% のチェック側に入る可能性が高い。

---

## 検証で確認できたこと

### ✓ DS フレームワーク (turn-defense 全 15 枚)

`action_framework_coefficients.md` の C 修正後 DS 式 = H + A − 3 − C を全 15 枚で照合:

| バケツ | DS 範囲 | 推奨 | 実カード推奨 | 一致 |
|--------|---------|------|------------|------|
| H3 (≥15) | DS ≥ 8 | チェックレイズ | CR | ✓ |
| H2 (8-14) | DS 0-7 | コール | コール | ✓ |
| H1 (<8) | DS < 0 | フォールド | フォールド | ✓ |

td_001〜td_015 全件で「H+A−3−C 計算 → 推奨」が一致。15/15 ✓

### ✓ バレルスコア係数

102/ 198 シナリオ検証で 16 セル中 14 一致 (87.5%)。barrel ≥7 で「積極」、<7 で「依存」の閾値はシリーズ全巻で確定。

### ✓ HandScore 役スコア

`role_score_verify/` で K72r 8ケース中 7 一致 (87.5%)。tpmk=8, tpgk=15, tptk=18 等は GTO 整合。

### ✓ 土台フレームワーク

α式 (1-α) と V:B 比、ICM・ドロー加点・C 係数（C=3/4/6）は全て検証済み。

---

## 修正提案

### 必須修正 (推奨アクション反転)

1. **tc_006** の `flopType` を「スーテッド」、`flopTypeCoeff` を 4、`barrelScore` を 5 に修正。`isAllRange` を `false`、`answer` を「チェック」、formula と conclusion も追従。
2. **tc_010** の `flopType` を「スーテッド」、`flopTypeCoeff` を 4、`barrelScore` を 7 に修正。`isAllRange` を `true`、`answer` を「CBet（バレル）」に修正。
3. **rf_010, rf_013, rf_016, rf_017, rf_018**: formula 最終ステップと answer の整合を取る。特に rf_010/rf_016 は方針決定（チェック or ベット）が必要。

### 推奨修正 (説明文整合)

4. **tc_011, tc_012, tc_019, tc_020, tc_022**: `flopType` をスーテッドに修正、`barrelScore` を再計算（推奨は変わらない）。
5. **tc_006, tc_010, tc_011, tc_012, tc_019, tc_020, tc_022** の `flopTypeReason` テキストに「① 同スート2枚以上? YES → スーテッド優先」のロジックを反映。

### 検討事項

6. **tc_021** (K9 air on J83 → 2) について、「全レンジCBet」の注釈に「H1 air は GTO で 33% チェック側に混在」を追記。または barrel=8 を境界として H1 専用ロジックを追加。
7. river-first カードの formula 設計を見直し: formula 最終判断を answer から逆算しないよう、「役 + ボード + ポジション → ベット/チェック」のマッピングを明文化。

---

## 検証データソース

- `knowledges/volume4/results/102/` (270 ターン CBet シナリオ TexasSolver 結果)
- `knowledges/volume4/results/barrel_score_verify/barrel_score_verify_table.md`
- `knowledges/volume4/results/role_score_verify/role_score_verify_result.json`
- `knowledges/volume4/results/c_coef_verify/c_coef_summary.json`
- `knowledges/volume4/action_framework_coefficients.md`
- `volume4/chapters/08-barrel-score.md` (FlopType 分類の優先順位)

---

## 修正完了履歴 (2026-05-05 追記)

**全項目修正完了**。本レポートで指摘した不整合は以下のコミットで解消済み:

### 必須修正（推奨アクション反転）

| 項目 | コミット | 状態 |
|------|---------|------|
| tc_006 を スーテッド + チェックに変更 | `195d6cf` | ✓ |
| tc_010 を スーテッド + CBet に変更 | `195d6cf` | ✓ |
| rf_010 / rf_016 formula↔answer 整合 | `85bcb26` | ✓ |
| rf_013 / rf_017 / rf_018 TPMK 薄バリュー分岐 | `85bcb26` | ✓ |

### 推奨修正

| 項目 | コミット | 状態 |
|------|---------|------|
| tc_011/012/019/020/022 を スーテッド に統一 | `195d6cf` で統合修正 | ✓ |
| tc_022〜tc_025 を削除（impossible flush combos） | `195d6cf` (25→21 cards) | ✓ |
| flopTypeReason テキストの「同スート2枚以上」優先表記 | `195d6cf` | ✓ |

### 追加対応（本レポート指摘外）

| 項目 | コミット |
|------|---------|
| Sub-NFD / ナッツストレートブロッカー +2 補正の実装 | `4c927a6` / `3834a21` |
| Wheel straight 完成 / J-Q-K-A の OESD→gutshot 修正 | `45a5f55` |
| ペア板 trips 認識 (set_plus 30) | `20d6261` |
| 重複カード validation | `295aed6` |
| flop-vs-cbet 系 5 deck の SDV (4分類) generator 化 | `ec27b42` / `1c22e18` |

**現状の cards (2026-05-05)**: tc_022-025 は存在しない。turn-cbet 21 cards 構成で、すべての formula↔answer は整合。`audit_card_consistency.py` で 411 cards 中 0 実体不整合を確認済み。

詳細は `poker-drill/CHANGELOG.md` 参照。
