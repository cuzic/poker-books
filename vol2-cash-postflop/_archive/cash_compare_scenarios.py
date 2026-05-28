#!/usr/bin/env python3
"""
マルチシナリオ横断比較スクリプト
findings/multistreet_*.json を読み込み、シナリオ間の戦略差異を集計する

使い方:
  python3 cash_compare_scenarios.py
  python3 cash_compare_scenarios.py > findings/comparison_report.md
"""

import json
from pathlib import Path

FINDINGS_DIR = Path(__file__).parent / "findings"

SCENARIO_ORDER = [
    # BB絡みSRP
    "UTG_BB", "HJ_BB", "CO_BB", "BTN_BB", "SB_BB",
    # BB絡まないSRP（コールドコール/SB守備）
    "UTG_CO", "HJ_BTN", "CO_BTN", "BTN_SB",
    # 3BP
    "BTN_3BP",
]
BOARD_TYPE_ORDER = [
    "型1_ハイドライ", "型2_ハイウェット", "型3_ロードライ",
    "型4_ローウェット", "型5_モノトーン", "型6_ペア高", "型7_ペア低",
]
TURN_TAG_ORDER = ["blank", "TA+_2nd", "TA+_3rd", "TA-_OC", "TA-_OC2", "danger"]


def load_all() -> dict:
    """全シナリオのJSONを読み込む"""
    data = {}
    for f in sorted(FINDINGS_DIR.glob("multistreet_*.json")):
        scenario = f.stem.replace("multistreet_", "")
        with open(f) as fp:
            d = json.load(fp)
        # results をboard_typeキーの辞書に変換
        board_map = {r["type"]: r for r in d.get("results", [])}
        data[scenario] = {"label": d.get("scenario", scenario), "boards": board_map}
    return data


def fmt_pct(v, default="  —"):
    if v is None:
        return default
    return f"{v:5.1f}%"


def fmt_bucket(summary: dict, bkt: str) -> str:
    """バケットのベット/チェック率を短縮フォーマット"""
    if not summary:
        return "  —"
    vals = summary.get(bkt, {})
    bet_keys = [k for k in vals if k not in ("check",) and vals[k] is not None and vals[k] >= 2.0]
    if not bet_keys:
        return "chk"
    return "/".join(f"{k.replace('bet','')}:{vals[k]:.0f}" for k in bet_keys[:2])


# ════════════════════════════════════════════════════════════════
# 1. フロップCBet率：シナリオ × ボード型 × バケット
# ════════════════════════════════════════════════════════════════

def report_flop_cbet(data: dict):
    print("\n" + "=" * 80)
    print("★ フロップCBet率（バリュー/マージナル/エアー）")
    print("  シナリオ × ボード型 × バケット別ベット率")
    print("=" * 80)

    scenarios = [s for s in SCENARIO_ORDER if s in data]

    # ヘッダー行
    hdr = f"{'ボード型':14s}"
    for scen in scenarios:
        hdr += f"  {scen:12s}"
    print(hdr)
    print(f"  {'  V  /  M  /  A':}")

    for btype in BOARD_TYPE_ORDER:
        print(f"\n  {btype}")
        row = f"  {'':14s}"
        for scen in scenarios:
            boards = data.get(scen, {}).get("boards", {})
            b = boards.get(btype)
            if not b:
                row += f"  {'N/A':12s}"
                continue
            f_off = b.get("flop_offense", {})
            bs = f_off.get("bucket_summary", {})
            # バリュー、マージナル、エアーのベット率合計
            def bet_pct(bkt):
                d = bs.get(bkt, {})
                return sum(v for k, v in d.items() if k != "check" and v is not None)

            v_pct = bet_pct("V")
            m_pct = bet_pct("M")
            a_pct = bet_pct("A")
            row += f"  {v_pct:3.0f}/{m_pct:3.0f}/{a_pct:3.0f}    "
        print(row)


# ════════════════════════════════════════════════════════════════
# 2. OOP Foldレート：シナリオ × ボード型
# ════════════════════════════════════════════════════════════════

