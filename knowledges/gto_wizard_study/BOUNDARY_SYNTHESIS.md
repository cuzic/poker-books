# 境界調査統合シンセシス — 累計 268 spots

調査期間: 2026-05-25 〜 2026-05-26
データソース: GTO Wizard API (MTT6mSimple @200.125bb)

## 大発見ランキング

### 🥇 #1: Turn IP cbet サイズの完全マッピング (B-7+B-7x2 = 30 spots)

#### Kxx + turn card によるサイズ切替の決定図

```
Kxx + 3        → 276% pot (low rank, polarized)
Kxx + 4,5,6,8,9 → 101% pot (mid range, balanced)
Kxx + T,J,Q     → 276% pot (broadway draw triggers polarization)
Kxx + A         → 101% pot (overcard, IP has Ax)
```

**法則**: 「ターンカードが BB のレンジを直撃しない」ほどサイズ大。

| 板タイプ | サイズ |
|--------|------|
| Dry high + low blank turn | 276% |
| Dry high + mid blank turn | 101% |
| Dry high + broadway turn | 276% |
| Wet connected | 101% |
| AK4 系（IP range adv 強） | 157% |
| Mono | 276% (or 101% if flush completes) |

---

### 🥈 #2: ターン donk on board pair の boundary (B-1+B-1x+B-1x2 = 36 spots)

#### 完全な「donk 発動条件」

**HIGH donk (40-60%)**: 連結 board × bottom/mid pair turn
- 987 + 8: **59.6%**
- 987 + 9: 47.9%
- T76 + 6: **53.1%**
- JT9 + 9: 39.2%
- Kxx + 7: 48.1%
- Kxx + 2: 38.5%
- QJ4 + 4: 39.7%
- 9h8s7d + 7: 61.6%

**EXTREME donk (70-86%)**: AK4 系での pair turn
- AK4 + K: **86.0%**
- AK4 + A: 71.6%

**ZERO donk (0-1%)**: 以下のすべて
- すべての blank turn
- Q/J/T-high board の top pair turn (QJ4+Q, T76+T, JT9+J): 0%
- AK4 + non-pair mid blank: 0%
- T76 + str8 complete (T76+8, T76+5): 0-19%

#### 簡略フロー

```
Turn = board のいずれかの rank と同じ？
├ YES (pair turn)
│  ├ board が AK系? → donk 70-86% (top pair も mid pair も)
│  ├ board が 9-high 以下 connected? → donk 40-60%
│  ├ board が high-disconnected (Kxx, QJ4)?
│  │  ├ bottom/mid pair → 38-48%
│  │  └ top pair (Kxx+K等) → 25%
│  └ board が Q/J/T-high connected (QJ4, T76, JT9)? → top pair 0%, mid/bot 0-40%
└ NO (blank/str8/flush) → donk 0-2%
```

---

### 🥉 #3: マルチウェイ SB donk のグラデーション (B-3+B-3x+B-3x2 = 30+ spots)

#### High card 別 SB donk 平均

| high group | avg donk% | n |
|---|---:|--:|
| A | 8-18% | 5 |
| K | 12-23% | 7 |
| Q | 16-28% | 5 |
| J/T | 15-25% | 9 |
| **9/8** | **17-28%** | 5 |
| <8 | 5-13% | 4 |

**意外な発見**: A-high より **8/9-high** で donk 多用。理由は「SB のレンジに 8x/9x のミドルペアハンドが多く、IP（HJ）の cbet レンジが弱体化する」。

#### 詳細パターン

| ボードタイプ | donk% | 例 |
|----------|------:|-----|
| **最低**: 低連結 rainbow | **2-7%** | 543, 654, 765 |
| 中連結 rainbow | 7-15% | 432, 876, T98 |
| K-high + 9 connector | 5-15% | K92 |
| **A/K-disconnected** | **15-25%** | A74, K64 |
| **Q-high disconnected** | **20-28%** | Q42, Q63 |
| **Mid-disconnected** | **20-35%** | 864, J52, J75 |
| パイア板（774） | 19% | flop donk |

---

### #4: probe spot (XX 後 turn first) の完全マトリクス (B-1 + B-8 + B-8x + B-8x2 = 47 spots)

#### 「BB がレンジ優位を取れる board × turn」が確定

**HIGH probe (50-92%)**: 連結 wet board × BB hit turn
- 9h7s5d + 6 (str8): **92%** 
- T76 + 8 (str8): 59%
- 9h7s5d + 8 (str8): 66%
- 987 + 9 (top pair on wet): 51%
- 987 + T (overcard/str8): 54%

