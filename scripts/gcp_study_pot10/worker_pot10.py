#!/usr/bin/env python3
"""
worker_pot10.py — GCP VM worker for pot-size-parametrized GTO analysis.

Supports 3-card boards (flop analysis) and 4-card boards (turn analysis).
Scenarios are loaded from scenarios_pot10.json, which carries per-scenario
pot_bb / effective_stack_bb / bet_sizes so different starting pot sizes
(e.g. 10 BB from 33% CBet) can be tested in a single run.

Extracts:
  Flop / Turn: ip_cbet_pct, ip_cbet_{size}, oop_fold_vs{size},
               cbet_overpair, cbet_top_pair, cbet_two_overcards, cbet_air

Usage (on GCP VM):
  python3 worker_pot10.py \
      --bucket BUCKET --vm-index 0 --n-vms 3 \
      --solver /opt/TexasSolver/build/console_solver \
      --solver-dir /opt/TexasSolver \
      --scenarios scenarios_pot10.json \
      [--threads 8] [--parallel 2]
"""
from __future__ import annotations
import argparse, json, os, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

RANK_VAL = {
    'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
    '9': 9,  '8': 8,  '7': 7,  '6': 6,  '5': 5,
    '4': 4,  '3': 3,  '2': 2,
}

# BTN open / BB defend, 100BB 6-max
BTN_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A9o,A8s,A8o,A7s,A7o,A6s,A6o,"
    "A5s,A5o,A4s,A4o,A3s,A3o,A2s,A2o,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K9o,K8s,K8o,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,"
    "JTs,JTo,J9s,J8s,J7s,J6s,"
    "T9s,T8s,T7s,T6s,"
    "98s,97s,96s,87s,86s,85s,76s,75s,65s,54s"
)
BB_RANGE = (
    "JJ,TT,99,88,77,66,55,44,33,22,"
    "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AQo,AJo,ATo,A9o,A8o,A7o,A6o,A5o,A4o,A3o,A2o,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "KQo,KJo,KTo,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,Q5s,Q4s,Q3s,Q2s,"
    "QJo,QTo,Q9o,Q8o,"
    "JTs,J9s,J8s,J7s,J6s,J5s,J4s,"
    "JTo,J9o,J8o,"
    "T9s,T8s,T7s,T6s,T5s,"
    "T9o,T8o,"
    "98s,97s,96s,95s,"
    "98o,"
    "87s,86s,85s,"
    "87o,"
    "76s,75s,74s,"
    "76o,"
    "65s,64s,"
    "65o,"
    "54s,53s,43s"
)

# ── Config templates ───────────────────────────────────────────────────────────

FLOP_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,flop,bet,{flop_bets}
set_bet_sizes ip,flop,allin
set_bet_sizes oop,flop,bet,{flop_bets}
set_bet_sizes oop,flop,allin
set_bet_sizes ip,turn,bet,33,75
set_bet_sizes ip,turn,allin
set_bet_sizes oop,turn,bet,33,75
set_bet_sizes oop,turn,allin
set_bet_sizes ip,river,bet,50
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,50
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy 3.0
set_max_iteration 300
start_solve
dump_result {dump_path}
"""

TURN_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,turn,bet,{turn_bets}
set_bet_sizes ip,turn,allin
set_bet_sizes oop,turn,bet,{turn_bets}
set_bet_sizes oop,turn,allin
set_bet_sizes ip,river,bet,50
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,50
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy 0.5
set_max_iteration 200
start_solve
dump_result {dump_path}
"""

GCS_PREFIX = 'pot10_study'

# ── GCS helpers ───────────────────────────────────────────────────────────────

def gcs_exists(bucket: str, path: str) -> bool:
    r = subprocess.run(['gsutil', '-q', 'stat', f'gs://{bucket}/{path}'], capture_output=True)
    return r.returncode == 0

def gcs_upload(local: str, bucket: str, path: str) -> None:
    subprocess.run(['gsutil', '-q', 'cp', local, f'gs://{bucket}/{path}'], check=True)


# ── Solver runner ──────────────────────────────────────────────────────────────

def run_solver(solver_bin: str, solver_dir: str, scenario: dict,
               dump_path: str, threads: int = 8, timeout: int = 1800) -> bool:
    board = scenario['board']
    pot   = scenario['pot_bb']
    stack = scenario['effective_stack_bb']
    n_cards = len(board.split(','))
    is_turn = n_cards == 4

    if is_turn:
        cfg = TURN_CONFIG.format(
            pot=pot, stack=stack, board=board,
            ip_range=BTN_RANGE, oop_range=BB_RANGE,
            turn_bets=scenario.get('turn_bet_sizes', '33,75'),
            threads=threads, dump_path=dump_path,
        )
    else:
        cfg = FLOP_CONFIG.format(
            pot=pot, stack=stack, board=board,
            ip_range=BTN_RANGE, oop_range=BB_RANGE,
            flop_bets=scenario.get('flop_bet_sizes', '33,75'),
            threads=threads, dump_path=dump_path,
        )

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
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
                proc.kill(); proc.wait()
                return False
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass


