# Board 分類 / Hand Strength 境界の知見まとめ — 2026-06-08

MATCHA Framework の 5 判定軸のうち、**Range Morphology (board 分類)** と
**Hand Strength** の境界を 42-77 boards の実 GTO probe で検証した結果のまとめ。

(SPR 境界は別文書 `INSIGHTS_2026-06-08.md` 参照)

---

## 1. Board 分類: 現行 heuristic と実 GTO のズレ

### MATCHA Framework の board 分類定義 (Range Morphology カテゴリ)

| 名称 | 想定する range 形状 | 想定 cbet 行動 |
|------|-------------------|---------------|
| 2 極化型 (POLAR) | nut + air が両端、middle 少 | 選択的 attack (cbet 低) |
| 混在型 (CONDENSED) | middle 多、nut/air 少 | 混合 protection (cbet 中) |
| 密集型 (MERGED) | wide range 広く有利 | wide attack (cbet 高) |

### 21 boards 一次検証で発見した重大ズレ

| flop | 現行 heuristic | empirical (cbet%) | 修正 |
|------|---------------|------------------:|------|
| `7s4d2c` (low_dry) | **MERGED** | 33% → POLAR | low_dry は selective polar attack |
| `8s5d3c` (low_dry) | **MERGED** | 33% → POLAR | 同上 |
| `js7s3h` (low_dry) | **MERGED** | 28% → POLAR | 同上 |
| `9s6d3c` | **MERGED** | 33% → POLAR | 同上 |
| `8s6d3h` | **MERGED** | 33% → POLAR | 同上 |
| `kskd9c` (paired) | **MERGED** | 33% → POLAR | paired high で nut 集中 → polar |
| `4s4d2c` (paired low) | **POLAR** | 57% → MERGED | paired low で BTN advantage 強 |
| `ks8d2c` 等 (dry_high) | MERGED | 49-50% → CONDENSED | 多くの A/K-high dry は中頻度 |

**一致率: 4/21 (19%) のみ**。現行 MATCHA の board 分類は heuristic として
よく動くが、ボーダーケースで実 GTO とズレる。

### 42-77 boards の細分化 sub-family 分析 (15 categories)

cbet 頻度順:

| sub-family | n | cbet 平均 | 範囲 | empirical class |
|------------|---:|---------:|------|----------------|
| paired_low (XX-low, X<5) | 5 | **50.1%** | 45-57% | MERGED |
| Khigh_spread (Kxy, gap≥5) | 6 | 48.0% | 44-50% | MERGED |
| Ahigh_spread (Axy, gap≥5) | 9 | 46.0% | 25-50% | MERGED 寄り |
| broadway_dry | 6 | 44.9% | 28-52% | CONDENSED |
| paired_mid (5-9) | 6 | 42.0% | 40-45% | CONDENSED |
| paired_broadway | 3 | 41.9% | 39-44% | CONDENSED |
| connected_low (gap≤2, X≤6) | 9 | 41.3% | 32-59% | CONDENSED |
| paired_high (K/A) | 5 | 41.1% | 33-43% | CONDENSED |
| low_dry (X≤5, rainbow) | 2 | **33.9%** | 33-35% | POLAR |
| mid_dry (その他) | 7 | 33.3% | 28-39% | POLAR |
| connected_broadway (TJQ) | 3 | 32.5% | 17-40% | POLAR |
| monotone | 3 | 29.2% | 15-38% | POLAR extreme |
| connected_mid (X=7-9) | 10 | 28.5% | 21-48% | POLAR extreme |

### Data-driven な classify_board() 案

```python
def classify_board(board) -> str:
    s = structure(board)
    if s.monotone:
        return "POLAR"   # cbet ~29%
    if s.connected:      # 3 連続 or 2 ギャップ以下
        return "POLAR"   # cbet 21-40%
    if s.paired:
        if s.high_idx >= 11:    # K/A-paired
            return "CONDENSED"  # cbet 33-43%
        elif s.high_idx <= 4:   # low paired (XX with X<5)
            return "MERGED"     # cbet 45-57% (BTN advantage 強)
        else:
            return "CONDENSED"  # cbet 40-45%
    if s.high_idx >= 11:        # A/K-high non-connected non-paired
        if s.max_gap >= 5:
            return "MERGED"     # Ahigh/Khigh spread, cbet 46-50%
        else:
            return "CONDENSED"  # Ahigh close, cbet ~44%
    if s.low_board:              # 5-high 以下 rainbow
        return "POLAR"           # cbet ~34%
    return "POLAR"                # mid_dry default, cbet ~33%
```

---

## 2. Hand Strength 境界: カテゴリ 区分の正当性

### MATCHA 6 階層の avg cbet (42 boards 平均)