**ZERO probe (<2%)**: 「board が IP range を直接強化」
- AK4 + K (BB に K 少): 0.1%
- QJ4 + T (IP の AKJ/AQJ 完成): 0.1%
- QJ4 + J (top pair, IP も J 多): 0.2%
- KQ4 + Q (mid pair, IP も Q 多): 0.1%
- JT8 + Q (broadway IP 強化): 0.1%
- KJ4 + T (str8 reach, IP に KQJT 多): 0%

**LOW probe (5-20%)**: dry board or scare A
- Kxx + various: 2-18%
- KQ4 + K (top pair): 12%
- KJ4 + Q (top pair): 15%

#### 法則

```
probe 率 = f(BB hit | IP hit)

HIGH: 連結 board + 連結 turn (str8, top pair on wet)
ZERO: board pair where IP range densely contains that rank
LOW: dry board または scare overcard
```

---

### #5: ペアフロップ B-9 NEW

| 板 | flop first | turn after cbet-call |
|---|----:|----:|
| KK7 | 0% donk | 0% donk |
| AAK | 0% donk | 0% donk |
| **774** | **19% donk!** | 0% donk |
| Q66 | - | 0% donk |
| 883 | - | 0% donk |

**唯一の例外**: **774 のような low-pair flop で BB がフロップ donk 19%**。
理由: BB のレンジに 7x（A7, 87, 76 等）が多く、フロップで自然に強化される。high-pair board (KK7, AAK) では IP のレンジに高ペアが多く、BB は donk しない。

### #6: モノフロップ B-10 NEW

| 板 | flop first | turn after cbet-call | XX turn (probe) |
|---|----:|----:|----:|
| KsQs7s | 0% | 0% | - |
| Js9s5s | 0.1% | 0% | - |
| KsQs7s+2h | - | - | **22.2%** |
| Js9s5s+2h | - | - | **20.9%** |
| AsTs5s+2h | - | 0.2% | - |
| QsTs6s+2h | - | 0.3% | - |

**法則**:
- Mono フロップで OOP donk は **ほぼ 0%**（IP のレンジ優位が強い）
- ただし XX 後の **mono probe = 20-22%**（IP のチェックバック → BB が攻める）

---

## 累計信頼度（最終）

| claim | 累計 n | 信頼度 |
|------|----:|------:|
| Flop donk = 0% (except 774-style low pair) | 5+10 | **高** |
| Turn donk = 0% (blank) | 13+10 | **高** |
| Turn donk on board pair: 板による (0%〜86%) | 13+12+12 | **高** |
| Turn cbet サイズ二極化 (101%/276%) | 20+10 | **高** |
| Multiway SB donk グラデーション | 17+15+15 | **高** |
| XX-XX river position 効果 | 12 | 中 |
| Probe spot board×turn matrix | 25+12 | **高** |
| Mono flop OOP = 0% | 1+10 | **高** |
| Paired flop OOP = 0% (except 774) | 10 | **中** |
| ICM bubble | 4 | 中 |

---

## 書籍 vol2 改訂マッピング（最終確定版）

| 章 | 修正内容 | データ根拠 |
|---|------|---------|
| ch03 flop | 「OOP flop donk = 0%」例外 774-style pair flop で 19% | B-9 |
| ch04 mono flop | Mono OOP donk = 0%、IP cbet 設計詳細 | B-10 |
| ch05 multiway | SB donk 板別表（high card × connectedness） | B-3 等 |
| **ch07 turn barrel** | **サイズ: 101% mid range / 276% broadway / 157% AK系** | B-7 |
| **ch08 turn defense** | **donk 発動条件フローチャート**（pair turn × board type） | B-1 |
| **ch08 probe spot** | **board × turn card マトリクス**（HIGH/ZERO/LOW 分類） | B-8 |
| ch10 river | XX-XX 後 lead 率（CO>BTN>HJ/UTG） | B-4 |
| ch11 multistreet | river card 効果表（pair/scare/blank/str8） | B-5 |
| vol4 ch10 ICM | BB AI 12.5% vs BTN | B-6 (限定) |

---

## ファイル

- `BOUNDARY_REPORT.md` / `BOUNDARY_REPORT2.md` / `BOUNDARY_REPORT3.md` / `BOUNDARY_REPORT4.md` — 詳細
- `FINAL_ACTION_GUIDE.md` — v2 行動指針
- `BOUNDARY_SYNTHESIS.md` (本ドキュメント) — 累計シンセシス
- `b1_*/`, `b3_*/`, `b4_*/`, `b5_*/`, `b7_*/`, `b8_*/`, `b9_*/`, `b10_*/`, `ICM_*/`, `SRP_*/`, `3way_*/`, `3bp_*/`, `flop_donk_*/`, `turn_*/`, `probe_*/` — 計 50+ topic dir
- 累計 **268 spots** の JSON データ
