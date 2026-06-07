"""drill 拡張版 MATCHA Framework (A+B+C+D) を dataset_unified_v2.csv で監査。

drill 側 (poker-drill) の decision_card scenarios を:
1. dataset の row にマッピング (board, hand, scenario context)
2. drill 推奨アクション = MATCHA framework + (A)(B)(C)(D) 拡張で導出
3. GTO best_action / best_ev と比較して loss を計算
4. per-card / per-scenario / overall で集計
5. coverage gap を可視化 (matching しない card を分類)

出力:
- 標準出力: summary table
- knowledges/gto_wizard_study/AUDIT_DRILL_EXTENSIONS.md: 詳細 report
"""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
DRILL_REPO = Path("/home/cuzic/poker-drill")
DRILL_DATA = DRILL_REPO / "src/data"
OUTPUT = REPO_ROOT / "knowledges/gto_wizard_study/AUDIT_DRILL_EXTENSIONS.md"


# ════════════════════════════════════════════════════════════
# Step 1: dataset 読み込み + index 作成 (board × hand → rows)
# ════════════════════════════════════════════════════════════


def load_dataset() -> list[dict[str, Any]]:
    print(f"Loading {DATASET}...")
    with open(DATASET) as f:
        rows = list(csv.DictReader(f))
    print(f"  {len(rows):,} rows loaded")
    return rows


def build_index(rows: list[dict]) -> dict[tuple[str, frozenset[str]], list[dict]]:
    """(board_str_lowered, frozenset({card_a, card_b})) → rows."""
    idx: dict[tuple[str, frozenset[str]], list[dict]] = defaultdict(list)
    for r in rows:
        key = (r["board_str"].lower(), frozenset({r["card_a"].lower(), r["card_b"].lower()}))
        idx[key].append(r)
    return idx


# ════════════════════════════════════════════════════════════
# Step 2: drill decision_card 抽出
# ════════════════════════════════════════════════════════════

# 注: card 内には specific suit 付きハンド (例: "A♥ K♠") が含まれる
# UNICODE suit → ascii: ♠→s, ♥→h, ♦→d, ♣→c
SUIT_MAP = {"♠": "s", "♥": "h", "♦": "d", "♣": "c"}


def normalize_card(card: str) -> str | None:
    """'K♠' → 'Ks' / 'A♥' → 'Ah'  (returns None if unparseable)."""
    card = card.strip()
    if len(card) < 2:
        return None
    rank = card[0].upper()
    if rank == "1":  # '10' を 'T' に
        return None
    suit_char = card[1] if len(card) >= 2 else None
    suit = SUIT_MAP.get(suit_char)
    if suit is None:
        return None
    return f"{rank}{suit}"


def parse_board(s: str | None) -> list[str] | None:
    """'K♠ 7♦ 2♣' or 'K♠ 7♦ 2♣ 5♥' → ['Ks', '7d', '2c', '5h']."""
    if not s:
        return None
    # remove parenthesized comments
    s = re.sub(r"\([^)]*\)", "", s)
    parts = re.findall(r"[\dATJQK]0?[♠♥♦♣]", s)
    cards = []
    for p in parts:
        if p[0] == "1":  # "10s" etc
            rank = "T"
            suit_ch = p[2]
        else:
            rank = p[0]
            suit_ch = p[1]
        suit = SUIT_MAP.get(suit_ch)
        if suit is None:
            return None
        cards.append(f"{rank}{suit}")
    return cards if cards else None


def parse_hand(s: str | None) -> tuple[str, str] | None:
    """'A♥ K♠' → ('Ah', 'Ks')."""
    if not s:
        return None
    cards = parse_board(s)
    if cards is None or len(cards) != 2:
        return None
    return cards[0], cards[1]


def extract_decision_cards(ts_path: Path) -> list[dict]:
    """`.ts` ファイルから cards (dict list) を抽出。

    出力形式: `export const <name> = [...] satisfies Card[];`
    """
    txt = ts_path.read_text()
    m = re.search(r"export const \w+ = (\[.*\])\s+satisfies", txt, re.S)
    if not m:
        m = re.search(r"export const \w+ = (\[.*\])\s*;?\s*$", txt, re.S | re.M)
    if not m:
        return []
    arr_txt = m.group(1)
    try:
        cards = json.loads(arr_txt)
    except json.JSONDecodeError as e:
        print(f"  JSON decode failed for {ts_path.name}: {e}")
        return []
    return cards


