# プリフロップスコア v7 仕様書

**作成日**: 2026-05-21
**ステータス**: 設計確定（実装・書籍反映は次フェーズ）
**対象**: Cash 6-max (100BB) + MTT (SBR≈25) の両方に対応
**前バージョン**: `PREFLOP_SCORE_SPEC.md` (v3, Cash のみ、全体平均 89.7%)

---

## 0. 変更サマリー

| 項目 | v3 (現行) | v7 (本仕様) |
|---|---|---|
| 精度 (Cash) | 89.7% | **94.5%** |
| MTT 対応 | なし | **あり (95.5%)** |
| 係数方式 | 固定 + BB 強化版 | コンテキスト別オーバーライド |
| スーテッドボーナス | +3 (固定) | suit_bonus (コンテキスト依存) |
| コネクターボーナス | diff1=+1, diff2-3=+0.5 | suited_connector (gap=0) / suited_connector1 (gap=1) |
| A-suited gap | ペナルティなし | a_suited_gap_cap でキャップ |
| T以下 suited gap | 無制限ペナルティ | low_high_cap でキャップ |
| MW (スクイーズ) | 補助ルール | MW_BB/MW_SB/MW_IP コンテキスト係数 |
| MTT ICM フェーズ | 未対応 | 閾値調整 + 例外ルール |

---

## 1. スコア式（v7 共通構造）

### 1.1 ペア

```
Score = H + L + pair_bonus
```

### 1.2 スーテッド

```
Score = H + L + suit_bonus − gap_cap + a_blocker + k_blocker + sc_bonus

gap_cap の計算:
  H = A(14): min(gap, a_suited_gap_cap)
  H = K(13): min(gap, 2)          ← 固定
  H = Q(12): min(gap, 3)          ← 固定
  H = J(11): min(gap, 4)          ← 固定
  H ≤ T(10): min(gap, low_high_cap)

sc_bonus の計算:
  gap = 0 → suited_connector
  gap = 1 → suited_connector1
  gap ≥ 2 → 0
```

### 1.3 オフスーツ

```
Score = H + L − gap_cap − low_pen + a_blocker + k_blocker

gap_cap の計算:
  H = A(14): min(gap, a_gap_cap)
  H = K(13): min(gap, k_gap_cap)
  H ≤ Q(12): gap (上限なし)

low_pen の適用:
  H ≠ A かつ L < 10 → low_pen を引く
  H = A → low_pen 免除
```

**補足**: `a_blocker` は H=14 のとき、`k_blocker` は H=13 のときのみ加算。

---

## 2. 係数定義と探索範囲

| 係数 | 説明 | 探索範囲 |
|---|---|---|
| `suit_bonus` | スーテッドボーナス | 3〜8 |
| `k_blocker` | K-high への追加ボーナス | 0〜2 |
| `a_blocker` | A-high への追加ボーナス | 0〜4 |
| `low_pen` | 低カード offsuit ペナルティ (L<10, H≠A) | 0〜5 |
| `a_gap_cap` | A-high offsuit gap キャップ | 0〜8 |
| `k_gap_cap` | K-high offsuit gap キャップ | 0〜8 |
| `pair_bonus` | ペアボーナス | 8〜16 |
| `a_suited_gap_cap` | A-high suited gap キャップ | 0〜8 |
| `suited_connector` | suited gap=0 ボーナス | 0〜5 |
| `suited_connector1` | suited gap=1 ボーナス | 0〜4 |
| `low_high_cap` | T-以下 suited gap キャップ | 1〜8 |

---

## 3. Cash ゲーム係数表

### 3.1 ベース係数（未指定コンテキストに適用）

Optuna TPE 2000 trials で最適化 (全 **56** シナリオ平均 **93.74%**)

| 係数 | ベース値 |
|---|---|
| suit_bonus | **4** |
| k_blocker | **3** |
| a_blocker | **5** |
| low_pen | **2** |
| a_gap_cap | **5** |
| k_gap_cap | **7** |
| pair_bonus | **16** |
| a_suited_gap_cap | **4** |
| suited_connector | **1** |
| suited_connector1 | **0** |
| low_high_cap | **5** |

### 3.2 コンテキスト別オーバーライド

ベース値と **異なる** 係数のみ記載。記載なし = ベース値を使用。

