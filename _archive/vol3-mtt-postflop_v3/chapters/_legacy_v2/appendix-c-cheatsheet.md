# 第付録C章 A モデル公式チートシート (1 ページ版)

実戦で 30 秒以内に参照できる凝縮版チートシートです。
7 ステップ判定 → MV/DV → TV バンド → α/β/cat/ε の流れをこの 1 枚で完結させます。

## 統一式 (7 ステップ)

```
TV = MV[hand] + DV[draw]
band = air (TV≤2) / weak (3-4) / mid (5-6) / strong (7-8) / nut (9+)

freq = base[ctx5][band]                  ← Vol2 と共通 (25 セル表)
     + α[ctx13]                          ← コンテキスト補正
     + β[ctx13] · I(TV ≥ 7)             ← 強ハンド補正 (TV≥7 のとき)
     + cat[クラス]                          ← ハンドクラス補正 (slowplay +6 / trash -14 / premium +7)
     + ε[board_family][ctx_group]        ← ボード補正

freq = clamp(freq, 0.02, 0.98)
```

### MV テーブル

| HP | 含まれる役 |
|---:|---|
| 2 | ノーペア, Aハイ, Kハイ, ロー・ポケットペア |
| 3 | アンダーペア, サードペア |
| 5 | セカンドペア |
| 7 | トップペア, オーバーペア |
| 8 | セット, トリップス |
| 9 | ツーペア, フラッシュ, ストレート, フルハウス, クアッズ |

### DV テーブル

| DP | ドロー種別 |
|---:|---|
| 0 | ドローなし, BDFD |
| 1 | ガットショット |
| 2 | OESD, フラッシュドロー |
| 3 | コンボドロー |

### ハンドカテゴリ (cat_offset 区分)

| カテゴリ | 含まれる役 |
|---|---|
| slowplay | ツーペア, フラッシュ, ストレート, セット, トリップス, フルハウス, クアッズ |
| trash | ロー・ポケットペア |
| premium | アンダーペア, オーバーペア |
| default | ノーペア, Aハイ, Kハイ, サードペア, セカンドペア, トップペア |

### Layer 1: base 25 セル (Vol2 共通)

| Context | air (TV 0-2) | weak (3-4) | mid (5-6) | strong (7-8) | nut (9+) |
|---|---:|---:|---:|---:|---:|
| Cash 100bb | 44% | 37% | 42% | 57% | 62% |
| MTT 25-50bb | 37% | 30% | 35% | 58% | 73% |
| MTT 100-200bb | 42% | 41% | 41% | 58% | 61% |
| 3-bet pot IP | 46% | 50% | 61% | 70% | 58% |
| Turn 2nd barrel | 6% | 6% | 3% | 7% | 7% |

### Layer 2: α / β layer (13 context)

| Context | α (コンテキスト補正) | β (強ハンド補正、TV≥7) |
|---|---:|---:|
| Cash 100bb | +2 | -0 |
| MTT 25bb | +36 | -5 |
| MTT 50bb | +0 | -3 |
| MTT 100bb | +26 | -6 |
| MTT 200bb | -5 | -4 |
| 3BP 20bb | -2 | -15 |
| 3BP 25bb | +3 | -15 |
| 3BP 50bb | +1 | +5 |
| 3BP 100bb | +0 | +8 |
| Turn MTT25 | -2 | -4 |
| Turn MTT50 | +1 | -4 |
| Turn MTT100 | +13 | -4 |
| Turn Cash100 | +1 | -5 |

### Layer 3: cat_offset (共通)

| Category | 含まれる役 | ハンドクラス補正 |
|---|---|---:|
| default | 通常 (top_pair / second_pair / 等) | +0pt |
| slowplay | set / trips / two_pair / fullhouse / flush / straight / quads | +6pt |
| trash | low_pair | -14pt |
| premium | overpair / underpair | +7pt |

