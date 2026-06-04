#!/usr/bin/env python3
"""
mtt_pairwise_study.py — MTT6mSimple 全軸ペアワイズ網羅調査

軸:
  SBR   : [10, 15, 20, 25, 50, 100, 200]          (スタック深さ)
  Pos   : [UTG, HJ, CO, BTN, SB]                  (ポジション / レンジ幅)
  Board : 12ボード × 型1-7 (2枚/型)               (ボードテクスチャ)

ペアワイズ (2-way) で全 (SBR×Pos), (SBR×Board), (Pos×Board) ペアを被覆する
最小テストケース集合を生成し、GTO Wizard MTT6mSimple API を呼び出す。

各レコードから抽出するもの:
  - cbet_pct   : 全レンジ平均ベット%
  - ras        : no_draw ベット% (Range Advantage Score プロキシ)
  - hand_agg   : ハンドカテゴリ別ベット%
  - draw_agg   : ドローカテゴリ別ベット%

使い方:
  TOKEN=xxx python3 mtt_pairwise_study.py --plan          # 計画を確認
  TOKEN=xxx python3 mtt_pairwise_study.py --collect       # 収集
  TOKEN=xxx python3 mtt_pairwise_study.py --collect --resume   # 再開
  TOKEN=xxx python3 mtt_pairwise_study.py --collect --sbr 25,50,200
  TOKEN=xxx python3 mtt_pairwise_study.py --collect --pos BTN,HJ,UTG
             python3 mtt_pairwise_study.py --analyze
             python3 mtt_pairwise_study.py --analyze --by-sbr
             python3 mtt_pairwise_study.py --analyze --by-position
             python3 mtt_pairwise_study.py --analyze --by-type
"""

import os, sys, json, time, argparse, itertools, base64, requests
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN = os.environ.get("TOKEN", "")
GAMETYPE    = "MTT6mSimple"
OUTPUT_DIR  = Path(__file__).parent / "findings" / "pairwise"
OUTPUT_FILE = OUTPUT_DIR / "mtt_pairwise.jsonl"
BASE_URL    = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─────────────────────────────────────────────────────────────
# パラメータ定義
# ─────────────────────────────────────────────────────────────

SBR_VALUES: list[int] = [10, 15, 20, 25, 30, 40, 50, 100, 200]

# 6-max 席順: LJ(UTG) → HJ → CO → BTN → SB → BB
# preflop_actions = 各プレイヤーのアクション列 (F/Rsize/C)
POSITION_CONFIGS: dict[str, dict] = {
    "UTG": {
        "pf": "R2.2-F-F-F-F-C",
        "label": "UTG-BB SRP",
        "range_pct": 15,
        "is_oop": False,   # UTG が IP (BBが OOP チェックしてから UTG が決断)
    },
    "HJ": {
        "pf": "F-R2.2-F-F-F-C",
        "label": "HJ-BB SRP",
        "range_pct": 18,
        "is_oop": False,
    },
    "CO": {
        "pf": "F-F-R2.2-F-F-C",
        "label": "CO-BB SRP",
        "range_pct": 25,
        "is_oop": False,
    },
    "BTN": {
        "pf": "F-F-F-R2.2-F-C",
        "label": "BTN-BB SRP",
        "range_pct": 48,
        "is_oop": False,
    },
    "SB": {
        "pf": "F-F-F-F-R3-C",
        "label": "SB-BB SRP",
        "range_pct": 30,
        "is_oop": True,    # SB が OOP → BB がフロップ IP で CBet
    },
}
POS_NAMES = list(POSITION_CONFIGS.keys())