#### [RFI] LJ / HJ / CO / BTN オープン (8 シナリオ, 精度 **95.6%**)

| 係数 | RFI 値 | ベースとの差 |
|---|---|---|
| low_pen | **3** | +1 |
| pair_bonus | **11** | −5 ★ |
| a_blocker | **4** | −1 |

*解釈: RFI はペアを過大評価しない（A ブロッカー価値も控えめ）。低カードペナルティは若干強め。*

#### [BB] BB defense vs open (13 シナリオ, 精度 **89.5%**)

| 係数 | BB 値 | ベースとの差 |
|---|---|---|
| suit_bonus | **6** | +2 ★ |
| suited_connector | **6** | +5 ★ |
| suited_connector1 | **4** | +4 ★ |

*解釈: BB は 1bb 払い済 → ポットオッズ改善 → suited 全面強化（SC ボーナス大幅増）。*

#### [IP] IP call / 3-bet defense (14 シナリオ, 精度 **92.9%**)

| 係数 | IP 値 | ベースとの差 |
|---|---|---|
| suited_connector1 | **2** | +2 ★ |
| pair_bonus | **12** | −4 ★ |

*解釈: IP は小ペアよりも suited connecter (gap=1) を重視。pair_bonus はポジション利のある IP で保守的に。*

#### [OOP] OOP call / SB vs 3-bet (9 シナリオ, 精度 **96.2%**)

| 係数 | OOP 値 | ベースとの差 |
|---|---|---|
| suited_connector1 | **4** | +4 ★ |
| pair_bonus | **12** | −4 ★ |

*解釈: OOP は位置不利 → ペアより suited の手を優先。SC(gap=1) ボーナスを最大化。*

#### [MW_BB] MW BB defense (4 シナリオ, 精度 **96.7%**)

| 係数 | MW_BB 値 | ベースとの差 |
|---|---|---|
| suited_connector1 | **5** | +5 ★ |
| low_pen | **6** | +4 ★ |
| pair_bonus | **11** | −5 ★ |

*解釈: MW BB は複数人ポット → SC (gap=1) を最大評価。低カードペナルティも最大化（MW の low-card コール減）。*

#### [MW_SB] MW SB squeeze (5 シナリオ, 精度 **95.9%**)

| 係数 | MW_SB 値 | ベースとの差 |
|---|---|---|
| suited_connector | **6** | +5 ★ |
| suited_connector1 | **5** | +5 ★ |

*解釈: MW SB スクイーズは suited connector 系（gap=0/1）を全力強化。ナットフラッシュ可能性で差別化。*

#### [MW_IP] MW IP squeeze (3 シナリオ, 精度 **96.1%**)

| 係数 | MW_IP 値 | ベースとの差 |
|---|---|---|
| suit_bonus | **8** | +4 ★ |
| suited_connector | **6** | +5 ★ |
| pair_bonus | **14** | −2 |
| a_blocker | **2** | −3 ★ |

*解釈: MW IP は position + suited 全評価。A ブロッカーより suited quality を優先。*

### 3.3 コンテキスト別精度サマリー

| コンテキスト | シナリオ数 | 精度 |
|---|---|---|
| RFI | 8 | 95.6% |
| BB | 13 | 89.5% |
| IP | 14 | 92.9% |
| OOP | 9 | 96.2% |
| MW_BB | 4 | 96.7% |
| MW_SB | 5 | 95.9% |
| MW_IP | 3 | 96.1% |
| **全体平均** | **56** | **93.7%** |

---

## 4. MTT 係数表 (SBR=25 ChipEV)

Optuna TPE 2000 trials で最適化。  
GTO データ: `gto-charts-mtt6.json` + `gto-charts-ext.json` SBR25 (計 **164** シナリオ)

### 4.1 MTT ベース係数

| 係数 | ベース値 |
|---|---|
| suit_bonus | **6** |
| k_blocker | **0** |
| a_blocker | **5** |
| low_pen | **0** |
| a_gap_cap | **5** |
| k_gap_cap | **2** |
| pair_bonus | **18** |
| a_suited_gap_cap | **4** |
| suited_connector | **4** |
| suited_connector1 | **3** |
| low_high_cap | **5** |

### 4.2 MTT コンテキスト別オーバーライド

#### [RFI] RFI オープン (23 シナリオ, 精度 **96.7%**)

