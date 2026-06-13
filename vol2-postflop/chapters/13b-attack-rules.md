# 第 13b 章　アタックルール — BET/CHECK の決定ロジック

## 14.1 アタックとは

**アタック** = 自分から最初に賭けを開始する（BET / C-BET）行動。
ディフェンス（相手のBETに対して call / raise / fold を選ぶ）とは別のシナリオです。

本章は「相手がチェックした後、または自分がファーストアクション」の局面で
**どの条件なら BET し、どの条件なら CHECK するか** を決定ロジックとして示します。

精度根拠: 6,418 hands × 16 シナリオの GTO Wizard 実測データで検証。
全体精度 **81.09%**（v9f、DT 上限 83.2% に対し −2.1pp）。
ランクベース閾値を導入した結果、旧版 v6d（76.3%）から +4.8pp 向上。

## 14.2 なぜ MATCHA Score を使わないのか

MATCHA Score（Grid + DV×mult + 2oc + 4pot − 2bs）は **ディフェンス専用** の公式です。
アタック判断に Score を使うと、ロジックが逆転するケースが生じます。

| ハンド × board | Score の示す行動 | アタックの正解 |
|---|---|---|
| TP+ × paired (SRP) | Grid=10 → fold 相当 | **BET**（ペアボードで TP+ は相対的に強い） |
| UP × paired (SRP) | Grid=40 → call 相当 | **BET**（ペアボードで UP が値上がりする） |
| 2P+ × dry (4BP) | Grid=25 → call 相当 | **CHECK**（SPR≈2 ではトラップが有効） |

Score がアタックに使えない理由: Grid 値は「相手のベットサイズに対する自ハンドの防御価値」を表しており、
「自分からベットしたときに相手が降りるかどうか」は別の問いです。

## 14.3 SRP フロップ IP — 判断ロジック

SRP（SPR ≈ 8〜12）で相手（OOP）がチェック。自分（IP）のアクション。

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

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+ | **BET** | 最強ハンドは全ボードでバリュー確定。相手のどのコール/フォールドも EV プラス |
| ② | TP+ × dry × (draw OR Q+high) | **BET** | Q/K/A ボードは相手レンジが連動。7-5-2 等の低 dry では TP+ も CHECK |
| ③ | TP+ × paired | **BET** | ペアボードで TP+ が相手レンジを支配 |
| ④ | UP × paired（A-board 除く） | **BET** | ペアボードは相手の 7x/8x 等が減り自ペアの相対価値が上昇 |
| ⑤ | UP × dry × gutshot × K/A-high | **BET** | K/A-high dry のみ gutshot UP が機能。低 dry は CHECK |
| ⑥ | エア × dry × strong draw × K/A-high | **BET** | FD/OESD/combo のみ K/A ボードで BET。低 dry の strong draw も CHECK |
| ⑦ | エア × wet × strong draw × Q-high+ | **BET** | Q 以上の wet ボードで strong draw が機能 |
| ⑧ | エア × paired + draw | **BET** | ペアボードは相手レンジが弱まるため gutshot でも機能 |

> **ランク閾値の考え方**: 「ボードが K/A-high（top rank ≥ 13）か否か」で BET/CHECK が分かれる。
> 低ボード（top rank ≤ J=11）は相手レンジが連動しにくく、弱い手の攻撃効率が落ちる。
> "strong draw" = FD / OESD / combo_draw（gutshot と twocards_bdfd は対象外）

**OOP フロップ SRP**: 原則 CHECK。以下の例外のみ BET:
- TP+ × dry × no-draw × A-high のみ → BET（donk bet として A-board で機能）
- 2P+ × wet × no-draw × 6-high 以下 → BET
- 2P+ × paired × no-draw × 5-high 以下 → BET
- 2P+ × dry × no-draw × A-high のみ → BET

## 14.4 3BP フロップ IP — 判断ロジック

3-bet pot（SPR ≈ 4〜6）。相手の 3bet レンジは AK / QQ+ 寄りにコンデンスされています。

