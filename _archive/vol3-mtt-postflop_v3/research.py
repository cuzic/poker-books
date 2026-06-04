#!/usr/bin/env python3
"""
GTO Wizard MTT調査スクリプト
使い方:
  TOKEN=eyJ... python3 research.py phase1
  TOKEN=eyJ... python3 research.py phase2
  TOKEN=eyJ... python3 research.py analyze findings/phase1_commit_lines.jsonl
"""

import os, sys, json, time, requests
from pathlib import Path

TOKEN = os.environ.get("TOKEN", "")
BASE_URL = "https://api.gtowizard.com/v4/solutions/spot-solution/"
GT = "MTTGeneral_ICM9m200PTPCT25"   # 9-max ICM, 200 players, PCT25 prize structure
FINDINGS_DIR = Path(__file__).parent / "findings"
FINDINGS_DIR.mkdir(exist_ok=True)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": f"Bearer {TOKEN}",
    "origin": "https://app.gtowizard.com",
    "referer": "https://app.gtowizard.com/",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API呼び出し
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def call_api(gametype, depth, stacks, preflop="", flop="", turn="", river="", board=""):
    params = {
        "gametype": gametype,
        "depth": str(depth),
        "stacks": "-".join(str(s) for s in stacks),
        "preflop_actions": preflop,
        "flop_actions": flop,
        "turn_actions": turn,
        "river_actions": river,
        "board": board,
    }
    resp = requests.get(BASE_URL, params=params, headers=HEADERS, timeout=30)
    return resp.json()

def check_auth():
    resp = call_api(GT, 50, [50]*9)
    if "AUTHENTICATION_FAILED" in str(resp):
        print("❌ 認証失敗: TOKEN が無効または期限切れです")
        sys.exit(1)
    print("✅ 認証OK")
    return resp

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# スタック設定ヘルパー
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def make_stacks_sbr(hero_bb, n_players=8):
    """
    hero_bb: ヒーロー(BTN)のスタック [BB]
    残りプレイヤーは平均スタックで埋める（合計=200BB×n_players/8想定で逆算）
    """
    avg = hero_bb * 0.9  # 残りプレイヤーの平均（ヒーローより少し小さく）
    stacks = [hero_bb] + [avg] * (n_players - 1)
    return stacks

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 1: SBR別コミットライン
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# vol2のボード7分類 代表ボード
BOARDS = {
    "型1_ハイドライ":  "Ks7d2c",   # K♠7♦2♣
    "型2_ハイウェット": "Qh8d3s",   # Q♥8♦3♠
    "型4_ローウェット": "Th9s8d",   # T♥9♠8♦
}

# SBR → BBスタック (BBアンテあり: SBR ≈ stack/2)
SBR_TO_BB = {
    "sbr30": 60,   # 60BB ≈ SBR30
    "sbr25": 50,   # 50BB ≈ SBR25
    "sbr20": 40,   # 40BB ≈ SBR20
    "sbr15": 30,   # 30BB ≈ SBR15
    "sbr10": 20,   # 20BB ≈ SBR10
}

# プリフロップアクション: BTN open 2.5BB → BB call (要検証)
# GTO Wizard のエンコーディングを確認してから修正する
PF_BTN_OPEN_BB_CALL = "r2.5c"   # ← 実際のフォーマットに合わせて修正

def phase1():
    """SBR別・ボード別のフロップ戦略を取得"""
    print("=== Phase 1: SBR別コミットライン ===")
    out_file = FINDINGS_DIR / "phase1_commit_lines.jsonl"
    results = []

    GT = "MTTGeneral_ICM8m200PTT3"

    for sbr_label, hero_bb in SBR_TO_BB.items():
        stacks = make_stacks_sbr(hero_bb)
        for board_label, board in BOARDS.items():
            label = f"{sbr_label}/{board_label}"
            print(f"  {label} ... ", end="", flush=True)
            try:
                resp = call_api(
                    GT, hero_bb, stacks,
                    preflop=PF_BTN_OPEN_BB_CALL,
                    board=board
                )
                status = "OK" if "error" not in str(resp).lower() else "ERR"
                print(status)

                record = {
                    "phase": 1,
                    "sbr": sbr_label,
                    "hero_bb": hero_bb,
                    "board_label": board_label,
                    "board": board,
                    "stacks": stacks,
                    "response": resp,
                }
                results.append(record)
                with open(out_file, "a") as f:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")

                time.sleep(1)  # レート制限回避

            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\nPhase 1 完了 → {out_file}")
    return results

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Phase 2: ICM補正値の定量化
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 同一シナリオをICMあり/なしで比較するgametype
# ※ chip-EVのgametypeは実際のGTOWizard仕様に合わせて修正が必要
GAMETYPES = {
    "ICM_mid":    "MTTGeneral_ICM8m200PTT3",   # ICMあり（中盤想定）
    "ICM_bubble": "MTTGeneral_ICM8m200PTT3",   # バブル（スタック設定で表現）
    # "CEV":      "MTTGeneral_CEV8m200PTT3",   # Chip-EV（存在する場合）
}