| 係数 | RFI 値 | ベースとの差 |
|---|---|---|
| suit_bonus | **5** | −1 |
| low_pen | **1** | +1 |

#### [BB] BB defense (26 シナリオ, 精度 **93.8%**)

| 係数 | BB 値 | ベースとの差 |
|---|---|---|
| suit_bonus | **9** | +3 ★ |
| pair_bonus | **10** | −8 ★ |
| a_blocker | **3** | −2 ★ |

*解釈: MTT BB は suit_bonus 最大化・ペアボーナス大幅削減（BB アンテでペアの相対価値が下がる）。*

#### [IP] IP call / 3-bet defense (18 シナリオ, 精度 **97.3%**)

| 係数 | IP 値 | ベースとの差 |
|---|---|---|
| low_pen | **6** | +6 ★ |

*解釈: MTT IP は低カードオフスーツに厳しくペナルティ（suited に相対優位を集める）。*

#### [OOP] OOP / SB defense (15 シナリオ, 精度 **96.6%**)

| 係数 | OOP 値 | ベースとの差 |
|---|---|---|
| suited_connector1 | **2** | −1 |
| low_pen | **5** | +5 ★ |

#### [MW_BB] MW BB defense (35 シナリオ, 精度 **89.0%**)

| 係数 | MW_BB 値 | ベースとの差 |
|---|---|---|
| suit_bonus | **9** | +3 ★ |
| suited_connector | **5** | +1 |
| suited_connector1 | **5** | +2 ★ |
| low_pen | **5** | +5 ★ |
| a_blocker | **1** | −4 ★ |

*解釈: MW BBは suited系を全体的に強化。低カードペナルティも厳格化。*

#### [MW_SB] MW SB squeeze (22 シナリオ, 精度 **95.9%**)

| 係数 | MW_SB 値 | ベースとの差 |
|---|---|---|
| suited_connector1 | **2** | −1 |
| a_blocker | **4** | −1 |

#### [MW_IP] MW IP squeeze (25 シナリオ, 精度 **96.9%**)

| 係数 | MW_IP 値 | ベースとの差 |
|---|---|---|
| suit_bonus | **3** | −3 ★ |
| suited_connector1 | **1** | −2 ★ |
| low_pen | **6** | +6 ★ |
| a_blocker | **4** | −1 |

### 4.3 MTT コンテキスト別精度サマリー

| コンテキスト | シナリオ数 | 精度 |
|---|---|---|
| RFI | 23 | 96.7% |
| BB | 26 | 93.8% |
| IP | 18 | 97.3% |
| OOP | 15 | 96.6% |
| MW_BB | 35 | 89.0% |
| MW_SB | 22 | 95.9% |
| MW_IP | 25 | 96.9% |
| **全体平均** | **164** | **94.6%** |

### 4.4 Cash vs MTT ベース係数差分

| 係数 | Cash | MTT | 差 | 解釈 |
|---|---|---|---|---|
| suit_bonus | 4 | **6** | +2 ★ | BBアンテでポットオッズ改善 → suited 価値 UP |
| k_blocker | 3 | **0** | −3 ★ | MTT は K-high の追加ブロッカーボーナス不要 |
| low_pen | 2 | **0** | −2 ★ | MTT では offsuit 低カードにペナルティ不要 |
| k_gap_cap | 7 | **2** | −5 ★ | MTT の K-high offsuit は gap に厳格（2 でキャップ） |
| pair_bonus | 16 | **18** | +2 ★ | MTT ではペアボーナスが Cash より高い |
| suited_connector | 1 | **4** | +3 ★ | MTT SC (gap=0) が Cash より大幅に高価値 |
| suited_connector1 | 0 | **3** | +3 ★ | MTT SC1 (gap=1) も Cash より高価値 |
| a_blocker | 5 | 5 | 0 | A-blocker は同等 |
| a_gap_cap | 5 | 5 | 0 | A-high offsuit gap cap は同等 |
| a_suited_gap_cap | 4 | 4 | 0 | A-suited gap cap は同等 |
| low_high_cap | 5 | 5 | 0 | T以下 suited gap cap は同等 |

---

## 5. 精度サマリー

### 5.1 Cash ゲーム (56 シナリオ, Optuna 2000 trials)

