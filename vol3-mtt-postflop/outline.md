# Vol3 MTT Postflop + Full UCBS-v2 アウトライン

作成日: 2026-05-28
基準: RESTRUCTURE_PLAN.md L101-122 + UCBS_V2_DCBS_FINAL.md (2026-05-28)
合計: ~125k 字、16 章 + 3 付録

---

## 章構成一覧

| 章 | ファイル名（新規生成先） | タイトル | 目標字数 |
|---|---|---|---:|
| 00 | 00-introduction.md | はじめに——Full UCBS-v2 で MTT を制する | 4k |
| 01 | 01-five-axes.md | Full UCBS-v2 の 5 軸——HP・DP・Confidence・Size・Context | 8k |
| 02 | 02-confidence.md | Confidence の判定——型 1-7 × 距離 × 例外 | 6k |
| 03 | 03-size.md | Size 軸——33% vs Overbet 116% の選択基準 | 5k |
| 04 | 04-context-switch.md | Context スイッチング——13 context の使い分け | 6k |
| 05 | 05-position-lift.md | Position lift——SB/BTN/CO/HJ/UTG の補正 | 4k |
| 06 | 06-mtt-25bb.md | MTT 25bb 終盤 cbet——push 圏直前の戦略 | 8k |
| 07 | 07-mtt-50bb.md | MTT 50bb 中盤 cbet——バブル前の主戦場 | 8k |
| 08 | 08-mtt-100bb.md | MTT 100bb 序盤 cbet——wide cbet の特殊性 | 8k |
| 09 | 09-mtt-200bb.md | MTT 200bb 深スタック cbet——FT 直後の深打ち | 6k |
| 10 | 10-3bp-series.md | 3BP IP SPR シリーズ——20/25/50/100bb の差 | 10k |
| 11 | 11-turn-cbet.md | Turn cbet 4 context——α=-0.35 シフトと context 別調整 | 8k |
| 12 | 12-full-dcbs.md | Full DCBS——4 context の守備 continue freq | 8k |
| 13 | 13-exceptions.md | 例外ルール 4 つ——型6/mono/A-x/turn-shift | 5k |
| 14 | 14-limitations.md | 苦手領域と限界——MTT 100bb とストレート完成 turn | 4k |
| 15 | 15-icm.md | ICM 補正——バブル/FT の調整（取得可能範囲） | 6k |
| 16 | 16-examples.md | 例題集——MTT 各 depth × SBR スイッチ練習 | 10k |
| App A | appendix-a-params.md | 付録 A: 13 context パラメータ完全表 | 5k |
| App B | appendix-b-dcbs.md | 付録 B: Full DCBS 4 context continue freq 表 | 3k |
| App C | appendix-c-cheatsheet.md | 付録 C: UCBS-v2 公式チートシート | 3k |

---

## 章別詳細

### ch00 はじめに (4k)

**目標**: Vol2 読了者が Vol3 を手に取る理由と、Full UCBS-v2 が解くものを明示する。

#### H2 見出し
1. この本が解く問題——Cash と MTT のポストフロップは何が違うか
2. Full UCBS-v2 とは——Light v2 との違いと 5 軸の概観
3. 本書の読み方——前提知識と各章の位置づけ
4. シリーズ全体図——Vol1〜Vol4 の連携

#### H3 見出し
- 1.1 MTT 固有のスタック深度分布（SBR 分布）
- 1.2 13 context が必要な理由
- 2.1 Light v2 (5 context) と Full v2 (13 context) の精度比較
- 2.2 本書の暗記対象数（~128 数値 + 1 式 + 4 例外）
- 3.1 前提用語の確認（HP/DP/CBS/型1-7/MDF）

**主要参照**: `vol3-mtt-postflop/chapters/00-introduction.md`（既存）、`UCBS_V2_DCBS_FINAL.md`
**既存章流用**: ○ 流用 + Full UCBS-v2 言及追加（序盤 2 節はほぼ流用可）

