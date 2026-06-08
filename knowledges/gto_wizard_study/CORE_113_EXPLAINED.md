# CORE 113 ルール — 意味解説と典型例

5-key 圧縮の CORE 113 ルールを「なぜそのアクションになるか」を含めて整理。
読者が「これは GTO で当然」と納得できる構造で、暗記アンカーを構築。

## アクション別の分布

| action | rules | rows | typical |
|--------|---:|---:|---------|
| **fold** | 72 (64%) | ~31K | 大半が trash_hands + 大きな bet を受けたとき |
| **call** | 37 (33%) | ~22K | weak/good_hands で defense 維持 |
| **raise** | 4 (3%) | ~9K | best_hands + 浅い SPR の jam value |

→ **「fold が圧倒的多数 (64%)」** = 弱手は降りるだけ。MATCHA の主目的は「いつ fold するか」の精度向上。

## トップ 10 (頻出順、累積カバー率)

| # | ルール | 累積 rows | 解釈 |
|---|--------|---------:|------|
| 1 | SRP river × エア × trash × 100% bet → **fold** (98%) | 5,317 | 「SRP river で エアな手に 100% pot bet 受けたら諦める」 |
| 2 | 4BP turn × エア × trash × 185% bet → **fold** (91%) | 9,593 | 「4BP turn で エアに overbet 受けたら降りる」 |
| 3 | SRP turn × エア × trash × 75% bet → **fold** (92%) | 13,310 | 「SRP turn で エア + trash eq + 75% bet 受けたら降りる」 |
| 4 | 3BP turn × エア × trash × 185% bet → **fold** (96%) | 16,914 | 「3BP turn で エアに overbet 受けたら降りる」 |
| 5 | SRP river × monotone × trash × 100% bet → **fold** (87%) | 20,061 | 「monotone river で trash eq + pot bet → flush 完成された、降りる」 |
| 6 | 4BP flop × connected_mid × weak × overbet → **call** (89%) | 22,831 | 「4BP flop の 9-7 board で weak eq + overbet → call (jam-or-fold ゾーン)」 |
| 7 | 4BP flop × TP+ × good × overbet → **raise** (89%) | 25,175 | 「4BP flop で TP+ + good eq + overbet 受けた → re-raise jam」 |
| 8 | DEF turn × エア × trash × 75% bet → **fold** (90%) | 27,511 | 「CR/donk-defense の turn で エア + trash → 降りる」 |
| 9 | SRP river × connected_mid × trash × 100% bet → **fold** (91%) | 29,788 | 「9-7 board の river で trash eq + 100% bet → 降りる」 |
| 10 | SRP flop × connected_mid × trash × allin → **fold** (93%) | 32,001 | 「9-7 board で flop allin 受けて trash eq → 降りる」 |

→ **トップ 10 ルールだけで rows 32K (21%) をカバー**

## アクション別 代表例

### 🔴 fold ルール (72 個、主に 弱手 vs 大きな bet)

**「エア tier + trash_hands + 大きな bet サイズ」の組合せが最多**:

| # | 条件 | action | 直感 |
|---|------|--------|------|
| 18 | SRP flop × エア × trash × allin | fold 100% | allin に エアで cold call はあり得ない |
| 19 | 3BP flop × エア × trash × overbet | fold 94% | 3BP flop の overbet に エア → 即降り |
| 32 | SRP river × エア × trash × overbet | fold 100% | river overbet + 弱手 → 100% fold |
| 38 | 3BP flop × connected_mid × trash × overbet | fold 100% | connected board の trash は完全降り |
| 60 | 3BP turn × monotone × trash × overbet | fold 100% | monotone turn で flush 完成された |

**「ミドルペア + trash_eq」の fold**:
| # | 条件 | action | 直感 |
|---|------|--------|------|
| 12 | SRP river × ミドルペア × trash × 100% bet | fold 87% | river で MP が trash eq = blocker 効果ゼロ、降りる |
| 36 | SRP flop × ミドルペア × trash × allin | fold 91% | flop allin に MP 弱 → 降りる |
| 40 | SRP river × ミドルペア × trash × overbet | fold 96% | overbet vs MP trash → 降りる |
| 98 | DEF turn × ミドルペア × trash × 75% bet | fold 93% | defense line でも MP trash は降りる |

**「強い手だが trash equity」の fold (board pair 化や flush 完成等の reaction)**:
| # | 条件 | action | 直感 |
|---|------|--------|------|
| 79 | SRP flop × TP+ × trash × allin | fold 95% | flop allin に TP で trash eq (board crushed) → 降りる |
| 104 | SRP flop × ツーペア × trash × allin | fold 96% | 2pair でも trash eq なら降りる (set or better vs you) |
| 113 | SRP flop × ナッツメイド × trash × allin | fold 86% | ナッツでも trash eq なら降りる (極稀だが possible) |

