# 第02章 Flop defense 詳細 — mv-based 公式と例外集

Flop defense は SPR が高く mv (絶対強さ) 軸が支配的です。
Vol2 の標準マトリックスを基盤に、GTO 検証で huge_loss を 0.49 BB まで圧縮する詳細公式を解説します。

## Flop defense 公式 v7 — 4 ルール体系

Flop defense は mv_cat (made hand category) と board_family を主軸に判断します。Vol2 の 5×4 マトリックスに 3 つの補正を加えた形が **Flop defense v8** (旧 v7 を改良) です。GTO 検証で huge_loss を **84% 削減** (always_CALL 0.87 BB → v8 0.14 BB) します。

```
Flop defense v8 (改良版):

Rule 1 (FOLD): mv ∈ {no_made_hand, ace_high, king_high}
              AND dv ∈ {no_draw, twocards_bdfd, onecard_bdfd, gutshot}
  → 完全 air + 弱ドロー (BDFD/gutshot) も FOLD
  ★ 旧 v7 は dv = no_draw のみだったが、weak draws も FOLD が GTO

Rule 2 (FOLD): mv ∈ {low_pair, third_pair} AND dv = no_draw
              AND board ∈ {dry_high, low_dry, dynamic_2tone}
  → 弱メイドは dry/2-tone 板でドミネイト多

Rule 3 (RAISE): mv = overpair
  → range advantage 持ち、value raise

Rule 4 (default): CALL
  → 上記以外は全て CALL (set/2P+ も slowplay = CALL)
```

### Rule 1 の重要拡張: weak_draw も AIR 扱い

旧 Vol3 v7 では「AIR + no_draw → FOLD」のみでしたが、検証で **AIR + weak_draw (gutshot/BDFD) も FOLD** が GTO であることが判明しました。

理由:
- **Gutshot は 4 outs (8.5% by river)** — Flop で受けて river まで届く確率約 16%
- **BDFD は 4.2% by river** — 実質ほぼ無価値
- これらの drawing equity では cbet の pot odds (25%) を満たさない
- **drawing equity + showdown value を合算しても call が EV マイナス**

この拡張により Vol3 v8 の huge_loss が **0.29 → 0.14 BB (-52%)** と劇的に改善します。

## なぜ overpair 以外 RAISE しないのか

Vol2 でも触れましたが、**set / 2P / trips は flop で RAISE せず CALL** が GTO です。

**理由 1: slowplay の価値**

強いハンドで raise すると相手の continue range が weak/bluff だけになる。call のまま turn/river まで連れていく方が、相手のブラフバレル + value bet を全部キャッチできて EV 高い。

**理由 2: range advantage の維持**

flop で set を持っていても、相手の cbet range は wide。raise すると相手は bluff を諦める。call すれば相手の bluff range もそのまま turn まで延命する。

**理由 3: overpair は例外**

overpair (AA, KK on T-7-2) は **絶対的に強い** + **多くの draws に対して vulnerable** という二面性。slowplay すると相手の turn card で逆転される確率が無視できない (例: KK on T-7-2 で turn A で AKx に negate される)。

この 3 つの理由で「**set/2P/trips は slowplay の方が EV 高い**」「**overpair だけは flop raise で value 取りに行く**」という GTO 結論になります。

## low_pair の特殊扱い

Rule 2 の **low_pair / 3rd_pair × no_draw × dry/2-tone → FOLD** は、Vol2 でも紹介した重要例外です。

**対象 board 詳細:**

- **dry_high**: K-7-2, A-9-4 など high card + 連結なし + ペアなし
- **low_dry**: 8-4-3, 9-6-2 など low card + 連結なし
- **dynamic_2tone**: T-9-8 with 2 same suit (連結 + flush draw 完成可能)

これらの板で low_pair (22 on K-7-2 など) は:

- 相手の cbet range は **high card 中心 or pocket pair**
- こちらの 22 のキッカーは極端に弱く、ほぼ確実に負け
- showdown まで連れていっても 22 で勝てる確率が低い

**dry_high の場合の loss**: 補正 1 を適用しないと huge_loss が 1.2 BB/decision まで膨らむ (low_pair × dry_high × no_draw cell)。補正 1 で 0.5 BB に圧縮できます。

## monotone board の例外

Vol2 では触れなかった例外: **monotone board** (3 枚同スート) では mv の意味が変わります。

**monotone 例: K♠7♠2♠**

- 自分の hand が ♠ (フラッシュ完成) → set より強い
- 自分が ♠ ナシの set → ナッツではない (相手の make flush に負ける可能性)
- 自分が ♠ ナシの TP → ほぼ負け確定

**Flop defense v7 の monotone 補正:**

```
monotone board での mv 解釈:
  - ナッツ flush (A♠ + ♠) → S (Strong) として扱う
  - non-nut flush → M (Medium) 扱い
  - non-flush の set / 2P → M 扱い (ナッツではない警戒)
  - non-flush の TP → W 扱い (一段下げる)
```

