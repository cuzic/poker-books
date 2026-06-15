# 第 5 章　Cash マルチウェイ / スクイーズ

マルチウェイ（MW）シナリオでも **同じ 4 係数** を使います。
閾値が変わるだけです。

## 5.1 GTO データ閾値（マルチウェイ平均）

| コンテキスト | 閾値 | シナリオ数 |
|---|---|---|
| MW_BB（BB スクイーズ） | 28 | 4 |
| MW_SB（SB スクイーズ） | 33 | 5 |
| MW_IP（IP スクイーズ） | 37 | 3 |

## 5.2 スクイーズ閾値の計算式

```
T_squeeze = T_3bet（vs オープナー） + 3 × N_callers
```

N_callers = コールした人数（オープナー以外）です。

### T_3bet 一覧（ポジション × オープナー）

| スクイーズ側 | vs UTG open | vs HJ open | vs CO open | vs BTN open |
|---|---|---|---|---|
| **BTN** | T_3bet=36 → sq=36+3N | T_3bet=36 → sq=36+3N | T_3bet=26 → sq=26+3N | — |
| **SB** | T_3bet=34 → sq=34+3N | T_3bet=32 → sq=32+3N | T_3bet=30 → sq=30+3N | T_3bet=25 → sq=25+3N |
| **BB** | T_3bet=36 → sq=36+3N | T_3bet=34 → sq=34+3N | T_3bet=30 → sq=30+3N | T_3bet=28 → sq=28+3N |

### 具体例

**BTN スクイーズ vs UTG open + CO cold call (N=1)**
```
T_3bet(BTN vs UTG) = 36
T_squeeze = 36 + 3 × 1 = 39
AA(41) ≥ 39 → スクイーズ ✓
KK(39) ≥ 39 → スクイーズ ✓
QQ(37) < 39 → フォールド ✗
```

**BB スクイーズ vs UTG open + BTN cold call (N=1)**
```
T_3bet(BB vs UTG) = 36
T_squeeze = 36 + 3 × 1 = 39
```

**コール 2 人（N=2）の場合**
```
T_squeeze = T_3bet + 3 × 2 = T_3bet + 6
（ほとんどのポジションで AA のみスクイーズ）
```

## 5.3 IP コールドコール（implied odds）

スクイーズ閾値に届かない場合でも、スーテッドコネクター系は
implied odds が成立すれば IP からコールドコール可能です。

```
【HU (N=0 cold callers)】
  IP かつ Score ≤ 23 (T9s 以下) かつ 100BB+ → コール

【MW (N=1 cold caller)】
  IP かつ Score ≤ 16 (76s 以下) かつ 100BB+ → コールのみ可能
  Score 17〜23 (87s〜T9s) は implied odds 不適用 → フォールド
```

## 【GTO とのズレ】

MW_BB（精度 96.7%）・MW_SB（95.9%）は非常に高精度です。
MW_IP はスクイーズサイズ依存でわずかにズレが生じます。
N=2 以上のスクイーズはデータ少なく概算値です。
