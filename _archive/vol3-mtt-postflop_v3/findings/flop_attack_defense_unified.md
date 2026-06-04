# フロップ攻撃・守備 統合フレームワーク（CBS ベース）

作成日: 2026-05-24  
データ: pairwise_study (SBR25, 75件) + defense_study (17シナリオ×12ボード)  
スコアリングシステム: **CBS = HP + DP**（generator.py 実装済み）

---

## CBS の3コンポーネント

| コンポーネント | コード名 | 説明 |
|-------------|--------|------|
| **現在価値** | HP（Hand Power） | メイドハンドの強さ（1-9） |
| **将来価値** | DP（Draw Power） | ドローの価値（0-3） |
| **信頼度** | Confidence（HIGH/MID/LOW） | ｜CBS - 閾値｜＋ボード型から算出 |

```
CBS = HP + DP
bet_direction = CBS ≥ threshold    (BTN=5, SB=7, LIMP=7)
confidence    = f(|CBS - threshold|, board_type)
CBet予測%     = FREQ_TABLE[(confidence, bet_direction)]
```

### HP テーブル（現在価値）

| ハンド種別 | HP | 備考 |
|----------|----|----|
| fullhouse | 2 | 極端なスロープレイ補正 |
| third_pair | 3 | |
| quads | 3 | スロープレイ |
| second_pair / underpair | 5 | BTN 閾値ちょうど |
| ace_high / king_high / no_made_hand | 5 | エアー（BTN は混合戦略） |
| set | 5 | スロープレイ補正（実質 HP=7 相当） |
| top_pair / overpair | 7 | |
| two_pair / trips / straight / flush | 9 | |

### DP テーブル（将来価値）

| ドロー種別 | DP |
|----------|-----|
| no_draw / BDFD 1枚 / BDFD 2枚 | 0 |
| gutshot | 1 |
| FD / NFD / OESD | 2 |
| コンボドロー | 3 |

⚠️ **エアーパラドックス**: no_made_hand + OESD → CBS = HP − 2 = 3（チェック方向）

---

## 攻撃（IP CBet）フレームワーク

### 基本ルール

- **CBS ≥ 5（BTN）/ CBS ≥ 7（SB/LIMP）** でベット方向
- 実際の CBet% は Confidence × bet_direction で決まる

### FREQ_TABLE（GTO 実測値で検証済み）

| Confidence | ベット方向（CBS ≥ 閾値） | チェック方向（CBS < 閾値） |
|-----------|---------------------|----------------------|
| HIGH | **79%** | 42% |
| MID  | **67%** | 39% |
| LOW  | **58%** | 37% |

### Confidence の決まり方

```python
distance = |CBS - threshold|
if distance ≥ 3:               → HIGH
if board_type == 1 and dist ≤ 2: → HIGH  # A高ドライ: 2距離でも安定
if board_type == 7 and dist == 1: → LOW   # ペア板: dist=1は不安定
if distance == 2:              → MID
if board_type in (3, 4):       → LOW   # コネクト/ローウェット: 不安定帯広い
```

### ボード型別 実効CBet%（BTN、SRP25）

| ボード型 | RAS | 代表CBS | Confidence | 実測CBet% |
|---------|-----|--------|-----------|---------|
| 型1 A高 | 59 | 7（top_pair） | HIGH | **79%** |
| 型7 ペア板 | 61 | 7（top_pair） | HIGH | **79%** |
| 型2 K/Q高 | 50 | 7 | MID | 67% |
| 型5 ミッド | 53 | 7 | MID | 67% |
| 型6 ロードライ | 41 | 7 | MID | 67% |
| 型3 コネクト | 36 | 7 | LOW | 58% |
| 型4 ローウェット | ≈39 | 7 | LOW | 58% |

RAS と Confidence の対応: **RAS が高い（= IP レンジ優位）ボードほど Confidence が HIGH** になる。

---

## 守備（OOP vs CBet）フレームワーク

攻撃側 CBS と対称的に、守備側も **HP・DP・信頼度** の3コンポーネントで判断する。

### OOP チェックレイズ（CR）閾値

