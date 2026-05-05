#!/usr/bin/env python3
"""3BPシナリオ検証スクリプト — TexasSolver パイプライン.

検証内容:
  A) K72r 3BP フロップ: OOP後手スコア = HandScore + A − 3 − C の検証
  B) K72r+3h ターン: SPR≈2.7 でのIP CBet頻度 (~100%) の検証
  C) スクイーズEV: 理論的検証 (TexasSolverは使用しない)

使用方法:
    python3 scripts/texassolver_3bp_verify.py [--skip-a] [--skip-b]

出力:
    knowledges/volume4/results/3bp_verify/scenario_A.json
    knowledges/volume4/results/3bp_verify/scenario_B.json
    knowledges/volume4/results/3bp_verify/summary.json
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
from typing import Any

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

SOLVER_BIN = "/home/cuzic/TexasSolver/build/console_solver"
SOLVER_DIR = "/home/cuzic/TexasSolver"
RESULTS_DIR = Path("/home/cuzic/poker-books/knowledges/volume4/results/3bp_verify")

TIMEOUT = 180  # 秒 (3分)

# ---------------------------------------------------------------------------
# シナリオ A: K72r 3BP フロップ
# ポット: 19bb, スタック: 91bb
# IP (BTN calling 3bet): JJ,TT,99,88,AQs,AQo,AJs,KQs,KJs,QJs,JTs,T9s
# OOP (BB 3bet):         AA,KK,QQ,AKs,AKo,A5s,A4s,A3s,A2s,76s,65s
# ボード: Kc,7d,2s
# IP ベット: 33%,50%,75%,allin; OOP ベット: 50%,100%,allin
# ---------------------------------------------------------------------------

SCENARIO_A_IP_RANGE = "JJ,TT,99,88,AQs,AQo,AJs,KQs,KJs,QJs,JTs,T9s"
SCENARIO_A_OOP_RANGE = "AA,KK,QQ,AKs,AKo,A5s,A4s,A3s,A2s,76s,65s"
SCENARIO_A_BOARD = "Kc,7d,2s"
SCENARIO_A_POT = 19
SCENARIO_A_STACK = 91

# Kc,7d,2s は「フロップ完結ツリー」: IP がファーストアクション
# TexasSolver の set_board に 3 枚のみ渡すとフロップツリーを構築する
# root は OOP (player=1) のチェック/ベットから始まる
# → OOP check 後の IP ベット に対する OOP レスポンスを解析する
SCENARIO_A_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes ip,flop,bet,33,50,75
set_bet_sizes ip,flop,allin
set_bet_sizes oop,flop,bet,50,100
set_bet_sizes oop,flop,allin
set_bet_sizes ip,turn,bet,50
set_bet_sizes ip,turn,allin
set_bet_sizes oop,turn,bet,50
set_bet_sizes oop,turn,allin
set_bet_sizes ip,river,bet,50
set_bet_sizes ip,river,allin
set_bet_sizes oop,river,bet,50
set_bet_sizes oop,river,allin
set_allin_threshold 0.67
build_tree
set_thread_num 8
set_accuracy 1.0
set_max_iteration 150
set_print_interval 50
set_dump_rounds 1
start_solve
dump_result {dump_path}
"""

# ---------------------------------------------------------------------------
# シナリオ B: K72r+3h ターン (SPR≈2.7)
# ポット: 31.3bb, スタック: 84.7bb
# IP (BTN, 3BP CBetter): AA,KK,QQ,JJ,TT,99,88,AKs,AQs,AJs,KQs
# OOP (BB, 3BP caller):  QQ,JJ,TT,99,88,AJs,ATs,KQs,KJs,QJs
# ボード: Kc,7d,2s,3h
# ---------------------------------------------------------------------------

SCENARIO_B_IP_RANGE = "AA,KK,QQ,JJ,TT,99,88,AKs,AQs,AJs,KQs"
SCENARIO_B_OOP_RANGE = "QQ,JJ,TT,99,88,AJs,ATs,KQs,KJs,QJs"
SCENARIO_B_BOARD = "Kc,7d,2s,3h"
SCENARIO_B_POT = 31  # 31.3 を整数近似
SCENARIO_B_STACK = 85  # 84.7 を整数近似

