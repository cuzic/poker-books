#!/usr/bin/env python3
"""
worker_cr_river.py — GCP VM worker for check-raise + river GTO analysis.

Flop boards (n_board=3): extracts both IP CBet AND OOP check-raise response.
River boards (n_board=5): extracts river IP value/bluff + OOP defense.

Usage (on GCP VM):
  python3 worker_cr_river.py \
      --bucket BUCKET --vm-index 0 --n-vms 1 \
      --solver /opt/TexasSolver/build/console_solver \
      --solver-dir /opt/TexasSolver \
      --scenarios scenarios_cr_river.json \
      [--threads 8] [--parallel 2]
"""
from __future__ import annotations
import argparse, json, os, subprocess, tempfile, time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

RANK_VAL = {
    'A': 14, 'K': 13, 'Q': 12, 'J': 11, 'T': 10,
    '9': 9,  '8': 8,  '7': 7,  '6': 6,  '5': 5,
    '4': 4,  '3': 3,  '2': 2,
}
SUIT_VAL = {'s': 0, 'h': 1, 'd': 2, 'c': 3}

# BTN open / BB defend, 100BB 6-max (same as worker_pot10)
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

# ── Config templates ────────────────────────────────────────────────────────

FLOP_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,flop,bet,{flop_bets}
set_bet_sizes ip,flop,allin
set_bet_sizes oop,flop,bet,{flop_bets}
set_bet_sizes oop,flop,raise,{flop_bets}
set_bet_sizes oop,flop,allin
set_bet_sizes ip,turn,bet,33,75
set_bet_sizes ip,turn,allin
set_bet_sizes oop,turn,bet,33,75
set_bet_sizes oop,turn,allin
set_bet_sizes ip,river,bet,50,100
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,50,100
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy 1.5
set_max_iteration 200
start_solve
dump_result {dump_path}
"""

RIVER_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,river,bet,{river_bets}
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,{river_bets}
set_bet_sizes oop,river,raise,{river_bets}
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy 0.5
set_max_iteration 200
start_solve
dump_result {dump_path}
"""

GCS_PREFIX = 'cr_river_study'


# ── GCS helpers ────────────────────────────────────────────────────────────

def gcs_exists(bucket: str, path: str) -> bool:
    r = subprocess.run(['gsutil', '-q', 'stat', f'gs://{bucket}/{path}'], capture_output=True)
    return r.returncode == 0

def gcs_upload(local: str, bucket: str, path: str) -> None:
    subprocess.run(['gsutil', '-q', 'cp', local, f'gs://{bucket}/{path}'], check=True)


# ── Solver runner ──────────────────────────────────────────────────────────

def run_solver(solver_bin: str, solver_dir: str, scenario: dict,
               dump_path: str, threads: int = 8, timeout: int = 900) -> bool:
    board = scenario['board']
    pot   = scenario['pot_bb']
    stack = scenario['effective_stack_bb']
    n_cards = len(board.split(','))

    if n_cards == 5:  # river
        cfg = RIVER_CONFIG.format(
            pot=pot, stack=stack, board=board,
            ip_range=BTN_RANGE, oop_range=BB_RANGE,
            river_bets=scenario.get('river_bet_sizes', '33,75'),
            threads=threads, dump_path=dump_path,
        )
    else:  # flop
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


# ── Hand categorization ────────────────────────────────────────────────────

def _parse_board_cards(board_str: str) -> list[tuple[int, int]]:
    cards = board_str.split(',')
    return [(RANK_VAL[c[0].upper()], SUIT_VAL[c[1].lower()]) for c in cards]

def _parse_hand_cards(combo: str) -> tuple[tuple[int,int], tuple[int,int]] | None:
    if len(combo) < 4:
        return None
    try:
        c1 = (RANK_VAL[combo[0].upper()], SUIT_VAL[combo[1].lower()])
        c2 = (RANK_VAL[combo[2].upper()], SUIT_VAL[combo[3].lower()])
        return (c1, c2)
    except KeyError:
        return None

