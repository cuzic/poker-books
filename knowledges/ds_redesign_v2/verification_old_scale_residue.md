# 旧スケール残骸検出レポート

検証日: 2026-05-05
対象: 全巻 (flop / flop-advanced / volume4 / volume5 / volume6 / digest) の chapter md
基準: SPEC_HANDSCORE.md / SPEC_OTHER_FORMULAS.md (新スケール HandScore 0-100 equity %)

## 0. 確定した新スケール早見

| 項目 | 旧 | 新 |
|---|---|---|
| HandScore 範囲 | 0-30 (or 0-50) | 0-100 (equity %) |
| 後手スコア式 | `+ A − 3 − C − M` | `+ A − C − M` |
| A | 3 / 2 / 1 (ドライ/セミ/ウェット) | 12 / 6 / 0 |
| C | 3 / 5 / 7 / 9 / 11 | 12 / 17 / 22 / 25 / 30 |
| M | 0 / 3 / 6 | 0 / 12 / 22 |
| 閾値 | ≥8 / 0-7 / <0 | ≥40 / 20-39 / <20 |
| ドロー加点 (旧) | FD +13, OESD +14, GS +10 | FD +36, OESD +32, GS +16 (Rule of 4 直接) |
| TPTK | 18 | 70 |
| TPGK | 15 | 62 |
| TPMK | 8 | 50 |
| TPWK | 6 | 45 |
| Set+ | 30 | 88-95 |

---

## 1. 各巻別ヒット集計

### 1.1 flop (フロップ基礎) — 書き換え漏れ多

| カテゴリ | 該当箇所 | 状態 |
|---|---|---|
| G ドロー加点旧値 | `06-outs-equity.md` 205-297 行（表 + 解説） | **要修正・大** |
| D 旧閾値 textual | `16-multiway-3bet.md:298` (`< 0 → フォールド` の引用) | **要修正・小** |

主修正対象は `flop/chapters/06-outs-equity.md`。表中の値とすべての説明文（OESD +14、FD +13、ガット +10、FD+OESD +17）が旧スケール。GTO 頻度の % は新旧共通だがドロー加点値は新スケール (×4 倍) に更新が必要。

参考: `flop/chapters/02-who-leads.md` の「平均 HandScore: UTG=20, BTN=10」も旧スケール感覚（新スケールでは equity % なので UTG レンジ vs 全体 ≈ 35-40 程度のはず）。ただし「相対値の早見表」として読めば致命傷ではないため**判断保留**。

### 1.2 flop-advanced — 微小

| カテゴリ | 該当箇所 | 状態 |
|---|---|---|
| G ドロー加点旧値 | `images/tools_map_vol2_vol3.txt:83` | 図版テキスト（再描画時に更新） |
| C M 値 | `18-appendix.md:483` | 「巻② ch16 (M=3/M=6 の経験則 vs 厳密)」課題リスト記述 — 残してよい |

本文 (.md) 自体は新スケールに移行済み。

### 1.3 volume4 (ターン・リバー基礎) — **重大・最優先**

| カテゴリ | 該当箇所 | 状態 |
|---|---|---|
| E 旧式 `+A−3−C` | `00-introduction.md:45,80,196` | **要修正・最優先** |
| D 旧閾値 | `00-introduction.md:82` (`≥ 8 → CR / 0〜7 / < 0`) | **要修正・最優先** |
| B/C 旧 A/C/M 係数 | `00-introduction.md:197-199` (A=3/2/1, C=3/5/7, M=0/3/6) | **要修正・最優先** |
| F 旧 HS スケール表記 | `00-introduction.md:194` (`0〜50`) | **要修正** |
| E/D 旧式 + 閾値 | `02-turn-river-position.md:116,128,137,139-141` | **要修正・最優先** |
| A 旧 C 値 | `11-defender-score-river.md:446-474` (C=9/C=11 検証コラム) | **判断保留**（GTO 検証データ自体が旧 C 表記。再検証で更新するか、注釈を追加） |
| B 旧 A 値文脈 | `13-oop-defense-basic.md:67` (`ドライ（A=3）` / `A値が2または1に更新` ) | **要修正** |
| F 旧 HS 18 比較 | `10-defender-score-turn.md:199` (`フロップA=3`) | **要修正・小** |

`volume4/chapters/00-introduction.md` と `02-turn-river-position.md` は導入章にも関わらず旧式・旧閾値・旧 A/C/M が完全に残存。**読者が最初に出会う章**であるため修正の影響が最大。

`volume4/10/11` の例本文と `12-16` ドリル群は既に C=22, A=12 など新スケールで書き直し済み（24 ヒット確認）。

### 1.4 volume5 (ターン・リバー応用) — 限定的

| カテゴリ | 該当箇所 | 状態 |
|---|---|---|
| C 旧 M 値説明 | `12-multiway.md:205,445` (`旧 M=3 → 新 M=12`) | **意図的残存**（旧→新の対応説明） |
| F/B 旧スケール参照 | `19-appendix-c.md:55,59` (`A=3/2/1`, `セット以上=30 / TPTK=18 / TPGK=15`) | **要修正・大** |

