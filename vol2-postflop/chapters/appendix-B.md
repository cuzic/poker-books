# 付録 B. 旧来理論との橋渡し早見表 ★暗記補助

> 本付録は **第 13 章 (旧来のポーカー理論との橋渡し)** を 1 ページに凝縮した
> 早見表です。 既知の理論にアンカーすることで MATCHA Score の各要素を「再構成」
> として吸収できます。 詳細は第 13 章 をご参照ください。

## B.1 DV と Rule of 4/2 早見

| draw | outs | DV 値 | flop (×3) | turn (×2) | river (×0) |
|---|---:|---:|---:|---:|---:|
| combo (FD + SD) | 12-15 | **4** | +12 | +8 | 0 |
| FD / OESD | 8-9 | **3** | +9 | +6 | 0 |
| gutshot / BDFD (2 枚) | 4 / 2 | **1** | +3 | +2 | 0 |
| no draw | 0-1 | 0 | 0 | 0 | 0 |

**Rule of 4/2**: outs × 4% (flop) / outs × 2% (turn) です。 OESD (8 outs) flop で
32% 完成 ≈ DV 3 × 3 = 9 points です。

## B.2 古典ボード 7 → MATCHA 3 分類

| 古典分類 | 例 | MATCHA |
|---|---|---|
| Dry rainbow / Dry connected (低 gap) | K-7-2 / 7-5-2 | **dry** |
| Wet / Monotone / Two-tone (connected) | T-9-8 / 9h7h3h | **wet** |
| Paired high / Paired low | K-K-7 / 7-7-2 | **paired** |

**判定**: paired → wet → dry の順序で判定します。

## B.3 旧 6 階層 Hand Strength → MATCHA 4 カテゴリ

| 旧 6 階層 | MATCHA 4 カテゴリ | 根拠 |
|---|---|---|
| ナッツメイド (FH / quads / SF) | **2P+** | 4BP で 2P 以上同挙動 |
| ストロング (set / flush / straight) | **2P+** | dry で value bet 同一 |
| ツーペア | **2P+** | paired で slowplay 同様 |
| トップペア以上 (TP / overpair) | **トップペア以上 (TP+)** | 維持 |
| アンダーペア (2nd / 3rd / underpair) | **アンダーペア** | 維持 |
| エア (high / king / ace high) | **エア** | 維持 |

**4BP huge%**: 「2P+」 統合により精度が大幅に向上しています。

## B.4 SPR 切り分け (古典 vs MATCHA)

| 古典 (Flynn 2007) | MATCHA 4 段階 | 範囲 | 典型 |
|---|---|---|---|
| Low SPR (< 1) | **オールインSPR** | < 1 | 4BP、 short push |
| Mid SPR (1-3) | **ローSPR** | 1-3 | 3BP、 短スタック |
| High SPR (3-7) | **ミディアムSPR** | 3-7 | SRP turn 後 |
| Very high SPR (> 7) | **ディープSPR** | > 7 | Cash 100bb flop、 200bb |

**SPR=3 反転点**: 同 K72 × SPR variation で set 4% → 96% (+92pp) です。

## B.5 Pot Odds と Score 閾値

| bs key | pot 比 | pot odds (必要 eq) | MDF |
|---|---|---:|---:|
| small_33 | 33% | **25%** | 60% |
| med_75p | 75% | 30% | 67% |
| med_100p | 100% | **33%** | 67% |
| overbet | 125-150% | 35-38% | 67-75% |
| overbet_185 | 185% | 41% | 73% |
| allin | varies | 33-50% | 67-100% |

**Score 閾値の意味**:
- Score 14 (call) = 必要 eq 25-33% (small-med bet で defend)
- Score 43 (raise) = 必要 eq 50%+、 value range 確定

## B.6 Range Morphology 用語対応

| 古典 (Janda / Sweeney) | MATCHA レンジ分布 | 例 board |
|---|---|---|
| polarized | **2 極化型** | dry board の cbet range |
| linear (merged) | **混在型** | wet board、 中位 hand 多 |
| capped | **密集型** | wet board の call back range |

MATCHA は morphology を board × カテゴリ × Grid 値に **吸収**しています。

## B.7 Sklansky Hand Groups → カテゴリ

| Sklansky 群 | preflop 例 | postflop カテゴリ (hit 時) |
|---|---|---|
| 群 1-2 (AA / KK / AKs) | premium | **2P+** |
| 群 3-4 (JJ / TT / AQs / KQs) | strong | **トップペア以上** |
| 群 5-7 (mid SC / mid suited) | playable | **アンダーペア** |
| 群 8 以下 (rag) | weak | **エア** |

**Theory of Poker (Sklansky 1987)**: Score 公式が「相手のカードを見ながらプレイ」
と「知らずにプレイ」 の EV ギャップを **整数近似で最小化** (avg loss 0.3587 BB) します。

## B.8 bs 6 段階と古典 sizing

| MATCHA bs key | 古典 sizing | 意味 | Score 補正 |
|---|---|---|---:|
| small_33 | range cbet (33%、 protection) | range adv 利用 | 0 |
| med_75p | medium polar (75%) | value heavy + bluff | −2 |
| med_100p | polar (100%、 nut adv) | range adv + nut adv | −4 |
| overbet | super polar (125-150%) | 相手 capped、 polar | −6 |
| overbet_185 | very super polar (185%) | over-bluff 含む | −8 |
| allin | commit (all-in) | jam-or-fold | −10 |

## B.9 1 ページ早見の使い方

1. **draw 判定** → E.1 で DV × mult を計算します
2. **board 判定** → E.2 で 3 タイプに集約します (dry/paired/wet)
3. **hand 判定** → E.3 で 4 カテゴリ に集約します (エア/ミドル/TP+/2P+)
4. **SPR 確認** → E.4 で 4 段階を確認します、 SPR=3 反転点に注意しましょう
5. **bs/pot 確認** → E.5 で必要 eq を確認し、 E.8 で sizing 解釈を確認します
6. **Score 計算** → Grid + DV×mult + 2×oc + 4×pot − 2×bs で計算します
7. **閾値比較** → ≥14 call / ≥43 raise / 14 = 25% eq で比較します

本付録 + 付録 A (公式 + Grid 早見) +  で実戦運用に必要な
全リファレンスが揃います。

## B.10 詳細は第 13 章へ

各対応の **data 駆動根拠** (audit 結果、 比較表) は第 13 章で詳述しています:

- 13.1 Outs と Rule of 4/2
- 13.2 古典ボード 7 → MATCHA 3 集約マトリックス
- 13.3 6 階層 → MATCHA 4 カテゴリ への集約
- 13.4 SPR 理論 (Flynn) と SPR=3 反転点
- 13.5 Pot Odds と MDF (公式閾値の意味づけ)
- 13.6 Range Morphology (Janda / Sweeney)
- 13.7 Sklansky Hand Groups (1976)
- 13.8 Theory of Poker (Sklansky 1987)
- 13.9 Bet Sizing 理論 (modern GTO)
