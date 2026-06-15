# 第 15 章　SRP — 標準 100bb

## 13.1 SRP の定義

**SRP** (Single Raised Pot) = プリフロップで 1 回のレイズ + 1 回のコールで成立した
ポットです。 最も基本的な pot 種別となります。

Score 公式上は **pot = 0** ですので、 公式そのままで対応します:

```
Score = Grid[カテゴリ][board] + DV × mult + 2 × oc − 2 × bs
```

(4 × pot = 0 のため省略可能)

## 13.2 audit 全体での SRP の位置

audit (n = 154,216) の SRP セグメントは以下の通りです:

- n = 43,660 (28.3%)
- huge%: 2.62%
- 主な huge: 例外 1 (TP+ × wet × flop × SRP → fold) と例外 2 (2P+ × wet × river × SRP → raise)

huge な判定は例外 1〜2、 5 でほぼ救済されます。

## 13.3 BTN open vs BB call を基準とした全 spots audit

最も頻出の SRP spot 構造は以下の通りです:

- BTN open (2.5bb) → BB call → flop
- effective stack: ~97.5bb
- pot: 5.5bb
- SPR: ~17 (ディープSPR)

このセットアップで GTO ソルバー 解析を回した spot 群が SRP audit の主体となります。

## 13.4 SRP 特有のパターン

### dry board での polarization

K-7-2 / A-7-2 / K-8-3 など dry board では:
- BTN cbet 大多数 (40-50%、 small 33% 多用)
- TP+ は Grid 38 で強気な raise/call
- エアは bluff frequency 中心

### wet board での check 多用

T-9-8 / 7-6-5 など wet board では:
- BTN cbet 低頻度 (28-35%、 大サイズ時のみ)
- 2P+ は slowplay 寄り (Grid 23、 raise 閾値跨ぎにくい)
- 例外 5 (2P+ × wet × flop × SRP → fold) で 2P 過大評価を修正します

### paired board での wide bet

K-K-2 / 7-7-2 / J-J-5 など paired board では:
- アンダーペア × paired = 40 で強気
- TP+ × paired = 10 で慎重
- 例外なし (paired は概ね公式マッチ)

## 13.5 SRP × turn 以降の注意点

SRP の turn では effective SPR がまだ 5-8 と高めです:

- turn DV mult = 2 (Rule of 2)
- アンダーペアの value は flop より低下します (turn で TP の確定度↑)
- 例外 3 (ミドル × wet × turn × vs CR → fold) は SRP では発動しません (pot vs CR)

SRP の river では DV = 0 で made hand 勝負となります:

- TP+ × dry = 38 (river でも最大値の一つ)
- 2P+ × wet × river × SRP → 例外 2 で **raise** 強制 (公式 pred call)

## 13.6 SRP 内 huge% 内訳

SRP の huge spots は主に以下の通りです:

1. **TP+ × wet × flop × SRP → fold** (例外 1、 n=350)
2. **2P+ × wet × river × SRP → raise** (例外 2、 n=258)
3. **2P+ × wet × flop × SRP → fold** (例外 5、 n=125)
4. その他 (n < 100)

→ SRP の huge は **wet board** に集中しています。 dry / paired board の SRP は huge% < 1% です。

## Cash/MTT note

SRP は Cash/MTT 共通公式です。 ただし pot 初期サイズは: Cash 5.5bb / MTT 6.0-7.5bb (ante 影響)。 flop SPR: Cash 100bb=17 / MTT 100bb=16 / MTT 25bb=4.2。 詳細は第 21 章をご参照ください。

## この章で覚える項目 (3 items)

1. SRP = Single Raised Pot、 pot 値 = 0
2. dry board は cbet 多用、 wet は慎重、 paired は wide
3. SRP の huge は wet board に集中 (例外 1 / 2 / 5 で救済)