---

### ch01 Full UCBS-v2 の 5 軸 (8k)

**目標**: HP・DP・Confidence・Size・Context の概念を数値込みで解説する。

#### H2 見出し
1. CBS = HP + DP——ポストフロップの「強さの足し算」
2. Confidence——ボード読みの信頼度 3 段階
3. Size——33% か 116% の 2 択
4. Context——13 種類のスイッチ
5. 統一式——5 軸をひとつの式にまとめる

#### H3 見出し
- 1.1 HP テーブル（16 hand → 6 バケット）の読み方
- 1.2 DP テーブル（4 段階）の意味
- 2.1 HIGH/MID/LOW の判定フロー
- 2.2 base_freq 6 セル（70/45/40/30/25/25）
- 3.1 polarize_enabled フラグ（cash のみ true）
- 3.2 Overbet 加算ルール（HIGH+20 / MID+15）
- 4.1 13 context の分類（Tier 0/1/3/4）
- 5.1 freq = base + α + β·I(CBS≥7) + offset + pos_lift + ax_lift

**主要参照**: `vol2-cash-postflop/ucbs_v2.py`（HP_TABLE/DP_TABLE/BASE_FREQ/統一式）、`UCBS_V2_DCBS_FINAL.md`
**既存章流用**: ✗ 全面新規（旧 02-cbs-system はシステムが異なる）

---

### ch02 Confidence の判定 (6k)

**目標**: 距離 + 型1-7 → HIGH/MID/LOW を実戦で即座に出せるようにする。

#### H2 見出し
1. CBS 距離の読み方——T=5 からの乖離
2. 型1-7 ×距離 → Confidence 分類表
3. 例外ルールの事前予告——型6 up と mono down
4. 実戦フロー——5 秒で Confidence を決める

#### H3 見出し
- 1.1 Distance = |CBS - T| の 3 区分（0, 1, 2, 3+）
- 2.1 型1（HIGH 有利）/ 型7（HIGH 独特）の特殊ルール
- 2.2 型5 = MID 固定の理由
- 3.1 型6 up の GTO 根拠
- 4.1 ボード → 型 → 距離 → Confidence の計算例（5 例）

**主要参照**: `vol2-cash-postflop/ucbs_v2.py`（calc_confidence / apply_confidence_exception）
**既存章流用**: ✗ 旧 02-cbs-system に類似の型分類あり、数値体系が異なるため新規

---

### ch03 Size 軸 (5k)

**目標**: 33% と 116% をフロップ上で即判定できる。

#### H2 見出し
1. Polarize 板の 5 条件——overbet が機能する形
2. サイズ選択の優先順位——context のフラグを確認する
3. Overbet 加算のメカニズム——+20 / +15 の意味
4. MTT では overbet 不使用——polarize_enabled=False の理由

#### H3 見出し
- 1.1 mid-rank connected（高 card < 9）条件
- 1.2 K-high spread × J 以上 mid の条件
- 1.3 A-high ミッドカード spread の条件
- 2.1 cash_100bb のみ polarize_enabled=True
- 3.1 base_freq × size の 8 セル早見表

**主要参照**: `vol2-cash-postflop/ucbs_v2.py`（is_polarize_board / BASE_FREQ overbet セル）
**既存章流用**: ✗ 新規

---

### ch04 Context スイッチング (6k)

**目標**: 13 context を「どの状況でどれを選ぶか」の木構造で覚える。

#### H2 見出し
1. Context 選択の木——SRP か 3BP か Turn かで分岐
2. Tier 0: cash_100bb——基準 context
3. Tier 1: MTT depth 4 種——25/50/100/200bb の差
4. Tier 3: 3BP IP 4 種——SPR が支配する世界
5. Tier 4: Turn 4 context——α=-0.35 の意味

