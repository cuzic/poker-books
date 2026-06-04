#!/usr/bin/env python3
"""
mtt_preflop_gto.py — MTT プリフロップ GTO データ収集（Vol.3 検証 + マルチウェイ）

spot-solution に board='' で問い合わせ、MTT 8-max プリフロップ全アクション層を収集。
SBR 別（40/25/20/15）に対応。

フェーズ（PHASE 環境変数）:
  probe    :  1コール — レスポンス形式確認（要最初に実行）
  rfi      :  7コール — UTG/UTG1/LJ/HJ/CO/BTN/SB のオープン率
  vs_open  : 14コール — BB(6) + SB(5) + IP cold-call(3) の守備
  vs_3bet  : 12コール — オープン側の 3-bet 対応（fold/call/4bet）
  vs_4bet  :  5コール — 3-bet 側の 4-bet 対応（fold/call/5bet）
  vs_5bet  :  3コール — 4-bet 側の 5-bet 対応（fold/AI）
  multiway : 31コール — raise+call(1人/2人/3人/4人) 後の fold/call/3bet
  all      : 72コール — 上記すべて（デフォルト）

使い方:
  TOKEN=eyJ... GWCLIENTID=xxx GOOGLE_ANAL_ID=yyy python3 mtt_preflop_gto.py
  TOKEN=eyJ... SBR=40 PHASE=probe    python3 mtt_preflop_gto.py
  TOKEN=eyJ... SBR=25 PHASE=multiway python3 mtt_preflop_gto.py
  TOKEN=eyJ... SBR=40 PHASE=all      python3 mtt_preflop_gto.py
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN          = os.environ.get("TOKEN", "")
GWCLIENTID     = os.environ.get("GWCLIENTID", "")
GOOGLE_ANAL_ID = os.environ.get("GOOGLE_ANAL_ID", "")
GT             = "MTTGeneral"
SBR            = os.environ.get("SBR", "40")
PHASE          = os.environ.get("PHASE", "all")

FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"

# ─── SBR 設定 ──────────────────────────────────────────────────────
SBR_CONFIGS = {
    # NOTE: depth/open/SB_open/3bet_* は GTO Wizard MTT ツリーの実際値
    # probe コマンドで確認済みのものは ✓ を付ける
    #
    # SBR=40: depth=40.125 ✓
    #   open=R2.3 ✓, sb_open=R3.5 ✓
    #   3bet_ip=R6.9 ✓(CO/BTN), 3bet_sb=R8.6 ✓, 3bet_bb=R9.2 ✓
    #   opener vs 3bet = fold/call/RAI (no partial 4-bet) ✓
    # SBR=25: depth=25.125 ✓
    #   open=R2.1 ✓, sb_open=R3 ✓
    #   3bet_bb: vs BTN=R6.3, vs CO=R5.3 ✓ → primary=R6.3
    #   3bet_sb: vs BTN=R6.3 (需確認), 3bet_ip: BTN vs CO=R5.3 (需確認)
    # SBR=20: depth=20.125 ✓
    #   open=R2 ✓, sb_open=R3 ✓
    #   3bet_bb: vs BTN=R5/R7, vs CO=R6 ✓ → primary=R5
    #   3bet_sb: vs BTN=R5/R7 (BB=SBと同サイズと仮定)
    #   3bet_ip: 未確認
    # SBR=15: depth=15.125 → 403 (ツリーなし)
    "40": {"depth": 40.125, "label": "Deep(SBR40)",
           "open": "2.3",  "sb_open": "3.5",
           "3bet_ip": "6.9", "3bet_sb": "8.6", "3bet_bb": "9.2",
           "4bet": "RAI"},
    "25": {"depth": 25.125, "label": "Middle-Deep(SBR25)",
           "open": "2.1",  "sb_open": "3",
           "3bet_ip": "5",   "3bet_sb": "6",   "3bet_bb": "6.3",
           "4bet": "RAI"},  # open/sb_open/3bet_ip(BTN vs CO)/3bet_sb(SB vs BTN)/3bet_bb(BB vs BTN) 全確認済み
    "20": {"depth": 20.125, "label": "Middle(SBR20)",
           "open": "2",    "sb_open": "3",
           "3bet_ip": "4.5", "3bet_sb": "5",   "3bet_bb": "5",
           "4bet": "RAI"},  # open/sb_open/3bet_ip(BTN vs CO)/3bet_bb(BB vs BTN) 確認済み; 3bet_sb 未確認(BB=SBと仮定)
    # SBR=15: depth=15.125 → HTTP 403（ツリーなし）→ skip
}

if SBR not in SBR_CONFIGS:
    print(f"❌ SBR={SBR!r} は不正。有効値: {list(SBR_CONFIGS)} (SBR=15 は403/ツリーなし)"); sys.exit(1)

cfg    = SBR_CONFIGS[SBR]
DEPTH  = cfg["depth"]
OR     = cfg["open"]       # open raise size (string)
BB3_IP = cfg["3bet_ip"]    # IP 3-bet size (UTG1/LJ/HJ/CO/BTN)
BB3_SB = cfg["3bet_sb"]    # SB 3-bet size
BB3_BB = cfg["3bet_bb"]    # BB 3-bet size
BB4    = cfg["4bet"]       # 4-bet size ("RAI" for shallow MTT trees)
BB5    = "RAI" if BB4 == "RAI" else str(int(float(BB4) * 2.4))

# SB の open（SBR 別で異なる）
SB_OR = cfg["sb_open"]

# ─── 8-max プリフロップスポット定義 ────────────────────────────────
# 8-max 位置順: UTG(1) UTG1(2) LJ(3) HJ(4) CO(5) BTN(6) SB(7) BB(8)
# NOTE: probe で actor の正式名称を確認すること（LJ=UTG? UTG+1?）

R     = f"R{OR}"      # open raise, e.g. "R2.3"
R3_IP = f"R{BB3_IP}"  # IP 3-bet (UTG1/LJ/HJ/CO/BTN)
R3_SB = f"R{BB3_SB}"  # SB 3-bet
R3_BB = f"R{BB3_BB}"  # BB 3-bet
R4    = BB4 if BB4 == "RAI" else f"R{BB4}"   # 4-bet (RAI in shallow MTT)
R5    = BB5 if BB5 == "RAI" else f"R{BB5}"   # 5-bet
RS    = f"R{SB_OR}"   # SB open

RFI_SPOTS = [
    # 7ポジション全部（8-maxは BTN まで5フォールド分）
    {"label": "UTG RFI",  "pf": "",              "actor": "UTG"},
    {"label": "UTG1 RFI", "pf": "F",             "actor": "UTG1"},
    {"label": "LJ RFI",   "pf": "F-F",           "actor": "LJ"},
    {"label": "HJ RFI",   "pf": "F-F-F",         "actor": "HJ"},
    {"label": "CO RFI",   "pf": "F-F-F-F",       "actor": "CO"},
    {"label": "BTN RFI",  "pf": "F-F-F-F-F",     "actor": "BTN"},
    {"label": "SB RFI",   "pf": "F-F-F-F-F-F",   "actor": "SB"},
]

VS_OPEN_SPOTS = [
    # 8-max 位置順: UTG(1) UTG1(2) LJ(3) HJ(4) CO(5) BTN(6) SB(7) BB(8)
    # BB は最後なので前の 7 ポジションが (raise + folds) で埋まる = 7要素
    # BB defense vs 全6ポジション（fold/call/3bet）
    {"label": "BB vs UTG",  "pf": f"{R}-F-F-F-F-F-F",  "actor": "BB"},  # UTG1..SB が fold (6F)
    {"label": "BB vs UTG1", "pf": f"F-{R}-F-F-F-F-F",  "actor": "BB"},  # LJ..SB が fold (5F)
    {"label": "BB vs LJ",   "pf": f"F-F-{R}-F-F-F-F",  "actor": "BB"},  # HJ..SB が fold (4F)
    {"label": "BB vs HJ",   "pf": f"F-F-F-{R}-F-F-F",  "actor": "BB"},  # CO..SB が fold (3F)
    {"label": "BB vs CO",   "pf": f"F-F-F-F-{R}-F-F",  "actor": "BB"},  # BTN/SB が fold (2F)
    {"label": "BB vs BTN",  "pf": f"F-F-F-F-F-{R}-F",  "actor": "BB"},  # SB が fold (1F) ✓
    # SB は 7 番目。前の 6 ポジションが (raise + folds) = 6 要素
    # SB defense vs 5ポジション（fold/call/3bet）
    {"label": "SB vs UTG",  "pf": f"{R}-F-F-F-F-F",    "actor": "SB"},  # UTG1..BTN が fold (5F)
    {"label": "SB vs UTG1", "pf": f"F-{R}-F-F-F-F",    "actor": "SB"},  # LJ..BTN が fold (4F)
    {"label": "SB vs LJ",   "pf": f"F-F-{R}-F-F-F",    "actor": "SB"},  # HJ..BTN が fold (3F)
    {"label": "SB vs HJ",   "pf": f"F-F-F-{R}-F-F",    "actor": "SB"},  # CO/BTN が fold (2F)
    {"label": "SB vs BTN",  "pf": f"F-F-F-F-F-{R}",    "actor": "SB"},  # BTN が raise (0F after) ✓
    # IP cold-call（BTN=6番目, CO=5番目）
    {"label": "BTN vs UTG", "pf": f"{R}-F-F-F-F",       "actor": "BTN"},  # UTG1/LJ/HJ/CO が fold (4F)
    {"label": "CO vs UTG",  "pf": f"{R}-F-F-F",         "actor": "CO"},   # UTG1/LJ/HJ が fold (3F)
    {"label": "BTN vs LJ",  "pf": f"F-F-{R}-F-F",       "actor": "BTN"},  # HJ/CO が fold (2F)
]

VS_3BET_SPOTS = [
    # オープン側の 3-bet 対応（fold/call/4bet）
    # 8-max: 3-bet後に残りプレイヤーが全フォールドしてからオープナーが応答
    # UTG オープン vs 各ポジション 3-bet
    {"label": "UTG vs UTG1 3bet", "pf": f"{R}-{R3_IP}-F-F-F-F-F-F", "actor": "UTG"},  # UTG1=IP
    {"label": "UTG vs LJ 3bet",  "pf": f"{R}-F-{R3_IP}-F-F-F-F-F",  "actor": "UTG"},  # LJ=IP
    {"label": "UTG vs BTN 3bet", "pf": f"{R}-F-F-F-F-{R3_IP}-F-F",  "actor": "UTG"},  # BTN=IP
    {"label": "UTG vs BB 3bet",  "pf": f"{R}-F-F-F-F-F-F-{R3_BB}",  "actor": "UTG"},  # BB
    # HJ オープン vs 3-bet
    {"label": "HJ vs CO 3bet",   "pf": f"F-F-F-{R}-{R3_IP}-F-F-F",  "actor": "HJ"},   # CO=IP
    {"label": "HJ vs BB 3bet",   "pf": f"F-F-F-{R}-F-F-F-{R3_BB}",  "actor": "HJ"},   # BB
    # CO オープン vs 3-bet
    {"label": "CO vs BTN 3bet",  "pf": f"F-F-F-F-{R}-{R3_IP}-F-F",  "actor": "CO"},   # BTN=IP
    {"label": "CO vs BB 3bet",   "pf": f"F-F-F-F-{R}-F-F-{R3_BB}",  "actor": "CO"},   # BB
    # BTN オープン vs 3-bet
    {"label": "BTN vs SB 3bet",  "pf": f"F-F-F-F-F-{R}-{R3_SB}-F",  "actor": "BTN"},  # SB
    {"label": "BTN vs BB 3bet",  "pf": f"F-F-F-F-F-{R}-F-{R3_BB}",  "actor": "BTN"},  # BB
    # SB オープン vs BB 3-bet
    {"label": "SB vs BB 3bet",   "pf": f"F-F-F-F-F-F-{RS}-{R3_BB}", "actor": "SB"},   # BB
    # CO vs SB 3-bet（SBR に応じた squeeze 対応）
    {"label": "CO vs SB 3bet",   "pf": f"F-F-F-F-{R}-F-{R3_SB}-F",  "actor": "CO"},   # SB
]

VS_4BET_SPOTS = [
    # 3-bet 側の 4-bet/shove 対応（MTT tree: opener の re-raise = RAI のみ）
    # pf: open + 3-bet + RAI(opener shove) → 3-bettor が fold or call
    {"label": "BB vs UTG shove",  "pf": f"{R}-F-F-F-F-F-F-{R3_BB}-RAI", "actor": "BB"},    # BB 3bet vs UTG shove
    {"label": "BB vs CO shove",   "pf": f"F-F-F-F-{R}-F-F-{R3_BB}-RAI", "actor": "BB"},    # BB 3bet vs CO shove
    {"label": "BB vs BTN shove",  "pf": f"F-F-F-F-F-{R}-F-{R3_BB}-RAI", "actor": "BB"},    # BB 3bet vs BTN shove
    {"label": "SB vs BTN shove",  "pf": f"F-F-F-F-F-{R}-{R3_SB}-F-RAI", "actor": "SB"},   # SB 3bet vs BTN shove
    {"label": "BTN vs CO shove",  "pf": f"F-F-F-F-{R}-{R3_IP}-F-F-RAI", "actor": "BTN"},  # BTN 3bet vs CO shove
]

VS_5BET_SPOTS = [
    # MTT: 3-bet → RAI(opener shove) → caller の respond は fold/call のみ
    # RAI-RAI シーケンスは 5-bet に相当; actorは shove を呼んだ 3-bettor
    # (実際には VS_4BET の actor=BB が fold or call RAI する場面と同じ)
    # MTT では独立した 5-bet size は存在しないため、このフェーズは通常 204
    {"label": "UTG vs BB shove+call", "pf": f"{R}-F-F-F-F-F-F-{R3_BB}-RAI-RAI", "actor": "UTG"},
    {"label": "BTN vs BB shove+call", "pf": f"F-F-F-F-F-{R}-F-{R3_BB}-RAI-RAI", "actor": "BTN"},
    {"label": "BTN vs SB shove+call", "pf": f"F-F-F-F-F-{R}-{R3_SB}-F-RAI-RAI", "actor": "BTN"},
]

MULTIWAY_PRE_SPOTS = [
    # ── raise + 1 caller: 残りポジションの fold/call/3bet ─────────
    # UTG raises + UTG1 calls → 残り IP が決断（8-max: LJ/HJ/CO/BTN/SB が fold して各ポジション到達）
    {"label": "LJ vs UTG+UTG1",   "pf": f"{R}-C",               "actor": "LJ"},   # 2要素→LJ(3)
    {"label": "BTN vs UTG+UTG1",  "pf": f"{R}-C-F-F-F",         "actor": "BTN"},  # 5要素→BTN(6)
    {"label": "SB vs UTG+UTG1",   "pf": f"{R}-C-F-F-F-F",       "actor": "SB"},   # 6要素→SB(7)
    {"label": "BB vs UTG+UTG1",   "pf": f"{R}-C-F-F-F-F-F",     "actor": "BB"},   # 7要素→BB(8)
    # UTG raises + LJ calls（UTG1 fold）→ HJ/BTN/BB
    {"label": "HJ vs UTG+LJ",     "pf": f"{R}-F-C",             "actor": "HJ"},   # 3要素→HJ(4)
    {"label": "BTN vs UTG+LJ",    "pf": f"{R}-F-C-F-F",         "actor": "BTN"},  # 5要素→BTN(6)
    {"label": "BB vs UTG+LJ",     "pf": f"{R}-F-C-F-F-F-F",     "actor": "BB"},   # 7要素→BB(8)
    # HJ raises + CO calls → BTN/SB/BB
    {"label": "BTN vs HJ+CO",     "pf": f"F-F-F-{R}-C",       "actor": "BTN"},
    {"label": "SB vs HJ+CO",      "pf": f"F-F-F-{R}-C-F",     "actor": "SB"},
    {"label": "BB vs HJ+CO",      "pf": f"F-F-F-{R}-C-F-F",   "actor": "BB"},
    # CO raises + BTN calls → SB/BB
    {"label": "SB vs CO+BTN",     "pf": f"F-F-F-F-{R}-C",     "actor": "SB"},
    {"label": "BB vs CO+BTN",     "pf": f"F-F-F-F-{R}-C-F",   "actor": "BB"},
    # BTN raises + SB calls → BB
    {"label": "BB vs BTN+SB",     "pf": f"F-F-F-F-F-{R}-C",   "actor": "BB"},

    # ── raise + 2 callers: 残りポジションの fold/call/3bet ────────
    # UTG raises + UTG1+LJ call → HJ/BTN/BB（8-max fold counts）
    {"label": "HJ vs UTG+UTG1+LJ", "pf": f"{R}-C-C",           "actor": "HJ"},   # 3要素→HJ(4)
    {"label": "BTN vs UTG+UTG1+LJ","pf": f"{R}-C-C-F-F",       "actor": "BTN"},  # 5要素→BTN(6)
    {"label": "BB vs UTG+UTG1+LJ", "pf": f"{R}-C-C-F-F-F-F",   "actor": "BB"},   # 7要素→BB(8)
    # LJ raises + HJ+CO call → BTN/SB/BB
    {"label": "BTN vs LJ+HJ+CO",  "pf": f"F-F-{R}-C-C",       "actor": "BTN"},
    {"label": "SB vs LJ+HJ+CO",   "pf": f"F-F-{R}-C-C-F",     "actor": "SB"},
    {"label": "BB vs LJ+HJ+CO",   "pf": f"F-F-{R}-C-C-F-F",   "actor": "BB"},
    # HJ raises + CO+BTN call → SB/BB
    {"label": "SB vs HJ+CO+BTN",  "pf": f"F-F-F-{R}-C-C",     "actor": "SB"},
    {"label": "BB vs HJ+CO+BTN",  "pf": f"F-F-F-{R}-C-C-F",   "actor": "BB"},
    # CO raises + BTN+SB call → BB
    {"label": "BB vs CO+BTN+SB",  "pf": f"F-F-F-F-{R}-C-C",   "actor": "BB"},

    # ── raise + 3 callers: SB/BB の fold/call/3bet ──────────────
    # UTG raises + UTG1+LJ+HJ call → CO/BTN/BB
    {"label": "CO vs UTG+3C",     "pf": f"{R}-C-C-C",         "actor": "CO"},
    {"label": "BTN vs UTG+3C",    "pf": f"{R}-C-C-C-F",       "actor": "BTN"},
    {"label": "BB vs UTG+3C",     "pf": f"{R}-C-C-C-F-F-F",   "actor": "BB"},
    # LJ raises + HJ+CO+BTN call → SB/BB
    {"label": "SB vs LJ+3C",      "pf": f"F-F-{R}-C-C-C",     "actor": "SB"},
    {"label": "BB vs LJ+3C",      "pf": f"F-F-{R}-C-C-C-F",   "actor": "BB"},
    # HJ raises + CO+BTN+SB call → BB
    {"label": "BB vs HJ+3C",      "pf": f"F-F-F-{R}-C-C-C",   "actor": "BB"},

    # ── raise + 4 callers: BB/SB が最終判断 ─────────────────────
    # UTG raises + UTG1+LJ+HJ+CO call → BTN/SB/BB
    {"label": "BTN vs UTG+4C",    "pf": f"{R}-C-C-C-C",       "actor": "BTN"},
    {"label": "BB vs UTG+4C",     "pf": f"{R}-C-C-C-C-F-F",   "actor": "BB"},
]

ALL_PHASES = [
    ("rfi",      RFI_SPOTS,         "RFI — 各ポジションのオープン"),
    ("vs_open",  VS_OPEN_SPOTS,     "vs Single Raise — BB/SB/IP の守備"),
    ("vs_3bet",  VS_3BET_SPOTS,     "vs 3-bet — オープン側の対応"),
    ("vs_4bet",  VS_4BET_SPOTS,     "vs 4-bet — 3-bet 側の対応"),
    ("vs_5bet",  VS_5BET_SPOTS,     "vs 5-bet — 4-bet 側の対応"),
    ("multiway", MULTIWAY_PRE_SPOTS,"マルチウェイ — raise+call(1/2/3/4人) 後の fold/call/3bet"),
]

# ─── 本書スコア式（検証用）─────────────────────────────────────────
# MTT は SBR 依存の T_open（既存 mtt-preflop 章より）
T_OPEN_MTT = {
    "40": {"UTG": 26, "UTG1": 24, "LJ": 22, "HJ": 20, "CO": 18, "BTN": 16, "SB": 24},
    "25": {"UTG": 27, "UTG1": 25, "LJ": 23, "HJ": 21, "CO": 19, "BTN": 17, "SB": 26},
    "20": {"UTG": 28, "UTG1": 26, "LJ": 24, "HJ": 22, "CO": 20, "BTN": 18, "SB": 28},
    "15": {"UTG": 30, "UTG1": 28, "LJ": 26, "HJ": 24, "CO": 22, "BTN": 20, "SB": 30},
}

# ─── 共通関数 ──────────────────────────────────────────────────────
def check_token():
    import base64 as _b64
    try:
        payload = TOKEN.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(_b64.urlsafe_b64decode(payload))
        exp = data.get("exp", 0)
        remaining = exp - time.time()
        if remaining <= 60:
            print(f"❌ TOKEN 期限切れ（残り{remaining:.0f}秒）"); sys.exit(1)
        print(f"✅ TOKEN OK（残り{remaining/60:.1f}分）")
    except Exception as e:
        print(f"❌ TOKEN パース失敗: {e}"); sys.exit(1)

def make_headers():
    h = {
        "accept":             "application/json, text/plain, */*",
        "accept-language":    "ja,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "authorization":      f"Bearer {TOKEN}",
        "cache-control":      "no-cache",
        "origin":             "https://app.gtowizard.com",
        "pragma":             "no-cache",
        "priority":           "u=1, i",
        "referer":            "https://app.gtowizard.com/",
        "sec-ch-ua":          '"Chromium";v="148", "Microsoft Edge";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile":   "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest":     "empty",
        "sec-fetch-mode":     "cors",
        "sec-fetch-site":     "same-site",
        "user-agent":         "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0",
    }
    if GWCLIENTID:     h["gwclientid"]     = GWCLIENTID
    if GOOGLE_ANAL_ID: h["google-anal-id"] = GOOGLE_ANAL_ID
    return h

def call_api(pf_actions: str):
    params = {
        "gametype":        GT,
        "depth":           str(DEPTH),
        "stacks":          "",
        "preflop_actions": pf_actions,
        "flop_actions":    "",
        "turn_actions":    "",
        "river_actions":   "",
        "board":           "",
    }
    for attempt in range(4):
        r = requests.get(BASE_URL, params=params, headers=make_headers(), timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code == 401:
            # google-anal-id has ~5 min TTL; retry without it
            h = make_headers()
            h.pop("google-anal-id", None)
            r = requests.get(BASE_URL, params=params, headers=h, timeout=30)
            if r.status_code == 200:
                return r.json()
        if r.status_code == 429:
            try:
                body = r.json()
                if body.get("time_period_in_seconds", 0) >= 86400:
                    ra = r.headers.get("Retry-After", "?")
                    print(f"  ❌ 日次クォータ超過 (limit={body['request_limit']}, {int(ra)//3600}時間後リセット)")
                    sys.exit(1)
            except Exception:
                pass
            wait = 10 * (attempt + 1)
            print(f"  [429] pf={pf_actions!r} → {wait}s 待機...")
            time.sleep(wait)
            continue
        print(f"  [HTTP {r.status_code}] pf={pf_actions!r}")
        return None
    return None

def get_player(data, pos):
    for p in data.get("players_info", []):
        player = p.get("player", {})
        if isinstance(player, dict) and player.get("position") == pos:
            return p
    return None

def classify_actions(sols):
    codes = {}
    for s in sols:
        a = s["action"]
        t, c = a["type"], a["code"]
        bp = float(a.get("betsize_by_pot") or 0)
        if   t == "FOLD":  codes["fold"]        = c
        elif t == "CALL":  codes["call"]        = c
        elif t == "CHECK": codes["check"]       = c
        elif t == "RAISE":
            if   bp < 0.40: codes["raise_small"] = c
            elif bp < 0.80: codes["raise_mid"]   = c
            elif bp < 1.50: codes["raise_large"] = c
            else:           codes["raise_allin"] = c
    return codes

def calc_hand_action_rates_from_shc(shc: dict) -> list:
    """simple_hand_counters から per-hand アクション率を返す（combo加重）。
    raise% = 1 - fold - call で計算（action code の差異を吸収）。"""
    rows = []
    for hand_name, hand_info in shc.items():
        combos = hand_info.get("total_combos", 0.0)
        if combos < 0.1:
            continue
        freqs = hand_info.get("actions_total_frequencies", {})
        fold  = freqs.get("F", 0.0)
        call  = freqs.get("C", 0.0)
        raise_total = max(0.0, 1.0 - fold - call)
        rows.append({"hc": hand_name, "total": round(combos, 1),
                     "fold": fold, "call": call, "raise": raise_total})
    total_range = sum(r["total"] for r in rows)
    for r in rows:
        r["share"] = round(r["total"] / total_range * 100, 1) if total_range > 0 else 0.0
    rows.sort(key=lambda x: -x["total"])
    return rows

def weighted_raise_rate(rows, raise_keys):
    if not raise_keys or not rows:
        return None
    tc = sum(r["total"] for r in rows)
    if tc == 0:
        return None
    return sum(r["total"] * sum(r.get(k, 0) or 0 for k in raise_keys) for r in rows) / tc

def print_hand_table(rows, label=""):
    if not rows:
        return
    keys = [k for k in rows[0] if k not in ("hc", "total", "share")]
    if label:
        print(f"\n  {label}")
    hdr = f"  {'ハンド':16s} {'コンボ':>6} {'シェア':>6}"
    for k in keys:
        hdr += f" {k:>12}"
    print(hdr)
    print(f"  {'-'*72}")
    for row in rows[:30]:
        line = f"  {row['hc']:16s} {row['total']:6.1f} {row['share']:5.1f}%"
        for k in keys:
            v = row.get(k)
            line += f" {v*100:11.0f}%" if v is not None else f"  {'—':>11}"
        print(line)

# ─── フェーズ実行 ──────────────────────────────────────────────────
def run_probe():
    print(f"\n=== PROBE: BTN RFI (pf='F-F-F-F-F') SBR={SBR} ===")
    data = call_api("F-F-F-F-F")
    if not data:
        print("❌ データ取得失敗"); return
    time.sleep(5.0)
    print("\n--- players_info ---")
    for p in data.get("players_info", []):
        player = p.get("player", {})
        pos    = player.get("position", "?") if isinstance(player, dict) else str(player)
        hcs    = p.get("hand_categories", [])
        sample = [h["name"] for h in hcs[:5]] if hcs else []
        print(f"  {pos}: {len(hcs)} hand_categories, sample={sample}")
    print("\n--- action_solutions ---")
    for s in data.get("action_solutions", []):
        a = s["action"]
        print(f"  {a['type']} code={a['code']} bp={a.get('betsize_by_pot')} hcs={len(s.get('hand_categories') or [])}")
    out = FINDINGS_DIR / f"mtt_preflop_probe_SBR{SBR}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n✅ raw dump → {out}")

def run_spots(spots: list, phase_key: str) -> dict:
    results = {}
    t_open = T_OPEN_MTT.get(SBR, {})
    for spot in spots:
        pf    = spot["pf"]
        actor = spot["actor"]
        label = spot["label"]
        print(f"\n--- {label} (pf={pf!r}, actor={actor}) ---")

        data = call_api(pf)
        time.sleep(5.0)
        if not data:
            print("  ❌ データ取得失敗"); continue

        player = get_player(data, actor)
        if not player:
            avail = [p["player"].get("position", "?") if isinstance(p.get("player"), dict) else "?"
                     for p in data.get("players_info", [])]
            print(f"  ⚠️ actor={actor!r} 見つからず。利用可能: {avail}")
            player = data.get("players_info", [{}])[0] if data.get("players_info") else None
            if not player:
                continue

        sols       = data.get("action_solutions", [])
        codes      = classify_actions(sols)
        shc        = (player or {}).get("simple_hand_counters", {})
        rows       = calc_hand_action_rates_from_shc(shc)

        tc = sum(r["total"] for r in rows)
        raise_rate = sum(r["total"] * r.get("raise", 0) for r in rows) / tc if tc else 0.0

        print(f"  コード: {codes}")
        print(f"  Raise%: {raise_rate*100:.1f}%")

        if phase_key == "rfi" and actor in t_open:
            threshold  = t_open[actor]
            gto_raise  = [r["hc"] for r in rows if r.get("raise", 0) >= 0.50]
            print(f"  T_open(SBR{SBR},{actor})={threshold}: GTO50%+={len(gto_raise)}ハンド")

        print_hand_table(rows, label=label)
        results[label] = {
            "pf":        pf,
            "actor":     actor,
            "codes":     codes,
            "raise_pct": round(raise_rate * 100, 1),
            "rows":      rows,
        }
    return results

def main():
    if not TOKEN:
        print("❌ TOKEN 未設定"); sys.exit(1)

    check_token()
    time.sleep(5.0)
    print(f"\nSBR={SBR}  depth={DEPTH}  open={OR}BB  3bet_ip={BB3_IP}/sb={BB3_SB}/bb={BB3_BB}  gametype={GT}")

    if PHASE == "probe":
        run_probe()
        return

    if PHASE == "all":
        phases_to_run = ALL_PHASES
    else:
        phases_to_run = [(k, s, d) for k, s, d in ALL_PHASES if k == PHASE]
        if not phases_to_run:
            print(f"❌ PHASE={PHASE!r} 不正。有効値: {[k for k,_,_ in ALL_PHASES]}"); sys.exit(1)

    total_calls = sum(len(s) for _, s, _ in phases_to_run)
    print(f"実行予定: {len(phases_to_run)}フェーズ / {total_calls}コール\n")

    all_results = {}
    for phase_key, spots, desc in phases_to_run:
        print(f"\n{'='*70}")
        print(f"■ {desc}  ({len(spots)}コール)")
        all_results[phase_key] = run_spots(spots, phase_key)

    out = FINDINGS_DIR / f"mtt_preflop_gto_SBR{SBR}_{PHASE}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"gametype": GT, "sbr": SBR, "depth": DEPTH, "phase": PHASE,
                   "open_size": OR, "results": all_results},
                  f, ensure_ascii=False, indent=2)
    print(f"\n✅ 完了 → {out}")

    # RFI サマリー
    if "rfi" in all_results:
        t_open = T_OPEN_MTT.get(SBR, {})
        print(f"\n=== RFI サマリー (SBR{SBR}) ===")
        print(f"  {'スポット':14s} | {'GTO Raise%':>11} | {'T_open':>7}")
        print(f"  {'-'*40}")
        pos_map = {s["label"]: s["actor"] for s in RFI_SPOTS}
        for label, res in all_results["rfi"].items():
            rp  = res.get("raise_pct")
            pos = pos_map.get(label, "?")
            th  = t_open.get(pos, "?")
            print(f"  {label:14s} | {f'{rp:.1f}%' if rp else '—':>11} | {str(th):>7}")

if __name__ == "__main__":
    main()
