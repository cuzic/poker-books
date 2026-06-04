# 第13章 早見表 — 5 公理 + 2 マトリックス + 補正 (1 ページ印刷推奨)

本書の核心を 1 ページに圧縮した実戦参照シートです。
印刷してテーブルの脇に置く、またはスマホで参照することを想定しています。

## 5 公理

1. **強さ 5 段階**: S (Strong: 2P+/set/straight/flush/overpair), M (Medium: TP/2nd/3rd/under pair), W (Weak: A/K-high/low pair), A (Air: no_made + no_draw), D (Draw: OESD/FD/combo, flop/turn のみ)
2. **サイズ 4 段階**: s (≤33% pot), m (50-75%), l (≈100%), o (≥150% or all-in)
3. **強いハンドは aggressive、弱いハンドは passive**
4. **サイズ 1 段階大きいごとに 1 段階タイト**
5. **完全 air は基本諦める** (river only blocker bluff)

## 攻撃マトリックス (自分が動く番)

**BET or CHECK by street**

| 強さ | Flop | Turn | River |
|------|------|------|-------|
| **S** | BET (33%) | CHECK (slowplay) | BET (66-75%) |
| **M** | CHECK | CHECK | BET on dry / CHECK on dynamic |
| **W** | CHECK | CHECK | CHECK |
| **A** | CHECK | CHECK | BET as bluff (dynamic + K-high) |
| **D** | CHECK (semibluff 控えめ) | CHECK | — |

## 守備マトリックス (相手のベットを受けた)

**FOLD / CALL / RAISE by hand × size**

| 強さ \ サイズ | s (小) | m (中) | l (大) | o (オーバー) |
|---------------|--------|--------|--------|-------------|
| **S** | RAISE | CALL | CALL | CALL |
| **M** | CALL | CALL | CALL | **FOLD** |
| **W** | CALL | CALL | **FOLD** | FOLD |
| **A** | CALL | **FOLD** | FOLD | FOLD |
| **D** | CALL | CALL | CALL | **FOLD** |

## 街ごとの補正 (マトリックスに加える例外)

### Flop 補正 (3 つで huge_gap loss 84% 削減)

- **補正 1**: W (low_pair / 3rd_pair) × no_draw × dry/dynamic_2tone → **FOLD**
- **補正 2** ⭐ (最重要): A-high / K-high × no_draw → **FOLD** (Flop に限り A 扱い)
- **補正 3**: overpair → **RAISE** (value 取り)

### Turn 補正 (84% → 92% に押し上げる重要拡張)

- vs overbet (≥100%):
-   - air × flush_draw × dry_high → **FOLD**
-   - air × OESD × dynamic → **FOLD**
-   - dynamic + top_pair + no_draw → **FOLD**
- vs medium (67%):
-   - **dynamic + A/K-high + 弱ドロー (gutshot/BDFD) → FOLD** ⭐ 最大の改善要因
-   - dynamic + 低/中ペア (low/under/3rd) + 弱ドロー → **FOLD**
-   - dynamic + 弱メイド + OESD → **FOLD**

### River 補正

- **TP × dry × overbet → CALL** (bluff catch、標準は M × o = FOLD)
- **TP × dynamic × l (100%) → CALL** (bluff catch、標準は M × l = CALL でこれは同じ)
- **TP/2P × dynamic × overbet → CALL** (bucket weak だが bluff catch +EV)
- **straight / flush / trips → bucket 関係なく CALL** (絶対強さ override)
- **真の all-in (raise 不可) では eqp > 65% で CALL**

## 決断フロー (毎回 5 秒で実行)

1. 自分のハンドの **強さ** を判定 (S/M/W/A/D)
2. 状況確認 (**攻撃** か **守備** か)
3. 守備なら **サイズ** 判定 (s/m/l/o)
4. マトリックス参照 → 該当セルのアクション
5. 街ごとの補正をチェック (該当すれば override)

## 迷ったときは 5 公理に戻る

マトリックスのセルを忘れたら、5 公理から推測できます。

例: "M × l を忘れた" → 公理 4「1 段階タイト」を当てはめる → M × m は CALL → M × l は「1 段階タイトで FOLD か CALL のまま」→ 公理 3「強いハンドは aggressive、弱いハンドは passive」より M は中間なので CALL を選ぶ。**正解: CALL**。

## 次のステップ — Vol3 への移行

本書 (Vol2) の **5 × 4 マトリックス + 5 公理 + 9 つの街補正 (Flop 3 + Turn 3 + River 4)** で Cash 100bb のポストフロップ判断の **平均 88%** (always_CALL 比 huge_loss 削減率: Flop 84%, Turn 92%, River 87%) が自動化されます。残る 7-13% は Vol3 詳細公式で改善できます (Turn 99%, River 97%)。

**Vol3 で扱う内容:**

- **MTT 25-200bb の stack depth 補正** — SPR が下がるほど bucket (相対強さ) 軸が支配的になる
- **真の all-in と "near-allin overbet" の意味論的差** — raise オプションの有無で公式が変わる
- **詳細例外 30+ パターン** — 本書の補正リストを更に深堀り

Vol2 を 80% 以上習得した方は Vol3 に進むことを推奨します。
