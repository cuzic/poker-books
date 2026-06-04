# GTO Wizard 研究 — 未調査領域 (GAPS)

**更新**: 2026-06-04 / **管理**: 新規 GTO Wizard 調査の優先順を決めるドキュメント

`RESEARCH_INVENTORY.md` で既存データを網羅した結果、**書籍が触れているが GTO 実測データがない領域** を整理。

## ✅ 既に十分カバー済 (再取得不要)

### Vol1 Preflop
- **BB defense 5 オープナー hand-level** ← `research/v3-additional/findings/task_a_*` (2026-06-04 取得)
- **Squeeze N=1/2 13 シナリオ hand-level** ← `task_c_*` (同上)
- **集約 RFI / vs_open / vs_3bet / multiway** ← `vol2/findings/cash_preflop_gto_summary.json`

### Vol2 Cash Postflop
- **Flop CBet 5-cat / per-mv-cat** ← `vol2/findings/cash_5cat_gto`, `cash_board_wide_gto`, `cash_defense_gto`, `cash_flop_detail_gto`
- **Turn pairwise (型1-7, 4 シナリオ × ボード)** ← `cash_pairwise_gto.json` (`phases: "turn"` まで)
- **Cash 100bb 7 型ボード × IP/OOP cbet/defense** ← `cash_5cat_gto` (BTN_BB, CO_BB, HJ_BB, UTG_BB, SB_BB, BTN_SB)

### Vol3 MTT Postflop
- **3BP 25/50/100bb × 8 ボード × BTN_BB/CO_BB postflop hand-level** ← `3bp25/50/100_raw/`
- **BB defense Cash 100bb × 8 ボード flop/turn/river** ← `def_cash100_bb_*_raw/`
- **BB defense MTT 25/50/100bb × 8 ボード flop** ← `def_mtt25/50/100_bb_raw/`
- **BB defense MTT 50bb turn/river 詳細** ← `def_mtt50_bb_turn/river_raw/`
- **MTT preflop SBR 別 BTN_BB / SB_BB** ← `vol3/findings/mtt_preflop_*`, `mtt_sb_bb_*`
- **MTT flop cbet SBR 別** ← `mtt_flop_cbet_*`
- **MTT check-raise SBR 別** ← `mtt_check_raise_*`
- **MTT turn barrel SBR 別** ← `mtt_turn_barrel_*`

---

## ❌ 未調査領域 (本当に必要なもの)

### 🔴 高優先度: Vol1 ch04 残りモード hand-level

書籍 ch04 §4.1 (BB defense) のみ実測済。§4.2-§4.6 は集約値 (fourbet_pct 等) のみ、または書籍が「理論値、GTO 検証なし」と明言。

| # | 領域 | 未調査内容 | spots | 書籍参照 |
|---|------|----------|-------|---------|
| D | **IP defense hand-level** | BTN/CO/HJ × UTG/HJ/CO 6 セルの 169 ハンド頻度 | 6 | §4.2 |
| E | **SB OOP defense hand-level** | SB vs UTG/HJ/CO/BTN 4 セルの 169 ハンド | 4 | §4.3 |
| F1 | **vs 3-bet オープナー判断 hand-level** | 12 (オープナー × 3-bettor) シナリオの 4-bet 判断 | 12 | §4.4 |
| F2 | **4-bet defense hand-level** ★ | 5 シナリオ、書籍が「理論値 GTO 検証なし」と明言 | 5 | §4.5 |
| F3 | **5-bet defense hand-level** ★ | 1 シナリオ、同上 | 1 | §4.6 |

**合計: ~28 spots = ~3 分の API call で Vol1 ch04 全 5 モードが実測 hand-level に**

★ は書籍が「GTO 検証なし、ポットオッズ理論 + n=40,000 モンテカルロ」と明言、実測で確定する価値が最大。

### 🔴 高優先度: Vol1 ch05 残りスクイーズ

| # | 領域 | spots | 書籍参照 |
|---|------|-------|---------|
| C2 | **Squeeze N=3 (3 callers) hand-level** | 3 callers シナリオ。書籍が「概算値」と明言 | ~5 | §5.2 (N≥2 のデータ不足) |

### 🟡 中優先度: Vol1 RFI / Vol2 River / 4 board family

| # | 領域 | spots | 書籍参照 |
|---|------|-------|---------|
| L | **Cash RFI 5 オープナー hand-level** | UTG/HJ/CO/BTN/SB の RFI レンジ実測 | 5 | ch03 (集約のみあり) |
| M | **Vol2 River pairwise hand-level** | 既存 cash_pairwise は turn まで、river なし | ~14 | ch07 / ch10 |
| N | **Vol2 board family 境界判定** | dry_high の top カード閾値 (J vs Q)、dynamic_2tone 定義 | ~10 | ch05 |

### 🟢 低優先度: 書籍範囲拡張

| # | 領域 | spots | 書籍参照 |
|---|------|-------|---------|
| J | **Vol3 4BP (4-bet pot) ポストフロップ** | 書籍未収録、新章追加可能 | ~30 | Vol3 ch07 が 3BP のみ |
| K | **Vol3 ICM Bubble/FT/PCT 詳細** | 書籍が「GTO ツール推奨」と明言 | ~20 | ch09 簡易のみ |
| O | **MTT preflop hand-level** | 集約のみ、ハンド別頻度なし | ~15 | Vol1 ch06-09 |

---

## 推奨実施プラン

### Phase α (Vol1 ch04 完全化、~28 spots / ~3 分)
タスク D + E + F1 + F2 + F3 = 28 spots
→ 書籍 Vol1 ch04 を **「全モード実測 hand-level」**に格上げ
→ 「理論値、GTO 検証なし」帯 (§4.5/§4.6) を実測で確定

### Phase β (Vol1 ch03 RFI + Vol1 ch05 N=3、~10 spots / ~1 分)
タスク L + C2 = 10 spots
→ Vol1 preflop 全章で hand-level が揃う

### Phase γ (Vol2 River + Vol2 境界、~24 spots / ~2 分)
タスク M + N = 24 spots
→ Vol2 Tier 1 の精度を Tier 2 並みに

### Phase δ (Vol3 新章、~50 spots / ~5 分)
タスク J + K = 50 spots
→ 書籍に新章追加 (4BP、ICM 詳細)

**全 Phase 合計: ~112 spots = 約 12 分の API call**

---

## Vol4 (Tell/Exploit) について

Vol4 はエクスプロイトベースで GTO Wizard データは間接的にしか使わない。
GTO Wizard は「対 GTO」のレンジを返すが、Vol4 は「対 Nit/CS/LAG/Maniac/TAG」の補正値が主題。

**Vol4 で GTO Wizard が役立つ場面**:
- ch11-14 (タイプ別補正) の **GTO ベースライン** を確認 (補正前の T_open 等)
- これは既に `cash_preflop_gto_summary.json` でカバー済み (RFI/vs_open/vs_3bet の集約)

→ **Vol4 のための追加調査は不要**

---

## 使い方

1. **新規調査を始める前に**: 本ドキュメントで「未調査領域」を確認
2. **既存データの所在を知るには**: `RESEARCH_INVENTORY.md` (ディレクトリ単位サマリ)
3. **個別ファイルの詳細は**: `RESEARCH_INVENTORY_DETAIL.md` (全 896 ファイル一覧)

調査スクリプトは `research/v3-additional/` に集約。スクリプト名は `task_<letter>_<scenario>.py`。
