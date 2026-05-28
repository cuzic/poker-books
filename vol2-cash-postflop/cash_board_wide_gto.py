#!/usr/bin/env python3
"""
cash_board_wide_gto.py — 広範なボードタイプ × シナリオ 網羅調査

調査ボード:
  型1 ハイドライ   : A/K/Q/J-high × キッカー高低 (6 boards)
  型2 ハイウェット  : A/K/Q/J-high × FD/コネクテッド (6 boards)
  型3 ロードライ   : 既存 3 boards
  型4 ローウェット  : 既存 3 boards
  型5 モノトーン   : 既存 3 boards
  型6a ペア最高AA/KK: 既存 3 boards
  型6b ペア高 QQ/JJ : 新規 4 boards
  型6c ペア中 TT/99 : 新規 4 boards
  型7 ペア低       : 既存 3 boards
  合計: 35 boards × 4 シナリオ = 140 エントリ × 2 API コール ≈ 280 calls

1 エントリ = 2 API コール:
  ① flop_actions="X"         → IP サイズ分布 + IP CBet by 5-cat
  ② flop_actions="X-{code}"  → OOP defense (fold/call/raise) by 5-cat

チェックポイント: 途中終了 → 再実行で続きから再開 (完了済みエントリをスキップ)

使い方:
  TOKEN=eyJ... python3 cash_board_wide_gto.py
  TOKEN=eyJ... PHASE=SRP_IP python3 cash_board_wide_gto.py   # 特定シナリオのみ
  TOKEN=eyJ... TYPE=型6b_ペア高 python3 cash_board_wide_gto.py # 特定型のみ
"""

import os, sys, time
from pathlib import Path
from collections import defaultdict
from board_meta import get_board_meta
import gto_api
from gto_api import (
    api_get, get_code, is_bet_code, dominant_bet, action_dist, load_json, save_json,
    ip_player, HC_RAW_ORDER, DC_RAW_ORDER,
)

PHASE       = os.environ.get("PHASE", "all")   # "all" or scenario id e.g. "SRP_IP"
TYPE_FILTER = os.environ.get("TYPE", "")       # "" = all, or e.g. "型6b_ペア高"

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)
OUTPUT_JSON  = FINDINGS_DIR / "cash_board_wide_gto.json"

# ─────────────────── シナリオ定義 ───────────────────
SCENARIOS = [
    {
        "id":    "SRP_IP",
        "label": "SRP BTN vs BB (BTN=IP raiser)",
        "pf":    "F-F-F-R2.5-F-C",
        "ip":    "BTN", "oop": "BB",
        "depth": 100, "spr": "~8",
    },
    {
        "id":    "SRP_OOP",
        "label": "SRP SB vs BB (BB=IP caller)",
        "pf":    "F-F-F-F-R3-C",
        "ip":    "BB", "oop": "SB",
        "depth": 100, "spr": "~8",
    },
    {
        "id":    "3BP_IP",
        "label": "3BP CO vs BTN (BTN=IP 3bettor)",
        "pf":    "F-F-R2.5-R9-F-F-C",
        "ip":    "BTN", "oop": "CO",
        "depth": 100, "spr": "~5",
    },
    {
        "id":    "3BP_OOP",
        "label": "3BP BTN vs BB (BTN=IP caller vs 3bet)",
        "pf":    "F-F-F-R2.5-F-R9-C",
        "ip":    "BTN", "oop": "BB",
        "depth": 100, "spr": "~5",
    },
]

