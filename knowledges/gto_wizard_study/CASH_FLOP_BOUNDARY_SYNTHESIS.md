# Cash Flop CBet 境界調査 — 99 spots シンセシス

生成日: 2026-05-27
データ: Cash6mGeneral_6mNL25R25 @ 100bb / 87 BTN + 12 HJ
累計 cash flop spots: **187**（B-20 28 + B-22 12 + B-23 1 + B-24 8 + B-25 22 + B-32-40 99 - 重複）

## 🎯 主要発見ベスト 10

### 1. **High card 別 cbet 頻度（BTN, rainbow non-paired）**

| high card | avg cbet% |
|---------|------:|
| **K** | **62.6%** ← peak |
| **Q** | **60.7%** |
| A | 47.7% ← 意外に低い |
| J | 42.1% |
| T | 37.8% |
| 9 | 41.8% |
| 8 | 46.6% |
| 7 | 39.6% |
| 6 | 48.9% |
| 5 | 53.2% |
| 4 | 47.7% |

**示唆**: **K-high が peak (62.6%)、A-high は意外に低い (47.7%)**。理由: A-high はオーバーキャッチが多くスローダウン、K-high は IP のレンジ優位明確で full cbet。

### 2. **サイズ層が完全二極化 (33% pot vs 116% overbet)**

BTN 79 non-paired spots での size 分布:
- **33% pot**: 53 spots
- **116% overbet**: 26 spots
- **中間サイズ (50-100%)**: **0 spots**

→ **「打つときは 33% small or 116% overbet」の二極化**。Cash 100bb で中間サイズは使われない。

### 3. **116% overbet が使われる board の法則**

Overbet (116%) が選択される 26 spots の特徴:

| パターン | 例 | 共通点 |
|--------|----|----|
| K-broadway disconnected | KJ4 (42% bet), KQJ (25%) | range advantage 強 + bluff catcher 限定 |
| A-broadway disconnected | AJ4 (28%), AT5 (33%), AT7 (29%), A87 (25%) | A 持ち少 + polarize |
| Q-broadway mid-wet | QT5 (57%), QJ6 (42%), Q87 (34%), Q86 (34%) | broadway mix |
| J/T mid-wet | J75 (33%), J84 (35%), J85 (33%), J95 (48%), JT6 (40%) | nutted catcher 区切る |
| T-low connected | T62 (44%), T72 (43%), T52 (43%) | overcard scare |
| Mid connected | 876 (30%), 765 (26%), 975 (30%), 864 (52% mid) | range overlap minimal |

**法則**: 「**BB が catcher として弱い手で対応する board**」で overbet polarize。

### 4. **2tone vs rainbow 差は board 依存**

| board | rainbow | 2tone | 差 |
|------|---:|---:|---:|
| K72 | 73.5% | 53.3% | -20pt |
| Q83 | 99.1% | 54.4% | **-45pt** |
| T98 | 43.5% | 44.5% | 0pt（同等） |
| 987 | 51.1%(HJ) | 43.9% | -7pt |
| AK4 | 36.9% | 40.2% | +3pt |

→ **dry board で 2tone 化すると -20〜-45pt**（FD draw 完成リスクで慎重化）
→ **wet board (T98, AK4) では 2tone と rainbow ほぼ同等**（既に wet）

### 5. **Mono board は一律 30-42%, 33% small bet**

| board | cbet% |
|------|---:|
| AsKs7s (A-high) | 38.3% |
| AsQs5s | 39.7% |
| KsQs7s (K-high) | 34.1% |
| QsTs6s (Q-high) | 38.4% |
| JsTs5s (J-high) | 38.9% |
| Ts8s5s (T-high) | 41.3% |
| 9s8s7s (9-high) | 33.2% |
| 8s6s4s (8-low) | 30.8% |

**法則**: **Mono = 「small 33% bet で 30-42% 頻度」**。BB がフラッシュドロー保有で IP は慎重 cbet。

### 6. **Paired flop は high pair で 80-88%, low pair で 52-67%**

| board | cbet% | パターン |
|------|---:|----|
| KK4 | **88.1%** | high pair + low kicker = IP の overpair 多 |
| QQ4 | 83.5% | 同上 |
| QQ8 | 82.0% | high pair + mid kicker |
| AAQ | 74.2% | |
| JJ4 | 66.5% | mid pair |
| 994 | 51.9% | mid pair + low kicker |
| 552 | 56.8% | low pair |
| **332** | **80.5%** | **lowest pair (例外! 高 cbet)** |

→ 「low pair = 低 cbet」の法則は **332 で例外**。理由: IP が overpair (44+) で常に支配。

### 7. **連結度 (gap) は単純な指標にならない**

| gap | avg cbet% |
|----|------:|
| gap 2 (最連結) | 49.9% |
| gap 3 | 65.9% |
| gap 4 | 42.8% |
| gap 5 | 47.4% |
| gap 6 | 41.7% |
| gap 7 | 40.3% |
| gap 8 | 60.2% |
| gap 9 | 55.7% |
| gap 10 | 62.7% |
| gap 11 | 65.7% |
| gap 12 (最 disconnected) | 50.6% |

