#!/usr/bin/env python3
"""
board_ras_collect.py — ボード固有RAS調査用 GTO Wizard 収集スクリプト

【目的】
  ハイカード × テクスチャーの組み合わせを体系的に収集し、
  CBSの「ボード補正」に使えるRAS分布テーブルを作る。

【収集対象】
  - シナリオ: SRP25/SRP20/SRP25_SB/SRP20_SB/LIMP25_SB/LIMP20_SB
  - ボード: 既存13枚 + 新規追加 = 約45枚
  - 保存: findings/board_ras_{scenario}.jsonl

【使い方】
  TOKEN=xxx GWCLIENTID=xxx python3 board_ras_collect.py --scenario SRP25
  TOKEN=xxx GWCLIENTID=xxx python3 board_ras_collect.py --all
  python3 board_ras_collect.py --analyze        # 収集済みデータの分析

【出力JSONL形式】
  {"scenario":"SRP25", "board":"Ks7d2c", "board_id":"K72_rain",
   "high_cat":"K-high", "texture":"dry",
   "ras": 0.726, "hand_agg": {...}, "draw_agg": {...}}
"""

import os, sys, json, time, argparse
from pathlib import Path
from collections import defaultdict
from typing import Any

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
FINDINGS_DIR   = Path(__file__).parent / "findings"
BASE_URL       = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─── シナリオ定義 ───────────────────────────────────────────
SCENARIOS: dict[str, dict[str, Any]] = {
    "SRP25":      {"depth": 25.125, "pf": "F-F-F-F-F-R2.1-F-C", "label": "BTN-BB SBR25"},
    "SRP20":      {"depth": 20.125, "pf": "F-F-F-F-F-R2-F-C",   "label": "BTN-BB SBR20"},
    "SRP25_SB":   {"depth": 25.125, "pf": "F-F-F-F-F-F-R3-C",   "label": "SB-BB  SBR25"},
    "SRP20_SB":   {"depth": 20.125, "pf": "F-F-F-F-F-F-R3-C",   "label": "SB-BB  SBR20"},
    "LIMP25_SB":  {"depth": 25.125, "pf": "F-F-F-F-F-F-C-X",    "label": "LIMP   SBR25"},
    "LIMP20_SB":  {"depth": 20.125, "pf": "F-F-F-F-F-F-C-X",    "label": "LIMP   SBR20"},
}

