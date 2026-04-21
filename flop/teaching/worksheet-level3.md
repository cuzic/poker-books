# Level 3 ワークシート（完全統合式）

<!-- markdownlint-disable MD036 MD040 MD056 MD060 -->
<!-- textlint-disable preset-ja-technical-writing/no-exclamation-question-mark -->
<!-- textlint-disable preset-ja-technical-writing/no-mix-dearu-desumasu -->

**指示**：各問題で完全統合式を使って最終 CBet スコアを算出し、判定を出してください。

**完全統合式**

```
CBet スコア = HandScore − BoardScore + Position + R3 + M + SPR + E + 3bP
```

**補正値早見**

| 項目 | 条件 | 補正値 |
|-----|-----|-------|
| Position | IP | +3 |
| Position | OOP | 0 |
| R3 | ハイカード × レイザー | +2 |
| R3 | ローカード × レイザー | −2 |
| R3 | ハイカード × コーラー | −2 |
| R3 | ローカード × コーラー | +2 |
| M | ヘッズアップ | 0 |
| M | 3-way | −3 |
| M | 4-way 以上 | −5 |
| SPR | SPR ≤ 3 | +2 |
| SPR | SPR 3〜6 | 0 |
| SPR | SPR 6〜15 | −1 |
| SPR | SPR ≥ 15 | −3 |
| E | タイトパッシブ（ロック） | +3 |
| E | TAG | +1 |
| E | GTO 近似 | 0 |
| E | LAG | −2 |
| E | コールステーション | −3 |
| 3bP | SRP（標準） | 0 |
| 3bP | 3bet ポット | −2 |
| 3bP | 4bet ポット | −4 |

**判定基準**：≥ 15 → CBet 75%、8〜14 → CBet 33%、2〜7 → チェック、< 2 → チェック・フォールド準備

---

## 問1

**状況**：BTN vs BB、K♠7♦2♣（BoardScore = 0）、ヘッズアップ SRP

- あなたのハンド：A♥K♦（TPTK：HandScore = 18）
- ポジション：BTN（IP）
- SPR：8（SPR 6〜15 → −1）
- 相手タイプ：ロック（E = +3）

**計算欄**

| 項目 | 値 |
|-----|---|
| HandScore | ___ |
| −BoardScore | ___ |
| Position | ___ |
| R3 | ___ |
| M | ___ |
| SPR | ___ |
| E | ___ |
| 3bP | ___ |
| **合計** | ___ |

判定：___

**解答**

| 項目 | 値 |
|-----|---|
| HandScore | 18 |
| −BoardScore | 0 |
| Position | +3 |
| R3 | +2（ハイカード × レイザー） |
| M | 0（ヘッズアップ） |
| SPR | −1（SPR 8） |
| E | +3（ロック） |
| 3bP | 0（SRP） |
| **合計** | **25** |

→ **CBet 75%**（強バンド、ロックへの搾取で大サイズが有効）

---

## 問2

**状況**：BTN vs BB、J♦8♣4♦（BoardScore = 4）、ヘッズアップ 3bet ポット

- あなたのハンド：A♠A♦（オーバーペア：HandScore = 20）
- ポジション：BTN（IP）
- SPR：4（3bet ポットで SPR 3〜6 → 0）
- 相手タイプ：GTO 近似（E = 0）

**計算欄**

| 項目 | 値 |
|-----|---|
| HandScore | ___ |
| −BoardScore | ___ |
| Position | ___ |
| R3 | ___ |
| M | ___ |
| SPR | ___ |
| E | ___ |
| 3bP | ___ |
| **合計** | ___ |

判定：___

**解答**

| 項目 | 値 |
|-----|---|
| HandScore | 20 |
| −BoardScore | −4 |
| Position | +3 |
| R3 | +2（ハイカード × レイザー） |
| M | 0（ヘッズアップ） |
| SPR | 0（SPR 4） |
| E | 0 |
| 3bP | −2（3bet ポット） |
| **合計** | **19** |

→ **CBet 75%**（3bP 補正 −2 があっても強バンド維持）

---

## 問3

**状況**：BTN vs BB vs CO、T♦9♦8♣（BoardScore = 7）、3-way SRP