#### H3 見出し
- 1.1 context 選択フロー図（テキスト表現）
- 2.1 cash_100bb が基準 context である理由
- 3.1 depth 系列の α 変動（+15 @ 100bb 異常値）
- 3.2 SB lift の depth 依存（-10 → -34）
- 4.1 3BP SPR と linear vs polarize の転換点（SPR≈5）
- 5.1 ターン進行 = α -35 シフトのルール

**主要参照**: `UCBS_V2_DCBS_FINAL.md` Tier 1/3/4 節、`vol2-cash-postflop/ucbs_v2.py` CONTEXTS 辞書
**既存章流用**: ○ 旧 01-sbr-to-spr の SPR 概念を前半に流用可

---

### ch05 Position lift (4k)

**目標**: SB/BTN/CO/HJ/UTG の pos_lift 値を覚えて補正を即適用できる。

#### H2 見出し
1. 基準は BTN（0）——ポジション別の lift 一覧
2. SB の特殊性——OOP opener はなぜ大幅マイナスか
3. Wide lift（CO/HJ/UTG）——レンジが広いほど bet が増える理由
4. MTT depth 別の pos_lift 変動

#### H3 見出し
- 1.1 context 別 pos_lift 表（mtt_25/50/100/200bb × 5 positions）
- 2.1 SB lift: mtt_25=-10, mtt_50=-29, mtt_200=-34（depth で増幅）
- 3.1 wide lift: mtt_25=+13, mtt_100=+17（MTT序盤ほど積極的）
- 4.1 3BP / turn context は pos_lift=0（位置均一）

**主要参照**: `vol2-cash-postflop/ucbs_v2.py` pos_lift 各 context
**既存章流用**: ✗ 新規

---

### ch06 MTT 25bb 終盤 cbet (8k)

**目標**: push 圏直前（SBR 20-25）での cbet 判断を実戦例で体得する。

#### H2 見出し
1. 25bb context の特徴——α=+6, β=+31
2. Slowplay の特殊性——-28 という強烈な抑制
3. SB lift -10 と wide lift +13
4. A-x range bet (+30) が効く条件
5. 実戦例題 5 問

#### H3 見出し
- 1.1 WRMSE 15.46%——25bb は最初に習得すべき context
- 2.1 セット/ツーペア/ストレートが check する理由（SPR 圧迫）
- 3.1 SB からの cbet 頻度の低さ（BTN との差）
- 4.1 A-high paired/dry の判定条件（gap≥8 or paired）
- 5.1 例題①〜⑤ 解説

**主要参照**: `knowledges/gto_wizard_study/draw_study_MTT25BB関連.jsonl`、既存 07-short.md
**既存章流用**: △ 旧 07-short の SBR/SPR 対応表を流用、cbet 数値は更新

---

### ch07 MTT 50bb 中盤 cbet (8k)

**目標**: バブル前の主戦場（SBR 40-60）での cbet を UCBS-v2 で体得する。

#### H2 見出し
1. 50bb context の特徴——α=-4, β=+19、精度 WRMSE 12.96%
2. SB lift -29 の衝撃——なぜここまで控えめか
3. Trash の激減——low_pair は -35 で徹底 check
4. Wide lift が 0——ポジション均等化の理由
5. 実戦例題 5 問

#### H3 見出し
- 1.1 50bb が全 context 中 最高精度の理由
- 2.1 50bb SB: ICM プレッシャーによる OOP 抑制
- 3.1 low_pair = 実質 fold 方向（-35 → 全頻度 ~20%）
- 4.1 CO/HJ/UTG の pos_lift=0（cash の +10 との違い）
- 5.1 例題①〜⑤ 解説

**主要参照**: `knowledges/gto_wizard_study/draw_study_MTT50BB.jsonl`、既存 06-middle.md
**既存章流用**: △ 旧 06-middle の深さ別概念を流用、数値は全面更新

---

### ch08 MTT 100bb 序盤 cbet (8k)

**目標**: MTT 序盤（SBR 80-100）の wide cbet 特性を理解し、精度限界を認識する。