# ボード定義: 型1〜型7、各2ボード (rainbow のみ)
STUDY_BOARDS: list[dict] = [
    # 型1: Ace dry (Aハイ、コネクティビティなし)
    {"board_id": "A94", "board": "Ah9d4s", "type": 1, "top_rank": 14, "label": "A-9-4"},
    {"board_id": "A72", "board": "Ah7d2s", "type": 1, "top_rank": 14, "label": "A-7-2"},
    # 型2: セミコネクト (Kハイ、中程度コネクティビティ)
    {"board_id": "K98", "board": "Kd9s8c", "type": 2, "top_rank": 13, "label": "K-9-8"},
    {"board_id": "Q83", "board": "Qh8d3s", "type": 2, "top_rank": 12, "label": "Q-8-3"},
    # 型3: OESD ウェット (高コネクティビティ)
    {"board_id": "T98", "board": "Th9s8d", "type": 3, "top_rank": 10, "label": "T-9-8"},
    {"board_id": "KJT", "board": "KhJdTs", "type": 3, "top_rank": 13, "label": "K-J-T"},
    # 型5: 断絶ハイカード (コネクティビティなし、Kハイ)
    {"board_id": "K72", "board": "Ks7d2c", "type": 5, "top_rank": 13, "label": "K-7-2"},
    {"board_id": "J73", "board": "Jh7d3s", "type": 5, "top_rank": 11, "label": "J-7-3"},
    # 型6: ローウェット (低カードコネクト)
    {"board_id": "765", "board": "7h6d5s", "type": 6, "top_rank": 7,  "label": "7-6-5"},
    {"board_id": "543", "board": "5h4d3s", "type": 6, "top_rank": 5,  "label": "5-4-3"},
    # 型7: ペアボード
    {"board_id": "KK8", "board": "KhKd8c", "type": 7, "top_rank": 13, "label": "K-K-8"},
    {"board_id": "772", "board": "7h7d2s", "type": 7, "top_rank": 7,  "label": "7-7-2"},
    # 追加: Q-high の位置確認用 (K-high パターンが Q でも成立するか)
    {"board_id": "Q98", "board": "Qh9d8s", "type": 2, "top_rank": 12, "label": "Q-9-8"},
    {"board_id": "Q72", "board": "Qh7d2s", "type": 5, "top_rank": 12, "label": "Q-7-2"},
    # 追加: 中段 OESD (T98 より低い帯域)
    {"board_id": "987", "board": "9h8d7s", "type": 3, "top_rank": 9,  "label": "9-8-7"},
]
BOARD_BY_ID  = {bd["board_id"]: bd for bd in STUDY_BOARDS}
BOARD_IDS    = [bd["board_id"] for bd in STUDY_BOARDS]
BOARD_TYPES  = sorted({bd["type"] for bd in STUDY_BOARDS})


# ─────────────────────────────────────────────────────────────
# ペアワイズ計画生成
# ─────────────────────────────────────────────────────────────

def generate_pairwise_plan(
    sbr_list: list[int] = SBR_VALUES,
    pos_list: list[str] = POS_NAMES,
    board_ids: list[str] = BOARD_IDS,
) -> list[tuple[int, str, str]]:
    """
    Greedy pairwise: (SBR×Pos), (SBR×Board), (Pos×Board) の全ペアを被覆する
    最小テストケース集合を返す。

    計算量: O(|tests| × |iterations|) = O(420 × 90) ≈ 38000 — 高速
    """
    # 被覆すべき全ペア
    required: set[tuple] = set()
    for s, p in itertools.product(sbr_list, pos_list):
        required.add(("sp", s, p))
    for s, b in itertools.product(sbr_list, board_ids):
        required.add(("sb", s, b))
    for p, b in itertools.product(pos_list, board_ids):
        required.add(("pb", p, b))

    all_tests = list(itertools.product(sbr_list, pos_list, board_ids))

    def pairs_of(s: int, p: str, b: str) -> frozenset:
        return frozenset({("sp", s, p), ("sb", s, b), ("pb", p, b)})

    covered: set[tuple] = set()
    selected: list[tuple] = []
    selected_set: set[tuple] = set()

    while covered < required:
        best: tuple | None = None
        best_gain = -1
        for t in all_tests:
            if t in selected_set:
                continue
            gain = len(pairs_of(*t) - covered)
            if gain > best_gain:
                best_gain, best = gain, t
        if best is None or best_gain == 0:
            break
        selected.append(best)
        selected_set.add(best)
        covered |= pairs_of(*best)

    missing = required - covered
    if missing:
        print(f"⚠️  被覆できないペア: {len(missing)} 件")

    return selected


