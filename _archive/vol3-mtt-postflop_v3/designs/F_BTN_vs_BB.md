# F系シナリオ設計: BTN vs BB フロップ（SRP）

*Task #4 改訂 / 新フレームワーク準拠 / 2026-05-22*

## 適用範囲
- ポジション: IP=BTN（フロップ前 raiser）／OOP=BB（caller）
- ストリート: フロップ
- ICM 想定: SBR25（Middle-Deep, SPR≈8）と SBR20（Middle, SPR≈6）
- フロップポット: 約 5.5 BB（BTN open 2.5BB + BB call 2.5BB + ante 0.5BB）
- 出典:
  - `mtt-postflop/findings/mtt_flop_cbet_SBR{20,25}_BTN_BB.json`
  - `mtt-postflop/findings/mtt_check_raise_SBR{20,25}.json`

---

## 新フレームワーク（本書統一の判断式）

旧版の「HS ≥ 65 なら Bet」「HS = 35–54 なら Check 寄り」といった**静的 HS 閾値**は本書では「3 軸統合の暗算ショートカット」として位置付けし直し、メインの判断フローは以下の不等式に統合します。

```
hand_equity  ≥  required_equity  →  ベット / コール
hand_equity  <  required_equity  →  フォールド（セミブラフ除く）

required_equity  =  α(b)  +  ICM 補正  +  ポジション補正

α(b):       1/4=17%  1/3=20%  1/2=25%  2/3=29%  pot=33%
ICM 補正:   序盤 0  中盤 +4  バブル +10  FT +15
ポジ補正:   IP -2  OOP +2
```

ハンドは **5 カテゴリ（Equity Trajectory）** で分類し、それぞれにフロップ典型 equity を割り当てます。

| カテゴリ | 定義 | フロップ equity 目安 | 行動の動機 |
|---------|------|-------------------|-----------|
| **Nutted** | セット / 2 ペア / overpair / TPTK | 70%+ | バリューベット |
| **Thin value** | TP 弱キッカー / 2nd pair 強 / underpair | 50–65% | **保護ベット**（今打たないと equity が下落する） |
| **SDV** (Showdown Value) | 3rd pair / ポケットの中位ペア / 強 A-high | 40–50% | チェックバック（安くショーダウン） |
| **Semi-bluff** | FD (36%) / OESD (32%) / FD+GS (48%) / FD+OESD (60%) | 30–60% | セミブラフ可（フォールド equity 次第） |
| **Air** | ノーペア・ノードロー | <20% | チェック or レンジ防衛ブラフ |

> **保護ベットとは**: Thin value はフロップでは equity 50–65% あっても、ターン以降に **オーバーカード・フラッシュ完成・ストレート完成** などで equity が大きく下落します。「**今は勝っているうちに pot を膨らませる**」という時間差攻撃が保護ベットの本質です。

---

## SBR→SPR→ベットサイズ早見

| SBR | SPR 目安 | CBet 主サイズ（GTO） | CR サイズ |
|-----|---------|----------------------|-----------|
| 25  | 8       | T1=20%（型1/6/7）と T3=33%（型2-5）混在 | x3.0（pot×5.05/spr 相当） |
| 20  | 6       | **T2=33% 一本化**（全型）              | x2.7（pot×4.8/spr 相当） |

> **暗算メモ**: SBR20 では T1(20%) は事実上 0%、CBet は 33% 一択。SBR25 では「ハイドライ／ペア板」は 20% 小さく、「ウェット／ロー」は 33-50% にスケール。

---

## F01B: IP CBet（BTN→BB、フロップ）

### 状況判断: ハンドを 5 カテゴリに分類する

