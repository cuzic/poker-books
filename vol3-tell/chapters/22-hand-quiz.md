---
chapter: "22"
title: "第22章　実戦ハンドクイズ"
section: "第5部 精度向上と実戦"
target_kchar: 10
status: draft
---

# 第22章　実戦ハンドクイズ

*対象: 🔰💻🎯*

> クイズの使い方：タイプを診断 → MATCHA 判定軸を歪める → アクションを決定
> 計 25 問 (5 ジャンル × 5 問)

---

## クイズの使い方

各問題で以下の順序で考えてみてください：

1. **タイプを診断** — 相手の行動・統計からタイプを特定します
2. **MATCHA 判定軸を歪める** — レンジ分布 / エクイティバケット / 形勢を補正します
3. **アクションを決定** — T_open / Score / sizing を決定します

解答は各問の下部に記載しています。考えてから読んでください。

---

## ジャンル A: タイプ診断クイズ (5 問)

---

### Q1. ライブのプレイヤー観察

🔰 真田が観察した相手の行動：

- 30 ハンド観察、参加回数 12 回 (VPIP=40%)
- 参加方法: リンプ 8 回、レイズ 4 回
- フロップでベットされて即 fold が 2 回、call 続行が 6 回
- ショーダウンで K7s をリバー call → 負け

**このプレイヤーはどのタイプでしょうか？**

<details>
<summary>解答 (クリック)</summary>

**コーリングステーション** (CS)

- VPIP 40%、PFR 推定 12〜13% → VPIP-PFR 差が大きい (パッシブ)
- リンプ 8/12 (リンプが多い) → CS の典型
- K7s でリバー call (弱いバリュー call) → CS 確定証拠
- **対応**: BTN T_open=15〜16、bluff 0%、value を厚めに

</details>

---

### Q2. HUD 統計でのタイプ判定

💻 林の HUD で観察した相手：

```
VPIP=29%、PFR=24%、3bet=11%、AFq=4.5、CBet=78%、FoldToCBet=38% (350 hands)
```

**このプレイヤーはどのタイプでしょうか？**

<details>
<summary>解答</summary>

**LAG**

- VPIP 29%、PFR 24% → 広い参加 + 高い PFR (アクティブ)
- 3bet 11% (高い) → 3bet が過剰ぎみ
- AFq 4.5、CBet 78% → bet/raise が過剰
- FoldToCBet 38% (TAG 範囲) → 自分が bet されると標準的に対応
- **対応**: T_open +3〜5 (絞る)、ブラフキャッチ範囲を拡大、call で trap

</details>

---

### Q3. 4bet 受けの反応で LAG / マニアック区別

🎯 岡田が遭遇した状況：

- 相手の VPIP=52%、PFR=38% (LAG / マニアック境界)
- hero CO open 2.5bb、相手 BTN 3bet 9bb、hero 4bet 24bb
- 相手の反応: 即 5bet jam (all in、相手スタック 92bb)

**このプレイヤーはどのタイプでしょうか？**

<details>
<summary>解答</summary>

**マニアック**

- 4bet 受けで即 5bet jam (= ブラフでも jam する) → マニアック確定
- LAG なら 4bet 受けは「バリュー (KK+/AK) のみ continue、ブラフは fold」
- 即 5bet (考えずに jam) もマニアックの典型的な行動です
- **対応**: jam 受けはバリュー (QQ+/AKs) のみ call、ブラフ 4bet は控える

</details>

---

### Q4. スキル系ルース判定

🎯 岡田が観察した相手：

- VPIP=52%、PFR=37% (見た目ルース)
- UTG では参加が少ない (10 ハンドに 1 回)、BTN ではほぼ全参加
- フロップで圧力を受けて 4 回中 3 回 fold (適切な fold)
- ショーダウン頻度 22% (低い)

**このプレイヤーは LAG か、それともスキル系ルース (TAG 近似) でしょうか？**

<details>
<summary>解答</summary>

**スキル系ルース (TAG 近似)**

- VPIP 52% でも内訳がポジション別 (UTG タイト、BTN ルース) → スキル系
- PFR 37% (高い) + フロップで適切に fold (LAG なら call が多い)
- ショーダウン 22% (低い、call で見ない) → スキル系です
- **対応**: TAG 準拠 (GTO 通り、エクスプロイトは控える)

</details>

---

### Q5. タイプ変容の検知

🔰 真田が観察した状況：

