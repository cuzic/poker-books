# A モデル 階層型 — Vol2/Vol3 統一構造設計

作成日: 2026-05-28
ステータス: 設計確定 (A+C3 Board family axis 採用)、Vol2/Vol3 書籍書き換え進行中

---

## 設計コンセプト

**Vol2 = Vol3 の純粋なサブセット**。Vol2 読者は 25 cell 表のみ覚え、Vol3 で α/β/offset/ε layer を追加学習。「Vol2 の知識がそのまま Vol3 で使える」を構造的に保証。

---

## 統一式

```
Vol2 (Light):
  freq = base[ctx5][band]
  例外: low_pair -10

Vol3 (Full):
  freq = base[ctx5][band]                       ← Vol2 と同じ
       + α[ctx13]                               ← context 全体 lift
       + β[ctx13] · I(TV ≥ 7)                  ← 強い役の追加 lift
       + offset[category]                       ← slowplay/trash/premium
       + ε[board_family][ctx_group]             ← 板テクスチャ別 (C3 軸)
  
  ctx5: cash / mtt_short / mtt_deep / 3bp / turn (Vol2 と同じ)
  ctx13: 細分化された 13 context (Vol3 で初出)
  board_family: dry_high (baseline) / paired / dynamic / low_dry
  ctx_group: cash / mtt_srp / 3bp
```

暗算ステップ:
- **Vol2**: 4 step (MV/DV → TV → band → base lookup → freq)
- **Vol3**: 7 step (Vol2 + α + β·I(TV≥7) + cat offset + 板分類 + ε)

---

## fit 値 (WLS、combos 加重)

### Vol2 base 25 cell

| Context | air | weak | mid | strong | nut |
|---|---:|---:|---:|---:|---:|
| **cash** | 44% | 37% | 42% | 57% | 62% |
| **mtt_short** | 37% | 30% | 35% | 58% | 73% |
| **mtt_deep** | 42% | 41% | 41% | 58% | 61% |
| **3bp** | 46% | 50% | 61% | 70% | 58% |
| **turn** | 6% | 6% | 3% | 7% | 7% |

### Vol3 α / β layer (13 context)

| Context | α | β (TV≥7) |
|---|---:|---:|
| cash_100bb | +2 | -0 |
| mtt_25bb | **+36** | -5 |
| mtt_50bb | +0 | -3 |
| mtt_100bb | **+26** | -6 |
| mtt_200bb | -5 | -4 |
| mtt_3bp_20bb | -2 | -15 |
| mtt_3bp_25bb | +3 | **-15** |
| mtt_3bp_50bb | +1 | +5 |
| mtt_3bp_100bb | +0 | +8 |
| mtt_25bb_turn_btn | -2 | -4 |
| mtt_50bb_turn_btn | +1 | -4 |
| mtt_100bb_turn_btn | +13 | -4 |
| cash_100bb_turn_btn | +1 | -5 |

### Category offset (Vol3 共通)

| カテゴリ | offset |
|---|---:|
| default | +0 |
| slowplay (set/trips/two_pair/fullhouse/flush/straight/quads) | **+6** |
| trash (low_pair) | **-14** |
| premium (overpair/underpair) | **+7** |

### Board family ε layer (C3 軸)

板分類:
- **dry_high** (baseline): ペアなし + ハイカード J 以上 + ストフラ系なし
- **paired**: ボードに同ランクが含まれる
- **dynamic**: モノトーン、または (ストレート連結 + ツーフラ)
- **low_dry**: ペアなし + 最高ランク T 以下

| family | cash | mtt_srp | 3bp |
|---|---:|---:|---:|
| dry_high | +0 | +0 | +0 |
| paired | +5 | +2 | -1 |
| **dynamic** | **-21** | **-11** | **-6** |
| low_dry | -9 | -9 | -2 |

**読み方**: cash で wet 板 (モノトーンや 678 ツーフラ等) は cbet 頻度が -21pt 落ちる。
mtt_srp と 3bp では落差が緩い (深スタックほど protected check 比率が高い)。

---

## 精度

### Context 別 WRMSE (A+C3 採用後)

| Context | A モデル (A+C3) | A ベース | 旧 5 軸モデル | Vol2 scope (base のみ) |
|---|---:|---:|---:|---:|
| cash_100bb | 18.8% | 20.7% | 16.4% | 21.1% |
| mtt_25bb | 17.6% | 19.6% | 15.5% | 36.1% |
| mtt_50bb | 17.6% | 18.2% | 13.0% | 19.1% |
| mtt_100bb | 25.0% | 26.8% | 22.0% | 35.5% |
| mtt_200bb | 19.9% | 19.8% | 14.1% | 21.5% |
| 3bp_20bb | 21.4% | 21.2% | 23.1% | 15.7% |
| 3bp_25bb | 15.4% | 15.3% | 18.7% | 15.7% |
| 3bp_50bb | 9.3% | 9.0% | 8.6% | 9.6% |
| 3bp_100bb | 13.9% | 14.7% | 13.4% | 15.3% |
| turn_mtt25 | 7.5% | 7.0% | 7.0% | 16.7% |
| turn_mtt50 | 14.5% | 14.4% | 14.4% | 19.1% |
| turn_mtt100 | 25.7% | 26.7% | 27.0% | 35.5% |
| turn_cash100 | 15.6% | 16.2% | 16.1% | 22.5% |
| **OVERALL** | **18.32%** | 18.88% | ~16% | ~21% |

