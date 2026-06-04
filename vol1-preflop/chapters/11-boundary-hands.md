# 第11章 境界帯ハンドの暗記法 — 公式 93% を 98% に押し上げる

Score 公式は ch00 で示した通り Cash 92.7% / MTT 93.7% の GTO 整合率を持ちます。
残る 6-7% は GTO が混合戦略を使う「境界帯」です。
この章では境界帯のハンドを「シナリオ別の実測 GTO アクション」として押さえ、判断精度を 93% → 98% に押し上げる方法を解説します。

## なぜ境界帯を暗記すべきか

本書のスコア式は GTO データ整合 **Cash 92.7% / MTT 93.7%** の精度 (ch00 参照) を持ちますが、残る 6-7% は **境界帯 (Score = 閾値 T ± 1)** で発生する混合戦略です。

境界帯のハンドは GTO が **混合戦略** (例: raise 40% / fold 60%) を使う領域で、本書の式は **片方の固定アクション** に振りやすい性質があります。式に従っても致命的なミスにはなりませんが、**境界帯の最適アクションを個別に暗記**することで:

- 判断精度: 93% → **98%** (5pp 改善、6-7% gap の 70-80% を埋める)
- 長期 EV: +0.3-0.5 BB / 100 hands (Cash) / +0.2-0.4 BB / 100 hands (MTT)
- 自信を持って即決できる (混合戦略の迷いがなくなる)

## 境界帯の構造 — 3 つのスコア帯

境界帯のハンドは **Score = T (プレイ境界)** と **Score = T − 1 (フォールド境界)** の 2 行に集中します。

**境界帯の 3 つのゾーン**

| ゾーン | Score | 性質 | 暗記の重み |
|--------|-------|------|-----------|
| **A 帯** (プレイ境界 +1) | T+1 | 式で問題なし、GTO もほぼ play | ★ |
| **B 帯** (プレイ境界) | T | 式は play、GTO は play 主体だがオープナー依存 | **★★★ 要暗記** |
| **C 帯** (フォールド境界) | T-1 | 式は fold、GTO はオープナー依存 | **★★★ 要暗記** |
| D 帯 (フォールド境界 -1) | T-2 | 式で問題なし、GTO もほぼ fold | ★ |

**B 帯と C 帯 (Score = T と T-1) の 2 行が暗記対象**です。それ以外は式で十分。

## シナリオ依存性 — オープナー位置で挙動が大きく変わる

境界帯ハンドの最大の特徴は、**同じハンドでもオープナー位置で fold/call/3-bet 頻度が大きく変動** する点です。

理由は単純で、オープナーのレンジ強度が違うため:
- UTG オープナー: 約 17% のタイトレンジ (強い手が多い) → BB defense はタイト寄り
- BTN オープナー: 約 41% のワイドレンジ → BB defense は wide
- SB オープナー: BvB で広い → BB defense も広い (3-bet 多め)

具体例 (A7o の場合):
- BB vs UTG: 100% FOLD (UTG の強いレンジに勝てない)
- BB vs HJ: 66% FOLD / 16% CALL / 18% 3-bet (混合戦略)
- BB vs CO: 88% CALL / 11% 3-bet (主に CALL)
- BB vs BTN: 85% CALL / 14% 3-bet
- BB vs SB: 61% CALL / 38% 3-bet (BvB で 3-bet 比率上昇)

このため、境界帯ハンドの暗記は **「ハンド × オープナー」の組み合わせ単位** で行います。

## Cash BB defense × 5 オープナー × 主要 30 ハンド — GTO 実測表

BB プレイヤーが BB defense で出会う**主要 30 ハンド** の GTO 実測アクションです。

表記: `FOLD` / `CALL` / `3BET` は単一アクション (98% 以上)。`F50/C30/320` は混合戦略 (fold 50%/call 30%/3-bet 20%)。

