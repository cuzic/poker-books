# GTO Wizard API 完全ノート

最終更新: 2026-05-28
データソース: UCBS-v2 + DCBS 構築で 1,000+ spots を fetch した実測知見

---

## 1. エンドポイント

| 用途 | Method | URL |
|---|---|---|
| spot solution 取得 | GET | `https://api.gtowizard.com/v4/solutions/spot-solution/` |
| access token 更新 | POST | `https://api.gtowizard.com/v1/token/refresh/` |

---

## 2. 認証

### 2.1 必須ヘッダ (spot-solution)

```
Authorization: Bearer <JWT access token>
google-anal-id: <opaque, session ごとに変化>
gwclientid: 930036c8-831c-4fca-8453-b0a298853e86
origin: https://app.gtowizard.com
referer: https://app.gtowizard.com/
user-agent: Mozilla/5.0 ...
accept: application/json, text/plain, */*
```

`google-anal-id` は **必須**。token と pair で session 認証されており、ペアが噛み合わないと 401。

### 2.2 トークン仕様

| Token | フォーマット | TTL | 用途 |
|---|---|---|---|
| access | JWT | **~15 分** (`exp` から `iat` まで 900 秒) | API 呼び出し |
| refresh | JWT | **~5 年** | access 更新 |

JWT payload は base64 デコードで `exp`/`iat` 確認可:
```python
import base64, json
payload = jwt.split('.')[1] + '=='
d = json.loads(base64.b64decode(payload))
print(d['exp'], d['iat'])
```

### 2.3 Refresh API リクエスト

```bash
curl -X POST 'https://api.gtowizard.com/v1/token/refresh/' \
  -H 'content-type: application/json' \
  -H 'google-anal-id: <session 同期されたもの>' \
  -H 'gwclientid: 930036c8-831c-4fca-8453-b0a298853e86' \
  -H 'origin: https://app.gtowizard.com' \
  -H 'referer: https://app.gtowizard.com/' \
  -H 'user-agent: Mozilla/5.0 ...' \
  -d '{"refresh": "<refresh token JWT>"}'
```

レスポンス: `{"access": "<new JWT>"}` (refresh token はローテーションしない)

### 2.4 ★ 重要: サーバー側セッション無効化

| 現象 | 説明 |
|---|---|
| JWT exp 残あり → 401 | JWT の有効期限内でもサーバーが拒否することがある |
| 新規ブラウザログイン → 全 token 無効 | ユーザーが gtowizard.com で再ログインすると過去 token がすべて revoke される |
| google-anal-id 不一致 → 401 | 古い google-anal-id では refresh も 401 になる |

**実用上の対策**:
1. fetch スクリプトは **キャッシュ機構必須** (raw JSON を `<topic>/<spot_id>.json` に保存)
2. 401 時の `refresh_access_token()` を組み込む
3. 長時間 fetch は分割実行、トークン定期更新
4. 1 トークン分で fetch しきれない時は **手動再注入** をユーザーに依頼

### 2.5 トークン更新時のフロー

ユーザーが Chrome DevTools の Network タブで spot-solution リクエストを **Copy as cURL** して提供:
```python
# 抽出すべき値
access_token = curl から 'Authorization: Bearer <X>' の X
google_anal_id = curl から 'google-anal-id: <X>' の X
# .token と .google_anal_id を更新
```

---

## 3. ユーザー権限とプラン

### 3.1 アカウント情報の取得

ログイン後の Account API で subscription 一覧を確認可。subscriptions[] 内の各 plan の `tier` (FREE/STARTER/PREMIUM/ELITE) と `type` (CASH/TOURNAMENT/ANY) で権限範囲が決まる。

### 3.2 観察済みサブスクリプション (アカウント `acc_bxtaiax7jw` 例)

| Tier | Type | アクセス可否 | hands/制限 |
|---|---|---|---|
| **STARTER** | CASH NLHOLDEM | Cash 100bb のみ | 100/月 |
| **PREMIUM** | TOURNAMENT NLHOLDEM | MTT 全 depth | 100,000/月 |
| FREE | ANY | 補助 | 10/日 |

### 3.3 gametype 別アクセス可否マトリクス

