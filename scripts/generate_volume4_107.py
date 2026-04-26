"""
generate_volume4_107.py  --  Turn bet size distribution analysis
Chapter 7: ターン専用ベットサイズ

Runs TexasSolver for representative scenarios across board types × turn card categories
and extracts the distribution of bet sizes used (33%, 50%, 75%, 150%, allin).
"""

import subprocess
import json
import os
import tempfile
import time

SOLVER = '/home/cuzic/TexasSolver/build/console_solver'
SOLVER_DIR = '/home/cuzic/TexasSolver'
OUT_DIR = '/home/cuzic/poker-books/knowledges/volume4/results/107'

IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "KQs,KJs,KTs,K9s,QJs,QTs,Q9s,JTs,J9s,T9s,98s,87s,76s,65s,54s,"
    "AKo,AQo,AJo,ATo,A9o,KQo,KJo,KTo,QJo,QTo,JTo"
)

OOP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,Q5s,QJo,QTo,"
    "JTs,J9s,J8s,J7s,JTo,J9o,"
    "T9s,T8s,T7s,T9o,T8o,"
    "98s,97s,96s,87s,86s,76s,75s,65s,64s,54s,53s,43s,"
    "AKo,AQo,AJo,ATo,A9o,A8o,A7o,A6o,A5o,A4o,A3o,A2o,"
    "KQo,KJo,KTo,K9o,K8o,K7o"
)

SCENARIOS = [
    # (board_label, board_4cards, turn_category, description)
    ('K72r_pair',   ['Kc','7d','2s','Ks'], 'pair',        'ドライ板 + ペアターン'),
    ('K72r_over',   ['Kc','7d','2s','As'], 'overcard',    'ドライ板 + オーバーカードターン'),
    ('K72r_blank',  ['Kc','7d','2s','3c'], 'blank',       'ドライ板 + ブランクターン'),
    ('J75r_pair',   ['Jh','7s','5d','Jc'], 'pair',        'セミ板 + ペアターン'),
    ('J75r_conn',   ['Jh','7s','5d','Tc'], 'connector',   'セミ板 + コネクターターン'),
    ('J75r_blank',  ['Jh','7s','5d','2c'], 'blank',       'セミ板 + ブランクターン'),
    ('T98r_pair',   ['Th','9s','8d','Tc'], 'pair',        'コネクテッド板 + ペアターン'),
    ('T98r_conn',   ['Th','9s','8d','6c'], 'connector',   'コネクテッド板 + コネクターターン'),
    ('987ss_flush', ['9s','8s','7h','6s'], 'flush',       'スーテッド板 + フラッシュターン'),
    ('987ss_blank', ['9s','8s','7h','2c'], 'blank',       'スーテッド板 + ブランクターン'),
]

CONFIG_TEMPLATE = """set_pot 10
set_effective_stack 92
set_board {board}
set_range_ip {ip}
set_range_oop {oop}
set_bet_sizes oop,turn,bet,50,100
set_bet_sizes oop,turn,allin
set_bet_sizes ip,turn,bet,33,50,75,150
set_bet_sizes ip,turn,allin
set_bet_sizes oop,river,bet,50
set_bet_sizes oop,river,allin
set_bet_sizes ip,river,bet,50
set_bet_sizes ip,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 200
set_print_interval 50
set_dump_rounds 1
start_solve
dump_result {dump}
"""

