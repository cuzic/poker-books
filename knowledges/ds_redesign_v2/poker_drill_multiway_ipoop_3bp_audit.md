# poker-drill マルチウェイ / IP-OOP / 3BP 対応状況調査

実施日: 2026-05-05

## 結論サマリ

| 領域 | カバー状況 | 数値整合 | 旧スケール残骸 |
|---|---|---|---|
| **マルチウェイ (3-way / 4-way+)** | ✓ 専用 deck 2 つ | ✓ M=12/22 | △ 1 件 dormant |
| **IP / OOP 区別** | ✓ 別 deck で分離 | ✓ ip_float_decision あり | △ 旧 docstring 1 件 |
| **3BP** | ✓ CBet/defense/turn の各 deck | △ SPR 閾値補正未反映 | △ 4 件 dormant |
| **4BP** | ✓ CBet/defense deck | △ HS 別判定なし (常に CALL) | △ 1 件 dormant |

主要な計算式 (calc_back_score, calc_m_coeff) は新スケール対応済み。
ただし UI 説明文と SPR 別閾値の補正が未反映。

## デッキ一覧（カバー対象）

```
src/data/
├── flop-cbet-3bp-cards.ts       3BP IP CBet 判断
├── flop-cbet-4bp-cards.ts       4BP IP CBet 判断
├── flop-cbet-multiway-cards.ts  マルチウェイ IP CBet 判断
├── flop-multiway-cards.ts       マルチウェイ defense
├── flop-vs-cbet-3bp-cards.ts    3BP IP defense (BTN call)
├── flop-vs-cbet-3bp-oop-cards.ts 3BP OOP defense (BB 3-bet caller)
├── flop-vs-cbet-4bp-cards.ts    4BP defense
├── turn-cbet-3bp-cards.ts       3BP turn CBet
└── ... (SRP 系の他 deck)
```

→ シナリオカバレッジは充分。

## 計算ロジックの新スケール対応状況

### scripts/generate/core/calc.py (canonical)

```python
calc_m_coeff(num_players):  # ✓ 新スケール
    2→0, 3→12, 4+→22

calc_back_score(hs, a, c, m):  # ✓ 新スケール
    return hs + a - c - m   (旧 -3 削除済み)

back_score_judgment(bs):  # ✓ SRP 閾値
    ≥40 CR / 20-39 CALL / <20 FOLD

ip_float_decision(hs, bucket):  # ✓ IP 専用判定
    H3 made → RAISE, H3 draw / H2 → FLOAT, H1 → FOLD
```

### IP / OOP の区別

```
IP defense:  ip_float_decision (calc.py)
              flop_defense_3bp.py で使用 (BTN 3BP defense)
              FLOAT/RAISE/FOLD の 3 択

OOP defense: back_score_judgment (calc.py)
              flop_defense.py / flop_defense_3bp_oop.py
              CR/CALL/FOLD の 3 択

→ IP/OOP の戦略的非対称性は generator level で正しく分離されている ✓
```

### マルチウェイの数値整合

```
flop_multiway.py:
  num_players = 3 or 4+
  m_coeff = calc_m_coeff(num_players)  # 12 or 22 ✓
  back_score = calc_back_score(hs, a, c, m_coeff)  # ✓

flop_cbet_multiway.py:
  _M_LABEL = {3: '3way (−15%)', 4: '4way+ (−30%)'}  # equity 低下%表示
  → 研究データ (12-15% / 21-25%) と概ね一致
```

## 発見された旧スケール残骸

### 1. dormant な「基準値 −3」ステップ (4 ファイル)

```python
# flop_defense.py:192
# flop_defense_3bp.py:138
# flop_defense_3bp_oop.py:148
# flop_multiway.py:144

rec.step('基準値', '−3')  # 旧スケール時代の baseline 表示
```

