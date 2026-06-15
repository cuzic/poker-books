# 第 26 章　Cash vs MTT chipEV のパラメータ差

> 本書 MATCHA Score は **Cash 100bb と MTT chipEV (25/50/100/200bb)** で同一公式
> として最適化されています。 ただし両者には **構造的パラメータ差** があり、
> 同じ Score 値でも「実 EV 解釈」 が微妙に異なります。 本章ではその差分を 8 つの
> 観点で整理し、 暗算公式の運用上の注意点を 1 ページの早見表にまとめます。

## 26.1 本章の位置づけ

MATCHA Score 公式そのもの (Grid + DV + oc + pot − bs) は Cash と MTT chipEV で
**同形** です。 154,216 spots の audit でも両者統合で検証されています。

ただ「同じ Score 値が実 EV でも同じ意味か」 を厳密に問うと、 以下 7 つの
パラメータが両者で異なります。

| パラメータ | Cash 100bb | MTT chipEV |
|---|---|---|
| ante | なし | 10-12.5% of BB (typical) |
| BB ante | なし | 1bb (pre-pot) |
| rake | あり (2.5-5%、 cap あり) | なし (chip 計算のみ) |
| open-raise sizing | 2.5bb 標準 | 2.0-2.25bb (ante 影響) |
| 3-bet sizing | 9-11bb | 6-8bb (effective SPR 維持) |
| 4-bet sizing | 21-26bb | 16-20bb |
| pot 初期サイズ | 5.5bb (SRP) | 6.5-7.5bb (ante 込み) |

これら 7 つの差が **bs (bet size) 解釈・SPR 計算・range 構造** を介して
MATCHA Score の運用に影響します。

## 26.2 ante の影響 — pot サイズと bs 解釈

### ante 込み pot

MTT では **ante 12.5% of BB** (例: 100bb の MTT で 12.5% ante = 0.125bb × 9 players
= 1.125bb)、 BB 1bb、 SB 0.5bb が pre-pot。 100bb effective、 BTN open 2.25bb、
BB call の SRP 初期 pot です:

- Cash 100bb: SB 0.5 + BB 1.0 + BTN 2.5 + BB 1.5 = **5.5bb**
- MTT 100bb (ante 12.5%): ante 1.125 + SB 0.5 + BB 1.0 + BTN 2.25 + BB 1.25
  = **6.125bb** (+11%)

ante が大きい late MTT (20-25% of BB) では更に +20-25%、 最大 **+25-50%** の
pot 増加になります。

### bs 解釈の調整

「33% bet」 は **pot に対する比率** ですが、 ante 込み pot では実 ante を含めて
**eq 必要量** が増えます。

| spot | bet サイズ | hero 必要 eq (pot odds) |
|---|---|---:|
| Cash SRP、 33% cbet (pot 5.5、 bet 1.8) | 1.8bb call | **25%** (pot odds 25.0%) |
| MTT 25bb、 33% cbet (pot 6.1、 bet 2.0) | 2.0bb call | **25%** (同じ) |

pot odds 自体は同一 (33% bet → 25% eq) ですが、 **実効 SPR が違う** ため
turn 以降の implied odds が変わってきます。

→ MATCHA Score 上は **bs は同じ key (small_33 = 0)** で扱います。 ただし MTT では
ante 込みで「実効 pot」 が大きく、 bs の bbeq 解釈が +10-20% 厚くなります。

## 26.3 BB ante の影響 — BB defense 広げ / SB squeeze 絞り

late MTT の **BB ante** ルール (= 1bb pre-pot から BB が拠出) では pot に 1bb
追加される構造で、 以下のような戦略変化が起きます。

### BB defense range wider

BB が pre-pot に拠出済 → 「降りるとロス」 のマージン拡大 → **BB の defense
レンジ wider 化** になります。

- Cash 100bb (no ante): BB vs BTN 2.5bb open call range 約 38%
- MTT 100bb (BB ante): BB vs BTN 2.0bb open call range 約 **45%** (+7pp)
- Cash 100bb での BB defense は MATCHA Score 上 t_call=14 でも、 MTT では
  実質 t_call=12 程度 (wider) です。

### SB squeeze tighter

逆に SB は steal 失敗の損が増える (steal 試行で BB が wider defend) → SB squeeze
range tighter になります。

- Cash: SB 3-bet vs BTN open 約 12%
- MTT BB ante: SB 3-bet vs BTN open 約 **8%** (-4pp)

→ MATCHA Score 上は SRP/3BP の pot 値は同じですが、 **MTT BB ante 時は SB 寄り
3BP の頻度が下がります**。

