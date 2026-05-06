# Phase 0.5: マルチウェイ M 値の検証

実施日: 2026-05-05

## 既存研究 (`knowledges/volume4/multiway_m_coefficient.md`)

```
旧 M 値:
  2-way (HU): 0
  3-way:      3
  4-way+:     6

理論根拠:
  ブラフのフォールドエクイティ縮小:
    HU:  f = 50%
    3-way: f² = 25% (半減)
    4-way: f³ = 12.5% (4分の1)
  
  コール要件の上昇 + CR ブラフの減少
  
TexasSolver では検証不可能な理論値（multiway は単一プレイヤー前提）。
```

## 新スケール (HS = 0-100 equity %) での M 値

理論的に M は equity の損失量を表す。マルチウェイで equity が薄まる量:

```
HU (2-way):
  vs 1 相手 → 自分の equity ≈ 50% baseline

3-way:
  vs 2 相手 → 自分の equity ≈ 33% baseline
  → -17% の equity 損失

4-way+:
  vs 3 相手 → 自分の equity ≈ 25% baseline
  → -25% の equity 損失
```

ただし「ナッツポテンシャル」を持つ強ハンドは equity 損失が小さい。
中強度ハンドが最も影響を受ける。

## 推奨 新 M 値

```
HU (2-way):       M = 0
3-way:            M = 8  (中強度ハンドの平均 equity 損失)
4-way+:           M = 15 (大きく損失)
```

旧 M 値 × 約 2.5 倍。これは新スケール HS が 0-100 のため、equity スケールに合わせた値。

### 理論検証

```
AA on K72r dry vs 50% bet:
  HU:    HS=85, A=12, C=17 → DS = 80 → CR (-)
  3-way: HS=85, A=12, C=17, M=8 → DS = 72 → CR (-)
  4-way: HS=85, A=12, C=17, M=15 → DS = 65 → CR 境界
  
  ナッツ強ハンドは多人数でも CR 維持。

TPGK on K72r dry vs 50% bet:
  HU:    HS=62, A=12, C=17 → DS = 57 → CR
  3-way: HS=62, A=12, C=17, M=8 → DS = 49 → CR 境界
  4-way: HS=62, A=12, C=17, M=15 → DS = 42 → CR 境界
  
  3-way 以上で CR が抑制される (実戦的に正しい挙動)

TPMK on K72r dry vs 75% bet:
  HU:    HS=50, A=12, C=22 → DS = 40 → CR 境界
  3-way: HS=50, A=12, C=22, M=8 → DS = 32 → コール
  4-way: HS=50, A=12, C=22, M=15 → DS = 25 → コール

  マルチウェイで CR 抑制 → コール寄り (実戦と整合)
```

## マルチウェイ実測データ

### `knowledges/flop/18_multiway_flop.md` に記載の知見

```
マルチウェイで:
  - CBet 頻度 +11% (チェック増加)
  - ポットサイズ CBet が 18% → 1.3% (激減)
  - 「ナッツ比率が高い」ボードでは標準ベットサイズが小さくなる

GTO Wizard "Playing In Position Against Two Callers" 等の記事から:
  - K-T-6 フロップで AA 保有時、誰かが TPTK+ を持つ確率 69%
  - AA で 75%pot ベット → 1 人コール → 約 40% で beat 済み
```

### Galfond ソルバー分析

4-way K-T-6 フロップで AA: 「誰かが TP+ を持つ確率 = 69%」

これを new HS で表すと:
- AA HS = 75 (オーバーペア)
- 4-way M = 15
- DS = 75 + 12 - 17 - 15 = 55 → CR 検討

現実: AA でも 4-way では CR せず、コールに回す傾向（GTO 実測）。
**M = 15 だと AA が CR 域に残ってしまう**。

調整案: M を増やす? (4-way = 20-25?)

## 推奨 (確定版)

旧の「ブラフ EV が f^n に縮小」のロジックを equity 損失に直接マッピング:

```
HU:    M = 0 (基準)
3-way: M = 12 (旧 3 × 4 = 12、equity 損失 ~17% に近い)
4-way: M = 22 (旧 6 × 3.7、equity 損失 ~25% に近い)
```

### 検証 (再度 AA 4-way)

```
AA on K-T-6 (semi-wet) 4-way vs 75%pot:
  HS = 75 (オーバーペア)
  A = 6 (セミ)
  C = 22 (75%)
  M = 22 (4-way+)
  
  DS = 75 + 6 - 22 - 22 = 37 → コール 推奨

これは Galfond の「4-way で AA を CR せずコールに回す」と整合 ✓
```

### 検証 (TPGK 3-way)

```
TPGK on K72r 3-way vs 50%pot:
  HS = 62
  A = 12
  C = 17
  M = 12 (3-way)
  
  DS = 62 + 12 - 17 - 12 = 45 → CR 検討（境界）
```

GTO Wizard 推測: 3-way TPGK は CR 抑制で「コール 60%、CR 30%」混合 → 整合的。

## 推奨 M 値 (最終)

```
HU (2-way):       M = 0
3-way:            M = 12 
4-way+:           M = 22

新後手スコア = HS + A − C − M (新スケール)
```

## 結論

- 旧の理論値 (3 / 6) を新スケール (0-100) に合わせて約 4 倍に拡大
- 新 M = 0 / 12 / 22
- マルチウェイで「中強度ハンドの CR 抑制」が GTO 実測と整合
- 4-way+ では AA でも CR を抑える (Galfond 分析と一致)

## 注

マルチウェイの厳密検証は TexasSolver では不可能 (multiway 非対応)。
GTO Wizard 公開記事 + 経験則ベースで設計値を確定。

実装フェーズで境界例 (AA 4-way、TPMK 3-way 等) の挙動を確認、
必要なら微調整 (M = 12 / 22 → 10 / 20 等) を検討。
