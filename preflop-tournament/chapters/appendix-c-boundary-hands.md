# 付録 C: 境界ハンドリスト（暗記推奨）

<!-- markdownlint-disable MD026 MD033 MD036 MD040 MD060 -->

> **使い方**: 閾値のすぐ内外に位置する「境界ハンド」は、スコアを毎回計算せずに記憶しておくことで判断速度が上がります。各フレームワークの境界付近で迷いやすいハンドを一覧化しました。

---

## C-1 SBR=25 UTG オープン境界（T_open=22.5）

閾値 22.5 を基準に、ギリギリ OK とギリギリ NG のハンドをまとめます。

### スーテッド: ギリギリ OK（スコア ≥ 22.5）

| ハンド | スコア | GTO 動向 |
|--------|--------|---------|
| KQs | 32 | 100% オープン |
| T9s | 26 | 100% オープン |
| 98s | 24 | 100% オープン |
| K8s | 24 | 100% オープン |
| T8s | 24 | 96% オープン |
| Q8s | 23.5 | 88% オープン |
| J8s | 23.5 | 100% fold（式の誤検知） |
| A3s | 23 | 54% fold（境界、やや fold 寄り） |
| K7s | 22 | 72% fold（T_open=22.5 をわずかに下回る） |

**実用上の境界**:
- スーテッドは K8s 以上（スコア 24）がオープン確定
- K7s（22）と 97s（22）は fold
- J8s, Q8s（23.5）は式上は OK だが、J8s は GTO では fold になる例外手

### オフスーツ: ギリギリ OK（スコア ≥ 22.5）

| ハンド | スコア | GTO 動向 |
|--------|--------|---------|
| AKo | 32 | 100% オープン |
| KJo | 25 | 100% オープン |
| QJo | 25 | 高頻度オープン |
| ATo | 27 | 100% オープン |
| KTo | 22.5 | 境界（約 50% オープン） |
| A9o | 23 | 100% fold（Axo 弱手問題） |

**注意**: A9o はスコア 23 で閾値を超えますが GTO では fold です。「ATo（27）は OK、A9o（23）は fold」を境界として覚えてください。

---

## C-2 SBR=25 BTN オープン境界（T_open=14）

BTN は T_open=14 と非常に低く、ほぼ全手がオープン対象です。ただし最低限以下の手は fold します。

### BTN で fold する主な手（スコア < 14）

| カテゴリ | 例 |
|---------|---|
| 低オフスーツ trash | 72o（スコア 9）、52o（スコア 7）等 |
| 低スーテッド trash | 32s（スコア 11）、42s（スコア 11）等 |
| 最低スーテッド | 23s, 24s, 25s（スコア 11〜10.5） |

**実用ルール**: BTN では「スーテッドはほぼ全手 OK（32s スコア 11 のみ検討）、オフスーツは 5 以下が確実 fold」。

---

## C-3 SBR=12 SB リンプ trap（暗記必須 6 手）

SBR ≤ 12 の SB でこれらを push するのは典型的なミスです。リンプが GTO 最善です。

| ハンド | スコア | SBR=12 SB アクション |
|--------|--------|-------------------|
| AKs | 37 | limp 100% |
| AQs | 35 | limp 100% |
| KQs | 32 | limp 100% |
| QJs | 30 | limp 94% |
| KJs | 30 | limp 86% |
| JTs | 28 | limp 95% |

**AA/KK も limp trap 対象**（ペアとして BTN で SBR=8〜12 常に limp）。

---

## C-4 BB 3-bet 確定リスト（SBR=25）

### vs UTG: 3-bet 確定 4 手

| ハンド | スコア |
|--------|--------|
| AKs | 37 |
| AKo | 32 |
| AQo | 30 |
| QTs | 28 |

これ以外の非ペアはコール中心です。KQs（32）, AQs（35）でも vs UTG はコールが主流です（GTO では 3-bet 頻度が混合）。

**ペア**: 99+ は 3-bet（push）、22〜88 はコール。

### vs BTN: 3-bet 対象（14 手前後）

| カテゴリ | 手 |
|---------|---|
| 高 Broadway offsuit | AQo+, AJo, ATo, KQo |
| Broadway suited | ATs+, AJs, KTs 等 |
| suited connector ブラフ | JTs, T9s, T8s, 98s |
| K-ブロッカーブラフ | K7s, K6s |
| Axo 9 | A9o |

**ペア vs BTN**: 22 以上すべて 3-bet（push）。

