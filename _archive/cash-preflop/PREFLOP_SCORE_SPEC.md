# プリフロップスコア — 仕様書

**作成日**: 2026-05-09
**ステータス**: 採用 (巻① 大改訂の中核)
**目的**: RFI / 対RFI / 3-bet / Call / 4-bet / 5-bet / Squeeze / BB defense
すべてのプリフロップ判断を **1 つのスコア式 + 1 つの閾値表** で扱う。
ただし BB defense のみ:
- **係数を別途強化** (suited+6 / conn+4 / conn23+2)
- **2 つの例外**: ペアは常に CALL / スーテッド差≤4 は常に CALL

---

## 1. スコア式

### 1.1 通常版 (RFI / 3-bet / 4-bet / 5-bet / Squeeze 用)

```
Score = H + L
      + ペアボーナス     +10  （ペアのみ）
      + スーテッドボーナス  +3
      + コネクター補正:
          差 1               +1
          差 2-3             +0.5
      + ブロッカー補正:
          A を含む           +3
          K を含む           +2
          A・K 両方          +4   （+3 と +2 を上書き）
      − ペナルティ:
          差 4 以上          −1   （A を含む場合は免除）
          両カード 9 未満    −1
```

### 1.2 BB defense 版

BB は 1bb 払い済 → ポットオッズが好い → スーテッド/コネクターを高評価:

```
Score_BB = H + L
         + ペアボーナス     +10
         + スーテッドボーナス  +6   （通常 +3 → +6）
         + コネクター補正:
             差 1              +4   （通常 +1 → +4）
             差 2-3            +2   （通常 +0.5 → +2）
         + ブロッカー補正:
             A=+3 / K=+2 / AK=+4 (通常版と同じ)
         − ペナルティ:
             差 4 以上              −1 (通常と同じ、A 免除)
             両カード 9 未満 (offsuit のみ)  −2 (通常 −1 → offsuit 限定 −2)
             (suited は両カード 9 未満ペナルティ免除)
```

**カード数値化**: A=14, K=13, Q=12, J=11, T=10, 9-2=そのまま

**主要ハンドのスコア例:**

| ハンド | H | L | bonus | blocker | penalty | Score |
|---|---|---|---|---|---|---|
| AA  | 14 | 14 | +10 (pair) | +3 (A) | 0 | **41** |
| KK  | 13 | 13 | +10 | +2 (K) | 0 | **38** |
| QQ  | 12 | 12 | +10 | 0 | 0 | **34** |
| JJ  | 11 | 11 | +10 | 0 | 0 | **32** |
| TT  | 10 | 10 | +10 | 0 | 0 | **30** |
| 99  | 9 | 9 | +10 | 0 | 0 | **28** |
| 22  | 2 | 2 | +10 | 0 | 0 | **14** |
| AKs | 14 | 13 | +3 (s) +1 (con) | +4 (AK) | 0 | **35** |
| AKo | 14 | 13 | +1 (con) | +4 (AK) | 0 | **32** |
| AQs | 14 | 12 | +3 +0.5 | +3 (A) | 0 | **32.5** |
| AQo | 14 | 12 | +0.5 | +3 | 0 | **29.5** |
| KQs | 13 | 12 | +3 +1 | +2 (K) | 0 | **31** |
| **KQo** | **13** | **12** | **+1 (con)** | **+2 (K)** | **0** | **28** |
| AJs | 14 | 11 | +3 +0.5 (gap=3) | +3 (A) | 0 | **31.5** |
| AJo | 14 | 11 | +0.5 (gap=3) | +3 | 0 | **28.5** |
| ATs | 14 | 10 | +3 (gap=4 連結ボーナスなし) | +3 | 0 | **30** |
| KJs | 13 | 11 | +3 +0.5 | +2 | 0 | **29.5** |
| QJs | 12 | 11 | +3 +1 | 0 | 0 | **27** |
| JTs | 11 | 10 | +3 +1 | 0 | 0 | **25** |
| T9s | 10 | 9 | +3 +1 | 0 | 0 | **23** |
| 76s | 7 | 6 | +3 +1 | 0 | −1 (low) | **16** |
| 65s | 6 | 5 | +3 +1 | 0 | −1 | **14** |
| 54s | 5 | 4 | +3 +1 | 0 | −1 | **12** |
| A5s | 14 | 5 | +3 | +3 (A) | 0 (A 免除) | **25** |

