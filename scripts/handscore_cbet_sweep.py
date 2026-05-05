#!/usr/bin/env python3
"""
HandScore → IP CBet% 連続スウィープ

OOP がチェック後、IP（BTN）の全コンボに HandScore を計算し、
HS 別 bet% をプロットして CBet の「自然なバケツ境界」を発見する。

ディフェンス版スウィープとの比較が目的。

使用方法:
    python3 scripts/handscore_cbet_sweep.py          # 全ボード実行
    python3 scripts/handscore_cbet_sweep.py --reuse  # キャッシュ再利用
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR  = "/home/cuzic/TexasSolver"
OUT_DIR     = Path("/home/cuzic/poker-books/knowledges/flop/results/handscore_boundary")

POT = 7
STACK = 97

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

RANK_STR = "23456789TJQKA"
RANK_VAL  = {r: i for i, r in enumerate(RANK_STR)}

def rv(r: str) -> int:
    return RANK_VAL[r.upper()]

def parse_combo(c: str) -> tuple[str, str, str, str]:
    return c[0].upper(), c[1].lower(), c[2].upper(), c[3].lower()

# ---------------------------------------------------------------------------
# HandScore（IP 版：オーバーペア対応追加）
# ---------------------------------------------------------------------------

def straight_draw_score(r1: str, r2: str, board_ranks: list[str]) -> int:
    hv1, hv2 = rv(r1), rv(r2)
    bvs = {rv(r) for r in board_ranks}
    all_v = {hv1, hv2} | bvs
    best = 0
    for lo in range(0, 9):
        window = set(range(lo, lo + 5))
        hand_in = {hv1, hv2} & window
        if not hand_in:
            continue
        missing = window - all_v
        if len(missing) == 1:
            mv = next(iter(missing))
            best = max(best, 14 if mv in (lo, lo + 4) else 10)
    # ホイール
    hw, bw = set(), set()
    for r, t in ((r1, hw), (r2, hw)):
        if rv(r) == 12: t.add(-1)
        t.add(rv(r))
    for r in board_ranks:
        if rv(r) == 12: bw.add(-1)
        bw.add(rv(r))
    ww = {-1, 0, 1, 2, 3}
    if hw & ww:
        miss = ww - (hw | bw)
        if len(miss) == 1:
            mv = next(iter(miss))
            best = max(best, 14 if mv in (-1, 3) else 10)
    return best


def compute_hs_ip(combo: str, board_ranks: list[str], board_suits: list[str]) -> int:
    """
    IP 用 HandScore。オーバーペアを 20 点として扱う。
    """
    r1, s1, r2, s2 = parse_combo(combo)

    from collections import Counter
    bc = Counter(board_ranks)
    board_sorted = sorted(board_ranks, key=rv, reverse=True)
    top = board_sorted[0]

    # セット / トリップス
    if r1 == r2 and r1 in board_ranks:
        return 25
    if bc.get(r1, 0) >= 2 or bc.get(r2, 0) >= 2:
        return 25

    # ツーペア
    if r1 in board_ranks and r2 in board_ranks and r1 != r2:
        return 18

    # オーバーペア（ポケットペアがボード全カードより上位）
    if r1 == r2 and all(rv(r1) > rv(b) for b in board_ranks):
        return 20

    # アンダーペア（ポケットペアがボードより下位）
    if r1 == r2:
        return 3   # ボトムペア相当

    # 1ペア
    made = 0
    sec  = board_sorted[1] if len(board_sorted) > 1 else None

    pair_rank: str | None = None
    kicker:    str | None = None
    if r1 in board_ranks:
        pair_rank, kicker = r1, r2
    elif r2 in board_ranks:
        pair_rank, kicker = r2, r1

    if pair_rank is not None and kicker is not None:
        if pair_rank == top:
            made = 8 if rv(kicker) >= rv("T") else 6
        elif pair_rank == sec:
            made = 9 if rv(kicker) >= rv("T") else 3
        else:
            made = 3   # ボトムペア

    # ドロー加点
    draw = 0
    if s1 == s2:
        cnt = board_suits.count(s1)
        draw = max(draw, 13 if cnt >= 2 else 4)
    sd   = straight_draw_score(r1, r2, board_ranks)
    draw = max(draw, sd)

    return made + draw


# ---------------------------------------------------------------------------
# CBet ノード取得
# ---------------------------------------------------------------------------

def get_ip_cbet_node(raw: dict) -> dict | None:
    """OOP チェック後の IP 行動ノードを返す"""
    check_node = raw.get("childrens", {}).get("CHECK")
    return check_node   # player=0 (IP) が bet/check を選ぶ


# ---------------------------------------------------------------------------
# HS 別 bet% 集計
# ---------------------------------------------------------------------------

def sweep_cbet_by_hs(ip_node: dict,
                     board_ranks: list[str],
                     board_suits: list[str]) -> dict[int, dict]:
    strat   = ip_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos  = strat.get("strategy", {})

    ci  = actions.index("CHECK") if "CHECK" in actions else None
    bis = [i for i, a in enumerate(actions) if a != "CHECK"]

    buckets: dict[int, dict] = collections.defaultdict(
        lambda: {"n": 0, "bet": 0.0, "check": 0.0}
    )

    for combo, probs in combos.items():
        hs    = compute_hs_ip(combo, board_ranks, board_suits)
        bet   = sum(probs[i] for i in bis if i < len(probs))
        check = probs[ci] if ci is not None and ci < len(probs) else 0.0
        b = buckets[hs]
        b["n"]     += 1
        b["bet"]   += bet
        b["check"] += check

    return dict(buckets)


def print_cbet_sweep(buckets: dict[int, dict], board_label: str) -> None:
    print(f"\n  [{board_label}] IP CBet% by HandScore  (OOP check → IP action)")
    print(f"  {'HS':>4}  {'n':>5}  {'Bet%':>7}  {'Chk%':>7}  グラフ (Bet%)")
    print(f"  {'-'*65}")
    for hs in sorted(buckets):
        b = buckets[hs]
        n = b["n"]
        if n == 0: continue
        bet = b["bet"]   / n * 100
        chk = b["check"] / n * 100
        bar = "█" * int(bet / 5 + 0.5)
        print(f"  {hs:>4}  {n:>5}  {bet:>6.1f}%  {chk:>6.1f}%  {bar}")


def find_cbet_jumps(buckets: dict[int, dict]) -> list[tuple[int, int, float, float]]:
    items = [(hs, b["bet"] / b["n"] * 100)
             for hs, b in sorted(buckets.items()) if b["n"] >= 3]
    jumps = []
    for i in range(1, len(items)):
        h0, r0 = items[i-1]
        h1, r1 = items[i]
        if abs(r1 - r0) >= 20:
            jumps.append((h0, h1, r0, r1))
    return jumps


# ---------------------------------------------------------------------------
# ソルバー
# ---------------------------------------------------------------------------

def run_solver(board: str, dump_path: str, timeout: int = 400) -> int:
    config = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board,
        ip_range=IP_RANGE, oop_range=OOP_RANGE, dump_path=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(config); cfg = f.name
    try:
        with open(cfg) as fin:
            proc = subprocess.Popen(
                [SOLVER_BIN], stdin=fin,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(); rc = -1
    finally:
        try: os.unlink(cfg)
        except OSError: pass
    return rc


# ---------------------------------------------------------------------------
# テストボード
# ---------------------------------------------------------------------------

BOARDS = [
    {"id": "K72r",  "board": "Kc,7d,2s",
     "board_ranks": ["K","7","2"], "board_suits": ["c","d","s"],
     "label": "K72r (dry)"},
    {"id": "T84r",  "board": "Tc,8d,4s",
     "board_ranks": ["T","8","4"], "board_suits": ["c","d","s"],
     "label": "T84r (semi)"},
    {"id": "T98r",  "board": "Tc,9d,8s",
     "board_ranks": ["T","9","8"], "board_suits": ["c","d","s"],
     "label": "T98r (wet)"},
    {"id": "Js8c4c", "board": "Js,8c,4c",
     "board_ranks": ["J","8","4"], "board_suits": ["s","c","c"],
     "label": "Js8c4c (FDあり)"},
]


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_jumps: list[dict] = []

    for sc in BOARDS:
        sid   = sc["id"]
        board = sc["board"]
        br_   = sc["board_ranks"]
        bs_   = sc["board_suits"]
        dump  = str(OUT_DIR / f"{sid}_raw.json")

        print(f"\n{'='*65}")
        print(f"  {sc['label']}")
        print(f"{'='*65}")

        if args.reuse and Path(dump).exists():
            print(f"  キャッシュ: {dump}")
        else:
            print(f"  Solving {board} ...")
            t0 = time.time()
            rc = run_solver(board, dump)
            if rc != 0 or not Path(dump).exists():
                print(f"  ERROR rc={rc}"); continue
            print(f"  完了 {time.time()-t0:.0f}s")

        raw = json.loads(Path(dump).read_text())
        ip_node = get_ip_cbet_node(raw)
        if ip_node is None:
            print("  IP CBet ノードなし"); continue

        buckets = sweep_cbet_by_hs(ip_node, br_, bs_)
        print_cbet_sweep(buckets, sc["label"])

        jumps = find_cbet_jumps(buckets)
        if jumps:
            print(f"\n  ⚡ 急変点 (≥20pp):")
            for jb, ja, rb, ra in jumps:
                print(f"     HS {jb:>2} → {ja:>2}:  {rb:.0f}% → {ra:.0f}%  (Δ={ra-rb:+.0f}pp)")

        all_jumps.append({"board": board, "label": sc["label"], "jumps": jumps,
                          "buckets": {str(k): v for k, v in buckets.items()}})

    # ─────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("【CBet 急変点まとめ】")
    print(f"{'='*65}")
    for s in all_jumps:
        for jb, ja, rb, ra in s["jumps"]:
            print(f"  {s['label']:20}  HS {jb}→{ja}  {rb:.0f}%→{ra:.0f}%")

    # ディフェンスとの比較サマリ
    print(f"\n{'='*65}")
    print("【CBet vs ディフェンス：主要ハンドのバケツ比較】")
    print(f"{'='*65}")
    print(f"  {'HS':>4}  {'代表ハンド':<25}  {'CBet(dry)':>9}  {'Defense(dry)':>12}")
    print(f"  {'-'*65}")

    # K72r のデータで比較
    k72_data = next((s for s in all_jumps if "K72r" in s["label"]), None)
    defense_map = {  # 前回の OOP ディフェンス実測値 (K72r vs 33%)
        0:  0.8,   # no pair
        3:  0.0,   # 2nd weak / bottom
        4:  4.4,   # BDFD
        6:  None,  # tpwk (not present in K72r defense data as distinct)
        8: 11.4,   # tpmk
        9:  0.0,   # 2nd strong
        13: 0.0,   # 2nd+BDFD
        18:100.0,  # two pair
        20: None,  # overpair
        25:100.0,  # set
    }
    hs_labels = {
        0:  "no pair / no draw",
        3:  "2nd pair weak / bottom",
        4:  "BDFD only",
        6:  "TPWK",
        8:  "TPMK",
        9:  "2nd pair strong",
        13: "2nd+BDFD",
        14: "pure OESD",
        18: "two pair",
        20: "overpair",
        25: "set / trips",
    }

    if k72_data:
        bucks = k72_data["buckets"]
        for hs, label in sorted(hs_labels.items()):
            key = str(hs)
            if key not in bucks: continue
            b = bucks[key]
            n = b["n"]
            if n == 0: continue
            cbet_pct = b["bet"] / n * 100
            def_pct  = defense_map.get(hs)
            def_str  = f"{def_pct:.0f}%" if def_pct is not None else "—"
            flag = ""
            if def_pct is not None and abs(cbet_pct - def_pct) >= 25:
                flag = "  ← 乖離!"
            print(f"  {hs:>4}  {label:<25}  {cbet_pct:>8.1f}%  {def_str:>12}{flag}")

    out = OUT_DIR / "cbet_sweep_summary.json"
    out.write_text(json.dumps(all_jumps, indent=2, ensure_ascii=False))
    print(f"\n  保存: {out}")


if __name__ == "__main__":
    main()