#### Cash 系 (STARTER tier)
| gametype | depth | アクセス | 備考 |
|---|---|---|---|
| **Cash6mGeneral_6mNL25R25** | 100 | ✓ 200 | 唯一 OK |
| Cash6mGeneral_6mNL25R25 | 50 | ✗ 403 | PERMISSION_DENIED |
| Cash6mGeneral_6mNL25R25 | 75, 125, 150, 200, 300, 500 | ✗ 403 | STARTER 範囲外 |
| Cash6mGeneral_6mNL100R5 | * | ✗ 404 | gametype 存在せず |
| Cash6mGeneral_6mNL500R5 | * | ✗ 404 | gametype 存在せず |
| Cash6mTest_6mNL100R2 | 200 | ✗ 403 | PERMISSION_DENIED |
| Cash6m50zGeneral | * | ✗ 403 | Zoom 系 (STARTER 外) |
| Cash6m500z* | * | ✗ 403 | Zoom 系 |
| CashHu500z* | * | ✗ 403 | Heads-up Zoom |

#### MTT 系 (PREMIUM tier)
| gametype | depth | アクセス | 備考 |
|---|---|---|---|
| **MTT6mSimple** | 25.125 | ✓ 200 | 浅 push 圏直前 |
| **MTT6mSimple** | 50.125 | ✓ 200 | バブル前後 |
| **MTT6mSimple** | 100.125 | ✓ 200 | start / FT 直後 |
| **MTT6mSimple** | 200.125 | ✓ 200 | deep |
| MTT6mSimple | 25, 50, 100, 200 (整数) | ✗ 403 | **`.125` 必須** |
| MTT6mGeneral | 200.125 | ✓ 200 | full bet tree (Simple よりサイズ多) |
| MTT6mGeneral | 75.125, 150.125 | ✗ 403 | 一部 depth のみ |
| **MTTGeneral_ICM6m200PTT2** | 28.125 | ✓ 200 | ICM bubble PT2 |
| MTTGeneral_ICM6m200PTT3 | * | ✗ 403 | 上位 ICM tier |
| MTTGeneral_ICM5m200PTT2 | * | ✗ 403 | 5m ICM |
| MTTGeneral_ICM9m200PT* | * | ✗ 403 | 9m ICM |
| MTT9mSimple | * | ✗ 403 | 9-max は権限外 |
| MTT9m* | * | ✗ 403 | 同上 |
| MTT9m_5mGeneral | * | ✗ 403 | |

### 3.4 ★ 罠: depth に `.125` が必要

MTT 系は `depth=100` だと **403 PERMISSION_DENIED**、`depth=100.125` で **200 OK**。
これは MTT の big blind ante 含む正確な BB 換算らしい。

### 3.5 罠: subscription 範囲内でも 403

- 過去成功した組み合わせでも、何らかの session 状態で 403 になることあり
- 例: `Cash6mGeneral depth=50` を probe → 1 spot 成功 → 残り全て 403 という観察
- 推測: 上位プラン期間のキャッシュ、subscription cycle 境界、etc.
- 実用上: 連続で 403 になった場合は手動再ログインを促す

---

## 4. リクエストパラメータ

### 4.1 必須パラメータ

```
gametype: 上記 3.3 マトリクス
depth: 数値 (MTT は `.125` 必須)
stacks: 6 ポジションの stack カンマ区切り (MTT は均等、Cash は空 "")
preflop_actions: F-R-C 形式 (詳細後述)
flop_actions: F-R-C 形式 (空可)
turn_actions: F-R-C 形式 (空可)
river_actions: F-R-C 形式 (空可)
board: 0/3/4/5 枚の board cards
```

### 4.2 アクション記法

| 記号 | 意味 |
|---|---|
| `F` | Fold |
| `C` | Call |
| `X` | Check |
| `R<num>` | Raise to N (bb 単位、絶対値) |
| `RAI` | All-in |

- 各ストリートは `-` 区切り
- 例: `preflop_actions=F-F-F-R2.5-F-C` = UTG/HJ/CO fold, BTN raise to 2.5, SB fold, BB call

### 4.3 ボード表記

