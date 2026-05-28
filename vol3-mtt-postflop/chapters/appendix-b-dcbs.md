# 付録 B: Full DCBS 4 context continue freq 完全表

Full DCBS（守備 continue freq）の数値をすべて 1 ページに凝縮したリファレンスです。
BB としてベットに直面したとき、HP とコンテキストを確認してこの表を参照してください。

## DCBS の計算式

DCBS（Defensive CBS Score）の continue freq は 2 段階で決まります。

```
continue_freq = base_dcbs[context][HP]
              + kicker_offset[context][hand]  ← HP=2 の手のみ適用

fold_freq = 1.0 − continue_freq
```

HP は UCBS-v2 と共通のバケット（2 / 3 / 5 / 7 / 8 / 9）を使います。
HP=2 の手（ノーペア系 / ロー・ポケットペア）はさらに kicker で細分化します。

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

## depth で反転する守備戦略

DCBS の最大の発見は「depth が増すほど air は fold する」という反転です。

| Context | air (HP=2) 基本 freq | top_pair (HP=7) freq |
|---|---:|---:|
| mtt_25bb（浅） | 67% | 100% |
| mtt_50bb（中） | 54% | 99% |
| mtt_100bb（深） | 28% | 98% |
| cash_100bb（基準） | 40% | 100% |

浅スタック（25bb）では air でも 67% call が GTO です。
これは「残りチップが少なく、フォールドコストが大きい」ためです。
深スタック（100bb）では air は 28% まで下がります。
top_pair 以上（HP≥7）はどの context でも 96%+ call となり、ほぼ変化しません。

## 計算例

### DCBS 計算スケッチ（3 例）

**例**: ノーペア (no_made_hand) を mtt_25bb で defense

1. HP = **2**
2. base = DCBS_BASE[mtt_25bb][HP=2] = **67%**
3. kicker offset (no_made_hand) = -12pt
→ **continue freq = 55%** (fold = 44%)

**例**: Aハイ (ace_high) を mtt_50bb で defense

1. HP = **2**
2. base = DCBS_BASE[mtt_50bb][HP=2] = **54%**
3. kicker offset (ace_high) = +17pt
→ **continue freq = 71%** (fold = 28%)

**例**: トップペア (top_pair) を mtt_100bb で defense

1. HP = **7**
2. base = DCBS_BASE[mtt_100bb][HP=7] = **98%**
→ **continue freq = 98%** (fold = 2%)