# ─── ボードリスト（体系的なハイカード × テクスチャー網羅）───────────────
# texture: dry / semi-wet / wet-connected / monotone / paired
BOARDS: list[dict[str, str]] = [

    # ══════════════════════════════════════════════
    # A-high（エースハイ）
    # ══════════════════════════════════════════════
    {"id": "A72_dry",   "board": "Ah7d2s",  "high": "A-high", "tex": "dry",
     "note": "Aハイ レインボー ドライ（最もシンプル）"},
    {"id": "A72_wet",   "board": "Ad7c2d",  "high": "A-high", "tex": "semi-wet",
     "note": "Aハイ 2トーン ドライ"},
    {"id": "A94_dry",   "board": "Ah9d4s",  "high": "A-high", "tex": "semi-wet",
     "note": "Aハイ レインボー セミドライ"},
    {"id": "A94_wet",   "board": "Ad9c4d",  "high": "A-high", "tex": "semi-wet",
     "note": "Aハイ 2トーン セミドライ"},
    {"id": "A87_conn",  "board": "Ah8d7s",  "high": "A-high", "tex": "wet-connected",
     "note": "Aハイ ミッドコネクテッド"},
    {"id": "A65_conn",  "board": "Ah6d5s",  "high": "A-high", "tex": "wet-connected",
     "note": "Aハイ ローコネクテッド"},
    {"id": "AKQ_broad", "board": "AhKdQs",  "high": "A-high", "tex": "dry",
     "note": "ブロードウェイ3枚（最高位ボード）"},
    {"id": "AJT_conn",  "board": "AhJdTs",  "high": "A-high", "tex": "wet-connected",
     "note": "Aハイ ブロードウェイコネクテッド"},
    {"id": "A32_low",   "board": "Ah3d2s",  "high": "A-high", "tex": "dry",
     "note": "Aハイ ローカード"},
    {"id": "A_mono",    "board": "Ah9h5h",  "high": "A-high", "tex": "monotone",
     "note": "Aハイ モノトーン"},
    {"id": "AA7_pair",  "board": "AhAd7c",  "high": "A-high", "tex": "paired",
     "note": "Aペアボード"},

    # ══════════════════════════════════════════════
    # K-high（キングハイ）
    # ══════════════════════════════════════════════
    {"id": "K72_dry",   "board": "Ks7d2c",  "high": "K-high", "tex": "dry",
     "note": "Kハイ レインボー ドライ（標準）"},
    {"id": "K72_wet",   "board": "Kd7c2d",  "high": "K-high", "tex": "semi-wet",
     "note": "Kハイ 2トーン ドライ"},
    {"id": "K95_semi",  "board": "Kh9d5s",  "high": "K-high", "tex": "semi-wet",
     "note": "Kハイ セミドライ"},
    {"id": "K65_conn",  "board": "Kh6d5s",  "high": "K-high", "tex": "wet-connected",
     "note": "Kハイ ミッドコネクテッド"},
    {"id": "KJT_conn",  "board": "KhJdTs",  "high": "K-high", "tex": "wet-connected",
     "note": "Kハイ ブロードウェイコネクテッド"},
    {"id": "KJT_wet",   "board": "KdJcTd",  "high": "K-high", "tex": "wet-connected",
     "note": "Kハイ ブロードウェイコネクテッド 2トーン"},
    {"id": "K98_conn",  "board": "Kd9s8c",  "high": "K-high", "tex": "wet-connected",
     "note": "Kハイ ミッドコネクテッド"},
    {"id": "K_mono",    "board": "Kh8h3h",  "high": "K-high", "tex": "monotone",
     "note": "Kハイ モノトーン"},
    {"id": "KK5_pair",  "board": "KhKd5s",  "high": "K-high", "tex": "paired",
     "note": "Kペアボード"},

    # ══════════════════════════════════════════════
    # Q-high（クイーンハイ）
    # ══════════════════════════════════════════════
    {"id": "Q83_dry",   "board": "Qh8d3s",  "high": "Q-high", "tex": "semi-wet",
     "note": "Qハイ レインボー セミドライ（標準）"},
    {"id": "Q83_wet",   "board": "Qd8c3d",  "high": "Q-high", "tex": "semi-wet",
     "note": "Qハイ 2トーン セミドライ"},
    {"id": "Q72_dry",   "board": "Qh7d2s",  "high": "Q-high", "tex": "dry",
     "note": "Qハイ ドライ"},
    {"id": "QT8_conn",  "board": "QhTd8s",  "high": "Q-high", "tex": "wet-connected",
     "note": "Qハイ コネクテッド"},
    {"id": "Q_mono",    "board": "Qh7h2h",  "high": "Q-high", "tex": "monotone",
     "note": "Qハイ モノトーン"},
    {"id": "QQ8_pair",  "board": "QhQd8s",  "high": "Q-high", "tex": "paired",
     "note": "Qペアボード"},

    # ══════════════════════════════════════════════
    # J-high / T-high（ミッドハイ）
    # ══════════════════════════════════════════════
    {"id": "J73_dry",   "board": "Jh7d3s",  "high": "J-high", "tex": "dry",
     "note": "Jハイ レインボー ドライ"},
    {"id": "J73_wet",   "board": "Jd7c3d",  "high": "J-high", "tex": "semi-wet",
     "note": "Jハイ 2トーン ドライ"},
    {"id": "J95_semi",  "board": "Jh9d5s",  "high": "J-high", "tex": "semi-wet",
     "note": "Jハイ セミドライ"},
    {"id": "JT8_conn",  "board": "JhTd8s",  "high": "J-high", "tex": "wet-connected",
     "note": "Jハイ コネクテッド"},
    {"id": "J_mono",    "board": "Jh6h2h",  "high": "J-high", "tex": "monotone",
     "note": "Jハイ モノトーン"},
    {"id": "JJ6_pair",  "board": "JhJd6s",  "high": "J-high", "tex": "paired",
     "note": "Jペアボード"},

    {"id": "T64_dry",   "board": "Th6d4s",  "high": "T-high", "tex": "dry",
     "note": "Tハイ ドライ"},
    {"id": "T98_conn",  "board": "Th9s8d",  "high": "T-high", "tex": "wet-connected",
     "note": "Tハイ ローコネクテッド（最ウェット）"},
    {"id": "T98_wet",   "board": "Td9s8d",  "high": "T-high", "tex": "wet-connected",
     "note": "Tハイ コネクテッド 2トーン"},
    {"id": "T87_conn",  "board": "Th8d7s",  "high": "T-high", "tex": "wet-connected",
     "note": "Tハイ 超コネクテッド"},
    {"id": "T_mono",    "board": "Th9h8h",  "high": "T-high", "tex": "monotone",
     "note": "Tハイ コネクテッドモノトーン"},
    {"id": "TT5_pair",  "board": "ThTd5s",  "high": "T-high", "tex": "paired",
     "note": "Tペアボード"},

    # ══════════════════════════════════════════════
    # Low boards（9以下のハイカード）
    # ══════════════════════════════════════════════
    {"id": "974_dry",   "board": "9h7d4s",  "high": "low",    "tex": "dry",
     "note": "9ハイ ドライ"},
    {"id": "965_conn",  "board": "9h6d5s",  "high": "low",    "tex": "wet-connected",
     "note": "9ハイ コネクテッド"},
    {"id": "765_conn",  "board": "7h6d5s",  "high": "low",    "tex": "wet-connected",
     "note": "7ハイ 超コネクテッド"},
    {"id": "765_wet",   "board": "7d6c5d",  "high": "low",    "tex": "wet-connected",
     "note": "7ハイ コネクテッド 2トーン"},
    {"id": "742_dry",   "board": "7h4d2s",  "high": "low",    "tex": "dry",
     "note": "7ハイ ドライ"},
    {"id": "low_mono",  "board": "7h6h5h",  "high": "low",    "tex": "monotone",
     "note": "7ハイ コネクテッドモノトーン"},
    {"id": "77x_pair",  "board": "7h7d2s",  "high": "low",    "tex": "paired",
     "note": "7ペアボード"},
]

