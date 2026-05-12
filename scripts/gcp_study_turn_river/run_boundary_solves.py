#!/usr/bin/env python3
"""
run_boundary_solves.py — Run TexasSolver locally for critical boundary boards.

Targets:
  1. rainbow_connected (B=67, just below T3=70 threshold) — T3 behavior unclear
  2. Connected low boards (T98r, T87r, 987r, 876r) — spread≤3 but top<J, get B=55
  3. 2tone_connected (QJT2t, JT9 2t) — get B=50 but high CBet
  4. mono additional (B=70 boundary) — size verification (33% vs 50%)
  5. rainbow_q (B=58 boundary) — T2 behavior at exact threshold

Extracts: btn_cbet_pct, btn_cbet_33/50/75, bb_fold_vs33/50/75,
          cbet_overpair, cbet_top_pair, cbet_two_overcards, cbet_air

Saves to: knowledges/flop/results/boundary_boards/
"""
from __future__ import annotations
import json, os, subprocess, tempfile, time
from pathlib import Path

SOLVER_BIN = '/home/cuzic/TexasSolver/build/console_solver'
SOLVER_DIR = '/home/cuzic/TexasSolver'
OUT_DIR = Path('/home/cuzic/poker-books/knowledges/flop/results/boundary_boards')
OUT_DIR.mkdir(parents=True, exist_ok=True)

