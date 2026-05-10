# M 係数（マルチウェイ補正）GTO Wizard Elite 検証プロトコル
Task #130

> **NOTE (2026-05-05)**: 旧スケール (HS 0-30) 時代の検証プロトコル。
> 新スケール (HS 0-100 equity %) における M 値の妥当性検証は
> [`../ds_redesign_v2/multiway_m_validation_v2.md`](../ds_redesign_v2/multiway_m_validation_v2.md) を参照。
> 新スケール M = {HU 0, 3-way 12, 4-way+ 22}。

## 概要

DS 式のマルチウェイ補正係数 M の検証。

```
DS = HS + A - 3 - C - M
M = 0 (HU), 3 (3-way), 6 (4-way+)
```

TexasSolver は HU 専用のため、GTO Wizard Elite の 3-way/4-way シナリオで検証する。

## 検証原理

DS = HS + A - 3 - C - M ≥ 0 → コール以上
DS < 0 → フォールド

HU で DS=0 のハンドがコール/フォールド境界となる。
3-way で M=3 が正しければ、そのハンドの DS = -3 → フォールドになるはず。

具体的に: K72r board, 33% CBet (C=3, A=3):
- HU DS = HS - 3  → HS ≥ 3 でコール
- 3-way DS = HS - 6 → HS ≥ 6 でコール（ボトムペア=4はフォールド）
- 4-way DS = HS - 9 → HS ≥ 9 でコール（アンダーペア=6もフォールド）

## GTO Wizard Elite 検証手順

### セットアップ

1. GTO Wizard Elite にログイン
2. Flop Play → Multiway シナリオを選択
3. BTN vs BB vs CO（3-way）シナリオを選択
4. ボード: K72r（K♠7♦2♣ または類似ドライボード）
5. BTN が 33% ポット CBet した場合の BB の応答を確認

### 確認ハンド一覧（OOP = BB の応答）

| ハンド | HS | HU DS | 3-way DS (M=3) | 3-way DS (M=6仮) | 期待（M=3正） |
|--------|----|----|----|----|-----|
| KT（TPMK=8） | 8 | 5 | 2 | -1 | CALL |
| K5（TPWK=6） | 6 | 3 | 0 | -3 | CALL境界 |
| JJ（アンダーペア=6） | 6 | 3 | 0 | -3 | CALL境界 |
| A2（ボトムペア=4） | 4 | 1 | -2 | -5 | FOLD ← 重要！ |
| 65s（OESD+BDFD=10） | 10 | 7 | 4 | 1 | CALL |
| A7（セカンドペア強=9） | 9 | 6 | 3 | 0 | CALL境界 |

**核心的確認ポイント**:
- HU ではボトムペア（HS=4, DS=1）が CALL → GTO CALL 多数
- 3-way でボトムペア（DS=-2）が FOLD → GTO FOLD 多数
- これが確認できれば M=3 の妥当性が証明される

### 4-way 検証

1. 4-way シナリオを選択（BTN vs BB vs CO vs HJ など）
2. 同じボードで同じ確認ハンド
3. KT (HS=8): DS = 8 - 9 = -1 → FOLD
4. KQ (HS=15): DS = 15 - 9 = 6 → CALL
5. セット (HS=30): DS = 30 - 9 = 21 → RAISE

M=6 が正しければ、KT（アンダーペア付近）は 4-way でフォールドになるはず。

## 期待結果サマリー

| シナリオ | M | HS≥N でコール | 具体例 |
|---------|---|-------------|------|
| HU（33% C=3） | 0 | HS ≥ 3（ボトムペア以上） | A2 CALL |
| 3-way（33% C=3） | 3 | HS ≥ 6（TPWK/アンダーペア以上） | A2 FOLD, JJ CALL境界 |
| 4-way（33% C=3） | 6 | HS ≥ 9（セカンドペア強以上） | JJ FOLD, A7 CALL境界 |

## 代替検証方法（GTO Wizard 不要）

**TexasSolver + 手動マルチウェイ近似**:
TexasSolver はマルチウェイ非対応だが、HU で相手の CBet レンジを「よりタイト（より多くの強ハンド）」に設定することで 3-way 相当の圧力を模倣できる可能性がある。ただしこれは近似であり正確な検証にはならない。

**既存文献からの理論的根拠**:
- 3-way ポットでの IP CBet 頻度は HU に比べて約 20-25 ポイント低い（GTO Wizard の公開データ: 65% → 42%）
- この差を DS スケールに換算すると、CBet 頻度低下は「より強いハンドが必要」を意味する
- HS の代表値 H3=17, H2=11, H1=4 から見ると、M=3 で H2 の下限が 7→10 に上がる = 3-way でのコール基準が H2 中盤以上に
- これは「3-way ではミドルペア以下は大きなアクションに対して慎重に」という poker の常識と整合

## ステータス

**現在: 未検証（2026-05-01 時点）**

GTO Wizard Elite アクセス時に上記手順で検証を実施し、結果を
`knowledges/volume4/results/m_coef_verify/` に保存する。

確認すべき最小限のシナリオ:
1. K72r 3-way BTN vs BB vs CO: BB の応答を A2（ボトムペア）で確認
2. K72r 4-way: JJ（アンダーペア）の応答確認

これらが理論通りになれば M=3/6 の妥当性が概ね確認できる。
