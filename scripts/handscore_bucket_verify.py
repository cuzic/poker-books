#!/usr/bin/env python3
"""
HandScore バケツ境界検証スクリプト

「数値式 → H3/H2/H1」vs「直接パターン表」の GTO 整合性を検証する。

検証する境界ハンド:
  - FD 単独 (formula H2=13): 直感では H3 と思われがちなフラッシュドロー
  - OESD 単独 (formula H2=14): H3 境界すれすれ
  - tpwk (formula H1=6): 弱キッカー TP → H1 は正しいか
  - tpmk (formula H2=8): H2 境界値

成功基準:
  - FD/OESD が tpmk と同程度の CBet 頻度 → H2 で正しい
  - FD/OESD が tpmk より大幅に高い CBet → H3 に引き上げる根拠あり
  - tpwk が tpmk より大幅に低い CBet → H1 で正しい
  - tpwk が tpmk と同程度 → H2 に引き上げる根拠あり

使用方法:
    python3 scripts/handscore_bucket_verify.py
    python3 scripts/handscore_bucket_verify.py --reuse  # キャッシュ再利用
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/flop/results/handscore_boundary")

POT = 7
STACK = 97

# BTN オープンレンジ
IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
    "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,"
    "T9s,T8s,T7s,T6s,"
    "98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)

# BB ディフェンドレンジ
OOP_RANGE = (
    "JJ,TT,99,88,77,66,55,44,33,22,"
    "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AQo,AJo,ATo,A9o,A8o,A7o,A6o,A5o,A4o,A3o,A2o,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "KQo,KJo,KTo,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,Q3s,Q2s,"
    "QJo,QTo,Q9o,Q8o,"
    "JTs,J9s,J8s,J7s,J6s,J5s,J4s,JTo,J9o,J8o,"
    "T9s,T8s,T7s,T6s,T5s,T9o,T8o,"
    "98s,97s,96s,95s,98o,"
    "87s,86s,85s,87o,"
    "76s,75s,74s,76o,"
    "65s,64s,65o,"
    "54s,53s,43s"
)

CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes ip,flop,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 300
set_print_interval 100
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""

# ---------------------------------------------------------------------------
# テスト定義
# ---------------------------------------------------------------------------

RANK_ORDER = "23456789TJQKA"

def rank_val(r: str) -> int:
    return RANK_ORDER.index(r.upper())


def parse_combo(combo: str) -> tuple[str, str, str, str]:
    """'AcKh' → (rank1, suit1, rank2, suit2)"""
    return combo[0].upper(), combo[1].lower(), combo[2].upper(), combo[3].lower()


def is_fd_on_board(combo: str, board_suits: list[str]) -> bool:
    """combo が board の 2枚スーテッドと同スートの FD かどうか"""
    r1, s1, r2, s2 = parse_combo(combo)
    for suit in set(board_suits):
        if board_suits.count(suit) >= 2:
            if s1 == suit and s2 == suit:
                return True
    return False


def makes_pair(combo: str, board_ranks: list[str]) -> bool:
    r1, _, r2, _ = parse_combo(combo)
    return r1 in board_ranks or r2 in board_ranks


def combo_rank_pair(combo: str) -> frozenset[str]:
    r1, _, r2, _ = parse_combo(combo)
    return frozenset([r1, r2])


def match_hand(combo: str, target_ranks: frozenset[str]) -> bool:
    return combo_rank_pair(combo) == target_ranks


# ---------------------------------------------------------------------------
# テストシナリオ
# ---------------------------------------------------------------------------

SCENARIOS = [
    {
        "id": "K72r",
        "board": "Kc,7d,2s",
        "board_ranks": ["K", "7", "2"],
        "board_suits": ["c", "d", "s"],
        "A": 3,
        "label": "K72r (dry, A=3)",
        "hands": [
            {
                "label": "tpwk K8o/K9o [formula H1=6]",
                "test_fn": lambda c: (
                    combo_rank_pair(c) in (frozenset(["K","8"]), frozenset(["K","9"]))
                    and parse_combo(c)[1] != parse_combo(c)[3]  # offsuit
                ),
                "formula_bucket": "H1",
                "formula_hs": 6,
                "intuitive_bucket": "H2",
            },
            {
                "label": "tpmk KTo/KJo [formula H2=8]",
                "test_fn": lambda c: (
                    combo_rank_pair(c) in (frozenset(["K","T"]), frozenset(["K","J"]))
                    and parse_combo(c)[1] != parse_combo(c)[3]  # offsuit
                ),
                "formula_bucket": "H2",
                "formula_hs": 8,
                "intuitive_bucket": "H2",
            },
        ],
    },
    {
        "id": "Kc7c2d",
        "board": "Kc,7c,2d",
        "board_ranks": ["K", "7", "2"],
        "board_suits": ["c", "c", "d"],
        "A": 3,
        "label": "Kc7c2d (flush draw board, A=3)",
        "hands": [
            {
                "label": "FD単独 Ac高FD [formula H2=13]",
                "test_fn": lambda c: (
                    parse_combo(c)[1] == "c" and parse_combo(c)[3] == "c"  # both clubs
                    and parse_combo(c)[0] == "A"                            # A-high FD
                    and not makes_pair(c, ["K", "7", "2"])                  # no pair
                    and parse_combo(c)[2] not in ("K", "7", "2")            # kicker not on board
                ),
                "formula_bucket": "H2",
                "formula_hs": 13,
                "intuitive_bucket": "H3",
            },
        ],
    },
    {
        "id": "T84r",
        "board": "Tc,8d,4s",
        "board_ranks": ["T", "8", "4"],
        "board_suits": ["c", "d", "s"],
        "A": 2,
        "label": "T84r (semi, A=2)",
        "hands": [
            {
                "label": "OESD単独 J9s ハート [formula H2=14]",
                "test_fn": lambda c: (
                    combo_rank_pair(c) == frozenset(["J", "9"])
                    and parse_combo(c)[1] == parse_combo(c)[3]  # suited
                    and parse_combo(c)[1] not in ("c", "d", "s")  # not same suit as board cards
                    # board: Tc, 8d, 4s → clubs/diamonds/spades on board
                    # so hearts only = no FD possible (no 2 hearts on board)
                    # Actually any suit of J9 works since T84 is rainbow,
                    # but J9s has both same suit = FD? No! Board is Tc8d4s (rainbow)
                    # so any pair of same-suited cards won't complete a FD
                    # (need 2 board cards of same suit for FD)
                ),
                "formula_bucket": "H2",
                "formula_hs": 14,
                "intuitive_bucket": "H3",
            },
            {
                "label": "OESD単独 J9s 全スート [formula H2=14]",
                "test_fn": lambda c: (
                    combo_rank_pair(c) == frozenset(["J", "9"])
                    and not makes_pair(c, ["T", "8", "4"])
                ),
                "formula_bucket": "H2",
                "formula_hs": 14,
                "intuitive_bucket": "H3",
            },
        ],
    },
]

# T84r は rainbow なので FD なし → J9s は全スートで OESD のみ
# 上の 2 つのテストは同じ結果になるはず（整合性確認）

# ---------------------------------------------------------------------------
# ソルバー実行
# ---------------------------------------------------------------------------

def run_solver(board: str, dump_path: str, timeout: int = 400) -> int:
    config = CONFIG_TEMPLATE.format(
        pot=POT,
        stack=STACK,
        board=board,
        ip_range=IP_RANGE,
        oop_range=OOP_RANGE,
        dump_path=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="ts_hsbv_") as f:
        f.write(config)
        cfg_path = f.name
    try:
        with open(cfg_path) as fin:
            proc = subprocess.Popen(
                [SOLVER_BIN], stdin=fin,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                rc = -1
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass
    return rc


# ---------------------------------------------------------------------------
# 結果解析
# ---------------------------------------------------------------------------

def get_ip_cbet_node(raw: dict) -> dict | None:
    """root → OOP CHECK → IP strategy ノードを返す"""
    return raw.get("childrens", {}).get("CHECK")


def get_oop_defense_node(raw: dict, bet_pct: int) -> dict | None:
    """root → OOP CHECK → IP BET X → OOP defense ノードを返す"""
    check_node = raw.get("childrens", {}).get("CHECK")
    if not check_node:
        return None
    expected = POT * bet_pct / 100.0
    for key, node in check_node.get("childrens", {}).items():
        if not key.startswith("BET"):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        if abs(amt - expected) < 1.5:
            return node
    return None


def extract_ip_cbet_by_filter(ip_node: dict, test_fn) -> dict:
    """IP ノードから条件に合う combo の CBet 頻度を計算"""
    strat = ip_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})

    try:
        check_idx = actions.index("CHECK")
    except ValueError:
        check_idx = None

    matched = []
    for combo, probs in combos.items():
        if not test_fn(combo):
            continue
        if check_idx is not None and check_idx < len(probs):
            cbet = 1.0 - probs[check_idx]
        else:
            cbet = 1.0
        matched.append({"combo": combo, "cbet": cbet})

    if not matched:
        return {"n": 0, "avg_cbet_pct": None, "combos": []}

    avg = sum(m["cbet"] for m in matched) / len(matched)
    return {
        "n": len(matched),
        "avg_cbet_pct": round(avg * 100, 1),
        "combos": sorted(matched, key=lambda x: -x["cbet"])[:6],
    }


def extract_oop_defense_by_filter(defense_node: dict, test_fn) -> dict:
    """OOP defense ノードから条件に合う combo の raise/call/fold を計算"""
    strat = defense_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})

    fold_idx = actions.index("FOLD") if "FOLD" in actions else None
    call_idx = actions.index("CALL") if "CALL" in actions else None
    raise_idxs = [i for i, a in enumerate(actions) if a not in ("FOLD", "CALL", "CHECK")]

    matched = []
    for combo, probs in combos.items():
        if not test_fn(combo):
            continue
        fold_p = probs[fold_idx] if fold_idx is not None and fold_idx < len(probs) else 0.0
        call_p = probs[call_idx] if call_idx is not None and call_idx < len(probs) else 0.0
        raise_p = sum(probs[i] for i in raise_idxs if i < len(probs))
        matched.append({"combo": combo, "fold": fold_p, "call": call_p, "raise": raise_p})

    if not matched:
        return {"n": 0}

    n = len(matched)
    avg_fold = sum(m["fold"] for m in matched) / n
    avg_call = sum(m["call"] for m in matched) / n
    avg_raise = sum(m["raise"] for m in matched) / n
    return {
        "n": n,
        "fold_pct": round(avg_fold * 100, 1),
        "call_pct": round(avg_call * 100, 1),
        "raise_pct": round(avg_raise * 100, 1),
    }


def classify_cbet(pct: float | None) -> str:
    if pct is None:
        return "N/A"
    if pct >= 85:
        return "H3相当"
    if pct >= 60:
        return "H2-H3"
    if pct >= 35:
        return "H2-H1境界"
    return "H1相当 (check傾向)"


def classify_defense(raise_p: float, call_p: float, fold_p: float) -> str:
    if raise_p >= 50:
        return "H3相当 (raise優位)"
    if raise_p >= 25:
        return "H2-H3 (raise混合)"
    if call_p >= 50:
        return "H2相当 (call優位)"
    if fold_p >= 50:
        return "H1相当 (fold優位)"
    return "混合"


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse", action="store_true", help="キャッシュ済み JSON を再利用")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_results: list[dict] = []

    for scenario in SCENARIOS:
        sid = scenario["id"]
        board = scenario["board"]
        dump_path = str(OUT_DIR / f"{sid}_raw.json")

        print(f"\n{'='*60}")
        print(f"Board: {scenario['label']}")
        print(f"{'='*60}")

        if args.reuse and Path(dump_path).exists():
            print(f"  キャッシュ再利用: {dump_path}")
        else:
            print(f"  TexasSolver 実行中 ({board}) ...")
            t0 = time.time()
            rc = run_solver(board, dump_path)
            elapsed = time.time() - t0
            if rc != 0 or not Path(dump_path).exists():
                print(f"  ERROR: solver rc={rc}")
                continue
            print(f"  完了: {elapsed:.0f}s")

        raw = json.loads(Path(dump_path).read_text())
        ip_node = get_ip_cbet_node(raw)
        oop_33_node = get_oop_defense_node(raw, 33)
        oop_75_node = get_oop_defense_node(raw, 75)

        if ip_node is None:
            print("  ERROR: IP CBet ノードが見つかりません")
            continue

        print(f"\n  {'ハンド':<35} {'IP CBet%':>10} {'分類':>15}  ['OOP vs33%']  ['OOP vs75%']")
        print(f"  {'-'*100}")

        for hand in scenario["hands"]:
            test_fn = hand["test_fn"]

            ip_stats = extract_ip_cbet_by_filter(ip_node, test_fn)
            cbet_pct = ip_stats.get("avg_cbet_pct")
            n = ip_stats.get("n", 0)

            cbet_class = classify_cbet(cbet_pct)
            cbet_str = f"{cbet_pct:.1f}% (n={n})" if cbet_pct is not None else "N/A"

            d33: dict = {}
            oop33_str = ""
            if oop_33_node:
                d33 = extract_oop_defense_by_filter(oop_33_node, test_fn)
                if d33.get("n", 0) > 0:
                    oop33_str = f"R={d33['raise_pct']:.0f}% C={d33['call_pct']:.0f}% F={d33['fold_pct']:.0f}%"

            d75: dict = {}
            oop75_str = ""
            if oop_75_node:
                d75 = extract_oop_defense_by_filter(oop_75_node, test_fn)
                if d75.get("n", 0) > 0:
                    oop75_str = f"R={d75['raise_pct']:.0f}% C={d75['call_pct']:.0f}% F={d75['fold_pct']:.0f}%"

            label = hand["label"]
            print(f"  {label:<35} {cbet_str:>16} {cbet_class:>15}  [{oop33_str:<25}]  [{oop75_str:<25}]")

            all_results.append({
                "board": board,
                "hand_label": label,
                "formula_bucket": hand["formula_bucket"],
                "formula_hs": hand["formula_hs"],
                "intuitive_bucket": hand["intuitive_bucket"],
                "n_combos": n,
                "ip_cbet_pct": cbet_pct,
                "oop_33": d33 if oop_33_node and d33.get("n", 0) > 0 else None,
                "oop_75": d75 if oop_75_node and d75.get("n", 0) > 0 else None,
            })

    # ── 判定サマリー ─────────────────────────────────────────────────────────
    print(f"\n\n{'='*60}")
    print("【判定サマリー】数値式バケツ vs 直接マッピング")
    print(f"{'='*60}")

    for r in all_results:
        if r["ip_cbet_pct"] is None:
            continue
        label = r["hand_label"].split("[")[0].strip()
        formula = r["formula_bucket"]
        intuitive = r["intuitive_bucket"]
        cbet = r["ip_cbet_pct"]

        verdict = "?"
        if formula == intuitive:
            verdict = "整合（数値式と直感が一致）"
        else:
            # FD/OESD: formula=H2, intuitive=H3
            # tpwk: formula=H1, intuitive=H2
            if formula == "H2" and intuitive == "H3":
                if cbet >= 80:
                    verdict = "⚠ 直感寄り: H3 扱いが適切かもしれない"
                else:
                    verdict = "✓ 数値式正しい: H2 行動と整合"
            elif formula == "H1" and intuitive == "H2":
                if cbet <= 45:
                    verdict = "✓ 数値式正しい: H1 行動と整合 (CBet 抑制)"
                else:
                    verdict = "⚠ 直感寄り: H2 扱いが適切かもしれない"

        print(f"  {label}")
        print(f"    式={formula}, 直感={intuitive}, IP CBet={cbet:.1f}%  → {verdict}")

        if r.get("oop_33"):
            d = r["oop_33"]
            cls = classify_defense(d["raise_pct"], d["call_pct"], d["fold_pct"])
            print(f"    OOP vs 33%: R={d['raise_pct']:.0f}% C={d['call_pct']:.0f}% F={d['fold_pct']:.0f}%  ({cls})")
        if r.get("oop_75"):
            d = r["oop_75"]
            cls = classify_defense(d["raise_pct"], d["call_pct"], d["fold_pct"])
            print(f"    OOP vs 75%: R={d['raise_pct']:.0f}% C={d['call_pct']:.0f}% F={d['fold_pct']:.0f}%  ({cls})")

    # JSON 保存
    summary_path = OUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
    print(f"\n結果保存: {summary_path}")


if __name__ == "__main__":
    main()
