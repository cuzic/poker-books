# 第04章 守備マトリックス — 相手のベットを受けたときのアクション

相手が先にベットしてきた局面で参照するのが守備マトリックスです。
5 × 4 (ハンド強さ 5 段 × サイズ 4 段) の 20 セルでアクション (FOLD/CALL/RAISE) を決めます。
この章では各セルの意味と、街ごとの微調整を解説します。

## 守備マトリックスの全貌

守備側 (相手のベットを受けた状態) で参照する 5 × 4 マトリックスです。本書の中核中の中核。

**守備マトリックス (FOLD / CALL / RAISE)**

| ハンド強さ \ サイズ | s (小) | m (中) | l (大) | o (オーバー) |
|----------------------|--------|--------|--------|-------------|
| **S** (Strong) | RAISE | CALL | CALL | CALL |
| **M** (Medium) | CALL | CALL | CALL | **FOLD** |
| **W** (Weak) | CALL | CALL | **FOLD** | FOLD |
| **A** (Air) | CALL | **FOLD** | FOLD | FOLD |
| **D** (Draw) | CALL | CALL | CALL | **FOLD** |

表をよく見ると、**サイズが 1 段階大きくなる (左→右) ごとに 1 段階タイトに対応** (CALL→FOLD) するパターンが綺麗に並んでいます。これが 5 公理 4「サイズが 1 段階大きいほど 1 段階タイトに」の正体です。

ハンド強さの **境界線** が斜めに走っているのが分かるはずです。
- S は全サイズでアグレッシブまたは CALL (FOLD なし)
- M は overbet でだけ FOLD
- W は大きい (l) と overbet で FOLD
- A は medium 以上で FOLD
- D は overbet でのみ FOLD (drawing odds が消失)

## セル別の解説

### S (Strong) 行 — ナッツ近辺で打ち返す

S (Strong = 2P+/set/straight/flush/overpair) の対応は明快です。

**S × s (small bet)** → **RAISE**
相手の small bet は「諦めたい」または「自分は弱いと思った probe」の合図。こちらの S が強いので、raise で value を取りにいくのが正解。raise size は「small bet の 3-4 倍」が標準 (詳細は ch05)。

**S × m / l / o** → **CALL**
相手が m 以上のサイズを打ってきたら、相手も強いことが多い。S で raise すると相手の更に強い S (こちらの S を超える S) に踏まれる可能性が増す。**CALL で安全に value を取りにいく**のが原則。

例外: **fullhouse / quads はサイズ問わず RAISE** (ほぼ確実にナッツなので)。

### M (Medium) 行 — 中程度のショウダウン価値

M (Medium = TP/2nd/3rd pair/underpair) は **showdown value** で勝負する層です。

**M × s** → **CALL**
相手の small bet は弱め。M の showdown value で十分勝てる。

**M × m** → **CALL**
標準的な cbet を受けているが、M でブラフキャッチできる確率も十分。

**M × l** → **CALL** (境界、ややリスク)
相手の large bet は polarized 寄り。M で call するか fold するか境界。本書では **CALL** を推奨します (相手のブラフ頻度を考慮して期待値プラス)。

**M × o (overbet)** → **FOLD**
Overbet は完全 polarized。相手のバリューはナッツ近辺、ブラフは完全 air。M でブラフキャッチしても、相手がバリューならほぼ確実に負け。**FOLD が原則**。

### W (Weak) 行 — 弱いショウダウン価値

W (Weak = A-high/K-high/low pair) は「ほぼ負けているが、最弱ではない」位置です。

**W × s** → **CALL**
相手の small bet は安いし、W でもブラフキャッチできる確率がある。

**W × m** → **CALL**
標準サイズに対しても、W の showdown value (特に A-high) でブラフキャッチを試みる。

**W × l / o** → **FOLD**
Large 以上のサイズは相手がバリュー寄り。W では勝てない。

