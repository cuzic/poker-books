# GTO Wizard API リファレンス（MTTGeneral ポストフロップ）

本ドキュメントは、`mtt-postflop/` 配下のスクリプト群が GTO Wizard の非公開 API を
呼び出す際に得られた知見をまとめたものです。2026-05-22 時点の仕様です。

---

## 1. エンドポイント

```
GET https://api.gtowizard.com/v4/solutions/spot-solution/
```

### クエリパラメータ

| パラメータ | 型 | 説明 | 例 |
|-----------|---|------|---|
| `gametype` | string | ゲームタイプ識別子 | `MTTGeneral` |
| `depth` | string | 実効スタック(BB) | `"25.125"` |
| `stacks` | string | 各プレイヤーのスタック(ハイフン区切り) | `""` (空文字でOK) |
| `preflop_actions` | string | プリフロップ行動列 | `"F-F-F-F-F-R2.1-F-C"` |
| `flop_actions` | string | フロップ行動列 | `"X"` または `""` |
| `turn_actions` | string | ターン行動列 | `""` |
| `river_actions` | string | リバー行動列 | `""` |
| `board` | string | ボードカード(連結) | `"Kd9s8c"` |

---

## 2. 認証

### 必須ヘッダー

```python
{
    "authorization":  "Bearer <JWT_TOKEN>",
    "gwclientid":     "<UUID>",           # ブラウザ固有ID
    "origin":         "https://app.gtowizard.com",
    "referer":        "https://app.gtowizard.com/",
}
```

### 注意点

- **`google-anal-id` ヘッダーは付けない方が安全**。
  セッション不一致の場合に HTTP 401 が返ることがある（gametype が異なる curl から
  トークンを取得した場合など）。
- `google-anal-id` なしでも API は正常動作する。
- トークンは JWT で、ペイロードの `exp` フィールドで有効期限を確認できる。
  一般に発行から **15 分** 程度で失効する。

```python
import base64, json, time

def check_remaining(token: str) -> float:
    payload = token.split(".")[1] + "=="
    data = json.loads(base64.b64decode(payload))
    return data["exp"] - time.time()   # 秒数
```

### HTTP ステータスの意味

| コード | 意味 |
|-------|------|
| 200 | 正常。レスポンスボディに解あり |
| 204 | 解なし（この depth/preflop_actions の組み合わせを GTO Wizard が未計算） |
| 401 | 認証失敗（トークン期限切れ、または `google-anal-id` 不整合） |
| 403 | アクセス禁止（サブスクリプション対象外のシナリオ） |
| 429 | レート制限。`Retry-After` ヘッダーで再試行まで待機 |

---

## 3. preflop_actions 文字列の形式

9 プレイヤー MTT（MTTGeneral）前提。位置順は UTG → UTG+1 → MP → MP+1 → HJ → CO → BTN → SB → BB。

```
F = Fold
R{size} = Raise to {size}BB
C = Call
X = Check
B{size} = Bet (ポストフロップ)
```

### SRP（シングルレイズドポット）確認済み文字列

| SBR | シナリオ | preflop_actions | depth |
|-----|---------|-----------------|-------|
| 40 | BTN vs BB | `F-F-F-F-F-R2.5-F-C` | 40.125 |
| 25 | BTN vs BB | `F-F-F-F-F-R2.1-F-C` | 25.125 |
| 20 | BTN vs BB | `F-F-F-F-F-R2-F-C` | 20.125 |
| 40 | SB vs BB | `F-F-F-F-F-F-R2.5-C` | 40.125 |
| 25 | SB vs BB | `F-F-F-F-F-F-R3-C` | 25.125 |
| 20 | SB vs BB | `F-F-F-F-F-F-R3-C` | 20.125 |

- SBR15 (depth=15.125) は HTTP 403（サブスクリプション対象外）
- BTN が F-F-F-F-F の後に raise = CO 以前が全員フォールドして BTN がオープン

### 3BP（スリーベットポット）確認済み文字列

| SBR | シナリオ | preflop_actions | depth | HTTP |
|-----|---------|-----------------|-------|------|
| 20 | BTN open → BB 3-bet → BTN call | `F-F-F-F-F-R2-F-R7-C` | 20.125 | ✅ 200 |
| 25 | BTN open → BB 3-bet → BTN call | R7/R8/R9 どれも | 25.125 | ❌ 204 |
| 30 | 各種 | 各種 | 30.125 | ❌ 204 |

