#!/usr/bin/env python3
"""巻4 検証 初期バイアス説決着: bet_sizes = [0.33] 単一サイズでの 30 ボード精度検証シナリオ生成.

背景:
  Volume2 精度問題で、現状 bet_sizes=[0.33, 0.5, 0.75, 1.5] の 4 択で CBet が 75-90%
  に張り付く。uniform 初期化 (regret=0 → regret matching が uniform) の場合、
  4 bet action + 1 check = 5 分岐のうち 4/5 = 80% が初期 bet 頻度となり、
  学習初期値として張り付く可能性。
  bet_sizes を [0.33] 1 サイズに絞れば 1/2 = 50% が初期 bet 頻度 → 決着。

参考 (ChatGPT コメント): 「診断 4: 5 サイズを 1 サイズに減らす」
  「これでなお 987mono が高ベットなら、5/7 ≈ 71% の初期バイアス説はほぼ消えます」

入力: 既存 `flop_accuracy_30/` の 30 シナリオ + index.json
出力先: `/home/cuzic/poker-books/knowledges/volume4/scenarios/flop_accuracy_30_single33/`
  - <scenario_id>.json  (既存の scenario_id をそのまま利用、bet_sizes_to_evaluate のみ [0.33] に変更)
  - index.json          (タイトルを更新、他は同じ)

変更点:
  - bet_sizes_to_evaluate: [0.33, 0.5, 0.75, 1.5] → [0.33]
  - 他設定 (iterations=5000, timeout=60, seed=42, pot=7, stack=97, multistreet=false) は既存と同じ
  - scenario_id / board は変更しない (集計スクリプトの再利用のため)
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List

SOURCE_DIR = Path(
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/flop_accuracy_30"
)
OUTPUT_DIR = Path(
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/flop_accuracy_30_single33"
)

SINGLE_BET_SIZES: List[float] = [0.33]


def transform_scenario(source_path: Path, output_path: Path) -> None:
    """シナリオ JSON の bet_sizes_to_evaluate を [0.33] に書き換える."""
    raw = source_path.read_text(encoding="utf-8")
    data: Dict[str, Any] = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError(f"シナリオがオブジェクトではない: {source_path}")

    # bet_sizes_to_evaluate を [0.33] に上書き
    data["bet_sizes_to_evaluate"] = list(SINGLE_BET_SIZES)

    # scenario_id / board / pot / stack / range 等はそのまま
    # solver_config (iterations / timeout / seed / exploitability_target_bb) もそのまま

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def transform_index(source_path: Path, output_path: Path) -> None:
    """index.json を複製し、title と bet_sizes メタを書き換える."""
    raw = source_path.read_text(encoding="utf-8")
    data: Dict[str, Any] = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError(f"index.json がオブジェクトではない: {source_path}")

    data["task"] = "flop_accuracy_30_single33"
    data["title"] = (
        "30 ボード精度検証 初期バイアス説決着: bet_sizes=[0.33] 単一サイズ"
    )
    data["bet_sizes"] = list(SINGLE_BET_SIZES)
    data["note"] = (
        "uniform 初期化による bet bias を切り分けるため、"
        "bet_sizes を [0.33, 0.5, 0.75, 1.5] の 4 択から [0.33] の単独に縮退。"
        "初期 bet 頻度は 1/2 = 50% となるため、学習結果がそこに近づけば"
        "初期バイアスが主因、75% 以上のままなら engine 側の歪みが主因。"
    )

    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    if not SOURCE_DIR.is_dir():
        print(f"ERROR: 元ディレクトリが存在しない: {SOURCE_DIR}", file=sys.stderr)
        return 1

    # 出力先を (再)作成
    if OUTPUT_DIR.exists():
        # 再実行時に古いファイルを残さない
        shutil.rmtree(OUTPUT_DIR)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)

    scenario_files = sorted(
        [p for p in SOURCE_DIR.iterdir() if p.is_file() and p.suffix == ".json" and p.name != "index.json"]
    )

    if len(scenario_files) != 30:
        print(
            f"WARN: シナリオファイル数が 30 ではない: {len(scenario_files)}",
            file=sys.stderr,
        )

    for src in scenario_files:
        dst = OUTPUT_DIR / src.name
        transform_scenario(src, dst)

    # index.json
    index_src = SOURCE_DIR / "index.json"
    if not index_src.exists():
        print(f"ERROR: 元の index.json が存在しない: {index_src}", file=sys.stderr)
        return 1
    transform_index(index_src, OUTPUT_DIR / "index.json")

    print(f"OK: {len(scenario_files)} 件のシナリオと index.json を生成")
    print(f"  出力先: {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
