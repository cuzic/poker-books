# UCBS-v2 例外ルール整理

作成日: 2026-05-28
ソース: UCBS_V2_DCBS_FINAL.md / vol2-cash-postflop/ucbs_v2.py (apply_confidence_exception / is_ax_dry_or_paired)
用途: Vol3 ch13「例外ルール 4 つ」の執筆 source

---

## 例外ルール一覧

| # | 通称 | 適用フェーズ | 適用 context | 効果 |
|---|---|---|---|---|
| O4 | 型6 信頼度 up | Confidence 計算後（前段） | 全 context | conf を 1 段上げる |
| O5 | mono board 信頼度 down | Confidence 計算後（前段） | cash のみ | conf を 1 段下げる |
| O8 | A-x range bet | freq 計算後（後段加算） | MTT BTN/CO のみ | +ax_range_bet pt 加算 |
| O9 | turn shift | context 選択時 | turn context | α -35、β 廃止 |

---

## 例外① 型6 信頼度 up（O4）

### 出現条件

- ボード分類が**型6**（ペア rank ≥ Q のペア板）
- 例: KK7、QQ4、AA9 など
- 適用 context: **全 13 context 共通**

### 実装

```python
# vol2-cash-postflop/ucbs_v2.py: apply_confidence_exception()
if board_type == 6:
    if conf == "LOW":
        conf = "MID"
    elif conf == "MID":
        conf = "HIGH"
# HIGH はそのまま変化なし
```

### GTO データ根拠

型6 ボード（高ランクペア）ではレンジ全体が関連しやすくなります。具体的には、開幕者はオーバーペアや KK などの強い役を多く持ち、BBも A-x など Aハイ帯を hold していることが多いです。そのため「自分のレンジの信頼度」が上がり、閾値からの距離が小さくても HIGH/MID で扱える根拠が強まります。

GTO Wizard の実測データでは、型6 ボードでの cbet freq が他の型と比べて平均 +8〜12pt 高く、信頼度を 1 段 up することでこの傾向を再現できます。この補正を外した場合の WRMSE は 2〜3pt 悪化します。

### WRMSE 改善

適用あり vs なし（cash_100bb 実測）:
- 型6 ボード: WRMSE 14.3% → 12.1%（-2.2pt）
- 全体 WRMSE への貢献: 約 -0.5pt（型6 が全ボードの ~15%）

### 書籍向けの覚え方

> **「高ランクペア板は自信 UP」**
> KK・QQ が出たら Confidence を 1 段強気に読む。
> LOW → MID、MID → HIGH に変換してから freq を引く。

---

## 例外② mono board 信頼度 down（O5、cash のみ）

### 出現条件

- ボードが**mono（3 枚同スーツ）**
- 例: Kh7h2h、Td8d5d など
- 適用 context: **cash_100bb のみ**（MTT は適用なし、`mono_conf_down=False`）

### 実装

```python
# vol2-cash-postflop/ucbs_v2.py: apply_confidence_exception()
if mono_down and suit_pattern == "mono":
    if conf == "HIGH":
        conf = "MID"
    elif conf == "MID":
        conf = "LOW"
# LOW はそのまま変化なし
```

### GTO データ根拠

cash ゲームでは mono board は「フラッシュドロー完成型」として IP のレンジが polarize します。開幕者レンジが（ナッツ系とブラフ系に）二極化するため、中間的なハンドの bet 根拠が弱まります。実測では mono board の cbet freq が通常板より -5〜-10pt 低く、Confidence を 1 段下げることで再現できます。

MTT では bet サイズ（33%固定）が小さく、polarize の影響が cash ほど大きくないため適用しません。

### WRMSE 改善

cash_100bb での mono board（全ボードの ~5%）:
- 適用あり: WRMSE 11.2%（mono 板のみ）
- 適用なし: WRMSE 14.8%（同）
- 改善: -3.6pt

### 書籍向けの覚え方

> **「3 枚同色（cash）は自信 DOWN」**
> Kh7h2h など全部同じマークなら Confidence を 1 段慎重に。
> HIGH → MID、MID → LOW に変換してから freq を引く。
> **MTT ではこのルール不要**（bet が小さいため影響が薄い）。

---

## 例外③ A-x range bet（O8）

### 出現条件

以下の**全て**を満たす場合に適用します。

1. **context が MTT**（cash_100bb は ax_range_bet=0.0）
2. **ポジションが BTN または CO**
3. ボードが **A-high** かつ（**paired** または **gap ≥ 8**）

```python
# vol2-cash-postflop/ucbs_v2.py: is_ax_dry_or_paired()
def is_ax_dry_or_paired(features):
    if features["high"] != "A":
        return False
    return features["paired"] or features["gap"] >= 8
```

**gap = top カード rank - low カード rank**（例: Ac5d2h の gap = 12）

### 適用効果（context 別）

| Context | ax_range_bet | 意味 |
|---|---:|---|
| mtt_25bb | **+30pt** | 終盤でも range bet ほぼ 100% |
| mtt_50bb | +11pt | 中盤は控えめ |
| mtt_100bb | +28pt | 序盤も range bet 活発 |
| mtt_200bb | +9pt | deep では穏やかな加算 |

### GTO データ根拠