**3BP のポット・SPR（SBR20 R7 の場合）**
- BTN が 7BB コール、BB が 7BB 3-bet、SB フォールド(0.5BB)、アンテ 1BB
- フロップポット ≈ 15.5BB、実効スタック残 ≈ 13BB → **SPR ≈ 0.84**

---

## 4. flop_actions 文字列

ポストフロップのアクションを表す。

| 文字列 | 意味 |
|-------|------|
| `""` (空) | フロップ全体の集計（アクション分岐前の根ノード） |
| `"X"` | OOP（BB）がチェック後、IP（BTN）の決断ノード |
| `"X-B{size}"` | OOPチェック → IPベット後のOOP視点 |
| `"B{size}"` | OOPがリードベットした後のIP視点 |
| `"X-X"` | 両者チェック（ターンへ） |

**注意**: SRP BTN vs BB で `flop_actions="X"` とすると、BB がチェックした後の
BTN（IP）の CBet 決断ノードを取得できる。

---

## 5. レスポンス構造

### トップレベル

```json
{
  "action_solutions":        [...],   // アクション別の詳細解
  "hand_categories_range":   [...],   // 1326コンボの hand_category インデックス
  "draw_categories_range":   [...],   // 1326コンボの draw_category インデックス
  "players_info":            [...],   // プレイヤー情報（旧API用途）
  "pot":                     float,   // ポットサイズ(BB)
  "effective_stack":         float    // 実効スタック(BB)
}
```

### action_solutions の各要素

```json
{
  "action": {
    "code":           "X",        // アクションコード (X/B33/B50/B75/C/F など)
    "type":           "CHECK",    // CHECK / BET / CALL / FOLD / RAISE
    "betsize_by_pot": 0.0         // ポット比ベットサイズ (0.33 = 33%ポット)
  },
  "strategy":          [...],     // 1326要素の float配列。各コンボの行動頻度
  "hand_categories":   [...],     // 17種ハンドカテゴリの集計値
  "draw_categories":   [...],     // 8種ドローカテゴリの集計値
  "total_frequency":   0.45       // このアクションの全体頻度
}
```

**重要**: 旧 API にあった `simple_hand_counters` は現在返されない（常に空 `{}`）。
コンボ別解析には `strategy` 配列 + `hand_categories_range` / `draw_categories_range` を使う。

---

## 6. hand_categories（ハンドカテゴリ）

`hand_categories_range[i]` が各コンボ i のカテゴリインデックス。

| name | 説明 |
|------|------|
| `no_made_hand` | メイドハンドなし（ドロー・ハイカードのみ） |
| `king_high` | キング高 |
| `ace_high` | エース高 |
| `low_pair` | ローペア（ボード最下カードとのペア） |
| `third_pair` | サードペア |
| `second_pair` | セカンドペア |
| `underpair` | アンダーペア（ポケットペアがボード全カードより低い） |
| `top_pair` | トップペア |
| `overpair` | オーバーペア |
| `two_pair` | ツーペア |
| `trips` | トリップス（ポケットペア + ボードで3枚） |
| `set` | セット（ポケットペア + ボード1枚でトリップス） |
| `straight` | ストレート |
| `flush` | フラッシュ |
| `full_house` | フルハウス |
| `quads` | フォーカード |
| `straight_flush` | ストレートフラッシュ |

---

## 7. draw_categories（ドローカテゴリ）

`draw_categories_range[i]` が各コンボ i のカテゴリインデックス。

| index | name | 説明 |
|-------|------|------|
| 0 | `no_draw` | ドローなし |
| 1 | `gutshot` | ガットショット（4枚ストレートドロー、片側） |
| 2 | `oesd` | OESD（両側ストレートドロー） |
| 3 | `flush_draw` | フラッシュドロー（手2枚+ボード2枚=4枚同スーツ） |
| 4 | `combo_draw` | コンボドロー（FD + ストレートドローの複合） |
| 12 | `nut_flush_draw` | ナットフラッシュドロー |
| 16 | `onecard_bdfd` | バックドアFD（手1枚+ボード2枚=3枚同スーツ） |
| 17 | `twocards_bdfd` | バックドアFD（手2枚+ボード1枚=3枚同スーツ） |

