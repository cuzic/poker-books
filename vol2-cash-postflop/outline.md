# Vol2 — Cash Postflop 完全ガイド (Light UCBS v2 + DCBS (cash 版)) 目次

作成日: 2026-05-28
ベース計画: `/home/cuzic/poker-books/RESTRUCTURE_PLAN.md` L52-91
合計: 12 章 + 付録、目標 ~70k 字

---

## 章構成一覧

| # | タイトル | 目標字数 | 既存章 | 流用度 |
|---|---|---:|---|---|
| 00 | はじめに | 3k | なし | — |
| 01 | CBS の式: HP + DP | 5k | 01-board-types (一部) | △ |
| 02 | Light UCBS の 25 セル表 | 6k | 02-cbet-ip (骨格参考) | △ |
| 03 | Cash 100bb cbet 完全ガイド | 8k | 02-cbet-ip (大部分) | △ |
| 04 | ボード読み (型1-7 簡素版) | 5k | 01-board-types | ○ |
| 05 | サイズ判別 (33% vs Overbet) | 4k | 02-cbet-ip 2-1 節 | △ |
| 06 | Position 補正 | 4k | なし | — |
| 07 | 3-bet pot postflop (cash) | 6k | 04-cbet-3bp-4bp | △ |
| 08 | DCBS (cash 版): 守備の暗算式 | 6k | 06-defense | ○ |
| 09 | Turn 2nd barrel: α=-0.35 シフト | 5k | 07-turn-barrel | △ |
| 10 | Multistreet plan | 6k | 08-turn-plan-defense + 11-multistreet-plan | ○ |
| 11 | 例題集 (cash 100bb 20 spots) | 8k | なし | — |
| App | 暗算チートシート | 4k | appendix-cheatsheet | ○ |

**流用度の定義**: ○ = 大部分を活かせる（Light 用語・数値の置換のみ）、△ = 構造・概念は参考になるが大幅な書き換えが必要（旧 HandScore/HS → CBS/HP+DP への移行含む）、✗ = スコープ外で新規必要

---

## ch00 — はじめに

**目標字数**: 3k 字
**目的**: Cash 100bb postflop 戦略の全体像を示し、暗算 5-7 秒で決断する読書ロードマップを提示する。

### H2: Vol2 が解く問い — なぜ postflop で迷うか
- H3: 「強さがわからない」「打つべきかわからない」の 2 源
- H3: 本書の解答: CBS 値 1 本 + 25 セル表

### H2: 本書の主役 — Light UCBS v2 と DCBS (cash 版)
- H3: 25 セル表 (5 context × 5 CBS バンド) の概要
- H3: DCBS (cash 版) (HP × 4 context continue freq 表) の概要

### H2: 読み方ガイド — 暗算フロー全体像
- H3: 6 ステップの暗算フロー図
- H3: 各章との対応

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (25 セル表・暗算フロー)
- RESTRUCTURE_PLAN.md (巻間相互参照)

**既存章流用**: なし (新規)

---

## ch01 — CBS の式: HP + DP

**目標字数**: 5k 字
**目的**: CBS = HP + DP の計算方法を習得する。HP テーブル (16 手 → 6 バケット) と DP テーブル (4 段階) を暗記し、任意のハンドで CBS を即算できる状態にする。

### H2: CBS とは何か — Combined Board Score
- H3: HP (Hand Power): 役の強さを 0-9 で表す
- H3: DP (Draw Power): ドローの価値を 0-3 で表す

### H2: HP テーブル (16 手 → 6 バケット)
- H3: 暗記のコツ — 6 値 (2/3/5/7/8/9) の意味
- H3: 例外ハンド (low_pair のケア)

### H2: DP テーブル (4 段階)
- H3: no_draw / gutshot / oesd+fd / combo_draw
- H3: DP の計算が難しいケース (バックドア等)