---

## 2. 閾値表（シーン別、v3 2026-05-19 GTO Wizard 3betV2 再検証）

### 2.1 RFI （オープン or フォールド）

| 自分のポジ | T_open |
|---|---|
| UTG | **24** |
| HJ  | **22** |
| CO  | **20** |
| BTN | **18** |
| SB  | **18** ※ |

判定: `Score ≥ T_open → Open Raise` / 未満 → Fold

※ SB は BB との 1 対 1。GTO ではリンプ（コール）も選択肢。T_open=18 は「レイズ or フォールド」モデルでの最適値。実戦では Score 14〜17 のハンドをリンプ検討。

### 2.2 対 RFI （3-bet / Call / Fold） — 通常スコア使用

二段閾値。`Score ≥ T_3bet → 3-bet` / `T_call ≤ Score < T_3bet → CALL` / `Score < T_call → FOLD`

T_call 省略は CALL レンジなし (3-bet or fold pure)。

| 自分↓ \ レイザー→ | UTG | HJ | CO | BTN |
|---|---|---|---|---|
| HJ  | 29 | — | — | — |
| CO  | 29 | 29 | — | — |
| BTN | **32 / 29** | **28 / 26** | 25 | — |
| SB  | 29 | 29 | 28 | 24 |

太字 = 二段閾値あり。BTN は CALL レンジが広い。

### 2.3 BB defense — Score_BB 使用 + 例外ルール

BB defense フロー（HU）:
```
Step 1: Score_BB ≥ T_3bet                      → 3-bet
Step 2: ペアハンド (22-AA)                      → CALL  ← 例外1
Step 3: スーテッドで差≤4 (32s, 43s, ..., AKs)  → CALL  ← 例外2 (HU)
Step 4: T_call ≤ Score_BB < T_3bet             → CALL
Step 5: Score_BB < T_call                      → FOLD
```

BB defense フロー（MW Level 1 — open + N cold calls）:
```
Step 1: Score_BB ≥ T_3bet + 3 × N_callers      → 3-bet (squeeze)
Step 2: ペアハンド (22-AA)                      → CALL  ← 例外1 変更なし
Step 3: スーテッドで差≤2                        → CALL  ← 例外2 MW (差3以上は通常判定)
Step 4: T_call ≤ Score_BB < T_squeeze          → CALL
Step 5: Score_BB < T_call                      → FOLD
```
*T_call (BB) は MW でも HU と同じ値を使う。例外2だけ diff≤4→diff≤2 に縮小。*
*詳細検証: セクション 4.5 参照。*

| レイザー | T_3bet | T_call |
|---|---|---|
| vs UTG | **33** | **25** |
| vs HJ  | **32** | **24** |
| vs CO  | **32** | **24** |
| vs BTN | **28** | **22** |
| vs SB  | **30** | **19** |

注: BB vs SB は BB がフロップ IP になる（SB が先行動）。T_3bet=30 は BvB では SB が広くオープン（T_open=18）するため BB も広く 3-bet。T_call=19 は IP 優位で広く call できる点を反映。GTO 精度 79.9%。GTO の二極化 bluff レンジ（Score_BB<28 の low-suited 系）は式では再現不可。

### 2.4 4-bet （vs 3-bet） — 通常スコア使用

シングル閾値。

| 自分のポジ | T_4bet |
|---|---|
| 全ポジ共通 | **33** |

`Score ≥ 33 → 4-bet` / 未満 → 3-bet を受けて Call または Fold

検算: AA(41), KK(38), QQ(34), AKs(35) が ≥33 で 4-bet。AKo(32), JJ(32), AQs(32.5) は閾値未満で 3-bet を受けてコール/フォールド。「QQ+/AKs で 4-bet」のルールが自動的に出る。

### 2.5 5-bet （4-bet 受け、コミット判断） — 通常スコア使用

| 自分のポジ | T_5bet |
|---|---|
| 全ポジ共通 | **39** |

`Score ≥ 39 → 5-bet (オールイン) or コール` / 未満 → Fold

検算: AA(41) のみ ≥39。KK(38) は閾値未満でコール (タイト寄り推奨)。「QQ 以下フォールド」ルールも自動再現。

### 2.6 Squeeze （1 オープン + 1 コール後の 3-bet）

理論的に T_3bet (vs RFI) + 3。GTO チャートなしのため概算。

