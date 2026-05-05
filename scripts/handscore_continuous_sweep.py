#!/usr/bin/env python3
"""
HandScore → OOP raise% 連続スウィープ

OOP ディフェンスノードの全コンボに HandScore を計算し、
HS 別 raise% をプロットして「自然な不連続点（バケツ境界）」を発見する。

使用方法:
    python3 scripts/handscore_continuous_sweep.py          # 全ボード実行
    python3 scripts/handscore_continuous_sweep.py --reuse  # キャッシュ再利用
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
SOLVER_DIR = "/home/cuzic/TexasSolver"
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/flop/results/handscore_boundary")

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
# HandScore 計算
# ---------------------------------------------------------------------------

def straight_draw_score(r1: str, r2: str, board_ranks: list[str]) -> int:
    """OESD=14, gutshot=10, それ以外=0  を返す"""
    hv1, hv2 = rv(r1), rv(r2)
    bvs = {rv(r) for r in board_ranks}
    all_v = {hv1, hv2} | bvs

    best = 0

    # 通常 5枚ウィンドウ (2〜A)
    for lo in range(0, 9):          # lo=0(2〜6) 〜 lo=8(T〜A)
        window = set(range(lo, lo + 5))
        hand_in = {hv1, hv2} & window
        if not hand_in:
            continue
        missing = window - all_v
        if len(missing) == 1:
            mv = next(iter(missing))
            if mv == lo or mv == lo + 4:
                best = max(best, 14)   # OESD (端が欠け)
            else:
                best = max(best, 10)   # gutshot (内側が欠け)

    # A-2-3-4-5 ホイール (Aを-1として扱う)
    hand_wheel  = set()
    board_wheel = set()
    for r, target in ((r1, hand_wheel), (r2, hand_wheel)):
        if rv(r) == 12:
            target.add(-1)
        target.add(rv(r))
    for r in board_ranks:
        if rv(r) == 12:
            board_wheel.add(-1)
        board_wheel.add(rv(r))

    wheel_window = {-1, 0, 1, 2, 3}
    wheel_all    = hand_wheel | board_wheel
    wheel_hand   = hand_wheel & wheel_window
    if wheel_hand:
        missing_w = wheel_window - wheel_all
        if len(missing_w) == 1:
            mv = next(iter(missing_w))
            if mv in (-1, 3):
                best = max(best, 14)
            else:
                best = max(best, 10)

    return best


def compute_hs(combo: str, board_ranks: list[str], board_suits: list[str]) -> int:
    """
    HandScore を計算して返す。
    強役（ストレート以上）は便宜的に 25 以上で返す。
    """
    r1, s1, r2, s2 = parse_combo(combo)

    # ── 強役チェック ──────────────────────────────────────
    # セット (ポケットペア がボードに1枚)
    if r1 == r2 and r1 in board_ranks:
        return 25

    # トリップス (ボードに2枚同ランク + 手札1枚が一致)
    from collections import Counter
    bc = Counter(board_ranks)
    if bc.get(r1, 0) >= 2 or bc.get(r2, 0) >= 2:
        return 25

    # 2ペア (手札の2枚がそれぞれ別のボードランクとペア)
    if r1 in board_ranks and r2 in board_ranks and r1 != r2:
        return 18

    # ── 1ペア ────────────────────────────────────────────
    made = 0
    board_sorted = sorted(board_ranks, key=rv, reverse=True)
    top = board_sorted[0]
    sec = board_sorted[1] if len(board_sorted) > 1 else None

    pair_rank = kicker = None
    if r1 in board_ranks:
        pair_rank, kicker = r1, r2
    elif r2 in board_ranks:
        pair_rank, kicker = r2, r1

    if pair_rank is not None and kicker is not None:
        if pair_rank == top:
            made = 8 if rv(kicker) >= rv("T") else 6   # tpmk / tpwk
        elif pair_rank == sec:
            made = 9 if rv(kicker) >= rv("T") else 3   # 2nd_strong / 2nd_weak
        else:
            made = 3                                     # bottom pair

    # ── ドロー加点 ────────────────────────────────────────
    draw = 0

    # FD / BDFD
    if s1 == s2:
        cnt = board_suits.count(s1)
        if cnt >= 2:
            draw = max(draw, 13)   # FD (ナッツ/非ナッツ区別しない版)
        else:
            draw = max(draw, 4)    # BDFD

    # ストレートドロー
    sd = straight_draw_score(r1, r2, board_ranks)
    draw = max(draw, sd)

    return made + draw


# ---------------------------------------------------------------------------
# ソルバー実行 & 解析
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


def get_oop_node(raw: dict, bet_pct: int) -> dict | None:
    check = raw.get("childrens", {}).get("CHECK")
    if not check: return None
    expected = POT * bet_pct / 100.0
    for key, node in check.get("childrens", {}).items():
        if not key.startswith("BET"): continue
        try:
            if abs(float(key.split()[1]) - expected) < 1.5:
                return node
        except (IndexError, ValueError):
            pass
    return None


def sweep_by_hs(oop_node: dict, board_ranks: list[str],
                board_suits: list[str]) -> dict[int, dict]:
    """HandScore → {n, raise_sum, call_sum, fold_sum} を集計"""
    strat  = oop_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos  = strat.get("strategy", {})

    fi = actions.index("FOLD") if "FOLD" in actions else None
    ci = actions.index("CALL") if "CALL" in actions else None
    ri = [i for i, a in enumerate(actions) if a not in ("FOLD", "CALL", "CHECK")]

    buckets: dict[int, dict] = collections.defaultdict(
        lambda: {"n": 0, "raise": 0.0, "call": 0.0, "fold": 0.0}
    )

    for combo, probs in combos.items():
        hs = compute_hs(combo, board_ranks, board_suits)
        f = probs[fi] if fi is not None and fi < len(probs) else 0.0
        c = probs[ci] if ci is not None and ci < len(probs) else 0.0
        r = sum(probs[i] for i in ri if i < len(probs))
        b = buckets[hs]
        b["n"]     += 1
        b["raise"] += r
        b["call"]  += c
        b["fold"]  += f

    return dict(buckets)


def print_sweep(buckets: dict[int, dict], bet_pct: int, board_label: str) -> None:
    """HS 別 raise% を ASCII グラフで表示"""
    print(f"\n  [{board_label}] vs {bet_pct}% CBet — OOP raise% by HandScore")
    print(f"  {'HS':>4}  {'n':>5}  {'R%':>6}  {'C%':>6}  {'F%':>6}  グラフ (R%)")
    print(f"  {'-'*70}")

    for hs in sorted(buckets):
        b  = buckets[hs]
        n  = b["n"]
        if n == 0: continue
        r  = b["raise"] / n * 100
        c  = b["call"]  / n * 100
        f  = b["fold"]  / n * 100
        bar = "█" * int(r / 5 + 0.5)  # 5% per block
        print(f"  {hs:>4}  {n:>5}  {r:>5.1f}%  {c:>5.1f}%  {f:>5.1f}%  {bar}")


def find_jumps(buckets: dict[int, dict], bet_pct: int) -> list[tuple[int, int, float, float]]:
    """raise% が急変する (≥20pp) 箇所を返す: (hs_before, hs_after, r_before, r_after)"""
    items = [(hs, b["raise"] / b["n"] * 100)
             for hs, b in sorted(buckets.items()) if b["n"] >= 5]
    jumps = []
    for i in range(1, len(items)):
        hs_prev, r_prev = items[i-1]
        hs_cur,  r_cur  = items[i]
        if abs(r_cur - r_prev) >= 20:
            jumps.append((hs_prev, hs_cur, r_prev, r_cur))
    return jumps


# ---------------------------------------------------------------------------
# テストボード
# ---------------------------------------------------------------------------

BOARDS = [
    {"id": "K72r",  "board": "Kc,7d,2s", "board_ranks": ["K","7","2"], "board_suits": ["c","d","s"], "A": 3, "label": "K72r (dry)"},
    {"id": "T84r",  "board": "Tc,8d,4s", "board_ranks": ["T","8","4"], "board_suits": ["c","d","s"], "A": 2, "label": "T84r (semi)"},
    {"id": "T98r",  "board": "Tc,9d,8s", "board_ranks": ["T","9","8"], "board_suits": ["c","d","s"], "A": 1, "label": "T98r (wet)"},
]

# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse", action="store_true", help="キャッシュ再利用")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # 先にユニット確認
    print("=== HandScore 計算ユニットチェック (K72r) ===")
    br = ["K","7","2"]; bs = ["c","d","s"]
    checks = [
        ("Kh5d",  6,  "tpwk"),
        ("KhTd",  8,  "tpmk"),
        ("7hQd",  9,  "2nd_strong"),
        ("7h5d",  3,  "2nd_weak"),
        ("AhJh",  4,  "BDFD (no FD on K72r rainbow)"),
        ("QhJh",  4,  "BDFD offsuit? wait: QhJh = suited hearts → BDFD"),
        ("KhKd", 25,  "set"),
        ("Kh7d", 18,  "2pair"),
    ]
    for combo, expected, label in checks:
        got = compute_hs(combo, br, bs)
        mark = "✓" if got == expected else f"✗ (got {got})"
        print(f"  {combo} ({label:35}): expected={expected} {mark}")

    print("\n=== HandScore 計算ユニットチェック (T84r) ===")
    br2 = ["T","8","4"]; bs2 = ["c","d","s"]
    checks2 = [
        ("Jh9h", 14, "OESD (J9 on T84)"),
        ("QhJh", 10, "gutshot (QJ on T84: 8-9-T-J-Q needs 9)"),
        ("Ah2h",  4, "BDFD"),
        ("Th5d",  6, "tpwk (T5o)"),
        ("ThJd",  8, "tpmk (TJ)"),
        ("8hJh", 14, "2nd_strong(9)+gut? Actually: 8=2nd pair, J+T+8 → gut=10, 2nd_strong=9: 9+10=19? let's see"),
    ]
    for combo, expected, label in checks2:
        got = compute_hs(combo, br2, bs2)
        mark = "✓" if got == expected else f"△ (got {got}, expected {expected})"
        print(f"  {combo} ({label:45}): {mark}")

    print()

    all_summary: list[dict] = []

    for sc in BOARDS:
        sid    = sc["id"]
        board  = sc["board"]
        br_    = sc["board_ranks"]
        bs_    = sc["board_suits"]
        dump   = str(OUT_DIR / f"{sid}_raw.json")

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

        for bet_pct in (33, 75):
            node = get_oop_node(raw, bet_pct)
            if node is None:
                print(f"  vs{bet_pct}% ノードなし"); continue

            buckets = sweep_by_hs(node, br_, bs_)
            print_sweep(buckets, bet_pct, sc["label"])

            jumps = find_jumps(buckets, bet_pct)
            if jumps:
                print(f"\n  ⚡ 急変点 (≥20pp jump) vs {bet_pct}%:")
                for jb, ja, rb, ra in jumps:
                    print(f"     HS {jb:>2} → {ja:>2}:  {rb:.0f}% → {ra:.0f}%  (Δ={ra-rb:+.0f}pp)")

            all_summary.append({
                "board": board, "bet_pct": bet_pct,
                "buckets": {str(k): v for k, v in buckets.items()},
                "jumps": jumps,
            })

    # ──────────────────────────────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("【急変点まとめ】— バケツ境界の候補")
    print(f"{'='*65}")
    for s in all_summary:
        label = s["board"].replace(",", "")
        if s["jumps"]:
            for jb, ja, rb, ra in s["jumps"]:
                print(f"  {label} vs{s['bet_pct']}%:  HS {jb}→{ja}  {rb:.0f}%→{ra:.0f}%")

    # 保存
    out = OUT_DIR / "sweep_summary.json"
    out.write_text(json.dumps(all_summary, indent=2, ensure_ascii=False))
    print(f"\n  保存: {out}")


if __name__ == "__main__":
    main()
