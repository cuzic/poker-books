# 第 27 章　ICM 入門 — chipEV と $EV のズレ ★定性

> **本章は定性記述のみ**です。 ICM/PKO の postflop GTO data は データ取得 tier
> 制限で取得不能なため、 数値モデル化は将来 Vol2.5 (ICM/PKO 別冊) で対応予定です。
> 本章では MATCHA Score を ICM 局面で使う際の **方針** のみをお示しします。

## 20.1 chipEV と $EV の違い

本書のメイン公式 MATCHA Score は **chipEV** ベースで最適化されています。

- **chipEV**: チップ単位の期待値 (1 チップ = 1 単位として計算)
- **$EV** ($/dollar EV): 実払戻し ($) ベースの期待値

Cash と MTT chipEV (25/50/100/200bb) では両者が一致するため、 MATCHA Score はそのまま適用できます。 一方 **ICM ステージ (賞金圏直前以降)** では両者に大きな乖離が生じ、 chipEV ベースの判断が損失を生むことがあります。

## 20.2 リスクプレミアム

「リスクプレミアム」 (risk premium) とは次のような現象です：

- 同 chipEV ハンドが ICM ステージで $EV− になる現象
- 短スタックは「fold すると一気に減るマージン」 が薄く、 jam を厳しめに判断する必要があります
- チップリーダーは「bust リスクなし」 で wide pressure が可能です

### 数値感覚

| ICM ステージ | 推定リスクプレミアム |
|---|---:|
| ICM なし (chipEV) | 0% |
| FT 9-handed | 2-5% |
| FT 5-handed | 5-10% |
| FT 3-handed | 10-15% |
| バブル (賞金圏直前) | **15-25%** |
| heads-up | 5-15% |

リスクプレミアム ≈「Score の閾値を引き上げる相当量」 と考えていただけます。

## 20.3 ICM Pressure の階層

ICM Pressure (圧力) は次の階層で増加します：

1. **early-mid stage MTT** → chipEV 同等 (本書公式 そのまま)
2. **late stage MTT** → ICM 軽い (補正 +2 程度)
3. **バブル** → ICM 最大 (補正 +5〜+10)
4. **賞金圏内 FT** → ICM 強 (補正 +3〜+8)
5. **heads-up** → 軽く戻る (補正 +1〜+3)

## 20.4 MATCHA Score の ICM 修正方針 (定性)

ICM ステージで MATCHA Score を使う際の **方針** (数値は目安) をご説明します：

- **T_call を引き上げ**: 14 → 16〜20 (call wide 化抑制)
- **T_raise を引き上げ**: 43 → 45〜50 (raise tight 化)
- **大きな pot を避ける**: 4BP / vs CR は特に慎重に (bust リスク高)
- **2P+以外の overbet 受け fold 化** (bluff catch range 削減)

これらは厳密な data 駆動ではなく、 ICM 一般理論からの推定です。 実 ICM データを audit するには GTO ソルバー ICM tier (現在 取得不能) が必要になります。

## 20.5 short stack vs chip leader

ICM 局面では stack size で挙動が真逆に分かれます：

| stack 立場 | 行動方針 | Score 補正 |
|---|---|---|
| chip leader | wide pressure、 bully | T_call −3〜−5 (緩める) |
| big stack (top 3) | tight value | T_call +0〜+2 |
| mid stack | tight pressure 受け | T_call +5〜+10 (厳しめ) |
| short stack | jam-or-fold | T_call +0 (commit 状態) |

chip leader は「bust リスクなし」 で wide 行動が可能で、 mid stack は「両側に挟まれる」立場で最も tight になります。

## 20.6 なぜ ICM data モデル化が困難か

ICM の数値モデル化は将来課題 (Vol2.5) です。 主な理由は次の通りです：

1. **データ取得制限**: GTO ソルバー ICM tier は postflop tier で 403 (取得不能)
2. **context の組合せ爆発**: stack 配分 (3+ players) × payout 構造 × position
3. **stage 別の動的変化**: 同じハンドが stage 進行で挙動変化
4. **データ scarcity**: chipEV データほど豊富にない

→ 当面は **MATCHA Score + ICM 補正 (定性)** で運用いただく形になります。

## Cash/MTT note

ICM は **MTT 専用概念** です (Cash は chipEV 等価)。 本章補正 (+5〜+10) は MTT 後期/バブル/FT 専用です。 Cash には ICM 補正一切不要です。

## この章で覚える項目 (4 items、 すべて定性)

1. chipEV (本書前提) と $EV (実払戻し) は ICM で乖離
2. リスクプレミアム = Score 閾値の引き上げ相当量
3. バブルが ICM 最大 (補正 +5〜+10)
4. ICM 数値モデル化は将来 Vol2.5 で対応予定