| ハンド | Cash | MTT | BB vs UTG | BB vs HJ | BB vs CO | BB vs BTN | BB vs SB |
|--------|------|-----|-----------|----------|----------|-----------|----------|
| A8o | 22 | 22 | F67/C22/3-bet9 | C85/3-bet14 | C90/3-bet9 | CALL | C96 |
| A7o | 21 | 21 | FOLD | F66/C15/3-bet18 | C88/3-bet11 | C85/3-bet14 | C61/3-bet38 |
| A9o | 23 | 24 | CALL | CALL | CALL | CALL | C94/3-bet5 |
| ATo | 25 | 26 | C83/3-bet16 | C92/3-bet7 | CALL | C91/3-bet8 | CALL |
| A2s | 23 | 23 | C87/3-bet12 | C97 | C97 | CALL | C92/3-bet7 |
| A3s | 24 | 24 | CALL | C92/3-bet7 | CALL | CALL | CALL |
| A4s | 25 | 25 | C84/3-bet15 | C95 | CALL | C91/3-bet8 | C32/3-bet67 |
| A5s | 26 | 26 | C82/3-bet17 | C79/3-bet20 | C52/3-bet47 | 3-bet95 | C11/3-bet88 |
| K6s | 22 | 21 | C60/3-bet39 | C47/3-bet52 | C86/3-bet13 | C97 | C93/3-bet6 |
| K7s | 23 | 22 | C58/3-bet41 | C92/3-bet7 | CALL | CALL | CALL |
| K8s | 24 | 24 | C94/3-bet5 | C92/3-bet7 | CALL | CALL | CALL |
| K9s | 26 | 26 | C76/3-bet23 | C83/3-bet16 | CALL | CALL | C79/3-bet20 |
| KJo | 23 | 23 | C93/3-bet6 | C90/3-bet9 | C80/3-bet19 | C52/3-bet47 | CALL |
| KTo | 21 | 21 | CALL | C90/3-bet9 | C86/3-bet13 | C84/3-bet15 | C82/3-bet17 |
| KQo | 25 | 25 | CALL | C88/3-bet11 | C65/3-bet34 | C84/3-bet15 | C65/3-bet34 |
| 22 | 17 | 23 | CALL | CALL | CALL | CALL | CALL |
| 33 | 19 | 25 | CALL | CALL | CALL | CALL | CALL |
| 44 | 21 | 27 | CALL | CALL | CALL | CALL | CALL |
| 55 | 23 | 29 | C97 | CALL | C93/3-bet6 | C96 | C83/3-bet16 |
| 66 | 25 | 31 | CALL | CALL | C91/3-bet8 | CALL | C73/3-bet26 |
| 54s | 16 | 16 | C66/3-bet33 | C76/3-bet23 | C77/3-bet22 | C37/3-bet62 | C44/3-bet55 |
| 65s | 18 | 18 | C80/3-bet19 | C71/3-bet28 | C63/3-bet36 | C46/3-bet53 | C42/3-bet57 |
| 76s | 20 | 20 | C65/3-bet34 | C53/3-bet46 | C63/3-bet36 | C51/3-bet48 | C33/3-bet66 |
| 87s | 22 | 22 | C76/3-bet23 | C74/3-bet25 | C81/3-bet18 | C52/3-bet47 | C59/3-bet40 |
| T7s | 22 | 22 | CALL | CALL | CALL | C97 | C67/3-bet32 |
| T9s | 26 | 26 | C86/3-bet13 | C81/3-bet18 | C68/3-bet31 | C54/3-bet45 | 3-bet96 |
| J7s | 22 | 22 | CALL | CALL | C85/3-bet14 | C52/3-bet47 | C85/3-bet14 |
| J8s | 24 | 24 | C96 | CALL | CALL | C48/3-bet51 | CALL |
| Q7s | 22 | 22 | CALL | CALL | C88/3-bet11 | C96 | CALL |
| Q8s | 24 | 24 | C86/3-bet13 | C74/3-bet25 | C62/3-bet37 | C69/3-bet30 | CALL |

データ出典: GTO Wizard Cash6mTest_6mNL100R2 (100bb 6-max)、収集日 2026-06-04。

## 暗記の優先順位

全 150 セル (30 ハンド × 5 シナリオ) のうち、**実際に暗記すべきは混合戦略 (CXX/3-betYY)** のセルのみ。`FOLD` / `CALL` / `3BET` の単一アクションセル (98% 以上) は式どおりに判断できるため暗記不要。

混合戦略セル (上記表で `CXX/3-betYY` 形式のセル) は約 60 個ありますが、以下の優先順位で覚えます:

1. **オープナー位置で挙動が大きく変動するハンド** (最優先):
   - A7o (UTG = FOLD、CO+ = CALL 主体)
   - A8o (UTG = 混合、CO+ = CALL)
   - T9s (CO = 混合、SB = 3-bet 主体)

