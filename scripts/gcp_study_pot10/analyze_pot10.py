#!/usr/bin/env python3
"""
analyze_pot10.py — pot=10 統一 GTO 検証の結果を集計し、書籍・calc.py との乖離を報告する。

Usage:
  python3 analyze_pot10.py [--results-dir DIR] [--output REPORT_MD]

Results are downloaded from GCS if not present locally.
"""
from __future__ import annotations
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

GCS_BUCKET = "poker-gto-study"
GCS_PREFIX = "pot10_study"
DEFAULT_RESULTS_DIR = Path(__file__).parent.parent.parent / "knowledges/gto_canonical/results"
DEFAULT_REPORT = Path(__file__).parent.parent.parent / "knowledges/gto_canonical/REPORT.md"
SCENARIOS_JSON = Path(__file__).parent / "scenarios_pot10.json"


# ── 現在の calc.py 設計値（書籍・アプリの設定値） ─────────────────────────────

DESIGN_VALUES = {
    # IP CBet 判断閾値
    "T1_cbet_threshold": 65,       # HS ≥ 65 → T1 常時 CBet
    "T2_cbet_b_threshold": 58,     # T2 + B ≥ 58 → CBet
    "T3_cbet_b_threshold": 62,     # T3 + B ≥ 62 → CBet (bluff)
    # OOP フォールド閾値
    "oop_fold_vs33_baseline": 15,  # vs 33%: HS < 15 でフォールド
    "oop_fold_vs75_baseline": 35,  # vs 75%: HS < 35 でフォールド
    # CBet 頻度の GTO 目標
    "target_cbet_pct_dry": 90,     # dry rainbow の目標 CBet % (range bet at 33%)
    "target_cbet_pct_wet": 75,     # wet 2tone の目標 CBet %
    "target_overpair_cbet": 90,    # オーバーペアの CBet %
    "target_top_pair_cbet": 90,    # トップペアの CBet % (range bet → near 90%)
    "target_air_cbet": 90,         # Air (dry board range bet at 33%)  ※wet boards ~30%
    # OOP フォールド率の目標 (MDF=75% → フォールド 25%)
    "target_oop_fold_vs33": 25,    # vs 33%: α=25% → 75% MDF
    "target_oop_fold_vs75": 43,    # vs 75%: α=43% → 57% MDF
}


# ── GCS からの結果ダウンロード ─────────────────────────────────────────────────

def download_results(results_dir: Path) -> None:
    results_dir.mkdir(parents=True, exist_ok=True)
    print(f"GCS からダウンロード: gs://{GCS_BUCKET}/{GCS_PREFIX}/results/ → {results_dir}")
    subprocess.run(
        ["gsutil", "-m", "cp", f"gs://{GCS_BUCKET}/{GCS_PREFIX}/results/*.json", str(results_dir)],
        check=True
    )


# ── 結果の読み込み ──────────────────────────────────────────────────────────────

def load_results(results_dir: Path) -> list[dict[str, Any]]:
    records = []
    for f in sorted(results_dir.glob("*.json")):
        try:
            records.append(json.loads(f.read_text()))
        except Exception as e:
            print(f"[WARN] {f.name}: {e}")
    return records


def load_scenarios() -> dict[str, dict]:
    d = json.loads(SCENARIOS_JSON.read_text())
    return {s["id"]: s for s in d["scenarios"]}


# ── ボードテクスチャ分類 ────────────────────────────────────────────────────────