### Light/Full との位置づけ

- **Light**: ~21% (Vol2 既存、25 cell のみ)
- **A モデル (A+C3 採用)**: **18.32%** (Vol2 同じ 25 cell + Vol3 で 38 数値追加)
- **旧 5 軸モデル**: ~16% (Vol3 既存、100+ 数値、5 軸式)

A モデルは Vol2 scope + Vol3 layer で **Light 比 -3pt**、旧 5 軸モデル比 +2pt の中間。**3BP では Full を上回る精度**。

---

## 暗記対象

### Vol2 読者の暗記 (Light と同じ)

- MV テーブル: 6 バケット (2/3/5/7/8/9)
- DV テーブル: 4 段階 (0-3)
- base 25 cell
- low_pair -10 例外
- **計 約 30 数値 + 1 例外**

### Vol3 読者の追加暗記

- α 13 値 (context 全体 lift)
- β 13 値 (TV≥7 のみ)
- カテゴリ offset 3 値
- 板分類 4 family ルール + ε 9 値 (3 family × 3 ctx_group、dry_high baseline)
- **追加 38 数値**

Vol3 合計: **約 68 数値**。現状 旧 5 軸モデル の 100+ 数値から削減、5 軸式から 6 step に簡素化。

---

## 構造の解釈

### α は「context の全体 cbet 頻度」を反映

- **mtt_25bb α=+32**: 「短スタックは push 圏直前で wide cbet」→ +32 全体 lift
- **mtt_200bb α=-8**: 「deep は protected check より厳選 cbet」→ -8
- **mtt_3bp_20bb α=-3**: 「3BP 浅は SPR 低で polarize、中域 check」

### β は「強い役で **追加** 何 % lift するか」

- **mtt_3bp_50/100 β=+5/+7**: 「深 3BP では強い役 (set/two pair) で polarize 強気」
- **mtt_3bp_20/25 β=-14/-15**: 「浅 3BP では強い役で slowplay 顕著」
- 通常 SRP は β ≈ 0 (Light の base で十分捕らえている)

### カテゴリ offset は文脈共通

- **slowplay +5**: set/two pair はやや bet 傾向 (全 context 共通)
- **trash -15**: low_pair は常に bet 控えめ
- **premium +7**: overpair/underpair は bet 強気

---

## 書籍構成への影響

### Vol2 (Cash + Light)

- ch01 TV = MV + DV (変更なし)
- ch02 25 cell 表 (新 base 25 cells、Light v2 と微妙に違うが構造同じ)
- ch08 D モデル (変更なし、D モデルは独立モデル)
- 例外: low_pair -10 のみ (簡素)

### Vol3 (MTT + Full)

- ch01 5 軸式 → **「Vol2 25 cell base + α/β layer + offset」に書き換え**
- ch02 Confidence 判定 → **削除 or 補助章** (新モデルは Confidence 軸使わず)
- ch03 Size 軸 → **削除** (Size 軸廃止、overbet は別途取扱)
- ch04 Context スイッチング → α/β 表の説明に再構成
- ch05 Position lift → **削除 or 簡素化** (新モデルでは pos_lift なし、必要なら例外で追加)
- ch06-09 MTT depth → 各 context の α/β を反映
- ch10 3BP → α/β の SPR 別差を強調
- ch11 Turn → α/β の turn 系を整理
- ch12 D モデル → 変更なし
- ch13 例外 → **「low_pair」と「型6」だけに簡素化**

### 暗算章の変更

- Vol2: 4 step (簡素化、変わらず)
- Vol3: 6 step (現状の 12-15 step から大幅改善)

---

## 実装ファイル

- 候補比較: `vol2-cash-postflop/ucbs_candidates_fit.py`
- 軸追加比較: `vol2-cash-postflop/ucbs_v3_axes.py` (C1/C2/C3 fitting)
- 最終モデル: `vol2-cash-postflop/ucbs_v3_final.py` (A+C3、確定パラメータ書き出し)
- 確定パラメータ: `knowledges/gto_wizard_study/ucbs_v3_params.json`、`UCBS_V3_PARAMS.md`

---

## 残課題

1. **mtt_100bb / mtt_100bb_turn の精度 26-27%** は構造的限界 (MTT6mSimple Simple tree の wide cbet 特性)。これは 旧 5 軸モデル でも同じ。書籍では「精度限界 context」として明示。
2. **書籍書き換え**: Vol2 ch02 (新 25 cell) と Vol3 ch01-13 の書き換えが必要。generator の更新も必要。
3. **D モデルは不変**: D モデルは独立モデルとして温存。Vol2 ch08 と Vol3 ch12 は変更不要。