新スケールでは A 値が -3 baseline を吸収したため、この step は不要。
ただし全て `if not use_sdv` 経路にあり、SDV 列が populated な CSV では発火しない。
**実害は出ていないが、コード上の混乱要因**。

### 2. flop_defense_3bp_oop.py docstring (旧式)

```python
# 行 5-7:
Formula: 後手スコア = HandScore + A − 3 − C (M=0 for HU)
Decision: back_score >= 8 → CR, >= 0 → CALL, < 0 → FOLD
```

両方とも旧スケール表記。実装コード (calc_back_score / back_score_judgment)
は新スケール対応しているが、ドキュメンテーションのみ古い。

### 3. SPR 別 CR 閾値補正の未反映

新ガイドライン (knowledges/ds_redesign_v2/spr_correction_3bp.md):

```
SPR ≥ 6 (SRP):    CR 閾値 ≥ 40
SPR 3〜5 (3BP):   CR 閾値 ≥ 60
SPR < 3 (4BP):    CR 閾値 ≥ 75
```

poker-drill では `back_score_judgment` が SRP 閾値 (≥40) のみを実装。
3BP の OOP defense で使うときも同じ閾値を適用。

```python
# flop_defense_3bp_oop.py:119
decision = _DECISION_MAP.get(csv_action) or back_score_judgment(back_score)
```

`csv_action` が CR/CALL/FOLD の場合はそちらが優先 (実用上問題なし)。
ただし conclusion 表示は SRP 表記:

```python
# flop_defense_3bp_oop.py:139
f'{spr_label}: 後手スコア{back_score} → CR推奨。'
'GTOはCR/CALL混合（強手ほどCALL配分あり、例: AA→CR46%/CALL54%）'
```

3BP では「閾値 ≥ 60」を併記すると教育的価値が高まる。

### 4. 4BP の HS 別判定なし

```python
# flop_defense_3bp.py:198 (build_4bp_card)
decision = 'CALL'  # ハードコード
```

4BP のすべてのカードが「CALL」になる。新ガイドラインでは:

```
≥ 75 (Set+) → CR 確定（オールイン commit）
30-74 → コール (ターンでフォールド余地ほぼなし)
< 30 → フォールド推奨
```

の 3 択にすべき。ただし 4BP のシナリオは「ほぼ commit 圏」なので、
CSV の expected_action で個別指定する運用なら害はない。

## 実害評価

```
ユーザーが見るカード: 24 デッキ × 数十カード = 数百枚
旧式残骸が UI に出ているか: 0 件 (.ts ファイルに「基準値」「−3」なし)

→ 実害ゼロ。すべて SDV 経路で正しく動作している
→ 修正は code hygiene のため
```

## 推奨修正アクション

### 必須 (低工数)

1. `flop_defense_3bp_oop.py:5-7` の docstring を新スケール表記に更新
2. 4 ファイルの `rec.step('基準値', '−3')` を削除
3. SPR 別閾値の表示を 3BP/4BP の conclusion に追加

### 推奨 (中工数)

4. `core/calc.py` に `back_score_judgment_by_spr(bs, spr)` を追加
   - SPR から閾値帯 (≥6/3-5/<3) を判定し対応する閾値を返す
5. 4BP デッキの decision を HS 別に変更可能にする

### オプション

6. `flop_cbet_multiway.py:49` の `_M_LABEL` を新スケール準拠の数値に更新
   - 例: `{3: '3way (M=12)', 4: '4way+ (M=22)'}`

## 検証

```
.ts ファイルでの旧式表現探索: 0 件 ✓
generator スクリプトの dormant 旧式: 5 箇所 (上記)
ユーザーへの実害: なし
```

## 結論

**poker-drill のマルチウェイ・IP/OOP・3BP/4BP のシナリオカバレッジと数値整合は良好**。
旧スケール残骸はすべて dormant (実害なし) だが、コード hygiene のため
タスク #348 / #349 で修正推奨。