---

## 8. コンボ別クロス集計の計算方法

```python
from collections import defaultdict

def compute_cross(data: dict) -> dict:
    dcr = data["draw_categories_range"]   # 1326要素
    hcr = data["hand_categories_range"]   # 1326要素
    
    draw_map, hand_map = {}, {}
    strategies = {}
    
    for item in data["action_solutions"]:
        code = item["action"]["code"]
        strategies[code] = item.get("strategy", [])
        if not draw_map:
            for d in (item.get("draw_categories") or []):
                draw_map[d["index"]] = d["name"]
        if not hand_map:
            for h in (item.get("hand_categories") or []):
                hand_map[h["index"]] = h["name"]
    
    bet_codes = [c for c in strategies if c != "X"]   # "X" = チェック
    cross = defaultdict(list)
    
    for i in range(min(1326, len(dcr), len(hcr))):
        # レンジ内判定: 全アクション頻度の和 > 0
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:
            continue
        bet_f = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        d_name = draw_map.get(dcr[i], f"unk_{dcr[i]}")
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")
        cross[(h_name, d_name)].append(bet_f)
    
    return {
        f"{h}|{d}": {"n": len(v), "avg": sum(v)/len(v)*100}
        for (h, d), v in cross.items()
    }
```

---

## 9. second_pair + FD が成立するボード設計

フラッシュドロー（手2枚 + ボード2枚 = 4枚同スーツ）と
セカンドペア（ボード2番目のランクとペア）を同時に持つコンボが存在するには、
**ペアになるボードカードのスーツがフラッシュスーツと異なる**ことが必要。

```
✅ Kd9c8d (K♦9♣8♦):
   フラッシュスーツ=♦、ペアカード=9♣(非♦) → J♦9♦ = 2ndP + FD

✅ Td9s8d (T♦9♠8♦):
   フラッシュスーツ=♦、ペアカード=9♠(非♦) → J♦9♦ = 2ndP + FD + OESD

❌ Th9s8s (T♥9♠8♠):
   フラッシュスーツ=♠、ペアカード=9♠(♠) → 9xでFDを持つには9♠が必要だが
   手札の9♠+他スペードでは2ndPとFDが同時成立しない
```

---

## 10. 確認済みシナリオ比較（SBR別 bet%）

`draw_study.py` の `--compare` モードで得られた主要結果（SRP25/SRP20/3BP20）。

### second_pair + ドローなし の IP bet%

| ボード | SRP25 | SRP20 | 3BP20 | 解釈 |
|-------|-------|-------|-------|------|
| K98（セミドライ） | 59% | 55% | **94%** | 3BPでレンジが絞られ2ndPがより強くなる |
| T98（ウェット） | 66% | 41% | **99%** | SPR低下で弱ハンドも押し込み |
| K72（ドライ） | 87% | 81% | 100% | ドライ板は常に高い |
| A94（エース高） | **100%** | **100%** | 36% | 3BPはBBがAx支配→ナット不利でチェック |
| 765（ローウェット） | 5% | 23% | **96%** | SRPではBTNの2ndP=弱手、3BPでは有力手 |

**重要な知見**: bet% は `f(SPR, board_type, preflop_context)` の 3 次元関数。
SRP と 3BP では「second_pair の格」が根本的に異なる（レンジ組成が変わるため）。

---

## 11. トークン取得手順（ブラウザのデベロッパーツール）

1. `https://app.gtowizard.com` でログイン
2. F12 → Network タブ → `spot-solution` リクエストをクリック
3. Request Headers から `authorization` の値（`Bearer eyJ...`）をコピー
4. 同じく `gwclientid` をコピー
5. **`google-anal-id` は不要**（付けると環境によって 401 になる）

トークンの有効期限は約 15 分。スクリプト実行前に残り時間を確認すること。

---

## 12. スクリプト一覧

