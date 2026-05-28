# 第 12 章　補助ルール

スコア式でカバーできない約 7〜8% のケースを補完する 4 つのルール。

## 12.1 小ペア set mining

ペアは式で自動的にスコアが高いが、スタックが浅いと収益性が低下する。
T_call 未満のペアでも深スタックならコールが正当化される。

```
コール額 × 15 ≤ 相手スタック → CALL
```

例: UTG オープン 3BB、相手スタック 50BB

コール額 = 3BB → 3 × 15 = 45BB ≤ 50BB → **CALL ✓**（スタック 40BB なら 45BB > 40BB → FOLD）

ペア別の判定（BB vs UTG open、T_call = 23 を基準）:

| ペア | Score | 式の判定（T_call=23） |
|---|---|---|
| 22 | 17 | Score=17 < 23 → コール額×15 ≤ スタックなら CALL |
| 33 | 19 | Score=19 < 23 → コール額×15 ≤ スタックなら CALL |
| 44 | 21 | Score=21 < 23 → コール額×15 ≤ スタックなら CALL |
| 55 | 23 | Score=23 ≥ 23 → コール（式で解決） |
| 66 | 25 | Score=25 ≥ 23 → コール（式で解決） |
| 77 | 27 | Score=27 ≥ 23 → コール（式で解決） |
| 88 | 29 | Score=29 ≥ 23 → コール（式で解決） |
| 99 | 31 | Score=31 ≥ 23 → コール（式で解決） |

## 12.2 スーテッドコネクター implied odds

低スコアの SC は式の T_call を下回ることが多いが、
IP + 深スタックなら implied odds が成立する。

```
【HU (1 対 1)】
  IP かつ Score ≤ 26 (T9s 以下) かつ 相手スタック ≥ 100BB → CALL

【MW (open + cold call あり, N=1)】
  IP かつ Score ≤ 20 (76s 以下) かつ 相手スタック ≥ 100BB → cold call 可
  Score 21〜26 (87s〜T9s) は implied odds 不適用 → FOLD
```

GTO 実測（BTN vs UTG + HJ cold call）:

| ハンド | Score | HU 参加 | MW (N=1) 参加 | 判定 |
|---|---|---|---|---|
| T9s | 26 | ✓ | ✗（ほぼ 0%） | MW: Score 26 > 20 → FOLD |
| 87s | 22 | ✓ | ✗ | MW: Score 22 > 20 → FOLD |
| 76s | 20 | ✓ | ✓（14%） | MW: Score 20 = 20 → cold call ギリギリ |
| 65s | 18 | ✓ | ✓（55%） | MW: Score 18 ≤ 20 → cold call ✓ |
| 54s | 16 | ✓ | ✓ | MW: Score 16 ≤ 20 → cold call ✓ |

## 12.3 3-bet ブラフコンボ（上級者向け）

GTO は A スーテッド低カード・K9s・QJs などをブラフ 3-bet に使う。
本式ではスコアが高くオープン推奨になるが、実戦では「ブラフ or open」どちらでも可。

主な 3-bet ブラフ候補: A6s(27), A5s(26), A4s(25), A3s(24), A2s(23), K9s(26), QJs(30)

本書では **式に従いオープン or フォールド** を推奨。
上級者は T_3bet 付近のこれらのハンドで混合戦略を検討。

## 12.4 BB ワイドコール（suited 補正）

BB は 1BB 投資済みでポットオッズが改善する。
suited ハンドは T_call より広くコールできる。

```
BB defense: suited ハンドの T_call を −2〜3 する
（より広くコール）
```

例: BB vs BTN open（T_call = 18）— T_call に近い suited ハンド:

- Q2s（Score = 17）: 17 < 18 → 通常はフォールド / suited 補正 T_call=16 → 17 ≥ 16 → コール ✓
- J3s（Score = 17）: 17 < 18 → 通常はフォールド / suited 補正 T_call=16 → 17 ≥ 16 → コール ✓
- T4s（Score = 17）: 17 < 18 → 通常はフォールド / suited 補正 T_call=16 → 17 ≥ 16 → コール ✓

精度 74% の主な誤分類はこの BB のワイドコール。
suited 補正（−2〜3）を使うことで精度が約 90% に改善する。

## まとめ: 4 つの補助ルール

| ルール | 適用条件 | 効果 |
|---|---|---|
| set mining | ペア + Score < T_call + 深スタック | コール ↑ |
| SC implied | Score ≤ 26 (T9s 以下) + IP + 100BB+ | コール ↑ |
| 3-bet ブラフ | A低スーテッド / K9s / QJs（上級者） | 3-bet ↑ |
| BB ワイドコール | suited + BB + T_call 境界 | コール ↑ |
