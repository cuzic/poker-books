---
chapter: "appendix-B"
title: "付録B　シリーズ式のおさらい"
section: "付録"
target_kchar: 5
status: draft
---

# 付録B　シリーズ式のおさらい

本書 (Vol3 MATCHA Exploits) は Vol1 (MATCHA Formula) + Vol2 (MATCHA Framework) を前提としています。この付録では、両巻の式を要約しておさらいしていきましょう。

---

## Vol1: MATCHA Formula (プリフロップ)

### プリフロップスコア式

```
Score = H + L
      + ペアボーナス     (ペアのみ +10)
      + スーテッドボーナス (suited +3)
      + コネクター差1    (+1) / 差 2-3 (+0.5)
      + ブロッカー: A=+3 / K=+2 / AK 両方=+4
      − ペナルティ: 差 4 以上 (-1、A 含むと免除) / 両カード 9 未満 (-1)
```

H, L はランクの数値 (A=14, K=13, ..., 2=2) です。

### T_open 閾値 (通常値)

| ポジション | 通常値 |
|----------|--------|
| UTG | 24 |
| HJ | 22 |
| CO | 20 |
| BTN | 18 |
| SB | 22 |

### T_3bet 閾値 (通常値)

| 状況 | T_3bet |
|---|---|
| BTN vs UTG | 32 |
| SB vs CO | 34 |
| BB vs HJ | 30 |

### T_4bet 閾値

通常 T_4bet = 33 です。

---

## Vol2: MATCHA Framework (ポストフロップ)

### MATCHA Score 公式

```
Score = Grid[カテゴリ][board] + DV × mult[street] + 2 × oc + 4 × pot − 2 × bs
判定: Score ≥ 43 → raise / ≥ 14 → call / else fold
```

### 5 つの判定軸

1. **レンジ分布** (range_morphology): 2 極化型 / 混在型 / 密集型
2. **ハンドストレングス** (hand_strength_tier): 2P+ / トップペア以上 (TP+) / ミドルペア / エア
3. **ベットサイジング** (bet_size_tier): スモール (33%) / ミディアム (75-100%) / オーバー (125%+) / オールイン
4. **SPR** (spr_tier): オールイン / ロー / ミディアム / ディープ
5. **エクイティバケット** (equity_aware_tier): 2P+ / 良ハンド / 弱ハンド / ブラフハンド

### 12 cells grid (カテゴリ × board)

| カテゴリ \ board | dry | paired | wet |
|---|---|---|---|
| 2P+ | 35 | 30 | 32 |
| TP+ | 22 | 18 | 20 |
| ミドルペア | 8 | 5 | 6 |
| エア | 0 | -2 | -1 |

(実値は Vol2 で確定されており、上記は概略です)

### DV (Draw Value)

| dv_cat | 値 (flop) | 値 (turn) | 値 (river) |
|---|---|---|---|
| コンボドロー | 12 | 8 | 0 |
| フラッシュドロー | 9 | 6 | 0 |
| OESD | 9 | 6 | 0 |
| ガットショット | 3 | 2 | 0 |
| BDFD | 3 | 2 | 0 |
| ドローなし | 0 | 0 | 0 |

### pot 種別

| 略称 | 正式 | 値 |
|---|---|---|
| SRP | Single Raised Pot | 0 |
| vs CR | CR ディフェンス (vs Check-Raise / vs Donk) | 2 |
| 3BP | 3-bet Pot | 2 |
| 4BP | 4-bet Pot | 4 |

### 3 つの補正

1. **vs CR 補正**: Check-Raise / Donk Bet に対応する補正
2. **vs Donk 補正**: 同様に Donk Bet 対応の補正です
3. **オープナー補正**: CO / HJ open river に適用します

---

## Vol3: MATCHA Exploits (本書) の追加

### タイプ別 Score シフト

| タイプ | shift |
|---|---|
| ニット相手 | +5 |
| CS 相手 | +3 |
| LAG 相手 | +8 |
| マニアック相手 | +12 |
| TAG 相手 | +2 |

### タイプ別 T_open シフト (BTN)

| タイプ | BTN T_open |
|---|---|
| ニット相手 | 13〜14 |
| CS 相手 | 15〜16 |
| LAG 左隣 | 21〜23 |
| マニアック 左隣 | 26〜28 |
| TAG | 18 (変更なし) |

### 5 つの逸脱軸 (本書のフレームワーク)

1. レンジ逸脱 (range imbalance)
2. 頻度逸脱 (frequency imbalance)
3. サイズ逸脱 (sizing imbalance)
4. ポジション逸脱 (position imbalance)
5. 判断逸脱 (decision imbalance)

---