def _classify_texture(board_str: str) -> str:
    from collections import Counter
    RANK_VAL = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    cards = [(RANK_VAL.get(c[0].upper(), 0), c[1].lower()) for c in board_str.split(",") if len(c) >= 2]
    if not cards:
        return "unknown"
    ranks = [r for r, _ in cards]
    suits = [s for _, s in cards]
    if len(set(suits)) == 1:
        return "mono"
    from collections import Counter as C
    if any(v >= 2 for v in C(ranks).values()):
        top = max(r for r, cnt in C(ranks).items() if cnt >= 2)
        return "paired_high" if top >= 10 else "paired_low"
    n_suits = len(set(suits))
    top = max(ranks)
    spread = max(ranks) - min(ranks)
    if n_suits == 2:
        return "2tone_ak" if top >= 13 else "2tone"
    if spread <= 3 and top >= 11:
        return "rainbow_connected"
    if top >= 13:
        return "rainbow_ak"
    if top == 12:
        return "rainbow_q"
    return "rainbow"


# ── 集計・分析 ─────────────────────────────────────────────────────────────────

def analyze(records: list[dict], scenarios: dict[str, dict]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "total": len(records),
        "errors": 0,
        "by_texture": {},
        "cbet_by_category": {},
        "oop_fold": {},
        "design_deviations": [],
    }

    cbet_vals: list[float] = []
    overpair_vals: list[float] = []
    top_pair_vals: list[float] = []
    air_vals: list[float] = []
    fold_vs33_vals: list[float] = []
    fold_vs75_vals: list[float] = []

    texture_groups: dict[str, list[float]] = {}

    for r in records:
        sid = r.get("scenario_id", "?")
        if "error" in r:
            summary["errors"] += 1
            continue

        scenario = scenarios.get(sid, {})
        board_str = r.get("board", scenario.get("board", ""))
        tex = _classify_texture(board_str) if board_str else "unknown"

        cbet = r.get("ip_cbet_pct")
        if cbet is not None:
            cbet_vals.append(cbet)
            texture_groups.setdefault(tex, []).append(cbet)

        if "cbet_overpair" in r:
            overpair_vals.append(r["cbet_overpair"])
        if "cbet_top_pair" in r:
            top_pair_vals.append(r["cbet_top_pair"])
        if "cbet_air" in r:
            air_vals.append(r["cbet_air"])
        if "oop_fold_vs33" in r:
            fold_vs33_vals.append(r["oop_fold_vs33"])
        if "oop_fold_vs75" in r:
            fold_vs75_vals.append(r["oop_fold_vs75"])

    def avg(lst: list[float]) -> float:
        return round(sum(lst) / len(lst), 1) if lst else float("nan")

    summary["cbet_avg"] = avg(cbet_vals)
    summary["cbet_by_category"] = {
        "overpair": avg(overpair_vals),
        "top_pair": avg(top_pair_vals),
        "air": avg(air_vals),
    }
    summary["oop_fold"] = {
        "vs33_avg": avg(fold_vs33_vals),
        "vs75_avg": avg(fold_vs75_vals),
    }
    summary["by_texture"] = {
        tex: {"avg_cbet": avg(vals), "n": len(vals)}
        for tex, vals in sorted(texture_groups.items())
    }

    # 設計値との乖離チェック
    devs = summary["design_deviations"]
    d = DESIGN_VALUES

    def check_dev(label: str, actual: float, target: float, threshold: float = 5.0) -> None:
        diff = actual - target
        if abs(diff) > threshold:
            devs.append({
                "item": label,
                "actual": actual,
                "target": target,
                "diff": round(diff, 1),
                "flag": "⚠️" if abs(diff) > 10 else "注意",
            })

    check_dev("Air CBet% (T3 bluff)", avg(air_vals), d["target_air_cbet"])
    check_dev("オーバーペア CBet%", avg(overpair_vals), d["target_overpair_cbet"])
    check_dev("トップペア CBet%", avg(top_pair_vals), d["target_top_pair_cbet"])
    check_dev("OOP fold vs33%", avg(fold_vs33_vals), d["target_oop_fold_vs33"])
    check_dev("OOP fold vs75%", avg(fold_vs75_vals), d["target_oop_fold_vs75"])

    return summary


# ── レポート生成 ───────────────────────────────────────────────────────────────

