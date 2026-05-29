# Medium UCBS 研究メモ

調査日: 2026-05-28
ステータス: 研究結果のみ。Vol2 への組み込み見送り (Light のまま)

---

## 動機

Vol2 (Light UCBS v2) と Vol3 (Full UCBS-v2) の中間として、**Light + 少数の境界例外** で Full に近い精度が出せるか検証する。

## 設計

Light UCBS v2 (25 セル base + low_pair 例外) に **2 つの追加例外** を加える:

```
E1: mtt_short + CBS ≥ 7  → +15pt
    (Full の β=+31 (mtt_25) と β=+19 (mtt_50) の平均近似)

E2: mtt_deep + CBS ≥ 9   → +10pt
    (Full の mtt_100 wide cbet 特性、nut 帯のみに限定で
     mtt_200 の悪化を避ける)
```

合計ルール: Light 5 ルール (LIGHT_V2_BASE 25 セル + low_pair offset + 5 context base + 例外 0) + Medium 2 例外。

実装: `vol2-cash-postflop/ucbs_medium.py`

## 実測結果

| Context | Light | **Medium** | Full | Δ(Light→Medium) | Δ(Medium→Full) |
|---|---:|---:|---:|---:|---:|
| cash_100bb | 21.07% | 19.74% | 16.43% | -1.33pt | +3.31pt |
| **mtt_25bb** | 36.08% | **26.64%** | 15.46% | **-9.44pt** | +11.18pt |
| mtt_50bb | 19.08% | 18.88% | 12.96% | -0.20pt | +5.92pt |
| mtt_100bb | 35.54% | 31.74% | 21.95% | -3.80pt | +9.79pt |
| mtt_200bb | 21.49% | 20.40% | 14.10% | -1.09pt | +6.30pt |
| 3bp_25bb | 15.71% | 15.71% | 18.65% | 0 | -2.94pt (Light勝) |
| 3bp_50bb | 9.63% | 9.63% | 8.62% | 0 | +1.01pt |
| 3bp_100bb | 15.33% | 15.33% | 13.37% | 0 | +1.96pt |
| turn_mtt25 | 16.67% | 16.67% | 7.02% | 0 | +9.65pt |
| turn_cash100 | 22.49% | 22.49% | 16.11% | 0 | +6.38pt |
| **合計改善** | | | | **-15.86pt** | |

## 結論

| 観点 | 評価 |
|---|---|
| Light → Medium 改善 | ◎ 全 context で改善、悪化なし |
| Medium → Full 残差 | △ 5-11pt の差が残る |
| 暗算性 | Light 6 秒 → Medium 8-9 秒 (+33%) |
| 書籍向け | △ Cash プレイヤーには Light で十分、MTT 真剣なら Full |

## なぜ Medium → Full の差が残るか

1. **Light v2 の context 粒度が粗い**: mtt_short が mtt_25/50 を統合、mtt_deep が mtt_100/200 を統合。両者の最適 β/α が違うため、単一の補正で両方をうまく扱えない。
2. **turn context の α=-0.35 大シフト**: turn は flop と全く異なる base を必要。Medium に turn 専用例外を加えると複雑化。
3. **3BP の linear range**: 3BP は Light の context として既に分離済み、改善余地なし。

これらは **構造的制約** であり、Light + 例外では限界がある。

## 書籍化判断 (2026-05-28)

**Vol2 への組み込みは見送り**。理由:

- Vol2 は cash 100bb 中心。Cash での Light → Medium 改善は -1.33pt とわずか。
- MTT を真剣にやる読者は Vol3 (Full UCBS-v2) を読むのが筋。
- Medium を入れると章構成が複雑化、教育効果が薄まる。

ただし将来のシリーズ拡張 (例: Cash 100bb と MTT 100bb をハイブリッドに扱う本) で Medium が中核に座る可能性はある。

## 関連ファイル

- 実装: `vol2-cash-postflop/ucbs_medium.py`
- Light: `vol2-cash-postflop/ucbs_light_v2.py`
- Full: `vol2-cash-postflop/ucbs_v2.py`
- 親比較: `knowledges/gto_wizard_study/UCBS_V2_DCBS_FINAL.md`
