#!/usr/bin/env python3
"""PokerBench (GTO Wizard 由来) と TexasSolver の per-holding 整合性検証.

PokerBench の K72r (Ks7h2d) サンプル (58 holdings) を取得し、
同じ K72r を TexasSolver で solve して per-holding 戦略を比較する。

両者で「dominant action」が一致する holdings の割合を測る。
これが高ければ PokerBench は TexasSolver の教師として機能する証拠になる。
"""
from __future__ import annotations
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from texassolver_accuracy_30 import build_config, run_solver, RESULTS_DIR  # noqa: E402

DUMP_PATH = REPO / "knowledges/volume4/scenarios/flop_accuracy_30_mr2/flop_acc30_K72r_mr2_FULL_DUMP.json"


def normalize_holding(h: str) -> str:
    """PokerBench 'AhKs' → ソート済 'AhKs'(AKオフ)."""
    cards = [h[i:i+2] for i in range(0, len(h), 2)]
    rv = {'A':14,'K':13,'Q':12,'J':11,'T':10,'9':9,'8':8,'7':7,'6':6,'5':5,'4':4,'3':3,'2':2}
    cards.sort(key=lambda c: -rv[c[0]])
    return ''.join(cards)


def parse_pb_action(decision: str) -> str:
    """PokerBench correct_decision を {bet, check} に正規化."""
    d = str(decision).strip().lower()
    return 'bet' if d.startswith('bet') else 'check' if d.startswith('check') else 'other'


def get_ts_dominant_action(probs: list, actions: list) -> tuple[str, float]:
    """TexasSolver strategy → 主アクション."""
    if not probs or not actions:
        return ('?', 0.0)
    max_idx = max(range(len(probs)), key=lambda i: probs[i])
    raw = actions[max_idx]
    if raw == 'CHECK':
        return ('check', probs[max_idx])
    return ('bet', probs[max_idx])


def main():
    # 1. PokerBench から K72r データ
    print("[1/3] PokerBench データ抽出中...")
    df = pd.read_csv(REPO / 'data/pokerbench/postflop_500k_train.csv', low_memory=False)
    pb_k72r = df[
        (df['evaluation_at'] == 'Flop') &
        (df['preflop_action'] == 'BTN/2.5bb/BB/call') &
        (df['hero_position'] == 'IP') &
        (df['postflop_action'] == 'OOP_CHECK') &
        (df['board_flop'] == 'Ks7h2d')
    ].copy()
    pb_k72r['pb_action'] = pb_k72r['correct_decision'].apply(parse_pb_action)
    pb_k72r = pb_k72r[pb_k72r['pb_action'].isin(['bet', 'check'])]
    print(f"  PokerBench K72r: {len(pb_k72r)} holdings")
    pb_dict = dict(zip(pb_k72r['holding'], pb_k72r['pb_action']))

    # 2. TexasSolver で Ks7h2d (K72r) を solve
    print("\n[2/3] TexasSolver で Ks7h2d を solve 中（~5 分）...")
    if not DUMP_PATH.exists():
        config = build_config('Ks,7h,2d', str(DUMP_PATH))
        t0 = time.time()
        exploit, rc = run_solver(config, timeout=600)
        elapsed = time.time() - t0
        if rc != 0 or not DUMP_PATH.exists():
            print(f"  ERROR rc={rc}, elapsed={elapsed:.0f}s")
            return
        print(f"  完了: {elapsed:.0f}s, exploitability={exploit}")
    else:
        print(f"  既存 dump 利用: {DUMP_PATH.name}")

    with open(DUMP_PATH) as f:
        ts_dump = json.load(f)

    check_node = ts_dump.get('childrens', {}).get('CHECK')
    if not check_node:
        print("ERROR: no CHECK node in dump")
        return

    strat_wrap = check_node.get('strategy', {})
    actions = strat_wrap.get('actions', [])
    combo_strats = strat_wrap.get('strategy', {})
    print(f"  TS K72r CHECK 後 IP の actions: {actions}")
    print(f"  TS holdings: {len(combo_strats)}")

    # 3. 比較
    print("\n[3/3] PokerBench vs TexasSolver per-holding 比較")
    print(f"{'Holding':<10} {'PB':>8} {'TS':>8} {'TS% bet':>8} {'一致':>5}")
    print('-' * 50)

    matches = 0
    total = 0
    pb_bet = 0
    ts_bet = 0
    disagreements = []
    for holding, pb_act in pb_dict.items():
        # PokerBench は holding を 'AhKs' 形式、TS は 'AhKs' か別か?
        if holding not in combo_strats:
            # スートを入れ替えてみる
            alt = holding[2:4] + holding[0:2]
            if alt in combo_strats:
                holding_ts = alt
            else:
                continue
        else:
            holding_ts = holding

        probs = combo_strats[holding_ts]
        # TS の bet 確率合計 = 1 - check 確率
        try:
            check_idx = actions.index('CHECK')
            ts_bet_prob = 1.0 - probs[check_idx]
        except ValueError:
            ts_bet_prob = sum(probs)

        ts_act, _ = get_ts_dominant_action(probs, actions)
        total += 1
        if pb_act == 'bet': pb_bet += 1
        if ts_act == 'bet': ts_bet += 1
        match = pb_act == ts_act
        if match:
            matches += 1
        else:
            disagreements.append((holding, pb_act, ts_act, ts_bet_prob))

    print(f"\n=== 比較結果 ===")
    print(f"  比較対象 holdings: {total}")
    print(f"  PB bet 率: {pb_bet/total:.1%}, TS bet 率: {ts_bet/total:.1%}")
    print(f"  主アクション一致: {matches}/{total} = {matches/total:.1%}")
    print()
    print(f"  不一致サンプル ({len(disagreements)} 件):")
    for h, pb, ts, p in disagreements[:15]:
        print(f"    {h:<6} PB={pb:<6} TS={ts:<6} (TS bet 確率={p:.2f})")


if __name__ == "__main__":
    main()
