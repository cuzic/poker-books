# Level 1 ワークシート（基本式）

<!-- markdownlint-disable MD036 MD040 MD056 MD060 -->
<!-- textlint-disable preset-ja-technical-writing/no-exclamation-question-mark -->
<!-- textlint-disable preset-ja-technical-writing/no-mix-dearu-desumasu -->

> ⚠️ **このワークシートは旧版の式に基づいています**
>
> 本書（巻②フロップ基礎）の最新設計では、CBet スコア統合式に代わって
> **「ハンド役割分類 × 9マスマトリクス」**（第9・10章）を使用します。
> HandScore は equity % 相当の 0-100 指標へ統一されています。
>
> 最新の判定方法は本書 **第9章（ハンド役割分類）**および
> **第10章（9マスマトリクス）**を参照してください。

**指示**：各問題で `CBet スコア = HandScore − BoardScore + ポジション係数` を計算し、判定してください。

**判定基準**

- スコア ≥ 15 → CBet 75%
- スコア 8〜14 → CBet 33%
- スコア 2〜7 → チェック
- スコア < 2 → チェック・フォールド準備

**ポジション係数**：IP = +3、OOP = 0

---

## 問1

- ボード：K♠7♦2♣（BoardScore = 0）
- あなたのハンド：A♥K♦（TPTK）
- ポジション：BTN（IP）
- SPR：8

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 18（TPTK）、BoardScore = 0、ポジション係数 = +3。CBet スコア = 18 − 0 + 3 = **21**。→ **CBet 75%**

---

## 問2

- ボード：K♠7♦2♣（BoardScore = 0）
- あなたのハンド：8♥8♦（アンダーペア）
- ポジション：BTN（IP）
- SPR：8

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 6（アンダーペア）、BoardScore = 0、ポジション係数 = +3。CBet スコア = 6 − 0 + 3 = **9**。→ **CBet 33%**

---

## 問3

- ボード：9♥8♥7♦（BoardScore = 7）
- あなたのハンド：K♦K♣（オーバーペア）
- ポジション：BTN（IP）
- SPR：10

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 20（オーバーペア）、BoardScore = 7、ポジション係数 = +3。CBet スコア = 20 − 7 + 3 = **16**。→ **CBet 75%**

---

## 問4

- ボード：9♥8♥7♦（BoardScore = 7）
- あなたのハンド：A♠Q♣（ハイカードのみ）
- ポジション：BTN（IP）
- SPR：10

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 0（ハイカードのみ）、BoardScore = 7、ポジション係数 = +3。CBet スコア = 0 − 7 + 3 = **−4**。→ **チェック・フォールド準備**

---

## 問5

- ボード：A♠8♥3♦（BoardScore = 2）
- あなたのハンド：K♠Q♣（ハイカードのみ）
- ポジション：BB（OOP）
- SPR：9

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 0（ハイカードのみ）、BoardScore = 2、ポジション係数 = 0（OOP）。CBet スコア = 0 − 2 + 0 = **−2**。→ **チェック・フォールド準備**

---

## 問6

- ボード：Q♣J♦9♠（BoardScore = 4）
- あなたのハンド：Q♥J♣（2ペア）
- ポジション：BTN（IP）
- SPR：7

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 26（2ペアは役スコア 26 相当：セット 30 より2段階下）→ 実際は HandScore を次の通り計算。セット=30、2ペアは役スコアとして 26 を使用。CBet スコア = 26 − 4 + 3 = **25**。→ **CBet 75%**

（補足：2ペアは通常 HandScore 26 と設定。付録Bの HandScore 早見表を参照）

---

## 問7

- ボード：J♠T♠9♦（BoardScore = 8）
- あなたのハンド：A♥A♦（オーバーペア）
- ポジション：BB（OOP）
- SPR：11

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 20（オーバーペア）、BoardScore = 8、ポジション係数 = 0（OOP）。CBet スコア = 20 − 8 + 0 = **12**。→ **CBet 33%**

---

## 問8

- ボード：K♦Q♠2♣（BoardScore = 3）
- あなたのハンド：A♣K♣（TPTK + BDFD）
- ポジション：BTN（IP）
- SPR：8

（BDFD = バックドアフラッシュドロー、HandScore に +4 加算）

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 18 + 4 = 22（TPTK + BDFD）、BoardScore = 3、ポジション係数 = +3。CBet スコア = 22 − 3 + 3 = **22**。→ **CBet 75%**

---

## 問9

- ボード：T♦9♦8♣（BoardScore = 7）
- あなたのハンド：J♥T♣（TPWK + OESD 要素なし、ただしT でトップペア）
- ポジション：CO（IP）
- SPR：9

（TPWK = トップペア・弱キッカー：HandScore = 10）

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 10（TPWK）、BoardScore = 7、ポジション係数 = +3。CBet スコア = 10 − 7 + 3 = **6**。→ **チェック**

---

## 問10

- ボード：7♦7♣K♠（ペアボード、BoardScore = −1）
- あなたのハンド：K♥Q♦（TPGK）
- ポジション：BTN（IP）
- SPR：8

（ペアボードの BoardScore は −1 であることに注意）

**計算欄**

- HandScore = ___
- BoardScore = ___
- ポジション係数 = ___
- CBet スコア = ___
- 判定：___

**解答**：HandScore = 15（TPGK）、BoardScore = −1（ペアボード）、ポジション係数 = +3。CBet スコア = 15 − (−1) + 3 = 15 + 1 + 3 = **19**。→ **CBet 75%**

---

## 解答まとめ

| 問 | ボード | ハンド | スコア | 判定 |
|----|-------|-------|-------|-----|
| 1 | K72r | TPTK（AK） IP | 21 | CBet 75% |
| 2 | K72r | アンダーペア（88） IP | 9 | CBet 33% |
| 3 | 987hh | オーバーペア（KK） IP | 16 | CBet 75% |
| 4 | 987hh | 空振り（AQ） IP | −4 | チェック・フォールド |
| 5 | A83r | 空振り（KQ） OOP | −2 | チェック・フォールド |
| 6 | QJ9r | 2ペア（QJ） IP | 25 | CBet 75% |
| 7 | JT9ss | オーバーペア（AA） OOP | 12 | CBet 33% |
| 8 | KQ2r | TPTK+BDFD（AK） IP | 22 | CBet 75% |
| 9 | T98dd | TPWK（JT） IP | 6 | チェック |
| 10 | 77Kr | TPGK（KQ）ペアボード IP | 19 | CBet 75% |