攻撃: `CBS ≥ threshold` → ベット方向  
守備: `HP ≥ CR_threshold(SPR)` → CR 方向

| SPR（SBR） | CR 閾値 | 相当ハンド | 備考 |
|----------|--------|---------|-----|
| ≥8（SBR25 SRP） | **HP ≥ 7** | top_pair 以上 | second_pair ではコール |
| 5〜6（SBR20 SRP） | **HP ≥ 7**（乾燥型）/ **HP ≥ 5**（湿潤型） | top_pair / second_pair+ | 型5/6 では second_pair で CR |
| 2〜3（3BP SBR20） | **HP ≥ 5** | second_pair 以上 | コミット圏拡大 |

### OOP CR の信頼度（ボード型別）— GTO 実測値で検証済み

| ボード型 | CR 信頼度 | top_pair CR% | 振る舞い |
|---------|---------|------------|--------|
| 型1 A高 | **LOW**（トラップ） | **37.6%** | TPTK = ほぼナッツ → コールで引き込み |
| 型2 K/Q高 | **HIGH** | **76.4%** | TPMK は AA/AK に負ける → 即 CR |
| 型3 コネクト | **LOW**（コール温存） | **38.7%** | ドロー多 → CR でポットを膨らませると不利 |
| 型4 ローウェット | **LOW**（コール温存） | **39.1%** | 同上 |
| 型5 ミッド | **HIGH** | **82.1%** | TPMK → AA/AK/KK 等多数に負ける → 即 CR |
| 型6 ロードライ | **HIGH** | **85.4%** | 低TP = 全オーバーカードに負ける → 即 CR |

**型3/4 が LOW な理由**  
コネクト・ローウェットボードは IP のレンジにドロー（FD/OESD）が多く含まれる。
OOP が CR するとポットが大きくなり、IP のドローエクイティが全て乗る。
コールで小さいポットをキープしターンで評価するほうが EV が高い。攻守ともにポット抑制で一致。

**型1 が LOW な理由（エース支配原理）**  
A高でOOPがAを持つ = TPTK = ほぼナッツ（IPのAAのみ上回る）。
IP の広いベットレンジ（多くのブラフ含む）に対してコールで引き込む戦略が最適。

**型2/5/6 が HIGH な理由（エース支配原理）**  
非A高ボードでOOPのTPは常に AA(6コンボ) + AK(9+コンボ) に負ける。
ターンでAが落ちたらスタックを失うリスクがあるため、今すぐ CR で equity を守る必要がある。

### OOP CR 守備 FREQ 参照表（top_pair no_draw 基準）

| 守備信頼度 | top_pair CR 実測% | 典型ハンドの行動 |
|---------|----------------|--------------|
| HIGH（型2/5/6） | **76〜85%** | top_pair → ほぼ CR |
| LOW（型1/3/4） | **37〜39%** | top_pair → コール優先 |

---

## 検証結果サマリー

GTO 実測データ（SRP25 BTN vs BB、12ボード）top_pair|no_draw CR% による照合結果:

| ボード型 | top_pair CR%（実測） | 守備 Confidence |
|---------|-------------------|---------------|
| 型1 A高 | **37.6%** | LOW（トラップ）|
| 型2 K/Q高 | **76.4%** | HIGH |
| 型3 コネクト | **38.7%** | LOW（ポット管理）|
| 型4 ローウェット | **39.1%** | LOW |
| 型5 ミッド | **82.1%** | HIGH |
| 型6 ロードライ | **85.4%** | HIGH |

**3BP での HP 閾値精度**: 分離 +6pp のみ → **ボード型が HP を上回って支配的**  
型6 3BP では second_pair(HP=5) でも CR 84%、型3 3BP では top_pair(HP=7) でも CR 15%。  
3BP の守備は「HP 閾値」より「ボード型別 Confidence」で判断するほうが正確。

### 誤分類の主なパターン（残差）

