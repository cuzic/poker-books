# キャッシュ・プリフロップ計算式 v2 仕様書

> GTO Wizard API（Cash6mGeneral_6mNL25R25, 100BB）データに基づく再設計。
> 従来の Score_R（オープン判定）に Score_C（コール判定）を追加した **二スコア体系**。

---

## 1. 二スコア体系の設計思想

| スコア | 用途 | 強化要素 |
|--------|------|----------|
| **Score_R** | オープン・3-bet・4-bet の「レイズ価値」 | ブロッカー（Aハイ・Kハイ）重視 |
| **Score_C** | コール判定の「引き価値」 | スーテッドボーナス増強（+6）、コネクタ増強 |

**根拠**：ブラフ3-betは「フォールドエクイティ + ナッツフラッシュ製造機」として機能するため、A-suitedなどのコール価値と3-betレイズ価値が逆転する現象（例：A9s > AJo as bluff 3-bet）は、二スコアでのみ自然に説明できる。

---

## 2. Score_R 式（レイズスコア）

```
■ ペア
  Score_R = 2R + (2 if R ≥ 10)
    例: AA=30, KK=28, QQ=26, JJ=24, TT=22, 99=18, 88=16, 77=14

■ 非ペア
  Base = H + L              （H=大きいランク, L=小さいランク, 2=2...A=14）
  スーテッドボーナス: +4（スーテッドなら）
  コネクタボーナス: gap=0→+3, gap=1→+2, gap=2→+1  （gap = H-L-1）
  ブロッカーボーナス: A→+2, K→+1, AK→+3

  例:
    AKs = 14+13 + 4 + 3(gap=0) + 3(AK) = 37
    AKo = 14+13 + 0 + 3        + 3     = 33
    AQs = 14+12 + 4 + 2(gap=1) + 2     = 34
    QJs = 12+11 + 4 + 3(gap=0) + 0     = 30
    JTs = 11+10 + 4 + 3(gap=0) + 0     = 28
    T9s = 10+9  + 4 + 3(gap=0) + 0     = 26
    87s = 8+7   + 4 + 3(gap=0) + 0     = 22
    KQo = 13+12 + 0 + 3(gap=0) + 1     = 29
    AJo = 14+11 + 0 + 1(gap=2) + 2     = 28
```

### Score_R 早見表（主要ハンド）

| Score_R | ハンド例 |
|---------|---------|
| 37 | AKs |
| 34 | AQs |
| 33 | AKo, KQs |
| 32 | AJs |
| 31 | KJs |
| 30 | AQo, AA, QJs, ATs |
| 29 | A9s, KTs, KQo |
| 28 | KK, JTs, A8s, AJo |
| 27 | KJo, K9s, A7s |
| 26 | QQ, T9s, Q9s, A6s, KTo |
| 25 | A5s, K8s |
| 24 | JJ, A4s, 98s, K7s |
| 23 | K6s, A3s |
| 22 | TT, A2s, K5s, 87s |
| 20 | K4s, 76s |
| 18 | 99, K3s, 65s |
| 16 | 88, K2s, 54s |
| 14 | 77, 43s |
| 12 | 66 |

---

## 3. Score_C 式（コールスコア）

```
■ ペア・オフスートハンド
  Score_C = Score_R  （変化なし）

■ スーテッドハンドのみ強化
  Base = H + L
  スーテッドボーナス: +6（Score_R の+4 より+2 増強）
  コネクタボーナス: gap=0→+4, gap=1→+2, gap≥2→+0（Score_R より強化、gap=2 ボーナス廃止）
  ブロッカーボーナス: Score_R と同じ（A+2, K+1, AK+3）

差分: Score_C(suited) - Score_R(suited) = 
  conn  gap=0: +3（スーテッドコネクタ）
  conn  gap=1: +2（スーテッドワングッパー）
  no    gap≥2: +2（スーテッド非コネクタ）
```

### Score_C 早見表（スーテッドのみ、非スーテッドは Score_R と同じ）

