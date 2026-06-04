# A モデル 将来改善案——例外ルール検討メモ

作成日: 2026-05-28
ステータス: 検討のみ。現状 A モデル (A+C3、WRMSE 18.3%) を確定として書籍化済み

---

## 背景

A モデルは WRMSE 18.32% で確定。旧 5 軸モデル (~16%) との +2pt 差は
「band 集約」という構造に由来する。本メモは Vol2 subset 性を維持しつつ、
新規例外ルールで精度向上を狙う候補を検討したもの。

検討経緯: 軸追加 (Confidence / Range advantage / Board family) で +0.5〜1pt 改善は
確認済み (C3 採用)。これ以上の改善は smooth axis ではなく **ピンポイント例外** が
現実的、という結論に到達。

---

## 例外候補 10 個 (期待効果別)

### 高優先 (+1pt 以上)

#### 候補 1: Kicker offset for MV ∈ {5, 7} ★★★

- 内容: top_pair / second_pair で kicker 別 offset を加算
- 動機: 現状 A モデルは MV=7 の AKo on K72 (top + nut kicker) と
  A2 on K72 (top + weak kicker) を同一視。GTO で 15-25pt 違うのを盲点扱い
- 設計: kicker_offset[hand_within_HP=7][board_highcard]
- 推定: **+12 params、+1.0〜1.5pt 改善**
- 暗算 step: +0 (kicker は元から見ている)
- Vol2 subset 維持: 可

#### 候補 2: cat × family interaction ★★★

- 内容: cat_offset を family 共通 (現状) から (4 family × 3 cat) 行列に展開
- 動機: 実測で trash on dynamic は cat_offset -25 相当、trash on paired は -8 程度。
  family 共通の -14 では取りきれない 17pt 差を吸収
- 設計: cat_offset[cat][board_family] = 4 × 3 = 12 cell (default は 0 baseline)
- 推定: **+9 params、+0.5〜1.0pt 改善**
- 暗算 step: +0 (表参照だけ)
- Vol2 subset 維持: 可 (Vol2 は cat_offset 自体を使わないため影響なし)
- **最も費用対効果が良い候補。書籍編集も軽微**

#### 候補 3: Turn overcard barrel rule ★★

- 内容: turn が overcard (flop に未開示の high card) で arrive のとき barrel ±10pt
- 動機: mtt_100bb_turn_btn (WRMSE 25.7%、worst context) を狙い撃ち
- 設計: I(turn_overcard) × ctx_turn の交互作用
- 推定: **+2-4 params、+0.5〜1.0pt 改善 (turn 限定)**
- 暗算 step: +0.5 (turn card 確認)
- Vol2 subset 維持: 可

### 中優先 (+0.3〜0.7pt)

#### 候補 4: Self-blocker rule for FD / SD ★

- 内容: 自分が flush draw 板で同 suit 持ち → bet +5〜10pt
- 動機: GTO 整合性は高いが narrow application
- 設計: I(has_suited_blocker) × ε[dynamic]
- 推定: +2-4 params、+0.3pt
- 暗算 step: +0.5 (自手 suit と板 suit の照合)

#### 候補 5: Range advantage tag (RvR per board) ★

- 内容: board feature から「BTN advantage / 中立 / BB advantage」3 値タグ
- 動機: dry_high の中の polarize を分離 (AsKsXx vs Tc8d4c は同じ dry_high だが
  RvR 異なる)
- 設計: 4 family を 12 family (4 × 3 RvR) に展開
- 推定: +6-12 params、+0.3〜0.5pt
- 暗算 step: +1 (RvR タグ判定)

#### 候補 6: Hand specific exception list (旧 5 軸モデル 風 O ルール) ★

- 内容: 実測 residual の top-10 cell を狙い撃ち (例: KKx on A-high、AKo on monotone 等)
- 推定: +5-10 params、+0.3〜0.5pt
- 個別ルールなので暗記負荷大、書籍向きでない

### 低優先 / 否定的

#### 候補 7: 2 ペア / set on connected (vulnerable nut)

- β = -15 で既に十分捕らえている。差分 +0.1pt 程度

#### 候補 8: SPR ヒューリスティック (≤2.5 のフラグ)

- context 分離済みで重複

#### 候補 9: Multiway 分岐

- 重要だが multiway data なし、スコープ外

#### 候補 10: Polarize size 軸再導入

- overbet は別問題、A モデルのスコープ外

---

## 構造的限界の評価

A モデルの WRMSE が 18% に張り付く根本原因は **band 集約**。同じ strong band 内で
MV=7 (top_pair) と MV=8 (set) を分離できない。

### 3 つの突破方向

| 方向 | 推定 WRMSE | 代償 |
|---|---:|---|
| band 廃止 → MV × DV × ctx 直接 lookup | 12-13% | params 63 → 240+、Vol2 subset 性消失、暗算不可 |
| band 細分化 (5 → 8) | 16% | params 25 → 40 cell、教育負担増 |
| **ピンポイント例外 (1+2+3 採用)** | **16〜16.5%** | params +25、暗算 step +1 (kicker)、Vol2 subset 維持 |

---

## 推奨ロードマップ (もし将来精度改善するなら)

優先順位:

1. **候補 2 (cat × family)** を実装。+0.5〜1pt、暗算 step +0、書籍編集軽微。
   費用対効果最高
2. **候補 1 (kicker offset for MV=7)** を実装。+1.0〜1.5pt、AKo / KQo 級の盲点解消
3. **候補 3 (turn overcard rule)** を turn context 限定で。+0.5〜1pt、worst context 改善

合算で WRMSE 16% 前後 (旧 5 軸モデル 並) まで届く可能性あり、Vol2 subset 性は維持。
ただし暗算 step が +1 (kicker 判別) 増えるので、「Vol3 reader でも 10 秒以内」の
目標とのトレードオフ。

---

## 検討結論 (2026-05-28)

**現状 A モデル (A+C3、18.3%) で書籍化確定**。理由:

- base のみ → 全 layerで -3pt 改善済み、Vol2 subset 性も完全保持
- 旧 5 軸モデル (~16%) との +2pt 差は構造的限界の範囲内、実戦判断に十分
- 暗算 7 step を 8 step 以上にすると「迷わない」という本書コンセプトと衝突
- 将来 Vol3 改訂時、または別シリーズで詰める余地として保留

---

## 関連ファイル

- 確定モデル: `vol3-mtt-postflop/ucbs_v3.py`
- パラメータ: `knowledges/gto_wizard_study/ucbs_v3_params.json`、`UCBS_V3_PARAMS.md`
- 設計ドキュメント: `knowledges/gto_wizard_study/UCBS_V3_HIERARCHICAL.md`
- 軸追加 fit 比較: `vol2-cash-postflop/ucbs_v3_axes.py`