### H2: CBS バンド — 5 区分への分類
- H3: air (0-2) / weak (3-4) / mid (5-6) / strong (7-8) / nut (9+)
- H3: バンド分類の実戦例 5 つ

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (HP/DP テーブル完全版)
- `ucbs_light_v2.py` (`cbs_band()`, `HP_TABLE`, `DP_TABLE`)
- `ucbs_v2.py` (HP_TABLE / DP_TABLE の元定義)

**既存章流用**: 01-board-types の §1-2 HandScore 部分を参考に概念再説明 (△)

---

## ch02 — Light UCBS の 25 セル表

**目標字数**: 6k 字
**目的**: 5 context × 5 CBS バンドの 25 セル表を完全に習得する。context の切り替え条件と、各セルが意味するものを理解する。

### H2: 25 セル表の全貌
- H3: 表の読み方 (context 行 × band 列)
- H3: % から「打つ/打たない」への変換 (≥50% → bet 推奨)

### H2: 5 context の定義と切り替え
- H3: cash (Cash 100bb SRP)
- H3: mtt_short (MTT ~50bb) / mtt_deep (MTT 100bb+)
- H3: 3bp (3-bet pot、SPR ~5) / turn (ターン 2nd barrel)

### H2: CBS バンド別の傾向分析
- H3: air / weak バンド — どこでも折りたたむか
- H3: strong / nut バンド — slowplay 例外の注意

### H2: low_pair 例外 (-10pt)
- H3: なぜ low_pair だけ特別扱いか
- H3: 適用例と非適用例

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (LIGHT_V2_BASE 全 25 値)
- `ucbs_light_v2.py` (`LIGHT_V2_BASE`, `LIGHT_V2_OFFSET`)

**既存章流用**: 02-cbet-ip の概念骨格を参考 (△、数値は全面置換)

---

## ch03 — Cash 100bb cbet 完全ガイド

**目標字数**: 8k 字
**目的**: Cash context を使った実戦的な cbet 判断を習得する。主要ボード × hand 5 例題で計算フローを体得する。

### H2: Cash context のパラメータ確認
- H3: LIGHT_V2_BASE["cash"] の 5 値
- H3: ボードタイプ (型1-7) との連携

### H2: 暗算フロー — cash cbet 6 ステップ
- H3: Step 1-3: CBS 計算
- H3: Step 4-6: バンド → freq → 判断

### H2: 例題 5 問 (K72r / Q83s / T98s / A♥K♥Q♥ / 777)
- H3: 型1-2 ドライ/ウェット High ボード
- H3: 型3-4 ロー/ウェット ボード
- H3: 型5-7 モノトーン・ペア ボード

### H2: チェック vs ベットの境界線
- H3: mid バンド (CBS 5-6) が最も判断が難しい理由
- H3: GTO Wizard データとの照合 (WRMSE 16.43%)

**主要参照**:
- `findings/light_ucbs_v2_formula.md`
- `findings/cash_5cat_gto.json` (Cash 100bb data)
- `ucbs_light_v2.py` (evaluate_against_v2 結果)

**既存章流用**: 02-cbet-ip の型別判断根拠を参考 (△)

---

## ch04 — ボード読み (型1-7 簡素版)

**目標字数**: 5k 字
**目的**: フロップ 7 分類を素早く見分けられる。ナッツアドバンテージとボードの関係を理解し、Light UCBS のサイズ判断と連動させる。

### H2: ボード 7 分類 — 3 要素で決まる
- H3: トップカード高さ / テクスチャ / ペア有無
- H3: 型1-7 一覧表と代表例

### H2: ナッツアドバンテージの読み方
- H3: SB 有利型 (型1・型2・型6)
- H3: BB 有利型 (型3・型4)

### H2: ボード読み 5 秒ルーチン
- H3: 判定チェックリスト (3 問)
- H3: 曖昧なケースの処理 (型5 モノトーン)