| コンテキスト | シナリオ数 | 精度 |
|---|---|---|
| RFI | 8 | 95.6% |
| BB | 13 | 89.5% |
| IP | 14 | 92.9% |
| OOP | 9 | 96.2% |
| MW_BB | 4 | 96.7% |
| MW_SB | 5 | 95.9% |
| MW_IP | 3 | 96.1% |
| **全体平均** | **56** | **93.7%** |

**注**: BB コンテキスト 89.5% は、ディフェンス幅の広いシナリオで GTO の mixed strategy を線形式で完全再現できない構造的限界。

### 5.2 MTT 6m SBR=25 ChipEV (164 シナリオ, Optuna 2000 trials)

| コンテキスト | シナリオ数 | 精度 |
|---|---|---|
| RFI | 23 | 96.7% |
| BB | 26 | 93.8% |
| IP | 18 | 97.3% |
| OOP | 15 | 96.6% |
| MW_BB | 35 | 89.0% |
| MW_SB | 22 | 95.9% |
| MW_IP | 25 | 96.9% |
| **全体平均** | **164** | **94.6%** |

### 5.3 v3 からの改善幅

| コンテキスト | v3 精度 | v7 精度 | 改善 |
|---|---|---|---|
| RFI (Cash) | 89.6% | 95.6% | +6.0% |
| BB defense (Cash) | 83.4〜88.2% | 89.5% | +1〜6% |
| **Cash 全体** | **89.7%** | **93.7%** | **+4.0%** |
| **MTT 全体** | — | **94.6%** | 新規 |

---

## 6. MTT ICM フェーズ補正

BBアンテ MTT では、残り枚数・位置（バブル近辺、ファイナルテーブル）によって  
プレイングレンジが ChipEV（スタック最大化）とは乖離する。

**設計方針**: スコア式の係数は変えず、**閾値調整** と **例外ルール** で対応する。  
（係数を変えると式の整合性が崩れ、書籍での説明が複雑になる）

### 6.1 フェーズ別 T_open 補正（RFI）

| フェーズ | 残り条件 | T_open 補正 |
|---|---|---|
| ChipEV (通常) | PCT75+ / SBR=25 以上 | **±0** |
| ICM 中圧 | PCT25〜50 付近 | **+2〜3** |
| バブル / FT 手前 | PCT10〜25 | **+4〜5** |

*実用: 通常閾値を覚えて、フェーズに応じてメンタルで加算する。*

### 6.2 ICM フェーズで脱落する典型ハンド

GTO 実測（GTO Wizard ICM シナリオ）より:

| ハンド | Cash/ChipEV | PCT50 (ICM 中) | バブル |
|---|---|---|---|
| 54s, 65s | BTN オープン ✓ | 折れ始め ▲ | **ほぼ Fold** ★ |
| 76s, 87s | BTN/CO オープン ✓ | 維持 | **Fold** ★ |
| 33, 44 | CO+ オープン ✓ | 維持 | 33 は Fold ★ |
| A5s, A6s | UTG+ オープン ✓ | 維持 | 維持 ◯ |
| T9s, JTs | 全ポジ ✓ | 維持 | 維持 ◯ |
| AKs, QQ+ | 全ポジ ✓ | 維持 | 維持 ◯ |

### 6.3 フェーズ別の補足ルール

```
[Phase: ChipEV / 通常]
  → 基本閾値をそのまま使用

[Phase: ICM 中圧 (PCT25〜50)]
  → T_open += 2
  → BTN/SB で 54s, 65s は Fold (score ≥ T_open でも除外)

[Phase: バブル / FT 手前 (PCT10〜25)]
  → T_open += 4
  → BTN/SB で 76s 以下 suited connector は Fold
  → CO以深 で 33 以下のペアは Fold

[Phase: ファイナルテーブル (ICM 最大)]
  → T_open += 5
  → 小ペア 22-44 は Fold（セットマイニング implied odds 計算困難）
  → 87s 以下 SC 系は Fold
```

### 6.4 BB defense のフェーズ補正

BB defense は ICM プレッシャー下でも基本的に「ディフェンスしなければなら  
ない」ポジション。ただし以下を調整:

```
[バブル / FT 以降]
  → T_call += 2  (wide call レンジを縮小)
  → 例外2 (suited diff≤4 → CALL) を diff≤2 に縮小
    → すでに MW Level-1 と同じ例外2 縮小ロジック
```

---

## 7. 主要ハンドのスコア例（v7 ベース係数）

