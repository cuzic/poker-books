"""
poker-coaching「Implementable GTO Charts」(PDF抽出画像) から
6-max 100BB の各ポジション・対RFI/対3bet レンジを抽出する。

入力: /tmp/preflop-charts-imgs/chart-NNN.jpg (002-023)
出力: knowledges/preflop/gto-charts.json (構造化データ)

使い方:
    python3 scripts/extract_gto_charts.py

Note: チャート画像は poker-coaching の公開 PDF を画像化したもの。
出典: https://www.pokercoaching.com/  Implementable GTO Charts
"""

from PIL import Image
import json
from pathlib import Path

RANKS = "AKQJT98765432"

# Chart number → semantic position label.
# Based on poker-coaching PDF page order.
# 6-max equivalents: LJ=UTG, HJ=MP.
CHART_LABELS = {
    "002": ("LJ_RFI", "Lojack RFI (= UTG in 6-max)"),
    "003": ("HJ_RFI", "Hijack RFI (= MP in 6-max)"),
    "004": ("CO_RFI", "Cutoff RFI"),
    "005": ("BTN_RFI", "Button RFI"),
    "006": ("SB_RFI", "Small Blind RFI (raise + limp 混合)"),
    "007": ("HJ_vs_LJ", "Hijack vs Lojack RFI (3bet IP)"),
    "008": ("CO_vs_LJ", "Cutoff vs Lojack RFI (3bet IP)"),
    "009": ("CO_vs_HJ", "Cutoff vs Hijack RFI (3bet IP)"),
    "010": ("BTN_vs_LJ", "Button vs Lojack RFI (3bet IP)"),
    "011": ("BTN_vs_HJ", "Button vs Hijack RFI (3bet IP)"),
    "012": ("BTN_vs_CO", "Button vs Cutoff RFI (3bet IP)"),
    "013": ("SB_vs_LJ", "Small Blind vs Lojack RFI (3bet OOP)"),
    "014": ("SB_vs_HJ", "Small Blind vs Hijack RFI (3bet OOP)"),
    "015": ("SB_vs_CO", "Small Blind vs Cutoff RFI (3bet OOP)"),
    "016": ("SB_vs_BTN", "Small Blind vs Button RFI (3bet OOP)"),
    "017": ("BB_vs_LJ", "Big Blind vs Lojack RFI (defense)"),
    "018": ("BB_vs_HJ", "Big Blind vs Hijack RFI (defense)"),
    "019": ("BB_vs_CO", "Big Blind vs Cutoff RFI (defense)"),
    "020": ("BB_vs_BTN", "Big Blind vs Button RFI (defense)"),
    "021": ("BvB_SB_strategy", "Blind vs Blind: SB Strategy"),
    "022": ("BvB_BB_vs_SB_limp", "Blind vs Blind: BB vs SB Limp"),
    "023": ("BvB_BB_vs_SB_raise", "Blind vs Blind: BB vs SB Raise"),
}


def hand_at(row: int, col: int) -> str:
    r, c = RANKS[row], RANKS[col]
    if row == col:
        return r + r
    elif row < col:
        return r + c + "s"
    else:
        return c + r + "o"


def is_gray(r: int, g: int, b: int, thr: int = 15) -> bool:
    avg = (r + g + b) / 3
    return abs(r - avg) < thr and abs(g - avg) < thr and abs(b - avg) < thr


def classify_color(r: int, g: int, b: int) -> str:
    """Classify a single pixel by RGB."""
    if r > 220 and g > 220 and b > 220:
        return "fold"
    if r > 180 and r - g > 50 and r - b > 50:
        return "raise"
    if b > 130 and b - r > 30 and b - g > 30:
        return "limp"
    if r > 200 and g > 100 and b > 100 and r > g + 20:
        return "mixed_raise"
    if b > 200 and r < 200 and b > r + 10:
        return "mixed_limp"
    return "unknown"


def cell_action(px, cx_min: int, cx_max: int, cy_min: int, cy_max: int) -> str:
    """Count colored pixels in central 50% region of cell, return dominant action."""
    x_start = int(cx_min + (cx_max - cx_min) * 0.25)
    x_end = int(cx_min + (cx_max - cx_min) * 0.75)
    y_start = int(cy_min + (cy_max - cy_min) * 0.25)
    y_end = int(cy_min + (cy_max - cy_min) * 0.75)

    counts: dict[str, int] = {}
    for y in range(y_start, y_end):
        for x in range(x_start, x_end):
            r, g, b = px[x, y]
            if max(r, g, b) < 80:
                continue
            if is_gray(r, g, b, thr=10) and 130 < r < 200:
                continue
            a = classify_color(r, g, b)
            counts[a] = counts.get(a, 0) + 1

    non_fold = sum(counts.get(k, 0) for k in ("raise", "limp", "mixed_raise", "mixed_limp"))
    fold_count = counts.get("fold", 0)
    if non_fold == 0:
        return "fold"

    best = max(("raise", "limp", "mixed_raise", "mixed_limp"), key=lambda k: counts.get(k, 0))
    if non_fold > fold_count * 0.5:
        return best
    return "fold"


def grid_bounds(img: Image.Image) -> tuple[int, int, int, int]:
    w, h = img.size
    return int(w * 0.020), int(h * 0.022), int(w * 0.985), int(h * 0.785)


def extract_chart(img_path: Path) -> dict[str, list[str]]:
    """Return action → [hands] dict for one chart."""
    img = Image.open(img_path).convert("RGB")
    px = img.load()
    if px is None:
        return {}
    left, top, right, bottom = grid_bounds(img)
    cell_w = (right - left) / 13
    cell_h = (bottom - top) / 13

    actions: dict[str, list[str]] = {}
    for row in range(13):
        for col in range(13):
            x0 = int(left + cell_w * col)
            x1 = int(left + cell_w * (col + 1))
            y0 = int(top + cell_h * row)
            y1 = int(top + cell_h * (row + 1))
            a = cell_action(px, x0, x1, y0, y1)
            actions.setdefault(a, []).append(hand_at(row, col))
    return actions


def hand_combo_count(hand: str) -> int:
    if len(hand) == 2:
        return 6
    return 4 if hand[2] == "s" else 12


def main() -> None:
    charts_dir = Path("/tmp/preflop-charts-imgs")
    output: dict[str, dict] = {}

    for chart_path in sorted(charts_dir.glob("chart-*.jpg")):
        idx = chart_path.stem.split("-")[1]
        if idx not in CHART_LABELS:
            continue
        label, description = CHART_LABELS[idx]
        actions = extract_chart(chart_path)
        combos = {a: sum(hand_combo_count(h) for h in hs) for a, hs in actions.items()}
        pcts = {a: round(c / 13.26, 1) for a, c in combos.items()}
        output[label] = {
            "chart_id": idx,
            "description": description,
            "combos": combos,
            "percent": pcts,
            "actions": {a: sorted(hs) for a, hs in actions.items()},
        }
        action_summary = " ".join(f"{a}={c}({pcts[a]}%)" for a, c in combos.items())
        print(f"{label:25} {action_summary}")

    out_path = Path("knowledges/preflop/gto-charts.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"\nWritten: {out_path}")


if __name__ == "__main__":
    main()