# ─── API ────────────────────────────────────────────────────

def make_headers() -> dict[str, str]:
    h: dict[str, str] = {
        "accept":          "application/json, text/plain, */*",
        "accept-language": "ja,en;q=0.9",
        "authorization":   f"Bearer {TOKEN}",
        "cache-control":   "no-cache",
        "origin":          "https://app.gtowizard.com",
        "referer":         "https://app.gtowizard.com/",
    }
    if GWCLIENTID:     h["gwclientid"]    = GWCLIENTID
    if GOOGLE_ANAL_ID: h["google-anal-id"] = GOOGLE_ANAL_ID
    return h

def call_api(board: str, depth: float, pf: str) -> dict | None:
    import requests
    params = {
        "gametype": GT, "depth": str(depth), "stacks": "",
        "preflop_actions": pf, "flop_actions": "X",
        "turn_actions": "", "river_actions": "", "board": board,
    }
    for attempt in range(4):
        try:
            r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        except Exception as e:
            print(f"    接続エラー: {e}"); time.sleep(5); continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            wait = int(r.headers.get("Retry-After", 15))
            print(f"    429 rate-limit: {wait}s 待機..."); time.sleep(wait); continue
        if r.status_code == 204:
            print(f"    204 No Content (このシナリオはデータなし)"); return None
        if r.status_code == 401:
            print(f"    401 Unauthorized"); return None
        print(f"    HTTP {r.status_code}")
        if attempt < 3: time.sleep(3)
    return None

