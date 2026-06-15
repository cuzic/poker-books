# 第 23 章　アタックルール — BET/CHECK の決定ロジック

## 23.1 アタックとは

**アタック** = 自分から最初に賭けを開始する（BET / C-BET）行動です。
ディフェンス（相手のBETに対して call / raise / fold を選ぶ）とは別のシナリオになります。

本章は「相手がチェックした後、または自分がファーストアクション」の局面で
**どの条件なら BET し、どの条件なら CHECK するか** を決定ロジックとして示します。

精度根拠: 6,418 hands × 16 シナリオの GTO Wizard 実測データで検証しました。
全体精度 **81.09%**（DT 上限 83.2% に対し −2.1pp）です。

## 23.2 なぜ MATCHA Score を使わないのか

MATCHA Score（Grid + DV×mult + 2oc + 4pot − 2bs）は **ディフェンス専用** の公式です。
アタック判断に Score を使うと、ロジックが逆転するケースが生じます。

| ハンド × board | Score の示す行動 | アタックの正解 |
|---|---|---|
| TP+ × paired (SRP) | Grid=10 → fold 相当 | **BET**（ペアボードで TP+ は相対的に強い） |
| UP × paired (SRP) | Grid=40 → call 相当 | **BET**（ペアボードで UP が値上がりする） |
| 2P+ × dry (4BP) | Grid=25 → call 相当 | **CHECK**（SPR≈2 ではトラップが有効） |

Score がアタックに使えない理由は、Grid 値が「相手のベットサイズに対する自ハンドの防御価値」を表しており、
「自分からベットしたときに相手が降りるかどうか」は別の問いだからです。

## 23.2b BET の3動機 — フロップ・ターン・リバー共通フレーム

アタック判断の全ストリートを貫く考え方です。**なぜ BET するのか** を3種類に分けると、
複雑に見えるルールが「理由から導ける」ようになります。

| 動機 | 記号 | 意味 | 代表ハンド |
|---|---|---|---|
| **バリュー** | **V** | 相手の弱い手からコールをもらう | 2P+、TP+、second_pair（薄いV） |
| **セミブラフ** | **S** | フォールドさせる＋当たれば強い | エア + draw（gutshot/FD/OESD） |
| **ブラフ** | **B** | ショーダウン価値ゼロ → フォールドさせるしかない | no_made_hand（リバー）、4BP dry の low_pair |

**CHECK になる理由** も2種類あります：

| 理由 | 意味 | 代表ハンド |
|---|---|---|
| **ショーダウン守（SD守）** | 勝てる可能性があるのに BET すると損 | king_high、ace_high、low_pair（リバー） |
| **スローレイ** | 強すぎて BET すると相手が降りる | set/flush（3BP フロップ）、overpair（4BP OOP） |

> **核心**: `king_high → CHECK` / `no_made_hand → BET` の理由
> - king_high はショーダウンで勝てる可能性がある → CHECK して守る（SD守）
> - no_made_hand はショーダウンで必ず負ける（ペアなし）→ BET 以外に勝ち手がない（B）

---

## 23.2c アタック全体マップ → 8 ルール（暗算コンパクト版）

### アタック傾向マップ（ざっくり把握）

まず「大体どのハンドが BET か CHECK か」を掴むようにしましょう。
◎ = BET 傾向（GTO 65%+）　△ = 境界（40〜65%）　× = CHECK 傾向（〜40%）

**フロップ**

| ハンド | SRP IP | SRP OOP | 3BP IP | 3BP OOP | 4BP |
|--------|:------:|:-------:|:------:|:-------:|:---:|
| set+ | ◎ | × | × *スロー* | × | × *スロー* |
| 2P+ | ◎ | × | ◎ | × | × *スロー* |
| TP+ | △ | × | ◎ | × | △ |
| 2nd/UP | △ | × | × | × | ◎ |
| 底ペア / no_made | △/× | × | × | × | △ |
| K/A-high | △ | × | × | × | △ |

> OOP はほぼ全部 CHECK します。4BP のみ「強いハンドほど CHECK（スローレイ）、弱いハンドが BET」に逆転するんです。

**ターン**

| ハンド | SRP IP | SRP OOP | 3BP IP | 3BP OOP | 4BP IP | 4BP OOP |
|--------|:------:|:-------:|:------:|:-------:|:------:|:-------:|
| set+ | ◎ | △ | ◎ | △ | ◎ | × *スロー* |
| 2P+ | ◎ | △ | ◎ | △ | ◎ | × *スロー* |
| TP+ | △ | × | △ | △ | ◎ | △ |
| 2nd/UP | × | × | × | × | ◎ | △ |
| 底ペア | × | × | × | × | △ | × |
| no_made | △ | × | △ | × | △ | × |
| K/A-high | △ | × | × | × | × | × |

> 4BP IP は弱いハンドまで広く BET 傾向です（底ペアも △60%）。
> 4BP OOP は逆転します: 2P+/set+ が CHECK（スローレイ）、弱いハンドはブラフ候補になります。

**リバー**

| ハンド | SRP | 3BP | 4BP IP | 4BP OOP |
|--------|:---:|:---:|:------:|:-------:|
| set+ / 2P+ | ◎ IP / △ OOP | ◎ IP / △ OOP | ◎ | △ |
| TP+ | ◎ | ◎ | ◎ | △ |
| 2nd/UP | △→◎ | ◎ | △ | ◎ |
| 底ペア | × | × | × | △ *逆転* |
| no_made | △ | △ | △ | × |
| K/A-high | **×（全場面）** | **×（全場面）** | × | × |

> K/A-high はリバーで必ず CHECK です（ショーダウン価値を守ります）。
> 底ペアは 4BP OOP リバーのみ逆転 BET します。no_made はほぼ境界（△）ですが 4BP OOP のみ CHECK になります。

---

### 8 ルール（暗算版）

上のマップの傾向を 8 条件に圧縮したものです。

精度: **LS=91%**（6,418 hands × 16 シナリオ実測）
定義: **底ハンド** = no_made_hand / low_pair / third_pair

---

### デフォルト: CHECK

以下のルールに一致しなければすべて CHECK です。

---

