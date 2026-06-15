# Flop v9b / River v15 公式拡張 (2026-06-05 確立)

## 概要

`scripts/three_class_model/dataset_unified.csv` (1.16M rows) に既存 Cash/MTT 公式 v8a/v10/v14 を適用、cell-level で境界 cell を特定。重大バグ 4 件と MTT 短スタック特有パターン 1 件を修正し v9b (flop) / v15 (river) を確立。

**検証スクリプト**: `scripts/three_class_model/mtt_formula_audit.py` (audit + v8a/v9b/v10/v14/v15 全公式の huge_loss / acc 比較)

**実装**: `scripts/three_class_model/flop_v9_test.py`, `river_v15.py`

## 改善サマリ

| street | 公式 | pot | 旧 huge_loss | 新 huge_loss | 削減 |
|--------|------|-----|-------------|--------------|------|
| Flop defense | v8a → v9b | **Cash100** | 0.241 BB | **0.061 BB** | **-75%** |
| Flop defense | v8a → v9b | **MTT100** | 0.380 BB | **0.129 BB** | **-66%** |
| Flop defense | v8a → v9b | MTT50 | 0.170 BB | 0.163 BB | -4% |
| Flop defense | v8a → v9b | MTT25 | 0.163 BB | 0.156 BB | -4% |
| Flop defense | v8a → v9b | other | 0.421 BB | **0.041 BB** | **-90%** |
| River defense | v14 → v15 | **Cash100** | 0.388 BB | **0.212 BB** | **-45%** |
| River defense | v14 → v15 | **MTT50** | 0.316 BB | **0.130 BB** | **-59%** |
| Turn defense (変更なし) | v10 | Cash100 / MTT50 | 0.048 / 0.067 BB | (据置) | — |

全体 (Cash + MTT defense):
- Flop: 0.267 → **0.134 BB** (-50%)
- River: 0.353 → **0.173 BB** (-51%)

## 発見されたバグ 4 件

### Bug 1: `river_bet_size()` substring 誤マッチ (重大、検証 script のバグ)

```python
# v14 / vol3_mtt_audit.py の元コード (BUG)
def river_bet_size(s):
    if "_R4" in s: return "small_30p"
    if "_R7" in s or "_R8" in s: return "med_75p"  # ← bug
    if "_R13" in s: return "med_100p"
    if "_R16" in s: return "overbet"
    if "_R89" in s or "_R35" in s: return "allin"
```

`_R89.6` は `_R8` を含むため早期に `med_75p` を返す → all-in 3569 行が誤分類。River v14 Cash100 acc が **70.6%** と低かった原因。

**修正**: 大きい順に判定する。
```python
if "_R89" in s or "_R35" in s: return "allin"  # 先に判定
if "_R16" in s: return "overbet"
if "_R13" in s: return "med_100p"
if "_R7" in s or "_R8" in s: return "med_75p"
if "_R4" in s: return "small_30p"
```

修正後 acc 70.6% → **82.3%**、huge_loss 1.559 → 0.388 BB。

### Bug 2: v14 `fullhouse × overbet → CALL` (実測 modal RAISE 96.5%)

```python
# v14 (BUG)
if mv == "fullhouse" and bs == "overbet": return "CALL"
```

dry_high × fullhouse × overbet 86 行で modal RAISE 96.5%, raise_freq 平均 0.965, ev_raise 平均 42 BB vs ev_call 33 BB。CALL は +9 BB の機会損失。**huge_loss 8.094 BB / acc 3.5%**。

**修正 (v15)**: fullhouse は overbet でも常 RAISE。
```python
if mv in {"quads", "fullhouse"}: return "RAISE"
```

修正後: huge_loss 8.09 → **0.06 BB**、acc 3.5% → **96.5%**。

### Bug 3: v14 broad `is_dyn × TP × weak/good → CALL`

```python
# v14 (BUG): monotone も DYNAMIC_RIVER に含まれるため引っかかる
if is_dyn and mv == "top_pair" and eb in {"weak_hands", "good_hands"}: return "CALL"
```

monotone × top_pair × allin × weak_hands 108 行で modal FOLD 94.4%, ev_fold +0.0 vs ev_call -55 BB。CALL は disaster。**huge_loss 7.541 BB / acc 5.6%**。

**修正 (v15)**: broad rule を削除。allin では `set/trips/straight/flush` のみ bucket good/best で CALL。TP は `dry_high/low_dry × overbet/med_100p` の bluff catcher case のみ CALL。