| カテゴリ | 例 | フロップ equity | アクション理由 |
|---------|----|----------------|---------------|
| Nutted | set / 2 pair / overpair / TPTK | 70%+ | 単純バリュー。required_eq < 25% なので全力ベット |
| Thin value | TP 弱 K / 2nd pair / underpair | 50–65% | **保護ベット**: ターン OC / FD 完成で equity 急落するので「今」打つ |
| SDV | 3rd pair / 中位ポケット | 40–50% | チェックバック。打つと OOP の上だけ call され、下を fold させて損 |
| Semi-bluff | FD / OESD / FD+GS | 32–60% | required_eq に届かなくても、フォールド equity と将来 equity でベット EV+ |
| Air | バックドアすら無し | <20% | 単独ではフォールド対象。レンジ防衛で混合のみ |

### 必要エクイティ（自分が CBet するときの fold equity 期待）

CBet サイズ b に対する α 式: α = b / (1+2b)。「自分が打つ側」のときは、フォールド equity がこの α を超えれば EV+ になります。

| サイズ | α | OOP の必要 fold% | ICM 中盤 (+4%) | ICM バブル (+10%) |
|--------|---|------------------|----------------|------------------|
| T1=20% (b=0.2) | 14.3% | 14.3% 以上 fold で利益 | 18.3% | 24.3% |
| T2=33% (b=0.33) | 19.9% | 19.9% 以上 fold で利益 | 23.9% | 29.9% |
| T3=50% (b=0.5) | 25.0% | 25.0% 以上 fold で利益 | 29.0% | 35.0% |
| T3=75% (b=0.75) | 30.0% | 30.0% 以上 fold で利益 | 34.0% | 40.0% |

### GTO データ要約（SBR25 / SBR20）

| 型 | flop 例 | CBet% SBR25 | CBet% SBR20 | 主サイズ SBR25 | 主サイズ SBR20 |
|----|---------|-------------|-------------|----------------|----------------|
| 型1 ハイドライ | Ks7d2c | **79.9%** | **68.6%** | T1=68% / T3=11% | T2=65% |
| 型2 ハイウェット | Qh8d3s | 69.7% | 56.7% | T1=52% / T3=15% | T2=49% |
| 型3 ロードライ | Jd7s5c | **52.7%** | 54.7% | T2=16% / T3=20% | T2=19% / T3=28% |
| 型4 ローウェット | Th9s8d | 67.1% | 72.3% | T2=28% / T3=17% | T2=44% / T3=27% |
| 型5 モノトーン | Ah9h5h | **97.9%** | **97.8%** | T2=49% / T3=24% | T2=81% / T3=15% |
| 型6 ペア高 | AsAcKd | 95.9% | 84.7% | T1=62% / T2=29% | T2=76% |
| 型7 ペア低 | 7s7d2c | 85.4% | 89.7% | T1=62% / T2=22% | T2=81% |

**カテゴリ別 bet%（SBR25 平均、7 ボード）**:

| カテゴリ | 平均 bet% | 解釈 |
|---------|-----------|------|
| Nutted (set/2pair/overpair/TPTK) | **84.2%** | バリューほぼ全力。set のみ under-bet trap で混合 |
| Thin value (2nd pair/underpair) | **74.3%** | 保護ベット高頻度。「今」打って equity を確定 |
| SDV (3rd pair) | **57.9%** | 混合戦略。レンジバランスのために半分は打つ |
| Air (no_made_hand) | **79.5%** | レンジ防衛＋セミブラフ込み。Air 単体ではない |

**主要パターン**:
- 範囲アドバンテージが明確な板（型1/5/6/7）→ CBet 80–98%（高頻度）
- レンジが拮抗 or BB 有利な板（型3/4）→ CBet 53–72%（選択頻度）
- 型2 ハイウェットは中間（57–70%）

### 決定フロー（3 ステップ）

#### Step 1: ハンドカテゴリ → equity 推定

| 自分の手 | カテゴリ | equity (ドライ) | equity (ウェット ×0.85) |
|---------|---------|----------------|----------------------|
| AA on K72 | overpair → Nutted | 88% | – |
| AKo on K72 | TPTK → Nutted | 78% | – |
| AKo on Q83 | A-high+BDFD → Semi-bluff 弱 | 24% | – |
| 88 on K72 | underpair → Thin value | 52% | – |
| 9 on T98 | 2nd pair → Thin value | – | 55% × 0.85 = 47% |
| FD on Q83 | FD → Semi-bluff | – | 9×4 = 36% |

