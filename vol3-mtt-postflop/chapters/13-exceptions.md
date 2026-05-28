# 第13章 例外ルール 4 つ——型6/mono/A-x/turn-shift

Full UCBS-v2 には 4 つの例外ルールがあります。
O4（型6 信頼度 up）・O5（mono board 信頼度 down、cash のみ）・O8（A-x range bet）・
O9（turn shift）の 4 ルールです。
各ルールの出現条件・GTO 根拠・WRMSE 改善幅を順に解説し、適用フローを整理します。

## 例外ルール一覧——4 つの補正と適用タイミング

Full UCBS-v2 の計算は基本的に「CBS → Confidence → freq」という流れで進みます。
4 つの例外ルールはそれぞれ異なるタイミングで介入します。

| 例外 | 通称 | 適用タイミング | 適用 context |
|---|---|---|---|
| O4 | 型6 信頼度 up | Confidence 計算後（前段） | 全 13 context |
| O5 | mono board 信頼度 down | Confidence 計算後（前段） | cash のみ |
| O8 | A-x range bet | freq 計算後（後段加算） | MTT BTN/CO のみ |
| O9 | turn shift | context 選択時 | turn context |

**前段例外（O4/O5）**: Confidence を決定した後、その値を上下に 1 段ずらします。
このシフトが base_freq の選択に影響するため、freq への影響が大きいです。
**後段加算（O8）**: freq の計算が完了した後に加算するため、他のパラメータと独立しています。
**context 選択時（O9）**: turn context を選んだ時点で α と β が自動的に変換されます。

4 例外の適用フロー（統合）:

```
1. board_type を判定（型1〜7）
2. CBS = HP + DP を計算
3. Confidence を calc_confidence() で算出
4. [O4] 型6 なら conf を 1 段 up（LOW→MID / MID→HIGH）
5. [O5] mono かつ cash なら conf を 1 段 down（HIGH→MID / MID→LOW）
6. direction = (CBS >= T=5)
7. size = polarize ? 116 : 33
8. base = BASE_FREQ[(conf, dir, size)]
9. freq = base + α + β·I(CBS≥7) + offset[category]
10. freq += pos_lift[position]
11. [O8] BTN/CO かつ MTT かつ ax_dry_or_paired なら freq += ax_range_bet
12. freq = clamp(freq, 0.02, 0.98)
※ turn context を選んだ時点で自動的に α≈-0.35 / β≈0 が適用（[O9]）
```

## 例外①: 型6 信頼度 up（O4）——mid 連結ウェット板

**適用条件**: ボード分類が型6（ペア rank ≥ Q のペア板）。例: KK7、QQ4、AA9 など。
適用 context は全 13 context 共通です。

**変換ルール**:
- LOW → MID（1 段 up）
- MID → HIGH（1 段 up）
- HIGH はそのまま変化なし

```python
# apply_confidence_exception() の実装
if board_type == 6:
    if conf == "LOW":
        conf = "MID"
    elif conf == "MID":
        conf = "HIGH"
```

**GTO 根拠**: 型6 ボード（高ランクペア板）では開幕者がオーバーペアや KK 等の強い手を
多く保有し、BB も A-x など Aハイ帯を多く保有します。
そのため「レンジ全体が関連するボード」となり、中間距離（|CBS-T|=1〜2）でも
HIGH/MID として扱える根拠が強まります。
GTO Wizard の実測データでは、型6 ボードでの cbet 頻度が他の型と比べて
平均 +8〜12pt 高く、Confidence を 1 段 up することでこの傾向を再現できます。

**WRMSE 改善**: cash_100bb での型6 ボード実測。
- 適用あり: WRMSE **12.1%**
- 適用なし: WRMSE **14.3%**（-2.2pt 悪化）
- 全体への貢献: 約 -0.5pt（型6 が全ボードの約 15%）

**覚え方**: 「高ランクペア板は自信 UP」。
KK・QQ が出たら Confidence を 1 段強気に読む。
LOW → MID、MID → HIGH に変換してから freq を引く。

