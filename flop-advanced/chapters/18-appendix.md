# 付録

<!-- textlint-disable -->

<!-- markdownlint-disable MD036 MD040 MD056 MD060 -->

本書の本文で扱った内容を、実戦時に即参照できる形にまとめた資料集。

---

## 付録 A　参考文献・謝辞

### 書籍 (古典)

- **David Sklansky** *The Theory of Poker* (Two Plus Two, 1987)
  - Fundamental Theorem of Pokerの出典
- **Dan Harrington** *Harrington on Hold'em Vol 1-3* (Two Plus Two, 2004-2006)
  - メタゲーム、レベル思考の基礎
- **Matt Janda** *Applications of No-Limit Hold'em* (DailyVariance, 2013)
  - エクスプロイトの枠組み、レンジ計算
- **Phil Galfond** *GFX: Game Theory Optimal Fundamentals* (Run It Once, 2018)
  - 動的頻度調整の理論

### 書籍 (現代)

- **Bill Chen & Jerrod Ankenman** *The Mathematics of Poker* (Conjelco, 2006)
  - コンボ計算・確率論の基礎
- **Michael Acevedo** *Modern Poker Theory* (D&B Publishing, 2019)
  - レンジ遷移、エクイティ分布論
- **Jonathan Little** *Excelling at No-Limit Hold'em* (D&B Publishing, 2015)
  - 境界判断の実戦例
- **Zachary Elwood** *Reading Poker Tells* (Via Regia Press, 2012)
  - ライブテルの現代的整理
- **Joe Navarro** *Read 'Em and Reap* (Collins, 2006)
  - 元FBI捜査官によるボディランゲージ論

### ウェブ / ツール

- **GTO Wizard** — <https://gtowizard.com/>（主要データ出典）
- **Upswing Poker Blog** — <https://upswingpoker.com/blog/>
- **Run It Once Training** — <https://www.runitonce.com/>
- **PokerCoaching.com (Jonathan Little)** — <https://pokercoaching.com/>
- **Red Chip Poker** — <https://redchippoker.com/>

### ソフトウェア

- **PioSolver** — <https://piosolver.com/>（ソルバー、$250〜）
- **GTO Wizard** — クラウドソルバー、$99/月
- **Simple Postflop** — <http://simplepostflop.com/>（$200）
- **PokerTracker 4** — <https://www.pokertracker.com/>（HUD、$80）
- **Hand2Note** — <https://hand2note.com/>（HUD、$90）
- **Flopzilla** — <https://flopzilla.com/>（レンジ分析、$25）

### シリーズ本

- 川西智也『迷わないポーカー① プリフロップ』（2026）— 巻1
- 川西智也『迷わないポーカー② フロップ[基礎]』（2026）— 巻2
- 川西智也『迷わないポーカー③ フロップ[応用]』（2026）— 本書 （巻3）
- 川西智也『迷わないポーカー④ ターン・リバー』（執筆予定）— 巻4

### 謝辞

本書はGTO Wizardの公開データ、古典ポーカー理論、そして巻2読者からのフィードバックなしには成立しませんでした。とくに精密レンジスコアの設計には30ボードのGTO実測データが不可欠で、GTO Wizard Blogの記事群に深く感謝します。

---

## 付録 B　精密レンジスコア 完全係数表 (拡張版)

巻2付録Dの係数表をそのまま踏襲しつつ、本書の第1章で扱った根拠データを付加した完全版。

### 基本式

```
CBet% = 90 − HighCardDeficit − TextureCost − SuitPenalty − Extra
        (ペアは override、monotone は 18% 固定)
```

### HighCardDeficit 表

| トップ | 減算 | 根拠 (実測平均) |
| :---: | :---: | :---: |
| A | 0 | top=A 平均 89% |
| K | 0 | top=K 平均 84% |
| Q | 5 | top=Q 平均 75% |
| J | 35 | top=J 平均 46% |
| T | 35 | top=T 平均 40% |
| 9 | 35 | top=9 平均 40% |
| 8 以下 | 30 | top ≤8 平均 52% |

### TextureCost 表

| max_diff | top ≤ 8 | top 9 rain | top 9 2tone | top T 2tone | top T rain | top J | top Q+ |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ≥ 8 (散開) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5-7 (中程度) | 5 | 5 | 5 | 5 | 5 | 5 | 5 |
| 3-4 (2連+G) | 5 | 15 | 15 | 15 | 15 | 15 | 25 |
| ≤ 2 (連続3) | 5 | 10 | 20 | 15 | 20 | 25 | 30 |

