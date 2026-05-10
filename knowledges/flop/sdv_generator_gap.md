# SDV (ショーダウンバリュー) Generator Gap

**起草日**: 2026-05-05
**起源**: poker-drill commit 3d2fe42 で flop-vs-cbet-cards.ts を手編集
**現状**: 手編集と generator output が乖離

---

## 1. 現状の食い違い

### 手編集 (commit 3d2fe42, 5月4日)

**フォーマット**: SDV (ショーダウンバリュー) 4 分類ベース
```
役割分類: 攻める / ショーダウンバリュー / 守る / 捨てる
formula.title: "役割マッピング → 防御アクション"
formula.steps: [役割分類, 根拠, ポジション, CBetサイズ, 役割×CBetサイズ]
flopDefense.role: SDV カテゴリ
flopDefense.roleReason: 役の根拠 + ポジション差説明
```

### Generator (`flop_defense.py`)

**フォーマット**: HandScore + back_score ベース
```
formula.title: "HandScore + ナッツアドバンテージ → 防御アクション"
formula.steps: [役スコア, ドロー加点, HandScore, A 係数, 基準値, C 補正, M 補正, 後手スコア合計, ナッツアドバンテージ, 判断]
flopDefense.role: なし
formula は計算的、SDV は概念的
```

### 答えの差異 (5 サンプル)

| ID | hand | board | bet% | manual answer | gen answer | 一致 |
|----|------|-------|------|--------------|-----------|------|
| fv_001 | A♥K♦ | A♠7♦2♣ | 33% | コール | コール | ✓ |
| fv_002 | K♥9♦ | K♠7♦2♣ | 50% | コール | コール | ✓ |
| fv_003 | K♥5♦ | K♠7♦2♣ | 75% | コール | フォールド | ✗ |
| fv_004 | A♥J♦ | A♠9♦5♣ | 50% | コール | チェックレイズ | ✗ |
| fv_005 | T♥T♦ | T♠7♦4♣ | 75% | コール | コール | ✓ |

24 枚中 N 枚で答えが異なる（要全件比較）。

---

## 2. 根本原因

**SDV と back_score は異なるフレームワーク:**

- **back_score** (DS = HS + A − C − M、新スケール 0-100): 数値的に「コール / CR / fold」の閾値で判定
- **SDV**: ハンドの役 × ポジション × ナッツアドバンテージで「攻める / SDV / 守る / 捨てる」をルックアップ

両者は重なる部分もあるが、境界での挙動が違う:
- back_score ≥ 20 → CALL（H1 でも MDF で守る）
- SDV「捨てる」→ FOLD（H1 weak はナッツ不利板で fold）

---

## 3. 提案: SDV を generator に取り込む

### 3.1 ロール分類テーブル

```python
SDV_ROLE_TABLE = {
    # (役カテゴリ, position, nut_advantage) → SDV_role
    ('set_plus', 'OOP', 'OOP有利'): '攻める',
    ('set_plus', 'OOP', 'IP有利'): '攻める',
    ('set_plus', 'OOP', '中立'): '攻める',
    ('two_pair', 'OOP', 'IP有利'): 'ショーダウンバリュー',
    ('two_pair', 'OOP', 'OOP有利'): '攻める',
    ('tptk', 'OOP', 'IP有利'): 'ショーダウンバリュー',
    ('tptk', 'OOP', 'OOP有利'): '攻める',
    ('tpgk', 'OOP', 'IP有利'): 'ショーダウンバリュー',
    ('tpgk', 'OOP', 'OOP有利'): '攻める',
    ('tpgk', 'OOP', '中立'): '守る',
    ('tpmk', 'OOP', 'IP有利'): 'ショーダウンバリュー',
    ('tpmk', 'OOP', 'OOP有利'): '守る',
    ('tpwk', 'OOP', '*'): '守る',
    ('second_pair_strong', 'OOP', '*'): '守る',
    ('second_pair_weak', 'OOP', '*'): '守る',
    ('underpair', 'OOP', '*'): '捨てる',
    ('bottom_pair', 'OOP', '*'): '捨てる',
    ('air', 'OOP', '*'): '捨てる',
    # Same for IP (with float behavior)
    ('tpgk', 'IP', 'IP有利'): 'ショーダウンバリュー',  # fv_019
    ('tpmk', 'IP', 'OOP有利'): 'ショーダウンバリュー',  # fv_020
    # ... etc
}

SDV_ACTION = {
    ('攻める', 'OOP'): 'CHECK_RAISE',
    ('攻める', 'IP'): 'RAISE',
    ('ショーダウンバリュー', 'OOP'): 'CALL',
    ('ショーダウンバリュー', 'IP'): 'BET (薄バリュー)',  # for IP cards
    ('守る', '*'): 'CALL' or 'FOLD' (CBetサイズで分岐),
    ('捨てる', '*'): 'FOLD',
}
```