SCENARIO_B_CONFIG = """\
set_pot {pot}
set_effective_stack {stack}
set_board {board}
set_range_ip {ip_range}
set_range_oop {oop_range}
set_bet_sizes oop,turn,bet,50
set_bet_sizes oop,turn,allin
set_bet_sizes ip,turn,bet,33,50,75
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
dump_result {dump_path}
"""

# ---------------------------------------------------------------------------
# ソルバー実行ユーティリティ
# ---------------------------------------------------------------------------


def run_solver(config_text: str, timeout: int = TIMEOUT) -> tuple[str, float | None, int]:
    """TexasSolverを実行し (dump_path, exploitability, returncode) を返す."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ts_3bp_cfg_"
    ) as f:
        f.write(config_text)
        cfg_path = f.name

    stdout_file = cfg_path.replace("ts_3bp_cfg_", "ts_3bp_stdout_")
    dump_path = cfg_path.replace("ts_3bp_cfg_", "ts_3bp_dump_").replace(".txt", ".json")

    # config_text に dump_path を埋め込む (既に format 済み)
    # → dump_path は config_text 内で指定済み

    try:
        with open(cfg_path) as fin, open(stdout_file, "w") as fout:
            proc = subprocess.Popen(
                [SOLVER_BIN],
                stdin=fin,
                stdout=fout,
                stderr=subprocess.DEVNULL,
                cwd=SOLVER_DIR,
            )
            try:
                rc = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                rc = -1
    finally:
        try:
            os.unlink(cfg_path)
        except OSError:
            pass

    exploitability = _parse_exploitability(stdout_file)
    try:
        os.unlink(stdout_file)
    except OSError:
        pass

    return dump_path, exploitability, rc


def _parse_exploitability(stdout_path: str) -> float | None:
    last_val = None
    try:
        with open(stdout_path, "rb") as f:
            content = f.read()
        for line in content.decode("utf-8", errors="replace").splitlines():
            line = line.strip()
            if "Total exploitability" in line and "precent" in line:
                try:
                    parts = line.split()
                    idx = parts.index("exploitability") + 1
                    last_val = float(parts[idx])
                except (IndexError, ValueError):
                    pass
    except OSError:
        pass
    return last_val


def solve(label: str, config_text: str, timeout: int = TIMEOUT) -> tuple[dict | None, float | None]:
    """ソルバーを実行し (result_json, exploitability) を返す. 失敗時は (None, None)."""
    print(f"  [{label}] TexasSolverを実行中...", flush=True)
    t0 = time.time()
    dump_path, exploit, rc = run_solver(config_text, timeout=timeout)
    elapsed = time.time() - t0
    print(f"  [{label}] rc={rc}, exploit={exploit}, elapsed={elapsed:.0f}s")

    if rc == -1:
        print(f"  [{label}] TIMEOUT")
        return None, exploit
    if rc != 0:
        print(f"  [{label}] ERROR rc={rc}")
        return None, exploit
    if not os.path.exists(dump_path):
        print(f"  [{label}] dump file not found: {dump_path}")
        return None, exploit

    try:
        with open(dump_path) as f:
            data = json.load(f)
        os.unlink(dump_path)
        return data, exploit
    except Exception as e:
        print(f"  [{label}] JSON parse error: {e}")
        return None, exploit

# ---------------------------------------------------------------------------
# シナリオ A: OOP レスポンス解析
#
# ツリー構造 (3枚ボード = フロップ完結):
#   root: OOP (player=1) → CHECK or BET
#   root.CHECK → IP (player=0) → CHECK or BET33 or BET50 or BET75 ...
#   root.CHECK.BET_33 → OOP (player=1) → CALL / RAISE / FOLD
# ---------------------------------------------------------------------------


def analyze_scenario_a(result_json: dict) -> dict:
    """K72r 3BP フロップ: OOP の各アクション頻度と特定コンボを解析."""
    analysis = {}

    # root は OOP アクション (player=1)
    root_player = result_json.get("player")
    root_actions = result_json.get("actions", [])
    print(f"  root player={root_player}, actions={root_actions}")

    children = result_json.get("childrens", {})

    # OOP CHECK → IP BET 33% → OOP response を探す
    check_node = children.get("CHECK")
    if check_node is None:
        # root がすでに IP のノードかもしれない
        # player=0 なら IP が先
        if root_player == 0:
            ip_node = result_json
            print("  root is IP node directly")
        else:
            print("  ERROR: no CHECK node in root OOP")
            return {"error": "no CHECK node"}
    else:
        ip_node = check_node

    ip_children = ip_node.get("childrens", {})
    ip_actions = ip_node.get("actions", [])
    print(f"  IP node actions: {ip_actions}")

    # IP BET 33% ノードを探す (33% of pot=19 ≈ 6.3bb)
    bet33_key = None
    for k in ip_children:
        if "BET" in k:
            # 33% of 19 ≈ 6.3
            try:
                amt = float(k.split()[-1])
                if 5.0 <= amt <= 8.0:
                    bet33_key = k
                    break
            except ValueError:
                pass

    if bet33_key is None:
        # fallback: 最小ベットを使う
        bet_keys = [k for k in ip_children if "BET" in k]
        if bet_keys:
            bet33_key = sorted(bet_keys, key=lambda k: float(k.split()[-1]))[0]

    print(f"  Using IP bet key: {bet33_key}")

    if bet33_key is None:
        print(f"  Available IP children: {list(ip_children.keys())}")
        return {"error": "no BET node for IP 33%", "ip_actions": ip_actions}

    # OOP response ノード (OOP が call/raise/fold を選ぶ)
    oop_response_node = ip_children[bet33_key]
    oop_resp_strat = oop_response_node.get("strategy", {})
    oop_resp_actions = oop_resp_strat.get("actions", [])
    oop_resp_combos = oop_resp_strat.get("strategy", {})

    print(f"  OOP response actions: {oop_resp_actions}")

    if not oop_resp_actions or not oop_resp_combos:
        return {"error": "empty OOP response strategy", "bet33_key": bet33_key}

    # --- 全コンボ平均 ---
    call_idx = next((i for i, a in enumerate(oop_resp_actions) if a == "CALL"), None)
    fold_idx = next((i for i, a in enumerate(oop_resp_actions) if a == "FOLD"), None)
    raise_idxs = [i for i, a in enumerate(oop_resp_actions) if "RAISE" in a or "BET" in a]

    total_call = 0.0
    total_fold = 0.0
    total_raise = 0.0
    n = 0
    for probs in oop_resp_combos.values():
        if call_idx is not None and call_idx < len(probs):
            total_call += probs[call_idx]
        if fold_idx is not None and fold_idx < len(probs):
            total_fold += probs[fold_idx]
        for ri in raise_idxs:
            if ri < len(probs):
                total_raise += probs[ri]
        n += 1

    avg_call = (total_call / n * 100) if n > 0 else 0.0
    avg_fold = (total_fold / n * 100) if n > 0 else 0.0
    avg_raise = (total_raise / n * 100) if n > 0 else 0.0

    analysis["bet33_key"] = bet33_key
    analysis["oop_response_actions"] = oop_resp_actions
    analysis["avg_call_pct"] = round(avg_call, 1)
    analysis["avg_fold_pct"] = round(avg_fold, 1)
    analysis["avg_raise_pct"] = round(avg_raise, 1)

    # シンプルなマッピング (スーテッドペアのみ)
    target_combos_simple = {
        "AA": ["AhAd", "AhAc", "AdAc"],
        "KK": ["KhKd", "KhKc", "KdKc"],
        "QQ": ["QhQd", "QhQc", "QdQc"],
        "AKs": ["AhKh", "AdKd", "AcKc"],
        "AKo": ["AhKd", "AhKc", "AdKh", "AdKc"],
        "A5s": ["Ah5h", "Ad5d", "Ac5c"],
        "A4s": ["Ah4h", "Ad4d", "Ac4c"],
    }

    combo_results = {}
    available_combos = set(oop_resp_combos.keys())

    for hand_name, combos_list in target_combos_simple.items():
        found = []
        for c in combos_list:
            if c in available_combos:
                found.append(c)
            # TexasSolver は順序が逆の場合もある
            c_rev = c[2:] + c[:2] if len(c) == 4 else None
            if c_rev and c_rev in available_combos:
                found.append(c_rev)

        if not found:
            # パターンマッチ (先頭2文字で検索)
            ranks = hand_name[:2]
            if hand_name[-1] == "s":  # スーテッド
                r1, r2 = ranks[0], ranks[1]
                found = [c for c in available_combos
                         if len(c) == 4 and c[0] == r1 and c[2] == r2 and c[1] == c[3]]
            elif hand_name[-1] == "o":  # オフスート
                r1, r2 = ranks[0], ranks[1]
                found = [c for c in available_combos
                         if len(c) == 4 and c[0] == r1 and c[2] == r2 and c[1] != c[3]]
            else:  # ペア
                r = ranks[0]
                found = [c for c in available_combos
                         if len(c) == 4 and c[0] == r and c[2] == r]

        if not found:
            combo_results[hand_name] = {"note": "combo not found in strategy"}
            continue

        call_tot = fold_tot = raise_tot = 0.0
        cnt = 0
        for c in found:
            probs = oop_resp_combos.get(c, [])
            if not probs:
                continue
            if call_idx is not None and call_idx < len(probs):
                call_tot += probs[call_idx]
            if fold_idx is not None and fold_idx < len(probs):
                fold_tot += probs[fold_idx]
            for ri in raise_idxs:
                if ri < len(probs):
                    raise_tot += probs[ri]
            cnt += 1

        if cnt > 0:
            combo_results[hand_name] = {
                "combos": found[:3],
                "n": cnt,
                "call_pct": round(call_tot / cnt * 100, 1),
                "fold_pct": round(fold_tot / cnt * 100, 1),
                "raise_pct": round(raise_tot / cnt * 100, 1),
            }
        else:
            combo_results[hand_name] = {"note": "no valid probs"}

    analysis["combo_analysis"] = combo_results
    return analysis


# ---------------------------------------------------------------------------
# シナリオ B: IP ターン CBet 頻度解析
#
# ツリー構造 (4枚ボード = ターン+リバーツリー):
#   root: OOP (player=1) → CHECK or BET
#   root.CHECK → IP (player=0) → CHECK or BET33 or BET50 ...
#   IP ベット頻度 = 1 - IP CHECK 頻度
# ---------------------------------------------------------------------------


def analyze_scenario_b(result_json: dict) -> dict:
    """K72r+3h ターン: IPのCBet頻度を解析."""
    root_player = result_json.get("player")
    root_actions = result_json.get("actions", [])
    print(f"  root player={root_player}, actions={root_actions}")

    children = result_json.get("childrens", {})

    # root は OOP (player=1)
    check_node = children.get("CHECK")
    if check_node is None:
        if root_player == 0:
            # IPが先のノード
            ip_node = result_json
        else:
            return {"error": "no CHECK node at OOP root"}
    else:
        ip_node = check_node

    ip_strat_wrapper = ip_node.get("strategy", {})
    ip_actions = ip_strat_wrapper.get("actions", [])
    ip_combos = ip_strat_wrapper.get("strategy", {})

    print(f"  IP node actions: {ip_actions}")

    if not ip_actions or not ip_combos:
        return {"error": "empty IP strategy"}

    check_idx = next((i for i, a in enumerate(ip_actions) if a == "CHECK"), None)

    total_cbet = 0.0
    n = 0
    for probs in ip_combos.values():
        if check_idx is not None and check_idx < len(probs):
            total_cbet += (1.0 - probs[check_idx])
        else:
            total_cbet += 1.0
        n += 1

    cbet_pct = (total_cbet / n * 100) if n > 0 else 0.0

    return {
        "ip_actions": ip_actions,
        "n_combos": n,
        "cbet_pct": round(cbet_pct, 1),
        "check_pct": round(100 - cbet_pct, 1),
    }


# ---------------------------------------------------------------------------
# シナリオ C: スクイーズ EV 理論計算
# ---------------------------------------------------------------------------


def squeeze_ev(
    raiser_bb: float,
    caller_bb: float,
    squeeze_size: float,
    fold_prob_raiser: float,
    fold_prob_caller: float,
) -> dict:
    """スクイーズのEV計算 (近似、GTO仮定なし).

    Args:
        raiser_bb: レイザーのレイズサイズ (bb)
        caller_bb: コーラーのコールサイズ (bb)
        squeeze_size: スクイーズサイズ (bb)
        fold_prob_raiser: レイザーがフォールドする確率
        fold_prob_caller: コーラーがフォールドする確率

    Returns:
        EV の内訳辞書
    """
    # ポット前 = ブラインド1.5bb + レイズ + コール
    # ここでは簡略化: dead_money = raiser_bb + caller_bb (既にポットにある分)
    dead_money = raiser_bb + caller_bb  # デッドマネー (SB 0.5bb は省略)
    pot_before_squeeze = dead_money  # スクイーズ前のポット

    # 相手がフォールドするシナリオ
    both_fold = fold_prob_raiser * fold_prob_caller
    raiser_calls_caller_folds = (1 - fold_prob_raiser) * fold_prob_caller
    raiser_folds_caller_calls = fold_prob_raiser * (1 - fold_prob_caller)
    both_call = (1 - fold_prob_raiser) * (1 - fold_prob_caller)

    # EV (スクイーズ投資額を差し引く前の獲得ポット)
    # 全員フォールド: dead_money を獲得
    ev_both_fold = both_fold * (pot_before_squeeze)
    # レイザーのみコール: ヘッズアップで継続 (equity≈0.5仮定)
    # → 正確には caller が fold するとその bb はポットに残る
    # ここではポット = dead_money + squeeze_size (caller folds, raiser calls)
    pot_if_raiser_calls = dead_money + squeeze_size  # caller_bb は既に dead_money に含む
    ev_raiser_calls = raiser_calls_caller_folds * (pot_if_raiser_calls * 0.5 - squeeze_size / 2)
    # コーラーのみコール
    pot_if_caller_calls = dead_money + squeeze_size  # raiser_bb は dead_money に含む
    ev_caller_calls = raiser_folds_caller_calls * (pot_if_caller_calls * 0.5 - squeeze_size / 2)
    # 両者コール: 3way (equity≈1/3仮定)
    pot_3way = dead_money + squeeze_size
    ev_3way = both_call * (pot_3way / 3 - squeeze_size)

    net_ev = ev_both_fold + ev_raiser_calls + ev_caller_calls + ev_3way

    return {
        "dead_money": dead_money,
        "pot_before": pot_before_squeeze,
        "squeeze_size": squeeze_size,
        "fold_prob_raiser": fold_prob_raiser,
        "fold_prob_caller": fold_prob_caller,
        "both_fold_prob": round(both_fold, 3),
        "ev_both_fold": round(ev_both_fold, 3),
        "ev_raiser_calls": round(ev_raiser_calls, 3),
        "ev_caller_calls": round(ev_caller_calls, 3),
        "ev_3way": round(ev_3way, 3),
        "net_ev": round(net_ev, 3),
    }


def analyze_scenario_c() -> dict:
    """スクイーズ閾値: コーラー1人でなぜ閾値が2下がるか定量的に示す."""

    # --- 通常 3bet (HU) ---
    # BTN open 2.5bb, BB 3bet 9bb
    # ポット: 2.5bb (BTN) + 0.5bb (SB, 省略) ≈ 3bb
    # BTN fold rate vs 3bet: ~55-65%, 典型値 60%
    hu_3bet_size = 9.0
    hu_raiser_bb = 2.5  # BTN open
    # BTN fold prob vs 3bet ≈ 0.60
    hu_fold_raiser = 0.60

    # HU 3bet EV: raiser = BTN のみ
    # dead_money = raiser_bb のみ (no caller)
    hu_dead = hu_raiser_bb  # + 1bb blind (簡略)
    hu_both_fold_ev = hu_fold_raiser * hu_dead
    hu_call_ev = (1 - hu_fold_raiser) * (hu_dead + hu_3bet_size) * 0.5 - hu_3bet_size
    hu_net_ev = hu_both_fold_ev + hu_call_ev

    # --- スクイーズ (BTN open + MP call) ---
    # BTN open 2.5bb, MP call 2.5bb, BB squeeze 10bb
    squeeze_size = 10.0
    raiser_bb = 2.5  # BTN
    caller_bb = 2.5  # MP

    # スクイーズに対する fold rate
    # レイザー (BTN) fold: ~55% (コーラーがいると相対的にフォールドしやすい)
    # コーラー (MP) fold: ~70% (デッドマネーを嫌がる)
    fold_raiser = 0.55
    fold_caller = 0.70

    sq_result = squeeze_ev(raiser_bb, caller_bb, squeeze_size, fold_raiser, fold_caller)

    # --- デッドマネーによる EV 上乗せ計算 ---
    # 同じ fold 率で HU 3bet vs スクイーズを比較
    # HU 3bet: dead = 2.5bb, squeeze: dead = 5.0bb
    # EV 差 (both_fold 部分) = (5.0 - 2.5) * fold_prob ≈ 2.5 * 0.6 = 1.5bb
    dead_money_bonus = caller_bb * fold_raiser  # コーラーがいる分の EV 上乗せ
    # 閾値への影響: HandScore 1pt ≈ 1bb EV に相当 (Chen 式の近似)
    # 従って EV 上乗せ ≈ 1.5bb → 閾値 -1〜-2 程度
    threshold_reduction_approx = dead_money_bonus  # bb 単位

    return {
        "hu_3bet": {
            "size_bb": hu_3bet_size,
            "dead_money_bb": hu_dead,
            "fold_raiser": hu_fold_raiser,
            "ev_fold": round(hu_both_fold_ev, 3),
            "ev_call": round(hu_call_ev, 3),
            "net_ev": round(hu_net_ev, 3),
        },
        "squeeze": sq_result,
        "dead_money_bonus_bb": round(dead_money_bonus, 3),
        "threshold_reduction_approx": round(threshold_reduction_approx, 2),
        "note": (
            f"コーラー1人のデッドマネー {caller_bb}bb により、"
            f"fold率 {fold_raiser*100:.0f}% × {caller_bb}bb = "
            f"{dead_money_bonus:.2f}bb の EV 上乗せ。"
            f"HandScore 1pt ≈ 1bb EV の近似より、閾値は約 {threshold_reduction_approx:.1f} 下がる。"
        ),
    }


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="3BPシナリオ検証")
    parser.add_argument("--skip-a", action="store_true", help="シナリオAをスキップ")
    parser.add_argument("--skip-b", action="store_true", help="シナリオBをスキップ")
    args = parser.parse_args()

    if not os.path.exists(SOLVER_BIN):
        print(f"ERROR: solver not found: {SOLVER_BIN}", file=sys.stderr)
        sys.exit(1)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {}

    # ===== シナリオ A =====
    print("\n" + "="*60)
    print("[A] K72r 3BP フロップ: OOP後手スコア検証")
    print("="*60)

    if not args.skip_a:
        with tempfile.TemporaryDirectory() as tmpdir:
            dump_a = os.path.join(tmpdir, "result_a.json")
            config_a = SCENARIO_A_CONFIG.format(
                pot=SCENARIO_A_POT,
                stack=SCENARIO_A_STACK,
                board=SCENARIO_A_BOARD,
                ip_range=SCENARIO_A_IP_RANGE,
                oop_range=SCENARIO_A_OOP_RANGE,
                dump_path=dump_a,
            )
            t0 = time.time()
            _, exploit_a, rc = run_solver(config_a, timeout=TIMEOUT)
            elapsed_a = time.time() - t0

            # dump_path は run_solver が temp ファイルとして生成するが、
            # config 内の dump_path は tmpdir 内を指す
            # → tmpdir 内のファイルを読む
            actual_dump = dump_a

            if rc == -1:
                print(f"  TIMEOUT ({elapsed_a:.0f}s)")
                result_a = {"status": "timeout", "elapsed_sec": round(elapsed_a, 1)}
            elif rc != 0:
                print(f"  ERROR rc={rc}")
                result_a = {"status": f"error_rc_{rc}"}
            elif not os.path.exists(actual_dump):
                print(f"  dump not found: {actual_dump}")
                result_a = {"status": "no_dump"}
            else:
                try:
                    with open(actual_dump) as f:
                        json_a = json.load(f)
                    analysis_a = analyze_scenario_a(json_a)
                    result_a = {
                        "status": "ok",
                        "scenario": "K72r_3BP_flop_OOP",
                        "board": SCENARIO_A_BOARD,
                        "pot_bb": SCENARIO_A_POT,
                        "stack_bb": SCENARIO_A_STACK,
                        "exploitability_pct": round(exploit_a, 3) if exploit_a else None,
                        "elapsed_sec": round(elapsed_a, 1),
                        "analysis": analysis_a,
                    }
                except Exception as e:
                    print(f"  parse error: {e}")
                    import traceback
                    traceback.print_exc()
                    result_a = {"status": f"parse_error: {e}"}

        results["scenario_a"] = result_a
        out_a = RESULTS_DIR / "scenario_A.json"
        with open(out_a, "w") as f:
            json.dump(result_a, f, ensure_ascii=False, indent=2)
        print(f"  → 保存: {out_a}")
    else:
        print("  スキップ")
        result_a = {"status": "skipped"}
        # 既存結果を読み込む
        out_a = RESULTS_DIR / "scenario_A.json"
        if out_a.exists():
            with open(out_a) as f:
                result_a = json.load(f)
        results["scenario_a"] = result_a

    # ===== シナリオ B =====
    print("\n" + "="*60)
    print("[B] K72r+3h ターン CBet (SPR=2.7): IP バレル頻度検証")
    print("="*60)

    if not args.skip_b:
        with tempfile.TemporaryDirectory() as tmpdir:
            dump_b = os.path.join(tmpdir, "result_b.json")
            config_b = SCENARIO_B_CONFIG.format(
                pot=SCENARIO_B_POT,
                stack=SCENARIO_B_STACK,
                board=SCENARIO_B_BOARD,
                ip_range=SCENARIO_B_IP_RANGE,
                oop_range=SCENARIO_B_OOP_RANGE,
                dump_path=dump_b,
            )
            t0 = time.time()
            _, exploit_b, rc_b = run_solver(config_b, timeout=TIMEOUT)
            elapsed_b = time.time() - t0

            actual_dump_b = dump_b

            if rc_b == -1:
                print(f"  TIMEOUT ({elapsed_b:.0f}s)")
                result_b = {"status": "timeout", "elapsed_sec": round(elapsed_b, 1)}
            elif rc_b != 0:
                print(f"  ERROR rc={rc_b}")
                result_b = {"status": f"error_rc_{rc_b}"}
            elif not os.path.exists(actual_dump_b):
                print(f"  dump not found: {actual_dump_b}")
                result_b = {"status": "no_dump"}
            else:
                try:
                    with open(actual_dump_b) as f:
                        json_b = json.load(f)
                    analysis_b = analyze_scenario_b(json_b)
                    result_b = {
                        "status": "ok",
                        "scenario": "K72r3h_turn_CBet_SPR2.7",
                        "board": SCENARIO_B_BOARD,
                        "pot_bb": SCENARIO_B_POT,
                        "stack_bb": SCENARIO_B_STACK,
                        "spr": round(SCENARIO_B_STACK / SCENARIO_B_POT, 2),
                        "exploitability_pct": round(exploit_b, 3) if exploit_b else None,
                        "elapsed_sec": round(elapsed_b, 1),
                        "analysis": analysis_b,
                    }
                except Exception as e:
                    print(f"  parse error: {e}")
                    import traceback
                    traceback.print_exc()
                    result_b = {"status": f"parse_error: {e}"}

        results["scenario_b"] = result_b
        out_b = RESULTS_DIR / "scenario_B.json"
        with open(out_b, "w") as f:
            json.dump(result_b, f, ensure_ascii=False, indent=2)
        print(f"  → 保存: {out_b}")
    else:
        print("  スキップ")
        result_b = {"status": "skipped"}
        out_b = RESULTS_DIR / "scenario_B.json"
        if out_b.exists():
            with open(out_b) as f:
                result_b = json.load(f)
        results["scenario_b"] = result_b

    # ===== シナリオ C =====
    print("\n" + "="*60)
    print("[C] スクイーズ EV: 理論検証")
    print("="*60)

    result_c = analyze_scenario_c()
    results["scenario_c"] = result_c
    out_c = RESULTS_DIR / "scenario_C.json"
    with open(out_c, "w") as f:
        json.dump(result_c, f, ensure_ascii=False, indent=2)
    print(f"  → 保存: {out_c}")

    # ===== サマリ出力 =====
    print("\n" + "="*60)
    print("=== 検証結果 ===")
    print("="*60)

    # [A]
    ra: Any = result_a
    print("\n[A] K72r 3BP OOP後手:")
    if ra.get("status") == "ok":
        an: Any = ra.get("analysis", {})
        cr_pct = an.get("avg_raise_pct", "N/A")
        call_pct = an.get("avg_call_pct", "N/A")
        fold_pct = an.get("avg_fold_pct", "N/A")
        print(f"  OOP vs IP 33%CBet: CR={cr_pct}%, CALL={call_pct}%, FOLD={fold_pct}%")
        print(f"  (exploitability: {ra.get('exploitability_pct', 'N/A')}%)")
        combo_an: Any = an.get("combo_analysis", {})
        for hand in ["AA", "KK", "QQ", "AKs", "AKo", "A5s", "A4s"]:
            c: Any = combo_an.get(hand, {})
            if "note" in c:
                print(f"  combo {hand}: {c['note']}")
            elif c:
                print(f"  combo {hand}: CR={c.get('raise_pct', 'N/A')}%, "
                      f"CALL={c.get('call_pct', 'N/A')}%, FOLD={c.get('fold_pct', 'N/A')}%")

        # 書籍予測との比較
        print("\n  書籍予測との比較:")
        predictions = {
            "AA": ("CR", "BackScore=17"),
            "AKs": ("CR", "BackScore=15"),
            "AKo": ("CR", "BackScore=15"),
            "QQ": ("CALL", "BackScore=3"),
            "A5s": ("CALL", "BackScore=1"),
        }
        for hand, (pred_action, reason) in predictions.items():
            c = combo_an.get(hand, {})
            if c and "note" not in c:
                actual_dominant = max(
                    [("CR", c.get("raise_pct", 0)),
                     ("CALL", c.get("call_pct", 0)),
                     ("FOLD", c.get("fold_pct", 0))],
                    key=lambda x: x[1]
                )[0]
                match = "整合" if actual_dominant == pred_action else "不整合"
                print(f"    {hand} ({reason}): 予測={pred_action}, 実際={actual_dominant} → {match}")
    elif ra.get("status") == "timeout":
        print(f"  TIMEOUT ({ra.get('elapsed_sec', '?')}s)")
    elif ra.get("status") == "skipped":
        print("  スキップ (既存結果使用)")
        if "analysis" in ra:
            an_s: Any = ra.get("analysis", {})
            print(f"  OOP vs IP 33%CBet: CR={an_s.get('avg_raise_pct', 'N/A')}%, "
                  f"CALL={an_s.get('avg_call_pct', 'N/A')}%, FOLD={an_s.get('avg_fold_pct', 'N/A')}%")
    else:
        print(f"  エラー: {ra.get('status')}")

    # [B]
    rb: Any = result_b
    print("\n[B] K72r+3h ターンCBet (SPR=2.7):")
    if rb.get("status") == "ok":
        an_b: Any = rb.get("analysis", {})
        cbet = an_b.get("cbet_pct", "N/A")
        print(f"  IP turnCBet頻度: {cbet}% (予測: ~100%)")
        spr = rb.get("spr", "?")
        match_str = "整合" if isinstance(cbet, (int, float)) and cbet >= 80 else "不整合"
        print(f"  SPR={spr} → 'SPR<3は常にバレル'ルールと{match_str}")
        print(f"  (exploitability: {rb.get('exploitability_pct', 'N/A')}%)")
    elif rb.get("status") == "timeout":
        print(f"  TIMEOUT ({rb.get('elapsed_sec', '?')}s)")
    elif rb.get("status") == "skipped":
        print("  スキップ (既存結果使用)")
        if "analysis" in rb:
            an_b2: Any = rb.get("analysis", {})
            cbet2 = an_b2.get("cbet_pct", "N/A")
            print(f"  IP turnCBet頻度: {cbet2}%")
    else:
        print(f"  エラー: {rb.get('status')}")

    # [C]
    rc_d: Any = result_c
    print("\n[C] スクイーズEV:")
    hu: Any = rc_d.get("hu_3bet", {})
    sq: Any = rc_d.get("squeeze", {})
    bonus = rc_d.get("dead_money_bonus_bb", "N/A")
    thresh = rc_d.get("threshold_reduction_approx", "N/A")
    print(f"  HU 3bet EV: {hu.get('net_ev', 'N/A')} bb")
    print(f"  スクイーズ EV: {sq.get('net_ev', 'N/A')} bb")
    print(f"  デッドマネー ボーナス: {bonus} bb")
    print(f"  閾値低下 (近似): -{thresh} pt")
    print(f"  {rc_d.get('note', '')}")

    # サマリ保存
    summary = {
        "generated_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "scenario_a_status": ra.get("status"),
        "scenario_b_status": rb.get("status"),
        "scenario_a_avg_raise_pct": (
            ra.get("analysis", {}).get("avg_raise_pct")
            if ra.get("status") in ("ok", "skipped") else None
        ),
        "scenario_b_cbet_pct": (
            rb.get("analysis", {}).get("cbet_pct")
            if rb.get("status") in ("ok", "skipped") else None
        ),
        "scenario_c_threshold_reduction": rc_d.get("threshold_reduction_approx"),
        "results": results,
    }
    summary_file = RESULTS_DIR / "summary.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  サマリ保存: {summary_file}")
    print(f"  結果ディレクトリ: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
