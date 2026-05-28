# Light UCBS v2 + Light DCBS — 書籍向け公式リファレンス

作成日: 2026-05-28
ソース: `ucbs_light_v2.py` / `dcbs.py` / `UCBS_V2_DCBS_FINAL.md`
用途: Vol2 各章 YAML から transclude・参照する単一情報源

---

## 1. HP テーブル (Hand Power) — 16 hand → 6 バケット

| HP 値 | Hand type |
|---:|---|
| 2 | no_made_hand, ace_high, king_high, low_pair |
| 3 | underpair, third_pair |
| 5 | second_pair |
| 7 | top_pair, overpair |
| 8 | set, trips |
| 9 | two_pair, flush, straight, fullhouse, quads |

**暗記のコツ**: 値は 2, 3, 5, 7, 8, 9 の 6 段階。「エアー=2、弱ペア=3、中ペア=5、トップ=7、セット=8、怪物=9」と覚えます。

---

## 2. DP テーブル (Draw Power) — 4 段階

| DP 値 | Draw type |
|---:|---|
| 0 | no_draw, twocards_bdfd |
| 1 | gutshot |
| 2 | oesd, fd (フラッシュドロー) |
| 3 | combo_draw (oesd + fd など) |

**計算例**:
- A♥K♥ on Q♥7♦2♣ → HP=7 (top_pair: A-high で Q hit → overpair 想定) + DP=0 = **CBS=7**
- 8♥7♥ on T♦9♠2♥ → HP=2 (no_made_hand) + DP=3 (OESD+FD) = **CBS=5**
- 6♠6♣ on A♠7♦2♣ → HP=3 (underpair) + DP=0 = **CBS=3**

---

## 3. CBS バンド — 5 区分

| バンド | CBS 範囲 | 直感的意味 |
|---|---:|---|
| air | 0-2 | 完全な空振り / weak air |
| weak | 3-4 | 弱ペア / weak draw |
| mid | 5-6 | 中程度のペア / 強ドロー |
| strong | 7-8 | トップペア以上 / セット |
| nut | 9+ | 2 ペア以上の怪物ハンド |

---

## 4. LIGHT_V2_BASE — 5 context × 5 CBS バンドの 25 セル表

ソース: `ucbs_light_v2.py` `LIGHT_V2_BASE` (行 30-37)

| context | air | weak | mid | strong | nut |
|---|---:|---:|---:|---:|---:|
| **cash** | 45% | 40% | 40% | 60% | 60% |
| **mtt_short** | 40% | 30% | 35% | 60% | 75% |
| **mtt_deep** | 40% | 40% | 40% | 60% | 60% |
| **3bp** | 45% | 50% | 60% | 70% | 60% |
| **turn** | 5% | 5% | 10% | 30% | 40% |

**読み方**: セルの値 = 「cbet を打つ頻度の目安」。
≥50% ならベット推奨、<50% ならチェック寄りと解釈します。

**context の定義**:
- `cash`: Cash 100bb SRP (single raised pot)。Vol2 の主役。
- `mtt_short`: MTT 25-50bb。終盤〜中盤の短スタック。
- `mtt_deep`: MTT 100bb+。序盤または深スタック。
- `3bp`: 3-bet pot (SPR ~5)。Cash/MTT 共通。
- `turn`: ターン 2nd barrel (フロップ cbet 後)。

---

## 5. LIGHT_V2_OFFSET — 例外補正

| hand | offset | 説明 |
|---|---:|---|
| low_pair | -10pt | context 問わず適用。trash 扱い。 |

**注意**: low_pair は HP=2 に分類されますが、no_made_hand・ace_high・king_high と異なり、ボードにある小さいペアを持っている状態です。値が低いほどブラフとして打ちにくいため、追加でマイナス補正を加えます。

---

## 6. DCBS — Light DCBS (cash 100bb) continue freq 表

ソース: `dcbs.py` `DCBS_CONTEXTS["cash_100bb"]` (行 57-64)

### 6-1. DCBS_BASE (HP 別 continue freq)

| HP | Hand type | continue freq | fold freq |
|---:|---|---:|---:|
| 2 | air (no_made_hand 等) | 40% | 60% |
| 3 | underpair, third_pair | 85% | 15% |
| 5 | second_pair | 98% | 2% |
| 7 | top_pair, overpair | 100% | 0% |
| 8 | set, trips | 100% | 0% |
| 9 | two_pair 以上 | 100% | 0% |

### 6-2. Kicker offset (HP=2 内の細分化)

HP=2 (air) のハンドに対して、以下のキッカー補正を加算します。

| hand | offset | 最終 continue freq |
|---|---:|---:|
| ace_high | +5pt | **45%** |
| king_high | +0pt | **40%** |
| no_made_hand | -3pt | **37%** |
| low_pair | -2pt | **38%** |

**適用条件**: kicker offset は HP=2 のハンドにのみ適用します。HP=3 以上は kicker offset = 0。

