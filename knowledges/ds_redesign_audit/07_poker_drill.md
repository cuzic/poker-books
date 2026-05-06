# 調査07: poker-drill アプリの HandScore 依存調査

実施日: 2026-05-05

## ファイル構成

```
/home/cuzic/poker-drill/
├── scripts/generate/         ← Python ジェネレータ（カードデータ生成）
│   ├── core/
│   │   ├── calc.py           ← HandScore 計算ロジック (★最重要)
│   │   ├── builder.py        ← カードビルド
│   │   └── recorder.py       ← データ記録
│   ├── flop_cbet.py / flop_cbet_3bp.py / ...   ← 各デッキ生成
│   ├── turn_cbet.py / turn_defense.py / ...
│   └── river_first.py / river_alpha.py / ...
├── src/
│   ├── data/*-cards.ts       ← generator から再生成（手編集禁止）
│   ├── core/cards/types.ts   ← TypeScript 型定義
│   └── components/CardFlip/  ← UI コンポーネント
```

## HandScore 計算のコア (`scripts/generate/core/calc.py`)

### 役スコア表 (`_ROLE_SCORE`)

```python
_ROLE_SCORE: dict[str, int] = {
    "set_plus":           30,
    "two_pair":           18,
    "overpair":           20,
    "tptk":               18,
    "tpgk":               15,
    "tpmk":                8,
    "tpwk":                6,
    "second_pair_strong":  9,
    "second_pair_weak":    3,
    "underpair":           6,
    "bottom_pair":         4,
    "air":                 0,
}
```

書籍の役スコアと**完全一致**している。

### 主要関数

| 関数 | 機能 |
|---|---|
| `calc_hand_score(hand, board)` | HandScore = 役スコア + ドロー加点 |
| `calc_hand_score_detail(hand, board)` | HandScore の内訳付き |
| `calc_river_hand_score(hand, board5)` | リバー版（ドロー加点 = 0） |
| `calc_river_vmb_bucket(score)` | リバー V/M/B 分類 |
| `calc_back_score(hs, a, c, m)` | 後手スコア = HS + A − 3 − C − M |
| `_hand_bucket(score)` | H1/H2/H3 分類（境界 ≥7 / ≥14） |
| `ip_float_decision(hs, bucket)` | IP フロート判断 |

### ハードコード閾値

```python
def _hand_bucket(score: int) -> str:
    if score >= 14:
        return "H3"
    if score >= 7:
        return "H2"
    return "H1"

def calc_river_vmb_bucket(hand_score: int):
    if hand_score >= 18:
        return "V"
    if hand_score >= 10:
        return "M"
    return "B"
```

## TypeScript 側

### 型定義 (`src/core/cards/types.ts`)

```typescript
backScore?: number;          // 後手スコア（数値）
handScore?: number;
handCategory?: string;       // 役分類
```

### UI コンポーネント

- `src/components/CardFlip/FlopCardBacks.tsx`: HandScore 表示・ブレイクダウン
- `src/components/CardFlip/TurnRiverCardBacks.tsx`: ターン・リバー HandScore 表示
- `src/screens/ExamScreen/ExamScreen.tsx`: 試験画面

これらは **Python から生成された値を表示するだけ** で、計算ロジックは持たない。

### カードデータ (`src/data/*-cards.ts`)

generator から再生成される（**手編集禁止**）。各カードの `score`, `bucket`, `backScore` などを保持。

```typescript
{
  "score": 15.0,           // HandScore (旧スケール 0-30)
  "label": "H3",
  ...
}
```

## デッキ別ファイル数