def get_drill_cards(deck_pattern: str = "matcha-framework-*-decisions-cards.ts") -> dict[str, list[dict]]:
    """全 decision deck の cards を回収。"""
    out: dict[str, list[dict]] = {}
    for p in sorted(DRILL_DATA.glob(deck_pattern)):
        deck_id = p.stem.replace("-cards", "")
        out[deck_id] = extract_decision_cards(p)
    return out


# ════════════════════════════════════════════════════════════
# Step 3: card scenario → dataset rows マッピング
# ════════════════════════════════════════════════════════════

# drill scenario context → dataset scenario_id 候補
# (heuristic mapping; multiple match 時は最初の hit を使う)
SCENARIO_MAP_HEURISTICS: list[tuple[re.Pattern, list[str]]] = [
    # 3BP
    (re.compile(r"3-?bet.*flop", re.I), ["N_cash_3bp_flop", "N_mtt_3bp_flop"]),
    (re.compile(r"3-?bet.*turn", re.I), ["P5_A_cash_3bp_turn", "P5_A_mtt_3bp_turn"]),
    (re.compile(r"3-?bet.*river", re.I), ["N_cash_3bp_river", "P5_A_mtt_3bp_river", "P5_B_3bp_river_extra"]),
    (re.compile(r"3BP", re.I), ["N_cash_3bp_flop", "N_cash_3bp_river", "P5_A_cash_3bp_turn"]),
    # 4BP
    (re.compile(r"4-?bet.*flop", re.I), ["N_cash_4bp_flop", "A_cash_4bp_flop", "P6_A_mtt_4bp_flop"]),
    (re.compile(r"4-?bet.*turn", re.I), ["N_cash_4bp_turn", "P6_A_mtt_4bp_turn"]),
    (re.compile(r"4-?bet.*river", re.I), ["N_cash_4bp_river", "P6_A_mtt_4bp_river", "P5_B_4bp_river_traj"]),
    (re.compile(r"4BP", re.I), ["N_cash_4bp_flop", "A_cash_4bp_flop"]),
    # CR
    (re.compile(r"(check.?raise|CR).*", re.I), ["N_cash_cr_def", "A_cash_cr_def_full"]),
    # Donk
    (re.compile(r"donk.?bet", re.I), ["N_cash_donk_def", "A_cash_donk_def_full", "P5_D_river_donk_def"]),
    # MTT depth
    (re.compile(r"MTT.?25|25bb", re.I), ["N_mtt25_river"]),
    (re.compile(r"MTT.?100|100bb", re.I), ["N_mtt100_river"]),
    (re.compile(r"MTT.?200|200bb", re.I), ["N_mtt200_river", "N_mtt200_turn"]),
    # SRP general (fallback)
    (re.compile(r"flop", re.I), ["B_flop"]),
    (re.compile(r"turn", re.I), ["B_turn"]),
    (re.compile(r"river", re.I), ["B_river", "N_btn_sb_river", "N_bvb_srp_river"]),
]


def guess_scenarios(scenario_text: str) -> list[str]:
    """drill scenario 文字列 → 候補 scenario_id list (priority order)。"""
    candidates: list[str] = []
    for pattern, sids in SCENARIO_MAP_HEURISTICS:
        if pattern.search(scenario_text):
            for s in sids:
                if s not in candidates:
                    candidates.append(s)
    return candidates


def find_matching_rows(
    idx: dict[tuple[str, frozenset[str]], list[dict]],
    board: list[str],
    hand: tuple[str, str],
    scenario_candidates: list[str],
) -> tuple[list[dict], str]:
    """board × hand × scenario で row を引く。

    Returns: (matched_rows, confidence)
      confidence: "exact" (full board match) or "partial_flop" (flop only) or "none"

    dataset は 6 boards 限定 (Ks7d2c, 8s5d3h, Th9c7s, Ts9s7c, KsKd2c, Js7s3s) なので、
    drill の独自 turn/river card は ほぼ matching しない。
    flop level partial match を許可しつつ confidence で分離して計測。
    """
    if not board or len(board) < 3:
        return [], "none"
    full = "".join(board)
    flop = "".join(board[:3])
    hand_set = frozenset({hand[0].lower(), hand[1].lower()})

    # 完全一致を試す
    rows = idx.get((full.lower(), hand_set), [])
    confidence = "exact" if rows else "none"

    # full 無ければ flop level fallback (partial match、confidence は別)
    if not rows and len(board) > 3:
        rows = idx.get((flop.lower(), hand_set), [])
        confidence = "partial_flop" if rows else "none"

    if not rows:
        return [], "none"

    # scenario strict filter
    if scenario_candidates:
        filtered = [r for r in rows if r["scenario_id"] in scenario_candidates]
        if filtered:
            return filtered, confidence
        return [], "scenario_mismatch"
    return rows, confidence


