# 第 31 章　境界ハンド総覧

## 31.1 本書の暗記対象を 1 表に集約

本書を通じて出てきた **境界ハンド / 境界 board / 例外ルール** を 1 章にまとめます。
全 56 項目のうち、暗記必須なものを次でご紹介します。

## 31.2 公式の核心

```
Score = Grid[カテゴリ][board] + DV × mult[street] + 2 × oc + 4 × pot − 2 × bs

≥ 43: レイズ / ≥ 14: コール / else: フォールド
```

## 31.3 12 cells Grid

|           | dry | paired | wet |
|-----------|----:|-------:|----:|
| エア | 3 | 5 | 1 |
| アンダーペア | 18 | 40 | 10 |
| トップペア以上 | 38 | 10 | 31 |
| 2P+ | 25 | 28 | 23 |

## 31.4 加算項の値

| 軸 | 値 |
|---|---|
| **DV** (combo / FD or OESD / gutshot or BDFD / no) | 4 / 3 / 1 / 0 |
| **street mult** (flop / turn / river) | 3 / 2 / 0 |
| **pot** (SRP / vs CR / 3BP / 4BP) | 0 / 2 / 2 / 4 (× 4) |
| **bs** (small / med75 / med100 / overbet / 185 / allin) | 0 / 1 / 2 / 3 / 4 / 5 (× −2) |
| **oc** (board 最高超え数) | 0 / 1 / 2 (× 2) |

## 31.5 例外 11 ルール

| # | 条件 | 公式 pred | 真の解 | n |
|--:|---|---|---|---:|
| 1 | TP+ × wet × flop × SRP | call | **fold** | 350 |
| 2 | 2P+ × wet × river × SRP | call | **raise** | 258 |
| 3 | ミドル × wet × turn × vs CR | call | **fold** | 179 |
| 4 | エア × wet × turn × 3BP | fold | **call** | 159 |
| 5 | 2P+ × wet × flop × SRP | call | **fold** | 125 |

→ すべて **wet** に集中しています。「wet × ?」を見かけたら例外候補として確認しましょう。

## 31.6 境界ハンド ~15 個 (第 7 章より抜粋)

公式値 ± 補正で覚える境界ハンド (multi spots)：

| ハンド | spot | 補正 | 備考 |
|---|---|---|---|
| A2s on A82 | TP+ × dry | -2 | TPWK |
| K9 on K72 | TP+ × dry | -1 | TPGK |
| 77 on K72 | ミドル × dry | +3 | second pair |
| A7s on AA7 | TP+ × paired | +5 | 2P 化 |
| TT on T87 | 2P+ × wet | -2 | set on wet |
| 65 on 998 | エア × paired | +3 | DV 効果 |
| 76s on 985 | エア × wet | +4 | OESD + bdfd |
| QQ on T98 | ミドル/TP+ 境界 | -3 | overpair on wet |

詳細は第 7 章をご参照ください。

## 31.7 境界 board ~10 個 (第 8 章より抜粋)

| board | 旧分類 | 修正 |
|---|---|---|
| 7-7-2 | paired | paired (MERGED、wide attack) |
| K-K-2 | paired | paired (CONDENSED、TP+ adv) |
| Q-J-T | wet | wet (POLAR) |
| T-9-8 | wet | wet (CONDENSED) |
| 7-5-2 | dry | dry (POLAR、low_dry) |
| A-7-2 | dry | dry (MERGED、A blocker) |
| Tdh 9h 4h (mono) | wet | wet (POLAR extreme) |

詳細は第 8 章をご参照ください。

## 31.8 short / deep stack 補正 (第 18-19 章より)

| stack 深度 | T_call | T_raise |
|---|---:|---:|
| 短スタック (≤ 25bb) | 12 | 40 |
| 標準 (100bb、本書 default) | **14** | **43** |
| 深スタック (200bb+) | 16 | 45 |

ICM/MW ではさらに上方修正となります (第 21-23 章参照)。

## 31.9 暗記項目の累積

| カテゴリ | 項目数 |
|---|---:|
| 公式 1 行 | 1 |
| 12 cells Grid | 12 |
| 加算項の値 (DV / mult / pot / bs / oc) | 5 |
| 例外 11 ルール | 5 |
| 境界ハンド | ~15 |
| 境界 board | ~10 |
| stack 補正 | 2 |
| ICM/MW 方針 | 2 |
| **計** | **~52 項目** |

(toc.md 当初目標 56 項目とほぼ一致します)

暗記 52 項目で、幅広いポストフロップ状況をカバーできます。焦らず、少しずつ身につけていってください。

## Cash/MTT note

境界総覧の暗記項目は Cash/MTT 共通です。短/深スタック補正 (第 18-19 章) と ICM/MW 補正 (第 21-23 章) の Cash/MTT 別運用については第 20, 24 章をご参照ください。

## この章で覚える項目 (累計表示のみ、既出のため新規 0)

(本章は復習章のため、新規暗記項目はありません)