#### Step 2: required_eq を算出

「自分がベットする側」なので、**OOP が fold する確率 ≥ α + ICM** を期待。逆に「自分の手 equity ≥ α + ICM + 2%（OOP補正は相手側）」が満たされれば、call されてもバリューが残ります。

中盤（SBR20、+4%）で **自分が IP CBet 20% pot** する場合の判定:

```
EV+(check 比較) を満たす条件:
  hand_equity ≥ α + ICM - 2(IP補正) ≈ 14.3 + 4 - 2 = 16.3%
```

このしきい値は非常に低いので、Air の半分・Semi-bluff 全部・SDV 以上のほぼ全カテゴリでベット EV+ になります。これが「IP CBet は広く打つ」結論の根拠です。

#### Step 3: equity ≥ required_eq か？

```
IF Nutted (≥70%): 即ベット。サイズは Thin value とミックスするため板に合わせる
ELIF Thin value (50–65%):
   今 equity ≥ 50%、ターン後 30% に下落 → 保護ベット（高頻度）
ELIF SDV (40–50%):
   call されるのは TP+ のみ → equity 後追いで 30% に下落 → チェックバック
ELIF Semi-bluff (FD 36%/OESD 32%):
   Air fold (≈70%) で EV+ → セミブラフ
ELIF Air (<20%):
   レンジ全体の Air share と頻度バランスで判定（GTO 既定 70% bet）
```

### サイズ選択（暗算ルール）

| SBR | 型1/6/7 | 型2 | 型3/4 | 型5 |
|-----|---------|-----|-------|-----|
| 25  | T1=20% | T1=20% 主, T3=33% も可 | T3=33–50%（強FD/SD は T3=75%） | T3=33–50% |
| 20  | **T2=33%** | T2=33% | T2=33%→T3=50% 二極 | T2=33% |

**暗算式**:「Dry/Pair → small（20% or 33%）、Wet → bigger（33–50%）、Mono → 33% でとにかく打つ」

### ICM 補正（SBR20 vs SBR25）

| 板 | CBet 差 | 解釈 |
|----|---------|------|
| 型1 | −11.3% | 浅くなると EV ベットを絞る（fold equity 低下） |
| 型2 | −13.0% | 同上、薄バリュー減少 |
| 型6 | −11.2% | 同上 |
| 型4 | **+5.2%** | 浅くなると pot 取り急ぐ |

**ルール**: SBR20 では「型1/2/6 の薄バリュー（Thin value 帯）を Check に回す」。型4 はむしろ攻める。これは ICM 補正で OOP fold% が +3.6% 上がるため、Thin value の保護ベット EV が再計算で下がるためです。

### 暗記ポイント（3 つ）

1. **Nutted + Thin value は「今打つ」**（保護ベット）。Thin value は equity が時間とともに下落するので、フロップで pot を膨らませる。
2. **SDV は基本チェックバック**（call されるのは上のみで損）。例外: 型6 ペア高では Air share が大きく fold 取りやすいので bet 混合。
3. **Semi-bluff は equity × フォールド equity で判定**。FD (36%) は required_eq 17–20% を上回るのでベット EV+。

---

## F03B: OOP Check-Raise（BB→BTN CBet に対し）

### 状況判断: CR レンジ構成

OOP は CBet を受けて 3 択（fold / call / CR）。CR は「**バリュー：ブラフ ≈ 2:1**」のポラライズ戦略で、レンジ上端と下端だけを使います。

| カテゴリ | CR への扱い | 理由 |
|---------|------------|------|
| Nutted (TP+) | CR バリューのコア | equity 70%+、3bet 食らっても 5bet 圏でジャム可 |
| Thin value | call 主体、CR は型7 のみ | CR で fold させたい相手手が少なく、value 損失大 |
| SDV | call またはチェックフォールド | プロテクションコール |
| Semi-bluff (FD/OESD) | **CR ブラフのコア** | equity 32–36% で 3bet されても call/フロート可能、fold equity 大 |
| Air | call と CR で配分（ブロッカー優先） | CR ブラフはレンジ防衛 |