| パターン | 誤分類理由 | 実測 CR% |
|--------|---------|--------|
| top_pair × 型2 | MID なのに CR 推奨と予測 | 43〜47%（コール寄り） |
| second_pair × 型7（ペア板） | HP=5 < thr=7 → 非CR 予測だが | 51〜61%（CR 推奨） |
| two_pair × 型2/5/6 | HP=9 → CR 推奨だが | 8〜26%（スロープレイ） |

型7ペア板の second_pair（= ペアでない rank のペア）は HP=5 でも CR が有効な例外。  
two_pair 以上の強役は SRP でもスロープレイが多い（HP=9 の平均 CR = 45%）。

---

## 攻守を貫く対称原理

### 攻撃 Confidence vs 守備 Confidence（非対称パターン）

| 型 | RAS | 攻撃 Conf | 守備 Conf | top_pair CR% | 解釈 |
|---|-----|---------|---------|------------|-----|
| 型1 A高 | 59 | HIGH | **LOW** | 37.6% | IP 広くベット、OOP は TPTK でトラップ |
| 型2 K/Q高 | 50 | MID | **HIGH** | 76.4% | OOP のTP は AA/AK に負ける |
| 型3 コネクト | 36 | LOW | **LOW** | 38.7% | 両側ドロー → ポット管理優先 |
| 型4 ローウェット | ≈39 | LOW | **LOW** | 39.1% | 同上 |
| 型5 ミッド | 53 | MID | **HIGH** | 82.1% | OOP のTP は AA/AK/KK 等に負ける |
| 型6 ロードライ | 41 | MID | **HIGH** | 85.4% | 低TP = 全オーバーカードに負ける |
| 型7 ペア板 | 61 | HIGH | 特殊 | — | second_pair が例外的に CR 推奨 |

**攻撃 HIGH → 守備 LOW（型1のみ）**: A高ボードでOOPがAを保有 = TPTK = ほぼナッツ → トラップで引き込む。  
**攻撃 MID → 守備 HIGH（型2/5/6）**: 非A高ボードでOOPのTPは AA/AKに負ける → 即CRで保護。  
**攻撃 LOW → 守備 LOW（型3/4）**: 双方ともドロー多 → ポット拡大を嫌い、コール温存。

### Confidence 非対称の理論的解明

**なぜ攻撃 Confidence（RAS 依存）と守備 Confidence（別の原理）は一致しないのか？**

攻撃 Confidence と守備 Confidence は **独立した2つの軸** に依存する：

```
攻撃 Confidence = f(RAS)           -- IP のレンジがボードに何割接続しているか
守備 Confidence = f(TP脆弱性)      -- OOP のトップペアが IP のレンジに何割負けるか
```

この2軸は独立して変動するため、RAS が高くても守備 Confidence が低い（型1）や、
RAS が中程度でも守備 Confidence が高い（型2/5/6）という非対称が生まれる。

#### エース支配原理（ACE DOMINANCE PRINCIPLE）

```
A がボードにある (型1):
  → OOP の Ax = TPTK = ほぼナッツ
  → IP の AAのみ 上回る（3コンボ）
  → TP 脆弱性 = 極低 → Defense Confidence = LOW（コールトラップ最適）

非 A のドライボード (型2/5/6):
  → OOP の TP = TPMK 以下
  → IP の AA(6) + AK(9+) が OOP の TP に全勝
  → TP 脆弱性 = 高 → Defense Confidence = HIGH（即 CR で保護）

ウェットボード (型3/4):
  → OOP の TP = 脆弱 だが、ドロー多でポット拡大が逆効果
  → IP の ドローエクイティが全部乗る → コールでポット管理
  → Defense Confidence = LOW（ポット管理優先）
```

#### 数値による確認

| 型 | OOP の TOP PAIR 例 | IPレンジで上回るコンボ | TP脆弱性 | 実測 CR% |
|---|----------------|-------------------|---------|--------|
| 型1 A72 | AK (TPTK) | AA のみ（3コンボ） | **低** | **37.6%** |
| 型2 K98 | KQ (TPMK) | AA(6) + AK(9〜12) | **高** | **76.4%** |
| 型5 J73 | JT (TPMK) | AA, KK, QQ... 多数 | **高** | **82.1%** |
| 型6 742 | 7x (TPWK) | 全オーバーカード | **最高** | **85.4%** |
| 型3 T98 | T9 (TPTK) | AA, AK など | 高いが... | 38.7% |