### A (Air) 行 — 完全な空ハンド

A (Air = no_made + no_draw) は最弱の層です。

**A × s** → **CALL**
安いコール価格。A でも turn で何か当たれば勝てる可能性がある。

**A × m / l / o** → **FOLD**
medium 以上のサイズは A で勝ち目がない。即座に fold。

公理 5「**完全 air は基本諦める**」の通り、A は基本フォールド。例外は s vs small bet で安く showdown を見にいくときだけ。

### D (Draw) 行 — 強いドローの戦い方

D (Draw = OESD/FD/combo) は **drawing odds** を計算して call する層です。

**D × s / m / l** → **CALL**
8-15 outs のドローは pot odds + implied odds で large bet までは call できる。

**D × o (overbet)** → **FOLD**
Overbet は **drawing odds を消す**。例えば flush draw (9 outs = 19% to hit by turn) は 33% pot に対しては call できるが、200% pot (overbet) に対しては約 67% の確率で hit する必要があり、これは数学的に不可能。**Overbet vs draw は FOLD**。

これは Vol3 / GTO 検証で確認された MTT 50bb turn の最大の発見でもあります (詳細は付録)。

## 街ごとの微調整

上記マトリックスは全街共通ですが、街ごとに微調整があります。

### Flop defense の微調整

Flop では追加で以下の例外があります。

- **W (low_pair / 3rd_pair) × m × dry board** → 通常は CALL だが、**dry_high (K-/A-high の dry board) や dynamic_2tone では FOLD**
- 理由: dry board では BTN の cbet レンジが強く、W は high card に負けていることが多い

Flop の詳細は ch05 で扱います。

### Turn defense の微調整

Turn では **draws の対応がより厳しく** なります。

- **A × o (overbet) × dry_high × flush_draw** → 通常 D 扱いで CALL だが、**dry_high の overbet では FD でも FOLD**
- **A × m × dynamic × OESD** → 通常 D 扱いで CALL だが、**dynamic 板で OESD でも FOLD** (implied odds 消失)
- 理由: turn 以降は SPR (stack-to-pot ratio) が下がり、drawing odds が悪化する

Turn の詳細は ch06 で扱います。

### River defense の微調整

River では **D (Draw) 行が消失** します (もうドローが残らない)。代わりに **bucket-based** (相対強さ) の判断が支配的になります。

- **W × l × dynamic で TP/2P は bluff catch (CALL)**: dynamic river で TP は通常 fold だが、相手の overbet range が広く bluff を含むことが多いため call
- **S × o (overbet/all-in) で straight や flush は CALL のみ** (raise オプションなし)

River の詳細は ch07 で扱います。

## マトリックスを忘れたときの対処 — 5 公理に戻る

実戦中にマトリックスの該当セルが思い出せないことがあります。そのときは 5 公理に戻れば必ず方向性が出ます。

**例: M × l (medium hand × large bet) を忘れた**

1. 公理 3「強いハンドは aggressive、弱いハンドは passive」 → M は強くも弱くもないので RAISE はしない、FOLD か CALL
2. 公理 4「サイズが 1 段階大きいほど 1 段階タイトに」 → m での M は CALL なので、l では「1 段階タイト = CALL のままか、FOLD」
3. 公理 5「完全 air は基本諦める」 → M は air ではないので、ここまで来たら CALL

→ **答え: CALL** (マトリックスとも一致)

5 公理だけでも 70-80% は正解できるよう設計されています。マトリックスは「より正確な答え」を出すための拡張版と考えてください。

## 次の章へ

攻撃 (ch03) と守備 (ch04) のマトリックスが揃いました。これだけで Cash 100bb のポストフロップ判断の **大半** がカバーされます。

次は街ごとの細部を ch05 (Flop)、ch06 (Turn)、ch07 (River) で扱います。各章とも「マトリックスの例外」と「街特有の補正」を中心に解説します。