```
TP+ または 2P+? → BET（ただし TP+×wet×no-draw×J-high 以上は CHECK）
エア × paired × low (≤6-high)? → BET
エア × dry × no-draw × ≤9-high? → BET
UP × dry × gutshot × K-high 以上? → BET
→ CHECK
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | TP+ 以上（wet×no-draw 除く） | **BET** | 相手のコンデンスされたレンジに対して TP+ 以上がバリューライン |
| ② | TP+ × wet × no-draw × ≤9-high | **BET** | 低 wet ボードは TP+ でも BET（9 以下の wet）。J-high 以上 wet×no-draw は CHECK |
| ③ | エア × paired × ≤6-high | **BET** | 低ペアボードは相手レンジが弱い。7 以上のペアは CHECK |
| ④ | エア × dry × no-draw × ≤9-high | **BET** | 9 以下のドライ低ボードでエアがブラフとして機能（56% BET） |
| ⑤ | UP / エア × wet/paired×high | **CHECK** | 相手が強いレンジを持つ局面でブラフは機能しない |

> SRP との違い: SRP では「UP×dry+draw → BET」「UP×paired → BET」等の例外があったが、
> 3BP では **TP+ 以上 + 低ボード限定の例外** に絞る。精度 84.7%。

## 14.5 4BP フロップ IP — 逆転ロジック

4-bet pot（SPR ≈ 2）。ポットが大きく、スタックが浅い。

```
2P+?                                          → CHECK（理由: トラップが有効）
UP × wet × no-draw?                           → CHECK
UP（その他）?                                 → BET（理由: スタック圧力）
TP+ × dry × 9-high 以下?                     → CHECK（低 dry は TP+ も CHECK）
TP+ × dry × 10-high 以上?                    → BET
TP+ × wet × no-draw × Q-high 以上?           → CHECK（高 wet は CHECK）
TP+ × wet（その他）?                          → BET
TP+ × paired?                                 → CHECK（TP+ も slowplay）
エア × dry × no-draw × ≤A前（A 除く）?       → BET（A-high dry は CHECK）
→ CHECK
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+ | **CHECK** | SPR≈2 では BET しても弱い手はフォールド → EV 低下。CHECK で強い手を誘う |
| ② | UP × (dry/paired)、UP × wet+draw | **BET** | ポット大 × スタック浅 → UP のベットが「フォールドかオールイン」を迫る圧力 |
| ③ | TP+ × dry × 10-high 以上 | **BET** | 高い dry ボード（T/J/Q/K-high）で TP+ はポラライズバリュー |
| ④ | TP+ × dry × 9-high 以下 | **CHECK** | 9 以下の低 dry では TP+ も CHECK（相手レンジが disconnected） |
| ⑤ | TP+ × wet × no-draw × J-high 以下 | **BET** | 低 wet は TP+ でも BET |
| ⑥ | TP+ × paired / TP+ × wet × Q-high+ no-draw | **CHECK** | ペアは slowplay、高 wet no-draw も CHECK |
| ⑦ | エア × dry × no-draw × non-A | **BET** | A-high 以外の dry ボードでエアをプレッシャーベット（74% BET） |

> **4BP の構造**: 「強い手（2P+）はトラップ、弱い手（UP）はプレッシャー」。
> SPR が浅いほど、ポット/スタック比が大きいベットが相手に大きな決断を迫る。

## 14.6 ターン IP — 判断ロジック

フロップで双方チェック後（または delayed C-BET）、ターンで相手がチェック。

### SRP ターン IP