def report_oop_fold(data: dict):
    print("\n" + "=" * 80)
    print("★ OOP Fold率（IP CBet後のOOP fold率）")
    print("  バケット: V(バリュー) / M(マージナル) / A(エアー)")
    print("=" * 80)

    scenarios = [s for s in SCENARIO_ORDER if s in data]

    hdr = f"  {'ボード型':14s}"
    for scen in scenarios:
        hdr += f"  {scen:16s}"
    print(hdr)
    print(f"  {'':14s}" + "".join(f"  {'V/M/A fold':16s}" for _ in scenarios))

    for btype in BOARD_TYPE_ORDER:
        row = f"  {btype:14s}"
        for scen in scenarios:
            boards = data.get(scen, {}).get("boards", {})
            b = boards.get(btype)
            if not b or not b.get("flop_defense"):
                row += f"  {'N/A':16s}"
                continue
            f_def = b["flop_defense"]
            bs = f_def.get("bucket_summary", {})

            def fold_pct(bkt):
                return bs.get(bkt, {}).get("fold", 0) or 0

            v_f = fold_pct("V")
            m_f = fold_pct("M")
            a_f = fold_pct("A")
            row += f"  {v_f:3.0f}/{m_f:3.0f}/{a_f:3.0f}         "
        print(row)


# ════════════════════════════════════════════════════════════════
# 3. ターンバレル率：ボード型 × ターンタグ × シナリオ
# ════════════════════════════════════════════════════════════════

def report_turn_barrel(data: dict):
    print("\n" + "=" * 80)
    print("★ ターンバレル率（IP: V/M/A）")
    print("  行=ボード型+ターンタグ / 列=シナリオ")
    print("=" * 80)

    scenarios = [s for s in SCENARIO_ORDER if s in data]

    hdr = f"  {'ボード型':12s} {'タグ':12s}"
    for scen in scenarios:
        hdr += f" {scen[:9]:>10s}"
    print(hdr)
    print(f"  {'':24s}" + "".join(f" {'V/M/A':>10s}" for _ in scenarios))

    for btype in BOARD_TYPE_ORDER:
        # ターンタグの一覧を最初のシナリオから取得
        tags_seen = []
        for scen in scenarios:
            boards = data.get(scen, {}).get("boards", {})
            b = boards.get(btype)
            if b and b.get("turns"):
                for t in b["turns"]:
                    tag = t.get("tag", "")
                    if tag not in tags_seen:
                        tags_seen.append(tag)
                break

        for tag in tags_seen:
            row = f"  {btype[:12]:12s} {tag[:12]:12s}"
            for scen in scenarios:
                boards = data.get(scen, {}).get("boards", {})
                b = boards.get(btype)
                if not b or not b.get("turns"):
                    row += f" {'N/A':>10s}"
                    continue
                turn = next((t for t in b["turns"] if t.get("tag") == tag), None)
                if not turn or not turn.get("ip_barrel"):
                    row += f" {'N/A':>10s}"
                    continue
                ib = turn["ip_barrel"]
                v = (ib.get("V") or 0) * 100
                m = (ib.get("M") or 0) * 100
                a = (ib.get("A") or 0) * 100
                row += f" {v:2.0f}/{m:2.0f}/{a:2.0f}  "
            print(row)
        print()


# ════════════════════════════════════════════════════════════════
# 4. TA+/-効果：blank対比でのバレル率変化
# ════════════════════════════════════════════════════════════════