1. **paired**: フロップ 3 枚に同ランクが含まれる
2. **dynamic**: モノトーン (3 枚同スート)、または (ストレート連結 + ツーフラ)
3. **dry_high**: 上記以外で、最高ランクが J 以上 (**baseline**、補正なし)
4. **low_dry**: 上記以外で、最高ランクが T 以下

### Layer 4: ε board family (3 ctx_group)

| Board family | Cash | MTT SRP | 3-bet Pot |
|---|---:|---:|---:|
| Dry High (J 以上のハイカード dry) | +0pt | +0pt | +0pt |
| Paired (ペアボード) | +5pt | +2pt | -1pt |
| Dynamic (モノトーン or 連結ツーフラ) | -21pt | -11pt | -6pt |
| Low Dry (T 以下の dry) | -9pt | -9pt | -2pt |

### D モデル 守備 continue freq (独立モデル)

### DCBS HP 別 base continue freq

| HP | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---:|---:|---:|---:|---:|
| 2 | 67% | 54% | 28% | 40% |
| 3 | 98% | 95% | 84% | 85% |
| 5 | 99% | 96% | 87% | 98% |
| 7 | 100% | 100% | 98% | 100% |
| 8 | 100% | 100% | 100% | 100% |
| 9 | 100% | 100% | 100% | 100% |

### DCBS Kicker offset (HP=2 内の細分化)

| Hand | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |
|---|---:|---:|---:|---:|
| Aハイ | +10pt | +17pt | +5pt | +5pt |
| Kハイ | +1pt | +6pt | +5pt | +0pt |
| ノーペア | -12pt | -13pt | +0pt | -3pt |
| ロー・ポケットペア | +0pt | -10pt | -10pt | -2pt |

## 7 ステップ判定フロー

**Step 1**: MV / DV を判定 → TV = MV + DV

**Step 2**: TV バンドを判定 (air/weak/mid/strong/nut)

**Step 3**: context を選ぶ
- SRP → cash_100bb or mtt_25/50/100/200bb
- 3BP IP → mtt_3bp_20/25/50/100bb
- turn → cash_100bb_turn_btn or mtt_25/50/100bb_turn_btn

**Step 4**: base[ctx5][band] を 25 セル表から lookup (Vol2 と同じ)

**Step 5**: α + β·I(TV≥7) + cat_offset を加算
- α は 13 context 別、β は TV≥7 のみ加算
- cat (ハンドクラス補正): slowplay +6 / trash -14 / premium +7 / default 0

**Step 6**: 板分類 (paired/dynamic/dry_high/low_dry) を判定
- paired: 同ランクあり → paired
- モノトーン or 連結ツーフラ → dynamic
- 最高ランク J 以上 → dry_high (baseline ε=0)
- 上記以外 → low_dry

**Step 7**: ε[board_family][ctx_group] を加算 → 最終 freq

## 精度サマリ (WRMSE)

| 精度帯 | Contexts |
|---|---|
| < 10% (極良) | mtt_25bb_turn_btn (7.5%), mtt_3bp_50bb (9.3%) |
| 10-15% (良) | mtt_3bp_100bb (13.9%), mtt_50bb_turn_btn (14.5%), mtt_3bp_25bb (15.4%), cash_100bb_turn_btn (15.6%) |
| 15-20% (許容) | mtt_25bb (17.6%), mtt_50bb (17.6%), cash_100bb (18.8%), mtt_200bb (19.9%) |
| 20-25% (注意) | mtt_3bp_20bb (21.4%) |
| 25%+ (限界) | mtt_100bb (25.0%), mtt_100bb_turn_btn (25.7%) |

**平均 WRMSE ≈ 18.3%** (A モデル 全体)。
WRMSE 25%+ の context は結果を ±20pt 幅で解釈してください。

---
**暗記対象**: MV 6 値 + DV 4 値 + base 25 セル + low_pair 例外 (Vol2) = 36 数値
+ α 13 + β 13 + cat_offset 3 + ε 9 (Vol3 追加) = **総計 約 70 数値 + 1 式**