### SuitPenalty

| スート構造 | 減算 |
| :---: | :---: |
| rainbow | 0 |
| 2-tone | 10 |
| monotone | override → 18% 固定 |

### Extra 4 ルール

| ルール | 条件 | 追加減算 | 対象ボード例 |
| :---: | --- | :---: | --- |
| E1 | mid=T かつ top≥Q かつ rainbow | -15 | KT5r, QT3r, AT2r |
| E2 | 3 枚とも T 以上 かつ 2-tone | -10 | KQTss, QJTss, AKJss |
| E3 | top=A/K/Q + mid=T + 2-tone + low<T | -15 | AT7ss, KJ4ss |
| E4 | top=Q かつ mid<T かつ 2-tone | -10 | Q83ss, Q72ss |

### Pair Override 表 (8 パターン)

| パターン | 頻度 | 根拠ボード |
| --- | :---: | --- |
| AA ペア (AA-X) | 90% | AA7, AAK |
| KK ペア (KK-X) | 85% | KK4, KK9, KKJ |
| QQ ペア (QQ-X) | 80% | QQ3, QQT |
| ミドルペア (TT-88) | 75% | TT5, 995, 883 |
| ローペア (77 以下) | 68% | 772, 665, 553 |
| A/K ハイ + ローペア (ペア ≤5) | 45% | K44, A33, K22 |
| A/K ハイ + 中ペア (ペア 6-T) | 76% | A99, K88, A88 |
| Q/J ハイ + ローペア | 55% | Q33, J55 |

### Ablation 分析 (Python 再現)

```python
# scripts/range_score.py 参照
# 30 ボードの検証結果:
# 完全 精密レンジスコア: R² = 0.914, MAE = 5.27
# − SuitPenalty: R² = 0.651 (-0.263)
# − Pair override: R² = 0.764 (-0.150)
# − Extra: R² = 0.840 (-0.074)
```

### 残存外れ値

**965r のみ**（|残差| ≥ 15のボード）:。

- GTO実測： 60%
- 精密レンジスコア予測： 40%
- 残差： +20%
- 原因： 9-6-5のmiddle=6は通常のロー連続と異なる特殊ドライ

v6（次回改訂）で追加ルール検討予定。

---

## 付録 C　17 型ボード判定早見表

第4章の17型と、代表ボードの一覧。

| 型 | 条件 | 代表例 | 平均頻度 |
| :---: | --- | --- | :---: |
| 1a | A/K/Q + 散開 + 2-tone | Q83ss | 55% |
| 1b | A/K/Q + 散開 + rainbow | K72r, A72r, Q53r | 87% |
| 2a | A/K/Q + max_diff 5-7 + 2-tone | AT7ss | 60% |
| 2c | 全 3 枚≥T + 2-tone | KQTss, QJTss | 35% |
| 2e | A/K/Q + mid=T + rainbow | KT5r, QT3r | 70% |
| 2f | A/K/Q + max_diff ≤4 + rainbow | QJ9r | 50% |
| 3c | J 以下 + max_diff 5-7 + 2-tone | J84ss | 50% |
| 3d | J 以下 + max_diff 5-7 + rainbow | J75r | 40% |
| 4a | J 以下 T トップ + 連続 + 2-tone | JT9ss, JT8ss, T98ss | 23-30% |
| 4b | J 以下 9- トップ + 連続 + 2-tone | 987ss | 25-30% |
| 4c | J 以下 T トップ + 連続 + rainbow | T87r, T98r | 40-45% |
| 4d | J 以下 9- トップ + 連続 + rainbow | 876r, 965r, 632r | 48-62% |
| 5a | 3 枚モノトーン + broadway | AKQmono | 15% |
| 5b | 3 枚モノトーン + low | 987mono | 20% |
| 6a | AA ペア | AA7, AAK | 90% |
| 6b | KK ペア | KK4, KK9 | 85% |
| 6c | QQ ペア | QQ3, QQT | 80% |
| 6d | 77 以下ペア | 772 | 70% |
| 7a | A/K ハイ + ペア≤7 | K44 | 43% |
| 7b | A/K ハイ + ペア 8-T | A99 | 78% |

