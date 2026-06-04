# Flop Attack Boundary Report — 100bb (cash-proxy) 20 spots

生成日: 2026-05-26
状況: **API 日次上限 850 req に到達** — 28% (20/72 spots) で打ち切り

## API アクセス状況

| ゲームタイプ | アクセス | 用途 |
|-----------|--------|----|
| MTT6mSimple @ 200.125bb | ✓ | deep stack (既存 268 spots) |
| MTT6mSimple @ 100.125bb | ✓ | **cash-proxy（新発見）** |
| MTT6mSimple @ 50.125bb | ✓ | mid-stack（取得前に上限） |
| MTT6mSimple @ 25.125bb | ✓ | short stack（取得前に上限） |
| MTT6mGeneral @ 多深度 | ✓ | (検証で 100bb 確認済) |
| Cash6m*（全種類）| ✗ 403 | user tier 不足 |

**重要発見**: API は **850 requests / 24 hours** の制限あり。今日累計 ~1000 requests で打ち切られた。次回 fetch は **24h 経過後**まで待つ必要あり。

---

## B-15: 100bb (cash-proxy) flop cbet — 全 position × 標準7板（部分達成）

### UTG vs BB (5 spots 完了)

| board | bet% | サイズ | 解釈 |
|------|------:|-----:|----|
| `Ks7d2c` (型1 dry) | 99.9 | 33% | full cbet |
| `Qh8d3s` (型2 wet) | 100.0 | 33% | full cbet |
| `Jd6c4d` (型3 mid-wet) | 98.9 | 33% | ほぼ full |
| `Th9s8d` (型4 conn) | 89.3 | 33% | 高頻度 |
| `AhKd4s` (AK range adv) | **60.7** | **116%** | **大幅減 + overbet** |

**UTG 平均: 89.8%**

### HJ vs BB (7 spots 完了)

| board | bet% | サイズ |
|------|------:|-----:|
| `Ks7d2c` | 100.0 | 33% |
| `Qh8d3s` | 99.9 | 33% |
| `Jd6c4d` | 98.1 | 33% |
| `Th9s8d` | 88.3 | 33% |
| `Ts5d2c` (型5 mid-dry) | 82.3 | **116%** |
| `AhKd4s` | **52.0** | **116%** |
| `Td7c6s` | 68.6 | 33% |

**HJ 平均: 84.2%**

### CO vs BB (5 spots 完了)

| board | bet% | サイズ |
|------|------:|-----:|
| `Ks7d2c` | 92.8 | 34% |
| `Qh8d3s` | 99.1 | 34% |
| `Th9s8d` | **42.5** | 115% |
| `AhKd4s` | 44.6 | 115% |
| `Td7c6s` | 45.0 | 115% |

**CO 平均: 64.8%（最低）**

### BTN vs BB (3 spots、partial)

| board | bet% | サイズ |
|------|------:|-----:|
| `Ks7d2c` | 73.3 | 34% |
| `Qh8d3s` | 86.3 | 34% |
| `Jd6c4d` | 72.5 | 34% |

**BTN 平均: 77.4%（部分データ）**

---

## 大発見

### 発見 1: 200bb から 100bb で AK4 系の cbet 頻度が激減

| 板 | 200bb (既存) | 100bb (新) | 変化 |
|---|------:|------:|-----|
| AK4 by UTG | ~100% | 60.7% | **-40pt** |
| AK4 by HJ | ~100% | 52.0% | **-48pt** |
| AK4 by CO | ~100% | 44.6% | **-55pt** |

→ 「**AK4 系は 100bb で大幅にチェック化**」が新発見。
理由: 100bb の SPR が低く、IP の AKQs などのトップペアは「コミット警戒」で check が選択される。

### 発見 2: Position 別の cbet 頻度（100bb）

| Position | avg cbet% | パターン |
|---------|------:|----|
| UTG | 89.8% | 最タイトレンジ、最高頻度 |
| HJ | 84.2% | UTG に近い |
| **CO** | **64.8%** | **意外な最低値** |
| BTN | 77.4% | 部分データ |

**注目**: CO < BTN < HJ < UTG。
理由: CO のレンジが「open range が広いがレンジ優位は限定的」で、HJ より広い range だが cbet 維持できない。BTN は range が広くてもポジション利得で cbet 増。

### 発見 3: サイズ二極化が 100bb でも観察される

旧来「33% 一択」だった flop cbet サイズが、100bb でも **33% / 116% の二極化** を示す:

- **33% pot**: standard (K72, Q83, J64 など多くの板)
- **116% pot (overbet)**: AK range advantage 板、T52 mid-dry 等

これは MTT 200bb のターン cbet 二極化と同じ構造です。

### 発見 4: T98 ボードで CO の cbet が激減

| 板 | UTG | HJ | CO |
|---|---:|---:|---:|
| Th9s8d | 89.3% | 88.3% | **42.5%** |

CO は range が広いため、T98 のような OOP range の hit が増える wet board で 50% 以下まで cbet を下げる。

---

## 未取得 (52 spots) — API 上限超過

| ID | 領域 | 残 spots |
|----|----|------:|
| B-15 BTN | 100bb BTN vs BB | 4 spots（部分） |
| B-15 SB | 100bb SB vs BB | 4 spots |
| **B-16** | 50bb mid-stack | 10 spots |
| **B-17** | 25bb short stack | 8 spots |
| **B-18** | 4 board × 4 depth | 16 spots |
| **B-19** | 特殊板 (paired/mono) | 10 spots |

---

## 推奨次ステップ

### 即座にできる作業

1. **既存 100bb 20 spots での書籍反映**: UTG/HJ の cbet 頻度が判明、ch04 (flop_ip_cbet) に「100bb と 200bb の cbet 頻度差」を追記可能
2. **既存 cash GCP study (395 boards) と 100bb の比較分析**: 旧 cash NL25 vs 新 MTT 100bb で同じ K72/Q83 板を比較

### 24h 後の再開

明日同時刻以降に fresh token + 残 52 spots を回収すれば、完全な depth gradient 検証が可能。

### 検討事項

- **Cash gametype アクセスは tier 制限**: user 様の GTO Wizard プランをチェック。Cash plan / Cash Premium へのアップグレードを検討
- **Daily quota 850 は計算しておく**: 1日に何 spot まで取れるか事前に計画

---

## ファイル

- 全 JSON: `b15_100bb_{utg,hj,co,btn}/` (20 spots)
- 報告: 本ドキュメント