この補正で monotone board の huge_loss を更に 0.1 BB 削減できます。Vol2 では深追いせず標準マトリックス通りに扱っていましたが、Vol3 では補正します。

## paired board の特殊扱い

**paired board** (K-K-7, 7-7-2 など) では mv の階層が変わります。

**paired 例: K-K-7**

- **トリップス (K のキッカー持ち、例 KQ)** → 通常の set 相当の S
- **アンダーペア (例 88, 99, TT)** → M に近い (相手の K キッカーレンジに勝つ可能性あり)
- **K-high キッカー (例 K♥Q♦ on K-K-7)** → 上記トリップスと同じ
- **オーバーペア (例 AA)** → 通常の S だが、相手のトリップス警戒で慎重に
- **7 のトリップス (相手のキッカーは弱い)** → S だが kicker 戦が起きる

**Flop defense v7 paired 補正:**

```
paired board:
  - underpair → M に格上げ (showdown value あり)
  - 弱い kicker の trips → S だが overcards 警戒 (turn A で逆転リスク)
  - パワーバランス: BB のレンジは K のキッカーが少ない → BTN 有利
```

Vol2 では「W (low_pair / 3rd_pair) on dry → FOLD」と単純化しましたが、paired board は dry とは違う扱いになります。

## 実戦例: Flop defense 詳細

**例 1: K-7-2 rainbow で 8♣8♥ (underpair)、相手が cbet 33%**

- mv 判定: 88 on K-7-2 = underpair → **M (Medium)**
- サイズ: 33% → **m**
- 標準マトリックス: M × m = **CALL**
- 補正チェック: 88 は low_pair ではなく underpair なので Rule 2 適用外
- **アクション: CALL** (Vol2 と同じ結論)

**例 2: K-7-2 rainbow で 2♣2♦ (low_pair = ボトムペア)、相手が cbet 50%**

- mv 判定: 22 = ボトムペア → **W (Weak)**
- サイズ: 50% → **m**
- 標準マトリックス: W × m = CALL
- 補正チェック: Rule 2 適用 (low_pair × no_draw × dry_high) → **FOLD**
- **アクション: FOLD** (補正で override)

**例 3: K♠7♠2♠ (monotone) で K♣Q♦ (TP no flush)、相手が cbet 67%**

- mv 判定: TP on monotone → 標準 M、monotone 補正で **W** (一段下げる)
- サイズ: 67% → **m**
- 標準マトリックス: W × m = CALL
- monotone 補正: TP without flush で W 扱い → そのまま CALL (W × m は CALL)
- **アクション: CALL** (ただし慎重に、turn で相手が pressure かけてきたら fold 寄り)

**例 4: K♠7♠2♠ (monotone) で A♠5♠ (nut flush)、相手が cbet 67%**

- mv 判定: nut flush → **S (Strong)**
- サイズ: 67% → **m**
- 標準マトリックス: S × m = **CALL** (slowplay)
- monotone 補正: nut flush は S のまま (S × m = CALL)
- **アクション: CALL** (slowplay、turn で相手の barrel を待つ)

## huge_loss セルランキング (top 5)

Vol3 の検証データから、Flop defense で huge_loss が大きい top 5 セル (Cash 100bb) は以下です。

**Flop defense huge_loss top 5**

| # | mv × board × dv | n | 標準マトリックス | GTO 実際 | mean loss |
|---|------------------|---|-------------------|----------|-----------|
| 1 | low_pair × dry_high × no_draw | 96 | CALL | **FOLD 89%** | 1.28 BB |
| 2 | third_pair × dry_high × no_draw | 100 | CALL | **FOLD 87%** | 1.21 BB |
| 3 | low_pair × dynamic_2tone × no_draw | 69 | CALL | **FOLD 84%** | 1.40 BB |
| 4 | third_pair × dynamic × no_draw | 91 | CALL | **FOLD 71%** | 0.82 BB |
| 5 | low_pair × low_dry × no_draw | 60 | CALL | **FOLD 75%** | 1.18 BB |

これら top 5 すべて **「弱ペア × no_draw × 何らかの板 → 実際は FOLD」** のパターンです。Rule 2 (補正 1) でこれらを **全部 FOLD に override** すれば huge_loss を大きく削減できます。

**削減効果:**

- Top 5 セル合計 loss: **約 1.2 BB/decision × 416 行 = 約 500 BB の損失機会**
- Rule 2 で FOLD に切替 → **70% 以上の損失を防げる** (一部は CALL が正解なケースを犠牲にするが、net positive)

## 次の章へ

Flop defense の詳細公式が見えました。次は **Turn defense** に進みます。ch03 で Cash 100bb の Turn (mv+dv 軸)、ch04 で MTT 50bb の Turn (bucket 軸) を扱い、SPR-axis-switching を実例で示します。
