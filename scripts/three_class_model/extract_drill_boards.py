"""drill cards 全 board を抽出 → dataset coverage 確認 → probe 必要 boards 特定。

drill cards (poker-drill/src/data/matcha-framework-*-decisions-cards.ts) から:
1. 全 unique boards を抽出 (flop / turn / river 含む)
2. 各 board の出現頻度 (drill 内での重要度の proxy)
3. dataset_unified_v2.csv の board と比較
4. 「drill が使うが dataset に無い」boards を probe 候補として出力

出力: knowledges/gto_wizard_study/DRILL_BOARD_COVERAGE.md
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET = REPO_ROOT / "scripts/three_class_model/dataset_unified_v2.csv"
DRILL_DATA = Path("/home/cuzic/poker-drill/src/data")
OUTPUT = REPO_ROOT / "knowledges/gto_wizard_study/DRILL_BOARD_COVERAGE.md"

SUIT_MAP = {"♠": "s", "♥": "h", "♦": "d", "♣": "c"}


def parse_board(s: str | None) -> list[str] | None:
    """'K♠ 7♦ 2♣' or 'K♠ 7♦ 2♣ → 5♥' → ['Ks','7d','2c','5h']."""
    if not s:
        return None
    s = re.sub(r"\([^)]*\)", "", s)
    parts = re.findall(r"[\dATJQK]0?[♠♥♦♣]", s)
    cards = []
    for p in parts:
        if p[0] == "1":
            rank, suit_ch = "T", p[2]
        else:
            rank, suit_ch = p[0], p[1]
        suit = SUIT_MAP.get(suit_ch)
        if suit is None:
            return None
        cards.append(f"{rank}{suit}")
    return cards if cards else None


def extract_cards(ts_path: Path) -> list[dict]:
    txt = ts_path.read_text()
    m = re.search(r"export const \w+ = (\[.*\])\s+satisfies", txt, re.S)
    if not m:
        m = re.search(r"export const \w+ = (\[.*\])\s*;?\s*$", txt, re.S | re.M)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return []


def main() -> None:
    # 1. dataset board 一覧
    print(f"Loading {DATASET}...")
    with open(DATASET) as f:
        rows = list(csv.DictReader(f))
    dataset_boards = Counter(r["board_str"].lower() for r in rows)
    dataset_flops = set()
    for b in dataset_boards:
        # flop = 最初の 6 char (3 cards × 2)
        if len(b) >= 6:
            dataset_flops.add(b[:6])
    print(f"  dataset boards: {len(dataset_boards)} unique, {len(dataset_flops)} unique flops")
    print(f"  dataset flops: {sorted(dataset_flops)}")

    # 2. drill cards 一覧
    print(f"\nLoading drill cards from {DRILL_DATA}...")
    drill_boards: Counter = Counter()
    drill_flops: Counter = Counter()
    drill_card_boards: dict[str, list[tuple[str, str]]] = defaultdict(list)  # deck → [(card_id, board)]

    for ts in sorted(DRILL_DATA.glob("matcha-framework-*-decisions-cards.ts")):
        deck = ts.stem.replace("-cards", "")
        for card in extract_cards(ts):
            board_s = card.get("front", {}).get("board")
            if not board_s:
                continue
            board = parse_board(board_s)
            if not board:
                continue
            full = "".join(board).lower()
            flop = "".join(board[:3]).lower()
            drill_boards[full] += 1
            drill_flops[flop] += 1
            drill_card_boards[deck].append((card.get("id", ""), full))

    print(f"  drill full boards: {len(drill_boards)} unique")
    print(f"  drill flops: {len(drill_flops)} unique")

    # 3. 比較
    missing_flops = set(drill_flops) - dataset_flops
    covered_flops = set(drill_flops) & dataset_flops
    print(f"\n=== Flop coverage ===")
    print(f"  drill 使用 flops: {len(drill_flops)}")
    print(f"  dataset カバー: {len(covered_flops)}")
    print(f"  dataset 不足 (probe 必要): {len(missing_flops)}")

    # 4. Report
    lines: list[str] = []
    lines.append("# drill board coverage — dataset 不足 boards のリスト")
    lines.append("")
    lines.append("drill の decision_cards で使われている board のうち、")
    lines.append("`dataset_unified_v2.csv` に含まれていない boards を抽出。")
    lines.append("これらを probe で取得すれば drill 全体を audit 可能になる。")
    lines.append("")
    lines.append(f"## サマリー")
    lines.append(f"- dataset 内 unique flops: **{len(dataset_flops)}**")
    lines.append(f"- drill 使用 unique flops: **{len(drill_flops)}**")
    lines.append(f"- カバー済: **{len(covered_flops)}**")
    lines.append(f"- **未カバー (probe 必要): {len(missing_flops)}**")
    lines.append("")

    lines.append("## dataset の既存 flops (audit 可能)")
    for f in sorted(dataset_flops):
        n_drill = drill_flops.get(f, 0)
        lines.append(f"- `{f}` — drill 使用 {n_drill} 回")
    lines.append("")

    lines.append("## drill が使うが dataset に無い flops (probe 候補)")
    lines.append("")
    lines.append("| flop | drill 使用回数 | 例 card |")
    lines.append("|------|---:|---|")
    for f, n in sorted(drill_flops.items(), key=lambda x: -x[1]):
        if f in missing_flops:
            example = ""
            for deck, items in drill_card_boards.items():
                for cid, b in items:
                    if b.startswith(f):
                        example = f"{deck}/{cid}"
                        break
                if example:
                    break
            lines.append(f"| `{f}` | {n} | {example} |")

    lines.append("")
    lines.append("## probe 優先度提案")
    lines.append("")
    lines.append("drill 使用回数 多い順:")
    lines.append("")
    sorted_missing = sorted(
        [(f, n) for f, n in drill_flops.items() if f in missing_flops],
        key=lambda x: -x[1],
    )
    cumulative = 0
    total_drill_uses = sum(drill_flops.values())
    for i, (f, n) in enumerate(sorted_missing, 1):
        cumulative += n
        coverage_pct = 100 * (cumulative + sum(drill_flops[f] for f in covered_flops)) / total_drill_uses
        lines.append(f"{i:>2}. `{f}` ({n} 使用) — top {i} probe で drill {coverage_pct:.0f}% カバー")

    lines.append("")
    lines.append("## probe scripts への接続")
    lines.append("")
    lines.append("各 missing flop に対し:")
    lines.append("1. SRP flop (BTN open vs BB call) を取得")
    lines.append("2. SRP turn / river (代表 turn/river card 各 1 枚)")
    lines.append("3. 3BP flop / turn / river")
    lines.append("4. 4BP flop / turn / river")
    lines.append("")
    lines.append("GTO Wizard API 形式: `Cash6mTest_6mNL100R2` (Cash 100bb) + `MTTGeneral_8m` (MTT)")
    lines.append("(`project_gtow_api_v4_postflop` memory 参照)")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines))
    print(f"\n📄 report: {OUTPUT}")


if __name__ == "__main__":
    main()