### BET ルール（4 条件）+ BET 例外（2 条件）

| # | 条件 | アクション | 動機 |
|---|------|-----------|------|
| **R1** | **TP+ 以上（トップペア以上、2P+/set+ 含む）** | **BET** | V バリュー |
| E1★ | （R1 の例外）trips / overpair × **4BP OOP** | **CHECK** | スローレイ |
| **R2** | **2nd/UP（セカンドペア/アンダーペア）× 4BP または リバー** | **BET** | V薄バリュー |
| **R3★** | **low/3rd（ローペア/サードペア）× 4BP OOP × リバー** | **BET（逆転！）** | B 純ブラフ |
| **R4★** | **no_made_hand × リバー**（ペアなし × リバー） | **BET** | B 純ブラフ |
| E2 | （R4 の例外）no_made_hand × 4BP OOP × リバー | **CHECK** | ブラフ不成立 |

---

### ターン専用補正（3 条件）

ターンのみに適用する追加条件です。4BP IP dry の「逆転」パターンを扱います。

定義: **底ハンド** = no_made_hand / low_pair / third_pair（ショーダウン価値がほぼゼロのハンド）

| # | 条件 | アクション | GTO% | 動機 |
|---|------|-----------|------|------|
| **T底★** | **底ハンド** × **4BP IP** × ターン × **dry** | **BET** | 52–68% | B 純ブラフ（逆転） |
| **T3** | 2nd/UP × **SRP IP** × ターン × **ドローあり** | **BET** | ~60% | S セミブラフ |

> **底ハンドとは**: no_made_hand（ペアなし）、low_pair（最低ペア）、third_pair（3番目ペア）の総称です。
> 4BP IP dry のターンではこの3つが同じ「逆転 BET」ルールに従うため、1条件で表現できます。
> ただしリバーでは no_made と low/3rd の行動が分かれるため（後述）、底ハンドの統合は**ターンのみ**有効です。

---

### 判定の優先順位（疑似コード）

```
デフォルト = CHECK

1. E1: trips/overpair × 4BP OOP     → CHECK（最優先）
2. R1: TP+ 以上                     → BET
3. R2: 2nd/UP × (4BP or リバー)     → BET
4. T底: 底ハンド × 4BP IP ターン dry→ BET ★（逆転）
5. T3: 2nd/UP × SRP IP ターン draw  → BET
6. R3: low/3rd × 4BP OOP リバー     → BET ★（逆転）
7. E2: no_made × 4BP OOP リバー     → CHECK
8. R4: no_made × リバー             → BET ★
```

合計 **8 条件**（精度 LS=91%）

---

### なぜリバーでは底ハンドを統合できないか

リバーの 4BP OOP dry で、底ハンド内部が**逆方向**に分岐するためです：

| 底ハンドの種類 | 4BP OOP リバー GTO% | 判定 |
|---|---|---|
| **low_pair** | 57.9% | → **BET**（R3 逆転） |
| **third_pair** | 76.4% | → **BET**（R3 逆転） |
| **no_made_hand** | 33.8% | → **CHECK**（E2 例外） |

no_made のみが CHECK になる理由は、4BP OOP では相手のレンジが AA/AK 寄りに絞られており、ブラフ（no_made）が機能しません。一方 low/3rd はブラフではなく「薄いスケア」としてフォールドを誘えるんです。

---

### 8 ルールで何が変わるか

| ストリート | カバー範囲 |
|------------|-----------|
| **フロップ** | R1（TP+→BET）が主役です。4BP は R2 で 2nd/UP も追加 |
| **ターン** | R1+R2 に加え T底（底ハンド統合・4BP IP dry 逆転）と T3（SRP IP draw） |
| **リバー** | R2+R3+R4 でほぼ完全カバーします。E1/E2 で 4BP OOP 例外を処理 |

> **注意点**: 後続の 14.3〜14.9 のシナリオ別ルールを参照してください。
> 8 ルールは「9 割の局面で正解」する圧縮版です。

---

### 確実に CHECK するケース（8 ルールの前提）

8 ルールは「BET 条件に当てはまらなければ CHECK」という構造ですが、
以下のケースは **BET ルールが発火していても CHECK が正解** です。
「相手レンジが強すぎる」か「ショーダウン価値を守る」かのどちらかが理由になります。

| 状況 | GTO BET% | 理由 |
|------|---------|------|
| **king_high / ace_high** — 全シナリオ | 約 27% | ショーダウン価値あり → 守ります |
| **TP+ 以上 × 3BP OOP** （フロップ・ターン） | 約 46% | 相手レンジが AA/KK 寄りで BET が裏目 |
| **2nd/UP × 4BP OOP ターン** | 約 47% | 4BP OOP は IP と逆ロジック（R2 の例外） |
| **two_pair/set × 4BP OOP ターン** | 約 30% | スローレイ（E1 の適用範囲を超えた強ハンド） |
| **低ペア（low/3rd）× SRP/3BP リバー** | 約 23% | ショーダウン価値あり → 守ります（4BP OOP は逆転） |

> **読み方**: 8 ルールで BET と判定されても上の表に当てはまる場合は CHECK です。
> 特に 4BP OOP のターンは「強いハンドほど CHECK（スローレイ）、弱いハンドは BET（ブラフ）」と
> 覚えるといいですよ。逆転パターンが整理しやすくなります。

---

## 23.3 SRP フロップ IP — 判断ロジック

SRP（SPR ≈ 8〜12）で相手（OOP）がチェック。自分（IP）のアクションを決めます。