```
2P+?                                 → BET
TP+ かつ dry かつ draw あり?        → BET（no draw は CHECK）
TP+ かつ draw あり?                 → BET
エア かつ draw あり (gutshot 以上)? → BET（no draw は CHECK）
→ CHECK（UP は draw あっても CHECK）
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+ | **BET** | ターンでも最強ハンドはバリュー確定 |
| ② | TP+×dry + draw | **BET** | dry ターンでも draw なし TP+ は 40% BET = CHECK 多数。draw で補完必須 |
| ③ | TP+×dry×no draw | **CHECK** | 40.3% BET — draw なし TP+ は dry でも CHECK が GTO 多数（反直感） |
| ④ | TP+×wet + draw | **BET** | draw が加わった TP+ は wet でもバリュー兼セミブラフ |
| ⑤ | エア + gutshot 以上 | **BET** | gutshot エア×dry 76%、OESD/FD 85〜100% のセミブラフ値 |
| ⑥ | UP（draw あり） | **CHECK** | UP はターンで BET しても相手に「より良い手がある」可能性が高い。Draw があっても原則 CHECK |

> **重要**: TP+×dry は **draw なし = CHECK**（逆直感）。GTO はターン到達後に dry ボードの TP+ を slowplay する。
> **SRP ターン IP 精度**: 85.8%（v6d 改訂後、全シナリオ中最高クラス）

### 3BP ターン IP

```
2P+?                                              → BET
TP+ かつ dry?                                    → BET
TP+ かつ paired × no-draw × A-only?              → BET（K 以下は CHECK）
TP+ かつ gutshot?                                → BET
UP × paired × 10-high 以上?                      → BET（10 以下の低ペアは CHECK）
エア × dry × no-draw × ≤8-high?                 → BET（9 以上の dry no-draw は CHECK）
エア × dry × draw あり?                          → BET
エア × wet × gutshot?                            → BET
エア × paired × strong × 10-high 以上?          → BET（9 以下の strong draw は CHECK）
エア × paired × no-draw × ≤9-high?              → BET（10 以上は CHECK — 逆方向！）
→ CHECK
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+ | **BET** | 3BP でも最強ハンドは継続バリュー |
| ② | TP+×dry | **BET** | dry ターンでは TP+ が相手の 3bet レンジに対して優位（85% BET） |
| ③ | TP+×paired×A-only | **BET** | A-board ペアのみ TP+ が BET。K 以下のペアは CHECK（25% BET） |
| ④ | TP+×gutshot | **BET** | gutshot で強化された TP+ はセミブラフ価値が付加される |
| ⑤ | UP×paired×10+ | **BET** | J/Q/K/A-high ペアで UP に価値が出る。9 以下の低ペアは CHECK |
| ⑥ | エア×dry×≤8-high×no-draw | **BET** | 8 以下の低 dry no-draw エアはブラフが機能（delayed bluff） |
| ⑦ | エア×dry+draw | **BET** | ドロー付きエアはセミブラフとして機能 |
| ⑧ | エア×wet+gutshot | **BET** | 69.4% BET — wet + gutshot の組合せはブラフ頻度が高い |
| ⑨ | エア×paired×strong×10+ | **BET** | 高ペアボードで strong draw エアがブラフとして機能 |
| ⑩ | エア×paired×no-draw×≤9 | **BET** | 低ペアボードはエア no-draw がブラフとして機能（逆直感） |

### 4BP ターン IP — フロップ逆転の継続