- あなたのハンド：K♥K♣（オーバーペア：HandScore = 20）
- ポジション：BTN（IP）
- SPR：9（SRP で SPR 6〜15 → −1）
- 相手タイプ：不明（E = 0）

**計算欄**

| 項目 | 値 |
|-----|---|
| HandScore | ___ |
| −BoardScore | ___ |
| Position | ___ |
| R3 | ___ |
| M | ___ |
| SPR | ___ |
| E | ___ |
| 3bP | ___ |
| **合計** | ___ |

判定：___

**解答**

| 項目 | 値 |
|-----|---|
| HandScore | 20 |
| −BoardScore | −7 |
| Position | +3 |
| R3 | −2（ローカード × レイザー） |
| M | −3（3-way） |
| SPR | −1（SPR 9） |
| E | 0 |
| 3bP | 0（SRP） |
| **合計** | **10** |

→ **CBet 33%**（3-way で M = −3 が効き、75% → 33% に落ちる。ウェットボードでの KK は慎重に）

---

## 問4

**状況**：CO vs BB、Q♠7♦2♣（BoardScore = 3）、ヘッズアップ SRP

- あなたのハンド：A♦5♦（空振り + BDFD：HandScore = 0 + 4 = 4）
- ポジション：CO（IP）
- SPR：10（SPR 6〜15 → −1）
- 相手タイプ：コールステーション（E = −3）

**計算欄**

| 項目 | 値 |
|-----|---|
| HandScore | ___ |
| −BoardScore | ___ |
| Position | ___ |
| R3 | ___ |
| M | ___ |
| SPR | ___ |
| E | ___ |
| 3bP | ___ |
| **合計** | ___ |

判定：___

**解答**

| 項目 | 値 |
|-----|---|
| HandScore | 4 |
| −BoardScore | −3 |
| Position | +3 |
| R3 | +2（ハイカード × レイザー） |
| M | 0（ヘッズアップ） |
| SPR | −1（SPR 10） |
| E | −3（コールステーション） |
| 3bP | 0（SRP） |
| **合計** | **2** |

→ **チェック（チェック・フォールド境界）**。コールステーションへのブラフは通りにくく、空振り+BDFD でのセミブラフは割に合わない。

---

## 問5

**状況**：BTN vs BB、A♣K♥Q♦（BoardScore = 4）、ヘッズアップ 4bet ポット

- あなたのハンド：A♠A♦（オーバーペア：HandScore = 20）
- ポジション：BTN（IP）
- SPR：2（4bet ポットで SPR ≤ 3 → +2）
- 相手タイプ：TAG（E = +1）

**計算欄**

| 項目 | 値 |
|-----|---|
| HandScore | ___ |
| −BoardScore | ___ |
| Position | ___ |
| R3 | ___ |
| M | ___ |
| SPR | ___ |
| E | ___ |
| 3bP | ___ |
| **合計** | ___ |

判定：___

**解答**

| 項目 | 値 |
|-----|---|
| HandScore | 20 |
| −BoardScore | −4 |
| Position | +3 |
| R3 | +2（ハイカード × レイザー） |
| M | 0（ヘッズアップ） |
| SPR | +2（SPR 2、浅い） |
| E | +1（TAG） |
| 3bP | −4（4bet ポット） |
| **合計** | **20** |

→ **CBet 75%**。4bP 補正 −4 でも SPR が浅い（+2）ため強バンドに残る。AA はスタックオフを目指す。

---

## 解答まとめ

| 問 | 状況 | ハンド | 合計スコア | 最終判定 |
|----|-----|-------|---------|---------|
| 1 | HU SRP、K72r | TPTK（AK）vs ロック IP | 25 | CBet 75% |
| 2 | HU 3bP、J84dd | OP（AA）vs GTO IP | 19 | CBet 75% |
| 3 | 3-way SRP、T98r | OP（KK） IP | 10 | CBet 33% |
| 4 | HU SRP、Q72r | 空振り+BDFD（A5）vs CS IP | 2 | チェック |
| 5 | HU 4bP、AKQr | OP（AA）vs TAG IP | 20 | CBet 75% |