# ─────────────────── ボード定義 ───────────────────
# 型1 ハイドライ: A/K/Q/J-high × レインボー (キッカー高低)
# 型2 ハイウェット: A/K/Q/J-high × 2トーン / コネクテッド
# 型6b/6c: QQ/JJ/TT/99 パーボード (新規)
ALL_BOARDS = [
    # ── 型1 ハイドライ (6 boards) ──────────────────────────────────
    # トップカード × キッカー高低 のマトリクス
    {"type": "型1_ハイドライ",  "flop": "As9d3c",  "desc": "A高・中キッカー"},
    {"type": "型1_ハイドライ",  "flop": "Ah7d2c",  "desc": "A高・低キッカー"},
    {"type": "型1_ハイドライ",  "flop": "Ks7d2c",  "desc": "K高・低キッカー"},
    {"type": "型1_ハイドライ",  "flop": "Kd9s3c",  "desc": "K高・中キッカー"},
    {"type": "型1_ハイドライ",  "flop": "Qs7d2c",  "desc": "Q高・低キッカー"},
    {"type": "型1_ハイドライ",  "flop": "Jd8s3c",  "desc": "J高・ドライ"},

    # ── 型2 ハイウェット (6 boards) ────────────────────────────────
    # A/K/Q/J-high × FDのみ vs コネクテッド+FD
    {"type": "型2_ハイウェット", "flop": "Ah9d3s",  "desc": "A高・2トーン"},
    {"type": "型2_ハイウェット", "flop": "Kh9d5s",  "desc": "K高・2トーン"},
    {"type": "型2_ハイウェット", "flop": "Kh9s8d",  "desc": "K高・コネクテッド"},
    {"type": "型2_ハイウェット", "flop": "Qh8d3s",  "desc": "Q高・2トーン"},
    {"type": "型2_ハイウェット", "flop": "Jh8d4s",  "desc": "J高・2トーン"},
    {"type": "型2_ハイウェット", "flop": "Qd9s6h",  "desc": "Q高・コネクテッド"},

    # ── 型3 ロードライ (3 boards) ──────────────────────────────────
    {"type": "型3_ロードライ",  "flop": "Jd7s5c",  "desc": "J中・ドライ"},
    {"type": "型3_ロードライ",  "flop": "9s6d2c",  "desc": "9低・ドライ"},
    {"type": "型3_ロードライ",  "flop": "8d5s2c",  "desc": "8低・ドライ"},

    # ── 型4 ローウェット (3 boards) ────────────────────────────────
    {"type": "型4_ローウェット", "flop": "Th9s8d",  "desc": "T連携・2トーン"},
    {"type": "型4_ローウェット", "flop": "9h8d7s",  "desc": "9連続"},
    {"type": "型4_ローウェット", "flop": "Jd9s8h",  "desc": "J連携・2トーン"},

    # ── 型5 モノトーン (3 boards) ──────────────────────────────────
    {"type": "型5_モノトーン",   "flop": "Ah9h5h",  "desc": "A高モノ"},
    {"type": "型5_モノトーン",   "flop": "Kd7d3d",  "desc": "K高モノ"},
    {"type": "型5_モノトーン",   "flop": "Qh8h4h",  "desc": "Q中モノ"},

    # ── 型6a ペア最高 AA/KK (3 boards) ────────────────────────────
    {"type": "型6a_ペア最高",    "flop": "AsAcKd",  "desc": "AAK"},
    {"type": "型6a_ペア最高",    "flop": "KhKd8c",  "desc": "KK8"},
    {"type": "型6a_ペア最高",    "flop": "AhAdQs",  "desc": "AAQ"},

    # ── 型6b ペア高 QQ/JJ (4 boards, 新規) ────────────────────────
    # QQ/JJ は AA/KK より多くのハンドがペアを作れる → 異なる動き
    {"type": "型6b_ペア高",      "flop": "QhQd8c",  "desc": "QQ8ドライ"},
    {"type": "型6b_ペア高",      "flop": "QsQd3c",  "desc": "QQ3ドライ"},
    {"type": "型6b_ペア高",      "flop": "JhJd8c",  "desc": "JJ8ドライ"},
    {"type": "型6b_ペア高",      "flop": "JsJd4c",  "desc": "JJ4ドライ"},

    # ── 型6c ペア中 TT/99 (4 boards, 新規) ────────────────────────
    # TT/99 は更に多くのハンドがヒット、コネクテッド寄り
    {"type": "型6c_ペア中",      "flop": "ThTd6s",  "desc": "TT6"},
    {"type": "型6c_ペア中",      "flop": "ThTd3c",  "desc": "TT3"},
    {"type": "型6c_ペア中",      "flop": "9h9d5c",  "desc": "995"},
    {"type": "型6c_ペア中",      "flop": "9s9d8h",  "desc": "998コネクト"},

    # ── 型7 ペア低 (3 boards) ──────────────────────────────────────
    {"type": "型7_ペア低",       "flop": "7s7d2c",  "desc": "77低"},
    {"type": "型7_ペア低",       "flop": "4s4d9c",  "desc": "44中"},
    {"type": "型7_ペア低",       "flop": "5h5c2d",  "desc": "55低"},
]