| Score_C | ハンド |
|---------|--------|
| 40 | AKs |
| 36 | AQs, KQs |
| 33 | AJs, KJs, QJs |
| 32 | ATs |
| 31 | A9s, JTs |
| 30 | A8s, KTs, QTs |
| 29 | A7s, K9s, T9s |
| 28 | A6s, K8s, J9s |
| 27 | A5s, K7s, Q9s, 98s |
| 26 | A4s, K6s, Q8s, T8s |
| 25 | A3s, K5s, Q7s, J8s, 87s |
| 24 | A2s, K4s, Q6s, J7s, 97s |
| 23 | K3s, Q5s, J6s, T7s, 76s |
| 22 | K2s, Q4s, J5s, T6s, 86s |
| 21 | Q3s, J4s, T5s, 96s, 65s |
| 20 | Q2s, J3s, T4s, 95s, 75s |
| 19 | J2s, T3s, 85s, 54s |
| 17 | 43s |
| 16 | 53s |
| 15 | 32s |

---

## 4. オープンレイズ（RFI）閾値

```
T_open（ポジション別）:
  UTG: 24（Score_R ≥ 24）
  HJ:  22
  CO:  20
  BTN: 18
  SB:  22

例外ルール：
  Ax-スーテッドは全ポジションから必ずオープン（A2s〜AKs）
  → UTG からでも A2s(SR=22), A3s(23) は T_open=24 未満だがオープン
  → 根拠: ナッツフラッシュドロー + ブロッカー価値が EV プラス
```

### RFI データ整合（主要境界）

| ポジション | GTO raise% | T_open | 境界ハンド |
|----------|-----------|--------|----------|
| UTG | 17.5% | 24 | 77=72%、88=100%、K5s=98%（例外）|
| HJ  | 21.7% | 22 | 55=47%、66=92% |
| CO  | 27.9% | 20 | 33=14%、44=53% |
| BTN | 40.6% | 18 | 22=33%（混合） |
| SB  | 34.4% | 22 | 33=81%、44=63% |

---

## 5. vs オープン（IP ポジション：BTN/CO/SB）

### 決定フロー

```
1. Score_R ≥ 29（非ペア）OR Score_R ≥ 26（ペア）→ バリュー3-bet
2. Ax-スーテッド（L ≤ 9）→ ブラフ3-bet（IP から）
3. Score_C ≥ T_call_IP[opener] → コール
4. ペア ≥ 77（77〜JJ）→ コール（セットマイニング）
5. それ以外 → フォールド
```

### T_call_IP（コール閾値）

```
T_call_IP = 34 - 2 × opener_rank
  UTG(rank=1): 32
  HJ(rank=2):  30
  CO(rank=3):  28
  BTN(rank=4): 26（SB からの場合）

例: BTN vs CO (T=28)
  コール: KQs(SC=36)、AJs(33)、KJs(33)、QJs(33)、ATs(32)、JTs(31)、A9s(31)...
  フォールド: A8s(SC=30) 以下のスーテッド（ただし A-スーテッドはブラフ3-bet候補）
  ペアコール: TT(99%C)、99(59%C)、88(44%C)、77(30%C)
```

### バリュー3-bet 対象ハンド（全 IP スポット一致）

| Score_R | ハンド | 3-bet 頻度 |
|---------|--------|-----------|
| 37 | AKs | 100% |
| 34 | AQs | 61-87% |
| 33 | AKo, KQs | 98-100% |
| 32 | AJs | 33-95% |
| 31 | KJs | 33-63% |
| 30 | AQo, AA, QJs, ATs | 66-100% |
| 29 | A9s, KTs, **KQo** | 45-99% |

**注**: KK(SR=28)、QQ(SR=26) は T_3bet_pairs=26 ルールで必ず3-bet対象。

### ブラフ3-bet 補足ルール（IP）