| 自分のポジ | T_squeeze |
|---|---|
| 全ポジ共通 | **T_3bet (vs オープナー) + 3** |

例: BTN squeeze vs UTG open + CO call → T_squeeze = 32 + 3 = **35**
- AA(41), KK(38), AKs(35) → squeeze
- QQ(34), AKo(32) → call (squeeze 不実行)

---

## 3. 検証精度（GTO チャート整合）

GTO Wizard `Cash6m500zGeneral25Open3betV2` (3bet サイズ R7.5/R10-R11) に対する v3 (2026-05-19) 検証結果:

| シーン | 平均精度 |
|---|---|
| RFI (LJ〜BTN) | 89.6% |
| RFI (SB) | 82.2% |
| 対 RFI 3-bet (HJ/CO) | 95.9〜97.0% |
| 対 RFI 3-bet (BTN) | 87.0〜89.9% |
| 対 RFI 3-bet (SB) | 91.7〜94.7% |
| **BB defense (4 シナリオ)** | **83.4〜88.2%** |
| **BB vs SB raise (BvB)** | **79.9%** |
| 4-bet | 100% (本書ルール一致) |
| **全体平均** | **89.7%** |

検証スクリプト: `poker-drill/scripts/precompute/verify_formula.py`
生データ: `poker-drill/scripts/precompute/raw_ranges_3betv2/`

旧精度 (v2, R13.5 3bet サイズ): 全体 85.3%
主な改善: ベットサイズを R10-R11 (3betV2) に統一することで BB defense の精度が +10% 改善。

### 3.1 既知の誤差ケース（境界ハンド一覧）

以下のハンドは GTO との不一致が頻発する。本書では「境界ハンド」として注記 or 補助ルールで対応。

#### ① QJs（Score=27）: 3-bet 見逃し

GTO は多くのシナリオで QJs を 3-bet するが、T_3bet=28 の閾値 1 点未満で式では 3-bet できない。
**対応**: 補助ルール「QJs は BTN/CO ポジから CO/HJ オープンに対し 3-bet 候補」として本文に記載。

#### ② A スーテッド系（A8s, A9s など Score=28-29）: 誤 3-bet

A ブロッカー(+3) + スーテッド(+3) で Score が膨らみ、GTO がフォールドすべき場面で式が 3-bet と判定。
特に HJ/CO ヒーローが UTG/HJ オープンに対する場面で顕著。

| ハンド | Score | 問題シナリオ | GTO | 式 |
|---|---|---|---|---|
| A9s | 29 | HJ vs UTG, CO vs UTG | FOLD | **3BET(誤)** |
| A8s | 28 | CO vs UTG, HJ vs UTG | FOLD | **3BET(誤)** |

**対応**: 補助ルール「A9s 以下の A スーテッドは vs UTG では 3-bet せずフォールド」として注記。

#### ③ BTN vs CO（T_3bet=T_call=24）: 誤 3-bet 多発

BTN vs CO は CALL レンジを持たない設計（T_3bet=24 で純粋 3-bet or fold）のため、Score=24-27 帯のハンドが全て誤 3-bet になる。GTO はこのレンジを広くコールする。
不一致ハンド数: **17 件**（スコア 24-27 帯の GTO コール推奨ハンド）。

**対応**: 本書では「BTN vs CO は 3-bet or fold、コールは原則しない」として単純化。GTO コールレンジは【GTO とのズレ】コラムで言及。

#### ④ 88, 99（Score=26, 28）: シナリオ依存の誤判定

| ハンド | Score | 問題シナリオ | GTO | 式 |
|---|---|---|---|---|
| 88 | 26 | BTN vs UTG (T_3bet=32) | CALL | **FOLD(誤)** |
| 99 | 28 | BTN vs UTG (T_3bet=32) | CALL | **FOLD(誤)** |

これは 4.1 の set mining 補助ルールで部分補完（コール額 × 15 ≤ 相手スタックなら CALL）。

#### ⑤ BB vs SB（Score_BB ベース）: GTO 二極化ブラフレンジ未再現

GTO は BB vs SB で Score_BB < 28 のブラフハンド（J7o, Q6o, 54s など）を 3-bet するが、線形スコアでは再現不可能。
T_3bet=32, T_call=18 で 82.2% 精度。残 17.8% はブラフ 3-bet 未再現が主因。

---

## 4. 補助ルール（プリフロップスコアでカバーできない 7-8% を補完）

