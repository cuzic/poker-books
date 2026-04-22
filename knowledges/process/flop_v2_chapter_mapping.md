# フロップ編 v2 新旧章マッピング

旧 30 章構成から新 19 章 + 付録構成への対応表。

## 変更の基本方針

1. **第I部 (7章)** を「型 + アクションプラン」中心に新規・再編
2. **第II部 (11章)** を「% で柔軟化」中心に既存章を統合・スリム化
3. **第19章** は「巻3 へのブリッジ」として新規執筆
4. **上級内容** (旧27-28章の詳細、ターン深掘り) は巻3 用ドラフトに退避
5. **付録** は 7 型早見表と 169 ハンド × 型別アクション表を新設

## 新旧対応表

| 新章 | 新タイトル | 対応元 (旧) | 作業種別 |
| --- | --- | --- | --- |
| 序 | はじめに (3段階学習法) + 用語 | 旧00 + 旧02 | 統合・軽量化 |
| 第1章 | ポーカーは技術で勝つ (全体像) | 旧01 flop-ev-variance | スリム化 |
| 第2章 | 誰がリードしているか (レンジ引継ぎ) | 旧03 preflop-range-carryover | ほぼ流用 |
| 第3章 | ボードを 7 型に分類する ★ | 旧05 前半 + 旧04 の一部 | **新規執筆** |
| 第4章 | 型別アクションプラン ★ | 旧07 cbet-three-purposes の精神 | **新規執筆** |
| 第5章 | ハンドを強・中・弱に分ける (簡易 HS) | 旧08 hand-score-flop | スリム化 |
| 第6章 | アウツとエクイティ基礎 | 旧06 outs-and-equity | ほぼ流用 |
| 第7章 | 第I部ドリル 10 問 | 旧23 flop-drill の前半 | 選別・再構成 |
| 第8章 | D3 チェックリスト (型 → %) | 旧05 board-score (既に D3 化済) | 流用 |
| 第9章 | HandScore の精緻化 | 旧08 hand-score-flop の詳細部分 | スリム化 |
| 第10章 | 9 マスマトリクス | 旧09 cbet-integration (既に 9マス化済) | 流用 |
| 第11章 | CBet サイズ選択 (33/50/75%) | 旧10 cbet-sizing | 流用 |
| 第12章 | GTO との乖離 | 旧11 gto-gap-cbet + 旧16 gto-gap-defense | 統合 |
| 第13章 | ポットオッズと防衛 | 旧12 pot-odds-defense + 旧13 call-fold-boundary | 統合 |
| 第14章 | チェックレイズ・ドンクベット | 旧14 check-raise + 旧15 donk-bet | 統合 |
| 第15章 | SPR とスタック深度 | 旧17 spr-strategy | 流用 |
| 第16章 | マルチウェイと 3bet ポット | 旧18 multiway-flop + 旧19 3bet-pot | 統合 |
| 第17章 | 相手タイプ別の調整 | 旧20 opponent-adjustment | 流用 |
| 第18章 | レンジ・ナッツアドバンテージ + 動的レンジ | 旧21 dynamic-range + 旧22 range-advantage | 統合 |
| 第19章 | 巻3 へのブリッジ ★ | 旧24 cheatsheet + 旧25 + 旧26 の精神 | **新規執筆** |
| 付録 | (下記参照) | 旧29 appendix | 再編 |

## 付録の再編

| 新付録 | 内容 | 対応元 (旧) | 作業 |
| --- | --- | --- | --- |
| A | 参考文献・謝辞 | 旧付録0 | 流用 |
| B | 7 型判定早見表 (代表 50 ボード) | **新設** | 新規 |
| C | D3 完全仕様 (Lite / Standard) | 新設 (モデル仕様書から抜粋) | 新規 |
| D | BDM v5 完全係数表 **のみ** | 旧付録L の BDM 部分を 2-3ページに簡約 | 大幅削減 |
| E | 主要ドロー完成率 + Rule of 2/4 | 旧付録E (数式まとめの一部) | 流用 |
| F | 169 ハンド × 型別 アクション一覧 | **新設** (旧付録B を刷新) | 新規 |
| G | よくある誤解 Q&A | 旧付録C | 流用 |
| H | 用語集 | 旧付録D | 流用 |
| I | 出典・再現性 | 旧付録K | 流用 |