```
2P+?                                               → BET
TP+ かつ paired?                                   → BET
TP+ かつ dry かつ (draw あり OR Q/K/A-high)?       → BET（低 dry は CHECK）
UP かつ paired?                                    → BET（ただし A-board は CHECK）
UP かつ dry かつ gutshot?                          → BET if K/A-high のみ
エア かつ dry かつ strong draw (FD/OESD/combo)?    → BET if K/A-high
エア かつ dry かつ gutshot?                        → BET（K/A-high のみ）
エア かつ wet かつ strong draw?                    → BET if Q-high 以上
エア かつ paired かつ draw あり (gutshot 以上)?    → BET
→ CHECK
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | 最強ハンドは全ボードでバリュー確定です。相手のどのコール/フォールドも EV プラス |
| ② | **V** | TP+ × dry × (draw OR Q+high) | **BET** | Q/K/A ボードは相手レンジが連動します。7-5-2 等の低 dry では TP+ も CHECK |
| ③ | **V** | TP+ × paired | **BET** | ペアボードで TP+ が相手レンジを支配します |
| ④ | **V** | UP × paired（A-board 除く） | **BET** | ペアボードは相手の 7x/8x 等が減り自ペアの相対価値が上昇します |
| ⑤ | **S** | UP × dry × gutshot × K/A-high | **BET** | K/A-high dry のみ gutshot UP がセミブラフとして機能します。低 dry は CHECK |
| ⑥ | **S** | エア × dry × strong draw × K/A-high | **BET** | FD/OESD/combo = セミブラフです。K/A ボードでのみ機能 |
| ⑦ | **S** | エア × wet × strong draw × Q-high+ | **BET** | Q 以上の wet ボードで strong draw がセミブラフとして機能します |
| ⑧ | **S** | エア × paired + draw | **BET** | ペアボードは相手レンジが弱まるため gutshot でもセミブラフが機能します |

> **ランク閾値の考え方**: 「ボードが K/A-high（top rank ≥ 13）か否か」で BET/CHECK が分かれます。
> 低ボード（top rank ≤ J=11）は相手レンジが連動しにくく、弱い手の攻撃効率が落ちます。
> "strong draw" = FD / OESD / combo_draw（gutshot と twocards_bdfd は対象外）

**OOP フロップ SRP**: 原則 CHECK します。以下の例外のみ BET です：
- TP+ × dry × no-draw × A-high のみ → BET（donk bet として A-board で機能）
- 2P+ × wet × no-draw × 6-high 以下 → BET
- 2P+ × paired × no-draw × 5-high 以下 → BET
- 2P+ × dry × no-draw × A-high のみ → BET

## 23.4 3BP フロップ IP — 判断ロジック

3-bet pot（SPR ≈ 4〜6）です。相手の 3bet レンジは AK / QQ+ 寄りにコンデンスされています。

```
TP+ または 2P+? → BET（ただし TP+×wet×no-draw×J-high 以上は CHECK）
エア × paired × low (≤6-high)? → BET
エア × dry × no-draw × ≤9-high? → BET
UP × dry × gutshot × K-high 以上? → BET
→ CHECK
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | TP+ 以上（wet×no-draw 除く） | **BET** | 相手のコンデンスされたレンジに対して TP+ 以上がバリューラインになります |
| ② | **V** | TP+ × wet × no-draw × ≤9-high | **BET** | 低 wet ボードは TP+ でも BET します（9 以下の wet）。J-high 以上 wet×no-draw は CHECK |
| ③ | **B** | エア × paired × ≤6-high | **BET** | 低ペアボードは相手レンジが弱い → エアのブラフが機能します（56% BET） |
| ④ | **B** | エア × dry × no-draw × ≤9-high | **BET** | 9 以下の低 dry ボードでエアのブラフが機能します（56% BET） |
| ⑤ | — | UP / エア × wet/paired×high | **CHECK** | 相手が強いレンジを持つ局面でブラフは機能しないんです |

> SRP との違い: SRP では「UP×dry+draw → BET」「UP×paired → BET」等の例外があったのですが、
> 3BP では **TP+ 以上 + 低ボード限定の例外** に絞ります。精度 84.7%です。

## 23.5 4BP フロップ — レンジベット戦略（SRP/3BP とは別ロジック）

4-bet pot（SPR ≈ 2）のフロップは **SRP/3BP とは根本的に別のゲーム** です。
GTO Wizard 実測データにより、4BP は **20% pot のレンジベット戦略** が最善と確認されました。


### 4BP フロップ BET ルール

```
Ultra-dry 低ボード（4s4d2c, 7s4d2c, 8s5d3c 型）?  → AI（オールイン直行）
TP+ ?                                               → BET（IP/OOP 問わず）
2ndペア / 3rdペア（IP）× connected?                 → BET（≈50%、レンジ分散）
→ CHECK（その他）
```

| 動機 | 条件 | アクション | 理由 |
|---|---|---|---|
| **V** | Ultra-dry 低ボード（742/752/853 型）× any | **AI** | 20% pot は機能しません。直接 all-in が最善です |
| **V** | TP+ × all boards (IP/OOP) | **BET 20% pot** | SPR≈2 でバリューを即回収します |
| **V/B** | 2nd/3rdペア × IP × connected | **BET 20% pot** | レンジ全体の EV を最大化します |

> **4BP の根本原理（レンジベット）**: SPR≈2 でベットしても相手が次のストリートで all-in になります。
> 強い手でもすぐに BET してバリューを回収する方が EV 高いんです。
> 3BP での「セット/フラッシュ → CHECK（スローレイ）」は 4BP では不要です。SPR が低すぎてスローレイの旨味がありません。

> **ベットサイズ**: 20% pot（= ≈11BB into ≈56BB pot）です。SRP/3BP の 33–50% pot とは全く異なります。

## 23.6 ターン IP — 判断ロジック

フロップで双方チェック後（または delayed C-BET）、ターンで相手がチェック。

### SRP ターン IP

