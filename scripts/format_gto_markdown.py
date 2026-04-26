"""
knowledges/preflop/gto-charts.json を再利用しやすい markdown に整形する。

使い方:
    python3 scripts/format_gto_markdown.py
出力: knowledges/preflop/gto-charts.md
"""

import json
from pathlib import Path

RANKS = "AKQJT98765432"

# 表示順 (ハンドカテゴリ別)
def hand_sort_key(hand: str):
    """Sort hands: pairs first by rank, then suited Ax-Kx-..., then offsuit."""
    if len(hand) == 2:
        # pair
        return (0, RANKS.index(hand[0]))
    h, l, suit = hand[0], hand[1], hand[2]
    suit_order = 1 if suit == "s" else 2
    return (suit_order, RANKS.index(h), RANKS.index(l))


def format_hand_list(hands: list[str]) -> str:
    """Group hands into pairs / suited / offsuit lines for readability."""
    pairs = sorted([h for h in hands if len(h) == 2],
                   key=lambda h: RANKS.index(h[0]))
    suited = sorted([h for h in hands if len(h) == 3 and h[2] == "s"],
                    key=lambda h: (RANKS.index(h[0]), RANKS.index(h[1])))
    offsuit = sorted([h for h in hands if len(h) == 3 and h[2] == "o"],
                     key=lambda h: (RANKS.index(h[0]), RANKS.index(h[1])))
    lines = []
    if pairs:
        lines.append("- **ペア**: " + ", ".join(pairs))
    if suited:
        # group by high card
        by_high: dict[str, list[str]] = {}
        for h in suited:
            by_high.setdefault(h[0], []).append(h)
        for high in RANKS:
            if high in by_high:
                lines.append(f"- **{high}xs**: " + ", ".join(by_high[high]))
    if offsuit:
        by_high = {}
        for h in offsuit:
            by_high.setdefault(h[0], []).append(h)
        for high in RANKS:
            if high in by_high:
                lines.append(f"- **{high}xo**: " + ", ".join(by_high[high]))
    return "\n".join(lines)


ACTION_JP = {
    "raise": "Raise (オープン / 3bet)",
    "limp": "Limp / Call",
    "fold": "Fold",
    "mixed_raise": "Mixed (raise寄り)",
    "mixed_limp": "Mixed (limp寄り)",
    "unknown": "Unknown",
}