- rank: `23456789TJQKA`
- suit: `s`(spade), `h`(heart), `d`(diamond), `c`(club)
- 例: `Ks7d2c` = K♠ 7♦ 2♣
- flop は 6 chars、turn は 8 chars、river は 10 chars

### 4.4 MTT 6m 標準 open sizes (R<num>)

| Position | 25bb | 50bb | 100bb | 200bb |
|---|---|---|---|---|
| UTG | R2.1 | R2.2 | R2.1 | R2.2 |
| HJ | R2.1 | R2.2 | R2.1 | R2.2 |
| CO | R2.2 | R2.3 | R2.2 | R2.4 |
| BTN | R2.5 | R2.5 | R2.5 | R2.6 |
| SB | R3.5 | R3.0 | R3.5 | R4.0 |

### 4.5 3-bet pot preflop pattern

| 用途 | preflop_actions | 説明 |
|---|---|---|
| 3BP25 BTN cold-call | `F-F-F-R2.5-F-R6.5-C` | BTN open R2.5, BB 3-bet to R6.5, BTN call |
| 3BP50 BTN cold-call | `F-F-F-R2.5-F-R8-C` | 50bb 用 3-bet R8 |
| 3BP100 BTN cold-call | `F-F-F-R2.5-F-R10-C` | 100bb 用 3-bet R10 |
| 3BP25 SB 3-bettor | `F-F-F-F-F-F-R3-R8-C` | SB open R3, BB 3-bet R8, SB call (MTTGeneral 形式、8 actions) |

### 4.6 Flop cbet size (BTN open vs BB)

| 深さ | 標準 small (33%) | Overbet (~116%) |
|---|---|---|
| 25bb | R1.1 | (該当少) |
| 50bb | ~R1.8 | (動的検出) |
| 100bb | ~R1.83 | R9.5 程度 |
| 200bb | ~R2.1 | overbet 多 |

実際の size は **空 `flop_actions=X` で fetch** → `action_solutions` の `R*` 系から最小値を抽出するのが安全。

### 4.7 ストリート進行のアクション例

| シナリオ | flop_actions | turn_actions | 測定対象 |
|---|---|---|---|
| Flop IP cbet | `X` | "" | IP (例: BTN) の bet/check 選択 |
| Flop OOP cbet | "" | "" | OOP (例: SB) の bet/check 選択 |
| BB defense vs flop cbet | `X-R<size>` | "" | BB の F/C/R 選択 |
| Turn 2nd barrel (IP) | `X-R<size>-C` | `X` | IP の turn bet/check |
| Turn OOP donk | `X-R<size>-C` | "" | OOP の turn bet/check (次の手番) |

---

## 5. レスポンス構造

### 5.1 全体構造

```json
{
  "action_solutions": [
    {
      "action": {
        "code": "X",
        "type": "CHECK",
        "betsize": "0",
        "betsize_by_pot": null,
        "position": "BTN",
        "display_name": "CHECK"
      },
      "total_frequency": 0.267,    // range 全体での頻度
      "total_combos": 168.5,       // 範囲内 combos
      "strategy": [0.5, 0.0, ...], // ★ 1326 elements、hand i ごとの freq
      "evs": [12.3, ...],          // 1326 elements
      "equity_buckets": {...},
      "hand_categories": [{"index": 0, "name": "no_made_hand"}, ...],
      "draw_categories": [{"index": 0, "name": "no_draw"}, ...]
    },
    {"action": {"code": "R2.1", ...}, "total_frequency": 0.733, ...}
  ],
  "hand_categories_range": [0, 5, 2, ...],  // 1326 hand category indices
  "draw_categories_range": [0, 0, 1, ...],  // 1326 draw category indices
  "blocker_rate": ..., "unblocker_rate": ...,
  "blockers_frequencies": ...,
  "players_info": [{...}, ...],
  "game": {...},
  "warning": null,
  "hands_locked": false,
  "usage": {...}
}
```

### 5.2 主要フィールド