# ─────────────────────────────────────────────────────────────
# API ユーティリティ
# ─────────────────────────────────────────────────────────────

def make_headers() -> dict[str, str]:
    h = {
        "accept":             "application/json, text/plain, */*",
        "accept-language":    "ja,en;q=0.9",
        "authorization":      f"Bearer {TOKEN}",
        "cache-control":      "no-cache",
        "origin":             "https://app.gtowizard.com",
        "pragma":             "no-cache",
        "referer":            "https://app.gtowizard.com/",
        "user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    gwcid = os.environ.get("GWCLIENTID", "")
    if gwcid:
        h["gwclientid"] = gwcid
    # CRITICAL: GOOGLE_ANAL_ID ヘッダーは絶対に設定しない (401 になる)
    return h


def token_remaining() -> float:
    """残り秒数を返す。不明の場合 999。"""
    if not TOKEN:
        return 0.0
    try:
        payload = TOKEN.split(".")[1] + "=="
        data = json.loads(base64.b64decode(payload + "=="))
        return max(0.0, data.get("exp", 0) - time.time())
    except Exception:
        return 999.0


def call_api(sbr: int, pos_key: str, board: str) -> dict | None:
    """
    GTO Wizard API を呼び出す。
    Returns:
      dict with "action_solutions" key → 成功
      {"_status": 204}                 → 解なし (スキップ)
      None                             → 認証エラー (終了)
    """
    depth  = float(sbr) + 0.125
    stacks = "-".join([f"{sbr}.125"] * 6)
    pf     = POSITION_CONFIGS[pos_key]["pf"]
    params: dict[str, Any] = {
        "gametype":        GAMETYPE,
        "depth":           str(depth),
        "stacks":          stacks,
        "preflop_actions": pf,
        "flop_actions":    "X",   # OOP チェック → IP が決断
        "turn_actions":    "",
        "river_actions":   "",
        "board":           board,
    }
    for attempt in range(3):
        try:
            r = requests.get(BASE_URL, params=params,
                             headers=make_headers(), timeout=30)
        except requests.RequestException as e:
            print(f"    network error: {e}")
            time.sleep(5)
            continue

        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 15))
            print(f"    429 rate-limit → {wait}s 待機")
            time.sleep(wait)
            continue
        if r.status_code in (401, 403):
            print(f"    {r.status_code} 認証エラー → トークン期限切れ")
            return None
        if r.status_code == 204:
            return {"_status": 204}
        print(f"    HTTP {r.status_code}: {r.text[:100]}")
        if attempt < 2:
            time.sleep(3)
    return {"_status": "error"}


# ─────────────────────────────────────────────────────────────
# CBet 集計
# ─────────────────────────────────────────────────────────────

def compute_cross(data: dict) -> dict[str, Any]:
    """
    draw_study.py と同一ロジック。
    (hand × draw) クロス集計 + draw_agg / hand_agg を返す。
    """
    dcr = data.get("draw_categories_range", [])
    hcr = data.get("hand_categories_range", [])
    as_ = data.get("action_solutions", [])

    draw_map: dict[int, str] = {}
    hand_map: dict[int, str] = {}
    strategies: dict[str, list[float]] = {}

    for item in as_:
        code = item["action"]["code"]
        strategies[code] = item.get("strategy", [])
        if not draw_map:
            for d in (item.get("draw_categories") or []):
                draw_map[d["index"]] = d["name"]
        if not hand_map:
            for h in (item.get("hand_categories") or []):
                hand_map[h["index"]] = h["name"]

    bet_codes = [c for c in strategies if c != "X"]
    cross     = defaultdict(list)
    draw_agg  = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    hand_agg  = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    n_in      = 0

    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001:
            continue
        n_in  += 1
        bet_f  = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        d_name = draw_map.get(dcr[i], f"unk_{dcr[i]}")
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")
        cross[(h_name, d_name)].append(bet_f)
        draw_agg[d_name]["total"] += 1
        draw_agg[d_name]["bet"]   += bet_f
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["bet"]   += bet_f

    return {
        "cross": {
            f"{h}|{d}": {"n": len(v), "avg": sum(v) / len(v) * 100 if v else 0}
            for (h, d), v in cross.items()
        },
        "draw_agg": {
            k: {"total": v["total"],
                "bet_pct": v["bet"] / v["total"] * 100 if v["total"] > 0 else 0}
            for k, v in draw_agg.items()
        },
        "hand_agg": {
            k: {"total": v["total"],
                "bet_pct": v["bet"] / v["total"] * 100 if v["total"] > 0 else 0}
            for k, v in hand_agg.items()
        },
        "n_combos": n_in,
    }


