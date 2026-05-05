#!/usr/bin/env python3
"""
C係数 (50%=4 vs 5, 75%=6 vs 7) GTO 検証スクリプト
K72r ドライボード, SRP BTN vs BB, IP CBet サイズ別の OOP 境界ハンドを実測。

検証仮説:
  ────────────────────────────────────────────
  CBet  | calc.py (C) | ch.16 (C) | 境界ハンド    | CALL→? / FOLD→?
  ────────────────────────────────────────────
  50%   |     5       |     4     | A2o (HS=4)  | FOLD→C=5正 / CALL→C=4正
  75%   |     7       |     6     | JJ  (HS=6)  | FOLD→C=7正 / CALL→C=6正
  ────────────────────────────────────────────

ボード: K♣7♦2♠ (dry, A=3)
ポット: 7bb, スタック: 97bb (標準 SRP BTN vs BB 100BB)

使用方法:
    python3 scripts/texassolver_c_coef_srp_verify.py [--dry-run]

出力:
    knowledges/volume4/results/c_coef_srp/result.json
    (標準出力にサマリーを表示)
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

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/volume4/results/c_coef_srp")

# BTN オープンレンジ (IP)
IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,"
    "A6s,A6o,A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,T9s,T8s,T7s,T6s,98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)

# BB ディフェンドレンジ (OOP) — QQ以上は3ベット、JJ以下コール
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

BOARD = "Kc,7d,2s"
POT = 7
STACK = 97

# フロップのみのツリー（ターン/リバーは省略してツリー圧縮）
CONFIG = f"""\
set_pot {POT}
set_effective_stack {STACK}
set_board {BOARD}
set_range_ip {IP_RANGE}
set_range_oop {OOP_RANGE}
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
dump_result {{dump_path}}
"""


def run_solver(dump_path: str, timeout: int = 300) -> int:
    config_text = CONFIG.format(dump_path=dump_path)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_ccoef_srp_"
    ) as f:
        f.write(config_text)
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


def get_oop_response_node(raw: dict[str, Any], bet_pct: int) -> dict[str, Any] | None:
    """
    OOP check → IP bet X → OOP response ノードを返す。
    root: OOP acts first (CHECK or BET)
    root['childrens']['CHECK']: IP acts
    ['CHECK']['childrens']['BET X']: OOP responds
    """
    ra: Any = raw
    check_node: Any = ra.get("childrens", {}).get("CHECK")
    if check_node is None:
        return None
    ip_children: Any = check_node.get("childrens", {})
    expected_amount = POT * bet_pct / 100.0
    for key, node in ip_children.items():
        if not key.startswith("BET"):
            continue
        try:
            amount = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        if abs(amount - expected_amount) < 1.5:
            return node  # type: ignore[return-value]
    return None


def extract_hand_stats(response_node: dict[str, Any], target_prefix: str) -> dict[str, Any]:
    """
    target_prefix: "JJ", "A2" など combo の先頭 2 文字
    """
    strat: Any = response_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        fold_idx = actions.index("FOLD")
        call_idx = actions.index("CALL")
    except ValueError:
        return {"error": f"FOLD/CALL not in actions: {actions}"}

    matched: list[dict[str, Any]] = []
    for combo, probs in combos.items():
        # combo like "JhJd", "Ah2c" etc.
        c0, c1 = combo[:2], combo[2:4]
        rank0 = c0[0].upper()  # A/K/Q/J/T/9...
        rank1 = c1[0].upper()
        pair_repr = "".join(sorted([rank0, rank1], reverse=True))
        if pair_repr.startswith(target_prefix) or combo[:2].upper() == target_prefix:
            fold_p = probs[fold_idx] if fold_idx < len(probs) else 0.0
            call_p = probs[call_idx] if call_idx < len(probs) else 0.0
            matched.append({"combo": combo, "call": call_p, "fold": fold_p})

    if not matched:
        return {"error": f"no combos found for prefix {target_prefix!r}"}

    avg_call = sum(m["call"] for m in matched) / len(matched)
    avg_fold = sum(m["fold"] for m in matched) / len(matched)
    return {
        "n_combos": len(matched),
        "avg_call_pct": round(avg_call * 100, 1),
        "avg_fold_pct": round(avg_fold * 100, 1),
        "combos": matched,
    }


# HandScore on K72r (ドライ)
HAND_SCORES: dict[str, int] = {
    "JJ": 6,   # underpair (J < K)
    "TT": 6,   # underpair
    "99": 6,   # underpair
    "A2": 4,   # bottom pair (2 on board) — A2o
    "A3": 0,   # air (neither A nor 3 on K72r) + no draw → HS=0 (A3o)
    "98": 14,  # OESD (9-8-7-6 or 8-7-6-5 needs checking): 9-8 + K,7,2 → no OESD actually
}

# ─── 手動確認: K72r での各ハンド ────────────────────────────────
# JJ: h=J(11) > K(13)? No. J < K → underpair → HS=6
# A2: h=A(14), l=2(2), 2 is on board → bottom_pair → HS=4
# A3: h=A(14), l=3(3), neither on board → air. No two-overcard (only A > K). No OESD. HS≈0
#   A3s: air + BDFD → 0+4=4
#   A3o: air + 0 → 0
# ──────────────────────────────────────────────────────────────

# テスト仕様:
# 1) A2o vs 50%:  CALL → C=4 (ch.16), FOLD → C=5 (calc.py)
# 2) JJ vs 75%:   CALL → C=6 (ch.16), FOLD → C=7 (calc.py)
# 補足:
# 3) A2o vs 33%:  両仮説とも CALL のはず (HS=4 ≥ C=3)  → 整合性チェック
# 4) JJ  vs 50%:  両仮説とも CALL のはず (HS=6 ≥ C=4,5) → 整合性チェック

TESTS = [
    (33,  "A2", 4, "sanity: A2o must CALL vs 33% (C=3, HS≥3 → CALL)"),
    (50,  "A2", 4, "KEY TEST: A2o vs 50% → CALL⇒C=4(ch.16), FOLD⇒C=5(calc.py)"),
    (75,  "A2", 4, "sanity: A2o must FOLD vs 75% (HS=4 < C=6,7)"),
    (50,  "JJ", 6, "sanity: JJ must CALL vs 50% (HS=6 ≥ C=4,5)"),
    (75,  "JJ", 6, "KEY TEST: JJ vs 75% → CALL⇒C=6(ch.16), FOLD⇒C=7(calc.py)"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="スキップして既存結果を表示")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    dump_path = str(OUT_DIR / "k72r_srp_raw.json")

    if args.dry_run:
        if not Path(dump_path).exists():
            print("dry-run: no cached result found. Run without --dry-run first.")
            return
    else:
        if Path(dump_path).exists():
            print(f"キャッシュ済み: {dump_path} を再利用します")
        else:
            print(f"TexasSolver 実行中 (K72r SRP, CBet 33/50/75%) ...")
            t0 = time.time()
            rc = run_solver(dump_path)
            elapsed = time.time() - t0
            if rc != 0 or not Path(dump_path).exists():
                print(f"ERROR: solver rc={rc}")
                return
            print(f"完了: {elapsed:.0f}s")

    raw: Any = json.loads(Path(dump_path).read_text())

    # ── 結果解析 ───────────────────────────────────────────────────────────────
    results = {}
    for bet_pct, hand, hs, desc in TESTS:
        node = get_oop_response_node(raw, bet_pct)
        if node is None:
            print(f"  [{bet_pct}% / {hand}] ノードが見つかりません")
            results[f"{bet_pct}_{hand}"] = {"error": "node not found"}
            continue
        stats = extract_hand_stats(node, hand)
        results[f"{bet_pct}_{hand}"] = stats

        call_p = stats.get("avg_call_pct", 0)
        fold_p = stats.get("avg_fold_pct", 0)
        verdict = ""
        if "error" not in stats:
            if call_p >= 60:
                verdict = "→ CALL優位"
            elif fold_p >= 60:
                verdict = "→ FOLD優位"
            else:
                verdict = "→ 混合"
        print(f"\n[{bet_pct}% / {hand} (HS={hs})]")
        print(f"  {desc}")
        print(f"  CALL={call_p:.1f}%  FOLD={fold_p:.1f}%  {verdict}")
        if stats.get("combos"):
            for c in stats["combos"][:4]:
                print(f"    {c['combo']}: call={c['call']*100:.0f}%, fold={c['fold']*100:.0f}%")

    # ── 判定 ──────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("C係数判定")
    print("=" * 60)

    # Test 50% / A2 (HS=4)
    key_50_a2 = results.get("50_A2", {})
    call_50 = key_50_a2.get("avg_call_pct", -1)
    if call_50 >= 50:
        print(f"  50% CBet: A2o (HS=4) CALL {call_50:.0f}%  → C ≤ 4 が正しい (ch.16 支持)")
    elif call_50 >= 0:
        fold_50 = key_50_a2.get("avg_fold_pct", 0)
        print(f"  50% CBet: A2o (HS=4) FOLD {fold_50:.0f}%  → C = 5 が正しい (calc.py 支持)")
    else:
        print("  50% CBet: A2o データなし")

    # Test 75% / JJ (HS=6)
    key_75_jj = results.get("75_JJ", {})
    call_75 = key_75_jj.get("avg_call_pct", -1)
    if call_75 >= 50:
        print(f"  75% CBet: JJ (HS=6)   CALL {call_75:.0f}%  → C ≤ 6 が正しい (ch.16 支持)")
    elif call_75 >= 0:
        fold_75 = key_75_jj.get("avg_fold_pct", 0)
        print(f"  75% CBet: JJ (HS=6)   FOLD {fold_75:.0f}%  → C = 7 が正しい (calc.py 支持)")
    else:
        print("  75% CBet: JJ データなし")
    print("=" * 60)

    # 保存
    out_json = OUT_DIR / "result.json"
    out_json.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\n結果保存: {out_json}")


if __name__ == "__main__":
    main()