POT   = 7
STACK = 97

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
set_thread_num 8
set_accuracy 0.5
set_max_iteration 500
set_print_interval 200
set_dump_rounds 1
start_solve
dump_result {dump}
"""

# ── Board list (critical boundary cases) ──────────────────────────────────────
# Format: (board_id, solver_str, expected_texture, b_score, note)
BOUNDARY_BOARDS = [
    # rainbow_connected (B=67) — T3 boundary cases
    ('KQJr_1',   'Kc,Qd,Jh',   'rainbow_connected', 67, 'KQJ rainbow — top K'),
    ('QJTr_1',   'Qc,Jd,Th',   'rainbow_connected', 67, 'QJT rainbow'),
    ('JT9r_1',   'Jc,Td,9h',   'rainbow_connected', 67, 'JT9 rainbow'),
    ('KJTr_1',   'Kc,Jd,Th',   'rainbow_connected', 67, 'KJT rainbow — spread 3'),
    ('QT9r_1',   'Qc,Td,9h',   'rainbow_connected', 67, 'QT9 rainbow — spread 3'),
    ('KQTr_1',   'Kc,Qd,Th',   'rainbow_connected', 67, 'KQT rainbow — spread 3'),

    # Low connected rainbow (top<J, spread<=3) — classified as B=55
    ('T98r_1',   'Tc,9d,8h',   'rainbow',           55, 'T98 rainbow — spread 2, top<J → should get B boost?'),
    ('T87r_1',   'Tc,8d,7h',   'rainbow',           55, 'T87 rainbow — spread 3, top<J'),
    ('987r_1',   '9c,8d,7h',   'rainbow',           55, '987 rainbow — spread 2, top<J'),
    ('876r_1',   '8c,7d,6h',   'rainbow',           55, '876 rainbow — spread 2, top<J'),
    ('T97r_1',   'Tc,9d,7h',   'rainbow',           55, 'T97 rainbow — spread 3'),
    ('986r_1',   '9c,8d,6h',   'rainbow',           55, '986 rainbow — spread 3'),

    # 2-tone connected boards — classified as B=50
    ('QJT2t_1',  'Qc,Jd,Tc',   '2tone',             50, 'QJT 2-tone — spread 2, top Q≥J, but 2-tone'),
    ('JT9_2t_1', 'Jc,Td,9c',   '2tone',             50, 'JT9 2-tone — spread 2'),
    ('T98_2t_1', 'Tc,9d,8c',   '2tone',             50, 'T98 2-tone — spread 2, top<J'),
    ('987_2t_1', '9c,8d,7c',   '2tone',             50, '987 2-tone — spread 2'),

    # Mono (B=70) — size verification
    ('K95cc_1',  'Kc,9c,5c',   'mono',              70, 'K95 mono — K high'),
    ('J84cc_1',  'Jc,8c,4c',   'mono',              70, 'J84 mono'),
    ('T73cc_1',  'Tc,7c,3c',   'mono',              70, 'T73 mono'),
    ('A52cc_1',  'Ac,5c,2c',   'mono',              70, 'A52 mono — A high'),

    # rainbow_q (B=58) — T2 boundary
    ('Q83r_1',   'Qc,8d,3h',   'rainbow_q',         58, 'Q83 rainbow — Q high dry'),
    ('Q72r_1',   'Qc,7d,2h',   'rainbow_q',         58, 'Q72 rainbow — Q high very dry'),
    ('Q94r_1',   'Qc,9d,4h',   'rainbow_q',         58, 'Q94 rainbow'),
    ('QT7r_1',   'Qc,Td,7h',   'rainbow_q',         58, 'QT7 rainbow — connected-ish'),
    ('Q86r_1',   'Qc,8d,6h',   'rainbow_q',         58, 'Q86 rainbow'),

    # 2tone_ak (B=56) — T2 boundary (need more data)
    ('A83t_1',   'Ac,8d,3c',   '2tone_ak',          56, 'A83 2-tone — A high dry'),
    ('K94t_1',   'Kc,9d,4c',   '2tone_ak',          56, 'K94 2-tone — K high dry'),
    ('A72t_1',   'Ac,7d,2c',   '2tone_ak',          56, 'A72 2-tone — A high very dry'),
    ('AT7t_1',   'Ac,Td,7c',   '2tone_ak',          56, 'AT7 2-tone — somewhat connected'),
    ('K86t_1',   'Kc,8d,6c',   '2tone_ak',          56, 'K86 2-tone'),
]

RANK_VAL = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}


def run_solver(board_str: str, dump_path: str, timeout: int = 300) -> bool:
    cfg = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board_str,
        ip=IP_RANGE, oop=OOP_RANGE, dump=dump_path,
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
        try: os.unlink(cfg_path)
        except OSError: pass


def _board_ranks(solver_str: str) -> tuple[int,int,int]:
    cards = solver_str.split(',')
    ranks = sorted([RANK_VAL[c[0].upper()] for c in cards], reverse=True)
    return ranks[0], ranks[1], ranks[2]


def _bet_node(parent: dict, target_pct: float) -> dict | None:
    expected = POT * target_pct / 100.0
    best, best_diff = None, float('inf')
    for key, node in parent.get('childrens', {}).items():
        if not key.startswith('BET'):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        diff = abs(amt - expected)
        if diff < best_diff:
            best_diff = diff
            best = node
    return best if best_diff < 2.5 else None


def _avg_action(node: dict, prefix: str) -> float:
    strat = node.get('strategy', {})
    actions: list[str] = strat.get('actions', [])
    combos: dict = strat.get('strategy', {})
    idxs = [i for i, a in enumerate(actions) if a.startswith(prefix) or a == prefix]
    if not idxs or not combos:
        return 0.0
    return sum(sum(probs[i] for i in idxs if i < len(probs))
               for probs in combos.values()) / len(combos)


def _categorize_combo(combo: str, r_hi: int, r_mid: int, r_lo: int) -> str:
    r1 = RANK_VAL.get(combo[0].upper(), 0)
    r2 = RANK_VAL.get(combo[2].upper(), 0)
    board_set = {r_hi, r_mid, r_lo}
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


def _cbet_by_category(check_node: dict, category: str, r_hi: int, r_mid: int, r_lo: int) -> float | None:
    strat = check_node.get('strategy', {})
    actions: list[str] = strat.get('actions', [])
    combos: dict = strat.get('strategy', {})
    bet_idxs = [i for i, a in enumerate(actions) if a.startswith('BET') or a == 'ALLIN']
    matched: list[float] = []
    for combo, probs in combos.items():
        if len(combo) < 4:
            continue
        if _categorize_combo(combo, r_hi, r_mid, r_lo) != category:
            continue
        matched.append(sum(probs[i] for i in bet_idxs if i < len(probs)))
    return sum(matched)/len(matched) if matched else None


def extract_metrics(raw: dict, r_hi: int, r_mid: int, r_lo: int) -> dict:
    check_node = raw.get('childrens', {}).get('CHECK')
    if check_node is None:
        return {'error': 'no CHECK node'}

    btn_cbet = (_avg_action(check_node, 'BET') + (_avg_action(check_node, 'ALLIN') or 0.0)) * 100.0
    metrics: dict = {'btn_cbet_pct': round(btn_cbet, 2)}

    for pct in [33, 50, 75]:
        sn = _bet_node(check_node, pct)
        if sn is None:
            continue
        strat = check_node.get('strategy', {})
        actions: list[str] = strat.get('actions', [])
        combos: dict = strat.get('strategy', {})
        expected = POT * pct / 100.0
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
        if best_idx >= 0 and combos:
            p = sum(probs[best_idx] for probs in combos.values() if best_idx < len(probs)) / len(combos)
            metrics[f'btn_cbet_{pct}'] = round(p * 100.0, 2)
        # OOP fold
        fold_p = _avg_action(sn, 'FOLD')
        metrics[f'bb_fold_vs{pct}'] = round(fold_p * 100.0, 2)

    for cat in ['overpair', 'top_pair', 'two_overcards', 'air']:
        p = _cbet_by_category(check_node, cat, r_hi, r_mid, r_lo)
        if p is not None:
            metrics[f'cbet_{cat}'] = round(p * 100.0, 2)

    return metrics


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='Show board list without running solver')
    ap.add_argument('--filter', default='', help='Only run boards matching this substring in ID')
    ap.add_argument('--force', action='store_true', help='Re-run even if result exists')
    args = ap.parse_args()

    boards = BOUNDARY_BOARDS
    if args.filter:
        boards = [b for b in boards if args.filter.lower() in b[0].lower() or args.filter.lower() in b[2].lower()]

    if args.dry_run:
        print(f'{"Board ID":15s}  {"Solver":15s}  {"Texture":22s}  {"B":3s}  Notes')
        print('-' * 80)
        for bid, solver_str, tex, b_score, note in boards:
            print(f'{bid:15s}  {solver_str:15s}  {tex:22s}  {b_score:3d}  {note}')
        print(f'\nTotal: {len(boards)} boards')
        return

    print(f'Running {len(boards)} boundary boards...\n')
    results = []

    for i, (bid, solver_str, tex, b_score, note) in enumerate(boards):
        out_file = OUT_DIR / f'{bid}.json'
        if out_file.exists() and not args.force:
            print(f'[SKIP] {bid} (cached)')
            results.append(json.load(out_file.open()))
            continue

        print(f'[{i+1:2d}/{len(boards)}] {bid:15s} ({tex}, B={b_score})  {solver_str}', end='', flush=True)
        r_hi, r_mid, r_lo = _board_ranks(solver_str)

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            dump_path = tmp.name

        t0 = time.time()
        ok = run_solver(solver_str, dump_path)
        elapsed = time.time() - t0

        if not ok:
            print(f'  FAILED ({elapsed:.0f}s)')
            results.append({'board_id': bid, 'error': 'solver failed'})
            continue

        raw = json.loads(Path(dump_path).read_text())
        Path(dump_path).unlink(missing_ok=True)
        metrics = extract_metrics(raw, r_hi, r_mid, r_lo)

        result = {
            'board_id': bid, 'solver_str': solver_str,
            'texture': tex, 'b_score': b_score, 'note': note,
            'r_hi': r_hi, 'r_mid': r_mid, 'r_lo': r_lo,
            'elapsed_s': round(elapsed, 1),
            **metrics,
        }
        out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        results.append(result)

        cbet = metrics.get('btn_cbet_pct', '?')
        t2 = metrics.get('cbet_two_overcards', '-')
        t3 = metrics.get('cbet_air', '-')
        fold33 = metrics.get('bb_fold_vs33', '-')
        print(f'  CBet={cbet}%  T2={t2}%  T3={t3}%  fold33={fold33}%  ({elapsed:.0f}s)')

    # ── Summary ───────────────────────────────────────────────────────────────
    print('\n' + '=' * 80)
    print('BOUNDARY BOARD RESULTS SUMMARY')
    print('=' * 80)
    ok_results = [r for r in results if 'error' not in r]
    print(f'Completed: {len(ok_results)}/{len(results)}\n')

    from collections import defaultdict
    by_texture: dict[str, list] = defaultdict(list)
    for r in ok_results:
        by_texture[r.get('texture', '?')].append(r)

    print(f'{"board_id":15s}  {"tex":22s}  {"B":3s}  {"cbet%":6s}  {"T2_2oc":7s}  '
          f'{"T3_air":7s}  {"fold33":7s}  {"fold50":7s}  {"fold75":7s}  {"notes"}')
    print('-' * 110)
    for tex_name in sorted(by_texture.keys()):
        for r in by_texture[tex_name]:
            cbet = r.get('btn_cbet_pct', '-')
            t2 = r.get('cbet_two_overcards', '-')
            t3 = r.get('cbet_air', '-')
            f33 = r.get('bb_fold_vs33', '-')
            f50 = r.get('bb_fold_vs50', '-')
            f75 = r.get('bb_fold_vs75', '-')
            print(f'{r["board_id"]:15s}  {tex_name:22s}  {r.get("b_score",0):3d}  '
                  f'{cbet!s:6s}  {t2!s:7s}  {t3!s:7s}  {f33!s:7s}  {f50!s:7s}  '
                  f'{f75!s:7s}  {r.get("note","")[:35]}')

    # Save combined results
    combined_path = OUT_DIR / 'boundary_results_combined.json'
    combined_path.write_text(json.dumps(ok_results, ensure_ascii=False, indent=2))
    print(f'\nResults saved to: {combined_path}')


if __name__ == '__main__':
    main()
