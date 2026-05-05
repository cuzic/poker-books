#!/usr/bin/env python3
"""
ナッツFD + ペア の GTO アクション検証

ボード Js8c4c (J♠8♣4♣) を使用:
  - clubs FD 可能 (8c, 4c on board)
  - ナッツFD = Ac-high clubs
  - ナッツFD + トップペア = AcJc (AJs の中の clubs combo)
  - 非ナッツFD + トップペア = KcJc, QcJc
  - ナッツFD のみ = AcQc, AcTc, Ac9c ...

使用方法:
    python3 scripts/handscore_fd_pair_verify.py          # ソルブして検証
    python3 scripts/handscore_fd_pair_verify.py --reuse  # キャッシュ再利用
"""
from __future__ import annotations

import argparse
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
# コンボ分類
# ---------------------------------------------------------------------------

BOARD_RANKS = ["J", "8", "4"]
BOARD_SUITS = ["s", "c", "c"]   # Js, 8c, 4c
BOARD_SET   = {"Js", "8c", "4c"}


def classify_combo(c: str) -> str:
    """
    コンボをカテゴリに分類。
    Returns:
        "nut_fd+pair"     : Ace-high clubs FD + ペア
        "nut_fd_only"     : Ace-high clubs FD, ペアなし
        "nonnut_fd+pair"  : 非ナッツ clubs FD + ペア
        "nonnut_fd_only"  : 非ナッツ clubs FD, ペアなし
        "pair_only"       : ペアのみ（FDなし）
        "other"           : その他（ストレートドロー、BDFD、役なし等）
    """
    r1, s1, r2, s2 = parse_combo(c)

    # 無効コンボ除去（ボードカードを含む）
    c1 = r1 + s1
    c2 = r2 + s2
    if c1 in BOARD_SET or c2 in BOARD_SET:
        return "invalid"

    # FD判定（clubs FDのみ：ボードに8c, 4c の2クラブ）
    has_clubs_fd = (s1 == "c" and s2 == "c")
    is_nut_fd    = has_clubs_fd and ("A" in (r1, r2))

    # ペア判定
    has_pair = (r1 in BOARD_RANKS) or (r2 in BOARD_RANKS)

    if is_nut_fd and has_pair:
        return "nut_fd+pair"
    if is_nut_fd and not has_pair:
        return "nut_fd_only"
    if has_clubs_fd and not is_nut_fd and has_pair:
        return "nonnut_fd+pair"
    if has_clubs_fd and not is_nut_fd and not has_pair:
        return "nonnut_fd_only"
    if has_pair:
        return "pair_only"
    return "other"


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


# ---------------------------------------------------------------------------
# 集計・表示
# ---------------------------------------------------------------------------