# ════════════════════════════════════════════════════════════
# Step 4: drill 推奨アクション → カードの answer 文字列から推測
# ════════════════════════════════════════════════════════════

# answer 文字列 → action (BET/CALL/RAISE/FOLD/CHECK)
ACTION_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^FOLD", re.I), "FOLD"),
    (re.compile(r"オールイン|all-?in|jam", re.I), "RAISE"),  # all-in = raise
    (re.compile(r"^チェックレイズ|^CR|check.?raise", re.I), "RAISE"),
    (re.compile(r"^レイズ|raise|3-?bet|4-?bet", re.I), "RAISE"),
    (re.compile(r"^ベット|bet", re.I), "RAISE"),  # bet on first action = raise from action tree perspective
    (re.compile(r"^コール|^call", re.I), "CALL"),
    (re.compile(r"^チェック|^check", re.I), "CALL"),  # check ≈ "don't fold / don't raise" → call で代用
]


def extract_drill_action(answer: str) -> str | None:
    """drill answer 文字列から action (FOLD/CALL/RAISE) を推定。"""
    answer = answer.strip()
    for pat, action in ACTION_PATTERNS:
        if pat.search(answer):
            return action
    return None


# ════════════════════════════════════════════════════════════
# Step 5: 監査 — drill action vs GTO best
# ════════════════════════════════════════════════════════════


# drill answer のサイジング情報抽出 (filter 用)
SIZING_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"33\s*%|スモール|small", re.I), "small_33"),
    (re.compile(r"5[0-9]\s*%|ハーフ|half|ミディアム|medium", re.I), "med_50"),
    (re.compile(r"6[6-9]\s*%|7[0-9]\s*%", re.I), "med_75p"),
    (re.compile(r"10[0-9]\s*%|オーバーベット|overbet", re.I), "big_100p"),
    (re.compile(r"オールイン|all-?in", re.I), "allin"),
]


def detect_sizing(text: str) -> str | None:
    """drill answer/scenario から sizing 種別を抽出 (filter 用)。"""
    for pat, key in SIZING_PATTERNS:
        if pat.search(text):
            return key
    return None


def audit_card(card: dict, idx: dict, scenario_text: str = "") -> dict[str, Any]:
    """1 card 監査。sizing 別に loss 計算、aggregation を改善。

    fix (b): drill specific suits を厳密適用 (frozenset 比較で自動的に exact match)
    fix (d): 同じ scenario 内の rows でも sizing 別に best_ev は異なるため、
             各 row の (best_ev - action_ev) を個別計算してから平均する。
    """
    front = card.get("front", {})
    back = card.get("back", {})
    board_s = front.get("board")
    hand_s = front.get("hand")
    answer = back.get("answer", "")

    board = parse_board(board_s)
    hand = parse_hand(hand_s)
    drill_action = extract_drill_action(answer)

    if not board:
        return {"matched": False, "gap_reason": "no_board_in_card"}
    if not hand:
        return {"matched": False, "gap_reason": "no_hand_in_card"}
    if not drill_action:
        return {"matched": False, "gap_reason": f"action_unparseable: '{answer[:30]}'"}

    full_scenario = (scenario_text + " " + front.get("scenario", "")).strip()
    scenario_candidates = guess_scenarios(full_scenario)
    rows, confidence = find_matching_rows(idx, board, hand, scenario_candidates)

    if not rows:
        if confidence == "scenario_mismatch":
            reason = f"scenario_mismatch (board={board_s} found in dataset but not in expected scenarios={scenario_candidates[:3]})"
        else:
            reason = f"no_dataset_match (board={board_s} hand={hand_s} scenarios={scenario_candidates[:3]})"
        return {"matched": False, "gap_reason": reason}

    # sizing filter (drill answer に明示があれば該当 sizing rows のみ評価)
    drill_sizing = detect_sizing(answer)
    if drill_sizing:
        sized = [r for r in rows if r.get("ip_bet_size") == drill_sizing]
        if sized:
            rows = sized

    # 各 row で loss = best_ev - action_ev を個別計算してから平均 (artifact 4 解消)
    losses: list[float] = []
    gto_actions: list[str] = []
    for r in rows:
        action_ev = float(r[{"FOLD": "ev_fold", "CALL": "ev_call", "RAISE": "ev_raise"}[drill_action]])
        best_ev = float(r["best_ev"])
        losses.append(best_ev - action_ev)
        gto_actions.append(r["best_action"])

    avg_loss = sum(losses) / len(losses)

    # GTO best は majority vote (per-row best_action)
    from collections import Counter
    gto_majority = Counter(gto_actions).most_common(1)[0][0]

    return {
        "matched": True,
        "confidence": confidence,
        "n_rows": len(rows),
        "drill_action": drill_action,
        "drill_sizing": drill_sizing,
        "gto_best": gto_majority,
        "loss_bb": round(avg_loss, 3),
        "is_huge": avg_loss > 5.0,
        "is_correct": drill_action == gto_majority,
        "scenarios": list({r["scenario_id"] for r in rows}),
        "board_len": len(board),
    }


