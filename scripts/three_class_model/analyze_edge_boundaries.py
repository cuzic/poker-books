"""エッジケース probe data を分析 — specific hand の equity / 行動を抽出。"""
from __future__ import annotations
import json
from pathlib import Path
from collections import defaultdict

DIR = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/probe_edge_boundaries")
OUT = Path("/home/cuzic/poker-books/knowledges/gto_wizard_study/EDGE_BOUNDARIES_ANALYSIS.md")

# Combo encoding (rank-major, SUITS="cdhs")
RANKS = "23456789TJQKA"
SUITS = "cdhs"


def combo_to_cards(idx: int) -> tuple[str, str]:
    """1326 unique combos, idx 0..1325."""
    # idx = c1 * 51 + c2 (offset by skipping c1)
    # Actually combinations: C(52, 2) = 1326
    # We use rank-major enumeration: card_a < card_b
    cards = []
    for r in range(13):
        for s in range(4):
            cards.append(RANKS[r] + SUITS[s])
    # 52 cards, 1326 combos
    pairs = []
    for i in range(52):
        for j in range(i+1, 52):
            pairs.append((cards[i], cards[j]))
    return pairs[idx] if 0 <= idx < len(pairs) else ("?", "?")


def cards_to_combo(c1: str, c2: str) -> int:
    cards = []
    for r in range(13):
        for s in range(4):
            cards.append(RANKS[r] + SUITS[s])
    try:
        i = cards.index(c1.lower())
        j = cards.index(c2.lower())
    except ValueError:
        return -1
    if i > j: i, j = j, i
    pairs = []
    for ii in range(52):
        for jj in range(ii+1, 52):
            pairs.append(ii * 1326 + jj)  # dummy, just index
    # Compute combo index
    # combos before i: sum_{ii<i} (52 - ii - 1) = i*51 - i*(i-1)/2
    idx = i * 51 - i * (i-1) // 2 + (j - i - 1)
    return idx


def analyze_probe(f: Path) -> dict:
    saved = json.loads(f.read_text())
    label = saved["label"]
    cat = saved["category"]
    desc = saved["description"]
    board = saved["board"]
    hero = saved["hero_hand"]
    data = saved["data"]
    actions = data.get("action_solutions", [])

    action_summary = []
    # hand_categories per action_type の集計
    tier_action_pct: dict = defaultdict(lambda: defaultdict(float))
    for a in actions:
        t = a["action"]["type"]
        sz = a["action"].get("betsize", 0)
        total_fq = a.get("total_frequency", 0)
        cats = a.get("hand_categories", [])
        action_summary.append({"type": t, "size": sz, "freq": total_fq, "cats": cats})
        for c in cats:
            name = c.get("name", "")
            f_in = c.get("total_frequency", 0)
            tier_action_pct[name][(t, sz)] += f_in

    return {
        "label": label, "category": cat, "description": desc,
        "board": board, "hero_hand": hero,
        "actions": action_summary,
        "tier_action_pct": dict(tier_action_pct),
    }


# Load all probes
probes = []
for f in sorted(DIR.glob("*.json")):
    try:
        probes.append(analyze_probe(f))
    except Exception as e:
        print(f"Error {f.name}: {e}")

print(f"Loaded {len(probes)} edge case probes")

# === Build report ===
lines = []
lines.append("# エッジケース 12 spots の GTO 実測")
lines.append("")
lines.append("MATCHA 公式の判定が直感に反する瞬間を data で確認。")
lines.append("各 spot で specific hand のアクション分布を実測。")
lines.append("")

by_cat = defaultdict(list)
for p in probes:
    by_cat[p["category"]].append(p)

CAT_NAMES = {
    "A_overestimate": "A. 過大評価リスク (強い tier だが equity 低い)",
    "B_underestimate": "B. 過小評価リスク (弱い tier だが equity 高い)",
    "C_counterfeit": "C. Counterfeit / board interaction",
    "D_pot_demote": "D. Pot type で格下げ",
    "ov_boundary": "1. overpair vs 2nd pair 境界",
    "aa_slowplay": "2. AA の slowplay 境界 (board の wet 度別)",
    "low_overpair_sizing": "3. 低 overpair の sizing 境界",
    "counterfeit": "4. counterfeit / paired board 境界",
    "combo_draw": "5. combo draw 境界",
    "pot_demote": "6. Pot type で格下げ",
    "spr_shallow": "7. 浅 SPR の overpair",
}

for cat in CAT_NAMES.keys():
    if cat not in by_cat: continue
    lines.append(f"## {CAT_NAMES[cat]}")
    lines.append("")
    for p in by_cat[cat]:
        lines.append(f"### {p['label']}")
        lines.append("")
        lines.append(f"**{p['description']}**")
        lines.append(f"- board: `{p['board']}`")
        lines.append(f"- hero: `{p['hero_hand']}`")
        lines.append("")
        lines.append("**Aggregate actions (range 全体):**")
        lines.append("")
        lines.append("| action | size | freq |")
        lines.append("|---|---:|---:|")
        for a in p["actions"]:
            sz_str = f"{a['size']}bb" if a["size"] else "-"
            lines.append(f"| {a['type']} | {sz_str} | {a['freq']*100:.1f}% |")
        lines.append("")

        # Identify hero's likely tier from hero_hand
        hero = p["hero_hand"]
        h1, h2 = hero[:2].lower(), hero[2:4].lower()
        h_rank1 = h1[0].upper()
        h_rank2 = h2[0].upper()
        is_pair = h_rank1 == h_rank2
        board_lower = p["board"].lower()
        board_ranks = [board_lower[i*2].upper() for i in range(len(board_lower) // 2)]
        RANKS = "23456789TJQKA"
        likely_tier = "?"
        if is_pair:
            h_rval = RANKS.index(h_rank1)
            board_rvals = [RANKS.index(r) for r in board_ranks if r in RANKS]
            top = max(board_rvals) if board_rvals else 0
            if h_rval == top: likely_tier = "trips/set"
            elif h_rval > top: likely_tier = "overpair"
            elif h_rval in board_rvals: likely_tier = "trips"
            else:
                # check 2nd/3rd pair
                if board_rvals and h_rval > sorted(board_rvals)[-2]:
                    likely_tier = "2nd pair"
                else:
                    likely_tier = "underpair"

        lines.append(f"**Hero tier 推定**: {likely_tier}")
        lines.append("")

        # Show tier-level breakdown if hero's likely tier matches
        related_tiers = []
        if "overpair" in likely_tier: related_tiers = ["overpair"]
        elif "trips" in likely_tier or "set" in likely_tier:
            related_tiers = ["trips", "set", "fullhouse", "quads"]
        elif "2nd" in likely_tier: related_tiers = ["second_pair", "third_pair"]
        elif "underpair" in likely_tier: related_tiers = ["underpair", "low_pair"]
        else: related_tiers = ["no_made_hand", "ace_high", "king_high"]

        for tier_name in related_tiers:
            if tier_name in p["tier_action_pct"]:
                lines.append(f"**Tier `{tier_name}` の行動分布:**")
                lines.append("")
                lines.append("| action | size | freq |")
                lines.append("|---|---:|---:|")
                tier_actions = p["tier_action_pct"][tier_name]
                tot = sum(tier_actions.values())
                for (t, sz), fq in sorted(tier_actions.items()):
                    pct = fq / tot * 100 if tot else 0
                    sz_str = f"{sz}bb" if sz else "-"
                    lines.append(f"| {t} | {sz_str} | {pct:.1f}% |")
                lines.append("")

print("Writing report...")
OUT.write_text("\n".join(lines))
print(f"\n📄 {OUT}")