## 巻3 用ドラフトに退避するもの

以下を `~/poker-books/volume3-draft/` に移動:

- 旧27 middle-mix-rules.md → 巻3 の「第I部: 混合戦略 R1-R6」の土台
- 旧28 advanced-formula.md → 巻3 の「第I部: BDM v5 完全解説」の土台
- 旧付録H (3バンド早見) → 巻3 付録
- 旧付録I (R4 フロー) → 巻3 付録
- 旧付録J (R6-R7 チートシート) → 巻3 付録
- 旧付録L (BDM v5 詳細検証) → 巻3 付録
- 旧付録M (HUD 統計からの E 補正) → 巻3 付録
- 旧25 turn-bridge.md → 巻3 の「第II部: ターン」の土台
- 旧26 gto-roadmap.md → 巻3 の「第IV部: GTO 統合」の土台

## 章ファイルのリネーム計画

```
# 削除 (巻3へ退避)
25-turn-bridge.md         → volume3-draft/
26-gto-roadmap.md         → volume3-draft/
27-middle-mix-rules.md    → volume3-draft/
28-advanced-formula.md    → volume3-draft/

# リネーム (既存内容を新章番号へ)
00-introduction.md        (そのまま)
01-flop-ev-variance.md    → 01-poker-is-skill.md
02-flop-terms.md          → (序に統合、削除)
03-preflop-range-carryover.md → 02-who-leads.md
04-common-flop-mistakes.md → (第3章の素材に吸収、削除)
05-board-score.md         → 08-d3-checklist.md
06-outs-and-equity.md     → 06-outs-equity.md
07-cbet-three-purposes.md → (第4章と統合、削除)
08-hand-score-flop.md     → 09-hand-score-detailed.md (詳細版)
09-cbet-integration.md    → 10-matrix-9cell.md
10-cbet-sizing.md         → 11-cbet-sizing.md
11-gto-gap-cbet.md        → 12-gto-gap.md (+ 旧16を統合)
12-pot-odds-defense.md    → 13-pot-odds-defense.md (+ 旧13を統合)
13-call-fold-boundary.md  → (12と統合、削除)
14-check-raise.md         → 14-check-raise-donk.md (+ 旧15を統合)
15-donk-bet.md            → (14と統合、削除)
16-gto-gap-defense.md     → (12と統合、削除)
17-spr-strategy.md        → 15-spr.md
18-multiway-flop.md       → 16-multiway-3bet.md (+ 旧19を統合)
19-3bet-pot.md            → (16と統合、削除)
20-opponent-adjustment.md → 17-opponent-adjust.md
21-dynamic-range.md       → 18-range-adv-dynamic.md (+ 旧22を統合)
22-range-advantage.md     → (18と統合、削除)
23-flop-drill.md          → 07-drill-beginner.md (前半部分のみ初心者ドリル)
24-cheatsheet.md          → (削除、要点を第19章と付録へ移動)
29-appendix.md            → 20-appendix.md

# 新規執筆
(new) 03-board-seven-types.md    # ★
(new) 04-action-plans.md         # ★
(new) 05-hand-strength-basic.md  # ★ (旧08のスリム版)
(new) 19-bridge-to-volume3.md    # ★
```

## 注意点

- リネーム時は内部の章参照 (「第X章参照」) も全て新番号に更新
- 画像ディレクトリ `images/` はファイル名先頭の `fXX-` を新章番号にリネーム
- `src/images.json` の画像マッピングも更新
- ビルド対象は `src/chapters/` なので、ファイル名と章番号のソート順が一致するよう 2 桁ゼロ詰めを維持

## 作業順序

1. タスク ① (このマッピング表) ✓
2. タスク ② 巻3 用ディレクトリ作成 + 退避 (旧25,26,27,28 + 一部付録)
3. タスク ③〜⑤ 新規章 3 本を執筆 (03, 04, 05, 07 初心者ドリル)
4. タスク ⑥ 既存章のリネーム一括実行
5. タスク ⑦ 第19章 (ブリッジ) 執筆
6. タスク ⑧〜⑩ 付録再編
7. タスク ⑪ ビルド確認
