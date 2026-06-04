# Cash 拡張調査 — 主要発見シンセシス

生成日: 2026-05-27
データ: **67 spots** Cash6mGeneral_6mNL25R25 @ 100bb 直接 API 取得
累計 cash spots: **96 spots**（B-20 28 + B-22 12 + B-23 1 + B-24 8 + B-25-31 67 - 重複）

## 🎯 主要発見ベスト 10

### 1. 🆕 Cash 3BP で Kxx は **0% cbet**（HJvBB）

| board | cbet% | size |
|------|---:|---:|
| **Ks7d2c (Kxx)** | **0%** | (315% if bet) |
| Qh8d3s | 50% | 20% |
| Jd6c4d | 33% | 20% |
| **Th9s8d** | **78%** | 20% |
| AhKd4s | 9% | 47% |
| **9h8s7d** | **98%** | 20% |
| KsKd7c (KK7) | 0% | (315%) |
| KsQs7s (mono) | 24% | 47% |

→ **「3BP の dry K-high は両者ともチェック」「3BP の connected (987, T98) は full cbet」**

### 2. Cash 3-way SB donk: connected で 53-76%

| board | donk% | パターン |
|------|---:|---|
| **Jh7s5c** | **75.7%** | connected mid-low |
| **Th9s8d** | **55.0%** | connected high |
| **Td7c6s** | **53.2%** | connected mid |
| Ah7c4d | 2.4% | high disconnected |
| Kh6s4c | 0.1% | K disconnected |
| Ks7d2c | 0.2% | K dry |
| 5d4s3c | 0.0% | low connected |

→ **MTT の発見（8/9-high が donk peak）と全然違う**！cash multiway では **connected board で SB が donk**。

### 3. Cash OOP defense (BB vs IP cbet): board × CR 率

| board | fold | call | CR |
|------|---:|---:|---:|
| AK4 | **66%** | 34% | **0%** |
| J64 | 60% | 33% | 7% |
| KK7 | 42% | 46% | 12% |
| Kxx | 34% | 55% | 11% |
| T98 | 29% | 56% | 15% |
| Qh4s2c | 32% | 54% | 14% |
| **987** | 35% | 38% | **28%** |
| **T76** | **19%** | 69% | 12% |

→ **AK4 で BB の CR = 0%、fold 66%**（IP の range adv 強い）
→ **987 で BB CR 28%**（最高 CR 率、wet board）
→ **T76 で fold 19%**（最低 fold 率、BB の range hit 多）

### 4. Cash IP turn cbet サイズ層: 67%/115%/185%

MTT (101%/157%/276%) とは異なる **3 サイズ層**:

| board+turn | bet% | size |
|---|---:|---|
| Ks7d2c+5h (blank) | 42% | **67%** |
| Ks7d2c+Ah (overcard) | 66% | 67% |
| **Ks7d2c+Qh (broadway)** | 46% | **185%** |
| Qh8d3s+2h | 28% | **185%** |
| Th9s8d+4c | 64% | 67% |
| **AhKd4s+2c** | 38% | **115%** |
| 9h8s7d+2c | 58% | 67% |

→ **broadway turn (Kxx+Q) と dry blank (Qh83+2) で 185% overbet**
→ **wet board と low pair → 67% bet (standard)**
→ **AK4 系は 115% (mid overbet)**

### 5. Cash 特殊 boards Position effect

ペアフロップ (KK7):
| pos | cbet% |
|----|---:|
| UTG | 99.9% |
| HJ | 99.9% |
| CO | 98.8% |
| BTN | 89.8% |
| SB | 50.3% |

ペアフロップ (774):
| pos | cbet% |
|----|---:|
| UTG | 46.1% |
| HJ | 45.0% |
| CO | 25.1% |
| SB | 54.9% |

→ **KK7 (top pair on flop): UTG-CO 高 cbet → SB で半減**
→ **774 (low pair): CO で 25% に低下、SB で復活**