```
2P+ × dry × no-draw × ≤8-high?               → CHECK（低 dry は 2P+ も CHECK）
2P+ （その他）?                               → BET
TP+ × paired × no-draw × ≤7-high?            → CHECK（低ペアは CHECK）
TP+ （その他）?                               → BET
UP × wet?                                     → BET（no-draw 含む）
UP × paired × no-draw × Q-high 以上?         → CHECK（J 以下は BET）
UP （その他）?                                → BET
エア × dry × gutshot × Q-high 以上?          → BET（J 以下は CHECK）
エア × dry × no-strong?                      → BET（strong draw は CHECK）
エア × wet × no-draw?                        → BET（no-draw のみ BET）
→ CHECK（エア×wet×strong/gutshot は CHECK）
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+（非 low dry） | **BET** | SPR≈1.5 でオールイン圧力として機能 |
| ② | 2P+×dry×≤8×no-draw | **CHECK** | 低 dry で 2P+ も CHECK（レンジが disconnected） |
| ③ | TP+（非 low-paired） | **BET** | TP+ はほぼ全ての状況で BET |
| ④ | UP×dry/paired×≤11 / UP×wet | **BET** | Q-high 以下のペアまで UP が BET。wet も BET |
| ⑤ | エア×wet×no-draw | **BET** | no-draw のみ BET（FD/gutshot は CHECK — 相手レンジと正面衝突） |
| ⑥ | エア×dry×gutshot×Q+ | **BET** | Q/K/A-high dry で gutshot エアが機能（J 以下は CHECK） |
| ⑦ | エア×dry×no-strong | **BET** | strong draw 以外の干渉しないエアを bluff |

> 4BP ターンの変化点: フロップでは「2P+ → CHECK（トラップ）」だったが、
> ターンでは SPR がさらに低下し、2P+ でも BET してオールインを狙う局面になる。

## 14.7 OOP ターン — 判断ロジック

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

OOP ターン SRP の基本は **CHECK**。2P+×wet/dry（バリュー）と draw 付きエアが BET 候補。
ランク閾値: 2P+×wet は 10-high 以上のみ BET、2P+×paired は 10 以下のみ BET。

### 3BP ターン OOP

```
TP+ × paired × no-draw × ≤10-high?  → BET（11 以上は CHECK）
TP+（その他）?                        → BET
2P+ × wet?                           → BET
2P+ × paired × 7-high 以上?          → BET（6 以下は CHECK）
エア × strong × (dry/wet)?            → BET
エア × strong × paired × ≤10-high?   → BET（J 以上のペアは CHECK）
エア × paired × gutshot × 12-high 以上? → BET（11 以下は CHECK）
→ CHECK
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | TP+ × non-high-paired | **BET** | 3BP OOP TP+ dry 81% / wet 69%。高ペアボード（Q/K/A）は CHECK |
| ② | 2P+×wet | **BET** | wet で強い手 + OOP ポジション不利の補填として BET |
| ③ | 2P+×paired×7+ | **BET** | 中〜高ペアボードで 2P+ がバリュー |
| ④ | エア×strong×(dry/wet) | **BET** | dry/wet のエア strong draw は OOP でもブラフとして機能 |
| ④' | エア×strong×paired×≤10 | **BET** | ペアボード strong は low のみ BET（J/Q/K/A ペアは CHECK） |
| ⑤ | エア×paired×gutshot×K+ | **BET** | A-high ペアボードで gutshot エアが機能（12 以上） |

### 4BP ターン OOP

```
TP+ × wet × no-draw?               → CHECK
TP+ × paired × 11-high 以上?      → CHECK（10 以下は BET）
TP+ × dry × no-draw × A-only?     → CHECK（K 以下は BET）
TP+（その他）?                      → BET
2P+ × wet?                         → BET
2P+ × paired × 10-high 以上?       → BET（9 以下は CHECK）
UP × dry + draw?                    → BET
エア × dry × gutshot × ≤9-high?    → BET（10 以上は CHECK）
→ CHECK
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | TP+（制限付き） | **BET** | 4BP OOP TP+。wet no-draw/高ペア/A-high dry は CHECK |
| ② | 2P+×wet | **BET** | wet ボードで 2P+ はバリューライン |
| ③ | 2P+×paired×10+ | **BET** | 高ペアボードで 2P+ が機能 |
| ④ | エア×dry×gutshot×≤9 | **BET** | 低 dry でエア+gutshot がブラフとして機能 |

## 14.8 リバー IP — 判断ロジック

フロップ・ターン双方チェック後、OOP がリバーをチェック（delayed attack 局面）。

### SRP リバー IP

```
2P+?                                   → BET
TP+ × (dry または paired)?             → BET
UP × paired × ≤11-high?               → BET（Q/K/A ペアは CHECK）
エア × (dry または wet)?              → BET
エア × paired × ≤11-high?             → BET（Q/K/A ペアは CHECK）
→ CHECK（TP+×wet → CHECK）
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+ | **BET** | ショーダウン価値が高く、BET してもコールされる手に勝っている |
| ② | TP+ × dry/paired | **BET** | 双方チェックが続いた後、TP+ は相手のレンジに対して依然価値を持つ |
| ③ | TP+ × wet | **CHECK** | 相手のチェックが強いレンジを示唆しうる。wet では慎重に |
| ④ | UP × paired × ≤J-high | **BET** | J 以下のペアボードで UP がブラフとして機能。Q/K/A ペアは CHECK |
| ⑤ | エア × dry/wet | **BET** | 全 3 チェック後の delayed bluff として機能 |
| ⑥ | エア × paired × ≤J-high | **BET** | J 以下のペアボードでエアがブラフとして機能（Q/K/A ペアは CHECK） |