---

## C-5 SB コール 19 手（SBR=25 vs BTN）

暗記推奨のコール手一覧です。

| # | ハンド | カテゴリ |
|---|--------|---------|
| 1 | K5s | K-suited |
| 2 | K6s | K-suited |
| 3 | K7s | K-suited |
| 4 | K8s | K-suited |
| 5 | K9s | K-suited |
| 6 | KJs | K-suited |
| 7 | 76s | suited connector |
| 8 | 87s | suited connector |
| 9 | 97s | suited connector |
| 10 | 98s | suited connector |
| 11 | T8s | suited connector |
| 12 | J8s | suited connector |
| 13 | Q8s | suited connector |
| 14 | Q9s | suited connector |
| 15 | KTo | Broadway offsuit |
| 16 | QTo | Broadway offsuit |
| 17 | QJo | Broadway offsuit |
| 18 | A7s | Ax 例外 |
| 19 | A8s | Ax 例外 |

**記憶補助**: 「K-suited 6 手 + suited connector 8 手（76s〜Q9s）+ Broadway offsuit 3 手 + Ax 例外 2 手」。

---

## C-6 UTG vs BB 3-bet: shove 6 手（SBR=25）

3-bet を受けた UTG がオールイン（shove）する確定 6 手です（T_shove=27）。

| ハンド | スコア |
|--------|--------|
| KK | 38 |
| AKs | 37 |
| AKo | 32 |
| AQs | 35 |
| AQo | 30 |
| QQ? | 34 |

**正確には**: KK（38）, AKs（37）, AQs（35）, QQ（34）, AKo（32）, AQo（30）のうち、T_shove=27 を超える手は上記すべてが該当します。ただし実測では「shove 6 手」は主に KK/AKs/AKo と AA（コールで価値引き出し）の構成です。AA はコールで対応することが多い点に注意してください。

**コール確定（T_call=22 以上かつ T_shove 未満）**: QQ, JJ, TT, AQs, AQo 等 22 手前後。

---

## C-7 BTN スクイーズ確定（UTG/HJ 絡み: T_sq=27〜28）

| ハンド | スコア |
|--------|--------|
| AA | 41 |
| KK | 38 |
| AQs | 35 |
| KQs | 32 |
| AKo | 32 |
| JJ | 32 |
| AQo | 30 |
| QJs | 30 |

T_sq=28 → スコア 28 以上が確定スクイーズ圏。AKs（37）, AQs（35）, QQ（34）, JJ（32）, KQs（32）, AKo（32）, AQo（30）, JTs（28）が代表です。

---

## C-8 境界ハンドまとめ表（一覧）

最も重要な「SBR=25、UTG、オープン境界」の境界ハンドを一枚でまとめます。

| ハンド | スコア | UTG T_open=22.5 判定 | 備考 |
|--------|--------|---------------------|------|
| KQs | 32 | OK | 確定 |
| 98s | 24 | OK | 確定 |
| K8s | 24 | OK | 確定 |
| T8s | 24 | OK | 確定 |
| Q8s | 23.5 | OK | 88% オープン |
| J8s | 23.5 | OK（式上） | 実際は fold 寄り |
| A3s | 23 | OK（式上） | 54% fold（境界） |
| KJo | 25 | OK | 確定 |
| QJo | 25 | OK | 確定 |
| ATo | 27 | OK | 確定 |
| A9o | 23 | OK（式上） | 実際は fold（Axo 問題） |
| KTo | 22.5 | 境界 | 約 50% オープン |
| K7s | 22 | NG | 72% fold |
| 97s | 22 | NG | fold |
| 87s | 21 | NG | fold |
| A8o | 22 | NG | fold |

---

> **付録 C まとめ**
>
> - SBR=25 UTG: スーテッドは K8s 以上 OK（K7s は NG）。K7s と K8s がスコア 2 差で分かれる
> - BTN（T_open=14）: ほぼ全手 OK。スコア 14 未満のゴミ手のみ fold
> - SBR=12 SB: 6 手（AKs/AQs/KQs/QJs/KJs/JTs）+ AA/KK は limp trap。push 厳禁
> - BB vs UTG: 3-bet 確定 4 手のみ（AKs/AKo/AQo/QTs）。残りはコール主体
> - SB コール: 19 手（K-suited + suited connector mid + Broadway offsuit + Ax 例外 2 手）
> - UTG shove（vs BB 3-bet）: KK/AKs/AKo が中心の 6 手前後