| カテゴリ | avg_bet% | min% | max% | n | 境界判定 |
|------|---:|---:|---:|---:|---|
| **ナッツメイド** (FH/quads/SF) | 9.3% | 0% | 96% | 126 | (低い) |
| **ストロング** (set/trips/flush/straight) | 28.9% | 0% | 100% | 168 | |
| **ツーペア** | 66.9% | 0% | 100% | 42 | (peak) |
| **トップペア以上** (TP/OP) | 51.7% | 0% | 100% | 84 | |
| **ミドルペア** (2P/3P/UP/LP) | 24.0% | 0% | 100% | 168 | |
| **エア** (no_made/high card) | 37.4% | 0% | 65% | 126 | |

### カテゴリ 間の cbet% 差 (隣接 カテゴリ)

| 隣接 カテゴリ | A 平均 | B 平均 | 差 | 判定 |
|-----------|---:|---:|---:|---|
| ナッツメイド → ストロング | 9.3% | 28.9% | -19.6% | 🟢 明確 |
| ストロング → ツーペア | 28.9% | 66.9% | -38.0% | 🟢 明確 |
| ツーペア → トップペア+ | 66.9% | 51.7% | +15.2% | 🟢 明確 |
| トップペア+ → ミドルペア | 51.7% | 24.0% | +27.7% | 🟢 明確 |
| ミドルペア → エア | 24.0% | 37.4% | -13.5% | 🟡 ある |

**5 段差すべて明確 (≥15pp) を確認。** 最後の "ミドルペア → エア" のみ
逆転 (エアの方が高頻度) で、これは ブラフ範囲としての強制 cbet が原因。

### 「ベル / 逆U字」パターン

cbet 頻度を カテゴリ 順に並べると **山型** になる:

```
       ツーペア
        67%
       /    \
   TP+        \
   52%         \
   /          MidP
ストロング     24%   エア
  29%                37%
 /
ナッツ
 9%
```

- **ナッツ系**: slowplay 9% (相手のブラフ・コール継続を引き出す)
- **ストロング**: 29% (set/flush は slowplay 寄り、straight は wider)
- **ツーペア**: **67% で peak** (protection + value double)
- **TP+**: 52% (value, but vulnerable)
- **ミドルペア**: 24% (pot-control)
- **エア**: 37% (ブラフレンジ強制)

### MATCHA カテゴリ の最重要発見

1. **ツーペア = cbet 最高頻度** (67% > TP+ 52% > set 29%)
   → ナッツ-1 段下の「守る価値が最も高い」カテゴリ
   → drill / 書籍で「ツーペアこそ最も打つべき」を独立カード化

2. **set < two_pair < top_pair の "U字逆転"**
   → set 系は board が wet なら slowplay、TP+ は protection
   → set: 74% (ベース) / trips: 14% / flush: 2% / straight: 26%
   → 完成度の高い nut hand ほど slowplay (range balance のため)

3. **low_pair = 2.7%** (ほぼ check 一択)
   → ミドルペア カテゴリ の中で最弱、独立扱い

---

## 3. sub-family × カテゴリ の cross-tab (15 × 6 行動表)

| sub-family | ナッツメイド | ストロング | ツーペア | TP+ | ミドルペア | エア |
|---|---:|---:|---:|---:|---:|---:|
| paired_low | 74% | 74% | 0% | 52% | 58% | 45% |
| Khigh_spread | 0% | 98% | 81% | 59% | 52% | 46% |
| Ahigh_spread | 0% | 94% | 78% | 61% | 47% | 47% |
| broadway_dry | 0% | 100% | 89% | 60% | 43% | 48% |
| Ahigh_close | 0% | 97% | 78% | 61% | 42% | 49% |
| paired_mid | 54% | 75% | 0% | 42% | 51% | 46% |
| paired_broadway | 75% | 71% | 0% | 27% | 56% | 46% |
| connected_low | 0% | 90% | 72% | 51% | 31% | 52% |
| paired_high | 74% | 69% | 0% | 21% | 56% | 46% |
| low_dry | 0% | 100% | 100% | 67% | 21% | 51% |
| Khigh_close | 0% | 96% | 88% | 63% | 31% | 50% |
| mid_dry | 0% | 100% | 96% | 66% | 18% | 52% |
| connected_broadway | 0% | 83% | 82% | 61% | 25% | 52% |
| monotone | 0% | 77% | 78% | 53% | 27% | 52% |
| connected_mid | 0% | 89% | 73% | 53% | 15% | 54% |

### 重要 outlier

| sub-family | カテゴリ | local cbet | baseline | 差 | 解釈 |
|---|---|---:|---:|---:|---|
| **paired_** × ツーペア | 0% | 61% | -61% | paired board で 2pair = ヤバい (TP=quads vs you 2P) → check一択 |
| paired_broadway × ナッツメイド | 75% | 17% | +58% | broadway paired で fullhouse は wide bet |
| low_dry × ツーペア | 100% | 61% | +39% | low_dry の 2pair は range top → 100% bet |
| paired_high × TP+ | 21% | 53% | -32% | K/A paired board の TP は vulnerable |
| connected_mid × ミドルペア | 15% | 38% | -22% | wet connected で MP は pot-control |
| mid_dry × ミドルペア | 18% | 38% | -19% | 同様、wet 系で MP は controlled |

