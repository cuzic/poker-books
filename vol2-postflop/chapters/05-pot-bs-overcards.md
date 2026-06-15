# 第 5 章　pot / bs / overcards の値

## 5.1 pot — 4 段階

ポット種別を表す軸です。値は係数 4 倍されて Score に加算されます。

| pot | 略称 | 値 |
|---|---|---:|
| Single Raised Pot | **SRP** | 0 |
| vs Check-Raise / vs Donk Bet | **vs CR** | 2 |
| 3-bet Pot | **3BP** | 2 |
| 4-bet Pot | **4BP** | 4 |

**4 × pot** の効果：
- SRP: 0 (基準)
- vs CR / 3BP: +8
- 4BP: +16

4BP は Score を +16 押し上げる **巨大な上方補正**です。これが 4BP で
「アンダーペアでもコール / 2P+はレイズ強行」を引き起こす源です。

## 5.2 bs (ベットサイズ) — 6 段階

相手の bet サイズです。値は係数 −2 倍されて Score から引かれます。

| key | 名前 | pot 比 | 値 |
|---|---|---|---:|
| small_33 | スモールベット | ~33% | 0 |
| med_75p | ミディアムベット | ~75% | 1 |
| med_100p | ミディアムベット | ~100% | 2 |
| overbet | オーバーベット | 125-150% | 3 |
| overbet_185 | オーバーベット | ~185% | 4 |
| allin | オールイン | 100% effective | 5 |

**−2 × bs** の効果：
- small_33: 0 (補正なし)
- med_75: −2
- med_100: −4
- overbet: −6
- overbet_185: −8
- allin: −10

## 5.3 overcards (oc)

hero の 2 枚のうち、board の最高 rank より上の枚数です。値 0 / 1 / 2 です。

```
oc = (hero card 1 > max(board) ? 1 : 0)
   + (hero card 2 > max(board) ? 1 : 0)
```

### 具体例

| board 最高 rank | hand | oc |
|---|---|---:|
| Kh 7c 2d (K-high) | AhTh | 1 (A のみ) |
| Kh 7c 2d | AsAd | 2 (A 2 枚) |
| Kh 7c 2d | QJs | 0 (両方 K 以下) |
| Th 9h 4c (T-high) | KQs | 2 |
| Th 9h 4c | 88 | 0 |

### overcards の意味

A-K-Q-J など overcards は将来 turn / river で TP+ に化ける **潜在 equity** です。
2 × oc で Score に小幅加算され、マージナルな call/fold で「コール側」に動かす役を担います。

特に「Kh 7c 2d で AhTh → エア + oc 1 → Score 微増」のように、raw エア でも
overcard でわずかに救済される設計になっています。

## 5.4 各係数の意味

| 係数 | 値 | 意味 |
|---|---:|---|
| `+4 × pot` | 4 | ポット拡大の上方補正 (4BP で +16) |
| `−2 × bs` | −2 | bet サイズの不利補正 (overbet で −6) |
| `+2 × oc` | 2 | overcard の潜在 equity (+2 〜 +4) |

係数 4 / 2 / 2 は **暗算しやすい小整数** に最適化されています (付録 B 参照)。これらは
Optuna で連続値最適化したあと、暗算可能な整数に丸めた結果です。

## 5.5 pot × bs の interaction を加法分解した理由

「4BP × overbet は特殊なはず」と思うかもしれません。audit では：

- interaction matrix (pot 4 × bs 6 = 24 cells) を試してみました → 集約過剰で性能悪化
- 加法分解 (`4 × pot − 2 × bs`) → 最良

つまり pot と bs は **独立**に効きます。これは pot 種別が「相手のレンジ構造を
決める」、bs が「ポットオッズ」を決める、という別次元の情報だからです。

## 5.6 実例：全要素を合わせた計算

board: Kh 7c 2d (dry)、hand: KsQs (TP+)、street: flop、pot: 3BP、bs: overbet (140%)、oc: 0

- カテゴリ = TP+
- Grid[TP+][dry] = **38**
- DV = 0 (made TP+、draw なし)
- 2 × oc = 0
- 4 × pot = 4 × 2 = **+8**
- −2 × bs = −2 × 3 = **−6**
- Score = 38 + 0 + 0 + 8 − 6 = **40**
- 14 ≤ 40 < 43 → **コール**

(GTO best: call、公式 pred も call、一致)

## Cash/MTT note

pot/bs/oc の係数は Cash/MTT 共通です。ただし **pot 値の解釈**：MTT は ante 込みで実 pot が +10-25% 大きく、bs の bbeq 解釈もそれに応じて厚くなります。

## この章で覚える項目 (3 items)

1. pot 値: SRP=0 / vs CR=2 / 3BP=2 / 4BP=4 (係数 4)
2. bs 値: small=0 / med=1〜2 / overbet=3〜4 / allin=5 (係数 −2)
3. overcards: 0/1/2 のうち board 最高超え枚数 (係数 2)
