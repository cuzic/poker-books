# 第App章 暗算チートシート — 全章まとめ

本付録は全 12 章の核心公式を 1-2 ページにまとめた横断参照表です。
実戦中に「あの数値なんだっけ」と迷ったときに参照してください。
25 セル表・D モデル 表・暗算フロー (6 step + 3-5 step) が 1 か所に集約されています。

## TV 計算表 (MV + DV)

### MV テーブル — 16 hand → 6 バケット

| HP | 含まれる役 |
|---:|---|
| 2 | ノーペア, Aハイ, Kハイ, ロー・ポケットペア |
| 3 | アンダーペア, サードペア |
| 5 | セカンドペア |
| 7 | トップペア, オーバーペア |
| 8 | セット, トリップス |
| 9 | ツーペア, フラッシュ, ストレート, フルハウス, クアッズ |

### DV テーブル — 4 段階

| DP | ドロー種別 |
|---:|---|
| 0 | ドローなし, BDFD |
| 1 | ガットショット |
| 2 | OESD, フラッシュドロー |
| 3 | コンボドロー |

**TV バンド (5 区分)**:

| バンド | TV 範囲 | 直感的意味 |
|---|---:|---|
| air | 0-2 | 役なし / ほぼ改善なし |
| weak | 3-4 | 弱ペア / gutshot 止まり |
| mid | 5-6 | 中程度のペア / 強ドロー |
| strong | 7-8 | トップペア / セット |
| nut | 9+ | 2 ペア以上の怪物 |

**低_pair 注意**: MV=2 に分類されるが、context 共通で -10pt 追加補正が入ります。

## A モデル — 25 セル表

### 5 context × 5 band の bet 頻度 (≥50% ならベット推奨)

| Context | エアー | 弱ペア | 中ペア | 強ペア | ナッツ |
|---|:-:|:-:|:-:|:-:|:-:|
| Cash 100bb | 45% | 40% | 40% | 60% | 60% |
| MTT 25-50bb | 40% | 30% | 35% | 60% | 75% |
| MTT 100-200bb | 40% | 40% | 40% | 60% | 60% |
| 3-bet pot IP | 45% | 50% | 60% | 70% | 60% |
| Turn 2nd barrel | 5% | 5% | 10% | 30% | 40% |

**例外**: `low_pair` -10pt (context 共通)

## D モデル (cash 版) — cash 100bb continue freq 表

### D モデル MV 別 continue freq (全 4 context)

### DCBS HP 別 base continue freq

| HP | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---:|---:|---:|---:|---:|
| 2 | 67% | 54% | 28% | 40% |
| 3 | 98% | 95% | 84% | 85% |
| 5 | 99% | 96% | 87% | 98% |
| 7 | 100% | 100% | 98% | 100% |
| 8 | 100% | 100% | 100% | 100% |
| 9 | 100% | 100% | 100% | 100% |

### DCBS Kicker offset (HP=2 内の細分化)

| Hand | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---|---:|---:|---:|---:|
| Aハイ | +10pt | +17pt | +5pt | +5pt |
| Kハイ | +1pt | +6pt | +5pt | +0pt |
| ノーペア | -12pt | -13pt | +0pt | -3pt |
| ロー・ポケットペア | +0pt | -10pt | -10pt | -2pt |

## ハンドカテゴリ (旧 5 軸モデル 参考)

### ハンドカテゴリ — slowplay / trash / premium / default

| カテゴリ | 含まれる役 |
|---|---|
| slowplay | ツーペア, フラッシュ, ストレート, セット, トリップス, フルハウス, クアッズ |
| trash | ロー・ポケットペア |
| premium | アンダーペア, オーバーペア |
| default | ノーペア, Aハイ, Kハイ, サードペア, セカンドペア, トップペア |

## 暗算フロー 6 ステップ (攻撃側 — A モデル)

```
[A モデル — 暗算フロー]

Step 1: MV 確認
  hand type → MV テーブル → MV 値 (2/3/5/7/8/9)

Step 2: DV 確認
  draw type → DV テーブル → DV 値 (0/1/2/3)

Step 3: TV 計算
  TV = MV + DV

Step 4: TV バンド判定
  0-2 → air / 3-4 → weak / 5-6 → mid / 7-8 → strong / 9+ → nut

Step 5: context 確認 + 25 セル表参照
  cash / mtt_short / mtt_deep / 3bp / turn × band → freq

Step 6: 例外補正 → 判断
  low_pair: freq -10pt
  pos_lift: SB -8pt / CO/HJ +10pt
  freq ≥ 50% → bet / freq < 50% → check
```

**所要時間**: 慣れると 5-7 秒で完了します。

## 暗算フロー 3-5 ステップ (守備側 — D モデル (cash 版))

```
[D モデル (cash 版) — 暗算フロー]

Step 1: MV 確認
  hand type → MV テーブル → MV 値

Step 2: context 確認
  cash 100bb が Vol2 の主役

Step 3: base continue freq 参照
  D モデル_BASE[cash_100bb][MV] → base freq

Step 4: kicker offset (MV=2 のみ)
  ace_high +5 / king_high 0 / no_made_hand -3 / low_pair -2
  MV ≥ 3 なら offset = 0

Step 5: 判断
  continue_freq ≥ 50% → call (ときに CR)
  continue_freq < 50% → fold
```

**所要時間**: 3-5 秒で完了します。

## 例外ルール 3 つ

A モデルの精度が特に低下するケース (WRMSE 20%+) と対処法を示します。

**例外 1: 型6 ボード (ペア高ボード)**
ペアのランクが Q 以上のボード (AA7, KK3 等) では、IP のナッツアドバンテージが大きく、A モデルが underestimate します。
対処: 信頼度 1 段 UP として freq を +5pt 目安で加算します。

**例外 2: モノトーン (3 枚同スーツ) ボード**
3 枚が同スーツのフロップ (A♥Q♥9♥ 等) では、フラッシュの保有率が全体の判断を支配します。
TV バンドはフラッシュの保有を考慮しないため、精度が大きく下がります。
対処: 信頼度 1 段 DOWN として freq を -5-10pt 目安で減算します。

**例外 3: ストレート / フラッシュ完成ターン**
ターンカードがストレートまたはフラッシュを完成させた場合、BBのコネクターやスーテッドが完成します。
turn context の WRMSE は通常 ~20% ですが、完成ターンでは 25-28% に拡大します。
対処: strong / nut バンドでも -10pt 追加で考え、スポット判断を優先します。

## 補正値クイックリファレンス

| 補正種別 | 値 | 適用条件 |
|---|---:|---|
| low_pair offset | -10pt | hand = low_pair (常時) |
| pos_lift SB | -8pt | SB から cbet |
| pos_lift BTN | 0pt | 基準 (補正なし) |
| pos_lift CO/HJ | +10pt | ワイドレンジ open 後 |
| ターン α シフト | -35pt 相当 | context を "turn" に変更 |
| 型6 高ペア | +5pt (目安) | ペア rank ≥ Q |
| モノトーン | -5 to -10pt | 3 枚同スーツ |
| 完成ターン | -10pt | フラッシュ / ストレート完成 |

**Vol2 スコープ外の参照先**:
- 13 context の詳細: Vol3 (旧 5 軸モデル) を参照
- MTT depth 別 D モデル (4 context): Vol3 (D モデル) を参照
- プリフロップ判断 (openレンジ・3bet等): Vol1 を参照
- エクスプロイト補正 (相手タイプ別): Vol5 を参照
