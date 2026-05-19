# 迷わないポーカー MTTプリフロップ編 — 目次・執筆ガイド（改訂版）

**対象**: 6-max / 9-max MTT、BB アンテあり、SBR 8〜40  
**スコア式**: v5final（MTT 専用 — キャッシュゲーム式とは別物）  
**データソース**: GTO Wizard MTTGeneralV2（9m） + MTT6mGeneral（6m） + ICM stages（2026-05-19）

---

## 核心フレームワーク（全章共通の参照軸）

### MTT スコア式 v5final（精度 93.6%）

```
ペア:    H + L + 12
suited:  H + L + 5 - gap_cap + Aブロッカー(+3)
  gap_cap: A→0, K→min(gap,2), Q→min(gap,3), J→min(gap,4), T以下→gap全額
offsuit: H + L - (L<10 なら -3) - gap + Aブロッカー(+3)   ← v4 互換
```

v4 との違い: ①ペアボーナス +10→+12 ②K/Q/J suited のギャップ補正に上限（K≤2, Q≤3, J≤4）

### ゾーン定義

| ゾーン | SBR 範囲 | 主な行動 |
|--------|---------|---------|
| **Zone P** | 8〜14 | Push / Fold（min-raise なし） |
| **Zone T** | 14〜20 | Push + min-raise 混在（移行帯） |
| **Zone O** | 20〜40 | min-raise 主体 |

### T_open 閾値表（v5final、chip-EV）

**9-max:**

| SBR | UTG | UTG1 | UTG2 | LJ | HJ | CO | BTN | SB |
|-----|-----|------|------|----|----|----|----|-----|
| 8  | 24 | 23 | 23 | 22 | 21 | 20 | 18 | N/A |
| 10 | 25 | 24 | 23 | 23 | 21 | 21 | 18 | N/A |
| 12 | 25 | 25 | 23 | 23 | 23 | 21 | 19 | 40 |
| 14 | 25 | 25 | 23 | 23 | 23 | 21 | 19 | 40 |
| 17 | 24 | 24 | 23 | 22 | 21 | 21 | 17 | 34 |
| 20 | 24 | 24 | 22 | 22 | 21 | 19 | 17 | 30 |
| 25 | 24 | 23 | 22 | 22 | 20 | 19 | 16 | 29 |
| 40 | 24 | 24 | 22 | 22 | 20 | 18 | 14 | 29 |

**6-max:**

| SBR | UTG | HJ | CO | BTN | SB |
|-----|-----|----|----|-----|-----|
| 8  | 22 | 21 | 20 | 18 | N/A |
| 10 | 23 | 22 | 21 | 18 | 40 |
| 12 | 23 | 23 | 21 | 19 | 36 |
| 14 | 23 | 22 | 21 | 19 | 38 |
| 17 | 22 | 22 | 20 | 19 | 34 |
| 20 | 22 | 21 | 19 | 16 | 34 |
| 25 | 22 | 20 | 19 | 16 | 29 |
| 40 | 22 | 20 | 18 | 14 | 30 |

### ICM 効果（9-max、SBR=25）

| ステージ | UTG | HJ | CO | BTN | BB vs UTG fold |
|---------|-----|----|----|-----|---------------|
| chip-EV | 24 | 20 | 19 | 16 | 17% |
| PCT50   | 24 | 21 | 19 | 17 | 28% |
| PCT37   | 25 | 21 | 19 | 17 | 33% |
| **FT**  | 25 | 23 | 21 | 19 | **44%** |

---

## 章構成（14 章 + 3 付録）

### 基礎（2 章）

#### Ch00: はじめに — MTT プリフロップ判断の特殊性
`chapters/00-introduction.md`

**主要トピック**:
- 本書の前提: 9-max が主、6-max が副（第1部/第2部）
- ICM を独立した第3部で扱う理由
- キャッシュゲームとの 3 つの違い（スタック深度・ICM 圧力・BB アンテ効果）
- SBR とゾーンの説明
- データ出典（GTO Wizard MTTGeneralV2/MTT6mGeneral, 2026-05）

