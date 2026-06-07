# 書籍構成計画 (2026-06-01)

「迷わないポーカー」シリーズ 4 巻体制の最終設計。Postflop 公式の二層構造 (Tier 1 簡易 / Tier 2 詳細) を Vol2 / Vol3 に振り分け。

## シリーズ全体構成

| 巻 | テーマ | 想定読者 | 主要式 |
|----|--------|----------|--------|
| **Vol1** | プリフロップ完全版 | 初心者〜中級 | Score_BB v7 (Chen 系) |
| **Vol2** | Cash / Postflop / **簡易** | 初心者〜中級 | **Tier 1 マトリックス + 5 公理** |
| **Vol3** | MTT / Postflop / **詳細** | 中級〜上級 | **Tier 2 詳細式 + stack 補正** |
| **Vol4** | Tell / Exploit | 中級〜上級 | プレイヤータイプ別補正 |

二層構造のメッセージ:
- **Vol2 = "迷ったらこれで 7-8 割正解"** (暗算で回せる)
- **Vol3 = "GTO ガチ整合 + MTT 特有の stack 補正"** (huge_loss 0.04-0.39 BB 級)

---

## Vol2: Cash / Postflop / 簡易（Tier 1）

### 設計思想

Cash 100bb SRP (BTN vs BB) を **唯一の想定状況** として「絶対覚えるべき core rule」だけを提示。

`5 × 4` マトリックス + 5 公理で全ポストフロップを cover。

### 5 公理（書籍 Part 0 で導入）

1. **強さは 5 段階で判定**:
   - **S** (Strong): 2P+, set, straight, flush, FH, overpair
   - **M** (Medium): top pair, 2nd/3rd pair, underpair
   - **W** (Weak): A-high, K-high, low_pair
   - **A** (Air): no_made + no_draw
   - **D** (Draw): OESD / FD / combo draw (Flop/Turn のみ)

2. **サイズは 4 段階で判定**:
   - **s** (small): ≤ 33% pot
   - **m** (medium): 50-75% pot
   - **l** (large): ≈ 100% pot
   - **o** (overbet): ≥ 150% pot or all-in

3. **強いハンドは aggressive、弱いハンドは passive**

4. **サイズが 1 段階大きいほど 1 段階タイトに対応**

5. **完全 air は基本諦める** (River のみ blocker 持ちでブラフ)

### 攻撃マトリックス (自分が動く時)

| 強さ | Flop | Turn | River |
|------|------|------|-------|
| **S** | BET | CHECK (slowplay) | BET |
| **M** | CHECK | CHECK | BET on dry / CHECK on dynamic |
| **W** | CHECK | CHECK | CHECK |
| **A** | CHECK | CHECK | BET as bluff |
| **D** | CHECK (semibluff 控えめ) | CHECK | n/a |

### 守備マトリックス (相手のベットに対応)

| 強さ \ サイズ | s (小) | m (中) | l (大) | o (オーバー) |
|--------------|--------|--------|--------|-------------|
| **S** | RAISE | CALL | CALL | CALL |
| **M** | CALL | CALL | CALL | FOLD |
| **W** | CALL | CALL | FOLD | FOLD |
| **A** | CALL | FOLD | FOLD | FOLD |
| **D** | CALL | CALL | CALL | FOLD |

### Vol2 章構成案 (10 章)

```
00. はじめに — なぜ簡易公式で十分か (EV loss 視点)
01. 強さ 5 段階 — 自分のハンドを分類する
02. サイズ 4 段階 — 相手のベットを読む
03. 攻撃マトリックス — Flop / Turn / River 共通
04. 守備マトリックス — Flop / Turn / River 共通
05. Flop の特殊性 — board family ごとの調整
06. Turn の特殊性 — slowplay 全面採用
07. River の特殊性 — polarization の理解
08. 練習問題 50 問 (自己診断)
09. 早見表付録 (1 ページに収まる総合表)
```

