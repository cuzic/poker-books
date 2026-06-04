# UCBS 3BP Context 追加検証結果

検証日: 2026-05-27
追加 context: `mtt_3bp_ip`, `mtt_3bp_oop`

## 結果サマリ（全 context）

| Context | Records | combos | WRMSE |
|---|---:|---:|---:|
| Cash 100bb | 347 | 20,146 | **21.43%** |
| MTT 25bb (SRP/LIMP) | 1,567 | 137,486 | **20.79%** |
| **MTT 3BP IP (BTN caller)** | 213 | 5,846 | **27.14%** |
| **MTT 3BP OOP (SB 3-bettor)** | 200 | 6,803 | **41.91%** |
| **MTT 全体** | 2,393 | 162,784 | 22.33% |

## 3BP の構造的特徴（実測）

### 3BP_IP (BTN コーラー、低 SPR linear range)

| Hand | bet% | Pattern |
|---|---:|---|
| top_pair | 97% | full bet |
| second_pair | 88% | high |
| third_pair | 67% | high |
| no_made_hand | 49% | mid-bluff |
| ace_high | 65% | bluff |
| low_pair | 53% | mid |
| set | 27% | slowplay 弱 |
| two_pair | 68% | linear value |
| fullhouse | 24% | slowplay |

→ **Linear range**: HP に応じて単調増加（slowplay 軽め）

### 3BP_OOP (SB 3-bettor、低 SPR polarize)

| Hand | bet% | Pattern |
|---|---:|---|
| top_pair | 91% | full bet |
| underpair | 60% | bet (board × pair) |
| no_made_hand | 51% | air bluff |
| ace_high | 40% | bluff |
| second_pair | 26% | rare bet |
| two_pair | 10% | **heavy slowplay** |
| third_pair | 8% | rare |
| set | 2% | **extreme slowplay** |
| low_pair | 1% | check |

→ **U 字型 (ポラライズ)**: 強と air が打つ、中間は check

## 構造的限界

CBS フレームワーク（HP + DP の単調スコア → freq map）は **monotonic な分布** を前提に設計されています。3BP_OOP の U 字型分布は CBS の根本前提と対立します。

**現在の対処（部分的）:**
- `hp_overrides` で set/two_pair などを低 HP に押し下げ
- `hand_freq_mod` で個別補正
- `simple_confidence` で board_type 修飾を無効化

しかし、これらは「正しい予測」ではなく「平均的 bias 補正」にとどまります。

## 構造的限界を超える選択肢

### A. 3BP_OOP を別モデル化（CBS から離脱）

```python
# polarize-aware モデル: HP→freq を U 字に
def freq_polarized_oop(hp):
    if hp >= 9: return 0.05  # slowplay (set, 2pair)
    if hp >= 7: return 0.85  # top_pair, overpair
    if hp == 5: return 0.30  # middle pair
    if hp == 3: return 0.10  # third pair, etc
    return 0.50  # air bluff (HP=2)
```

WRMSE は劇的改善するが、CBS の統一構造を破壊。

### B. UCBS-v4: U 字対応 freq 関数

```python
# context 別に freq マップを多項式や U 字関数で定義
freq_curve = {
    "linear": lambda hp: 0.45 + 0.07 * hp,     # MTT 25bb など
    "polarized_v": lambda hp: ...               # 3BP_OOP 用 U 字
}
```

### C. 現状を受容（推奨）

| 観点 | 受容判断 |
|---|---|
| Cash + 標準 MTT で WRMSE < 22% 達成済み | ✓ 実用十分 |
| 3BP_OOP のみ 42% の例外 | 文書化して限界明示 |
| 書籍では「3BP_OOP は polarize で別ルール」と注記 | 教育的にも妥当 |

## 推奨

**C. 現状受容 + 3BP_OOP の特殊性を文書化**:

- UCBS は cash 100bb と MTT 標準シナリオ（SRP, LIMP, 3BP_IP）で実用精度（WRMSE 20-27%）
- 3BP_OOP は CBS 構造の限界を超える polarized 分布のため、別ルール（slowplay 中心の経験則）が必要
- 書籍ではこれを「UCBS の適用範囲」として明示

## 全 4 context の実用評価

| Context | 実用判定 | 備考 |
|---|---|---|
| cash_100bb | ★★★ | 21.43%、書籍即採用可 |
| mtt_25bb | ★★★ | 20.79%、書籍即採用可 |
| mtt_3bp_ip | ★★ | 27%、linear だが追加 tuning で改善可能 |
| mtt_3bp_oop | ★ | 42%、CBS の構造的限界、別アプローチ必要 |
