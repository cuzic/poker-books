#!/usr/bin/env python3
"""フロップ check-raise + river GTO 調査シナリオ JSON 生成.

出力: scenarios_cr_river.json

シナリオ内訳:
  cr_study  : フロップ check-raise / OOP 反応調査 (15 ボード, pot=6)
  river_snap: ターン上がりリバー snap-off 調査 (12 シナリオ, pot=28)

cr_study ボード選定基準:
  - 乾燥 K/A-high  (2 boards)
  - セミウェット broadway  (2 boards)
  - コネクテッド mid  (2 boards)
  - FD ボード  (3 boards: dry FD, wet FD, mono)
  - ペアボード  (2 boards)
  - ロー  (2 boards)
  - ハイFD  (2 boards)

river_snap ボード:
  - ターン K73r-As/Kh + river card (pot=28 は 10bb ターン → 33% bet/call)
  - 代表 6 ターンボード × 2 river カード
"""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).parent / "scenarios_cr_river.json"

# ── Check-raise 調査ボード (pot=6, SRP flop) ────────────────────────────────
CR_BOARDS = [
    # Dry high boards
    {"id": "cr_K72r",  "board": "Kc,7d,2s",  "texture": "dry_K_high"},
    {"id": "cr_A82r",  "board": "Ac,8d,2s",  "texture": "dry_A_high"},
    # Semi-wet broadway
    {"id": "cr_JT5r",  "board": "Jc,Td,5s",  "texture": "semi_broadway"},
    {"id": "cr_KQTr",  "board": "Kc,Qd,Ts",  "texture": "semi_broadway_high"},
    # Connected mid
    {"id": "cr_987r",  "board": "9s,8d,7c",  "texture": "connected_mid"},
    {"id": "cr_T86r",  "board": "Tc,8d,6s",  "texture": "connected_mid2"},
    # FD boards
    {"id": "cr_K83fd", "board": "Kc,8c,3d",  "texture": "fd_K_high"},
    {"id": "cr_Q85fd", "board": "Qc,8c,5d",  "texture": "fd_Q_high"},
    {"id": "cr_JT4fd", "board": "Jc,Tc,4d",  "texture": "fd_broadway_fd"},
    # Monotone
    {"id": "cr_K75m",  "board": "Ks,7s,5s",  "texture": "mono"},
    # Paired boards
    {"id": "cr_KK7r",  "board": "Kc,Kd,7s",  "texture": "paired_high"},
    {"id": "cr_774r",  "board": "7c,7d,4s",   "texture": "paired_mid"},
    # Low boards
    {"id": "cr_742r",  "board": "7c,4d,2s",   "texture": "low_dry"},
    {"id": "cr_865r",  "board": "8c,6d,5s",   "texture": "low_connected"},
    # High FD
    {"id": "cr_A85fd", "board": "Ac,8c,5d",   "texture": "fd_A_high"},
]

