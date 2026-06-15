# 第 28 章　バブル戦略 — リスクプレミアムの極大化 ★定性

> **本章は定性記述のみです**。ICM/PKO 数値モデル化は将来 Vol2.5 で対応予定です。

## 21.1 バブルの定義

**バブル** = MTT で「賞金圏直前」の状況です。例えば、全 100 人で in-the-money 15 人なら、残り 16 人になった瞬間からバブルが始まります。1 人飛ぶと 15 人全員が賞金を獲得できるようになるため、ICM Pressure が最大になります。

## 21.2 ICM Pressure の最大化

バブルでは ICM Pressure（リスクプレミアム）が**最大**になります：

- **short stack**: jam しないと先送りされて blinds で消耗し、一方 jam で bust すると致命傷になります
- **chip leader**: bust リスクがないので wide な pressure をかけられます
- **mid stack**: 両側に挟まれて、行動できなくなる（lock-up 現象）になりやすいです

## 21.3 short stack jam range の絞り

chipEV（本書のデフォルト）の jam range より**tight**な jam range が GTO で推奨されます：

| ICM ステージ | short stack (15bb) jam range |
|---|---|
| chipEV (no ICM) | ~30% (LP open + reraise) |
| ICM mild (FT 9) | ~25% |
| ICM heavy (FT 5) | ~20% |
| **バブル** | **~15%** (Premium + 高エクイティのみ) |

→ MATCHA Score の T_call / T_raise を「Score +5〜+10」相当に引き上げることをおすすめします。

## 21.4 chip leader の wide steal

chip leader は逆に bully することができます：

- 全 position で wide open（BTN 60%、CO 45% など）
- short / mid stack の defense は tight になるため、fold equity が高いです
- 4BP / 5BP の jam を受け止める stack も持っています

→ chip leader の視点では MATCHA Score の T_open / T_3bet を緩めることがおすすめです。

## 21.5 mid stack の受難

mid stack（上から 3-5 番手）は最も厳しい状況です：

- chip leader からの pressure を受ける（fold せざるを得ないことが多いです）
- short stack の jam を受け止めにくい（bust すると mid 失格になります）
- 結果：**tight 一方通行**で、行動がほぼできなくなります

mid stack の survival 戦略としては：

- premium hand のみ play（AA / KK / QQ / AK）
- speculative hand（SC / mid pair）は fold します
- bubble 通過後に通常 strategy に復帰します

## 21.6 short stack スタイルの jam threshold（定性）

short stack（≤12bb）の jam range は ICM stage 別に変化します：

| stack | chipEV jam range | バブル jam range |
|---|---|---|
| 10bb | 30% (LP) | 18% |
| 8bb | 40% | 25% |
| 5bb | 60% | 45% |
| 3bb | 90% | 80% (any 2 fold 困難) |

short stack 程 ICM 影響は小さい傾向です（もう committed の領域だからです）。大きい short stack ほど tight 化が進みます。

## 21.7 MATCHA Score 適用上の注意

バブルで MATCHA Score を使う際に気をつけることがあります：

1. **T_call を +5〜+10 引き上げます**（14 → 19〜24）
2. **T_raise も同等に引き上げます**（43 → 48〜53）
3. **4BP / vs CR は特に慎重にしましょう**（bust リスクが大きい pot だからです）
4. **2P+ 以外の wet × river overbet 受け → 強制 fold とします**（例外 2 を逆方向に override します）

例を挙げると：
- ミドル × dry × flop × SRP × small_33: chipEV Score = 18 → call（≥14）
- バブル補正後: T_call = 20 → 18 < 20 → fold になります

## 21.8 バブル通過後の再調整

バブル通過（= 賞金圏 in 後）では：

- ICM Pressure が一段下がります（バブル → FT 過渡期）
- short stack は再び jam 化します（chipEV 寄りに復帰します）
- mid stack は息を吹き返します

→ MATCHA Score の補正を**+5 → +2**程度に戻すことがおすすめです。

## Cash/MTT note

バブルは MTT 専用です。Cash には存在しません。本章の補正は MTT 賞金圏直前のみ適用します。ante 込みの MTT late stage と組合せて運用することをおすすめします（第 21 章併用）。

## この章で覚える項目 (4 items、すべて定性)

1. バブル = ICM Pressure 最大、リスクプレミアム 15-25%
2. short stack jam range 大幅 tight 化 (~15%)
3. mid stack は受難、premium only
4. MATCHA Score T_call/raise +5〜+10 補正