モノフロップ KQ7s:
| pos | cbet% |
|----|---:|
| UTG | 51% |
| HJ | 50% |
| CO | 38% |
| SB | 18% |

→ **モノ board は SB で 18% まで低下**

### 6. SB limp pot: BB lead 70-89%

| board | BB bet% | size |
|------|---:|---|
| Kxx | 70.7% | 50% |
| T98 | 89.4% | 50% |
| AK4 | 79.8% | 50% |
| 987 | 88.5% | 50% |
| **Q42** | **0.3%** | 180% (rare) |

→ SB limp の弱さを利用して **BB はほぼ常に bet**（Q42 air 例外を除く）

### 7. Cash XX-XX river: BTN vs HJ で逆転

| line | board | BB lead% |
|----|------|---:|
| HJvBB Kxx5h3d | dry | **50.3%** |
| BTNvBB Kxx5h3d | dry | **19.8%** |
| HJvBB 987-4-2 | wet | **62.9%** |
| BTNvBB 987-4-2 | wet | 23.9% |

→ **Cash では HJ vs > BTN vs**（MTT 100bb の反対）
→ HJ open はタイト → BB の range adv 大 → BB lead 多
→ BTN open は wide → BB の range adv 小 → BB lead 少

### 8. Cash turn give-up river

| board (5 cards) | BB lead% | size |
|---------------|---:|---|
| Ks7d2c5h3d | 50.6% | 25% |
| 9h8s7d4c2d | **62.8%** | **100%** |

→ Wet board の turn give-up 経路で 63% lead、100% pot overbet。

### 9. ウェット boards で position 効果が消える

| pos | 987 cbet | T98 cbet |
|----|---:|---:|
| UTG | 50.5% | 89.3% |
| HJ | 51.1% | 88.3% |
| CO | 49.4% | 42.5% |
| BTN | - | - |
| SB | 54.1% | - |

→ **987: 全 position で ~50%**（コネクテッドで range adv 均等化）

### 10. 累計 cash spots と coverage

| 領域 | spots | カバー率 |
|----|---:|----|
| 100bb 全 position × 7 boards | 28 | ✓ 完全 |
| 特殊 boards × position | 22 | ✓ 良好 |
| 3BP HJvBB | 8 | △ 部分（他 position 未） |
| OOP defense | 10 | ✓ 良好 |
| Turn cbet | 8 | △ 部分 |
| 3-way SB donk | 8 | ✓ 良好 |
| SB limp pot | 5 | ✓ 良好 |
| River (XX-XX / turn-give-up) | 6 | △ 部分 |

## 書籍 vol2 改訂への影響

### 訂正が必要

| 章 | 旧記述 | 新発見 |
|---|------|------|
| ch04 flop cbet | 「BTN 75%」 | Cash BTN 平均 51%、MTT 63% |
| ch05 multiway | 「中ランクで donk」 | **Cash multiway: connected で 53-76% donk** (MTT と全然違う) |
| ch07 turn barrel | 「サイズ 101%/276%」 | **Cash 100bb は 67%/115%/185%** (3 サイズ層、MTT と異なる) |
| ch10 river | 「BTN > HJ で BB lead」 | **Cash では HJ > BTN で逆転** |

### 新規追加候補

1. **「Cash 3BP の Kxx は両者 check」** — 直感外、独立節必要
2. **「Cash multiway は connected で donk」** — 章追加
3. **「Cash turn cbet 67%/115%/185%」** — サイズ表更新
4. **「Cash SB limp BB lead 80%」** — 新節

## ファイル

- 詳細データ: `b25_cash_*/`, `b26_cash_3bp/`, `b27_cash_oop_def/`, `b28_cash_turn/`, `b29_cash_multiway/`, `b30_cash_limp/`, `b31_cash_river/`
- 集計レポート: 本ドキュメント + `CASH_EXTENDED_REPORT.md`
- 直接比較: `CASH_MTT_FINAL_VERDICT.md`
