#!/usr/bin/env python3
"""
verify_draw_bonus_v2.py — [GTO-V1] 純ドロー draw_bonus 精度検証（再設計版）

Board: T♠7♠3♦ → 2♥ (semi-wet, 2 spades on flop, blank turn)
比較手 (全て OOP range 内の有効コンボ):
  6♠4♠ → 純FD（ペアなし、OC なし）  HS予測=26  (base=8, FD+18)
  K♣Q♦ → 2OC のみ（FD なし）         HS予測=20  (base=20)
  A♣Q♣ → Aハイ（OC x1）              HS予測=25  (base=25)
  9♣8♦ → 純OESD（9とT♠で9-T...8♣ と 7♠ で7-8-9-T → OESD) HS予測=24
  8♠5♠ → 純FD のみ（8♠+5♠+T♠+7♠=4枚）  HS予測=26
"""
from __future__ import annotations
import json, subprocess, tempfile, os, time, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'poker-drill' / 'scripts' / 'generate' / 'core'))

SOLVER_BIN = '/home/cuzic/TexasSolver/build/console_solver'
SOLVER_DIR = '/home/cuzic/TexasSolver'
OUT_DIR    = Path(__file__).parent / 'results'
THREADS    = 4
ACCURACY   = 0.5
MAX_ITER   = 300

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

# Board: T♠7♠3♦ → 2♥
BOARD = 'Ts,7s,3d,2h'

TARGETS = {
    '6s4s': {'label': '6♠4♠ 純FD',          'hs_pred': 26, 'type': 'pure_FD',   'base': 8,  'draw': '+18(FD)'},
    '8s5s': {'label': '8♠5♠ 純FD',          'hs_pred': 26, 'type': 'pure_FD',   'base': 8,  'draw': '+18(FD)'},
    'KcQd': {'label': 'K♣Q♦ 2OC',           'hs_pred': 50, 'type': 'made_TPMK', 'base': 50, 'draw': 'none'},
    'AcQc': {'label': 'A♣Q♣ Aハイ',         'hs_pred': 25, 'type': 'made_Ahigh','base': 25, 'draw': 'none'},
    '9c8d': {'label': '9♣8♦ OESD',          'hs_pred': 24, 'type': 'pure_OESD', 'base': 8,  'draw': '+16(OESD)'},
    'JcTc': {'label': 'J♣T♣ 2OC+BDFD',     'hs_pred': 20, 'type': '2OC',       'base': 20, 'draw': '+2(BDFD)'},
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


def get_bet_node(tree: dict, approx_chips: float) -> tuple[str, dict] | tuple[None, None]:
    check_node = tree.get('childrens', {}).get('CHECK')
    if not check_node:
        return None, None
    best_key, best_node, best_diff = None, None, 999.0
    for key, node in check_node.get('childrens', {}).items():
        try:
            chips = float(key.replace('BET ', ''))
        except ValueError:
            continue
        if abs(chips - approx_chips) < best_diff:
            best_key, best_node, best_diff = key, node, abs(chips - approx_chips)
    return best_key, best_node


def combo_defense(node: dict, combos: list[str]) -> dict[str, dict]:
    sb = node.get('strategy', {})
    actions: list[str] = sb.get('actions', [])
    strat: dict        = sb.get('strategy', {})
    result = {}
    for c in combos:
        if c not in strat:
            result[c] = {}
            continue
        freqs = strat[c]
        d: dict[str, float] = {}
        for i, a in enumerate(actions):
            f = freqs[i] if i < len(freqs) else 0.0
            if a.upper() == 'FOLD':
                d['fold'] = f
            elif a.upper() == 'CALL':
                d['call'] = f
            else:
                d['raise'] = d.get('raise', 0.0) + f
        result[c] = d
    return result


def print_table(bet_pct: float, defense: dict[str, dict]) -> None:
    pot = 10
    chips = bet_pct / 100 * pot
    print(f'\n--- vs IP ~{bet_pct:.0f}% ポット bet ({chips:.1f} chips) ---')
    print(f'{"手":18s} {"HS予測":7s} {"タイプ":16s} {"fold%":7s} {"call%":7s} {"raise%":7s} {"def%":7s}')
    for combo, info in TARGETS.items():
        d = defense.get(combo, {})
        if not d:
            print(f'{info["label"]:18s} {info["hs_pred"]:7d} {info["type"]:16s}  (range外)')
            continue
        fold_p  = d.get('fold',  0) * 100
        call_p  = d.get('call',  0) * 100
        raise_p = d.get('raise', 0) * 100
        def_p   = call_p + raise_p
        print(f'{info["label"]:18s} {info["hs_pred"]:7d} {info["type"]:16s} {fold_p:7.1f} {call_p:7.1f} {raise_p:7.1f} {def_p:7.1f}')


def insights(results: dict[float, dict]) -> None:
    print('\n■ draw_bonus 検証サマリー')
    for pct in sorted(results):
        d = results[pct]
        fd1  = d.get('6s4s', {}); fd2 = d.get('8s5s', {})
        osd  = d.get('9c8d', {})
        jtc  = d.get('JcTc', {})
        ahigh = d.get('AcQc', {})

        def def_pct(x): return (x.get('call', 0) + x.get('raise', 0)) * 100

        fd_avg   = (def_pct(fd1) + def_pct(fd2)) / 2 if fd1 and fd2 else def_pct(fd1) or def_pct(fd2)
        osd_d    = def_pct(osd)
        ahigh_d  = def_pct(ahigh)
        jtc_d    = def_pct(jtc)

        # 同 HS 比較: FD(26) vs Aハイ(25)
        if fd1 and ahigh:
            diff = fd_avg - ahigh_d
            tag = ('← FD 過剰評価' if diff < -15 else
                   '← FD 過小評価' if diff > 15 else '← 誤差範囲内')
            print(f'  vs {pct:.0f}%: FD avg(HS≈26)={fd_avg:.1f}%  Aハイ(HS25)={ahigh_d:.1f}%  '
                  f'OESD(HS24)={osd_d:.1f}%  2OC(HS20)={jtc_d:.1f}%  diff={diff:+.1f}% {tag}')


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    dump = str(OUT_DIR / 'draw_bonus_v2_raw.json')

    print('=== Draw Bonus GTO Verification v2 ===')
    print(f'Board: {BOARD}  (T♠7♠3♦→2♥, semi+blank)')
    print(f'accuracy={ACCURACY}, max_iter={MAX_ITER}, threads={THREADS}\n')

    tree = run_solver(dump)
    if not tree:
        print('Solver failed.'); return

    # pot=10 → chips: 33%≈3.3, 50%=5.0, 75%=7.5
    targets = list(TARGETS.keys())
    all_results: dict[float, dict] = {}
    for pct in [33.0, 50.0, 75.0]:
        chips = pct / 100 * 10
        key, node = get_bet_node(tree, chips)
        if node is None:
            print(f'  No node for {pct}%'); continue
        print(f'  vs ~{pct}% → node: {key}')
        d = combo_defense(node, targets)
        all_results[pct] = d
        print_table(pct, d)

    insights(all_results)

    out = OUT_DIR / 'draw_bonus_v2_results.json'
    out.write_text(json.dumps(
        {str(p): r for p, r in all_results.items()}, ensure_ascii=False, indent=2))
    print(f'\n保存: {out}')


if __name__ == '__main__':
    main()