修正後: huge_loss 7.54 → **0.02 BB**、acc 5.6% → **94.4%**。

### Bug 4: v14 `dynamic × 2P × allin × good_hands` を FOLD と判定 (重大、MTT 特有)

v14 では `mv == "two_pair"` の allin spot は default FOLD (ABSOLUTELY_STRONG に含まれず)。しかし MTT50 dynamic × 2P × allin × good_hands 55 行で modal CALL 100%, ev_call **+31 BB** vs ev_fold 0。FOLD は 31 BB の損失。**huge_loss 20.109 BB**。

**修正 (v15)**: 2P を allin の強メイドハンドに追加。
```python
if bs == "allin":
    if mv in {"two_pair", "set", "trips", "straight", "flush"}:
        if eb in {"best_hands", "good_hands"}: return "CALL"
        if is_dry and mv in {"set", "trips", "straight", "flush"}: return "CALL"
        return "FOLD"
```

修正後 MTT50 huge_loss 0.316 → **0.130 BB**。

## v9b 拡張: AIR×BDFD×dry の depth 軸 + 短スタック CR

### Bug 5: v8a `no_made_hand × BDFD × dry → CALL` (Cash/MTT100 で modal FOLD)

```python
# v8a — dry/low_dry × WEAK_DRAW × AIR は default の CALL に落ちる
if mv in AIR:
    if dv == "no_draw": return "FOLD"
    if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
# (dry_high/low_dry は default CALL)
```

しかし実測:
- Cash100 dry_high × no_made × twocards_bdfd (n=452): modal **FOLD** 77.9%, huge_loss 1.369 BB
- MTT100 dry_high × no_made × twocards_bdfd (n=704): modal **FOLD** 61.2%, huge_loss 2.622 BB
- MTT25 同 cell: modal **CALL** 50%+ (短スタックは implied odds で防御)
- MTT50 同 cell: modal **CALL** 55%+

→ deep stack は FOLD、short stack は CALL という depth 依存パターン。

### 短スタック CR: `third_pair × dry × no_draw`

- MTT25 dry_high × third_pair × no_draw (n=1251): modal **RAISE 93.4%** (CR 戦略)
- MTT50 同 cell (n=1251): modal **RAISE 91.8%**
- Cash100 同 cell: modal **CALL 83.2%** (CR ではなく call で bluff catch)

v8a は **FOLD** を返す → MTT で huge_loss 2.06 BB。

### v9b 公式 (depth-aware)

```python
def _is_short_stack(r):
    """source_path から short stack (≤50bb) か判定。depth 列は preprocessing で欠損。"""
    p = str(r.get("source_path", "")).lower()
    if "mtt25" in p or "mtt50" in p: return True
    if "cash100" in p or "mtt100" in p or "mtt200" in p: return False
    depth_raw = r.get("depth", 100)
    try:
        depth = float(depth_raw) if pd.notna(depth_raw) else 100.0
    except (ValueError, TypeError):
        depth = 100.0
    return depth > 0 and depth <= 50


def flop_def_v9b(r):
    mv, dv, bf = r["mv_cat"], r["dv_cat"], r["board_family"]
    is_short = _is_short_stack(r)

    if mv in AIR:
        if dv == "no_draw": return "FOLD"
        if dv in WEAK_DRAW and bf in DYNAMIC_BOARDS: return "FOLD"
        if dv in WEAK_DRAW and bf in DRY_BOARDS and not is_short: return "FOLD"  # NEW

    if mv in {"low_pair", "third_pair"} and dv == "no_draw" and bf in DRY_BOARDS | {"dynamic_2tone"}:
        if is_short: return "RAISE"  # MTT 短スタック CR
        return "FOLD"

    if mv == "overpair": return "RAISE"
    return "CALL"
```

### v9b 効果 (cell 別)

| pot | bf | mv | dv | n | v8a huge | v9b huge |
|-----|-----|----|----|---|----------|----------|
| Cash100 | dry_high | no_made_hand | twocards_bdfd | 452 | 1.37 BB | **0.00 BB** |
| Cash100 | low_dry | no_made_hand | twocards_bdfd | 108 | 1.99 BB | **0.00 BB** |
| Cash100 | dry_high | ace_high | onecard_bdfd | 150 | 0.76 BB | **0.11 BB** |
| MTT100 | dry_high | no_made_hand | onecard_bdfd | 582 | 2.75 BB | **0.00 BB** |
| MTT100 | dry_high | no_made_hand | twocards_bdfd | 704 | 2.62 BB | **0.00 BB** |
| MTT100 | low_dry | no_made_hand | twocards_bdfd | 168 | 2.19 BB | **0.02 BB** |
| MTT25 | dry_high | third_pair | no_draw | 1251 | 2.09 BB | **0.52 BB** |
| MTT50 | dry_high | third_pair | no_draw | 1251 | 2.06 BB | **0.75 BB** |