# ─────────────────── 9類型マッピング（ナット強度グラデーション）───────────────────
# V1: ナッツ相当の完成手 (セット, ストレート, フラッシュ以上)
#     ※ ストレート/フラッシュはナット/非ナット判別不可だが強力なため V1 に分類
# V2: 強い完成手 (ツーペア, オーバーペア, トリップス)
# V3: 薄いバリュー (トップペア)
# D1: ナッツドロー (ナットFD, コンボドロー)
# D2: 通常ドロー (非ナットFD, OESD)
# D3: 弱いドロー (ガットショット, バックドア2枚)
# BC: ブラフキャッチャー (セカンドペア, アンダーペア, サードペア)
# Air: 外れ (ローペア以下, ハイカードのみ)
HC_9CAT = {
    "straight_flush": "V1", "quads":    "V1", "fullhouse": "V1",
    "flush":          "V1", "straight": "V1", "set":       "V1",
    "trips":          "V2", "two_pair": "V2", "overpair":  "V2",
    "top_pair":       "V3",
    "second_pair":    "BC", "underpair": "BC", "third_pair": "BC",
    "low_pair":       "Air", "ace_high":   "Air", "king_high":  "Air",
    "queen_high":     "Air", "jack_high":  "Air", "ten_high":   "Air",
    "no_made_hand":   "Air",
}
DC_9CAT = {
    "combo_draw":     "D1", "nut_flush_draw": "D1",
    "flush_draw":     "D2", "oesd":           "D2",
    "gutshot":        "D3", "twocards_bdfd":  "D3",
}
# ベット頻度が高い順に並べる（V1 > V2 > V3 > D1 > D2 > D3 > BC > Air が理論的期待）
CAT_ORDER = ["V1", "V2", "V3", "D1", "D2", "D3", "BC", "Air"]

# 5類型への集約マップ（後処理用 / 旧データとの互換）
CAT_TO_5 = {
    "V1": "V", "V2": "V", "V3": "V",
    "D1": "D", "D2": "D", "D3": "WD",
    "BC": "BC", "Air": "Air",
}



def collect_raw_ip(player, cbet_code):
    """players_info[1] (IP) から各生カテゴリの bet/check% を収集
    ベット/チェックノード専用"""
    result = {}
    for hc in player.get("hand_categories", []):
        n = hc.get("total_combos", 0)
        if n < 0.3: continue
        af  = hc.get("actions_total_frequencies", {})
        bet = af.get(cbet_code, 0.0)
        chk = af.get("X", 0.0)
        result[hc["name"]] = {
            "n":     round(n, 1),
            "bet":   round(bet * 100, 1),
            "check": round(chk * 100, 1),
        }
    for dc in player.get("draw_categories", []):
        n = dc.get("total_combos", 0)
        if n < 0.3: continue
        af  = dc.get("actions_total_frequencies", {})
        bet = af.get(cbet_code, 0.0)
        chk = af.get("X", 0.0)
        result[dc["name"]] = {
            "n":     round(n, 1),
            "bet":   round(bet * 100, 1),
            "check": round(chk * 100, 1),
        }
    return result

