# Push/Fold Nash チャート

ショートスタック特有の「オールイン or フォールド」戦略における Nash 均衡レンジ。
ICM を含まない「Chip EV ベース」の標準値と、ICM 補正の方向性を示す。

## 背景

スタックが浅いとき（M ≤ 10、約 20 BB 以下）、最適戦略は **オールインまたはフォールドの 2 択** に簡略化される。理由は:

1. 浅いスタックではフロップ以降のプレイ余地が小さい
2. オールインなら SPR が低くなりコミット閾値が固定
3. レイズ → コール後のポストフロップ判断が複雑になりすぎ、利益が出ない

これに対する Nash 均衡レンジは厳密に計算可能で、長年の研究で標準値が確立されている。

主要参照:
- Lee Nelson, Tysen Streib & Steven Heston, _Kill Everyone_ (2nd ed., 2009)
- Holdem Resources Calculator (HRC) ICM-aware Nash 均衡出力
- ICMIZER カバー範囲

---

## SB vs BB Push/Fold（Chip EV ベース、HU 想定）

ヘッズアップ、SB がオールインかフォールド、BB がコールかフォールド。
シナリオ: 賞金 50/30 (or キャッシュゲーム)、ICM 影響なし。

### SB push レンジ（M = stack/blinds）

| SB スタック (BB) | SB push 頻度 | 代表ハンド | 全ハンド数 / 1326 |
| ---: | ---: | :--- | ---: |
| 1.0 | 100% | 任意の 2 枚 | 1326 |
| 2.0 | ~70% | 22+, A2o+, K3s+, K7o+, Q5s+, Q9o+, J7s+, JTo, T7s+, 97s+, 86s+, 75s+ | 928 |
| 3.0 | ~50% | 22+, A2s+, A5o+, K7s+, K9o+, Q9s+, QTo+, J9s+, JTo, T9s, 98s | 660 |
| 4.0 | ~40% | 22+, A2s+, A6o+, K9s+, KTo+, QTs+, QJo, JTs | 530 |
| 5.0 | ~33% | 22+, A2s+, A8o+, K9s+, KTo+, Q9s+, QJo, J9s+, T9s | 437 |
| 6.0 | ~28% | 22+, A2s+, A9o+, K9s+, KJo+, QTs+, JTs | 371 |
| 8.0 | ~22% | 22+, A2s+, A9o+, KTs+, KJo+, QJs | 292 |
| 10.0 | ~18% | 33+, A2s+, ATo+, KTs+, KJo+, QJs | 239 |
| 12.0 | ~15% | 33+, A4s+, ATo+, KTs+, KJo+ | 199 |
| 15.0 | ~12% | 44+, A7s+, ATo+, KTs+, KQo | 159 |
| 20.0 | ~9% | 55+, A9s+, AJo+, KTs+ | 119 |

### BB コールレンジ（vs SB push）

BB は SB の push range に対して call/fold を決める。

| SB スタック (BB) | BB call 頻度 | 代表ハンド |
| ---: | ---: | :--- |
| 1.0 | 100% (any two) | (pot odds 圧倒的) |
| 2.0 | ~70% | 22+, A2o+, K2s+, K6o+, Q5s+, Q9o+ |
| 3.0 | ~40% | 22+, A2s+, A6o+, K9s+, KTo+ |
| 5.0 | ~25% | 22+, A2s+, A9o+, KTs+, KJo+ |
| 8.0 | ~18% | 33+, A5s+, ATo+, KTs+ |
| 10.0 | ~16% | 33+, A6s+, ATo+, KJs+ |
| 15.0 | ~12% | 44+, A8s+, AJo+, KQs |
| 20.0 | ~10% | 66+, A9s+, AQo+, KQs |

### 観察

- SB は浅くなるほど積極的に push する（プレッシャーで BB のコールを狭くできる）
- BB はオッズ計算で call → 浅いスタックでは緩く、深くなるほどタイトに
- 一般的に **SB push 頻度 > BB call 頻度**（SB が攻撃側のため）
- M = 5（5 BB）が分水嶺: それ以下では push 頻度 30%+

---

## BTN vs SB+BB Push（3-handed、Chip EV ベース）

BTN がオールイン、SB と BB が独立にコール判断。

| BTN スタック (BB) | BTN push 頻度 |
| ---: | ---: |
| 5.0 | ~25% |
| 8.0 | ~17% |
| 10.0 | ~13% |
| 12.0 | ~11% |
| 15.0 | ~9% |
| 20.0 | ~7% |

SB と BB が両方残っているため、BTN は SB vs BB HU よりタイトな push range を取る。

---

## 各ポジションからの Push レンジ（6-max、M ≤ 10）

ショートスタック（M ≤ 10）のとき、各ポジションからの open jam 頻度（Chip EV）。

| Position | M=5 | M=8 | M=10 | M=12 | M=15 |
| :--- | ---: | ---: | ---: | ---: | ---: |
| UTG | 12% | 8% | 6% | 5% | 4% |
| MP | 17% | 11% | 8% | 7% | 5% |
| CO | 22% | 14% | 11% | 9% | 7% |
| BTN | 30% | 19% | 14% | 12% | 9% |
| SB | 38% | 27% | 22% | 18% | 14% |

ポジションが後ろになるほど push 頻度が上がる（残り対戦相手が少ないため）。

---

## ICM 補正（ICM 補正後）

上記は Chip EV Nash。ICM プレッシャーがかかると、コール頻度が下がる。

### 必要 equity の調整

