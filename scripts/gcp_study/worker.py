#!/usr/bin/env python3
"""GCP VM worker: runs TexasSolver for assigned board slice, uploads results to GCS.

Usage:
  python3 worker.py \
      --bucket BUCKET_NAME \
      --vm-index 0 \
      --n-vms 5 \
      --solver /opt/TexasSolver/build/console_solver \
      --solver-dir /opt/TexasSolver \
      --boards boards.json \
      [--threads 8] \
      [--parallel 7]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# ── Config ────────────────────────────────────────────────────────────────────

POT   = 7
STACK = 97
ACCURACY     = 0.5
MAX_ITERATION = 400

IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,"
    "JTs,JTo,J9s,J8s,J7s,"
    "T9s,T8s,T7s,"
    "98s,97s,87s,86s,76s,75s,65s,54s"
)

OOP_RANGE = (
    "JJ,TT,99,88,77,66,55,44,33,22,"
    "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AQo,AJo,ATo,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "KQo,KJo,KTo,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,QJo,QTo,"
    "JTs,J9s,J8s,JTo,"
    "T9s,T8s,T7s,T9o,"
    "98s,97s,96s,98o,"
    "87s,86s,87o,"
    "76s,75s,76o,"
    "65s,65o,"
    "54s,53s,43s"
)

CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip}
set_range_oop {oop}
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes ip,flop,allin
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy {accuracy}
set_max_iteration {max_iter}
set_print_interval 200
set_dump_rounds 1
start_solve
dump_result {dump}
"""

# ── GCS helpers ───────────────────────────────────────────────────────────────

def gcs_exists(bucket: str, path: str) -> bool:
    r = subprocess.run(["gsutil", "-q", "stat", f"gs://{bucket}/{path}"],
                       capture_output=True)
    return r.returncode == 0


def gcs_upload(local: str, bucket: str, path: str) -> None:
    subprocess.run(["gsutil", "-q", "cp", local, f"gs://{bucket}/{path}"],
                   check=True)


def gcs_download(bucket: str, path: str, local: str) -> bool:
    r = subprocess.run(["gsutil", "-q", "cp", f"gs://{bucket}/{path}", local],
                       capture_output=True)
    return r.returncode == 0


# ── Solver runner ──────────────────────────────────────────────────────────────

def run_solver(solver_bin: str, solver_dir: str, board: str, dump_path: str,
               threads: int = 8, timeout: int = 300) -> bool:
    cfg = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board,
        ip=IP_RANGE, oop=OOP_RANGE,
        threads=threads, accuracy=ACCURACY, max_iter=MAX_ITERATION,
        dump=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(cfg)
        cfg_path = f.name
    try:
        with open(cfg_path) as fin:
            proc = subprocess.Popen(
                [solver_bin], stdin=fin,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=solver_dir,
            )
            try:
                rc = proc.wait(timeout=timeout)
                return rc == 0 and Path(dump_path).exists()
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                return False
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass


# ── Metric extraction ──────────────────────────────────────────────────────────

RANK_VAL = {"A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
            "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2}


def board_ranks(solver_str: str) -> tuple[int, int, int]:
    cards = solver_str.split(",")
    ranks = sorted([RANK_VAL[c[0].upper()] for c in cards], reverse=True)
    return ranks[0], ranks[1], ranks[2]


def _bet_node(parent: dict, target_pct: float) -> dict | None:
    """Return the BET child node closest to target_pct % of POT."""
    expected = POT * target_pct / 100.0
    best: dict | None = None
    best_diff = float("inf")
    for key, node in parent.get("childrens", {}).items():
        if not key.startswith("BET"):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        diff = abs(amt - expected)
        if diff < best_diff:
            best_diff = diff
            best = node
    return best if best_diff < 2.0 else None


def _avg_action(node: dict, action_prefix: str) -> float | None:
    strat = node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})
    idxs = [i for i, a in enumerate(actions)
             if a.startswith(action_prefix) or a == action_prefix]
    if not idxs or not combos:
        return None
    total = sum(
        sum(probs[i] for i in idxs if i < len(probs))
        for probs in combos.values()
    )
    return total / len(combos)


def _categorize_combo(combo: str, r_hi: int, r_mid: int, r_lo: int) -> str:
    """Classify IP combo into one of 5 categories."""
    r1 = RANK_VAL.get(combo[0].upper(), 0)
    r2 = RANK_VAL.get(combo[2].upper(), 0)
    board_set = {r_hi, r_mid, r_lo}
    if r1 == r2:                          # pocket pair
        if r1 > r_hi:   return "overpair"
        if r1 < r_lo:   return "underpair"
        return "mid_pair"
    hi, lo = max(r1, r2), min(r1, r2)
    if hi == r_hi or lo == r_hi:          return "top_pair"
    if hi > r_hi and lo > r_hi:           return "two_overcards"
    if hi not in board_set and lo not in board_set:
        return "air"
    return "other"


def _cbet_by_category(check_node: dict, category: str,
                       r_hi: int, r_mid: int, r_lo: int) -> float | None:
    strat = check_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})
    bet_idxs = [i for i, a in enumerate(actions)
                if a.startswith("BET") or a == "ALLIN"]
    matched: list[float] = []
    for combo, probs in combos.items():
        if len(combo) < 4:
            continue
        if _categorize_combo(combo, r_hi, r_mid, r_lo) != category:
            continue
        p_bet = sum(probs[i] for i in bet_idxs if i < len(probs))
        matched.append(p_bet)
    return (sum(matched) / len(matched)) if matched else None