- セッション開始 1 時間: VPIP=12%、参加が少ない、bet が控えめ (ニット)
- 1 時間 30 分時点: バッドビート敗北 (-100bb)
- 直近 20 ハンド: 参加 14 回、大きな bet を連発

**どう判断すべきでしょうか？**

<details>
<summary>解答</summary>

**マニアック化 (チルト)**

- 急変前: ニット (VPIP 12%、参加が少ない)
- バッドビート後: 参加 70%、大きな bet を連発 → マニアック化中
- **対応**: タイプ仮説を「ニット」→「マニアック化中」に更新、T_open +8〜10 で絞る、jam 受けは強気に行く
- スタックが減ったり時間が経つと元のニットに戻る可能性 → 20 ハンドごとに再評価がおすすめです

</details>

---

## ジャンル B: プリフロップ調整クイズ (5 問)

---

### Q6. ニット BB 相手の BTN T_open

🔰 真田が BTN にいます。BB は確定ニット (VPIP=10%、200 hands)。

**BTN T_open はいくつに設定すべきでしょうか？**

<details>
<summary>解答</summary>

**T_open = 13〜14** (-4〜5)

- 通常 BTN T_open = 18
- 確定ニット相手はスチール利益を最大化 → -4〜5
- 13〜14 で Score=13 のハンド (K♠5♠ Score=13 等) も open 範囲に入ります
- ニット BB はほぼ 3bet をしてこず、すぐに fold します

</details>

---

### Q7. マニアック左隣の T_open

💻 林が CO にいます。BTN がマニアック (確定、VPIP=58%、PFR=42%)。

**CO T_open はいくつに設定すべきでしょうか？**

<details>
<summary>解答</summary>

**T_open = 28〜30** (+8〜10)

- 通常 CO T_open = 20
- マニアック左隣 → 3bet ジャムが頻発 → T_open +8〜10
- QQ+/AKs まで絞りましょう
- cold call で IP プレイも併用 (3bet で 4bet jam を避ける戦略)

</details>

---

### Q8. LAG opener vs hero BB defense

🎯 岡田が BB にいます。CO は LAG (PFR=28%、3bet=12%)。

CO open 2.5bb。**hero T_call と T_3bet はいくつに設定すべきでしょうか？**

<details>
<summary>解答</summary>

- **T_call = 11** (通常 16 → -5、広げる)
- **T_3bet (バリュー) = 28〜30** (-2〜4、より早く 3bet)
- **T_3bet (ブラフ) = 拡大 +5%pt** (LAG の open レンジは広いため)

LAG の open レンジは広いので、相対的に hero のディフェンスレンジも広げます。中強度のハンドも call できますし、強いハンドではより早めに 3bet していきましょう。

</details>

---

### Q9. CS リンプ iso

🔰 真田が BTN にいます。CO がリンプしています (CS 確定、VPIP=47%)。BB / SB は通常タイプ。

hero は A♠T♣ を持っています。**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**iso 5bb (raise)**

- CS リンプには iso (単独 raise) がおすすめです
- iso サイズ: 5bb (CS を heads-up に持ち込む戦略)
- A♠T♣ は iso 範囲 (CS 相手なら -2〜3 で Score=19 → open 範囲)
- call (limp behind) は MW 化のリスクがあるため、iso を優先しましょう

</details>

---

### Q10. ニット 3bet 受け

💻 林が BTN にいます。SB が確定ニット (PFR=8%、3bet=1%、200 hands)。

hero open 2.5bb with JJ → SB 3bet 12bb。**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**fold** (JJ も fold)

- ニットの 3bet は KK+/AK がほぼ確定 (3bet=1% = 最上位カテゴリ のみ)
- JJ の Equity vs {KK+/AK} = 約 30% → call/4bet は適切ではありません
- 通常の SB 3bet なら JJ は call/4bet 候補ですが、ニット相手では **fold** がおすすめです
- 例外: ニットが直前にバッドビートでチルト中なら call 検討も可能

</details>

---

## ジャンル C: フロップ調整クイズ (5 問)

---

### Q11. CS 相手のフロップ Cbet サイズ

🔰 真田が BTN open with AQ、CS BB call (確定)。

フロップ A♣8♦4♠ (hero トップペア)。

**Cbet サイズはいくつにすべきでしょうか？**

<details>
<summary>解答</summary>

**75% pot** (大きめ)