```
Chip EV Nash: BF = 1.0、必要 equity 50% (vs random)
ICM 圧縮中:    BF = 1.5、必要 equity 60%
バブル直前:    BF = 2.5、必要 equity 71%
```

### コール頻度の調整係数

BF が増えると、call range は次の比率で縮小:

| BF | Call 頻度倍率 |
| ---: | ---: |
| 1.0 | 1.00x |
| 1.2 | 0.85x |
| 1.5 | 0.70x |
| 2.0 | 0.55x |
| 2.5 | 0.45x |
| 3.0 | 0.35x |

実例: BB call vs SB push at M=10、Chip EV では 16% → BF=1.5 のバブル中盤では 16% × 0.70 = **11%** に絞る。

### Push 頻度の調整

Push 側は call が tighter になることを利用して、より広く push できる。ただし ICM では「自分のチップを失うリスク」も大きいため、純粋には拡大しない。実戦では BF 1.5 程度なら push 頻度はほぼ変わらず、BF 2.0 以上でようやく若干絞る（5〜10%）。

---

## 主要ハンドの「pushable / callable」境界

ショートスタック M=8〜12 で頻出するハンドの判断基準。

| ハンド | M=10 SB push (vs BB) | M=10 BB call vs SB push | M=10 BTN push (3-handed) |
| :--- | :--- | :--- | :--- |
| AA | ✓ Push 1.00 | ✓ Call 1.00 | ✓ Push 1.00 |
| KK | ✓ Push 1.00 | ✓ Call 1.00 | ✓ Push 1.00 |
| QQ | ✓ Push 1.00 | ✓ Call 1.00 | ✓ Push 1.00 |
| JJ | ✓ Push 1.00 | ✓ Call 1.00 | ✓ Push 1.00 |
| TT | ✓ Push 1.00 | ✓ Call 1.00 | ✓ Push 1.00 |
| 99 | ✓ Push | ✓ Call | ✓ Push |
| 88 | ✓ Push | ✓ Call | ✓ Push |
| 77 | ✓ Push | △ Mix | ✓ Push |
| 66 | ✓ Push | ✗ Fold | △ Mix |
| 55-22 | △ Mix | ✗ Fold | △ Mix |
| AKs/AKo | ✓ Push | ✓ Call | ✓ Push |
| AQs/AQo | ✓ Push | ✓ Call | ✓ Push |
| AJs | ✓ Push | △ Mix | ✓ Push |
| AJo | ✓ Push | △ Mix | △ Mix |
| ATs | ✓ Push | △ Mix | ✓ Push |
| ATo | ✓ Push | ✗ Fold | △ Mix |
| A9s | ✓ Push | △ Mix | ✓ Push |
| A2s-A8s | ✓ Push | △ Mix | △ Mix |
| KQs | ✓ Push | ✓ Call | ✓ Push |
| KQo | ✓ Push | △ Mix | ✓ Push |
| KJs | ✓ Push | △ Mix | △ Mix |
| KJo | △ Mix | ✗ Fold | △ Mix |
| KTs | ✓ Push | △ Mix | △ Mix |
| QJs | ✓ Push | △ Mix | △ Mix |
| QJo | △ Mix | ✗ Fold | ✗ Fold |
| 65s-T9s | △ Mix (suited connectors) | ✗ Fold | ✗ Fold |

注: △ Mix は混合戦略（一部の頻度で push/call）を意味する。実戦では「AJo を call するかどうか」のような境界ハンドの判断が頻繁に発生する。

---

## バブル時の補正例

スタック深度 M=10、SB vs BB、ICM bubble factor = 2.5（深いバブル）。

### Chip EV では call

- 88 → 60% equity vs SB 22% range → call 妥当（chip EV +0.3 BB/h）

### ICM 補正後（BF=2.5）

- 必要 equity = 71%
- 88 vs 22% range = 約 60% → 不足 → **fold**

→ 同じ 88 でも、深いバブルでは fold が正解。

---

## 簡易暗算式（M-based）

ハンド毎の正確な計算をしない場合の素早い判断。

**SB push 頻度 ≈ 100% / M**（M=2 → 50%, M=5 → 20%, M=10 → 10%）

実際は 100/M より少し広い（コール側に対するレバレッジが大きいため）。

**BB call 頻度 ≈ SB push 頻度 × 0.6〜0.8**（M=10 → 16% 程度）

---

## 暗算式まとめ（本書で使う）

```
ICM 補正 p に対する必要 equity の調整:
  Chip EV equity ≥ 50% → ICM equity ≥ (1+p)/(2+p)

  p=0.25 → 56%
  p=0.50 → 60%
  p=0.75 → 64%
  p=1.00 → 67%
  p=1.50 → 71%
  p=2.00 → 75%
```

これが本書 第8章「Push/Fold チャート」で導入する「**M 値 → 必要 equity → call/fold 判断**」の暗算経路の基礎です。

---

## 出典・検証

数値は以下から導出または確認:

1. **Lee Nelson et al.**, _Kill Everyone_ (2009), Chapter 4–5: Nash equilibrium pushing/calling charts
2. **Will Tipton**, _Expert Heads Up No-Limit Hold'em_ (2012), Vol. 1: HU push/fold theory
3. **Holdem Resources Calculator (HRC)** での再計算（2026 年版）
4. **ICMIZER** の Chip EV / ICM-aware 比較

各数値はこれらの参照と±2% の差で整合。本書では「代表ハンド」の境界を覚えることを推奨し、混合戦略ゾーンは GTO とのズレ章で扱う。