---

## 7. DCBS — 全 4 context continue freq 比較表

ソース: `dcbs.py` `DCBS_CONTEXTS` + `UCBS_V2_DCBS_FINAL.md`

### HP=2 (air) のみ: context 別 base continue freq

| context | air base | ace_high offset | ace_high 最終 |
|---|---:|---:|---:|
| mtt_25bb | 67% | +10pt | 77% |
| mtt_50bb | 54% | +17pt | 71% |
| mtt_100bb | 28% | +5pt | 33% |
| **cash_100bb** | **40%** | **+5pt** | **45%** |

**発見**: 深スタックほど air は fold。mtt_100bb では air の 72% が fold するのに対し、cash_100bb では 60% が fold (よりルーズ)。

### top_pair (HP=7) はどこでも continue ≈ 100%

| context | top_pair continue |
|---|---:|
| mtt_25bb | 100% |
| mtt_50bb | 99% |
| mtt_100bb | 96% |
| cash_100bb | 100% |

---

## 8. 暗算フロー — Light UCBS v2 (6 ステップ)

```
[Step 1] HP 確認
  hand type → HP テーブル → HP 値 (2/3/5/7/8/9)

[Step 2] DP 確認
  draw type → DP テーブル → DP 値 (0/1/2/3)

[Step 3] CBS 計算
  CBS = HP + DP

[Step 4] CBS バンド判定
  CBS 0-2 → air
  CBS 3-4 → weak
  CBS 5-6 → mid
  CBS 7-8 → strong
  CBS 9+  → nut

[Step 5] context 確認 + 25 セル表参照
  (cash / mtt_short / mtt_deep / 3bp / turn) × band
  → LIGHT_V2_BASE[context][band] = freq

[Step 6] 例外補正 → 判断
  low_pair なら freq -= 10pt
  pos_lift 補正 (SB -8, CO/HJ +10)
  freq ≥ 50% → bet
  freq < 50% → check
```

**所要時間目安**: 手慣れると 5-7 秒で Step 1-6 を完了できます。

---

## 9. 暗算フロー — Light DCBS (3-5 ステップ)

```
[Step 1] HP 確認 (DCBS 用)
  hand type → HP テーブル → HP 値

[Step 2] context 確認
  cash 100bb か MTT 何 bb か

[Step 3] base continue freq 参照
  DCBS_BASE[context][HP] → base freq

[Step 4] kicker offset (HP=2 のみ)
  HP=2 なら hand 別の offset を加算
  HP≥3 なら offset = 0

[Step 5] 判断
  continue_freq ≥ 50% → call (or raise)
  continue_freq < 50% → fold
```

---

## 10. 補正値まとめ (cash 100bb)

| 補正種別 | 値 | 条件 |
|---|---:|---|
| pos_lift SB | -8pt | SB から cbet する場合 |
| pos_lift BTN | 0pt | 基準 (補正なし) |
| pos_lift CO/HJ | +10pt | ワイドレンジから open した場合 |
| pos_lift UTG | 0pt | タイトレンジ (補正なし) |
| ターン α シフト | -35pt | フロップ → ターンに進んだとき |
| 型6 ボード | +1 段 (信頼度 up) | mid 連結ウェット ボード |
| mono ボード | -1 段 (信頼度 down) | 3 枚同スーツ (cash のみ) |
| low_pair offset | -10pt | 常時適用 |

---

## 11. 精度参考 (WRMSE)

Light UCBS v2 は Full UCBS-v2 に対して以下の精度差があります。

| context | Light v2 WRMSE | Full v2 WRMSE | 差 |
|---|---:|---:|---:|
| cash_100bb | ~19% | 16.43% | +2-3pt |
| mtt_25bb (mtt_short) | ~18% | 15.46% | +2-3pt |
| mtt_50bb (mtt_short) | ~16% | 12.96% | +3pt |
| mtt_100bb (mtt_deep) | ~24% | 21.95% | +2pt |
| 3bp_50bb (3bp) | ~12% | 8.62% | +3pt |
| turn (cash_100bb_turn) | ~20% | 16.11% | +4pt |

**解釈**: Full v2 に比べて +2-4pt の誤差増で、「暗算 5 秒」との交換代として許容できる範囲です。MTT 100bb 系は Light/Full とも精度低め (20%+)。

---

## 関連ファイル

- 実装 (Light UCBS v2): `vol2-cash-postflop/ucbs_light_v2.py`
- 実装 (DCBS): `vol2-cash-postflop/dcbs.py`
- 実装 (Full UCBS-v2 参考): `vol2-cash-postflop/ucbs_v2.py`
- 仕様書 (詳細): `knowledges/gto_wizard_study/UCBS_V2_DCBS_FINAL.md`
- 章 outline: `vol2-cash-postflop/outline.md`
- 用語定義: `vol2-cash-postflop/findings/terminology.md`
