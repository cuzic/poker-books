#!/usr/bin/env python3
"""pot=10 統一 GTO 検証シナリオ JSON 生成.

出力: scenarios_pot10.json

シナリオ内訳:
  accuracy30  : フロップ 30 ボード (マルチストリート化, pot=6)
  2oc         : 2OC 加点検証フロップ 6 ボード (pot=6)
  c_coef      : C 係数 SRP 検証フロップ 4 ボード (pot=6)
  range_read  : ターン 30 シナリオ (10 フロップ × 3 ターンカード, pot=10)

合計: ~70 シナリオ
"""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).parent / "scenarios_pot10.json"

# ---------------------------------------------------------------------------
# accuracy30: 既存 30 ボードをマルチストリート化 (フロップ 3 枚, pot=6)
# ---------------------------------------------------------------------------
ACCURACY30_BOARDS = [
    "Kc,7d,2s", "Ac,7d,2s", "Kc,4d,4s", "Qc,5d,3s", "Ac,8d,2s",
    "Kc,8d,3s", "Ac,5d,2s", "Kc,9d,5s", "Kc,Td,5s", "Jc,7d,5s",
    "Qc,8c,3d", "Ac,Tc,7d", "Jc,8c,4d", "Qc,Jd,9s", "Tc,8d,7s",
    "8c,7d,6s", "9c,8c,7d", "Jc,Tc,9d", "9h,8h,7h", "Kc,Qc,Td",
    "Ah,Kh,Qh", "Jc,Tc,8d", "Tc,9d,8s", "Tc,9c,8d", "7c,7d,2s",
    "Ac,Ad,Ks", "Kc,Kd,9s", "9c,6d,5s", "6c,3d,2s", "Ac,9d,9s",
]

# ---------------------------------------------------------------------------
# 2OC: 2 オーバーカード加点 +24 検証フロップ (max rank が低いボードを選択)
# ---------------------------------------------------------------------------
OC2_BOARDS = [
    "7c,4d,2s",   # max=7  → AK-88 がすべて 2OC
    "8c,5d,3s",   # max=8
    "6c,4d,2s",   # max=6  (ローボード)
    "Tc,6d,3s",   # max=T  → AA-JJ が 2OC
    "Jc,7d,4s",   # max=J
    "Kc,7d,2s",   # max=K  (accuracy30 と重複だが 2OC 目的で再利用)
]

# ---------------------------------------------------------------------------
# c_coef: C 係数 SRP 検証 (代表 4 テクスチャ, フロップ 3 枚)
# ---------------------------------------------------------------------------
C_COEF_BOARDS = [
    "Kc,7d,2s",   # ドライ K-high
    "Jc,Td,5s",   # セミウェット broadway
    "9s,8d,7c",   # コネクテッド
    "Ks,7s,5s",   # モノトーン
]

# ---------------------------------------------------------------------------
# range_read: ターン 30 シナリオ (4 枚ボード, pot=10)
# ---------------------------------------------------------------------------
RANGE_READ_TURNS = [
    # K73r × 3
    {"id": "rr_K73r_As",  "board": "Kc,7d,2s,Ah", "turn_type": "OC_ace"},
    {"id": "rr_K73r_9d",  "board": "Kc,7d,2s,9d", "turn_type": "blank"},
    {"id": "rr_K73r_7h",  "board": "Kc,7d,2s,7h", "turn_type": "pair"},
    # A72r × 3
    {"id": "rr_A72r_Kh",  "board": "Ac,7d,2s,Kh", "turn_type": "OC_king"},
    {"id": "rr_A72r_9d",  "board": "Ac,7d,2s,9d", "turn_type": "blank"},
    {"id": "rr_A72r_7h",  "board": "Ac,7d,2s,7h", "turn_type": "pair"},
    # JT5r × 3
    {"id": "rr_JT5r_Ah",  "board": "Jc,Td,5s,Ah", "turn_type": "OC_ace"},
    {"id": "rr_JT5r_9d",  "board": "Jc,Td,5s,9d", "turn_type": "straight"},
    {"id": "rr_JT5r_6h",  "board": "Jc,Td,5s,6h", "turn_type": "blank_low"},
    # 987r × 3
    {"id": "rr_987r_6h",  "board": "9s,8d,7c,6h", "turn_type": "straight"},
    {"id": "rr_987r_Td",  "board": "9s,8d,7c,Td", "turn_type": "OC_ten"},
    {"id": "rr_987r_9h",  "board": "9s,8d,7c,9h", "turn_type": "pair"},
    # K72fd × 3
    {"id": "rr_K72fd_3s", "board": "Ks,7s,2h,3s", "turn_type": "flush_hit"},
    {"id": "rr_K72fd_Ah", "board": "Ks,7s,2h,Ah", "turn_type": "OC_ace"},
    {"id": "rr_K72fd_7h", "board": "Ks,7s,2h,7h", "turn_type": "pair"},
    # JT5fd × 3
    {"id": "rr_JT5fd_2s", "board": "Js,Ts,5h,2s", "turn_type": "flush_hit"},
    {"id": "rr_JT5fd_Ah", "board": "Js,Ts,5h,Ah", "turn_type": "OC_ace"},
    {"id": "rr_JT5fd_9s", "board": "Js,Ts,5h,9s", "turn_type": "straight_fd"},
    # QQ4r × 3
    {"id": "rr_QQ4r_Ah",  "board": "Qc,Qd,4s,Ah", "turn_type": "OC_ace"},
    {"id": "rr_QQ4r_Kd",  "board": "Qc,Qd,4s,Kd", "turn_type": "OC_king"},
    {"id": "rr_QQ4r_4h",  "board": "Qc,Qd,4s,4h", "turn_type": "pair"},
    # AKTr × 3
    {"id": "rr_AKTr_Qh",  "board": "Ac,Kd,Ts,Qh", "turn_type": "straight"},
    {"id": "rr_AKTr_5d",  "board": "Ac,Kd,Ts,5d", "turn_type": "blank"},
    {"id": "rr_AKTr_As",  "board": "Ac,Kd,Ts,As", "turn_type": "pair"},
    # T86r × 3
    {"id": "rr_T86r_7h",  "board": "Tc,8d,6s,7h", "turn_type": "straight"},
    {"id": "rr_T86r_Ah",  "board": "Tc,8d,6s,Ah", "turn_type": "OC_ace"},
    {"id": "rr_T86r_Td",  "board": "Tc,8d,6s,Td", "turn_type": "pair"},
    # K75mono × 3
    {"id": "rr_K75m_3h",  "board": "Ks,7s,5s,3h", "turn_type": "blank"},
    {"id": "rr_K75m_As",  "board": "Ks,7s,5s,As", "turn_type": "flush_hit"},
    {"id": "rr_K75m_7h",  "board": "Ks,7s,5s,7h", "turn_type": "pair"},
]