| ファイル | 目的 | 主な調査内容 |
|---------|------|------------|
| `mtt_flop_cbet.py` | フロップ CBet 分析 | 型別CBet率・守備率 |
| `mtt_turn_barrel.py` | ターンバレル分析 | TA+/TA- 判定 |
| `mtt_sb_bb.py` | SB vs BB 分析 | SBオープン後のポストフロップ |
| `mtt_check_raise.py` | OOP チェックレイズ分析 | CR頻度・フォールド率 |
| `equity_study.py` | ハンド別エクイティ調査 | TPTK/2ndP等のベット閾値 |
| `draw_study.py` | ドロー×ハンドカテゴリ分析 | FD/SD/BDFD × ハンドタイプのクロス集計 |
| `diagnose_sbr20.py` | SBR20 preflop_actions 診断 | HTTP200になるパラメータ探索 |

### draw_study.py の使い方

```bash
# トークン設定（GOOGLE_ANAL_IDは不要）
export TOKEN="eyJhbGci..."
export GWCLIENTID="930036c8-..."

# preflop_actions の有効サイズを発見
uv run --with requests draw_study.py --probe-pf

# データ収集（シナリオ指定）
uv run --with requests draw_study.py --collect --scenario SRP25
uv run --with requests draw_study.py --collect --scenario SRP20
uv run --with requests draw_study.py --collect --scenario 3BP20

# グループ絞り込み（トークン節約）
uv run --with requests draw_study.py --collect --scenario SRP25 --group K98

# 単シナリオ分析
uv run --with requests draw_study.py --analyze --scenario SRP25

# 複数シナリオ比較
uv run --with requests draw_study.py --compare --scenarios SRP25 SRP20 3BP20
```

### SCENARIO_CONFIGS（draw_study.py 定義）

| キー | depth | preflop_actions | 状態 |
|-----|-------|-----------------|------|
| SRP25 | 25.125 | `F-F-F-F-F-R2.1-F-C` | ✅ 利用可 |
| SRP20 | 20.125 | `F-F-F-F-F-R2-F-C` | ✅ 利用可 |
| SRP15 | 15.125 | `F-F-F-F-F-R2-F-C` | ❌ HTTP 403（サブスク対象外） |
| 3BP25 | 25.125 | `F-F-F-F-F-R2.1-F-R8-C` | ❌ HTTP 204（解なし） |
| 3BP20 | 20.125 | `F-F-F-F-F-R2-F-R7-C` | ✅ 利用可（SPR≈0.84） |

---

## 13. 既知の落とし穴

| 問題 | 原因 | 対処 |
|-----|------|------|
| `strategy` が全て 0 | レンジ外コンボ（その depth/pf では存在しない手） | `sum(strategy) < 0.001` でスキップ |
| `total_frequency` が常に 0 | 旧バグ: `s.get("frequency")` ではなく `s.get("total_frequency")` | 修正済み |
| HTTP 401（全リクエスト） | `google-anal-id` ヘッダーの不整合 | ヘッダーを省略して再実行 |
| HTTP 204（3BP25） | GTO Wizard に当該シナリオの解が存在しない | 3BP20 を使用 |
| `simple_hand_counters` が空（ポストフロップ） | API 仕様変更（廃止） | `action_solutions.strategy` + `*_range` で代替 |
| `simple_hand_counters` が空（プリフロップ） | 同上だが Cash 旧スクリプトは依存していた | `players_info[i].hand_categories` を使う |
| `second_pair + flush_draw` が 0件 | ペアカードとFDスーツが同じボード | ペアカードをFDスーツ外にしたボードを設計する |
| MTT の `avg` 値が 0〜100 の%スケール | `action_solutions[*].hand_categories[*].avg` は % 単位 | 0.01 倍して 0〜1 に変換する |

---

## 14. gametype 一覧

| gametype 識別子 | ゲーム | テーブル人数 | depth デフォルト |
|----------------|--------|------------|----------------|
| `MTTGeneral` | MTT トーナメント（BBアンテあり） | 9 人 (8-max ツリー) | SBR依存 (下記) |
| `Cash6mGeneral_6mNL25R25` | キャッシュ 6-max NL25 | 6 人 | 100 (= 100BB) |

環境変数 `GT` で切り替える（`gto_api.py` 共通モジュール参照）。

```python
import os
GT = os.environ.get("GT", "Cash6mGeneral_6mNL25R25")
```

---

## 15. プリフロップ共通仕様

ポストフロップと**同じエンドポイント**を `board=""` で呼ぶとプリフロップノードが返る。

