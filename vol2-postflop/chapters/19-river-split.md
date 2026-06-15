# 第 19 章　RIVER — split rule v6 (役で value bet + 役なしで bluff bet)

## 19.1 RIVER は polarized strategy が最適

RIVER の構造的特徴としては、**役確定済み (draw 完成不可)** で、 equity が 0% / 100% に二極化します。 これにより GTO は **polarized strategy** (両端 bet、 中間 check) が最適となるのです。

## 19.2 RIVER 専用ルール (Score 公式無視)

```
① top_pair 以上 (= overpair / 2P / set / trips / straight / flush / FH / quads / SF) → value bet
② no_made_hand (= 完全に役なし、 high card にもならない) → bluff bet ★
③ それ以外 (ace_high / king_high / second_pair / low_pair etc.) → check
```

## 19.3 完全 air が 74% bet する GTO 理論の data 確証

| 場面 | bet 率 |
|---|---:|
| no_made_hand 全体 | 62.9% |
| × dry | 56.1% |
| × paired | 64.2% |
| **× wet** | **74.2%** ★ |

→ **「役なし、 draw なし、 call されたら 100% 負け確定」 の hand を 74% bet** が GTO 解です。 これは相手の bluff catcher を fold させるための **bluff frequency 維持**という考え方です。

教科書 (Janda、 Acevedo) が定性的に語ってきた polarization 理論を、 174K hands で初めて定量化した data です。

## 19.4 効果 (data 検証、 段階別)

| ルール | acc | avg loss BB/hand |
|---|---:|---:|
| baseline (Score 公式) | 45.05% | 0.384 |
| v1: top_pair 以上 → bet のみ | 65.52% | 0.086 |
| **v6: + no_made_hand → bluff** | **70.13%** ★ | **0.042** (-50%) |
| 参考 v8: + second_pair × paired/wet | 71.24% | 0.040 |

v1 → v6 で **+4.6pp acc / -52% loss** という改善が見られます。 v8 はさらに微改善ですが、暗算負荷を考えると v6 を採用するのがおすすめです。

## 19.5 中間役 (ace_high, low_pair, second_pair) は check

これらは「**showdown value 保持 hand**」という特徴があります：

| 役 | river bet 率 | 解釈 |
|---|---:|---|
| ace_high | 14.9% | showdown まで進めば call 勝ち |
| king_high | 24.1% | 同上 (相手の queen_high 等に勝つ) |
| low_pair | 12.2% | bluff catcher、 相手の bluff に call |
| second_pair | 49.0% | boundary (paired board のみ bet 寄り) |

これらを bet すると「相手の TP+ に call され負け」で大損してしまいます。 「中間役は **check で showdown へ**」が GTO 最適という原則を覚えておくことがおすすめです。

## 19.6 直感的解釈

RIVER は equity が 0% / 100% に近づく street です：

- **強 hand (made)** = value bet (相手の bluff catcher から call を取ります)
- **完全 air** = bluff bet (call されたら負け確定ですが、 fold equity が大きいのです)
- **中間 hand** = check (showdown で勝つか相手の bluff に call します)

これは **「両端 bet、 中間 check」** の polarized strategy という形です。 flop/turn では merged だった戦略が river で完全に二極化します。

## 19.7 効果 (data 検証)

| 指標 | Score 公式のまま | RIVER split v6 |
|---|---:|---:|
| Acc | 45.1% | **70.1%** (+25pp) ★★ |
| avg loss BB/hand | 0.384 | **0.042** (-89%) ★★ |
| Cov | 49.8% | **93.6%** (D cell 7 → 0) ★ |
| MQS v6 | 58.0 | **76.6** (+18.6) |
| **MQS v7 (実害)** | - | **88.2** ★★ |

→ **公式の中で最大の改善幅** です。 5 context 中で RIVER だけ Score 公式が崩壊していたのが、 split rule で完全復活します。

## この章で覚える項目 (4 items)

1. **役確定 (top_pair 以上) → 確定 value bet**
2. **役なし完全 air → 確定 bluff bet** ← 直感に反するが GTO 最適
3. 中間役 (ace_high, low_pair etc.) → **check で showdown へ**
4. RIVER acc 45 → 70% (+25pp)、 avg loss -89%、 公式中最大の改善