| デッキ | カードデータ | 生成スクリプト |
|---|---|---|
| preflop_open | preflop-formula-cards.ts | preflop_open.py |
| preflop_3bet | preflop-3bet-cards.ts | preflop_3bet.py |
| preflop_4bet | preflop-4bet-cards.ts | preflop_4bet.py |
| preflop_call | preflop-call-cards.ts | preflop_call.py |
| preflop_squeeze | preflop-squeeze-cards.ts | preflop_squeeze.py |
| preflop_memory | preflop-memory-cards.ts | -（手書き） |
| flop_cbet | flop-cbet-cards.ts | flop_cbet.py |
| flop_cbet_3bp | flop-cbet-3bp-cards.ts | flop_cbet_3bp.py |
| flop_cbet_4bp | flop-cbet-4bp-cards.ts | flop_cbet_4bp.py |
| flop_cbet_multiway | flop-cbet-multiway-cards.ts | flop_cbet_multiway.py |
| flop_donk | flop-donk-cards.ts | -（手書き） |
| flop_multiway | flop-multiway-cards.ts | flop_multiway.py |
| flop_vs_cbet | flop-vs-cbet-cards.ts | flop_defense.py |
| flop_vs_cbet_3bp | flop-vs-cbet-3bp-cards.ts | flop_defense_3bp.py |
| flop_vs_cbet_3bp_oop | flop-vs-cbet-3bp-oop-cards.ts | flop_defense_3bp_oop.py |
| flop_vs_cbet_4bp | flop-vs-cbet-4bp-cards.ts | -（手書き） |
| turn_cbet | turn-cbet-cards.ts | turn_cbet.py |
| turn_cbet_3bp | turn-cbet-3bp-cards.ts | turn_cbet_3bp.py |
| turn_defense | turn-defense-cards.ts | turn_defense.py |
| river_first | river-first-cards.ts | river_first.py |
| river_alpha | river-alpha-cards.ts | -（手書き） |
| river_defense | river-defense-cards.ts | river_defense.py |

**全 22 デッキ**のうち generator-driven は 17 デッキ、手書き 5 デッキ。

## スケール変更時の作業項目

### A. Python ジェネレータ側（`calc.py` を中心に書き換え）

1. `_ROLE_SCORE` を新スケールへ
2. ドロー加点を「アウツ × 2」ベースへ
3. `_hand_bucket` 閾値の更新（≥14 → equity ベース）
4. `calc_river_vmb_bucket` 閾値の更新
5. `calc_back_score` の C/A/M 値の更新
6. `ip_float_decision` の閾値更新

### B. データ再生成

```
17 デッキの generator を回す:
  python scripts/generate/flop_cbet.py
  python scripts/generate/flop_cbet_3bp.py
  ...
```

ジェネレータが出力する `*-cards.ts` を全て再生成。手編集禁止のため**ジェネレータ側で完結**する設計。

### C. 手書きデッキの値更新

5 デッキ（preflop_memory / flop_donk / flop_vs_cbet_4bp / river_alpha / その他）は手編集が必要。

### D. UI 表示の閾値判定

`FlopCardBacks.tsx`, `TurnRiverCardBacks.tsx` 内のハードコード閾値（≥18 で V、≥10 で M など）を新スケールに対応。

### E. テスト更新

`src/components/CardFlip/__tests__/*.e2e.test.tsx` の期待値を新スケール対応。

```
flop/__tests__/RiverDefenseBack.e2e.test.tsx
flop/__tests__/TurnCbetBack.e2e.test.tsx
flop/__tests__/TurnBack.e2e.test.tsx
flop/__tests__/BeginnerVerifiability.smoke.test.tsx
```

## 工数見積

| 作業 | 所要時間 |
|---|---|
| `calc.py` の役スコア・ドロー加点・閾値の書き換え | 4 時間 |
| 後手スコア式の C/A/M 値更新 | 1 時間 |
| 17 デッキのジェネレータ実行・データ再生成 | 30 分 |
| 5 手書きデッキの値更新 | 2 時間 |
| UI 閾値判定の更新（FlopCardBacks / TurnRiverCardBacks） | 2 時間 |
| テスト更新（約 4 ファイル） | 2 時間 |
| `bun run build` 確認・E2E テスト pass | 1 時間 |
| **合計** | **約 12.5 時間 (≒ 1.5 日)** |

## 結論

- HandScore 計算は `calc.py` 1 ファイルに集約 → **再設計の起点**
- 17 デッキは generator-driven のため再生成のみ → **データ作業は短時間**
- 手書き 5 デッキは個別更新が必要
- UI コンポーネントは値表示のみのため **計算変更の影響は限定的**
- E2E テストの期待値更新が必要

**poker-drill 側の作業: 1.5 日**で完了可能。書籍側の Phase 3 と並行で進められる。