**字数目安**: 3,500 字

---

#### Ch01: MTT スコア式 v5final
`chapters/01-score-formula.md`

**主要トピック**:
- v5final 設計思想（キャッシュ式との違い、K-ブロッカー廃止、pair +12）
- 非ペア計算手順（5 ステップ）
- ペアの扱い（pair +12 で 66+ が UTG からオープン）
- suited face-card gap cap の意味（K7s が fold, K8s が open の境界）
- 主要スコア早見表（AA=40, KK=38, 77=26, 66=24, K8s=24, T9s=24, 98s=22）
- 式の精度 93.6% と境界ハンドの扱い

**核心式**:
```
ペア:   H + L + 12
suited: H + L + 5 - min(gap, 15-H)[H≥11] or 0[H=14] or gap[H≤10] + A→+3
off:    H + L - [L<10:-3] - gap[H<14] + A→+3
```

**字数目安**: 5,500 字

---

### 第1部: 6-max MTT（4 章）

#### Ch02: 6m Zone P — Push/Fold（SBR 8〜14）
`chapters/02-6m-zone-p.md`

**主要トピック**:
- 6m の特徴: UTG=HJ ≈ 9m の CO相当。EP 格差が小さい
- Zone P 全体像（T_push: UTG=22-23, HJ=21-22, CO=20-21, BTN=18-19）
- ペアの push 境界（最低ペア表 6m版）
- 6m の SB: OOP でも参加基準がゆるい（UTG より広い）
- SBR=8/10/12/14 詳細
- 【GTO とのズレ】: 6m FT では短スタックで特に tight

**字数目安**: 5,000 字

---

#### Ch03: 6m Zone O — オープンレンジ（SBR 17〜40）
`chapters/03-6m-zone-o.md`

**主要トピック**:
- 6m vs 9m の開き（UTG が 2 点広い: 22 vs 24）
- SBR=20/25/40 の T_open 全ポジション詳細
- ペアの最低オープン表（6m 版）
- HJ/CO/BTN の比較（9m と HJ/CO は類似、BTN は同等）
- 6m ではポジションの価値がより高い
- オープンサイズ（R2.1〜2.3）

**字数目安**: 5,500 字

---

#### Ch04: 6m BB ディフェンス & SB vs BTN
`chapters/04-6m-defense.md`

**主要トピック**:
- 6m BB defense vs 各ポジション（call/3-bet/fold 率表）
- 6m SB vs BTN: 3-bet か fold（コールは稀）
- SBR=25 BB vs UTG: 3-bet=7%, call=74%, fold=19%
- SBR=25 BB vs BTN: 3-bet=20%, call=72%, fold=8%

**字数目安**: 4,500 字

---

#### Ch05: 6m コールドコール & 3-bet & 4-bet
`chapters/05-6m-ip-actions.md`

**主要トピック**:
- 6m IP cold call レンジ（BTN vs UTG / BTN vs HJ）
- 6m 3-bet レンジ
- 4-bet 閾値
- 6m の ICM への切り替え: FT では UTG+2-3, HJ+3-4 タイト

**字数目安**: 5,000 字

---

### 第2部: 9-max MTT（6 章）

#### Ch06: 9m Zone P — Push/Fold（SBR 8〜14）
`chapters/06-9m-zone-p.md`

**主要トピック**:
- 9m Zone P 全体像（T_push: UTG=24-25, LJ=22-23, HJ=21-23, CO=20-21, BTN=18-19, SB=38-40）
- ペアの push 境界（最低ペア表 9m版）
- EP（UTG/UTG1/UTG2）の tight 要件（SBR=12 UTG は 55+)
- SB のリンプ trap（プレミアム手はリンプ→誘い込み）
- SBR=8/10/12/14 詳細

**字数目安**: 5,500 字

---

#### Ch07: 9m Zone O — オープンレンジ（SBR 17〜40）
`chapters/07-9m-zone-o.md`

