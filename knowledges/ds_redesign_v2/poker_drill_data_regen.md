# poker-drill カードデータ再生成（新スケール 0-100）

## 概要

`/home/cuzic/poker-drill/scripts/generate/core/calc.py` の新スケール対応を受け、generator-driven な全 17 デッキ（および追加 1 ファイル）の `src/data/*-cards.ts` を再生成。

## 結果サマリ

- **再生成成功: 17/17 デッキ + flop-vs-cbet-4bp（flop_defense_3bp.py から副生成）**
- **`bun run build`: 成功**
- **calc 単体テスト: 全パス**

## Step 1: calc.py テスト

```
python3 scripts/generate/core/test_calc.py → ALL TESTS PASSED
```

## Step 2: generator 実行

| script | 出力ファイル | カード数 |
|---|---|---|
| preflop_open.py | preflop-formula-cards.ts | 25 |
| preflop_3bet.py | preflop-3bet-cards.ts | 25 |
| preflop_4bet.py | preflop-4bet-cards.ts | 24 |
| preflop_call.py | preflop-call-cards.ts | 19 |
| preflop_squeeze.py | preflop-squeeze-cards.ts | 16 |
| flop_cbet.py | flop-cbet-cards.ts | 21 |
| flop_cbet_3bp.py | flop-cbet-3bp-cards.ts | 15 |
| flop_cbet_4bp.py | flop-cbet-4bp-cards.ts | 12 |
| flop_cbet_multiway.py | flop-cbet-multiway-cards.ts | 18 |
| flop_multiway.py | flop-multiway-cards.ts | 15 |
| flop_defense.py | flop-vs-cbet-cards.ts | 24 |
| flop_defense_3bp.py | flop-vs-cbet-3bp-cards.ts (+ 4bp 6 cards) | 12 + 6 |
| flop_defense_3bp_oop.py | flop-vs-cbet-3bp-oop-cards.ts | 12 |
| turn_cbet.py | turn-cbet-cards.ts | 21 |
| turn_cbet_3bp.py | turn-cbet-3bp-cards.ts | 15 |
| turn_defense.py | turn-defense-cards.ts | 15 |
| river_first.py | river-first-cards.ts | 18 |
| river_defense.py | river-defense-cards.ts | 12 |

すべてのスクリプトが exit 0 で完了。

## Step 3: ビルド確認

```
bun run build → ✓ built in 880ms（PWA 含めて成功）
```

## Step 4: 値の整合性確認

### HandScore 範囲（新スケール 0-100）

| ファイル | 件数 | min | max | bucket 分布 |
|---|---|---|---|---|
| flop-cbet-cards.ts | 21 | 10 | 88 | H1:6, H2:8, H3:7 |
| flop-cbet-3bp-cards.ts | 15 | 20 | 88 | H1:8, H2:11, H3:23 |
| flop-cbet-4bp-cards.ts | 12 | 40 | 88 | H2:6, H3:18 |
| flop-cbet-multiway-cards.ts | 18 | 10 | 88 | H1:4, H2:18, H3:14 |
| flop-vs-cbet-cards.ts | 24 | 10 | 88 | (handScore field) |
| flop-vs-cbet-3bp-cards.ts | 12 | 40 | 91 | (handScore field) |
| flop-vs-cbet-3bp-oop-cards.ts | 12 | 40 | 88 | (handScore field) |
| flop-multiway-cards.ts | 15 | 10 | 88 | (handScore field) |
| turn-cbet-cards.ts | 21 | 10 | 100 | H1:14, H2:12, H3:22 |
| turn-cbet-3bp-cards.ts | 15 | 10 | 88 | H1:3, H2:5, H3:7 |
| turn-defense-cards.ts | 15 | 25 | 96 | H1:9, H2:27, H3:9 |
| river-first-cards.ts | 18 | 10 | 88 | (役スコア) |
| river-defense-cards.ts | 12 | 15 | 88 | (役スコア) |

### TPGK サンプル確認

- `flop-vs-cbet-cards.ts` fv_001: A♠7♦2♣ + A♥K♦ (TPGK) → `handScore: 62` 
- `flop-cbet-cards.ts` 先頭カード TPGK 相当: `score: 62.0`, `handDesc: "HandScore 62 → 中（H2）"`
- TPMK サンプル: K♠7♦2♣ + K♥9♦ (TPMK) → `handScore: 50`

### bucket 閾値確認

新閾値で正しくラベリングされている:
- HandScore 62 → 中（H2）
- HandScore 88 → 強（H3）
- HandScore 32 → 弱（H1）

## 失敗デッキ

なし。全 17 デッキ + 副生成 1 ファイルが新スケールで正常に再生成完了。
