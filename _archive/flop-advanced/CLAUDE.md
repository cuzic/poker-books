# 『迷わないポーカー③ フロップ[応用]』執筆プロジェクト

## 本書の位置づけ

巻②（フロップ基礎）の続編。T1/T2/T3 と B/HS を習得した読者がレンジ優位の視点で
フロップ判断を精密化するための応用書。NL100〜NL400 程度のプレイヤー向け。

## 本巻のテーマ

1. **レンジ優位**：ナッツアドバンテージ + エクイティアドバンテージで CBet 判断を精緻化
2. **後手の攻防**：チェックレイズ・ドンクベット・OOP コーリングレンジの定量化
3. **特殊状況**：マルチウェイ・3-bet ポット・4-bet ポット・SB vs BB

## 核心式

### テクスチャ別 CBet%（GTO実測, 68ボード）

```
paired_high(B=83): 97.8%
rainbow_ak(B=62):  96.3%
mono(B=70):        95.4%
paired_low(B=71):  93.1%
2tone_ak(B=56):    91.1%
rainbow(B=55):     88.2%
2tone(B=50):       86.7%
```

### CR 判断（GTO実測 — 15ボード TexasSolver, 2026-05-13）

```
バリュー CR: HS ≥ 65 かつ SPR ≥ 6
ブラフ CR: HS 30-50 + ナッツドロー + SPR ≥ 6
CR サイズ: 3× IP bet
CR 頻度（GTO実測）: ドライ11-17% / ウェット2トーン14-18% / コネクテッド19-26% / ペア板mid28%
```

### 3-bet ポット（SPR≈5）

CBet: 50-75% / T3 ブラフは B≥55 程度に緩和

### 4-bet ポット（SPR≈2）

SPR<3 → CR閾値=75 / T1 常時 75% / コミット前提

## 章構成（16章）

| ファイル | 章 | 内容 |
|---------|---|------|
| 00-range-intro.md | 第00章 | レンジで考える — 入り口 |
| 01-range-advantage.md | 第01章 | フロップでのレンジ優位 |
| 02-cbet-by-category.md | 第02章 | ハンドカテゴリ別 CBet 分析 |
| 03-texture-accuracy.md | 第03章 | ボードテクスチャ × CBet 精度 |
| 04-check-raise-detail.md | 第04章 | チェックレイズ詳細 |
| 05-check-raise-range.md | 第05章 | チェックレイズレンジ構築 |
| 06-donk-bet.md | 第06章 | ドンクベット |
| 07-oop-calling.md | 第07章 | OOP コーリングレンジ |
| 08-size-tell.md | 第08章 | サイズ・テル |
| 09-multistreet-flop.md | 第09章 | マルチストリート展望 |
| 10-bluff-selection.md | 第10章 | ブラフ選択原則 |
| 11-multiway.md | 第11章 | マルチウェイのフロップ戦略 |
| 12-3bet-pot.md | 第12章 | 3-bet ポットのフロップ戦略 |
| 13-opponent-adjust.md | 第13章 | 相手タイプ別エクスプロイト |
| 14-sb-vs-bb.md | 第14章 | SB vs BB |
| 15-4bet-pot.md | 第15章 | 4-bet ポットのフロップ戦略 |

第04-05章: 15 ボード GTO 実測値（TexasSolver）で更新済み（2026-05-13）。第06章ドンクベットは Vol4 で詳細扱い。

## ビルド

```bash
bun run build:flop-advanced
```

## 関連ファイル

- `scripts/calc.py`: SSOT 計算式
- `scripts/generate/specs/vol3_*.yaml`: 章仕様
- `scripts/generate/outlines/vol3_*.md`: 自動生成アウトライン
- `knowledges/gto_canonical/REPORT.md`: GTO 検証レポート
