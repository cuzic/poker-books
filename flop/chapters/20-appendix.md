# 付録

<!-- markdownlint-disable MD036 MD056 MD060 -->
<!-- textlint-disable preset-ja-technical-writing/no-exclamation-question-mark -->
<!-- textlint-disable preset-ja-technical-writing/no-mix-dearu-desumasu -->
<!-- textlint-disable preset-ja-technical-writing/no-doubled-joshi -->
<!-- textlint-disable preset-ja-technical-writing/ja-no-successive-word -->

本書の本文で扱った内容を、実戦時に即参照できる形にまとめた資料集です。

---

## 付録A　参考文献・謝辞

### 書籍

- **Bill Chen & Jerrod Ankenman** *The Mathematics of Poker* (Conjelco, 2006)
- **Matt Janda** *Applications of No-Limit Hold'em* (DailyVariance, 2013)
- **Michael Acevedo** *Modern Poker Theory* (D&B Publishing, 2019)
- **Jonathan Little** *Excelling at No-Limit Hold'em* (D&B Publishing, 2015)
- **Phil Gordon** *Phil Gordon's Little Green Book* (Simon Spotlight, 2005)

### ウェブ / ツール

- **GTO Wizard** — <https://gtowizard.com/>（主要データ出典、有料プラン推奨）
- **Upswing Poker Blog** — <https://upswingpoker.com/blog/>
- **SplitSuit Poker (Gareth James)** — <https://www.splitsuit.com/>
- **PokerCoaching.com (Jonathan Little)** — <https://pokercoaching.com/>
- **Run It Once Training** — <https://www.runitonce.com/>
- **The Poker Bank** — <https://www.thepokerbank.com/>

### 前作（本シリーズ）

- 川西智也『プリフロップは計算で勝つ』（2026）
  - <https://cuzic.github.io/poker-books/preflop/>

### 次作（予定）

- 川西智也『ポーカー・ポストフロップ完全攻略』（仮題、執筆予定）
  - 本書の上級編（BDM v5、混合戦略、ターン、リバー、GTO統合）を収録

### 謝辞

本書はこれらの公開データと先行書籍の蓄積なしには成立しえません。とくにGTO Wizardの膨大な分析データ、SplitSuitの分類フレームワーク、Phil Galfondのレンジ均衡論には大きな影響を受けています。

---

## 付録B　7 型判定早見表 (代表 50 ボード)

第3章で定義した7型へのボード分類を、代表50ボードで事前計算したものです。実戦で迷ったときの照合用。

### 型1: ハイ × ドライ (⚡ 全開モード)

| ボード | 判定条件 |
| --- | --- |
| K♣7♦2♠ | トップ K、max_diff=11、rainbow |
| K♣9♦4♥ | トップ K、max_diff=9、rainbow |
| K♣9♦3♣ | トップ K、max_diff=10、rainbow (wait 2-tone になる場合は型2) |
| K♦Q♠2♣ | トップ K、max_diff=11、rainbow |
| A♦K♠5♣ | トップ A、max_diff=9、rainbow |
| A♠8♥3♦ | トップ A、max_diff=11、rainbow |
| A♠8♥2♦ | トップ A、max_diff=12、rainbow |
| Q♣6♦3♠ | トップ Q、max_diff=9、rainbow |
| Q♣J♥2♦ | トップ Q、max_diff=10、rainbow (J が mid だが連続でない) |

### 型2: ハイ × ウェット (🎯 狙い撃ちモード)

| ボード | 判定条件 |
| --- | --- |
| Q♥J♥8♣ | トップ Q、2-tone (♥♥) |
| A♠8♠3♦ | トップ A、2-tone (♠♠) |
| K♠T♦5♣ | トップ K、max_diff=8、rainbow だが高ボード連続条件 (≤4かつtop≥T) に非該当 → 型1 (要注意) |
| K♣J♦9♥ | トップ K、max_diff=4、top≥T → 高ボード連続 ✓ |
| Q♣J♦9♠ | トップ Q、max_diff=3、top≥T → 高ボード連続 ✓ |
| A♥T♥3♦ | トップ A、2-tone (♥♥) |
| Q♠J♦9♣ | トップ Q、max_diff=3、高ボード連続 ✓ |
| KQTss | 全 broadway + 2-tone |
| K♠Q♦T♣ | トップ K、max_diff=3、高ボード連続 ✓ |

