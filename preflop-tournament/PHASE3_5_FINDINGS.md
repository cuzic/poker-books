# Phase 3-5 データ分析結果

**調査日**: 2026-05-19  
**収集データ**: MTTGeneral (8-max, BB ante) + MTTMRonlyGeneral + MW (多人数ポット)  

---

## A. アクセス確認結果

| ゲームタイプ | アクセス | 備考 |
|---|---|---|
| `MTTGeneral` depth=SBR+0.125 | ✅ | Phase 1/2 完了（162ファイル）|
| `MTTMRonlyGeneral` SBR 8-25 | ✅ | 126ファイル収集 |
| `MTTMRonlyGeneral` SBR 30+ | ❌ PERMISSION_DENIED | — |
| `MTTGeneral` depth=SBR (no ante) | ❌ PERMISSION_DENIED | — |
| ICM 全種 | ❌ PERMISSION_DENIED | 上位プランが必要 |
| `MTT9mGeneral`, `MTT6mGeneral` | ❌ | 403 |

**結論**: Phase 4（Classic vs Ante）と Phase 3（ICM）は現サブスクリプションでは取得不可。

---

## B. Phase 5: MW N≥3 シナリオ

### B-1. 収集結果

| SBR | 成功 | 失敗 | 失敗理由 |
|-----|------|------|---------|
| 25 | 10/15 | 5 (limp) | limp pot = ツリーに存在しない |
| 40 | 10/15 | 5 (limp) | 同上 |

**成功シナリオ**: BTN_vs_UTGo_HJc, BTN_vs_UTGo_COc, BTN_vs_UTGo_HJc_COc, CO_vs_UTGo_HJc, BB_vs_UTGo_BTNc, BB_vs_UTGo_COc, BB_vs_UTGo_HJc_COc, BB_vs_BTNo_SBc, SB_vs_UTGo_BTNc, SB_vs_COo_BTNc

**Limp pot シナリオ（C-F-F-C 等）**: SBR=17/20/25/40 全てでツリーに存在しない（空レスポンス）。MTTGeneral のツリーはリンプポットマルチウェイを事前計算していない。

#### SBR=17/20 追加 MW 結果

| シナリオ | SBR=17 | SBR=20 |
|---------|--------|--------|
| CO_vs_UTGo_HJc | ❌ 失敗 | ❌ 失敗 |
| BTN_vs_UTGo_HJc | ❌ 失敗 | ❌ 失敗 |
| BB_vs_UTGo_HJc_COc | ❌ 失敗 | ❌ 失敗 |
| BTN_vs_UTGo_COc | ✅ 成功 | ✅ 成功 |
| BB_vs_UTGo_BTNc | ✅ 成功 | ✅ 成功 |
| BB_vs_UTGo_COc | ✅ 成功 | ✅ 成功 |
| BB_vs_BTNo_SBc | ✅ 成功 | ✅ 成功 |
| SB_vs_UTGo_BTNc | ✅ 成功 | ✅ 成功 |
| SB_vs_COo_BTNc | ✅ 成功 | ✅ 成功 |

**重要な発見**: SBR=17/20 では **HJ が UTG open R2 に cold call できない**（ツリー外）。CO/BTN の cold call は有効。HJ cold call が必要なシナリオは SBR≥25 でのみ収集可能。

→ **Cold call 可能な最低 SBR**:
- HJ cold call: SBR≥25（開放レイズゾーン以降のみ）
- CO/BTN cold call: SBR≥17 も有効

### B-2. BB の MW 効果 @SBR=25

**UTG open (R2.1) への BB 参加率**:

| シナリオ | BB 平均参加率 | 低下量 |
|---------|-------------|--------|
| HU (vs UTG only) | 82.1% | — |
| vs UTG + BTN cold call | ≈78% | -4% |
| vs UTG + CO cold call | ≈78% | -4% |
| vs UTG + HJ + CO cold calls | **60.4%** | **-21.7%** |

**MW で fold に転じる手（HU では参加、UTG + HJ+CO では fold）**:
- Ax offsuit 弱 (A2o–A9o): 全折れ
- Qx offsuit (Q5o–QJo): 全折れ
- Kx offsuit 弱 (K4o–K9o): 大部分折れ
- Jx offsuit 弱 (J7o–J9o): 全折れ
- T7o, T8o: 折れ
- suited 低キッカー (T2s, T3s, J2s, 72s): 折れ