**主要トピック**:
- 9m の T_open 全ポジション（SBR=17/20/25/40）
- UTG 24 を基準とした相対記憶（UTG1=-1, LJ=-2, HJ=-4, CO=-5, BTN=-8）
- K8s=24 で UTG からオープン（v5final の主要境界）
- ペアの最低オープン表（9m: 66+ from UTG at SBR=25）
- BTN の広いオープン（T=16 ≈ ゴミ以外全部）
- SB のオープン（SBR=25: T=29 ≈ suited Broadway + strong Ax のみ）

**字数目安**: 5,500 字

---

#### Ch08: 9m マルチウェイポット
`chapters/08-9m-multiway.md`

**主要トピック**:
- MW の基本原則（caller が増えると squeeze 閾値が急騰）
- BTN/CO squeeze: 2-way=35 → 4-way=32（+コールは 2-way のみ）
- SB squeeze: 2-way=34 → 4-way=32
- BB defense fold 率の急増:
  - 2-way (UTG): fold=17%
  - 3-way (UTG+BTN): fold=23%
  - 4-way (UTG+HJ+BTN): fold=45%
  - 4-way (UTG+LJ+HJ): fold=58%
  - 4-way LP (HJ+CO+BTN): fold=35%
- BB の参加縮小パターン（offsuit 弱から順に fold）
- SBR 別安定性（SBR=17〜40 で類似したパターン）

**字数目安**: 5,000 字

---

#### Ch09: 9m BB ディフェンス
`chapters/09-9m-bb-defense.md`

**主要トピック**:
- SBR=8 のショートスタック BB（3-bet=0, call=24-39%、ほぼ fold or call with odds）
- SBR=10-14 への遷移（3-bet 登場、fold 率改善）
- SBR=17-40: 3-bet/call/fold の安定形
  - vs UTG(SBR=25): 3bet=7%, call=76%, fold=17%
  - vs CO(SBR=25): 3bet=16%, call=75%, fold=10%
  - vs BTN(SBR=25): 3bet=20%, call=73%, fold=7%
  - vs SB(SBR=25): 3bet=10%, call=72%, fold=18%
- BB defense vs SB push（SBR=12: push に直面する BB）

**字数目安**: 5,000 字

---

#### Ch10: 9m IP コールドコール & 3-bet & 4-bet
`chapters/10-9m-ip-actions.md`

**主要トピック**:
- IP cold call（BTN vs UTG, BTN vs CO, HJ vs UTG）
- BTN cold call vs UTG: suited score≥20, offsuit score≥27
- 3-bet レンジ（BB vs UTG: T_3bet=28）
- 4-bet 閾値（UTG vs BB 3-bet: SBR=25 T_4bet=34）
- スクイーズ閾値（BTN/SB vs UTG+cold caller）

**字数目安**: 5,000 字

---

#### Ch11: 9m Zone T — 移行帯（SBR 14〜20）
`chapters/11-9m-zone-t.md`

**主要トピック**:
- Zone T の構造（push と min-raise の混在）
- SBR=14: EP は strong 手を push、中程度を min-raise
- SBR=17: push がほぼ消えて min-raise 主体
- SBR=20 からの T_open への接続
- SB のリンプ比率の変化

**字数目安**: 4,500 字

---

### 第3部: ICM 戦略（3 章）

#### Ch12: ICM 基礎とバブル戦略
`chapters/12-icm-bubble.md`

**主要トピック**:
- ICM 圧力とは（チップの非線形価値）
- バブル段階別（PCT50 → PCT37 の変化）
- バブルでの T_open 変化（9m SBR=25）:
  - chip-EV: UTG=24, HJ=20, BTN=16
  - PCT37:   UTG=25, HJ=21, BTN=17
  → バブルは chip-EV より +1 程度（軽微）
- バブルでの BB defense 変化:
  - chip-EV fold=17% → PCT37 fold=33%（UTG vs BB、SBR=25）
- 6m vs 9m のバブル差異
- 実戦での意思決定: 「バブルでの BTN open は +1 点要求」

**字数目安**: 5,000 字

---

#### Ch13: ファイナルテーブル戦略
`chapters/13-icm-ft.md`