def extract_metrics(raw: dict, board_info: dict) -> dict:
    r_hi  = board_info["r_hi"]
    r_mid = board_info["r_mid"]
    r_lo  = board_info["r_lo"]

    check_node = raw.get("childrens", {}).get("CHECK")
    if check_node is None:
        return {"error": "no CHECK node"}

    # Overall BTN CBet rate
    btn_cbet = _avg_action(check_node, "BET")
    allin_p  = _avg_action(check_node, "ALLIN") or 0.0
    btn_cbet_pct = ((btn_cbet or 0.0) + allin_p) * 100.0

    # BTN CBet by size
    metrics: dict[str, Any] = {
        "btn_cbet_pct": round(btn_cbet_pct, 2),
    }
    for pct in [33, 50, 75]:
        bn = _bet_node(check_node, pct)
        if bn is not None:
            strat = check_node.get("strategy", {})
            actions = strat.get("actions", [])
            combos  = strat.get("strategy", {})
            # Find the matching BET action index
            expected = POT * pct / 100.0
            best_idx, best_diff = -1, float("inf")
            for i, a in enumerate(actions):
                if not a.startswith("BET"):
                    continue
                try:
                    amt = float(a.split()[1])
                except (IndexError, ValueError):
                    continue
                d = abs(amt - expected)
                if d < best_diff:
                    best_diff = d
                    best_idx = i
            if best_idx >= 0 and combos:
                p = sum(probs[best_idx] for probs in combos.values()
                        if best_idx < len(probs)) / len(combos)
                metrics[f"btn_cbet_{pct}"] = round(p * 100.0, 2)

    # BB fold vs CBet size
    for pct in [33, 50, 75]:
        bn = _bet_node(check_node, pct)
        if bn is not None:
            fold_p = _avg_action(bn, "FOLD")
            if fold_p is not None:
                metrics[f"bb_fold_vs{pct}"] = round(fold_p * 100.0, 2)

    # CBet by hand category
    for cat in ["overpair", "underpair", "two_overcards", "top_pair", "air"]:
        p = _cbet_by_category(check_node, cat, r_hi, r_mid, r_lo)
        if p is not None:
            metrics[f"cbet_{cat}"] = round(p * 100.0, 2)

    return metrics


# ── Per-board processor ────────────────────────────────────────────────────────

def process_board(board: dict, solver_bin: str, solver_dir: str,
                  bucket: str, threads: int, tmpdir: Path) -> dict:
    board_id  = board["board_id"]
    gcs_path  = f"gcp_study/results/{board_id}.json"

    # Check cache
    if gcs_exists(bucket, gcs_path):
        print(f"[SKIP] {board_id} (cached)", flush=True)
        return {"board_id": board_id, "cached": True}

    dump_file = str(tmpdir / f"{board_id}.json")
    t0 = time.time()
    ok = run_solver(solver_bin, solver_dir, board["solver_str"], dump_file,
                    threads=threads)
    elapsed = time.time() - t0

    if not ok:
        print(f"[FAIL] {board_id} ({elapsed:.0f}s)", flush=True)
        return {"board_id": board_id, "error": "solver failed"}

    raw: Any = json.loads(Path(dump_file).read_text())
    Path(dump_file).unlink(missing_ok=True)

    metrics = extract_metrics(raw, board)
    result = {**board, **metrics, "elapsed_s": round(elapsed, 1)}

    # Save locally then upload
    local_result = str(tmpdir / f"result_{board_id}.json")
    Path(local_result).write_text(json.dumps(result, ensure_ascii=False))
    gcs_upload(local_result, bucket, gcs_path)
    Path(local_result).unlink(missing_ok=True)

    status = "OK" if "error" not in metrics else f"ERR:{metrics['error']}"
    cbet = metrics.get("btn_cbet_pct", "?")
    print(f"[{status}] {board_id:12s}  CBet={cbet}%  ({elapsed:.0f}s)", flush=True)
    return {"board_id": board_id, "ok": True}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket",     required=True)
    ap.add_argument("--vm-index",   type=int, required=True)
    ap.add_argument("--n-vms",      type=int, required=True)
    ap.add_argument("--solver",     required=True)
    ap.add_argument("--solver-dir", required=True)
    ap.add_argument("--boards",     default="boards.json")
    ap.add_argument("--threads",    type=int, default=8,
                    help="TexasSolver thread_num per instance")
    ap.add_argument("--parallel",   type=int, default=6,
                    help="Boards processed simultaneously")
    args = ap.parse_args()

    boards: list[dict] = json.loads(Path(args.boards).read_text())
    assigned = [b for i, b in enumerate(boards) if i % args.n_vms == args.vm_index]
    print(f"VM {args.vm_index}/{args.n_vms}: {len(assigned)} boards assigned")

    tmpdir = Path(tempfile.mkdtemp(prefix="solver_"))

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futs = {
            pool.submit(process_board, b, args.solver, args.solver_dir,
                        args.bucket, args.threads, tmpdir): b["board_id"]
            for b in assigned
        }
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as e:
                bid = futs[fut]
                print(f"[EXC] {bid}: {e}", flush=True)
                results.append({"board_id": bid, "error": str(e)})

    ok_count  = sum(1 for r in results if r.get("ok") or r.get("cached"))
    err_count = len(results) - ok_count
    print(f"\nDone: {ok_count} OK, {err_count} errors")

    # Upload a completion marker
    marker = str(tmpdir / f"done_vm{args.vm_index}.txt")
    Path(marker).write_text(f"ok={ok_count} err={err_count}")
    gcs_upload(marker, args.bucket, f"gcp_study/done/vm{args.vm_index}.txt")

    tmpdir.rmdir() if not any(tmpdir.iterdir()) else None


if __name__ == "__main__":
    main()
