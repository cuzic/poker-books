# 第 25 章　深スタック (200bb+)

## 25.1 深スタックでの Score 公式の挙動

deep stack (effective 200bb+) では SPR が自動的に上昇します。

| typical | stack | pot 初期 | flop SPR |
|---|---:|---:|---:|
| Cash 100bb SRP | 100 | 5.5 | ~17 |
| Cash 200bb SRP | 200 | 5.5 | **~35** |
| Cash 500bb SRP (high stake) | 500 | 5.5 | ~90 |

deep stack ではディープSPR が更に深くなり、 implied odds が大きく効きます。

## 25.2 deep stack での implied odds

SPR > 20 では、以下のような特徴が出てきます。

- アンダーペア × flop → コール (set up 価値、 turn / river で 2P / set 完成期待)
- gutshot / OESD → コール (大量の implied odds)
- スーテッドコネクター → wide call

Score 公式の DV × mult は flop で 12 (combo draw)、 turn で 8 まで上がります。
これに deep stack の implied odds を考慮するなら +2〜+3 の補正がおすすめです。

- DV(3) → 実 implied DV(4) on deep stack
- gutshot DV(1) → 実 DV(2)

ただしこれは大まかな目安です。厳密化は本書のスコープ外です。

## 25.3 200bb での Score 閾値補正

Cash 200bb の audit (limited data) から推定する補正をご紹介します。

- T_call: 14 → **16** (call slightly tight、 deep stack では bluff catch 慎重に)
- T_raise: 43 → **45** (raise threshold やや上げる、 over-protection 抑制)

→ deep stack では **post-flop の implied odds 価値を Score に乗せる** より、
閾値を上げて「強い手だけ raise / value 重視」 が GTO 推奨です。

## 25.4 Cash 200bb と MTT 200bb の同構造性

audit (limited、 ~10K rows) で Cash 200bb と MTT 200bb の挙動を比較してみました。

- 同 board / 同 hand での GTO action 一致率 92%+
- huge spots の構造が同じ (主に wet × river)
- 例外ルール 5 つはそのまま適用可能

→ MATCHA Score は **stack depth 軸でも汎用** だと確認されています。

## 25.5 deep stack での board family 別注意

### dry × deep

- TP+: 慎重に (Score 38 + 0 = 38 → call)、 overprotection を控えましょう
- 2P+: slowplay を強化 (deep stack では trap が効きます)
- ミドル: 18 + 0 = 18 → call (implied odds で許容)

### wet × deep

- 例外 1 (TP+ × wet × flop × SRP → fold) は deep stack でも有効です
- 2P+ × wet × river × SRP → raise (例外 2)、 deep stack でこそ
  pot コントロール後の overbet 価値が出てきます

### paired × deep

- ミドル × paired = 40 → raise 強行 (deep stack でも変わりません)

## 25.6 200bb での例外ルール調整

例外 11 ルール (第 9 章) のうち、 deep stack で挙動が変わるものをピックアップしました。

- 例外 1 (TP+ × wet × flop × SRP → fold): deep stack で **更に強化** (fold 厳格に)
- 例外 2 (2P+ × wet × river × SRP → raise): deep stack でこそ overbet 化
- 例外 4 (エア × wet × turn × 3BP → call): deep stack でも有効 (bluff catch)

deep stack では例外 1 と 2 が最頻出パターンなので、確実に覚えましょう。

## Cash/MTT note

deep stack は **Cash 主体の概念** (Cash 200bb+)、 MTT 200bb は早期のみです。 本章の補正 (t_call 16 / t_raise 45) は両者共通です。 Cash deep では rake 込みで t_call 更に +1-2 推奨です。

## この章で覚える項目 (3 items)

1. deep stack (200bb+) は SPR 自動上げ、 implied odds 大
2. T_call 14 → 16、 T_raise 43 → 45 で補正
3. Cash 200bb = MTT 200bb の同構造性 (MATCHA Score 汎用)