def _has_flush_draw(hand: tuple, board: list) -> bool:
    """True if exactly 4 cards of same suit (flush draw, not already made)."""
    all_suits = [c[1] for c in list(hand) + board]
    suit_counts = Counter(all_suits)
    return any(v == 4 for v in suit_counts.values())

def _has_oesd(hand: tuple, board: list) -> bool:
    """Open-ended straight draw: 4 consecutive ranks with outs on both ends."""
    all_ranks = sorted({c[0] for c in list(hand) + board})
    for i in range(len(all_ranks) - 3):
        window = all_ranks[i:i+4]
        if window[-1] - window[0] == 3:
            # Check it's truly open-ended (not wheel-end or broadway-end only)
            low, high = window[0], window[-1]
            if low > 2 and high < 14:
                return True
    return False

def _has_gutshot(hand: tuple, board: list) -> bool:
    """Gutshot straight draw: 4-card straight with one gap."""
    all_ranks = sorted({c[0] for c in list(hand) + board})
    for i in range(len(all_ranks) - 2):
        for j in range(i+1, len(all_ranks)):
            for k in range(j+1, len(all_ranks)):
                for l in range(k+1, len(all_ranks)):
                    window = [all_ranks[i], all_ranks[j], all_ranks[k], all_ranks[l]]
                    span = window[-1] - window[0]
                    if span == 4:  # 5 - 1 = 4 span for 4 consecutive
                        return True
                    if span == 3:  # already OESD
                        pass
    return False

def categorize_hand(combo: str, board_str: str) -> str:
    """Categorize hand type for CR/river analysis."""
    hand = _parse_hand_cards(combo)
    if hand is None:
        return 'unknown'
    board = _parse_board_cards(board_str)

    h_ranks = sorted([c[0] for c in hand], reverse=True)
    board_ranks_sorted = sorted([c[0] for c in board], reverse=True)
    board_rank_set = {c[0] for c in board}
    hand_rank_set = {c[0] for c in hand}

    # Pocket pair
    is_pp = h_ranks[0] == h_ranks[1]

    # Set or trips
    if is_pp and h_ranks[0] in board_rank_set:
        return 'set'

    # Two pair (both hand cards pair with board, or hand pair + board pair)
    board_rank_counts = Counter(c[0] for c in board)
    pairs_to_board = sum(1 for r in hand_rank_set if r in board_rank_set)
    if pairs_to_board == 2:
        return 'two_pair'
    if pairs_to_board == 1 and any(v >= 2 for v in board_rank_counts.values()):
        return 'two_pair'

    # Overpair
    if is_pp and h_ranks[0] > board_ranks_sorted[0]:
        return 'overpair'

    # Top pair
    if board_ranks_sorted[0] in hand_rank_set:
        return 'top_pair'

    # Middle/bottom pair
    for r in board_ranks_sorted[1:]:
        if r in hand_rank_set:
            return 'pair'

    # Draw classifications (no made hand)
    has_fd = _has_flush_draw(hand, board)
    has_oesd = _has_oesd(hand, board)

    if has_fd and has_oesd:
        return 'combo_draw'
    if has_fd:
        return 'flush_draw'
    if has_oesd:
        return 'oesd'
    if _has_gutshot(hand, board):
        return 'gutshot'

    # Overcards
    overcards = sum(1 for r in h_ranks if r > board_ranks_sorted[0])
    if overcards == 2:
        return 'two_overcards'
    if overcards == 1:
        return 'one_overcard'

    return 'air'


# ── Generic tree helpers ───────────────────────────────────────────────────

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


def _bet_node_by_pct(parent: dict, target_pct: float, pot: float) -> dict | None:
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
        if diff < max(3.0, expected * 0.30) and diff < best_diff:
            best_diff = diff
            best = node
    return best