### 必要エクイティ（IP の 3bet に対する CR 側の equity）

CR x3 を IP が 3bet（オールイン or pot）した場合、CR 側が pot コミット気味になります:

| サイズ | α | ICM 中盤 (+4%) |
|--------|---|----------------|
| CR 元 bet × 3（≈ pot 100%）| 33.3% | 37.3% |
| 3bet vs CR（≈ pot 200% over）| 40%+ | 44%+ |

**結論**: CR バリューは「3bet されても equity 40%+ を保てるか」で線引き。Nutted (70%+) は安全、Thin value (50–65%) は IP の 3bet レンジ（Nutted のみ）に対して equity 不足、よって CR から外れます。

### GTO データ要約

| 型 | flop | CR% SBR25 | CR% SBR20 | サイズ SBR25 | サイズ SBR20 |
|----|------|-----------|-----------|--------------|--------------|
| 型1 ハイドライ | Ks7d2c | **27.5%** | **30.3%** | x3.0 (R5.05) | x2.7 (R4.8) |
| 型2 ハイウェット | Qh8d3s | 21.5% | 24.2% | x3.0 | x2.7 |
| 型3 ロードライ | Jd7s5c | 20.2% | 22.0% | x3.0 | x2.7 |
| 型4 ローウェット | Th9s8d | 18.1% | 19.0% | x3.0 | x2.7 |
| 型5 モノトーン | Ah9h5h | **9.3%** | **11.0%** | x3.0 | x2.7 |
| 型6 ペア高 | AsAcKd | **4.1%** | **8.9%** | x3.0 | x2.7 |
| 型7 ペア低 | 7s7d2c | **30.6%** | **31.4%** | x3.0 | x2.7 |

**CR 頻度の階層**:
- 高 CR（27–31%）: **型1 / 型7**（ドライ低ペア・ハイドライ） ← BB のミドルペア群が CR バリュー
- 中 CR（18–25%）: 型2 / 型3 / 型4
- 低 CR（4–11%）: **型5 / 型6**（IP の超強レンジ板）

### カテゴリ別 CR 構成

| 型 | CR バリュー（Nutted） | CR ブラフ（Semi-bluff/Air） |
|----|---------------------|---------------------------|
| 型1 | top_pair 76–88% / 2pair | second_pair, ace_high, no_made_hand 14% |
| 型2 | top_pair 76–88% | king_high, third_pair |
| 型3 | top_pair 79–85% | overpair も少量、強ドロー |
| 型4 | straight 57–63% / top_pair 50–59% / 2pair | second_pair 10–23%、強FD |
| 型5 | flush 40–47% | top_pair（ナットアドない時のみ少量） |
| 型6 | trips 36–71% **のみ** | （ブラフ皆無） |
| 型7 | trips 80% / 2nd-pair 99% / full | ace/king_high 13–42% |

### 決定フロー（3 ステップ）

#### Step 1: ハンドカテゴリ判定

```
IF Nutted（TP+, 2pair, set）:
   ボード型に応じて CR or 単 call
   型1/4/7 → 高頻度 CR（バリュー強）
   型5/6 → call 主体（IP の Nutted と平行で CR してもバリュー薄）

ELIF Thin value（2nd pair, underpair）:
   原則 call。型7 のみ例外（M→71% CR、後述）

ELIF Semi-bluff（FD/OESD/強 BDFD+OC）:
   CR ブラフ候補。equity 32–36% + フォールド equity で EV+

ELIF Air（純トラッシュ）:
   fold 主体。ブロッカー（型1 で K-high 弱）のみ少量 CR
```

#### Step 2: 必要エクイティ確認