#### action_solutions[]
各アクション (CHECK / RAISE / FOLD / CALL) ごとに:
- `action.code`: API パラメータと一致する文字列 (`X`, `R2.5`, `C`, `F`)
- `total_frequency`: range 全体での選択率
- **`strategy`**: 1326 個の combo それぞれの選択率 (★ per-hand 分析の核)
- `hand_categories`: combo index → カテゴリ名のマップ
- `draw_categories`: 同上、draw 用

#### hand_categories_range
- 長さ 1326 (全 hole card combo)
- 各要素は hand_categories の index (= カテゴリ名)
- hand i のカテゴリ名: `hand_categories[hand_categories_range[i]].name`

#### Hand categories (観察済み 14 種)
```
no_made_hand, ace_high, king_high,
low_pair, underpair, third_pair, second_pair, top_pair, overpair,
two_pair, set, trips, straight, flush, fullhouse, quads
```

#### Draw categories (観察済み 6 種)
```
no_draw, twocards_bdfd, gutshot, oesd, fd, combo_draw
```

### 5.3 重要: aggregate vs per-hand

- `total_frequency` = range 全体での action 採用率 (1 数値)
- `strategy[i]` = combo i (= 特定 2 枚の hole cards) での action 採用率
- **per-hand 分析には `strategy` 配列 + `hand_categories_range` を結合**

#### per-hand 集計アルゴリズム
```python
def compute_hand_agg(data):
    dcr = data["draw_categories_range"]   # 1326
    hcr = data["hand_categories_range"]   # 1326
    as_ = data["action_solutions"]
    hand_map = {}
    strategies = {}
    for item in as_:
        code = item["action"]["code"]
        strategies[code] = item.get("strategy", [])
        if not hand_map:
            for h in item.get("hand_categories") or []:
                hand_map[h["index"]] = h["name"]
    bet_codes = [c for c in strategies if c != "X"]
    hand_agg = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    for i in range(1326):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:  # range 外 (preflop で fold したハンド)
            continue
        bet_f = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["bet"] += bet_f
    return {k: {"total": v["total"],
                "bet_pct": v["bet"]/v["total"]*100 if v["total"] > 0 else 0}
            for k, v in hand_agg.items()}
```

#### Defense (fold/call/raise) の場合
```python
fold_code = "F"
cont_codes = [c for c in strategies if c != fold_code]   # C, R*
# continue_freq = sum(strategies[c][i] for c in cont_codes)
```

### 5.4 combo index 体系

- 1326 = C(52, 2)、全 2 枚 hole cards 組合せ
- range 外の combo は全 action の strategy が ~0 になる → 集計時に除外
- `hand_categories_range[i]` で combo i のカテゴリ取得
- 同じ category index は同じ action 内の `hand_categories` 配列でマップ

---

## 6. エラーハンドリング

### 6.1 HTTP status

| Code | 意味 | 対処 |
|---|---|---|
| 200 | OK | data 取得成功 |
| **204** | No Solution | tree 内に解なし、別ライン試行 |
| **401** | Unauthorized | refresh → 失敗時手動更新 |
| **403** | PERMISSION_DENIED | subscription 範囲外、別 gametype/depth |
| **404** | Not Found | gametype が存在しない、名前確認 |
| **422** | Validation Error | preflop/flop_actions が tree 外、`action_solutions` から code 確認 |
| **429** | Rate Limit | バックオフ retry (実用上ほぼ出ない) |
| 500 | Server Error | 一定間隔で retry |

### 6.2 401 自動 refresh パターン

```python
def call_api(client, params, max_retries=5):
    backoff = 2.0
    for _ in range(max_retries):
        try:
            r = client.get(BASE_URL, params=params, timeout=30.0)
            if r.status_code == 200:
                return 200, r.json()
            if r.status_code == 401:
                new = refresh_access_token()
                if new:
                    client.headers["authorization"] = f"Bearer {new}"
                    continue
                return 401, None    # refresh 失敗、手動更新待ち
            if r.status_code == 429:
                time.sleep(backoff); backoff *= 2; continue
            return r.status_code, None
        except Exception:
            time.sleep(backoff); backoff *= 2
    return 0, None
```

### 6.3 422 対処: tree 外 action

