# 巻4 固有の執筆方針

## 対象読者

巻2 (フロップ基礎) と巻3 (フロップ応用) を読了した中級者。
巻2 の BoardScore・HandScore・CBet統合式を既知として扱う。

## 主要コンセプト

### バレルスコア — ダブルバレル暗算式

ターン CBet 判断を「FlopType 係数 + TurnCard 係数」の足し算で決定する簡易フロー。
GTO ソルバー実測 270 シナリオに基づいて係数を設定。全 17 セルで GTO 🟢/🟡 分類と一致。

```
バレルスコア = FlopType 係数 + TurnCard 係数
FlopType: ドライ=8, セミ=6, スーテッド=4, コネクテッド=3
TurnCard: ペア=4, OC=3, ブランク=2, フラッシュ=1, コネクター=0
閾値: バレルスコア ≥ 7 → 🟢, バレルスコア < 7 → 🟡
```

### ターンカード 5 分類

1. **オーバーカード** (A/K/Q 等、フロップ最高位より高い)
2. **ブランク** (絡まない低〜中ランクカード)
3. **ペア** (フロップカードと同ランク)
4. **フラッシュ** (3 枚目の同スートで flush draw 発生/完成)
5. **コネクター** (ストレート完成/強化)

### Alpha 式 (リバー価値/ブラフ配分)

Alpha = 1/(1 + ポットオッズ) を用いた最適ブラフ頻度の計算式。
巻2 の MDF フレームワークを拡張して適用。

## 章立て

```
volume4-draft/chapters/
  01-turn-overview.md           第1章  ターンの位置づけ ✓
  02-turn-card-categories.md    第2章  ターンカードの5分類 ✓ (270シナリオ実測)
  03-range-transition.md        第3章  フロップ→ターンのレンジ遷移 ✓
  04-double-barrel.md           第4章  ダブルバレルの論理 ✓ (バレルスコア実測)
  05-turn-defense.md            第5章  ターンディフェンス ✓
  06-turn-checkback.md          第6章  チェックバック・プロービング ✓
  07-turn-bet-size.md           第7章  ターン専用ベットサイズ ✓ (10シナリオ実測)
  08-turn-problems.md           第8章  ターン実戦例 20 問 ✓
  09-river-overview.md          第9章  リバーの特殊性 ✓
  10-river-vb-ratio.md          第10章 バリュー/ブラフ配分 ✓
  11-blocker-theory.md          第11章 ブロッカー論 ✓
  12-river-checkback.md         第12章 チェックビハインドとチェックレイズ ✓
  13-river-overbet.md           第13章 リバーオーバーベット ✓
  14-river-vs-checkraise.md     第14章 リバー vs チェックレイズ ✓
  15-river-mdf.md               第15章 リバー MDF の実用的扱い ✓
  16-river-problems.md          第16章 リバー実戦例 20 問 ✓
  17-hand-review.md             第17章 ソルバーによるハンドレビュー ✓
  18-multistreet-integration.md 第18章 マルチストリート統合判断 ✓
  19-combined-drills.md         第19章 総合ドリル 50 問 ✓
  20-appendix.md                付録 ✓
  21-three-bet-pot.md           第21章 3bet ポットのターン・リバー ✓
  22-oop-turn-checkraise.md     第22章 OOP ターンチェックレイズ ✓
  23-turn-overbet.md            第23章 ターンオーバーベット ✓
  24-pot-commitment.md          第24章 ポットコミットメントとオールイン判断 ✓
  25-sb-vs-bb.md                第25章 SB vs BB のターン・リバー ✓
  26-multiway.md                第26章 マルチウェイポットのターン・リバー ✓
```

全26章執筆完了 (2026-04-24)。GTO データ: 270ターンCBetシナリオ + 10ベットサイズシナリオ。

## GTO データの扱い

- 出典: TexasSolver (C++ CFR ソルバー) 実測
- 表記: 本文では「GTO ソルバー実測」と記す (ソルバー名は付録 G に記載)
- 精度: exploitability < 0.5% (十分な収束)
- シナリオ: 270 ターン CBet シナリオ (30 フロップ × 9 ターンカード)
- 生データ: `knowledges/volume4/results/102/`

## 数値の一貫性

- 巻2 との接続: BoardScore 6 以上 → 高 CBet ボード
- ターン CBet の基準:
  - ≥ 70%: 積極的ダブルバレル推奨
  - 40-70%: ハンドクラス依存
  - < 40%: チェックバック基本
- 100BB, 6-max キャッシュゲームを想定

## 文体

巻2/3 のですます調を継続。コラム形式の【GTO とのズレ】を各章に挿入。
