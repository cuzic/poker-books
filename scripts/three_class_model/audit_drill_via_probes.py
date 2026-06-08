"""drill decision cards を probe data (summary) で監査。

per-combo データ展開は不要、高レベル check:
- drill card の board × scenario を probe dir から探す
- drill 推奨 action (BET/CALL/FOLD/RAISE) が GTO majority と一致するか確認
- frequency と sizing も比較

入力:
- /home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill_btn_cbet/*.json (Hero attacker)
- /home/cuzic/poker-books/knowledges/gto_wizard_study/probe_drill_bb_defense/*.json (Hero defender)
- /home/cuzic/poker-books/knowledges/gto_wizard_study/probe_3bp_4bp/*.json (3BP/4BP)
- /home/cuzic/poker-drill/src/data/matcha-framework-*-decisions-cards.ts (drill cards)

出力: knowledges/gto_wizard_study/AUDIT_DRILL_VIA_PROBES.md
"""
from __future__ import annotations
import csv, json, re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GTOW = REPO_ROOT / "knowledges/gto_wizard_study"
DRILL = Path("/home/cuzic/poker-drill/src/data")
OUTPUT = GTOW / "AUDIT_DRILL_VIA_PROBES.md"

SUIT_MAP = {"♠": "s", "♥": "h", "♦": "d", "♣": "c"}


def parse_board(s: str | None) -> list[str] | None:
    if not s: return None
    s = re.sub(r"\([^)]*\)", "", s)
    parts = re.findall(r"[\dATJQK]0?[♠♥♦♣]", s)
    cards = []
    for p in parts:
        rank = "T" if p[0]=="1" else p[0]
        suit_ch = p[2] if p[0]=="1" else p[1]
        suit = SUIT_MAP.get(suit_ch)
        if suit is None: return None
        cards.append(f"{rank}{suit}")
    return cards if cards else None


def extract_cards(ts: Path) -> list[dict]:
    txt = ts.read_text()
    m = re.search(r"export const \w+ = (\[.*\])\s+satisfies", txt, re.S)
    if not m: return []
    try: return json.loads(m.group(1))
    except: return []


def drill_action(answer: str) -> str | None:
    a = answer.strip()
    if re.search(r"^FOLD", a, re.I): return "FOLD"
    if re.search(r"オールイン|all-?in|jam", a, re.I): return "RAISE"
    if re.search(r"^チェックレイズ|^CR|check.?raise", a, re.I): return "RAISE"
    if re.search(r"^レイズ|raise|3-?bet|4-?bet", a, re.I): return "RAISE"
    if re.search(r"^ベット|bet", a, re.I): return "BET"
    if re.search(r"^コール|^call", a, re.I): return "CALL"
    if re.search(r"^チェック|^check", a, re.I): return "CHECK"
    return None


def hero_role(scenario_text: str) -> str:
    """drill scenario から hero の role を推定 (attacker / defender)。"""
    txt = scenario_text
    if re.search(r"BB.?check|BB の番.*BTN", txt) or re.search(r"checks?\W*$", txt):
        # BB が hero、check → defender? or BTN attacker?
        pass
    if re.search(r"cbet|3.?バレル|2.?バレル", txt, re.I):
        # facing cbet → defender
        return "defender"
    if re.search(r"BB.?の番", txt):
        return "defender"
    # BTN が action → attacker
    if re.search(r"Hero.*アクション", txt):
        return "attacker"
    return "unknown"


def load_probe_summary(prefix_dir: Path) -> dict[str, list[dict]]:
    """flop → [actions list (action_type, total_freq, betsize)]"""
    out: dict[str, list[dict]] = {}
    for f in sorted(prefix_dir.glob("*.json")):
        saved = json.loads(f.read_text())
        flop = (saved.get("flop") or "").lower()
        if not flop: continue
        actions = saved.get("data", {}).get("action_solutions", [])
        out[flop] = [
            {
                "type": a["action"]["type"],
                "display": a["action"]["display_name"],
                "betsize": a["action"]["betsize"],
                "freq": a.get("total_frequency", 0),
                "ev": a.get("total_ev", 0),
            }
            for a in actions
        ]
    return out