> リバー「エア全 BET」の直感: フロップ・ターンとチェックが続いた後、IP のエアはどのボードでも「相手が弱い」を意味する。
> ただし Q/K/A-board のペアは相手が強い手を持ちやすく、エア/UP は CHECK に転換。

### 3BP リバー IP

```
TP+ または 2P+?                       → BET
エア × (wet または dry)?              → BET（常に BET — K/A も例外なし）
エア × paired × no-draw × ≤11-high?  → BET（Q/K/A ペアは CHECK）
→ CHECK（UP → CHECK）
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | TP+ / 2P+ | **BET** | SPR≈3 では TP+ 以上がリバーで明確なバリュー |
| ② | エア × wet | **BET** | ドローミスのエアが wet ボードでブラフとして機能 |
| ③ | エア × dry | **BET** | 74% BET — K/A-high でも例外なく BET（旧版 K/A → CHECK は誤り） |
| ④ | エア × paired × ≤J-high | **BET** | J 以下のペアボードでエアのブラフが機能 |
| ⑤ | UP | **CHECK** | UP は「バリューとして弱く、ブラフとして機能しない」中途半端な強さ |
| ⑥ | エア × paired × Q/K/A-high | **CHECK** | 高ペアボードではエアのブラフ効率が落ちる |

### 4BP リバー IP

```
2P+?          → ALLIN
TP+?          → BET / ALLIN
UP かつ paired? → ALLIN
→ CHECK
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+ | **ALLIN** | SPR≈1 ではポット全額が最大バリュー。チェックはナッツを捨てることになる |
| ② | TP+ | **BET/ALLIN** | 4BP リバーでは TP+ もオールインバリューライン |
| ③ | UP × paired | **ALLIN** | ペアボードの UP はブラフとして圧力をかけられる唯一の局面 |
| ④ | エア | **CHECK** | 4BP の強いレンジにエアのブラフは機能しない |

> 4BP の流れ: フロップ 2P+→CHECK（トラップ）→ ターン 2P+→BET（SPR 低下）→ リバー 2P+→ALLIN（全額押す）

## 14.9 OOP リバー — polarization ロジック

フロップ・ターン双方チェック後、リバーで OOP がファーストアクション。

### SRP リバー OOP