`flop_actions=X-R2.0-C` を試して 422 が出る場合、その board の tree に `R2.0` が無い。
**先に空 flop_actions=X で fetch** → `action_solutions` から実際の `R*` code を取得して再 fetch。

```python
# Detect actual size code
data = call_api(params_with_X_only)
sizes = [s["action"]["code"] for s in data["action_solutions"]
         if s["action"]["code"].startswith("R")]
# Use smallest available size
size_code = sorted(sizes, key=lambda c: float(c[1:]))[0]
```

### 6.4 204 No Solution

- 一部の tree 枝で MTT6mSimple は解なし
- 観察例: 3BP HJvBB `X-R19.9-C` 後の turn は無解
- 対処: 別の preflop_actions or 別 gametype

---

## 7. レート制限と quota

### 7.1 実測 (大規模 fetch から)

| 観察 | 結果 |
|---|---|
| 0.3 秒間隔 | 問題なし、429 出ず |
| 連続 120 spots | block なし |
| 1 session で 1 token 内: ~120-200 spots fetch 可 |
| 429 出現頻度 | ほぼ無し |

### 7.2 Daily quota

| Tier | hands/月 |
|---|---:|
| FREE | ~300 (10/day × 30) |
| STARTER | 100 (cash 用) |
| PREMIUM | 100,000 (MTT 用) |
| (旧 ELITE) | ~850/24h 観測 |

実用上、数百 spots/日 なら quota は問題にならない。

### 7.3 推奨 fetch 速度

- 0.3 秒 sleep が安全
- 0.15 秒でも問題なかった
- バッチサイズ: **1 token cycle = 100-150 spots** が現実的上限

---

## 8. 実装パターン

### 8.1 ファイル構成

```
scripts/gto_wizard_study/
  .token              # access token (15 分有効)
  .refresh_token      # refresh token (5 年有効)
  .google_anal_id     # session-pair な ID
  fetch_smart.py      # 汎用 fetch + refresh
  API_NOTES.md        # 本ファイル
```

### 8.2 推奨 fetch script の骨格

```python
def collect(profile_name):
    profile = PROFILES[profile_name]
    raw_dir = FINDINGS / profile["raw_dir"]   # キャッシュ
    raw_dir.mkdir(parents=True, exist_ok=True)
    token = TOKEN_FILE.read_text().strip()
    with httpx.Client(headers=headers(token)) as client:
        for spot in TASKS:
            raw_path = raw_dir / f"{spot['id']}.json"
            if raw_path.exists():
                data = json.load(open(raw_path))   # cached
            else:
                status, data = call_api(client, spot_params)
                if status != 200:
                    log_failure(spot, status); continue
                with open(raw_path, "w") as f:
                    json.dump(data, f)
                time.sleep(0.3)
            results.append(compute_hand_agg(data))
    write_jsonl(out_file, results)
```

### 8.3 トラブル症状と対処早見表

| 症状 | 原因 | 対処 |
|---|---|---|
| 401 token expired | JWT exp < 0 or session 無効化 | refresh → 失敗時は手動再注入 |
| 401 連続 | refresh token も無効 (session ロスト) | curl 形式でユーザーから新トークン取得 |
| 403 PERMISSION_DENIED | subscription 範囲外 | 別 gametype/depth に切替 |
| 403 過去 OK の組合せ | 何らかの subscription 境界 | 手動再ログイン依頼 |
| 404 not found | gametype 名が無効 | 3.3 マトリクスで正確な名前確認 |
| 422 validation | preflop/flop_actions が tree 外 | 前段 fetch で `action_solutions` から code 取得 |
| 204 no solution | tree 内に解なし | 別ラインに変更、別 gametype |
| `strategy` 配列が空 | 想定外、ほぼ起きない | 別パラメータで再試行 |

---

## 9. UCBS-v2 + DCBS で取得した実測データ概要

### 9.1 取得した jsonl ファイル (mtt-postflop/findings/)