def build_scenarios() -> list[dict]:
    scenarios = []

    # accuracy30 (フロップ, pot=6)
    seen = set()
    for board in ACCURACY30_BOARDS:
        sid = "acc30_" + board.replace(",", "").replace(" ", "")
        scenarios.append({
            "id": sid, "tag": "accuracy30",
            "board": board, "n_board": 3,
            "pot_bb": 6, "effective_stack_bb": 94,
            "flop_bet_sizes": "33,75", "turn_bet_sizes": "33,75",
        })
        seen.add(board)

    # 2oc (フロップ, pot=6) — accuracy30 と重複しているものはスキップ
    for board in OC2_BOARDS:
        sid = "2oc_" + board.replace(",", "").replace(" ", "")
        entry = {
            "id": sid, "tag": "2oc",
            "board": board, "n_board": 3,
            "pot_bb": 6, "effective_stack_bb": 94,
            "flop_bet_sizes": "33,75", "turn_bet_sizes": "33,75",
        }
        if board in seen:
            # 既に accuracy30 にある → tag を追加するだけ（重複 solve 不要）
            for s in scenarios:
                if s["board"] == board and s["tag"] == "accuracy30":
                    s["tag"] = "accuracy30,2oc"
        else:
            scenarios.append(entry)
            seen.add(board)

    # c_coef (フロップ, pot=6) — 重複スキップ
    for board in C_COEF_BOARDS:
        if board in seen:
            for s in scenarios:
                if s["board"] == board:
                    if "c_coef" not in s["tag"]:
                        s["tag"] += ",c_coef"
        else:
            sid = "cc_" + board.replace(",", "").replace(" ", "")
            scenarios.append({
                "id": sid, "tag": "c_coef",
                "board": board, "n_board": 3,
                "pot_bb": 6, "effective_stack_bb": 94,
                "flop_bet_sizes": "33,75", "turn_bet_sizes": "33,75",
            })
            seen.add(board)

    # range_read (ターン, pot=10)
    for t in RANGE_READ_TURNS:
        scenarios.append({
            "id": t["id"], "tag": "range_read",
            "board": t["board"], "n_board": 4,
            "turn_type": t["turn_type"],
            "pot_bb": 10, "effective_stack_bb": 92,
            "flop_bet_sizes": "33,75", "turn_bet_sizes": "33,75",
        })

    return scenarios


def main() -> None:
    scenarios = build_scenarios()
    n_flop  = sum(1 for s in scenarios if s["n_board"] == 3)
    n_turn  = sum(1 for s in scenarios if s["n_board"] == 4)
    tags: dict[str, int] = {}
    for s in scenarios:
        for t in s["tag"].split(","):
            tags[t] = tags.get(t, 0) + 1

    doc = {"meta": {"total": len(scenarios), "flop": n_flop, "turn": n_turn,
                    "tags": tags, "pot_flop": 6, "pot_turn": 10,
                    "stack_flop": 94, "stack_turn": 92,
                    "bet_sizes": "33,75 (no overbet)"},
           "scenarios": scenarios}

    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2))
    print(f"生成完了: {OUT}")
    print(f"  合計 {len(scenarios)} シナリオ (フロップ {n_flop} + ターン {n_turn})")
    print(f"  タグ別: {tags}")


if __name__ == "__main__":
    main()