### 型3: ロー × ドライ (🤔 控えめモード)

| ボード | 判定条件 |
| --- | --- |
| J♠7♦2♣ | トップ J、max_diff=9、rainbow |
| T♠6♦3♣ | トップ T、max_diff=7、rainbow |
| J♦7♠5♣ | トップ J、max_diff=6、rainbow |
| J♠9♦6♥ | トップ J、max_diff=5、rainbow、高ボード連続 NG (max_diff>4) |
| 8♣7♦5♠ | トップ 8、max_diff=3、rainbow、top<T → 型3 |

### 型4: ロー × ウェット (🛡️ 撤退モード)

| ボード | 判定条件 |
| --- | --- |
| T♥9♠8♣ | 連続3枚、rainbow |
| 9♠8♦7♣ | 連続3枚、rainbow |
| J♠T♠9♦ | 連続3枚 + 2-tone |
| 9♣8♣7♦ | 連続3枚 + 2-tone |
| T♦9♦8♣ | 連続3枚 + 2-tone |
| 8♠7♠6♦ | 連続3枚 + 2-tone |
| 7♥6♥5♣ | 連続3枚 + 2-tone |
| T♦9♣6♠ | max_diff=4、rainbow、top=T → 高ボード連続 ✓ |
| 6♥5♥4♦ | 連続3枚 + 2-tone |

### 型5: モノトーン (📕 見送りモード)

| ボード | 判定条件 |
| --- | --- |
| A♥K♥Q♥ | 3 スートすべて ♥ |
| 9♠8♠7♠ | 3 スートすべて ♠ |
| K♥9♥5♥ | 3 スートすべて ♥ |
| J♠6♠4♠ | 3 スートすべて ♠ |
| A♥T♥4♥ | 3 スートすべて ♥ |

### 型6: ペア (ハイ + 高キッカー) (⚡ 全開モード、小サイズ)

| ボード | 判定条件 |
| --- | --- |
| A♣A♦K♠ | AA ペア + K キッカー |
| K♠K♦9♣ | KK ペア + 9 キッカー |
| Q♠Q♦T♣ | QQ ペア + T キッカー |
| K♠K♦8♣ | KK ペア + 8 キッカー |
| A♣A♦T♠ | AA ペア + T キッカー |

### 型7: ペア (そのほか) (🎯 中程度モード)

| ボード | 判定条件 |
| --- | --- |
| 7♦7♣K♠ | 77 ペア、キッカー K (< 8 でないがペアが 7) |
| 7♦7♣3♣ | 77 ペア、キッカー 3 |
| 9♥9♦2♣ | 99 ペア、キッカー 2 |
| K♦4♣4♠ | 44 ペア + K キッカー (ペアが 4 なので型7) |
| A♠9♥9♦ | 99 ペア + A キッカー |
| T♠T♦5♣ | TT ペア + 5 キッカー |
| 8♠8♣3♦ | 88 ペア + 3 キッカー |

---

## 付録C　D3 完全仕様

第8章で導入したD3チェックリストの正式仕様。

### D3 (中級版): 10 個の数字で 7 型 × 強度を捕捉

```text
Step 1: モノトーン?       → 20%
Step 2: ペア?
  - ハイペア (QQ+) + 高キッカー (≥8):    80%
  - ハイペア (QQ+) + 低キッカー (<8):    50%
  - ミドル/ローペア (トップがペア):      72%
  - A/K ハイ + ローペア (ペア≤7):        45%
  - A/K ハイ + 中ペア (ペア 8-T):         75%
Step 3: ウェット判定
  - 連続3枚 (max_diff ≤ 2)
  - 2-tone
  - 高ボード連続 (max_diff ≤ 4 かつ top ≥ T)
Step 4: トップ A/K/Q × ウェット
          ドライ  ウェット
    ハイ   85%    55%
    ロー   55%    30%
```

### D3 Lite (初心者版): 5 個の数字

```text
モノトーン     20%
ペア (一律)    68%
ハイ ドライ    85%
ハイ ウェット  55%
ロー (一律)    35%
```

### D3 と 7 型の対応