def _rate_by_category(node: dict, cat: str, board_str: str,
                      action_prefixes: list[str]) -> float | None:
    """Average frequency of actions matching prefixes, for combos of given category."""
    strat = node.get('strategy', {})
    actions: list[str] = strat.get('actions', [])
    combos: dict = strat.get('strategy', {})
    idxs = [i for i, a in enumerate(actions)
            if any(a.startswith(p) or a == p for p in action_prefixes)]
    matched = []
    for combo, probs in combos.items():
        if len(combo) < 4:
            continue
        if categorize_hand(combo, board_str) == cat:
            freq = sum(probs[i] for i in idxs if i < len(probs))
            matched.append(freq)
    return (sum(matched) / len(matched)) if matched else None


# ── Flop extraction (IP CBet + OOP check-raise) ───────────────────────────

def extract_flop_metrics(raw: dict, scenario: dict) -> dict:
    board_str = scenario['board']
    pot = scenario['pot_bb']
    bet_sizes = [int(s.strip()) for s in scenario.get('flop_bet_sizes', '33,75').split(',') if s.strip().isdigit()]

    # Root: OOP acts first
    check_node = raw.get('childrens', {}).get('CHECK')
    if check_node is None:
        return {'error': 'no CHECK at flop root'}

    metrics: dict[str, Any] = {}

    # IP CBet overall
    ip_cbet = (_avg_action(check_node, 'BET') + _avg_action(check_node, 'ALLIN')) * 100.0
    metrics['ip_cbet_pct'] = round(ip_cbet, 2)

    # IP CBet by category
    for cat in ['overpair', 'top_pair', 'two_overcards', 'flush_draw', 'air']:
        p = _rate_by_category(check_node, cat, board_str, ['BET', 'ALLIN'])
        if p is not None:
            metrics[f'ip_cbet_{cat}'] = round(p * 100.0, 2)

    # Per bet size: OOP response (fold/call/cr)
    for pct in bet_sizes:
        bet_node = _bet_node_by_pct(check_node, pct, pot)
        if bet_node is None:
            continue

        fold_pct  = _avg_action(bet_node, 'FOLD') * 100.0
        call_pct  = _avg_action(bet_node, 'CALL') * 100.0
        raise_pct = (_avg_action(bet_node, 'RAISE') + _avg_action(bet_node, 'ALLIN')) * 100.0

        metrics[f'oop_fold_vs{pct}']  = round(fold_pct, 2)
        metrics[f'oop_call_vs{pct}']  = round(call_pct, 2)
        metrics[f'oop_cr_vs{pct}']    = round(raise_pct, 2)

        # CR by hand category
        cr_cats = ['set', 'two_pair', 'overpair', 'top_pair', 'pair',
                   'combo_draw', 'flush_draw', 'oesd', 'two_overcards', 'air']
        for cat in cr_cats:
            p = _rate_by_category(bet_node, cat, board_str, ['RAISE', 'ALLIN'])
            if p is not None:
                metrics[f'oop_cr_{cat}_vs{pct}'] = round(p * 100.0, 2)

    return metrics


# ── River extraction (IP value/bluff + OOP defense) ───────────────────────

