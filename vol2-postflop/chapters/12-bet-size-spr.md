# 第 12 章　Bet Sizing と SPR — 2 段階と反転点

## 12.1 Bet Sizing は 2 段階で 90% カバー

Audit の結果、bet サイズは 2 種類に簡略化しても 90% カバーできることが確認されています:

| 新 2 段階 | 範囲 | freq (全 boards) |
|---|---|---:|
| **small 33%** | 1.5-2 bb cbet | 45-50% |
| **over 100%+** | 5-10 bb cbet | 30-35% |
| medium (75-100%) | mid | < 10% |

**medium (50-75%) は実 GTO ではほぼ未使用**です。

実戦では「small 33% と overbet 100%+ のどちらか」 を覚えれば
ほぼ事足りてしまいます。

## 12.2 board family 別の dominant sizing

| board family | dominant sizing | freq |
|---|---|---|
| dry MERGED (K-7-2、 paired_low) | small 33% | 40-50% |
| connected wet (T-9-8、 6-5-4) | large 100%+ | 2-6% (低頻度・大サイズ) |
| broadway dry | small 33% | 40-50% |
| low_dry / mid_dry | large 100%+ | 33% |

「dry → small bet 多用、 wet → 高頻度 check + 時々 large bet」 という基本パターンを押さえておくと、判断がシンプルになります。

## 12.3 SPR 4 段階

| SPR 段階 | 範囲 | 典型 |
|---|---|---|
| オールインSPR | < 1 | 4BP、 short stack push |
| ローSPR | 1-3 | 3BP、 短スタック |
| ミディアムSPR | 3-7 | SRP の turn 後 |
| ディープSPR | > 7 | Cash 100bb の flop、 200bb |

## 12.4 SPR=3 が GTO 戦略反転点

同じ board (Ks 7d 2c) × SPR variation の cbet 頻度を実測値で見てみましょう:

| カテゴリ | SPR 1.3 (4BP) | SPR 3.4 (3BP) | SPR 8 (Cash50) | SPR 16 (Cash100) |
|---|---:|---:|---:|---:|
| 2P+ (set) | **4%** | 41% | 69% | **96%** |
| ツーペア | 18% | 80% | 97% | 83% |
| トップペア以上 | 61% | 70% | 68% | 61% |
| アンダーペア | **73%** | 49% | 43% | 55% |
| エア | 41% | 46% | 46% | 44% |

### SPR=3 を境に逆転

- **SPR < 3 (4BP / shallow)**: 強い手 slowplay、 アンダーペア突撃 (set 4% / ミドル 73%)
- **SPR > 3 (deep)**: 強い手 fastplay、 アンダーペア 抑制 (set 96% / ミドル 55%)

これは Score 公式上では `4 × pot` で表現されます:
- 4BP (pot=4) → Score +16、 アンダーペアが call 閾値を超えやすくなります
- SRP (pot=0) → Score 補正なし

## 12.5 4BP でアンダーペア 73% > set 4% の逆転現象

ちょっと意外かもしれません。**4BP では set より アンダーペアの方が bet 頻度が高い**のです。

理由としては:
- 4BP は SPR < 2、 effective stack/pot 比が極小
- set は slowplay 価値が大きい (相手の 3BP/4BP コミット range は wide で trap が効く)
- アンダーペアは「迷う」 範囲、 GTO は jam-or-fold で jam 寄せになります
- 結果として ミドル 73% bet vs set 4% slowplay となるわけです

この逆転を Score 公式は **「2P+ × 4BP」 で +16 補正 + slowplay 隅**
で巧みに表現しています。 Score 値そのものは set が高いのですが、 アンダーペアでも 4BP 補正で
call 閾値を悠々越えるので強気の判断に出られます。

## 12.6 4BP は別ゲーム (Tier A) の証拠

4BP の特殊性は audit でも明確に分離されます。

- Cash 4BP と MTT 100bb 4BP は **同構造** (audit で確認されています)
- SRP / 3BP / vs CR とは別系統です

Score 公式は 1 つで対応でき、`4 × pot = +16` で吸収されます。

## Cash/MTT note

Bet Sizing 2 段階 (small 33% / over 100%) は Cash/MTT 共通です。 SPR 4 段階の境界も共通ですが、 MTT は ante 込みで SPR が数% 低く、 SPR=3 反転点を Cash より早く跨ぐようになります (詳細は第 21 章をご参考ください)。

## この章で覚える項目 (4 items)

1. Bet sizing は実質 2 段階 (small 33% / over 100%+) で 90% カバー
2. SPR 4 段階 (オールイン / ロー / ミディアム / ディープ)
3. SPR=3 が GTO 戦略反転点
4. 4BP で アンダーペア 73% > set 4% の逆転 (4BP は別ゲーム)