def make_bubble_stacks(hero_bb, n_players=8):
    """バブル想定: ショートスタック(10BB)2人、ビッグスタック(80BB)2人、残り平均"""
    return [hero_bb, 10, 10, 80, 80, hero_bb, hero_bb*0.8, hero_bb*0.8]

def phase2():
    """ICMステージ別のフォールド閾値変化を取得"""
    print("=== Phase 2: ICM補正値の定量化 ===")
    out_file = FINDINGS_DIR / "phase2_icm_adjustment.jsonl"

    BOARD = "Qs7d2c"   # Q♠7♦2♣ 型1 ハイドライ
    HERO_BB = 40       # SBR=20固定

    scenarios = [
        # (label, gametype, stacks_func, hero_bb)
        ("中盤_均等",   "MTTGeneral_ICM8m200PTT3", make_stacks_sbr(HERO_BB)),
        ("バブル_混在", "MTTGeneral_ICM8m200PTT3", make_bubble_stacks(HERO_BB)),
    ]

    for label, gt, stacks in scenarios:
        print(f"  [{label}] ... ", end="", flush=True)
        try:
            resp = call_api(gt, HERO_BB, stacks, preflop=PF_BTN_OPEN_BB_CALL, board=BOARD)
            print("OK" if "error" not in str(resp).lower() else "ERR")

            record = {
                "phase": 2,
                "label": label,
                "gametype": gt,
                "hero_bb": HERO_BB,
                "board": BOARD,
                "stacks": stacks,
                "response": resp,
            }
            with open(out_file, "a") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

            time.sleep(1)
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\nPhase 2 完了 → {out_file}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# レスポンス解析
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def analyze(filepath=None):
    """JSONLファイルのレスポンス構造を確認する"""
    if filepath is None:
        filepath = FINDINGS_DIR / "phase1_commit_lines.jsonl"

    print(f"=== レスポンス解析: {filepath} ===\n")
    with open(filepath) as f:
        for i, line in enumerate(f):
            try:
                rec = json.loads(line)
                resp = rec.get("response", {})
                print(f"--- [{rec.get('sbr','?')} / {rec.get('board_label','?')}] ---")
                print(f"  response keys: {list(resp.keys()) if isinstance(resp, dict) else type(resp)}")

                # アクション/戦略情報を探す
                for key in ["actions", "strategy", "hands", "spots", "ev", "combos", "ranges"]:
                    if key in resp:
                        val = resp[key]
                        print(f"  {key}: {str(val)[:300]}")
                print()
            except Exception as e:
                print(f"  Parse error: {e}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# テスト: API形式の確認（認証後に1回だけ実行）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def probe():
    """APIレスポンス構造を確認するための探索呼び出し"""
    print("=== API Probe ===")
    resp = check_auth()
    print("\n最初のレスポンスキー:")
    if isinstance(resp, dict):
        for k, v in resp.items():
            print(f"  {k}: {str(v)[:200]}")
    elif isinstance(resp, list):
        print(f"  list len={len(resp)}, first={str(resp[0])[:200]}")
    else:
        print(f"  {resp}")

    # preflop_actionsの形式をいくつか試す (9-max BTN open → BB call)
    # 9人: UTG,UTG+1,UTG+2,LJ,HJ,CO,BTN,SB,BB
    # BTN openならUTG〜COの6人がfoldしてからBTNがraise、SBがfold、BBがcall
    print("\n=== preflop_actions 形式テスト (BTN vs BB SRP) ===")
    stacks_9 = [50]*9
    for pf in [
        "F-F-F-F-F-F-R2.5-F-C",   # 6folds, BTN R2.5, SB fold, BB call
        "F-F-F-F-F-R2.5-F-C",     # 5folds (8-max?)
        "F-F-F-F-F-F-R2-F-C",     # 6folds, BTN R2, SB fold, BB call
        "F-F-F-F-F-F-R2.5-C",     # 6folds, BTN R2.5, BB call (SB skip?)
        "R2-F-R6-F-F-F-F-F-F-C",  # 既知の3BP形式 (確認用)
    ]:
        r = call_api(GT, 50, stacks_9, preflop=pf, board="Ks7d2c")
        ok = "error" not in str(r).lower() and "AUTHENTICATION" not in str(r) and "action_solutions" in str(r)
        print(f"  preflop={pf!r:30s} → {'OK' if ok else 'ERR'}: {str(r)[:100]}")
        time.sleep(0.5)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# エントリポイント
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    if not TOKEN:
        print("❌ TOKEN 環境変数が未設定です")
        print("   TOKEN=eyJ... python3 research.py probe")
        sys.exit(1)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "probe"

    if cmd == "probe":
        probe()
    elif cmd == "phase1":
        check_auth()
        phase1()
    elif cmd == "phase2":
        check_auth()
        phase2()
    elif cmd == "analyze":
        filepath = sys.argv[2] if len(sys.argv) > 2 else None
        analyze(filepath)
    elif cmd == "all":
        check_auth()
        phase1()
        phase2()
    else:
        print(f"不明なコマンド: {cmd}")
        print("使い方: TOKEN=eyJ... python3 research.py [probe|phase1|phase2|analyze|all]")