def generate_report(summary: dict, output: Path) -> str:
    lines = [
        "# pot=10 統一 GTO 検証レポート",
        "",
        f"生成日: 2026-05-13",
        f"シナリオ数: {summary['total']}（エラー: {summary['errors']}）",
        "",
        "## 全体 CBet 頻度",
        "",
        f"平均 IP CBet%: **{summary['cbet_avg']}%**",
        "",
        "### テクスチャ別",
        "",
        "| テクスチャ | 平均 CBet% | n |",
        "|-----------|-----------|---|",
    ]
    for tex, v in summary["by_texture"].items():
        lines.append(f"| {tex} | {v['avg_cbet']}% | {v['n']} |")

    lines += [
        "",
        "## ハンドカテゴリ別 CBet%",
        "",
        "| カテゴリ | GTO 実測% | 設計目標% | 差 |",
        "|---------|---------|---------|-----|",
    ]
    d = DESIGN_VALUES
    for cat, target_key, actual in [
        ("オーバーペア", "target_overpair_cbet", summary["cbet_by_category"]["overpair"]),
        ("トップペア",   "target_top_pair_cbet", summary["cbet_by_category"]["top_pair"]),
        ("Air (T3)",    "target_air_cbet",       summary["cbet_by_category"]["air"]),
    ]:
        target = d[target_key]
        diff = f"{actual - target:+.1f}" if actual == actual else "N/A"
        lines.append(f"| {cat} | {actual}% | {target}% | {diff} |")

    lines += [
        "",
        "## OOP フォールド率",
        "",
        "| ベットサイズ | GTO 実測% | MDF 理論値% | 差 |",
        "|------------|---------|-----------|-----|",
    ]
    for size, actual_key, mdf in [
        ("33%", "vs33_avg", 25),
        ("75%", "vs75_avg", 43),
    ]:
        actual = summary["oop_fold"][actual_key]
        diff = f"{actual - mdf:+.1f}" if actual == actual else "N/A"
        lines.append(f"| vs {size} | {actual}% | {mdf}% | {diff} |")

    lines += ["", "## 設計値との乖離", ""]

    devs = summary["design_deviations"]
    if not devs:
        lines.append("乖離なし（全指標が許容範囲内）")
    else:
        lines += [
            "| 項目 | 実測 | 設計値 | 差 | フラグ |",
            "|------|------|-------|-----|------|",
        ]
        for dev in devs:
            lines.append(
                f"| {dev['item']} | {dev['actual']}% | {dev['target']}% | {dev['diff']:+} | {dev['flag']} |"
            )

    lines += ["", "## 反映推奨事項", ""]
    if devs:
        lines.append("以下の値を calc.py / 書籍に反映することを検討してください：")
        for dev in devs:
            lines.append(f"- **{dev['item']}**: {dev['actual']}% （現設計: {dev['target']}%, 差: {dev['diff']:+}pt）")
    else:
        lines.append("現在の設計値は GTO と整合しています。反映不要。")

    lines += ["", "---", "<!-- generated by analyze_pot10.py -->"]
    report = "\n".join(lines)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report, encoding="utf-8")
    print(f"レポート生成: {output}")
    return report


# ── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    ap = argparse.ArgumentParser(description="pot=10 GTO 検証結果の分析")
    ap.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    ap.add_argument("--output", "-o", type=Path, default=DEFAULT_REPORT)
    ap.add_argument("--download", action="store_true", help="GCS から結果をダウンロード")
    args = ap.parse_args()

    if args.download:
        download_results(args.results_dir)

    records = load_results(args.results_dir)
    if not records:
        print("結果ファイルが見つかりません。--download オプションを試してください。")
        sys.exit(1)

    scenarios = load_scenarios()
    print(f"ロード: {len(records)} 件の結果")

    summary = analyze(records, scenarios)
    report = generate_report(summary, args.output)
    print(report)


if __name__ == "__main__":
    main()