def overall_cbet(crs: dict) -> float:
    """全レンジ加重平均ベット%"""
    tot = bet = 0.0
    for d in crs["draw_agg"].values():
        tot += d["total"]
        bet += d["total"] * d["bet_pct"] / 100
    return bet / tot * 100 if tot > 0 else 0.0


# ─────────────────────────────────────────────────────────────
# データ永続化
# ─────────────────────────────────────────────────────────────

def load_existing() -> dict[tuple, dict]:
    existing: dict[tuple, dict] = {}
    if OUTPUT_FILE.exists():
        for line in OUTPUT_FILE.read_text().splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
                key = (rec["sbr"], rec["pos"], rec["board_id"])
                existing[key] = rec
            except (json.JSONDecodeError, KeyError):
                pass
    return existing


# ─────────────────────────────────────────────────────────────
# --plan: 計画を確認
# ─────────────────────────────────────────────────────────────

def cmd_plan(args):
    sbr_list   = [int(x) for x in args.sbr.split(",")] if args.sbr else SBR_VALUES
    pos_list   = args.pos.split(",")                    if args.pos else POS_NAMES
    board_ids  = BOARD_IDS

    plan = generate_pairwise_plan(sbr_list, pos_list, board_ids)
    full = len(sbr_list) * len(pos_list) * len(board_ids)

    print(f"=== ペアワイズ計画 ===")
    print(f"  SBR: {sbr_list}")
    print(f"  Pos: {pos_list}")
    print(f"  Boards: {len(board_ids)} 枚")
    print(f"  全組合せ: {full}")
    print(f"  ペアワイズ最小: {len(plan)} テストケース ({len(plan)/full*100:.0f}%)")
    print()

    # 被覆ペア数の確認
    n_sp = len(sbr_list) * len(pos_list)
    n_sb = len(sbr_list) * len(board_ids)
    n_pb = len(pos_list) * len(board_ids)
    print(f"  被覆対象ペア: SBR×Pos={n_sp} + SBR×Board={n_sb} + Pos×Board={n_pb} = {n_sp+n_sb+n_pb}")
    print()

    # SBR × Position の分布確認
    sbr_pos_covered: set = set()
    sbr_brd_covered: set = set()
    pos_brd_covered: set = set()
    for s, p, b in plan:
        sbr_pos_covered.add((s, p))
        sbr_brd_covered.add((s, b))
        pos_brd_covered.add((p, b))
    print(f"  被覆済み SBR×Pos: {len(sbr_pos_covered)}/{n_sp}")
    print(f"  被覆済み SBR×Board: {len(sbr_brd_covered)}/{n_sb}")
    print(f"  被覆済み Pos×Board: {len(pos_brd_covered)}/{n_pb}")
    print()

    # 最初の20件を表示
    print("  先頭20件:")
    for s, p, b in plan[:20]:
        bd = BOARD_BY_ID[b]
        print(f"    SBR={s:3d}  {p:3s}  {bd['label']:8s}  (型{bd['type']})")
    if len(plan) > 20:
        print(f"    ... (合計 {len(plan)} 件)")


# ─────────────────────────────────────────────────────────────
# --collect: データ収集
# ─────────────────────────────────────────────────────────────