**主要トピック**:
- FT のタイト化の本質（トップフィニッシュのプレミアム）
- 9m FT T_open（SBR=25）: UTG=25, HJ=23, CO=21, BTN=19 → **全体+3〜5点**
- 6m FT T_open（SBR=25）: UTG=23, HJ=21, CO=21, BTN=19 → 類似のタイト化
- 6m FT SBR=20: UTG=25, HJ=25 → 極端なタイト化
- FT BB defense（SBR=25 vs UTG）:
  - chip-EV: fold=17% → **FT: fold=44%**
  - SBR=20: chip-EV fold=16% → **FT: fold=47%**
- FT での MW: squeeze 閾値がさらに上昇
- 実戦フロー: 「FT に入ったら BTN/CO も +3-5 点要求に切り替え」

**字数目安**: 5,500 字

---

#### Ch14: 実戦フロー確認と総括
`chapters/14-summary.md`

**主要トピック**:
- 6m vs 9m の比較一覧（どう使い分けるか）
- chip-EV vs ICM の切り替えタイミング
- 意思決定フロー全体像（SBR → ゾーン → format → chip-EV or ICM → ポジション → スコア → 閾値）
- よくある判断ミス Top 5
- GTO Wizard との精度ギャップの受け入れ方
- 境界ハンドクイズ（10 問）

**字数目安**: 4,500 字

---

### 付録

#### 付録 A: MTT スコア v5final 早見表
`chapters/appendix-a-score-table.md`

**内容**: ペア+主要 suited+offsuit の全スコア一覧（グループ別）
**字数目安**: 2,500 字

---

#### 付録 B: ポジション別閾値カード（6m / 9m / ICM）
`chapters/appendix-b-threshold-cards.md`

**内容**:
- 6m: T_open 全ポジション × SBR 表
- 9m: T_open 全ポジション × SBR 表
- ICM: FT/バブル差分表（chip-EV との差を示す）
**字数目安**: 3,000 字

---

#### 付録 C: 境界ハンドリスト（暗記推奨）
`chapters/appendix-c-boundary-hands.md`

**内容**:
- K8s=24（9m UTG SBR=25 の境界）
- 66=24（ペアの 9m UTG 境界 at SBR=25）
- T9s=24, 98s=22（suited connector の位置づけ）
- SBR 別最低オープンペア（9m/6m）
- BB 3-bet 確定リスト
**字数目安**: 2,500 字

---

## 全章文字数見通し

| Part | 章数 | 目安字数 |
|------|-----|---------|
| 基礎 | 2 | 9,000 |
| 第1部: 6-max | 4 | 20,000 |
| 第2部: 9-max | 6 | 30,500 |
| 第3部: ICM | 3 | 15,000 |
| ドリル・まとめ | 1 | 4,500 |
| 付録 | 3 | 8,000 |
| **合計** | **19** | **87,000** |

---

## 執筆上の注意事項

1. **式の表記統一**: `score_mtt(h)` または単に「スコア」で統一。キャッシュの `preflop_score` とは別
2. **SBR 表記**: 「SBR=25」（BB は省略）
3. **9m ポジション**: UTG, UTG1, UTG2, LJ, HJ, CO, BTN, SB, BB（9人制）
4. **6m ポジション**: UTG(=LJ), HJ, CO, BTN, SB, BB（6人制）
5. **ICM ステージ表記**: chip-EV / PCT50 / PCT37(bubble) / FT
6. **精度表記**: 「式の精度は 93.6%（全 SBR × ポジション × 10,478 手中 9,811 手一致）」
7. **GTO とのズレ コラム**: 各章末に設置
8. **スコア例**: K8s=24（K高suited gap cap 適用例）、66=24（pair +12 例）を必ず示す

---

## データソース

- `poker-drill/scripts/precompute/raw_ranges_tournament_9m/`: 9m chip-EV データ
- `poker-drill/scripts/precompute/raw_ranges_icm/`: 6m chip-EV + 全 ICM データ
- `poker-drill/scripts/precompute/analyze_tournament_9m.py`: 9m 分析スクリプト
- `poker-drill/scripts/precompute/analyze_icm_stages.py`: ICM 比較スクリプト
