# 付録 B: SBR 別参照カード

<!-- markdownlint-disable MD026 MD033 MD036 MD040 MD060 -->

> **使い方**: ゾーンと SBR が決まったら、対応するカードを参照してください。数値は v4 スコア（非ペア）または最低ペアランク（ペア）です。

---

## B-1 Zone P カード（SBR=8〜14）

Zone P は push/fold 完結のゾーンです。min-raise はほぼ使いません（SBR=14 の UTG/UTG1 を除く）。

### T_push 非ペア（push が主流の最低スコア）

| SBR | UTG  | UTG1 | UTG2 | HJ   | CO   | BTN  | SB  |
|-----|------|------|------|------|------|------|-----|
| 8   | 22   | 22   | 22   | 14   | 14   | 14   | 12  |
| 10  | 25.5 | 22   | 14   | 14   | 14   | 14   | 9   |
| 12  | 27   | 18   | 16   | 14   | 14   | 14   | 10  |
| 14  | 25   | 24   | 18   | 16   | 14   | 14   | 12  |

**SBR=8 UTG 注意**: スコア 22 閾値だが K8s/T8s 等が GTO で fold になる例外あり。実用的な暗記リスト: 「Ax 全手 + KJo 以上 + JTs/QTs + 22 以上のペア」。

**SB の T_push**: SB は limp 戦略と混在するため、この表は純 push（limp を除く）の最低スコアです。リンプ trap については B-3 を参照してください。

### 最低オープンペア（Zone P: 直接参照）

| SBR | UTG | UTG1 | UTG2 | HJ  | CO  | BTN |
|-----|-----|------|------|-----|-----|-----|
| 8   | 22+ | 22+  | 22+  | 22+ | 22+ | 22+ |
| 10  | 44+ | 33+  | 22+  | 22+ | 22+ | 22+ |
| 12  | 55+ | 44+  | 33+  | 22+ | 22+ | 22+ |
| 14  | 66+ | 55+  | 44+  | 22+ | 22+ | 22+ |

**読み方**: 「55+」= 55, 66, 77, 88, 99, TT, JJ, QQ, KK, AA の全て。「22+」= 全ペア。

### SB リンプ trap（Zone P 特有）

SBR ≤ 12 の SB では、以下のプレミアム手がリンプ（call/limp in）の GTO 最善です。push してしまうと獲得は 1.5BB 止まり。リンプなら BB 誘い込みでポストフロップ全スタックを狙えます。

| リンプ対象（SBR=12 SB） | スコア |
|------------------------|--------|
| AKs | 37 |
| AQs | 35 |
| KQs | 32 |
| QJs | 30 |
| KJs | 30 |
| JTs | 28 |

**簡略記憶**: 「SBR ≤ 12 の SB はプレミアム手（AKs/AQs/KQs/QJs/KJs/JTs）はリンプ、残りは push or fold」。

---

## B-2 Zone O カード（SBR=20〜40）

Zone O は min-raise 主体のゾーンです。push は AA/KK 等のごく一部のみです。

### T_open 非ペア（オープン可の最低スコア）

| SBR | UTG  | UTG1 | UTG2 | HJ   | CO   | BTN  |
|-----|------|------|------|------|------|------|
| 20  | 23.5 | 23   | 21   | 19   | 17   | 14   |
| 25  | 22.5 | 22   | 21   | 17   | 15   | 14   |
| 30  | 22   | 21   | 19   | 17   | 17   | 13   |
| 40  | 21   | 21   | 17   | 17   | 15   | 13   |

**BTN の特殊性**: SBR=25〜30 で T_open=13〜14 はスコア上ほぼ全手オープン可能。弱いオフスーツ（スコア 3〜10 程度）のみ fold。

**オープンサイズの変化**:
- SBR ≤ 20: R2（2BB）
- SBR=25, 30: R2.1
- SBR=40: R2.3

### 最低オープンペア（Zone O: 直接参照）

| SBR | UTG | UTG1 | UTG2 | HJ  | CO  | BTN |
|-----|-----|------|------|-----|-----|-----|
| 20  | 66+ | 66+  | 55+  | 55+ | 44+ | 22+ |
| 25  | 55+ | 55+  | 44+  | 44+ | 44+ | 44+ |
| 30  | 44+ | 44+  | 33+  | 33+ | 33+ | 33+ |
| 40  | 44+ | 33+  | 22+  | 33+ | 33+ | 22+ |

### BB ディフェンス要約（SBR=25）

**基本方針**: フォールドは最低限のゴミ手のみ。3-bet は価値ハンドと一部ブラフのみ。コールが大多数。

| 対レイズ | T_fold（近似） | T_3bet（value） | 3-bet ブラフ補完 |
|---------|-------------|----------------|----------------|
| vs UTG  | 12 | 28 | なし |
| vs HJ   | 10 | 26 | JTs, T9s |
| vs CO   | 8  | 24 | JTs, T9s, 98s |
| vs BTN  | 8  | 27 | T9s, T8s, 98s, K6-7s |

**BB 折れる手の目安**: 「gap ≥ 4 かつ高カードが 9 以下のオフスーツ（例: J6o, T5o, 85o, K2o 等）」。スーテッドは基本コール（スコア不問）。

