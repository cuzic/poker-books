#!/usr/bin/env python3
"""境界ペア6ボードのGTO分析スクリプト.

BTN(IP) vs BB(OOP), SRP のフロップ CBet 戦略を TexasSolver で分析する。

対象ボード:
  1. Qc,7d,2h  型1・全開モード
  2. Jc,7d,2h  型4・撤退モード
  3. Kc,9d,3h  型2・狙い撃ちモード
  4. Kc,8d,3h  型1・全開モード
  5. Qc,Qd,8h  型6・全開33%
  6. Qc,Qd,7h  型7・中程度モード
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

# ─── 設定 ──────────────────────────────────────────────────────────────────
SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
OUT_DIR = Path("/home/cuzic/poker-books/knowledges/flop/results/boundary_analysis")

POT   = 7    # BTN 3.5x open → BB call → flop pot = 7bb
STACK = 97   # 残スタック (effective_stack)

# BTN(IP) 6-max open range
IP_RANGE = (
    "AA,KK,QQ,JJ,TT,99,88,77,66,55,44,33,22,"
    "AKs,AKo,AQs,AQo,AJs,AJo,ATs,ATo,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "KQs,KQo,KJs,KJo,KTs,KTo,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "QJs,QJo,QTs,QTo,Q9s,Q8s,Q7s,Q6s,"
    "JTs,JTo,J9s,J8s,J7s,"
    "T9s,T8s,T7s,"
    "98s,97s,"
    "87s,86s,"
    "76s,75s,"
    "65s,54s"
)

# BB(OOP) defend range
OOP_RANGE = (
    "JJ,TT,99,88,77,66,55,44,33,22,"
    "AQs,AJs,ATs,A9s,A8s,A7s,A6s,A5s,A4s,A3s,A2s,"
    "AQo,AJo,ATo,"
    "KQs,KJs,KTs,K9s,K8s,K7s,K6s,K5s,K4s,K3s,K2s,"
    "KQo,KJo,KTo,"
    "QJs,QTs,Q9s,Q8s,Q7s,Q6s,"
    "QJo,QTo,"
    "JTs,J9s,J8s,"
    "JTo,"
    "T9s,T8s,T7s,"
    "T9o,"
    "98s,97s,96s,"
    "87s,86s,"
    "76s,75s,"
    "65s,54s,43s"
)

CONFIG_TEMPLATE = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,flop,bet,60,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes ip,flop,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 0.5
set_max_iteration 400
set_print_interval 100
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""

# TexasSolver のツリー構造 (実測で確認):
# Root node (player=1 = OOP/BB): OOP が先に check または donk bet
#   → root['childrens']['CHECK'] = IP が CBet または check する IP アクションノード
#   → root['childrens']['BET 4'] = OOP donk 4 に IP が応答するノード
#
# CHECK child (player=0 = IP/BTN): OOP check 後に IP が行動
#   Actions: CHECK, BET 2(≈33%), BET 4(≈50%), BET 5(≈75%), BET 97(allin)
#   Strategy combos: IP (BTN) のハンドレンジ (AA/KK/QQ 含む)
#   → ここで IP CBet 率を計算する
#
# CHECK→BETx child (player=1 = OOP/BB): IP の CBet に OOP が応答
#   Strategy combos: OOP (BB) のハンドレンジ
#   Actions: FOLD, CALL, RAISE → フォールド率を計算する

# IP bet sizes at CHECK node (pot=7, configured 33/50/75):
# BET 2 = 2/7 ≈ 29%pot (= round(7*0.33) = round(2.31) = 2)
# BET 4 = 4/7 ≈ 57%pot (= round(7*0.50) = round(3.5) = 4)
# BET 5 = 5/7 ≈ 71%pot (= round(7*0.75) = round(5.25) = 5)
IP_BET_SIZES = {
    "33": 2.0,   # ≈29%pot
    "50": 4.0,   # ≈57%pot
    "75": 5.0,   # ≈71%pot
}

# 分析対象ボード
BOARDS = [
    ("Qc,7d,2h", "q72r", "型1・全開モード"),
    ("Jc,7d,2h", "j72r", "型4・撤退モード"),
    ("Kc,9d,3h", "k93r", "型2・狙い撃ちモード"),
    ("Kc,8d,3h", "k83r", "型1・全開モード"),
    ("Qc,Qd,8h", "qq8r", "型6・全開33%"),
    ("Qc,Qd,7h", "qq7r", "型7・中程度モード"),
]

RANK_MAP = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
}


# ─── ソルバー実行 ────────────────────────────────────────────────────────────
def run_solver(board: str, dump_path: str, timeout: int = 600) -> int:
    config = CONFIG_TEMPLATE.format(
        pot=POT, stack=STACK, board=board,
        ip_range=IP_RANGE, oop_range=OOP_RANGE,
        dump_path=dump_path,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(config)
        cfg = f.name
    try:
        with open(cfg) as fin:
            proc = subprocess.Popen(
                [SOLVER_BIN], stdin=fin,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
            )
            try:
                return proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill(); proc.wait(); return -1
    finally:
        try:
            os.unlink(cfg)
        except OSError:
            pass


# ─── ボード情報 ──────────────────────────────────────────────────────────────
def board_ranks(board: str) -> list[int]:
    """ボードカードのランク（降順）."""
    return sorted([RANK_MAP[c[0].upper()] for c in board.split(",")], reverse=True)


def board_rank_set(board: str) -> set[int]:
    return set(RANK_MAP[c[0].upper()] for c in board.split(","))


def board_suits(board: str) -> list[str]:
    return [c[1].lower() for c in board.split(",")]


def is_paired_board(board: str) -> bool:
    ranks = board_ranks(board)
    return len(set(ranks)) < len(ranks)


# ─── ノード取得ヘルパー ─────────────────────────────────────────────────────
def get_ip_cbet_node(raw: dict) -> dict | None:
    """root(OOP acts first) → CHECK child = IP が CBet する節点."""
    return raw.get("childrens", {}).get("CHECK")


def find_best_bet_node(children: dict, target_amt: float, tolerance: float = 1.5) -> tuple[str | None, dict | None]:
    """target_amt に最も近い BET 子ノードを返す."""
    best_key = None
    best_node = None
    best_diff = float("inf")
    for key, node in children.items():
        if not key.startswith("BET"):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        diff = abs(amt - target_amt)
        if diff < tolerance and diff < best_diff:
            best_diff = diff
            best_key = key
            best_node = node
    return best_key, best_node


# ─── IP CBet 率の計算 ────────────────────────────────────────────────────────
def compute_ip_cbet_total(raw: dict) -> dict:
    """IP(BTN) の CBet 率を CHECK ノードから計算する.

    TexasSolver ツリー構造:
      root (OOP acts) → CHECK → IP acts here (IP range combos)
    """
    ip_node = get_ip_cbet_node(raw)
    if ip_node is None:
        return {"error": "CHECK node not found"}

    strat = ip_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        chk_idx = actions.index("CHECK")
    except ValueError:
        return {"error": "CHECK not in actions"}

    # 各アクションの合計確率（全コンボ平均）
    action_totals = [0.0] * len(actions)
    n_combos = 0
    for combo, probs in combos.items():
        n_combos += 1
        for i, p in enumerate(probs):
            if i < len(action_totals):
                action_totals[i] += p

    if n_combos == 0:
        return {"error": "no combos"}

    avg_probs = [t / n_combos for t in action_totals]
    check_pct = avg_probs[chk_idx] * 100

    # CBet = BET の合計
    bet_probs: dict[str, float] = {}
    for i, act in enumerate(actions):
        if act.startswith("BET"):
            bet_probs[act] = avg_probs[i] * 100

    total_cbet = sum(bet_probs.values())
    top_bet = max(bet_probs, key=bet_probs.get) if bet_probs else None

    # top_bet からサイズラベルを付与
    top_size_label = "?"
    if top_bet:
        try:
            amt = float(top_bet.split()[1])
            if amt >= STACK * 0.9:
                top_size_label = "allin"
            elif abs(amt - IP_BET_SIZES["33"]) <= 0.5:
                top_size_label = "33%(BET2)"
            elif abs(amt - IP_BET_SIZES["50"]) <= 0.5:
                top_size_label = "50%(BET4)"
            elif abs(amt - IP_BET_SIZES["75"]) <= 0.5:
                top_size_label = "75%(BET5)"
            else:
                approx_pct = round(amt / POT * 100)
                top_size_label = f"{approx_pct}%pot"
        except (IndexError, ValueError):
            pass

    return {
        "total_cbet_pct": round(total_cbet, 1),
        "check_pct": round(check_pct, 1),
        "bet_breakdown": {k: round(v, 1) for k, v in bet_probs.items()},
        "top_bet_key": top_bet,
        "top_bet_label": top_size_label,
        "n_combos": n_combos,
    }


# ─── BB フォールド率の計算 ───────────────────────────────────────────────────
def compute_bb_fold_vs_cbet(raw: dict, config_pct: int) -> dict:
    """BTN が config_pct% CBet した後の BB 全コンボ平均フォールド率.

    TexasSolver ツリー:
      root(OOP) → CHECK(IP acts) → BETx(OOP responds here)
    config_pct は 33/50/75 のいずれか。
    対応する実際の bet 額: IP_BET_SIZES[str(config_pct)]
    """
    ip_node = get_ip_cbet_node(raw)
    if ip_node is None:
        return {"error": "CHECK node not found"}

    target_amt = IP_BET_SIZES.get(str(config_pct), POT * config_pct / 100.0)
    key, bet_node = find_best_bet_node(ip_node.get("childrens", {}), target_amt)

    if bet_node is None:
        all_bet_keys = [k for k in ip_node.get("childrens", {}) if k.startswith("BET")]
        if not all_bet_keys:
            return {"error": f"no BET nodes under CHECK", "config_pct": config_pct}
        all_bet_keys.sort(key=lambda k: abs(float(k.split()[1]) - target_amt))
        key = all_bet_keys[0]
        bet_node = ip_node["childrens"][key]

    strat = bet_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        fold_idx = actions.index("FOLD")
    except ValueError:
        return {"error": f"FOLD not in {actions}", "key_used": key}

    folds = []
    for combo, probs in combos.items():
        if fold_idx < len(probs):
            folds.append(probs[fold_idx])

    if not folds:
        return {"error": "no combos", "key_used": key}

    avg_fold = sum(folds) / len(folds)
    return {
        "key_used": key,
        "actual_bet_amt": float(key.split()[1]),
        "avg_fold_pct": round(avg_fold * 100, 1),
        "n_combos": len(folds),
    }


# ─── ハンド強度別 CBet 率 ─────────────────────────────────────────────────────
def combo_rank(combo: str) -> tuple[int, int]:
    r0 = RANK_MAP.get(combo[0].upper(), 0)
    r1 = RANK_MAP.get(combo[2].upper(), 0)
    return (max(r0, r1), min(r0, r1))


def classify_combo(combo: str, board: str) -> str:
    """コンボのハンド強度カテゴリを返す."""
    b_ranks = board_ranks(board)
    b_rank_set = board_rank_set(board)
    b_suits = board_suits(board)
    b_is_paired = is_paired_board(board)

    r0 = RANK_MAP.get(combo[0].upper(), 0)
    r1 = RANK_MAP.get(combo[2].upper(), 0)
    s0 = combo[1].lower()
    s1 = combo[3].lower()

    # ポケットペア判定
    is_pocket_pair = (r0 == r1)

    # ボード上の最高ランク
    top_board = b_ranks[0]
    mid_board = b_ranks[1] if len(b_ranks) > 1 else 0

    # ペアボード対応
    if b_is_paired:
        # ペアボードでのトリップス
        pair_rank = next(r for r in b_ranks if b_ranks.count(r) >= 2)
        if r0 == pair_rank or r1 == pair_rank:
            return "trips"
        if is_pocket_pair and r0 > top_board:
            return "overpair"
        if is_pocket_pair and r0 == top_board:
            return "top_set"  # フルハウス
        # トップペア (非ペアランクとペア)
        non_pair_ranks = [r for r in b_ranks if r != pair_rank]
        if non_pair_ranks:
            top_non_pair = non_pair_ranks[0]
            if r0 == top_non_pair or r1 == top_non_pair:
                return "top_pair"
        return "air"

    # 通常ボード
    # セット
    if is_pocket_pair and r0 in b_rank_set:
        return "set"

    # オーバーペア
    if is_pocket_pair and r0 > top_board:
        return "overpair"

    # アンダーペア (ボード最大ランク未満のポケットペア)
    if is_pocket_pair and r0 < top_board and r0 not in b_rank_set:
        return "underpair"

    # トップペア
    hits_top = (r0 == top_board or r1 == top_board)
    if hits_top:
        top_kicker = max(r for r in [r0, r1] if r != top_board) if r0 != r1 else top_board
        # TPTKの目安: キッカーがトップ5(AKQJTのいずれか)
        if top_kicker >= 10:
            return "tptk"
        return "top_pair"

    # ミドルペア
    hits_mid = (r0 == mid_board or r1 == mid_board)
    if hits_mid:
        return "middle_pair"

    # オーバーカード2枚 (エア)
    if r0 > top_board and r1 > top_board and not is_pocket_pair:
        return "2oc"

    # エア
    return "air"


def compute_cbet_by_category(raw: dict, board: str) -> dict[str, dict]:
    """IP(BTN)のカテゴリ別CBet率を CHECK ノードから計算."""
    ip_node = get_ip_cbet_node(raw)
    if ip_node is None:
        return {}
    strat = ip_node.get("strategy", {})
    actions: list[str] = strat.get("actions", [])
    combos: dict[str, list[float]] = strat.get("strategy", {})

    try:
        chk_idx = actions.index("CHECK")
    except ValueError:
        return {}

    categories: dict[str, list[float]] = {}
    for combo, probs in combos.items():
        cat = classify_combo(combo, board)
        cbet = 1.0 - probs[chk_idx] if chk_idx < len(probs) else 1.0
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(cbet)

    result: dict[str, dict] = {}
    for cat, vals in categories.items():
        result[cat] = {
            "avg_cbet_pct": round(sum(vals) / len(vals) * 100, 1),
            "n": len(vals),
        }
    return result


# ─── メイン ─────────────────────────────────────────────────────────────────
def analyze_board(board: str, slug: str) -> dict:
    dump_path = str(OUT_DIR / f"{slug}.json")

    if Path(dump_path).exists():
        print(f"  キャッシュ済み: {dump_path}")
    else:
        print(f"  TexasSolver 実行中 (Board: {board}) ...")
        t0 = time.time()
        rc = run_solver(board, dump_path)
        elapsed = time.time() - t0
        if rc != 0 or not Path(dump_path).exists():
            print(f"  ERROR: solver rc={rc}")
            return {}
        print(f"  完了: {elapsed:.0f}s")

    raw: Any = json.loads(Path(dump_path).read_text())

    # 1. BTN全体CBet率
    cbet_info = compute_ip_cbet_total(raw)

    # 2. BBフォールド率 (CHECK→BETx→OOP response)
    bb_fold_33 = compute_bb_fold_vs_cbet(raw, 33)   # BET 2 (≈33%) を検索
    bb_fold_75 = compute_bb_fold_vs_cbet(raw, 75)   # BET 5 (≈75%) を検索

    # 3. ハンド強度別CBet率
    cat_cbet = compute_cbet_by_category(raw, board)

    result = {
        "board": board,
        "slug": slug,
        "cbet": cbet_info,
        "bb_fold_vs_33pct": bb_fold_33,
        "bb_fold_vs_75pct": bb_fold_75,
        "cbet_by_category": cat_cbet,
    }

    # save enriched result back
    Path(dump_path.replace(".json", "_analysis.json")).write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def print_results(results: list[tuple[str, str, str, dict]]) -> None:
    print()
    print("=" * 85)
    print("境界ペア6ボード CBet 分析結果 (BTN vs BB, SRP, pot=7, stack=97)")
    print("=" * 85)

    # ── テーブル1: CBet 概要 ──
    print()
    print("【テーブル1: BTN CBet 率と BB フォールド率】")
    # IP bet sizes (from CHECK node): BET2(≈33%), BET4(≈50%), BET5(≈75%)
    print(f"{'ボード':<14} {'タイプ':<16} {'CBet%':>7} {'最頻サイズ':>14} {'BBfold@33%':>11} {'BBfold@75%':>11}")
    print(f"{'':14} {'':16} {'':7} {'':14} {'(BET2)':>11} {'(BET5)':>11}")
    print("-" * 80)
    for board, slug, label, r in results:
        if not r:
            print(f"  {board:<12} {'ERROR'}")
            continue
        c = r.get("cbet", {})
        f33 = r.get("bb_fold_vs_33pct", {})
        f75 = r.get("bb_fold_vs_75pct", {})
        cbet_pct = c.get("total_cbet_pct", "?")
        top_label = c.get("top_bet_label", "?")
        fold33 = f33.get("avg_fold_pct", "?")
        fold75 = f75.get("avg_fold_pct", "?")
        print(f"  {board:<12} {label:<16} {cbet_pct:>7} {top_label:>14} {fold33:>10}% {fold75:>10}%")

    # ── テーブル2: カテゴリ別 CBet 率 ──
    print()
    print("【テーブル2: ハンド強度別 BTN CBet 率】")
    cats = ["overpair", "underpair", "tptk", "top_pair", "middle_pair", "2oc", "air", "set", "trips"]
    header = f"{'ボード':<14}"
    for cat in cats:
        header += f" {cat[:8]:>9}"
    print(header)
    print("-" * (14 + 10 * len(cats)))
    for board, slug, label, r in results:
        if not r:
            continue
        cat_data = r.get("cbet_by_category", {})
        row = f"  {board:<12}"
        for cat in cats:
            d = cat_data.get(cat, {})
            pct = d.get("avg_cbet_pct")
            if pct is None:
                row += f" {'---':>9}"
            else:
                row += f" {pct:>8.1f}%"
        print(row)

    # ── テーブル3: ボード間差分 ──
    print()
    print("【テーブル3: 境界ボード差分】")
    pairs = [
        ("Q72 vs J72", "q72r", "j72r", "高カードQ(型1)vs J(型4)"),
        ("K93 vs K83", "k93r", "k83r", "9(型2)vs 8(型1)セカンドカード差"),
        ("QQ8 vs QQ7", "qq8r", "qq7r", "ペアボード: 8(型6)vs 7(型7)"),
    ]
    result_map = {slug: r for _, slug, _, r in results}
    print(f"{'比較':<28} {'CBet差':>8} {'BBfold@33%差':>13}")
    print("-" * 55)
    for pair_name, slug_a, slug_b, desc in pairs:
        ra = result_map.get(slug_a, {})
        rb = result_map.get(slug_b, {})
        if not ra or not rb:
            print(f"  {pair_name}: データなし")
            continue
        ca = ra.get("cbet", {}).get("total_cbet_pct", 0)
        cb = rb.get("cbet", {}).get("total_cbet_pct", 0)
        fa = ra.get("bb_fold_vs_33pct", {}).get("avg_fold_pct", 0)
        fb = rb.get("bb_fold_vs_33pct", {}).get("avg_fold_pct", 0)
        diff_cbet = ca - cb if isinstance(ca, (int, float)) and isinstance(cb, (int, float)) else "?"
        diff_fold = fa - fb if isinstance(fa, (int, float)) and isinstance(fb, (int, float)) else "?"
        if isinstance(diff_cbet, float):
            diff_cbet = round(diff_cbet, 1)
        if isinstance(diff_fold, float):
            diff_fold = round(diff_fold, 1)
        print(f"  {pair_name:<28} {diff_cbet:>+7}% {diff_fold:>+12}%")
        print(f"    ({desc})")

    # ── テーブル4: ベット内訳 ──
    print()
    print("【テーブル4: BTN ベットサイズ内訳 (%)】")
    for board, slug, label, r in results:
        if not r:
            continue
        c = r.get("cbet", {})
        breakdown = c.get("bet_breakdown", {})
        print(f"  {board} ({label}):")
        for k, v in sorted(breakdown.items(), key=lambda x: float(x[0].split()[1])):
            amt = float(k.split()[1])
            if amt >= STACK * 0.9:
                size_desc = "allin(BET97)"
            elif abs(amt - IP_BET_SIZES["33"]) <= 0.5:
                size_desc = f"~33%(BET{int(amt)})"
            elif abs(amt - IP_BET_SIZES["50"]) <= 0.5:
                size_desc = f"~50%(BET{int(amt)})"
            elif abs(amt - IP_BET_SIZES["75"]) <= 0.5:
                size_desc = f"~75%(BET{int(amt)})"
            else:
                approx_pct = round(amt / POT * 100)
                size_desc = f"{approx_pct}%pot(BET{int(amt)})"
            print(f"    {k} ({size_desc}): {v:.1f}%")
        print()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"TexasSolver 境界ペア6ボード分析")
    print(f"pot={POT}, stack={STACK}, accuracy=0.5, max_iter=400")
    print()

    all_results: list[tuple[str, str, str, dict]] = []
    for board, slug, label in BOARDS:
        print(f"[{slug}] {board} ({label})")
        r = analyze_board(board, slug)
        all_results.append((board, slug, label, r))

    print_results(all_results)

    # 全ボードの集計を一つのJSONに保存
    summary = {entry[1]: entry[3] for entry in all_results if entry[3]}
    summary_path = OUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\n集計: {summary_path}")


if __name__ == "__main__":
    main()