```
2P+?                                 → BET（V バリュー）
TP+ かつ dry かつ draw あり?        → BET（V+S バリュー兼セミブラフ）
TP+ かつ draw あり?                 → BET（V+S）
エア かつ draw あり (gutshot 以上)? → BET（S セミブラフ）
→ CHECK（UP は draw あっても CHECK）
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | ターンでも最強ハンドはバリュー確定です |
| ② | **V+S** | TP+×dry + draw | **BET** | draw なし TP+ は 40% BET = CHECK 多数です。draw で補完が必須 |
| ③ | — | TP+×dry×no draw | **CHECK（スローレイ）** | 40.3% BET — draw なし TP+ は dry でも CHECK が GTO 多数（反直感） |
| ④ | **V+S** | TP+×wet + draw | **BET** | draw が加わった TP+ は wet でもバリュー兼セミブラフになります |
| ⑤ | **S** | エア + gutshot 以上 | **BET** | gutshot エア×dry 76%、OESD/FD 85〜100% のセミブラフ値 |
| ⑥ | — | UP（draw あり） | **CHECK（SD守）** | UP のブロッカー価値 < ショーダウン価値です。Draw があっても原則 CHECK |

> **重要**: TP+×dry は **draw なし = CHECK**（逆直感）です。GTO はターン到達後に dry ボードの TP+ を slowplay します。


### 3BP ターン IP

```
2P+?                                              → BET
TP+ かつ dry?                                    → BET
TP+ かつ paired × no-draw × A-only?              → BET（K 以下は CHECK）
TP+ かつ gutshot?                                → BET
UP × paired × 10-high 以上?                      → BET（10 以下の低ペアは CHECK）
no_made_hand × dry × draw (gutshot/FD)?          → BET ★（55–84%）
→ CHECK（エア全て: ace_high/king_high/low_pair/third_pair は draw があっても CHECK ★）
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | 3BP でも最強ハンドは継続バリューです |
| ② | **V** | TP+×dry | **BET** | dry ターンでは TP+ が相手の 3bet レンジに対して優位（85% BET） |
| ③ | **V** | TP+×paired×A-only | **BET** | A-board ペアのみ TP+ が BET します。K 以下のペアは CHECK（25% BET） |
| ④ | **V+S** | TP+×gutshot | **BET** | gutshot で強化された TP+ はセミブラフ価値が付加されます |
| ⑤ | **V** | UP×paired×10+ | **BET** | J/Q/K/A-high ペアで UP に価値が出ます。9 以下の低ペアは CHECK |
| ⑥ ★ | **S** | **no_made_hand × dry × draw（gutshot/FD）** | **BET** | 純ブラフハンドのみ draw でセミブラフが機能します（55–84% BET）|
| ✗ | — | エア（ace_high/king_high/low_pair/third_pair）× any | **CHECK（SD守）★** | ショーダウン価値あり → 守ります。GTO: low_pair 22%、ace_high gutshot 22% |

> **3BP ターン エア = 全 CHECK（no_made_hand+draw の例外のみ）**:
> **no_made_hand**（ペアなし純ブラフ）だけが draw でセミブラフとして機能します。
> King/Ace-high はブロッカー値があるのですが CHECK が EV 高いんです。

### 4BP ターン IP — ボード × ハンドカテゴリ 別ロジック

```
【dry ボード】
TP+ または two_pair 以上?                → BET（77–78%）
second_pair?                            → BET ★★（73.9%）← 重要追記
third_pair × (no_draw または gutshot)? → BET ★（64–100%）
low_pair × (no_draw または gutshot)?   → BET（51–52%）
no_made_hand × (no_draw または gutshot)? → BET ★（56–58%）
king_high × any?                        → CHECK ★（24–30%、gain=14.71 BB）
ace_high × any?                         → CHECK ★（23–50%）
エア × FD/OESD?                         → CHECK（34–38%）

【paired ボード】
TP+?                                    → BET（66%）
third_pair × no_draw?                   → BET ★（90.5%、gain=4.35 BB）
ace_high × no_draw?                     → BET ★（59.2%）
→ CHECK（no_made_hand 36.7%、second_pair 28.8% は全て CHECK）

【wet ボード】
TP+?                                    → BET（52%）
→ CHECK（エア全て: low_pair 26.8%、third_pair 28% は CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ①D | **V** | **dry**: TP+/2P | **BET** | 61–78% | SPR≈1.5 でオールイン圧力として機能します |
| ①D_b ★★ | **V薄/B** | **dry**: second_pair | **BET** | 73.9% | TP+/2P の次に位置する薄いバリュー。dry × 4BP では K/A-high コールを誘えます |
| ②D ★ | **B** | **dry**: third_pair × no_draw/gutshot | **BET** | 64–100% | ショーダウン価値低 → ブラフがオールイン圧力として機能します |
| ③D ★ | **B** | **dry**: no_made_hand × no_draw/gutshot | **BET** | 56–58% | ショーダウン価値ゼロ → 純ブラフが最もプレッシャー機能します |
| ④D ★ | — | **dry**: king_high または ace_high | **CHECK（SD守）** | 24–30% | ショーダウン価値あり → 守ります |
| ⑤D | — | **dry**: エア × FD/OESD | **CHECK（スローレイ）** | 34–38% | 強ドロー = 相手に踏み込まれると負けます → CHECK |
| ①P ★ | **B** | **paired**: third_pair × no_draw | **BET** | 90.5% | ペアボードで low_pair が「ロウ 3 枚目」→ 相手フォールド誘発 |
| ②P ★ | **B** | **paired**: ace_high × no_draw | **BET** | 59.2% | A-high はペアボードでスケア（相手のボードペアを超えた） |
| ①W | **V** | **wet**: TP+ | **BET** | 52% | wet でも TP+ はバリューです |

> **4BP ターン dry の核心**: second_pair は 73.9% BET — TP+ の次に位置する薄いバリュー（paired の 28.8% とは別物）です。
> K/A-high は CHECK してショーダウンを狙います。
> **dry × second_pair ≠ paired × second_pair**: dry では K/A-high のコールを取れるのですが、paired では相手のフルハウス可能性が高く BET 不可です。

> 4BP ターンの位置付け: フロップ「TP+ → BET、エア→CHECK（レンジベット）」から、ターンは「low_pair/no_made_hand → BET に転換」します。SPR が低下し、ブラフのプレッシャーが増すんです。

## 23.7 OOP ターン — 判断ロジック

双方フロップチェック後、ターンで OOP（= 自分）がファーストアクション。

### SRP ターン OOP

```
2P+ × wet × 10-high 以上? → BET（9 以下 wet は CHECK）
2P+ × dry?               → BET
2P+ × paired × ≤10-high? → BET（11 以上は CHECK）
エア × wet + draw?        → BET
エア × dry × strong × ≤11-high? → BET（12 以上 K-high は CHECK）
エア × paired × draw × ≤10-high? → BET（11 以上は CHECK）
→ CHECK
```

OOP ターン SRP の基本は **CHECK** です。2P+×wet/dry（バリュー）と draw 付きエアが BET 候補になります。
ランク閾値: 2P+×wet は 10-high 以上のみ BET、2P+×paired は 10 以下のみ BET です。

### 3BP ターン OOP

```
TP+ (top_pair, overpair, trips) × dry?       → BET（71–81%）
TP+ × paired × no-draw × ≤10-high?          → BET（11 以上は CHECK）
TP+ × wet?                                   → BET（44–69%）
no_made_hand × dry/wet × draw (gutshot/FD)?  → BET ★（59–84%）
→ CHECK（エア全て: ace_high/king_high/low_pair × any は CHECK ★）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | **TP+ × dry**（top_pair/overpair/trips） | **BET** | 64–81% | 3BP OOP はポジション不利ですが TP+ は dry でバリューが勝ります |
| ② | **V** | **TP+ × paired × ≤10-high** | **BET** | 65% | 高ペアボード（J/Q/K/A）は CHECK、10 以下はバリューです |
| ③ | **V** | **TP+ × wet** | **BET** | 44–69% | wet でも TP+ はバリューラインになります |
| ④ ★ | **S** | **no_made_hand × draw（gutshot/FD）** | **BET** | 59–84% | ショーダウン価値ゼロ × draw = セミブラフのみが機能します |
| ✗ | — | エア（ace_high/king_high/low_pair）× any | **CHECK（SD守）★** | 8–24% | ショーダウン価値あり → 守ります。OOP エアは draw があっても不利なんです |