### Vol2 目標スペック

- 字数: 60-70k 字
- EV loss: 簡易マトリックスで always_CHECK/CALL の **数十倍マシ**
- 想定読者: ポーカー歴 1 年未満の初心者でも回せる
- 暗算難度: AAo を 25 点と覚える程度 (Chen 系)

---

## Vol3: MTT / Postflop / 詳細（Tier 2）

### 設計思想

Vol2 の簡易公式の上に **「huge_gap セルをほぼ潰す」詳細例外** を積み上げる。MTT 特有の stack depth (25-200bb) 補正も加える。

### Tier 2 詳細式 (検証済み)

#### Flop attack: default CHECK + 7 BET 例外
huge_loss は既に最小化済み。

#### Flop defense (mv-based v7)
```
FOLD: air ∧ no_draw
FOLD: low_pair/3rd_pair ∧ no_draw ∧ board ∈ {dry_high, low_dry, dynamic_2tone}
RAISE: overpair (on best bucket equity)
else CALL
```
- huge_loss 0.49 BB (mv_cat 上限)

#### Turn defense (mv+dv v8) ⭐⭐⭐⭐
```
vs overbet (≥100% pot):
  FOLD: 弱メイド ∧ 弱ドロー (no/BDFD/gutshot)
  FOLD: air ∧ flush_draw on dry_high
  FOLD: air ∧ oesd on dynamic
  FOLD: dynamic + top_pair + no_draw
  else: CALL

vs medium (≤67% pot):
  FOLD: air ∧ no_draw
  FOLD: dynamic + 弱メイド (excl 2nd_pair) + 弱ドロー
  FOLD: dynamic + oesd + 弱メイド (excl 2nd_pair)
  else: CALL
```
- huge_loss 0.037 BB (96.3% acc on huge)
- Turn では mv + dv が最強 (bucket overlay 逆効果)

#### Turn attack: always CHECK
データ上 0.003 BB loss (MTT 25bb 偏重)

#### River attack (polar + slowplay v7)
```
CHECK: STRONG (2P+/set+/straight+) on dry boards (slowplay)
CHECK: top_pair on dynamic 系 (vulnerable)
BET: value (OP, TP/dry, 2P+/dynamic)
BET: bluff = {no_made_hand, king_high}
CHECK: medium SDV (A-high, low/2nd/3rd pair)
```
- huge_loss 0.16 BB

#### River defense (bucket+mv override v14) ⭐⭐⭐
```
quads → RAISE
fullhouse: vs overbet → CALL (slowplay), else → RAISE

vs allin:
  best_bucket + eqp>0.85 → CALL
  dry + set/trips/straight/flush → CALL
  good_bucket + straight/flush/trips → CALL
  monotone + flush → CALL
  dynamic + top_pair + good/weak bucket → CALL (counter-intuitive)
  else → FOLD

mv ∈ {straight, flush, trips} → CALL (絶対強さ override bucket)
mv = top_pair × dry × {overbet/100%} → CALL (bluff catch)

best_bucket: eqp>0.96 RAISE else CALL
good_bucket: CALL
weak_bucket:
  vs overbet → (dyn+2P CALL / else FOLD)
  vs 100% → FOLD
  else → CALL
trash → FOLD
```
- huge_loss 0.388 BB (88% vs default)
- River では bucket (相対強さ) が最強

### MTT stack depth 補正 (要追加調査)

現状データ: Cash 100bb のみ。MTT 25/50/100/200bb 用の補正係数を追加調査で決定。

想定される補正:
- **25bb**: SPR≈4 → コミットメント近い、weak 帯までブロフキャッチ拡大
- **50bb**: SPR≈8 → 標準 (Cash 100bb の挙動に近い)
- **100bb**: SPR≈16 → Cash と類似 (微妙な調整)
- **200bb**: SPR≈25 → Cash 200bb 想定 (overbet 多用、bluff catch 拡大)