Cash ベース係数 (suit_bonus=4, pair_bonus=16, suited_connector=1, suited_connector1=0,
a_suited_gap_cap=4, a_gap_cap=5, k_gap_cap=7, low_high_cap=5, a_blocker=5, k_blocker=3, low_pen=2)

| ハンド | H+L | ボーナス | ギャップ補正 | ブロッカー | SC ボーナス | Score |
|---|---|---|---|---|---|---|
| AA | 28 | +16 (pair) | — | — | — | **44** |
| KK | 26 | +16 (pair) | — | — | — | **42** |
| QQ | 24 | +16 (pair) | — | — | — | **40** |
| JJ | 22 | +16 (pair) | — | — | — | **38** |
| TT | 20 | +16 (pair) | — | — | — | **36** |
| 99 | 18 | +16 (pair) | — | — | — | **34** |
| 66 | 12 | +16 (pair) | — | — | — | **28** |
| 22 | 4 | +16 (pair) | — | — | — | **20** |
| AKs | 27 | +4 (s) | −min(0,4)=0 | +5 (A) | +1 (gap=0) | **37** |
| AKo | 27 | — | −min(0,5)=0 | +5 (A) | — | **32** |
| AQs | 26 | +4 | −min(1,4)=1 | +5 | +0 (gap=1) | **34** |
| AQo | 26 | — | −min(1,5)=1 | +5 | — | **30** |
| KQs | 25 | +4 | −min(0,2)=0 | +3 (K) | +1 (gap=0) | **33** |
| KQo | 25 | — | −min(0,7)=0 | +3 | — | **28** |
| AJs | 25 | +4 | −min(2,4)=2 | +5 | +0 (gap=2) | **32** |
| AJo | 25 | — | −min(2,5)=2 | +5 | — | **28** |
| KJs | 24 | +4 | −min(1,2)=1 | +3 | +0 (gap=1) | **30** |
| QJs | 23 | +4 | −min(0,3)=0 | — | +1 (gap=0) | **28** |
| JTs | 21 | +4 | −min(0,4)=0 | — | +1 (gap=0) | **26** |
| T9s | 19 | +4 | −min(0,5)=0 | — | +1 (gap=0) | **24** |
| 98s | 17 | +4 | −min(0,5)=0 | — | +1 (gap=0) | **22** |
| 87s | 15 | +4 | −min(0,5)=0 | — | +1 (gap=0) | **20** |
| 76s | 13 | +4 | −min(0,5)=0 | — | +1 (gap=0) | **18** |
| 65s | 11 | +4 | −min(0,5)=0 | — | +1 (gap=0) | **16** |
| 54s | 9 | +4 | −min(0,5)=0 | — | +1 (gap=0) | **14** |
| A5s | 19 | +4 | −min(8,4)=4 | +5 | 0 (gap=8) | **24** |
| A8s | 22 | +4 | −min(5,4)=4 | +5 | 0 (gap=5) | **27** |
| K8s | 21 | +4 | −min(4,2)=2 | +3 | 0 (gap=4) | **26** |
| K7s | 20 | +4 | −min(5,2)=2 | +3 | 0 (gap=5) | **25** |
| J8s | 19 | +4 | −min(2,4)=2 | — | 0 (gap=2) | **21** |
| T7s | 17 | +4 | −min(2,5)=2 | — | 0 (gap=2) | **19** |

---

## 8. v3 → v7 変換ガイド

### スコア式の変化

| 要素 | v3 | v7 |
|---|---|---|
| pair_bonus | 固定 +10 | コンテキスト別 (12〜16) |
| suit_bonus | 固定 +3 | コンテキスト別 (3〜8) |
| conn diff1 | +1 | suited_connector1 (0〜4) |
| conn diff2-3 | +0.5 | 0 (gap≥2 はボーナスなし) |
| conn diff0 | なし | suited_connector (0〜5) |
| a_blocker | 固定 +3 | コンテキスト別 (0〜4) |
| k_blocker | 固定 +2 | コンテキスト別 (0〜2) |
| AK 合算 | +4 (a+k 上書き) | a_blocker + k_blocker (合算) |
| gap A-suited | ペナルティなし | a_suited_gap_cap でキャップ |
| gap T以下 suited | 無制限 | low_high_cap でキャップ |
| both<9 penalty | -1 | low_pen でコンテキスト別 |

