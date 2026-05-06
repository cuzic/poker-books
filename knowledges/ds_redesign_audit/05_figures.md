# 調査05: 図版・チャート inventory（数値固定の画像）

実施日: 2026-05-05

## 巻別の図版数

| 巻 | 章での参照 | images/ ディレクトリ | 主要 figcaption テーマ |
|---|---:|---:|---|
| preflop | **58** | 55 | Score 計算、レンジテーブル、3-bet など |
| flop (巻②) | **24** | 70 | HandScore、ボード分類、MDF、ドロー完成率 |
| flop-advanced (巻③) | 0 | 1 | （図版なし） |
| volume4 (巻④) | **0** | 0 | （図版なし） |
| volume5 (巻⑤) | **0** | 0 | （図版なし） |
| volume6 (巻⑥) | **0** | 0 | （図版なし） |
| digest | **0** | 0 | （図版なし） |
| **合計** | **82** | **126** | |

**重要発見**: 巻③/④/⑤/⑥/digest は図版を一切使っていない。スケール変更による画像影響は **巻① preflop と巻② flop に限定**。

## 数値再生成が必要な flop 画像

### A. HandScore 数値が焼き込まれている可能性が高い (要再生成)

| 画像 | alt 内容 | 章 | 重要度 |
|---|---|---|---|
| `f03-fig2-position-handscore-bars.jpg` | UTG〜BB各ポジションのフロップ平均HandScore比較棒グラフ | flop/02 | 高（HS 数値） |
| `f17-fig1-spr-handscore-map.jpg` | SPRとHandScoreを2軸にした4象限判断マップ | flop/15 | 高（HS 値が軸） |
| `f18-fig2-multiway-range-contraction.jpg` | プレイヤー数別推奨HandScoreしきい値テーブル | flop/16 | 高（しきい値） |

### B. MDF / 数値が焼き込まれている可能性 (要見直し)

| 画像 | alt 内容 | 章 |
|---|---|---|
| `f12-fig2-mdf-table.jpg` | フロップのベットサイズ別MDF早見テーブル | flop/13 |
| `f06-fig3-draw-completion-table.jpg` | FD/OESD/GS等の主要ドローのターン・リバー・2枚合計完成率早見表 | flop/06 |

### C. 構造図のみ・数値依存少 (再生成不要の可能性)

| 画像 | alt 内容 |
|---|---|
| `f03-fig1-range-propagation.jpg` | レンジ → HandScore 計算 → アクションへ伝搬するフロー図 |
| `f23-fig1-drill-overview.jpg` | ドリル全体像 |

## 巻① preflop の図版

巻① preflop は HandScore を 1 度しか使わないが、**Chen Score 系統の独自 Score 数値が大量にある**:
- p05-fig*: 基本スコア式
- p07-fig*: ポジション別しきい値
- p21-fig*: 中盤ミックスルール
- 他に 50+ 図版

ただし preflop の Score 系統は HandScore とは独立の値スケール（`Open Score = 6+, 3bet Score = 4+`）。**案【大】の影響を直接は受けない**。

ただし「**equity % との関係**」を読者が混同する可能性があり、preflop の表記を新スケール側に合わせるかは設計判断。

## 図版生成方針

### 推奨: 該当画像のみ再生成（差分対応）

`grep` で抽出した数値依存画像（A 群 3 枚 + B 群 2 枚 = 5 枚）のみ AI 再生成。

```
プロンプト生成例 (gemini-3.1-flash-image-preview):

【新 f03-fig2】
"UTGからBBまでの各ポジション（UTG/HJ/CO/BTN/SB/BB）の
フロップ平均 HandScore を equity % で表示する縦棒グラフ。
Y軸: HandScore (equity %, 0-100)。各バーに数値をラベル表示。
新スケールでの代表値:
  UTG: 75% (タイトレンジ)
  HJ:  72%
  CO:  68%
  BTN: 60% (ワイドレンジ)
  SB:  62%
  BB:  55%（コール込み）
```

### 工数

| 作業 | 件数 | 所要時間 |
|---|---:|---|
| 数値依存画像の特定（完了） | 5 | - |
| AI 再生成プロンプト作成 | 5 | 30 分 |
| Gemini API で生成 (gemini-3.1 を使用) | 5 | 15 分 |
| 確認・差し替え | 5 | 30 分 |
| 微調整・再生成 | 2-3 (推定) | 30 分 |
| **合計** | | **2 時間** |

## 結論

- **影響は巻② flop の 5 枚のみ**（巻③〜digest は図版不使用）
- 巻① preflop は独立 Score 系統で影響を受けない
- 工数 **2 時間**で対応可能
- **AI モデル指定**: ユーザーグローバルルールにより
  - ✗ gemini-2.5-flash-image（使用禁止）
  - ✓ gemini-3.1-flash-image-preview または gemini-3-pro-image-preview を使用