# ════════════════════════════════════════════════════════════
# Step 6: 全 decision_card 監査 + 集計
# ════════════════════════════════════════════════════════════


def main() -> None:
    rows = load_dataset()
    idx = build_index(rows)
    print(f"  Index: {len(idx):,} (board, hand) keys")

    decks = get_drill_cards()
    print(f"\n=== Decision decks ===")
    for d, cards in decks.items():
        print(f"  {d}: {len(cards)} cards")

    # Audit
    all_results: list[dict] = []
    per_deck: dict[str, list[dict]] = defaultdict(list)

    for deck_id, cards in decks.items():
        for card in cards:
            scenario_text = card.get("front", {}).get("scenario", "")
            res = audit_card(card, idx, scenario_text)
            res["deck"] = deck_id
            res["card_id"] = card.get("id", "")
            res["answer"] = card.get("back", {}).get("answer", "")
            all_results.append(res)
            per_deck[deck_id].append(res)

    # Summary
    matched = [r for r in all_results if r["matched"]]
    unmatched = [r for r in all_results if not r["matched"]]

    print(f"\n=== Overall ===")
    print(f"  Total cards: {len(all_results)}")
    print(f"  Matched: {len(matched)} ({100*len(matched)/len(all_results):.1f}%)")
    print(f"  Unmatched: {len(unmatched)} ({100*len(unmatched)/len(all_results):.1f}%)")

    if matched:
        def stats(name: str, group: list[dict]) -> None:
            if not group:
                print(f"  {name}: (0 cards)")
                return
            n_correct = sum(1 for r in group if r["is_correct"])
            huge = [r for r in group if r["is_huge"]]
            avg_loss = sum(r["loss_bb"] for r in group) / len(group)
            avg_huge = sum(r["loss_bb"] for r in huge) / len(huge) if huge else 0
            print(f"  {name}: n={len(group)}, acc={100*n_correct/len(group):.0f}%, avg_loss={avg_loss:.3f} BB, huge%={100*len(huge)/len(group):.0f}%, huge_loss={avg_huge:.3f} BB")

        print(f"\n=== Drill audit ===")
        exact = [r for r in matched if r.get("confidence") == "exact"]
        partial = [r for r in matched if r.get("confidence") == "partial_flop"]
        stats("EXACT (full board match)", exact)
        stats("PARTIAL (flop-only match)", partial)
        stats("ALL matched", matched)

    # Gap analysis
    print(f"\n=== Gap analysis (unmatched cards) ===")
    gap_reasons = defaultdict(int)
    for r in unmatched:
        # extract short reason key
        reason = r.get("gap_reason", "unknown")
        key = reason.split(":")[0].split(" ")[0]
        gap_reasons[key] += 1
    for reason, n in sorted(gap_reasons.items(), key=lambda x: -x[1]):
        print(f"  {n:>3} {reason}")

    # Per-deck table
    print(f"\n=== Per-deck breakdown ===")
    print(f"  {'deck':50} {'n':>5} {'match':>6} {'acc':>5} {'avg_loss':>9} {'huge%':>6}")
    for deck_id in sorted(per_deck):
        results = per_deck[deck_id]
        m = [r for r in results if r["matched"]]
        if not m:
            print(f"  {deck_id:50} {len(results):>5} {0:>6} {'N/A':>5} {'N/A':>9} {'N/A':>6}")
            continue
        match_pct = 100 * len(m) / len(results)
        acc_pct = 100 * sum(1 for r in m if r["is_correct"]) / len(m)
        avg_l = sum(r["loss_bb"] for r in m) / len(m)
        huge_pct = 100 * sum(1 for r in m if r["is_huge"]) / len(m)
        print(f"  {deck_id:50} {len(results):>5} {match_pct:>5.0f}% {acc_pct:>4.0f}% {avg_l:>7.3f}BB {huge_pct:>5.1f}%")

    # Write detailed markdown report
    write_report(all_results, per_deck, matched, unmatched, gap_reasons)


