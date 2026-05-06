# poker-drill calc.py 新スケール対応 変更点

実装日: 2026-05-05
対象: `/home/cuzic/poker-drill/scripts/generate/core/calc.py`
仕様根拠: `knowledges/ds_redesign_v2/SPEC_HANDSCORE.md` / `SPEC_OTHER_FORMULAS.md`

## 1. 概要

旧 0-30 スケールの HandScore を、equity % で読める新 0-100 スケール (v3) に全面移行。
関数シグネチャは変更せず、内部の値・閾値のみ更新 → UI / TS 型定義との互換は維持。

## 2. 変更ファイル

| ファイル | 行数 | 変更内容 |
|---|---:|---|
| `scripts/generate/core/calc.py` | 〜1100 (旧 1363) | 値・閾値・ストリート別ドロー加点 |
| `scripts/generate/core/test_calc.py` | 1442 | 期待値を新スケールに更新 |
| `scripts/input/situation04_turn_cbet_inputs.csv` | 23 | 3 行のバケット境界変動を反映 |

## 3. 主要関数別の変更

### 3.1 `_ROLE_SCORE` (役スコア辞書)

旧 0-30 → 新 0-100 (equity %)。

| role | 旧 | 新 |
|---|---:|---:|
| set_plus | 30 | 88 |
| two_pair | 18 | 78 |
| overpair | 20 | 75 |
| tptk | 18 | 70 |
| tpgk | 15 | 62 |
| tpmk | 8 | 50 |
| tpwk | 6 | 45 |
| second_pair_strong | 9 | 42 |
| second_pair_weak | 3 | 32 |
| underpair | 6 | 40 |
| bottom_pair | 4 | 32 |
| air | 0 | 15 (中央値、ハイカードで上書き) |

加えて air は `h_rank` でハイカード扱い:
- A 系 → 25 / K 系 → 20 / Q 系 → 15 / J 以下 → 10

### 3.2 完成役の絶対値

ストレート / フラッシュは `_MADE_STRAIGHT=82` / `_MADE_BROADWAY=85` / `_MADE_FLUSH=85` / `_MADE_NUT_FLUSH=90` の 4 定数で表現。
旧コードは全て 30 (= set_plus と同値) だった。

### 3.3 `_hand_bucket(score)` (3 バケツ分類)

```python
旧: ≥14 H3 / ≥7 H2 / else H1
新: ≥65 H3 / ≥35 H2 / else H1
```

### 3.4 `calc_river_vmb_bucket(score)`

```python
旧: ≥18 V / ≥10 M / else B
新: ≥70 V / ≥35 M / else B
```

### 3.5 `calc_back_score(hs, a, c, m)`

旧: `hs + a − 3 − c − m` (ベースライン -3 補正あり)
新: `hs + a − c − m` (-3 を A 値に吸収)

### 3.6 `back_score_judgment(score)` 閾値

```python
旧: ≥8 CR / ≥0 CALL / else FOLD
新: ≥40 CR / ≥20 CALL / else FOLD
```

### 3.7 `ip_float_decision(hs, bucket)` 閾値

```python
旧: H3 中 hs≥18 → RAISE, else FLOAT
新: H3 中 hs≥70 → RAISE, else FLOAT
```

### 3.8 `_C_COEFF_TABLE` (C 値)

| ベットサイズ | 旧 C | 新 C | α |
|---|---:|---:|---:|
| 33% | 3 | 12 | 0.250 |
| 50% | 4 | 17 | 0.333 |
| 75% | 6 | 22 | 0.429 |
| 100% | 9 | 25 | 0.500 |
| 150% | 11 | 30 | 0.600 |

### 3.9 `calc_a_coeff` 戻り値

| ボード | 旧 A | 新 A | label |
|---|---:|---:|---|
| ドライ | 3 | 12 | "ドライ" |
| セミウェット | 2 | 6 | "セミウェット" |
| ウェット | 1 | 0 | "ウェット" |

### 3.10 `calc_m_coeff(num_players)`

| 人数 | 旧 M | 新 M |
|---|---:|---:|
| 2 (HU) | 0 | 0 |
| 3 | 3 | 12 |
| 4+ | 6 | 22 |

### 3.11 ドロー加点 (ストリート別、Rule of 4 / 2)

新規導入: `_street_from_board(cards)` (3=flop, 4=turn, 5=river)
ストリートで multiplier 切替: flop=4 / turn=2 / river=0

