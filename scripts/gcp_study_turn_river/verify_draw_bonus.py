#!/usr/bin/env python3
"""
verify_draw_bonus.py — GTO検証: draw_bonus（アウツ × 2）は弱い役スコアで過剰評価か？

Board: K♥9♥3♦ → 7♦ (2tone_ak + blank turn)
OOP(BB) が IP(BTN) の 33/50/75% CBet に直面したときの defense 頻度を手別に計測。
"""
from __future__ import annotations
import json, subprocess, tempfile, os, time
from pathlib import Path

SOLVER_BIN = '/home/cuzic/TexasSolver/build/console_solver'
SOLVER_DIR = '/home/cuzic/TexasSolver'
OUT_DIR    = Path(__file__).parent / 'results'
THREADS    = 4
ACCURACY   = 0.5
MAX_ITER   = 200

OOP_RANGE = ('JJ,TT,99,88,77,66,55,44,33,22,'
             'AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,AQo,AJo,ATo,'
             'KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,KQo,KJo,KTo,'
             'QJs,QTs,Q9s,Q8s,Q7s,Q6s,QJo,QTo,JTs,J9s,J8s,JTo,'
             'T9s,T8s,T7s,T9o,98s,97s,96s,98o,87s,86s,87o,76s,75s,76o,65s,65o,54s,53s,43s')
IP_RANGE  = ('AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,'
             'AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,'
             'KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,'
             'QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,JTs,JTo,J9s,J8s,J7s,'
             'T9s,T8s,T7s,98s,97s,87s,86s,76s,75s,65s,54s')

BOARD = 'Kh,9h,3d,7d'

PREDICTED = {
    'JhTh': {'label': 'J♥T♥ 純FD',      'hs': 26, 'draw': 'FD 9outs',   'base': 8},
    'QsJs': {'label': 'Q♠J♠ 2OC',        'hs': 20, 'draw': 'none',       'base': 20},
    'Th8h': {'label': 'T♥8♥ 純OESD',     'hs': 24, 'draw': 'OESD 8outs', 'base': 8},
    'KdQd': {'label': 'K♦Q♦ TPMK',       'hs': 50, 'draw': 'none',       'base': 50},
    'AdJd': {'label': 'A♦J♦ Aハイのみ',  'hs': 25, 'draw': 'none',       'base': 25},
}