def collect_raw_oop(action_sols):
    """OOP の fold/call/raise% を生カテゴリ別に収集
    フォールド/コール/レイズノード専用"""
    cat_total   = defaultdict(float)
    cat_actions = defaultdict(lambda: defaultdict(float))

    for asol in action_sols:
        raw = get_code(asol)
        if not raw: continue
        if raw == "F":         name = "fold"
        elif raw == "C":       name = "call"
        elif is_bet_code(raw): name = "raise"
        else: continue

        for hc in asol.get("hand_categories", []):
            n = hc.get("total_combos", 0)
            if n < 0.3: continue
            cat_total[hc["name"]]         += n
            cat_actions[hc["name"]][name] += n
        for dc in asol.get("draw_categories", []):
            n = dc.get("total_combos", 0)
            if n < 0.3: continue
            cat_total[dc["name"]]         += n
            cat_actions[dc["name"]][name] += n

    result = {}
    for cat, total in cat_total.items():
        if total < 0.3: continue
        result[cat] = {"n": round(total, 1)}
        for act in ("fold", "call", "raise"):
            result[cat][act] = round(cat_actions[cat].get(act, 0) / total * 100, 1)
    return result

def aggregate_9cat(raw_ip):
    """生カテゴリデータを 9類型に集約（後処理用）"""
    buckets = {c: {"n": 0.0, "bet_sum": 0.0} for c in CAT_ORDER}
    for name, d in raw_ip.items():
        cat = HC_9CAT.get(name) or DC_9CAT.get(name)
        if not cat: continue
        n = d["n"]
        buckets[cat]["n"]       += n
        buckets[cat]["bet_sum"] += d["bet"] * n / 100
    result = {}
    for cat in CAT_ORDER:
        b = buckets[cat]
        n = b["n"]
        if n < 0.3: continue
        result[cat] = {"n": round(n, 1), "bet": round(b["bet_sum"] / n * 100, 1)}
    return result

def aggregate_9cat_oop(raw_oop):
    """OOP 生データを 9類型に集約（後処理用）"""
    buckets = {c: {"n": 0.0, "fold": 0.0, "call": 0.0, "raise": 0.0} for c in CAT_ORDER}
    for name, d in raw_oop.items():
        cat = HC_9CAT.get(name) or DC_9CAT.get(name)
        if not cat: continue
        n = d["n"]
        buckets[cat]["n"]     += n
        for act in ("fold", "call", "raise"):
            buckets[cat][act] += d.get(act, 0) * n / 100
    result = {}
    for cat in CAT_ORDER:
        b = buckets[cat]
        n = b["n"]
        if n < 0.3: continue
        result[cat] = {"n": round(n, 1)}
        for act in ("fold", "call", "raise"):
            result[cat][act] = round(b[act] / n * 100, 1)
    return result

load_results  = lambda: load_json(OUTPUT_JSON)
save_results  = lambda results: save_json(OUTPUT_JSON, results)

def is_done(results, flop, scenario_id):
    return any(r["flop"] == flop and r["scenario"] == scenario_id for r in results)