def extract_river_metrics(raw: dict, scenario: dict) -> dict:
    board_str = scenario['board']
    pot = scenario['pot_bb']
    bet_sizes = [int(s.strip()) for s in scenario.get('river_bet_sizes', '33,75').split(',') if s.strip().isdigit()]

    # River root: OOP acts first (check or donk)
    # Normal line: OOP checks → IP bets
    check_node = raw.get('childrens', {}).get('CHECK')
    if check_node is None:
        return {'error': 'no CHECK at river root'}

    metrics: dict[str, Any] = {}

    # IP overall bet frequency on river
    ip_bet = (_avg_action(check_node, 'BET') + _avg_action(check_node, 'ALLIN')) * 100.0
    metrics['ip_bet_pct'] = round(ip_bet, 2)

    # IP check-back frequency
    ip_check = _avg_action(check_node, 'CHECK') * 100.0
    metrics['ip_check_pct'] = round(ip_check, 2)

    # Per bet size: value/bluff breakdown + OOP defense
    river_full_board = board_str  # 5-card board
    for pct in bet_sizes:
        bet_node = _bet_node_by_pct(check_node, pct, pot)
        if bet_node is None:
            continue

        fold_pct = _avg_action(bet_node, 'FOLD') * 100.0
        call_pct = _avg_action(bet_node, 'CALL') * 100.0
        metrics[f'oop_fold_vs{pct}'] = round(fold_pct, 2)
        metrics[f'oop_call_vs{pct}'] = round(call_pct, 2)

        # IP bet breakdown by hand strength
        value_cats = ['set', 'two_pair', 'overpair', 'top_pair']
        bluff_cats = ['flush_draw', 'oesd', 'two_overcards', 'air']

        value_freqs = []
        for cat in value_cats:
            p = _rate_by_category(check_node, cat, river_full_board, ['BET', 'ALLIN'])
            if p is not None:
                metrics[f'ip_bet_{cat}_vs{pct}'] = round(p * 100.0, 2)
                value_freqs.append(p)

        bluff_freqs = []
        for cat in bluff_cats:
            p = _rate_by_category(check_node, cat, river_full_board, ['BET', 'ALLIN'])
            if p is not None:
                metrics[f'ip_bet_{cat}_vs{pct}'] = round(p * 100.0, 2)
                bluff_freqs.append(p)

    # OOP donk bet (if it exists)
    oop_donk = _avg_action(raw, 'BET') * 100.0
    if oop_donk > 0.5:
        metrics['oop_donk_pct'] = round(oop_donk, 2)

    return metrics


# ── Per-scenario processor ─────────────────────────────────────────────────

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

    n_cards = len(scenario['board'].split(','))
    if n_cards == 5:
        metrics = extract_river_metrics(raw, scenario)
        street = 'RVR'
    else:
        metrics = extract_flop_metrics(raw, scenario)
        street = 'FLP'

    result = {**scenario, **metrics, 'elapsed_s': round(elapsed, 1)}

    local_result = str(tmpdir / f'result_{sid}.json')
    Path(local_result).write_text(json.dumps(result, ensure_ascii=False))
    gcs_upload(local_result, bucket, gcs_path)
    Path(local_result).unlink(missing_ok=True)

    cbet = metrics.get('ip_cbet_pct', metrics.get('ip_bet_pct', '?'))
    cr33 = metrics.get('oop_cr_vs33', '-')
    cr75 = metrics.get('oop_cr_vs75', '-')
    tag  = scenario.get('tag', '')
    print(f'[{street}] {sid:32s}  tag={tag}  CBet/Bet={cbet}%  CR33={cr33}%  CR75={cr75}%  ({elapsed:.0f}s)',
          flush=True)
    return {'scenario_id': sid, 'ok': True}


# ── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--bucket',     required=True)
    ap.add_argument('--vm-index',   type=int, required=True)
    ap.add_argument('--n-vms',      type=int, required=True)
    ap.add_argument('--solver',     required=True)
    ap.add_argument('--solver-dir', required=True)
    ap.add_argument('--scenarios',  default='scenarios_cr_river.json')
    ap.add_argument('--threads',    type=int, default=8)
    ap.add_argument('--parallel',   type=int, default=2)
    args = ap.parse_args()

    scenarios: list[dict] = json.loads(Path(args.scenarios).read_text())['scenarios']
    assigned = [s for i, s in enumerate(scenarios) if i % args.n_vms == args.vm_index]

    n_flop  = sum(1 for s in assigned if s['n_board'] == 3)
    n_river = sum(1 for s in assigned if s['n_board'] == 5)
    print(f'VM {args.vm_index}/{args.n_vms}: {len(assigned)}/{len(scenarios)} scenarios '
          f'({n_flop} flop-CR, {n_river} river)')

    tmpdir = Path(tempfile.mkdtemp(prefix='solver_cr_'))
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
