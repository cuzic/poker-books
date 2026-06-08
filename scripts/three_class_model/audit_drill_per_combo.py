"""drill cards を per-combo level で GTO audit (probe data 使用)。

入力:
- knowledges/gto_wizard_study/probe_drill_btn_cbet/*.json (Hero=BTN attacker)
- knowledges/gto_wizard_study/probe_drill_bb_defense/*.json (Hero=BB defender)
- /home/cuzic/poker-drill/src/data/matcha-framework-*-decisions-cards.ts

各 drill card (board, hand, role) について:
1. probe からそのコンボの strategy[i] / evs[i] / best action を抽出
2. drill が示唆する action と比較
3. loss = best_ev - drill_action_ev を計算

出力: knowledges/gto_wizard_study/AUDIT_DRILL_PER_COMBO.md
"""
from __future__ import annotations
import csv, json, re
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GTOW = REPO_ROOT / "knowledges/gto_wizard_study"
DRILL = Path("/home/cuzic/poker-drill/src/data")
OUTPUT = GTOW / "AUDIT_DRILL_PER_COMBO.md"

# Card encoding (GTO Wizard convention, archived extract_gtow.py より)
RANKS = "23456789TJQKA"
SUITS = "cdhs"
SUIT_MAP = {"♠": "s", "♥": "h", "♦": "d", "♣": "c"}


def card_idx(name: str) -> int:
    """'Ks' → 47, '2d' → 1 等。"""
    n = name.lower()
    return RANKS.lower().index(n[0].lower()) * 4 + SUITS.index(n[1].lower())


def combo_to_cards(i: int) -> tuple[str, str] | None:
    """1326 combo idx → (card_a, card_b) like ('Ah', 'Ks')."""
    k = i
    for a in range(51):
        block = 51 - a
        if k < block:
            b = a + 1 + k
            return f"{RANKS[a//4]}{SUITS[a%4]}", f"{RANKS[b//4]}{SUITS[b%4]}"
        k -= block
    return None


def cards_to_combo(card_a: str, card_b: str) -> int:
    """('Ah', 'Ks') → combo idx."""
    a = card_idx(card_a)
    b = card_idx(card_b)
    if a > b: a, b = b, a
    # idx = sum_{a'=0..a-1}(51 - a') + (b - a - 1)
    idx = a * 51 - a * (a - 1) // 2 + (b - a - 1)
    return idx


def parse_board(s: str) -> list[str]:
    s = re.sub(r"\([^)]*\)", "", s)
    parts = re.findall(r"[\dATJQK]0?[♠♥♦♣]", s)
    cards = []
    for p in parts:
        rank = "T" if p[0]=="1" else p[0]
        suit_ch = p[2] if p[0]=="1" else p[1]
        cards.append(f"{rank}{SUIT_MAP[suit_ch]}")
    return cards


def parse_hand(s: str) -> tuple[str, str] | None:
    cards = parse_board(s)
    if len(cards) != 2: return None
    return cards[0], cards[1]


def extract_drill_cards(ts: Path) -> list[dict]:
    txt = ts.read_text()
    m = re.search(r"export const \w+ = (\[.*\])\s+satisfies", txt, re.S)
    if not m: return []
    try: return json.loads(m.group(1))
    except: return []


def drill_action(answer: str) -> str | None:
    a = answer.strip()
    if re.search(r"^FOLD", a, re.I): return "FOLD"
    if re.search(r"オールイン|all-?in|jam", a, re.I): return "RAISE"
    if re.search(r"^チェックレイズ|^CR", a, re.I): return "RAISE"
    if re.search(r"^レイズ", a, re.I): return "RAISE"
    if re.search(r"^ベット|bet", a, re.I): return "BET"
    if re.search(r"^コール", a, re.I): return "CALL"
    if re.search(r"^チェック", a, re.I): return "CHECK"
    return None


def hero_role(scenario: str, board_len: int) -> str:
    """drill scenario → 'attacker' (Hero acts first/BB checks) or 'defender' (Hero faces bet)。"""
    if re.search(r"cbet|2.?バレル|3.?バレル", scenario, re.I):
        return "defender"
    if re.search(r"BB.?の番|BTN.?の番.*cbet", scenario):
        return "defender"
    return "attacker"


def load_probes(probe_dir: Path) -> dict[str, dict]:
    """flop → probe data dict."""
    out = {}
    for f in sorted(probe_dir.glob("*.json")):
        saved = json.loads(f.read_text())
        flop = (saved.get("flop") or "").lower()
        if flop:
            out[flop] = saved.get("data", {})
    return out


