#!/usr/bin/env python3
"""
worker_turn_river.py — GCP VM worker for turn+river GTO analysis.

Supports 4-card boards (turn analysis) and 5-card boards (river analysis).
Extracts:
  Turn: ip_cbet_pct, ip_cbet_33/50/75, oop_fold_vs33/50/75,
        cbet_overpair, cbet_top_pair, cbet_two_overcards, cbet_air
  River: ip_bet_pct, ip_bet_50/75/100, oop_fold_vs50/75/100,
         bet_made_hand, bet_air (bluff rate)

Usage (on GCP VM):
  python3 worker_turn_river.py \
      --bucket BUCKET --vm-index 0 --n-vms 5 \
      --solver /opt/TexasSolver/build/console_solver \
      --solver-dir /opt/TexasSolver \
      --boards boards_turn.json [--boards-river boards_river.json] \
      [--threads 8] [--parallel 2]
"""
from __future__ import annotations
import argparse, json, os, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

# ── Game parameters ───────────────────────────────────────────────────────────
TURN_POT   = 10   # after flop 33% CBet call
TURN_STACK = 92
RIVER_POT  = 20   # after turn 50% CBet call
RIVER_STACK = 80

ACCURACY_TURN  = 0.5
ACCURACY_RIVER = 0.5
MAX_ITER_TURN  = 300
MAX_ITER_RIVER = 200

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}

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

TURN_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip}
set_range_oop {oop}
set_bet_sizes oop,turn,bet,50,100
set_bet_sizes oop,turn,allin
set_bet_sizes ip,turn,bet,33,50,75
set_bet_sizes ip,turn,allin
set_bet_sizes oop,river,bet,50,100
set_bet_sizes oop,river,allin
set_bet_sizes ip,river,bet,50,100
set_bet_sizes ip,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy {accuracy}
set_max_iteration {max_iter}
set_print_interval 100
set_dump_rounds 1
start_solve
dump_result {dump}
"""

RIVER_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip}
set_range_oop {oop}
set_bet_sizes oop,river,bet,50,100
set_bet_sizes oop,river,allin
set_bet_sizes ip,river,bet,50,75,100
set_bet_sizes ip,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy {accuracy}
set_max_iteration {max_iter}
set_print_interval 100
set_dump_rounds 1
start_solve
dump_result {dump}
"""

# ── GCS helpers ───────────────────────────────────────────────────────────────

def gcs_exists(bucket: str, path: str) -> bool:
    r = subprocess.run(['gsutil', '-q', 'stat', f'gs://{bucket}/{path}'], capture_output=True)
    return r.returncode == 0

def gcs_upload(local: str, bucket: str, path: str) -> None:
    subprocess.run(['gsutil', '-q', 'cp', local, f'gs://{bucket}/{path}'], check=True)

def gcs_download(bucket: str, path: str, local: str) -> bool:
    r = subprocess.run(['gsutil', '-q', 'cp', f'gs://{bucket}/{path}', local], capture_output=True)
    return r.returncode == 0


# ── Solver runner ──────────────────────────────────────────────────────────────