| 型 | D3 予測頻度 | 備考 |
| --- | --- | --- |
| 型1: ハイ × ドライ | 85% | 高頻度 (全開モード) |
| 型2: ハイ × ウェット | 55% | 中頻度 (狙い撃ち) |
| 型3: ロー × ドライ | 55% | 中頻度 (控えめ) |
| 型4: ロー × ウェット | 30% | 低頻度 (撤退) |
| 型5: モノトーン | 20% | 低頻度 (見送り) |
| 型6: ペア (ハイ + 高キッカー) | 80% | 高頻度 (全開) |
| 型7: ペア (そのほか) | 45-75% | 中頻度 (中程度) |

### GTO 検証結果

30ボードのGTO Wizardデータとの一致：。

- **R² = 0.873**
- **MAE = 6.03%**
- **Pearson r = +0.938**

検証スクリプト： `scripts/bdm.py`

---

## 付録D　BDM v5 完全係数表 (次巻予告)

次巻『ポーカー・ポストフロップ完全攻略』で詳説する精密モデル **BDM v5** の完全係数表のみ掲載します。本書では計算方法の詳細解説は行いません。興味のある読者は次巻を参照してください。

### 基本式

```text
CBet% = 90 − HighCardDeficit − TextureCost − SuitPenalty − Extra
        (ペアは override、monotone は 18% 固定)
```

### HighCardDeficit

| トップ | 減算 |
| --- | --- |
| A, K | 0 |
| Q | 5 |
| J, T, 9 | 35 |
| 8 以下 | 30 |

### TextureCost (max_diff = トップ − ボトム)

| max_diff | トップ条件 | 減算 |
| --- | --- | --- |
| ≥ 8 (散開) | - | 0 |
| 5〜7 (中程度) | - | 5 |
| 3〜4 (2連+ギャップ) | top ≤ 8 | 5 |
| 3〜4 | top 9-T | 15 |
| 3〜4 | top J | 15 |
| 3〜4 | top Q+ | 25 |
| ≤ 2 (連続3枚) | top ≤ 8 | 5 |
| ≤ 2 | top 9 rainbow | 10 |
| ≤ 2 | top 9 2-tone | 20 |
| ≤ 2 | top T 2-tone | 15 |
| ≤ 2 | top T rainbow | 20 |
| ≤ 2 | top J | 25 |
| ≤ 2 | top Q+ | 30 |

### SuitPenalty

| スート構造 | 減算 |
| --- | --- |
| rainbow | 0 |
| 2-tone | 10 |
| monotone | override → 18% |

### Extra (ブロードウェイ補正)

| 条件 | 追加減算 |
| --- | --- |
| mid=T かつ top≥Q かつ rainbow | -15 |
| 3枚とも T 以上 かつ 2-tone | -10 |
| top=A/K/Q + mid=T + 2-tone + low<T | -15 |
| top=Q かつ mid<T かつ 2-tone | -10 |

### Pair Override

| パターン | 頻度 |
| --- | --- |
| ハイペア (QQ+) + 高キッカー (≥8) | 82% |
| ハイペア (QQ+) + 低キッカー (<8) | 50% |
| ミドルペア (TT-88) | 75% |
| ローペア (77 以下) | 68% |
| A/K ハイ + ローペア (ペア ≤7) | 45% |
| A/K ハイ + 中ペア (ペア 8-T) | 76% |
| Q/J ハイ + ローペア | 55% |

### 精度

- **R² = 0.914**（D3の0.873を上回る）
- **MAE = 5.27%**
- Pearson r = +0.962

再現コード： `scripts/bdm.py` (関数 `bdm_v5()`)

---

## 付録E　主要ドロー完成率 + Rule of 2/4

第6章で扱ったドロー計算の早見表。

### 主要ドローのアウツ数と正確な確率

| ドロー | アウツ | ターン完成 | 2ストリート合計 | Rule of 4 | 誤差 |
| --- | --- | --- | --- | --- | --- |
| モンスタードロー (FD + OESD) | 15 | 31.9% | 54.1% | 60% | -5.9% |
| FD + ガットショット | 12 | 25.5% | 45.0% | 48% | -3.0% |
| フラッシュドロー (FD) | 9 | 19.1% | 35.0% | 36% | -1.0% |
| OESD / ダブルガットショット | 8 | 17.0% | 31.5% | 32% | -0.5% |
| 2 オーバーカード | 6 | 12.8% | 24.1% | 24% | +0.1% |
| ガットショット | 4 | 8.5% | 16.5% | 16% | +0.5% |