**BB ペア判断（SBR=25）**:
- vs UTG: 99+ は 3-bet（push）、22〜88 はコール
- vs HJ/CO/BTN: 22 以上は全部 3-bet（push）

**BB 3-bet 確定非ペア（SBR=25）**:
- vs UTG: AKs, AKo, AQo, QTs の 4 手
- vs BTN: ATs+/AJs+/AQo+/AJo+/ATo+/KQo + JTs + T9s + T8s + 98s + K7s + K6s + A9o

---

## B-3 SB ディフェンス要約（SBR=25 vs BTN オープン）

SB は OOP のため fold 65%。コールは 19 手のみです。

### SB の 3 択

| アクション | 手数 | 主な対象 |
|-----------|-----|---------|
| push（3-bet） | 28 手 | Ax suited / Ax offsuit 強 / strong Broadway |
| コール | 19 手 | K-suited 一部 / suited mid connector / Broadway offsuit |
| fold | 残り（約 109 手） | その他全て |

### SB push（3-bet）主要ハンド

| カテゴリ | 手 |
|---------|---|
| Ax suited | A2s〜A6s, A9s〜AKs（A7s, A8s は例外コール） |
| Ax offsuit | A7o 以上 |
| Strong Broadway | KQs, KTs, QJs, QTs, JTs, T9s |
| Strong offsuit | AKo, AQo, AJo, ATo, KQo, KJo |

### SB コール 19 手

| カテゴリ | 手 |
|---------|---|
| K-suited | K5s, K6s, K7s, K8s, K9s, KJs |
| Suited connector（gap≤4） | 76s, 87s, 97s, 98s, T8s, J8s, Q8s, Q9s |
| Broadway offsuit | KTo, QTo, QJo |
| Ax 例外 | A7s, A8s |

**記憶補助**: 「SB コール = K-suited か suited mid connector（76s〜Q8s 程度）か Broadway offsuit」。

### SBR 別コール範囲変化

| SBR | コール手数 | 差分 |
|-----|---------|------|
| 17  | 11 手 | SBR=25 から: 76s, A7s, A8s, 87s, 97s, KJs, KTo, QJo が未参加 |
| 20  | 15 手 | 上記から: K5s, 87s, 97s, KTo, QJo, QJs が加わる |
| 25  | 19 手 | 基準。76s, A7-8s, KJs, T8s/98s 等が全部参加 |

**SBR が浅いほどコール範囲は狭くなります**。SBR=17 では連続性の弱い手や K5s 等をコールする価値が低下します。

---

## B-4 3-bet に直面した場合の対処表（Zone O 全般）

Zone O では 4-bet のサイズが存在せず、fold/call/オールイン（shove）の 3 択です。

### T_shove / T_call テーブル（SBR=25 代表）

| オープナー | 3-bettter | T_shove | T_call | shove 手数 | call 手数 |
|-----------|-----------|---------|--------|-----------|---------|
| UTG | BB | 27 | 22 | 6 | 22 |
| UTG | BTN（cold） | 26 | 20 | 10 | 29 |
| HJ | BB | 22 | 20 | 13 | 35 |
| CO | BB | 20 | 20 | 17 | 36 |
| BTN | BB | 16 | 16 | 14 | 51 |

**実戦での使い方**:
```
score ≥ T_shove → オールイン
T_call ≤ score < T_shove → コール
score < T_call → fold
```

**SBR 別 T_shove 安定性（UTG vs BB 3-bet）**:

| SBR | T_shove | T_call | shove 手数 |
|-----|---------|--------|-----------|
| 20  | 26      | 22     | 6 |
| 25  | 27      | 22     | 6 |
| 30  | 27      | 22     | 7 |

UTG の shove 範囲は SBR によらず KK/AKs/AKo ≈ 6 手程度で安定しています。

---

## B-5 スクイーズ閾値要約（SBR=25）

オープン + コールドコールへの参入判断です。

| スクイーザー | 状況 | T_sq | 代表ハンド |
|------------|------|------|---------|
| BTN | UTG+HJ | 27.5 | AA/KK/AK/AQ/JJ+ |
| BTN | UTG+CO | 28 | 同上（より tight） |
| SB | UTG+BTN | 25.5 | AA/KK/AK/AQ/JJ/TT+ |
| SB | CO+BTN | 20 | 上記 + AJs/KQs 等 |
| BB | UTG+CO | 26 | 価値ハンドのみ |
| BB | BTN+SB | 14 | 広いポーラー range |

**注意**: BB vs BTN+SB の T_sq=14 は score_mtt 単純閾値では精度 60% です。実際は「ペア全部 + A-blocker ブラフ」の特殊構造です。

---

> **付録 B まとめ**
>
> - Zone P（SBR ≤ 14）: T_push 表と最低 push ペア表を参照。SBR=8 UTG は暗記リストが有効
> - Zone O（SBR 20〜40）: T_open 表と最低オープンペア表を参照。BTN はほぼ全手参加
> - BB ディフェンス: 「スーテッドは常にコール」「3-bet 確定は 4 手のみ（vs UTG）」を基本とする
> - SB ディフェンス: fold 65%、コール 19 手、push 28 手が SBR=25 の基準
> - 3-bet に直面: T_shove/T_call の 2 閾値で 3 分割（fold/call/shove）