# ─────────────────── メイン調査ループ ───────────────────
def run():
    gto_api.update_session()
    results = load_results()
    done_count = len(results)

    # フィルタ適用
    boards = ALL_BOARDS
    if TYPE_FILTER:
        boards = [b for b in boards if b["type"] == TYPE_FILTER]
    scenarios = SCENARIOS
    if PHASE != "all":
        scenarios = [s for s in SCENARIOS if s["id"] == PHASE]

    total = len(boards) * len(scenarios)
    pending = [(b, s) for b in boards for s in scenarios
               if not is_done(results, b["flop"], s["id"])]

    print(f"ボード: {len(boards)}  シナリオ: {len(scenarios)}  "
          f"合計: {total}  完了済: {done_count}  残り: {len(pending)}")
    print(f"出力: {OUTPUT_JSON}\n")

    try:
        for idx, (bconf, scen) in enumerate(pending, 1):
            flop   = bconf["flop"]
            bt     = bconf["type"]
            pf     = scen["pf"]
            depth  = scen["depth"]
            label  = f"{bt} {flop} × {scen['id']}"

            # ── API コール ① : IP が直面するノード (check or bet) ──
            sols1 = api_get(flop, "X", pf, depth=depth)
            time.sleep(0.4)
            if not sols1:
                print(f"  SKIP (no data) {label}", file=sys.stderr)
                continue

            action_sols1 = sols1.get("action_solutions", [])
            cbet_code    = dominant_bet(action_sols1)
            ip_plr       = ip_player(sols1)

            if not ip_plr or not cbet_code:
                print(f"  SKIP (no IP player or no bet) {label}", file=sys.stderr)
                continue

            # IP サイズ分布 + 生カテゴリ別 bet%
            dist   = action_dist(action_sols1)
            ip_raw = collect_raw_ip(ip_plr, cbet_code)

            # ── API コール ② : OOP が IP ベットに直面するノード ──
            sols2 = api_get(flop, f"X-{cbet_code}", pf, depth=depth)
            time.sleep(0.4)
            oop_raw  = None
            cr_codes = []
            if sols2:
                action_sols2 = sols2.get("action_solutions", [])
                oop_raw  = collect_raw_oop(action_sols2)
                cr_codes = [get_code(a) for a in action_sols2 if is_bet_code(get_code(a))]

            entry = {
                "board_type":  bt,
                "flop":        flop,
                "desc":        bconf["desc"],
                "scenario":    scen["id"],
                "ip":          scen["ip"],
                "oop":         scen["oop"],
                "spr":         scen["spr"],
                "cbet_code":   cbet_code,
                "action_dist": dist,
                "board_meta":  get_board_meta(flop),  # ナット情報（API非依存）
                "ip_raw":      ip_raw,      # 生カテゴリ (GTO Wizard 粒度)
                "oop_raw":     oop_raw,     # 生カテゴリ (GTO Wizard 粒度)
                "cr_codes":    cr_codes,    # OOP が取れるレイズサイズ
                # 9類型集約 (後処理用)
                "ip_9cat":    aggregate_9cat(ip_raw),
                "oop_9cat":   aggregate_9cat_oop(oop_raw) if oop_raw else None,
            }
            results.append(entry)
            save_results(results)

            # 進捗表示（代表カテゴリのみ表示）
            def _i(name): return f"{ip_raw[name]['bet']:.0f}%" if name in ip_raw else "-"
            def _o(name, act):
                return f"{oop_raw[name].get(act,0):.0f}%" if oop_raw and name in oop_raw else "-"
            sizes_str = " ".join(f"{d['code']}={d['freq']:.0%}" for d in dist if is_bet_code(d["code"]))
            print(f"[{idx:3d}/{len(pending)}] {label}  [{sizes_str}]")
            print(f"  IP:  set={_i('set')} str={_i('straight')} 2p={_i('two_pair')} "
                  f"op={_i('overpair')} tp={_i('top_pair')} 2nd={_i('second_pair')} "
                  f"nfd={_i('nut_flush_draw')} fd={_i('flush_draw')} gs={_i('gutshot')} air={_i('no_made_hand')}")
            print(f"  OOP: set fold={_o('set','fold')}/call={_o('set','call')}/raise={_o('set','raise')}  "
                  f"tp fold={_o('top_pair','fold')}/call={_o('top_pair','call')}  "
                  f"2nd fold={_o('second_pair','fold')}/call={_o('second_pair','call')}")

    except RuntimeError as e:
        if "DAILY_QUOTA_EXCEEDED" in str(e):
            print(f"\n⚠ 日次クォータ超過 — {len(results)} エントリ保存済み", file=sys.stderr)
            save_results(results)
            sys.exit(2)
        raise

    print(f"\n完了: {len(results)} エントリ → {OUTPUT_JSON}")
    return results