### 7 型 → 17 型マッピング (巻2 との対応)

```
巻2 型1 (ハイ×ドライ) → 1a, 1b, 2e
巻2 型2 (ハイ×ウェット) → 2a, 2c, 2f
巻2 型3 (ロー×ドライ) → 3d
巻2 型4 (ロー×ウェット) → 3c, 4a, 4b, 4c, 4d
巻2 型5 (モノトーン) → 5a, 5b
巻2 型6 (ペア+高キッカー) → 6a
巻2 型7 (ペア、そのほか) → 6d, 7a, 7b
```

---

## 付録 D　HUD 統計詳細表

第10章のE補正の根拠となるHUD統計の精密表。

### 基本 7 指標と標準値 (6-max 100BB)

| 指標 | 標準値 | Nit | TAG | LAG | Fish |
| :---: | :---: | :---: | :---: | :---: | :---: |
| VPIP | 22-25% | ≤16 | 18-25 | 28-35 | 35+ |
| PFR | 18-22% | ≤13 | 15-22 | 22-32 | ≤15 |
| AFq | 45% | ≤30 | 40-55 | 55-75 | ≤25 |
| 3Bet% | 6-9% | ≤3 | 5-9 | 8-13 | ≤2 |
| CBet% (IP) | 55-65% | 45-55 | 55-65 | 65-80 | 45-60 |
| Fold vs CB% | 55-65% | 70+ | 55-65 | 35-50 | 40-55 |
| Check-Raise% | 8-12% | ≤5 | 8-12 | 12-18 | ≤3 |

### E 補正式 (再掲)

```
E = V_score × 0.4 + P_score × 0.4 + A_score × 0.2

V_score = (相手 VPIP − 22) / 10
P_score = (相手 PFR − 18) / 10
A_score = (相手 AFq − 45) / 20

E の範囲: -1.5 〜 +1.5
```

### サンプル別の信頼性

```
< 200 ハンド: 主要 3 指標は使わない、標準値と仮定
200-500: VPIP, PFR のみ信頼
500-1000: 基本 3 指標を採用、Fold vs CB も参照
1000+: 全指標を使ったエクスプロイト
```

### 相手タイプ 5 分類詳細 (境界値を含む)

```
Nit:        VPIP ≤16, PFR ≤13, AFq ≤30
  サブ分類: Super Nit (VPIP ≤12), Regular Nit (VPIP 13-16)

TAG:        VPIP 18-25, PFR 15-22, AFq 40-55
  サブ分類: Tight TAG (VPIP 18-21), Standard TAG (VPIP 22-25)

LAG:        VPIP 28-35, PFR 22-32, AFq 55-75
  サブ分類: Loose LAG (VPIP 32-35), Standard LAG (VPIP 28-31)

Fish:       VPIP 35+, PFR ≤15, AFq ≤25
  サブ分類: Passive Fish (AFq ≤20), Calling Station (AFq ≤15)

TAGGY (境界): VPIP 17, VPIP 26-27 など
  判定: CBet% と 3Bet% で微調整
```

---

## 付録 E　プレイヤータイプ別 搾取チートシート

第11章の32例を要約した1ページサマリー。

### Nit 相手 (E ≈ -1.0)

```
基本方針: ブラフ増、過剰フォールド、3bet ブラフ活用

ブラフ頻度:
  CBet ブラフ: 50 → 70-80% (特に 33% サイズ)
  3bet ブラフ: 5 → 10-15%

ディフェンス:
  相手の 33% CBet: 後手下限ライン 通り (75%)
  相手の 75% CBet: ほぼフォールド (後手下限 無視)
  相手の オーバーベット: 完全フォールド (TPTK でも)

サイズ:
  自分のバリュー: 標準 (33-75%)
  自分のブラフ: 小-中 (33-50%)、大サイズ無駄
```

### TAG 相手 (E ≈ 0)

```
基本方針: GTO 近い対応、境界で R2 ランダム化、メタゲーム活用

ブラフ頻度:
  CBet ブラフ: 標準 (40-50%)
  3bet ブラフ: 標準 (5-8%)

ディフェンス:
  後手下限ライン 通り、サイズ別に計算
  境界ハンドで R2 適用

サイズ:
  標準、サイズ 2 択 (R4) を使う
```

### LAG 相手 (E ≈ +1.0)