def best_action_per_combo(data: dict, combo_idx: int) -> tuple[str, float, dict[str, float]]:
    """指定 combo の best action と各 action の EV。"""
    actions = data.get("action_solutions", [])
    if not actions:
        return "?", 0.0, {}
    ev_by_action: dict[str, float] = {}
    for a in actions:
        act_type = a["action"]["type"]
        evs = a.get("evs", [])
        if combo_idx < len(evs):
            ev = evs[combo_idx]
            # 同 type が複数 sizing で出る場合 (BET 33% vs BET 75% など)、最大 EV を採用
            if act_type not in ev_by_action or ev > ev_by_action[act_type]:
                ev_by_action[act_type] = ev
    if not ev_by_action:
        return "?", 0.0, {}
    best = max(ev_by_action.items(), key=lambda x: x[1])
    return best[0], best[1], ev_by_action


def is_blocked(combo_idx: int, board_cards: list[str]) -> bool:
    pair = combo_to_cards(combo_idx)
    if not pair: return True
    return pair[0].lower() in [c.lower() for c in board_cards] or pair[1].lower() in [c.lower() for c in board_cards]


def main() -> None:
    btn_cbet = load_probes(GTOW / "probe_drill_btn_cbet")
    bb_def = load_probes(GTOW / "probe_drill_bb_defense")
    threebp = load_probes(GTOW / "probe_3bp_4bp")
    print(f"Probes loaded: btn_cbet={len(btn_cbet)}, bb_defense={len(bb_def)}, 3BP/4BP={len(threebp)}")

    results: list[dict] = []

    for ts in sorted(DRILL.glob("matcha-framework-*-decisions-cards.ts")):
        deck = ts.stem.replace("-cards", "")
        for card in extract_drill_cards(ts):
            cid = card.get("id", "")
            front = card.get("front", {})
            back = card.get("back", {})
            board_s = front.get("board")
            hand_s = front.get("hand")
            answer = back.get("answer", "")
            scenario = front.get("scenario", "")

            if not board_s or not hand_s:
                results.append({"deck": deck, "cid": cid, "match": False, "reason": "no_board_or_hand"})
                continue
            board = parse_board(board_s)
            hand = parse_hand(hand_s)
            d_act = drill_action(answer)
            if not board or len(board) < 3:
                results.append({"deck": deck, "cid": cid, "match": False, "reason": "board_unparseable"})
                continue
            if not hand:
                results.append({"deck": deck, "cid": cid, "match": False, "reason": "hand_unparseable"})
                continue
            if not d_act:
                results.append({"deck": deck, "cid": cid, "match": False, "reason": "drill_action_unparseable"})
                continue
            if hand[0].lower() in [c.lower() for c in board] or hand[1].lower() in [c.lower() for c in board]:
                results.append({"deck": deck, "cid": cid, "match": False, "reason": "hand_blocked_by_board"})
                continue

            # Select probe source
            role = hero_role(scenario, len(board))
            flop_key = "".join(board[:3]).lower()
            is_3bp = "3bet" in deck
            is_4bp = "4bet" in deck
            probe: dict | None = None
            if is_3bp or is_4bp:
                # 3BP/4BP probes (placeholder — not yet hand-level wired)
                probe = None
            else:
                probe = btn_cbet.get(flop_key) if role == "attacker" else bb_def.get(flop_key)

            if not probe:
                results.append({"deck": deck, "cid": cid, "match": False, "reason": f"no_probe (role={role}, flop={flop_key})"})
                continue

            combo_idx = cards_to_combo(hand[0], hand[1])
            gto_best, gto_ev, ev_by_action = best_action_per_combo(probe, combo_idx)

            # drill action's EV
            drill_ev = ev_by_action.get(d_act, 0.0)
            # BET = RAISE in API (BET is also RAISE type)
            if d_act in ("BET", "RAISE"):
                drill_ev = max(ev_by_action.get("BET", 0.0), ev_by_action.get("RAISE", 0.0))

            loss = gto_ev - drill_ev
            # Normalize gto_best for comparison
            d_norm = "BET/RAISE" if d_act in ("BET","RAISE") else d_act
            g_norm = "BET/RAISE" if gto_best in ("BET","RAISE") else gto_best

            results.append({
                "deck": deck, "cid": cid, "match": True,
                "role": role,
                "flop": flop_key,
                "hand": f"{hand[0]}{hand[1]}",
                "drill_action": d_act,
                "drill_ev": round(drill_ev, 3),
                "gto_best": gto_best,
                "gto_ev": round(gto_ev, 3),
                "loss_bb": round(loss, 3),
                "correct": d_norm == g_norm,
                "is_huge": loss > 5.0,
                "ev_by_action": {k: round(v, 3) for k, v in ev_by_action.items()},
                "answer": answer[:40],
            })

    matched = [r for r in results if r.get("match")]
    unmatched = [r for r in results if not r.get("match")]
    print(f"\n=== Overall ===")
    print(f"  total: {len(results)}, matched: {len(matched)} ({100*len(matched)/len(results):.1f}%)")

    if matched:
        n_correct = sum(1 for r in matched if r["correct"])
        n_huge = sum(1 for r in matched if r["is_huge"])
        avg_loss = sum(r["loss_bb"] for r in matched) / len(matched)
        huge_losses = [r["loss_bb"] for r in matched if r["is_huge"]]
        avg_huge = sum(huge_losses) / len(huge_losses) if huge_losses else 0
        print(f"  accuracy: {100*n_correct/len(matched):.1f}% ({n_correct}/{len(matched)})")
        print(f"  avg loss / decision: {avg_loss:.3f} BB")
        print(f"  huge mistakes (>5 BB): {n_huge} ({100*n_huge/len(matched):.1f}%)")
        print(f"  avg huge_loss: {avg_huge:.3f} BB")

    by_deck: dict[str, list] = defaultdict(list)
    for r in results:
        by_deck[r["deck"]].append(r)
    print(f"\n=== Per deck ===")
    for d, rs in sorted(by_deck.items()):
        m = [r for r in rs if r.get("match")]
        if not m:
            print(f"  {d:50} {len(rs):>3} match=0")
            continue
        ok = sum(1 for r in m if r["correct"])
        avg_l = sum(r["loss_bb"] for r in m) / len(m)
        huge = sum(1 for r in m if r["is_huge"])
        print(f"  {d:50} {len(rs):>3} match={len(m)} ({100*len(m)/len(rs):.0f}%) acc={100*ok/len(m):.0f}% avg_loss={avg_l:.2f}BB huge={huge}")

    # Print wrong predictions
    wrong = sorted([r for r in matched if not r["correct"]], key=lambda x: -x["loss_bb"])[:20]
    print(f"\n=== Worst predictions (drill != GTO best, top 20 by loss) ===")
    for r in wrong:
        print(f"  loss={r['loss_bb']:6.2f}BB [{r['deck'][:32]:32}] {r['cid']:12} hand={r['hand']:6} drill={r['drill_action']:5}({r['drill_ev']:.2f}) gto={r['gto_best']:5}({r['gto_ev']:.2f}) | {r['answer']}")

    # Write report
    lines = []
    lines.append("# drill audit per-combo (1326 combo enumeration、GTO Wizard API データ)")
    lines.append("")
    if matched:
        n_correct = sum(1 for r in matched if r["correct"])
        avg_loss = sum(r["loss_bb"] for r in matched) / len(matched)
        huge_losses = [r["loss_bb"] for r in matched if r["is_huge"]]
        avg_huge = sum(huge_losses) / len(huge_losses) if huge_losses else 0
        lines.append("## サマリー")
        lines.append(f"- total cards: {len(results)}, matched: {len(matched)} ({100*len(matched)/len(results):.1f}%)")
        lines.append(f"- accuracy (drill_action == gto_best per-combo): **{100*n_correct/len(matched):.1f}%**")
        lines.append(f"- avg loss / decision: **{avg_loss:.3f} BB**")
        lines.append(f"- huge mistakes (>5 BB): {sum(1 for r in matched if r['is_huge'])} ({100*sum(1 for r in matched if r['is_huge'])/len(matched):.1f}%)")
        lines.append(f"- avg huge_loss: **{avg_huge:.3f} BB**")

    lines.append("\n## per-deck")
    lines.append("| deck | n | matched | acc | avg_loss | huge |")
    lines.append("|------|---:|---:|---:|---:|---:|")
    for d, rs in sorted(by_deck.items()):
        m = [r for r in rs if r.get("match")]
        if not m:
            lines.append(f"| {d} | {len(rs)} | 0 | N/A | N/A | N/A |")
            continue
        ok = sum(1 for r in m if r["correct"])
        avg_l = sum(r["loss_bb"] for r in m) / len(m)
        huge = sum(1 for r in m if r["is_huge"])
        lines.append(f"| {d} | {len(rs)} | {len(m)} | {100*ok/len(m):.0f}% | {avg_l:.2f}BB | {huge} |")

    lines.append("\n## worst predictions (top 20)")
    lines.append("| deck | card | hand | drill | drill_ev | GTO | GTO_ev | loss | answer |")
    lines.append("|------|------|------|-------|--------:|-----|-------:|----:|--------|")
    for r in wrong[:20]:
        lines.append(f"| {r['deck'][:25]} | {r['cid']} | {r['hand']} | {r['drill_action']} | {r['drill_ev']} | {r['gto_best']} | {r['gto_ev']} | {r['loss_bb']} | {r['answer']} |")

    OUTPUT.write_text("\n".join(lines))
    print(f"\n📄 {OUTPUT}")


if __name__ == "__main__":
    main()
