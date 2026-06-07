# Vol4/Vol5 目次草案 (2026-05-12)

## 状態: DRAFT — GTO 調査結果待ち
## 最終確定: pot10 + range_read + river study 完了後

---

## Vol4: 迷わないポーカー④ ターン・リバー[基礎]

**コンセプト:** マルチストリート判断の基礎。ターンカードの意味とバレル決定。
リバーまで見越した SPR 管理。

**想定読者:** Vol2/3 修了者。ターンで何を考えればいいか迷っている中級者。

**GTO データ依存:** range_read 30 ターンシナリオ (完了済み) + pot10 turn シナリオ

---

### 目次

| 章 | タイトル | 核心コンテンツ | 必要 GTO データ |
|---|---------|-------------|--------------|
| 序 | ターンの標準状況 | pot=10bb, stack=92bb (SRP BTN vs BB, 33% CBet call) | — |
| 01 | ターンカード 5 分類 | blank / OC / pair / straight / flush_hit | range_read: 30 scenarios |
| 02 | ターンでのハンドスコア更新 | フロップ HS → ターン HS の変化 | — |
| 03 | バレル判断: T1/T2 は常時 | GTO 78%+ bet rate → T1/T2 always, T3→B≥67 | range_read: ip_bet33_freq |
| 04 | ターンサイズは 33% | GTO 確認済み: size=33% が最適 | range_read: size analysis |
| 05 | ターンカード別レンジ更新 | OC/pair/flush-hit でレンジがどう変わるか | range_read: turn_type 別 |
| 06 | OOP ターン反応 | Check-call/check-fold の閾値 (pot10 turn 結果) | pot10: turn OOP fold |
| 07 | SPR と「コミット」の境界 | SPR < 3 → オールイン志向 | — |
| 08 | リバーを逆算する (intro) | ターンアクションがリバーを決める | range_read: ip_check→river |
| 09 | マルチストリートフロー | フロップ → ターン → リバーの全体像 | — |
| 10 | 実戦例 10 問 | 代表ターンシナリオ | — |
| 付録A | ターンシナリオ 30 参照表 | CBet freq / check freq / OOP call 一覧 | range_read 全 30 件 |
| 付録B | SPR × リバーサイズ ガイド | — | — |

**章数合計:** 10章 + 2付録

---

### 核心式

```
ターン標準状況:
  pot = 10bb (フロップ 6bb × 33% CBet × call → 10bb)
  stack = 92bb (start 100 - open 2 - call 2 - CBet 2 = 92bb... 要確認)

ターン barrel 判断:
  T1 (HS≥65): 常にバレル, size=33%
  T2 (HS≥20): 常にバレル, size=33%
  T3 (HS<20):  B≥67 のみ, size=33%

ターンカード効果 (HS 変化):
  OC_ace (A 来): AK/AQ の HS 大幅上昇, K ハイ TP は下降
  pair (ボードペア): TS の HS は倍増, TP は下降
  straight: OESD/GS の HS 急上昇
  flush_hit: FD の HS 急上昇

α (ターン 33% bet):
  α = 3.3 / (10 + 3.3) = 24.8% ≈ 25%
  MDF = 75%, V:B = 3:1

SPR 分類:
  SPR ≥ 6: large (3 streets)
  SPR 3-5: medium (2 streets)
  SPR < 3: small (commit soon)
```

---

## Vol5: 迷わないポーカー⑤ ターン・リバー[応用]

**コンセプト:** リバーの本質 (エクイティの終点) と高度なマルチストリート判断。
ブラフ構築・バリュー・ディフェンスの体系化。

**想定読者:** Vol4 修了者。リバーで判断に迷う中上級者。バランスを意識したい人。

**GTO データ依存:** river study (12 シナリオ) + range_read 拡張

---

### 目次

| 章 | タイトル | 核心コンテンツ | 必要 GTO データ |
|---|---------|-------------|--------------|
| 序 | リバーの特殊性 | エクイティ実現の終点。引き分けなし | — |
| 01 | VMB バケット | V≥70, M≥35, B<35 の意味 | river study |
| 02 | リバーバリューベット | T1 常時、T2→IP のみ。サイズ 50% or 100% | river study: ip_bet_pct |
| 03 | リバーブラフ | 最適頻度 = α / (1 - α). ハンド選択原則 | river study: V:B ratio |
| 04 | リバーディフェンス | MDF = 1 - α. OOP fold 閾値 | river study: oop_fold |
| 05 | ショーダウンバリュー | check-behind でバリューを取る判断 | river study: ip_check_pct |
| 06 | ターンオーバーベット入門 | 150% bet の条件と効果 | — |
| 07 | リバーオーバーベット | 100%+での B≥83 ルール | — |
| 08 | Check-raise on river | OOP リバー CR の使い方 | — |
| 09 | マルチストリート総合 | フロップ → ターン → リバーのライン設計 | range_read + river |
| 10 | 実戦例 10 問 (応用) | 複雑なシナリオ | — |
| 付録A | リバーシナリオ参照表 | 12 シナリオの値/ブラフ/ディフェンス一覧 | river study 全 12 件 |
| 付録B | リバーサイズ × V:B 比テーブル | — | — |

**章数合計:** 10章 + 2付録

---

### 核心式

```
VMB (Value/Middle/Bluff):
  V ≥ 70: ベット推奨 (価値ある手)
  M ≥ 35: 状況次第 (IP→ベット, OOP→チェック)
  B < 35:  チェック (ブラフ候補 or SDV)

リバーバリュー:
  T1(HS≥70) = V → 常にベット
  T2(HS≥35) = M → IP: ベット, OOP: チェック
  T3(HS<35)  = B → チェック (SDV または ブラフとして使用)

リバーブラフ頻度:
  bluff_freq = α / (1 - α)
  α=25% → bluff=33% of bets
  α=33% → bluff=50% of bets (1:1)
  α=50% → bluff=100% (2:1 V:B)

OOP ディフェンス:
  MDF = 1 - α
  vs50% → MDF=67%  vs100% → MDF=50%

リバーサイズ選択:
  B ≥ 83 (paired_high) → 100% pot
  その他 → 50% pot
```

---

## GTO 調査進捗 (Vol4/5 に必要なもの)

| データ | 調査状況 | 用途 |
|-------|---------|-----|
| range_read 30 ターンシナリオ | ✅ 完了 | Vol4 ch01-08 |
| pot10 ターン 30 シナリオ | 🔄 実行中 | Vol4 ch06 (OOP fold on turn) |
| river study 12 シナリオ | 🔄 実行中 (0/12 完了) | Vol5 ch01-05 |
| ターン OOP probe/donk | ❌ 未調査 (Vol4 ch06 補足) | Vol4 応用部分 |
| リバーオーバーベット分析 | ❌ 未調査 | Vol5 ch06-07 |

## 現行 vol4/vol5 との比較

現行 vol4 (volume4/): 20章 → 新 Vol4: 10章 + 2付録
- ch08 barrel-score, ch09 alpha-formula → 統合して ch03/04 に
- ch10 defender-score-turn → 新 ch06 に
- ch11 defender-score-river → Vol5 ch04 に
- ch07 blocker-basics → 新 Vol4 ch08 的な内容へ

現行 vol5 (volume5/): 20章 → 新 Vol5: 10章 + 2付録
- ch01 three-axes → Vol5 序章に
- ch02 backward-induction → Vol5 ch09 に
- ch06-07 overbet → Vol5 ch06-07 として維持
- ch08 check-raise → Vol5 ch08 として維持