> **3BP OOP ターン エア = 全 CHECK**: IP 同様に、ace_high/king_high/low_pair は draw があっても CHECK が最善です。
> **trips × dry → BET (71%)** を忘れずにしましょう（trips は tier_i=4、2P+ に含まれるのですが OOP dry で明示的に BET）。

### 4BP ターン OOP — dry で overpair/2P が逆転する

```
top_pair × dry?                      → BET（59.1%）
trips × dry?                         → BET（55.6%）
overpair × dry?                      → CHECK ★（29.8%、gain=2.33 BB）
two_pair × dry × no-draw?            → CHECK ★（24%）
set × dry?                           → CHECK（25.9%、スローレイ）
second_pair × gutshot?               → BET ★（91.8%、gain=3.45 BB）
third_pair × gutshot?                → BET ★（88.3%）
→ CHECK（other: no_made_hand 15.9%、third_pair no_draw 38%）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ①T | **V** | **top_pair × dry** | **BET** | 59.1% | OOP でも top_pair dry はバリュー優先です |
| ②T | **V** | **trips × dry** | **BET** | 55.6% | trips は OOP でも BET です（GTO 実測） |
| ③T ★ | — | **overpair × dry** | **CHECK（スローレイ）** | 29.8% | 4BP OOP overpair は CHECK です！相手レンジ（AK/AA+）に対して BET は危険 |
| ④T ★ | — | **two_pair × dry × no-draw** | **CHECK（スローレイ）** | 24% | SPR≈1.5 で BET→AI のリスク大 → CHECK でスタック保全します |
| ⑤T | — | **set × dry** | **CHECK（スローレイ）** | 25.9% | 強すぎて BET すると相手が降ります → CHECK でトラップ |
| ⑥T ★ | **S** | **second_pair × gutshot** | **BET** | 91.8% | ほぼ 100% BET — gutshot が付いた second_pair は最強セミブラフです |
| ⑦T ★ | **S** | **third_pair × gutshot** | **BET** | 88.3% | third_pair+gutshot も強力セミブラフです（BET でフォールドか draw 完成） |

> **4BP OOP dry ターンの核心**: "overpair が CHECK、third_pair+draw が BET"です。
> 4BP で overpair を CHECK する理由: OOP × 4BP × dry の overpair は SPR≈1.5 で BET するとほぼ全ての相手のコールに負けます（相手は AK/AA+）。
> 逆に third_pair/second_pair+gutshot = ショーダウン価値がなく、フォールドエクイティのみがある → BET が最善です。

## 23.8 リバー IP — 判断ロジック

フロップ・ターン双方チェック後、OOP がリバーをチェック（delayed attack 局面）。

**【リバー dry ボード共通パターン】** GTO 実測で判明したリバーの核心ルール：

| mv_cat | SRP IP | 3BP IP | 4BP IP | 理由 |
|---|---|---|---|---|
| **no_made_hand** | 61.9% → **BET** | 60.8% → **BET** | 57.6% → **BET ★** | ショーダウン価値ゼロ → ブラフのみ |
| **second_pair** | 52.7% → **BET ★** | 79.5% → **BET ★** | 54.0% → **BET ★** | thin value（弱い手のコールに勝つ） |
| **underpair** | 57.9% → **BET** | 59.0% → **BET ★** | 48.1% → 境界 | 同上 |
| **third_pair** | 25.5% → CHECK | 69.0% → **BET** | 23.2% → CHECK | 3BP のみ BET |
| **king_high** | 2.5% → **CHECK ★** | 0.4% → **CHECK ★** | 3.2% → CHECK | ショーダウン価値あり |
| **ace_high** | 22.9% → **CHECK ★** | 1.9% → **CHECK ★** | 1.4% → CHECK | ショーダウン価値あり |
| **low_pair** | 13.2% → **CHECK ★** | 10.1% → **CHECK ★** | 13.3% → CHECK | ショーダウン価値あり |

> **no_made_hand（ペアなし純エア）はブラフです。ace/king_high はショーダウン価値を守りましょう。**

### SRP リバー IP

```
2P+?                              → BET
TP+ × (dry または paired)?        → BET
second_pair または underpair?      → BET ★（thin value）
no_made_hand × dry/wet?           → BET ★（ブラフ）
→ CHECK（king_high/ace_high/low_pair/third_pair × dry → CHECK ★）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | 91-100% | 最強ハンドはフルバリューです |
| ② | **V** | TP+ × dry/paired | **BET** | 91.4% | 3 チェック後も TP+ はバリューです |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 52.7% | 薄いバリュー — 相手の ace/king_high よりも強いんです |
| ④ ★ | **V薄** | **underpair × dry** | **BET** | 57.9% | 薄いバリューとして機能します |
| ⑤ ★ | **B** | **no_made_hand × dry/wet** | **BET** | 61.9% | ショーダウン価値ゼロ → ブラフが唯一の選択肢です |
| ✗ ★ | — | **king_high/ace_high/low_pair/third_pair** | **CHECK（SD守）** | 2-25% | ショーダウン価値あり → 守りましょう。BET すると相手の強い手にコールされ損 |