def run_solver(solver_bin: str, solver_dir: str, board: str, dump_path: str,
               is_river: bool, threads: int = 8, timeout: int = 600) -> bool:
    pot   = RIVER_POT   if is_river else TURN_POT
    stack = RIVER_STACK if is_river else TURN_STACK
    acc   = ACCURACY_RIVER if is_river else ACCURACY_TURN
    mi    = MAX_ITER_RIVER if is_river else MAX_ITER_TURN
    tmpl  = RIVER_CONFIG if is_river else TURN_CONFIG
    cfg = tmpl.format(
        pot=pot, stack=stack, board=board,
        ip=IP_RANGE, oop=OOP_RANGE,
        threads=threads, accuracy=acc, max_iter=mi, dump=dump_path,
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
        try: os.unlink(cfg_path)
        except OSError: pass


# ── Metric extraction ──────────────────────────────────────────────────────────

def _board_ranks(board_str: str, n_cards: int = 4) -> tuple[int,...]:
    cards = board_str.split(',')[:n_cards]
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
    return sum(sum(probs[i] for i in idxs if i < len(probs))
               for probs in combos.values()) / len(combos)


def _categorize_combo(combo: str, ranks: tuple[int,...]) -> str:
    r1 = RANK_VAL.get(combo[0].upper(), 0)
    r2 = RANK_VAL.get(combo[2].upper(), 0)
    r_hi = ranks[0]
    r_lo = ranks[-1]
    board_ranks_set = set(ranks)
    if r1 == r2:
        return 'overpair' if r1 > r_hi else ('underpair' if r1 < r_lo else 'mid_pair')
    hi, lo = max(r1, r2), min(r1, r2)
    if hi == r_hi or lo == r_hi:
        return 'top_pair'
    if hi > r_hi and lo > r_hi:
        return 'two_overcards'
    if hi not in board_ranks_set and lo not in board_ranks_set:
        return 'air'
    return 'other'


def _cbet_by_category(node: dict, cat: str, ranks: tuple[int,...]) -> float | None:
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
    return sum(matched)/len(matched) if matched else None


def extract_turn_metrics(raw: dict, board_str: str) -> dict:
    """Extract turn CBet + defense metrics from a 4-card board solve."""
    ranks = _board_ranks(board_str, 4)
    pot = TURN_POT
    # Turn root: OOP acts first → CHECK → IP bets/checks
    check_node = raw.get('childrens', {}).get('CHECK')
    if check_node is None:
        return {'error': 'no CHECK node at turn root'}

    # IP turn CBet rate
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
    for pct in [33, 50, 75]:
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
        if best_idx >= 0 and combos_strat and best_diff < 3.0:
            p_val = sum(probs[best_idx] for probs in combos_strat.values()
                        if best_idx < len(probs)) / len(combos_strat)
            metrics[f'ip_cbet_{pct}'] = round(p_val * 100.0, 2)

    # OOP fold rate vs each IP bet size
    for pct in [33, 50, 75]:
        bn = _bet_node(check_node, pct, pot)
        if bn is not None:
            fold_p = _avg_action(bn, 'FOLD')
            metrics[f'oop_fold_vs{pct}'] = round(fold_p * 100.0, 2)

    return metrics


def extract_river_metrics(raw: dict, board_str: str) -> dict:
    """Extract river first-bet + defense metrics from a 5-card board solve."""
    ranks = _board_ranks(board_str, 5)
    pot = RIVER_POT
    # River root: OOP acts first → CHECK → IP bets/checks behind
    check_node = raw.get('childrens', {}).get('CHECK')
    if check_node is None:
        return {'error': 'no CHECK node at river root'}

    ip_bet = (_avg_action(check_node, 'BET') + _avg_action(check_node, 'ALLIN')) * 100.0
    metrics: dict[str, Any] = {'ip_bet_pct': round(ip_bet, 2)}

    # Bet rate by hand category (value/bluff)
    for cat in ['overpair', 'top_pair', 'two_overcards', 'air']:
        p = _cbet_by_category(check_node, cat, ranks)
        if p is not None:
            metrics[f'bet_{cat}'] = round(p * 100.0, 2)

    # IP bet size distribution
    strat = check_node.get('strategy', {})
    actions: list[str] = strat.get('actions', [])
    combos_strat: dict = strat.get('strategy', {})
    for pct in [50, 75, 100]:
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
            p_val = sum(probs[best_idx] for probs in combos_strat.values()
                        if best_idx < len(probs)) / len(combos_strat)
            metrics[f'ip_bet_{pct}'] = round(p_val * 100.0, 2)

    # OOP fold rate vs each IP bet size
    for pct in [50, 75, 100]:
        bn = _bet_node(check_node, pct, pot)
        if bn is not None:
            fold_p = _avg_action(bn, 'FOLD')
            metrics[f'oop_fold_vs{pct}'] = round(fold_p * 100.0, 2)

    return metrics


# ── Per-board processor ────────────────────────────────────────────────────────

def process_board(board: dict, solver_bin: str, solver_dir: str,
                  bucket: str, threads: int, tmpdir: Path) -> dict:
    scenario_id = board['scenario_id']
    is_river = board.get('street') == 'river'
    gcs_prefix = 'turn_river_study'
    gcs_path = f'{gcs_prefix}/results/{scenario_id}.json'

    if gcs_exists(bucket, gcs_path):
        print(f'[SKIP] {scenario_id}', flush=True)
        return {'scenario_id': scenario_id, 'cached': True}

    board_str = board['board']
    dump_file = str(tmpdir / f'{scenario_id}.json')
    t0 = time.time()
    ok = run_solver(solver_bin, solver_dir, board_str, dump_file,
                    is_river=is_river, threads=threads)
    elapsed = time.time() - t0

    if not ok:
        print(f'[FAIL] {scenario_id} ({elapsed:.0f}s)', flush=True)
        return {'scenario_id': scenario_id, 'error': 'solver failed', 'elapsed_s': elapsed}

    raw: Any = json.loads(Path(dump_file).read_text())
    Path(dump_file).unlink(missing_ok=True)

    if is_river:
        metrics = extract_river_metrics(raw, board_str)
    else:
        metrics = extract_turn_metrics(raw, board_str)

    result = {**board, **metrics, 'elapsed_s': round(elapsed, 1)}

    local_result = str(tmpdir / f'result_{scenario_id}.json')
    Path(local_result).write_text(json.dumps(result, ensure_ascii=False))
    gcs_upload(local_result, bucket, gcs_path)
    Path(local_result).unlink(missing_ok=True)

    cbet_key = 'ip_bet_pct' if is_river else 'ip_cbet_pct'
    cbet_val = metrics.get(cbet_key, '?')
    t2 = metrics.get('cbet_two_overcards' if not is_river else 'bet_two_overcards', '-')
    t3 = metrics.get('cbet_air' if not is_river else 'bet_air', '-')
    street = 'RIV' if is_river else 'TRN'
    print(f'[{street}] {scenario_id:28s}  CBet={cbet_val}%  T2={t2}%  T3={t3}%  ({elapsed:.0f}s)', flush=True)
    return {'scenario_id': scenario_id, 'ok': True}


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bucket',      required=True)
    ap.add_argument('--vm-index',    type=int, required=True)
    ap.add_argument('--n-vms',       type=int, required=True)
    ap.add_argument('--solver',      required=True)
    ap.add_argument('--solver-dir',  required=True)
    ap.add_argument('--boards',      default='boards_turn.json',
                    help='Turn scenarios JSON')
    ap.add_argument('--boards-river', default='boards_river.json',
                    help='River scenarios JSON (empty = skip river)')
    ap.add_argument('--threads',     type=int, default=8)
    ap.add_argument('--parallel',    type=int, default=2)
    args = ap.parse_args()

    all_boards: list[dict] = []
    for boards_file in [args.boards, args.boards_river]:
        p = Path(boards_file)
        if p.exists():
            all_boards.extend(json.loads(p.read_text()))
        else:
            print(f'[WARN] {boards_file} not found — skipping')

    assigned = [b for i, b in enumerate(all_boards) if i % args.n_vms == args.vm_index]
    print(f'VM {args.vm_index}/{args.n_vms}: {len(assigned)}/{len(all_boards)} boards assigned '
          f'({sum(1 for b in assigned if b.get("street")=="turn")} turn, '
          f'{sum(1 for b in assigned if b.get("street")=="river")} river)')

    tmpdir = Path(tempfile.mkdtemp(prefix='solver_tr_'))
    results: list[dict] = []

    with ThreadPoolExecutor(max_workers=args.parallel) as pool:
        futs = {pool.submit(process_board, b, args.solver, args.solver_dir,
                            args.bucket, args.threads, tmpdir): b['scenario_id']
                for b in assigned}
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as e:
                sid = futs[fut]
                print(f'[EXC] {sid}: {e}')
                results.append({'scenario_id': sid, 'error': str(e)})

    ok_count  = sum(1 for r in results if r.get('ok') or r.get('cached'))
    err_count = len(results) - ok_count
    print(f'\nDone: {ok_count} OK, {err_count} errors')

    marker = str(tmpdir / f'done_vm{args.vm_index}.txt')
    Path(marker).write_text(f'ok={ok_count} err={err_count}')
    gcs_upload(marker, args.bucket, f'turn_river_study/done/vm{args.vm_index}.txt')


if __name__ == '__main__':
    main()
