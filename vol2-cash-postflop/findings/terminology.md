# Vol2 用語定義 — Light UCBS v2 + Light DCBS

作成日: 2026-05-28
用途: Vol1 (preflop) / Vol3 (MTT Full) / Vol4 (Tell) との整合確認。章執筆前の用語ロック。

---

## 1. 核心用語 — HP / DP / CBS

### HP (Hand Power)
**定義**: フロップでのハンドの「役の強さ」を整数 (0-9) で表したスコア。
ドローを含まず、現時点の役だけで決まる。

- 範囲: 2, 3, 5, 7, 8, 9 の 6 バケット
- 変数名: `HP_TABLE[hand_type]`
- ソース: `ucbs_v2.py` 行 60-80 (HP_TABLE)

**Vol1 との衝突なし**: Vol1 の `Score` / `H` / `L` はプリフロップ評価式であり、ポストフロップ HP とは独立した概念です。名前の一文字が同じ (H) ですが、文脈が完全に異なるため混同の恐れはありません。

**Vol3 との整合**: Vol3 (Full UCBS-v2) も同一の `HP_TABLE` を使用します (`ucbs_v2.py` の HP_TABLE を共有)。Vol2/Vol3 間で HP 値は完全に共通です。

---

### DP (Draw Power)
**定義**: フロップでのドローの「期待価値」を整数 (0-3) で表したスコア。
役ではなく将来の改善可能性のみを表す。

- 範囲: 0, 1, 2, 3 の 4 段階
- 変数名: `DP_TABLE[draw_type]`
- ソース: `ucbs_v2.py` DP_TABLE

**Vol1 との衝突なし**: Vol1 に DP という用語は登場しません。

**Vol3 との整合**: Full UCBS-v2 でも同一定義を使用。完全共通。

---

### CBS (Combined Board Score)
**定義**: CBS = HP + DP。フロップにおけるハンドの「総合的な強さ」を表す整数スコア。

- 計算式: `CBS = HP_TABLE[hand] + DP_TABLE[draw]`
- 範囲: 理論上 2-12、実用上 2-12
- ソース: `ucbs_light_v2.py` `ucbs_v2.py`

