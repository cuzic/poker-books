# 『迷わないポーカー Vol2 — ポストフロップ完全版』(MATCHA Framework 編) 目次

## 本書の位置づけ

- **シリーズ**: 『迷わないポーカー』MATCHA シリーズの Vol2
- **MATCHA acronym** (シリーズ共通): Math Algorithm for Tier-Categorized Hold'em Action
- **対象**: Cash 100bb と MTT chipEV (25/50/100/200bb) のポストフロップ
- **手法**: **MATCHA Framework** — 5 つの判定軸 + TEA グリッド + 3 つのモード + 3 つの補正
- **精度**: GTO Wizard 実測 293K rows で huge_loss 11 専用公式比 -62%
- **対象外**: ICM/PKO postflop (将来 Vol2.5 で対応)
- **シリーズ姉妹巻**: Vol1 (MATCHA Formula、プリフロップ) / Vol3 (MATCHA Exploits、相手タイプ別)
- **用語集**: https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b

## 暗記コスト目標

| 項目 | 数 |
|------|---:|
| Layer 1: 5 つの判定軸 | 5 |
| Layer 2: TEA グリッド (Tier × Edge = Action) | 1 (9 主要 cell) |
| Layer 3: 3 つのモード | 3 |
| Layer 4: 3 つの補正 + 5 例外 | 8 |
| 境界ハンド | ~30 |
| **計** | **~50 項目** |

vs 旧 11 専用公式の ~165 分岐 + 50 境界 = 215 項目 → **暗記コスト -77%**

---

## 序章 (ch00)

### 00. ポストフロップが難しい本当の理由
- mv (made-value) と equity の違い
- 「自分の役は決まっても相手のレンジは確率分布」(雑談で発見した命題)
- MATCHA Framework の全体像 (5 つの判定軸 + 3 つのモード + 3 つの補正)
- 暗算 philosophy: 式で 9 割、境界ハンドは暗記

---

## 第1部: 5 つの判定軸 (ch01-05)

### 01. レンジ分布 — 相手のレンジ構造を 3 段階で読む
- **2極化型** (dynamic, dynamic_2tone, monotone): 相手にドロー/ナッツ完成あり
- **混在型** (dry_high, low_dry, paired): 相手大半 air、たまに set+
- **密集型**: その他
- なぜ「相手レンジ構造」を board family で代理できるか (probe data 引用)
- **暗記項目**: 6 ボードファミリー → 3 カテゴリの振り分け

### 02. ハンドストレングス — 自分のハンドを 6 階層で位置づける
- **ナッツメイド / ストロング / ツーペア / トップペア以上 / ミドルペア / エア**
- mv_cat の生分類 (top_pair, set, etc.) を 6 階層に圧縮する利点
- **暗記項目**: mv_cat 17 種類 → 6 階層の対応

### 03. ベットサイジング — 相手のベットサイズを 4 段階で読む
- **スモールベット** (33% pot) / **ミディアムベット** (50-100%) / **オーバーベット** (130%+) / **オールイン**
- なぜ 75% と 100% を ミディアムベット にまとめてよいか
- **暗記項目**: 4 カテゴリの閾値

### 04. SPR — ポット commitment 度を 1 軸で表す
- **オールインSPR** (<1) / **ローSPR** (1-3) / **ミディアムSPR** (3-7) / **ディープSPR** (>7)
- ポット種別 × ストリート × スタック深度の 27 組合せを 4 カテゴリに圧縮する魔法
- 各カテゴリの defense 原則
- **暗記項目**: 4 カテゴリの戦略原則

### 05. エクイティバケット — 「実効的な強さ」を 4 段階で補正
- 絶対強さ (mv) × 相対強さ (vs opp range) の融合
- **モンスターハンド / 良ハンド / 弱ハンド / ブラフハンド**
- 例: set × 弱ハンド → ストレート板の set / ace_high × モンスターハンド → ナッツブロッカー
- エクイティバケットの自分での推定法 (実戦応用)
- **暗記項目**: ハンドストレングス × エクイティバケット 結合表 (24 cell、規則的)

---

## 第2部: TEA グリッド (ch06)

### 06. 形勢 — Tier × Edge = Action グリッド
- 5 つの判定軸の組合せ → 形勢 (優勢 / 五分五分 / 劣勢) の導出
- **優勢**: 自分のハンドが相手レンジより前 (hero has the edge)
- **五分五分**: 互角、ベットサイズで判断 (no edge)
- **劣勢**: 相手レンジが強い、ブラフキャッチ条件のみコール (villain has the edge)
- 略称 **TEA グリッド** の使い方
- **暗記項目**: TEA グリッド (9 主要 cell)

---

## 第3部: 3 つのモード (ch07-09)

### 07. バリューモード — 優勢時の攻める判断
- リバー → コール / 非リバー × 非2極化型 → レイズ / 2極化型 → slowdown コール
- モノトーン での例外
- **暗記項目**: 1 ルール + 2 例外