### Rule of 2 and 4

```text
フロップ段階 (2 ストリート残り): 完成確率 ≈ アウツ × 4
ターン段階 (1 ストリート残り):   完成確率 ≈ アウツ × 2
```

### 10 アウツ以上の拡張公式

```text
エクイティ (%) = (アウツ × 4) − (アウツ − 8)
             = アウツ × 3 + 8
```

8アウツ以下では補正がゼロorマイナスになるため、10アウツ以上でのみ使用。

### ダーティアウツ (ディスカウント)

- フラッシュvsナッツフラッシュの疑いあり： 1-2アウツ差し引く
- ストレート完成でボードが危険にならないか確認
- BDFDは通常の加点方式に含めない（別枠 +4）

### BDFD/BDSD の扱い

| ドロー | 実質加算エクイティ | HandScore での扱い |
| --- | --- | --- |
| BDFD (ナッツまたは強) | 約 +4% | +4 点 (固定) |
| BDSD | 約 +2% | +2 点 |

---

## 付録F　169 ハンド × 代表 6 ボード 型別アクション

プリフロップレンジの169ハンド (8Xo、AA…) がフロップでどう動くか、型ごとの一覧。

### ボード1: K♣7♦2♠ (型1: ハイ × ドライ, D3=85%)

| ハンド | HandScore | 強度 | アクション (IP) |
| --- | --- | --- | --- |
| KK (セット) | 30 | 強 | CBet 75% |
| AA (オーバーペア) | 20 | 強 | CBet 75% |
| AK (TPTK) | 18 | 強 | CBet 75% |
| KQ (TPGK+BDFD) | 19 | 強 | CBet 75% |
| 88 (アンダーペア) | 6 | 中 | CBet 33% |
| AQ (空振り + BDFDなし) | 0 | 弱 | チェック半々 |
| A♥Q♥ (空振り + BDFD) | 4 | 弱 | CBet 33% (ブラフ) |

### ボード2: 9♥8♥7♦ (型4: ロー × ウェット, D3=30%)

| ハンド | HandScore | 強度 | アクション (IP) |
| --- | --- | --- | --- |
| 77 (セット) | 30 | 強 | CBet 50% |
| A♥T♥ (モンスタードロー) | 15 | 中 | チェック (ウェットは強ハンドでも控え) |
| JT (OESD + FD) | 15 | 中 | チェック |
| KK (オーバーペア) | 20 | 中 | チェック (型4 ではセット級以下は中扱い) |
| JTo (OESD) | 12 | 中 | チェック |

### ボード3: A♠8♥3♦ (型1: ハイ × ドライ, D3=85%)

| ハンド | HandScore | 強度 | アクション (IP) |
| --- | --- | --- | --- |
| AK (TPTK) | 18 | 強 | CBet 75% |
| AQ (TPGK) | 15 | 強 | CBet 75% |
| A♥K♥ (TPTK + BDFD) | 22 | 強 | CBet 75% |
| KQ (空振り) | 0 | 弱 | チェック (BDFDなし) |
| 99 (アンダーペア) | 6 | 中 | CBet 33% |

### ボード4: Q♣J♦9♠ (型2: ハイ × ウェット、高ボード連続, D3=55%)

| ハンド | HandScore | 強度 | アクション (IP) |
| --- | --- | --- | --- |
| QQ (セット) | 30 | 強 | CBet 50% |
| JJ (セット) | 30 | 強 | CBet 50% |
| AK (OESD + BDFD) | 16 | 中 (上位) | CBet 33% |
| AQ (TPTK) | 18 | 強 | CBet 50% |
| KT (OESD) | 12 | 中 | CBet 33% |

### ボード5: T♥9♠8♣ (型4: ロー × ウェット、連続3枚, D3=30%)

| ハンド | HandScore | 強度 | アクション (IP) |
| --- | --- | --- | --- |
| JT (OESD+TP) | 22 | 強 | CBet 50% |
| TT (オーバーペア) | 20 | 中 | チェック |
| QJ (OESD) | 12 | 中 | チェック |
| 76 (OESD) | 12 | 中 | チェック |