CFG = """set_pot 10
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


def run_solver(dump_path: str) -> dict | None:
    cfg = CFG.format(board=BOARD, ip=IP_RANGE, oop=OOP_RANGE,
                     threads=THREADS, acc=ACCURACY, mi=MAX_ITER, dump=dump_path)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(cfg); cfg_file = f.name
    t0 = time.time()
    try:
        with open(cfg_file) as fin:
            proc = subprocess.Popen([SOLVER_BIN], stdin=fin,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                                    cwd=SOLVER_DIR)
            _, _ = proc.communicate(timeout=600)
    finally:
        os.unlink(cfg_file)
    print(f'  Solved in {time.time()-t0:.0f}s, rc={proc.returncode}')
    if proc.returncode != 0 or not Path(dump_path).exists():
        return None
    return json.loads(Path(dump_path).read_text())


def _combo_defense(node: dict, combos: list[str]) -> dict[str, dict]:
    """OOP response strategy at `node` (IP just bet, OOP responds)."""
    strat_block = node.get('strategy', {})
    actions: list[str] = strat_block.get('actions', [])
    combo_strat: dict  = strat_block.get('strategy', {})

    # debug: show a sample of combos present
    sample = list(combo_strat.keys())[:5]
    print(f'    Strategy sample combos: {sample}')
    print(f'    Actions: {actions}')

    results: dict[str, dict] = {}
    for combo in combos:
        if combo not in combo_strat:
            results[combo] = {}
            continue
        freqs = combo_strat[combo]
        d: dict[str, float] = {}
        for i, a in enumerate(actions):
            freq = freqs[i] if i < len(freqs) else 0.0
            au = a.upper()
            if au == 'FOLD':
                d['fold'] = freq
            elif au == 'CALL':
                d['call'] = freq
            else:
                d['raise'] = d.get('raise', 0.0) + freq
        results[combo] = d
    return results


def get_bet_node(tree: dict, approx_pct: float) -> tuple[str, dict] | tuple[None, None]:
    """root → OOP CHECK → IP bet node closest to approx_pct%."""
    check_node = tree.get('childrens', {}).get('CHECK')
    if check_node is None:
        return None, None
    ip_kids = check_node.get('childrens', {})
    # pot=10, chips = pct/100 * 10
    target_chips = approx_pct / 100 * 10
    best_key, best_node, best_diff = None, None, 999
    for key, node in ip_kids.items():
        try:
            chips = float(key.replace('BET ', '').replace('ALLIN', '999'))
        except ValueError:
            continue
        diff = abs(chips - target_chips)
        if diff < best_diff:
            best_key, best_node, best_diff = key, node, diff
    return best_key, best_node


def analyze_vs_bet(tree: dict, bet_pct: float, target_combos: list[str]) -> dict[str, dict]:
    key, node = get_bet_node(tree, bet_pct)
    if node is None:
        print(f'  No node found for ~{bet_pct}% bet')
        return {}
    print(f'  vs ~{bet_pct}% → using node: {key}')
    return _combo_defense(node, target_combos)


def print_table(title: str, defense: dict[str, dict]) -> None:
    print(f'\n--- {title} ---')
    print(f'{"手":14s} {"HS予測":7s} {"タイプ":14s} {"fold%":7s} {"call%":7s} {"raise%":7s} {"def%":7s}')
    for combo, info in PREDICTED.items():
        d = defense.get(combo, {})
        if not d:
            print(f'{info["label"]:14s} {info["hs"]:7d} {info["draw"]:14s}  (combo not found)')
            continue
        fold_p  = d.get('fold',  0) * 100
        call_p  = d.get('call',  0) * 100
        raise_p = d.get('raise', 0) * 100
        def_p   = call_p + raise_p
        print(f'{info["label"]:14s} {info["hs"]:7d} {info["draw"]:14s} {fold_p:7.1f} {call_p:7.1f} {raise_p:7.1f} {def_p:7.1f}')


def insights(all_results: dict[float, dict]) -> None:
    print('\n■ 考察: 純ドロー(FD/OESD) vs 安定SDV の defense% 比較')
    for pct, defense in sorted(all_results.items()):
        fd   = defense.get('JhTh', {})
        osd  = defense.get('Th8h', {})
        qj   = defense.get('QsJs', {})
        aj   = defense.get('AdJd', {})
        if not fd or not qj:
            continue
        fd_d  = (fd.get('call',0) + fd.get('raise',0)) * 100
        qj_d  = (qj.get('call',0) + qj.get('raise',0)) * 100
        osd_d = (osd.get('call',0) + osd.get('raise',0)) * 100 if osd else -1
        aj_d  = (aj.get('call',0) + aj.get('raise',0)) * 100 if aj else -1
        diff_fd_qj   = fd_d - qj_d
        diff_osd_aj  = osd_d - aj_d if osd_d >= 0 and aj_d >= 0 else None

        tag = ''
        if diff_fd_qj < -15:
            tag = '← FD 過剰評価の証拠'
        elif diff_fd_qj > 15:
            tag = '← FD 過小評価'
        else:
            tag = '← 誤差範囲'

        print(f'  vs {pct:.0f}%: FD(HS26)={fd_d:.1f}% | 2OC(HS20)={qj_d:.1f}%  diff={diff_fd_qj:+.1f}% {tag}')
        if diff_osd_aj is not None:
            tag2 = '← OESD 過剰評価' if diff_osd_aj < -15 else ('← 誤差範囲' if abs(diff_osd_aj) <= 15 else '← OESD 過小')
            print(f'         OESD(HS24)={osd_d:.1f}% | Aハイ(HS25)={aj_d:.1f}%  diff={diff_osd_aj:+.1f}% {tag2}')


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    dump_path = str(OUT_DIR / 'draw_bonus_raw.json')

    print('=== Draw Bonus GTO Verification ===')
    print(f'Board: {BOARD} (2tone_ak + blank turn)')
    print(f'accuracy={ACCURACY}, max_iter={MAX_ITER}, threads={THREADS}\n')

    tree = run_solver(dump_path)
    if tree is None:
        print('Solver failed.'); return

    targets = list(PREDICTED.keys())
    all_results: dict[float, dict] = {}

    for pct in [33.0, 50.0, 75.0]:
        d = analyze_vs_bet(tree, pct, targets)
        all_results[pct] = d
        print_table(f'OOP defense vs IP ~{pct:.0f}% bet', d)

    insights(all_results)

    out = OUT_DIR / 'draw_bonus_results.json'
    out.write_text(json.dumps(
        {str(pct): {c: d for c, d in res.items()} for pct, res in all_results.items()},
        ensure_ascii=False, indent=2))
    print(f'\n結果保存: {out}')


if __name__ == '__main__':
    main()