def report_ta_effect(data: dict):
    print("\n" + "=" * 80)
    print("★ TA+/-効果：blank対比でのIPバレル率変化（Vバリューのみ）")
    print("=" * 80)

    scenarios = [s for s in SCENARIO_ORDER if s in data]
    print(f"  {'ボード型':14s} {'ターン':8s} {'タグ':12s}", end="")
    for scen in scenarios:
        print(f"  {scen[:8]:>8s}", end="")
    print()

    for btype in BOARD_TYPE_ORDER:
        # blankのV%を基準として差分を計算
        blank_vals = {}
        for scen in scenarios:
            boards = data.get(scen, {}).get("boards", {})
            b = boards.get(btype)
            if not b or not b.get("turns"):
                continue
            blank_t = next((t for t in b["turns"] if t.get("tag") == "blank"), None)
            if blank_t and blank_t.get("ip_barrel"):
                blank_vals[scen] = (blank_t["ip_barrel"].get("V") or 0) * 100

        # blank行
        row = f"  {btype[:14]:14s} {'(blank)':8s} {'baseline':12s}"
        for scen in scenarios:
            v = blank_vals.get(scen)
            row += f"  {fmt_pct(v):>8s}"
        print(row)

        # 他タグの差分
        for scen in scenarios:
            boards = data.get(scen, {}).get("boards", {})
            b = boards.get(btype)
            if not b or not b.get("turns"):
                continue
            for t in b["turns"]:
                if t.get("tag") == "blank":
                    continue
                tag = t.get("tag", "")
                card = t.get("card", "")
                # 最初のシナリオだけ行頭を書く
                if scen == scenarios[0]:
                    row = f"  {'':14s} {card:8s} {tag[:12]:12s}"
                    for s2 in scenarios:
                        b2 = data.get(s2, {}).get("boards", {}).get(btype)
                        if not b2 or not b2.get("turns"):
                            row += f"  {'N/A':>8s}"
                            continue
                        t2 = next((tt for tt in b2["turns"] if tt.get("tag") == tag), None)
                        if not t2 or not t2.get("ip_barrel"):
                            row += f"  {'N/A':>8s}"
                            continue
                        v2 = (t2["ip_barrel"].get("V") or 0) * 100
                        base2 = blank_vals.get(s2)
                        d2 = v2 - base2 if base2 is not None else None
                        row += f"  {('+'+f'{d2:.0f}%') if d2 and d2 > 0 else (f'{d2:.0f}%' if d2 is not None else 'N/A'):>8s}"
                    print(row)
                    break  # 行は各タグ1回のみ
        print()


# ════════════════════════════════════════════════════════════════
# 5. シナリオ別要約表
# ════════════════════════════════════════════════════════════════

def report_scenario_summary(data: dict):
    print("\n" + "=" * 80)
    print("★ シナリオ別フロップCBet傾向サマリー")
    print("  （全ボード型の平均CBet率）")
    print("=" * 80)

    for scen in SCENARIO_ORDER:
        if scen not in data:
            continue
        boards = data[scen]["boards"]
        label = data[scen]["label"]
        print(f"\n  【{scen}】{label}")

        for btype in BOARD_TYPE_ORDER:
            b = boards.get(btype)
            if not b:
                continue
            f_off = b.get("flop_offense", {})
            bs = f_off.get("bucket_summary", {})
            def bet_total(bkt):
                d = bs.get(bkt, {})
                return sum(v for k, v in d.items() if k != "check" and v is not None)

            v_b = bet_total("V")
            m_b = bet_total("M")
            a_b = bet_total("A")

            # Turn summary: blank vs TA+ diff
            turns = b.get("turns", [])
            blank_v = None
            ta_plus_vs = []
            for t in turns:
                ib = t.get("ip_barrel") or {}
                tv = (ib.get("V") or 0) * 100
                if t.get("tag") == "blank":
                    blank_v = tv
                elif "TA+" in t.get("tag", ""):
                    ta_plus_vs.append(tv)

            ta_avg = sum(ta_plus_vs) / len(ta_plus_vs) if ta_plus_vs else None
            if ta_avg is not None and blank_v is not None:
                diff = ta_avg - blank_v
                ta_delta = f"+{diff:.0f}%" if diff > 0 else f"{diff:.0f}%"
            else:
                ta_delta = "N/A"

            print(f"    {btype:14s} | Flopbet V:{v_b:3.0f}% M:{m_b:3.0f}% A:{a_b:3.0f}%"
                  f" | TurnBarrel(blank) V:{blank_v or 0:3.0f}%  TA+効果:{ta_delta}")


def main():
    data = load_all()
    if not data:
        print("findings/ に multistreet_*.json が見つかりません")
        return

    print(f"読み込み完了: {list(data.keys())}")

    report_flop_cbet(data)
    report_oop_fold(data)
    report_turn_barrel(data)
    report_ta_effect(data)
    report_scenario_summary(data)

    print("\n\n✅ 比較レポート完了")


if __name__ == "__main__":
    main()