### Vol3 章構成案 (15-18 章)

```
00. はじめに — Vol2 簡易公式の限界と Tier 2 の役割
01. Tier 1 マトリックス復習 + Tier 2 へのブリッジ
02. 街ごとの理論的アクシス (Flop=mv, Turn=mv+dv, River=bucket)
03-04. Flop defense 詳細 (mv-based)
05-06. Turn defense 詳細 (mv+dv+board)
07-08. River defense 詳細 (bucket+mv override)
09. River attack 詳細 (polarization)
10. MTT 25bb 補正
11. MTT 50bb 補正
12. MTT 100bb 補正
13. MTT 200bb 補正
14. 3-bet pot 詳細 (Cash + MTT)
15. ICM 補正 (バブル付近)
16. 練習問題 100 問 (huge_gap セル中心)
17. 早見表付録 (Tier 2 全 30+ ルール)
```

### Vol3 目標スペック

- 字数: 90-120k 字
- EV loss: huge_gap で各街 0.04-0.39 BB (default の 88-99% 削減)
- 想定読者: ポーカー歴 3 年以上 + Vol2 既読
- GTO Wizard 整合性: 90%+ (検証済みデータあり)

---

## 二層構造のメッセージング

### Vol2 (簡易)
> 「ポストフロップは難しく見えますが、5 段階の強さと 4 段階のサイズで 8 割は決まります。」
> 「迷ったらこの 25 セル表を見るだけ。それで GTO に十分近い判断ができます。」

### Vol3 (詳細)
> 「Vol2 の簡易公式で外す残り 2 割 — それを潰すための詳細例外集です。」
> 「Turn では draws の有無、River では相対強さ (bucket) で判断が変わります。」
> 「MTT は stack depth で挙動が変わるため、Cash の感覚をそのまま持ち込めません。」

---

## データ充実プラン (追加 fetch 必要分)

### 現状データ量 (2026-06-01 時点)

| 内容 | 量 | source |
|------|-----|--------|
| Flop attack | 426k rows | gto_wizard_full + study (Cash+MTT 混合) |
| Flop defense | 90k rows | def_mtt25/50_bb_raw + def_cash100_bb_raw |
| Turn attack | 99k rows | turn_cash100/mtt25/100_btn_raw |
| Turn defense | 7.5k rows | **Cash 100bb のみ** |
| River attack | 50k rows | SRP_BTN_river_check, b4_xxxx_river, probe_river |
| River defense | 14k rows | **Cash 100bb のみ** |

### Vol3 のため要追加 fetch

**最優先 (MTT 守備データ)**:
1. **MTT 25bb turn/river defense** — ショートスタックの極タイト守備
2. **MTT 50bb turn/river defense** — 標準 MTT 深さ
3. **MTT 100bb turn/river defense** — Cash 比較用

**次優先 (多様な bet サイズ)**:
4. **Cash 100bb の中間サイズ** — 現状 67%/185% (turn)、50%/100% は欠如
5. **3-bet pot 詳細** — 既存 a few spots のみ

**最後**:
6. **ICM バブル付近** — Vol3 ch15 用、特殊ケース

各 fetch のスケジュール (今後の token 取得タイミング次第):
- Phase 1 (次回): MTT 50bb turn/river defense ≈ 40 spots × 2 streets = 80 fetches
- Phase 2: MTT 25bb turn/river defense ≈ 60 fetches
- Phase 3: MTT 100bb + Cash 中間サイズ ≈ 80 fetches

---

## 検証実績 (2026-06-01 時点)

### Cash 100bb (Vol2)