`19-appendix-c.md` のシリーズ継承表で旧スケールを"継承元"として表記している箇所が複数。線 230 では「A 係数（新スケール: ドライ=12/...）巻② で新スケールで再定義」と新スケール表記もあり混在。**冒頭のサマリ表 (55, 59 行) を新スケールに揃える必要あり**。

### 1.5 volume6 (トーナメント) — クリーン

すべての本文が新スケール（0-100, A/C/M 新値, 閾値 40/20）に統一済み。`Harrington's M ratio` (M=3, M=6 等) は別概念で意図的残存。19 章の ICM 補正は旧スケール `× 5` を `× 20` に変換した式として明記済みで整合。

### 1.6 digest (ダイジェスト) — 部分的

| カテゴリ | 該当箇所 | 状態 |
|---|---|---|
| G ドロー加点旧値 | `01-outs-equity.md:75-114` (FD +13 / OESD +14 / ガット +10) | **要修正・大** |
| F 旧 HS textual | `19-appendix-a.md:212` (`旧 → 新` 変換表) | **意図的残存**（変換ガイド） |
| D 旧閾値 textual | `19-appendix-a.md:212` 同上 | **意図的残存** |
| F textual | `12-defender-score-turn-river.md:68` (`HandScore=18+25=43`) | **誤読扱い・確認済**（実際は新スケール: 25=Aハイ + 18=FD ターン Rule of 2 加点。`18-drill-30.md:391` の Q17 解説と整合） |

`digest/chapters/01-outs-equity.md` だけが書き換え漏れ。表全体と 4 行の解説文を新値（FD +36 / OESD +32 / GS +16 / FD+OESD +52）に修正。

---

## 2. カテゴリ別ヒット数 (書き換え漏れのみ、意図的残存除外)

| カテゴリ | flop | flop-adv | vol4 | vol5 | vol6 | digest | 合計 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A. C 値旧 | 0 | 0 | 2† | 0 | 0 | 0 | 2 |
| B. A 値旧 | 0 | 0 | 5 | 1 | 0 | 0 | 6 |
| C. M 値旧 | 0 | 0 | 1 | 0‡ | 0‡ | 0 | 1 |
| D. 旧閾値 | 1 | 0 | 4 | 0 | 0 | 0‡ | 5 |
| E. `−3` 旧式 | 0 | 0 | 5 | 0 | 0 | 0 | 5 |
| F. 旧 HS 値 | 0 | 0 | 1 | 2 | 0 | 0 | 3 |
| G. ドロー旧加点 | 1 (file) | 0 | 0 | 0 | 0 | 1 (file) | 2 |
| **合計** | **2** | **0** | **18** | **3** | **0** | **1** | **24** |