### 3BP リバー IP — 最大改善（gain 上位集中）

```
TP+ 以上（top_pair, two_pair, trips, straight, flush, set, fullhouse）? → BET（96-100%）
third_pair × dry?      → BET ★（69%）
second_pair × dry?     → BET ★（79.5%）
underpair × dry?       → BET ★（59.0%）
no_made_hand × dry?    → BET（60.8%）
→ CHECK ★（king_high=0.4%、ace_high=1.9%、low_pair=10.1% → 全て CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | TP+ 以上 (TP+/2P+/trips/straight/flush) | **BET** | 96–100% | SPR≈3 での強バリュー |
| ② ★ | **B/V薄** | **third_pair × dry** | **BET** | 69.0% | 3BP SPR≈3 では thin value+ブラフとして機能します |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 79.5% | 薄いバリュー |
| ④ ★ | **V薄** | **underpair × dry** | **BET** | 59.0% | 薄いバリュー |
| ⑤ ★ | **B** | **no_made_hand × dry** | **BET** | 60.8% | ショーダウン価値ゼロ → ブラフのみ |
| ✗ ★★★ | — | **king_high × dry** | **CHECK（SD守）** | 0.4% | ほぼ 100% CHECK です |
| ✗ ★★★ | — | **ace_high × dry** | **CHECK（SD守）** | 1.9% | ショーダウン価値あり → 守ります |
| ✗ ★★★ | — | **low_pair × dry** | **CHECK（SD守）** | 10.1% | リバーの重要な CHECK ハンド |

> **3BP IP リバー dry 核心**: "エア=CHECK、UP=BET" — 従来の TP+/UP/エアの三分類を捨てましょう。
> `king_high`/`ace_high`/`low_pair` → CHECK（ショーダウン価値を守る）。
> `second_pair`/`underpair`/`third_pair`/`no_made_hand` → BET（thin value or ブラフ）。

### 4BP リバー IP — no_made_hand/second_pair が解禁される

```
2P+ または TP+?         → ALLIN（SPR≈1 で全額押す）
no_made_hand × dry?    → BET ★（57.6%、gain=44.85 BB/100）
second_pair × dry?     → BET ★（54.0%）
→ CHECK（king_high/ace_high/low_pair/third_pair → CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | 2P+ / TP+ | **ALLIN** | 85-100% | SPR≈1 では全額でバリューを取ります |
| ② ★ | **B** | **no_made_hand × dry** | **BET** | 57.6% | ショーダウン価値ゼロ → ブラフです：相手がフォールドするかオールインするしかありません |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 54.0% | 薄いバリュー |
| ✗ | — | king_high/ace_high/low_pair/third_pair | **CHECK（SD守）** | 1-23% | ショーダウン価値あり → 守ります |

## 23.9 OOP リバー — polarization ロジック

フロップ・ターン双方チェック後、リバーで OOP がファーストアクション。

**【OOP リバー dry ボード共通パターン】**

| mv_cat | SRP OOP | 3BP OOP | 4BP OOP |
|---|---|---|---|
| **second_pair** | 67.5% → **BET ★** | 85.2% → **BET** | 73.0% → **BET** |
| **underpair** | 62.9% → **BET ★** | 65.9% → **BET** | 51.9% → BET |
| **no_made_hand** | 53.7% → **BET ★** | 50.7% → BET | 33.8% → CHECK |
| **third_pair** | 40.1% → 境界 | 75.2% → **BET** | 76.4% → **BET ★** |
| **low_pair** | 18.0% → CHECK | 17.3% → **CHECK ★★★** | 57.9% → **BET ★★★** |
| **king_high** | 48.6% → 境界 | 0.0% → **CHECK ★★★** | 4.0% → CHECK |
| **ace_high** | 20.2% → CHECK | 10.3% → **CHECK ★★★** | 34.8% → 境界 |
| **overpair** | 74.1% → BET | — | 12.5% → **CHECK ★** |
| **trips** | 45.0% → 境界 | 46.7% → 境界 | 43.4% → **CHECK ★** |

### SRP リバー OOP

```
TP+ または 2P+?                → BET
second_pair または underpair?  → BET ★（thin value）
no_made_hand × dry?            → BET ★（ブラフ）
→ CHECK（ace_high/low_pair → CHECK; king_high は境界: 48.6%）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | TP+ / 2P+ | **BET** | 64-100% | 強バリュー |
| ② ★ | **V薄** | **second_pair × dry** | **BET** | 67.5% | 薄いバリュー |
| ③ ★ | **V薄** | **underpair × dry** | **BET** | 62.9% | 薄いバリュー |
| ④ ★ | **B** | **no_made_hand × dry** | **BET** | 53.7% | ショーダウン価値ゼロ → ブラフです |
| ✗ | — | ace_high × dry | **CHECK（SD守）** | 20.2% | ショーダウン価値あり → 守ります |
| ✗ | — | low_pair × dry | **CHECK（SD守）** | 18.0% | ショーダウン価値あり → 守ります |

### 3BP リバー OOP — エア全般 CHECK（逆転）

```
TP+ (top_pair/overpair) × dry?          → BET（89%）
third_pair または second_pair?          → BET ★（75-85%）
underpair × dry?                        → BET ★（65.9%）
no_made_hand × dry?                     → BET（50.7%、ほぼ境界）
→ CHECK ★（king_high=0%、ace_high=10%、low_pair=17%、two_pair=45.6%、trips=46.7% → CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | **TP+ × dry**（top_pair/overpair） | **BET** | 74-89% | OOP でも TP+ はバリューラインです |
| ② ★ | **B/V薄** | **third_pair × dry** | **BET** | 75.2% | thin value + ブラフとして機能します |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 85.2% | 最も明確な薄いバリュー |
| ④ ★ | **V薄** | **underpair × dry** | **BET** | 65.9% | 薄いバリュー |
| ⑤ | **B** | **no_made_hand × dry** | **BET** | 50.7% | ショーダウン価値ゼロです。GTO はほぼ 50/50 ですが pure air はブラフが基本方針 |
| ✗ ★★★ | — | king_high × dry | **CHECK（SD守）** | 0.0% | 完全に CHECK です — ショーダウン価値あり |
| ✗ ★★★ | — | ace_high × dry | **CHECK（SD守）** | 10.3% | ショーダウン価値あり |
| ✗ ★★★ | — | low_pair × dry | **CHECK（SD守）** | 17.3% | ショーダウン価値あり |
| ✗ ★ | — | two_pair × dry | **CHECK（スローレイ）** | 45.6% | OOP × dry × 3BP では two_pair も CHECK です |
| ✗ | — | trips × dry | **CHECK（スローレイ）** | 46.7% | 境界（46.7%）|