**ルール**: BB MW Level 1（cold caller 2人+以上）では、弱いオフスーツ全般を fold。

BB 3-bet サイズも拡大: HU = R7.5 → MW(2 callers) = R8.6（スクイーズ効果）。

### B-3. BTN の MW cold call @SBR=25

**BTN 参加率（UTG open 後）**:

| シナリオ | BTN 平均参加率 | BTN actions |
|---------|-------------|------------|
| vs UTGo + HJc (3-way) | 16.9% | F, C, R7.1, RAI |
| vs UTGo + COc (3-way) | 17.7% | F, C, R7.1, RAI |
| vs UTGo + HJc + COc (4-way) | **9.8%** | **F, R7.5, RAI** |

**重要**: 4-way ではアクションが `['F', 'R7.5', 'RAI']` のみ = **cold call 不可**。fold か squeeze のみ。

**MW で BTN が折れる手**:
- JTs: 3-way では 85-92%、4-way では 0%
- T9s: 3-way では 54-64%、4-way では 0%
- 98s: 3-way では 33-39%、4-way では 0%
- 77: 3-way では 100%、4-way では 6%
- QJs: 3-way では 100%、4-way では 34%
- AJo: 3-way では 63-82%、4-way では 0%

**ルール**:
- 3-way（cold caller 1人）: BTN は 22+ と premium Broadway のみ参加
- **4-way（cold callers 2人）: BTN は cold call 不可。fold か squeeze (AAs+, 大 SC) のみ**

### B-4. CO の MW 参加（UTG open + HJ cold call）@SBR=25

`CO_vs_UTGo_HJc` actions: ['F', 'C', 'R7.3', 'RAI'] — CO は cold call オプションあり。

---

## C. MTTMRonlyGeneral vs MTTGeneral（SB limp 比較）

### C-1. MTTMRonlyGeneral の特徴

- actions: `['F', 'R2(or R2.1)', 'RAI']` — limp (C) なし
- SBR 8-25 で全 18 シナリオ × 7 SBR = 126ファイル収集済み

**UTG_RFI**: MTTGeneral と MTTMRonlyGeneral で差異なし（SBR=25）。UTG は limp しないため。

### C-2. SB_RFI での差異 @SBR=25

| MTTGeneral actions | ['F', 'C', 'R3', 'RAI'] | SB は R3 (3BB) にオープン |
|---|---|---|
| MTTMRonlyGeneral actions | ['F', 'R3', 'RAI'] | limp なし |

**MTTGeneral SB の limp-or-raise 分布**:

| 手 | MTTGeneral | MTTMRonlyGeneral |
|---|---|---|
| QJs | 100% limp | 100% raise (R3) |
| 76s | 100% limp | 100% raise |
| 65s | 100% limp | 100% raise |
| 77 | 51% limp, 49% raise | 100% raise |
| AKo | 64% limp, 36% raise | 100% raise |
| AQo | 85% limp, 15% raise | 100% raise |
| AKs | 100% raise | 100% raise (同じ) |
| A2o | 76% limp, 16% push | 100% push |
| JJ-TT | 10-12% limp | 100% raise |

**結論**: MTTGeneral の SB は「中スーテッド SC (65s, 76s) + ブロードウェイ弱オフスーツ (AKo, AQo)」を limp trap として使う。MRonly ではこれらが強制的に raise またはなくなる。

### C-3. MTTMRonlyGeneral の使用用途

MTTMRonlyGeneral は「Classic（アンテなし）」の代替ではなく、
「**SB limp が禁止された世界**」= limp trap 効果の検証用データ。

書籍での活用: 「SB リンプ戦略の Why」を説明する際に「MRonly では全部 raise になる」と対比できる。

---

## D. 次のステップ

- [x] Phase 1/2: 162ファイル（完了）
- [x] Phase 5 MW: 20ファイル（SBR=25/40、open-raise シナリオのみ）
- [x] MTTMRonlyGeneral: 126ファイル（SBR 8-25）
- [ ] Phase 5 limp pot: SBR≤20 での収集（次トークン）
- [ ] Phase 3 ICM: 上位プランへのアップグレードが必要
- [ ] Phase 4 Classic: 上位プランへのアップグレードが必要
- [ ] 分析スクリプト `verify_formula_tournament.py` の実装
- [ ] MTT 版閾値表のドラフト
