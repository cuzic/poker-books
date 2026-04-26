#!/usr/bin/env python3
"""巻4 検証 #49: overbet 除去実験の結果集計スクリプト.

baseline (flop_accuracy_30_results, bet_sizes=[0.33, 0.5, 0.75, 1.5]) と
no-overbet (overbet_exclusion_results, bet_sizes=[0.33, 0.5, 0.75]) の
CBet 頻度 / bet_by_size 分解を比較し、Markdown レポートと統合 JSON を生成する。

使い方:
  python3 scripts/collect_overbet_exclusion.py \
    --index /home/cuzic/poker-books/knowledges/volume4/scenarios/\
flop_accuracy_30_no_overbet/index.json \
    --baseline-results /home/cuzic/poker-gto/docs/benchmarks/flop_accuracy_30_results \
    --new-results /home/cuzic/poker-gto/docs/benchmarks/overbet_exclusion_results \
    --output-md /home/cuzic/poker-gto/docs/benchmarks/overbet_exclusion_experiment.md \
    --output-json /home/cuzic/poker-books/knowledges/volume4/results/\
overbet_exclusion_YYYYMMDD.json
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# ボード分類
# ---------------------------------------------------------------------------

# generate_flop_accuracy_30.py のコメントに基づく分類
BOARD_CATEGORY: Dict[str, str] = {
    # ドライ (BoardScore 0〜3)
    "K72r": "dry",
    "A72r": "dry",
    "K44": "dry",
    "Q53r": "dry",
    "A82r": "dry",
    "K83r": "dry",
    "A52r": "dry",
    "K95r": "dry",
    # セミウェット (BoardScore 4〜6)
    "KT5r": "semiwet",
    "J75r": "semiwet",
    "Q83ss": "semiwet",
    "AT7ss": "semiwet",
    "J84ss": "semiwet",
    "QJ9r": "semiwet",
    "T87r": "semiwet",
    "876r": "semiwet",
    # ウェット (BoardScore 7〜11)
    "987ss": "wet",
    "JT9ss": "wet",
    "KQTss": "wet",
    "JT8ss": "wet",
    "T98r": "wet",
    "T98ss": "wet",
    # モノトーン
    "987mono": "mono",
    "AKQmono": "mono",
    # 特殊
    "772": "paired",
    "AAK": "paired",
    "KK9": "paired",
    "965r": "semiwet",
    "632r": "dry",
    "A99": "paired",
}


@dataclass
class BoardEntry:
    scenario_id: str
    board_label: str
    category: str
    gto_freq_pct: float
    baseline_check_pct: Optional[float] = None
    baseline_bet_total_pct: Optional[float] = None
    baseline_bet_by_size: Dict[str, float] = field(default_factory=dict)
    new_check_pct: Optional[float] = None
    new_bet_total_pct: Optional[float] = None
    new_bet_by_size: Dict[str, float] = field(default_factory=dict)

    @property
    def baseline_error_pct(self) -> Optional[float]:
        if self.baseline_bet_total_pct is None:
            return None
        return abs(self.baseline_bet_total_pct - self.gto_freq_pct)

    @property
    def new_error_pct(self) -> Optional[float]:
        if self.new_bet_total_pct is None:
            return None
        return abs(self.new_bet_total_pct - self.gto_freq_pct)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def load_index(path: Path) -> List[Dict[str, Any]]:
    raw = path.read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"index.json がオブジェクトではありません: {path}")
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        raise ValueError(f"index.json.scenarios が配列ではありません: {path}")
    return scenarios


def load_result(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def extract_aggregate(
    result: Optional[Dict[str, Any]],
) -> tuple[Optional[float], Optional[float], Dict[str, float]]:
    """(check_pct, bet_total_pct, bet_by_size_pct) を抽出する.

    result が success でなければ全て None。
    """
    if result is None:
        return None, None, {}
    if result.get("status") != "success":
        return None, None, {}
    agg = result.get("aggregate")
    if not isinstance(agg, dict):
        return None, None, {}
    check_raw = agg.get("check_frequency")
    check_pct = (
        float(check_raw) * 100.0 if isinstance(check_raw, (int, float)) else None
    )
    bet_total_raw = agg.get("bet_frequency_total")
    bet_total_pct = (
        float(bet_total_raw) * 100.0
        if isinstance(bet_total_raw, (int, float))
        else None
    )
    bet_by_raw = agg.get("bet_by_size")
    bet_by_pct: Dict[str, float] = {}
    if isinstance(bet_by_raw, dict):
        for k, v in bet_by_raw.items():
            if isinstance(v, (int, float)):
                bet_by_pct[str(k)] = float(v) * 100.0
    return check_pct, bet_total_pct, bet_by_pct


# ---------------------------------------------------------------------------
# 集計
# ---------------------------------------------------------------------------


def collect(
    index_scenarios: List[Dict[str, Any]],
    baseline_dir: Path,
    new_dir: Path,
) -> List[BoardEntry]:
    entries: List[BoardEntry] = []
    for item in index_scenarios:
        scenario_id = str(item.get("scenario_id", ""))
        board_label = str(item.get("board_label", ""))
        category = BOARD_CATEGORY.get(board_label, "other")
        gto_freq_raw = item.get("gto_wizard_bet_freq", 0)
        gto_freq = (
            float(gto_freq_raw) if isinstance(gto_freq_raw, (int, float)) else 0.0
        )

        entry = BoardEntry(
            scenario_id=scenario_id,
            board_label=board_label,
            category=category,
            gto_freq_pct=gto_freq,
        )

        baseline_res = load_result(baseline_dir / f"{scenario_id}.json")
        b_check, b_total, b_by = extract_aggregate(baseline_res)
        entry.baseline_check_pct = b_check
        entry.baseline_bet_total_pct = b_total
        entry.baseline_bet_by_size = b_by

        new_res = load_result(new_dir / f"{scenario_id}.json")
        n_check, n_total, n_by = extract_aggregate(new_res)
        entry.new_check_pct = n_check
        entry.new_bet_total_pct = n_total
        entry.new_bet_by_size = n_by

        entries.append(entry)
    return entries


@dataclass
class Summary:
    baseline_avg_err: float
    baseline_max_err: float
    baseline_max_board: str
    new_avg_err: float
    new_max_err: float
    new_max_board: str
    by_category: Dict[str, Dict[str, float]]


def summarize(entries: List[BoardEntry]) -> Summary:
    baseline_errs: List[tuple[str, float]] = [
        (e.board_label, e.baseline_error_pct)
        for e in entries
        if e.baseline_error_pct is not None
    ]
    new_errs: List[tuple[str, float]] = [
        (e.board_label, e.new_error_pct)
        for e in entries
        if e.new_error_pct is not None
    ]

    def stats(pairs: List[tuple[str, float]]) -> tuple[float, float, str]:
        if not pairs:
            return 0.0, 0.0, "(none)"
        values = [v for _, v in pairs]
        avg = sum(values) / len(values)
        max_v = max(values)
        max_label = next(lbl for lbl, v in pairs if abs(v - max_v) < 1e-9)
        return avg, max_v, max_label

    b_avg, b_max, b_lbl = stats(baseline_errs)
    n_avg, n_max, n_lbl = stats(new_errs)

    # カテゴリ別
    by_cat: Dict[str, Dict[str, float]] = {}
    cats = sorted(set(e.category for e in entries))
    for cat in cats:
        cat_entries = [e for e in entries if e.category == cat]
        b_list = [
            e.baseline_error_pct
            for e in cat_entries
            if e.baseline_error_pct is not None
        ]
        n_list = [
            e.new_error_pct for e in cat_entries if e.new_error_pct is not None
        ]
        by_cat[cat] = {
            "count": float(len(cat_entries)),
            "baseline_avg_err": sum(b_list) / len(b_list) if b_list else 0.0,
            "new_avg_err": sum(n_list) / len(n_list) if n_list else 0.0,
            "delta": (
                (sum(n_list) / len(n_list) if n_list else 0.0)
                - (sum(b_list) / len(b_list) if b_list else 0.0)
            ),
        }

    return Summary(
        baseline_avg_err=b_avg,
        baseline_max_err=b_max,
        baseline_max_board=b_lbl,
        new_avg_err=n_avg,
        new_max_err=n_max,
        new_max_board=n_lbl,
        by_category=by_cat,
    )


# ---------------------------------------------------------------------------
# Markdown 出力
# ---------------------------------------------------------------------------


def fmt_pct_or_dash(v: Optional[float]) -> str:
    if v is None:
        return "—"
    return f"{v:.1f}%"


def fmt_bet_by_size(d: Dict[str, float]) -> str:
    if not d:
        return "—"
    items = sorted(d.items(), key=lambda kv: float(kv[0]))
    return " / ".join(f"{k}:{v:.1f}" for k, v in items)


def format_markdown(entries: List[BoardEntry], summary: Summary) -> str:
    lines: List[str] = []
    lines.append("# Overbet 除去実験: bet_sizes=[0.33, 0.5, 0.75]")
    lines.append("")
    lines.append(f"実施日: {date.today().isoformat()}")
    lines.append("")
    lines.append("## 実験設計")
    lines.append("")
    lines.append(
        "#49 H5 レポートで 987mono の bet_by_size 分解が "
        "`check: 15.7%, 0.33: 51.3%, 0.5: 4.2%, 0.75: 3.5%, 1.0: 2.7%, 1.5: 22.6%` "
        "と二極化し、1.5x オーバーベットに 22.6% の重みが置かれていた。"
    )
    lines.append("")
    lines.append(
        "本実験では **bet_sizes_to_evaluate を `[0.33, 0.5, 0.75]` に制限** "
        "(baseline の `[0.33, 0.5, 0.75, 1.5]` から 1.5x を除外) し、"
        "総 CBet 頻度が落ちるか、および bet_by_size がどう再配分されるかを検証する。"
    )
    lines.append("")
    lines.append(
        "- baseline scenario dir: "
        "`knowledges/volume4/scenarios/flop_accuracy_30/` "
        "(bet_sizes=[0.33, 0.5, 0.75, 1.5])"
    )
    lines.append(
        "- no-overbet scenario dir: "
        "`knowledges/volume4/scenarios/flop_accuracy_30_no_overbet/` "
        "(bet_sizes=[0.33, 0.5, 0.75])"
    )
    lines.append(
        "- 共通設定: ES_MCCFR, iterations=5000, timeout=60s, seed=42, "
        "BtnOpen100bb vs BbDefendVsBtn, pot=7bb, stack=97bb"
    )
    lines.append("")
    lines.append("## 30 ボード結果テーブル")
    lines.append("")
    lines.append(
        "| ボード | 分類 | 参考 (%) | baseline CBet | 新 CBet | Δ CBet | "
        "baseline 誤差 | 新誤差 | 誤差改善 |"
    )
    lines.append(
        "|---|---|---:|---:|---:|---:|---:|---:|---:|"
    )
    for e in entries:
        b_total = fmt_pct_or_dash(e.baseline_bet_total_pct)
        n_total = fmt_pct_or_dash(e.new_bet_total_pct)
        if (
            e.baseline_bet_total_pct is not None
            and e.new_bet_total_pct is not None
        ):
            delta_cbet = f"{e.new_bet_total_pct - e.baseline_bet_total_pct:+.1f}"
        else:
            delta_cbet = "—"
        b_err = fmt_pct_or_dash(e.baseline_error_pct)
        n_err = fmt_pct_or_dash(e.new_error_pct)
        if (
            e.baseline_error_pct is not None
            and e.new_error_pct is not None
        ):
            # 誤差改善 = baseline_err - new_err (正なら改善)
            improve = f"{e.baseline_error_pct - e.new_error_pct:+.1f}"
        else:
            improve = "—"
        lines.append(
            f"| {e.board_label} | {e.category} | {e.gto_freq_pct:.0f}% | "
            f"{b_total} | {n_total} | {delta_cbet} | {b_err} | {n_err} | {improve} |"
        )
    lines.append("")
    lines.append("## サマリ")
    lines.append("")
    lines.append("| 指標 | baseline | 新 (no-overbet) | 差分 |")
    lines.append("|---|---:|---:|---:|")
    lines.append(
        f"| 平均絶対誤差 | {summary.baseline_avg_err:.1f}% | "
        f"{summary.new_avg_err:.1f}% | "
        f"{summary.new_avg_err - summary.baseline_avg_err:+.1f}pt |"
    )
    lines.append(
        f"| 最大誤差 | {summary.baseline_max_err:.1f}% "
        f"({summary.baseline_max_board}) | "
        f"{summary.new_max_err:.1f}% ({summary.new_max_board}) | "
        f"{summary.new_max_err - summary.baseline_max_err:+.1f}pt |"
    )
    lines.append("")
    lines.append("### ボード分類別 平均誤差")
    lines.append("")
    lines.append("| 分類 | ボード数 | baseline 平均誤差 | 新 平均誤差 | 差分 |")
    lines.append("|---|---:|---:|---:|---:|")
    for cat, st in summary.by_category.items():
        lines.append(
            f"| {cat} | {int(st['count'])} | "
            f"{st['baseline_avg_err']:.1f}% | "
            f"{st['new_avg_err']:.1f}% | "
            f"{st['delta']:+.1f}pt |"
        )
    lines.append("")
    lines.append("## 987mono / AKQmono bet_by_size 分解")
    lines.append("")
    lines.append("### 987mono")
    lines.append("")
    mono_987 = next((e for e in entries if e.board_label == "987mono"), None)
    if mono_987 is not None:
        lines.append("| 項目 | baseline ([0.33, 0.5, 0.75, 1.5]) | 新 ([0.33, 0.5, 0.75]) |")
        lines.append("|---|---:|---:|")
        lines.append(
            f"| check | {fmt_pct_or_dash(mono_987.baseline_check_pct)} | "
            f"{fmt_pct_or_dash(mono_987.new_check_pct)} |"
        )
        lines.append(
            f"| 総 CBet | {fmt_pct_or_dash(mono_987.baseline_bet_total_pct)} | "
            f"{fmt_pct_or_dash(mono_987.new_bet_total_pct)} |"
        )
        for k in ["0.33", "0.5", "0.75", "1.5"]:
            b_v = mono_987.baseline_bet_by_size.get(k)
            n_v = mono_987.new_bet_by_size.get(k)
            lines.append(
                f"| bet_{k} | {fmt_pct_or_dash(b_v)} | {fmt_pct_or_dash(n_v)} |"
            )
        lines.append(
            f"| 参考値 (GTO Wizard) | {mono_987.gto_freq_pct:.0f}% (総 CBet) | "
            f"{mono_987.gto_freq_pct:.0f}% (総 CBet) |"
        )
    lines.append("")
    lines.append("### AKQmono")
    lines.append("")
    mono_akq = next((e for e in entries if e.board_label == "AKQmono"), None)
    if mono_akq is not None:
        lines.append("| 項目 | baseline | 新 |")
        lines.append("|---|---:|---:|")
        lines.append(
            f"| check | {fmt_pct_or_dash(mono_akq.baseline_check_pct)} | "
            f"{fmt_pct_or_dash(mono_akq.new_check_pct)} |"
        )
        lines.append(
            f"| 総 CBet | {fmt_pct_or_dash(mono_akq.baseline_bet_total_pct)} | "
            f"{fmt_pct_or_dash(mono_akq.new_bet_total_pct)} |"
        )
        for k in ["0.33", "0.5", "0.75", "1.5"]:
            b_v = mono_akq.baseline_bet_by_size.get(k)
            n_v = mono_akq.new_bet_by_size.get(k)
            lines.append(
                f"| bet_{k} | {fmt_pct_or_dash(b_v)} | {fmt_pct_or_dash(n_v)} |"
            )
        lines.append(
            f"| 参考値 (GTO Wizard) | {mono_akq.gto_freq_pct:.0f}% (総 CBet) | "
            f"{mono_akq.gto_freq_pct:.0f}% (総 CBet) |"
        )
    lines.append("")
    lines.append("## 判定")
    lines.append("")
    if mono_987 is not None and mono_987.new_bet_total_pct is not None:
        cbet_new = mono_987.new_bet_total_pct
    else:
        cbet_new = 0.0
    delta_avg = summary.new_avg_err - summary.baseline_avg_err

    if delta_avg > 2.0:
        verdict = (
            "**bet_sizes 刈り込みは逆効果**。平均誤差が "
            f"{delta_avg:+.1f}pt 悪化しており、overbet 除去は誤差軽減に寄与しない。"
        )
    elif cbet_new <= 65.0 and summary.new_avg_err < 20.0:
        verdict = (
            "**overbet regret に問題がある可能性が高い**。"
            f"987mono の総 CBet が {cbet_new:.1f}% まで落ち "
            f"(baseline 78.9%)、平均誤差も "
            f"{summary.new_avg_err:.1f}% に縮小した。"
            "次は overbet の regret / EV 計算コードの調査を優先する。"
        )
    elif cbet_new >= 70.0:
        verdict = (
            "**overbet は主因ではない**。overbet を除去しても 987mono の"
            f" CBet が {cbet_new:.1f}% に留まり、33%/50%/75% に過剰重みが "
            "移動しただけ。根本原因は戦略抽出 (MCCFR 収束 / 情報集合設計) "
            "または villain レンジの 3bet 含有にある可能性が高い。"
        )
    else:
        verdict = (
            f"**中間的**。987mono CBet は {cbet_new:.1f}% (baseline 78.9%) に留まり、"
            f"平均誤差は {summary.new_avg_err:.1f}% ({delta_avg:+.1f}pt)。"
            "overbet の寄与はあるが主因とは断定できない。"
        )
    lines.append(verdict)
    lines.append("")
    lines.append("## 次アクション提案")
    lines.append("")
    if cbet_new <= 65.0:
        lines.append(
            "1. **overbet regret バグ調査** — 1.5x 選択時の EV / regret 更新ロジック"
            " を静的レビュー。`volume2_board_accuracy.rs` / solver_engine 周辺を確認。"
        )
        lines.append(
            "2. **bet_sizes=[0.33, 0.5, 0.75, 1.0] 実験** — 1.0 を戻して "
            "1.5 だけ除去した構成で再実行し、問題が 1.5 特有かを切り分け。"
        )
    else:
        lines.append(
            "1. **H2: プリフロップ履歴注入** — villain レンジに Bb3betVsBtn 相当 "
            "(QQ+/AKs/AKo) が残っていないか確認、`preflop_action_history` で除外。"
        )
        lines.append(
            "2. **iterations 増加実験** — 5,000 → 50,000 / 200,000 で 987mono の "
            "CBet が収束するか再確認 (`flop_accuracy_30_200k.md` との照合)。"
        )
        lines.append(
            "3. **情報集合粒度** — MCCFR の bucket 設計を再検討し、"
            "flushdraw ブロッカー感度を見直す。"
        )
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 統合 JSON 出力
# ---------------------------------------------------------------------------


def build_result_json(
    entries: List[BoardEntry], summary: Summary
) -> Dict[str, Any]:
    return {
        "task": "overbet_exclusion",
        "date": date.today().isoformat(),
        "baseline_bet_sizes": [0.33, 0.5, 0.75, 1.5],
        "new_bet_sizes": [0.33, 0.5, 0.75],
        "boards": [
            {
                "scenario_id": e.scenario_id,
                "board_label": e.board_label,
                "category": e.category,
                "gto_wizard_bet_freq_pct": e.gto_freq_pct,
                "baseline": {
                    "check_pct": e.baseline_check_pct,
                    "bet_total_pct": e.baseline_bet_total_pct,
                    "bet_by_size_pct": e.baseline_bet_by_size,
                    "error_pct": e.baseline_error_pct,
                },
                "new": {
                    "check_pct": e.new_check_pct,
                    "bet_total_pct": e.new_bet_total_pct,
                    "bet_by_size_pct": e.new_bet_by_size,
                    "error_pct": e.new_error_pct,
                },
            }
            for e in entries
        ],
        "summary": {
            "baseline_avg_err_pct": summary.baseline_avg_err,
            "baseline_max_err_pct": summary.baseline_max_err,
            "baseline_max_err_board": summary.baseline_max_board,
            "new_avg_err_pct": summary.new_avg_err,
            "new_max_err_pct": summary.new_max_err,
            "new_max_err_board": summary.new_max_board,
            "by_category": summary.by_category,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--baseline-results", required=True, type=Path)
    parser.add_argument("--new-results", required=True, type=Path)
    parser.add_argument("--output-md", required=True, type=Path)
    parser.add_argument("--output-json", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    if not args.index.exists():
        print(f"index.json が見つかりません: {args.index}", file=sys.stderr)
        return 1
    if not args.baseline_results.is_dir():
        print(
            f"baseline results ディレクトリが見つかりません: {args.baseline_results}",
            file=sys.stderr,
        )
        return 1
    if not args.new_results.is_dir():
        print(
            f"new results ディレクトリが見つかりません: {args.new_results}",
            file=sys.stderr,
        )
        return 1

    scenarios = load_index(args.index)
    entries = collect(scenarios, args.baseline_results, args.new_results)
    summary = summarize(entries)

    md = format_markdown(entries, summary)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(md, encoding="utf-8")

    result_json = build_result_json(entries, summary)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(result_json, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"wrote {args.output_md}, {args.output_json} "
        f"(baseline_avg={summary.baseline_avg_err:.1f}%, "
        f"new_avg={summary.new_avg_err:.1f}%)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
