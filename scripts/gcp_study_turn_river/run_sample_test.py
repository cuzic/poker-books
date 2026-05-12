#!/usr/bin/env python3
"""
run_sample_test.py — Quick local validation run.

Runs 10 representative scenarios to verify the pipeline is correct:
  - 2 × mono (blank + overcard)
  - 2 × rainbow_connected (blank + pair)
  - 2 × paired_high (blank + overcard)
  - 2 × rainbow (blank + connector)
  - 1 × river (mono)
  - 1 × river (rainbow)

Uses lower accuracy (10.0) and fewer iterations (30) for speed (~5-8 min total).
"""
from __future__ import annotations
import json, subprocess, tempfile, time, os
from pathlib import Path

SOLVER_BIN = '/home/cuzic/TexasSolver/build/console_solver'
SOLVER_DIR = '/home/cuzic/TexasSolver'
OUT_DIR    = Path(__file__).parent
THREADS    = 4
ACCURACY   = 10.0
MAX_ITER   = 30

SAMPLE_BOARDS = [
    # id, board, street
    ('mono_blank',      'Kc,9c,5c,2d',   'turn'),
    ('mono_overcard',   'Kc,9c,5c,Ah',   'turn'),
    ('rc_blank',        'Kc,Qd,Jh,2s',   'turn'),
    ('rc_pair',         'Kc,Qd,Jh,Kd',   'turn'),
    ('ph_blank',        'Kc,Kd,7s,2h',   'turn'),
    ('ph_overcard',     'Tc,Td,6s,Ah',   'turn'),
    ('rbow_blank',      'Tc,7d,2s,3h',   'turn'),
    ('rbow_conn',       'Tc,7d,2s,6h',   'turn'),
    ('river_mono',      'Kc,9c,5c,2d,8d', 'river'),
    ('river_rbow',      'Tc,7d,2s,3h,Qc', 'river'),
]

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}
IP_RANGE = ('AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,'
            'AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,'
            'KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,'
            'QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,JTs,JTo,J9s,J8s,J7s,'
            'T9s,T8s,T7s,98s,97s,87s,86s,76s,75s,65s,54s')
OOP_RANGE = ('JJ,TT,99,88,77,66,55,44,33,22,'
             'AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,AQo,AJo,ATo,'
             'KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,KQo,KJo,KTo,'
             'QJs,QTs,Q9s,Q8s,Q7s,Q6s,QJo,QTo,JTs,J9s,J8s,JTo,'
             'T9s,T8s,T7s,T9o,98s,97s,96s,98o,87s,86s,87o,76s,75s,76o,65s,65o,54s,53s,43s')

TURN_CFG = """set_pot 10
set_effective_stack 92
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
set_accuracy {acc}
set_max_iteration {mi}
set_print_interval {mi}
set_dump_rounds 1
start_solve
dump_result {dump}
"""

RIVER_CFG = """set_pot 20
set_effective_stack 80
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
set_accuracy {acc}
set_max_iteration {mi}
set_print_interval {mi}
set_dump_rounds 1
start_solve
dump_result {dump}
"""


def run_one(board_id: str, board: str, street: str, tmpdir: Path) -> dict:
    dump_file = str(tmpdir / f'{board_id}.json')
    cfg_tmpl = RIVER_CFG if street == 'river' else TURN_CFG
    cfg = cfg_tmpl.format(board=board, ip=IP_RANGE, oop=OOP_RANGE,
                          threads=THREADS, acc=ACCURACY, mi=MAX_ITER, dump=dump_file)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(cfg)
        cfg_path = f.name

    t0 = time.time()
    try:
        with open(cfg_path) as fin:
            proc = subprocess.Popen([SOLVER_BIN], stdin=fin,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    cwd=SOLVER_DIR)
            rc = proc.wait(timeout=180)
    finally:
        os.unlink(cfg_path)

    elapsed = time.time() - t0
    if rc != 0 or not Path(dump_file).exists():
        return {'board_id': board_id, 'error': f'solver failed rc={rc}', 'elapsed_s': elapsed}

    raw = json.loads(Path(dump_file).read_text())
    Path(dump_file).unlink(missing_ok=True)

    # import extraction from worker
    import sys; sys.path.insert(0, str(OUT_DIR))
    if street == 'river':
        from worker_turn_river import extract_river_metrics
        metrics = extract_river_metrics(raw, board)
        cbet_key = 'ip_bet_pct'
    else:
        from worker_turn_river import extract_turn_metrics
        metrics = extract_turn_metrics(raw, board)
        cbet_key = 'ip_cbet_pct'

    cbet = metrics.get(cbet_key, '?')
    t2   = metrics.get('cbet_two_overcards' if street != 'river' else 'bet_two_overcards', '-')
    t3   = metrics.get('cbet_air' if street != 'river' else 'bet_air', '-')
    print(f'[{street[:3].upper()}] {board_id:18s} {board:25s}  '
          f'bet={cbet}%  T2={t2}%  T3={t3}%  ({elapsed:.0f}s)')
    return {'board_id': board_id, 'board': board, 'street': street,
            'elapsed_s': round(elapsed, 1), **metrics}


def main() -> None:
    print(f'Running {len(SAMPLE_BOARDS)} sample boards with accuracy={ACCURACY}, max_iter={MAX_ITER}')
    print(f'Threads={THREADS} per board (sequential)')
    print('-' * 90)

    tmpdir = Path(tempfile.mkdtemp(prefix='solver_sample_'))
    results = []
    t_start = time.time()

    for board_id, board, street in SAMPLE_BOARDS:
        result = run_one(board_id, board, street, tmpdir)
        results.append(result)

    total = time.time() - t_start
    ok = sum(1 for r in results if 'error' not in r)
    print(f'\n{ok}/{len(results)} OK in {total:.0f}s')

    if ok < len(results):
        print('Errors:')
        for r in results:
            if 'error' in r:
                print(f'  {r["board_id"]}: {r["error"]}')

    out = OUT_DIR / 'sample_test_results.json'
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f'Saved: {out}')


if __name__ == '__main__':
    main()