def run_scenario(label, board_cards, turn_category, description):
    board_str = ','.join(board_cards)
    out_path = os.path.join(OUT_DIR, f'betsize_{label}.json')

    if os.path.exists(out_path):
        with open(out_path) as f:
            existing = json.load(f)
        if existing.get('status') == 'ok':
            print(f'  [SKIP] {label} already done')
            return existing

    tmpdir = tempfile.mkdtemp(prefix='ts107_')
    cfg_path = os.path.join(tmpdir, 'config.txt')
    stdout_path = os.path.join(tmpdir, 'stdout.txt')
    dump_path = os.path.join(tmpdir, 'result.json')

    config = CONFIG_TEMPLATE.format(
        board=board_str,
        ip=IP_RANGE,
        oop=OOP_RANGE,
        dump=dump_path,
    )

    with open(cfg_path, 'w') as f:
        f.write(config)

    print(f'  Running {label} ({description})...', flush=True)
    t0 = time.time()

    with open(stdout_path, 'w') as stdout_f:
        proc = subprocess.Popen(
            [SOLVER],
            stdin=open(cfg_path),
            stdout=stdout_f,
            stderr=subprocess.STDOUT,
            cwd=SOLVER_DIR,
        )

    try:
        proc.wait(timeout=250)
    except subprocess.TimeoutExpired:
        proc.kill()
        print(f'  TIMEOUT: {label}')
        return None

    elapsed = time.time() - t0

    # Read stdout for exploitability
    exploit_pct = None
    with open(stdout_path) as f:
        for line in f:
            if 'Total exploitability' in line:
                parts = line.strip().split()
                for i, p in enumerate(parts):
                    if p == 'exploitability':
                        try:
                            exploit_pct = float(parts[i+1])
                        except:
                            pass

    if not os.path.exists(dump_path):
        print(f'  ERROR: no dump for {label}')
        return None

    with open(dump_path) as f:
        tree = json.load(f)

    # Parse full bet size distribution
    size_dist = parse_bet_size_dist(tree)
    cbet_pct = parse_cbet_pct(tree)

    result = {
        'label': label,
        'board': board_cards,
        'board_label': board_cards[:3],
        'turn_card': board_cards[3],
        'turn_category': turn_category,
        'description': description,
        'turn_cbet_pct': cbet_pct,
        'bet_size_distribution': size_dist,
        'exploitability_pct': exploit_pct,
        'elapsed_sec': round(elapsed, 1),
        'status': 'ok',
    }

    with open(out_path, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f'  Done: CBet={cbet_pct:.1f}%, sizes={size_dist}, elapsed={elapsed:.0f}s')
    return result


def parse_cbet_pct(tree):
    check_node = tree.get('childrens', {}).get('CHECK', {})
    strat = check_node.get('strategy', {})
    actions = strat.get('actions', [])
    if not actions:
        return 0.0
    combo_strats = strat.get('strategy', {})
    if not combo_strats:
        return 0.0
    check_idx = actions.index('CHECK') if 'CHECK' in actions else None
    if check_idx is None:
        return 100.0
    total_bet = 0.0
    for probs in combo_strats.values():
        total_bet += 1.0 - probs[check_idx]
    return (total_bet / len(combo_strats)) * 100


def parse_bet_size_dist(tree):
    """
    Extract the distribution of bet sizes used when IP CBets on the turn.
    Returns dict: {action_name: avg_prob_given_cbet}
    """
    check_node = tree.get('childrens', {}).get('CHECK', {})
    strat = check_node.get('strategy', {})
    actions = strat.get('actions', [])
    combo_strats = strat.get('strategy', {})

    if not actions or not combo_strats:
        return {}

    check_idx = actions.index('CHECK') if 'CHECK' in actions else None

    size_totals = {a: 0.0 for a in actions if a != 'CHECK'}
    combo_count = 0

    for combo, probs in combo_strats.items():
        cbet_prob = 1.0 - (probs[check_idx] if check_idx is not None else 0.0)
        if cbet_prob < 0.01:
            continue
        combo_count += 1
        for i, a in enumerate(actions):
            if a != 'CHECK':
                size_totals[a] += probs[i] / cbet_prob if cbet_prob > 0 else 0.0

    if combo_count == 0:
        return {}

    # Normalize
    result = {}
    for a, total in size_totals.items():
        result[a] = round((total / combo_count) * 100, 1)

    return result


if __name__ == '__main__':
    os.makedirs(OUT_DIR, exist_ok=True)

    results = []
    for label, board, category, desc in SCENARIOS:
        r = run_scenario(label, board, category, desc)
        if r:
            results.append(r)

    summary = {
        'total': len(SCENARIOS),
        'completed': len(results),
        'results': results,
    }

    with open(os.path.join(OUT_DIR, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f'\nCompleted {len(results)}/{len(SCENARIOS)} scenarios')

    # Print summary table
    print()
    print(f'{"Label":<15} {"Category":<12} {"CBet%":>6} {"33%":>6} {"50%":>6} {"75%":>6} {"150%":>6} {"Allin":>6}')
    print('-' * 75)
    for r in results:
        dist = r.get('bet_size_distribution', {})
        def g(key_part):
            for k, v in dist.items():
                if key_part in k:
                    return f'{v:.0f}%'
            return '-'
        print(f'{r["label"]:<15} {r["turn_category"]:<12} {r["turn_cbet_pct"]:>5.1f}% '
              f'{g("33"):>6} {g("50"):>6} {g("75"):>6} {g("150"):>6} {g("ALLIN"):>6}')
