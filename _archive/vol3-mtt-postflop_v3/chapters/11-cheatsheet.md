# 第12章 早見表 — 全公式 + 例外 30+ (2 ページ印刷推奨)

Vol3 の全公式・例外・SPR 別判断フローを 2 ページに圧縮した実戦参照シートです。
Vol2 早見表と組み合わせて使用することを想定しています。

## SPR で公式を選ぶ (中核ルール)

```
実戦中の公式選択フロー:

1. 現在の SPR を計算 (残スタック ÷ 現在のポット)
2. 公式選択:
   - SPR ≥ 7  → Cash v8 (mv+dv 軸) or Vol2 マトリックス
   - SPR 3-7 → Cash v14 / MTT v9 (bucket + mv 軸)
   - SPR ≤ 2 → MTT v15 (bucket + 真allin 軸)
3. 公式適用 → アクション決定
```

## Flop defense v7 (mv-based、全 depth 共通)

```
Rule 1 (FOLD): air ∧ no_draw → FOLD
Rule 2 (FOLD): {low_pair, 3rd_pair} ∧ no_draw
              ∧ board ∈ {dry_high, low_dry, dynamic_2tone}
              → FOLD
Rule 3 (RAISE): overpair → RAISE
Rule 4 (default CALL): else
```

## Cash 100bb Turn defense v8 (mv+dv 軸、SPR ~7)

```
vs overbet (≥100% pot):
  O1: weak_mv (air/A-K-high/弱中ペア/2nd) ∧ weak_draw (no/BDFD/gutshot) → FOLD
  O2: air ∧ FD ∧ dry_high → FOLD
  O3: air ∧ OESD ∧ dynamic → FOLD
  O4: TP ∧ no_draw ∧ dynamic → FOLD
  default: CALL

vs medium (≤67% pot):
  M1: air ∧ no_draw → FOLD
  M2: dynamic ∧ 弱メイド (excl 2nd_pair) ∧ 弱ドロー → FOLD
  M3: dynamic ∧ OESD ∧ 弱メイド (excl 2nd_pair) → FOLD
  default: CALL

vs small (≤33%): Vol2 マトリックス通り
```

## MTT 50bb Turn defense v9 (bucket 軸、SPR ~3)

```
best_hands:
  vs overbet ∧ 強メイド (set/2P+/straight/flush+) ∧ 非monotone → RAISE
  else → CALL
good_hands: 同上
weak_hands:
  vs overbet:
    強ドロー (OESD/FD/combo) ∧ 非monotone → CALL
    else → FOLD
  vs small → CALL
trash_hands:
  vs overbet → FOLD
  vs small:
    強ドロー ∧ 非monotone → CALL
    else → FOLD
```

## Cash 100bb River defense v14 (bucket + mv override、SPR ~3)

```
Nut hands:
  quads → RAISE
  fullhouse:
    bs ≠ overbet → RAISE
    bs = overbet → CALL (slowplay)

vs near-all-in (Cash の R89.6, raise option あり):
  best_hands ∧ eqp > 0.85 → CALL
  dry + set/trips/straight/flush → CALL
  good + straight/flush/trips → CALL
  monotone + flush → CALL
  dynamic + TP + good/weak bucket → CALL (反直感)
  else → FOLD

mv override (絶対強さ):
  mv ∈ {straight, flush, trips} → CALL
  TP × dry × overbet|med_100p → CALL (bluff catch)

bucket-based:
  best: eqp > 0.96 → RAISE, else CALL
  good → CALL
  weak: overbet:
          dynamic ∧ 2P → CALL
          else → FOLD
        med_100p → FOLD
        else → CALL
  trash → FOLD
```

## MTT 50bb River defense v15 (bucket + 真allin、SPR ~1)

```
Nut hands:
  quads → RAISE
  fullhouse:
    bs ≠ overbet → RAISE
    bs = overbet → CALL

vs 真 all-in (R35.5、raise 不可):
  best_hands ∧ eqp > 0.85 → CALL
  dry + set/trips/straight/flush → CALL
  good + straight/flush/trips → CALL
  monotone + flush → CALL
  dynamic + TP + good/weak bucket → CALL
  else → FOLD

mv override: (Cash v14 と同じ)

vs med_100p (raise option あり):
  best ∧ eqp > 0.93 → RAISE
  best ∧ {straight/flush/trips} → RAISE
  else best → CALL
  good ∧ {2P/straight/flush} ∧ dynamic → RAISE
  else good → CALL
  weak ∧ {straight/flush/trips} → CALL
  weak ∧ {TP/2P/2nd/3rd} ∧ eqp > 0.55 → CALL
  else weak → FOLD
  trash → FOLD
```