**主要参照**:
- `chapters/01-board-types.md` (流用元、型定義と表)
- `findings/flop_action_logic.md`

**既存章流用**: 01-board-types §1-1 の型分類表を全面流用 (○)

---

## ch05 — サイズ判別 (33% vs Overbet)

**目標字数**: 4k 字
**目的**: polarize ボードを見抜き、適切なベットサイズ (33% or 116%) を選択できる。

### H2: 2 サイズの意味
- H3: 33% = バランス bet (wide range)
- H3: 116% overbet = polarize bet (nuts / air only)

### H2: polarize ボードの 5 条件
- H3: ナッツアドバンテージ大 / ドロー少ない / ボード単調
- H3: 型1 ハイドライ → polarize の代表例
- H3: 型4 ローウェット → 33% バランスの代表例

### H2: CBS バンドとサイズの組み合わせ
- H3: strong / nut バンドでのサイズ選択
- H3: mid バンド (33% 推奨) の理由

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (size 軸の説明)
- `ucbs_v2.py` (`polarize_board()`)

**既存章流用**: 02-cbet-ip §2-1 SRP 決定表の構造を参考 (△)

---

## ch06 — Position 補正 (SB/BTN/CO/HJ/UTG)

**目標字数**: 4k 字
**目的**: ポジション別の CBS freq 補正量を暗記し、SB (OOP) と BTN/CO (IP) での判断の違いを数値で理解する。

### H2: ポジション補正の仕組み
- H3: pos_lift とは何か
- H3: BTN を基準 (0) とした相対補正

### H2: Cash 100bb の pos_lift 値
- H3: SB: -8pt (OOP で不利)
- H3: CO/HJ: +10pt (ワイドレンジ補正)
- H3: UTG: 0 (タイトレンジで補正なし)

### H2: ポジション補正の実戦適用
- H3: SB vs BB 特殊なダイナミクス
- H3: CO/HJ の「wide lift」が生じる理由

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (pos_lift 値)
- `ucbs_v2.py` (O7 position lift)
- UCBS_V2_DCBS_FINAL.md (MTT depth series パラメータ表)

**既存章流用**: なし (新規)

---

## ch07 — 3-bet pot postflop (cash)

**目標字数**: 6k 字
**目的**: 3-bet pot (SPR ~5) での Light UCBS 適用方法を習得する。SPR 低下によるコミット圧力と slowplay 特性の変化を理解する。

### H2: 3bp context の特徴
- H3: SPR ~5 の意味 — コミット判断が近い
- H3: LIGHT_V2_BASE["3bp"] の 5 値解説

### H2: 3bp での暗算フロー
- H3: CBS → 3bp バンド freq の読み方
- H3: mid バンド (CBS 5-6) が 60% と高い理由

### H2: SPR 別の調整
- H3: SPR ≤3 (4-bet pot 相当) の特殊扱い
- H3: SPR 3-7 の中間ゾーン

### H2: 例題 3 問
- H3: QQ on A♠7♦2♣ (3bp)
- H3: KJo on K♠9♥3♦ (3bp)
- H3: 87s on T♠9♠8♦ (3bp)

**主要参照**:
- `chapters/04-cbet-3bp-4bp.md` (SPR 計算・概念)
- `findings/light_ucbs_v2_formula.md` (3bp context)
- UCBS_V2_DCBS_FINAL.md (Tier 3 観察)

**既存章流用**: 04-cbet-3bp-4bp の SPR 計算・コミット概念を流用 (△)

---

## ch08 — DCBS (cash 版): 守備の暗算式

**目標字数**: 6k 字
**目的**: BB が cbet を受けたとき、continue (call + raise) か fold かを HP 別 continue freq 表から即判断できる。

### H2: DCBS の構造
- H3: DCBS_BASE: HP バケット × continue freq (4 値)
- H3: Kicker offset: HP=2 (air) 内の細分化