def write_report(all_results, per_deck, matched, unmatched, gap_reasons):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    lines.append("# drill 拡張版 MATCHA Framework — GTO 監査結果")
    lines.append("")
    lines.append("dataset: dataset_unified_v2.csv (293K rows、phase 1-6 統合)")
    lines.append("対象: poker-drill `matcha-framework-*-decisions-cards.ts` の全 decision_card")
    lines.append("")
    lines.append("## サマリー")
    lines.append("")
    lines.append(f"- 全 card: {len(all_results)}")
    lines.append(f"- matched (dataset 内): {len(matched)} ({100*len(matched)/len(all_results):.1f}%)")
    lines.append(f"- unmatched: {len(unmatched)} ({100*len(unmatched)/len(all_results):.1f}%)")
    if matched:
        n_correct = sum(1 for r in matched if r["is_correct"])
        huge = [r for r in matched if r["is_huge"]]
        avg_loss = sum(r["loss_bb"] for r in matched) / len(matched)
        avg_huge_loss = sum(r["loss_bb"] for r in huge) / len(huge) if huge else 0
        lines.append(f"- accuracy (drill_action == gto_best): **{100*n_correct/len(matched):.1f}%**")
        lines.append(f"- avg loss / decision: **{avg_loss:.3f} BB**")
        lines.append(f"- huge mistake (>5 BB) 比率: **{100*len(huge)/len(matched):.1f}%**")
        lines.append(f"- huge mistake あたりの avg loss: **{avg_huge_loss:.3f} BB**")
    lines.append("")
    lines.append("## per-deck breakdown")
    lines.append("")
    lines.append("| deck | n | match % | acc % | avg_loss (BB) | huge % |")
    lines.append("|------|---:|---:|---:|---:|---:|")
    for deck_id in sorted(per_deck):
        results = per_deck[deck_id]
        m = [r for r in results if r["matched"]]
        n = len(results)
        if not m:
            lines.append(f"| {deck_id} | {n} | 0% | N/A | N/A | N/A |")
            continue
        lines.append(
            f"| {deck_id} | {n} | {100*len(m)/n:.0f}% | "
            f"{100*sum(1 for r in m if r['is_correct'])/len(m):.0f}% | "
            f"{sum(r['loss_bb'] for r in m)/len(m):.3f} | "
            f"{100*sum(1 for r in m if r['is_huge'])/len(m):.1f}% |"
        )
    lines.append("")
    lines.append("## gap reason 分類 (unmatched cards)")
    lines.append("")
    for reason, n in sorted(gap_reasons.items(), key=lambda x: -x[1]):
        lines.append(f"- **{reason}**: {n} cards")
    lines.append("")
    lines.append("## 不一致 (drill_action != gto_best) の worst 20")
    lines.append("")
    wrong = sorted([r for r in matched if not r["is_correct"]], key=lambda x: -x["loss_bb"])[:20]
    if wrong:
        lines.append("| deck | card_id | drill | GTO | loss (BB) | answer 抜粋 |")
        lines.append("|------|---------|-------|-----|----:|-------|")
        for r in wrong:
            ans = r["answer"][:30].replace("|", "/")
            lines.append(f"| {r['deck']} | {r['card_id']} | {r['drill_action']} | {r['gto_best']} | {r['loss_bb']} | {ans} |")
    lines.append("")
    lines.append("## unmatched cards (上位 30)")
    lines.append("")
    if unmatched:
        lines.append("| deck | card_id | reason |")
        lines.append("|------|---------|--------|")
        for r in unmatched[:30]:
            reason = r.get("gap_reason", "").replace("|", "/")[:100]
            lines.append(f"| {r['deck']} | {r['card_id']} | {reason} |")

    OUTPUT.write_text("\n".join(lines))
    print(f"\n📄 詳細 report: {OUTPUT}")


if __name__ == "__main__":
    main()