## River attack v7 (Cash/MTT 共通)

```
Rule 1 (CHECK): 強メイド (set/trips/straight/flush+) ∧ board ∈ dry → slowplay
Rule 2 (CHECK): TP ∧ board ∈ dynamic → vulnerable
Rule 3 (BET value): {TP, overpair, 2P, set, trips, straight, flush+}
                  (Rule 1, 2 で先に CHECK 判定済みは除外)
Rule 4 (BET bluff): {no_made_hand, king_high}
Rule 5 (CHECK default): else (medium SDV / A-high)
```

## Cash vs MTT の判断: 30+ 例外パターン

### Flop defense の Cash/MTT 共通例外

- low_pair × no_draw × dry_high → FOLD
- low_pair × no_draw × low_dry → FOLD
- low_pair × no_draw × dynamic_2tone → FOLD
- 3rd_pair × no_draw × dry_high → FOLD
- 3rd_pair × no_draw × dynamic → FOLD
- overpair → RAISE (Rule 3)
- monotone board + non-nut flush → M 扱い (一段下げる)
- paired board + underpair → M 扱い (一段上げる)

### Cash 100bb Turn 詳細例外

- vs overbet: air ∧ FD × dry_high → FOLD
- vs overbet: air ∧ OESD × dynamic → FOLD
- vs overbet: TP ∧ no_draw × dynamic → FOLD
- vs medium: dynamic + 弱メイド (excl 2nd) + 弱ドロー → FOLD
- vs medium: dynamic + OESD + 弱メイド (excl 2nd) → FOLD
- vs medium: 2nd_pair + gutshot → CALL (除外条件)

### MTT 50bb Turn 詳細例外

- best/good × overbet × 強メイド × 非monotone → RAISE (commit)
- monotone board での RAISE 抑制 → CALL
- trash × small × 強ドロー × 非monotone → CALL (drawing odds)

### Cash 100bb River 詳細例外

- straight/flush/trips → bucket 関係なく CALL (mv override)
- TP × dry × overbet → CALL (bluff catch)
- TP × dry × med_100p → CALL
- dynamic × TP × overbet (weak bucket) → CALL (bluff catch)
- dynamic × no_made × med_100p → CALL (反直感 bluff catch)
- fullhouse × overbet → CALL (slowplay)
- quads → RAISE

### MTT 50bb River 真allin 例外

- best × allin → CALL (eqp 関係なく、raise 不可)
- set/straight/flush × allin → CALL (raise option なし)
- trash × allin → FOLD
- weak × allin × eqp > 0.65 → CALL

## 判断フロー (毎回 5-10 秒で実行)

1. 現在の **SPR** を計算 → 公式選択
2. **street** を確認 (flop/turn/river)
3. 自分のハンドの **mv** (made hand category) を判定
4. ドローがある場合 **dv** を判定 (flop/turn のみ)
5. 可能なら **bucket** (相対強さ) を推定 (river では特に重要)
6. 相手の **bet size** をカテゴリー化 (s/m/l/o)
7. **board family** を確認 (dry_high/low_dry/dynamic/paired/monotone)
8. 公式を適用 → アクション決定
9. 例外リストをチェック → 該当すれば override

## Vol2 / Vol3 / Vol4 への発展

Vol3 で扱った Tier 2 詳細公式 (huge_loss 0.04-0.39 BB) は、Cash 100bb と MTT 50bb をほぼカバーします。残る領域:

- **MTT 25bb / 100bb / 200bb の詳細** — 現サブスクで詳細データ取得不可、将来研究課題
- **ICM 補正** — 専門ツール (ICMIZER, HRC) で個別計算
- **相手タイプ別エクスプロイト** — Vol4 (テル) で扱う

Vol3 で 80% 以上習得した方は **Vol4 (テル・エクスプロイト)** に進むことを推奨します。Vol4 では「相手がルーズな場合は閾値をどう変えるか」など、本書 (GTO 基準) の上に補正を加える方法を学びます。

## 終わりに

Vol3 では **SPR-axis-switching** という中核理論を学び、Cash 100bb と MTT 50bb の判断公式を比較しました。最も重要なメッセージは:

> **「Cash か MTT か」ではなく「SPR がどれだけ低いか」が公式を変える**

この理論的洞察があれば、Vol3 で扱わない depth (Cash 50bb, MTT 75bb など) でも自力で適切な公式を選択できるはずです。

ポーカーは終わりのないゲームですが、本書の公式群は **GTO 整合 92%+** という現時点で最も精緻な簡易公式集の一つです。実戦で活用してください。