```
TP+?                                             → BET
2P+?                                             → BET（dry/wet/paired 全て）
UP × paired × 13-high 以上（K/A）?              → BET（J 以下は CHECK）
エア × paired × ≤12-high?                       → BET（K/A ペアは CHECK）
エア × dry × no-draw × ≤10-high?               → BET（J 以上の dry は CHECK）
→ CHECK
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | TP+ | **BET** | SRP OOP リバー TP+ 80% BET — 最も明確なバリュー |
| ② | 2P+ | **BET** | 2P+ 全ボードで BET（旧「dry×K/A → CHECK」は誤り、60% BET） |
| ③ | UP × K/A-high paired | **BET** | K/A-board ペアで UP がブラフとして機能 |
| ④ | エア × paired × ≤Q-high | **BET** | Q 以下のペアボードでエアがブラフ。K/A ペアは CHECK |
| ⑤ | エア × dry × ≤10-high | **BET** | J 以下の低 dry ボードでエアがブラフとして機能 |
| ⑥ | エア × dry × J-high 以上 | **CHECK** | J/Q/K/A dry ではエア CHECK が多数 |
| ⑦ | UP × low paired / エア × wet | **CHECK** | showdown value を守る |

> **改訂**: 旧版「TP+/2P+ → BET、それ以外 CHECK」→ 新版ではランク別のエア/UP 例外あり。
> 2P+×dry は 60% BET で CHECK は誤り（旧 K/A-board → CHECK を削除）。

### 3BP リバー OOP

```
エア × dry?  → BET（74% BET — K/A-high も例外なし）
エア × paired × no-draw × ≤11-high? → BET（Q/K/A ペアは CHECK）
エア × wet/paired(high)? → CHECK
UP × dry × A-only? → BET（K 以下は CHECK）
→ BET（2P+ / TP+ / UP はすべて BET）
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | 2P+ / TP+ / UP | **BET** | 3BP OOP リバー: UP 65% / TP+ 73% / 2P+ 57% — エア以外が BET |
| ② | UP × dry × A-only | **BET** | A-board dry でのみ UP がブラフとして機能（K-board は CHECK） |
| ③ | エア × dry | **BET** | 74% BET — K/A-high でも例外なく BET（旧版 K/A → CHECK は誤り） |
| ④ | エア × paired × ≤J-high | **BET** | J 以下のペアボードで delayed bluff が機能 |
| ⑤ | エア × wet/paired×Q+ | **CHECK** | 高 wet/高ペアボードではエアのブラフ効率が落ちる |

> UP が BET する理由: 3BP SPR≈3 ではスタックが浅く、UP もリバーで適切なバリューを持つ。
> エア×dry は常に BET: K/A ボードでも 74% BET — dry ボードでの delayed bluff が有効。

### 4BP リバー OOP — UP が逆転する

```
エア? → CHECK
→ BET（UP / 2P+ / TP+ はすべて BET。UP が最強 BET カテゴリ）
```

| ルール | 条件 | アクション | 理由 |
|---|---|---|---|
| ① | UP | **BET** | 4BP OOP リバー UP 70% BET — UP が最強！SPR≈1 でプレッシャー BET として最有効 |
| ② | 2P+ / TP+ | **BET** | 2P+ 57% / TP+ 53% — バリューライン |
| ③ | エア | **CHECK** | エア 20% BET — ほぼ全て CHECK |

> **4BP OOP リバーの逆転**: SPR≈1 まで浅くなると UP が最強 BET 頻度を持つ。
> これは 4BP フロップ（UP→BET/2P+→CHECK）と同じ SPR 逆転ロジックの継続。

## 14.10 ポット種別 × ストリート 決定ロジック まとめ

### IP アタックまとめ

| | **フロップ IP** | **ターン IP** | **リバー IP** |
|---|---|---|---|
| **SRP** | 2P+ / TP+×dry-paired / UP×paired / UP×dry+draw / エア×dry-wet+strong / エア×paired+draw → BET | 2P+ / TP++draw / UP×paired / エア+draw → BET（UP は CHECK、TP+×dry no_draw → CHECK） | 2P+ / TP+×dry-paired / UP×paired / エア（全 board） → BET |
| **3BP** | TP+ 以上 / エア×paired → BET | 2P+ / TP+×dry / TP++gutshot / UP×paired / エア×dry+draw / エア×wet+gutshot → BET | TP+ 以上 / エア×wet-dry → BET |
| **4BP** | UP→BET / 2P+→CHECK（逆転） | 2P+ / TP+ / UP / エア×dry → BET | TP+ 以上 → ALLIN |

### OOP アタックまとめ

| | **フロップ OOP** | **ターン OOP** | **リバー OOP** |
|---|---|---|---|
| **SRP** | 常に CHECK | 2P+×wet/dry → BET | TP+ / 2P+ → BET |
| **3BP** | 常に CHECK | TP+ / 2P+×wet / エア×dry+draw / エア×wet+gutshot → BET | UP / TP+ / 2P+ / エア×dry → BET |
| **4BP** | 常に CHECK | TP+ → BET | UP / TP+ / 2P+ → BET（UP が最強） |

**4BP の流れを追う（2P+ を例に）**:

