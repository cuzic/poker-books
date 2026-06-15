---
chapter: "appendix-C"
title: "付録C　タイプ別調整まとめ表"
section: "付録"
target_kchar: 4
status: draft
---

# 付録C　タイプ別調整まとめ表

実戦で参考にしやすい、1 ページの早見表です。

---

## プリフロップ調整 (BTN T_open / T_3bet)

| タイプ | BTN T_open | T_3bet (バリュー) | T_3bet (ブラフ) | iso 推奨 |
|---|---|---|---|---|
| GTO 均衡 | 18 | 32 | 28 | 標準 |
| ニット | **13〜14** | 36 (絞る) | **22〜24** (拡大) | あり |
| CS | **15〜16** | 36〜38 (絞る) | **0%** (禁止) | 必須 |
| LAG (左隣) | **21〜23** | 28〜30 | 30 (絞る) | あり |
| マニアック (左隣) | **26〜28** | 30 (バリューのみ) | **0%** (禁止) | call で trap |
| TAG | 18 (変更なし) | 32 | 28 | 標準 |

---

## ポストフロップ MATCHA 判定軸 補正

| タイプ | レンジ分布見立て | エクイティバケット | 形勢 | bluff Cbet | value sizing |
|---|---|---|---|---|---|
| ニット | 2 極化型寄り | hero 2P+↓ | 優勢↓ | **+15〜20%pt** | 33% (small) |
| CS | 密集型寄り | hero 良ハンド↑ | 五分五分→優勢 | **0%** (禁止) | 50〜75% |
| LAG | 2 極化型寄り | hero 弱→良 | 劣勢→五分五分 | -5%pt | 標準 50% |
| マニアック | 2 極化型極端 | hero ミドル→良 | 劣勢→五分五分 | **0%** (禁止) | check trap |
| TAG | (補正小) | (補正小) | (微小) | ±5%pt | 標準 50% |

---

## Score シフト (vs ベット側、コール側)

| タイプ相手 | Score shift |
|---|---|
| ニット相手 | +5 (call 寄り、慎重に) |
| CS 相手 | +3 |
| LAG 相手 | +8 (ブラフキャッチ拡大) |
| マニアック相手 | +12 |
| TAG 相手 | +2 (微調整) |

---

## ターン・リバー sizing matrix

### バリュー bet サイズ

| タイプ \ board | dry | paired | wet |
|---|---|---|---|
| ニット | 100〜150% (overbet、強い手のみ) | 100% | 75% (CR risk) |
| CS | 75% | 50% | 50% (CR risk) |
| LAG | 100% | 75% | 75% |
| マニアック | check | check | check |
| TAG | 50〜75% | 50% | 50〜75% |

### bluff bet 頻度

| タイプ | bluff freq |
|---|---|
| ニット相手 | 拡大 (60% scare card で打つ) |
| CS 相手 | 0% (絶対禁止) |
| LAG 相手 | 慎重に (33% scare card のみ) |
| マニアック相手 | 0% (絶対禁止) |
| TAG 相手 | 標準 (33%) |

---

## リバー big bet 受けの判定

| bet サイズ | ニット相手 | CS 相手 | LAG 相手 | マニアック相手 | TAG 相手 |
|---|---|---|---|---|---|
| 33% | call any | fold (TP 程度) | call | call | call |
| 50% | fold (TPTK 未満) | fold (TP) | call (mid+) | call (any pair) | call (TP+) |
| 75% | fold (TP) | fold (TP) | call (TP+) | call (mid pair+) | call (TP+) |
| 100% | **fold all** | fold (overpair) | call (TP+) | call (TP+) | fold (mid pair) |
| 150% | fold | fold | call (TP+ 慎重に) | call (TP+) | fold |
| 200% | fold | fold | fold (overpair+) | call (overpair) | fold |

---

## 席選び早見表

| 状況 | 推奨アクション |
|---|---|
| CS が右隣 | 席替え (左に移しましょう) |
| CS が左隣 | 維持します |
| LAG が左隣 | 即席替えしましょう |
| マニアックが左隣 | 即席替え (最優先)します |
| フィッシュ 2 人以上 | 維持します。卓品質は高いです |
| フィッシュ 0 人 | 卓変更を検討しましょう |

---

## 過剰調整の上限 (第 20 章)

| 調整項目 | 上限 |
|---|---|
| T_open シフト | ±10 |
| T_3bet シフト | ±8 |
| Score シフト | ±12 |
| bluff freq シフト | ±50%pt |
| value sizing シフト | ±50%pt |

---
