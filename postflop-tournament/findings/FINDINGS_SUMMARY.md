# GTO Wizard MTT調査 — 実測結果サマリー

**調査日**: 2026-05-19  
**使用gametype**: `MTTGeneral`（8-max, Chip-EV）  
**preflop action形式**: `F-F-F-F-F-{raise}-F-C`（8-max、5folds→BTN→SB→BB）  
**SB vs BB**: `F-F-F-F-F-F-R3-C`（6folds→SB R3→BB C）

---

## 発見1: BTN CBet frequency（BTN vs BB SRP、BBチェック後のBTN戦略）

BTNはIP（位置優位）。BBがOOPでcheckした後のBTNのbet/check頻度。

| SBR（depth） | 型1 Ks7d2c (High Dry) | 型2 Qh8d3s (High Wet) | 型4 Th9s8d (Low Connected) |
|------------|---------------------|---------------------|--------------------------|
| SBR60 (60.125) | CBet **97.5%** (Check 2.5%) | CBet **87.0%** (Check 13.0%) | CBet **60.0%** (Check 40.0%) |
| SBR40 (40.125) | CBet **91.0%** (Check 9.0%) | CBet **87.7%** (Check 12.3%) | CBet **49.9%** (Check 50.1%) |
| SBR25 (25.125) | CBet **79.9%** (Check 20.1%) | CBet **70.2%** (Check 29.8%) | CBet **67.6%** (Check 32.4%) |
| SBR20 (20.125) | CBet **68.6%** (Check 31.4%) | CBet **57.3%** (Check 42.7%) | CBet **72.3%** (Check 27.7%) |

### BTN CBetサイズ分布（代表値、depth=25.125）

| ボード型 | 主なbet size | 頻度 |
|---------|-----------|-----|
| 型1 K72 | R1.15 (約33%pot) | 68% |
| 型2 Q83 | R1.15 (約33%pot) | 52% |
| 型4 T98 | R1.9 (約50%pot) + R3.15 (約100%pot) | 混合 |

### 考察

1. **型1（ハイドライ）は最も高いCBet頻度**: SBR60で97.5%。小ベット（33%pot）主体。
2. **型4（ローコネクテッド）はCBet頻度が低い**: SBR40でほぼ50%チェック。打つときは大ベット（50%〜100%pot）。
3. **浅いSBRほど型1/型2のCBetが減少**: SBR20では型2が57%まで低下（SPR浅くリスク増大）。
4. **型4はSBRによる単調な変化なし**: ローコネクテッドはSPRに関係なくチェック頻度が高い。

---

## 発見2: SB vs BB SRP（SBがOOP先手、SBのフロップ戦略）

SBはpreflop raiser（R3=3BB）、BBはcall。フロップでSBが先手（OOP）。

| ボード型 | Check | Bet小(R1=33%pot) | Bet中(R2=66%pot) | Bet大(R3.15=100%pot) |
|--------|-------|----------------|----------------|-------------------|
| 型1 K72 | 53.1% | 12.6% | 22.0% | 9.9% |
| 型2 Q83 | 54.9% | 12.5% | 15.7% | 10.4% |
| 型4 T98 | 59.2% | 9.5% | 10.5% | 11.3% |

### 考察

- SBはBTNより「先手ベット」が多い（BTN vs BBではBBがほぼ100%チェック）
- 型1でもSBのCheck頻度は53%（BTNの20%より大きい）→ OOPのため慎重
- 全型でSBのBet頻度は40〜47%（BTNのCBet率より低い）

---

## 調査制約事項

### GTO Wizard APIの制限で取得できなかったデータ

1. **ICM補正後のpostflop**: `MTTGeneral_ICM*` gametypeはpostflopソリューションが非公開（PERMISSION_DENIED または HTTP 204）。ICM補正値はtoc.mdの仮設値（+3〜5%中盤、+10〜15%バブル）を採用。

2. **マルチウェイpostflop**: CO open → BTN call → BB callの3wayフロップは未収録（HTTP 204）。

3. **9-max ICMのSRP**: `MTTGeneral_ICM9m200PTPCT25`はUTG/3BPシナリオのみ（SRPは未収録）。

4. **SBR10以下のpostflop**: depth=10.125はpreflop action treeでraise optionなし（push/fold境界、SRP非適用）。

---

## 推奨改訂箇所（toc.md → 章への反映）

### CBet基準（実測に基づく修正）

**現行toc.md**:
- 型1: T3CBet可能（エアーも可）
- SPR<5では型1/6でもエアーCBetなし

**実測結果の示唆**:
- 型1 SBR25: CBet79.9%（チェック20.1%）→ 頻繁にCBetが正解
- 型1 SBR20: CBet68.6% → SPR≈6でも高頻度CBetが標準
- 型4 SBR25: CBet67.6%, CheckでもOK（50%以上がbet/checkの混合）

**修正案**: 「SPR<5で型1エアーCBetなし」は正確ではない可能性。型1のCBet頻度はSBR20でも68%あり、エアーCBetが完全になくなるわけではない。ただし浅いSBRでは「コミット判断をしてからCBet」の判断フローが重要。

### SB vs BB OOP戦略の追記

SBがOOPで先手する場合のフロップ戦略（第7章・バブル等で言及可能）:
- SBはBTNほど積極的にCBetしない（OOPのため）
- Check頻度53〜59%が標準
- 打つ時は小〜大ベットを混合（型1/2より型4の方がラージベット比率高い）

---

## 生データファイル

- `findings/phase1_btn_bb_srp.jsonl` — BB初動チェック頻度（SBR4段階×ボード3種）
- `findings/phase1_btn_cbet.jsonl` — BTN CBet戦略（SBR4段階×ボード3種）
- `findings/phase2_icm_stages.jsonl` — ICMステージ比較（Chip-EVのみ取得成功）
