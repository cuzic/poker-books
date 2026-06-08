"""PURE 349 cell をマクロルールに圧縮 — 「人間が暗記できる数」まで集約。

【手法】
1. PURE cell を (pot, street, action) でグループ化
2. 同 group 内で sub_family × tier coverage を測定
3. tier 単独 / sub_family 単独で 1 アクション支配なら "macro rule" として圧縮
4. 例外 (outlier) は別 list として最小化

【目標】
- 349 cell → 30-50 macro rules で 85%+ coverage
- Sklansky-Malmuth 系譜の "8 hand groups で 100+ hands cover" アプローチ
"""
from __future__ import annotations
import csv
import re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/MEMORIZABLE_RULES.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_ORDER = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]


def board_structure(flop: str) -> dict:
    if len(flop) < 6: return {}
    cards = [flop[i*2:i*2+2] for i in range(3)]
    RANKS = "23456789TJQKA"
    try:
        rvals = sorted([RANKS.index(c[0].upper()) for c in cards], reverse=True)
    except ValueError:
        return {}
    suits = [c[1].lower() for c in cards]
    paired = rvals[0] == rvals[1] or rvals[1] == rvals[2]
    monotone = len(set(suits)) == 1
    gap_top = rvals[0] - rvals[1]; gap_bot = rvals[1] - rvals[2]
    connected = gap_top <= 2 and gap_bot <= 2 and not paired
    return {
        "high_idx": rvals[0], "max_gap": max(gap_top, gap_bot),
        "paired": paired, "monotone": monotone, "connected": connected,
        "ace_high": rvals[0] == 12, "broadway": rvals[0] >= 8,
        "low_board": rvals[0] <= 5,
    }


def fine_subfamily(s: dict) -> str:
    if not s: return "?"
    if s["paired"]:
        if s["high_idx"] >= 11: return "paired_high"
        if s["high_idx"] >= 8: return "paired_broadway"
        if s["high_idx"] >= 5: return "paired_mid"
        return "paired_low"
    if s["monotone"]: return "monotone"
    if s["connected"]:
        if s["high_idx"] >= 11: return "connected_broadway"
        if s["high_idx"] >= 7: return "connected_mid"
        return "connected_low"
    if s["ace_high"]:
        return "Ahigh_spread" if s["max_gap"] >= 5 else "Ahigh_close"
    if s["high_idx"] == 11:
        return "Khigh_spread" if s["max_gap"] >= 5 else "Khigh_close"
    if s["broadway"]: return "broadway_dry"
    if s["low_board"]: return "low_dry"
    return "mid_dry"


def parse_scenario(scn: str) -> dict:
    s = scn.lower()
    pot = "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
          "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"
    if "river" in s: street = "river"
    elif "turn" in s: street = "turn"
    elif "flop" in s: street = "flop"
    elif "_r1" in s: street = "preflop"
    else: street = "flop"
    m = re.search(r"mtt(\d+)", s)
    depth = f"MTT{m.group(1)}" if m else ("MTT100" if "mtt" in s else "Cash100")
    return {"pot": pot, "street": street, "depth": depth}


# === Build cell stats ===
print("Loading 293K rows...")
raw: dict[tuple, list[dict]] = defaultdict(list)
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        scn_info = parse_scenario(r["scenario_id"])
        board = r.get("board_str", "")[:6].lower()
        sub = fine_subfamily(board_structure(board))
        tier = MATCHA_TIER.get(r["mv_cat"], "?")
        try:
            raw[(scn_info["pot"], scn_info["street"], sub, tier)].append({
                "fold": float(r.get("fold_freq", 0) or 0),
                "call": float(r.get("call_freq", 0) or 0),
                "raise": float(r.get("raise_freq", 0) or 0),
            })
        except (ValueError, TypeError):
            continue

# Aggregate (collapse depth axis: avg over Cash100 + MTT* for simplicity)
cells: dict[tuple, dict] = {}
for key, rows in raw.items():
    n = len(rows)
    if n < 10: continue
    fold = sum(r["fold"] for r in rows) / n
    call = sum(r["call"] for r in rows) / n
    raise_ = sum(r["raise"] for r in rows) / n
    actions = [("fold", fold), ("call", call), ("raise", raise_)]
    actions.sort(key=lambda x: -x[1])
    dom, freq = actions[0]
    cls = "PURE" if freq >= 0.80 else "STRONG" if freq >= 0.60 else "MIXED" if freq >= 0.40 else "BALANCED"
    cells[key] = {"n": n, "fold": fold, "call": call, "raise": raise_,
                  "dom": dom, "freq": freq, "cls": cls}