### 08. ショーダウンモード — 五分五分時の判断
- オールインSPR → コール (committed)
- 強ドロー → コール
- オーバーベット × 無ドロー → 慎重 FOLD
- 既定 コール
- **暗記項目**: 1 ルール + 4 条件

### 09. ブラフキャッチモード — 劣勢時の引く判断
- 強ドロー → コール
- スモールベット × 混在型 × ブロッカー → コール
- 既定 FOLD
- ace_high ナッツブロッカーの威力 (Section A 実測 +27pp)
- **暗記項目**: 1 ルール + 3 条件

---

## 第4部: ポット種別補正 (ch10-12)

### 10. SRP — 標準 100bb base
- 3 モードそのまま適用
- BTN open vs BB call が基準

### 11. 3BP — 3-bet pot の補正
- SPR 自動切替 (ミディアムSPR/ローSPR/オールインSPR)
- リバー bucket fallback の強化
- **暗記項目**: 2 例外

### 12. 4BP — 4-bet pot の独特の世界
- 相手レンジ tight (QQ+/AK)、相手弱ハンド 40-60%
- オールインSPR (<1.5) → "fold は損"
- ミドルペア → コール always (4BP wide defense)
- モノトーン での slowdown
- ボード固有の例外 (dry_A94 vs dry_K72)
- **暗記項目**: 4 例外

---

## 第5部: 状況補正 (ch13-15)

### 13. チェックレイズ補正 (flop / turn)
- 相手 value-heavy (opp_strong 46%)
- 形勢を 1 段階下げ
- turn donk vs turn CR の真逆方針 (phase5 発見)
- **暗記項目**: shift table + 1 例外

### 14. ドンクベット補正 (flop / turn / river)
- 相手 air-heavy (opp_weak 54-61%)
- 形勢 劣勢→五分五分 のみ上げ + レイズ→コール変換
- river ドンクベットは mid-heavy (注意)
- **暗記項目**: shift table + 1 例外

### 15. オープナー補正 (CO/HJ open river)
- river のみ effective (turn では opener 差なし、phase5 発見)
- CO/HJ open → 形勢を 1 段階下げ (相手 value-heavier than BTN)
- **暗記項目**: river-only shift

---

## 第6部: スタック深度補正 (ch16-17)

### 16. 短スタック (≤25bb) — shove/fold 軸
- SPR 自動下げ (ディープSPR→ミディアムSPR, ミディアムSPR→ローSPR, ローSPR→オールインSPR)
- pair + → コール (committed)
- 短スタック特有の境界 hand
- **暗記項目**: SPR shift + 2 例外

### 17. 深スタック (200bb+) — implied odds の世界
- SPR 自動上げ
- ミドルペア × flop/turn → コール (implied odds)
- 深スタックでの slowplay 抑制 (Section A 発見、ディープSPR で aggression)
- **暗記項目**: SPR shift + 2 例外

---

## 第7部: 実戦 (ch18-20)

### 18. 境界ハンド集
- 5 つの判定軸の境界 hand 一覧 (30 ハンド以内)
- 各境界での GTO 最善手 (フローでカバーできない 20%)

### 19. ドリル (20 問)
- 5 軸の判定 + TEA グリッド導出 + モード適用の実践
- 解説で MATCHA の各層を可視化

### 20. チートシート
- 1 枚で全体像 (5 軸の判定 → TEA グリッド → 3 モード)
- A4 1 枚で印刷可能

---

## 付録

### A. MATCHA Framework 完全公式表
- 全 cell (5 軸の組合せ) と推奨 action

### B. audit 結果
- MATCHA vs 11 専用公式の per-scenario huge_loss 比較
- データソース: `scripts/three_class_model/NEW_FORMULA_AUDIT.md` 等

### C. GTO Wizard データ取得方法
- 再現性確保用、API 利用と probe 設計の解説
- 自前 audit で読者が MATCHA v2 を作る道筋

---

## 想定ページ数

| Part | 章数 | 想定ページ |
|------|----:|----------:|
| 序章 | 1 | 5 |
| 第1部 (判定軸) | 5 | 25 |
| 第2部 (TEA グリッド) | 1 | 8 |
| 第3部 (モード) | 3 | 12 |
| 第4部 (ポット種別) | 3 | 18 |
| 第5部 (状況補正) | 3 | 12 |
| 第6部 (スタック深度) | 2 | 8 |
| 第7部 (実戦) | 3 | 15 |
| 付録 | 3 | 12 |
| **計** | **24** | **~115p** |

vs 旧 Vol2 (180p) + 旧 Vol3 (200p) = 380p → **-70%**

## 関連リソース

- 公式実装: `scripts/three_class_model/udg_v2.py` (ファイル名 legacy、内容は MATCHA SSOT)
- audit script: `scripts/three_class_model/audit_new_formulas.py`
- データ生成 spec: `scripts/generate/specs/vol2_ch{NN}_*.yaml` (後日作成)
- generator: `scripts/generate/book_generator.py` (vol2 章用に流用)
- **用語集 HTML**: https://gistpreview.github.io/?dbb75f11330aff4346de987c4f4fb91b
