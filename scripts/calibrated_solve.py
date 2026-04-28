#!/usr/bin/env python3
"""TexasSolver の出力を 17 型別に補正して GTO Wizard 相当値を返すラッパー.

3 つのモードで動作する:

(1) `--ts-cbet-pct` を渡す: ソルバー実行をスキップして補正のみ適用
    python3 scripts/calibrated_solve.py --board K72r --ts-cbet-pct 78.1

(2) `--solve` を渡す: TexasSolver を呼び出して補正適用 (要環境)
    python3 scripts/calibrated_solve.py --board K72r --solve

(3) `--batch FILE` を渡す: JSON にまとまった複数ボードを一括処理
    [{"board": "K72r", "ts_cbet_pct": 78.1}, ...]

出力 JSON:
  {
    "board": "K72r",
    "type_code": "1b",
    "type_name": "high-dry-rainbow",
    "raw_ts": 78.1,
    "offset": 17.6,
    "offset_stdev": 4.0,
    "calibrated": 95.7,
    "confidence_band": [91.7, 99.7],
    "n_training_samples": 7,
    "fallback_used": false
  }
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from board_classifier import classify  # noqa: E402

CORRECTION_TABLE_PATH = REPO / "knowledges/flop-advanced/correction_table.json"
DIRECT_TRUTH_PATH = REPO / "knowledges/flop-advanced/direct_truth_table.json"


def load_table() -> dict:
    with open(CORRECTION_TABLE_PATH) as f:
        return json.load(f)["table"]


def load_direct_truth() -> dict:
    """ボード別名 → entry の lookup dict を返す."""
    if not DIRECT_TRUTH_PATH.exists():
        return {}
    with open(DIRECT_TRUTH_PATH) as f:
        d = json.load(f)
    by_alias = {}
    for entry in d["entries"]:
        for alias in [entry["board_id"]] + entry.get("board_aliases", []):
            by_alias[alias.lower()] = entry
    return by_alias


def calibrate(
    board: str,
    ts_cbet_pct: float | None = None,
    table: dict | None = None,
    direct_truth: dict | None = None,
) -> dict:
    """1 ボード分の補正を計算.

    優先順位:
      1. direct_truth_table に該当 → 公式値を直接返す (source='gto_wizard_blog')
      2. ts_cbet_pct + correction_table → 補正適用 (source='ts_calibrated')
    """
    if direct_truth is None:
        direct_truth = load_direct_truth()

    # Phase 3: 直接 lookup
    direct = direct_truth.get(board.lower())
    if direct:
        feat = classify(direct["board_id"])
        return {
            "board": board,
            "source": "gto_wizard_blog",
            "type_code": direct.get("type_code") or feat.type_code,
            "type_name": feat.type_name,
            "calibrated": direct["ip_cbet_pct"],
            "calibrated_clamped": direct["ip_cbet_pct"],
            "confidence_band": [direct["ip_cbet_pct"], direct["ip_cbet_pct"]],
            "raw_ts": round(ts_cbet_pct, 1) if ts_cbet_pct is not None else None,
            "offset": None,
            "offset_stdev": 0.0,
            "n_training_samples": None,
            "fallback_used": False,
            "source_url": direct.get("source_url"),
            "source_section": direct.get("source_section"),
            "size_distribution": direct.get("size_distribution"),
            "notes": direct.get("notes"),
        }

    # Phase 2: TS + 補正
    if ts_cbet_pct is None:
        raise ValueError(f"{board} は direct truth に無く、ts_cbet_pct も未指定")

    if table is None:
        table = load_table()

    feat = classify(board)
    type_info = table.get(feat.type_code)
    fallback = False
    if type_info is None or type_info["n"] == 0:
        type_info = table["_global"]
        fallback = True

    offset = type_info["mean_offset"]
    stdev = type_info["stdev_offset"]
    calibrated = round(ts_cbet_pct + offset, 1)
    band_low = round(calibrated - stdev, 1)
    band_high = round(calibrated + stdev, 1)

    return {
        "board": board,
        "source": "ts_calibrated",
        "type_code": feat.type_code,
        "type_name": feat.type_name,
        "raw_ts": round(ts_cbet_pct, 1),
        "offset": offset,
        "offset_stdev": stdev,
        "calibrated": calibrated,
        "calibrated_clamped": max(0.0, min(100.0, calibrated)),
        "confidence_band": [max(0.0, band_low), min(100.0, band_high)],
        "n_training_samples": type_info["n"],
        "fallback_used": fallback,
    }


def run_solver_and_calibrate(board: str) -> dict:
    """TexasSolver を実行して raw 値を取得し補正適用 (上位の wrapper script を再利用)."""
    raise NotImplementedError(
        "TexasSolver 実行はホスト依存。texassolver_accuracy_30.py を流用してください。"
    )


def main():
    p = argparse.ArgumentParser(
        description="TexasSolver 出力を 17 型別に補正して GTO Wizard 相当値を返す",
    )
    p.add_argument("--board", help="ボード文字列 (例: K72r, KQTss, AAK)")
    p.add_argument("--ts-cbet-pct", type=float,
                   help="TexasSolver で得た raw CBet 頻度 (%%)")
    p.add_argument("--batch", type=Path,
                   help="JSON 配列ファイル: [{board, ts_cbet_pct}, ...]")
    p.add_argument("--solve", action="store_true",
                   help="ソルバー実行 (未実装、将来用)")
    p.add_argument("--format", choices=["json", "table"], default="json")
    args = p.parse_args()

    table = load_table()
    results = []

    direct_truth = load_direct_truth()

    if args.batch:
        items = json.loads(args.batch.read_text())
        for item in items:
            results.append(calibrate(
                item["board"], item.get("ts_cbet_pct"),
                table=table, direct_truth=direct_truth,
            ))
    elif args.board:
        results.append(calibrate(
            args.board, args.ts_cbet_pct,
            table=table, direct_truth=direct_truth,
        ))
    else:
        p.error("--board を指定してください (--ts-cbet-pct または --batch と併用)")

    if args.format == "json":
        print(json.dumps(results if args.batch else results[0],
                         ensure_ascii=False, indent=2))
    else:
        print(f"{'Board':<10} {'Source':<14} {'Type':<6} {'Raw TS':>7} "
              f"{'Calibrated':>10} {'Band':<14} {'N':>4}")
        print("-" * 75)
        for r in results:
            band_str = (f"[{r['confidence_band'][0]:.1f},"
                        f"{r['confidence_band'][1]:.1f}]")
            ts_str = f"{r['raw_ts']:>7.1f}" if r.get('raw_ts') is not None else "    -  "
            n_str = str(r['n_training_samples']) if r.get('n_training_samples') is not None else "exact"
            print(f"{r['board']:<10} {r['source']:<14} {r['type_code']:<6} "
                  f"{ts_str} {r['calibrated']:>10.1f} {band_str:<14} {n_str:>4}")


if __name__ == "__main__":
    main()