### 型6 ボードでの信頼度 up 効果（計算例）

**例**: Aハイ (ace_high) on `KhKd7c` (BTN, context=mtt_25bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +6, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 51%**

**例**: サードペア (third_pair) on `QsQh4d` (BTN, context=cash_100bb)

1. HP = 3, DP = 0, CBS = **3**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +0, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 45%**

## 例外②: mono board 信頼度 down（O5）——cash のみ

**適用条件**: ボードが mono（3 枚同スーツ）。例: Kh7h2h、Td8d5d など。
適用 context は **cash_100bb のみ**（MTT context は `mono_conf_down=False` のため不適用）。

**変換ルール**:
- HIGH → MID（1 段 down）
- MID → LOW（1 段 down）
- LOW はそのまま変化なし

```python
# apply_confidence_exception() の実装
if mono_down and suit_pattern == "mono":
    if conf == "HIGH":
        conf = "MID"
    elif conf == "MID":
        conf = "LOW"
```

**GTO 根拠**: cash ゲームでは overbet（116%）が使用可能であり、mono board では
IP のレンジが「ナッツ系（フラッシュ完成）とブラフ系」に polarize します。
この二極化により中間的なハンドの bet 根拠が弱まり、全体の cbet 頻度が下がります。
実測では mono board の cbet 頻度が通常板より -5〜-10pt 低く、
Confidence を 1 段 down することで再現できます。

**MTT が適用外の理由**: MTT では bet サイズが 33% 固定（polarize_enabled=False）であり、
polarize の影響が cash ほど大きくありません。
サイズが小さいため、mono board でも bet の根拠が相対的に維持されます。

**WRMSE 改善**: cash_100bb での mono board（全ボードの約 5%）実測。
- 適用あり: WRMSE **11.2%**
- 適用なし: WRMSE **14.8%**（-3.6pt 悪化）

**覚え方**: 「3 枚同色（cash）は自信 DOWN」。
Kh7h2h など全部同じマークなら Confidence を 1 段慎重に。
HIGH → MID、MID → LOW に変換してから freq を引く。
MTT ではこのルール不要（bet が小さいため影響が薄い）。

## 例外③: A-x range bet（O8）——MTT BTN/CO のみ

**適用条件**: 以下の 3 条件を全て満たす場合に適用します。
1. context が MTT（cash_100bb は ax_range_bet=0.0 のため不適用）
2. ポジションが BTN または CO
3. ボードが A-high かつ（paired または gap ≥ 8）

```python
def is_ax_dry_or_paired(features):
    if features["high"] != "A":
        return False
    return features["paired"] or features["gap"] >= 8
# gap = top カード rank - low カード rank
# 例: Ac5d2h の gap = A(14) - 2(2) = 12 → gap ≥ 8 → ax range bet 適用
```

**context 別の ax_range_bet 値**:

| Context | ax_range_bet | 用途 |
|---|---:|---|
| mtt_25bb | **+30pt** | 終盤でも range bet ほぼ 100% |
| mtt_50bb | **+11pt** | 中盤は控えめ |
| mtt_100bb | **+28pt** | 序盤でも range bet 活発 |
| mtt_200bb | **+9pt** | 深スタックは穏やかな加算 |

**GTO 根拠**: MTT の BTN/CO は「A-high dry/paired board では range 全体で小 bet する」
戦略が GTO 最善に近いことが実測で確認されています。
A はオープナーのレンジ強度が高く、BB との equity gap が大きいため、
ほぼ全ハンドで小 bet（33%）が成立します。
実測では BTN の Ac5d2h で全 hand カテゴリが 80%+ bet を選択し、
通常の UCBS-v2 予測を 30pt 超えることが確認されています。

**覚え方**: 「MTT の BTN/CO でエース高 + 散らばり板 → 全部ベット」。
A + (ペア板 or 3 カード間隔 8 以上) が条件。
25bb 終盤: +30pt（ほぼ全ハンドで cbet）
50bb 中盤: +11pt（穏やかな range bet）
100bb 序盤: +28pt（序盤でも range bet 活発）

### A-x range bet の適用例

**例**: サードペア (third_pair) on `Ah7d2c` (BTN, context=mtt_25bb)

1. HP = 3, DP = 0, CBS = **3**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +6, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 81%**

**例**: Aハイ (ace_high) on `AsKs3h` (BTN, context=mtt_100bb)

1. HP = 2, DP = 0, CBS = **2**
2. threshold = 5, |CBS-T| → confidence = **HIGH**
3. direction = (CBS≥T) = **False**
4. size = **33%** (small)
5. base_freq[(HIGH, False, 33)] = **45%**
6. α = +15, β·I(CBS≥7) = +0, offset(default) = +0
→ **frequency = 88%**

## 例外④: turn shift（O9）——α -35、β 廃止

**適用条件**: フロップ cbet 後、ターンに進んで 2nd barrel を検討する場合。
turn context（mtt_25bb_turn_btn 等）を選択した時点で自動適用されます。

**変換ルール（mtt_25bb → mtt_25bb_turn_btn の例）**:

| パラメータ | Flop (mtt_25bb) | Turn (mtt_25bb_turn_btn) |
|---|---:|---:|
| **α** | +0.06 | **-0.41** |
| **β (CBS≥7)** | +0.31 | **+0.01** |
| off_slowplay | -0.28 | -0.28（変化なし） |
| off_trash | -0.23 | **-0.01**（緩和） |
| off_premium | +0.15 | +0.08 |

**書籍ルール**: ターンに入ったら α を -35pt シフト、β をゼロにする。
フロップで α=+6pt だった mtt_25bb → ターンで α=-41pt（差 -47pt）。
強い役でも追加 lift（β）はなくなります。
low_pair（trash）はターンで復活します（off_trash が -0.23 → -0.01 に緩和）。

**GTO 根拠**: ターンでは全体の bet 頻度が約 35% 低下します。
GTO 実測でフロップ平均 55% → ターン平均 35〜45% に減少します。
強い役（CBS≥7）への追加 lift（β）が消えるのは、ターンでは役の強さよりも
「ボード変化との相性」が支配的になるためです。
off_trash が緩和されるのは、ターンでは low_pair も一部 bet 有力になるためです。

**WRMSE 改善**: ターン context の精度（α シフト + β 廃止の効果）。
- mtt_25bb_turn: WRMSE **7.02%**（全 13 context 中最高精度）
- 参考フロップ mtt_25bb: 15.46%
- α シフトなし（フロップ mtt_25bb をそのまま使用）: WRMSE 推定 35%+ に悪化

**完成役 turn card の限界**:
ターンカードがストレート/フラッシュを完成させる場合は UCBS-v2 非対応です（ch14 詳述）。
KJT + Q（ストレート完成）で WRMSE 28%、T98r + 7 で WRMSE 19% と精度が著しく低下します。

**覚え方**: 「ターンに入ったら α を -35、β をゼロに」。
ただしストレート/フラッシュ完成カードは UCBS-v2 非対応、手の絶対強度で判断する。

## まとめカード

| 例外 | 一言 | 適用スコープ |
|---|---|---|
| O4 型6 up | 高ランクペア板 → Conf +1 段 | 全 13 context |
| O5 mono down | 3 同スーツ → Conf -1 段 | cash のみ |
| O8 A-x range | A-high 散らばり/ペア + BTN/CO → +ax_range_bet pt | MTT BTN/CO |
| O9 turn shift | ターン = α -35、β ゼロ | turn context |

- **O4 と O5 は前段**（Confidence を変換してから base_freq を引く）
- **O8 は後段**（freq 計算後に加算、他パラメータと独立）
- **O9 は context 選択時に自動適用**（turn context 選択 = α/β 自動変換）
- **O4 と O5 は同時適用不可**（型6 mono board は存在するが O4 が優先、O5 は同時適用しない）