def cmd_collect(args):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    sbr_list  = [int(x) for x in args.sbr.split(",")] if args.sbr else SBR_VALUES
    pos_list  = [p.strip() for p in args.pos.split(",")] if args.pos else POS_NAMES

    plan = generate_pairwise_plan(sbr_list, pos_list, BOARD_IDS)
    if args.full:
        plan = list(itertools.product(sbr_list, pos_list, BOARD_IDS))
        print(f"全網羅モード: {len(sbr_list)}SBR × {len(pos_list)}Pos × {len(BOARD_IDS)}Board = {len(plan)}組合せ")
    else:
        plan = generate_pairwise_plan(sbr_list, pos_list, BOARD_IDS)
        print(f"ペアワイズ計画: {len(plan)} テストケース")

    existing = load_existing() if args.resume else {}

    remaining = [(s, p, b) for (s, p, b) in plan
                 if (s, p, b) not in existing]

    print(f"既存データ: {len(existing)} 件  収集対象: {len(remaining)} 件")
    rem_sec = token_remaining()
    if rem_sec < 120:
        print(f"⚠️  トークン残り{rem_sec:.0f}秒 — 停止。TOKEN を更新して --resume で再開してください。")
        sys.exit(1)
    print(f"トークン残り: {rem_sec/60:.1f}分\n")

    done = skipped = errors = 0
    with OUTPUT_FILE.open("a") as fout:
        for idx, (sbr, pos_key, board_id) in enumerate(remaining):
            # トークン期限チェック (60秒切ったら停止)
            rem = token_remaining()
            if rem < 60:
                print(f"\n⚠️  トークン残り{rem:.0f}秒 — 停止。--resume で再開してください。")
                break

            bd = BOARD_BY_ID[board_id]
            print(f"  [{idx+1:3d}/{len(remaining)}] SBR={sbr:3d} {pos_key:3s} {bd['label']:8s}", end="  ", flush=True)

            data = call_api(sbr, pos_key, bd["board"])

            # 認証エラー → 終了
            if data is None:
                print("❌ 認証エラー — 停止")
                break

            # データなし (204/error) → スキップ記録
            status = data.get("_status")
            if status in (204, "error") or "action_solutions" not in data:
                label = "204 No Content" if status == 204 else str(status)
                print(f"⚫ {label}")
                rec = {
                    "sbr": sbr, "pos": pos_key, "board_id": board_id,
                    "board": bd["board"], "type": bd["type"],
                    "status": str(status), "cbet_pct": None,
                }
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
                skipped += 1
                time.sleep(0.3)
                continue

            # 正常データ → compute_cross
            crs  = compute_cross(data)
            cb   = overall_cbet(crs)
            ras  = crs["draw_agg"].get("no_draw", {}).get("bet_pct", 0.0)
            tp = crs["hand_agg"].get("top_pair",    {}).get("bet_pct")
            op = crs["hand_agg"].get("overpair",    {}).get("bet_pct")
            st = crs["hand_agg"].get("set",          {}).get("bet_pct")
            nd = crs["hand_agg"].get("no_made_hand", {}).get("bet_pct")

            extras = []
            if tp is not None: extras.append(f"TP={tp:.0f}%")
            if op is not None: extras.append(f"OP={op:.0f}%")
            if st is not None: extras.append(f"Set={st:.0f}%")
            if nd is not None: extras.append(f"Air={nd:.0f}%")
            print(f"✅ CBet={cb:.0f}%  RAS={ras:.0f}%  " + "  ".join(extras[:3]))

            rec = {
                "sbr":       sbr,
                "pos":       pos_key,
                "board_id":  board_id,
                "board":     bd["board"],
                "type":      bd["type"],
                "top_rank":  bd["top_rank"],
                "label":     bd["label"],
                "status":    "ok",
                "cbet_pct":  round(cb, 2),
                "ras":       round(ras, 2),
                "hand_agg":  {k: round(v["bet_pct"], 2) for k, v in crs["hand_agg"].items()},
                "draw_agg":  {k: round(v["bet_pct"], 2) for k, v in crs["draw_agg"].items()},
                "n_combos":  crs["n_combos"],
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            done += 1
            time.sleep(0.5)

    print(f"\n完了: 収集={done}件  スキップ={skipped}件  エラー={errors}件")
    print(f"出力: {OUTPUT_FILE}")


# ─────────────────────────────────────────────────────────────
# --analyze: 分析
# ─────────────────────────────────────────────────────────────

def load_records() -> list[dict]:
    if not OUTPUT_FILE.exists():
        print("データなし。先に --collect を実行してください。")
        sys.exit(1)
    records = []
    for line in OUTPUT_FILE.read_text().splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
            if rec.get("status") == "ok" and rec.get("cbet_pct") is not None:
                records.append(rec)
        except json.JSONDecodeError:
            pass
    return records


def pivot_table(records: list[dict], row_key: str, col_key: str,
                row_vals: list, col_vals: list, val_key: str = "cbet_pct") -> None:
    """pivot: rows=row_key, cols=col_key, cell=mean(val_key)"""
    data: dict[Any, dict[Any, list]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        rv = r.get(row_key)
        cv = r.get(col_key)
        vv = r.get(val_key)
        if rv in row_vals and cv in col_vals and vv is not None:
            data[rv][cv].append(vv)

    # ヘッダー
    col_w = max(len(str(c)) for c in col_vals)
    col_w = max(col_w, 5)
    row_w = max(len(str(r)) for r in row_vals) + 2

    header = " " * row_w + "  " + "  ".join(f"{str(c):>{col_w}s}" for c in col_vals)
    print(header)
    print("-" * len(header))
    for rv in row_vals:
        row = f"{str(rv):{row_w}s}  "
        for cv in col_vals:
            vals = data[rv][cv]
            if vals:
                row += f"{sum(vals)/len(vals):>{col_w}.0f}%"
            else:
                row += " " * col_w + "-"
            row += "  "
        print(row)


def cmd_analyze(args):
    records = load_records()
    print(f"分析対象: {len(records)} 件\n")

    # ── 1. SBR × Position (全ボード平均 CBet%)
    print("=== 1. CBet% — SBR × Position (全ボード平均) ===")
    pivot_table(records, "sbr", "pos", SBR_VALUES, POS_NAMES)
    print()

    # ── 2. SBR × Board type (全ポジション平均)
    print("=== 2. CBet% — SBR × Board型 (全ポジション平均) ===")
    # board_id → board type の変換が必要なので、type を直接使う
    type_records = [dict(r, board_type=r["type"]) for r in records]
    pivot_table(type_records, "sbr", "board_type",
                SBR_VALUES, BOARD_TYPES, "cbet_pct")
    print()

    # ── 3. Position × Board type
    print("=== 3. CBet% — Position × Board型 (全SBR平均) ===")
    pivot_table(type_records, "pos", "board_type",
                POS_NAMES, BOARD_TYPES, "cbet_pct")
    print()

    # ── 4. ポジション差: ディープ vs ショート
    if args.by_position or True:
        print("=== 4. ポジション差 — 200BB vs 25BB (ボード別) ===")
        for bd in STUDY_BOARDS:
            bid = bd["board_id"]
            bd_recs = [r for r in records if r["board_id"] == bid]
            if not bd_recs:
                continue
            print(f"\n  [{bd['label']} 型{bd['type']}]")
            for pos in POS_NAMES:
                deep = next((r["cbet_pct"] for r in bd_recs if r["sbr"] == 200 and r["pos"] == pos), None)
                shrt = next((r["cbet_pct"] for r in bd_recs if r["sbr"] == 25  and r["pos"] == pos), None)
                d_s = f"{deep:3.0f}%" if deep is not None else "  —"
                s_s = f"{shrt:3.0f}%" if shrt is not None else "  —"
                diff = f"{deep-shrt:+.0f}%" if (deep is not None and shrt is not None) else "  —"
                print(f"    {pos:3s}: 200BB={d_s}  25BB={s_s}  Δ={diff}")
        print()

    # ── 5. SBR 別詳細 (--by-sbr)
    if args.by_sbr:
        print("=== 5. SBR別詳細 — Position × Board ===")
        for target_sbr in SBR_VALUES:
            subset = [r for r in records if r["sbr"] == target_sbr]
            if not subset:
                continue
            print(f"\n  SBR={target_sbr}BB:  CBet% (Pos × Board)")
            bids = [bd["board_id"] for bd in STUDY_BOARDS]
            header = f"{'Pos':4s}  " + "  ".join(f"{b:>5s}" for b in bids)
            print("  " + header)
            print("  " + "-" * len(header))
            for pos in POS_NAMES:
                row = f"  {pos:4s}  "
                for bid in bids:
                    vals = [r["cbet_pct"] for r in subset if r["pos"] == pos and r["board_id"] == bid]
                    row += f"  {vals[0]:4.0f}%" if vals else "     -"
                print(row)

    # ── 6. ハンドタイプ別: Position × SBR の主要ハンド
    if args.by_type:
        print("=== 6. ハンドタイプ別 CBet% — 主要ハンド (全ボード平均) ===")
        hand_keys = ["top_pair", "overpair", "set", "two_pair", "second_pair", "no_made_hand"]
        for hk in hand_keys:
            hand_data: dict[int, dict[str, list]] = defaultdict(lambda: defaultdict(list))
            for r in records:
                ha = r.get("hand_agg", {})
                if hk in ha:
                    hand_data[r["sbr"]][r["pos"]].append(ha[hk])
            vals_exist = any(hand_data[s][p] for s in SBR_VALUES for p in POS_NAMES)
            if not vals_exist:
                continue
            print(f"\n  [{hk}]")
            header = f"{'SBR':5s}  " + "  ".join(f"{p:>5s}" for p in POS_NAMES)
            print("  " + header)
            for sbr in SBR_VALUES:
                row = f"  {sbr:5d}  "
                for pos in POS_NAMES:
                    vals = hand_data[sbr][pos]
                    row += f"  {sum(vals)/len(vals):4.0f}%" if vals else "     -"
                print(row)

    # ── 7. 収集状況サマリー
    print("\n=== 収集状況 ===")
    all_lines = []
    if OUTPUT_FILE.exists():
        all_lines = [l for l in OUTPUT_FILE.read_text().splitlines() if l.strip()]
    total_recs = len(all_lines)
    ok_recs    = len(records)
    skip_recs  = total_recs - ok_recs
    print(f"  全レコード: {total_recs}  (OK={ok_recs}, スキップ={skip_recs})")

    # 未収集ペアの確認
    plan = generate_pairwise_plan()
    existing_keys = {(r["sbr"], r["pos"], r["board_id"]) for r in records}
    missing_plan = [(s, p, b) for (s, p, b) in plan if (s, p, b) not in existing_keys]
    print(f"  ペアワイズ計画: {len(plan)} 件  未収集: {len(missing_plan)} 件")
    if missing_plan and len(missing_plan) <= 20:
        for s, p, b in missing_plan:
            print(f"    SBR={s:3d} {p:3s} {b}")


# ─────────────────────────────────────────────────────────────
# エントリーポイント
# ─────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description="MTT6mSimple 全軸ペアワイズ調査",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("--plan",        action="store_true", help="ペアワイズ計画を表示（API呼び出しなし）")
    ap.add_argument("--collect",     action="store_true", help="データ収集")
    ap.add_argument("--full",        action="store_true", help="全組合せ収集（ペアワイズではなく全件、--collect と組み合わせて使用）")
    ap.add_argument("--analyze",     action="store_true", help="収集済みデータを分析")
    ap.add_argument("--resume",      action="store_true", help="既存データを引き継いで再開")
    ap.add_argument("--sbr",         default="",          help="収集対象SBR (カンマ区切り: 25,50,200)")
    ap.add_argument("--pos",         default="",          help="収集対象ポジション (カンマ区切り: BTN,HJ,UTG)")
    ap.add_argument("--by-sbr",      action="store_true", help="SBR別詳細ピボット表を出力")
    ap.add_argument("--by-position", action="store_true", help="ポジション効果の詳細を出力")
    ap.add_argument("--by-type",     action="store_true", help="ハンドタイプ別CBet%を出力")

    args = ap.parse_args()

    if args.plan:
        cmd_plan(args)
    elif args.collect:
        if not TOKEN:
            print("ERROR: TOKEN 環境変数が未設定")
            sys.exit(1)
        cmd_collect(args)
    elif args.analyze:
        cmd_analyze(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