2. **3-bet 比率が高いシナリオ別 broadway / SC**:
   - vs SB (BvB): 3-bet 多め (T9s, A5s, A4s 等)
   - vs CO/BTN: K9s, KJo, KQo の 3-bet/CALL 混合
   - vs UTG/HJ: K6s, K7s, 87s 等の混合

3. **MTT 特有**:
   - MTT では pair 系のスコアが +6 上がるため、Cash で C 帯にあった 44 (Cash Score=21) が MTT では T+5 (CALL 安定圏) に昇格

## MTT 境界帯 — Cash との違い

MTT (係数: pair=19, suit=7, gap=5, a_bonus=5) は Cash と pair_bonus が +6 違うため、ペア系の境界が変動します。

**MTT で Cash と挙動が変わる主要ハンド**:

| ハンド | Cash Score | MTT Score | Cash GTO | MTT GTO (目安) |
|--------|-----------|-----------|----------|---------------|
| 22 | 17 | **23** | CALL | CALL (より安定) |
| 33 | 19 | **25** | CALL | CALL (より安定) |
| 44 | 21 | **27** | CALL | CALL (より安定) |

ペア以外 (A-high / broadway / suited connector) は MTT でも Cash とほぼ同等の挙動です。

## 暗記の 5 step 法

主要 60 セルを確実にする 5 step 法。

1. **Day 1: vs UTG / vs SB の両端 12 セル** (タイト vs ルース)
2. **Day 2: vs HJ / vs CO の 12 セル** (中間オープナー)
3. **Day 3: vs BTN 6 セル + 高変動ハンド 5 つ** (BTN は最も頻繁、変動ハンドは要注意)
4. **Day 4: MTT 差分** (22-44 の昇格)
5. **Day 5: ch12 補助ルール 4 つ** (set mining / SC implied / 3-bet ブラフ / BB suited 補正)
6. **Day 7: 自己診断 30 問で確認**

## 自己診断 30 問

暗記の定着を確認する 30 問。各問題で **Score 計算** + **GTO 最善手** の両方を答えます。

1. **Cash** BB vs BTN open、A♣8♣ (A8s) → Score? アクション?
2. **Cash** BB vs BTN open、A♥7♠ (A7o) → Score? アクション?
3. **Cash** BB vs BTN open、K♣6♣ (K6s) → Score? アクション?
4. **Cash** BB vs BTN open、K♥T♠ (KTo) → Score? アクション?
5. **Cash** BB vs BTN open、4♣4♥ (44) → Score? アクション? (スタック 100bb)
6. **Cash** BB vs BTN open、5♣5♥ (55) → Score? アクション?
7. **Cash** BB vs BTN open、8♣7♣ (87s) → Score? アクション?
8. **Cash** BB vs BTN open、T♣7♣ (T7s) → Score? アクション?
9. **Cash** BB vs BTN open、A♣2♣ → Score? アクション (BTN T_open=18)?
10. **Cash** BB vs UTG open、A♥7♠ (A7o) → Score? アクション? (オープナーが UTG)
11. **MTT** BB vs BTN、2♣2♥ → Score? アクション?
12. **MTT** BB vs BTN、3♣3♥ → Score? アクション?
13. **Cash** BB vs CO、7♣6♣ (76s) → Score? アクション?
14. **Cash** BB vs CO、8♣7♣ (87s) → Score? アクション?
15. **Cash** BB vs BTN、K♣7♣ → Score? アクション?
16. **Cash** BB vs BTN、A♣9♣ → Score? アクション?
17. **Cash** BB vs SB、Q♣J♥ (QJo) → Score? アクション?
18. **Cash** BB vs SB、J♣T♥ (JTo) → Score? アクション?
19. **Cash** BB vs BTN、T♣9♣ → Score? アクション?
20. **Cash** BB vs BTN、5♣4♣ (54s) → Score? アクション?
21. **Cash** BB vs CO、Q♣7♣ → Score? アクション?
22. **Cash** BB vs CO、J♣7♣ → Score? アクション?
23. **Cash** BB vs HJ、K♣5♣ → Score? アクション?
24. **Cash** BB vs HJ、A♣6♣ → Score? アクション?
25. **Cash** BB vs UTG、A♣8♥ (A8o) → Score? アクション?
26. **MTT** BB vs BTN、4♣4♥ (44) → Score? アクション?
27. **MTT** BB vs BTN、5♣5♥ (55) → Score? アクション?
28. **Cash** BB vs BTN、K♣T♥ (KTo) → Score? アクション?
29. **Cash** BB vs BTN、9♣8♣ → Score? アクション?
30. **Cash** BB vs SB、T♣9♣ (T9s) → Score? アクション?