### 4.1 小ペア set mining
ペア (22-99) で `Score < T_call` でも、深スタックなら CALL:
```
コール額 × 15 ≤ 相手スタック → CALL
```
例: 3BB に 33 でコール、相手 45BB+ あれば CALL。

### 4.2 スーテッドコネクター 暗黙オッズ

SC で `Score < T_call` でも implied odds が成立する場合は参加可。
**HU と MW で適用範囲が異なる。**

```
【HU (1 対 1)】
  IP かつ Score ≤ 23 (54s〜T9s) かつ 相手スタック ≥ 100BB → CALL

【MW Level 1 (open + cold call、IP から)】
  IP かつ Score ≤ 16 (54s〜76s) かつ 相手スタック ≥ 100BB → cold call のみ可
  Score 17〜23 (87s〜T9s) は implied odds ルール不適用 → FOLD

【MW Level 1 (open + cold call、OOP から: BB/SB)】
  OOP では BB/SB の squeeze ルールおよび Score_BB 判定を使う（2.3 / 2.6）
```

スコア対照（参考）:

| ハンド | Score | HU implied odds | MW IP implied odds |
|--------|-------|----------------|-------------------|
| 54s    | 12    | ✓              | ✓                 |
| 65s    | 14    | ✓              | ✓                 |
| 76s    | 16    | ✓              | ✓（ギリギリ）      |
| 87s    | 18    | ✓              | ✗                 |
| 98s    | 20    | ✓              | ✗                 |
| T9s    | 23    | ✓              | ✗                 |
| JTs    | 25    | ✓（4.3 参照）  | ✗                 |

GTO 実測（BTN vs UTG open + HJ cold call): 65s=55%・76s=14% 参加、87s〜JTs ≈ 0%。

### 4.3 3-bet ブラフコンボ（上級者向け）
A2s-A5s (wheel suited), K9s, QJs などはGTO上でブラフ 3-bet 候補。
本書では「上級者向けの混合戦略」として別章で扱う。本式では fold 扱い。
MW スクイーズでは A3s/A4s が IP squeeze 候補として浮上するが、T_squeeze 閾値に委ねる（閾値を超えれば自動的に raise 判定）。

### 4.4 BB defense wide call
BB は 1bb 払い済 → ポットオッズが好い。式の T_call よりさらに広く CALL:
```
BB は IP オープンに対し suited 系を T_call − 3 まで広く CALL
```
精度 74% の主な誤分類はこの BB の wide call。

### 4.5 マルチウェイ (MW) での参加判断 — ベットレベル別

MW では「ベットレベル（何回目の bet か）」× 「参加人数」で閾値が変わる。
二段閾値（T_call / T_raise）はそのまま使い、閾値値のみ以下のルールで決定する。

#### Level 1 MW: open + N cold calls（3bet 前）

例: UTG open → HJ cold call → BTN の判断

```
T_raise (squeeze) = T_3bet(vs opener) + 3 × N_callers
T_call  (IP)      = N=1: Score ≤ 16 implied odds のみ (4.2 参照) / N=2: FOLD
T_call  (OOP/BB)  = Score_BB を使った 2.3 の判定を適用（例外2縮小あり、後述）
```

> ⚠️ **スコープ**: 本仕様は N≤2（キャッシュゲームで現実的な範囲）のみ扱う。
> N≥3 のシナリオ（トーナメント序盤の多人数ポット等）は **プリフロップ トーナメント編** で別途扱う。

**IP (BTN/CO) の判定フロー:**
```
[N=1: open + 1 cold call]
  Step 1: Score ≥ T_squeeze                            → raise (スクイーズ)
  Step 2: Score ≤ 16 + suited + gap≤1 + IP + ≥100BB   → cold call (implied odds)
  Step 3: それ以外                                      → FOLD

[N=2: open + 2 cold calls]
  Step 1: Score ≥ T_squeeze (T_3bet + 6)               → raise (スクイーズ)
  Step 2: FOLD  ← N=2 では IP でも implied odds 不適用
```

N=2 で implied odds を取らない理由: 5 人が関わるポットで BTN/CO が低 SC でコールすると
reverse implied odds（後ろから再スクイーズ）リスクが増大し、期待値がマイナス転化する。

