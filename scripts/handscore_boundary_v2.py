#!/usr/bin/env python3
"""
HandScore バケツ境界検証 v2 — 非ナッツFD / tpwk OOP / 組み合わせハンド

v1 の課題を補完:
  1. 非ナッツ FD (Q高・T高) — FD を一律 H3 にしていいか確認
  2. tpwk の OOP 防衛データ — H1→H2 変更根拠
  3. 組み合わせハンド (pair+FD, pair+BDFD, pair+gut, OESD+pair) の実測

使用方法:
    python3 scripts/handscore_boundary_v2.py
    python3 scripts/handscore_boundary_v2.py --reuse   # キャッシュ再利用
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

# ---------------------------------------------------------------------------
# コンボ分類ユーティリティ
# ---------------------------------------------------------------------------

def parse_combo(c: str) -> tuple[str, str, str, str]:
    return c[0].upper(), c[1].lower(), c[2].upper(), c[3].lower()

def ranks(c: str) -> frozenset[str]:
    r1, _, r2, _ = parse_combo(c)
    return frozenset([r1, r2])

def suited(c: str) -> bool:
    _, s1, _, s2 = parse_combo(c)
    return s1 == s2

def offsuit(c: str) -> bool:
    return not suited(c)

def has_pair_with(c: str, board_ranks: list[str]) -> bool:
    r1, _, r2, _ = parse_combo(c)
    return r1 in board_ranks or r2 in board_ranks

def has_fd(c: str, board_suits: list[str]) -> bool:
    """手札2枚が同スート、かつそのスートがボードに2枚ある"""
    _, s1, _, s2 = parse_combo(c)
    if s1 != s2:
        return False
    return board_suits.count(s1) >= 2

def top_pair_kicker(c: str, top_rank: str) -> str | None:
    """c がトップペアなら kicker の rank を返す、違えば None"""
    r1, _, r2, _ = parse_combo(c)
    if r1 == top_rank:
        return r2
    if r2 == top_rank:
        return r1
    return None

RANK_VAL = {r: i for i, r in enumerate("23456789TJQKA")}

def rank_val(r: str) -> int:
    return RANK_VAL.get(r.upper(), -1)

# ---------------------------------------------------------------------------
# テストシナリオ定義
# ---------------------------------------------------------------------------
# board_suits は ['c','d','s'] など小文字でフラット展開

SCENARIOS = [
    # ──────────────────────────────────────────────────────────────────────
    # Board 1: Ks7c2c — ナッツFD vs 非ナッツFD、ペア+FD 組み合わせ
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "Ks7c2c",
        "board": "Ks,7c,2c",
        "board_ranks": ["K", "7", "2"],
        "board_suits": ["s", "c", "c"],
        "A": 3,
        "label": "Ks7c2c (dry, clubs FD board)",
        "hands": [
            {
                "label": "ナッツFD単独 AcXc [formula H2=13]",
                "test_fn": lambda c: (
                    suited(c)
                    and parse_combo(c)[1] == "c"          # clubs
                    and parse_combo(c)[0] == "A"           # A-high
                    and not has_pair_with(c, ["K","7","2"])
                ),
                "formula_hs": 13,
                "formula_bucket": "H2",
                "intuitive": "H3 (強いドロー)",
            },
            {
                "label": "非ナッツFD QcXc [formula H2=13]",
                "test_fn": lambda c: (
                    suited(c)
                    and parse_combo(c)[1] == "c"
                    and parse_combo(c)[0] == "Q"
                    and not has_pair_with(c, ["K","7","2"])
                ),
                "formula_hs": 13,
                "formula_bucket": "H2",
                "intuitive": "H2 (Q高FD)",
            },
            {
                "label": "非ナッツFD TcXc [formula H2=13]",
                "test_fn": lambda c: (
                    suited(c)
                    and parse_combo(c)[1] == "c"
                    and parse_combo(c)[0] == "T"
                    and not has_pair_with(c, ["K","7","2"])
                ),
                "formula_hs": 13,
                "formula_bucket": "H2",
                "intuitive": "H2 (T高FD)",
            },
            {
                "label": "tpmk+nut FD KcJc/KcTc [formula H3=21/20]",
                "test_fn": lambda c: (
                    suited(c)
                    and parse_combo(c)[1] == "c"
                    and ranks(c) in (frozenset(["K","J"]), frozenset(["K","T"]))
                    # Kc pairs Ks on board, Jc/Tc = nut(near-nut) FD component
                ),
                "formula_hs": 21,
                "formula_bucket": "H3",
                "intuitive": "H3",
            },
            {
                "label": "tpwk+FD Kc5c [formula H3=19]",
                "test_fn": lambda c: (
                    suited(c)
                    and parse_combo(c)[1] == "c"
                    and ranks(c) == frozenset(["K","5"])
                ),
                "formula_hs": 19,
                "formula_bucket": "H3",
                "intuitive": "H3",
            },
            {
                "label": "tpmk no FD KhJd/KhTd [formula H2=8]",
                "test_fn": lambda c: (
                    offsuit(c)
                    and ranks(c) in (frozenset(["K","J"]), frozenset(["K","T"]))
                ),
                "formula_hs": 8,
                "formula_bucket": "H2",
                "intuitive": "H2",
            },
            {
                "label": "tpmk+BDFD KhJh [formula H2=12]",
                "test_fn": lambda c: (
                    suited(c)
                    and ranks(c) in (frozenset(["K","J"]), frozenset(["K","T"]))
                    and parse_combo(c)[1] != "c"   # not clubs (no FD, only BDFD)
                    # hearts/diamonds/spades: no 2nd card of same suit on Ks7c2c board
                ),
                "formula_hs": 12,
                "formula_bucket": "H2",
                "intuitive": "H2 (ペア+BDFD)",
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────────
    # Board 2: Ad7c2s — tpwk vs tpmk の OOP 防衛 (rainbow, FD なし)
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "A72r",
        "board": "Ad,7c,2s",
        "board_ranks": ["A", "7", "2"],
        "board_suits": ["d", "c", "s"],
        "A": 3,
        "label": "A72r (dry, rainbow — tpwk vs tpmk OOP テスト)",
        "hands": [
            {
                "label": "tpwk A3o-A6o [formula H1=6]",
                "test_fn": lambda c: (
                    offsuit(c)
                    and parse_combo(c)[0] == "A"
                    and parse_combo(c)[2] in ("3","4","5","6")
                ),
                "formula_hs": 6,
                "formula_bucket": "H1",
                "intuitive": "H2 (ペアあり)",
            },
            {
                "label": "tpmk ATo/AJo [formula H2=8]",
                "test_fn": lambda c: (
                    offsuit(c)
                    and ranks(c) in (frozenset(["A","T"]), frozenset(["A","J"]))
                ),
                "formula_hs": 8,
                "formula_bucket": "H2",
                "intuitive": "H2",
            },
            {
                "label": "tpwk A8o/A9o [formula H1=6]",
                "test_fn": lambda c: (
                    offsuit(c)
                    and parse_combo(c)[0] == "A"
                    and parse_combo(c)[2] in ("8","9")
                ),
                "formula_hs": 6,
                "formula_bucket": "H1",
                "intuitive": "H2",
            },
        ],
    },

    # ──────────────────────────────────────────────────────────────────────
    # Board 3: Tc8d4s (v1 既存) — gutshot / BDFD / pair+gut 追加
    # ──────────────────────────────────────────────────────────────────────
    {
        "id": "T84r_v2",
        "board": "Tc,8d,4s",
        "board_ranks": ["T", "8", "4"],
        "board_suits": ["c", "d", "s"],
        "A": 2,
        "label": "T84r (semi) — gutshot/BDFD/組み合わせ追加",
        "hands": [
            {
                "label": "gutshot単独 QhJh [formula H2=10]",
                # QJ on T84: 8-9-T-J-Q needs 9 (interior) = gutshot
                "test_fn": lambda c: (
                    suited(c)
                    and ranks(c) == frozenset(["Q","J"])
                    and not has_pair_with(c, ["T","8","4"])
                    and not has_fd(c, ["c","d","s"])   # rainbow board → no FD possible
                ),
                "formula_hs": 10,
                "formula_bucket": "H2",
                "intuitive": "H2",
            },
            {
                "label": "BDFD単独 Ah2h [formula H1=4]",
                # A2 on T84: A と 2 はどちらも board に当たらない, hearts BDFD
                "test_fn": lambda c: (
                    suited(c)
                    and ranks(c) == frozenset(["A","2"])
                    and not has_pair_with(c, ["T","8","4"])
                ),
                "formula_hs": 4,
                "formula_bucket": "H1",
                "intuitive": "H1",
            },
            {
                "label": "2ndペア+gut 8hJh [formula H3~19]",
                # 8hJh on T84: pair of 8s + gutshot (J-T-?-8-7 needs 9)
                # formula: second_pair(9)+gut(10)=19 → H3
                "test_fn": lambda c: (
                    suited(c)
                    and ranks(c) == frozenset(["8","J"])
                    and not has_fd(c, ["c","d","s"])   # board rainbow: 同スートあっても no FD
                ),
                "formula_hs": 19,
                "formula_bucket": "H3",
                "intuitive": "H3 (ペア+ドロー)",
            },
            {
                "label": "OESD単独 J9 全スート [formula H2=14] (v1 再確認)",
                "test_fn": lambda c: (
                    ranks(c) == frozenset(["J","9"])
                    and not has_pair_with(c, ["T","8","4"])
                ),
                "formula_hs": 14,
                "formula_bucket": "H2",
                "intuitive": "H3",
            },
        ],
    },
]

# ---------------------------------------------------------------------------
# ソルバー実行
# ---------------------------------------------------------------------------

def run_solver(board: str, dump_path: str, timeout: int = 400) -> int:
    config = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board,
        ip_range=IP_RANGE, oop_range=OOP_RANGE, dump_path=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, prefix="ts_hsbv2_") as f:
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
                proc.kill(); proc.wait(); rc = -1
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass
    return rc


def get_ip_cbet_node(raw: dict) -> dict | None:
    return raw.get("childrens", {}).get("CHECK")


def get_oop_defense_node(raw: dict, bet_pct: int) -> dict | None:
    check = raw.get("childrens", {}).get("CHECK")
    if not check:
        return None
    expected = POT * bet_pct / 100.0
    for key, node in check.get("childrens", {}).items():
        if not key.startswith("BET"):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        if abs(amt - expected) < 1.5:
            return node
    return None


def extract_ip_cbet(ip_node: dict, fn) -> dict:
    strat = ip_node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})
    try:
        chk_idx = actions.index("CHECK")
    except ValueError:
        chk_idx = None
    matched = []
    for c, probs in combos.items():
        if not fn(c):
            continue
        cbet = (1.0 - probs[chk_idx]) if chk_idx is not None and chk_idx < len(probs) else 1.0
        matched.append((c, cbet))
    if not matched:
        return {"n": 0, "pct": None}
    avg = sum(v for _, v in matched) / len(matched)
    return {"n": len(matched), "pct": round(avg * 100, 1),
            "top": sorted(matched, key=lambda x: -x[1])[:4]}


def extract_oop(node: dict, fn) -> dict:
    strat = node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})
    fi = actions.index("FOLD") if "FOLD" in actions else None
    ci = actions.index("CALL") if "CALL" in actions else None
    ri = [i for i, a in enumerate(actions) if a not in ("FOLD","CALL","CHECK")]
    matched = []
    for c, probs in combos.items():
        if not fn(c):
            continue
        f = probs[fi] if fi is not None and fi < len(probs) else 0.0
        call = probs[ci] if ci is not None and ci < len(probs) else 0.0
        raise_ = sum(probs[i] for i in ri if i < len(probs))
        matched.append((c, f, call, raise_))
    if not matched:
        return {"n": 0}
    n = len(matched)
    return {
        "n": n,
        "F": round(sum(x[1] for x in matched)/n*100, 1),
        "C": round(sum(x[2] for x in matched)/n*100, 1),
        "R": round(sum(x[3] for x in matched)/n*100, 1),
    }


def bucket_from_defense(R: float, C: float, F: float) -> str:
    if R >= 50:  return "H3 (raise優位)"
    if R >= 25:  return "H2-H3境界"
    if C >= 50:  return "H2 (call優位)"
    if F >= 50:  return "H1 (fold優位)"
    return "混合"


def bucket_from_cbet(pct: float | None) -> str:
    if pct is None: return "N/A"
    if pct >= 85:   return "H3相当"
    if pct >= 60:   return "H2-H3"
    if pct >= 35:   return "H2-H1境界"
    return "H1相当"


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reuse", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict] = []

    for sc in SCENARIOS:
        sid = sc["id"]
        board = sc["board"]
        dump_path = str(OUT_DIR / f"{sid}_raw.json")

        print(f"\n{'='*65}")
        print(f"  {sc['label']}")
        print(f"{'='*65}")

        if args.reuse and Path(dump_path).exists():
            print(f"  キャッシュ: {dump_path}")
        else:
            print(f"  Solving {board} ...")
            t0 = time.time()
            rc = run_solver(board, dump_path)
            elapsed = time.time() - t0
            if rc != 0 or not Path(dump_path).exists():
                print(f"  ERROR rc={rc}"); continue
            print(f"  完了 {elapsed:.0f}s")

        raw = json.loads(Path(dump_path).read_text())
        ip_node     = get_ip_cbet_node(raw)
        oop33_node  = get_oop_defense_node(raw, 33)
        oop75_node  = get_oop_defense_node(raw, 75)

        if ip_node is None:
            print("  ERROR: IP node missing"); continue

        print(f"\n  {'ハンド':<40} {'CBet%':>7} {'IP分類':>12}  OOP vs33%                OOP vs75%")
        print(f"  {'-'*115}")

        for h in sc["hands"]:
            fn    = h["test_fn"]
            ip_s  = extract_ip_cbet(ip_node, fn)
            d33: dict = extract_oop(oop33_node, fn) if oop33_node else {"n":0}
            d75: dict = extract_oop(oop75_node, fn) if oop75_node else {"n":0}

            cb_str  = f"{ip_s['pct']:.1f}% (n={ip_s['n']})" if ip_s["pct"] is not None else "N/A"
            cb_cls  = bucket_from_cbet(ip_s["pct"])

            def fmt_oop(d: dict) -> str:
                if d.get("n", 0) == 0:
                    return "—"
                cls = bucket_from_defense(d["R"], d["C"], d["F"])
                return f"R={d['R']:.0f}% C={d['C']:.0f}% F={d['F']:.0f}%  [{cls}]"

            label = h["label"]
            print(f"  {label:<40} {cb_str:>13} {cb_cls:>12}")
            print(f"    {'vs33%':>6}: {fmt_oop(d33)}")
            print(f"    {'vs75%':>6}: {fmt_oop(d75)}")
            print()

            all_rows.append({
                "board": board, "label": label,
                "formula_bucket": h["formula_bucket"],
                "formula_hs": h["formula_hs"],
                "intuitive": h["intuitive"],
                "ip_cbet": ip_s["pct"], "n_ip": ip_s["n"],
                "oop33": d33 if d33.get("n",0)>0 else None,
                "oop75": d75 if d75.get("n",0)>0 else None,
            })

    # ────────────────────────────────────────────────────────────────────
    print(f"\n\n{'='*65}")
    print("【判定サマリー】数値式バケツ vs 直接マッピング v2")
    print(f"{'='*65}")
    print()

    HEADER = f"{'ハンド':<35} {'式':>4} {'直感':>5}  {'IP CBet':>8}  OOP判定(vs33% / vs75%)"
    print(f"  {HEADER}")
    print(f"  {'-'*100}")

    for r in all_rows:
        lbl  = r["label"].split("[")[0].strip()
        fb   = r["formula_bucket"]
        ib   = r["intuitive"].split()[0]
        cb   = f"{r['ip_cbet']:.0f}%" if r["ip_cbet"] is not None else "N/A"

        def oop_verdict(d: dict | None) -> str:
            if not d:
                return "—"
            return bucket_from_defense(d["R"], d["C"], d["F"])

        v33 = oop_verdict(r.get("oop33"))
        v75 = oop_verdict(r.get("oop75"))

        match = "✓" if fb.split()[0] == ib.split()[0] else "⚠"
        print(f"  {match} {lbl:<35} {fb:>4} {ib:>5}  {cb:>8}  {v33} / {v75}")

    # 保存
    out = OUT_DIR / "summary_v2.json"
    out.write_text(json.dumps(all_rows, indent=2, ensure_ascii=False))
    print(f"\n  保存: {out}")


if __name__ == "__main__":
    main()