#### H2 見出し
1. 100bb context の異常値——α=+15 という突出した特徴
2. WRMSE 21.95%——精度が低い理由と対処法
3. Wide lift +17——序盤ほど広くベットする理由
4. A-x range bet +28——序盤でも継続する range bet
5. 実戦例題 4 問

#### H3 見出し
- 1.1 MTT6mSimple tree の wide cbet 特性
- 2.1 WRMSE 20%+ は「信頼度低めで使う」シグナル
- 3.1 CO/HJ/UTG の wide=+17（vs 25bb の +13）
- 4.1 序盤は ICM 小さく range bet が成立する条件
- 5.1 例題①〜④ + 限界ケース（WRMSE 高いケース）

**主要参照**: `knowledges/gto_wizard_study/draw_study_MTT100BB.jsonl`
**既存章流用**: △ 旧 04-deep.md の序盤コンセプト流用可、数値は全面更新

---

### ch09 MTT 200bb 深スタック cbet (6k)

**目標**: FT 直後など深スタック（SBR 150+）での cbet 判断を習得する。

#### H2 見出し
1. 200bb context の特徴——α=-4, β=+11、SB lift -34
2. 50bb との構造的類似
3. Slowplay の穏やかな抑制——-15 (50bb の -12 と近い)
4. 実戦例題 3 問

#### H3 見出し
- 1.1 WRMSE 14.10%——200bb の信頼性
- 2.1 「深」= SB はよりフォールド傾向、wide は変化なし
- 3.1 200bb でもセット/ストレートは check 有力
- 4.1 例題①〜③

**主要参照**: `knowledges/gto_wizard_study/draw_study_MTT200BB.jsonl`
**既存章流用**: △ 旧 04-deep.md の後半流用可

---

### ch10 3BP IP SPR シリーズ (10k)

**目標**: 3BP IP での 4 深度（20/25/50/100bb）の違いを体系的に理解する。

#### H2 見出し
1. 3BP の SPR——4 深度の対応表
2. 20/25bb（低 SPR）——linear range の middle bet
3. 50bb（深 SPR、最高精度）——polarize への転換
4. 100bb（deep polarize）——premium 大幅 up
5. 実戦フロー——まず SPR を確認してから context 選択

#### H3 見出し
- 1.1 SPR 対応表（20bb=2.5 / 25bb=2.7 / 50bb=5.5 / 100bb=11）
- 2.1 20bb: trash=-3（ほぼ bet）、slowplay=-40（check 有力）
- 2.2 25bb: slowplay=-66（最強の抑制）の理由
- 3.1 50bb で WRMSE 8.62%——なぜ最高精度か
- 4.1 100bb: premium=+20、trash=-48 の両極化
- 5.1 「SPR≤3 = linear, SPR≥5 = polarize」の判断木

**主要参照**: `knowledges/gto_wizard_study/draw_study_3BP*.jsonl`、既存 12-3bp.md
**既存章流用**: ✗ 旧 12-3bp は旧体系（CBS閾値53%方式）、UCBS-v2 ベースで全面書き換え

---

### ch11 Turn cbet 4 context (8k)

**目標**: ターン 2nd barrel を UCBS-v2 の α シフトで定量化する。

#### H2 見出し
1. Flop → Turn 変換ルール——α -35, β 廃止
2. 4 context 比較——25/50/100bb_turn + cash_turn
3. Trash の変化——turn では low_pair も一部 bet 有力
4. 完成役 turn card の例外処理
5. 実戦例題 5 問

#### H3 見出し
- 1.1 α -35 の意味（全体 bet 率が 35pt 低下）
- 1.2 β 廃止の意味（強い役への追加 lift が消える）
- 2.1 mtt_25bb_turn: WRMSE 7.02%、最高精度 context
- 2.2 mtt_100bb_turn: WRMSE 26.95%（フロップと同様に精度低）
- 3.1 off_trash: -23 → -1 (ターンは low_pair も bet 増える)
- 4.1 ストレート/フラッシュ完成 turn の特殊判定（WRMSE 19-28%）
- 5.1 例題①〜⑤