CR を打つときの自分の必要 equity:
- IP が 100% fold → equity 不要（最大の EV）
- IP が一部 fold + call → call レンジに対して equity 40%+ が望ましい
- IP が 3bet → コミット圏に入る、equity 45%+ 必須

中盤の場合、ICM 補正 +4% でブラフ CR の閾値（IP fold equity）が **20% → 24% 以上**に上がります。

#### Step 3: サイズ

- **CR サイズ = 元のベットの x3 を基本**（SBR25=x3.0, SBR20=x2.7）
- pot に対し約 5x（SBR25）/ 4.8x（SBR20）
- ドラブル板でも板別差はなく **「x3 一択」**

### 型7 ペア低の特殊性（Thin value から CR）

型7 では BB のオーバーペア（88+）と 2nd pair（22）が **「相対 Nutted」** に昇格します。IP のレンジは A-high が主体（pre-flop で 22 を持っていない）なので、equity 70%+ が確保できます。よって 99/22 は Thin value ではなく Nutted として CR に回ります。

### ICM 補正

- SBR20 では全板で CR% が **+1–5%**（浅いほうが CR ジャムでの fold equity 高い）
- 特に **型6 は +4.8%**: 浅いと trips のみでなく second_pair も少量 CR に回る

### 暗記ポイント（3 つ）

1. **CR 頻度 = 型7 ≈ 型1（30%） > 型2/3/4（20%） > 型5/6（10% 以下）**
2. **CR バリュー = Nutted（TP+）が主、CR ブラフ = Semi-bluff（FD/OESD）と Air のブロッカー**
3. **サイズは元 Bet × 3 一択**

---

## F04B: OOP Call/Fold エクイティ判断（BB が CBet に call/fold）

### 状況判断: CBet を受けたときの 3 択

「fold / call / CR」のうち、CR は F03B で扱ったので、ここでは **call と fold の境界** に集中します。

| カテゴリ | 行動 | 理由 |
|---------|------|------|
| Nutted (TP+) | CR or call 41% | F03B 参照 |
| Thin value | **call 73–80%** | equity 50–65% + ポットオッズ 25% → 楽勝でコール |
| SDV | **call 82%** | プロテクションコール、CR は 14% |
| Semi-bluff (FD/Ahigh+BD) | call 57% / CR 13% | フロート＋セミブラフ CR |
| Air | fold 69% | required_eq に届かず |

### 必要エクイティ（コール側）

| サイズ | α | ICM 中盤 (+4%) | OOP 補正 (+2%) | 合計 |
|--------|---|----------------|---------------|------|
| T1=20% (b=0.2) | 14.3% | 18.3% | 20.3% | **20.3%** |
| T2=33% (b=0.33) | 19.9% | 23.9% | 25.9% | **25.9%** |
| T3=50% (b=0.5) | 25.0% | 29.0% | 31.0% | **31.0%** |
| T3=75% (b=0.75) | 30.0% | 34.0% | 36.0% | **36.0%** |

→ 自分の手 equity が上記を上回ればコール、下回ればフォールド（セミブラフ除く）。

### GTO データ要約

| 型 | call% SBR25 | fold% SBR25 | call% SBR20 | fold% SBR20 |
|----|-------------|-------------|-------------|-------------|
| 型1 ハイドライ | 27.4 | 45.1 | 19.9 | 49.8 |
| 型2 ハイウェット | 33.7 | 44.9 | 27.6 | 48.2 |
| 型3 ロードライ | 44.1 | 35.7 | 42.6 | 35.4 |
| 型4 ローウェット | 45.2 | 36.7 | 44.3 | 36.7 |
| 型5 モノトーン | 49.0 | 41.7 | 42.9 | 46.0 |
| 型6 ペア高 | 28.4 | 67.4 | 22.7 | 68.4 |
| 型7 ペア低 | 25.7 | 43.7 | 15.4 | 53.2 |

> **range 全体の fold% が α より高く見える理由**: OOP レンジの 30–60% は Air カテゴリで、Air 単体 fold ≈ 69%（required_eq に届かない）。範囲全体としては Air share × Air fold ≈ 35% が固まりとして fold に流れます。**α は個別ハンド判定では正しい**。