def analyze_node(oop_node: dict, bet_pct: int) -> None:
    strat   = oop_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos  = strat.get("strategy", {})

    fi = actions.index("FOLD") if "FOLD" in actions else None
    ci = actions.index("CALL") if "CALL" in actions else None
    ri = [i for i, a in enumerate(actions) if a not in ("FOLD", "CALL", "CHECK")]

    groups: dict[str, dict] = {
        "nut_fd+pair":    {"n": 0, "r": 0.0, "c": 0.0, "f": 0.0, "combos": []},
        "nut_fd_only":    {"n": 0, "r": 0.0, "c": 0.0, "f": 0.0, "combos": []},
        "nonnut_fd+pair": {"n": 0, "r": 0.0, "c": 0.0, "f": 0.0, "combos": []},
        "nonnut_fd_only": {"n": 0, "r": 0.0, "c": 0.0, "f": 0.0, "combos": []},
        "pair_only":      {"n": 0, "r": 0.0, "c": 0.0, "f": 0.0, "combos": []},
    }

    for combo, probs in combos.items():
        cat = classify_combo(combo)
        if cat not in groups:
            continue
        g = groups[cat]
        f = probs[fi] if fi is not None and fi < len(probs) else 0.0
        c = probs[ci] if ci is not None and ci < len(probs) else 0.0
        r = sum(probs[i] for i in ri if i < len(probs))
        g["n"] += 1
        g["r"] += r
        g["c"] += c
        g["f"] += f
        g["combos"].append((combo, r, c, f))

    print(f"\n  vs {bet_pct}% CBet")
    print(f"  {'カテゴリ':<22}  {'n':>4}  {'R%':>6}  {'C%':>6}  {'F%':>6}  {'バケツ判定'}")
    print(f"  {'-'*70}")

    ORDER = ["nut_fd+pair", "nut_fd_only", "nonnut_fd+pair", "nonnut_fd_only", "pair_only"]
    for cat in ORDER:
        g = groups[cat]
        n = g["n"]
        if n == 0:
            print(f"  {cat:<22}  {'—':>4}")
            continue
        r = g["r"] / n * 100
        c = g["c"] / n * 100
        f = g["f"] / n * 100
        bucket = "H3" if r >= 40 else ("H2" if r >= 10 or c >= 60 else "H1")
        print(f"  {cat:<22}  {n:>4}  {r:>5.1f}%  {c:>5.1f}%  {f:>5.1f}%  → {bucket}")

    # nut_fd+pair の個別コンボ詳細
    g = groups["nut_fd+pair"]
    if g["n"] > 0:
        print(f"\n  [nut_fd+pair 個別コンボ]")
        for combo, r, c, f in sorted(g["combos"], key=lambda x: -x[1]):
            print(f"    {combo}  R={r*100:>5.1f}%  C={c*100:>5.1f}%  F={f*100:>5.1f}%")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()

    # ──────────────────────────────────────────────
    # 1. T98r two pair 確認（既存キャッシュ）
    # ──────────────────────────────────────────────
    print("=" * 65)
    print("【確認①】ウェットボード (T98r) の two pair")
    print("=" * 65)
    t98_path = OUT_DIR / "T98r_raw.json"
    if t98_path.exists():
        raw98 = json.loads(t98_path.read_text())
        for bet_pct in (33, 75):
            node = get_oop_node(raw98, bet_pct)
            if node is None:
                print(f"  vs{bet_pct}% ノードなし"); continue
            strat   = node.get("strategy", {})
            actions = strat.get("actions", [])
            combos  = strat.get("strategy", {})
            fi = actions.index("FOLD") if "FOLD" in actions else None
            ci = actions.index("CALL") if "CALL" in actions else None
            ri = [i for i, a in enumerate(actions) if a not in ("FOLD", "CALL", "CHECK")]

            two_pair_combos = []
            for combo, probs in combos.items():
                r1, s1, r2, s2 = parse_combo(combo)
                board_r = ["T", "9", "8"]
                if r1 in board_r and r2 in board_r and r1 != r2:
                    f = probs[fi] if fi is not None and fi < len(probs) else 0.0
                    c = probs[ci] if ci is not None and ci < len(probs) else 0.0
                    r = sum(probs[i] for i in ri if i < len(probs))
                    two_pair_combos.append((combo, r, c, f))

            if two_pair_combos:
                n  = len(two_pair_combos)
                ar = sum(x[1] for x in two_pair_combos) / n * 100
                ac = sum(x[2] for x in two_pair_combos) / n * 100
                af = sum(x[3] for x in two_pair_combos) / n * 100
                bucket = "H3" if ar >= 40 else ("H2" if ar >= 10 or ac >= 60 else "H1")
                print(f"  vs{bet_pct}%: n={n}  R={ar:.1f}%  C={ac:.1f}%  F={af:.1f}%  → {bucket}")
    else:
        print("  T98r_raw.json not found")

    # ──────────────────────────────────────────────
    # 2. Js8c4c: ナッツFD+ペア 検証
    # ──────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("【確認②】ナッツFD + ペア  (ボード Js8c4c)")
    print("  Js:J♠  8c:8♣  4c:4♣  →  クラブFD可能")
    print("  AcJc = トップペア(J) + ナッツFD(Ac-high clubs)")
    print("=" * 65)

    dump = str(OUT_DIR / "Js8c4c_raw.json")
    if args.reuse and Path(dump).exists():
        print(f"  キャッシュ: {dump}")
    else:
        print("  Solving Js,8c,4c ...")
        t0 = time.time()
        rc = run_solver("Js,8c,4c", dump)
        if rc != 0 or not Path(dump).exists():
            print(f"  ERROR rc={rc}"); return
        print(f"  完了 {time.time()-t0:.0f}s")

    raw = json.loads(Path(dump).read_text())

    print("\n  ボード: J♠8♣4♣  (クラブFD = 8c,4cが2枚)")
    print("  ─────────────────────────────────────────────────────────────────")
    for bet_pct in (33, 75):
        node = get_oop_node(raw, bet_pct)
        if node is None:
            print(f"  vs{bet_pct}% ノードなし"); continue
        analyze_node(node, bet_pct)

    print()


if __name__ == "__main__":
    main()