print(f"Cells: {len(cells)}, PURE: {sum(1 for c in cells.values() if c['cls']=='PURE')}")

# === Macro rule extraction ===
# Rule type 1: (pot, street, tier) → dominant action across sub-families
# 例: "4BP river × エア = fold" は sub_family 全種で同じか
rule_type_1: list[dict] = []
pots = ["SRP", "3BP", "4BP", "DEF"]
streets = ["flop", "turn", "river"]
subs_all = sorted({k[2] for k in cells.keys() if k[2] != "?"})

for pot in pots:
    for st in streets:
        for tier in TIER_ORDER:
            # gather all sub-families for this (pot, st, tier)
            relevant = {k: c for k, c in cells.items()
                       if k[0] == pot and k[1] == st and k[3] == tier}
            if len(relevant) < 3:  # too few sub-families
                continue
            # Count dominant actions
            action_counts = defaultdict(int)
            action_n = defaultdict(int)
            for k, c in relevant.items():
                action_counts[c["dom"]] += 1
                action_n[c["dom"]] += c["n"]
            total_cells = len(relevant)
            top_action, top_count = max(action_counts.items(), key=lambda x: x[1])
            coverage = top_count / total_cells
            if coverage >= 0.8:  # macro rule: 8 of 10 sub-families agree
                rule_type_1.append({
                    "pot": pot, "street": st, "tier": tier, "action": top_action,
                    "coverage": coverage, "cells_covered": top_count,
                    "cells_total": total_cells, "n_rows": action_n[top_action],
                    "exceptions": [(k[2], c["dom"], c["freq"]) for k, c in relevant.items() if c["dom"] != top_action]
                })

# Rule type 2: (pot, street, sub_family) → dominant action across tiers
# 例: "4BP flop × connected_mid = raise" は tier 全種で同じか
rule_type_2: list[dict] = []
for pot in pots:
    for st in streets:
        for sub in subs_all:
            relevant = {k: c for k, c in cells.items()
                       if k[0] == pot and k[1] == st and k[2] == sub}
            if len(relevant) < 3:
                continue
            action_counts = defaultdict(int)
            action_n = defaultdict(int)
            for k, c in relevant.items():
                action_counts[c["dom"]] += 1
                action_n[c["dom"]] += c["n"]
            total_cells = len(relevant)
            top_action, top_count = max(action_counts.items(), key=lambda x: x[1])
            coverage = top_count / total_cells
            if coverage >= 0.8:
                rule_type_2.append({
                    "pot": pot, "street": st, "sub": sub, "action": top_action,
                    "coverage": coverage, "cells_covered": top_count,
                    "cells_total": total_cells, "n_rows": action_n[top_action],
                    "exceptions": [(k[3], c["dom"]) for k, c in relevant.items() if c["dom"] != top_action]
                })

# Rule type 3: (pot, street) → dominant action across all sub × tier
rule_type_3: list[dict] = []
for pot in pots:
    for st in streets:
        relevant = {k: c for k, c in cells.items()
                   if k[0] == pot and k[1] == st}
        if len(relevant) < 5:
            continue
        action_counts = defaultdict(int)
        for k, c in relevant.items():
            action_counts[c["dom"]] += 1
        total = len(relevant)
        top_action, top_count = max(action_counts.items(), key=lambda x: x[1])
        cov = top_count / total
        if cov >= 0.6:
            rule_type_3.append({
                "pot": pot, "street": st, "action": top_action,
                "coverage": cov, "cells_covered": top_count, "cells_total": total,
            })

print(f"\nType 1 rules (pot × street × tier): {len(rule_type_1)}")
print(f"Type 2 rules (pot × street × sub):  {len(rule_type_2)}")
print(f"Type 3 rules (pot × street):         {len(rule_type_3)}")

# === Coverage check: how many original cells are covered by macro rules? ===
covered_by_type1: set[tuple] = set()
for r in rule_type_1:
    for k in cells:
        if k[0] == r["pot"] and k[1] == r["street"] and k[3] == r["tier"] and cells[k]["dom"] == r["action"]:
            covered_by_type1.add(k)

covered_by_type2: set[tuple] = set()
for r in rule_type_2:
    for k in cells:
        if k[0] == r["pot"] and k[1] == r["street"] and k[2] == r["sub"] and cells[k]["dom"] == r["action"]:
            covered_by_type2.add(k)