### ボード6: 5♣4♦2♠ (型3: ロー × ドライ、厳密には型3 の辺緯, D3=55%)

| ハンド | HandScore | 強度 | アクション (IP) |
| --- | --- | --- | --- |
| AA (オーバーペア) | 20 | 強 | CBet 50% |
| 55 (セット) | 30 | 強 | CBet 50% |
| 33 (ストレート完成A2345) | 30 | 強 | CBet 50% |
| AK (空振り) | 0 | 弱 | チェック |
| 76s (ガットショット + BDFD) | 6 | 中 | CBet 33% (ドロー付き) |

---

## 付録G　よくある誤解 Q&A

### Q1: ウェットボードでは CBet しないべきですか

A: 完全にチェックというのは誤解です。ウェットボードでも **強ハンド (セット、ストレート、フラッシュ)** では50% CBetが正解です。大きなサイズを避けるのが正しく、「打つか打たないか」ではなく「どれくらいのサイズで打つか」の問題。

### Q2: ドンクベットは本当に禁止ですか

A: 初心者は避けるべきです。BBがOOPからドンクを打つと、レンジが弱く見えるためBTNのIPレイズにさらされます。第14章でドンクの条件を示していますが、初心者は「基本はチェックフォールドorチェックコール」に徹するのが安全。

### Q3: MDF は覚えなくていいですか

A: 中級以上では必須です。33% ベットに対してMDFは75%、75% ベットに対してMDFは57%。これを下回るディフェンス頻度は相手にブラフを許します。第13章で扱います。

### Q4: オーバーベット (150%) はいつ打ちますか

A: リバーでナッツアドバンテージが極端に強いとき。フロップでは基本75% が最大サイズ。オーバーベットは巻3の「リバー戦略」で扱います。

### Q5: フロップで相手のハンドを特定できますか

A: 単一ハンドまでは絞れません。レンジ（ハンドの集合）として扱います。相手の事前行動（プリフロップレンジ、フロップのアクション）からレンジを絞り込み、確率分布で考えるのが本書のアプローチ。

### Q6: 3bet ポットでも本書式は使えますか

A: はい。ただしレンジが狭まるため、D3頻度に +5%、ブラフ弱ハンドは削減する補正が必要。第16章で詳述。

### Q7: マルチウェイで本書式は使えますか

A: 3-way以上ではマトリクスの頻度帯を「1段下」に読み替える。4-way以上では強ハンドのみベット。第16章を参照。

### Q8: ミックス戦略 (混合頻度) は覚えるべきですか

A: 初中級は不要。本書の決定論的マトリクスで9割対応できます。ミックス戦略は巻3で扱います。

### Q9: 「ハイ×ドライ」と「ロー×ドライ」で頻度 (85% vs 55%) がなぜこれほど違うのですか

A: PFAのプリフロップレンジが階段状に構成されているからです。A/K/QにはAX/KX/QXコンボが密集しますが、J以下ではBBのディフェンスレンジにコネクターが多く、レンジ優位が消失します。

### Q10: AQo はマルチウェイで本当に機能しませんか

A: はい。マルチウェイではAQoの価値が激減します。プリフロップで3-betしてヘッズアップに持ち込むか、フォールドが正解。

---

## 付録H　用語集

### 数値指標

- **D3**: 本書のボード頻度モデル。4マス + ペア5種 + モノoverrideでCBet頻度を算出。
- **HandScore**: 役 + ドロー + ブロッカーの和で自ハンドを数値化。0-30以上。
- **BDM v5**: D3の精密版。次巻で詳解。R² 0.914。
- **MDF (Minimum Defense Frequency)**: 相手のベットに対して少なくとも守るべき頻度。1 −（ベット額 /（ベット額 + ポット））。
- **SPR (Stack-to-Pot Ratio)**: ポストフロップのスタック対ポット比。
- **EV (期待値)**: 長期的な平均収益。

### アクション

- **CBet (Continuation Bet)**: プリフロップレイザーがフロップで最初に打つベット。
- **ドンクベット**: BBなどOOPからプリフロップアグレッサーに対して打つベット。通常は非標準。
- **チェックレイズ**: チェックした後、相手のベットに対してレイズする行動。
- **3bet**: プリフロップの3番目のレイズ（リレイズ）。
- **4bet**: プリフロップの4番目のレイズ（3betへのリレイズ）。

