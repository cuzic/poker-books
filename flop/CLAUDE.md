# 『迷わないポーカー② フロップ[基礎]』執筆プロジェクト

## 本書の位置づけ

前作『迷わないポーカー① プリフロップ』の続編。SRP（BTN vs BB、pot=6bb、stack=97bb）フロップを
5 ステップで暗算する判断フローを体系化した初中級者向け書籍。

## コア公式（3本柱）

### 1. ボードスコア B（9ルール）

```
1. モノトーン             → B = 70
2. ペアボード × top ≥ T  → B = 83
3. ペアボード × top < T  → B = 71
4. 2トーン × top A/K     → B = 56
5. 2トーン               → B = 50
6. レインボー × spread≤3 × top≥J → B = 67
7. レインボー × top A/K  → B = 62
8. レインボー × top Q    → B = 58
9. レインボー            → B = 55
```

### 2. ハンドスコア HS

```
HS = role_score + draw_bonus + 2OC_bonus
役スコア: セット85 / 2ペア75 / TPTK65 / オーバーペア60 / etc.
ドローボーナス: FD+30 / OESD+24 / BDFD+6(フロップのみ) / ガットショット+12
2OCボーナス: +24
```

### 3. CBet 判断の 3 ルール

```
T1（HS≥65）: 常時 CBet
T2（HS≥20）: B≥58 なら CBet
T3（HS<20）: B≥62 なら CBet（ブラフ）
```

### CBet サイズ

```
paired_high (B=83): 50%
mono (B=70): 75%
その他: 33%
```

### OOP フォールド閾値

```
vs33%: HS < 15（+2tone+5, -mono5, -paired_high10）
vs75%: HS < 35（同補正）
```

### C 値（ブラフ収益判断）

```
C = α × 50
33%→C=12, 50%→C=17, 75%→C=22, 100%→C=25, 150%→C=30
```

## 章構成（11章）

| ファイル | 章 | 内容 |
|---------|---|------|
| 00-srp-intro.md | 序章 | SRP 標準状況・5ステップフロー概要 |
| 01-board-score.md | 第01章 | ボードスコア B (9ルール) |
| 02-hand-score.md | 第02章 | ハンドスコア HS |
| 03-flop-tier.md | 第03章 | T1/T2/T3 ティアシステム |
| 04-cbet-decision.md | 第04章 | CBet 判断の黄金律 |
| 05-cbet-size.md | 第05章 | CBet サイズ選択 |
| 06-fold-threshold.md | 第06章 | OOP フォールド閾値テーブル |
| 07-c-value.md | 第07章 | C値: どれだけ押すか |
| 08-check-raise.md | 第08章 | チェックレイズ入門 |
| 09-check-check.md | 第09章 | Check-check と弱いゲーム |
| 10-flow-chart.md | 第10章 | フロップ判断フローチャート（本書総まとめ） |

## GTO 整合性

pot10 study (68ボード) で検証済み：
- 平均 CBet: 92.2%（paired_high=97.8%, rainbow_ak=96.3%, 2tone=86.7%）
- OOP fold vs33%: 25.0% = MDF理論値(25%)と完全一致
- OOP fold vs75%: 42.5% ≈ MDF理論値(43%)

## ビルド

```bash
bun run build:flop
```

## 関連ファイル

- `scripts/calc.py`: SSOT 計算式
- `scripts/generate/specs/vol2_*.yaml`: 章仕様
- `scripts/generate/outlines/vol2_*.md`: 自動生成アウトライン
- `knowledges/gto_canonical/REPORT.md`: GTO 検証レポート
