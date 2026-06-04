# 追加GTO調査計画

**作成日**: 2026-05-19  
**前提gametype**: `MTTGeneral`（8-max, Chip-EV）  
**不可**: ICM SRP postflop / マルチウェイ / SBR<10

既収集データのギャップを埋める6シナリオ。優先順で並べる。

---

## S1【最優先】BBのCBet応答率（フォールド/コール/チェックレイズ率）

### なぜ必要か

BTNのCBet頻度は測定済み（型1:79.9%, 型4:67.6% at SBR25）。しかし**BBがどれだけフォールドするか**が不明なため、CBetの収益性が検証できない。BBフォールド率が高ければCBet閾値を下げられる可能性がある。

### パラメータ

| 項目 | 値 |
|-----|---|
| Gametype | `MTTGeneral` |
| Depth | 25.125, 20.125 |
| Preflop | `F-F-F-F-F-R2.1-F-C`（SBR25）/ `F-F-F-F-F-R2-F-C`（SBR20） |
| Boards | 型1 Ks7d2c / 型2 Qh8d3s / 型4 Th9s8d（既存3種） |
| **Flop action** | `R1.15`（BTNが33%ポットCBet）→ BBのレスポンスを取得 |

### API呼び出しイメージ

```python
# BBのCBet応答: flop_actions="R1.15" でBTNがベットした状態のBBのアクションを取得
resp = call_api(
    "MTTGeneral", depth=25.125, stacks=[],
    preflop="F-F-F-F-F-R2.1-F-C",
    flop="R1.15",    # BTNが33%ベット後のBBアクション
    board="Ks7d2c"
)
```

### 期待するデータ

BB fold% / call% / raise% × 3ボード型 × 2 SBR = 18データポイント

### 章への貢献

第3章・第4章のCBet閾値、第11章のマルチウェイCBet禁止根拠の定量化

---

## S2【優先】残り4ボード型のBTN CBet頻度

### なぜ必要か

7分類のうち型1/2/4しか測定していない。型3/5/6/7は第3〜5章で扱うが実測根拠なし。

### 代表ボード選定

| ボード型 | 代表ボード | 選定理由 |
|--------|---------|--------|
| 型3 ミッドウェット | `Jd6c4d` | Jハイ、2トーン、スプレッド8 |
| 型5 ミッドドライ | `Ts5d2c` | Tハイ、レインボー、スプレッド9 |
| 型6 ペアボード | `7s7d2c` | 7ペア、ドライ |
| 型7 モノトーン | `KsJs8s` | 3スペード |

### パラメータ

| 項目 | 値 |
|-----|---|
| Gametype | `MTTGeneral` |
| Depth | 20.125 / 25.125 / 40.125（3段階） |
| Preflop | 各depthに応じたBTN raise size |
| Boards | 上記4種（新規） |
| Flop action | なし（BTNの初手戦略を取得） |

### 期待するデータ

4ボード型 × 3 SBR = 12データポイント（CBet% + 主要サイズ分布）

### 章への貢献

第3〜5章のボード型別CBet基準の完成、付録Cの全ボード型対応チートシート

---

## S3【優先】SBR15のBTN CBet頻度（境界値）

### なぜ必要か

SPR≈4.5（SBR15）は「Short」と「Middle」の境界。第4章と第5章の閾値が交差する重要ゾーン。depth=10.125はpush/fold境界で取得不可だが、15.125は取得可能なはず。

### パラメータ

| 項目 | 値 |
|-----|---|
| Gametype | `MTTGeneral` |
| Depth | 15.125 |
| Preflop | **要事前確認**: raise sizeをpreflop treeで特定 |
| Boards | 型1 Ks7d2c / 型2 Qh8d3s / 型4 Th9s8d |

### 事前確認コマンド（raise size特定）

```python
# SBR15でのBTN raise sizeを確認
for raise_size in [1.8, 2.0, 2.1, 2.3, 2.5]:
    r = call_api("MTTGeneral", 15.125, [],
                 preflop=f"F-F-F-F-F-R{raise_size}-F-C",
                 board="Ks7d2c")
    print(f"R{raise_size}: {'OK' if 'action_solutions' in str(r) else 'ERR'}")
```

### 期待するデータ

型1/2/4 × SBR15 = 3データポイント（既存SBR20/25/40/60との比較に使用）

### 章への貢献

第5章のコミットライン（SPR4.5）の実測値

---

## S4【高優先】ターンバレル頻度

### なぜ必要か

第12章のバレルスコア閾値（≥7で継続）はvol2のキャッシュデータに基づく。MTTでは浅いSBRの影響でターン判断が異なる可能性がある。`call_api`の`flop`パラメータで「フロップCBet→BBコール後のターン」を取得できる。

### ターンカード選定（型1 Ks7d2c を起点に）

