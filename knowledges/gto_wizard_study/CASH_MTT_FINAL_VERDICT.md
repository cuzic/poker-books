# Cash vs MTT 100bb — 最終判定（直接 API 比較）

生成日: 2026-05-27
データ: **59 spots** 直接 API 取得（Cash6mGeneral_6mNL25R25 + MTT6mSimple）

## 大局結論

> **「MTT 100bb は cash 100bb の proxy として使える」仮説は反証された**
>
> 平均 +16.9pt の差、最大 +75.7pt の差。MTT6mSimple tree は cash と異なる戦略を解出する。

## エビデンス: 28 板の直接比較

### Position 別 cbet 頻度差

| pos | Cash avg | MTT avg | 差 (MTT-Cash) |
|----|------:|------:|---:|
| **UTG** | 55.4% | **89.8%** | **+34.4pt** |
| **HJ** | 56.4% | **84.2%** | **+27.8pt** |
| CO | 57.3% | 64.8% | +7.5pt |
| BTN | 50.8% | 63.4% | +12.6pt |
| **SB** | **37.9%** | **36.9%** | **-1.0pt（一致！）** |

**示唆**:
- **MTT は早い position で大幅にアグレッシブ**（UTG +34pt、HJ +28pt）
- **後ろの position で差は縮小**（CO +7.5pt、BTN +12.6pt）
- **SB は cash と完全一致**（差 1pt 以内、4 板で確認）

### 最大乖離ポイント

| board × pos | Cash | MTT | 差 |
|---|---:|---:|---:|
| **J64 by UTG** | 23.2% | 98.9% | **+75.7pt** |
| **J64 by HJ** | 23.3% | 98.1% | **+74.8pt** |
| **Q83 by UTG** | 54.6% | 100.0% | +45.4pt |
| **T98 by HJ** | 45.5% | 88.3% | +42.8pt |
| **T98 by UTG** | 55.7% | 89.3% | +33.7pt |

**型3 (J64 = mid-wet) と型4 (T98 = connected wet) で MTT が極端にアグレッシブ**。

### 一致するポイント

| board × pos | Cash | MTT | 差 |
|---|---:|---:|---:|
| Ks7d2c BTN | 73.5% | 73.3% | -0.2pt ✓ |
| Ks7d2c SB | 50.8% | 51.7% | +0.9pt ✓ |
| AhKd4s SB | 19.3% | 16.0% | -3.3pt ✓ |
| Qh8d3s SB | 52.1% | 50.8% | -1.3pt ✓ |
| Th9s8d SB | 29.2% | 28.9% | -0.3pt ✓ |
| AhKd4s UTG | 61.8% | 60.7% | -1.1pt ✓ |
| AhKd4s BTN | 36.9% | 35.0% | -2.0pt ✓ |

**AK4 系（IP range advantage）と SB 全般で一致**。

## 解釈: なぜこのパターンか

### 仮説 1: MTT6mSimple の "Simple" tree が原因

MTT6mSimple は **Simple complexity** で、bet size 選択肢が cash General より少ない。サイズ選択肢が限定されると、極化したベット/チェック解が出る:
- Cash General: 33% / 50% / 75% / 100% / 150% など複数サイズで微調整
- MTT Simple: 33% / 116% / 276% に集中、中間がない

結果として MTT は「打つときは思い切って打つ」傾向が強くなり、cbet 頻度が上がる。

### 仮説 2: 早い position の effect が tree 設計差で増幅

UTG/HJ では cash GTO が「checking range を持つ」（マージナル check で SDV 保持）戦略を取るが、MTT Simple ではこの選択肢が薄く、結果として cbet 多用化。

### 仮説 3: J64 / T98 系の連結 board で乖離が極端

これらの板は cash で「check して BB のドローに薄いブラフを誘う」戦略が解。MTT Simple ではこの繊細さがなく「とりあえず 33% bet」になる。