### ボード分類 (本書)

- **型1-7**: 本書の7型分類（第3章）。
- **ドライ**: ウェット条件にいずれも該当しないボード。
- **ウェット**: 連続3枚 / 2-tone / 高ボード連続のいずれかに該当。
- **モノトーン**: 3枚とも同スート。
- **2-tone**: 3枚のうち2枚が同スート。
- **rainbow**: 3枚とも異なるスート。

### ドロー

- **OESD (Open-Ended Straight Draw)**: 両端ストレートドロー、8アウツ。
- **ガットショット**: 中抜けストレートドロー、4アウツ。
- **ダブルガットショット**: 2か所の中抜け、計8アウツ。
- **FD (Flush Draw)**: フラッシュドロー、9アウツ。
- **BDFD (Backdoor Flush Draw)**: バックドアフラッシュドロー、ターン+リバーで成立。

### レンジ関連

- **レンジアドバンテージ**: 両者のレンジ全体でボードと相性が良いか。
- **ナッツアドバンテージ**: 最強クラスのハンドをどちらが多く持つか。
- **ブロッカー**: 相手のコンボを自分が持っていることで減らす効果。
- **ディスブロッカー**: 相手の弱いハンドを自分が持っていることで弱レンジを減らす効果。

### 役

- **TP (Top Pair)**: ボードの最高ランクとペアを作った状態。
- **TPTK (Top Pair Top Kicker)**: トップペア + 最強キッカー（通常AK）。
- **TPGK (Good Kicker)**: トップペア + 良キッカー。
- **TPWK (Weak Kicker)**: トップペア + 弱キッカー。
- **オーバーペア**: ボードの最高カードより高いポケットペア。
- **セット**: ポケットペアがボードで3枚目を引いた（強い）。
- **トリップス**: ボードのペアに自分の1枚が合って3枚目を作る（セットより弱く見られがち）。

---

## 付録I　出典・再現性

### GTO Wizard データ

本書の検証に使用した30ボードはGTO Wizardの公開データ（無料プランで閲覧可能）から抽出しています。主要な出典：。

- GTO Wizard Blog: *Flop Heuristics: IP C-Betting in Cash Games*
  <https://blog.gtowizard.com/flop-heuristics-ip-c-betting-in-cash-games/>
- GTO Wizard Blog: *The Mechanics of C-Bet Sizing*
  <https://blog.gtowizard.com/the-mechanics-of-c-bet-sizing/>
- GTO Wizard Blog: *Maximizing Value on Monotone Flops*
  <https://blog.gtowizard.com/maximizing-value-on-monotone-flops/>
- GTO Wizard Blog: *C-Betting As the OOP Preflop Raiser*
  <https://blog.gtowizard.com/c-betting-as-the-oop-preflop-raiser/>

### Upswing Poker 等のそのほかの出典

- *10 Fundamental Tips for The Most Common Types of Flops*
  <https://upswingpoker.com/board-texture-tips/>
- *GTO C-Bet Frequency Quiz Answers*
  <https://upswingpoker.com/gto-c-bet-quiz-answers/>
- *Board Texture Breakdowns* (SplitSuit Poker)
  <https://www.splitsuit.com/flop-textures>
- *Continuation Betting 101* (PokerCoaching)
  <https://pokercoaching.com/blog/continuation-betting-101/>

### 再現性

本書のD3モデルとBDM v5モデルは、以下のPythonスクリプトで実装されています。30ボードでのR² / MAE / Pearson rを再現できます。

```bash
cd poker-books/
python3 scripts/bdm.py
```

出力例：。

```text
D3    : R² = 0.873  MAE = 6.03  r = 0.938
BDM v5: R² = 0.914  MAE = 5.27  r = 0.962
```

### 検証プロトコル

- **対象**: 6-max 100BBキャッシュ、BTN vs BB SRP
- **ボード数**: 30（ドライ/セミウェット/ウェット/ペア/モノトーン各種）
- **実測日**: 2026年4月
- **環境**: Python 3.13、統計モジュール標準ライブラリのみ

### v2 への検証計画

- 代表100スポットでGTO Wizardの有料プランを用いた自動検証
- 読者から実戦ハンドデータを募り、本書式のEV損失を回帰分析
- 結果をWeb版 (GitHub Pages) で随時更新