```
FD (9 outs):  flop +36 / turn +18  (旧 +13 一律)
OESD (8):     flop +32 / turn +16  (旧 +12 一律)
GS (4):       flop +16 / turn +8   (旧 +6 一律)
FD+OESD (13): flop +52 / turn +26  (旧 +15 一律)
2 OC (6):     flop +24 / turn +12  (旧 +9 一律)
NFD nut blocker: 9*m + 5            (旧 +3 over plain FD)
Sub-NFD: 9*m + 3                    (旧 +2 over plain FD)
BDFD (固定):  flop +5 (turn 不適用) (旧 +4)
ナッツストレート blocker: +3        (旧 +2)
```

OESD on air は新スケールでも H3 lift (`max(role_score + draw_bonus, 65)`) で旧挙動を維持。

### 3.12 上限クランプ

`total > 100 → 100` を `calc_hand_score` / `calc_hand_score_detail` 末尾で適用。

### 3.13 BarrelScore 系列

`classify_board_type_for_turn` / `classify_turn_card` / `calc_barrel_score`
→ **旧スケール継続** (SPEC_OTHER_FORMULAS.md §3 「旧スケール継続」)。
FlopType: 8/6/4/3、TurnCard: 4/3/2/1/0、閾値 ≥7。

## 4. テスト結果

### 4.1 ユニットテスト

```
$ python scripts/generate/core/test_calc.py
ALL TESTS PASSED  (1065 PASS, 0 FAIL)
```

### 4.2 更新したテスト件数

- 値の置換 (`(1, "ウェット")` → `(0, "ウェット")` 等の A 値タプル): 約 25 箇所
- HandScore role アサーション: 16 箇所 (TPTK/TPGK/TPMK/TPWK/Set 等)
- ドロー加点アサーション: 8 箇所 (FD/OESD/コンボ/BDFD/Gutshot)
- バケット境界アサーション: 6 箇所
- C 値タプル: 5 箇所
- M 値: 4 箇所
- back_score 6 箇所、judgment 7 箇所
- river_vmb 8 箇所
- 完成役 (straight/flush) スコア: 6 箇所
- N-04 リグレッション: 1 箇所

### 4.3 CSV データ更新 (situation04)

旧スケールでは H3 だった以下 3 行が新スケールでは境界変動:

| 行 | hand | board | 旧 bucket / action | 新 bucket / action |
|---|---|---|---|---|
| 1 | KQ | K72-5h | H3 / CBET | H2 / CBET |
| 9 | A3o | T98-6c | H1 / CHECK | H2 / CHECK |
| 12 | J9 | J75-3h on connector turn | H3 / CBET | H2 / CHECK |

(action 変動 1 件 = J9 行: barrel=6<7 で H3 のみ CBet → 新スケールで H2 落ちで CHECK)

## 5. 互換性

### 5.1 関数シグネチャ

すべて変更なし。値だけが変わるため呼び出し側は無修正で動作。
- `calc_hand_score(hand_str, board_str) -> tuple[int, str]`
- `calc_hand_score_detail(...)` 返り値構造同じ
- `calc_back_score(hs, a, c, m) -> int` 同じ
- 全 calc_a/c/m_coeff、judgment 関数同じ

### 5.2 TS 型定義

`src/core/cards/types.ts` は変更不要 (HandScore 型は `number`)。
カードデータ (`src/data/*-cards.ts`) は generator 再実行で自動更新。

### 5.3 generator スクリプト

`scripts/generate/*.py` (flop_cbet, flop_defense, turn_defense, river_first 等
20 ファイル超) は無修正で動く。再実行時に新スケールでカードが生成される。

## 6. 残課題

1. **カードデータ (TS) の再生成**:
   `scripts/generate/run_all.sh` (or 個別 generator) を実行して `src/data/*-cards.ts` を新スケールで再生成する必要あり。
   特に `turn-cbet-cards.ts` の `formula.steps[4].value` の "HandScore 15" などは旧値のまま。

2. **他の CSV (situation01-20)** の `hand_bucket` / `expected_action` カラム:
   今回は situation04 のみ更新。同様の境界変動が他 CSV でも発生するため、generator 実行後の検証が必要。

3. **`scripts/verify/verify_all.py`** が旧閾値前提なら、新スケール対応の確認が必要。

4. **Air ハイカードの粒度**: 現実装は `h_rank` だけで A/K/Q/J 系を判定。
   `l_rank` も A 系だと `h_rank == 14 or l_rank == 14` で 25 にしているため整合的だが、
   今後 A-K 等の細分化が必要なら追加実装。

5. **絶対値の絶妙な調整**: SPEC_HANDSCORE.md §11 (4-flush ボード等) の
   特殊状況は未実装。Phase 2 後半で追加検討。

## 7. 検証コマンド

```bash
cd /home/cuzic/poker-drill
python scripts/generate/core/test_calc.py        # ユニットテスト
# → ALL TESTS PASSED (1065 PASS)
```