型3 は脆弱性が高いにもかかわらず CR% が低い（39%）。これはポット管理の効果：
CR でポットが膨らむと IP のフラッシュドロー・ストレートドローの エクイティが乗り、
期待値がコールを下回る。「保護の必要性 > ドローコスト」が成立するのは **ドライボードのみ**。

#### 統一原則

```
攻撃 Confidence = 高RAS (≥55) → HIGH、中RAS (40-55) → MID、低RAS (<40) → LOW
守備 Confidence = 乾燥ボードでAなし → HIGH、乾燥ボードでAあり → LOW、ウェット → LOW
```

特に「乾燥ボードで A なし = OOP の TP が AA/AK に支配される」という単純な原則が
守備 Confidence を決める。RAS（攻撃 Confidence の源泉）とは無関係に変動する。

---

### HP の対称性（SRP25、BTN vs OOP）

攻撃側（IP=BTN）と守備側（OOP=BB）は **同じ HP 尺度** を使うが判断が逆方向になる：

| HP 値 | 代表ハンド | IP の行動 | OOP の行動（vs CBet） |
|------|---------|---------|------------------|
| 2〜3 | third_pair / fullhouse | チェック | フォールド |
| 5 | second_pair / underpair | BTN ではベット | SPR≥8 ではコール |
| 7 | top_pair / overpair | 常にベット | SPR≥8 では CR or コール |
| 9 | two_pair+ / trips | 常にベット | 即 CR（コミット確認） |

### コール域（HP=5 帯）の意味

IP が HP=5（second_pair / underpair）でベットするとき、OOP の同じ HP=5 手は：
- **SPR≥8（SBR25 SRP）**: コール（まだコミットラインに届かない）
- **SPR2〜3（3BP）**: CR（コミット圏に入り、IP のベットに押し返す）

これが「スタックが短くなるほど OOP の CR 率が上がる」根拠。

### SBR 補正（CR 閾値の変化）

| SBR | SPR | OOP CR 閾値 | CR 率変化 |
|-----|-----|-----------|---------|
| 25 | ≈8 | HP ≥ 7（top_pair） | 基準 |
| 20 | ≈6 | HP ≥ 7（乾燥）/ HP ≥ 5（湿潤） | +12〜18pp 上昇 |
| 15 | ≈4.5 | HP ≥ 5（推定） | さらに拡大 |
| 3BP | ≈2.2 | HP ≥ 5（second_pair） | 最大拡大 |

---

## 3BP は別ルール（CBS が機能しない領域）

GTO データ検証の結果、3BP（SPR≈2.2〜2.7）では CBS ルールが「常数予測（50%/20%）」にすら
負ける。3BP はスコアリングではなく **is_pair（ペアがあるか）** を軸にした別枠組みが必要。

### 検証結果（WRMSE）

| ルール | SRP25 | 3BP OOP | 3BP IP |
|-------|-------|---------|--------|
| CBS（HP閾値） | **20.5%** | 48〜54% | 32〜34% |
| 常時50% / 常時20% | — | 38.2% | 31.0% |
| **is_pair ルール（新）** | — | **30.5%** | **31.0%（同等）** |

### 3BP ルール（is_pair ベース）

#### 守備 OOP（3ベット側がIPのCBetに応答）

```
① ペアなし（no_made_hand / ace_high / king_high）→ フォールド
   [実測: fold=30〜67%]

② set / fullhouse → コール（スロープレイ）
   [実測: call=88%]

③ ペアあり HP≥5（underpair / second_pair / top_pair / overpair）→ CR
   [実測: CR=58〜72%、fold=0%]

④ two_pair / trips（HP=9）→ 混合（CR≈49%、コール≈51%）
   ボード型で判断: 型5/6=CR積極、型1/3=コール気味
```

#### 守備 IP（コール側がOOPリードに応答）

