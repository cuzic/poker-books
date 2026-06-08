"""4-key cell (sub × tier × eq_bucket) からマクロルール抽出 + 評価。

【ルール階層】(優先度 降順)
- Type A: (pot, street, tier, eq_bucket) → action [3-key partition の最具体]
- Type B: (pot, street, sub, eq_bucket) → action [board × eq]
- Type C: (pot, street, eq_bucket) → action [equity 単独]
- Type D: (pot, street, tier) → action [旧 tier-based]
- Type E: (pot, street, sub) → action [board-based]
- Type F: (pot, street) → action [meta]
- Default: equity-based fallback (best→call, good→call, weak→fold, trash→fold)

各レイヤーで coverage ≥80% (or 60% for meta) を満たすルールを採用。
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/MEMORIZABLE_RULES_4KEY.md"

MATCHA_TIER = {
    "fullhouse":"ナッツメイド","quads":"ナッツメイド","straight_flush":"ナッツメイド",
    "set":"ストロング","trips":"ストロング","straight":"ストロング","flush":"ストロング",
    "two_pair":"ツーペア",
    "top_pair":"トップペア以上","overpair":"トップペア以上",
    "second_pair":"ミドルペア","third_pair":"ミドルペア","underpair":"ミドルペア","low_pair":"ミドルペア",
    "no_made_hand":"エア","king_high":"エア","ace_high":"エア",
}
TIER_ORDER = ["ナッツメイド","ストロング","ツーペア","トップペア以上","ミドルペア","エア"]
EQ_ORDER = ["best_hands","good_hands","weak_hands","trash_hands"]


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
    else: street = "flop"
    return {"pot": pot, "street": street}


print("Loading rows...")
all_rows = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        scn_info = parse_scenario(r["scenario_id"])
        board = r.get("board_str", "")[:6].lower()
        sub = fine_subfamily(board_structure(board))
        tier = MATCHA_TIER.get(r["mv_cat"], "?")
        eq_b = r.get("equity_bucket", "?")
        if eq_b == "?": continue
        try:
            best_action = r["best_action"].lower()
            ev_fold = float(r["ev_fold"])
            ev_call = float(r["ev_call"])
            ev_raise = float(r["ev_raise"])
            best_ev = float(r["best_ev"])
            f_action = r.get("formula_action", "").lower()
            f_loss = float(r.get("formula_loss", 0) or 0)
        except (KeyError, ValueError, TypeError):
            continue
        all_rows.append({
            "pot": scn_info["pot"], "street": scn_info["street"],
            "sub": sub, "tier": tier, "eq_b": eq_b,
            "best_action": best_action,
            "ev_fold": ev_fold, "ev_call": ev_call, "ev_raise": ev_raise,
            "best_ev": best_ev, "f_action": f_action, "f_loss": f_loss,
        })

print(f"Loaded {len(all_rows):,} rows with equity data")


# === Build cells at each grouping level ===
def build(group_fn, min_n=10):
    raw = defaultdict(list)
    for r in all_rows:
        raw[group_fn(r)].append(r)
    cells = {}
    for k, rs in raw.items():
        if len(rs) < min_n: continue
        n = len(rs)
        # best action by row count (best_action is already per-row, count majority)
        action_counts = defaultdict(int)
        for r in rs:
            action_counts[r["best_action"]] += 1
        top, top_n = max(action_counts.items(), key=lambda x: x[1])
        cells[k] = {"n": n, "dom": top, "freq": top_n / n}
    return cells


def extract_rules(cells: dict, group_keys: tuple, all_keys: tuple, cov_threshold: float = 0.8):
    """group_keys (e.g., (pot, street, tier, eq_b)) ベースのルール抽出。
    coverage = 同 (group) 内で dom が一致する割合。"""
    rules: dict[tuple, dict] = {}
    for key, c in cells.items():
        if c["freq"] >= cov_threshold:
            rules[key] = {"action": c["dom"], "freq": c["freq"], "n": c["n"]}
    return rules


print("\n=== Building cells at each level ===")
cells_a = build(lambda r: (r["pot"], r["street"], r["tier"], r["eq_b"]), 5)
cells_b = build(lambda r: (r["pot"], r["street"], r["sub"], r["eq_b"]), 5)
cells_c = build(lambda r: (r["pot"], r["street"], r["eq_b"]), 10)
cells_d = build(lambda r: (r["pot"], r["street"], r["tier"]), 10)
cells_e = build(lambda r: (r["pot"], r["street"], r["sub"]), 10)
cells_f = build(lambda r: (r["pot"], r["street"]), 10)
print(f"  A (pot,st,tier,eq): {len(cells_a)} cells")
print(f"  B (pot,st,sub,eq):  {len(cells_b)} cells")
print(f"  C (pot,st,eq):      {len(cells_c)} cells")
print(f"  D (pot,st,tier):    {len(cells_d)} cells")
print(f"  E (pot,st,sub):     {len(cells_e)} cells")
print(f"  F (pot,st):         {len(cells_f)} cells")

# Extract rules at each level (coverage ≥80%, meta ≥60%)
rules_a = extract_rules(cells_a, (), (), 0.8)
rules_b = extract_rules(cells_b, (), (), 0.8)
rules_c = extract_rules(cells_c, (), (), 0.7)
rules_d = extract_rules(cells_d, (), (), 0.8)
rules_e = extract_rules(cells_e, (), (), 0.7)
rules_f = extract_rules(cells_f, (), (), 0.6)
print(f"\n=== Rules extracted (with cov threshold) ===")
print(f"  Type A: {len(rules_a)} rules")
print(f"  Type B: {len(rules_b)} rules")
print(f"  Type C: {len(rules_c)} rules")
print(f"  Type D: {len(rules_d)} rules")
print(f"  Type E: {len(rules_e)} rules")
print(f"  Type F: {len(rules_f)} rules")


# === default by eq_bucket ===
DEFAULT_BY_EQ = {
    "best_hands": "call",   # 1 of best is high freq raise / call but call covers more
    "good_hands": "call",
    "weak_hands": "fold",
    "trash_hands": "fold",
}


def predict_hierarchical(r: dict) -> tuple[str, str]:
    """階層的 lookup。優先度: A > B > C > D > E > F > default."""
    k_a = (r["pot"], r["street"], r["tier"], r["eq_b"])
    if k_a in rules_a: return rules_a[k_a]["action"], "A"
    k_b = (r["pot"], r["street"], r["sub"], r["eq_b"])
    if k_b in rules_b: return rules_b[k_b]["action"], "B"
    k_c = (r["pot"], r["street"], r["eq_b"])
    if k_c in rules_c: return rules_c[k_c]["action"], "C"
    k_d = (r["pot"], r["street"], r["tier"])
    if k_d in rules_d: return rules_d[k_d]["action"], "D"
    k_e = (r["pot"], r["street"], r["sub"])
    if k_e in rules_e: return rules_e[k_e]["action"], "E"
    k_f = (r["pot"], r["street"])
    if k_f in rules_f: return rules_f[k_f]["action"], "F"
    return DEFAULT_BY_EQ.get(r["eq_b"], "fold"), "DEFAULT"


# === Evaluate ===
print("\n=== Evaluating hierarchical compressed rules ===")
src_stats: dict[str, dict] = defaultdict(lambda: {"c": 0, "t": 0, "l": []})
total_correct = 0; total_loss = []; huge = 0
pot_stats: dict[str, dict] = defaultdict(lambda: {"c": 0, "t": 0, "l": [], "h": 0})

for r in all_rows:
    pred, src = predict_hierarchical(r)
    pred_ev = {"fold": r["ev_fold"], "call": r["ev_call"], "raise": r["ev_raise"]}[pred]
    loss = max(0, r["best_ev"] - pred_ev)
    correct = (pred == r["best_action"])
    src_stats[src]["t"] += 1; src_stats[src]["l"].append(loss)
    if correct: src_stats[src]["c"] += 1; total_correct += 1
    total_loss.append(loss)
    if loss > 5: huge += 1
    p = r["pot"]
    pot_stats[p]["t"] += 1; pot_stats[p]["l"].append(loss)
    if correct: pot_stats[p]["c"] += 1
    if loss > 5: pot_stats[p]["h"] += 1

n = len(all_rows)
acc = total_correct/n*100
avg = sum(total_loss)/n
print(f"Total: {n:,}")
print(f"Accuracy: {acc:.2f}%")
print(f"Avg loss: {avg:.4f} BB")
print(f"Huge: {huge/n*100:.2f}%")

print(f"\n{'src':10} {'n':>10} {'pct':>5} {'acc':>7} {'avg loss':>10}")
for src in ["A","B","C","D","E","F","DEFAULT"]:
    s = src_stats[src]
    if s["t"] == 0: continue
    a = s["c"]/s["t"]*100
    av = sum(s["l"])/len(s["l"])
    p = s["t"]/n*100
    print(f"  {src:8} {s['t']:>10,} {p:>4.1f}% {a:>6.2f}% {av:>9.4f}BB")

print(f"\n{'pot':6} {'n':>10} {'acc':>7} {'avg':>10} {'huge%':>7}")
for p in ["SRP","3BP","4BP","DEF"]:
    s = pot_stats[p]
    if s["t"] == 0: continue
    a = s["c"]/s["t"]*100
    av = sum(s["l"])/len(s["l"])
    h = s["h"]/s["t"]*100
    print(f"  {p:4} {s['t']:>10,} {a:>6.2f}% {av:>8.4f}BB {h:>6.2f}%")

# Formula baseline
f_correct = sum(1 for r in all_rows if r["f_action"] and r["f_action"]==r["best_action"])
f_total = sum(1 for r in all_rows if r["f_action"])
f_loss_sum = sum(r["f_loss"] for r in all_rows if r["f_action"])
f_huge = sum(1 for r in all_rows if r["f_action"] and r["f_loss"]>5)

# === Generate report ===
lines = []
lines.append("# 圧縮ルール 4-key (sub × made_tier × equity_bucket)")
lines.append("")
lines.append("MATCHA Framework の 5 軸を活用したマクロルール抽出。階層 6 レイヤー + default。")
lines.append("")
lines.append("## ルール階層")
lines.append("")
lines.append("| level | cell key | cells 数 | rules 数 (cov ≥閾値) |")
lines.append("|-------|---------|---:|---:|")
lines.append(f"| A | (pot, street, tier, **eq_bucket**) | {len(cells_a)} | {len(rules_a)} (cov ≥0.8) |")
lines.append(f"| B | (pot, street, sub, **eq_bucket**) | {len(cells_b)} | {len(rules_b)} (cov ≥0.8) |")
lines.append(f"| C | (pot, street, **eq_bucket**) | {len(cells_c)} | {len(rules_c)} (cov ≥0.7) |")
lines.append(f"| D | (pot, street, tier) | {len(cells_d)} | {len(rules_d)} (cov ≥0.8) |")
lines.append(f"| E | (pot, street, sub) | {len(cells_e)} | {len(rules_e)} (cov ≥0.7) |")
lines.append(f"| F | (pot, street) | {len(cells_f)} | {len(rules_f)} (cov ≥0.6) |")
total_rules = len(rules_a)+len(rules_b)+len(rules_c)+len(rules_d)+len(rules_e)+len(rules_f)
lines.append(f"| Default | eq_bucket → action map | — | 4 |")
lines.append(f"| **合計** | | | **{total_rules + 4}** |")
lines.append("")

lines.append("## 評価結果")
lines.append("")
f_acc = f_correct/f_total*100 if f_total else 0
f_avg = f_loss_sum/f_total if f_total else 0
f_h = f_huge/f_total*100 if f_total else 0
lines.append("| variant | rules | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| **4-key 圧縮 (本ルール)** | {total_rules+4} | **{acc:.2f}%** | **{avg:.4f} BB** | **{huge/n*100:.2f}%** |")
lines.append(f"| フル 4-key lookup | 556 | 78.13% | 0.21 BB | 0.82% |")
lines.append(f"| 旧 3-key 圧縮 | 51 | 63.72% | 0.88 BB | 3.43% |")
lines.append(f"| 既存公式 v9b/v10/v15 | — | {f_acc:.2f}% | {f_avg:.4f} BB | {f_h:.2f}% |")
lines.append("")

lines.append("## source 別 breakdown")
lines.append("")
lines.append("| source | n | rows% | accuracy | avg loss |")
lines.append("|---|---:|---:|---:|---:|")
for src in ["A","B","C","D","E","F","DEFAULT"]:
    s = src_stats[src]
    if s["t"] == 0: continue
    a = s["c"]/s["t"]*100
    av = sum(s["l"])/len(s["l"])
    pc = s["t"]/n*100
    lines.append(f"| {src} | {s['t']:,} | {pc:.1f}% | {a:.2f}% | {av:.4f} BB |")
lines.append("")

lines.append("## pot type 別")
lines.append("")
lines.append("| pot | n | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
for p in ["SRP","3BP","4BP","DEF"]:
    s = pot_stats[p]
    if s["t"] == 0: continue
    a = s["c"]/s["t"]*100; av = sum(s["l"])/len(s["l"]); h = s["h"]/s["t"]*100
    lines.append(f"| {p} | {s['t']:,} | {a:.2f}% | {av:.4f} BB | {h:.2f}% |")
lines.append("")

lines.append("## Type A ルール一覧 (最具体: pot × street × tier × eq_bucket)")
lines.append("")
lines.append("| pot | street | tier | eq_bucket | action | freq | n |")
lines.append("|---|---|---|---|---|---:|---:|")
sorted_a = sorted(rules_a.items(), key=lambda x: (x[0][0], ["flop","turn","river"].index(x[0][1]),
                                                    TIER_ORDER.index(x[0][2]) if x[0][2] in TIER_ORDER else 99,
                                                    EQ_ORDER.index(x[0][3]) if x[0][3] in EQ_ORDER else 99))
for k, v in sorted_a:
    lines.append(f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | **{v['action']}** | {v['freq']*100:.0f}% | {v['n']:,} |")
lines.append("")

lines.append("## Type B ルール一覧 (board × eq_bucket)")
lines.append("")
lines.append("| pot | street | sub_family | eq_bucket | action | freq | n |")
lines.append("|---|---|---|---|---|---:|---:|")
sorted_b = sorted(rules_b.items(), key=lambda x: (x[0][0], ["flop","turn","river"].index(x[0][1]),
                                                    x[0][2],
                                                    EQ_ORDER.index(x[0][3]) if x[0][3] in EQ_ORDER else 99))
for k, v in sorted_b[:50]:  # top 50
    lines.append(f"| {k[0]} | {k[1]} | {k[2]} | {k[3]} | **{v['action']}** | {v['freq']*100:.0f}% | {v['n']:,} |")
if len(sorted_b) > 50:
    lines.append(f"| ... (残り {len(sorted_b)-50}) | | | | | | |")
lines.append("")

lines.append("## Type C ルール (equity 単独)")
lines.append("")
lines.append("| pot | street | eq_bucket | action | freq | n |")
lines.append("|---|---|---|---|---:|---:|")
for k, v in sorted(rules_c.items()):
    lines.append(f"| {k[0]} | {k[1]} | {k[2]} | **{v['action']}** | {v['freq']*100:.0f}% | {v['n']:,} |")
lines.append("")

lines.append("## 結論")
lines.append("")
lines.append(f"- **{total_rules+4} ルール**で accuracy **{acc:.1f}%**、loss **{avg:.3f} BB**")
lines.append(f"- フル lookup (556 cells) から {(556 - total_rules - 4):+d} cell 削減、accuracy {acc-78.13:+.1f}pp、loss {(avg-0.21)/0.21*100:+.1f}%")
lines.append(f"- 既存公式と比較: accuracy {acc-f_acc:+.1f}pp、loss {(avg-f_avg)/f_avg*100:+.1f}%")
lines.append("")
lines.append("**Sklansky Hand Groups の系譜**: 100+ hands を 8 group に圧縮した先例同様、")
lines.append("293K spots を {} ルールに圧縮。MATCHA Framework の判断式として実用十分。".format(total_rules+4))

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
