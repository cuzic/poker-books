# poker-drill HandScore + 役割マッピング 調査レポート

実施日: 2026-05-05

`/home/cuzic/poker-drill/` の HandScore 関連箇所を全数 survey した結果。
新スケール (0-100 equity %) への移行で UI コンポーネントの更新が必要な箇所を特定。

## 1. 計算コア (calc.py) - Agent K で対応中

```
/home/cuzic/poker-drill/scripts/generate/core/calc.py
  - _ROLE_SCORE 辞書 (旧 0-30 → 新 0-100)
  - calc_hand_score / calc_river_hand_score
  - _hand_bucket (≥14/≥7 → ≥65/≥35)
  - calc_river_vmb_bucket (≥18/≥10 → ≥70/≥35)
  - calc_back_score (旧 -3-C → 新 -C-M)
  - ip_float_decision (≥18 → ≥70)
```

## 2. UI コンポーネント (要更新)

### 2-1. FlopCardBacks.tsx (1900+ 行)

**役割 → HS 範囲のマッピング (lines 203-208)** ★最重要
```typescript
const ROLE_HS_RULE: Record<string, string> = {
  "攻める":           "HS ≥ 18（強）",        // → "HS ≥ 70（強）"
  "ショーダウンバリュー": "7 ≤ HS < 18（中）",   // → "35 ≤ HS < 70（中）"
  "守る":             "5 ≤ HS < 14（中下）",   // → "30 ≤ HS < 65（中下）"
  "捨てる":           "HS < 5（弱）",          // → "HS < 30（弱）"
};
```

**判定セルでの閾値 (line 612)**
```typescript
cond: "上記以外（HS < 7）"  // → "上記以外（HS < 35）"
```

**精密 HS の境界 (lines 1273-1283)**
```typescript
const typeCorr = afterDrawBlocker >= 14 ? ... : 0;  // → >= 65
const preciseBucket: "H1" | "H2" | "H3" = preciseHS >= 14 ? "H3" : preciseHS >= 7 ? "H2" : "H1";
// → preciseHS >= 65 ? "H3" : preciseHS >= 35 ? "H2" : "H1"
const baseBucket = baseHS >= 14 ? "H3" : baseHS >= 7 ? "H2" : "H1";  // 同上
```

**メイドハンド判定 (line 2164)**
```typescript
const isMade = roleScore >= 30;  // → roleScore >= 80 (Set+ / Flush+ / Straight+)
```

### 2-2. TurnRiverCardBacks.tsx

**後手スコア閾値 (lines 81-83)** ★最重要
```typescript
{ range: "8以上",  ... match: score >= 8 },     // → "40以上", >= 40
{ range: "0〜7",   ... match: score >= 0 && score < 8 }, // → "20〜39", >= 20 && < 40
{ range: "0未満",  ... match: score < 0 },       // → "20未満", < 20
```

**ナッツ判定 (line 692)**
```typescript
const isNuts = handScore >= 30;  // → >= 88 (Set+ / Flush+ / FH+)
```

**CBet 判定 (line 854)**
```typescript
const isCbet = handScore >= 18;  // → >= 70 (TPTK 以上)
```

**バレルスコア + HS 連携 (line 1063-1065)**
```typescript
const turnJudge = barrelScore >= 7
  ? "積極バレル"
  : handScore >= 18  // → >= 70
  ? ...
```

**V/M/B 分類 (line 1174)**
```typescript
if (hs >= 18) return "V";  // → >= 70
```

**HS 説明文 (lines 719, 1325-1326)**
```typescript
HS≥30（セット/フラッシュ/ストレート）→ OB検討局面  // → HS≥85（...）
{ cond: "HS ≥ 30（セット / フラッシュ / ストレート）?", ...,
  match: handScore >= 30 && bucket === "V" }  // → >= 85
{ cond: "HS 18〜29（TPTK / 2ペア / OP）?", ...,
  match: handScore >= 18 && handScore < 30 && bucket === "V" }  // → 70〜84
```

**V バケツ説明 (line 1617)**
```typescript
<span>✓ V バケツ（HS ≥ 18）→ CR トリガー</span>  // → HS ≥ 70
```

**H3 説明 (line 1874)**
```typescript
<span>✓ H3（HS ≥ 14）のメイドハンドが最も効果的</span>  // → HS ≥ 65
```

**Action 判定 (line 1701)**
```typescript
const action = score >= 8 ? "CR" : score >= 0 ? "CALL" : "FOLD";  // → >= 40 / >= 20 / < 20
```

**バケツ表示 (line 1783)**
```typescript
bucket={riverHs >= 18 ? "H3" : riverHs >= 7 ? "H2" : "H1"}  // → >= 65 / >= 35 / < 35
```