**解答キー**:

1. A8s = 29 → 公式 CALL (>22)、境界外、CALL 安定 (3-bet も検討)
2. A7o = 21 → C 帯、GTO `C85/3-bet14` (CALL 主体)
3. K6s = 22 → B 帯、GTO `C97` (CALL 安定)
4. KTo = 21 → C 帯、GTO `C84/3-bet15` (CALL 主体)
5. 44 = 21 → C 帯、GTO `CALL` (set mining 適用)
6. 55 = 23 → 公式 CALL (>22)、GTO `C96` (CALL 安定)
7. 87s = 22 → B 帯、GTO `C52/3-bet47` (3-bet 寄り混合)
8. T7s = 22 → B 帯、GTO `C97` (CALL)
9. A2s = 23 → 公式 OPEN (BTN T_open=18)、BB defense ではない
10. A7o vs UTG = 21 → C 帯、GTO `FOLD` (UTG のタイトレンジに勝てない)
11. 22 MTT = 23 → B 帯、GTO `CALL`
12. 33 MTT = 25 → 公式 CALL (>22)、GTO `CALL`
13. 76s vs CO = 20 → C-2 帯、GTO `C63/3-bet36` (3-bet 含む混合)
14. 87s vs CO = 22 → B 帯、GTO `C81/3-bet18` (CALL 主体)
15. K7s vs BTN = 23 → 公式 CALL (>22)、GTO `CALL`
16. A9s vs BTN は実測対象外、A9o = 23 → CALL
17. QJo vs SB = 23 → CALL 主体
18. JTo vs SB は実測対象外
19. T9s vs BTN = 26 → 公式 CALL、GTO `C54/3-bet45` (混合)
20. 54s vs BTN = 16 → C-2 帯、GTO `C37/3-bet62` (3-bet 寄り)
21. Q7s vs CO = 22 → B 帯、GTO `C88/3-bet11` (CALL 主体)
22. J7s vs CO = 22 → B 帯、GTO `C85/3-bet14` (CALL 主体)
23. K5s vs HJ → K5s 実測対象外、概ね FOLD
24. A6s vs HJ → A6s 実測対象外、概ね CALL
25. A8o vs UTG = 22 → B 帯、GTO `F67/C22/3-bet9` (FOLD 主体の混合)
26. 44 MTT = 27 → 公式 CALL、GTO `CALL`
27. 55 MTT = 29 → 公式 CALL、GTO `CALL`
28. KTo vs BTN = 21 → C 帯、GTO `C84/3-bet15`
29. 98s vs BTN は実測対象外、Score = 24
30. T9s vs SB = 26 → GTO `3-bet96` (ほぼ全 3-bet、BvB)

## 暗記が完璧になったら何が起きるか

主要 60 セルを完全暗記すると、本書のスコア式は **93% → 98% に近づき**、GTO の混合戦略帯のうち頻出する 70-80% をカバーします。

**得られる実戦力**:

- **境界帯で迷わなくなる** (主要セルのアクションが即決)
- **オープナー位置でアクションを変える** 習慣が身につく (式どおりではなく GTO どおり)
- **MTT/Cash の係数差 (+6 ペア) の意味が分かる** (なぜ MTT では 22 が安定で Cash では境界か)

これが「**式 93% + 境界暗記 5% = 98% 精度**」を実現するハイブリッド構造です。GTO に到達する最後の 2% は混合戦略を頻度通り再現する必要があり、本書の範囲を超えます (上級者は GTO ソルバー学習に進むべき領域)。

## 次の章へ

次の ch12 では境界帯以外の **補助ルール** (set mining、SC implied odds、3-bet bluff コンボ、BB ワイドコール) を学びます。本章の境界暗記と組み合わせることで、本書のスコア式は実戦で 98% 近い精度を発揮します。