## v15 完全コード (river)

```python
DYNAMIC = {"dynamic", "dynamic_2tone", "monotone"}
DRY = {"dry_high", "low_dry"}
ABSOLUTELY_STRONG = {"straight", "flush", "trips"}


def river_def_v15(r):
    eb = r["equity_bucket"]
    bs = r["bet_size"]
    mv = r["mv_cat"]
    eqp = r.get("eq_percentile")
    bf = r["board_family"]
    is_dry = bf in DRY

    # 1) nuts / fullhouse は常 RAISE (Bug 2 修正)
    if mv in {"quads", "fullhouse"}: return "RAISE"

    # 2) vs allin
    if bs == "allin":
        # 2P を強メイドに追加 (Bug 4 修正)
        if mv in {"two_pair", "set", "trips", "straight", "flush"}:
            if eb in {"best_hands", "good_hands"}: return "CALL"
            if is_dry and mv in {"set", "trips", "straight", "flush"}: return "CALL"
            return "FOLD"
        if eb == "best_hands" and pd.notna(eqp) and eqp > 0.85: return "CALL"
        if bf == "monotone" and mv == "flush": return "CALL"
        # broad TP × weak/good → CALL を削除 (Bug 3 修正)
        return "FOLD"

    # 3) ABSOLUTELY_STRONG (non-allin)
    if mv in ABSOLUTELY_STRONG:
        if eb == "trash_hands" and bs == "overbet": return "FOLD"  # dominated straight
        return "CALL"

    # 4) TP × dry × overbet/med_100p → CALL (bluffcatcher)
    if mv == "top_pair" and is_dry and bs in {"overbet", "med_100p"}: return "CALL"

    # 5) bucket fallback
    if eb == "best_hands":
        if pd.notna(eqp) and eqp > 0.96: return "RAISE"
        return "CALL"
    if eb == "good_hands": return "CALL"
    if eb == "weak_hands":
        if bs == "overbet":
            if bf in DYNAMIC and mv == "two_pair": return "CALL"
            return "FOLD"
        if bs == "med_100p": return "FOLD"
        return "CALL"
    return "FOLD"
```

## 残る境界 cell (v9b/v15 でも huge_loss > 0.3 BB)

185 件中、特に高 huge_loss が残るパターン:

**Flop (v9b 後)**:
- MTT25/50 で第三層公式適用後も `third_pair × dry × no_draw` で 0.5-0.75 BB 残る
  - データ修正済だが、RAISE 戦略の細部 (size, board 具体性) を捉えきれていない
- MTT25 で `low_pair × low_dry × no_draw` (n=300) huge_loss ~0.5 BB

**River (v15 後)**:
- `dynamic × straight × overbet × dynamic` (n=1030): huge_loss 1.32 BB
  - 一部 dominated straight の存在、blocker effect の細部
- `dynamic × 2P × med_100p` (n=259): huge_loss 0.72 BB
- `dry_high × 2nd pair × overbet`: huge_loss 0.87 BB

これらは追加データ (Phase B fetch) ではなく **公式の微細化** が必要 (例: straight × overbet × dominated → FOLD ルール、kicker / blocker 軸の導入)。

## データ補強の進捗

- **R1 Cash 6m river allin defender**: 62 spots 取得完了 (2026-06-05、task #1 完了)
  - 場所: `research/v4-postflop/findings/r1_*.json`
  - bucket=trash → FOLD パターンの検証データ
  - **未だ dataset_unified.csv に未統合** (`r1_extract.py` で hand-level CSV 化 + マージが残タスク)

R1 統合後、river v15 の精度がさらに上がる見込み (特に Cash100 で bucket 軸の信頼度向上)。

## 適用範囲と書籍化

- **Vol2 (Cash postflop)**: v9b / v15 を中核公式に
- **Vol3 (MTT postflop)**: 同じ v9b / v15 を主、加えて MTT 短スタック CR ルールを明示
- **章末コラム**: 「Cash と MTT で公式が同じ ≠ 戦略が同じ」を v9b の `_is_short_stack` 分岐で示す
- **境界ハンド集**: 残境界 cell (straight × overbet 等) を「機械的に学ぶ」リストとして付録