### 2-3. その他

```
src/components/Common/VerifyChecklist.tsx: HS 表示（数値直接、閾値なし）
src/core/glossary.ts:                       用語定義 (HS の概念説明)
src/core/bookRef.ts:                        書籍参照
```

## 3. データファイル (TypeScript card data)

```
src/data/*-cards.ts (22 デッキ):
  - 各カードの "score" フィールド (旧 0-30 値)
  - "label" / "bucket" / "backScore" 等
  - generator から再生成される (手編集禁止)
  → calc.py 更新後、各 generator 実行で自動更新
```

## 4. 型定義 (types.ts) - 変更不要

```typescript
backScore?: number;
handScore?: number;
score: number | null;
threshold: number | null;
```

型は number のため、値の範囲が 0-30 → 0-100 になっても影響なし。

## 5. テスト (E2E + smoke)

```
src/components/CardFlip/__tests__/RiverDefenseBack.e2e.test.tsx
src/components/CardFlip/__tests__/TurnCbetBack.e2e.test.tsx
src/components/CardFlip/__tests__/TurnBack.e2e.test.tsx
src/components/CardFlip/__tests__/BeginnerVerifiability.smoke.test.tsx
+ 約 17 テストファイル
```

期待値の更新が必要 (旧スケール値 → 新スケール値)。

## 6. UI 更新作業まとめ

### Phase 3.5 #314 (UI コンポーネント) で対応する箇所:

**FlopCardBacks.tsx (約 8 箇所)**:
- ROLE_HS_RULE (lines 205-208) ← 文字列変更
- 判定セル "HS < 7" (line 612) ← "HS < 35"
- precise HS 境界 (lines 1273-1283) ← 14 → 65, 7 → 35
- メイド判定 (line 2164) ← 30 → 88

**TurnRiverCardBacks.tsx (約 12 箇所)**:
- 閾値 8 → 40 (lines 81-83, 1701)
- 閾値 18 → 70 (lines 692, 854, 1065, 1174, 1326, 1617)
- 閾値 30 → 85 (lines 692, 719, 1325)
- 閾値 14 → 65 (line 1874)
- バケツ判定 (line 1783)

**説明文の数値も更新必要**:
- "HS ≥ 18" 等の表記を文字列で含む箇所
- worked example 風の数値表示

### 推奨: sed-based 置換ではなく、手動レビュー + Edit
- 数字単独 (`>= 18`) は他の意味でも使われる (例: `kicker >= 12`)
- 役割ラベル "攻める/守る/捨てる/SDV" は維持
- バケツラベル "H1/H2/H3" は維持

## 7. テスト更新

```
expect(score).toBe(15)  // 旧 → expect(score).toBe(62) // 新 (TPGK)
expect(bucket).toBe("H3")  // 不変
expect(judgment).toBe("CR")  // 不変
```

各テストファイルで具体的な数値期待値が変わる。約 50-100 件想定。

## 8. 結論

### 移行作業量

| ファイル | 変更箇所 | 難易度 |
|---|---:|---|
| calc.py (Python) | 50+ 行 | 中 (Agent K 担当中) |
| FlopCardBacks.tsx | 8 箇所 | 低 (sed 不可、Edit で個別) |
| TurnRiverCardBacks.tsx | 12 箇所 | 低 |
| データ生成 (22 デッキ) | 自動 | 低 (generator 実行のみ) |
| E2E テスト (17 ファイル) | 50+ 期待値 | 中 |

### 影響範囲

- **計算ロジック**: calc.py 1 ファイル中央集権
- **UI 表示**: 2 主要ファイル + 約 20 箇所
- **データ**: ジェネレータ駆動で自動再生成
- **テスト**: 期待値更新

### 順序

```
1. calc.py 完了 (Agent K)
2. データ再生成 (#312, #313)
3. UI コンポーネント更新 (#314)
4. テスト更新 + ビルド (#315)
```

## 9. 役割マッピング → 新スケール対応の早見表

```
旧スケール (0-30):
  攻める:           HS ≥ 18 (強)
  ショーダウンバリュー: 7 ≤ HS < 18 (中)
  守る:             5 ≤ HS < 14 (中下)
  捨てる:           HS < 5 (弱)

新スケール (0-100 equity %):
  攻める:           HS ≥ 70 (TPTK 以上)
  ショーダウンバリュー: 35 ≤ HS < 70 (TPGK / セカンドペア相当)
  守る:             30 ≤ HS < 65 (TPMK / TPWK / アンダーペア)
  捨てる:           HS < 30 (役なし / ハイカード)

簡略変換: 新スケール ≈ 旧スケール × 4 + 補正
```
