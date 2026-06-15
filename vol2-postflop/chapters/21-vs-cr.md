# 第 21 章　vs CR (CR ディフェンス) — turn donk vs CR は真逆

## 21.1 vs CR の定義

**vs CR** (CR ディフェンス) = hero が cbet 後に相手から **チェックレイズ**
または **ドンクベット** を受けた場面です。 「DEF」 という旧称は廃止しました。

Score 公式上は **pot = 2** → **+ 4 × 2 = +8** (3BP と同じ補正)。

```
Score = Grid + DV × mult + 2 × oc + 8 − 2 × bs
```

## 21.2 vs CR の typical setup

- BTN open → BB call → flop → BTN cbet → BB raise → BTN ?
- pot は cbet 倍率分膨らんでいます (SRP × 1.5〜2 程度)
- effective SPR: 3-5 (ミディアムSPR)

## 21.3 turn donk vs turn CR は真逆

データ検証で判明した重要事実です。

| シナリオ | 相手の range 構造 | hero defense 推奨 |
|---|---|---|
| **vs CR** (check raise 受け) | opp value-heavy (46% strong) | tight defense、 fold 多用 |
| **vs Donk** (ドンクベット受け) | opp air-heavy (54-61% weak) | wide defense、 call 多用 |

同じ pot 種別 (vs CR = 2、 vs Donk = 2) なのに **相手のレンジ構造が真逆**です。

### audit データ

| 状況 | opp_strong% | opp_weak% |
|---|---:|---:|
| BTN flop cbet → BB CR | 46% | 22% |
| BB flop donk (BTN は preflop raiser) | 18% | 54% |
| BTN turn check → BB bet (donk) | 14% | 61% |

→ CR は「相手が強い signal」、 Donk は「相手が弱い signal」です。

## 21.4 Score 公式での扱い

本書は両者を **pot=2 (+8)** で同一扱いしています。 これは以下の理由です。

- audit で「pot 軸を vs CR / vs Donk に分離しても性能向上せず」
- 例外 3 (ミドル × wet × turn × vs CR → fold) と例外 4 のような **個別例外** で差を吸収

例外 3 は vs CR の「相手 value-heavy」 を反映しています。 例外 4 は 3BP × wet × turn の bluff
catch (vs Donk と似た構造)です。

## 21.5 vs CR audit セグメント

- n = 34,092 (22.1%)
- huge%: 1.45%
- 主な huge: DEF T_raise=49 補正 + ex9/ex10 Turn CR fold 不足
- vs CR 総合精度: **80.5 Grade S** (208K hands 検証)

## 21.6 vs CR の board family 別注意

### dry × vs CR

- TP+: Grid 38 + 8 = 46 → **DEF T_raise=49** → call (GTO CALL 61%)
  - ⚠️ DEF 文脈では T_raise=49 を使います。 Score=46 < 49 → call
- TP+ × dry × turn × vs CR: **ex10 でさらに fold** に変換します (GTO FOLD 62.3%)
  - turn だけ「fold まで下げる」 ポイントに注意してください (flop/river は call)
- ミドル × dry: Grid 18 + 8 = 26 → call (踏ん張ります)
- TP+/ミドル × dry × turn × vs CR: **ex9 で fold** に変換します (TP+ GTO FOLD 56%、 ミドル GTO FOLD 71.5%)
  - ⚠️ vs Donk には ex9/ex10 を適用しません

### wet × vs CR

- ミドル × wet × turn × vs CR: 例外 3 で **fold 強制**です
  - 公式 Score: Grid 10 + 0 (turn DV=0 if no draw) + 8 − 4 (bs med_100) = 14 → call
  - 実 GTO: fold (相手 value-heavy)
- 2P+ は Grid 23 + 8 = 31 → call (slowplay)
- エアは Grid 1 + 8 − 4 = 5 → fold

### paired × vs CR

- ミドル × paired: Grid 40 + 8 = 48 → **DEF T_raise=49** → call (GTO CALL 91-97%)
  - ⚠️ DEF 文脈では T_raise=49 を使います。 Score=48 < 49 → call
- TP+ × paired = 10 + 8 = 18 → call (trip 警戒)

## 21.7 ドンクベット受け (vs Donk) の扱い

vs Donk も pot = 2 として同じ式で扱いますが、 相手の range が異なるため少し工夫が必要です。

- vs Donk × エア: 公式上は fold 寄りですが、 実 GTO は call 寄りです (bluff catch)
- vs Donk × TP+: 公式上も実 GTO も call です (donk への TP+ は call 維持)

**DEF 閾値補正 (vs Donk でも適用):**
- ミドル × paired: Score=48 → T_raise=49 → call (旧 raise 誤判定を解消します)
- TP+ × dry: Score=46 → T_raise=49 → call (旧 raise 誤判定を解消します)

**vs Donk 専用例外:**
- **ex11**: 2P+ (trips/FH/quads) × paired × river × vs Donk → raise (value)。 Donk の river range は弱いため GTO RAISE 100%です

## Cash/MTT note

vs CR の真逆現象 (turn donk vs turn CR で BTN defense 真逆) は Cash と MTT で共通です。 例外 3 (ミドル × wet × turn × vs CR → fold) も両者に適用します。

## この章で覚える項目 (6 items)

1. vs CR = check raise/donk 受け、 pot 値 = 2、 Score +8 補正
2. vs CR は opp value-heavy (相手 46% strong)
3. vs Donk は opp air-heavy (相手 54-61% weak、 真逆)
4. **DEF 閾値補正**: vs CR/Donk では T_raise = **49** を使います (通常 43 から引き上げ)
5. **ex9**: (アンダーペア/TP+) × dry × turn × vs CR → fold (⚠️ vs Donk 不可)
6. **ex10**: TP+ × wet × turn × vs CR → fold (⚠️ vs Donk 不可)
7. **ex11**: river × vs Donk × trips以上 × paired → value raise