# ─────────────────── サマリー出力 ───────────────────
def save_summary(results):
    path = FINDINGS_DIR / "cash_board_wide_gto_summary.md"
    SHORT_TYPE = {
        "型1_ハイドライ": "型1", "型2_ハイウェット": "型2",
        "型3_ロードライ": "型3", "型4_ローウェット": "型4",
        "型5_モノトーン": "型5", "型6a_ペア最高": "型6a",
        "型6b_ペア高": "型6b", "型6c_ペア中": "型6c",
        "型7_ペア低": "型7",
    }

    # カテゴリ説明
    CAT_DESC = {
        "V1": "V1(ナッツ相当:セット/ストレート/フラッシュ以上)",
        "V2": "V2(強:ツーペア/オーバーペア/トリップス)",
        "V3": "V3(薄:トップペア)",
        "D1": "D1(ナッツドロー:ナットFD/コンボD)",
        "D2": "D2(通常ドロー:FD/OESD)",
        "D3": "D3(弱ドロー:ガット/バックドア)",
        "BC": "BC(ブラフキャッチャー:セカンドペア以下)",
        "Air": "Air(外れ)",
    }

    lines = [
        "# キャッシュ フロップ広範調査サマリー（9類型）\n\n",
        "## カテゴリ定義\n\n",
        "| 略称 | 内容 |\n|---|---|\n",
    ]
    for k, v in CAT_DESC.items():
        lines.append(f"| {k} | {v} |\n")
    lines.append("\n**理論上の期待ベット順: V1 > V2 > V3 > D1 > D2 > D3 > BC > Air**\n\n")
    lines.append("※ ストレート/フラッシュはナット判別不可のため V1 に一括分類\n")
    lines.append("※ ナットFD と 通常FD は D1/D2 として区別\n\n---\n\n")

    for scen_id in ["SRP_IP", "SRP_OOP", "3BP_IP", "3BP_OOP"]:
        entries = [r for r in results if r["scenario"] == scen_id]
        if not entries:
            continue

        # ── IP CBet% (生カテゴリ) ──
        ip_cols = [n for n in HC_RAW_ORDER + DC_RAW_ORDER]
        # 実際にデータが存在するカテゴリのみ列に含める
        present = set()
        for e in entries:
            present.update(e.get("ip_raw", {}).keys())
        ip_cols = [c for c in ip_cols if c in present]

        lines.append(f"## {scen_id} — IP CBet% by 生カテゴリ\n\n")
        header = "| ボード型 | ボード | size | " + " | ".join(ip_cols) + " |\n"
        lines.append(header)
        lines.append("|---|---|---|" + "---|" * len(ip_cols) + "\n")
        for e in sorted(entries, key=lambda x: (x["board_type"], x["flop"])):
            bt       = SHORT_TYPE.get(e["board_type"], e["board_type"])
            dist     = e.get("action_dist", [])
            size_str = " ".join(f"{d['code']}={d['freq']:.0%}" for d in dist if is_bet_code(d["code"]))
            raw      = e.get("ip_raw", {})
            cols     = " | ".join(
                f"{raw[c]['bet']:.0f}%(n={raw[c]['n']:.0f})" if c in raw else "-"
                for c in ip_cols
            )
            lines.append(f"| {bt} | `{e['flop']}` {e['desc']} | {size_str} | {cols} |\n")

        # ── OOP Defense% (生カテゴリ) ──
        oop_cols = [n for n in HC_RAW_ORDER + DC_RAW_ORDER]
        present_oop = set()
        for e in entries:
            present_oop.update((e.get("oop_raw") or {}).keys())
        oop_cols = [c for c in oop_cols if c in present_oop]

        lines.append(f"\n### {scen_id} — OOP Defense% by 生カテゴリ\n\n")
        lines.append("| ボード型 | ボード | カテゴリ | Fold | Call | Raise | n |\n")
        lines.append("|---|---|---|---|---|---|---|\n")
        for e in sorted(entries, key=lambda x: (x["board_type"], x["flop"])):
            bt  = SHORT_TYPE.get(e["board_type"], e["board_type"])
            raw = e.get("oop_raw") or {}
            for cat in oop_cols:
                d = raw.get(cat)
                if not d: continue
                lines.append(
                    f"| {bt} | `{e['flop']}` | {cat} "
                    f"| {d.get('fold',0):.0f}% "
                    f"| {d.get('call',0):.0f}% "
                    f"| {d.get('raise',0):.0f}% "
                    f"| {d.get('n',0):.0f} |\n"
                )
        lines.append("\n")

    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"サマリー: {path}")


# ─────────────────── エントリポイント ───────────────────
if __name__ == "__main__":
    if not gto_api.TOKEN:
        print("ERROR: TOKEN 環境変数が未設定\n使い方: TOKEN=eyJ... python3 cash_board_wide_gto.py",
              file=sys.stderr)
        sys.exit(1)

    results = run()
    if results:
        save_summary(results)
    print("Done.")
