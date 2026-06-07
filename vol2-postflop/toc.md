# 『迷わないポーカー Vol2 — ポストフロップ完全版』目次

## 本書の位置づけ

- **対象**: Cash 100bb と MTT chipEV (25/50/100/200bb) のポストフロップ
- **手法**: UDG (Universal Defense Grid) — 5 tier + 3 universal rule + 3 modifier
- **精度**: GTO Wizard 実測 293K rows で huge_loss 11 専用公式比 -62%
- **対象外**: ICM/PKO postflop (将来 Vol3.5 で対応)

## 暗記コスト目標

| 項目 | 数 |
|------|---:|
| Layer 1: tier 関数 | 5 |
| Layer 2: matchup 表 | 1 (9 cell) |
| Layer 3: universal rule | 3 |
| Layer 4: modifier | 3 + 5 例外 |
| 境界ハンド | ~30 |
| **計** | **~50 項目** |

vs 旧 11 専用公式の ~165 分岐 + 50 境界 = 215 項目 → **暗記コスト -77%**

---

## 序章 (ch00)

### 00. ポストフロップが難しい本当の理由
- mv (made-value) と equity の違い
- 「自分の役は決まっても相手の range は確率分布」(雑談で発見した命題)
- UDG framework の全体像 (5 + 3 + 3)
- 暗算 philosophy: 式で 9 割、境界ハンドは暗記

---

## 第1部: 5 tier 概念 (ch01-05)

### 01. board_polar_tier — 相手 range の構造を 3 段階で読む
- POLAR (dynamic, dynamic_2tone, monotone): 相手に draw/nut 完成あり
- MERGED (dry_high, low_dry, paired): 相手大半 air、たまに set+
- MID: その他
- なぜ「相手 range 構造」を board family で代理できるか (probe data 引用)
- **暗記項目**: 6 board family → 3 tier の振り分け

### 02. hand_strength_tier — 自分のハンドを 6 階層で位置づける
- NUT_MADE / STRONG / TWO_PAIR / PAIR / MID_PAIR / AIR
- mv_cat の生分類 (top_pair, set, etc.) を 6 階層に圧縮する利点
- **暗記項目**: mv_cat 17 種類 → 6 tier の対応

### 03. bet_size_tier — 相手のベットサイズを 4 段階で読む
- SMALL (33% pot) / MED (50-100%) / BIG (130%+) / ALLIN
- なぜ 75% と 100% を MED にまとめてよいか
- **暗記項目**: 4 tier の閾値

### 04. SPR tier — ポット commitment 度を 1 軸で表す
- SHALLOW (<1) / LOW (1-3) / MID (3-7) / HIGH (>7)
- pot type × street × depth の 27 組合せを 4 tier に圧縮する魔法
- 各 tier の defense 原則
- **暗記項目**: 4 tier の戦略原則

### 05. equity_aware_tier — 「実効的な強さ」を equity bucket で補正
- 絶対強さ (mv) × 相対強さ (vs opp range) の融合
- 例: set × weak_hands → MID (str8 board 上の set)、ace_high × best_hands → HIGH (nut blocker)
- equity_bucket の自分での推定法 (実戦応用)
- **暗記項目**: hand_tier × equity_bucket 結合表 (24 cell、規則的)

---

## 第2部: matchup tier (ch06)

### 06. AHEAD / TIE / BEHIND — 3 択で判断を確定する
- 5 tier の組合せ → matchup 3 階層への導出表
- AHEAD: 自分が相手 range より前
- TIE: 互角、bet_size で fold/call 判断
- BEHIND: 相手 range が強い、bluff catch 条件のみ call
- **暗記項目**: matchup 表 (9 主要 cell)

---

## 第3部: 3 universal rule (ch07-09)

### 07. AHEAD rule — 攻める判断
- river → CALL / 非river × non-POLAR → RAISE / POLAR → slowdown CALL
- monotone での例外
- **暗記項目**: 1 ルール + 2 例外

### 08. TIE rule — 普通の判断
- SHALLOW SPR → CALL (committed)
- strong_draw → CALL
- BIG bet × no draw → cautious FOLD
- 既定 CALL
- **暗記項目**: 1 ルール + 4 条件

