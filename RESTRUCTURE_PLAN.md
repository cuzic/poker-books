# 「迷わないポーカー」シリーズ再構成 plan

作成日: 2026-05-28
ベース知見: UCBS-v2 + DCBS 17-context フレームワーク完成 (2026-05-28)

---

## 新構成 (4 巻体制)

| 巻 | テーマ | 状態 | 主要式 |
|---|---|---|---|
| **Vol1** | Preflop 完全版 (Cash + MTT 統合) | 既存流用 | Score_BB v7 (preflop) |
| **Vol2** | Postflop **Cash + 簡易版** | **新規執筆** | Light UCBS v2 + Light DCBS |
| **Vol3** | Postflop **MTT + 精緻版** | **新規執筆** | Full UCBS-v2 + Full DCBS |
| **Vol4** | Tell / Exploit | 既存流用 (リナンバー) | プレイヤータイプ別補正 |

---

## Directory 再編

### リネーム計画

| 現在 | 新名 | アクション |
|---|---|---|
| `preflop/` | `vol1-preflop/` | rename |
| `cash-postflop/` | `vol2-cash-postflop/` | rename + Light 主体に再執筆 |
| `mtt-postflop/` | `vol3-mtt-postflop/` | rename + Full UCBS-v2 完全反映 |
| `tell/` | `vol4-tell/` | rename + 巻番号参照修正 |
| `cash-preflop/` | `_archive/cash-preflop/` | archive |
| `mtt-preflop/` | `_archive/mtt-preflop/` | archive |

### スクリプト/設定の更新

- `scripts/build.ts`: vol1-4 のパス更新
- `book.json` (各巻内): identifier / title 更新
- `.github/workflows/deploy.yml`: パス参照確認
- `CLAUDE.md` (root): Directory Structure 更新

---

## Vol1 (Preflop 統合版): 既存維持

`vol1-preflop/` (旧 `preflop/`):
- 章: 00-introduction, 01-score-formula, 02-thresholds, 03-cash-rfi, 04-cash-defense, 05-cash-multiway, 06-mtt-coefficients, 07-mtt-sbr, 08-mtt-icm, 09-mtt-9max, ...
- 状態: 初稿生成中、内容は基本そのまま
- 修正: 巻間参照 (vol2/vol3/vol4 への誘導) の追加のみ

---

## Vol2 (Cash + 簡易版): 章構成案

`vol2-cash-postflop/` の新規構成:

### 主要式: Light UCBS v2 + Light DCBS

| 章 | タイトル | 内容 | 目標字数 |
|---|---|---|---:|
| 00 | はじめに | Cash で迷わない postflop、暗算 5-7 秒 | 3k |
| 01 | CBS の式: HP + DP | 基礎の足し算、HP/DP テーブル詳述 | 5k |
| 02 | Light UCBS の 25 セル表 | context × CBS バンド の核心 | 6k |
| 03 | Cash 100bb cbet 完全ガイド | 主要 context、例題 5 つ | 8k |
| 04 | ボード読み (型 1-7 簡素版) | 型分類のショートカット | 5k |
| 05 | サイズ判別 (33% vs Overbet) | polarize 板の見抜き方 | 4k |
| 06 | Position 補正 (SB/BTN/CO/HJ/UTG) | position lift の覚え方 | 4k |
| 07 | 3-bet pot postflop (cash) | SPR 別、簡素版 | 6k |
| 08 | Light DCBS: 守備の暗算式 | pair+ call / air kicker 判定 | 6k |
| 09 | Turn 2nd barrel: α=-0.35 シフト | turn 簡易対応 | 5k |
| 10 | Multistreet plan | flop→turn→river の繋がり | 6k |
| 11 | 例題集 (cash 100bb 20 spots) | 暗算練習 | 8k |
| App | 暗算チートシート | 25 セル + DCBS 表 + 公式まとめ | 4k |

**合計: ~70k 字、12 章 + 付録**

### 既存 `cash-postflop/chapters/` の流用判定

| 既存 ch | 新 Vol2 ch | 流用度 |
|---|---|---|
| 01-board-types | **04** ボード読み | ◯ 流用 + Light 対応 |
| 02-cbet-ip | **03** Cash cbet | △ 大幅書き換え (UCBS-v2 から Light に簡素化) |
| 03-cbet-oop-donk | (省略 or 簡素) | × Light では深入りせず |
| 04-cbet-3bp-4bp | **07** 3-bet pot | △ Light 表で簡素化 |
| 05-cbet-multiway | (省略) | × Vol2 スコープ外、後付け検討 |
| 06-defense | **08** Light DCBS | ○ DCBS 反映 |
| 07-turn-barrel | **09** Turn 簡易 | △ Light の α シフト主体 |
| 08-turn-plan-defense | **10** Multistreet | ○ 流用 |
| 09-river-alpha | (省略 or 10 統合) | × Light では river 深入りせず |
| 10-river-action | (省略 or 10 統合) | × |
| 11-multistreet-plan | **10** Multistreet | ○ |
| appendix-cheatsheet | **App** | ○ 25 セル表で更新 |