| カード | 意味 | 分類 |
|------|-----|-----|
| `As` | オーバーカード（Kより高い） | ブランク（BTN有利） |
| `Jd` | アンダーカード・ブランク | ブランク（BTN有利） |
| `2c` | ボードペア（2ペア） | ペアカード |
| `6s` | ミドルブランク | ニュートラル |
| `9d` | バックドアストレート完成かも | やや危険 |

### パラメータ

| 項目 | 値 |
|-----|---|
| Gametype | `MTTGeneral` |
| Depth | 25.125 |
| Preflop | `F-F-F-F-F-R2.1-F-C` |
| Board | `Ks7d2c`（型1 ハイドライ）+`Th9s8d`（型4）の2ボード |
| Flop action | `R1.15-C`（BTNが33%CBet、BBがコール） |
| Turn | 上記5種 × 2ボード |

### API呼び出しイメージ

```python
resp = call_api(
    "MTTGeneral", depth=25.125, stacks=[],
    preflop="F-F-F-F-F-R2.1-F-C",
    flop="R1.15-C",   # BTN CBet → BB call
    board="Ks7d2c",
    turn="As"         # ターンカード指定
)
# → BTNのターンアクション戦略（bet% / check%）を取得
```

### 期待するデータ

5ターンカード × 2ボード = 10データポイント（BTNのバレル率）

### 章への貢献

第12章のバレルスコア閾値のMTT補正（「≥7」が正確かどうかの検証）

---

## S5【中優先】3BPポストフロップ（ICM gametype）

### なぜ必要か

第10章（3BPポストフロップ）の根拠が理論のみ。`MTTGeneral_ICM9m200PTPCT25`はSRP不可だが3BPは収録済みと確認されている。

### パラメータ

| 項目 | 値 |
|-----|---|
| Gametype | `MTTGeneral_ICM9m200PTPCT25` |
| Preflop | `R2-F-R6-F-F-F-F-F-F-C`（UTG open R2 → CO 3bet R6 → BB call） |
| Depth | 100.125（大きめのスタックが必要？→要確認） |
| Boards | 型1 Ks7d2c / 型2 Qh8d3s / 型4 Th9s8d |

### 事前確認コマンド（3BP action formatと必要depthの特定）

```python
for pf in [
    "R2-F-R6-F-F-F-F-F-F-C",    # UTG open, CO 3bet, BB call
    "F-F-F-F-R2.1-R6-F-F-F-C",  # CO open, BTN 3bet, BB call
    "F-F-F-F-F-R2.1-R7-F-C",    # BTN open, SB 3bet, BB call
]:
    for depth in [50.125, 100.125]:
        r = call_api("MTTGeneral_ICM9m200PTPCT25", depth, [],
                     preflop=pf, board="Ks7d2c")
        print(f"depth={depth}, pf={pf[:20]}: {'OK' if 'action_solutions' in str(r) else str(r)[:80]}")
```

### 期待するデータ

3BPポストフロップでのIP/OOP CBet頻度 × 3ボード型

### 章への貢献

第10章の「SPR≈2でのコミット or 降り判断」の実測根拠

---

## S6【補足】SB vs BB SRP の複数SBR（SBR20/40）

### なぜ必要か

SBがOOPで先手を取るシナリオはSBR25のみ測定済み。SBR20（SPR≈6）とSBR40（SPR≈12）の比較でOOPリード頻度の深度依存性を確認できる。

### パラメータ

| 項目 | 値 |
|-----|---|
| Gametype | `MTTGeneral` |
| Preflop | SBR20: `F-F-F-F-F-F-R3-C` → **要確認: SBR20でのSB raise size** |
| Depth | 20.125 / 40.125 |
| Boards | 型1/2/4 |

### 事前確認

SBR20/40でのSBの raise size が3BBか否かを確認してから実行。

---

## 実行順序と推奨バッチ

| 優先度 | シナリオ | API呼び出し数 | 所要時間目安 |
|------|--------|----------|----------|
| 1 | S1 BBのCBet応答率 | 12（3ボード×2SBR×2サイズ） | 15分 |
| 2 | S2 残り4ボード型 | 12（4ボード×3SBR） | 15分 |
| 3 | S3 SBR15境界値 | 3+5（確認含む） | 10分 |
| 4 | S4 ターンバレル | 10（5カード×2ボード） | 15分 |
| 5 | S5 3BP postflop | 3+確認 | 10分 |
| 6 | S6 SB vs BB SBR変化 | 6 | 10分 |

**合計**: 約50〜60 API呼び出し、75分（トークン有効期間15分を考慮して4〜5セッションに分割）

## 取得できないデータの代替方針

| 欠落データ | 代替方針 |
|---------|--------|
| ICM SRP postflop実測値 | 理論値（+10〜15%）を使用し、章末コラムで「実測不可のため推定値」と明記 |
| マルチウェイ実測値 | GTO Wizardのサポートページ・学術論文の統計値（Poker Solver研究）を参照 |
| SBR<10 SRP | Push/Fold境界であるため不要（vol3のプッシュフォールド表を参照） |