def compute_agg(data: dict) -> dict | None:
    """API レスポンス → draw_agg / hand_agg を計算（RAS = no_draw bet_pct）"""
    dcr = data.get("draw_categories_range", [])
    hcr = data.get("hand_categories_range", [])
    as_ = data.get("action_solutions", [])
    if not as_: return None

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
    draw_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    hand_agg: dict[str, dict] = defaultdict(lambda: {"total": 0.0, "bet": 0.0})
    n = 0

    for i in range(min(1326, len(dcr), len(hcr))):
        total = sum(s[i] for s in strategies.values() if i < len(s))
        if total < 0.001: continue
        n += 1
        bet_f  = sum(strategies[c][i] for c in bet_codes if i < len(strategies[c]))
        d_name = draw_map.get(dcr[i], f"unk_{dcr[i]}")
        h_name = hand_map.get(hcr[i], f"unk_{hcr[i]}")
        draw_agg[d_name]["total"] += 1
        draw_agg[d_name]["bet"]   += bet_f
        hand_agg[h_name]["total"] += 1
        hand_agg[h_name]["bet"]   += bet_f

    return {
        "draw_agg": {k: {"total": v["total"],
                         "bet_pct": round(v["bet"]/v["total"]*100, 2) if v["total"] > 0 else 0}
                     for k, v in draw_agg.items()},
        "hand_agg": {k: {"total": v["total"],
                         "bet_pct": round(v["bet"]/v["total"]*100, 2) if v["total"] > 0 else 0}
                     for k, v in hand_agg.items()},
        "n_combos": n,
    }

# ─── 収集 ───────────────────────────────────────────────────

def collect(scenario_key: str, force: bool = False) -> None:
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}"); return
    cfg = SCENARIOS[scenario_key]
    outf = FINDINGS_DIR / f"board_ras_{scenario_key}.jsonl"
    FINDINGS_DIR.mkdir(exist_ok=True)

    # 既存データ読み込み
    existing: set[str] = set()
    if outf.exists() and not force:
        for line in outf.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                existing.add(rec.get("board_id", ""))

    print(f"\n=== COLLECT: {cfg['label']} ({scenario_key}) ===")
    print(f"  出力: {outf}")
    print(f"  対象: {len(BOARDS)}ボード（既存スキップ: {len(existing)}）\n")

    new_count = 0
    with outf.open("a") as fout:
        for bcfg in BOARDS:
            bid = bcfg["id"]
            if bid in existing:
                print(f"  ⏭  {bid:15s} スキップ")
                continue

            board = bcfg["board"]
            print(f"  ⬇  {bid:15s} {board} — {bcfg['note'][:30]}")
            data = call_api(board, depth=cfg["depth"], pf=cfg["pf"])
            if data is None:
                print(f"    ❌ スキップ")
                time.sleep(1)
                continue

            agg = compute_agg(data)
            if agg is None:
                print(f"    ❌ 集計失敗")
                continue

            nd = agg["draw_agg"].get("no_draw", {})
            ras = nd.get("bet_pct", 0) / 100.0
            print(f"    RAS={ras*100:.1f}%  combos={agg['n_combos']}")

            rec = {
                "scenario": scenario_key,
                "board_id":  bid,
                "board":     board,
                "high_cat":  bcfg["high"],
                "texture":   bcfg["tex"],
                "note":      bcfg["note"],
                "ras":       round(ras, 4),
                **agg,
            }
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            new_count += 1
            time.sleep(0.5)  # API レート制限対策

    print(f"\n  完了: {new_count}件追加 (合計 {len(existing)+new_count}件)")