→ 既存 12 章 → 新 12 章 + 付録、約 60% 流用 + 40% 新規

---

## Vol3 (MTT + 精緻版): 章構成案

`vol3-mtt-postflop/` の新規構成:

### 主要式: Full UCBS-v2 (13 context) + Full DCBS (4 context)

| 章 | タイトル | 内容 | 目標字数 |
|---|---|---|---:|
| 00 | はじめに | MTT 全 depth/SPR を精緻にカバー | 4k |
| 01 | Full UCBS-v2 の 5 軸 | HP+DP+Confidence+Size+Context の意味 | 8k |
| 02 | Confidence の判定 | 型1-7 ボード × 距離 × 例外 (型6) | 6k |
| 03 | Size 軸 (33% vs Overbet 116%) | polarize 判定の 5 条件 | 5k |
| 04 | Context スイッチング | 13 context の切替方法 | 6k |
| 05 | Position lift | SB/BTN/CO/HJ/UTG 補正 | 4k |
| 06 | Example: MTT 25bb 終盤 cbet | 主要 context 1 | 8k |
| 07 | MTT 50bb 中盤 cbet | バブル前の cbet 戦略 | 8k |
| 08 | MTT 100bb 序盤 cbet | MTT6mSimple の特殊性 | 8k |
| 09 | MTT 200bb 深 cbet (FT 直後) | deep play | 6k |
| 10 | 3BP IP SPR シリーズ | 20/25/50/100bb の差 | 10k |
| 11 | Turn cbet 4 context | α=-0.35 + context 別調整 | 8k |
| 12 | Full DCBS (4 context) | defense の depth 別 | 8k |
| 13 | 例外ルール (4 つ) | 型6, mono, A-x, turn-shift | 5k |
| 14 | 苦手領域と限界 | mtt_100bb, ストレート turn | 4k |
| 15 | ICM 補正 (取得可能なら) | bubble / FT の調整 | 6k |
| 16 | 例題集 (MTT 各 depth) | depth/SPR スイッチ練習 | 10k |
| App A | 13 context パラメータ完全表 | α/β/offset/lift の全数値 | 5k |
| App B | Full DCBS 4 context 表 | continue freq 完全表 | 3k |
| App C | UCBS-v2 公式 cheat sheet | 5 軸の公式まとめ | 3k |

**合計: ~125k 字、16 章 + 3 付録**

### 既存 `mtt-postflop/chapters/` の流用判定

| 既存 ch | 新 Vol3 ch | 流用度 |
|---|---|---|
| 00-introduction | **00** | ○ 流用 + Full UCBS-v2 言及 |
| 01-sbr-to-spr | **04** Context | ○ SPR の話に統合 |
| 02-cbs-system | **01** Full UCBS-v2 | ✗ 全面書き換え (旧 CBS → UCBS-v2) |
| 03-icm-postflop | **15** ICM | △ Full UCBS-v2 ベースで再執筆 |
| 04-deep | **09** MTT 200bb | △ Full の数値で更新 |
| 05-flop-defense | **12** Full DCBS | ✗ DCBS 反映で書き換え |
| 06-middle | **07** MTT 50bb | △ context 表反映 |
| 07-short | **06** MTT 25bb | △ |
| 08-very-short | (省略 or 06 統合) | × Vol3 スコープ |
| 09-midgame | (省略) | × Vol1/Vol3 で分散済 |
| 10-bubble | **15** ICM | △ |
| 11-final-table | (省略 or 15 統合) | × |
| 12-3bp | **10** 3BP series | ✗ 4 SPR 全網羅で書き換え |
| 13-multiway | (省略) | × Vol3 スコープ外 |
| 14-turn-river | **11** Turn cbet | △ Turn 主体、river は別途 |
| 15-quiz | **16** 例題集 | ○ 流用 |
| appendix | **App A-C** | △ 3 つに分割再編 |

→ 既存 16 章 → 新 16 章 + 3 付録、約 30% 流用 + 70% 新規

---

## Vol4 (Tell / Exploit): 既存維持

`vol4-tell/` (旧 `tell/`):
- 章: 00-introduction, 01-player-types, 02-live-diagnosis-action, 03-live-diagnosis-tells, ...
- 状態: 初稿完了、gist 公開済み
- 修正: 巻番号参照のみ (vol5 → vol4)、相互参照修正

---

## 巻間相互参照

### 必須リンク

```
Vol1 (Preflop)
  → Vol2/Vol3: 「Postflop は Vol2 (Cash簡易) または Vol3 (MTT精緻) へ」

Vol2 (Cash + Light)
  ← Vol1: Score_BB v7 (preflop) を前提知識
  → Vol3: 「精度上げたい / MTT を打つなら Vol3」
  → Vol4: 「相手タイプ別の調整は Vol4」

Vol3 (MTT + Full)
  ← Vol1: Score_BB v7 (preflop)
  ← Vol2: Light UCBS の知識を発展 (任意)
  → Vol4: エクスプロイト調整

Vol4 (Tell)
  ← Vol2/Vol3: GTO ベースの計算式
  - プレイヤータイプ別補正
```