## 26.4 rake の有無 — Cash thin value 効率↓

Cash では rake (typically 2.5-5%、 cap $3-5) が pot から引かれます。 これが
**thin value spots** に重く効きます。

### thin value threshold

「flat call の EV ≈ 0.05 BB」 の thin spot では:

- Cash: rake 0.03 BB → 実 EV = 0.02 BB (微 +EV)
- MTT chipEV: 0.05 BB (純 chip 計算)

→ Cash では「微 +EV の薄いコール」 は rake で潰される可能性が大きいです。 MATCHA Score
上では t_call=14 を **t_call=15-16 程度に上げる** のが Cash 厳密運用の指針です。

### check 寄りの判断

「thin value vs check」 が微妙な spot では:

- river × dry × トップペア以上 × 弱いキッカー (TPWK) で薄 value bet:
  - Cash: rake 込みで EV 0 付近 → check が正解
  - MTT: 純 chip で微 +EV → 薄 bet

MATCHA Score 上は Grid + 補正で 38 → 36 程度に微減 (= 「raise しない、 call
止まり」 になりがち) で対応します。

## 26.5 open-raise sizing 差 — SPR 計算への影響

- **Cash 100bb**: BTN open 2.5bb 標準
- **MTT 100bb** (ante 12.5%): BTN open 2.25bb 標準
- **MTT 25bb** (ante 12.5%): BTN open 2.0bb (min-raise 寄り)

flop での effective SPR は以下のようになります。

| spot | open | SRP pot | flop SPR (BB call) |
|---|---:|---:|---:|
| Cash 100bb | 2.5bb | 5.5 | 17.7 |
| MTT 100bb (ante) | 2.25bb | 6.0 | 16.3 |
| MTT 50bb (ante) | 2.25bb | 6.0 | 7.9 |
| MTT 25bb (ante) | 2.0bb | 5.5 | **4.2** |

SPR は MTT で若干低く、 **SPR=3 反転点 (第 12 章)** を Cash より早く跨ぐ傾向があります。

→ MATCHA Score 上は bs 解釈に直接影響します (MTT では同じ「33% bet」 でも実 bb が
小さいため)。 short stack MTT では bs の判定を厳しく (1bb の bet も 25% over なら
med_75p 扱い) しましょう。

## 26.6 3-bet / 4-bet sizing 差 — 3BP/4BP の SPR

- Cash 3-bet IP: 9bb (3.6× of 2.5bb open)
- Cash 3-bet OOP: 11bb (4.4×)
- MTT 3-bet IP: 6-7bb (2.7-3.1× of 2.25bb)
- MTT 3-bet OOP: 8bb (3.6×)

3BP での flop SPR は以下の通りです。

| spot | 3-bet | 3BP pot | flop SPR |
|---|---:|---:|---:|
| Cash 100bb 3BP IP | 9bb | 19.5 | 4.6 |
| MTT 100bb 3BP IP (ante) | 6.5bb | 14.5 | 6.2 |
| Cash 100bb 4BP IP | 21bb | 43 | 1.8 |
| MTT 100bb 4BP IP | 16bb | 33.5 | **2.5** |

→ Cash の方が SPR がやや低く、 4BP では Cash の方が「commitment 寄り」、
MTT の方が「post-flop play 余地あり」 になります。 MATCHA Score の 4BP pot 値 (4) は両者
共通で audit 済です。

## 26.7 MTT 早期 / 中期 / 後期 — chipEV の純度

MTT chipEV モデルが厳密に成り立つのは **early-mid stage** に限られます。

| stage | stack | chipEV ≈ \$EV か | MATCHA Score |
|---|---|---|---|
| 早期 (Level 1-5) | 100bb+ | ほぼ純 chipEV | そのまま適用 |
| 中期 (Level 6-15) | 50-100bb | chipEV メイン、 ICM 微影響 | そのまま (補正 +0〜+1) |
| 後期 (Level 16-25) | 25-50bb | chipEV と \$EV 乖離開始 | 補正 +1〜+3 |
| 賞金圏直前 (バブル) | 10-30bb | **乖離最大** | 第 23 章 (+5〜+10) |
| FT (3-9 left) | 多様 | 乖離大 | 第 22 章 (+3〜+8) |

→ 中期までは MATCHA Score そのまま、 後期から ICM 補正を意識しましょう。 賞金圏直前は
本書 (chipEV) の対象外で、 将来 Vol2.5 で対応する予定です。

## 26.8 MATCHA Score の Cash/MTT 別解釈

