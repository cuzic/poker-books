#!/usr/bin/env python3
"""
verify_draw_bonus_v3.py — [GTO-V1] 純ドロー draw_bonus 精度検証（第3版）

Board: K♥9♥5♦ → 2♣ (2tone_ak + blank turn)
比較手（全て OOP range 内の有効コンボ）:

  純FD (no OC, no pair, no OESD):
    Q♥8♥ (Q8s): FD 9outs, HS予測=26 (base8+FD18)
    J♥8♥ (J8s): FD 9outs, HS予測=26

  A-high:
    A♣Q♦ (AQo-partial): 1OC (A>K), no draw, HS予測=25

  FD+1OC:
    A♥Q♥ (AQs-hearts): FD+1OC, HS予測≈34 (base8+FD18+1OC8)

  TPGK:
    K♦Q♦ (KQo-partial): K♦ pairs K♥ = TPGK, HS予測≈55

  2OC air (control):
    Q♣J♦: both < K, no pair, no draw, HS予測≈8

比較の核心:
  純FD (HS≈26) vs A-high (HS≈25) の defense% が一致すれば draw_bonus 適正
  純FD が大幅に低ければ draw_bonus は過剰評価
  純FD が大幅に高ければ draw_bonus は過小評価
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
MAX_ITER   = 400

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

# Board: K♥9♥5♦ → 2♣
BOARD = 'Kh,9h,5d,2c'

TARGETS = {
    'Qh8h': {'label': 'Q♥8♥ 純FD',       'hs_pred': 26, 'type': 'pure_FD',   'draw': 'FD9'},
    'Jh8h': {'label': 'J♥8♥ 純FD',       'hs_pred': 26, 'type': 'pure_FD',   'draw': 'FD9'},
    'AcQd': {'label': 'A♣Q♦ Aハイ',      'hs_pred': 25, 'type': 'Ahigh_1OC', 'draw': 'none'},
    'AhQh': {'label': 'A♥Q♥ FD+1OC',    'hs_pred': 34, 'type': 'FD+1OC',    'draw': 'FD9+1OC'},
    'KdQd': {'label': 'K♦Q♦ TPGK',      'hs_pred': 55, 'type': 'TPGK',      'draw': 'none'},
    'QcJd': {'label': 'Q♣J♦ 2OC air',   'hs_pred':  8, 'type': 'air_2OC',   'draw': 'none'},
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
            au = a.upper()
            if au == 'FOLD':
                d['fold'] = f
            elif au == 'CALL':
                d['call'] = f
            else:
                d['raise'] = d.get('raise', 0.0) + f
        result[c] = d
    return result


def print_table(bet_pct: float, defense: dict[str, dict]) -> None:
    pot = 10
    chips = bet_pct / 100 * pot
    print(f'\n--- vs IP ~{bet_pct:.0f}% ポット bet ({chips:.1f} chips) ---')
    print(f'{"手":20s} {"HS予測":7s} {"タイプ":14s} {"draw":10s} {"fold%":7s} {"call%":7s} {"raise%":7s} {"def%":7s}')
    for combo, info in TARGETS.items():
        d = defense.get(combo, {})
        if not d:
            print(f'{info["label"]:20s} {info["hs_pred"]:7d} {info["type"]:14s} {info["draw"]:10s}  (range外)')
            continue
        fold_p  = d.get('fold',  0) * 100
        call_p  = d.get('call',  0) * 100
        raise_p = d.get('raise', 0) * 100
        def_p   = call_p + raise_p
        print(f'{info["label"]:20s} {info["hs_pred"]:7d} {info["type"]:14s} {info["draw"]:10s} {fold_p:7.1f} {call_p:7.1f} {raise_p:7.1f} {def_p:7.1f}')


def insights(results: dict[float, dict]) -> None:
    print('\n■ draw_bonus 検証サマリー（純FD vs A-high）')
    print('  判定基準: diff > +15% → FD過小評価 / diff < -15% → FD過剰評価 / ±15%以内 → 適正')
    print()
    for pct in sorted(results):
        d = results[pct]
        fd_qh8h = d.get('Qh8h', {}); fd_jh8h = d.get('Jh8h', {})
        ahigh    = d.get('AcQd', {})
        fd_oc    = d.get('AhQh', {})
        tpgk     = d.get('KdQd', {})
        air      = d.get('QcJd', {})

        def def_pct(x: dict) -> float:
            return (x.get('call', 0) + x.get('raise', 0)) * 100

        fd1_d  = def_pct(fd_qh8h)
        fd2_d  = def_pct(fd_jh8h)
        fd_avg = (fd1_d + fd2_d) / 2 if fd_qh8h and fd_jh8h else (fd1_d or fd2_d)
        ah_d   = def_pct(ahigh)
        oc_d   = def_pct(fd_oc)
        tp_d   = def_pct(tpgk)
        air_d  = def_pct(air)

        diff_fd_ah = fd_avg - ah_d
        if fd_qh8h and ahigh:
            tag = ('← FD 過剰評価' if diff_fd_ah < -15 else
                   '← FD 過小評価' if diff_fd_ah > 15 else '← 誤差範囲内（適正）')
            print(f'  vs {pct:.0f}%:')
            print(f'    TPGK(HS55)={tp_d:.1f}%  純FD_avg(HS26)={fd_avg:.1f}%  Aハイ(HS25)={ah_d:.1f}%  '
                  f'FD+1OC(HS34)={oc_d:.1f}%  air(HS8)={air_d:.1f}%')
            print(f'    純FD - Aハイ = {diff_fd_ah:+.1f}%  {tag}')


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    dump = str(OUT_DIR / 'draw_bonus_v3_raw.json')

    print('=== Draw Bonus GTO Verification v3 ===')
    print(f'Board: {BOARD}  (K♥9♥5♦→2♣, 2tone_ak + blank turn)')
    print(f'accuracy={ACCURACY}, max_iter={MAX_ITER}, threads={THREADS}')
    print()
    print('手の検証:')
    print('  Q♥8♥: FD(Q♥8♥+K♥9♥=4♥) + no OC(Q<K) + no pair + no OESD = 純FD ✓')
    print('  J♥8♥: FD(J♥8♥+K♥9♥=4♥) + no OC(J<K) + no pair + J-8-9 is gutshot(not OESD) = 純FD ✓')
    print('  A♣Q♦: A>K=1OC + no pair + no draw = Aハイ ✓')
    print('  A♥Q♥: FD(A♥Q♥+K♥9♥=4♥) + A>K=1OC = FD+1OC ✓')
    print('  K♦Q♦: K♦pairs K♥=TPGK ✓')
    print('  Q♣J♦: both<K + no pair + no draw = air ✓')
    print()

    tree = run_solver(dump)
    if not tree:
        print('Solver failed.'); return

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

    out = OUT_DIR / 'draw_bonus_v3_results.json'
    out.write_text(json.dumps(
        {str(p): r for p, r in all_results.items()}, ensure_ascii=False, indent=2))
    print(f'\n保存: {out}')


if __name__ == '__main__':
    main()