# ── Metric extraction ──────────────────────────────────────────────────────────

def _board_ranks(board_str: str) -> tuple[int, ...]:
    cards = board_str.split(',')
    return tuple(sorted([RANK_VAL[c[0].upper()] for c in cards], reverse=True))


def _bet_node(parent: dict, target_pct: float, pot: int) -> dict | None:
    expected = pot * target_pct / 100.0
    best, best_diff = None, float('inf')
    for key, node in parent.get('childrens', {}).items():
        if not key.startswith('BET'):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        diff = abs(amt - expected)
        if diff < max(3.0, expected * 0.25) and diff < best_diff:
            best_diff = diff
            best = node
    return best


def _avg_action(node: dict, prefix: str) -> float:
    strat = node.get('strategy', {})
    actions: list[str] = strat.get('actions', [])
    combos: dict = strat.get('strategy', {})
    idxs = [i for i, a in enumerate(actions) if a.startswith(prefix) or a == prefix]
    if not idxs or not combos:
        return 0.0
    return sum(
        sum(probs[i] for i in idxs if i < len(probs))
        for probs in combos.values()
    ) / len(combos)


def _categorize_combo(combo: str, ranks: tuple[int, ...]) -> str:
    r1 = RANK_VAL.get(combo[0].upper(), 0)
    r2 = RANK_VAL.get(combo[2].upper(), 0)
    r_hi = ranks[0]
    r_lo = ranks[-1]
    board_set = set(ranks)
    if r1 == r2:
        return 'overpair' if r1 > r_hi else ('underpair' if r1 < r_lo else 'mid_pair')
    hi, lo = max(r1, r2), min(r1, r2)
    if hi == r_hi or lo == r_hi:
        return 'top_pair'
    if hi > r_hi and lo > r_hi:
        return 'two_overcards'
    if hi not in board_set and lo not in board_set:
        return 'air'
    return 'other'


def _cbet_by_category(node: dict, cat: str, ranks: tuple[int, ...]) -> float | None:
    strat = node.get('strategy', {})
    actions: list[str] = strat.get('actions', [])
    combos: dict = strat.get('strategy', {})
    bet_idxs = [i for i, a in enumerate(actions) if a.startswith('BET') or a == 'ALLIN']
    matched: list[float] = []
    for combo, probs in combos.items():
        if len(combo) < 4:
            continue
        if _categorize_combo(combo, ranks) == cat:
            matched.append(sum(probs[i] for i in bet_idxs if i < len(probs)))
    return sum(matched) / len(matched) if matched else None


def extract_metrics(raw: dict, scenario: dict) -> dict:
    """Extract IP CBet + OOP fold metrics from a flop or turn solve."""
    board_str = scenario['board']
    ranks = _board_ranks(board_str)
    pot = scenario['pot_bb']
    n_cards = len(board_str.split(','))
    street_label = 'turn' if n_cards == 4 else 'flop'
    bet_sizes_str = scenario.get(f'{street_label}_bet_sizes', '33,75')
    bet_sizes = [int(s.strip()) for s in bet_sizes_str.split(',') if s.strip().isdigit()]

    # OOP acts first; IP CBet after OOP check
    check_node = raw.get('childrens', {}).get('CHECK')
    if check_node is None:
        return {'error': f'no CHECK node at {street_label} root'}

    ip_cbet = (_avg_action(check_node, 'BET') + _avg_action(check_node, 'ALLIN')) * 100.0
    metrics: dict[str, Any] = {'ip_cbet_pct': round(ip_cbet, 2)}

    # CBet rate by hand category
    for cat in ['overpair', 'top_pair', 'two_overcards', 'air']:
        p = _cbet_by_category(check_node, cat, ranks)
        if p is not None:
            metrics[f'cbet_{cat}'] = round(p * 100.0, 2)

    # IP CBet size distribution
    strat = check_node.get('strategy', {})
    actions: list[str] = strat.get('actions', [])
    combos_strat: dict = strat.get('strategy', {})
    for pct in bet_sizes:
        expected = pot * pct / 100.0
        best_idx, best_diff = -1, float('inf')
        for i, a in enumerate(actions):
            if not a.startswith('BET'):
                continue
            try:
                amt = float(a.split()[1])
            except (IndexError, ValueError):
                continue
            d = abs(amt - expected)
            if d < best_diff:
                best_diff = d
                best_idx = i
        if best_idx >= 0 and combos_strat and best_diff < max(3.0, expected * 0.25):
            p_val = sum(
                probs[best_idx] for probs in combos_strat.values()
                if best_idx < len(probs)
            ) / len(combos_strat)
            metrics[f'ip_cbet_{pct}'] = round(p_val * 100.0, 2)

    # OOP fold rate vs each IP bet size
    for pct in bet_sizes:
        bn = _bet_node(check_node, pct, pot)
        if bn is not None:
            fold_p = _avg_action(bn, 'FOLD')
            metrics[f'oop_fold_vs{pct}'] = round(fold_p * 100.0, 2)

    return metrics


