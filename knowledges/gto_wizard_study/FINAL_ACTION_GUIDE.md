# GTO Wizard 検証完了 — 最終行動指針 v2

調査日: 2026-05-25 (boundary v1) + 2026-05-26 (boundary v2)
累計データ: **109 spots**（初回 63 + 境界 v1 47 + 境界 v2 46-2失敗）

## 大局結論：旧指針の重要修正

旧 v1 指針 → 新 v2 指針への主要修正:

| 旧 claim | 新 claim |
|---------|----------|
| 「ターン donk = 0%」 | **「blank turn で 0%」「board pair turn で 25-86%」「bottom pair turn は普遍的に 40-60%」** |
| 「flop donk = 0%」 | 「flop donk = 0%」（5 板で確定、変更なし） |
| 「multiway SB donk T76 で 25%」 | 「**連結度よりも high-card 性で決まる**。低連結 543/654/765 は 2-7%、高 disconnected K64/Q42 は 20-30%、middle-disconnected J75/T76 は 25-35%」 |
| 「XX-XX river BB lead 20-54%」 | 「UTG/HJ:25%、CO:38%、BTN:32% — CO が最大」 |
| 「turn give-up river BB lead 37-78%」 | 「river card 依存。pair top:60%、blank:37%、scare A:26-44%、str8 complete:43-60%」 |

---

## ターン アグレッサー（旧 v1 と同じ、未変更）

GCP study 395 board の結論を維持:

```
継続バレル: paired_high で 99%、rainbow_connected で 90%、2tone で 78%
サイズ: 33% pot 支配的（例外: AK4 等 range-advantage 板で overbet 158%）
```

---

## ターン ディフェンダー（**大幅修正**）

### 新ルール: ターン donk 判定（IP cbet→call 後 BB first）

**従来「常に check」は誤り。Turn card の出方で判定:**

| Turn card の種類 | donk 頻度 | サイズ |
|----------------|----------:|------|
| **Blank turn**（オーバーカードなし、ペアなし、str8 なし） | 0% | (check) |
| **Top pair turn** (KK on Kxx) — 高ランク board | **25-72%** | 33% pot 小 |
| **Top pair turn** — 中ランク board (QQ on QJ4 等) | 0% | (check) |
| **Mid pair turn** on dry high board (e.g. Kxx→7) | **48%** | 33% |
| **Mid pair turn** on connected board (QJ4→J) | 0% | (check) |
| **Mid pair turn** on AK4→K (super range adv) | **86%** | 20% |
| **Bottom pair turn**（普遍的） | **38-62%** | 33% |
| **Str8 completing turn**（ストレートが板に出る） | 0%（多くの場合） | (check) |
| **Str8 draw turn** (T76→9) | 17% | 33% |
| **Overcard turn**（A drop on 987） | 0% | (check) |
| **Flush completing turn** | 0% | (check) |

### 判定フロー

```
■ ターン OOP（cbet-call 後）
  1. Turn が flop card のいずれかとペアになる？
     YES → donk 候補 (30-60%)、サイズ 33% pot
       1a. Bottom pair → 必ず donk 検討（40-60%）
       1b. Mid pair on dry high → donk（40-50%）
       1c. Mid pair on connected → check
       1d. Top pair on K/A-high → donk（25-70%）
       1e. Top pair on T/J/Q-high → check
     NO → 2 へ
  2. Turn が str8/flush 完成？
     YES → check（board がコーディネートしすぎ）
  3. Turn が overcard？
     YES → check（IP の cbet range も overcard を打つ）
  4. それ以外 (blank) → 必ず check（donk 0%）
```

### 理由（GTO 解釈）

- **Bottom pair turn**: BB のレンジには小ペア・コネクターが多く、bottom card にヒット率が高い。一方 IP の cbet range はトップペア・オーバーペア中心で bottom card にヒットしない。BB のレンジが排他的に強くなる → リード OK
- **Top pair on K/A 板**: BB が K-high 板でコール時、K7/K8/K9 などの弱トップペア候補が多い。Turn の K で BB が top pair に「昇格」する確率が高い
- **Top pair on Q/J/T 板**: 逆に IP も Qx/Jx/Tx を多く cbet するため、turn pair で BB が単独優位にならない
- **Str8/flush 完成**: 「ナッツがボードに見える」ので両者とも cautious

---

## マルチウェイ フロップ SB ディフェンダー（**大幅修正**）

### 新ルール: 3-way フロップ SB lead 判定

**旧「連結度で決まる」は誤り。実際は board の high card + disconnection で決まる**

| ボードタイプ | SB lead 率（HJ open multiway） |
|-----------|----------:|
| 低連結 (543, 654, 765 rainbow) | **2-7%**（lead しない） |
| 低連結 + low card pair (982) | 10% |
| 連結 + 高ランク (J97, J95) | 14-20% |
| Mid disconnected (864, 872, J75) | 18-34% |
| Mid mixed (T85, T97, J85) | 16-22% |
| High disconnected (A74, K64, Q42) | **18-26%** |
| Q-high air (Q42) | **26%**（最大級） |

### Position 比較（HJ vs CO vs BTN 開きの multiway）

