# 第 11 章　Hand Strength — 6 階層 → 4 集約の理由

## 11.1 旧 6 階層

| index | 名前 | 含むハンド |
|---:|---|---|
| 5 | ナッツメイド | FH / quads / SF |
| 4 | ストロング | set / flush / straight / 2P |
| 3 | ツーペア | (旧分類で独立) |
| 2 | トップペア以上 | TP / overpair |
| 1 | アンダーペア | second / third / underpair |
| 0 | エア | high card / king / ace high |

実は旧 6 階層は「ストロング」「ツーペア」「ナッツメイド」を細分化したものです。

## 11.2 4 集約の data 駆動根拠

監査で カテゴリ 数を変えた直接比較をしてみると、以下のような結果が得られます：

| 構成 | Grid cells | avg loss | 採否 |
|---|---:|---:|---|
| 6 カテゴリ (旧) | 18 | 0.3722 BB | × |
| 5 カテゴリ | 15 | 0.4084 BB | × (集約過剰) |
| **4 カテゴリ-B (本書)** | **12** | **0.3587 BB** | **★採用** |
| 4 カテゴリ-A (ペア統合) | 12 | 0.3843 BB | × |
| 7 カテゴリ (細分化) | 21 | 0.3874 BB | × (overfit) |

**4 カテゴリ-B (上位統合) が最良です**。「ナッツ / ストロング / 2P」を「2P+ハンド」1 階層に統合した版が勝者となりました。

## 11.3 「2P+」 統合の決定的役割

統合の決め手は 4BP での挙動です。4BP では 2P 以上はすべて「強行 value」が GTO 最適で、細分化しても出力が同じになります（call / raise の中で混合）。統合することで Score 公式の 4BP 補正（+16）が直接効くようになります。

## 11.4 mv_cat 17 種類 → 4 集約の対応

GTO ソルバー 内部の mv_cat 17 種類が本書 4 カテゴリに対応します：

```
2P+: two_pair, set, trips, straight, flush, fullhouse, quads, straight_flush
トップペア以上:    top_pair, overpair
アンダーペア:        second_pair, third_pair, underpair, low_pair
エア:              no_made_hand, king_high, ace_high
```

第 2 章で詳述したとおりです。

## 11.5 6 → 4 集約の理論的妥当性

「上位 3 階層を統合して情報損失がないか？」という不安への監査結果は以下の通りです：

- ナッツ × paired と 2P × paired は GTO 出力が「99% 同じ」（両方とも slowplay → call）
- set と flush は wet board で「両方とも check call base」
- straight と FH は dry board で「両方とも value raise」

→ 細分化しても出力は変わりません。統合することで Grid を 12 に減らし、暗記コストを半減できます。

## 11.6 「エクイティバケット」との関係

MATCHA Framework ではハンドストレングスを 4 階層に集約し、**エクイティバケットは独立軸として廃止**して Grid 値に吸収しています。

ハンドストレングスとエクイティバケットの情報が重複していたため、単純化により暗算が大幅に楽になりました。

## Cash/MTT note

Hand Strength の 6→4 集約は Cash/MTT 共通です。

## この章で覚える項目 (3 items)

1. 4 カテゴリ (2P+ / TP+ / アンダーペア / エア) で暗算コスト最小
2. 2P+統合が 4BP の huge% を低く保つ立役者
3. エクイティバケット軸は廃止、 Grid に吸収済