### 09. BEHIND rule — 引く判断 (bluff catch 条件)
- strong_draw → CALL
- SMALL bet × MERGED × blocker → CALL
- 既定 FOLD
- ace_high blocker の威力 (Section A 実測 +27pp)
- **暗記項目**: 1 ルール + 3 条件

---

## 第4部: pot type modifier (ch10-12)

### 10. SRP modifier — 標準 100bb base
- universal rule そのまま
- BTN open vs BB call が基準

### 11. 3BP modifier — 3-bet pot の補正
- SPR tier 自動切替 (MID/LOW/SHALLOW)
- river bucket fallback の強化
- **暗記項目**: 2 例外

### 12. 4BP modifier — 4-bet pot の独特の世界
- opp range tight (QQ+/AK)、opp_weak 40-60%
- SPR<1.5 → "fold は損"
- MID_PAIR → CALL always (4BP wide defense)
- monotone での slowdown
- board-specific 例外 (dry_A94 vs dry_K72)
- **暗記項目**: 4 例外

---

## 第5部: action context modifier (ch13-15)

### 13. CR defense (flop / turn)
- opp は value-heavy (opp_strong 46%)
- matchup を 1 段階下げ
- turn donk vs turn CR の真逆方針 (phase5 発見)
- **暗記項目**: shift table + 1 例外

### 14. donk defense (flop / turn / river)
- opp は air-heavy (opp_weak 54-61%)
- matchup BEHIND→TIE のみ上げ + RAISE→CALL 変換
- river donk は mid-heavy (注意)
- **暗記項目**: shift table + 1 例外

### 15. opener position modifier (CO/HJ open river)
- river のみ effective (turn では opener 差なし、phase5 発見)
- CO/HJ open → matchup 1 段階下げ (opp value-heavier than BTN)
- **暗記項目**: river-only shift

---

## 第6部: depth modifier (ch16-17)

### 16. 短スタック (≤25bb) — shove/fold 軸
- SPR tier 自動下げ (HIGH→MID, MID→LOW, LOW→SHALLOW)
- pair + → CALL (committed)
- 短スタック特有の境界 hand
- **暗記項目**: tier shift + 2 例外

### 17. 深スタック (200bb+) — implied odds の世界
- SPR tier 自動上げ
- MID_PAIR × flop/turn → CALL (implied odds)
- 深スタックでの slowplay 抑制 (Section A 発見、HIGH SPR で aggression)
- **暗記項目**: tier shift + 2 例外

---

## 第7部: 実戦 (ch18-20)

### 18. 境界ハンド集
- 5 tier の境界 hand 一覧 (30 ハンド以内)
- 各境界での GTO 最善手 (フローでカバーできない 20%)

### 19. ドリル (20 問)
- 5 tier の判定 + matchup 導出 + rule 適用の実践
- 解説で UDG の各層を可視化

### 20. チートシート
- 1 枚で全体像 (5 tier の判定 → matchup 表 → 3 rule)
- A4 1 枚で印刷可能

---

## 付録

### A. UDG 完全公式表
- 全 cell (5 tier 組合せ) と推奨 action

### B. audit 結果
- UDG v2 vs 11 専用公式の per-scenario huge_loss 比較
- データソース: `scripts/three_class_model/NEW_FORMULA_AUDIT.md` 等

### C. GTO Wizard データ取得方法
- 再現性確保用、API 利用と probe 設計の解説
- 自前 audit で読者が UDG v3 を作る道筋

---

## 想定ページ数

| Part | 章数 | 想定ページ |
|------|----:|----------:|
| 序章 | 1 | 5 |
| 第1部 (tier) | 5 | 25 |
| 第2部 (matchup) | 1 | 8 |
| 第3部 (rule) | 3 | 12 |
| 第4部 (pot type) | 3 | 18 |
| 第5部 (context) | 3 | 12 |
| 第6部 (depth) | 2 | 8 |
| 第7部 (実戦) | 3 | 15 |
| 付録 | 3 | 12 |
| **計** | **24** | **~115p** |

vs 旧 Vol2 (180p) + 旧 Vol3 (200p) = 380p → **-70%**

## 関連リソース

- 公式実装: `scripts/three_class_model/udg_v2.py`
- audit script: `scripts/three_class_model/audit_new_formulas.py`
- データ生成 spec: `scripts/generate/specs/vol2_ch{NN}_*.yaml` (後日作成)
- generator: `scripts/generate/book_generator.py` (vol2 章用に流用)