**主要参照**: `knowledges/gto_wizard_study/draw_study_TURN_*.jsonl`、既存 14-turn-river.md
**既存章流用**: △ 旧 14-turn-river の TA フレームワーク概念は参考可、数値体系は刷新

---

### ch12 Full DCBS (4 context) (8k)

**目標**: BB defense の continue freq を 4 context × HP × kicker で即算できる。

#### H2 見出し
1. DCBS の構造——HP バケット × context の 2 段テーブル
2. depth で反転する defense 戦略——「深いほど fold」
3. Kicker offset——HP=2 内の ace_high / king_high 細分化
4. DCBS vs MDF——GTO 根拠の確認
5. 実戦例題 5 問

#### H3 見出し
- 1.1 DCBS 式: continue_freq = base[HP] + kicker_offset[hand]
- 2.1 mtt_25bb: air=67%、mtt_100bb: air=28%（2.4 倍の差）
- 2.2 top_pair 以上は 96%+ で変わらない（コンテキスト共通）
- 3.1 ace_high: +10 (25bb) → +5 (100bb)（kicker 効果が depth で減衰）
- 4.1 MDF 計算（ポットサイズ ÷ (ポット + bet)）との対応
- 5.1 例題①〜⑤（4 context をそれぞれ扱う）

**主要参照**: `vol2-cash-postflop/dcbs.py`（DCBS_CONTEXTS）、`UCBS_V2_DCBS_FINAL.md` DCBS 節
**既存章流用**: ✗ 旧 05-flop-defense は旧体系、DCBS ベースで全面書き換え

---

### ch13 例外ルール 4 つ (5k)

**目標**: 4 例外を「出現条件 + 適用方法 + 覚え方」で確実に覚える。

#### H2 見出し
1. 例外ルール一覧——4 つの補正と適用タイミング
2. 例外①: 型6 信頼度 up——mid 連結ウェット板
3. 例外②: mono board 信頼度 down（cash のみ）
4. 例外③: A-x range bet (+30, MTT BTN/CO のみ)
5. 例外④: turn shift——α -35, β 廃止

#### H3 見出し
- 2.1 型6 = ペア rank≥Q の判定条件と GTO 根拠
- 2.2 LOW→MID / MID→HIGH のシフト効果
- 3.1 mono board で cash のみ down する理由（polarize range が narrow）
- 4.1 A-high paired or gap≥8 の判定条件（is_ax_dry_or_paired）
- 5.1 フロップ → ターン移行時の自動 α シフト

**主要参照**: `vol2-cash-postflop/ucbs_v2.py`（apply_confidence_exception / is_ax_dry_or_paired）、`UCBS_V2_DCBS_FINAL.md` 例外節
**既存章流用**: ✗ 新規（旧章に対応する章なし）

---

### ch14 苦手領域と限界 (4k)

**目標**: UCBS-v2 が不正確な状況を正直に示し、実戦での過信を防ぐ。

#### H2 見出し
1. WRMSE 20%+ の context——何が難しいか
2. MTT 100bb の wide cbet 問題
3. ストレート/フラッシュ完成 turn の特殊性
4. フレームワーク外の状況——マルチウェイ・OOP bet

#### H3 見出し
- 1.1 精度帯分布（<10% / 10-15% / 15-20% / 20%+）
- 2.1 MTT6mSimple tree が 33/116% しか選択しない問題
- 3.1 完成役 turn: KJT+Q で WRMSE 28%、T98+7 で 19%
- 4.1 本書のスコープ（BTN/CO/HJ/UTG IP cbet、BB defense）

**主要参照**: `UCBS_V2_DCBS_FINAL.md` 構造的限界節
**既存章流用**: ✗ 新規

---

### ch15 ICM 補正 (6k)

