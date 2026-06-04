# UCBS 検証結果 — Cash + MTT 統一達成

検証日: 2026-05-27
モデル: UCBS (Universal CBS, 5 軸)
ファイル: `cash-postflop/ucbs.py`, `cash-postflop/ucbs_mtt_eval.py`

## 結果サマリ

| Context | Data | n records | combos | WRMSE |
|---|---|---:|---:|---:|
| **cash_100bb** | cash_5cat_gto.json | 347 | 20,146 | **21.43%** |
| **mtt_25bb** | draw_study_*.jsonl (10 files) | 1,980 | 150,135 | **20.41%** |

**結論**: 1 つの UCBS 構造で cash と MTT 両方を WRMSE < 22% で予測可能。

## 構造

```
UCBS = HP + DP + Confidence + Size (+ Context)

  HP_TABLE (共通):     hand → 1-9
  DP_TABLE (共通):     draw → 0-3
  Confidence (共通):   f(|CBS - threshold|, board_type)
  Size (context):     polarize 判定で 33% / 116%
  
Context 切替:
  thresholds (per scenario)
  hp_overrides (per context, 微調整)
  hand_freq_mod (per context, bias 補正)
  freq_small / freq_overbet (per context)
```

## MTT ファイル別精度

| ファイル | scenario | n | WRMSE |
|---|---|---:|---:|
| SRP20_SB | SB cbet | 226 | **14.3%** |
| SRP25_SB | SB cbet | 229 | 16.9% |
| SRP20_SB_cc | BTN IP after SB call | 223 | 18.6% |
| SBR25 | BTN baseline | 80 | 19.1% |
| LIMP20_SB | SB limp pot | 160 | 19.3% |
| SRP25_SB_cc | BTN IP after SB call | 229 | 19.4% |
| LIMP25_SB | SB limp pot | 160 | 19.6% |
| SRP20 | BTN cbet | 223 | 25.3% |
| SRP25 | BTN cbet | 229 | 25.9% |
| SRP20_CO | CO cbet | 221 | 27.3% |

SB IP cbet が最も精度高い。BTN/CO は範囲広く、追加調整余地あり。

## Hand 別 bias

両 context で残るバイアス:

| Hand | Cash bias | MTT bias | 解釈 |
|---|---:|---:|---|
| no_made_hand | -1% | -3% | 良好 |
| ace_high | -2% | +2% | 良好 |
| king_high | -4% | +3% | 良好 |
| low_pair | +4% | +14% | MTT で大きい (n=1260) |
| underpair | -1% | -8% | 良好 |
| third_pair | +3% | +9% | MTT 軽微 |
| second_pair | 0% | **+17%** | MTT 改善余地 |
| top_pair | +6% | +2% | 良好 |
| overpair | -2% | -3% | 良好 |
| two_pair | +1% | +2% | 良好 |
| straight | +7% | -4% | 良好 |
| flush | -1% | -3% | 良好 |
| set | -3% | +12% | MTT 改善余地 |
| trips | 0% | -3% | 良好 |
| fullhouse | +1% | +23% | MTT 小サンプル (n=143) |

## Context 別パラメータ最終形

### cash_100bb
- thresholds: 全 position = 5
- polarize_enabled: True
- hp_overrides: low_pair=1, set=9, trips=9, flush=7, two_pair=8, king_high=3, no_made_hand=3
- hand_freq_mod: 12 entries で bias 補正

### mtt_25bb
- thresholds: 全 position = 5
- polarize_enabled: False
- hp_overrides: なし
- hand_freq_mod: 9 entries で MTT 短スタック特性に補正

## 残課題

1. **MTT second_pair / set / low_pair の bias** が +12〜17%
   - mtt_25bb の hand_freq_mod 微調整で更に改善可
2. **3BP context** が未登録（draw_study_3BP*.jsonl は skip）
3. **mtt_50bb / mtt_100bb / mtt_200bb / cash_50bb** の検証データなし

## UCBS の価値（再確認）

| 観点 | 効果 |
|---|---|
| 統一構造 | HP+DP+Confidence+Size が cash/MTT 両対応 |
| Context 切替 | 1 パラメータで game type 変更 |
| 精度 | Cash 21.43% / MTT 20.41%（両方 < 22%） |
| 拡張性 | 3BP, ICM, PKO 等を context 追加で対応 |
| 学習者 | 1 つの式を覚えれば cash も MTT も使える |
| 書籍 | 各巻で同じ用語、context 表で違いを示せる |