```
IP ポジション（BTN/CO/SB）から vs オープン：
  Ax-スーテッド（A2s〜A9s）→ 3-bet（BTN vs CO で 69-100%）
  補足: KQo(SR=29) も IP から広く3-bet
  補足: AJo, KJo は vs CO/BTN から IP 3-bet ブラフ
```

**理由**: A-スーテッド低キッカーは「ナッツフラッシュドロー + A ブロッカー」でブラフEVが高い。ただし vs UTG/HJ の IP からは注意（A9s は vs UTG でも 58% 3-bet と高め）。

### IP 精度検証（GTO Wizard データ対比）

| スポット | 精度 | 主要エラー |
|---------|------|----------|
| BTN vs UTG | 96.2% | 88/99/QQ混合 |
| BTN vs HJ | 96.4% | 同上 |
| BTN vs CO | 93.4% | AJo/KJo/KQo ブラフ3-bet |
| SB vs BTN | 90.3% | AJo/ATo(SB からの広い3-bet) |
| CO vs UTG | 95.2% | KQo(3-bet 捕捉) |
| **IP 全体** | **93.7%** | ペア境界・ブラフオフスート |

---

## 6. vs オープン（BB）

BB はポット・オッズが高く（最大2.5x→コール3:1）、防御レンジが広い。

### BB 3-bet 閾値（opener別）

```
T_3bet_BB = 32 - 2 × opener_rank
  vs UTG(1): 30 → AA/AKs/AKo/AQs+
  vs HJ(2):  28 → +KK
  vs CO(3):  26 → +QQ/JJ/KQs
  vs BTN(4): 24 → +JJ/TT（頻繁に3-bet）
  vs SB(≈5): 22 → 広い（TT/99/88 も）

例外: Ax-スーテッド（A2s〜A9s）はブラフ3-bet候補（vs CO/BTN/SB は頻度高）
```

### BB コール閾値

```
■ ペア: 全てコール（22〜99 全て BB vs UTG でコール、ポットオッズ有利）

■ スーテッドハンド:
  T_call_BB_s = 19 - 2 × (opener_rank - 1)
    vs UTG: 17  (43s SC=17、53s SC=16 でコール境界)
    vs HJ:  15  (53s SC=16 以上 → 32s SC=15 は折り畳む)
    vs CO:  13
    vs BTN: 11
    vs SB:  13

  ※ スーテッドコネクタ（gap=0,1）は SC が高く優先的にコール

■ オフスートハンド（ペア以外）:
  T_call_BB_o = 30 - 2 × opener_rank（Score_R 使用）
    vs UTG: 28  → AQo/AJo+ コール（AQo=30、AJo=28）
    vs HJ:  26  → +KJo(27)/KQo(29)
    vs CO:  24  → +ATo(26)
    vs BTN: 22  → +A9o/K9o/JTo/T9o
    vs SB:  22  → 同様
```

**注**: BB のオフスート境界は複雑（A5o は vs SB でブラフ3-bet、A7o はコールで混合など）。詳細は GTO データ参照。スーテッドコネクタ優先のディフェンスが基本。

---

## 7. vs 3-bet（4-bet 判定）

### 4-bet バリュー閾値

```
OOP（UTG/HJ）の場合:
  T_4bet_value = 30（AKs/AKo + AA のみピュアバリュー）
  T_4bet_bluff = 24（A4s/A5s をブラフ4-bet）

IP（CO/BTN）の場合:
  T_4bet_value = 24（JJ+、AKs、AKo、KJs、KTs 等）
  T_4bet_bluff = 23（A3s〜A5s、K5s）

コールレンジ（GTO):
  OOP vs 3-bet: AQs(SC=36)、AJs(33)、T9s(29)、JJ(24)、87s(25)...Score_C ≥ 29
  IP vs 3-bet: AQs/KQs/AJs + 76s/65s/54s（ポットオッズ良好）
```

### vs 3-bet 閾値（簡易）