```
基本方針: ブラフ減、ブラフキャッチ増、チェックレイズ誘引

ブラフ頻度:
  CBet ブラフ: 50 → 20-30% (LAG はコール多)
  3bet ブラフ: 5 → 3-5% (コールバックされる)

ディフェンス:
  相手の 33% CBet: 広くコール (後手下限確率 +10%)
  相手の 75% CBet: 後手下限確率 +10%、ブラフキャッチ積極
  相手のトリプルバレル: コールダウン

サイズ:
  バリュー薄く (LAG はコール前提)
  サイズ大きく (LAG はコールする)
```

### Fish 相手 (E varies)

```
基本方針: ブラフ封印、バリュー厚、広くバリューベット

ブラフ頻度:
  CBet ブラフ: 50 → 10% (Fish は降りない)
  3bet ブラフ: 5 → 0% (完全封印)

ディフェンス:
  相手のコール: 自分のバリューを信じる
  相手のレイズ: ほぼナッツ確定、フォールド

サイズ:
  バリュー: 75% 以上、3 ストリートフル
  薄いバリュー: TP 弱キッカーでも打つ
  Fish は ShowDown Value を軽視 → 広く バリュー
```

---

## 付録 F　メタゲーム理論の古典引用

### Sklansky の Fundamental Theorem of Poker

> 「プレイヤーは、相手のハンドを知っているかのように打つべき。そこから外れるほど、相手は利益を得る」

**解釈**: 相手のレンジを精密に読めば読むほど、自分のEVが上がる。

### Harrington のレベル思考

> 「レベル 1: 自分のハンド。レベル 2: 相手のハンド。レベル 3: 相手が自分のハンドをどう読むか。レベル 4 以上は通常過剰」

**解釈**: 対戦相手より1レベル上を目指す原則。レベル4+ は自滅の元。

### Janda の搾取枠組み

> 「GTO は防御戦略。搾取は攻撃戦略。相手の弱点に集中して攻める」

**解釈**:「すべての弱点を攻めない」。最大の弱点を集中的に搾取。

### Galfond の動的頻度

> 「戦略は静的ではない。各ハンドで微妙に調整するのが上級者」

**解釈**: メタゲームの核心。イメージ構築と利用の循環。

### Chen & Ankenman のコンボ論

> 「ポーカーは情報不完全ゲーム。確率論で最適化できる部分と、できない部分を区別せよ」

**解釈**: コンボ計算とブロッカー効果は数学的に解ける。メタゲームは数学を超える領域。

---

## 付録 G　よくある誤解 Q&A 上級編

### Q1: 精密レンジスコア の係数は全部覚えるべきか

**A**: 実戦では不要。5つの重要型（型2c、型2e、型4d、型7a、型7b）だけ覚えればR² 0.90相当の精度。残りは巻2の7型で近似可能。

### Q2: 混合戦略 R1-R6 はすべて同時に使う

**A**: いいえ。R1は常時、R2は境界セルのみ、R3は常時、R4はベット確定時、R5は高頻度×強、R6はディフェンス時。適用範囲が分かれている。

### Q3: メタゲームは全相手に使える

**A**: いいえ。レベル2以上の相手（TAG、上級LAG）にのみ有効。Fish/Nitにはメタゲーム無意味。

### Q4: HUD なしでエクスプロイトできる

**A**: 可能だが精度が落ちる。1オービット（5-6ハンド）観察で粗いE推定、補正量は30% 減らす。

### Q5: 「搾取しすぎ」と「GTO に戻るべき」の境界は

**A**: 相手が5ハンド以上自分のブラフをコール、自分のパターンが読まれた兆候 → 即GTO復帰。

### Q6: 17 型と 7 型、どちらで運用

**A**: 巻2読者は7型で十分。NL200+ の上級者は17型で +5-10% のEV上乗せ。

### Q7: 「タイミングテル」と「物理テル」の優先度は

**A**: オンライン = タイミング主体、ライブ = 物理 + タイミング + サイズの統合。

### Q8: レベル 3 以上は本当に不要

**A**: 対プロ戦 (NL1000+) では必要。それ以下ではFPSのリスクが上回る。

### Q9: 3bet ポットでも 精密レンジスコア は使える

**A**: 使えるが、SPRが低いため **+5% の補正** を加える。4betポットは別モデル（次巻で扱う）。