```python
params = {
    "gametype":        GT,
    "depth":           str(depth),
    "stacks":          "",
    "preflop_actions": pf_actions,  # ここで現在のアクション列を指定
    "flop_actions":    "",           # 空のまま
    "turn_actions":    "",
    "river_actions":   "",
    "board":           "",           # ← これが空 = プリフロップ
}
```

### レスポンス構造（プリフロップ）

```json
{
  "action_solutions": [...],         // アクション別の全コンボ戦略
  "players_info": [...],             // 現在の決断プレイヤー (actor)
  "pot": float,                      // 現在のポット (BB単位)
  "effective_stack": float           // 実効スタック (BB単位)
}
```

- `players_info` にはアクティブプレイヤー**1〜2 人**だけが入る
  （プリフロップはアクターが 1 人ずつ）
- `players_info[i]["player"]["position"]` で位置を特定する
- `players_info[i].hand_categories` の各要素に
  `actions_total_frequencies` が入っており、fold/call/raise 率が分かる

### ハンド別アクション率の取り出し方（プリフロップ）

```python
def get_player(data: dict, position: str) -> dict | None:
    for p in data.get("players_info", []):
        player = p.get("player", {})
        if isinstance(player, dict) and player.get("position") == position:
            return p
    return None

def hand_action_rates(player: dict) -> list[dict]:
    rows = []
    for hc in player.get("hand_categories", []):
        n = hc.get("total_combos", 0)
        if n < 0.1:
            continue
        af = hc.get("actions_total_frequencies", {})
        fold  = af.get("F", 0.0)
        call  = af.get("C", 0.0)
        raise_rate = max(0.0, 1.0 - fold - call)
        rows.append({"hand": hc["name"], "combos": n,
                     "fold": fold, "call": call, "raise": raise_rate})
    return sorted(rows, key=lambda x: -x["combos"])
```

---

## 16. Cash ポストフロップ固有事項

### depth と SPR

Cash は `depth=100`（固定）。フロップポットは約 6BB（BTN 2.5BB open + BB call + 0.5BB デッド SB）。

| シナリオ | depth | フロップポット | 実効スタック残 | **SPR** |
|---------|-------|------------|-------------|---------|
| SRP BTN-BB | 100 | ≈ 6BB | ≈ 97.5BB | **≈ 16** |
| SRP SB-BB  | 100 | ≈ 7.5BB | ≈ 96.5BB | **≈ 13** |
| 3BP BTN(caller)-BB | 100 | ≈ 19BB | ≈ 81BB | **≈ 4** |

MTT（SBR25 SRP: SPR ≈ 4）と比べて Cash SRP の SPR は約 4 倍高く、ボードテクスチャーの影響が支配的。ハンド単体のスコア（CBS）は MTT に比べて効きにくい。

### 確認済みプリフロップ文字列（Cash 6-max, depth=100）

位置順: `UTG(1) HJ(2) CO(3) BTN(4) SB(5) BB(6)`

| シナリオ | preflop_actions |
|---------|-----------------|
| SRP BTN vs BB | `F-F-F-R2.5-F-C` |
| SRP CO vs BB  | `F-F-R2.5-F-F-C` |
| SRP HJ vs BB  | `F-R2.5-F-F-F-C` |
| SRP UTG vs BB | `R2.5-F-F-F-F-C` |
| SRP SB vs BB  | `F-F-F-F-R3-C` ← SBは 3BB open |
| SRP BTN vs SB | `F-F-F-R2.5-C-F` |
| 3BP CO vs BTN (BTN 3bet) | `F-F-R2.5-R9-F-F-C` |
| 3BP BTN vs BB (BB 3bet) | `F-F-F-R2.5-F-R9-C` |

### Cash postflop で利用可能なシナリオ

`cash_5cat_gto.py` / `cash_board_wide_gto.py` で収集済み：

| シナリオID | preflop_actions | IP側 | OOP側 | SPR目安 |
|-----------|-----------------|------|-------|---------|
| `SRP_IP`  | `F-F-F-R2.5-F-C` | BTN | BB | ≈16 |
| `SRP_OOP` | `F-F-F-F-R3-C`   | BB  | SB | ≈13 |
| `3BP_IP`  | `F-F-R2.5-R9-F-F-C` | BTN | CO | ≈5 |
| `3BP_OOP` | `F-F-F-R2.5-F-R9-C` | BTN | BB | ≈5 |

