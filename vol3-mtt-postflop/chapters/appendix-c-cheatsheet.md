# 付録 C: UCBS-v2 公式チートシート（1 ページ版）

実戦で 30 秒以内に参照できる凝縮版チートシートです。
5 ステップ判定 → HP/DP → Confidence → freq の流れをこの 1 枚で完結させます。

## 統一式（5 軸）

```
CBS = HP[hand] + DP[draw]

freq = base_freq[(conf, direction, size)]
     + α                      # context 均一シフト
     + β · I(CBS ≥ 7)        # 強い役帯 lift（ターンは β≈0）
     + offset[category]       # slowplay/trash/premium 補正
     + pos_lift[position]     # SB/BTN/CO/HJ/UTG 補正
     + ax_range_bet           # A-x range bet（MTT BTN/CO のみ）

freq = clamp(freq, 0.02, 0.98)
```

**閾値 T = 5（全 context 共通）**
direction = (CBS ≥ T) → true = bet 寄り / false = check 寄り

### HP テーブル

| HP | 含まれる役 |
|---:|---|
| 2 | ノーペア, Aハイ, Kハイ, ロー・ポケットペア |
| 3 | アンダーペア, サードペア |
| 5 | セカンドペア |
| 7 | トップペア, オーバーペア |
| 8 | セット, トリップス |
| 9 | ツーペア, フラッシュ, ストレート, フルハウス, クアッズ |

### DP テーブル

| DP | ドロー種別 |
|---:|---|
| 0 | ドローなし, BDFD |
| 1 | ガットショット |
| 2 | OESD, フラッシュドロー |
| 3 | コンボドロー |

### ハンドカテゴリ（offset 区分）

| カテゴリ | 含まれる役 |
|---|---|
| slowplay | ツーペア, フラッシュ, ストレート, セット, トリップス, フルハウス, クアッズ |
| trash | ロー・ポケットペア |
| premium | アンダーペア, オーバーペア |
| default | ノーペア, Aハイ, Kハイ, サードペア, セカンドペア, トップペア |

### 13 context パラメータ早見表（±%pt）

| Context | α | β | slowplay | trash | premium | SB lift | wide lift | A-x lift |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cash_100bb | +0 | -2 | +2 | -23 | +15 | -8 | +10 | +0 |
| mtt_25bb | +6 | +31 | -28 | -23 | +15 | -10 | +13 | +30 |
| mtt_50bb | -4 | +19 | -12 | -35 | +20 | -29 | +0 | +11 |
| mtt_3bp_20bb | +2 | +14 | -40 | -3 | -4 | +0 | +0 | +0 |
| mtt_3bp_25bb | +9 | +19 | -66 | -44 | -9 | +0 | +0 | +0 |
| mtt_3bp_50bb | +7 | +30 | -40 | -45 | +14 | +0 | +0 | +0 |
| mtt_3bp_100bb | +5 | +30 | -33 | -48 | +20 | +0 | +0 | +0 |
| mtt_25bb_turn_btn | -41 | +1 | -28 | -1 | +8 | +0 | +0 | +0 |
| mtt_50bb_turn_btn | -37 | -0 | -25 | -3 | +10 | +0 | +0 | +0 |
| mtt_100bb_turn_btn | -26 | -0 | -26 | -14 | +32 | +0 | +0 | +0 |
| cash_100bb_turn_btn | -37 | +0 | -27 | -8 | +22 | +0 | +0 | +0 |
| mtt_3bp_ip | +2 | +14 | -40 | -3 | -4 | +0 | +0 | +0 |
| mtt_200bb | -4 | +11 | -15 | -31 | +14 | -34 | +0 | +9 |
| mtt_100bb | +15 | +9 | -17 | -19 | +8 | -11 | +17 | +28 |

### DCBS 守備 continue freq（HP 別 base）

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

## 5 ステップ判定フロー

**Step 1: context を選ぶ**
- SRP → スタック深度で mtt_25/50/100/200bb または cash_100bb
- 3BP IP → SPR で mtt_3bp_20/25/50/100bb
- ターン継続 → フロップ context の _turn 版

**Step 2: CBS を計算する**
- CBS = HP + DP（上表参照）
- T=5 と比較して direction を決める

**Step 3: Confidence を決める**
- |CBS − T| ≥ 3 → HIGH（distance 大）
- 型1 かつ distance ≤ 2 → HIGH（型1 特権）
- 型7 かつ distance = 0 → HIGH / distance = 1 → LOW
- distance = 2 → MID
- 型5（モノトーン）→ MID 固定
- 型3/型4 → LOW
- その他 → MID

**Step 4: freq を計算する**
- base_freq[(conf, direction, 33)] から開始（MTT は常に size=33）
- α + β·I(CBS≥7) + offset[category] + pos_lift + ax_lift を加算

**Step 5: 例外 4 ルールを確認する**

**例外①** 型6 board（ペア rank ≥ Q）→ Confidence を 1 段 up（LOW→MID / MID→HIGH）

**例外②** mono board（cash のみ）→ Confidence を 1 段 down（HIGH→MID / MID→LOW）

**例外③** A-x range bet（MTT BTN/CO のみ）→ is_ax_dry_or_paired が true なら ax_range_bet を加算
- is_ax_dry_or_paired = (high_card=A) かつ (paired OR gap ≥ 8)

**例外④** Turn shift → α から −35pt、β を 0 に設定（_turn context 選択で自動適用）

## 精度サマリ（WRMSE）

| 精度帯 | Contexts |
|---|---|
| < 10%（極良） | mtt_3bp_50bb (8.62%), mtt_25bb_turn (7.02%) |
| 10–15%（良） | mtt_50bb (12.96%), mtt_3bp_100bb (13.37%), mtt_200bb (14.10%), mtt_50bb_turn (14.44%), mtt_25bb (15.46%) |
| 15–20%（許容） | cash_100bb (16.43%), cash_turn (16.11%), mtt_3bp_25bb (18.65%) |
| 20%+（注意） | mtt_100bb (21.95%), mtt_3bp_20bb (23.08%), mtt_100bb_turn (26.95%) |

**平均 WRMSE ≈ 16%**（cbet + DCBS 全体）。
WRMSE 20%+ の context は結果を ±10pt 幅で解釈してください。

---
**暗記対象**: HP 6値 + DP 4値 + BASE_FREQ 8セル = 18 数値（共通）
+ context パラメータ約 78 数値 + DCBS 32 数値 = **総計 128 数値 + 1 式 + 4 例外**
