#!/usr/bin/env python3
"""
ドロー加点 TexasSolver 境界検証 v3 (新スケール 0-100 equity %)

旧版 draw_bonus_verify.py の新スケール対応。
旧版は残し、新規 v3 として作成。

新仕様 (knowledges/ds_redesign_v2/SPEC_HANDSCORE.md / SPEC_OTHER_FORMULAS.md):
  後手スコア = HS + A - C - M
  C: {33: 12, 50: 17, 75: 22, 100: 25, 150: 30}
  A: dry=12 / semi=6 / wet=0
  閾値: >=40 RAISE / >=20 CALL / <20 FOLD

ドロー加点 (新スケール、フロップ Rule of 4):
  FD (9 outs): +36
  OESD (8 outs): +32
  GS (4 outs): +16
  FD + OESD: +52
  BDFD: +5 (固定)
  BDSD: +2 (固定)

このスクリプトでは TexasSolver 解析 raw JSON が既に存在することを前提に、
ドロー加点を含む HS で DS 予測 vs GTO 実測を照合する（OOP CALL/RAISE/FOLD）。
新規 solver 起動はせず、既存キャッシュ (k72r_srp_raw.json 等) のみ使用。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

REPO = Path("/home/cuzic/poker-books")
sys.path.insert(0, str(REPO / "scripts"))
from c_coefficients_v3 import (  # noqa: E402
    A_TABLE, C_TABLE, M_TABLE,
    DS_TH_RAISE, DS_TH_CALL,
    defender_score, predict_defender,
)

OUT_DIR = REPO / "knowledges/volume4/results/draw_bonus_verify"

# 新スケールの代表ドロー HS (役なし + ドロー加点)
# 弱役 (ハイカード ~10) + ドロー加点
HS_BDFD = 13   # ハイカード(8) + BDFD(+5)
HS_OESD = 42   # ハイカード(10) + OESD(+32) ← 純 OESD のみ
HS_FD = 46     # ハイカード(10) + FD(+36)
HS_FD_NUTS = 51   # A or K ハイ(15) + FD(+36)
HS_TPTK = 70


def get_bet_node(raw: dict, bet_amount: float, tol: float = 1.5) -> dict | None:
    """root → CHECK → BET X ノードを返す（IP CBet 後の OOP 応答）。最近傍を返す。"""
    check = raw.get("childrens", {}).get("CHECK")
    if not check:
        return None
    best_node = None
    best_dist = float("inf")
    for key, node in check.get("childrens", {}).items():
        if not key.startswith("BET"):
            continue
        try:
            amt = float(key.split()[1])
        except (IndexError, ValueError):
            continue
        dist = abs(amt - bet_amount)
        if dist <= tol and dist < best_dist:
            best_dist = dist
            best_node = node
    return best_node


def get_combo_action(node: dict, combo: str) -> dict | None:
    strat = node.get("strategy", {})
    actions = strat.get("actions", [])
    combos = strat.get("strategy", {})
    probs = combos.get(combo)
    if probs is None:
        return None
    return {a: round(p, 4) for a, p in zip(actions, probs)}


def dominant_action(amap: dict) -> str:
    call = amap.get("CALL", 0)
    fold = amap.get("FOLD", 0)
    raise_total = sum(v for k, v in amap.items() if "RAISE" in k)
    if raise_total >= call and raise_total >= fold:
        return "raise"
    if call >= fold:
        return "call"
    return "fold"


def verify_draw_combos(
    raw: dict, board_label: str, board_type: str,
    targets: list[tuple[str, int, str]],
    bet_mapping: list[tuple[float, int]],
) -> list[dict]:
    """
    targets: [(combo, hs, desc)]
    bet_mapping: [(bet_bb, bet_pct)]  # bet_pct は 33/50/75 など
    """
    a_val = A_TABLE[board_type]
    m_val = M_TABLE["HU"]
    results = []
    for combo, hs, desc in targets:
        combo_results = {
            "combo": combo, "hs": hs, "desc": desc, "by_bet": []
        }
        for bet_bb, bet_pct in bet_mapping:
            c_val = C_TABLE[bet_pct]
            node = get_bet_node(raw, bet_bb)
            if node is None:
                combo_results["by_bet"].append({
                    "bet_bb": bet_bb, "bet_pct": bet_pct, "c": c_val,
                    "ds": None, "predict": None,
                    "call": None, "raise": None, "fold": None,
                    "match": "N/A",
                })
                continue

            ds = defender_score(hs, a_val, c_val, m_val)
            predict = predict_defender(ds)

            amap = get_combo_action(node, combo)
            if amap is None:
                combo_results["by_bet"].append({
                    "bet_bb": bet_bb, "bet_pct": bet_pct, "c": c_val,
                    "ds": ds, "predict": predict,
                    "call": None, "raise": None, "fold": None,
                    "match": "N/A (not in range)",
                })
                continue

            call_p = amap.get("CALL", 0)
            fold_p = amap.get("FOLD", 0)
            raise_p = sum(v for k, v in amap.items() if "RAISE" in k)
            actual = dominant_action(amap)
            match = (predict == actual)
            # MDF 例外: predict=fold, call > 30%, ウェット板
            is_mdf_exception = (
                not match and predict == "fold"
                and call_p >= 0.30 and board_type == "wet"
            )
            combo_results["by_bet"].append({
                "bet_bb": bet_bb, "bet_pct": bet_pct, "c": c_val,
                "ds": ds, "predict": predict,
                "call": round(call_p, 3), "raise": round(raise_p, 3),
                "fold": round(fold_p, 3),
                "actual": actual, "match": match,
                "mdf_exception": is_mdf_exception,
            })
        results.append(combo_results)
    return results


def print_results(title: str, results: list[dict], bet_labels: list[str]) -> None:
    print(f"\n{'=' * 72}")
    print(title)
    print(f"{'=' * 72}")
    print(f"  {'コンボ':8} {'HS':>3} | ", end="")
    for lbl in bet_labels:
        print(f" {lbl:24}", end="")
    print()
    print("  " + "-" * (12 + 26 * len(bet_labels)))

    for r in results:
        print(f"  {r['combo']:8} HS={r['hs']:>3} | ", end="")
        for b in r["by_bet"]:
            if b["call"] is None:
                print(f" {'N/A':24}", end="")
                continue
            ds = b["ds"]
            pred = b["predict"]
            call_pct = round(b["call"] * 100)
            raise_pct = round(b["raise"] * 100)
            fold_pct = round(b["fold"] * 100)
            is_mdf = b.get("mdf_exception", False)
            flag = "✓" if b["match"] else ("△MDF" if is_mdf else "✗")
            cell = f"DS={ds:+d}→{pred[:1].upper()} R{raise_pct}C{call_pct}F{fold_pct} {flag}"
            print(f" {cell:24}", end="")
        print(f"  {r['desc'][:30]}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ──────────────────────────────────────────────
    # 1. K72r: BDFD 検証 (HS=13: ハイカード+BDFD)
    # ──────────────────────────────────────────────
    print("\n▶ [1/2] BDFD 検証 — K72r (Kc,7d,2s, dry A=12)")
    k72r_path = REPO / "knowledges/volume4/results/c_coef_srp/k72r_srp_raw.json"
    if not k72r_path.exists():
        print(f"  WARN: {k72r_path} 未存在 → スキップ")
        k72r_results = []
    else:
        k72r_raw = json.loads(k72r_path.read_text())
        k72r_bdfd = [
            ("5c4c", HS_BDFD, "54s BDFD clubs (Kc)"),
            ("5d4d", HS_BDFD, "54s BDFD diamonds (7d)"),
            ("5s4s", HS_BDFD, "54s BDFD spades (2s)"),
            ("6d5d", HS_BDFD, "65s BDFD diamonds"),
            ("6c4c", HS_BDFD, "64o BDFD clubs"),
        ]
        # K72r では bet_bb: 33%→2.0bb, 50%→4.0bb (TexasSolver 設定), 75%→5.0bb
        k72r_bets = [(2.0, 33), (4.0, 50), (5.0, 75)]
        k72r_results = verify_draw_combos(
            k72r_raw, "K72r", "dry", k72r_bdfd, k72r_bets,
        )
        # 期待: HS=13, A=12, C=12 → DS=13. >=20 (call) には届かず fold
        # → 仕様: BDFD は弱、33% でもフォールド寄り
        print_results(
            "BDFD (HS=13) on K72r dry",
            k72r_results,
            ["33%pot", "50%pot", "75%pot"],
        )

    # ──────────────────────────────────────────────
    # 2. T98r: OESD 検証 (HS=42: ハイカード+OESD)
    # ──────────────────────────────────────────────
    print("\n▶ [2/2] OESD 検証 — T98r (Th,9d,8c, wet A=0)")
    t98r_path = REPO / "knowledges/volume4/results/phase1/th9d8c/defender_result.json"
    if not t98r_path.exists():
        print(f"  WARN: {t98r_path} 未存在 → スキップ")
        t98r_results = []
    else:
        t98r_raw = json.loads(t98r_path.read_text())
        t98r_oesd = [
            ("Js7s", HS_OESD, "J7o OESD (J-T-9-8-7)"),
            ("7s6d", HS_OESD, "76o OESD (6-7-8-9-T)"),
            ("7d6s", HS_OESD, "76o OESD"),
            ("7s6s", HS_OESD, "76s OESD"),
        ]
        t98r_bets = [(2.0, 33), (4.0, 50), (5.0, 75)]
        t98r_results = verify_draw_combos(
            t98r_raw, "T98r", "wet", t98r_oesd, t98r_bets,
        )
        # 期待: HS=42, A=0, C=12 → DS=30 (CALL). 75% C=22 → DS=20 (CALL 境界)
        print_results(
            "OESD (HS=42) on T98r wet",
            t98r_results,
            ["33%pot", "50%pot", "75%pot"],
        )

    # ──────────────────────────────────────────────
    # 総合サマリー
    # ──────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("総合サマリー: ドロー加点値 DS 整合確認 v3 (新スケール)")
    print("=" * 72)
    print()
    print("BDFD (HS=13) on K72r dry:")
    print(f"  33% C=12: DS = 13 + 12 - 12 = 13 → FOLD")
    print(f"  75% C=22: DS = 13 + 12 - 22 =  3 → FOLD")
    print()
    print("OESD (HS=42) on T98r wet:")
    print(f"  33% C=12: DS = 42 +  0 - 12 = 30 → CALL")
    print(f"  75% C=22: DS = 42 +  0 - 22 = 20 → CALL (境界)")
    print()
    print("FD (HS=46) on Q83ss semi:")
    print(f"  33% C=12: DS = 46 +  6 - 12 = 40 → RAISE")
    print(f"  75% C=22: DS = 46 +  6 - 22 = 30 → CALL")

    summary = {
        "scale": "v3 (new, 0-100 equity %)",
        "draw_HS_values": {
            "BDFD": HS_BDFD,
            "OESD_pure": HS_OESD,
            "FD": HS_FD,
            "FD_nuts": HS_FD_NUTS,
        },
        "BDFD_K72r": k72r_results,
        "OESD_T98r": t98r_results,
        "expected": {
            "BDFD": "FOLD across all sizes (HS too weak)",
            "OESD_wet": "CALL on 33%-75%; boundary at 75%",
            "FD_semi": "RAISE on 33%, CALL on 75%",
        },
    }
    out = OUT_DIR / "draw_bonus_verify_v3_result.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n保存: {out}")


if __name__ == "__main__":
    main()
