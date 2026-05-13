#!/usr/bin/env python3
"""
local_cr_study.py — Run CR flop study locally (no GCS).

Reads:   scripts/gcp_study_cr_river/scenarios_cr_river.json
Solves:  15 flop boards via TexasSolver
Writes:  knowledges/cr_river_study/{id}.json
         knowledges/cr_river_study/SUMMARY.md

Usage:
    python3 scripts/local_cr_study.py [--dry-run] [--id cr_K72r]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Re-use extraction logic from the GCS worker
sys.path.insert(0, str(Path(__file__).parent / 'gcp_study_cr_river'))
from worker_cr_river import (  # type: ignore
    BTN_RANGE, BB_RANGE, extract_flop_metrics
)

# Flop-only config (no turn/river subtrees): much faster, ~60-120s per board
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
set_allin_threshold 0.67
build_tree
set_thread_num {threads}
set_accuracy 0.5
set_max_iteration 300
start_solve
dump_result {dump_path}
"""

SOLVER_BIN = '/home/cuzic/TexasSolver/build/console_solver'
SOLVER_DIR = '/home/cuzic/TexasSolver'
SCENARIOS_JSON = Path(__file__).parent / 'gcp_study_cr_river' / 'scenarios_cr_river.json'
RESULTS_DIR = Path(__file__).parent.parent / 'knowledges' / 'cr_river_study'

TEXTURE_LABELS = {
    'dry_K_high': 'ドライ(K-high)',
    'dry_A_high': 'ドライ(A-high)',
    'semi_broadway': 'セミウェット(Broadway)',
    'semi_broadway_high': 'セミウェット(Broadway高)',
    'connected_mid': 'コネクテッド(中)',
    'connected_low': 'コネクテッド(低)',
    'suited': 'スーテッド',
    'paired': 'ペア板',
    'wet': 'ウェット',
}

TEXTURE_GROUPS = {
    'ドライ': ['dry_K_high', 'dry_A_high', 'low_dry'],
    'セミウェット': ['semi_broadway', 'semi_broadway_high'],
    'コネクテッド': ['connected_mid', 'connected_mid2', 'low_connected'],
    'スーテッド/FD': ['fd_K_high', 'fd_Q_high', 'fd_broadway_fd', 'fd_A_high', 'mono'],
    'ペア板': ['paired_high', 'paired_mid'],
}


def run_solver(scenario: dict, dump_path: str, threads: int = 8, timeout: int = 600) -> bool:
    board = scenario['board']
    pot = scenario['pot_bb']
    stack = scenario['effective_stack_bb']
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
                [SOLVER_BIN], stdin=fin,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
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


def solve_scenario(scenario: dict, dry_run: bool = False) -> dict | None:
    sid = scenario['id']
    result_path = RESULTS_DIR / f'{sid}.json'

    if result_path.exists():
        print(f'  [{sid}] Using cached result')
        with open(result_path) as f:
            return json.load(f)

    if dry_run:
        print(f'  [{sid}] DRY-RUN: would solve {scenario["board"]}')
        return None

    print(f'  [{sid}] Solving {scenario["board"]}...', end='', flush=True)
    t0 = time.time()
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tf:
        dump_path = tf.name

    try:
        ok = run_solver(scenario, dump_path)
        elapsed = time.time() - t0
        if not ok:
            print(f' FAILED ({elapsed:.0f}s)')
            return None

        with open(dump_path) as f:
            raw = json.load(f)
        metrics = extract_flop_metrics(raw, scenario)
        metrics['elapsed_s'] = round(elapsed, 1)
        metrics['board'] = scenario['board']
        metrics['texture'] = scenario.get('texture', '')
        metrics['id'] = sid
        print(f' done ({elapsed:.0f}s) cr_vs33={metrics.get("oop_cr_vs33", "?")}%')

        result_path.parent.mkdir(parents=True, exist_ok=True)
        with open(result_path, 'w') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        return metrics
    finally:
        try:
            os.unlink(dump_path)
        except OSError:
            pass


def generate_summary(results: list[dict]) -> str:
    lines = ['# CR フロップ研究 — 結果サマリー\n']
    lines.append(f'調査ボード数: {len(results)}\n')
    lines.append('\n## 個別ボード結果\n')
    lines.append('| ID | ボード | テクスチャ | CR_vs33% | CR_vs75% | CBet% |')
    lines.append('|----|--------|-----------|---------|---------|-------|')

    for r in sorted(results, key=lambda x: x.get('texture', '')):
        sid = r.get('id', '?')
        board = r.get('board', '?')
        tex = TEXTURE_LABELS.get(r.get('texture', ''), r.get('texture', '?'))
        cr33 = r.get('oop_cr_vs33', '—')
        cr75 = r.get('oop_cr_vs75', '—')
        cbet = r.get('ip_cbet_pct', '—')
        lines.append(f'| {sid} | {board} | {tex} | {cr33}% | {cr75}% | {cbet}% |')

    lines.append('\n## テクスチャ別集計\n')
    for group_name, textures in TEXTURE_GROUPS.items():
        group_results = [r for r in results if r.get('texture', '') in textures]
        if not group_results:
            continue
        cr33_vals = [r['oop_cr_vs33'] for r in group_results if 'oop_cr_vs33' in r]
        cr75_vals = [r['oop_cr_vs75'] for r in group_results if 'oop_cr_vs75' in r]
        if cr33_vals:
            avg33 = round(sum(cr33_vals) / len(cr33_vals), 1)
            avg75 = round(sum(cr75_vals) / len(cr75_vals), 1) if cr75_vals else '—'
            lines.append(f'**{group_name}** (n={len(group_results)}): CR_vs33={avg33}%, CR_vs75={avg75}%')

    return '\n'.join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--id', help='Solve specific scenario ID only')
    args = parser.parse_args()

    with open(SCENARIOS_JSON) as f:
        data = json.load(f)

    flop_scenarios = [s for s in data['scenarios'] if s.get('n_board', 3) == 3]
    if args.id:
        flop_scenarios = [s for s in flop_scenarios if s['id'] == args.id]

    print(f'Running {len(flop_scenarios)} flop CR scenarios...')

    results = []
    for scenario in flop_scenarios:
        r = solve_scenario(scenario, dry_run=args.dry_run)
        if r:
            results.append(r)

    if results:
        summary = generate_summary(results)
        summary_path = RESULTS_DIR / 'SUMMARY.md'
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        with open(summary_path, 'w') as f:
            f.write(summary)
        print(f'\nSummary written to {summary_path}')
        print('\n--- Summary ---')
        print(summary)
    else:
        print('No results generated.')


if __name__ == '__main__':
    main()
