# 第 29 章　マルチウェイ (3+ way) — 公式の前提崩れ ★Vol3 連携

> **本章は定性記述のみです**。 MW の詳細は Vol3 (MATCHA Exploits) ch16 で扱います。

## 22.1 公式の単独 villain 前提

MATCHA Score は **hero vs 1 villain** の構造で最適化されています。 これが 3+way
(マルチウェイ、 MW) では大きく崩れてしまいます:

- **fold equity の急減**: 全員が fold する確率は (1 − f)^n で n が増えるほど低下します
- **range の overlap**: 複数 villain がそれぞれ独立 range を持つため hero の equity 低下します
- **bluff range の機能不全**: bluff してもどこかで call されるため効きにくくなります

## 22.2 MW での MATCHA Score の限界

MW (3+ way) で MATCHA Score をそのまま使うと、以下のような問題が生じます:

- **bluff frequency 過剰** → EV− になりやすいです
- **薄い value bet** → multiple caller では勝てません
- **強気の cbet** → range 全体で −EV になる傾向です

→ MW では **公式値を強制下方修正** するか、 そもそも別ルール (MW 5 原則) を使うことをおすすめします。

## 22.3 MW 5 原則 (Vol3 詳細)

Vol3 (MATCHA Exploits) ch16 で扱う MW 5 原則 (要点のみをご紹介します):

### 原則 1: ブラフ生成禁止

3+ way では fold equity 急減 (1 − f)^n のため、 ブラフ range を作らないことが重要です。

### 原則 2: バリュー集中

薄バリューは控え、 強 hand 主体 (TP+ 以上) に絞ることをおすすめします。 アンダーペアは showdown 寄りで進めましょう。

### 原則 3: ハンド選好変更

SC・小ペアを優遇します (multiway で implied odds 大)、 broadway off (KQo 等) は相対的に弱体化します。

### 原則 4: T_open 引き上げ (+3〜+12 程度)

プリフロップで MW を予想したら open range を tight 化しましょう:

- HU 想定 T_open 22 → MW (3 way 想定) T_open 28
- 効果: そもそも MW を回避できます

### 原則 5: アイソレート優先

squeeze で先に 1 vs 1 に戻せれば公式 +shift が復活します。 MW を避ける動きを心がけましょう。

## 22.4 short stack 混在時の effective SPR 管理

MW で short stack 混在する場合 (例: BTN 100bb、 SB 15bb、 BB 100bb の 3way) を考えてみましょう:

- vs short stack の effective SPR = 1.5 (短スタック側)
- vs BB の effective SPR = 17 (deep stack 側)

→ **villain ごとに effective SPR が異なる** ため、 short side に対しては jam-or-fold、
deep side に対しては slowplay という **真逆の戦略** が同時に必要になります。

これは MATCHA Score (HU 前提) では表現不可能です。 MW では「強い手は short side jam、
deep side slowplay」 という分離行動が GTO 推奨されます。

## 22.5 MW での MATCHA Score 適用上の注意

緊急時に MW で MATCHA Score を使う場合は、以下の調整をしましょう:

1. **T_call を +10〜+15 引き上げます** (14 → 24〜29)
2. **bluff を一切やりません** (Score < T_raise でも raise しない)
3. **2P+ 以外の wet board → fold ベースにします**
4. **オープナー補正 (CO/HJ open river)** で形勢を 1 段階下げます

## 22.6 詳細は Vol3 へ

MW の data 駆動 strategy は **Vol3 (MATCHA Exploits) ch16** で詳述します。
本書 (Vol2) では「MW では公式が崩れる」 という事実のみを示し、 詳細は姉妹巻に
お任せしています。

Vol3 (MATCHA Exploits) ch16 では:
- MW 5 原則の data 裏付け
- player type (ニット / TAG / LAG / CS / マニアック) 別の MW exploit
- short stack 混在時の position 別 SPR 管理

などを扱います。

## Cash/MTT note

MW (3+ way) 頻度は Cash と MTT で **テーブルサイズに依存します** (詳細は第 25 章): 6-max=25% / 8-max=35% / 9-max=45%。 MW 5 原則は両者共通適用です。 Cash 9-max LIVE と MTT 9-max early が最頻発場面となります。

## この章で覚える項目 (5 items、 すべて定性)

1. MW (3+ way) では fold equity 急減
2. MW 5 原則: bluff 禁止 / value 集中 / hand 選好変更 / T_open 引上げ / アイソレート
3. short stack 混在で villain ごとに effective SPR が異なる
4. MATCHA Score 単独 villain 前提が崩れる
5. 詳細は Vol3 ch16 で対応
