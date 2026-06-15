# 第 2 章　カテゴリ — ハンドストレングス 4 段階

## 2.1 4 段階の階層

MATCHA Score では hand を 4 段階の **カテゴリ** に分類します。

| index | カテゴリ 名 | 含まれるハンド (mv_cat) |
|---:|------|------|
| 0 | **エア** | no_made_hand、 king_high、 ace_high |
| 1 | **アンダーペア** | second_pair、 third_pair、 underpair、 low_pair |
| 2 | **トップペア以上** (TP+) | top_pair、 overpair |
| 3 | **2P+** | two_pair、 set、 trips、 straight、 flush、 fullhouse、 quads、 straight_flush |

## 2.2 各 カテゴリ の定義詳細

### エア (カテゴリ 0)

ボードと噛み合わないハンド全般です。

- no_made_hand: high card にすらならない (例: J8o on Kh 7c 2d)
- king_high: K-high の no pair (例: AKo on Q-7-2、 board K より下のキッカー)
- ace_high: A-high の no pair (例: AKo on Q-7-2、 hero に A あり)

draw が付いていても「メイドはエア」として扱います。 draw 価値は DV で別途加算されるため、 カテゴリ には含めません。

### アンダーペア (カテゴリ 1)

ボードのトップではないペアです。

- second_pair: ボード 2 位の rank とのペア (例: K-7-2 で 77)
- third_pair: ボード 3 位の rank とのペア
- underpair: ボード最低 rank より下のポケットペア (例: K-7-2 で 55)
- low_pair: ボード最低 rank とのペア

### トップペア以上 (TP+、 カテゴリ 2)

ボードのトップを叩いた / ボードを上回るペアです。

- top_pair: ボード最高 rank とのペア (例: K-7-2 で AK、 KQ、 KJ ...)
- overpair: ボードを越えるポケットペア (例: K-7-2 で AA、 QQ)

### 2P+ — ツーペア以上のメイドハンド (カテゴリ 3)

本書では **2P+** (ツーペア以上、 英語業界の "two pair plus" の略記) を 1 つの カテゴリ として扱います。 含まれる役は以下の 8 種類すべてです:

- **2P** (ツーペア): 例 K-7-2 で K7、 72
- **セット**: ポケットペア × ボードヒット (例 7-K-2 で 77)
- **トリップス**: ボードペア × hand の rank (例 K-K-2 で AK)
- **ストレート / フラッシュ / フルハウス / クアッズ / ストレートフラッシュ**

**初出につき詳しく**: 2P+ は「ツーペア以上」 を表す本書略記です。 TP+ (トップペア以上) と対称的な表記になっています。 以降本書では **2P+** と短縮表記します。

## 2.3 なぜ 4 段階で十分か (data 駆動の発見)

MATCHA Framework では 4 段階のカテゴリ 分類を採用しています。
data 検証から、階層数による Grid サイズと判定精度の関係は以下の通りです:

| カテゴリ 数 | Grid cells | avg loss |
|---:|---:|---:|
| 4 (本書) | **12** | **0.3587 BB** |
| 5 | 15 | 0.4084 BB |
| 6 | 18 | 0.3722 BB |
| 7 | 21 | 0.3874 BB |

**4 階層が最適なバランスを実現しています**。 これは「2P〜SF を統合した 2P+」 が、情報損失なしで暗記コストを削減するためです。

集約のキーは「実 GTO ではナッツメイド (FH / quads) も 2P もどちらも value bet の主役で、 出力アクションがほぼ同じ」 という観察です。 細分化しても判断は変わりません。

## 2.4 カテゴリ 判定の手順

ハンドを見たら、 上から順に判定してみてください。

1. **2P+か?** (ツーペア / set / トリップス / straight / flush / FH / quads / SF)
   - はい → カテゴリ 3、 終了
2. **トップペア以上か?** (top_pair / overpair)
   - はい → カテゴリ 2、 終了
3. **ペアか?** (second_pair〜low_pair / underpair)
   - はい → カテゴリ 1 (アンダーペア)、 終了
4. それ以外 → カテゴリ 0 (エア)

draw だけのハンド (例: T9 on K-Q-2、 OESD) は **エア** です。 draw 価値は DV で加算されます。

## 2.5 mv_cat 17 種類との対応表

GTO ソルバー 内部の `mv_cat` (made-value category) との対応をまとめました:

| mv_cat | 本書 カテゴリ |
|---|---|
| no_made_hand | エア |
| king_high / ace_high | エア |
| second_pair / third_pair / underpair / low_pair | アンダーペア |
| top_pair / overpair | トップペア以上 |
| two_pair | 2P+ |
| set / trips | 2P+ |
| straight / flush | 2P+ |
| fullhouse / quads / straight_flush | 2P+ |

17 種類が 4 階層に集約されます。

## 2.6 ポーカー古典文献との系譜

ポーカーの古典文献 (Sklansky-Malmuth / Janda 等) では
hand strength を **6 階層** に細分化することが一般的でした。 本書ではこれを 4 カテゴリ に集約します。

| 旧 6 階層 | 旧定義 | MATCHA 4 カテゴリ | 集約理由 |
|---|---|---|---|
| ナッツメイド | FH / quads / SF | **2P+** | GTO 出力同一 (value heavy) |
| ストロング | set / flush / straight | **2P+** | 同上 |
| ツーペア | 2P 単独 | **2P+** | 4BP で 2P 以上同挙動 |
| トップペア以上 | top_pair / overpair | **トップペア以上 (TP+)** | 維持 |
| アンダーペア | 2nd / 3rd / underpair / low | **アンダーペア** | 維持 |
| エア | high card / king / ace_high | **エア** | 維持 |

### なぜ上位を統合するのか — GTO の実測に基づく

data 分析から、上位の細分化は実は判定に活かされていないことが分かりました:

- **4BP × set vs 4BP × 2P**: 両者とも slowplay 率 96%、 GTO 出力ほぼ同一
- **dry × ナッツメイド vs dry × ストロング**: 両者とも value bet 強行、 細分化情報過多
- **paired × 2P**: 0-30% bet (slowplay)、 ナッツと同じ check 寄り挙動

上位 3 階層を細分化しても GTO 出力が変わりません。 「2P+」 に集約することで Grid を 12 マスに整理し、 暗記コストを削減できます (詳細根拠は第 11 章)。

### Sklansky Hand Groups (1976) との関係

旧来の preflop ハンド分類 Sklansky Hand Groups (8 群) との系譜:

- 群 1-2 (AA / KK / AKs 等) → 本書 **2P+** 系譜
- 群 3-4 (TT / 99 / AQs 等) → **トップペア以上** 系譜
- 群 5-7 (中位 broadway / SC) → **アンダーペア** 系譜
- 群 8 以下 (rag) → **エア** 系譜

ただし Sklansky は preflop 分類、 本書は postflop カテゴリです。 詳細は第 13 章 (旧来理論との橋渡し) で扱います。

## Cash/MTT note

カテゴリ 4 段階 (エア / アンダーペア / トップペア以上 / 2P+) は Cash と MTT で同一定義です。 GTO 上の頻度差はありません。 mv_cat → 4 階層対応も共通です。

## この章で覚える項目 (5 items)

1. カテゴリ 4 段階の順序 (エア / アンダーペア / TP+ / 2P+)
2. エアは「ペアもないハンド全部」
3. アンダーペアは「トップ以外のペアと underpair」
4. TP+ は「top pair と overpair」
5. 2P+ は「2P 以上全部」