### カテゴリ別ガイド（型1 ハイドライ vs T1=20%）

| カテゴリ | share | hand_equity | required_eq (20%) | 行動 |
|---------|-------|------------|-------------------|------|
| 2pair (Nutted) | 1.9% | 90%+ | 20.3% | Call 73% / CR 27% |
| TP (Nutted) | 12.2% | 78% | 20.3% | Call 24% / **CR 76%** |
| 2nd pair (Thin value) | 13.8% | 52% | 20.3% | Call 55% / CR 45% |
| 3rd pair (SDV) | 5.4% | 40% | 20.3% | Call 76% / CR 24% |
| ace_high (Semi-bluff 弱) | 7.6% | 24% | 20.3% | Call 73% / CR 25% / fold 2% |
| no_made_hand (Air) | 59.1% | <15% | 20.3% | **fold 76%** |

→ TP は equity 78% で十分 call できますが、CR でさらに value を作るほうが EV 高。SDV (3rd pair) は equity 40% > required_eq 20% でコール。Air は equity < required_eq でフォールド。

### 板別の例外

- **型1/2/6**（ハイ系/ペア高）: A-high は call、それ以下の Air は fold（fold 線が高い）
- **型3/4**（ロー系）: king-high まで call、ガッツショット保持で 50% call
- **型5 モノトーン**: 同じスートが1枚あれば call（FD ブロッカー含む）
- **型7 ペア低**: ペアトリップ目以下は fold 多めだが、A-high は call

### サイズ依存補正

- T1(20%) vs: required_eq 20% → Call ゾーン広い
- T3(50%) vs: required_eq 31% → Call ゾーン狭い、CR or Fold の二極化
- T3(75%) vs: required_eq 36% → 型3 でのみ発生、Nutted で CR、それ未満は fold

### ICM 補正（SBR20）

- SBR20 では required_eq +4% で Thin value の境界が上がる:
  - 型1 call −7.5%, fold +4.7%, CR +2.8%
  - 型7 call −10.3%, fold +9.5%
- 「中途半端な call で 1bb 失うより、強い CR か fold か」を選好

### 決定フロー（3 ステップ）

```
Step 1: ハンドカテゴリ → equity 推定
Step 2: required_eq = α + ICM + OOP補正 を算出（例: T2 vs SBR20 → 25.9%）
Step 3: equity ≥ required_eq か？
        - YES → call（または Nutted なら CR）
        - NO  → fold（ただし Semi-bluff は CR でフォールド equity 取り）
```

### 暗記ポイント（3 つ）

1. **Thin value 以上（equity ≥ 50%）は基本 call**（required_eq 25% を楽勝で超える）
2. **Semi-bluff の FD は equity 36%、required_eq 25% → call 余裕**。OESD (32%) も同様。
3. **SBR20 では call → fold or CR に振る**（required_eq +4% で SDV の一部が border に）

---

## F05B: IP vs CR 応答（BTN が CBet 後 BB から CR を受けて応答）

### 状況判断: CR を受けたときの 3 択

| カテゴリ | 行動 | 理由 |
|---------|------|------|
| Nutted (set/2pair/TPTK 高) | **3bet（オールイン or 部分）** | equity 70%+、コミット |
| Thin value (TPMK/overpair) | call（型3/4/5 では 3bet も可） | call で SDV 取り |
| SDV | call | プロテクション |
| Semi-bluff (FD+) | call（フロート＋実現 equity） | equity 32–48% で MDF 達成 |
| Air | fold | required_eq 30% に届かない |

### 必要エクイティ（CR コール側）

CR x3 サイズに対する pot odds:
- pot 5.5 + CBet 1.1 (20%) + CR 3.3 → 残り 9.9、call 2.2 → pot odds 2.2 / (9.9+2.2) = **18%**
- ただし SPR 残り 1.8 で **暗黙のオッズ + コミット圏入り**
- 中盤 ICM +4% + IP 補正 −2% → required_eq ≈ **20%**