### 「迷ったらどう読むか」フロー

```
読者 = Cash プレイヤー初心者
  → Vol1 → Vol2 (Light で完結) → Vol4 (exploit)

読者 = MTT プレイヤー
  → Vol1 → Vol3 (Full 必要) → Vol4

読者 = 両方やる
  → Vol1 → Vol2 (簡素な暗算式を習得) → Vol3 (精度上げる) → Vol4
```

---

## 移行作業の段階

### Phase 1: Directory 再編 (低リスク)

```
mv preflop vol1-preflop
mv cash-postflop vol2-cash-postflop
mv mtt-postflop vol3-mtt-postflop
mv tell vol4-tell
mkdir -p _archive
mv cash-preflop _archive/
mv mtt-preflop _archive/
```

### Phase 2: スクリプト・設定更新

- `scripts/build.ts` のパス
- `book.json` の各巻 identifier / title
- `.github/workflows/deploy.yml` 確認
- `CLAUDE.md` (root) の Directory Structure 更新

### Phase 3: Vol2 執筆 (Light UCBS/DCBS 主体)

- 章ごとに既存 cash-postflop の流用判定
- generator script (scripts/generate/) も Light 仕様に更新
- 25 セル表を中心に再構成

### Phase 4: Vol3 執筆 (Full UCBS-v2 主体)

- mtt-postflop の旧 CBS を Full UCBS-v2 に書き換え
- 13 context の完全網羅
- 例外ルール 4 つの章
- (オプション) ICM 章: MTTGeneral_ICM6m200PTT2 から追加データ取得が必要

### Phase 5: Vol1 / Vol4 の参照更新

- 巻番号の修正 (vol5 → vol4 など)
- 相互リンクの追加

### Phase 6: ビルド・公開

- HTML/EPUB ビルド
- gistpreview 公開
- GitHub Pages デプロイ

---

## 既存資産

### コード資産 (vol2-cash-postflop/ 内に移動)

- `cash-postflop/ucbs_v2.py` → 13 context フル実装
- `cash-postflop/dcbs.py` → 4 context defense
- `cash-postflop/ucbs_light_v2.py` → 簡易版 5 context
- `cash-postflop/ucbs_v2_*.py` → 各種 fit/eval スクリプト
- `mtt-postflop/{mtt100bb,turn_cbet,bb_defense}_draw_study.py` → fetch スクリプト

### データ資産 (mtt-postflop/findings/ に集中)

- `draw_study_MTT25/50/100/200BB.jsonl` (480 spots)
- `draw_study_3BP25/50/100.jsonl` (72 spots)
- `draw_study_TURN_*.jsonl` (~113 spots, 4 contexts)
- `draw_study_DEF_*.jsonl` (96 spots, 4 contexts)
- `cash_5cat_gto.json` (cash 100bb baseline)

### ドキュメント資産

- `knowledges/gto_wizard_study/UCBS_V2_DCBS_FINAL.md` — Vol3 章構成のソース
- `scripts/gto_wizard_study/API_NOTES.md` — 開発者向け
- `knowledges/gto_wizard_study/*.md` — 各種研究レポート

---

## 想定スケジュール

| Phase | 内容 | 所要 |
|---|---|---|
| 1-2 | Directory 再編 + 設定更新 | 1 セッション (1-2 時間) |
| 3 | Vol2 章執筆 | 章ごと 1-2 時間 × 12 = 12-24 時間 |
| 4 | Vol3 章執筆 | 章ごと 1-2 時間 × 16 = 16-32 時間 |
| 5 | Vol1/Vol4 参照更新 | 1 セッション |
| 6 | ビルド・公開 | 1 セッション |

**合計: 40-60 時間 (執筆 28-56 時間 + 雑務 ~6 時間)**

---

## リスクと注意点

### リスク 1: 既存巻の整合性

- Vol1 (preflop) は postflop 巻と用語が一致する必要
- 「HP」「DP」「CBS」「型1-7」を Vol1 でも先取り定義しておく

### リスク 2: 重複・矛盾

- Vol2 Light と Vol3 Full で同じ概念が違う深さで扱われる
- 「Vol2 で軽く、Vol3 で深く」と説明する明確な区別が必要

### リスク 3: 「Light は実用に耐えるか?」

- MTT 短スタックでは Light の精度低 (Δ +20pt)
- → Vol2 は **Cash + 標準 (cash 100bb / mtt 50bb)** に絞る
- MTT 25bb の暗算は Light 不可、Full UCBS-v2 が必要

### リスク 4: ICM データ未取得

- Vol3 ch15 (ICM) は MTTGeneral_ICM6m200PTT2 から追加 fetch 必要
- データ取得しない選択 → Vol3 から ICM 章を省略

---

## 次のアクション

1. **この plan の承認/修正**
2. Phase 1 (Directory rename) 実行
3. Phase 3 (Vol2 執筆) または Phase 4 (Vol3 執筆) のどちらから着手するか決定
4. (オプション) Vol3 ICM 章のためのデータ取得