### bs 値の解釈差

Cash と MTT で **bs key は同じ** (small_33 = 0、 ..., allin = 5) ですが、
ante の有無で「pot に対する比率」 と「実 bb 損失」 が乖離します。

- Cash 33% bet: pot 5.5 の 33% = 1.8bb
- MTT 33% bet (ante 12.5%): pot 6.1 の 33% = 2.0bb

bs key 自体は変わらず、 実効 bb 単位の差は **±10%** 程度です。

### SPR 計算の差

MTT では ante 込み pot で SPR が **数% 低下** します。 SPR=3 反転点を跨ぐ判定は
慎重に (例: Cash で SPR 3.2 → MTT で SPR 2.9 になり、 set の bet 頻度が逆転) しましょう。

### Grid と pot/oc の係数

Grid 12 cells は両者で同一です。 pot 値 (SRP=0 / vs CR=2 / 3BP=2 / 4BP=4) も同一です。
**MATCHA Score は 154,216 spots 統合最適化** で Cash と MTT 同公式に揃えました。

## 26.9 Cash/MTT 差分 1 ページ早見表 (暗記推奨)

| 項目 | Cash 100bb | MTT chipEV |
|---|---|---|
| 公式 | MATCHA Score (同形) | MATCHA Score (同形) |
| ante | なし | 10-25% of BB |
| BB ante | なし | 1bb (late stage) |
| rake | あり (実 EV −0.03 BB) | なし |
| open sizing | 2.5bb | 2.0-2.25bb |
| 3bet sizing | 9-11bb | 6-8bb |
| 4bet sizing | 21-26bb | 16-20bb |
| SRP pot | 5.5bb | 6.0-7.5bb |
| flop SPR (SRP) | 17 | 16 (100bb) / 4 (25bb) |
| 4BP flop SPR | 1.8 | 2.5 |
| BB defense range (vs BTN open) | 38% | 45% (BB ante) |
| SB 3-bet vs BTN | 12% | 8% (BB ante) |
| t_call 微補正 | +0 (default) | +0 (default) |
| t_raise 微補正 | +0 | +0 |
| Cash thin value 補正 | t_call +1〜+2 (rake 込) | 不要 |
| ICM 補正 (後期 MTT) | 不要 | +1〜+3 (後期) |
| バブル補正 | 不要 | +5〜+10 (第 23 章) |
| 例外 11 ルール | 共通適用 | 共通適用 |

## 26.10 Cash 専用の運用 tip

- **rake 重い場 (online micro stake)**: t_call +2 (thin value 削除)
- **rakeback / VIP 還元あり**: t_call 補正不要 (実 rake はほぼ無)
- **live cash (rake high % / no cap)**: t_call +3 (薄 value 危険)
- **deep stack (Cash 200bb+)**: 第 26 章補正 (t_call +2)

## 26.11 MTT 専用の運用 tip

- **早期 (chipEV stage)**: MATCHA Score そのまま
- **中期 (50-100bb)**: そのまま (補正 +0〜+1)
- **後期 (25-50bb)**: 補正 +1〜+3 (慎重に)
- **賞金圏直前 (バブル)**: 第 23 章補正 (+5〜+10)
- **FT (3-9 left)**: 第 22 章補正 (+3〜+8)
- **PKO (バウンティ込み)**: 本書対象外 (将来 Vol2.5)

## 26.12 この章の結論

MATCHA Score は **Cash 100bb と MTT chipEV を 1 つの公式で扱える** ことを 154,216
spots audit で確認しました。 7 つのパラメータ差は **実効 bb 単位で ±10-20%** の
微差で、 公式の運用上は **bs と SPR の解釈** に注意するだけで対応可能です。

例外 11 ルール (第 9 章)、 短/深スタック補正 (第 18-19 章)、 ICM 補正 (第 21-22 章)
はすべて Cash と MTT で共通適用してください。

## Cash/MTT note: 本章自体が Cash/MTT 差分章

本章は Cash/MTT 差分を扱う専用章のため、 差分は本文全体で詳述しています。 他章の Cash/MTT
note からは本章を参照する形にしています。

## この章で覚える項目 (4 items)

1. MATCHA Score 公式は Cash と MTT chipEV で同形
2. 主要パラメータ差: ante / BB ante / rake / open-raise sizing / 3-bet sizing / SRP pot / 4BP SPR
3. Cash 補正: rake 重時 t_call +2、 live cash +3
4. MTT 補正: 後期 +1〜+3、 バブル +5〜+10、 FT +3〜+8