| 開いた pos | SB lead 平均 | n |
|-----------|------:|--:|
| HJ open + SB+BB call | 16.9% | 15 |
| CO open + SB+BB call | 20.5% | 6 |
| BTN open + SB+BB call | **23.5%** | 7 |

**示唆**: BTN open multiway では SB が最も積極的にリードする（BTN レンジが広く、SB のレンジ優位が相対的に大きい）。

### 判定フロー

```
■ 3-way フロップ SB first
  1. Board が low rainbow connected (543, 654, 765)
     → check（lead 0-5%）
  2. Board に A/K/Q が含まれ disconnected
     → 20-30% で lead（33% pot サイズ）
     → SB のポケットペアがレンジで unique 優位
  3. Board が mid-disconnected (864, J75)
     → 20-35% で lead
  4. 開いた pos が BTN なら +5pt 増し
```

---

## XX-XX 後の river BB ディフェンダー / アグレッサー（**部分修正**）

### Position effect

| 相手 pos | BB river lead 平均 | サイズ傾向 |
|----------|------:|-------|
| UTG vs | 24.9% | 126% overbet 中心 |
| HJ vs | 24.4% | 126% overbet |
| **CO vs** | **38.4%** | 33%/126% 混合（CO 最大） |
| BTN vs | 31.9% | 33% 多め |

### Turn give-up 後の river card 効果

`flop / X-R<cbet>-C / X-X / river` の BB lead 率は **river card で激変**:

| Flop+Turn | River card 種類 | BB lead% |
|---------|--------------|------:|
| 987+4 (wet) | Blank (2) | **78%** |
| 987+4 | Board pair (4 再度) | **76%** |
| 987+4 | Str8 complete (T) | 60% |
| 987+4 | Pair top (9) | 55% |
| 987+4 | Scare A | **26%**（最低） |
| Kxx+5h | Pair top (K) | **61%** |
| Kxx+5h | Scare (A) | 44% |
| Kxx+5h | Mid blank (Q) | 38% |
| Kxx+5h | Blank (3) | 37% |
| QJ4+7 | Board pair (7) | 45% |
| QJ4+7 | Scare (A) | 44% |
| QJ4+7 | Str8 complete (T) | 43% |
| QJ4+7 | Blank (2) | 42% |
| QJ4+7 | Pair top (Q) | 28%（最低） |

### 判定フロー

```
■ Turn give-up 後の river BB first
  1. River が wet board の board pair → lead 65-80%
  2. River が dry board の top pair → lead 60%
  3. River が wet board の top pair / str8 complete → 40-60%
  4. River が blank → 35-45%
  5. River が scare A on wet → **lead 控えめ 25%**（A は IP に当たる）
  6. River が dry-board pair top で IP もよく持つ → lead 28-30%（控えめ）
```

サイズは概ね 33% pot か 125% overbet の **二峰性**。「BB が中ランクハンド多い」spot は 33% bet、「ナッツ+air 極化」spot は overbet。

---

## リバー ディフェンダー（未変更）

MDF + bluff catch 判定は v1 と同じ。

---

## 書籍反映マッピング（最終版）

| 巻 | 章 | 修正内容 |
|---|---|------|
| **vol2 ch08「ターン defense」** | ターン donk の新ルール表 | 「blank turn 0%」「board pair で 40-86%」 |
| **vol2 ch05「マルチウェイ」** | SB lead 板別表 | 「低連結 = lead しない」「Q/K-high disconnected で 20-30% lead」 |
| **vol2 ch10「リバー戦略」** | XX-XX river BB lead 表 | 「CO > BTN > UTG/HJ」「river card で 26-78% 変動」 |
| **vol2 ch11「multistreet plan」** | river card 効果表 | wet/dry × pair/scare/str8 マトリクス |
| **vol4 ch10「ICM bubble」** | BB vs BTN all-in 12.5% | （v1 のまま） |

## 信頼度サマリ

| claim | 旧 n | 新 n | 信頼度 |
|------|----:|----:|------:|
| Flop donk = 0% | 5 | 5 | 高 |
| Turn donk = 0% (blank) | 3 | 13 | 高 |
| Turn donk on board pair | 0 | 13 | **高（新）** |
| Multiway SB donk pattern | 4 | 17+10 | **高（新）** |
| XX-XX river position | 3 | 12 | 中-高 |
| River give-up card effect | 3 | 14 | **高（新）** |
| ICM bubble | 4 | 4 | 中（未拡張） |

## 残課題

- **ICM stack 構成依存性 (B-6)** — 未着手、5-15bb BB stack 等での挙動
- **turn cbet size 二極化 (B-7)** — overbet 切替条件
- **probe spot turn card 効果 (B-8)** — 詳細マッピング
- **Cash games**（Premium tier 範囲外）
- **9-max**（Premium tier 範囲外）

---

ファイル:
- 詳細データ: `BOUNDARY_REPORT.md` / `BOUNDARY_REPORT2.md`
- 個別 JSON: 各 topic 配下
- 旧 SUMMARY 統合候補: `SUMMARY.md` を本ドキュメントで上書き予定