# ─── 分析 ───────────────────────────────────────────────────

def analyze() -> None:
    all_data: list[dict] = []
    for path in sorted(FINDINGS_DIR.glob("board_ras_*.jsonl")):
        sc_key = path.stem.replace("board_ras_", "")
        for line in path.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                rec.setdefault("sc_key", sc_key)
                all_data.append(rec)

    if not all_data:
        # 既存 draw_study_*.jsonl からもRAS抽出して統合表示
        print("board_ras_*.jsonl が見つかりません。draw_study データのみ分析します。")
        return

    print(f"\n収集済み: {len(all_data)} レコード")

    # テクスチャー × シナリオ クロス表
    def sc_group(sc):
        if "LIMP" in sc: return "LIMP"
        if "SB" in sc:   return "SB"
        return "BTN"

    print("\n=== ハイカード × テクスチャー 別 平均RAS（SBシナリオ）===")
    sb_data = [r for r in all_data if sc_group(r.get("sc_key","")) == "SB"]
    textures = ["dry","semi-wet","wet-connected","monotone","paired"]
    highs    = ["A-high","K-high","Q-high","J-high","T-high","low"]
    print(f"  {'':10s}", end="")
    for t in textures:
        print(f"  {t[:9]:>9s}", end="")
    print()
    for h in highs:
        print(f"  {h:10s}", end="")
        for t in textures:
            recs = [r for r in sb_data if r.get("high_cat")==h and r.get("texture")==t]
            if recs:
                avg = sum(r["ras"] for r in recs)/len(recs)
                print(f"  {avg*100:8.1f}%", end="")
            else:
                print(f"  {'—':>8s}", end="")
        print()

    print("\n=== テクスチャー別 RAS分布（シナリオ別）===")
    for sc_g in ["BTN","SB","LIMP"]:
        recs = [r for r in all_data if sc_group(r.get("sc_key",""))==sc_g]
        if not recs: continue
        by_tex: dict[str, list] = defaultdict(list)
        for r in recs:
            by_tex[r.get("texture","?")].append(r["ras"])
        print(f"\n  {sc_g}:")
        for tex in textures:
            vals = by_tex.get(tex, [])
            if not vals: continue
            avg = sum(vals)/len(vals)
            rng = f"{min(vals)*100:.0f}-{max(vals)*100:.0f}%"
            print(f"    {tex:14s}: avg={avg*100:.1f}%  range={rng}  n={len(vals)}")

# ─── メイン ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=list(SCENARIOS.keys()),
                        help="収集するシナリオキー")
    parser.add_argument("--all",      action="store_true", help="全シナリオを収集")
    parser.add_argument("--analyze",  action="store_true", help="収集済みデータを分析")
    parser.add_argument("--force",    action="store_true", help="既存データを上書き")
    args = parser.parse_args()

    if args.analyze:
        analyze()
    elif args.all:
        for sc in SCENARIOS:
            collect(sc, force=args.force)
    elif args.scenario:
        collect(args.scenario, force=args.force)
    else:
        print("使い方:")
        print("  --scenario SRP25    # 指定シナリオを収集")
        print("  --all               # 全シナリオを収集")
        print("  --analyze           # 収集済みデータを分析")
        print(f"\n登録ボード数: {len(BOARDS)}")
        print(f"登録シナリオ: {list(SCENARIOS.keys())}")
        by_tex: dict[str, int] = defaultdict(int)
        by_high: dict[str, int] = defaultdict(int)
        for b in BOARDS:
            by_tex[b["tex"]] += 1
            by_high[b["high"]] += 1
        print(f"\nテクスチャー内訳:")
        for t, n in sorted(by_tex.items()):
            print(f"  {t:16s}: {n}枚")
        print(f"\nハイカード内訳:")
        for h, n in sorted(by_high.items()):
            print(f"  {h:10s}: {n}枚")

if __name__ == "__main__":
    main()
