"""5-key ルールを 3 階層 (CORE / FALLBACK / DEFAULT) に明確化。

【設計思想】
読者の認知負荷を最小化するため、3 階層で役割分担:

1. CORE (暗記必須、~30-50 rules)
   - 最頻出 + 最高 accuracy の L1/L2 ルール
   - rows カバー率 ≥50% を目標
   - 書籍本文 + drill カード前面に掲載

2. FALLBACK (付録参照、~150-300 rules)
   - CORE で捌けない spot の精密判定
   - L3-L7 の補完ルール
   - 書籍付録、drill カード裏面に掲載

3. DEFAULT (暗記不要、4 rules)
   - 全 CORE/FALLBACK で hit しなかった spot の最終 fallback
   - equity_bucket → action の単純 mapping
   - 「迷ったらこれ」の指示

【選定基準】
- CORE: L1/L2 ルール ∧ n ≥ 200 (rows coverage 高) ∧ freq ≥ 0.85 (accuracy 高)
- FALLBACK: 残り全 L1-L7 ルール
- DEFAULT: eq_bucket → {best:call, good:call, weak:fold, trash:fold}
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/FINAL_3TIER_RULES.md"

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
                "f_action": r.get("formula_action", "").lower(),
                "f_loss": float(r.get("formula_loss", 0) or 0),
            })
        except (KeyError, ValueError, TypeError):
            continue
print(f"Loaded {len(all_rows):,} rows")


def build(group_fn, min_n=5):
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


# === Build all cell tables ===
print("\nBuilding cells...")
cells_L1 = build(lambda r: (r["pot"], r["street"], r["tier"], r["eq_b"], r["bs"]), 3)
cells_L2 = build(lambda r: (r["pot"], r["street"], r["sub"], r["eq_b"], r["bs"]), 3)
cells_L3 = build(lambda r: (r["pot"], r["street"], r["tier"], r["eq_b"]), 5)
cells_L4 = build(lambda r: (r["pot"], r["street"], r["eq_b"], r["bs"]), 5)
cells_L5a = build(lambda r: (r["pot"], r["street"], r["tier"], r["bs"]), 5)
cells_L5b = build(lambda r: (r["pot"], r["street"], r["sub"], r["eq_b"]), 5)
cells_L6 = build(lambda r: (r["pot"], r["street"], r["eq_b"]), 10)
cells_L7 = build(lambda r: (r["pot"], r["street"]), 10)


def filter_rules(cells, cov):
    return {k: v for k, v in cells.items() if v["freq"] >= cov}


# === CORE: L1/L2 with high coverage (n ≥ 200, freq ≥ 0.85) ===
print("\nSelecting CORE rules (L1/L2 with n≥200, freq≥0.85)...")
core_L1 = {k: v for k, v in cells_L1.items() if v["n"] >= 200 and v["freq"] >= 0.85}
core_L2 = {k: v for k, v in cells_L2.items() if v["n"] >= 200 and v["freq"] >= 0.85}
print(f"  CORE L1: {len(core_L1)} rules")
print(f"  CORE L2: {len(core_L2)} rules")

# === FALLBACK: remaining L1-L7 ===
fb_L1 = {k: v for k, v in filter_rules(cells_L1, 0.80).items() if k not in core_L1}
fb_L2 = {k: v for k, v in filter_rules(cells_L2, 0.80).items() if k not in core_L2}
fb_L3 = filter_rules(cells_L3, 0.80)
fb_L4 = filter_rules(cells_L4, 0.80)
fb_L5a = filter_rules(cells_L5a, 0.70)
fb_L5b = filter_rules(cells_L5b, 0.70)
fb_L6 = filter_rules(cells_L6, 0.70)
fb_L7 = filter_rules(cells_L7, 0.60)
fb_total = (len(fb_L1) + len(fb_L2) + len(fb_L3) + len(fb_L4)
            + len(fb_L5a) + len(fb_L5b) + len(fb_L6) + len(fb_L7))
print(f"  FALLBACK: {fb_total} rules")
print(f"    L1: {len(fb_L1)}, L2: {len(fb_L2)}, L3: {len(fb_L3)}, L4: {len(fb_L4)}")
print(f"    L5a: {len(fb_L5a)}, L5b: {len(fb_L5b)}, L6: {len(fb_L6)}, L7: {len(fb_L7)}")

# === DEFAULT ===
DEFAULT_BY_EQ = {"best_hands":"call","good_hands":"call","weak_hands":"fold","trash_hands":"fold"}
print(f"  DEFAULT: 4 rules (eq → action)")
print(f"  Total: {len(core_L1)+len(core_L2)+fb_total+4} rules")


def predict_3tier(r: dict) -> tuple[str, str]:
    """CORE → FALLBACK → DEFAULT の順で lookup."""
    # CORE
    k_l1 = (r["pot"], r["street"], r["tier"], r["eq_b"], r["bs"])
    if k_l1 in core_L1: return core_L1[k_l1]["dom"], "CORE_L1"
    k_l2 = (r["pot"], r["street"], r["sub"], r["eq_b"], r["bs"])
    if k_l2 in core_L2: return core_L2[k_l2]["dom"], "CORE_L2"
    # FALLBACK
    if k_l1 in fb_L1: return fb_L1[k_l1]["dom"], "FB_L1"
    if k_l2 in fb_L2: return fb_L2[k_l2]["dom"], "FB_L2"
    k_l3 = (r["pot"], r["street"], r["tier"], r["eq_b"])
    if k_l3 in fb_L3: return fb_L3[k_l3]["dom"], "FB_L3"
    k_l4 = (r["pot"], r["street"], r["eq_b"], r["bs"])
    if k_l4 in fb_L4: return fb_L4[k_l4]["dom"], "FB_L4"
    k_l5a = (r["pot"], r["street"], r["tier"], r["bs"])
    if k_l5a in fb_L5a: return fb_L5a[k_l5a]["dom"], "FB_L5a"
    k_l5b = (r["pot"], r["street"], r["sub"], r["eq_b"])
    if k_l5b in fb_L5b: return fb_L5b[k_l5b]["dom"], "FB_L5b"
    k_l6 = (r["pot"], r["street"], r["eq_b"])
    if k_l6 in fb_L6: return fb_L6[k_l6]["dom"], "FB_L6"
    k_l7 = (r["pot"], r["street"])
    if k_l7 in fb_L7: return fb_L7[k_l7]["dom"], "FB_L7"
    # DEFAULT
    return DEFAULT_BY_EQ.get(r["eq_b"], "fold"), "DEFAULT"


# === Evaluate ===
print("\nEvaluating 3-tier rules...")
tier_stats: dict[str, dict] = defaultdict(lambda: {"c":0,"t":0,"l":[]})
src_stats: dict[str, dict] = defaultdict(lambda: {"c":0,"t":0,"l":[]})
total_correct = 0; total_loss = []; huge = 0

for r in all_rows:
    pred, src = predict_3tier(r)
    pred_ev = {"fold": r["ev_fold"], "call": r["ev_call"], "raise": r["ev_raise"]}[pred]
    loss = max(0, r["best_ev"] - pred_ev)
    correct = (pred == r["best_action"])
    src_stats[src]["t"] += 1; src_stats[src]["l"].append(loss)
    if correct: src_stats[src]["c"] += 1; total_correct += 1
    total_loss.append(loss)
    if loss > 5: huge += 1

    if src.startswith("CORE"): tier = "CORE"
    elif src.startswith("FB"): tier = "FALLBACK"
    else: tier = "DEFAULT"
    tier_stats[tier]["t"] += 1; tier_stats[tier]["l"].append(loss)
    if correct: tier_stats[tier]["c"] += 1

n = len(all_rows)
acc = total_correct/n*100
avg = sum(total_loss)/n
h = huge/n*100
core_n = len(core_L1)+len(core_L2)
fb_n = fb_total
total_n = core_n + fb_n + 4

print(f"\n=== 3-Tier Compressed Rules ===")
print(f"  CORE: {core_n} rules")
print(f"  FALLBACK: {fb_n} rules")
print(f"  DEFAULT: 4 rules")
print(f"  Total: {total_n} rules")
print(f"\nAccuracy: {acc:.2f}%")
print(f"Avg loss: {avg:.4f} BB")
print(f"Huge: {h:.2f}%")

print(f"\n{'tier':10} {'n':>10} {'rows%':>6} {'acc':>7} {'avg loss':>10}")
for tier in ["CORE","FALLBACK","DEFAULT"]:
    s = tier_stats[tier]
    if s["t"] == 0: continue
    a = s["c"]/s["t"]*100; av = sum(s["l"])/len(s["l"])
    print(f"  {tier:8} {s['t']:>10,} {s['t']/n*100:>5.1f}% {a:>6.2f}% {av:>9.4f}BB")

# === Sort CORE rules by n (frequency × coverage) ===
core_sorted = []
for k, v in core_L1.items():
    core_sorted.append(("L1", k, v))
for k, v in core_L2.items():
    core_sorted.append(("L2", k, v))
core_sorted.sort(key=lambda x: -x[2]["n"])

# === Report ===
lines = []
lines.append("# 3 階層 ルール (CORE / FALLBACK / DEFAULT) — 暗記負荷を最小化")
lines.append("")
lines.append("読者が「いつ何を覚えるか」を明確にした 3 階層構造。")
lines.append("")
lines.append("## 階層構成")
lines.append("")
lines.append("| tier | 目的 | 選定基準 | ルール数 | 配置 |")
lines.append("|------|------|---------|---:|------|")
lines.append(f"| **CORE** | 暗記必須 | L1/L2 ∧ n≥200 ∧ freq≥0.85 | **{core_n}** | 書籍本文 + drill カード前面 |")
lines.append(f"| **FALLBACK** | 例外対応 (参照可) | L1-L7 残り | {fb_n} | 書籍付録 + drill カード裏面 |")
lines.append(f"| **DEFAULT** | catch-all | eq_bucket → action | 4 | 「迷ったらこれ」指示 |")
lines.append(f"| **合計** | | | **{total_n}** | |")
lines.append("")

lines.append("## 全体評価")
lines.append("")
lines.append("| variant | rules | accuracy | avg loss | huge% |")
lines.append("|---|---:|---:|---:|---:|")
lines.append(f"| **3-tier (本)** | {total_n} | **{acc:.2f}%** | **{avg:.4f} BB** | **{h:.2f}%** |")
lines.append("| 5-key 圧縮 | 652 | 75.60% | 0.32 BB | 1.47% |")
lines.append("| 4-key 圧縮 | 230 | 73.34% | 0.39 BB | 1.78% |")
lines.append("| 既存公式 | — | 59.46% | 1.86 BB | 9.65% |")
lines.append("")

lines.append("## 各 tier の貢献")
lines.append("")
lines.append("| tier | rows | rows% | accuracy | avg loss |")
lines.append("|---|---:|---:|---:|---:|")
for tier in ["CORE","FALLBACK","DEFAULT"]:
    s = tier_stats[tier]
    if s["t"] == 0: continue
    a = s["c"]/s["t"]*100; av = sum(s["l"])/len(s["l"])
    lines.append(f"| {tier} | {s['t']:,} | {s['t']/n*100:.1f}% | {a:.2f}% | {av:.4f} BB |")
lines.append("")

lines.append("## source 別 breakdown")
lines.append("")
lines.append("| source | n | rows% | accuracy | avg loss |")
lines.append("|---|---:|---:|---:|---:|")
for src in ["CORE_L1","CORE_L2","FB_L1","FB_L2","FB_L3","FB_L4","FB_L5a","FB_L5b","FB_L6","FB_L7","DEFAULT"]:
    s = src_stats[src]
    if s["t"] == 0: continue
    a = s["c"]/s["t"]*100; av = sum(s["l"])/len(s["l"])
    lines.append(f"| {src} | {s['t']:,} | {s['t']/n*100:.1f}% | {a:.2f}% | {av:.4f} BB |")
lines.append("")

lines.append(f"## CORE {core_n} ルール (暗記対象、frequency 順)")
lines.append("")
lines.append("**この {} ルールだけ覚えれば、全 spot の {:.0f}% を {:.0f}% accuracy で処理可能**".format(
    core_n, tier_stats['CORE']['t']/n*100, tier_stats['CORE']['c']/tier_stats['CORE']['t']*100 if tier_stats['CORE']['t'] else 0))
lines.append("")
lines.append("| # | level | pot | street | 軸1 | 軸2 | 軸3 | action | freq | n |")
lines.append("|---|---|---|---|---|---|---|---|---:|---:|")
for i, (level, k, v) in enumerate(core_sorted, 1):
    if level == "L1":
        pot, st, tier, eq, bs = k
        lines.append(f"| {i} | L1 | {pot} | {st} | tier={tier} | eq={eq} | bs={bs} | **{v['dom']}** | {v['freq']*100:.0f}% | {v['n']:,} |")
    else:
        pot, st, sub, eq, bs = k
        lines.append(f"| {i} | L2 | {pot} | {st} | sub={sub} | eq={eq} | bs={bs} | **{v['dom']}** | {v['freq']*100:.0f}% | {v['n']:,} |")
lines.append("")

lines.append("## DEFAULT ルール (4 個、暗記不要だが指示として明示)")
lines.append("")
lines.append("| eq_bucket | action |")
lines.append("|-----------|--------|")
for eq, act in DEFAULT_BY_EQ.items():
    lines.append(f"| {eq} | {act} |")
lines.append("")

lines.append("## drill / 書籍への反映プラン")
lines.append("")
lines.append(f"### Phase 1 (即時、最低限の実用化)")
lines.append(f"- CORE {core_n} ルールを drill 1 deck (1 カード = 1 ルール) として作成")
lines.append(f"- 書籍 Vol2 巻末「決定論的判定表」に CORE のみ掲載")
lines.append(f"- 読者は CORE だけで {tier_stats['CORE']['t']/n*100:.0f}% の spot を捌ける")
lines.append("")
lines.append(f"### Phase 2 (詳細版)")
lines.append(f"- FALLBACK {fb_n} ルールを drill 第 2 deck + 書籍付録")
lines.append(f"- CORE + FALLBACK で {(tier_stats['CORE']['t']+tier_stats['FALLBACK']['t'])/n*100:.0f}% の spot")
lines.append("")
lines.append(f"### Phase 3 (catch-all)")
lines.append(f"- DEFAULT 4 ルールは指示として目立つ位置に掲載")
lines.append(f"- 「CORE/FALLBACK で迷ったら DEFAULT を見る」flow")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