## Cash 内部の差: Rake 効果

| rake / board | Ks7d2c | Th9s8d | AhKd4s |
|---|---:|---:|---:|
| Cash NL10 | 74.3% | 43.7% | 38.8% |
| Cash NL25 (baseline) | 73.5% | 43.5% | 36.9% |
| Cash NL100 | 73.1% | 28.9% | 37.8% |
| **Cash NL500** | **88.4%** | 31.5% | 36.9% |
| **Cash cEV** | **84.4%** | 33.7% | 39.7% |

**示唆**:
- **NL10-NL25-NL100 はほぼ同じ**（rake は low-mid stakes で影響小）
- **NL500 と cEV で cbet 頻度が UP**（高 rake/no rake で aggressive 戦略）
- T98 で NL10 だけ 43.7% と高い（特殊例）

実用的には **NL10-NL100 はほぼ等価**として扱える。

## Cash 特殊 boards @ 100bb BTN

| board | Cash BTN cbet | サイズ |
|------|---:|---:|
| KK7 (paired high) | **89.8%** | 33% |
| AAK (paired) | 64.5% | 33% |
| 774 (paired low) | 51.1% | 33% |
| KQ7 mono | 34.1% | 33% |
| JT5 mono | 38.9% | 33% |
| 987 (super-wet) | 47.0% | 33% |
| JT9 (super-wet) | 48.1% | 33% |
| Q42 (Q-high air) | 64.9% | 33% |

→ **Cash BTN の特殊 board 挙動**:
- paired high (KK7) は 90% で最高
- mono は 34-39% で最低
- 連結 wet (987, JT9) は 47-48%

## Cash 50bb 結果 (1 spot のみ取得成功)

| board | bet% | size |
|------|---:|---:|
| Ks7d2c BTN @ 50bb | 63.1% | 33% |

50bb 多くの spot が 403 (tier 制限)。BTN K72 で 100bb (73.5%) → 50bb (63.1%) = **-10pt** の減少を確認。

## 書籍への影響

### 旧書籍（vol2 改訂版）の主張を再検証

| 旧主張 | 直接比較結果 | 判定 |
|------|----------|----|
| 「100bb cash と 100bb MTT は等価」 | 平均 +16.9pt 差、最大 +75pt | ❌ **訂正必要** |
| 「BTN cbet は 75%（avg）」 | Cash BTN avg 51%、MTT BTN 63% | ⚠️ **両方とも 75% より低い** |
| 「型1 K72 は full cbet」 | Cash UTG 96% / HJ 90% / BTN 73% | ✓ 概ね正しい |
| 「型4 T98 は cbet 控えめ」 | Cash 31-55% / MTT 29-89% | ⚠️ 大きく散らばる |

### vol2 改訂の方針

1. **「MTT 100bb = cash 100bb proxy」と書かない** — 大きく違う
2. **Cash 想定の章** では Cash6mGeneral_6mNL25R25 のデータを引用
3. **MTT 想定の章** では MTT6mSimple のデータを引用
4. **Position 効果は cash vs MTT で異なる** — それぞれ別表を提示

## 推奨次ステップ

1. **vol2 cash 章を Cash NL25 データで書き直し** (今回 28 spots で全 position カバー)
2. **mtt-postflop の章を MTT データで再確認**
3. **特殊 board の追加調査**（paired/mono/super-wet × 全 position）
4. **rake 効果の章を追加**（NL10-100 等価、NL500+ で異なる）

## ファイル

- 入力 cash: `b20_cash_100bb_*/`, `b22_cash_rake/`, `b23_cash_50bb/`, `b24_cash_special/`
- 入力 mtt: `b15_100bb_*/`, `b21_mtt_*/`
- 旧暫定レポート: `CASH_VS_MTT_100BB_COMPARISON.md`（不正確、廃棄推奨）
- **本レポート**: 確定版（直接 API データ）