→ **U 字型: 最連結と最 disconnected で高い、中間 (gap 4-7) で低い**。
中間 gap は wet board が多く、cbet 控えめになる。

### 8. **K-high gradient の cbet 階層**

| K-high board | cbet% | size |
|------------|---:|---|
| KK4 (paired low) | 88% | 33% |
| KsJdTc (KJT broadway-wet) | **99%** | 33% |
| KT5 | 90% | 33% |
| K83 | 78% | 33% |
| KQ5 | 75% | 33% |
| K72 | 73% | 33% |
| K54 | 70% | 33% |
| K52 | 66% | 33% |
| K53 | 65% | 33% |
| K95 | 61% | 33% |
| K94 | 60% | 33% |
| K87 (wet) | 57% | 33% |
| K76 (wet) | 55% | 33% |
| K98 (wet) | 51% | 33% |
| **KsJd4c (KJ4 nuanced)** | **42%** | **116%** |
| **KsQd7c (KQ7 wet broadway)** | **46%** | **116%** |
| **KsQdJc (KQJ wet broadway)** | **25%** | **116%** |

→ K-high は K72 等の dry で 60-80%、KQJ 系で **overbet polarize**。

### 9. **A-high の特殊性**

| A-high board | cbet% | size |
|-----------|---:|---|
| AKQ (broadway) | 74% | 33% |
| AQJ (broadway) | 78% | 33% |
| A65 (low conn) | 48% | 33% |
| A82 | 52% | 33% |
| A92 | 53% | 33% |
| A95 | 55% | 33% |
| A72 | 51% | 33% |
| A52 | 47% | 33% |
| **AJ4 (mid)** | 28% | **116%** |
| **AT5** | 33% | 116% |
| **AT7 (wet)** | 29% | 116% |
| **A87 (wet)** | 25% | 116% |

→ **A-high broadway は 74-78% small bet**、**A-high mid-wet (AJ4, AT5, AT7, A87) は overbet polarize**。
→ A-high low (A52-A95) は **50% で中庸**（IP の Ax 多保有でも range advantage 限定）

### 10. **Low connected board の特殊パターン**

| board | cbet% | size |
|------|---:|---|
| 876 | 30% | 116% |
| 765 | 26% | 116% |
| 975 (gap) | 30% | 116% |
| 654 | 48% | 33% |
| 543 | 54% | 33% |
| 432 | 48% | 33% |
| 864 (gap mid) | 52% | 33% |
| 8h5d3c (gap) | 58% | 33% |
| 7h5d3c (gap) | 53% | 33% |

→ **最連結 (876, 765, 975) → 30% で overbet polarize**
→ **wheel 系 (654, 543, 432) → 50% で standard bet**
→ Gap がある (864, 753 等) → 53-58% で standard bet

---

## 書籍 vol2 改訂への含意

### Cash flop cbet 戦略の決定木（書籍提示用）

```
1. Board が paired か？
   ├ YES (high pair flop) → 80-88% cbet, 33% pot
   ├ YES (low pair flop) → 52-65% cbet, 33% (332 例外 81%)
   └ NO → 2 へ

2. Board が mono か？
   ├ YES → 30-42% cbet, 33% pot (small bet)
   └ NO → 3 へ

3. High card は何か？
   ├ K-high → 60-80% cbet, 33% pot (KJ4/KQJ等 broadway は 116% overbet)
   ├ Q-high → 35-95% (broadway は polarize)
   ├ A-high broadway → 70-80%, 33%
   ├ A-high low → 47-55%, 33%
   ├ A-high mid wet → 25-33%, 116% overbet
   ├ J/T-high mid → 30-50%, 116% overbet 多用
   └ Low connected (876/765) → 30%, 116% overbet
   └ Wheel (654/543) → 50%, 33%

4. 2tone か rainbow か？
   ├ Dry board + 2tone → cbet -20〜-45pt 控えめ
   └ Wet board (T98+) は影響小
```

### 旧 vol2 ch04 の訂正候補

| 旧記述 | 新発見 | 訂正案 |
|------|------|------|
| 「BTN cbet 75%」 | Avg 52%、size 二極 | 「Standard 50-60%、AK系 overbet 30%」 |
| 「型1 dry は full cbet」 | K72r=73%、Q83r=99%、A52r=47% | 「K/Q-high dry で full、A-high は控えめ」 |
| 「型4 wet は check」 | 連結度で差大 | 「最連結 (876/765) で overbet、wheel は standard」 |
| 「33% 主流」 | 116% overbet が 1/3 | 「33%/116% 二極化、中間サイズなし」 |

---

## ファイル

- 詳細: `b32_*/`, `b33_*/`, `b34_*/`, `b35_*/`, `b36_*/`, `b37_*/`, `b38_*/`, `b39_*/`, `b40_*/`
- レポート: `CASH_DIVERSITY_REPORT.md` (生表), 本ドキュメント (シンセシス)

## 累計 cash spots: **187** + MTT 100bb **24** = **211 spots 大規模 cash/MTT 100bb 比較**

これだけのデータがあれば書籍 vol2 を完全に再設計可能。