```
フロップ: 2P+ → CHECK（トラップ。BET してもコールは強い手のみ）
ターン  : 2P+ → BET（SPR 低下でオールイン圧力が有効に）
リバー  : 2P+ → ALLIN（SPR≈1、チェックは価値を捨てる）
```

## 14.11 SPR とロジックの関係

SPR（スタック/ポット比）がアタックロジックを支配する原理:

| SPR | 構造 | ロジック |
|---|---|---|
| ≈8〜12（SRP） | スタックが深い | UP の BET は限定的。ドロー補正が重要 |
| ≈4〜6（3BP） | 中程度 | TP+ 以上に一本化。ブラフは機能しにくい |
| ≈2（4BP フロップ） | 浅い | 強い手はトラップ、弱い手はプレッシャー（逆転） |
| ≈1.5（4BP ターン） | さらに浅い | 弱い手（UP）も BET がオールイン圧力として有効 |
| ≈1（4BP リバー） | 最浅 | 強い手は全額（ALLIN）。弱い手は CHECK |

**原則**: SPR が低いほど、ベットが相手に「フォールドかオールイン」の二択を迫る。
この圧力が有効なハンドは SPR によって変わる。

## この章で覚える項目 (16 items)

1. **SRP フロップ IP**: `2P+` / `TP+×paired` / `TP+×dry×Q/K/A-high or draw` / `UP×paired（A除く）` / `エア×dry-wet+strong×K/A-high` / `エア×paired+draw` → BET
2. **SRP フロップ OOP**: 原則 CHECK。例外: `TP+×dry×A-only` / `2P+×wet/paired×low` / `2P+×dry×A-only` → BET
3. **3BP フロップ IP**: `TP+（wet×no-draw×high 除く）` / `エア×paired×≤6-high` / `エア×dry×≤9×no-draw` → BET
4. **4BP フロップ IP**: `UP` → BET、`2P+` → CHECK（強弱逆転）。`TP+×dry×9+` → BET、`エア×dry×non-A` → BET
5. **SRP ターン IP**: `2P+` / `TP++draw` / `エア+gutshot以上` → BET、`TP+×dry×no draw → CHECK`（反直感）、`UP` は CHECK
6. **3BP ターン IP**: `2P+` / `TP+×dry` / `TP++gutshot` / `UP×paired×10+` / `エア×dry×≤8×no-draw` / `エア×dry+draw` / `エア×wet+gutshot` / `エア×paired（rank 別）` → BET
7. **4BP ターン IP**: `2P+` / `TP+` / `UP（wet×no-draw 除く）` / `エア×dry` / `エア×wet` → BET（細部はランク閾値あり）
8. **OOP ターン SRP**: `2P+×wet/dry` → BET、`2P+×paired×≤10` → BET、`エア+draw` → BET
9. **OOP ターン 3BP**: `TP+（高ペア除く）` / `2P+×wet` / `2P+×paired×7+` / `エア×strong` → BET
10. **OOP ターン 4BP**: `TP+（制限付き）` / `2P+×wet` / `2P+×paired×10+` / `エア×dry×gutshot×≤9` → BET
11. **SRP リバー IP**: `2P+` / `TP+×dry-paired` / `UP×paired×≤J` / `エア×dry-wet` / `エア×paired×≤J` → BET
12. **3BP リバー IP**: `TP+ 以上` / `エア×wet-dry（常に BET）` / `エア×paired×≤J` → BET（`UP` → CHECK）
13. **4BP リバー IP**: `TP+ 以上` → ALLIN、`UP×paired×K/A+` → ALLIN、`エア×dry×non-A` → BET
14. **SRP OOP リバー**: `TP+ / 2P+` → BET、`UP×K/A-paired` → BET、`エア×paired×≤Q` → BET、`エア×dry×≤10` → BET
15. **3BP OOP リバー**: `UP / TP+ / 2P+` → BET、`エア×dry（常に BET、K/A も例外なし）` / `エア×paired×≤J` → BET
16. **4BP OOP リバー**: `エア以外 BET`（UP が最強 BET カテゴリ — SPR 逆転）
