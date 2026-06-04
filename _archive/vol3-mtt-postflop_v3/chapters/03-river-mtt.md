# 第06章 River defense 詳細 — MTT 50bb (真allin aware、v15)

MTT 50bb の River defense は **真の all-in** (raise 不可) が頻発するため、Cash と本質的に異なる判断が必要です。
v15 公式 (bucket + 真allin 判定) で huge_loss を 0.038 BB まで圧縮 — 全公式中最高精度。

## MTT 50bb River の特殊性

MTT 50bb River は以下の特徴があります。

- SPR ~1 (Cash の River の 1/3)
- **真の all-in が頻発** (残スタックでこれ以上 raise できない状態でのベット)
- サイズの選択肢: med_100p (R13.7) と allin (R35.5)
- **bucket 軸が完全に支配** + 真allin の意味論考慮

これらの結果、Cash の River v14 を MTT 50bb に適用すると huge_loss 0.316 BB (Cash 100bb での 0.388 と類似)、しかし **MTT 専用 v15** に切り替えると **0.038 BB** という劇的改善が得られます (88% 削減)。

## 「真の all-in」の意味

Cash 100bb と MTT 50bb の **"all-in"** は意味が違います。

**all-in の意味論的差**

| | Cash 100bb | MTT 50bb |
|---|-----------|----------|
| ベットコード | R89.6 | R35.5 |
| サイズ (pot 比) | 421% pot | 235% pot |
| 残スタック | まだあり | **ゼロ** |
| Raise オプション | あり (理論的に R100+ で raise 可) | **なし** (真の all-in) |
| set/straight × allin | RAISE (raise option を使う) | **CALL のみ** |
| こちらの判断軸 | bucket + RAISE の余地 | bucket + call/fold の二択 |

MTT 50bb で all-in を受けたら、こちらの選択は **call か fold の二択** のみ。raise option が消えるため、Cash の "強いハンド × allin = RAISE" 戦略は適用できません。

代わりに「相手の all-in レンジに対して **eqp > 65% で call、≤ 65% で fold**」というシンプルな判断になります。

## MTT 50bb River v15 公式

```
MTT 50bb River defense v15:

── Nut hands (最優先) ──
mv = quads → RAISE
mv = fullhouse ∧ bs ≠ overbet → RAISE
mv = fullhouse ∧ bs = overbet → CALL (slowplay, raise 余地少)

── vs all-in (真 allin、R35.5、raise 不可) ──
best_hands ∧ eqp > 0.85 → CALL
bf ∈ dry ∧ mv ∈ {set, trips, straight, flush} → CALL
good_hands ∧ mv ∈ {straight, flush, trips} → CALL
bf = monotone ∧ mv = flush → CALL
dynamic ∧ mv = top_pair ∧ bucket ∈ {good, weak} → CALL (Cash と同じ)
その他 → FOLD

── mv override ──
mv ∈ {straight, flush, trips} → CALL (絶対強さ)
mv = top_pair ∧ bf ∈ dry ∧ bs ∈ {overbet, med_100p} → CALL

── vs med_100p (raise option あり) ──
best_hands ∧ eqp > 0.93 → RAISE
best_hands → CALL
good_hands → CALL
weak_hands ∧ bs ∈ {overbet, med_100p}:
  dynamic ∧ mv = two_pair → CALL (bluff catch)
  else → FOLD
weak_hands → CALL
trash_hands → FOLD
```

## v15 の検証結果

**MTT 50bb River defense 公式比較**

| 公式 | accuracy | mean loss | huge_loss |
|------|---------|-----------|-----------|
| always_FOLD | 65% | 3.53 BB | (large) |
| always_CALL | 18% | 6.42 BB | (large) |
| Cash v14 を MTT に適用 | 84.2% | 0.267 | 0.316 |
| **MTT v15 (真allin aware)** | **92.3%** | **0.040** | **0.038** ⭐⭐⭐⭐ |

MTT v15 は huge_loss 0.038 BB — **全公式中最高精度**。Cash v14 比で **8.3 倍の改善**。

**改善の本質**: Cash v14 は all-in vs best_hands = RAISE と判断するが、MTT の真 all-in では RAISE option がない → CALL すべき。この 1 つの違いだけで huge_loss が劇的に変わる。

## Cash v14 vs MTT v15 の違いを 1 ルールで言うと

Cash v14 と MTT v15 の最重要な違いは **「allin に対する best_hands の挙動」** です。

- **Cash v14**: best_hands + allin + eqp > 0.85 → **CALL** (RAISE option を使わない、bucket-based)
- **MTT v15**: best_hands + allin → **CALL** (eqp threshold なし、raise option もそもそもない)

実は Cash の "all-in" は厳密には all-in ではなく **421% pot overbet (R89.6)**。この overbet を受けて raise する option はあるが、最大 raise が all-in (R100+) になるので実質的には RAISE か CALL の二択。MTT の場合は最初から all-in 状態なので CALL か FOLD のみ。

**判断のシンプル化**: MTT の真 all-in は「bucket でこれ以上ないほど明確に判断できる」。eqp 細かい数値は要らず、bucket だけで 90%+ 正解。

## 実戦例: MTT 50bb River defense

**例 1: River K-7-2-3-A (dry) で AKo (TP-A)、相手が真 all-in 235% pot**

- bucket: TP-A = weak/good (相手の all-in レンジに対して微妙)
- mv override: TP × dry × allin → CALL (bluff catch)
- **アクション: CALL** (Cash と同じ結論だが理由が違う: Cash は bucket-based、MTT は単純 mv override)

**例 2: River T-9-8-2-J (dynamic で straight 完成) で 6♣7♣ (straight)、相手が真 all-in**

- bucket: straight on dynamic = good (相手の all-in レンジに対して中程度)
- mv override: mv = straight → CALL
- **アクション: CALL** (絶対強さの straight で call、相手のナッツ flush 可能性は受け入れる)

**例 3: River K-7-2-3-A で 4♠4♦ (low pair)、相手が真 all-in 235%**

- bucket: low_pair on dry = trash
- mv override: 対象外
- 標準: trash × all-in → **FOLD**
- **アクション: FOLD**

**例 4: River で fullhouse、相手が overbet (R20 程度、まだ raise 可能なサイズ)**

- Rule 1: mv = fullhouse ∧ bs ≠ overbet → RAISE...
- 待って、これは "overbet" カテゴリーかどうか。R20 が pot 30 BB の 67% なら med、200% なら overbet
- 仮に overbet とすると: Rule 1 の条件「bs ≠ overbet」に該当しない → CALL (slowplay)
- **アクション: CALL** (slowplay、相手の raise option を引き出す)

## MTT 50bb 全体の所見

MTT 50bb の Turn (v9) + River (v15) を組み合わせると、防御側の判断公式は以下のシンプルさになります。

**Turn (SPR ~3、二極化サイズ):**

- bucket だけで判断
- 強メイドは overbet 時に RAISE (commit)、small 時に CALL
- 強ドローは non-monotone なら call、monotone は fold

**River (SPR ~1、真 allin 多):**

- bucket + mv override (絶対強さの straight/flush/trips は無条件 call)
- 真 allin は eqp > 0.65 で CALL、それ以下 FOLD
- paired board / monotone board の特殊扱い

**全体メッセージ**: MTT 50bb は「bucket とサイズの 2 つで 90% 決まる、絶対強さで残り 10% を補正」というシンプルな世界。

## 次の章へ

Cash と MTT の River defense を学びました。次の ch07 では **River attack** に進み、polarized 戦略の詳細を解説します。攻撃側は Cash/MTT 共通で扱えます。