def main() -> None:
    src = Path("knowledges/preflop/gto-charts.json")
    data = json.loads(src.read_text())

    out: list[str] = []
    out.append("# 6-max 100BB GTO Preflop Charts リファレンス")
    out.append("")
    out.append("> 本ファイルは poker-coaching の **Implementable GTO Charts** "
               "（Jonathan Little 監修、6-max 100BB Cash） を画像から抽出した GTO "
               "プリフロップレンジの再利用可能なリファレンス。")
    out.append(">")
    out.append("> - 出典: <https://www.pokercoaching.com/> "
               "Implementable GTO Charts（公開 PDF）")
    out.append("> - 抽出スクリプト: `scripts/extract_gto_charts.py`")
    out.append("> - 構造化データ: `knowledges/preflop/gto-charts.json`")
    out.append(">")
    out.append("> **6-max ↔ 9-max のポジション対応**")
    out.append("> - LJ (Lojack) = UTG（6-max では最早ポジション）")
    out.append("> - HJ (Hijack) = MP（6-max のミドル）")
    out.append("> - CO / BTN / SB / BB は同じ")
    out.append("")
    out.append("## 想定条件")
    out.append("")
    out.append("- **スタック**: 100BB ディープ")
    out.append("- **ベットサイズ**:")
    out.append("  - RFI: SB 以外は 2.5BB、SB は 3BB")
    out.append("  - 3bet IP: 3.5x、3bet OOP: 4x")
    out.append("  - BB vs SB Limp: 3.5x")
    out.append("  - 4bet IP: 2.3x、4bet OOP: 2.5x")
    out.append("- **戦略**: 「Implementable」の名の通り、"
               "純粋 GTO の混合戦略をできるだけ単一行動に丸めた版（混合 33% でも 1 ハンド代表に集約）")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## 目次")
    out.append("")
    out.append("- [Raise First In (RFI)](#raise-first-in-rfi)")
    out.append("- [Facing RFI: In Position (IP 3bet)](#facing-rfi-in-position-ip-3bet)")
    out.append("- [Facing RFI: Out of Position (OOP)](#facing-rfi-out-of-position-oop)")
    out.append("- [Blind vs Blind](#blind-vs-blind)")
    out.append("")
    out.append("---")

    # Categorize charts by section
    sections = [
        ("## Raise First In (RFI)", ["LJ_RFI", "HJ_RFI", "CO_RFI", "BTN_RFI", "SB_RFI"]),
        ("## Facing RFI: In Position (IP 3bet)",
         ["HJ_vs_LJ", "CO_vs_LJ", "CO_vs_HJ", "BTN_vs_LJ", "BTN_vs_HJ", "BTN_vs_CO"]),
        ("## Facing RFI: Out of Position (OOP)",
         ["SB_vs_LJ", "SB_vs_HJ", "SB_vs_CO", "SB_vs_BTN",
          "BB_vs_LJ", "BB_vs_HJ", "BB_vs_CO", "BB_vs_BTN"]),
        ("## Blind vs Blind",
         ["BvB_SB_strategy", "BvB_BB_vs_SB_limp", "BvB_BB_vs_SB_raise"]),
    ]

    for section_title, keys in sections:
        out.append("")
        out.append(section_title)
        out.append("")
        for key in keys:
            if key not in data:
                continue
            chart = data[key]
            out.append(f"### {key}")
            out.append("")
            out.append(f"_{chart['description']}_")
            out.append("")
            # Frequency summary
            out.append("**頻度 (combos / 1326)**:")
            out.append("")
            for action, c in sorted(chart["combos"].items(), key=lambda kv: -kv[1]):
                pct = chart["percent"][action]
                jp = ACTION_JP.get(action, action)
                out.append(f"- {jp}: **{c}** combos ({pct}%)")
            out.append("")
            # Each action's hands
            for action, hands in chart["actions"].items():
                if action == "fold":
                    continue
                jp = ACTION_JP.get(action, action)
                out.append(f"#### {jp}")
                out.append("")
                out.append(format_hand_list(hands))
                out.append("")
            out.append("---")
            out.append("")

    out.append("")
    out.append("## 利用例")
    out.append("")
    out.append("```python")
    out.append("import json")
    out.append("data = json.load(open('knowledges/preflop/gto-charts.json'))")
    out.append("# Lojack (= UTG in 6-max) RFI raise hands:")
    out.append("lj_raise_hands = set(data['LJ_RFI']['actions']['raise'])")
    out.append("# 'AA', 'AKs', ... in lj_raise_hands")
    out.append("```")
    out.append("")
    out.append("## 注意事項")
    out.append("")
    out.append("- 抽出スクリプトはピクセル分類で多少の誤差が出る場合があります。"
               "特に **SB_RFI / BvB_SB_strategy / BvB_BB_vs_SB_***  は赤・青が同じセル内で"
               "縞模様や半分塗りで混ざる**混合戦略表示**のため、個別ハンドのアクションが"
               "実際の純粋 GTO と数 % 程度ズレる可能性があります。")
    out.append("- 単純な RFI（LJ_RFI / HJ_RFI / CO_RFI / BTN_RFI）と "
               "対 RFI (HJ_vs_LJ などの IP 3bet) は raise / fold の二値なので抽出精度が高いです。")
    out.append("- Implementable GTO は混合戦略を単純化した版です。"
               "本格的な GTO 比較には GTO Wizard 等の解析ソフトを使ってください。")
    out.append("- レンジは **2.5BB オープン** を前提としています。"
               "サイジングが変わるとレンジも微妙に変化します（特に 3bet 後の 4bet）。")
    out.append("")

    out_path = Path("knowledges/preflop/gto-charts.md")
    out_path.write_text("\n".join(out))
    print(f"Written: {out_path} ({len(out)} lines)")


if __name__ == "__main__":
    main()