# ── River snap-shot 調査 ────────────────────────────────────────────────────
# ターン after CBet(33%) + Call → pot ≈ 10bb, 次のリバーカードで river 調査
# 実質: turn board (4 枚) + river card (5 枚目)
# pot=14bb (turn start) → IP bet 33%=4.7bb → call → pot=23bb river start
# effective stack ≈ 92 - 4.7 = 87bb
#
# シンプルに: 代表ターンボード 6 つ × 2 river カードで 12 シナリオ
# board = 5 cards, pot=23, stack=87
RIVER_SCENARIOS = [
    # K73r turn: As / blank / pair ターン済み → riverはその先
    # K73r_As_ターン → river 5 枚目
    {"id": "rv_K73r_As_2c",  "board": "Kc,7d,2s,Ah,2c",  "river_type": "pair_low",    "prev_turn": "OC_ace"},
    {"id": "rv_K73r_As_Jd",  "board": "Kc,7d,2s,Ah,Jd",  "river_type": "blank_mid",   "prev_turn": "OC_ace"},
    # A72r_Kh ターン → river
    {"id": "rv_A72r_Kh_Ts",  "board": "Ac,7d,2s,Kh,Ts",  "river_type": "blank_mid",   "prev_turn": "OC_king"},
    {"id": "rv_A72r_Kh_7d",  "board": "Ac,7d,2s,Kh,7d",  "river_type": "pair_mid",    "prev_turn": "OC_king"},
    # JT5r_9d ターン (straight completed on turn) → river
    {"id": "rv_JT5r_9d_2h",  "board": "Jc,Td,5s,9d,2h",  "river_type": "blank_low",   "prev_turn": "straight"},
    {"id": "rv_JT5r_9d_Qh",  "board": "Jc,Td,5s,9d,Qh",  "river_type": "OC",          "prev_turn": "straight"},
    # 987r_6h ターン → river
    {"id": "rv_987r_6h_As",  "board": "9s,8d,7c,6h,As",  "river_type": "OC_ace",      "prev_turn": "straight"},
    {"id": "rv_987r_6h_3d",  "board": "9s,8d,7c,6h,3d",  "river_type": "blank_low",   "prev_turn": "straight"},
    # K72fd_3s ターン (flush hit) → river
    {"id": "rv_K72fd_3s_8h", "board": "Ks,7s,2h,3s,8h",  "river_type": "blank",       "prev_turn": "flush_hit"},
    {"id": "rv_K72fd_3s_Kh", "board": "Ks,7s,2h,3s,Kh",  "river_type": "pair_top",    "prev_turn": "flush_hit"},
    # QQ4r_Ah ターン → river
    {"id": "rv_QQ4r_Ah_5d",  "board": "Qc,Qd,4s,Ah,5d",  "river_type": "blank",       "prev_turn": "OC_ace"},
    {"id": "rv_QQ4r_Ah_Qh",  "board": "Qc,Qd,4s,Ah,Qh",  "river_type": "quads_Q",     "prev_turn": "OC_ace"},
]

# River pot は turn bet-call 後の想定:
# Turn pot=10bb → IP bet 33% (3.3bb) → OOP call → river pot = 16.6bb ≈ 17bb
# Turn stack 92bb → bet 3.3bb → river stack ≈ 88.7bb ≈ 89bb
RIVER_POT = 17
RIVER_STACK = 89


def build_scenarios() -> list[dict]:
    scenarios = []

    # check-raise study (フロップ, pot=6)
    for b in CR_BOARDS:
        scenarios.append({
            "id": b["id"],
            "tag": "cr_study",
            "board": b["board"],
            "n_board": 3,
            "texture": b["texture"],
            "pot_bb": 6,
            "effective_stack_bb": 94,
            "flop_bet_sizes": "33,75",
            "turn_bet_sizes": "33,75",
        })

    # river snapshot (5 枚ボード)
    for r in RIVER_SCENARIOS:
        scenarios.append({
            "id": r["id"],
            "tag": "river_snap",
            "board": r["board"],
            "n_board": 5,
            "river_type": r["river_type"],
            "prev_turn": r.get("prev_turn", ""),
            "pot_bb": RIVER_POT,
            "effective_stack_bb": RIVER_STACK,
            "river_bet_sizes": "33,75",
        })

    return scenarios


def main() -> None:
    scenarios = build_scenarios()
    n_flop  = sum(1 for s in scenarios if s["n_board"] == 3)
    n_river = sum(1 for s in scenarios if s["n_board"] == 5)
    tags: dict[str, int] = {}
    for s in scenarios:
        for t in s["tag"].split(","):
            tags[t] = tags.get(t, 0) + 1

    doc = {
        "meta": {
            "total": len(scenarios), "flop_cr": n_flop, "river": n_river,
            "tags": tags,
            "pot_flop": 6, "pot_river": RIVER_POT,
            "stack_flop": 94, "stack_river": RIVER_STACK,
            "bet_sizes": "flop=33,75  river=33,75",
            "purpose": "OOP check-raise freq + river value/bluff/defense",
        },
        "scenarios": scenarios,
    }

    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f"生成完了: {OUT}")
    print(f"  合計 {len(scenarios)} シナリオ (フロップ CR {n_flop} + リバー {n_river})")
    print(f"  タグ別: {tags}")


if __name__ == "__main__":
    main()