→ equity 20% を超えるカテゴリは call EV+。
- Nutted: 確実超え
- Thin value (50–65%): 超える
- SDV (40–50%): 超える
- Semi-bluff (32–48%): 超える
- Air (<20%): 届かない → fold

### GTO データ要約（全板）

| 型 | fold% SBR25 | call% SBR25 | 3bet% SBR25 | fold% SBR20 | call% SBR20 | 3bet% SBR20 |
|----|-------------|-------------|-------------|-------------|-------------|-------------|
| 型1 ハイドライ | 32.4 | 56.8 | 10.8 | 32.2 | 56.8 | 11.1 |
| 型2 ハイウェット | 30.8 | 63.0 | 6.2 | 30.8 | 60.6 | 8.5 |
| 型3 ロードライ | 27.7 | 61.8 | 10.5 | 28.3 | 57.3 | **14.4** |
| 型4 ローウェット | 28.7 | 59.3 | 12.0 | 29.7 | 52.5 | **17.8** |
| 型5 モノトーン | 31.2 | 55.8 | 13.1 | 33.3 | 43.4 | **23.4** |
| 型6 ペア高 | 35.6 | 63.9 | 0.5 | 35.3 | 64.7 | 0.0 |
| 型7 ペア低 | 30.4 | 51.0 | 18.7 | 32.2 | 47.4 | **20.5** |

**MDF**:
- CR サイズ x3 に対し pot odds ≈ 18% → MDF ≈ 72%（fold≤28%）
- 実 GTO fold% は 28–36%。Air 部分がそのまま fold に流れる構造。

### カテゴリ別応答（型1 ハイドライ SBR25 vs CR）

| カテゴリ | share | hand_equity | required_eq | 行動 |
|---------|-------|------------|-------------|------|
| 2pair (Nutted) | 2.2% | 90% | 20% | Call 100% |
| TP (Nutted) | 21.3% | 75% | 20% | Call 72% / **3bet 28%** |
| 2nd pair (Thin value) | 6.2% | 50% | 20% | Call 88% / 3bet 12% |
| underpair (Thin value) | 5.9% | 50% | 20% | Call 86% / 3bet 14% |
| 3rd pair (SDV) | 2.9% | 38% | 20% | Call 100% |
| ace_high (Semi-bluff 弱) | 20.1% | 24% | 20% | Call 70% / fold 24% / 3bet 6% |
| no_made_hand (Air) | 41.4% | <15% | 20% | **fold 66%** / call 29% |

### 決定フロー（3 ステップ）

```
Step 1: ハンドカテゴリ → equity 推定
Step 2: required_eq = α(CR call) + ICM ≈ 20%
Step 3: equity ≥ required_eq か？
        - Nutted (≥70%): 3bet ジャム（pot コミットでも勝率高）
        - Thin value (50–65%): call（型3/4/5 では 3bet も可）
        - SDV (40–50%): call
        - Semi-bluff (32–48%): call（フロート）
        - Air (<20%): fold
```

### 板別 3bet トリガー

| 型 | 3bet コアハンド |
|----|-----------------|
| 型1 | TP（A2–A7 タイプ）= 28% 3bet |
| 型3 | TP=43–53% 3bet、overpair=19–31% 3bet |
| 型4 | overpair=49–59%, TP=30–57%, 2pair=27–31% |
| 型5 | TP=50–72% 3bet、king ハイブラフあり 15–24% |
| 型7 | 2nd pair=100%, underpair=75–82%, A-high ジャムブラフ 32–53% |

**型7 ペア低の特殊性**: BB の CR レンジに 2nd pair (88s, 22s) が含まれるため、IP の overpair (99–AA) は **A-high の半数を 3bet ブラフに混ぜる**。

### サイズと SPR