# ── Per-scenario processor ─────────────────────────────────────────────────────

def process_scenario(scenario: dict, solver_bin: str, solver_dir: str,
                     bucket: str, threads: int, tmpdir: Path) -> dict:
    sid = scenario['id']
    gcs_path = f'{GCS_PREFIX}/results/{sid}.json'

    if gcs_exists(bucket, gcs_path):
        print(f'[SKIP] {sid}', flush=True)
        return {'scenario_id': sid, 'cached': True}

    dump_file = str(tmpdir / f'{sid}.json')
    t0 = time.time()
    ok = run_solver(solver_bin, solver_dir, scenario, dump_file, threads=threads)
    elapsed = time.time() - t0

    if not ok:
        print(f'[FAIL] {sid} ({elapsed:.0f}s)', flush=True)
        return {'scenario_id': sid, 'error': 'solver failed', 'elapsed_s': elapsed}

    raw: Any = json.loads(Path(dump_file).read_text())
    Path(dump_file).unlink(missing_ok=True)

    metrics = extract_metrics(raw, scenario)

    result = {**scenario, **metrics, 'elapsed_s': round(elapsed, 1)}

    local_result = str(tmpdir / f'result_{sid}.json')
    Path(local_result).write_text(json.dumps(result, ensure_ascii=False))
    gcs_upload(local_result, bucket, gcs_path)
    Path(local_result).unlink(missing_ok=True)

    cbet_val = metrics.get('ip_cbet_pct', '?')
    t2 = metrics.get('cbet_two_overcards', '-')
    t3 = metrics.get('cbet_air', '-')
    n_cards = len(scenario['board'].split(','))
    street = 'TRN' if n_cards == 4 else 'FLP'
    tag = scenario.get('tag', '')
    print(f'[{street}] {sid:32s}  tag={tag}  CBet={cbet_val}%  T2={t2}%  air={t3}%  ({elapsed:.0f}s)',
          flush=True)
    return {'scenario_id': sid, 'ok': True}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bucket',     required=True)
    ap.add_argument('--vm-index',   type=int, required=True)
    ap.add_argument('--n-vms',      type=int, required=True)
    ap.add_argument('--solver',     required=True)
    ap.add_argument('--solver-dir', required=True)
    ap.add_argument('--scenarios',  default='scenarios_pot10.json')
    ap.add_argument('--threads',    type=int, default=8)
    ap.add_argument('--parallel',   type=int, default=2)
    args = ap.parse_args()

    scenarios: list[dict] = json.loads(Path(args.scenarios).read_text())['scenarios']
    assigned = [s for i, s in enumerate(scenarios) if i % args.n_vms == args.vm_index]

    flop_n = sum(1 for s in assigned if len(s['board'].split(',')) == 3)
    turn_n = sum(1 for s in assigned if len(s['board'].split(',')) == 4)
    print(f'VM {args.vm_index}/{args.n_vms}: {len(assigned)}/{len(scenarios)} scenarios assigned '
          f'({flop_n} flop, {turn_n} turn)')

    tmpdir = Path(tempfile.mkdtemp(prefix='solver_p10_'))
    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futs = {
            pool.submit(process_scenario, s, args.solver, args.solver_dir,
                        args.bucket, args.threads, tmpdir): s['id']
            for s in assigned
        }
        for fut in as_completed(futs):
            sid = futs[fut]
            try:
                results.append(fut.result())
            except Exception as e:
                print(f'[EXC] {sid}: {e}')
                results.append({'scenario_id': sid, 'error': str(e)})

    ok_count  = sum(1 for r in results if r.get('ok') or r.get('cached'))
    err_count = len(results) - ok_count
    print(f'\nDone: {ok_count} OK, {err_count} errors')

    marker = str(tmpdir / f'done_vm{args.vm_index}.txt')
    Path(marker).write_text(f'ok={ok_count} err={err_count}')
    gcs_upload(marker, args.bucket, f'{GCS_PREFIX}/done/vm{args.vm_index}.txt')


if __name__ == '__main__':
    main()