### H2: Cash 100bb の continue freq 表
- H3: HP=2 (air): 40% continue
- H3: HP=3 (weak pair): 85% continue
- H3: HP=5 (mid pair): 98% continue
- H3: HP=7 (top pair+): 100% continue

### H2: Kicker offset — ace_high と no_made_hand の差
- H3: ace_high: +5pt (45% continue)
- H3: no_made_hand: -3pt (37% continue)
- H3: low_pair: -2pt (38% continue)

### H2: call vs check-raise 配分
- H3: MDF との整合確認
- H3: CR 候補ハンドの選び方

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (DCBS cash_100bb 完全表)
- `dcbs.py` (DCBS_CONTEXTS["cash_100bb"])
- `chapters/06-defense.md` (MDF 概念・HS 閾値構造)

**既存章流用**: 06-defense の MDF 説明・HS 閾値設計を DCBS 版に再構成 (○)

---

## ch09 — Turn 2nd barrel: α=-0.35 シフト

**目標字数**: 5k 字
**目的**: ターンに進んだとき、フロップ freq から -35pt シフトするルールを習得する。Light UCBS の turn context を使って 2nd barrel の判断を暗算する。

### H2: ターンで何が変わるか
- H3: フロップ → ターンの freq シフトルール
- H3: α=-0.35 シフトの直感的意味

### H2: turn context の 25 セル表
- H3: LIGHT_V2_BASE["turn"] の 5 値 (air 5%, nut 40%)
- H3: フロップとの差分

### H2: TA+ / TA- の判定 (簡素版)
- H3: TA+ カード: IP のレンジが強くなるターン
- H3: TA- カード: BB のレンジが強くなるターン

### H2: ストレート / フラッシュ完成ターンの例外
- H3: UCBS の精度低下 (WRMSE 19-28%)
- H3: 例外処理の簡易ルール

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (turn context)
- `chapters/07-turn-barrel.md` (TA+/TA- 定義・実測データ)
- UCBS_V2_DCBS_FINAL.md (Tier 4 観察)

**既存章流用**: 07-turn-barrel の TA 概念・実測データを Light 文脈に簡素化 (△)

---

## ch10 — Multistreet plan

**目標字数**: 6k 字
**目的**: フロップ → ターン → リバーの 3 ストリートを通した「計画」の立て方を習得する。1 手ずつではなく、3 ストリートの連携で期待値を最大化する考え方。

### H2: マルチストリート設計の考え方
- H3: 「フロップの判断」がターン・リバーを縛る理由
- H3: SPR と残りベット回数の関係

### H2: フロップ → ターン の繋がり
- H3: cbet 後 (IP) のバレル / チェックバック判断
- H3: check-back 後 (IP) のターン再開

### H2: ターン → リバー の繋がり
- H3: ターンで call した後のリバー選択
- H3: ポットコミット判定 (SPR < 1)

### H2: 例題 2 問 (マルチストリート通し)
- H3: K♠7♦2♣ → Th → As の 3 ストリート
- H3: T♠9♠8♦ → 7h → Kd の 3 ストリート

**主要参照**:
- `chapters/08-turn-plan-defense.md` (プローブ・donk・defense 3 択)
- `chapters/11-multistreet-plan.md` (API 連鎖・設計手順)
- `chapters/10-river-action.md` (リバー 3 バケット)

**既存章流用**: 08-turn-plan-defense + 11-multistreet-plan を統合・簡素化 (○)

---

## ch11 — 例題集 (cash 100bb 20 spots)

**目標字数**: 8k 字
**目的**: cash 100bb の代表的な 20 スポットで暗算フロー全体を練習する。各問に「CBS 計算 → context → freq → 判断」の解答例を記載する。

### H2: 例題の構成
- H3: 問題形式の説明 (hand / board / position / pot / stack)
- H3: 解答フォーマット

### H2: IP cbet 例題 10 問 (cash SRP)
- H3: 問 1-5: バリュー帯 (CBS 7-9)
- H3: 問 6-10: 境界帯 (CBS 4-6)