### Cash postflop の flop_actions

MTT と同じ形式。IP の CBet 率を調べる場合は `flop_actions="X"`。

```python
# IP CBet 決断ノード（OOP がチェックした後の IP 視点）
flop_actions = "X"

# OOP チェック → IP ベット後の OOP 守備ノード
flop_actions = f"X-{bet_code}"  # bet_code: "bet33", "bet50", "bet75" など
```

### Cash のベットコード

Cash ツリーは MTT より豊富なサイジングが存在する。

| コード | ポット比 |
|-------|---------|
| `bet20` | 20% |
| `bet25` | 25% |
| `bet33` | 33% |
| `bet50` | 50% |
| `bet75` | 75% |
| `bet100` | 100% |
| `bet125` | 125% |
| `bet150` | 150% |
| `betover` | オーバーベット（150%超） |

MTT は主に `bet33` 一択; Cash は複数サイズが混在する。

---

## 17. Cash プリフロップ

**gametype**: `Cash6mGeneral_6mNL25R25`  
**board**: `""` (空文字)  
**depth**: `100` (= 100BB)

### 位置順（6-max）

```
UTG(1) → HJ(2) → CO(3) → BTN(4) → SB(5) → BB(6)
```

### preflop_actions 文字列（確認済み）

| フェーズ | スポット | preflop_actions | actor |
|---------|---------|-----------------|-------|
| RFI | UTG open | `""` | UTG |
| RFI | HJ open | `"F"` | HJ |
| RFI | CO open | `"F-F"` | CO |
| RFI | BTN open | `"F-F-F"` | BTN |
| RFI | SB open | `"F-F-F-F"` | SB |
| vs_open | BB vs UTG | `"R2.5-F-F-F-F"` | BB |
| vs_open | BB vs BTN | `"F-F-F-R2.5-F"` | BB |
| vs_open | BB vs SB | `"F-F-F-F-R3.5"` | BB |
| vs_open | SB vs BTN | `"F-F-F-R2.5"` | SB |
| vs_open | BTN vs CO (IP cold) | `"F-F-R2.5"` | BTN |
| vs_3bet | BTN vs BB 3bet | `"F-F-F-R2.5-F-RAI"` | BTN |
| vs_3bet | UTG vs HJ 3bet | `"R2.5-R8-F-F-F-F"` | UTG |
| vs_4bet | HJ vs UTG 4bet | `"R2.5-R8-F-F-F-F-R21.5"` | HJ |

### Cash アクションサイズ（確認済み）

| アクション | サイズ |
|-----------|-------|
| オープンレイズ（UTG/HJ/CO/BTN） | 2.5BB |
| SB オープン | 3.5BB |
| IP 3-bet | 8BB |
| SB 3-bet vs BTN | 11BB |
| BB 3-bet vs IP | RAI（オールイン） |
| 4-bet（IP 3-bettor → opener） | 21.5BB |

### マルチウェイ（Cash 6-max で確認済みのスポット）

```
R2.5-C     → CO が判断 (UTG open + HJ call)    ✅ 200
R2.5-C-F   → BTN が判断 (UTG open + HJ call)   ✅ 200
R2.5-C-F-F → SB が判断                          ✅ 200
R2.5-F-C-F-F → BB が判断 (UTG + CO cold-call)  ✅ 200
```

```
R2.5-F → HJ が判断 (UTG open のみ, cold-call 探索)  ❌ 204
```

### `simple_hand_counters` の挙動（Cash プリフロップ）

プリフロップでは `players_info[i].hand_categories` を使う。
`simple_hand_counters` は現 API では**空になることがある**ため、
`hand_categories` の `actions_total_frequencies` を使って fold/call/raise 率を算出する。

---

## 18. MTT プリフロップ

**gametype**: `MTTGeneral`  
**board**: `""` (空文字)  
**depth**: SBR に依存（下記）

### 位置順（MTT 9人 / 8-max ツリー）

```
UTG(1) → UTG1(2) → LJ(3) → HJ(4) → CO(5) → BTN(6) → SB(7) → BB(8)
```

### SBR 別 depth・アクションサイズ（確認済み）