**目標**: バブルと FT での cbet 頻度調整を数値で示す。

#### H2 見出し
1. ICM とは——チップ EV vs $EV の乖離
2. バブルでの cbet 調整——全体 -5〜-15pt
3. FT での cbet 調整——賞金差 × スタック位置
4. UCBS-v2 との統合——context 選択後に ICM 補正を加える

#### H3 見出し
- 1.1 バブル ICM 係数の GTO 観察値
- 2.1 ショートスタック vs ビッグスタックのバブル戦略差
- 3.1 FT 9人残 vs 5人残の補正差
- 4.1 「UCBS-v2 freq × (1 - ICM 係数)」の概算式

**主要参照**: `knowledges/gto_wizard_study/phase2_icm_stages.jsonl`、既存 10-bubble.md / 11-final-table.md
**既存章流用**: △ 旧 10-bubble / 11-final-table の ICM 概念流用、UCBS-v2 統合は新規

---

### ch16 例題集 (10k)

**目標**: MTT の各 depth/SBR でのフル判定練習（20 問）。

#### H2 見出し
1. 問題の使い方——context 選択 → CBS → Confidence → freq の 4 ステップ
2. 問題 1〜5: SRP 25bb（終盤）
3. 問題 6〜10: SRP 50bb（中盤）
4. 問題 11〜15: 3BP（SPR 別）
5. 問題 16〜20: Turn cbet

#### H3 見出し
- 2.1 解答①〜⑤ 詳解
- 3.1 解答⑥〜⑩ 詳解
- 4.1 解答⑪〜⑮ 詳解（3 種 SPR を含む）
- 5.1 解答⑯〜⑳ 詳解（α シフト適用確認）

**主要参照**: 各 context の draw_study_*.jsonl
**既存章流用**: ○ 旧 15-quiz.md の問題形式を流用、内容は UCBS-v2 ベースで全面更新

---

### 付録 A: 13 context パラメータ完全表 (5k)

**目標**: 執筆・実戦両用の数値リファレンス。

#### H2 見出し
1. UCBS-v2 共通テーブル（HP/DP/BASE_FREQ）
2. Tier 0 + Tier 1: cash + MTT depth 5 context 表
3. Tier 3: 3BP IP 4 context 表
4. Tier 4: Turn 4 context 表

**主要参照**: `UCBS_V2_DCBS_FINAL.md`、`vol2-cash-postflop/ucbs_v2.py` CONTEXTS
**既存章流用**: △ 旧 appendix.md の早見表形式を流用、全数値を更新

---

### 付録 B: Full DCBS 4 context continue freq 表 (3k)

**目標**: DCBS 全数値の 1 ページ早見表。

#### H2 見出し
1. HP 別 base freq 表（4 context × HP 4 段階）
2. Kicker offset 表（HP=2 の手 × 4 context）
3. 計算例（3 問）

**主要参照**: `vol2-cash-postflop/dcbs.py` DCBS_CONTEXTS

---

### 付録 C: UCBS-v2 公式チートシート (3k)

**目標**: 実戦で 30 秒以内に参照できる 1 枚。

#### H2 見出し
1. 5 軸の統一式
2. HP/DP テーブル（暗記用コンパクト版）
3. Confidence 判定フロー（型 × 距離）
4. 例外ルール 4 箇条

---

## 既存章との流用判定サマリ

