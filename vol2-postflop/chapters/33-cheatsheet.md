# 第 33 章　チートシート (A4 1 枚)

> 本章は印刷推奨です。A4 1 枚に圧縮した公式 + Grid + 例外 11 ルール をまとめました。
> 実戦中はこのページだけ目を通すだけで判断が可能になります。

---

## MATCHA Score (ポストフロップ暗算公式)

```
Score = Grid[カテゴリ][board]
      + DV × mult[street]
      + 2 × overcards
      + 4 × pot
      − 2 × bs

if Score ≥ 43: レイズ
elif Score ≥ 14: コール
else:                 フォールド
```

## 12 cells Grid (覚える数字)

|           | dry | paired | wet |
|-----------|----:|-------:|----:|
| エア | 3 | 5 | 1 |
| アンダーペア | 18 | 40 | 10 |
| トップペア以上 | 38 | 10 | 31 |
| 2P+ | 25 | 28 | 23 |

## 加算項の値

**DV**: combo=4 / FD or OESD=3 / gut or BDFD=1 / no=0
**mult**: flop=3 / turn=2 / river=0
**pot**: SRP=0 / vs CR=2 / 3BP=2 / 4BP=4 (係数 ×4)
**bs**: small=0 / med75=1 / med100=2 / over=3 / over185=4 / allin=5 (係数 ×−2)
**oc**: 0 / 1 / 2 (係数 ×2)

## 例外 11 ルール (すべて wet)

| # | カテゴリ × board × street × pot | 公式 → 真解 |
|--:|---|---|
| 1 | **TP+ × wet × flop × SRP** | call → **fold** |
| 2 | **2P+ × wet × river × SRP** | call → **raise** |
| 3 | **ミドル × wet × turn × vs CR** | call → **fold** |
| 4 | **エア × wet × turn × 3BP** | fold → **call** |
| 5 | **2P+ × wet × flop × SRP** | call → **fold** |

## 短スタック / 深スタック補正

| stack | T_call | T_raise |
|---|---:|---:|
| ≤ 25bb | 12 | 40 |
| 100bb (本書 default) | **14** | **43** |
| 200bb+ | 16 | 45 |

ICM/MW: 上記 + 5〜+10 上方修正 (定性)

## 暗算手順 (5-10 秒)

1. カテゴリ 判定 (4 段階)
2. board 判定 (3 タイプ)
3. Grid 12 から数字 1 つ拾う
4. + DV × mult、 + 2 × oc、 + 4 × pot
5. − 2 × bs
6. 14 / 43 と比較、 wet なら例外チェック

## 性能 (audit、 n=154,216)

- avg loss: **0.3587 BB**
- huge%: **1.49%**
- 4BP huge: **0.53%** ★

---

## (ポケット版) 表紙の裏に貼る用

```
Score = Grid[カテゴリ][board] + DV×{3,2,0} + 2oc + 4pot − 2bs
≥43: R / ≥14: C / <14: F

           dry  paired  wet
エア        3     5     1
ミドル     18    40    10
TP+        38    10    31
2P+  25    28    23

例外 5: wet × [TP+ flop SRP / 2P+ river SRP /
        ミドル turn vsCR / エア turn 3BP /
        2P+ flop SRP]
```

## Cash/MTT note

チートシートは Cash/MTT 共通です。補正は 1 行で十分です。**「MTT 後期 +1-3 / バブル +5-10 / 9-max +2 / Cash rake 重 +1-2」**という感じで調整しましょう。詳細は第 21 章 (Cash/MTT) と第 25 章 (テーブルサイズ) をご参照ください。

## この章で覚える項目

(本章はリファレンス章、 新規暗記項目なし)