- SBR25 / pot 2.25bb / CBet T1=20% → pot 3.15bb → CR=10bb → IP 残り 18bb → 3bet=オールイン（SPR≈1.8）
- SBR20 / pot 2.25bb / CBet T2=33% → pot 3.75bb → CR=11bb → IP 残り 9bb → **3bet=ジャム強制**

### ICM 補正（SBR20 vs SBR25）

- **3bet 頻度が +3–10% 増加**（型3=+3.9%, 型4=+5.8%, 型5=+10.3%, 型7=+1.8%）
- 浅いため call→ジャム or fold の二極化
- SBR20 ではブラフ 3bet が増えるが、fold する範囲はほぼ同じ

### 暗記ポイント（3 つ）

1. **fold ≈ 30%、call ≈ 55–65%、3bet ≈ 10–15%** が全板共通の比率
2. **型6 は 3bet 禁止**（trips にコミット）、**型5/7 は 3bet 多め（15–25%）**
3. **SBR20 では 3bet が 5–10% 増える**（call→ジャムに振る）

---

## 付録: 板別チートシート（暗算用1行サマリー）

| 型 | IP CBet | OOP CR | IP vs CR |
|----|---------|--------|----------|
| 1 ハイドライ | 80% / T1 | 28%（TPコア） | call 57% / 3bet 11% |
| 2 ハイウェット | 65% / T1-T3 | 22% | call 62% / 3bet 7% |
| 3 ロードライ | 53% / T3 | 21% | call 60% / 3bet 12% |
| 4 ローウェット | 70% / T3 | 18% | call 56% / 3bet 15% |
| 5 モノトーン | **98%** / T3 | 10% | call 50% / 3bet 18% |
| 6 ペア高 | 90% / T1 | 6% | call 64% / 3bet 0% |
| 7 ペア低 | 87% / T1-T2 | 31% | call 49% / 3bet 20% |

---

## 整合性チェック

- **新フレームワーク（hand_equity ≥ α + ICM + position）と GTO データの一致**:
  - Nutted (70%+) → 全板でベット 84%+、コール 100%
  - Thin value (50–65%) → 保護ベット 74%（IP）／ コール 73–80%（OOP）
  - Semi-bluff (32–48%) → ベット 70%+（フォールド equity と共存）／ コール 57%
  - Air (<20%) → フォールド 69%
- vol2（cash）と比較し、MTT/ICM 補正は SBR20 で「CBet −5〜−10%、CR +1〜5%、3bet +3〜10%」の方向で一貫。
- TA+/TA- フレームワーク（vol4 既存）と矛盾なし: CR バリューレンジは「Nutted」、ブラフは「Semi-bluff（FD/OESD）」で TA- 判定と一致。

## 旧フレームワーク（参考）

旧版で使っていた HS 閾値は本フレームの「暗算ショートカット」として温存:

| 旧 HS 閾値 | 新カテゴリ | 新フレームでの判断 |
|-----------|-----------|------------------|
| HS≥65 (TPTK) | Nutted の下限 | required_eq < 30% のサイズなら常にコール / ベット |
| HS 55–64 (TPMK) | Thin value の上限 | required_eq < 25% でコール、保護ベット候補 |
| HS 50–54 (TP 弱) | Thin value の下限 | required_eq < 22% のときのみコール |
| HS 42–49 (2nd pair 強) | SDV ↔ Thin value 境界 | コミット圏でのみコール圏 |
| HS 30–41 (TP 弱・3rd pair) | SDV | チェック主体、required_eq < 20% でだけコール |
| HS≤29 (Air/弱ペア) | Air | フォールド主体、BD あれば semi-bluff 昇格 |

## 元データ
- `/home/cuzic/poker-books/mtt-postflop/findings/mtt_flop_cbet_SBR25_BTN_BB.json`
- `/home/cuzic/poker-books/mtt-postflop/findings/mtt_flop_cbet_SBR20_BTN_BB.json`
- `/home/cuzic/poker-books/mtt-postflop/findings/mtt_check_raise_SBR25.json`
- `/home/cuzic/poker-books/mtt-postflop/findings/mtt_check_raise_SBR20.json`