| SBR | depth | オープン | SB オープン | IP 3-bet | SB 3-bet | BB 3-bet | 4-bet |
|-----|-------|---------|-----------|---------|---------|---------|-------|
| 40 | 40.125 | R2.3 | R3.5 | R6.9 | R8.6 | R9.2 | RAI |
| 25 | 25.125 | R2.1 | R3 | R5 | R6 | R6.3 | RAI |
| 20 | 20.125 | R2 | R3 | R4.5 | R5 | R5 | RAI |
| 15 | 15.125 | — | — | — | — | — | ❌ HTTP 403 |

- SBR15 は403（サブスクリプション対象外）
- MTT では浅いスタックのため 4-bet は常に RAI（オールイン）
- `depth` は `SBR + 0.125` （BBアンテ=1BB分の小数点）

### preflop_actions 文字列（MTT, SBR25 の例）

| フェーズ | スポット | preflop_actions |
|---------|---------|-----------------|
| RFI | UTG open | `""` |
| RFI | HJ open | `"F-F-F"` |
| RFI | BTN open | `"F-F-F-F-F"` |
| RFI | SB open | `"F-F-F-F-F-F"` |
| vs_open | BB vs BTN | `"F-F-F-F-F-R2.1-F"` |
| vs_open | SB vs BTN | `"F-F-F-F-F-R2.1"` |
| vs_3bet | BTN vs BB | `"F-F-F-F-F-R2.1-F-R6.3"` → BTN |
| vs_4bet | BB vs BTN shove | `"F-F-F-F-F-R2.1-F-R6.3-RAI"` → BB |
| multiway | BB vs BTN+SB | `"F-F-F-F-F-R2.1-C"` → BB |

### マルチウェイ（MTT, SBR25/SBR40 で確認済みスポット例）

```
R-C-F-F-F-F-F  → BB が判断 (UTG open + UTG1 call, others fold)  ✅
F-F-F-R-C      → SB が判断 (HJ open + CO call)                   ✅
F-F-F-R-C-C    → SB が判断 (HJ open + CO+BTN call)               ✅
```

- MTT は raise+4callers まで収録（31スポット）
- Cash と異なり UTG+HJ のコールドコールも収録されている

### フェーズ別 API コール数（MTT プリフロップ）

| フェーズ | コール数 | 内容 |
|---------|---------|------|
| probe | 1 | BTN RFI でレスポンス形式確認 |
| rfi | 7 | UTG/UTG1/LJ/HJ/CO/BTN/SB のオープン率 |
| vs_open | 14 | BB(6) + SB(5) + IP cold-call(3) の守備 |
| vs_3bet | 12 | オープン側の 3-bet 対応 |
| vs_4bet | 5 | 3-bet 側の shove 対応 |
| vs_5bet | 3 | RAI-RAI シーケンス（通常 204） |
| multiway | 31 | raise+call(1〜4人) 後の fold/call/3bet |
| **all** | **73** | 上記全部 |

---

## 19. gametype 別の差分まとめ

| 項目 | `MTTGeneral` (ポストフロップ) | `MTTGeneral` (プリフロップ) | `Cash6mGeneral_6mNL25R25` (ポストフロップ) | `Cash6mGeneral_6mNL25R25` (プリフロップ) |
|-----|------|------|------|------|
| `board` | ボード文字列 (例: `"Kd9s8c"`) | `""` 空文字 | ボード文字列 | `""` 空文字 |
| `depth` | SBR 依存（20〜40） | SBR 依存（20〜40） | `100` 固定 | `100` 固定 |
| `flop_actions` | `""` or `"X"` など | `""` | `""` or `"X"` など | `""` |
| ハンドデータ取得元 | `action_solutions.strategy` + `*_range` | `players_info[i].hand_categories` | `players_info[i].hand_categories` | `players_info[i].hand_categories` |
| `simple_hand_counters` | 空（廃止） | 空（廃止） | 空（廃止） | 空（廃止） |
| 有効 SBR/SPR | SBR 15〜40 (15=403) | SBR 20〜40 (15=403) | 常に ~SPR16 (100BB) | N/A |
| ベットサイズ種類 | 主に `bet33` 一択 | N/A | `bet20`〜`betover` 多数 | N/A |
| draw_agg の avg スケール | 0〜100 (%) | N/A | 0〜100 (%) | N/A |