| Street | Tier 1 想定 acc | **Tier 2 実測 huge_loss** | 対 default 削減 |
|--------|----------------|---------------------------|----------------|
| Flop attack | ~80% | 0.023 BB (mean) | — |
| Flop defense | ~75% | 0.49 BB | 62% |
| Turn attack | ~95% | 0.003 BB (always CHECK) | — |
| **Turn defense (v8 mv+dv)** | ~80% | **0.037 BB** ⭐⭐⭐⭐ | **99%** |
| River attack | ~70% | 0.16 BB | 70% |
| **River defense (v14 bucket+mv)** | ~75% | **0.388 BB** ⭐⭐⭐ | **88%** |

### MTT 50bb (Vol3) — 主要差分

| Street | Cash v? を適用 | **MTT 専用 v? huge_loss** | 軸変化 |
|--------|---------------|---------------------------|--------|
| Flop defense | v7 同様で OK | (未検証だが mv ベースで OK) | mv |
| **Turn defense** | Cash v8: 0.133 | **MTT v9 pure bucket: 0.057** ⭐ | **mv+dv → bucket** |
| **River defense** | Cash v14: 0.316 | **MTT v15 (true-allin aware): 0.038** ⭐⭐⭐⭐ | **bucket + raise 不可判定** |

### 重要な意味論的発見: "allin" の意味が depth で変わる

- **Cash 100bb の "allin"** = R89.6 (421% pot だが**まだ raise 可**) → 強メイドは RAISE
- **MTT 50bb の "allin"** = R35.5 (235% pot、**真の all-in、raise 不可**) → call/fold のみ

これは **「stack depth はベットサイズの意味 (raise オプション有無) も変える」** という Vol3 の重要メッセージ。

### 街 × stack depth × アクシス対応 (Vol3 中核理論)

| 状況 | SPR (flop後) | 支配軸 | 理由 |
|------|-------------|--------|------|
| Cash 100bb Flop | ~10 | mv | 絶対強さ |
| Cash 100bb Turn | ~7 | mv + dv | ドローの implied odds 大 |
| Cash 100bb River | ~3 | **bucket** | ドロー消失、相対強さ |
| MTT 50bb Flop | ~6 | mv | 絶対強さ |
| **MTT 50bb Turn** | **~3** | **bucket** ⭐ | Cash River と同じ |
| MTT 50bb River | ~1 | bucket | universal |

**Vol3 中核メッセージ**: 「SPR が下がるほど bucket (相対強さ) の比重が増える。MTT では Cash より早く bucket 軸が支配的になる。」

---

## Tier 設計上の鉄則

### 簡易にすべきもの (Vol2 残す)
- マトリックス自体
- 5 段階 / 4 段階の閾値
- "1 段階タイトに" の規則

### 詳細にすべきもの (Vol3 へ)
- 街ごとのアクシス切り替え (mv → mv+dv → bucket)
- 板タイプ補正 (dynamic vs dry)
- 板読み補正 (TP × dynamic = vulnerable)
- Stack depth 補正
- Bet サイズの細分化 (33%/50%/67%/75%/100%/150%/all-in)

### 二層に分けない (両方に書く)
- 5 公理 (Vol2 中核 / Vol3 でも復習)
- 各街の役割 (Flop = range war / Turn = polarization / River = showdown)

---

## 次のアクション候補

A. **MTT データ追加 fetch** (Vol3 のため)
B. **Vol2 章稿の Tier 1 マトリックスベース書き直し** (既存 11 章を簡易化)
C. **Vol3 章稿の Tier 2 詳細書き直し** (既存 16 章を v8/v14 ベースに)
D. **練習問題セットの自動生成** (huge_gap 中心のドリル)

優先度の判断材料: 既存 Vol2/Vol3 章稿の状態と公開予定。

---

## 関連メモリ

- `project_postflop_3rule_formula.md` — 公式の詳細実装
- `project_vol2_vol5_rewrite.md` — Vol2 旧書き直し履歴
- `project_unified_preflop_score_v2.md` — Vol1 仕様 (preflop)
- `project_new_books_status.md` — vol2/tell 新書進捗
