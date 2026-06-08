# SPR gradient 分析 — 同 board (Ks7d2c) × SPR 変化

BTN 攻撃 IP 側、SRP/3BP/4BP × Cash 50/100bb で同 K72 rainbow flop を probe。
SPR が連続的に変化したとき、tier ごとの cbet 行動がどう変わるか。

## 概要 (SPR 昇順)

| spot | SPR | sizing | 総 cbet% |
|---|---:|---|---:|
| 4bp_flop | 1.3 | 11.3bb | 53.7% |
| 3bp_flop | 3.4 | 4.5bb | 43.7% |
| depth_50_flop | 8.0 | 4.6bb | 33.0% |
| depth_100_flop | 16.0 | 1.9bb | 50.2% |

## tier × SPR の cbet 頻度

| tier | SPR 1.3 | SPR 3.4 | SPR 8.0 | SPR 16.0 |
|---|---:|---:|---:|---:|
| ナッツメイド | 0% | 0% | 0% | 0% |
| ストロング | 4% | 41% | 69% | 96% |
| ツーペア | 18% | 80% | 97% | 83% |
| トップペア以上 | 61% | 70% | 68% | 61% |
| ミドルペア | 73% | 49% | 43% | 55% |
| エア | 41% | 46% | 46% | 44% |

## 観察

### tier ごとの SPR sensitivity

- **ナッツメイド**: SPR1.3=0% → SPR3.4=0% → SPR8=0% → SPR16=0% (安定)
- **ストロング**: SPR1.3=4% → SPR3.4=41% → SPR8=69% → SPR16=96% (★ SPR1→3 で急変)
- **ツーペア**: SPR1.3=18% → SPR3.4=80% → SPR8=97% → SPR16=83% (★ SPR1→3 で急変)
- **トップペア以上**: SPR1.3=61% → SPR3.4=70% → SPR8=68% → SPR16=61% (安定)
- **ミドルペア**: SPR1.3=73% → SPR3.4=49% → SPR8=43% → SPR16=55% (★ SPR1→3 で急変)
- **エア**: SPR1.3=41% → SPR3.4=46% → SPR8=46% → SPR16=44% (安定)

### MATCHA SPR 4 段階との対応

- **オールイン (<1)**: 本データになし (4BP turn / 3BP river 等が該当)
- **ロー (1-3)**: SPR 1.3 (4BP flop) 側 — value heavy, jam-or-fold
- **ミディアム (3-7)**: SPR 3.4 (3BP flop) 側 — value/bluff 分離
- **ディープ (>7)**: SPR 8/16 (SRP) 側 — protect range, 多様な sizing

実 GTO で tier ごとに SPR の sensitivity が異なる:
- ナッツメイド/ストロング: SPR↑で常に高頻度ベット (value 一貫)
- ツーペア/トップペア: SPR↓ (3BP/4BP) で頻度↑ (jam 価値)、SPR↑ (SRP) で控えめ
- ミドルペア/エア: SPR↑ で頻度↑ (multi-street bluff 可、ブラフ余地)