```
① 全ハンド: 基本コール（トラップ）
   [実測: 平均CR=18〜29%]

② 型5/6（ミッド/ロードライ）× HP≥5 のみ CR 有効
   [実測: underpair=81%、second_pair=56〜84%]

③ set / two_pair / top_pair / overpair → コール（SPR低いほどトラップ優先）
```

#### 攻撃 OOP（3ベット側がCBet）

```
→ 全レンジCBet（実測 86〜92%）
   set は例外（混合〜スロープレイ）
```

#### 攻撃 IP（コール側がCBet）

```
→ 混合戦略（ほぼ全ハンド 45〜60%）
   is_pair / HP によらず flat → 定数ルール「約50%でCBet」
```

### なぜ CBS が 3BP で機能しないか

HP=5 に「ペアあり（underpair/second_pair）」と「ノーペア（ace_high/king_high/no_made）」
が混在し、前者は commit zone（fold=0%、CR=58%+）、後者はフォールド主体（fold=30〜67%）。
CBS は this 区別を持たないため、HP=5 での予測が大きく外れる。

3BP は SPR が低く「コミット判断」の問題であり、ハンドの相対強度（HP）より
「既にペアを持っているか」という is_pair フラグが行動を決定する。

---

## 実用判断フロー（CBS 統合版）

### IP（攻撃側）

```
1. CBS = HP + DP を計算
2. CBS ≥ 5（BTN）or CBS ≥ 7（SB/LIMP）? → ベット方向 / チェック方向
3. |CBS - 閾値| と ボード型 → Confidence (HIGH/MID/LOW)
4. FREQ_TABLE[(Confidence, 方向)] = 実際の CBet%
   例: top_pair(CBS=7) BTN 型1 → HIGH × TRUE → 79%
   例: second_pair(CBS=5) BTN 型3 → LOW × TRUE → 58%（境界なので低め）
```

### OOP（守備側）

```
1. OOP 自身の HP + DP を計算
2. HP ≥ CR_threshold(SPR)?  → CR 方向 / コール or フォールド
   SRP25: HP ≥ 7、SRP20 湿潤: HP ≥ 5、3BP: HP ≥ 5
3. ボード型 → CR 信頼度（エース支配原理）
   型1 A高: LOW → コールトラップ優先（TPTK=ほぼナッツ）
   型2/5/6: HIGH → 積極 CR（AA/AKに負ける脆弱TP）
   型3/4 ウェット: LOW → コールでポット管理
4. draw がある場合: DP ≥ 2（FD/OESD）ならコールで equity を守る
```

---

## コール域とその解釈

| ボード型 | IP ベット開始（CBS） | OOP CR 開始（HP） | コール域の意味 |
|---------|----------------|---------------|------------|
| 型1 A高 | CBS=5（HP=5） | HP=7（top pair） | HP=5 帯（second_pair/underpair）→ 広くフロート |
| 型2 K/Q高 | CBS=5 | HP=7 | HP=5〜6 帯 → 選択的フロート |
| 型3 コネクト | CBS=7（IP も絞る） | HP=7 | HP=7 に集中 → ほぼ二択 |
| 型6 ロードライ | CBS=5〜7 | HP=7 | HP≤5 はほぼフォールド → 二択 |

---

## 書籍活用ポイント

- **攻撃（ch03、ch04）**: CBS ≥ 5 (BTN) / CBS ≥ 7 (SB) を軸に、Confidence でベット率調整
- **守備（ch03 SRP 守備）**: HP ≥ 7 (SRP) / HP ≥ 5 (3BP) + ボード型で CR or コール決定
- **3BP（ch10）**: IP の深いトラップ（HP=9 でもコール）+ セット逆転則
- **暗記推奨**:
  - HP: 5 = second_pair/underpair/set/air（BTN境界）、7 = top_pair/overpair（SB境界）
  - CR閾値: SRP → HP≥7、3BP → HP≥5
  - ボード型 CR 信頼度: 型1 = トラップ（A高）、型2/5/6 = 積極CR（非A高ドライ）、型3/4 = コール（ウェット）