### 書籍への反映方針

- **キャッシュ vol1**: ベース係数 + RFI/BB コンテキスト係数のみ掲載（IP/OOP は付録）
- **MTT vol3**: MTT ALL 係数で統一（コンテキスト別は付録）
- **BB defense**: BB オーバーライドを適用した Score_BB 版を本文に
- **MW (スクイーズ)**: MW コンテキスト係数 (TBD) + 閾値補正を章末コラムで

---

## 9. 全データ検証ツール

### 9.1 データファイル (1763 シナリオ)

| ファイル | シナリオ数 | 内容 |
|---|---|---|
| `gto-charts.json` | 36 | Cash 6m HU (既存) |
| `gto-charts-mtt6.json` | 421 | MTT 6m ChipEV SBR8〜40 + squeeze/MW/3bet |
| `gto-charts-icm.json` | 731 | ICM 6m/8m/9m × SBR全域 × フェーズ全域 |
| `gto-charts-mtt9m.json` | 411 | MTT 9m SBR8〜40 + MW/3bet |
| `gto-charts-ext.json` | 164 | Cash archive + MTT GTO 詳細 |

生成スクリプト: `scripts/build_master_gto_charts.py`

### 9.2 検証コマンド例

```bash
# Cash 全シナリオ
uv run scripts/validate_preflop_formula.py --game cash

# MTT 6m SBR25 ChipEV のみ
uv run scripts/validate_preflop_formula.py --game mtt --table 6 --sbr 25 --icm chipev

# ICM フェーズ比較 (9m SBR25)
uv run scripts/validate_preflop_formula.py --icm pct25 pct50 ft --table 9 --sbr 25

# 係数カスタマイズして検証
uv run scripts/validate_preflop_formula.py --game mtt --sbr 25 --params suit_bonus=6 low_pen=0

# 精度ワースト20を表示
uv run scripts/validate_preflop_formula.py --top 20
```

### 9.3 全データ検証サマリー (v7 ベース係数)

| セット | シナリオ数 | 平均精度 |
|---|---|---|
| Cash 6m HU | 58 | 92.8% |
| MTT 6m SBR25 ChipEV | 93 | 93.0% |
| ICM 9m SBR25 pct25/pct50/ft | 50 | 92.5% |
| ICM ft: pct25=92.6%, pct50=93.7%, ft=91.3% | — | — |

## 10. 関連ファイル

| ファイル | 内容 |
|---|---|
| `cash-preflop/PREFLOP_SCORE_SPEC.md` | v3 (現行仕様、Cash only) |
| `cash-preflop/PREFLOP_SCORE_SPEC_V7.md` | 本ドキュメント |
| `cash-postflop/v7_context_optuna.py` | Cash コンテキスト別 Optuna スクリプト |
| `cash-postflop/v7_mtt_compare.py` | Cash vs MTT 係数比較 Optuna スクリプト |
| `cash-postflop/v7_multiway_optuna.py` | MW コンテキスト Optuna (実行中) |
| `scripts/build_mtt_gto_charts.py` | MTT GTO データ → gto-charts 形式変換 |
| `scripts/append_multiway_to_gto_charts.py` | MW シナリオ追加スクリプト |
| `knowledges/preflop/gto-charts.json` | Cash GTO データ (36 シナリオ) |
| `knowledges/preflop/mtt-gto-charts-SBR25.json` | MTT GTO データ (16 シナリオ) |
| `mtt-postflop/findings/mtt_preflop_gto_SBR25_rfi.json` | MTT RFI GTO 生データ |
| `mtt-postflop/findings/mtt_preflop_gto_SBR25_vs_open.json` | MTT BB defense 生データ |

---

## 11. 未解決事項 / 次ステップ

| 項目 | 状態 |
|---|---|
| SB_RFI 精度改善 (68.6% の構造的限界) | GTO リンプ混合戦略を補助ルール化で対応 |
| ICM FT フェーズ低精度 (91.3%) の改善 | 閾値+5 補正で対応済み、さらに詳細検証可能 |
| 書籍本文への反映 | vol1/vol3 の該当章 generator から再生成 |
| poker-drill への統合 | preflop_score.py の係数テーブルを v7 に更新 |
| MTT 9m 係数の最適化 | 現在は 6m 係数を流用。9m 専用 Optuna は任意 |