> **3BP OOP dry リバー核心**: `king_high=0%`、`low_pair=17.3%` → CHECK です（ショーダウン価値を守る）。
> `second_pair/underpair` → BET です。
> `no_made_hand` はほぼ 50/50（50.7%）— 迷ったら BET でいいんですが GTO 的には誤差範囲です。

### 4BP リバー OOP — lower_pair が逆転 BET

```
top_pair または two_pair または straight?     → BET（55-88%）
third_pair × dry?                            → BET ★★★（76.4%）
low_pair × dry?                              → BET ★★★（57.9%）
second_pair × dry?                           → BET（73.0%）
→ CHECK（overpair=12.5% ★ / trips=43.4% / fullhouse=43.1% / king_high=4% → CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | top_pair / two_pair / straight | **BET** | 55–88% | バリューラインです |
| ② ★ | **V/B** | set / second_pair / underpair | **BET** | 52–73% | SPR≈1 でのバリュー/ブラフ |
| ③ ★★★ | **B** | **third_pair × dry** | **BET** | 76.4% | ショーダウン価値低 → ブラフが最善です |
| ④ ★★★ | **B** | **low_pair × dry** | **BET** | 57.9% | ショーダウン価値低 → ブラフです |
| ✗ ★ | — | **overpair × dry** | **CHECK（スローレイ/SD守）** | 12.5% | SPR≈1 で相手レンジに対して守ります |
| ✗ ★ | — | **trips × dry** | **CHECK（スローレイ）** | 43.4% | trips が CHECK です |
| ✗ | — | **king_high / no_made_hand** | **CHECK** | 4–34% | エアはほぼ CHECK |

> **4BP OOP dry リバー核心**: "lower_pair（low_pair/third_pair）が BET、overpair/trips が CHECK"です。
> low_pair(57.9%)がBET、overpair(12.5%)がCHECKなんです。
> 理由: 4BP OOP でoverpair はSPR≈1 でオールインを押し付けられると負けます。
> low_pair はショーダウン価値が低くブラフが最善なんです。

## 23.10 BET の3動機 × ポット種別 まとめ

### V バリュー BET — 弱い手のコールをもらう

| ストリート | SRP | 3BP | 4BP |
|---|---|---|---|
| **ターン IP** | 2P+、TP+ + draw | 2P+、TP+×dry、UP×paired×10+ | TP+/2P × dry |
| **ターン OOP** | 2P+×wet/dry | TP+（trips含む）×dry | top_pair/trips × dry |
| **リバー IP** | 2P+/TP+、second_pair、underpair（薄いV） | 2P+/TP+、second_pair/underpair/third_pair（薄いV） | 2P+/TP+ → ALLIN、second_pair（薄いV） |
| **リバー OOP** | 2P+/TP+、second_pair/underpair（薄いV） | TP+、second_pair/underpair/third_pair（薄いV） | top_pair/two_pair/set/second_pair/underpair |

> **「薄いバリュー（V薄）」とは**: second_pair/underpair が ace/king_high に勝てるのでコールをもらえるんです。
> BET しても損しない相手（弱いエア）がいる = バリュー BET が成立します。

### S セミブラフ — draw があるのでフォールドさせるか当たれば勝つ

| ストリート | SRP | 3BP | 4BP |
|---|---|---|---|
| **ターン IP** | エア + gutshot以上（76-100%） | no_made_hand × dry × draw（55-84%）| no_made_hand/third_pair × dry gutshot |
| **ターン OOP** | エア × wet + draw | no_made_hand × draw（59-84%）| second/third_pair × gutshot（88-92%）|
| **リバー** | — | — | — |

> リバーにドロー待ちは存在しません → **リバーにセミブラフはありません**。
> リバーで BET する弱い手は V薄（ペアが薄いバリュー）か B（純ブラフ）のどちらかです。

### B 純ブラフ — ショーダウン価値ゼロ → フォールドさせるしかない

| ストリート | SRP | 3BP | 4BP IP | 4BP OOP |
|---|---|---|---|---|
| **ターン IP** | — | — | third_pair/no_made_hand × dry | — |
| **ターン OOP** | — | — | — | third_pair+gutshot（88%）|
| **リバー IP** | no_made_hand（62%） | no_made_hand（61%） | no_made_hand（58%）| — |
| **リバー OOP** | no_made_hand（54%） | — | — | third_pair(76%)/low_pair(58%) |

> **ブラフの必要条件**: ショーダウン価値が「ほぼゼロ」= CHECK しても 0% に近い勝率なんです。
> この条件を満たすのは: no_made_hand（ペアなし）、4BP OOP の low_pair/third_pair（相手レンジに負ける）。

### — CHECK — ショーダウン価値を守るか、スローレイ

| CHECK の理由 | 代表ハンド | 代表場面 |
|---|---|---|
| **ショーダウン守**: BET すると弱い手にコールされ損 | king_high、ace_high、low_pair（SRP/3BP） | 3BP リバー dry — low_pair(10%) CHECK ★★★ |
| **スローレイ**: 強すぎて BET すると降りられる | set/flush（3BP フロップ）、trips（4BP OOP） | 4BP OOP: trips(43%) CHECK |
| **中途半端**: バリューにもブラフにも機能しない | UP × dry（SRP ターン）、king/ace_high（4BP ターン dry） | SRP ターン UP: draw あっても CHECK |

**4BP ターン IP dry — 逆転パターン（重要）**:
```
薄バリュー:    second_pair → BET ★★（73.9%）← 追記
ブラフ枠:     third_pair → BET ★（64%）、no_made_hand → BET ★（57%、draw なし/gutshot のみ）
ショーダウン守: king_high/ace_high → CHECK ★（24%）
注意:         no_made_hand × FD/OESD → CHECK（強ドローでも 4BP では CHECK）
直感と逆！ 「高いカードほど CHECK、low_pair/no_made は BET、second_pair も BET」
```

**4BP OOP リバー dry — 逆転パターン（重要）**:
```
ブラフ枠:    third_pair → BET ★★★（76%）、low_pair → BET ★★★（58%）
スローレイ:  overpair → CHECK ★（12.5%）、trips → CHECK ★（43%）
直感と逆！ 「弱いペアが BET、overpair が CHECK」= SPR≈1 の圧力
```

## 23.11 SPR とロジックの関係

SPR（スタック/ポット比）がアタックロジックを支配する原理です：

| SPR | 構造 | ロジック |
|---|---|---|
| ≈8〜12（SRP） | スタックが深い | UP の BET は限定的です。ドロー補正が重要 |
| ≈4〜6（3BP） | 中程度 | TP+ 以上に一本化します。ブラフは機能しにくい |
| ≈2（4BP フロップ） | 浅い | 強い手はトラップ、弱い手はプレッシャー（逆転） |
| ≈1.5（4BP ターン） | さらに浅い | 弱い手（UP）も BET がオールイン圧力として有効 |
| ≈1（4BP リバー） | 最浅 | 強い手は全額（ALLIN）。弱い手は CHECK |

**原則**: SPR が低いほど、ベットが相手に「フォールドかオールイン」の二択を迫ります。
この圧力が有効なハンドは SPR によって変わっていくんです。

## この章で覚える項目 (17 items)

**【最優先】全ストリート統一 8 ルール**
0. **8 ルール（コンパクト版）**: 底ハンド=`no_made/low/3rd`と定義します。デフォルト=CHECK。判定順: E1=`trips/overpair×4BP OOP→CHECK`→R1=`TP+→BET`→R2=`2nd/UP×(4BP/river)→BET`→T底=`底ハンド×4BP IP turn dry→BET★`→T3=`2nd/UP×SRP IP turn×draw→BET`→R3=`low/3rd×4BP OOP river→BET★`→E2=`no_made×4BP OOP river→CHECK`→R4=`no_made×river→BET★`。精度 LS=91%

**フロップ（V/S/B 分類）**
1. **SRP フロップ IP**: V=`2P+/TP+×dry-paired/UP×paired`、S=`UP×dry×gutshot×K/A/エア×strong draw×Q+`、B=`エア×low dry（低ボードでブラフ機能）`
2. **SRP フロップ OOP**: 原則 CHECK です。例外 V=`TP+×dry×A-only` / `2P+×wet/paired×low`
3. **3BP フロップ IP**: V=`TP+`、B=`エア×paired≤6/エア×dry≤9`（低ボードブラフ）。スローレイ=`セット/フラッシュ→CHECK ★`
4. **4BP フロップ**: V=`TP+→BET 20%pot（82-100%）/Ultra-dry→AI`。スローレイなし（SPR低すぎ）

**ターン（V バリュー / S セミブラフ）**
5. **SRP ターン IP**: V=`2P+`、V+S=`TP++draw`、S=`エア+gutshot以上`。スローレイ=`TP+×dry×no draw → CHECK ★`、SD守=`UP → CHECK`
6. **3BP ターン IP**: V=`2P+/TP+×dry/UP×paired×10+`、S=`no_made_hand×dry×draw ★`。SD守=`ace_high/king_high/low_pair → 全 CHECK ★`
7. **4BP ターン IP dry**: V薄=`second_pair→BET ★★（73.9%）`、B=`third_pair/no_made_hand→BET ★`、V=`TP+/2P`。SD守=`king_high/ace_high→CHECK ★`（逆転！）。FD/OESD×no_made→CHECK ★（⑤D）
8. **4BP ターン IP paired**: B=`third_pair→BET ★（90%）`、B=`ace_high→BET ★（59%）`
9. **SRP OOP ターン**: V=`2P+×wet/dry`、S=`エア+draw`
10. **3BP OOP ターン**: V=`TP+(trips含む)×dry`、S=`no_made_hand×draw ★`。SD守=`エア全（ace/king/low）→ CHECK ★`
11. **4BP OOP ターン dry**: V=`top_pair/trips`、S=`second/third_pair×gutshot ★（88-92%）`。スローレイ=`overpair/two_pair → CHECK ★`（逆転！）

**リバー（V薄 / B 純ブラフ / CHECK）**
12. **SRP リバー IP**: V=`2P+/TP+`、V薄=`second_pair/underpair`、B=`no_made_hand`。SD守=`king/ace_high/low_pair/third_pair → CHECK ★`
13. **3BP リバー IP**: V=`TP+`、V薄=`second_pair(79.5%)/underpair/third_pair(69%)`、B=`no_made_hand(61%)`。SD守=`king_high(0.4%)/ace_high(1.9%)/low_pair(10%) → CHECK ★★★`
14. **4BP リバー IP**: V=`TP+/2P+ → ALLIN`、B=`no_made_hand(58%)`、V薄=`second_pair(54%)`
15. **SRP OOP リバー**: V=`TP+/2P+`、V薄=`second_pair/underpair`、B=`no_made_hand`。SD守=`ace_high/low_pair → CHECK`
16. **3BP OOP リバー**: V薄=`second_pair(85%)/underpair(66%)/third_pair(75%)`、B=`no_made_hand×dry(50.7%)`。SD守=`king_high(0%)/low_pair(17%)/two_pair(45.6%) → CHECK ★★★`。**4BP OOP**: B=`third_pair(76%)/low_pair(58%) → BET ★★★`（逆転！）、スローレイ=`overpair(12.5%)/trips(43%) → CHECK ★`