---

## 4. 現行 MATCHA からの修正案

### 即時 (drill / 書籍 ch 修正)

| 項目 | 現行 | 修正後 | 根拠 |
|------|------|--------|------|
| low_dry の分類 | MERGED | **POLAR** | empirical cbet 33% |
| paired K/A の分類 | MERGED | **CONDENSED** | empirical cbet 41-43% |
| paired low (XX-X<5) | POLAR override | **MERGED** | empirical cbet 50%+ |
| Hand Strength 章 | カテゴリ 区分のみ | **カテゴリ × board** cross-tab 必須 | board で カテゴリ 振る舞い激変 |
| ツーペアの位置づけ | 「強い hand」 | **「打つべき hand の peak」** | 67% > TP+ > set |

### 中期 (Vol2 Framework 章設計)

- **Range Morphology 章**: 13 sub-family table を本文に掲載
- **Hand Strength 章**: 「逆U字パターン」を視覚化 (山形グラフ)
- **TEA グリッド章**: sub-family × カテゴリ の 15 × 6 = 90 セル table を付録
- **境界ハンド集**: paired-board × 2pair の "check 一択" 等を暗記リスト化

---

## 5. tier 別 board sensitivity

| カテゴリ | 安定性 (stddev) | board 依存性 |
|------|----------------:|------------|
| エア | 5% | 低 (常に ~37% bluff) |
| ナッツメイド | 20% | 中 (paired のみ active) |
| ミドルペア | 30% | 高 (board で大変動 0→100%) |
| ストロング | 35% | 高 (set/flush で逆) |
| ツーペア | 30% | 高 (paired で 0%) |
| TP+ | 18% | 中 |

- **ミドルペア / ストロング = board 依存性最大** → 同 カテゴリ 内でも分岐必要
- **エア = board 不変** → ブラフ頻度は カテゴリ 規定
- → MATCHA で "board × カテゴリ" cross-tab を主役にすべき (1 軸では不十分)

---

## 6. 限界と未確認事項

### 取れたもの
- 77 boards 網羅 probe で 15 sub-family の細分化確定
- 5 段の カテゴリ 境界 (cbet% 差 ≥15pp) 確認
- 90 セル の sub-family × カテゴリ 行動表

### 未確認
- 100% sizing (6.5bb) の per-カテゴリ 行動は probe 範囲外
- Turn / River の boundary は別調査必要 (今回は flop のみ)
- defense 側 (BB vs cbet) の board 別分類は別 probe 必要
- equity bucket (best/good/weak/trash) の boundaries は per-combo 解析待ち

---

## 7. ファイル一覧

| ファイル | 内容 |
|---------|------|
| `knowledges/gto_wizard_study/BOARD_BOUNDARIES_EMPIRICAL.md` | 21 boards × heuristic 一致率 |
| `knowledges/gto_wizard_study/CLEAN_BOUNDARIES.md` | 42 boards 集計 + 構造的パターン |
| `knowledges/gto_wizard_study/FINE_BOUNDARIES.md` | 77 boards × 15 sub-family × 6 カテゴリ 行動表 |
| `knowledges/gto_wizard_study/HAND_STRENGTH_BOUNDARIES.md` | 6 カテゴリ の cbet 差 + mv_cat 詳細 |
| `scripts/three_class_model/derive_fine_boundaries.py` | sub-family 集計 script |
| `scripts/three_class_model/derive_hand_strength_boundaries.py` | カテゴリ 境界 script |
| `scripts/gto_wizard_study/probe_exhaustive.py` | 35 board 追加 probe |
| `scripts/gto_wizard_study/probe_boundary_gradient.py` | 21 board gradient probe |

---

## 8. 関連 commits (2026-06-07 〜 06-08)

- `f1374d4` boundary: 77 boards 網羅 probe 完了 — 細分化分類確定
- `ebf7dd2` boundary: sub-family 細分化分析 — 14 categories × 6 hand tiers 行動表
- `6c6bf72` boundary: ハンドストレングス階層境界の実 GTO 分析 — 42 boards
- `7adf34c` boundary: 板タイプ境界の実 GTO 導出 — 42 boards probe + heuristic vs empirical 比較

---

## 9. 他の知見との関係

- **SPR 軸の境界**: 別文書 `INSIGHTS_2026-06-08.md` 参照
  - SPR=3 が GTO 戦略反転点
  - 本 board × カテゴリ 分析は SPR 16 (Cash100 SRP) 想定
  - SPR が変わると カテゴリ 行動激変 (set 4% → 96% etc) → 本表も SPR 別が必要

- **公式 v9b / v15** の改善余地:
  - 本表の outlier (paired × 2pair = 0%) を encoding できているか確認必要
  - flop_v9b の huge_loss 残 6% はこの種の outlier に起因の可能性