### 3.2 既存テーブルの参考

flop-vs-cbet-cards.ts の役割分類は `commit 3d2fe42` で確立済み。24 枚の (hand, board, position, nut_adv, role) マッピングを抽出して上記テーブルを精緻化できる。

### 3.3 並走戦略

- **フェーズ 1**: 既存 generator の formula 形式は維持しつつ、`flopDefense.role` フィールドだけを SDV ロジックで埋める
- **フェーズ 2**: formula 形式を SDV ベースに切り替え（`title: "役割マッピング → 防御アクション"`）
- **フェーズ 3**: flop-vs-cbet-3bp / flop-multiway / flop-vs-cbet-4bp も同様に SDV 化

---

## 4. 実装の優先度と作業量見積もり

**優先度: 中〜高**

理由:
- 現状は手編集と generator が乖離しており、技術的負債（再生成すると手編集が消える）
- 教育的にも SDV 4 分類は明快（巻4 第7章のフレームワークに整合）

**作業量**:
- フェーズ 1（role フィールド追加のみ）: 3-5 時間（テーブル定義 + テスト）
- フェーズ 2（formula 形式切り替え）: 5-8 時間（builder 修正、UI 互換性確認）
- フェーズ 3（他デッキ対応）: 各 2-3 時間 × 3 デッキ

---

## 5. 暫定対応 → 解消（2026-05-05）

~~実装するまでの間、以下の運用ルールで凌ぐ~~

**全フェーズ完了**:

- フェーズ 1+2 完了 (commit ec27b42): `flop-vs-cbet-cards.ts` 24枚を SDV generator 化
  - CSV (`situation02_flop_defense_inputs.csv`) に SDV 列を追加
  - `flop_defense.py` に SDV モード分岐を実装
  - `core/builder.py` の `build_flop_defense_card` に SDV パラメータを追加
- フェーズ 3 完了 (commit 1c22e18): 残り 4 deck の SDV 化
  - `flop-vs-cbet-3bp-cards.ts` (12枚, 3 ステップ)
  - `flop-vs-cbet-4bp-cards.ts` (6枚, 4 ステップ)
  - `flop-vs-cbet-3bp-oop-cards.ts` (12枚, 5 ステップ)
  - `flop-multiway-cards.ts` (15枚, 5 or 6 ステップ)
- データエラー修正 (commit fa3ddf5): mw_010 と rf_002 の重複カード解消

**現在の状況**:

- 全 5 deck (flop-vs-cbet, 3bp, 4bp, 3bp-oop, multiway) は generator から SDV 4 分類で再生成可能
- 手編集禁止リストは空（feedback memory 更新済み）
- calc.py 変更（NFD 等）に対しても全 deck を安全に regen できる

**残課題**:

- なし。本ドキュメントは履歴として保持。将来の SDV ロジック発展時の参考資料。

## 6. 教訓

このフェーズで得た知見:

1. **CSV にデータ列を追加する戦略は強力**: ロジック実装より単純で柔軟
2. **手編集と generator の食い違いは早期検出が重要**: git diff チェックを CI に組み込むべき
3. **重複カード（A♠ in hand and board）は generator が自動検出すべき**: 将来 calc.py に validation を追加する余地あり
