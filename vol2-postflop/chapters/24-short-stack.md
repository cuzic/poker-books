# 第 24 章　短スタック (≤ 25bb)

## 24.1 短スタックでの Score 公式の挙動

short stack (effective ≤ 25bb) では SPR が自動的に低下します：

| typical | stack | pot 初期 | flop SPR |
|---|---:|---:|---:|
| Cash 100bb SRP | 100 | 5.5 | ~17 |
| MTT 50bb SRP | 50 | 5.5 | ~8 |
| MTT 25bb SRP | 25 | 5.5 | **~3.5** |
| MTT 15bb SRP | 15 | 5.5 | ~1.7 |

短スタックでは **ディープSPR → ミディアムSPR → ローSPR** に自動的に下がっていき、
SPR=3 の戦略反転点をしばしば跨ぎます。

## 24.2 short stack の committed range

SPR < 3 では「ペア以上 = コール」が GTO 推奨となります (committed range)：

- アンダーペア以上 → all-in 受けでもコールするのがよいです (例：K72 で 55、effective 20bb)
- エア + draw → ふつう fold ですが、SPR < 2 の場合は jam 候補になります

Score 公式上では **4 × pot** が小さいため pot 補正が効かない一方で、short stack では
**bs (実際の bet サイズ) が pot に対して大きく出る**ため −2 × bs が効きすぎる
ことがあります。

→ short stack では bs を厳密に判定することがおすすめです (例：8bb pot に 5bb cbet = 62% → med_75p 扱い)。

## 24.3 MTT 25 での Score 閾値補正

MTT 25bb のような short stack では、経験的に閾値を以下のように補正するとよいです：

- T_call：14 → **12** (call を広くして、committed range で fold しすぎないようにする)
- T_raise：43 → **40** (raise 閾値をやや下げて、jam-or-call を促進する)

ただしこれは大まかな目安です。厳密には例外ルールで対応します。

## 24.4 short stack での例外ルール調整

例外 11 ルール (第 9 章) のうち、short stack で挙動が変わるものをご紹介します：

- 例外 1 (TP+ × wet × flop × SRP → fold)：short stack では Score 18 + DV ≈ 24 で fold せず call するようになります。short stack は committed だからです。
- 例外 2 (2P+ × wet × river × SRP → raise)：short stack でも有効で、むしろ jam 化していきます
- 例外 3 (ミドル × wet × turn × vs CR → fold)：short stack では call を維持します (committed)

→ short stack では **例外 1 と 3 を無効化**するのが指針です。

## 24.5 ICM 連携 (短スタック × バブル)

short stack × バブルでは Score 公式に追加補正が必要になります (第 23 章 参照)。

- バブルでは t_call +5〜+10 (fold を厳しくする)
- short stack × バブルの short stack は **「fold 寄りの jam-or-fold」** となります

詳細は第 6 部 (ICM/MW) で扱います。

## Cash/MTT note

short stack は **MTT 主体の概念**です (Cash 25bb は cap game でのみ登場します)。本章の補正値 (t_call 12 / t_raise 40) は MTT 25-50bb stage に最適化されています。Cash の short stack は committed range の概念は同じですが、実際の登場頻度は低くなります。

## この章で覚える項目 (3 items)

1. short stack (≤25bb) は SPR 自動下げ、 SPR=3 を跨ぐことが多い
2. T_call 14 → 12、 T_raise 43 → 40 で補正
3. 例外 1 と 3 は short stack で無効化 (committed)