| ポジション | 4-bet | コール | フォールド |
|-----------|-------|--------|----------|
| OOP(UTG) | SR ≥ 28 + ブラフA4s/A5s | SC ≥ 29 + JJ/TT | それ以下 |
| IP(BTN/CO) | SR ≥ 24 + ブラフA3s〜A7s | SC ≥ 29 + TT-88 | それ以下 |

---

## 8. 体系まとめ（一覧表）

### 意思決定マトリクス

| シナリオ | レイズ条件 | コール条件 | フォールド |
|---------|----------|----------|----------|
| **RFI** | SR ≥ T_open[pos] + Ax-suit | — | SR < T_open |
| **IP vs open** | SR ≥ 29（非ペア）/ SR ≥ 26（ペア）+ A-suit bluff | SC ≥ 34-2×rank + pair 77+ | それ以外 |
| **BB vs open** | SR ≥ 32-2×rank + A-suit bluff | ペア全て + SC ≥ T_BB_s + SR ≥ T_BB_o | それ以外 |
| **vs 3-bet** | SR ≥ 28(OOP)/24(IP) + A-suit bluff | SC ≥ 29 + pair | — |

---

## 9. 補足ルール一覧

### 9-1. Ax-スーテッド「万能ルール」
```
全シナリオで Ax-スーテッド（Aがハイカード）は特別扱い:
  RFI:     全ポジションから必ずオープン
  IP3-bet: A2s〜A9s は IP からブラフ3-bet（A ブロッカー + ナッツFD）
  BB3-bet: vs CO/BTN/SB から A4s/A5s 以下もブラフ3-bet

例外: A-スーテッド高キッカー（AJs/AQs/AKs）は バリュー3-bet。
```

### 9-2. KK・QQ ペア特例
```
KK(SR=28): 必ず3-bet（T_3bet_value=29 で除外されるが常に3-bet）
QQ(SR=26): 必ず3-bet（IP から全て、BB からも多くの状況で3-bet）
JJ(SR=24): IP vs CO/BTN から3-bet、vs UTG/HJ はコール
TT(SR=22): IP vs BTN/SB から3-bet、他はコール/フォールド
```

### 9-3. Score_C が Score_R と同じになるケース
```
オフスートハンドはコール価値がレイズ価値と同等。
フラッシュドローがないため Score_C の強化は適用しない。

実践: オフスートハンドの意思決定 = Score_R のみで判断。
```

---

## 10. 既存仕様（v1）との比較

| 項目 | v1 | v2（本仕様） |
|-----|----|------------|
| スコア数 | 1（Score_R） | 2（Score_R + Score_C） |
| 3-bet 閾値 | 固定なし | **T_3bet = 29/26（ペア）** |
| コール閾値 | なし（BB Score のみ） | **T_call_IP = 34-2×rank** |
| ブラフ3-bet | なし | **Ax-suit 補足ルール** |
| IP精度 | ~89.7% | **~93.7%**（BTN/CO/SB vs open） |
| BB 精度 | ~79.9%（BB vs SB） | 64-85%（BB の polar 3-bet が複雑） |
| RFI 精度 | ~89.7% | **84.8%**（Ax-suit 例外込み） |
| **全体** | ~89.7% | **87.8%** |

---

## 11. データ出典

GTO Wizard API で収集（2026-05-21）:
- ゲームタイプ: `Cash6mGeneral_6mNL25R25`（100BB 6-max キャッシュ）
- フェーズ: RFI, vs_open, vs_3bet, vs_4bet, vs_5bet, multiway
- 収集ファイル: `cash-postflop/findings/preflop_gto_*.json`

主要検証ポイント（全 IP スポット、非ペアハンド）:
- T_3bet_value=30 → 全スポット一致（AA/KK/AKs/AKo/AQs/AQo/KQs/AJs/KJs/QJs）
- T_call_IP=34-2×rank → 精度 92〜98%（スポット別）
- A-スーテッドブラフ3-bet → 全 IP スポットで A2s〜A9s が 60-100% 3-bet
