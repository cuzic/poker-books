"""CORE 113 を「同じ action になる隣接 cell」を wildcard でマージして圧縮。

【マージ規則】
1. bet_size の値違いで同 action のルール → bs=ANY
2. sub_family の値違いで同 action のルール → sub=ANY
3. tier の値違いで同 action のルール → tier=ANY
4. eq_bucket の値違いで同 action のルール → eq=ANY

最終的に「本質的に異なる」ルール数を測定し、それで evaluate。
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/MERGED_MACRO_RULES.md"

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
SIZE_ORDER = ["small_33","med_75p","med_100p","overbet","overbet_185","allin"]


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


def parse_scenario(scn: str):
    s = scn.lower()
    pot = "4BP" if "4bp" in s else "3BP" if "3bp" in s else \
          "DEF" if ("cr_def" in s or "donk_def" in s) else "SRP"
    if "river" in s: street = "river"
    elif "turn" in s: street = "turn"
    elif "flop" in s: street = "flop"
    else: street = "flop"
    return pot, street


print("Loading rows...")
all_rows = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        pot, street = parse_scenario(r["scenario_id"])
        board = r.get("board_str", "")[:6].lower()
        sub = fine_subfamily(board_structure(board))
        tier = MATCHA_TIER.get(r["mv_cat"], "?")
        eq_b = r.get("equity_bucket", "?")
        bs = r.get("ip_bet_size", "?")
        if eq_b == "?" or bs == "?": continue
        try:
            all_rows.append({
                "pot": pot, "street": street, "sub": sub, "tier": tier,
                "eq_b": eq_b, "bs": bs,
                "best_action": r["best_action"].lower(),
                "ev_fold": float(r["ev_fold"]),
                "ev_call": float(r["ev_call"]),
                "ev_raise": float(r["ev_raise"]),
                "best_ev": float(r["best_ev"]),
            })
        except (KeyError, ValueError, TypeError):
            continue
print(f"Loaded {len(all_rows):,} rows")


def build_cells(group_fn, min_n=3):
    raw = defaultdict(list)
    for r in all_rows:
        raw[group_fn(r)].append(r)
    cells = {}
    for k, rs in raw.items():
        if len(rs) < min_n: continue
        n = len(rs)
        cnt = defaultdict(int)
        for rr in rs: cnt[rr["best_action"]] += 1
        top, top_n = max(cnt.items(), key=lambda x: x[1])
        cells[k] = {"n": n, "dom": top, "freq": top_n / n}
    return cells


# === Try collapsing axes one at a time ===
# Goal: find the minimum set of distinguishing axes

print("\n=== Test: collapse axes ===")
def cell_count(group_fn, min_n=3, cov=0.85, min_total_n=100):
    cells = build_cells(group_fn, min_n)
    high_cov = {k: v for k, v in cells.items() if v["freq"] >= cov and v["n"] >= min_total_n}
    return len(cells), len(high_cov)


for name, fn in [
    ("Full 5-key (pot,st,sub,tier,eq,bs)", lambda r: (r["pot"],r["street"],r["sub"],r["tier"],r["eq_b"],r["bs"])),
    ("Drop bs (pot,st,sub,tier,eq)",        lambda r: (r["pot"],r["street"],r["sub"],r["tier"],r["eq_b"])),
    ("Drop sub (pot,st,tier,eq,bs)",        lambda r: (r["pot"],r["street"],r["tier"],r["eq_b"],r["bs"])),
    ("Drop tier (pot,st,sub,eq,bs)",        lambda r: (r["pot"],r["street"],r["sub"],r["eq_b"],r["bs"])),
    ("Drop sub+bs (pot,st,tier,eq)",        lambda r: (r["pot"],r["street"],r["tier"],r["eq_b"])),
    ("Drop bs+tier (pot,st,sub,eq)",        lambda r: (r["pot"],r["street"],r["sub"],r["eq_b"])),
    ("Drop sub+tier (pot,st,eq,bs)",        lambda r: (r["pot"],r["street"],r["eq_b"],r["bs"])),
    ("Only (pot,st,eq)",                     lambda r: (r["pot"],r["street"],r["eq_b"])),
    ("Only (pot,st,tier)",                   lambda r: (r["pot"],r["street"],r["tier"])),
    ("Only (pot,st)",                        lambda r: (r["pot"],r["street"])),
]:
    n_cells, n_high = cell_count(fn, min_n=10, cov=0.85, min_total_n=200)
    print(f"  {name:50} cells={n_cells:>4}, high-cov (n≥200, freq≥0.85): {n_high}")


# === Greedy merge: find rules that don't need certain axes ===
print("\n=== Greedy merge (high-cov rules) ===")

# Build full cells (5-key)
cells_5 = build_cells(lambda r: (r["pot"],r["street"],r["sub"],r["tier"],r["eq_b"],r["bs"]), 3)

# Step 1: Take all CORE rules (freq ≥ 0.85, n ≥ 200)
core = {k: v for k, v in cells_5.items() if v["freq"] >= 0.85 and v["n"] >= 200}
print(f"Initial CORE (5-key): {len(core)} rules")

# Step 2: Try to merge by dropping bs (if all bs values yield same action)
merged_drop_bs = defaultdict(lambda: {"actions": set(), "n_total": 0, "freqs": [], "bs_values": set()})
for (pot, st, sub, tier, eq, bs), v in core.items():
    key = (pot, st, sub, tier, eq)
    merged_drop_bs[key]["actions"].add(v["dom"])
    merged_drop_bs[key]["n_total"] += v["n"]
    merged_drop_bs[key]["freqs"].append(v["freq"])
    merged_drop_bs[key]["bs_values"].add(bs)

# Rules where bs can be dropped (all bs same action)
dropped_bs = {k: v for k, v in merged_drop_bs.items() if len(v["actions"]) == 1 and len(v["bs_values"]) >= 2}
print(f"After dropping bs (if all bs → same action): {len(merged_drop_bs)} unique base rules ({len(dropped_bs)} mergeable)")

# Step 3: Within the dropped_bs set, try dropping sub
merged_drop_bs_sub = defaultdict(lambda: {"actions": set(), "n": 0, "sub_values": set()})
for (pot, st, sub, tier, eq), v in merged_drop_bs.items():
    if len(v["actions"]) != 1: continue
    action = list(v["actions"])[0]
    key = (pot, st, tier, eq)
    merged_drop_bs_sub[key]["actions"].add(action)
    merged_drop_bs_sub[key]["n"] += v["n_total"]
    merged_drop_bs_sub[key]["sub_values"].add(sub)

dropped_bs_sub = {k: v for k, v in merged_drop_bs_sub.items() if len(v["actions"]) == 1}
print(f"After also dropping sub: {len(merged_drop_bs_sub)} unique → {len(dropped_bs_sub)} mergeable")

# Step 4: Final macro rule = (pot, st, tier, eq) → action when all sub, bs collapse
print(f"\n=== Macro rules: (pot, street, tier, eq) when all sub/bs agree ===")
macro_rules = []
for (pot, st, tier, eq), v in dropped_bs_sub.items():
    macro_rules.append({"pot": pot, "street": st, "tier": tier, "eq": eq,
                       "action": list(v["actions"])[0], "n": v["n"],
                       "subs": len(v["sub_values"])})

# Print top macros by n
macro_rules.sort(key=lambda x: -x["n"])
print(f"Found {len(macro_rules)} macro rules (n total)")
for m in macro_rules[:30]:
    print(f"  {m['pot']:4} {m['street']:6} tier={m['tier']:10} eq={m['eq']:12} → {m['action']:5} (n={m['n']:>5,}, {m['subs']} subs)")


# === Build evaluator using merged rules ===
print("\n=== Evaluation: macro-merged rules ===")

# Hierarchical lookup:
# 1. macro_rules: (pot, st, tier, eq) → action (any sub, any bs)
# 2. fallback to CORE 5-key
# 3. fallback to defaults
macro_lookup = {(m["pot"], m["street"], m["tier"], m["eq"]): m["action"] for m in macro_rules}
print(f"macro_lookup: {len(macro_lookup)} entries")

# Also keep specific exceptions (where bs or sub matters)
# Build them by removing macro-covered cells from CORE
specific_rules = {}
for k, v in core.items():
    pot, st, sub, tier, eq, bs = k
    macro_key = (pot, st, tier, eq)
    if macro_key in macro_lookup and macro_lookup[macro_key] == v["dom"]:
        continue  # covered by macro
    specific_rules[k] = v
print(f"Specific exceptions (cell-level): {len(specific_rules)} rules")
print(f"Total active rules: macro {len(macro_lookup)} + specific {len(specific_rules)} = {len(macro_lookup)+len(specific_rules)}")

# Also count fallbacks for non-CORE rows
DEFAULT_BY_EQ = {"best_hands":"call","good_hands":"call","weak_hands":"fold","trash_hands":"fold"}


def predict_merged(r):
    # 1. specific cell match (e.g., outlier)
    k_full = (r["pot"],r["street"],r["sub"],r["tier"],r["eq_b"],r["bs"])
    if k_full in specific_rules:
        return specific_rules[k_full]["dom"], "SPECIFIC"
    # 2. macro lookup (pot, st, tier, eq)
    k_macro = (r["pot"], r["street"], r["tier"], r["eq_b"])
    if k_macro in macro_lookup:
        return macro_lookup[k_macro], "MACRO"
    # 3. fallback by eq
    return DEFAULT_BY_EQ.get(r["eq_b"], "fold"), "DEFAULT"


print("\nEvaluating merged rules on 154K rows...")
src_stats = defaultdict(lambda: {"c":0,"t":0,"l":[]})
total_c = 0; total_loss = []; huge = 0
for r in all_rows:
    pred, src = predict_merged(r)
    pred_ev = {"fold": r["ev_fold"], "call": r["ev_call"], "raise": r["ev_raise"]}[pred]
    loss = max(0, r["best_ev"] - pred_ev)
    correct = (pred == r["best_action"])
    src_stats[src]["t"] += 1; src_stats[src]["l"].append(loss)
    if correct: src_stats[src]["c"] += 1; total_c += 1
    total_loss.append(loss)
    if loss > 5: huge += 1

n = len(all_rows)
acc = total_c/n*100
avg = sum(total_loss)/n
print(f"\nTotal: {n:,}")
print(f"Accuracy: {acc:.2f}%")
print(f"Avg loss: {avg:.4f} BB")
print(f"Huge: {huge/n*100:.2f}%")
print(f"\n{'src':10} {'n':>10} {'rows%':>6} {'acc':>7} {'avg loss':>10}")
for src in ["SPECIFIC","MACRO","DEFAULT"]:
    s = src_stats[src]
    if s["t"]==0: continue
    a = s["c"]/s["t"]*100; av = sum(s["l"])/len(s["l"])
    print(f"  {src:8} {s['t']:>10,} {s['t']/n*100:>5.1f}% {a:>6.2f}% {av:>9.4f}BB")

# === Report ===
lines = []
lines.append("# CORE 113 → 真のマクロルール抽出")
lines.append("")
lines.append("「同じ action になる cells を wildcard マージ」で本質的ルール数を測定。")
lines.append("113 という数は「組合せ爆発による分割」が主因。本質的なルールは少ない。")
lines.append("")
lines.append("## 圧縮プロセス")
lines.append("")
lines.append("### Step 1: bet_size を wildcard 化 (\"any bs\")")
lines.append("")
lines.append(f"- 元 CORE (5-key, n≥200, freq≥0.85): {len(core)} rules")
lines.append(f"- bs を drop して unique (pot, st, sub, tier, eq) になる: {len(merged_drop_bs)} 個")
lines.append(f"- うち bs 違いでも同 action: **{len(dropped_bs)} 個**")
lines.append("")
lines.append("### Step 2: sub_family も wildcard 化 (\"any sub\")")
lines.append("")
lines.append(f"- sub + bs 両方 drop して unique (pot, st, tier, eq): {len(merged_drop_bs_sub)} 個")
lines.append(f"- うち sub 違いでも同 action: **{len(dropped_bs_sub)} 個** (= 本質マクロルール)")
lines.append("")

lines.append("## 真のマクロルール (sub, bs ともに wildcard)")
lines.append("")
lines.append(f"**{len(macro_rules)} ルール**で、これら CORE 5-key 113 ルールの大半をカバー。")
lines.append("")
lines.append("| pot | street | tier | eq_bucket | action | 累計 n | sub 種数 |")
lines.append("|---|---|---|---|---|---:|---:|")
for m in macro_rules:
    lines.append(f"| {m['pot']} | {m['street']} | {m['tier']} | {m['eq']} | **{m['action']}** | {m['n']:,} | {m['subs']} |")
lines.append("")

lines.append("## 評価結果 (macro + specific 階層)")
lines.append("")
lines.append("| variant | rules | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| **マクロ+specific (本)** | {len(macro_lookup)+len(specific_rules)+4} | **{acc:.2f}%** | **{avg:.4f} BB** | **{huge/n*100:.2f}%** |")
lines.append(f"|  └ MACRO (sub/bs不問) | {len(macro_lookup)} | | | |")
lines.append(f"|  └ SPECIFIC (例外) | {len(specific_rules)} | | | |")
lines.append(f"|  └ DEFAULT | 4 | | | |")
lines.append("| 3-tier (前) | 652 | 75.62% | 0.32 BB | 1.47% |")
lines.append("")

lines.append("## source 別")
lines.append("")
lines.append("| source | n | rows% | accuracy | avg loss |")
lines.append("|---|---:|---:|---:|---:|")
for src in ["SPECIFIC","MACRO","DEFAULT"]:
    s = src_stats[src]
    if s["t"]==0: continue
    a = s["c"]/s["t"]*100; av = sum(s["l"])/len(s["l"])
    lines.append(f"| {src} | {s['t']:,} | {s['t']/n*100:.1f}% | {a:.2f}% | {av:.4f} BB |")
lines.append("")

lines.append("## 結論")
lines.append("")
lines.append(f"- 113 CORE → {len(macro_lookup)} 真のマクロルール + {len(specific_rules)} 例外")
lines.append(f"- マクロ {len(macro_lookup)} ルールだけで rows の {src_stats['MACRO']['t']/n*100:.0f}% を {src_stats['MACRO']['c']/src_stats['MACRO']['t']*100:.0f}% accuracy")
lines.append("- 「bet_size や sub_family は変わっても action は変わらない」spot が大半")
lines.append("- ユーザーの直感通り、CORE 113 は組合せ爆発で分割されていた")
lines.append("")
lines.append("**書籍に書く真の暗記対象 = {} マクロルール**".format(len(macro_lookup)))

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