### H2: OOP defense 例題 5 問
- H3: 問 11-15: DCBS continue freq 適用

### H2: 3bp / Turn 例題 5 問
- H3: 問 16-18: 3bp context
- H3: 問 19-20: turn context

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (全公式・数値)
- `findings/cash_5cat_gto.json` (実データで問題作成)
- `findings/cash_defense_gto.json`

**既存章流用**: なし (新規生成)

---

## App — 暗算チートシート

**目標字数**: 4k 字
**目的**: 全 12 章の核心公式を 1-2 ページにまとめた横断参照表。実戦中に参照できる。

### H2: CBS 計算表 (HP + DP)
- H3: HP テーブル 16 手 → 6 バケット
- H3: DP テーブル 4 段階

### H2: Light UCBS 25 セル表 (5 context × 5 band)
- H3: % 表 (パーセント形式)
- H3: 「打つ (≥50%)/打たない (<50%)」二値化版

### H2: DCBS (cash 版) — cash 100bb continue freq 表
- H3: HP=2/3/5/7 の continue freq
- H3: Kicker offset (ace_high/king_high/no_made_hand/low_pair)

### H2: 補正まとめ
- H3: pos_lift 4 値 (SB / BTN / CO-HJ / UTG)
- H3: ターン シフト -35pt
- H3: 例外 3 ルール (型6 up / mono down / low_pair -10)

**主要参照**:
- `findings/light_ucbs_v2_formula.md` (全数値の単一情報源)

**既存章流用**: appendix-cheatsheet の表構造を参考 (○、数値は全置換)

---

## 既存章 → 新章 流用判定サマリ

| 既存章 | 新 ch | 流用度 | 主な変更点 |
|---|---|---|---|
| 01-board-types | ch04 (+ ch01 一部) | ○ | 型定義表を全流用。HandScore → CBS への用語置換 |
| 02-cbet-ip | ch02, 03, 05 | △ | HS バケット → CBS バンド / 旧表数値を全置換 |
| 03-cbet-oop-donk | (省略) | ✗ | Light スコープ外 |
| 04-cbet-3bp-4bp | ch07 | △ | SPR 計算・コミット概念を流用、数値を DCBS に置換 |
| 05-cbet-multiway | (省略) | ✗ | Vol2 スコープ外 |
| 06-defense | ch08 | ○ | MDF 概念を流用、HS 閾値 → DCBS continue freq に置換 |
| 07-turn-barrel | ch09 | △ | TA 概念を流用、α=-0.35 主体に簡素化 |
| 08-turn-plan-defense | ch10 (統合) | ○ | 3 シナリオ構造を流用 |
| 09-river-alpha | (ch10 に統合) | △ | α 式の説明のみ ch10 末尾に簡素収録 |
| 10-river-action | (ch10 に統合) | △ | 3 バケット概念を ch10 末尾に簡素収録 |
| 11-multistreet-plan | ch10 (統合) | ○ | API 連鎖構造を参考、読者向けに平易化 |
| appendix-cheatsheet | App | ○ | 表構造を流用、全数値を Light UCBS/DCBS に置換 |

**全体**: 既存 12 章のうち 7 章が「○/△」で流用可能。03/05 章のみ完全省略。

---

## 次ステップ (Phase 3 開始前チェックリスト)

- [ ] `findings/light_ucbs_v2_formula.md` 作成 (Task #66)
- [ ] `findings/terminology.md` 作成 (Task #67)
- [ ] ch00 から順番に generator で執筆開始 (Task #68〜)
- [ ] 各章の主要参照ファイルが存在するか確認
  - `findings/cash_5cat_gto.json` ✓
  - `findings/cash_defense_gto.json` ✓
  - `mtt-postflop/findings/draw_study_*.jsonl` (vol3 ディレクトリに存在)