def best_action(actions: list[dict]) -> tuple[str, float, str]:
    """最頻 action type を返す。 (type, freq, sizing or None)"""
    by_type: dict[str, float] = defaultdict(float)
    sizes_by_type: dict[str, list[tuple[str, float]]] = defaultdict(list)
    for a in actions:
        t = a["type"]
        by_type[t] += a["freq"]
        sizes_by_type[t].append((a["betsize"], a["freq"]))
    if not by_type:
        return "?", 0, ""
    best = max(by_type.items(), key=lambda x: x[1])
    sizes = sorted(sizes_by_type[best[0]], key=lambda x: -x[1])
    return best[0], best[1], sizes[0][0] if sizes else ""


def action_match(drill: str, gto_type: str) -> bool:
    """drill action と GTO action type が一致するか。"""
    # BET / RAISE は同義扱い
    aggressive = ("BET", "RAISE")
    if drill in aggressive and gto_type in aggressive: return True
    if drill == "CHECK" and gto_type == "CHECK": return True
    if drill == "CALL" and gto_type == "CALL": return True
    if drill == "FOLD" and gto_type == "FOLD": return True
    return False


def main():
    btn_cbet = load_probe_summary(GTOW / "probe_drill_btn_cbet")
    bb_def = load_probe_summary(GTOW / "probe_drill_bb_defense")
    threebp = load_probe_summary(GTOW / "probe_3bp_4bp")
    print(f"BTN cbet probes: {len(btn_cbet)} flops")
    print(f"BB defense probes: {len(bb_def)} flops")
    print(f"3BP/4BP probes: {len(threebp)} flops")

    # categorize drill cards
    cards_audit: list[dict] = []
    for ts in sorted(DRILL.glob("matcha-framework-*-decisions-cards.ts")):
        deck = ts.stem.replace("-cards", "")
        for card in extract_cards(ts):
            scenario = card.get("front", {}).get("scenario", "")
            board_s = card.get("front", {}).get("board")
            answer = card.get("back", {}).get("answer", "")
            board = parse_board(board_s)
            if not board:
                cards_audit.append({"card_id": card.get("id"), "deck": deck, "match": False, "reason": "no_board"})
                continue
            flop = "".join(board[:3]).lower()
            d_act = drill_action(answer)
            if d_act is None:
                cards_audit.append({"card_id": card.get("id"), "deck": deck, "match": False, "reason": "drill_action_unparseable"})
                continue
            role = hero_role(scenario)

            # ルックアップ: deck 名で SRP/3BP/4BP 判定
            is_3bp = "3bet" in deck or "3BP" in scenario
            is_4bp = "4bet" in deck or "4BP" in scenario
            if is_4bp or is_3bp:
                source = "3BP" if is_3bp else "4BP"
                # 3BP/4BP は BB OOP first-action only (we don't have BTN cbet probes for 3BP/4BP)
                acts = threebp.get(flop, [])
            elif role == "attacker":
                source = "btn_cbet"
                acts = btn_cbet.get(flop, [])
            elif role == "defender":
                source = "bb_defense"
                acts = bb_def.get(flop, [])
            else:
                source = "unknown_role"
                acts = btn_cbet.get(flop, [])  # default attacker
            if not acts:
                cards_audit.append({"card_id": card.get("id"), "deck": deck, "match": False, "reason": f"no_probe ({source}, flop={flop})"})
                continue
            gto_t, gto_freq, gto_size = best_action(acts)
            correct = action_match(d_act, gto_t)
            cards_audit.append({
                "card_id": card.get("id"),
                "deck": deck,
                "match": True,
                "source": source,
                "role": role,
                "flop": flop,
                "drill_action": d_act,
                "gto_action": gto_t,
                "gto_freq": round(gto_freq, 3),
                "gto_size": gto_size,
                "correct": correct,
                "answer_short": answer[:40],
            })

    # Summary
    matched = [c for c in cards_audit if c.get("match")]
    unmatched = [c for c in cards_audit if not c.get("match")]
    print(f"\n=== Overall ===")
    print(f"  total: {len(cards_audit)}")
    print(f"  matched: {len(matched)} ({100*len(matched)/len(cards_audit):.1f}%)")
    if matched:
        n_correct = sum(1 for c in matched if c["correct"])
        print(f"  accuracy: {100*n_correct/len(matched):.1f}% ({n_correct}/{len(matched)})")

    by_deck: dict[str, list] = defaultdict(list)
    for c in cards_audit:
        by_deck[c["deck"]].append(c)
    print(f"\n=== Per deck ===")
    for deck, cs in sorted(by_deck.items()):
        m = [c for c in cs if c.get("match")]
        if not m:
            print(f"  {deck:50} total={len(cs)} match=0")
            continue
        ok = sum(1 for c in m if c["correct"])
        print(f"  {deck:50} total={len(cs)} match={len(m)} ({100*len(m)/len(cs):.0f}%) acc={100*ok/len(m):.0f}%")

    # Reasons for unmatched
    reasons: dict[str, int] = defaultdict(int)
    for c in unmatched:
        r = c.get("reason", "?").split(":")[0].split(" ")[0]
        reasons[r] += 1
    print(f"\n=== Unmatched reasons ===")
    for r, n in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {r}: {n}")

    # Wrong answers (drill != gto)
    wrong = sorted([c for c in matched if not c["correct"]], key=lambda x: x["deck"])
    print(f"\n=== Wrong predictions (drill != GTO majority): {len(wrong)} ===")
    for c in wrong[:30]:
        print(f"  [{c['deck'][:35]:35}] {c['card_id']:12} drill={c['drill_action']:5} GTO={c['gto_action']:6} ({c['gto_freq']*100:.0f}%, size={c['gto_size']}) | {c['answer_short']}")

    # Write report
    lines = []
    lines.append("# drill audit via probe data (high-level、per-action summary)")
    lines.append("")
    lines.append("ロジック未知の検算者は、各カード裏面の reference 表を見て答えに辿れるが、")
    lines.append("そもそも drill 推奨答え自体が GTO と一致するかの monetization audit。")
    lines.append("")
    lines.append("## サマリー")
    lines.append(f"- total cards: {len(cards_audit)}")
    lines.append(f"- matched: {len(matched)}")
    if matched:
        n_correct = sum(1 for c in matched if c["correct"])
        lines.append(f"- accuracy: **{100*n_correct/len(matched):.1f}%**")
    lines.append("")
    lines.append("## per-deck")
    lines.append("| deck | total | matched | acc |")
    lines.append("|------|---:|---:|---:|")
    for deck, cs in sorted(by_deck.items()):
        m = [c for c in cs if c.get("match")]
        n = len(cs)
        if not m:
            lines.append(f"| {deck} | {n} | 0 | N/A |")
            continue
        ok = sum(1 for c in m if c["correct"])
        lines.append(f"| {deck} | {n} | {len(m)} | {100*ok/len(m):.0f}% |")
    lines.append("")
    lines.append("## wrong predictions (top 20)")
    lines.append("| deck | card | drill | GTO | freq | size | answer |")
    lines.append("|------|------|-------|-----|---:|------|--------|")
    for c in wrong[:20]:
        lines.append(f"| {c['deck']} | {c['card_id']} | {c['drill_action']} | {c['gto_action']} | {c['gto_freq']*100:.0f}% | {c['gto_size']} | {c['answer_short']} |")
    OUTPUT.write_text("\n".join(lines))
    print(f"\n📄 report: {OUTPUT}")


if __name__ == "__main__":
    main()