- CS は call が過剰ぎみ → サイズを大きくしてもバリュー回収できます
- 50% でも OK ですが、CS は薄いハンドでも call するので 75% で利益を最大化しましょう
- **オーバーベット (125%+) は禁止** — CS でも「大きすぎ」で fold する場合があります

</details>

---

### Q12. ニット相手の bluff Cbet 判断

💻 林が BTN open with 9♥8♥、ニット BB call (確定、FoldToCBet=70%)。

フロップ K♣5♦2♠ (hero エア、9♥8♥ はドロー なし)。

**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**bluff Cbet 33%**

- ニット相手の FoldToCBet=70% → bluff Cbet が高い EV を期待できます
- サイズは 33% で十分 (小さなサイズで fold を取れる)
- ニットの K-high call レンジは Kx がほぼ確定で、ペアなしは fold する
- 9♥8♥ は backdoor straight + backdoor flush のエクイティがあるため、call されてもターンで継続できます

</details>

---

### Q13. LAG の CR 対応

🎯 岡田が CO open with KK、LAG BTN call。

フロップ T♥7♠4♦、CO Cbet 50% → LAG CR (3x = 75%)。

**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**call** (raise も検討ですが、call がより安全)

- LAG の CR はブラフが半分以上 (50%+) → KK のオーバーペアで十分受けられます
- raise (re-raise) するとLAG が 4bet jam してくる場合があります (vs set のリスク)
- call で受けて、ターン以降の動きで形勢を再評価しましょう
- ターン scare card (A、ストレート/フラッシュ完成) → より慎重に
- ブランクターン → call 続行 or bet retake

</details>

---

### Q14. マニアック相手の set スロープレイ

🔰 真田が BTN open with 88、マニアック BB call。

フロップ A♠8♣4♦ (hero set)。

**Cbet すべきか、check すべきでしょうか？**

<details>
<summary>解答</summary>

**check** (slowplay trap)

- マニアック相手のセットは **check trap** がおすすめです
- check → マニアック bet 確率 70%+ → call で誘導できます
- bet (Cbet 50%) するとマニアックが「ブラフ Cbet」と判断して降りる可能性があります
- check call で 3 ストリート分の利益を取りに行きましょう
- ターン以降の動きで raise / call を判断します

</details>

---

### Q15. MW (3way) でのフロップ判断

💻 林が BTN open with AK、CS SB call + マニアック BB call (3way)。

フロップ Q♥8♣4♦ (hero エア、ドロー なし)。

**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**check fold (Cbet しない)**

- MW (3way 以上) でブラフ Cbet は禁止 (5 原則の 1)
- AK のエアではエクイティが不足しており、3 人いれば誰かに Qx があります
- bluff Cbet するとCS が call、マニアックが raise する可能性があります
- check → ターンで board の変化を見て再判断しましょう
- 例外: ターンで A が落ちる → bet 検討 (top pair に昇格)

</details>

---

## ジャンル D: MATCHA 軸調整クイズ (5 問)

---

### Q16. レンジ分布の見立て補正

🎯 岡田が BTN open with K♠T♠、ニット BB call。

フロップ K♣9♣6♦。Vol2 ではこの板は「混在型」(密集 + 2 極化の中間)。

**ニット相手では、レンジ分布の見立てをどう補正すべきでしょうか？**

<details>
<summary>解答</summary>

**2 極化型に補正**

- ニットの call レンジは「Kx + 大きな PP (TT+) + 強 FD」と限定的です
- 混在型 → 2 極化型に補正しましょう
- 結果: hero のトップペア (KT) は薄いバリュー (相手も K か overpair)
- **対応**: Cbet small (33%)、ターンでバレル削減、リバーで bet を慎重に

</details>

---

### Q17. エクイティバケットの見立て補正 (vs LAG)

🔰 真田が BB defense vs LAG SB raise。

フロップ J♠T♣8♦、LAG SB Cbet 75%。

hero は 9♥7♥ (gutshot, BDFD)。Vol2 通常では「弱ハンド (call 不可)」。

**LAG 相手ではどう補正すべきでしょうか？**

<details>
<summary>解答</summary>

**「良ハンド」相当に昇格**

- LAG の Cbet は 75% がブラフで、レンジが広い → hero のエクイティバケットを 1 段階上げましょう
- 9♥7♥ (gutshot=4 outs, BDFD=1 out) → 通常 Equity 18%
- LAG 相手なら「ブラフキャッチ範囲」として call が OK
- ターンで形勢を再評価します (LAG が check したら call で誘い、bet 続行ならドロー完成待ち or fold)