**旧 HandScore (HS) との違い**:
既存の `vol2-cash-postflop/chapters/` (旧 draft) では `HandScore (HS)` という概念を使っていましたが、新 Vol2 では CBS に一本化します。HS は 0-100 のエクイティ近似だったのに対し、CBS は 2-12 の整数スコアです。チャプターを新規生成する際は HS を CBS に置き換えてください。既存 chapters/*.md は読み取り専用で変更しないため、旧 HS 表記はそのまま残ります (将来の generator 側で吸収)。

**Vol1 との衝突なし**: Vol1 に CBS という用語は登場しません。

**Vol3 との整合**: Full UCBS-v2 も CBS = HP + DP を使用。完全共通。

---

## 2. CBS バンド — 5 区分

| バンド名 | CBS 範囲 | 旧 HandScore バケットとの対応 | 意味 |
|---|---:|---|---|
| **air** | 0-2 | エアー (HS≤34 の一部) | 役なし・ほぼ改善なし |
| **weak** | 3-4 | エアー〜マージナル境界 | 弱いペア / gutshot 止まり |
| **mid** | 5-6 | マージナル (HS 35-64 の一部) | 中程度のペア / 強いドロー |
| **strong** | 7-8 | バリュー (HS≥65) | トップペア / セット |
| **nut** | 9+ | バリュー上位 | 2 ペア以上の怪物 |

**旧 3 バケット (バリュー/マージナル/エアー) との関係**:
新 Vol2 では旧 3 バケットを使いません。5 バンドに移行します。旧 chapter では HS 閾値テーブルを使っていましたが、新章では CBS バンドから直接 25 セル表を参照します。

---

## 3. Light UCBS v2

**定義**: 5 context × 5 CBS バンドの 25 セル表から cbet 頻度を導く暗算システム。
フル UCBS-v2 の 13 context を 5 context に圧縮した簡易版。

- 名称: Light UCBS v2 (または Light v2)
- 25 セル表: `LIGHT_V2_BASE[context][band]`
- 例外: `LIGHT_V2_OFFSET["low_pair"] = -0.10` (-10pt)
- ソース: `ucbs_light_v2.py`

**Vol3 との区別**: Vol3 では Full UCBS-v2 (13 context) を使います。Vol2 の「Light」と Vol3 の「Full」で意図的に深さを変えています。読者への説明: 「Vol2 は Cash と MTT 中後盤をカバーする 5 context 版、Vol3 は 13 context の完全版」。

---

## 4. Light DCBS

**定義**: BB が cbet を受けたときの continue freq (call + raise) を HP × context で求める守備側モデル。
フル DCBS の 4 context をそのまま使うが、Vol2 では cash_100bb を主役とする。

- 名称: Light DCBS (または DCBS)
- 主要テーブル: `DCBS_CONTEXTS["cash_100bb"]["base"]` (HP → continue freq)
- kicker offset: `DCBS_CONTEXTS["cash_100bb"]["kicker"]`
- ソース: `dcbs.py`

**Vol3 との違い**: Vol3 では 4 context (mtt_25/50/100bb + cash_100bb) を全て扱います。Vol2 では cash_100bb に絞り、MTT depth 比較は付録または簡略説明とします。

---

## 5. context — 5 種類の定義

| context 名 | 対応シナリオ | スタック | 備考 |
|---|---|---|---|
| `cash` | Cash 100bb SRP (IP cbet) | 100bb | Vol2 の主役 |
| `mtt_short` | MTT 25-50bb SRP | 25-50bb | 終盤〜中盤 |
| `mtt_deep` | MTT 100-200bb SRP | 100bb+ | 序盤 / 深スタック |
| `3bp` | 3-bet pot (Cash or MTT) | any | SPR ~5 が典型 |
| `turn` | ターン 2nd barrel (cbet 後) | any | α=-0.35 相当 |

**Vol3 の 13 context との対応**:
| Light v2 context | Full v2 contexts (対応) |
|---|---|
| cash | cash_100bb |
| mtt_short | mtt_25bb, mtt_50bb |
| mtt_deep | mtt_100bb, mtt_200bb |
| 3bp | mtt_3bp_20bb, mtt_3bp_25bb, mtt_3bp_50bb, mtt_3bp_100bb |
| turn | mtt_25bb_turn_btn, mtt_50bb_turn_btn, cash_100bb_turn_btn |

---

## 6. 型1-7 (ボード分類)

**定義**: フロップを 7 種類に分類するショートカット。「トップカード高さ」「テクスチャ」「ペア有無」の 3 要素で決定。

| 型 | 名称 | 条件 | ナッツアドバンテージ |
|---|---|---|---|
| 型1 | ハイドライ | top≥Q かつ rainbow かつ spread>3 | SB 有利 |
| 型2 | ハイウェット | top≥Q かつ (2-tone or spread≤3) | SB 有利 |
| 型3 | ロードライ | top<Q かつ rainbow かつ spread>3 | BB 有利 |
| 型4 | ローウェット | top<Q かつ (2-tone or spread≤3) | BB 有利 |
| 型5 | モノトーン | 3 枚同スーツ | 境界 |
| 型6 | ペア高 | ペア rank≥Q | SB 有利 |
| 型7 | ペア低 | ペア rank<Q | 中立 |

**Vol1 との関係**: Vol1 (preflop) では型1-7 を使いません。postflop 専用の概念です。Vol1 ch12 (付録) で「postflop は Vol2 でボード 7 分類を学ぶ」と一言触れる程度で十分です。

**Vol3 との整合**: Vol3 (Full UCBS-v2) も同一の型1-7 を使用します。信頼度シフトルール (型6 up, mono down) も共通。

---

## 7. MDF (Minimum Defense Frequency)

**定義**: 相手のブラフを採算割れにするために、OOP が守らなければならない最低ディフェンス頻度。
`MDF = 1 - α = pot / (pot + bet)`

**Vol2 での位置づけ**: ch08 (Light DCBS) の設計根拠として説明します。対局中に MDF 計算は不要で、DCBS テーブルで代替します。

**旧用語との整合**: 旧 ch06 では「後手下限」という表現が使われていましたが、これは廃棄済み。MDF で統一します (グローバルフィードバック: `feedback_mdf_terminology.md` 参照)。

---

## 8. TA+ / TA- (Turn Advantage)

**定義**: ターンカードが IP のレンジを強化するか (TA+) または BB のレンジを強化するか (TA-) を表す 2 値指標。

- TA+: IP のレンジが BB より有利になるターン → バレル継続推奨
- TA-: BB のレンジが有利になるターン → チェックバック推奨

**Vol2 での位置づけ**: ch09 (Turn 2nd barrel) で使用。Light 版では詳細な计算は省略し「ブロードウェイカードは TA+、低ランクカードは TA- 寄り」という簡易ルールに簡素化します。

---

## 9. 旧用語との対応表

執筆者が旧 chapters/*.md と新 outline/generator を混同しないための対応表です。

| 旧用語 (旧 ch ベース) | 新用語 (Light UCBS v2 ベース) | 備考 |
|---|---|---|
| HandScore (HS) | CBS (Combined Board Score) | 全面置換 |
| バリュー / マージナル / エアー (バケット) | strong / mid / air (バンド) | 5 バンドに拡張 |
| R (役スコア) | HP (Hand Power) | 役の強さを表す整数 |
| D (DrawBonus) | DP (Draw Power) | ドローの価値 |
| SRP 決定表 | 25 セル表 (Light UCBS v2) | context 対応の拡張版 |
| HS 閾値テーブル | DCBS continue freq 表 | DCBS に置換 |
| 後手下限 | MDF | 廃棄済み用語 |

---

## 10. Vol1 / Vol3 / Vol4 との衝突チェック

### Vol1 (preflop) — 衝突なし

Vol1 の主要用語:
- `Score` = プリフロップスコア (H + L + pair_bonus + suit_bonus - gap)
- `T_open` = ポジション別オープン閾値
- `Score_BB` = BB 守備スコア

これらはすべてプリフロップ専用で、Vol2 の CBS / HP / DP / 型1-7 とは独立しています。名前の重複もありません。

**要注意点 1**: Vol1 の `H` / `L` (高い方・低い方のカードランク) と Vol2 の HP (Hand Power) は別概念です。読者が両方読む場合、"H" の意味が変わることを序文で注記します。

### Vol3 (MTT Full UCBS-v2) — 整合済み

Vol3 は Full UCBS-v2 を使い、CBS / HP / DP / 型1-7 を Vol2 と同一定義で使用します。違いは context の粒度 (5 vs 13) と追加パラメータ (α, β, slowplay offset など)。整合上の問題はありません。

### Vol4 (Tell / Exploit) — 衝突なし

Vol4 はプレイヤータイプ別補正を扱い、ポストフロップの基礎式 (CBS) への参照はほぼありません。「Vol2 で学んだ CBS を相手タイプで調整」という誘導リンクを ch00 に追加するだけで十分です。

---

## 11. 用語確定版 (章執筆時の参照テーブル)

| 正式用語 | 略称 | 初出章 | 定義 |
|---|---|---|---|
| Hand Power | HP | ch01 | 役の強さを 2-9 で表す整数 |
| Draw Power | DP | ch01 | ドローの価値を 0-3 で表す整数 |
| Combined Board Score | CBS | ch01 | CBS = HP + DP |
| CBS バンド | バンド | ch01 | air/weak/mid/strong/nut |
| Light UCBS v2 | Light v2 | ch02 | 5 context × 5 band の 25 セル表 |
| Light DCBS | DCBS | ch08 | HP 別 continue freq 表 |
| Minimum Defense Frequency | MDF | ch08 | 最低守備頻度 |
| Turn Advantage | TA | ch09 | ターンカードのレンジ有利性 |
| ボード型 | 型1-7 | ch04 | フロップ 7 分類 |
| context | — | ch02 | 5 種類のシナリオ分類 |
| continue freq | — | ch08 | コール + レイズの合計頻度 |
| pos_lift | — | ch06 | ポジション補正値 (pt) |