| 既存 ch（vol3-mtt-postflop） | 新 ch | 流用度 | 判定根拠 |
|---|---|---|---|
| 00-introduction.md | ch00 | ○ 流用 | SPR/SBR 説明の前半は流用可。Full UCBS-v2 言及を後半に追加 |
| 01-sbr-to-spr.md | ch04 Context | ○ 流用 | SPR の計算・概念を context 選択の導入として流用 |
| 02-cbs-system.md | ch01 5 軸 | ✗ 書き換え | HP テーブル値が旧体系と異なる（旧: エアー HP=5） |
| 03-icm-postflop.md | ch15 ICM | △ 部分流用 | ICM 概念は流用可、UCBS-v2 との統合式は新規 |
| 04-deep.md | ch09 200bb | △ 部分流用 | deep スタックのコンセプト流用可、数値は更新 |
| 05-flop-defense.md | ch12 DCBS | ✗ 書き換え | 旧体系（MDF/commit line 方式）→ DCBS に全面移行 |
| 06-middle.md | ch07 50bb | △ 部分流用 | 50bb の中盤コンセプト流用可、cbet 数値は更新 |
| 07-short.md | ch06 25bb | △ 部分流用 | 25bb の終盤コンセプト流用可 |
| 08-very-short.md | (省略) | ✗ スコープ外 | Vol3 では SBR<10 は別 context なし |
| 09-midgame.md | (省略) | ✗ スコープ外 | Vol1/プリフロップ側で扱う内容 |
| 10-bubble.md | ch15 ICM | △ 部分流用 | バブル補正概念は流用可 |
| 11-final-table.md | ch15 ICM 統合 | △ 部分流用 | FT 補正概念は流用可 |
| 12-3bp.md | ch10 3BP | ✗ 書き換え | 旧体系（「ナッツだけ check/アーチ型」）→ UCBS-v2 4 context に |
| 13-multiway.md | (省略) | ✗ スコープ外 | Vol3 のスコープ外（マルチウェイは ch14 限界節で言及） |
| 14-turn-river.md | ch11 Turn | △ 部分流用 | TA フレームワーク概念は参考可、Turn context 数値は新規 |
| 15-quiz.md | ch16 例題集 | ○ 流用 | 問題形式・解答形式を流用、数値は UCBS-v2 ベースに更新 |
| appendix.md | App A-C | △ 分割 | 旧付録を 3 つに分割、数値を全面更新 |

**流用率サマリ**:
- ○ (ほぼ流用): 3 章（00, 01→04, 15→16）
- △ (部分流用): 7 章（03, 04, 06, 07, 10, 11, 14 + appendix）
- ✗ (新規/書き換え): 6 章（02, 05, 08, 09, 12, 13）+ 省略 4 章

約 30% 流用 + 70% 新規（RESTRUCTURE_PLAN.md 見通しと一致）。

---

## Vol2 との重複範囲と Vol3 の差別化

| テーマ | Vol2 (Light) の扱い | Vol3 (Full) の差別化 |
|---|---|---|
| HP/DP/CBS | 定義・解説 (ch01) | 共通定義を前提として省略 |
| Confidence | 距離 × 型 の基礎 (ch02 内) | 全 7 型 × 距離 の完全分類表 |
| Size | 33% vs Overbet の原則 (ch05) | polarize_enabled=False (MTT) の理由を深掘り |
| Context | 5 context (Light v2) | 13 context を Tier 別に完全展開 |
| MTT depth | mtt_short / mtt_deep の 2 分類 | 25/50/100/200bb を個別章で詳解 |
| 3BP | 1 章 + 簡素表 (ch07) | 4 SPR ×パラメータ全数値 (ch10) |
| Turn | α=-0.35 シフトのみ (ch09) | 4 context × turn 完全パラメータ (ch11) |
| DCBS | cash_100bb 主体 + MTT 参照 (ch08) | 4 context 全数値 + kicker 表 (ch12) |
| 例外ルール | 型6 up / mono down のみ簡述 | 4 例外を章立て (ch13) |
| 精度・限界 | 言及なし | ch14 で WRMSE 分布を明示 |
| ICM | (Vol3 に委ねる) | ch15 で UCBS-v2 × ICM の統合式 |

**Vol3 の差別化核心**: 「同じ式・同じ HP/DP だが、context の粒度が 13 種あり、深度 × SPR × turn の完全パラメータを扱う」。読者は Vol2 を読んでから Vol3 に進むことで「なぜ MTT では数値が違うのか」を定量的に理解できる。
