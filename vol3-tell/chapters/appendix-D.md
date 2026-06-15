---
chapter: "appendix-D"
title: "付録D　参考文献・推薦図書"
section: "付録"
target_kchar: 4
status: draft
---

# 付録D　参考文献・推薦図書

本書執筆の元になった文献・参考資料の一覧です。

---

## 1. ポーカー戦略の古典

### Bill Chen & Jerrod Ankenman『The Mathematics of Poker』(2006)

数学的アプローチによるポーカー戦略の古典です。本シリーズの「Chen Formula」(プリフロップスコア式の原型) の源流になっています。

### David Sklansky & Mason Malmuth『Hold'em Poker for Advanced Players』(1988)

ハンドグループ分類の決定版です。本書のタイプ分類 5 軸はこの体系の現代的な発展といえます。

### Matthew Janda『Applications of No-Limit Hold'em』(2013)

レンジ思考の現代版です。フロップ・ターン・リバーのレンジ構築理論がまとめられています。

---

## 2. テル・心理学

### Mike Caro『Caro's Book of Poker Tells』(1984)

身体テル研究の古典です。「Caro の法則」(弱い時は強そうに、強い時は弱そうに) という考え方を確立しました。第 3 章で批判的に引用しています。

### Joe Navarro『Read 'Em and Reap』(2006)

元 FBI 行動分析官による非言語コミュニケーション研究です。リラックス vs 緊張の見極めを体系化しています。

### Zachary Elwood『Verbal Poker Tells』(2014)

会話テル研究の決定版です。直接発言・間接発言・静寂と饒舌の対比を分類しています。第 3 章で参照しています。

### Alan Schoonmaker『Your Worst Poker Enemy』(2007)

心理学者によるポーカー心理学です。タイプ分類とプレイヤー心理の関係が整理されています。

### Tommy Angelo『Elements of Poker』(2007)

メンタルゲームの古典です。「タイプは固定ではない」「チルト管理」といった概念を確立しています。

---

## 3. GTO / モダンポーカー理論

### Michael Acevedo『Modern Poker Theory』(2019)

ソルバー時代の体系書です。MATCHA Framework (Vol2) の理論的なバックボーンになっています。

### GTO ソルバー (オンラインソルバー)

本書のデータ源です。公開ブログ "The Five Imbalances of Exploitative Poker" は本書 第 5 章のフレームワークの基礎になっています。
- URL: https://blog.gtowizard.com/the-five-imbalances-of-exploitative-poker/

### PIOSolver / GTO+ (ソルバーソフトウェア)

実測ベンチマーク用のツールです。Vol2 の MATCHA Score 公式の検証で使用しています。

---

## 4. ライブポーカー実戦

### Phil Hellmuth『Play Poker Like the Pros』(2003)

タイプ別対応のライブ実戦解説です。動物に例えたタイプ分類 (Mouse, Elephant, Eagle, Lion, Jackal) は本書 5 タイプ分類の影響源になっています。

### Daniel Negreanu『Power Hold'em Strategy』(2008)

ライブでの観察技術についてまとめた本です。「Small Ball」戦略 (ポットを小さく保つ) は本書 第 10 章 (vs TAG) に反映しています。

### Doyle Brunson『Super/System 2』(2004)

ライブの古典です。心理戦・席選びの原理がまとめられています。

---

## 5. シリーズ内参照

### 『迷わないポーカー Vol1』(MATCHA Formula)

プリフロップ完全版です。Score 式・T_open / T_3bet 閾値の SSOT (唯一の情報源) としての役割を果たしています。Cash + MTT (ICM/PKO 含む) を統合しています。

### 『迷わないポーカー Vol2』(MATCHA Framework)

ポストフロップ完全版です。MATCHA Score 公式・5 判定軸・12 cells grid・3 補正の SSOT としての役割を果たしています。Cash 100bb + MTT chipEV (25-200bb) を統合しています。

### MATCHA シリーズ用語集

HTML 公開版があります: https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b

---

## 6. オンラインリソース

### Run It Once Training (旧)

Phil Galfond による教育コンテンツです。LAG vs TAG の境界判定の参考になります。

### Upswing Poker

Doug Polk / Ryan Fee による教育プログラムです。タイプ別 frequency の数値根拠を提供しています。

### TwoPlusTwo Forums

歴史的なポーカー戦略フォーラムです。ライブテル・タイプ分類の議論が蓄積されています。

### Reddit r/poker

現代のオンライン議論コミュニティです。HUD 設定・タイプ分布の参考になります。

---

## 7. 本シリーズの位置づけ

本書 (Vol3 MATCHA Exploits) は、以下の系譜に連なっています：

```
Bill Chen (2000s)         — ハンド数値化
    ↓
Sklansky-Malmuth (1988)   — チャンキング思考
    ↓
Matthew Janda (2013)      — レンジ思考
    ↓
Michael Acevedo (2019)    — ソルバー時代の体系
    ↓
本シリーズ (2026)         — 暗算公式 + 5 軸 + タイプ別歪め
```

上記の理論を「初心者が暗算で回せる形」「タイプ別に判定軸を歪める形」にアップデートしたものが MATCHA シリーズです。

---

## 8. 著作権と引用方針

本書中のデータ・アルゴリズムは GTO ソルバー / PIOSolver の出力を元に独自に整理したものです。具体的な solve 数値は本シリーズが集約しています。

引用文献の主張・データは原典の権利者に帰属します。商用利用や転載の際は原典の確認をしてください。

---

> **ここまで読んでいただきありがとうございました。**
> **MATCHA Exploits の旅は、本書を閉じた瞬間から始まります。**

---