**中〜高 SC が消える理由**: JTs(25)/T9s(23)/QJs(27) は通常の T_call=29 未満なのでもとより
fold 寄り。HU では 4.2 implied odds で救われていたが、MW では同ルールが適用されなくなる。
スクイーズ閾値(T_squeeze=35 前後)にも届かない → fold 確定。

GTO 実測（BTN vs UTG+HJ/CO, N=1）:

| ハンド | Score | HU 参加率 | MW 参加率 | MW 判定 |
|--------|-------|---------|---------|--------|
| 65s    | 14    | 62%     | 55%     | Step2 cold call ✓ |
| 76s    | 16    | 76%     | 15%     | Step2 cold call ✓ |
| 87s    | 18    | 41%     | 0%      | fold ✓ |
| T9s    | 23    | 100%    | 0%      | fold ✓ |
| JTs    | 25    | 100%    | 2%      | fold ✓ |
| A4s    | 23    | 100%    | 100%    | Step1 squeeze ✓ |

---

**BB defense MW — 例外2のN スケール縮小:**

HU BB defense では「スーテッド差≤4 → 常に CALL」(例外2) が広い参加を保証している。
MW では 2G (gap=3) ハンドの suited premium が劇的に低下するため、例外2 を N に応じて縮小する。

```
例外2 の適用閾値: diff ≤ max(0, 2 - N_callers)

  HU (N=0): diff≤4   （変更なし）
  N=1:      diff≤1   （SC のみ — gap=1 の suited）
  N≥2:      例外なし  （純粋 Score_BB vs T_call 判定）
```

直感: N が増えるほどポットが多人数化し、suited draw の実現率が下がる。
SC(diff=1) は最も連結性が高く MW でも価値を維持するが、1G 以上は OOP では実現率不足。

**N=1 検証（BB vs UTG + BTN cold call、T_call=25）:**

| ハンド | Score_BB | HU 例外2(diff≤4) | MW N=1 例外2(diff≤1) | Score判定 | GTO MW | 精度 |
|--------|----------|---------|---------|------------|--------|------|
| J9s    | 28       | diff=2→CALL | diff=2 → Score | 28≥25→CALL | 100%   | ✓ |
| T8s    | 26       | diff=2→CALL | diff=2 → Score | 26≥25→CALL | 100%   | ✓ |
| 97s    | 24       | diff=2→CALL | diff=2 → Score | 24<25→FOLD | 96%    | △ |
| 86s    | 22       | diff=2→CALL | diff=2 → Score | 22<25→FOLD | 100%   | ✗ |
| 87s    | 25       | diff=1→CALL | diff=1→CALL(例外) | — | 100%   | ✓ |
| 76s    | 22       | diff=1→CALL | diff=1→CALL(例外) | — | 100%   | ✓ |
| **J8s** | **27** | diff=3→CALL | diff=3 → Score | **27≥25→CALL** | **41%** | **✓** |
| **T7s** | **25** | diff=3→CALL | diff=3 → Score | **25=25→border** | **9%**  | **△** |
| **96s** | **23** | diff=3→CALL | diff=3 → Score | **23<25→FOLD** | **0%**  | **✓** |
| **85s** | **21** | diff=3→CALL | diff=3 → Score | **21<25→FOLD** | **0%**  | **✓** |
| J7s    | 23       | diff=4→CALL | diff=4 → Score | 23<25→FOLD  | 0%   | ✓ |

*97s(24)/86s(22) は GTO 上 CALL だが、diff≤1 例外に入らずスコア不足でFOLD → 誤差約2件。*
*タイトな設計として許容範囲（Formula はシンプルさ優先）。*

---

**SB MW Level 1 — cold caller のポジションで挙動が分岐:**

GTO 実測（N=1 cold call）による SB の suited connector 参加率変化：

| SB シナリオ | HU→MW SC Δ | HU→MW 1G Δ | 傾向 |
|------------|-----------|-----------|------|
| vs UTG / MW:+BTN | −0.296 | −0.013 | SC 大幅減（BTN+HJ の2人がいるため） |
| vs UTG / MW:+CO  | −0.330 | −0.013 | SC 大幅減 |
| vs HJ  / MW:+BTN | +0.133 | +0.106 | **SC 増加** |
| vs CO  / MW:+BTN | +0.092 | +0.079 | **SC 増加** |
| vs UTG / MW:+BTN（再掲） | +0.130 | +0.064 | SC 増加 |