MTT での BTN/CO は「A-high dry/paired board では range 全体で小 bet する」戦略が GTO 最善に近いことが判明しています。A はオープナーのレンジ強度が高く、BB との equity gap が大きいため、ほぼ全ハンドで小 bet が成立します。実測では BTN の Ac5d2h の全 hand カテゴリが 80%+ bet を選択し、UCBS-v2 の通常予測を 30pt 超えることが確認されています。

### 計算例

- Context: mtt_25bb, 手: third_pair, Board: Ah7d2c（A-high, gap=11, not paired → ax range bet）
- pos_lift (BTN) = 0.00、ax_range_bet = +0.30
- CBS = HP[third_pair] + DP[no_draw] = 3 + 0 = 3
- direction = false（3 < T=5）
- conf = MID（distance=2）
- base = base_freq[(MID, false, 33)] = 0.333
- alpha = +0.06（mtt_25bb）
- beta_term = 0（CBS < 7）
- offset = 0（default category）
- freq = 0.333 + 0.06 + 0 + 0 + 0 + 0.30 = **0.693 → 69%**

（通常は 39% → +30pt の効果）

### 書籍向けの覚え方

> **「MTT の BTN/CO でエース高 + 散らばり板 → 全部ベット」**
> A + (ペア板 or 3 カード間隔 8 以上) が条件。
> 25bb 終盤: +30pt（ほぼ全ハンドで cbet）
> 50bb 中盤: +11pt（穏やかな range bet）
> 100bb 序盤: +28pt（序盤でも range bet 活発）

---

## 例外④ turn shift（O9）

### 出現条件

- フロップ cbet 後、ターンに進んで**2nd barrel を検討する場合**
- `turn context` を選択した時点で自動適用される
- 例: mtt_25bb → **mtt_25bb_turn_btn** に切り替え

### 変換ルール

| パラメータ | Flop (mtt_25bb 例) | Turn (mtt_25bb_turn_btn) |
|---|---:|---:|
| **α** | +0.06 | **-0.41** |
| **β (CBS≥7)** | +0.31 | **+0.01** |
| off_slowplay | -0.28 | -0.28（変化なし） |
| off_trash | -0.23 | **-0.01** |
| off_premium | +0.15 | +0.08 |

**書籍ルール**: ターンに進んだら α を -35pt シフト、β は廃止（≈ 0）。

### GTO データ根拠

ターンでは全体的に bet 頻度が約 35% 低下します（GTO 実測: フロップ平均 55% → ターン平均 35〜45%）。強い役（CBS≥7）への追加 lift（β）が消えるのは、ターンでは役の強さよりも「ボード変化との相性」が支配的になるためです。また off_trash が -0.23 → -0.01 に緩和されるのは、ターンでは low_pair も一部 bet 有力になるためです。

### WRMSE 改善

Turn context の精度（α シフト + β 廃止の効果）:
- mtt_25bb_turn: WRMSE **7.02%**（全 context 中最高精度）
- 参考: フロップ mtt_25bb: 15.46%

ターンへの α シフトを適用しない場合（フロップ mtt_25bb をそのまま使用）の WRMSE は推定 35%+ に悪化します。

### 完成役 turn card の例外（UCBS-v2 の限界）

ターンカードがストレートまたはフラッシュを完成させる場合、UCBS-v2 は機能しません:

| Turn パターン | WRMSE | 理由 |
|---|---:|---|
| KJT + Q（ストレート完成） | 28% | Q で多くの hand がストレート完成 |
| T98r + 7（ストレート完成） | 19% | 7 でストレート完成 |
| 通常 turn card | 3-5% | UCBS-v2 完璧適合 |

この場合は「ストレート/フラッシュ完成 turn = 通常判定を放棄、手の絶対強度で判断」と覚えます（ch14 苦手領域で詳述）。

### 書籍向けの覚え方

> **「ターンに入ったら α を -35、β をゼロに」**
> フロップで α=+6 だった mtt_25bb → ターンで α=-41（差 -47pt）。
> 強い役でも追加 lift（β）はなくなる。
> 低ペア（low_pair）はターンで復活（off_trash が緩和）。
>
> **ただし**: ストレート/フラッシュ完成カードは UCBS-v2 非対応。

---

## 例外適用フロー（統合）

```
1. board_type を判定（型1-7）
2. CBS = HP + DP を計算
3. Confidence を calc_confidence() で算出
4. 【O4】 型6 なら conf を 1 段 up
5. 【O5】 mono かつ cash なら conf を 1 段 down
6. direction = (CBS >= T)
7. size = polarize ? 116 : 33
8. base = BASE_FREQ[(conf, dir, size)]
9. freq = base + α + β·I(CBS≥7) + offset[category]
10. freq += pos_lift[position]
11. 【O8】 BTN/CO かつ MTT かつ ax_dry_or_paired なら freq += ax_range_bet
12. freq = clamp(freq, 0.02, 0.98)

* turn context を選んだ時点で自動的に α≈-0.35 / β≈0 (【O9】)
```

---

## 4 例外の一言まとめ（暗記カード）

| 例外 | 一言 | 適用スコープ |
|---|---|---|
| O4 型6 up | 高ランクペア板 → Conf +1 段 | 全 context |
| O5 mono down | 3 同スーツ → Conf -1 段 | cash のみ |
| O8 A-x range | A-high 散らばり/ペア + BTN/CO → +30 | MTT BTN/CO |
| O9 turn shift | ターン = α -35、β ゼロ | turn context |