| ファイル | 用途 | spots |
|---|---|---:|
| draw_study_SRP*.jsonl, LIMP*.jsonl | 既存 (MTTGeneral 25bb) | 1,567 records |
| draw_study_3BP20.jsonl | 既存 3BP (MTTGeneral) | 213 |
| **draw_study_3BP25.jsonl** | 新規 3BP25 | 24 |
| **draw_study_3BP50.jsonl** | 新規 3BP50 | 24 |
| **draw_study_3BP100.jsonl** | 新規 3BP100 | 24 |
| **draw_study_MTT50BB.jsonl** | MTT 50bb 全 position | 120 |
| **draw_study_MTT100BB.jsonl** | MTT 100bb 全 position | 120 |
| **draw_study_MTT200BB.jsonl** | MTT 200bb 全 position | 120 |
| **draw_study_TURN_MTT25_BTN.jsonl** | Turn cbet | 30 |
| **draw_study_TURN_MTT50_BTN.jsonl** | Turn cbet | 30 |
| **draw_study_TURN_MTT100_BTN.jsonl** | Turn cbet | 23 |
| **draw_study_TURN_CASH100_BTN.jsonl** | Turn cbet cash | 30 |
| **draw_study_DEF_MTT25_BB.jsonl** | BB defense | 24 |
| **draw_study_DEF_MTT50_BB.jsonl** | BB defense | 24 |
| **draw_study_DEF_MTT100_BB.jsonl** | BB defense | 24 |
| **draw_study_DEF_CASH100_BB.jsonl** | BB defense cash | 24 |

合計 **1,000+ spots** (新規 ~600 spots)

### 9.2 fetch スクリプト

| ファイル | 役割 |
|---|---|
| `mtt-postflop/mtt100bb_draw_study.py` | Multi-profile flop cbet fetch (depth: 50/100/200, cash50/200, 3bp 25/50/100) |
| `mtt-postflop/turn_cbet_study.py` | Turn cbet fetch (4 profiles) |
| `mtt-postflop/bb_defense_study.py` | BB defense fetch (4 profiles) |
| `mtt-postflop/board_ras_collect.py` | (旧) RAS data |
| `mtt-postflop/cash6m_draw_study.py` | (旧) cash 100bb fetch |

### 9.3 全体精度

- UCBS-v2 (cbet, 13 contexts): 平均 WRMSE ~16%、最高 7.02% (turn_mtt25), 8.62% (3bp_50bb)
- DCBS (defense, 4 contexts): 平均 WRMSE ~15%

詳細は `knowledges/gto_wizard_study/UCBS_V2_DCBS_FINAL.md`。

---

## 10. 取得対象の選定指針

### 10.1 「迷わないポーカー」シリーズに必要な context

| 巻 | 必要 gametype | 取得状況 |
|---|---|---|
| vol1 cash preflop | (preflop only) | API 不要 |
| vol2 cash postflop | Cash6mGeneral_6mNL25R25 d=100 | ✓ 完備 |
| vol3 MTT preflop | (preflop only) | API 不要 |
| vol4 MTT postflop | MTT6mSimple d=25/50/100/200 | ✓ 完備 |
| vol5 tell/exploit | — | 計算式不要 |

### 10.2 取得しない方が良いもの (subscription 不要)

- Cash 200bb / 50bb / Zoom: 書籍ターゲット層が薄い
- 9-max: 主要市場は 6-max
- ICM PTT3 以上: PTT2 で十分

### 10.3 今後検討候補

- River cbet (Tier 4 リバー): turn と同じ構造で α だけ動くか?
- ICM bubble (Tier 5): MTTGeneral_ICM6m200PTT2 で取得可能
- OOP donk: 既存 b1_turn_donk/turn_donk_BB データあり

---

## 付録 A: cURL からトークン抽出パターン

ユーザーが gtowizard.com の Network タブで spot-solution リクエストを Copy as cURL したものから以下を抽出:

```bash
# Bearer の後ろの JWT
authorization: Bearer eyJhbGciOiJIUzI1NiIs...
                     ^^^^^^^^^^^^^^^^^^^^^^^ → .token に保存

# google-anal-id ヘッダーの値
google-anal-id: <opaque string>
                ^^^^^^^^^^^^^^^^ → .google_anal_id に保存
```

refresh_token の場合、`/v1/token/refresh/` への POST リクエストの body に `refresh` フィールドあり (上の `.refresh_token` に保存)。
