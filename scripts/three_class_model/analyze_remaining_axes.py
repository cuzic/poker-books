"""新規 10 spots probe (Bet Sizing + Defense + Turn/River) を tier 別に分析。"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_remaining_axes")
OUT = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/REMAINING_AXES_ANALYSIS.md")

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}


def analyze(p: Path) -> dict:
    saved = json.loads(p.read_text())
    label = saved.get("label", "?")
    axis = saved.get("axis", "?")
    board = saved.get("board", "")
    actions = saved.get("data", {}).get("action_solutions", [])

    by_action: list[dict] = []
    for a in actions:
        t = a["action"]["type"]
        sz = a["action"].get("betsize", 0)
        fq = a["total_frequency"]
        tiers: dict[str, float] = defaultdict(float)
        for cat in a.get("hand_categories", []):
            tiers[MATCHA_TIER.get(cat["name"], "?")] += cat.get("total_frequency", 0)
        by_action.append({"type": t, "size": sz, "freq": fq, "tiers": dict(tiers)})

    return {"label": label, "axis": axis, "board": board, "actions": by_action}


def main():
    by_axis: dict[str, list[dict]] = defaultdict(list)
    for f in sorted(DIR.glob("*.json")):
        r = analyze(f)
        by_axis[r["axis"]].append(r)

    tier_order = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]

    lines = []
    lines.append("# Bet Sizing / Defense / Turn-River 軸の境界 — 10 spots 実 probe")
    lines.append("")
    lines.append("2026-06-08 token で取得した 10 spots を tier 別に分析。")
    lines.append("")

    # ============ Bet Sizing ============
    lines.append("## 1. Bet Sizing 軸 (wet board cbet)")
    lines.append("")
    lines.append("BTN attacker on wet/connected boards: cbet 頻度 + sizing 選択")
    lines.append("")
    print("=== Bet Sizing (BTN cbet on wet boards) ===")
    for r in by_axis.get("BS", []):
        lines.append(f"### {r['board']} ({r['label']})")
        lines.append("")
        lines.append("| action | size | freq | エア | ミドルペア | TP+ | ツーペア | ストロング | ナッツメイド |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for a in r["actions"]:
            sz_str = f"{a['size']}bb" if a["size"] else "-"
            row = f"| {a['type']} | {sz_str} | {a['freq']*100:.0f}% |"
            for t in ["エア","ミドルペア","トップペア以上","ツーペア","ストロング","ナッツメイド"]:
                v = a["tiers"].get(t, 0)
                tier_sum = sum(a["tiers"].values())
                if tier_sum > 0:
                    row += f" {v/tier_sum*100:.0f}% |"
                else:
                    row += " — |"
            lines.append(row)
        lines.append("")
        print(f"  {r['board']}: ", end="")
        for a in r["actions"]:
            print(f"{a['type']}{a['size'] if a['size'] else ''}={a['freq']*100:.0f}% ", end="")
        print()

    lines.append("### Bet Sizing 軸の発見")
    lines.append("")
    lines.append("- **Wet/connected board は cbet 頻度激低 (2-6%)** → BTN は check-back 中心")
    lines.append("- **cbet するときは 100% pot (6.5bb) 一択** → polar attack")
    lines.append("- MATCHA の Bet Sizing 4 段階のうち、wet board では `オーバーベット (>75%)` のみ使用")
    lines.append("- → wet board の sizing 判断は **\"打つか/打たないか\"** が本質、サイズ選択は二次的")
    lines.append("")

    # ============ Defense ============
    lines.append("## 2. Defense 軸 (BB vs BTN 33% cbet)")
    lines.append("")
    lines.append("BB defender が flop 33% cbet (1.9bb) に対する fold/call/raise 分布")
    lines.append("")
    print("\n=== Defense (BB vs 33% cbet) ===")
    lines.append("| board | sub-family | fold% | call% | raise% | raise size |")
    lines.append("|---|---|---:|---:|---:|---|")
    for r in by_axis.get("DEF", []):
        fold = sum(a["freq"] for a in r["actions"] if a["type"] == "FOLD") * 100
        call = sum(a["freq"] for a in r["actions"] if a["type"] == "CALL") * 100
        raise_acts = [a for a in r["actions"] if a["type"] == "RAISE"]
        raise_freq = sum(a["freq"] for a in raise_acts) * 100
        raise_size = raise_acts[0]["size"] if raise_acts else "-"
        board = r["board"]
        sub = "MERGED" if board == "ks7d2c" else "POLAR (wet)" if board == "ts9d8c" else "CONDENSED (broadway dry)" if board == "qs7d2c" else "?"
        lines.append(f"| {board} | {sub} | {fold:.0f}% | {call:.0f}% | {raise_freq:.0f}% | {raise_size}bb |")
        print(f"  {board}: F={fold:.0f}% C={call:.0f}% R={raise_freq:.0f}% ({raise_size}bb)")
    lines.append("")

    lines.append("### Defense 軸の発見")
    lines.append("")
    lines.append("- BB は **board に関わらず ~70% defend** (fold 28-30% 一定)")
    lines.append("- **raise 頻度は board で変動**:")
    lines.append("  - dry K72: raise 12% (sizing 5bb = 2.6x cbet)")
    lines.append("  - wet T98: raise 7% (sizing 10.3bb = 5.4x cbet, much larger)")
    lines.append("  - broadway Q72: raise 6% (sizing 10.3bb)")
    lines.append("- → **CR sizing は board で変わる**: dry は小さく、wet は大きく (polar)")
    lines.append("- MATCHA 守備の判断軸として: **fold MDF は一定 (~30%)、raise は board で polar**")
    lines.append("")

    # ============ Turn/River ============
    lines.append("## 3. Turn/River 軸 (K72 progression)")
    lines.append("")
    lines.append("同 K72 flop の street ごとの IP cbet 行動")
    lines.append("")
    print("\n=== Turn/River (K72 progression) ===")
    lines.append("| street/line | action 分布 |")
    lines.append("|---|---|")
    for r in by_axis.get("TR", []):
        actions_str = " / ".join(f"{a['type']}{a['size'] if a['size'] else ''}={a['freq']*100:.0f}%" for a in r["actions"])
        line_desc = {
            "tr_K723_turn_betc": "flop bet-call → turn 3h",
            "tr_K723_turn_chk": "flop check-check → turn 3h",
            "tr_K7238_river_1barrel": "flop bet-call → turn check → river 8s",
        }.get(r["label"], r["label"])
        lines.append(f"| {line_desc} | {actions_str} |")
        print(f"  {line_desc}: {actions_str}")
    lines.append("")

    lines.append("### Turn/River 軸の発見")
    lines.append("")
    lines.append("- **flop bet-call → turn brick (3h)**: BTN check 100% — bluff を継続せず、強い手のみ次 barrel")
    lines.append("  → \"flop bet-call line\" の turn は ほぼ完全 check (薄い valued only)")
    lines.append("- **flop check-check → turn brick**: BTN delayed cbet 55% (sizing 1.9bb = 33%)")
    lines.append("  → flop check 後の turn は 半分以上 bet (range narrow されたため value 多い)")
    lines.append("- **flop bet-call → turn check → river brick**: BTN river bet 45% (sizing 2.4bb = 25%)")
    lines.append("  → 1 barrel 後の river は薄い value で small bet")
    lines.append("- MATCHA Framework に **street 別補正 (薄い valued vs bluff catch)** が必要")
    lines.append("")

    # ============ 統合 ============
    lines.append("## 4. 統合発見 — MATCHA 5 軸への影響")
    lines.append("")
    lines.append("### Bet Sizing 軸 (5 軸目) の data 裏付け")
    lines.append("")
    lines.append("| board family | dominant sizing | 解釈 |")
    lines.append("|--------------|----------------|------|")
    lines.append("| dry MERGED (K72) | small 33% (1.9bb) | range advantage, wide attack |")
    lines.append("| connected wet (T98) | overbet 100%+ (6.5bb) | polar attack, low freq |")
    lines.append("| 中間 (broadway dry) | small 33% | merged |")
    lines.append("- → MATCHA 4 段階 (small/medium/over/allin) のうち **medium (50%) はほぼ unused**")
    lines.append("- → 簡易化: **2 段階 (small ~33% / over ~100%)** で 90% カバー")
    lines.append("")
    lines.append("### Defense 軸の data 裏付け")
    lines.append("")
    lines.append("- BB MDF (fold 上限) は ~30% で board 不変")
    lines.append("- raise frequency は board で 6-12% に分布")
    lines.append("- raise size は board で 2.6x ~ 5.4x cbet (wet ほど large)")
    lines.append("")
    lines.append("### Street 別補正")
    lines.append("")
    lines.append("- flop bet → turn check はほぼ確定 (giving up bluffs)")
    lines.append("- delayed cbet (flop check → turn bet) は range narrowing で 55% bet")
    lines.append("- river thin value は small (25%) sizing")
    lines.append("- → MATCHA Framework の 3 補正に **\"line-aware sizing\"** を追加検討")

    OUT.write_text("\n".join(lines))
    print(f"\n📄 {OUT}")


if __name__ == "__main__":
    main()