† C=9/C=11 検証コラムは GTO 実測値の検証であり、文脈で「旧 C 値の妥当性検証」として残してよい。ただし新 C=25/30 への対応注釈を追加すべき。
‡ 意図的残存 (旧→新比較記述、Harrington's M ratio など) は除外。

---

## 3. 優先度別 修正対象一覧

### P0 (最優先 — 読者が最初に触れる章で旧式が残っている)

1. `volume4/chapters/00-introduction.md`
   - 41-46 行: 後手スコア式骨格を `HandScore + A − C − M` に
   - 80-82 行: 同上 + 閾値を `≥40 / 20-39 / <20` に
   - 194-200 行: 巻①〜3 接続セクションの A/C/M を新値に、HandScore レンジを `0〜100` に
2. `volume4/chapters/02-turn-river-position.md`
   - 116, 137 行: 式骨格 `+ A − 3 − C` → `+ A − C`
   - 128 行: HandScore `0〜50` → `0〜100 (equity %)`
   - 139-141 行: 閾値 `≥8/0〜7/<0` → `≥40/20-39/<20`

### P1 (高優先 — 表・解説で具体値が古い)

3. `flop/chapters/06-outs-equity.md` 行 205-297: ドロー加点表すべて新スケール (×4)
4. `digest/chapters/01-outs-equity.md` 行 75-114: 同上、簡易表も新スケール
5. `volume5/chapters/19-appendix-c.md` 行 55, 59: A 係数と役スコアの旧値テーブルを新スケールに

### P2 (中優先 — 本文中の旧値文脈)

6. `volume4/chapters/13-oop-defense-basic.md:67`: `A=3 / 2 / 1` → `A=12 / 6 / 0`
7. `volume4/chapters/10-defender-score-turn.md:199`: `フロップA=3` → `フロップ A=12`
8. `flop/chapters/16-multiway-3bet.md:298`: `後手スコア < 0` → `後手スコア < 20`

### P3 (確認・注釈追加)

9. `volume4/chapters/11-defender-score-river.md` 446-474 行（C=9/C=11 GTO 検証コラム）
   - GTO 実測 batch は旧 C 表記で実行されたため、本文は「（旧スケール表記の C=9 = 新スケールの C=25）」のような注釈追加が望ましい。再検証なしで値変換は不可。

### P4 (再描画時のみ — 本文には影響しない)

10. `flop-advanced/chapters/images/tools_map_vol2_vol3.txt`: 図版テキスト

---

## 4. 自動修正スクリプト案

`flop/06`、`digest/01`、`volume5/19` 等の表は機械的置換で対処可能。`volume4/00`、`02` は文脈を伴う書き換えのため Edit ベースで個別修正を推奨。

```bash
# (1) flop/06-outs-equity と digest/01-outs-equity のドロー値テーブル
# ガットショット +10 → +16
# 2オーバーカード +7 → +24
# OESD +14 → +32
# FD +13 → +36
# FD + ガット +14 → +48
# モンスター/FD+OESD +17 → +52

for f in flop/chapters/06-outs-equity.md digest/chapters/01-outs-equity.md; do
  sed -i \
    -e 's/| \*\*+10\*\* |/| **+16** |/g' \
    -e 's/| +7 |/| +24 |/g' \
    -e 's/| \*\*+14\*\* |/| **+32** |/g' \
    -e 's/| +13 |/| +36 |/g' \
    -e 's/| \*\*+17\*\* |/| **+52** |/g' \
    "$f"
done
# 注: 表セルが入り組んでいるため目視確認必須
```

**volume4/00 と 02 は機械置換不向き** (文脈ある説明文)。Edit ツールでの個別修正を推奨:

- `+ A − 3 − C` → `+ A − C` (5 箇所、grep で位置特定済み)
- `≥ 8 → チェックレイズ検討` → `≥ 40 → チェックレイズ検討`
- `0〜7 → コール` → `20〜39 → コール`
- `< 0 → フォールド` → `< 20 → フォールド`
- `ドライ=3、セミ=2、ウェット=1` → `ドライ=12、セミ=6、ウェット=0`
- `33%=3、50%=5、75%=7` → `33%=12、50%=17、75%=22 (リバーは 100%=25 / 150%=30 追加)`
- `HU=0、3-way=3、4-way+=6` → `HU=0、3-way=12、4-way+=22`
- `0〜50` (HandScore レンジ) → `0〜100 (equity %)`

---

## 5. 「残ってもよい」と判断した箇所のまとめ

1. `volume6/chapters/19-formula-correction.md:216` — 「旧スケール (0〜30 範囲) の `p × 5`」: ICM 補正の係数導出説明の中で旧スケール値を歴史的経緯として明示。新スケール `p × 20` の妥当性を導く。
2. `volume5/chapters/12-multiway.md:205, 445` — 「旧スケール M=3 → 新スケール M=12」: 旧→新の対応を読者に説明。
3. `digest/chapters/19-appendix-a.md:212` — 旧→新変換表 A-10 セクション全体: 既刊シリーズから移行する読者向け変換ガイド。
4. `volume6` Harrington's M ratio (M=3, M=6 等) — 後手スコア M 係数とは別概念のため残置。
5. `volume4/10/19/16/05`、`volume5/11/14/16/00`、`volume6/23` 等の「TurnCard 係数: ペア=4 / OC=3 / ブランク=2 / フラッシュ=1 / コネクター=0」 — バレルスコアの TurnCard 係数で、HandScore とは別の旧来からの設計値。残置。
6. `volume5` の「ランクカウント A=2, K=1」のような表記 — ボード読みでのランク出現枚数で、A/C/M 係数とは無関係。

---

## 6. 検証コマンド (再走確認用)

```bash
# 主要旧式 + 旧閾値の grep
cd /home/cuzic/poker-books

# E. 旧式
grep -rEn "\+\s*A\s*[−-]\s*3\s*[−-]\s*C" \
  flop/chapters/ flop-advanced/chapters/ volume4/chapters/ volume5/chapters/ volume6/chapters/ digest/chapters/

# D. 旧閾値（コール域 0〜7、CR ≥8、フォールド <0）
grep -rEn "後手スコア\s*≥\s*8\b|後手スコア\s*<\s*0\b|0〜7\s*→" \
  flop/chapters/ flop-advanced/chapters/ volume4/chapters/ volume5/chapters/ volume6/chapters/ digest/chapters/

# B. 旧 A 値
grep -rEn "ドライ=3|セミ=2|ウェット=1" \
  flop/chapters/ flop-advanced/chapters/ volume4/chapters/ volume5/chapters/ volume6/chapters/ digest/chapters/

# G. 旧ドロー加点
grep -rEn "FD.*\+13|OESD.*\+14|ガットショット.*\+10" \
  flop/chapters/ flop-advanced/chapters/ volume4/chapters/ volume5/chapters/ volume6/chapters/ digest/chapters/
```
