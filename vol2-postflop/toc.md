# 『迷わないポーカー Vol2 — ポストフロップ完全版』(MATCHA Framework 編) 目次

## 本書の位置づけ

- **シリーズ**: 『迷わないポーカー』MATCHA シリーズの Vol2
- **MATCHA acronym** (シリーズ共通): Math Algorithm of Twelve-Cell Hold'em Action
- **対象**: Cash 100bb と MTT chipEV (25/50/100/200bb) のポストフロップ
- **中核**: **MATCHA Score** — Grid 12 cells (4 カテゴリ × 3 board) + DV street 別 + 加算式の暗算公式
- **理論バックボーン**: 5 つの判定軸 + 12 cells grid + 3 つのモード + 3 つの補正
- **精度**: 154,216 spots audit で avg loss **0.3587 BB** / huge **1.49%** (旧公式比 -14% / -16%)
- **対象外**: ICM/PKO postflop (将来 Vol2.5 で対応)
- **姉妹巻**: Vol1 (MATCHA Formula、プリフロップ) / Vol3 (MATCHA Exploits、相手タイプ別)
- **連携アプリ**: poker-drill (https://poker-drill.vercel.app) — 本書公式の 200+ cards ドリル
- **用語集**: https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b

## 設計方針 (2026-06-09 大幅改訂)

旧設計 (5 軸モデル中心、 公式は巻末補論) → 新設計 (**MATCHA Score を本核に再構成**)。

理由:
- poker-drill の実装で MATCHA Score が中心ツールと確定
- 5 軸モデルは「公式の背景」として理論バックボーンに移動
- ドリルは poker-drill アプリで提供 (本書のドリル節を最小化)
- **境界・例外の解説** を強化 (paper 級の発見を織り込む)

## 暗記コスト目標

| 項目 | 数 |
|------|---:|
| 公式: Grid 12 cells + 加算式 | 13 |
| 例外: 5 ルール | 5 |
| 境界ハンド (sub-family × カテゴリ の outlier) | ~30 |
| ポット補正 + スタック補正 | ~8 |
| **計** | **~56 項目** |

vs 旧 11 専用公式の ~165 分岐 + 50 境界 = 215 項目 → **暗記コスト -74%**

---

## 序章 (ch00)

### 00. ポストフロップを 5 秒で解く
- mv (made-value) と equity の違い (確率分布としての相手レンジ)
- 旧来の専用公式 (11 個、 165 分岐) → MATCHA Score (1 公式、 56 項目) への進化
- 「暗算で 5 秒」の達成方法 — Grid 表 + 加算式
- 本書の使い方: 第 1 部で公式、 第 2 部で境界・例外、 第 3 部で背景理論
- poker-drill アプリとの連携 (200+ cards で実戦練習)

---

## 第1部: MATCHA Score 公式 (ch01-05)

> 本書の核心。 全 154,216 spots で最適化された 1 公式を 5 章で完全マスター。

### 01. 公式の全体像
- 公式: `Score = Grid[カテゴリ][board] + DV × mult[street] + 2 × oc + 4 × pot − 2 × bs`
- 判定: `Score ≥ 43 → raise / ≥ 14 → call / else fold`
- 性能: avg loss 0.3587 BB、 huge 1.49% (旧公式比 -14% / -16%)
- 公式が解いている問題: 「相手の bet 受けで call/raise/fold を 5 秒で出す」
- 5 軸の整数化 (Score = 5 軸の重み付け和)

### 02. カテゴリ — ハンドストレングス 4 段階
- **エア** (no_made_hand / king_high / ace_high)
- **アンダーペア** (second_pair / third_pair / underpair / low_pair)
- **トップペア以上** (top_pair / overpair)
- **2P+** (two_pair / set / trips / straight / flush / FH / quads / SF)
- なぜ 4 段階で十分か (data 駆動の発見、 6→4 カテゴリ 集約で性能維持)
- mv_cat 17 種類 → 4 階層の対応表

### 03. board — 3 タイプ
- **dry** (unpaired / rainbow / 非 connected)
- **paired** (同 rank ペアあり)
- **wet** (connected ≤ gap 2 or monotone)
- board 判定の手順 (3 ステップ: paired → wet → else dry)
- 旧 6 ボードファミリー との対応

### 04. DV と street multiplier — Rule of 4/2 の整数化
- DV 値: combo=4 / FD/OESD=3 / gutshot/BDFD=1 / none=0
- multiplier: flop ×3 / turn ×2 / river ×0
- Rule of 4 (out × ~8%) と Rule of 2 (out × ~4%) の系譜
- DV をなぜ カテゴリ に統合できないか (overcards との独立性)
- river で DV ×0 になる根拠 (draw 完成不可、 sensitivity 確認)

### 05. pot / bs / overcards の値
- pot: SRP=0 / vs CR=2 / 3BP=2 / 4BP=4
- bs: small_33=0 / med_75=1 / med_100=2 / overbet=3 / overbet_185=4 / allin=5
- overcards: hero の 2 枚のうち board 最高 rank より上の枚数 (0-2)
- 各軸の係数 (4×pot / -2×bs / 2×oc) の意味

---

## 第2部: Grid 12 cells と境界・例外 (ch06-09)

> 公式の数値核 + 暗記必須の境界・例外を集約。 本書の暗記項目はここに集中。

### 06. 12 cells grid の完全解説 ★本書の魔法核心

**本章は本書の最大の難所であり、 最大の発見である。**

12 cells grid は **線形ではない**。 「役が強いほど値が大きい」 でも「dry board ほど値が大きい」 でもない。 Hand × Board の **複雑な interaction** で値が増減する、 直感に反する数値表である。 この interaction を「12 の物語」 として理解することが本書の核心。

#### 12 cells 全表

|           | dry | paired | wet |
|-----------|----:|-------:|----:|
| エア       |  3 |  **5** |  1 |
| アンダーペア | 18 | **40** | 10 |
| TP+       | **38** | 10 | 31 |
| 2P+ | 25 | 28 | 23 |

#### 直感に反する 6 つの発見

1. **ミドル × paired = 40 が最高値** (ミドルなのに最強)
   - 直感: アンダーペアは中位、 paired board は trip 警戒 → 値は低いはず
   - 真実: paired board では **相手の range が wide で air-heavy** に偏り、 アンダーペアでも range 中の上位、 value 取りやすい

2. **TP+ × paired = 10 が中位の低値** (TP+ なのに paired で弱体化)
   - 直感: TP+ は強い手、 どこでも価値あるはず
   - 真実: paired board で TP+ は trip range に負ける、 ミドル paired より大幅減

3. **2P+ × dry = 25 が 2P+ × paired = 28 より低い**
   - 直感: dry こそ強い手の主戦場のはず
   - 真実: dry では over-protection 不要、 paired では 2P 〜 FH range で取りに行く価値が高い

4. **2P+ × wet = 23** が最低の2P+値
   - 直感: 2P+は wet でも強いはず
   - 真実: wet board の draw 完成 / set / straight / flush で互角、 厚すぎる value bet は逆効果

5. **エア × dry = 3 < エア × paired = 5**
   - 直感: dry の方が hero エアでも勝機あり (board 弱)
   - 真実: paired board では **相対 range** で意外と call できる (相手も air 多い)

6. **TP+ × dry = 38 vs TP+ × wet = 31** (差はわずか 7)
   - 直感: TP+ は dry だけ強く、 wet では大幅弱体化のはず
   - 真実: wet でも TP+ は **相手の draw range** に対し range advantage 持続、 31 と高値維持

#### 12 cells の 4 つの暗記原則

各 cell の数値はランダムではなく、 4 つの原則の組合せで覚えられる:

1. **paired board の wide-range effect**: 相手の range が広がる → 中位 hand (ミドル/エア) の相対価値↑、 強 hand (TP+/2P+) の相対価値↓
2. **dry board の polarization effect**: 相手の range が分極化 → TP+ 一辺倒で最強、 中位は不利
3. **wet board の equity sharing**: draw の存在で eq が共有 → 2P+の value↓、 TP+ の defense は持続
4. **エアの flat pattern**: どの board でも 1-5 の low range、 sizing/oc/pot で補正

#### 数値暗記法 (12 cells すべての値の覚え方)

| 暗記キー | 値 | 由来・連想 |
|---|---:|---|
| ミドル × paired | **40** | 最高峰、 paired bluff range の例外 |
| TP+ × dry | **38** | TPTK 王道、 dry polarization |
| TP+ × wet | 31 | 一の位 1 = "still strong" |
| 2P+ × paired | 28 | FH potential |
| 2P+ × dry | 25 | 5×5、 set/straight default |
| 2P+ × wet | 23 | dry 比 -2 = draw sharing |
| ミドル × dry | 18 | paired の半分 (40÷2-2) |
| ミドル × wet | 10 | wet で半減 |
| TP+ × paired | 10 | trip discount |
| エア × paired | 5 | wide range premium |
| エア × dry | 3 | base |
| エア × wet | 1 | floor |

#### 最適化過程 (詳細は付録 B)

- 4 カテゴリ × 3 board の 12 自由度を Optuna TPE で全 154,216 spots に最適化
- 旧 6 カテゴリ × 3 board (Grid 18) との比較で **集約しても性能向上** が確定
- 「ミドル × paired = 40」 は data から発見された値で、 GTO 理論から演繹的に導出するのは困難
- これこそが本公式の **最大価値** — 「データが教えてくれた事実」 を 1 つの整数に凝縮した

### 07. 境界ハンド集 — Hand Strength の outlier
- **逆 U 字パターン**: set 9% → 2P 67% peak → エア 37% (paired board)
- **ツーペア 67% peak の意味** — paired board で意外にも 2P が最も bet されない
- ボトムペア vs アンダーペア の境界
- mv_cat 別 outlier:
  - underpair (board 最高 rank より下のペア)
  - second_pair vs third_pair
  - top_pair の kicker 強弱 (TPTK vs TPGK vs TPWK)
- 境界ハンド ~15 個の暗記リスト

### 08. 境界ボード集 — Range Morphology の修正
- 現行 heuristic vs 実 GTO の **一致率 19% (4/21)** という現実
- **paired board の特殊性**:
  - paired × 2P = 0% (set/FH に劣るため)
  - paired × overpair が wet 寄り
- **low_dry の修正** (旧分類は overshoot)
- **wet 内の sub-family**:
  - dynamic_2tone vs monotone vs straight-heavy connector
- 77 boards cross-tab から抜粋した outlier ~15 個

### 09. 例外 5 ルール (huge loss 回避)
- 公式 pred と GTO best の confusion 分析 (2,303 huge spots)
- 例外 1: **TP+ × wet × flop × SRP** → fold (公式 pred=call、 n=350、 avg 14.5 BB)
- 例外 2: **2P+ × wet × river × SRP** → raise (公式 pred=call、 n=258、 avg 15.4 BB)
- 例外 3: **アンダーペア × wet × turn × vs CR** → fold (n=179、 avg 9.9 BB)
- 例外 4: **エア × wet × turn × 3BP** → call (公式 pred=fold、 n=159、 avg 9.5 BB、 bluff catch)
- 例外 5: **2P+ × wet × flop × SRP** → fold (n=125、 avg 12.5 BB)
- 適用条件: 「公式 pred が指定値の時のみ override」(条件付き例外)
- 5 ルール暗記で huge spots 47% を救う

---

## 第3部: 公式の背景 — 4 判定軸 (ch10-12)

> Score 公式の理論バックボーン。 公式だけ使う読者は読み飛ばし可。  
> 旧 5 軸モデルの「エクイティバケット」 は MATCHA Score 公式に数値として吸収済 → 廃止。

### 10. Range Morphology — board 分類の data 裏付け
- 旧 6 ボードファミリー (dry_high / low_dry / dynamic / dynamic_2tone / monotone / paired)
- **現行 heuristic 一致率 19%** の経緯と教訓
- data-driven な分類への移行 (3 タイプに集約)
- sub-family × カテゴリ の cross-tab (15 × 6 = 90 cell の発見)
- なぜ 3 タイプで Score 公式に十分か (情報損失の少なさ)

### 11. Hand Strength — 6 階層 → 4 集約の理由
- 旧 6 階層 (ナッツ / ストロング / 2P / TP+ / ミドル / エア)
- 4 集約の data 駆動根拠:
  - 6 カテゴリ (Grid 18): 0.3722 BB
  - 4 カテゴリ-B (Grid 12) ★: 0.3587 BB ← 採用
  - 5 カテゴリ (Grid 15): 0.4084 BB (集約過剰)
  - 7 カテゴリ (Grid 21): 0.3874 BB (細分化で overfit)
- 2P+ (2P〜SF) の統合が **4BP で huge -85% を達成** した経緯
- mv_cat 17 種類 → 4 集約の対応詳細

### 12. Bet Sizing と SPR — 2 段階と反転点
- **Bet Sizing は 2 段階で 90% カバー** (small 33% / over 100%)
- medium (50-75%) は実は不要だった発見
- SPR 4 段階 (オールインSPR / ローSPR / ミディアムSPR / ディープSPR)
- **SPR=3 が GTO 戦略反転点** — 同 K72 × SPR variation で set 4% → 96% (+92pp)
- 4BP でアンダーペア 73% > set 4% の逆転現象 (4BP は別ゲーム)

### 13. 旧来のポーカー理論との橋渡し ★暗記補助
- **Outs と Rule of 4/2** (Petriv): DV multiplier (flop ×3 / turn ×2 / river ×0) の整数化根拠
  - 各 draw の outs カウント表 (FD=9 / OESD=8 / gutshot=4 / combo=12-15)
  - Rule of 4/2 (flop で残り 2 枚 × 4%、 turn で残り 1 枚 × 2%) と DV multiplier の対応
- **古典ボード 7 分類** → MATCHA 3 分類 集約マトリックス
  - Dry rainbow / Dry connected → dry
  - Wet / Monotone / Two-tone (connected) → wet
  - Paired high / Paired low → paired
- **旧 6 階層 Hand Strength** → MATCHA 4 カテゴリ 対応表
  - ナッツメイド / 2P+ (set 以上) → 2P+
  - ツーペア → 2P+ (本書は集約、 旧書では中位)
  - ストロング / TP+ → TP+
  - ミドル → アンダーペア / エア → エア
- **SPR 理論** (Flynn): 1-3-7 切り分け → MATCHA 4 段階 (オールイン / ロー / ミディアム / ディープ)
- **Pot Odds / MDF** (Minimum Defense Frequency): 公式閾値 ≥14 call の意味づけ
  - bs 別 pot odds (33% → 25%、 75% → 30%、 100% → 33%、 overbet → 38%)
  - MDF (1 − pot/(pot + 2 × bet)) と Score 閾値の対応
- **Range Morphology** (Janda): polarized / linear / merged → 2 極化型 / 混在型 / 密集型
- **Sklansky Hand Groups** (1976): カテゴリ 4 段階の系譜、 群 1-2 = 2P+、 群 3-4 = TP+、 群 5-7 = ミドル、 群 8 以下 = エア
- **Theory of Poker** (Sklansky 1987): MATCHA Score が「相手のカードを見ながらプレイ」 と「相手のカードを知らずにプレイ」 のギャップを最小化する整数近似
- **Bet Sizing 理論**: 33% (pot 切り取り) / 75-100% (polar) / overbet (super polar) の意味づけと MATCHA bs 6 段階の対応
- **暗記項目**: 旧 → 新 対応表 (1 ページ早見、 付録 E に再掲)

---

## 第4部: ポット種別 + コンテキスト別 (ch14-23)

> 攻撃の 2 大原則 (ch14) を最初に押さえ、SRP/3BP/4BP (ch15-17) → TURN/RIVER + polarization (ch18-20) → vs CR/Donk (ch21-22) → アタック 8 ルール統合 (ch23) の順で学ぶ。

### 14. アタック入門 — OOP は全チェック、IP は強手のみベット ★先読み
- **大原則 1: OOP → 全チェック** — 情報漏れ防止、レイズへの対応なし
- **大原則 2: IP → 2P+ または TP+ ならベット、それ以下はチェック**
- この 2 原則で GTO の 6 割以上をカバー
- 第 23 章 (アタック 8 ルール) で精度 LS=91% まで拡張

### 15. SRP — 標準 100bb
- Score 公式そのまま (pot=0)
- BTN open vs BB call を基準 とした全 spots audit
- avg loss 0.3587 BB の内訳: SRP で 1.99% huge

### 15. 3BP — 3-bet pot
- pot=2 として公式に組込
- 3BP 特有の SPR 低下 (effective SPR 4 前後)
- 例外 4: エア × wet × turn × 3BP → call (bluff catch、 公式 pred=fold)

### 16. 4BP — 専用 lookup table ★
- Score 公式は 4BP で機能しない (acc 57.4%) → 専用 lookup に切り替え
- **bet 推奨 4 cells**: TP+ × dry/wet、 ミドル × dry/paired
- **2P+ × paired = check (15%)** — BB super tight range で blocker 警戒
- lookup 採用で MQS 71.3 → 78.4、 全 cell B 級以上

### 17. TURN — 専用 lookup + split rule
- **2P+ → bet** (3 cells lookup)
- **overpair → bet** (split rule)
- **no_made_hand × paired/wet → bluff bet** (polarization 入口、 50.7%)

### 18. RIVER — split rule v6
- **役確定 (top_pair 以上) → value bet**
- **no_made_hand (完全 air) → bluff bet** (56-74%)
- 中間役 (ace_high / low_pair 等) → check

### 19. ストリート別 polarization — 完全 air が river で 74% bet する理由
- GTO 理論の data 駆動的俯瞰 — ストリートで戦略が反転する理由
- 完全 air × no_draw の bet 率 (全 context 横断: flop 0% → turn 50% → river 74%)
- なぜ river で完全 air が 74% bet するのか (polarized strategy の到達点)
- ストリート別の戦略変化と 公式 polarization 組込みの確認 (第 17/18 章)
- 暗算では何を覚えるか

### 20. vs CR (CR ディフェンス) — turn donk vs CR は真逆
- pot=2 として公式に組込 (3BP と同等)
- **turn donk vs turn CR で BTN defense が真逆** (probe phase5 発見)
- vs CR: 相手 value-heavy (opp_strong 46%)
- vs Donk: 相手 air-heavy (opp_weak 54-61%)
- 例外 3: アンダーペア × wet × turn × vs CR → fold (n=179)

### 21. vs Donk Bet — ドンクベットへの対応
- ドンクベットの発生頻度 — ターンカードが鍵
- vs Donk のレンジ分析 — vs CR と真逆 (opp air-heavy)
- MATCHA Score での計算 (pot=2 相当、ただし補正方向は CR と逆)
- ターンドンク — ボードペア時の対応
- フロップドンク / リバードンク の対応指針

### 23. アタックルール — BET/CHECK の決定ロジック ★実戦統合
- **デフォルト=CHECK + 8 条件** のコンパクト暗算ルール (精度 LS=91%)
- 8 ルール全体: R1 (TP+→BET) / R2 (2nd/UP×4BP/river→BET) / T底 (底×4BP IP turn dry→BET★) / T3 (2nd/UP×SRP IP turn draw→BET) / R3 (low/3rd×4BP OOP river→BET★) / E1 (trips/OP×4BP OOP→CHECK) / E2 (no_made×4BP OOP river→CHECK★) / R4 (no_made×river→BET★)
- ◎/△/× 傾向マップ (フロップ/ターン/リバー × 5 シナリオ) — 全体俯瞰
- 逆転パターン 4 件 (T底/R3/R4/E1) の優先暗記
- 第 15-22 章で学んだ全ポット種別・コンテキストを統合した判断フロー

---

## 第5部: スタック深度と Cash/MTT 差分 (ch23-25)

### 23. 短スタック (≤25bb)
- SPR 自動下げ (ディープSPR → ミディアムSPR、 etc.)
- pair + → コール (committed range)
- MTT25 での Score 閾値補正
- depth-aware v9b/v10/v15 (legacy) 系列との関係 (付録 B 参照)

### 24. 深スタック (200bb+)
- SPR 自動上げ
- アンダーペア × flop/turn → コール (implied odds)
- 200bb での MATCHA Score 閾値補正
- Cash 200bb と MTT200bb の同構造性

### 25. Cash vs MTT chipEV のパラメータ差 ★新章
- **ante の影響**: 10-12.5% of BB、 pot サイズ +25-50%、 bs 解釈の調整
- **BB ante の影響**: 1bb pre-pot、 BB defense range wider、 SB squeeze tighter
- **rake の有無**: Cash は thin value 効率↓、 MTT は rake 無 (chip 計算のみ)
- **open-raise sizing 差**: Cash 2.5bb / MTT 2.0-2.25bb (ante 影響)
- **3-bet sizing 差**: Cash 9-11bb / MTT 6-8bb (effective SPR 維持)
- **MTT 早期 / 中期 / 後期** での chipEV 純度
- **MATCHA Score の Cash/MTT 別解釈** (bs 値の見方、 SPR 計算)
- **暗記項目**: Cash/MTT 差分表 (1 ページ早見)

---

## 第6部: トーナメント特有・多人数 (ch26-29) ★定性 + 構造解説

> 本書のメイン手法 (MATCHA Score) は **Cash + MTT chipEV** に最適化。  
> 本部では ICM/バブル/マルチウェイ など **公式の前提が崩れる場面** を定性的に補足、  
> + テーブルサイズ (6/8/9-max) 別の Score 適用調整 を解説。  
> GTO data 不能な ICM/PKO の数値モデル化は将来 Vol2.5 (ICM/PKO 別冊) で対応予定。

### 26. ICM 入門 — chipEV と $EV のズレ ★定性
- chipEV (本書の前提) と $EV (実払戻し) の違い
- **リスクプレミアム** — 同 chipEV ハンドが ICM ステージで $EV− になる現象
- ICM Pressure の階層: バブル / FT / heads-up
- **MATCHA Score の ICM 修正方針** (定性): t_call/t_raise を引き上げ、 大きな pot は避ける
- short stack vs chip leader: chip leader は wide pressure、 short は jam-or-fold
- なぜ data モデル化困難か (API 制限 / context の組合せ爆発)

### 27. バブル戦略 — リスクプレミアムの極大化 ★定性
- バブル定義 (賞金圏直前)、 ICM Pressure 最大
- **short-stack jam range の絞り** — chipEV の push range より tight
- chip leader の wide steal — リスクなしで bully
- **mid-stack 受難** — どちらにも捕まる、 tight 一方通行
- 短スタックスタイルから AI への jam threshold (定性)
- MATCHA Score 適用上の注意 (バブルでは t_call +5〜+10 相当、 厳しめ)

### 28. マルチウェイ (3+ way) — 公式の前提崩れ ★Vol3 連携
- **公式の単独 villain 前提** が 3+way では成立しない (fold equity 急減)
- **MW 5 原則** (詳細は Vol3 ch16):
  1. ブラフ生成禁止 (fold equity 急減、 EV-)
  2. バリュー集中 (薄バリュー控え、 強 hand 主体)
  3. ハンド選好変更 (SC・小ペア優遇、 broadway off 弱体化)
  4. T_open 引き上げ (+3〜+12 程度)
  5. アイソレート優先 (1 vs 1 に戻せれば公式 +shift 復活)
- short stack 混在時の SPR 別管理 (villain ごとに effective SPR が違う)
- **詳細は Vol3 (MATCHA Exploits) ch16 へ誘導**

### 29. テーブルサイズ別調整 (6/8/9-max) ★新章
- **6-max** (本書のメイン想定): UTG=15-18% / range 標準 / polar 寄り / 3-bet 多
- **8-max**: UTG=13-15% / 混在 range / 3-bet 中
- **9-max**: UTG=10-12% (最 tight) / merged range / multiway 頻度高
- 各テーブルサイズでの **MATCHA Score 補正**:
  - 9-max では UTG/LJ open range が tight → hero の defend range も狭く (Score +2-3 引き上げ)
  - multiway 頻度が高い 9-max では MW 5 原則の適用率 up
  - 6-max は無調整で公式適用可
- **席選び効果の規模** (Vol3 ch15 連携): 9-max ほど左右の影響大
- **range structure 差**: polar (6-max) → merged (9-max) の中間
- **暗記項目**: テーブルサイズ × 補正一覧 (1 表)

---

## 第7部: 実戦 (ch30-32)

### 30. 境界ハンド総覧
- 第 2 部の境界 (hand / board / 例外) を 1 表に集約
- ~30 ハンド/spot の暗記リスト
- フローでカバーできない 20% の spots

### 31. ドリル抜粋 (12 問)
- 各部 (公式 / 境界 / 4 軸 / pot / 深度 / Cash vs MTT / トーナメント / テーブルサイズ) から 1-2 問ずつ抜粋
- 計算過程の可視化 (Grid lookup → 加算 → 閾値)
- 詳細は poker-drill アプリへ:
  - 基本 (32 例題)
  - ヒント大 (60 spots、 軸判定済み + 表参照)
  - 応用 (60 spots、 シナリオから軸判定)
  - 境界 spot ドリル (50 spots)

### 32. チートシート
- A4 1 枚に圧縮 (公式 1 行 + Grid 12 cells + 例外 5 ルール)
- 印刷推奨
- ポケットサイズ版も付録 A に同等

---


## 付録

### 付録 A. MATCHA Score 公式 + Grid 早見
- 公式 1 行 + Grid 12 cells の参照表
- 各軸の値一覧 (カテゴリ / board / DV / mult / pot / bs)
- 例外 5 ルール早見

### 付録 B. 旧来理論との橋渡し早見表 ★暗記補助
- 1 ページで全対応 (Outs Rule of 4/2 / 古典ボード 7 分類 / 旧 6 階層 / SPR / Pot Odds / MDF / Range Morphology / Sklansky Hand Groups)
- 第 13 章を凝縮した参照表

### 付録 C. MATCHA Quality Score (MQS) — 公式の品質保証指標
- MQS 5 component (Action Accuracy / Loss Quality / Coverage / Outlier F1 / Robustness)
- 174,793 hands × 5 context 検証結果 (SRP/3BP/4BP/TURN/RIVER)
- Grade S (MQS v6=82.0 / v7=91.2) の根拠と天井理由

---

## 想定ページ数

| Part | 章数 | 想定ページ |
|------|----:|----------:|
| 序章 (ch00) | 1 | 4 |
| 第1部 公式 (ch01-05) | 5 | 25 |
| 第2部 境界・例外 (ch06-09) | 4 | 22 |
| 第3部 4 軸の背景 (ch10-13) | 4 | 22 |
| 第4部 ポット種別 + コンテキスト別 (ch14-23) | 10 | 42 |
| 第5部 深度 + Cash/MTT 差 (ch24-26) | 3 | 14 |
| 第6部 ICM/MW/テーブルサイズ (ch26-29) | 4 | 18 |
| 第7部 実戦 (ch30-32) | 3 | 10 |
| 付録 A-C | 3 | 10 |
| **計** | **32 + 序 + 付録 3** | **~163p** |

vs 旧 Vol2 (180p) + 旧 Vol3 (200p) = 380p → **-69%**

---

## 関連リソース

### poker-drill アプリ (連携)
- URL: https://poker-drill.vercel.app
- Vol2 MATCHA Score Final カテゴリ: 6 deck (calc/grid/exceptions/realtime/guided/applied)、 ~270 cards
- Vol2 MATCHA Framework カテゴリ: 17 deck (foundation 8 + practical 9)
- Vol3 MATCHA Exploits カテゴリ: 16 deck (player_types + shift/attack/preflop_defense/multiway/5axis/turn/river/over_adjustment)

### 知識ベース (knowledges/gto_wizard_study/)
- `MATCHA_SCORE_V3.md` — 公式の完全 reference
- `HUGE_LOSS_V3.md` — 例外 5 ルールの分析
- `INSIGHTS_2026-06-08_FULL.md` — 5 軸の data 裏付け
- `INSIGHTS_2026-06-08_BOARDS_HANDS.md` — Board / Hand 境界
- `PROBE_PRIORITY_FINDINGS.md` — 334 spots の発見
- 詳細は付録 D へ

### スクリプト (scripts/)
- `three_class_model/dataset_unified_v2.csv` — 154,216 spots dataset
- `three_class_model/optimize_grid_*.py` — Optuna 最適化
- `generate/` — 本書 generator (vol2_book_generator.py 作成予定)

---

*更新日: 2026-06-09 (MATCHA Score 中心の再構成)*