### Q10: 「5 ハンドで相手タイプ判定」は本当に可能

**A**: 粗い判定のみ。正確なタイプ判定は50-100ハンド、エクスプロイト発動は200+ ハンド推奨。

---

## 付録 H　出典・再現性

### GTO データ出典

本書の検証に使用した30ボードは、GTO Wizardの公開データ（無料プランで閲覧可能）から抽出。

### 主要参考記事

- GTO Wizard Blog: *Flop Heuristics: IP C-Betting in Cash Games*
  <https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/>
- GTO Wizard Blog: *The Mechanics of C-Bet Sizing*
  <https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/>
- GTO Wizard Blog: *Blockers & Unblockers*
  <https://blog.gtowizard.com/blockers-unblockers-the-secret-to-picking-great-bluffs/>
- GTO Wizard Blog: *Principles of River Play*
  <https://blog.gtowizard.com/principles-of-river-play/>
- Upswing Poker Blog: *Exploitative Strategy*
  <https://upswingpoker.com/blog/>
- Red Chip Poker: *Player Type Exploitation*
  <https://redchippoker.com/>

### 再現スクリプト

本書のモデル（精密レンジスコア含む）はPythonスクリプトで実装。

```bash
cd poker-books/
python3 scripts/range_score.py
```

出力例：。

```
簡易レンジスコア    : R² = 0.873  MAE = 6.03  r = 0.938
精密レンジスコア: R² = 0.914  MAE = 5.27  r = 0.962
```

### 検証プロトコル

- 対象： 6-max 100BBキャッシュ、BTN vs BB SRP
- ボード数： 30（ドライ/セミウェット/ウェット/ペア/モノトーン各種）
- 実測日： 2026年
- 環境： Python 3.13、統計モジュール標準ライブラリのみ

### 次巻 (巻4) への検証拡張

巻4では100-200ボードの拡張検証を予定：。

- ターン・リバーのGTOデータ追加取得
- マルチストリートEVの定量化
- 965r問題を解くv6モデルの研究

---

## 付録 I　検証スクリプト リファレンス

### `scripts/range_score.py` の主要関数

```python
def kantan_score(ranks: list[int], suits: list[str], paired: bool) -> int:
    """簡易レンジスコア 暗算モデル (4 ステップ、10 数字)"""
    ...

def seimitsu_score(ranks: list[int], suits: list[str], paired: bool) -> int:
    """精密レンジスコア 精密モデル (4 項減算式 + Extra 4 ルール + Pair override)"""
    ...
```

### 使用例

```python
from range_score import kantan_score, seimitsu_score
from verify_flop_gto import parse_board

ranks, suits, paired = parse_board("K72r")
print(f"簡易レンジスコア: {kantan_score(ranks, suits, paired)}%")      # → 85%
print(f"精密レンジスコア: {seimitsu_score(ranks, suits, paired)}%")  # → 90%
```

### 拡張ポイント (巻4 に向けて)

```python
# 巻4 でターン対応を追加する場合:
def range_score_turn(flop_ranks, turn_card, flop_action, ...) -> int:
    """ターン CBet 頻度を予測"""
    ...

# リバー対応:
def range_score_river(flop_ranks, turn, river, history, ...) -> int:
    """リバー アクション頻度を予測"""
    ...
```

### テスト再現

```bash
# 30 ボードの全予測値を出力
python3 scripts/range_score.py

# 特定ボードのモデル比較
python3 -c "
from scripts.range_score import kantan_score, seimitsu_score
from scripts.verify_flop_gto import parse_board
for board in ['K72r', 'A82r', '965r', 'KQTss']:
    r, s, p = parse_board(board)
    print(f'{board}: 簡易レンジスコア={kantan_score(r,s,p)}%, 精密レンジスコア={seimitsu_score(r,s,p)}%')
"
```

---

## 最後に

本書（巻3）は、**エクスプロイト上級** と **レンジ推定** の体系化を試みました。巻2で培ったGTO基礎の上に、相手を読み、搾取し、メタゲームに持ち込む道具を提供します。

次巻 **巻4『ターン・リバー編 (仮題)』** で、フロップ以降のストリート判断を扱います。本書の精密レンジスコア + レンジ推定 + 搾取戦略を、ターン・リバーの多ストリート思考に拡張していきます。

お読みいただきありがとうございました。実戦での上達を願っています。

**著者**