</details>

---

### Q18. 形勢の歪み (vs マニアック)

💻 林が BTN call (cold call) with TT、マニアック CO open。

フロップ Q♣7♠4♦。マニアック CO bet 100% pot。

Vol2 通常では TT (アンダーペア) は「劣勢」帯。

**マニアック相手ではどう補正すべきでしょうか？**

<details>
<summary>解答</summary>

**劣勢 → 五分五分に格上げ → call**

- マニアックの 100% bet はブラフの含有率が 50%+ (極端な 2 極化)
- TT の Equity vs {Qx + ブラフ} = 約 50%
- 通常の TAG 相手なら fold ですが、マニアック相手は call がおすすめです
- ターンで scare card (overcard) なら fold 候補、ブランクなら call 続行

</details>

---

### Q19. 12 cells grid の補正

🎯 岡田が BTN open with A♠5♠、CS BB call。

フロップ J♣8♦3♥。Vol2 12 cells grid では:
- hand: エア (A high)
- board: dry

通常の grid 値は「Score 0 (low)」。

**CS 相手ではどう動くでしょうか？**

<details>
<summary>解答</summary>

**bluff Cbet は控える、check fold**

- CS は call が過剰ぎみ → bluff Cbet は損失になります
- 12 cells grid の Score 0 (エア on dry) はそもそもブラフ候補ですが…
- CS 相手では bluff freq=0% (絶対禁止) です
- check で一旦諦めて、ターンで board の変化を見ましょう
- 例外: ターンで A が落ちる → bet 検討 (top pair に昇格)

</details>

---

### Q20. vs CR 補正 (タイプ別)

🔰 真田が CO open with TT、LAG BTN call。

フロップ 9♣6♦2♠、CO Cbet 50% → LAG BTN CR (2.5x)。

Vol2 MATCHA Score 公式で TT (overpair) を計算し、LAG 相手の調整を踏まえて判断してください。

**LAG 相手ではどう判断するでしょうか？**

<details>
<summary>解答</summary>

**DEF 閾値補正 → call (T_raise=49 を適用)**

- TT on 9♣6♦2♠ = TP+ × dry × vs CR (DEF) → **DEF T_raise=49 を適用**
- 公式 Score = Grid[TP+][dry] + 4×pot = 38 + 8 = 46 → T_raise=49 では **call** (46 < 49)
- GTO CALL 61%。DEF 閾値補正で自動的に call に収束します
- LAG 補正 (+3) もあり call の信頼度は高いです (LAG CR はブラフが 50%+)
- raise (re-raise) はリスク: LAG の本当のナッツ CR への支払いになる場合があります
- 比較: ニット相手なら CR はほぼバリュー → call → fold 寄りに判断

</details>

---

## ジャンル E: リバー判断クイズ (5 問)

---

### Q21. ニット相手のリバーオーバーベット

🔰 真田が BTN open with K♥T♥、ニット BB call (確定)。

フロップ Q♠8♦4♣ (Cbet 33% → call)
ターン 2♥ (check → check)
リバー A♠ (scare overcard)

**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**bluff overbet 150%**

- ニット相手 + scare card (overcard) → 最高のブラフチャンスです
- ニットの call レンジは Qx が中心 → A overcard で大半が fold します
- サイズは overbet (150%) で fold equity を最大化しましょう
- 失敗時のコストは大きいため、ニット判定の確信度が高い場合のみおすすめです
- K♥T♥ は showdown value がないため、bluff or fold の選択になります

</details>

---

### Q22. CS 相手のリバーバリューサイズ

💻 林が BTN open with AQ、CS BB call。

フロップ A♣8♦4♠ (Cbet 50% → call)
ターン T♣ (bet 75% → call)
リバー 3♦

hero は A♣Q♦ (top pair top kicker)。

**リバーサイズはいくつにすべきでしょうか？**

<details>
<summary>解答</summary>

**50〜75% bet** (ミディアム)

- CS は call が過剰ぎみ → value をしっかり取りましょう、ただし overbet は避けます
- 50% で確実に call、75% で薄いバリューも回収できます
- 100%+ は CS でも fold が増える傾向 (「大きすぎ」感)
- 3 バレル目で CS 相手は最大の利益チャンスです

</details>

---

### Q23. LAG 相手のオーバーベット受け

