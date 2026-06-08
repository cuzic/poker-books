"""eq_bucket を人間が判定できる形に分解。

【現状の困難】
eq_bucket (best/good/weak/trash) は GTO Wizard の per-combo equity_percentile から
bucket 化された値。人間が暗算するには equity を自分で概算 + percentile 推定が必要。

【探索する proxy】
1. tier (made hand) と eq_bucket の対応 — tier だけで bucket を推定できるか?
2. tier × board_family の cross-tab — board 込みなら推定可能か?
3. hand_eq の直接判定 — equity (0-100%) を見れば bucket は決まるか?

【目標】
読者が暗算 / 簡易ルールで eq_bucket を判定できるアルゴリズム
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
OUT = ROOT / "knowledges/gto_wizard_study/EQ_BUCKET_DECODER.md"

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
        "paired": paired, "monotone": monotone, "connected": connected,
        "wet": (monotone or connected),
    }


def board_label(s):
    if not s: return "?"
    if s["paired"]: return "paired"
    if s["monotone"]: return "monotone"
    if s["connected"]: return "connected"
    return "dry"


# Load
print("Loading rows...")
rows = []
with CSV_PATH.open() as f:
    for r in csv.DictReader(f):
        tier = MATCHA_TIER.get(r["mv_cat"], None)
        eq_b = r.get("equity_bucket", "")
        if tier is None or eq_b not in EQ_ORDER: continue
        try:
            hand_eq = float(r.get("hand_eq", 0) or 0)
            perc = float(r.get("eq_percentile", 0) or 0)
        except (ValueError, TypeError):
            continue
        board = r.get("board_str", "")[:6].lower()
        bl = board_label(board_structure(board))
        rows.append({
            "tier": tier, "mv_cat": r["mv_cat"], "eq_b": eq_b,
            "hand_eq": hand_eq, "perc": perc, "board_label": bl,
        })
print(f"Loaded {len(rows):,} rows")


# === Decoder 1: tier alone → bucket ===
print("\n=== tier 単独で bucket を推定 ===")
tier_bucket = defaultdict(lambda: defaultdict(int))
for r in rows:
    tier_bucket[r["tier"]][r["eq_b"]] += 1
print(f"{'tier':18}", end=" ")
for b in EQ_ORDER:
    print(f"{b[:8]:>10}", end=" ")
print()
for tier in TIER_ORDER:
    print(f"  {tier:16}", end=" ")
    total = sum(tier_bucket[tier].values())
    for b in EQ_ORDER:
        pct = tier_bucket[tier][b] / total * 100 if total else 0
        print(f"{pct:>9.1f}%", end=" ")
    print()


# === Decoder 2: tier × board_label → bucket ===
print("\n=== tier × board_label の cross-tab ===")
tb_bucket = defaultdict(lambda: defaultdict(int))
for r in rows:
    tb_bucket[(r["tier"], r["board_label"])][r["eq_b"]] += 1

print(f"{'tier':16} {'board':10}", end=" ")
for b in EQ_ORDER: print(f"{b[:8]:>10}", end=" ")
print(f"{'modal':>12}")
typical_mapping = {}
for tier in TIER_ORDER:
    for bl in ["dry","paired","connected","monotone"]:
        d = tb_bucket[(tier, bl)]
        total = sum(d.values())
        if total < 100: continue
        print(f"  {tier:14} {bl:10}", end=" ")
        modal = max(d.items(), key=lambda x: x[1])
        for b in EQ_ORDER:
            pct = d[b] / total * 100
            print(f"{pct:>9.1f}%", end=" ")
        print(f" {modal[0]:>12}")
        typical_mapping[(tier, bl)] = modal[0]


# === Decoder 3: hand_eq → bucket (equity 単独で bucket 決まるか) ===
print("\n=== hand_eq の bucket 別分布 ===")
eq_buckets_by_range = defaultdict(lambda: defaultdict(int))
for r in rows:
    eq = r["hand_eq"]
    eq_pct = eq * 100
    # Bin equity in 10% increments
    bin_v = int(eq_pct // 10) * 10
    if bin_v >= 90: bin_v = 90
    eq_buckets_by_range[bin_v][r["eq_b"]] += 1

print(f"{'eq%':10}", end=" ")
for b in EQ_ORDER: print(f"{b[:8]:>10}", end=" ")
print(f"{'modal':>12}")
for bin_v in sorted(eq_buckets_by_range.keys()):
    d = eq_buckets_by_range[bin_v]
    total = sum(d.values())
    if total < 100: continue
    print(f"  {bin_v}-{bin_v+10:<5}", end=" ")
    modal = max(d.items(), key=lambda x: x[1])
    for b in EQ_ORDER:
        pct = d[b] / total * 100
        print(f"{pct:>9.1f}%", end=" ")
    print(f" {modal[0]:>12}")


# === Decoder 4: hand_eq → bucket 推定の精度測定 ===
# Use simple thresholds
def eq_to_bucket(eq_pct):
    if eq_pct >= 0.70: return "best_hands"
    if eq_pct >= 0.50: return "good_hands"
    if eq_pct >= 0.30: return "weak_hands"
    return "trash_hands"


correct = 0
for r in rows:
    if eq_to_bucket(r["hand_eq"]) == r["eq_b"]:
        correct += 1
print(f"\n=== Decoder 4: hand_eq の閾値 (0.30/0.50/0.70) で bucket 推定 ===")
print(f"  Accuracy: {correct/len(rows)*100:.2f}%")


# === Decoder 5: per_percentile → bucket ===
perc_bucket = defaultdict(lambda: defaultdict(int))
for r in rows:
    p = r["perc"] * 100
    bin_v = int(p // 10) * 10
    if bin_v >= 90: bin_v = 90
    perc_bucket[bin_v][r["eq_b"]] += 1

print(f"\n=== eq_percentile vs bucket ===")
print(f"{'perc%':10}", end=" ")
for b in EQ_ORDER: print(f"{b[:8]:>10}", end=" ")
print(f"{'modal':>12}")
for bin_v in sorted(perc_bucket.keys()):
    d = perc_bucket[bin_v]
    total = sum(d.values())
    if total < 100: continue
    print(f"  {bin_v}-{bin_v+10:<5}", end=" ")
    modal = max(d.items(), key=lambda x: x[1])
    for b in EQ_ORDER:
        pct = d[b] / total * 100
        print(f"{pct:>9.1f}%", end=" ")
    print(f" {modal[0]:>12}")


# === Report ===
lines = []
lines.append("# eq_bucket を人間が判定できる形に分解")
lines.append("")
lines.append("MATCHA 公式の最大の障壁 = eq_bucket (best/good/weak/trash) の判定。")
lines.append("以下、人間が暗算で eq_bucket を推定する複数アプローチを提示。")
lines.append("")

lines.append("## アプローチ 1: tier 単独で bucket を推定")
lines.append("")
lines.append("「自分の hand tier だけで eq_bucket を決められるか」")
lines.append("")
lines.append("| tier | best | good | weak | trash | modal (代表) |")
lines.append("|------|---:|---:|---:|---:|---|")
for tier in TIER_ORDER:
    d = tier_bucket[tier]
    total = sum(d.values())
    if total == 0: continue
    modal = max(d.items(), key=lambda x: x[1])
    row = f"| {tier} |"
    for b in EQ_ORDER:
        pct = d[b] / total * 100
        row += f" {pct:.0f}% |"
    row += f" **{modal[0]}** ({modal[1]/total*100:.0f}%) |"
    lines.append(row)
lines.append("")
lines.append("→ tier 単独では bucket が一意に決まらない。tier × board が必要。")
lines.append("")

lines.append("## アプローチ 2: tier × board_label の対応表 (推奨)")
lines.append("")
lines.append("board 4 種 (dry / paired / connected / monotone) × tier 6 種 = 24 cells。")
lines.append("**この表 1 枚で eq_bucket を推定可能。**")
lines.append("")
lines.append("| tier | board | best% | good% | weak% | trash% | 推定 |")
lines.append("|---|---|---:|---:|---:|---:|---|")
for tier in TIER_ORDER:
    for bl in ["dry","paired","connected","monotone"]:
        d = tb_bucket[(tier, bl)]
        total = sum(d.values())
        if total < 100: continue
        modal = max(d.items(), key=lambda x: x[1])
        row = f"| {tier} | {bl} |"
        for b in EQ_ORDER:
            pct = d[b] / total * 100
            row += f" {pct:.0f}% |"
        row += f" **{modal[0]}** |"
        lines.append(row)
lines.append("")

lines.append("## アプローチ 3: hand_eq (equity%) の閾値判定")
lines.append("")
lines.append("自分の hand 概算 equity (相手 range vs) で bucket 推定。")
lines.append("")
lines.append("| equity% | best | good | weak | trash | modal |")
lines.append("|---|---:|---:|---:|---:|---|")
for bin_v in sorted(eq_buckets_by_range.keys()):
    d = eq_buckets_by_range[bin_v]
    total = sum(d.values())
    if total < 100: continue
    modal = max(d.items(), key=lambda x: x[1])
    row = f"| {bin_v}-{bin_v+10}% |"
    for b in EQ_ORDER:
        pct = d[b] / total * 100
        row += f" {pct:.0f}% |"
    row += f" **{modal[0]}** |"
    lines.append(row)
lines.append("")
lines.append(f"**簡易ルール (equity 閾値)**: ≥70% → best, ≥50% → good, ≥30% → weak, else trash")
lines.append(f"- accuracy: **{correct/len(rows)*100:.1f}%** ({correct:,} / {len(rows):,})")
lines.append("")

lines.append("## アプローチ 4: eq_percentile (相手 range 内位置)")
lines.append("")
lines.append("「相手の hand range の中で自分の手は上位何 %?」で bucket 推定。")
lines.append("")
lines.append("| percentile | best | good | weak | trash | modal |")
lines.append("|---|---:|---:|---:|---:|---|")
for bin_v in sorted(perc_bucket.keys()):
    d = perc_bucket[bin_v]
    total = sum(d.values())
    if total < 100: continue
    modal = max(d.items(), key=lambda x: x[1])
    row = f"| {bin_v*1}-{bin_v+10}% |"
    for b in EQ_ORDER:
        pct = d[b] / total * 100
        row += f" {pct:.0f}% |"
    row += f" **{modal[0]}** |"
    lines.append(row)
lines.append("")
lines.append("**閾値**: percentile ≥ 85% → best, ≥ 65% → good, ≥ 35% → weak, else trash")
lines.append("")

lines.append("## 書籍 / drill 向けの推奨アプローチ")
lines.append("")
lines.append("### 簡易判定 (暗算用) — 2 段階")
lines.append("")
lines.append("1. **tier × board の典型表 (24 cells)** で第一推定")
lines.append("2. equity を体感で +/− 1 段補正")
lines.append("")
lines.append("### 中級者向け — equity 直接判定")
lines.append("")
lines.append("```")
lines.append("自分の hand 概算 equity (vs 相手 range) で判定:")
lines.append("- 70% 以上 → best_hands")
lines.append("- 50-70%  → good_hands")
lines.append("- 30-50%  → weak_hands")
lines.append("- 30% 未満 → trash_hands")
lines.append("```")
lines.append("")
lines.append(f"この閾値で eq_bucket 推定 **{correct/len(rows)*100:.1f}% 一致** ({correct:,}/{len(rows):,} rows)")
lines.append("")

lines.append("## 結論")
lines.append("")
lines.append("- tier 単独では bucket 判定 不可")
lines.append("- **tier × board の 24-cell 対応表** で 大半カバー")
lines.append(f"- 「equity 概算 → 閾値判定」が最も普遍的、accuracy {correct/len(rows)*100:.0f}%")
lines.append("- 書籍では (a) 24-cell 表 + (b) equity 閾値 の 2 段階提示が良い")

OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
