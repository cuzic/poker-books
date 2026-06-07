# 『エクスプロイト・ポーカー — 相手タイプ別に崩す技術』(Vol3 MATCHA Exploits 編) 執筆プロジェクト

## プロジェクト概要

『迷わないポーカー』MATCHA シリーズ Vol3 (**MATCHA Exploits 編**)。Vol1 (MATCHA Formula、プリフロップ) + Vol2 (MATCHA Framework、ポストフロップ) の判定軸・閾値をベースに、**相手プレイタイプ別に MATCHA の判定軸を歪めるエクスプロイト戦略**を体系化した書籍。

## MATCHA Framework との接続

エクスプロイトとは、**相手の 5 つの逸脱軸を読み、MATCHA の判定軸を歪めて形勢を変える技術**である。

| 巻 | サブブランド | 役割 |
|---|---|---|
| Vol1 (プリフロップ) | MATCHA Formula | Score_BB v7 (ポジションティア + コンテキストキャリブレーション) |
| Vol2 (ポストフロップ) | MATCHA Framework | 5 判定軸 × TEA グリッド × 3 モード × 3 補正 |
| **Vol3 (本書)** | **MATCHA Exploits** | **MATCHA の各判定軸を、相手タイプに応じて歪める方法** |

MATCHA acronym (シリーズ共通): **M**ath **A**lgorithm for **T**ier-**C**ategorized **H**old'em **A**ction

## 5 つの逸脱軸 (GTO Wizard "Five Imbalances of Exploitative Poker")

相手が GTO から逸脱する 5 軸:

| 軸 | 英語 | 観察対象 |
|---|---|---|
| ① レンジ逸脱 | Range imbalance | 参加レンジが broad / narrow |
| ② 頻度逸脱 | Frequency imbalance | call / fold / raise の頻度 |
| ③ サイズ逸脱 | Sizing imbalance | bet サイズの偏り |
| ④ ポジション逸脱 | Position imbalance | IP / OOP の使い方の偏り |
| ⑤ 判断逸脱 | Decision imbalance | 状況判断のずれ |

## プレイタイプ 5 分類

5 つの逸脱軸の組合せから判定:

| タイプ | 主な逸脱 | 概要 |
|---|---|---|
| ニット | レンジ狭・頻度低 | タイト&受動 |
| TAG (Tight Aggressive) | (バランス取り) | タイト&攻撃 |
| LAG (Loose Aggressive) | 頻度高・サイズ多様 | ルース&攻撃 |
| コーリングステーション | 頻度高 (call偏重) | ルース&受動 |
| マニアック | 頻度最大・サイズ最大 | 極端ルース&過剰攻撃 |

## エクスプロイトの定式化 — MATCHA 判定軸の歪め方

| 相手タイプ | レンジ分布の見立て | エクイティバケットの見立て | 形勢の歪み方 |
|---|---|---|---|
| ニット | 実質 **2極化型** 寄り | hero のモンスター/良ハンド比率↓ | 優勢↓、ブラフキャッチ機会↓ |
| コーリングステーション | 実質 **密集型** 寄り | hero の良ハンド比率↑ | 優勢で薄バリュー↑ |
| LAG | 実質 **2極化型** + 頻度過剰 | hero の弱ハンドも実質 良ハンド | 劣勢→五分五分の格上げ、ブラフキャッチ↑ |
| マニアック | **2極化型** 極端 (ナッツ or ブラフ) | hero のミドルペアも実質 良ハンド | 劣勢→五分五分の大幅格上げ |
| TAG | (GTO 近似) | (補正なし) | 微小な調整のみ |

## Directory Structure

```
vol3-tell/
├── chapters/               # 本文 (00-introduction〜21-*.md)
├── research.md             # 調査資料 (12 セクション)
├── toc.md                  # 目次・執筆ガイド (MATCHA 用語で再構成中)
├── plan.md                 # 書籍企画書
├── book.json               # 書誌メタデータ
└── CLAUDE.md               # このファイル
```

## 執筆方針

### 文体
- ですます調で統一
- 1 文 150 字以内、読点 3 個以内
- 専門用語は初出時に簡易定義を併記

### 章の標準構造（第2部タイプ別章）

1. **タイプの本質**（太字でリード）
2. **見分け方** — 5 つの逸脱軸のどれが顕著か
3. **プリフロップ：Score 閾値をどう歪めるか**（T_open / T_3bet の変化表）
4. **ポストフロップ：MATCHA の判定軸をどう歪めるか**
   - レンジ分布の見立て補正
   - エクイティバケットの見立て補正
   - 形勢 (優勢/五分五分/劣勢) の歪み方
   - モード (バリュー/ショーダウン/ブラフキャッチ) の適用変更
5. **ターン・リバー固有の調整**
6. **⚠️ やりすぎ注意**

### 品質基準

- 閾値変化は必ず表形式で示す（通常値 → 歪め後の値 → 変化量）
- 具体的な手（例：A♠J♦）とボード（例：J♣8♦5♠）を使う
- MATCHA の判定軸を具体的な数値・カテゴリで示す
- 各章末に【GTOとのズレ】コラムは不要（Vol2 で扱う）

## 用語ポリシー

- **本文表記**: 日本語 (Vol2 用語集に準拠) https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b
- **MATCHA 用語**: レンジ分布 / ハンドストレングス / ベットサイジング / SPR / エクイティバケット / 形勢 / 3 モード / 3 補正 を直接使用
- **逸脱軸**: 「5 つの逸脱軸」「レンジ逸脱」「頻度逸脱」「サイズ逸脱」「ポジション逸脱」「判断逸脱」(全部和訳)
- **プレイタイプ**: ニット / TAG / LAG / コーリングステーション / マニアック (「キャリングステーション」は誤記)

## 核心式 (Vol1 + Vol2 から継承)

### プリフロップスコア (Vol1)

```
Score = H + L
      + ペアボーナス   +10  （ペアのみ）
      + スーテッドボーナス +3
      + コネクター差1  +1   / 差2-3 +0.5
      + ブロッカー: A=+3 / K=+2 / AK 両方=+4
      − ペナルティ: 差4以上−1 (A 含むと免除) / 両カード 9 未満 −1
```

### T_open 閾値（通常値、Vol1）

| ポジション | 通常値 |
|----------|--------|
| UTG | 24 |
| HJ | 22 |
| CO | 20 |
| BTN | 18 |
| SB | 22 |

### MATCHA Framework (Vol2) の継承

ポストフロップの判定軸・モード・補正は Vol2 を SSOT として参照。
本書では各軸の **歪め方** のみ記述。

## ペルソナ

- 🔰 真田（A）: ライブ半年。読みを行動に繋げたい
- 💻 林（B）: オンライン中級者。GTO理論とライブを接続したい
- 🎯 岡田（C）: ライブ8年。感覚をシステム化したいベテラン

## 関連リソース

- Vol2 用語集 (HTML): https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b
- Vol2 CLAUDE.md: `vol2-postflop/CLAUDE.md` (MATCHA Framework 詳細)
- Vol1 CLAUDE.md: `vol1-preflop/` (Score_BB v7 詳細)
- GTO Wizard "Five Imbalances": https://blog.gtowizard.com/the-five-imbalances-of-exploitative-poker/

## 次のステップ

- 各章の chapters/*.md は旧用語 (HS/B/C/T1/T2/T3 系) で記述済 → MATCHA 用語で再執筆が必要
- 章タイトル・toc.md は本書 update 済 (MATCHA 用語)
- generator 経由での再生成を検討