🎯 岡田が BB defense vs LAG BTN raise。

フロップ K♣8♦4♠ (Cbet 50% → call)
ターン 2♥ (bet 75% → call)
リバー T♣、LAG BTN bet 150% (overbet)

hero は K♥T♠ (top + 2nd pair = 2 pair on river)。

**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**call**

- LAG の overbet にもブラフが含まれています (LAG はオーバーベット濫用傾向)
- K♥T♠ (top + 2nd pair on river = K♣T♣ 等の 2 pair) は LAG 相手で call 範囲です
- LAG のレンジ: バリュー (set, 2 pair stronger) + ブラフ (busted draw)
- Equity 計算: 約 40%、call 必要 Equity 38% (overbet 150%) → ギリギリ call が可能です
- 例外: LAG の overbet が初めて (前 2 ストリート check の後の overbet) なら、バリュー寄りで fold 検討も

</details>

---

### Q24. マニアック相手のチェック誘導

🔰 真田が BTN open with set 88、マニアック BB call。

フロップ A♠8♣4♦ (check trap、マニアック bet → call)
ターン 2♥ (check、マニアック bet → call)
リバー 9♣

マニアック BB bet 200% pot (overbet)。

**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**call (snap)**

- マニアック相手のセットはバリュー全力で fold は禁止です
- リバー 200% overbet も snap call しましょう
- マニアックの 200% は両極 (ナッツ or ブラフ)、ブラフの確率は 50%+
- set 88 (3 of a kind) はストレート (5678 や 6789 のみ負け) 以外で勝ちます
- 比較: ニット相手の同じ overbet なら fold が必須です

</details>

---

### Q25. TAG 相手のリバー微調整

💻 林が CO open with AK、TAG BTN call。

フロップ A♣8♦4♠ (Cbet 50% → call)
ターン T♣ (bet 75% → call)
リバー 3♦、CO check (hero が check)

TAG BTN bet 100% pot。

hero AK (top pair top kicker)。

**どうするべきでしょうか？**

<details>
<summary>解答</summary>

**call** (call が標準です、TAG 相手は GTO 通り)

- TAG の bet レンジ: バリュー (Ax の強いキッカー？、2 pair, set) + ブラフ (busted FD/SD)
- AKo は AKs/AQ の強いキッカーに負けることはありますが、その他では勝ちます
- GTO ベースでは TPTK は call 範囲です
- TAG のリバーブラフ頻度は約 33% 想定で、AK はエクイティが十分です
- **観察ポイント**: TAG のリバーブラフが過去 10 ショーダウンで何回出たか確認しましょう
  - 5 回中 1 回程度 (= fold タイプ) → fold 寄り
  - 5 回中 2 回出ている (= 標準) → call がおすすめ

</details>

---

## クイズ総評

25 問中、以下を目安に自己採点してみてください：

- 22 問以上正解 → エクスプロイトマスター
- 18〜21 問正解 → 本書の理解は深く、実戦投入が可能です
- 13〜17 問正解 → タイプ別章を再読することをおすすめします
- 12 問以下 → 第 1 部 (診断) から再読がおすすめです

間違えた問題は **「ジャンル別の弱点」** を示しています。

- ジャンル A 弱: 第 1〜4 章を再読
- ジャンル B 弱: 第 11 章を再読
- ジャンル C 弱: 第 12 章を再読
- ジャンル D 弱: 第 5 章 (5 軸) を再読
- ジャンル E 弱: 第 14 章を再読

---

## 最後に

本書を通読していただきありがとうございました。

エクスプロイトは「相手の偏りを活用する」技術です。MATCHA の判定軸を歪めることで、GTO の外側で稼ぐことができます。これが Vol3 (MATCHA Exploits) の核心です。

実戦では本書のテンプレート的な適用ではなく、**観察 → タイプ判定 → MATCHA 軸の歪め → アクション** の 4 段階フローを意識的に回してみてください。最初は時間がかかるかもしれませんが、習慣化すれば瞬時の判断ができるようになります。

観察ノート (第 19 章) を手元に置き、ショーダウンを記録して、自分のエクスプロイト精度を上げていくことをおすすめします。

付録 A〜D には実用的なまとめ表を掲載しています。実戦の参考にしてください。

詳細な poker-drill 練習は **poker-drill アプリ** でできます。本書全章対応の deck が用意されています。

> **健闘を祈ります** — エクスプロイトの旅はこれからです。

---