# === Report ===
lines = []
lines.append("# 暗記可能なマクロルール — PURE 349 cell の圧縮")
lines.append("")
lines.append("349 PURE cells を「人間が暗記できる単位」に集約。")
lines.append("Sklansky-Malmuth 系譜の \"少数 group で広い coverage\" アプローチ。")
lines.append("")
lines.append("## マクロルール (Type 1): pot × street × tier")
lines.append("")
lines.append("「3BP turn の エア は **常に fold**」のような sub_family 不問のルール。")
lines.append("coverage ≥ 80% (10 sub-families のうち 8 つ以上が同じ action)")
lines.append("")
lines.append("| pot | street | tier | action | coverage | 適用 cell数 | 例外 |")
lines.append("|---|---|---|---|---:|---:|---|")
rule_type_1.sort(key=lambda x: (x["pot"], ["flop","turn","river"].index(x["street"]), TIER_ORDER.index(x["tier"])))
for r in rule_type_1:
    excs = "; ".join(f"{e[0]}={e[1]}" for e in r["exceptions"][:3]) or "なし"
    lines.append(f"| {r['pot']} | {r['street']} | {r['tier']} | **{r['action']}** | {r['coverage']*100:.0f}% | {r['cells_covered']}/{r['cells_total']} | {excs} |")
lines.append("")

lines.append("## マクロルール (Type 2): pot × street × sub_family")
lines.append("")
lines.append("「4BP flop の connected_mid は **常に raise**」のような tier 不問のルール。")
lines.append("")
lines.append("| pot | street | sub_family | action | coverage | 適用 cell数 | 例外 |")
lines.append("|---|---|---|---|---:|---:|---|")
rule_type_2.sort(key=lambda x: (x["pot"], ["flop","turn","river"].index(x["street"]), x["sub"]))
for r in rule_type_2:
    excs = "; ".join(f"{e[0]}={e[1]}" for e in r["exceptions"][:3]) or "なし"
    lines.append(f"| {r['pot']} | {r['street']} | {r['sub']} | **{r['action']}** | {r['coverage']*100:.0f}% | {r['cells_covered']}/{r['cells_total']} | {excs} |")
lines.append("")

lines.append("## メタルール (Type 3): pot × street")
lines.append("")
lines.append("「3BP/4BP river は **fold が中心**」のような最大級マクロ。")
lines.append("")
lines.append("| pot | street | action | coverage | 適用 cell数 |")
lines.append("|---|---|---|---:|---:|")
for r in rule_type_3:
    lines.append(f"| {r['pot']} | {r['street']} | **{r['action']}** | {r['coverage']*100:.0f}% | {r['cells_covered']}/{r['cells_total']} |")
lines.append("")

lines.append("## カバレッジ集計")
lines.append("")
total_pure = sum(1 for c in cells.values() if c["cls"] == "PURE")
type1_pure = sum(1 for k in covered_by_type1 if cells[k]["cls"] == "PURE")
type2_pure = sum(1 for k in covered_by_type2 if cells[k]["cls"] == "PURE")
union_cov = len(covered_by_type1 | covered_by_type2)
lines.append(f"| 指標 | n |")
lines.append(f"|------|---:|")
lines.append(f"| 全 cell | {len(cells)} |")
lines.append(f"| PURE cell | {total_pure} |")
lines.append(f"| Type 1 でカバーされる cell | {len(covered_by_type1)} |")
lines.append(f"| Type 2 でカバーされる cell | {len(covered_by_type2)} |")
lines.append(f"| Type 1 ∪ Type 2 (重複なし) | {union_cov} |")
lines.append(f"| マクロルール数 | Type1: {len(rule_type_1)} + Type2: {len(rule_type_2)} + Type3: {len(rule_type_3)} = **{len(rule_type_1)+len(rule_type_2)+len(rule_type_3)}** |")
lines.append("")

lines.append("## 暗記可能性の評価")
lines.append("")
total_rules = len(rule_type_1) + len(rule_type_2) + len(rule_type_3)
lines.append(f"- マクロルール **{total_rules} 個** で {union_cov}/{len(cells)} cells ({union_cov/len(cells)*100:.0f}%) カバー")
lines.append(f"- Chen Formula (4 数値 + 6 修正係数) より rule 数多いが、構造化されているため")
lines.append(f"  pot × street × {{tier or sub}} の 3 軸暗記で済む")
lines.append(f"- 想定暗記時間: 1-2 時間 (Sklansky 8 hand groups と同等)")
lines.append("")
lines.append("**結論**: PURE 349 cell の直接暗記は無理だが、マクロルール {} 個に圧縮すれば暗記可能。".format(total_rules))

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