### 🟡 call ルール (37 個、defense 維持)

**「weak/good_hands で bet 受けて call」が王道**:

| # | 条件 | action | 直感 |
|---|------|--------|------|
| 6 | 4BP flop × connected_mid × weak × overbet | call 89% | 4BP の wet board で TP-ish → call |
| 11 | 4BP flop × mid_dry × weak × overbet | call 88% | 4BP の dry board で weak → call jam-or-fold |
| 14 | 4BP turn × connected_mid × weak × 185% bet | call 86% | 4BP turn で weak eq でも MDF call |
| 22 | 4BP flop × ミドルペア × weak × overbet | call 98% | 4BP の MP は call で commit (jam-or-fold) |
| 29 | 3BP flop × エア × weak × 75% bet | call 93% | 3BP で エア tier (弱だが eq そこそこ) → call MDF |
| 75 | 4BP flop × paired_high × best × overbet | call 89% | best eq でも 4BP の paired board は call (slowplay/trap) |

**「good_hands + 中サイズ bet」の call**:
| # | 条件 | action | 直感 |
|---|------|--------|------|
| 35 | SRP turn × connected_mid × good × 75% bet | call 93% | good eq で 75% bet → call (value catch) |
| 44 | SRP turn × TP+ × good × 75% bet | call 96% | TP+ + good eq に 75% bet → call |
| 46 | DEF flop × broadway_dry × good × 75% bet | call 89% | broadway board で good eq → defense call |
| 65 | 3BP flop × monotone × good × 75% bet | call 87% | flush draw 等の semi-bluff catch |

### 🟢 raise ルール (4 個、ナッツ系の jam value)

| # | 条件 | action | 直感 |
|---|------|--------|------|
| 7 | 4BP flop × TP+ × good × overbet | raise 89% | 4BP の TP+ で overbet 受けた → re-raise jam (jam value zone) |
| 76 | 4BP turn × mid_dry × good × 185% bet | raise 98% | 4BP turn の overbet を re-raise (確信 value) |
| 81 | 4BP turn × paired_high × good × 185% bet | raise 99% | paired board で trips/FH を持って re-raise |
| 97 | SRP river × ナッツメイド × best × 100% bet | raise 99% | river ナッツに 100% bet → re-raise (full value) |

## pot type 別の特徴

| pot | rules | 特徴 |
|-----|---:|------|
| SRP | ~45 | river で fold rules 多数 (主 受け弱手) |
| 3BP | ~25 | turn の defense calls + overbet 受け fold |
| 4BP | ~22 | jam-or-fold ゾーン (TP+ raise + weak call の二択) |
| DEF | ~21 | CR/donk-defense の standard MDF (~30% fold, 多 call) |

## 暗記アンカー (10 個の「マクロ理解」)

CORE 113 を暗記する前に、これらの **マクロ法則** をまず体に染み込ませる:

1. **「エア tier + trash eq に大きな bet は降りる」** → ルール 1, 3, 4, 8, 18, 19, 32 (約 25 ルール)
2. **「ミドルペア + trash eq は降りる」** → 12, 36, 40, 98
3. **「強い手 (TP+/2pair/ナッツ) でも trash eq なら降りる」** → 79, 104, 113 (board crushed 認識)
4. **「monotone river + trash → flush 完成、降りる」** → 5, 31, 60
5. **「4BP の overbet 受けたら、weak は call、good は raise」** → 6, 7 (jam-or-fold ゾーン)
6. **「best_hands + 浅い SPR = jam value re-raise」** → 7, 76, 81, 97
7. **「good_hands に 75% bet → call (value catch)」** → 35, 44, 46, 65
8. **「3BP の エア tier だが weak eq → call で MDF」** → 29, 85, 106
9. **「paired board の best/good eq は call で slowplay」** → 75, 105, 99
10. **「connected board の good eq → call で semi-bluff/draw catch」** → 35, 52, 65

→ **10 マクロ法則** で CORE 113 のほぼ全パターンを「意味付け」できる。
   読者は法則を覚えれば、個別ルールも生成可能。

## drill / 書籍への反映

### Phase 1: マクロ 10 法則 (drill 第 1 deck = 10 cards、書籍 1 章)
- 暗記負荷最小、Chen Formula 規模
- これだけで rows ~30-40% を 80%+ accuracy 想定

### Phase 2: CORE 113 (drill 第 2 deck = 113 cards、書籍判定表)
- フル CORE で rows 42% を 92% accuracy
- マクロ法則の "具体化" として learning curve 緩やか

### Phase 3: FALLBACK 535 (書籍付録 + drill 裏面)
- 例外参照用、暗記不要
