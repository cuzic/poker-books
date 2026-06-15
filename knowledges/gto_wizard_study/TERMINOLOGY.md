# MATCHA シリーズ用語集 (2026-06-09 確定)

本書および poker-drill / memory で統一すべき用語の確定リスト。

## A. 公式系

| 概念 | 確定用語 | 備考 |
|---|---|---|
| 公式の正式名 | **MATCHA Score** | 「v3」 等のバージョン表記は削除 |
| 計算式 | `Score = Grid[カテゴリ][board] + DV × mult[street] + 2 × oc + 4 × pot − 2 × bs` | 英数字記号で記述 |
| 判定 | `Score ≥ 43 → raise / ≥ 14 → call / else fold` | 数値そのまま |
| 12 cells grid | **12 cells grid** | 一般名詞 (固有名詞化しない)、 旧 TEA グリッドの後継。 **本フレームワークの魔法核心** — 線形ではなく Hand × Board の interaction で複雑に増減する 12 整数の表 |
| 閾値 (文章内) | コール閾値 / レイズ閾値 | 式内では `t_call / t_raise` |

## B. カテゴリ 4 段階 (本書最頻出)

| index | **確定用語** | 略称 | 含むハンド |
|---:|---|---|---|
| 0 | **エア** | — | no_made_hand / king_high / ace_high |
| 1 | **アンダーペア** | — | second_pair / third_pair / underpair / low_pair |
| 2 | **トップペア以上** | **TP+** | top_pair / overpair |
| 3 | **2P+** | — | two_pair / set / trips / straight / flush / FH / quads / SF |

## C. board 3 タイプ

| 確定用語 | 定義 |
|---|---|
| **dry** | unpaired / rainbow / 非 connected |
| **paired** | 同 rank ペアあり |
| **wet** | connected (gap ≤ 2) または monotone (3 枚同 suit) |

## D. DV (Draw Value)

| dv_cat | 確定用語 | 値 |
|---|---|---:|
| combo_draw | コンボドロー (combo) | 4 |
| nut_flush_draw / flush_draw | フラッシュドロー (FD/NFD) | 3 |
| oesd | OESD (オープンエンドストレートドロー) | 3 |
| gutshot | ガットショット | 1 |
| twocards_bdfd | BDFD (バックドアフラッシュドロー) | 1 |
| onecard_bdfd / no_draw | ドローなし | 0 |

| street | DV 倍率 |
|---|---:|
| flop | ×3 (Rule of 4 整数化) |
| turn | ×2 (Rule of 2 整数化) |
| river | ×0 (draw 完成不可) |

## E. pot 種別

| 略称 | 正式 | 値 |
|---|---|---:|
| **SRP** | Single Raised Pot | 0 |
| **vs CR** | CR ディフェンス (vs Check-Raise / vs Donk Bet) | 2 |
| **3BP** | 3-bet Pot | 2 |
| **4BP** | 4-bet Pot | 4 |

注: 旧称 「DEF」 は廃止、 **「vs CR」** または **「CR ディフェンス」** を使う。

## F. bet size 6 段階

| key | 確定用語 | 値 |
|---|---|---:|
| small_33 | スモールベット (33%) | 0 |
| med_75p | ミディアムベット (75%) | 1 |
| med_100p | ミディアムベット (100%) | 2 |
| overbet | オーバーベット (125%) | 3 |
| overbet_185 | オーバーベット (185%) | 4 |
| allin | オールイン | 5 |

注: 簡素化説明では med_75 + med_100 を 「ミディアムベット (75-100%)」 で統合してよい。

## G. その他公式要素

| 概念 | 確定用語 |
|---|---|
| overcards | オーバーカード (略称 oc、 値 0-2) |
| mv (made value) | mv_cat (英数字、 内部識別子) |

## H. 5 軸 (理論バックボーン、 Vol2 第3 部で扱う)

| 確定用語 | 内部 key |
|---|---|
| **レンジ分布** | range_morphology (旧 board_polar_tier) |
| **ハンドストレングス** | hand_strength_tier |
| **ベットサイジング** | bet_size_tier |
| **SPR** | spr_tier |
| **エクイティバケット** | equity_aware_tier |

## I. 形勢・モード・補正 (旧 TEA グリッド構造、 Score 公式に吸収済)

| 旧構造 | 確定方針 |
|---|---|
| **形勢** (優勢 / 五分五分 / 劣勢) | 第 3 部で背景説明のみ。 公式は Score 数値で代替 |
| **3 モード** (バリュー / ショーダウン / ブラフキャッチ) | 同上 (Score 値で吸収済) |
| **3 補正** (vs CR / vs Donk / オープナー) | 第 4 部 (pot 種別) と例外 5 ルールで個別解説 |
| **TEA グリッド** | **廃止** — 「12 cells grid」 (一般名詞) で代替 |

## J. Vol3 (Exploits) 関連

| 概念 | 確定用語 |
|---|---|
| プレイタイプ 5 分類 | ニット / TAG / LAG / コーリングステーション (CS) / マニアック |
| 5 つの逸脱軸 | Five Imbalances / 5 つの逸脱軸 |
| Score-shift | Score シフト / 閾値補正 |
| 強度 mild | 軽度 |
| 強度 extreme | 極端 |
| **attack view** | **ベット側** (hero がベットする側) |
| **defense view** | **コール側** (hero が受けて call/raise/fold する側) |

## K. シリーズ用語

| 略称 | 正式 |
|---|---|
| Vol1 | MATCHA Formula (プリフロップ) |
| Vol2 | MATCHA Framework (ポストフロップ) |
| Vol3 | MATCHA Exploits (相手タイプ別) |
| MATCHA acronym | Math Algorithm of Twelve-Cell Hold'em Action |

## 廃止用語 (旧 → 新)

| 旧用語 | 新用語 / 廃止理由 |
|---|---|
| Score Final v3 / MATCHA Score v3 | **MATCHA Score** (バージョン表記なし) |
| ストロング以上 / ストロ+ / 強役以上 | **2P+** |
| DEF / Defense pot | **vs CR / CR ディフェンス** |
| TEA グリッド / Tier × Edge = Action | **12 cells grid** (一般名詞) |
| attack view / 攻撃視点 | **ベット側** |
| defense view / 防御視点 | **コール側** |
| 旧 5 軸の細分名 (board_polar_tier 等) | 5 軸の確定日本語名を使う (H 節参照) |
| 旧 6 階層 (ナッツ/ストロング/2P/TP+/MP/エア) | **4 階層に集約** (B 節参照) |

---

*更新日: 2026-06-09 (用語確定)*  
*関連: vol2-postflop/toc.md / vol3-tell/toc.md / poker-drill/scripts/generate/_common/matcha_terms.py*
