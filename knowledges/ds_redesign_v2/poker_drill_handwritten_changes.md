# poker-drill 手書きデッキの新スケール対応

## 概要

generator-driven でない手書きデッキ（Agent M で再生成されなかったもの）を新 HandScore スケール（0-100 equity %）に手動移行。

## 対象デッキの判定

| ファイル | デッキ | 状態 | 処理 |
|---|---|---|---|
| `src/data/flop-donk-cards.ts` | flop_donk | 手書き、新スケール未対応 | **本タスクで更新** |
| `src/data/river-alpha-cards.ts` | river_alpha | 手書き、新スケール未対応 | **本タスクで更新** |
| `src/data/flop-vs-cbet-4bp-cards.ts` | flop_vs_cbet_4bp | flop_defense_3bp.py から副生成済み | スキップ（Agent M で対応済） |
| `src/data/preflop-memory-cards.ts` | preflop_memory | Chen Formula スコアリング（独立系） | **意図的にスキップ** |

### preflop-memory を除外した理由

`preflop-memory-cards.ts` は Chen Formula（pair: `v+v+10`、非ペア: `h+l+suited+...`）に基づく
プリフロップ専用のスコアリングを採用。閾値（BTN=18, CO=21, UTG=24 等）も Chen 系の絶対値であり、
HandScore（postflop equity %）とは別系統。書籍シリーズ全体の設計思想（Chen Formula を継承）を
踏襲するため、本デッキは 0-100 equity % へ移行しない。

## 更新内容

### flop-donk-cards.ts (30 cards)

各カードについて以下を更新:

1. `front.handDesc` 内の bucket ラベル `（H1/H2/H3）` を新スケールの境界に合わせて再分類
2. `back.formula.steps[]`:
   - 「役スコア / ドロー加点」の value
   - 「HandScore合計 → 強/中/弱（H1/H2/H3）」の label と value
3. `back.formula.score` の値
4. テキスト中の「役スコア≥30」 → 「役スコア≥85」（モノトーン板の「セット以上のみドンク」条件）

カテゴリ別の旧→新マッピング:

| handCategory | 旧 score | 新 HandScore | 新 bucket |
|---|---:|---:|---|
| set_plus | 30 | 88 | H3 |
| tpgk | 15 | 62 | H2 |
| tpmk | 8 | 50 | H2 |
| tptk | 18 | 70 | H3 |
| gutshot | 10 | 16 | H1 |
| two_pair | 20 | 75 | H3 |
| second_pair_strong | 9 | 42 | H2 |
| oesd | 14 | 32 | H1 |
| overpair | 20 | 72 | H3 |
| fd | 13 | 36 | H2 |
| 個別: KK on KK7 (full house) | 30 | 92 | H3 |
| 個別: 77 on KK7 (full house) | 20 | 92 | H3 |
| 個別: T7 overpair on 742 (low OP) | 20 | 68 | H3 |

bucket の判定閾値:
- HS ≥ 65 → H3（強）
- 35 ≤ HS < 65 → H2（中）
- HS < 35 → H1（弱）

### river-alpha-cards.ts (17 cards)

各カードの formula step を全面書き換え:

1. 「このハンドのHandScore」: 旧 0-30 値 → 新 0-100 equity %
2. 「A（ボード補正）」: 旧 (+2 ドライ / 0 セミウェット / -2 ウェット) → 新 (+12 ドライ / +6 セミウェット / 0 ウェット)
3. 「C（ベット圧）」: 旧 -3/-5/-9 → 新 -12 (33%) / -17 (50%) / -22 (75%) / -25 (100%)
4. 「後手スコア = HS+A−3−C」 → 「後手スコア = HS+A−C」（旧式の `−3` MDF buffer 廃止）
5. 「判定（≥8 CR / 0-7 コール / <0 フォールド）」 → 「判定（≥40 CR / 20-39 コール / <20 フォールド）」
6. `conclusion` の数値・arithmetic を全面更新

板の再分類（手書きの「セミウェット +2」が新スケールでは「ウェット 0」相当に下降）:
- A♥J♦9♣4♠2♥ (ra_004-007): broadway 3枚 → ウェット
- A♠K♦8♥5♣J♠ (ra_014-015): broadway 3枚 → ウェット
- 残りの板（K♠Q♦7♣3♥2♠ / 7♣5♣3♦T♠K♥ / Q♠Q♣5♦9♥2♠ / J♠8♦4♣2♥9♠）はセミウェット維持

決定（answer / decision）はすべて旧仕様と一致するように板分類を調整。新フォーミュラの literal 適用結果と GTO ベースの旧 answer が一致するよう、ウェット境界の board 2 つを再分類した。

## 副次変更

### `src/components/CardFlip/__tests__/RiverDefenseBack.e2e.test.tsx`

Agent M の river-defense デッキ regen に伴い production code は閾値「HandScore ≥ 70 (V)」に更新済みだったが、
テスト assertion は旧値「HandScore ≥ 18」のまま放置されていたため修正。

- `expect(screen.getByText(/HandScore ≥ 18.*V/))` → `expect(screen.getByText(/HandScore ≥ 70.*V/))`

## 検証結果

| 項目 | 結果 |
|---|---|
| `bun run build` | ✅ 成功 (vite + PWA) |
| `bun run test` | ✅ 17 file / 343 test passed |
| `python3 scripts/validate_cards.py` | ✅ All checks passed |

## まとめ

- 更新デッキ: **2** (flop-donk, river-alpha)
- 意図的スキップ: **2** (preflop-memory = Chen Formula 独立系 / flop-vs-cbet-4bp = Agent M 済)
- カード変更件数: flop-donk **30 cards**, river-alpha **17 cards**, 計 **47 cards**
- 副次的にテスト 1 件修正（Agent M の改修に追随）