**解釈**: cold caller が BTN (wide range) の場合、SB は低 SC (54s-76s) を**ブラフスクイーズ**として使用。
cold caller が HJ/CO (tight range vs UTG) の場合は BTN/CO IP と同様に SC が消える。

簡易ルール（上級者向け）:
```
SB MW Level 1 — cold caller が BTN/CO (IP) の場合:
  Score ≤ 16 + suited + gap≤1 → ブラフスクイーズ候補
  T_squeeze 式の範囲外だが folding equity で成立
```

通常の T_squeeze = T_3bet + 3N ルールでは捕捉不能なため、本書では「上級補助ルール」として注記。

#### Level 2 MW: raise + 3bet + N cold calls（4bet 前）

例: UTG open → HJ 3bet → CO cold flat → BTN の判断

```
T_raise (4bet squeeze) = T_4bet + 3 × N_callers = 33 + 3 × N
T_call  = 未検証。概算: T_4bet - 4 程度の narrow zone + implied odds なし
```

コール額が大きくなるため low SC の implied odds は成立しにくい。
GTO データ未取得のため概算値。

#### Level 3 MW: raise + 3bet + 4bet + N cold calls（5bet 前）

```
T_raise (5bet) = T_5bet + 3 × N_callers = 39 + 3 × N
```

実質 AA のみ。

---

**ベットレベル別まとめ**:

| MW レベル | N | 構造 | T_raise | T_call (IP) | T_call (BB) |
|----------|---|------|--------|------------|------------|
| Level 1  | 1 | open + 1 call | T_3bet + 3 | Score ≤ 16 (54s-76s) | HU と同じ T_call (例外2: diff≤1) |
| Level 1  | 2 | open + 2 calls | T_3bet + 6 | FOLD (implied odds 不適用) | HU と同じ T_call (例外2なし) |
| Level 1  | ≥3 | — | — | **トーナメント編スコープ** | **トーナメント編スコープ** |
| Level 2  | — | 3bet + N calls | T_4bet + 3N | 要検証 | 要検証 |
| Level 3  | — | 4bet + N calls | T_5bet + 3N | ほぼなし | ほぼなし |

---

## 5. 旧式からの変更点（巻① 既刊との差分）

### 廃止される概念
- **Score₃ (= H + 0.5L + ブロッカー...)**: プリフロップスコアに吸収
- **0.5 × Low Card 重み**: H と L を等価に扱う
- **「3betスコア」「Score₃」表記**: プリフロップスコア一本

### 一本化により新規追加
- **ブロッカー項を共通スコアに組み込み**: A=+3 / K=+2 / AK=+4
- **二段閾値テーブル**: T_3bet と T_call の両方を扱う表
- **5-bet 閾値 T_5bet=39**: 4-bet 受けの判断
- **Squeeze 閾値 T_3bet+3×コール数**: マルチウェイ補正

### 既存維持
- **ペア +10**: 重要なペア表現
- **スーテッド +3**: コネクター系の playability
- **set mining ルール**: 補助ルールとして温存
- **A 含むハンドのギャップ・ペナルティ免除**: A 補正

---

## 6. 採用判断のポイント

### 採用する場合のメリット
1. **暗算式が 1 つになる** — 巻① の認知負荷が大きく下がる
2. **チートシートが見開き 1 ページに圧縮可能**
3. **書籍構造の整合性**: 全シーンが同じ式 + 閾値変えのみ
4. **GTO 検証精度 91-93%** — 既刊の formula と同等以上
5. **巻① のリリース前なので、改訂のコストは妥当**
6. **poker-drill UI も統合可能** — back card 部品の共通化

### 採用しない場合 (Score₃ 維持) のメリット
- 教育的価値「3-bet では H 偏重」を残せる
- 既存実装を温存できる

### 推奨
**採用** (本書未公開のため改訂コスト OK + 設計シンプリシティ大)。

---

## 7. 関連ファイル

- 仕様: 本ドキュメント
- 計算 ref: `scripts/generate/core/preflop_score.py` (Phase 2 で作成予定)
- GTO データ: `knowledges/preflop/gto-charts.json`
- キャリブレーションスクリプト: `/tmp/calibrate_unified.py` (knowledges/ に保存予定)
- 巻① 章: `preflop/chapters/05`, `07`, `12-17`, `18-19`, `23-appendix`
- poker-drill generators: `scripts/generate/preflop_*.py`
- poker-drill UI: `src/components/CardFlip/PreflopBack*.tsx`
