#!/usr/bin/env python3
"""
inventory_summarize.py — ディレクトリ単位で既存研究データをサマライズ

inventory_scan.py の詳細版とは別に、Claude が読みやすい形 (~200 行) に集約する。

各 raw ディレクトリ / findings ディレクトリのカバー範囲を抽出:
  - 何のシナリオか (BB defense / 3BP / Cash etc)
  - 何 depth か (25bb/50bb/100bb)
  - 何 phase か (preflop/flop/turn/river)
  - 何ボードカバー
  - データレベル (hand-level / per-cat / aggregate)
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path.home() / "poker-books"
TARGETS = [
    ROOT / "vol2-cash-postflop" / "findings",
    ROOT / "vol3-mtt-postflop" / "findings",
    ROOT / "research" / "v3-additional" / "findings",
]


def quick_classify(p: Path) -> dict:
    """ファイルを軽量分析。"""
    try:
        if p.suffix == ".jsonl":
            with open(p) as f:
                first = f.readline()
            data = json.loads(first) if first else {}
        else:
            with open(p) as f:
                data = json.load(f)
    except Exception:
        return {"level": "?", "context": "?"}

    # data level
    level = "aggregate"
    def has_169(obj, depth=0):
        if depth > 4:
            return False
        if isinstance(obj, list) and len(obj) == 169:
            return True
        if isinstance(obj, dict):
            if "hand_freqs" in obj:
                return True
            for v in obj.values():
                if has_169(v, depth+1):
                    return True
        elif isinstance(obj, list) and obj:
            return has_169(obj[0], depth+1)
        return False

    if has_169(data):
        level = "preflop-hand-level (169)"
    else:
        # postflop: action_solutions + strategy[N] (N != 169)
        is_postflop = isinstance(data, dict) and "action_solutions" in data
        # check categories
        cat_keys = set()
        def walk_keys(obj, depth=0):
            if depth > 3:
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    cat_keys.add(k)
                    walk_keys(v, depth+1)
            elif isinstance(obj, list) and obj:
                walk_keys(obj[0], depth+1)
        walk_keys(data)
        if is_postflop:
            level = "postflop-hand-level (action_solutions)"
        elif cat_keys & {"V", "BC", "WD", "Air", "D"}:
            level = "per-5cat (V/BC/WD/Air)"
        elif cat_keys & {"バリュー", "ブラフキャッチャー", "エアー", "ドロー", "ウィークドロー"}:
            level = "per-5cat (jp)"
        elif cat_keys & {"overpair", "top_pair", "set", "no_made_hand", "second_pair"}:
            level = "per-mv-cat (16 役)"

    return {"level": level}


def main():
    by_dir: dict[str, dict] = defaultdict(lambda: {
        "files": [],
        "levels": defaultdict(int),
        "size_kb": 0,
    })

    for target in TARGETS:
        if not target.exists():
            continue
        for p in sorted(target.rglob("*.json")):
            d = str(p.parent.relative_to(ROOT))
            info = quick_classify(p)
            by_dir[d]["files"].append(p.name)
            by_dir[d]["levels"][info["level"]] += 1
            by_dir[d]["size_kb"] += p.stat().st_size // 1024
        for p in sorted(target.rglob("*.jsonl")):
            d = str(p.parent.relative_to(ROOT))
            info = quick_classify(p)
            by_dir[d]["files"].append(p.name)
            by_dir[d]["levels"][info["level"]] += 1
            by_dir[d]["size_kb"] += p.stat().st_size // 1024

    # Directory groupings with descriptions
    DIR_INFO = {
        "vol2-cash-postflop/findings": (
            "Vol2 Cash 100bb 6m postflop の集約データ",
            "5 ポジ (UTG/HJ/CO/BTN/SB) × 7 board type × cbet/defense",
            "Vol2 ch03-05 (Tier 1 マトリックス) の根拠データ",
        ),
        "vol3-mtt-postflop/findings": (
            "Vol3 MTT postflop 雑多 / md + 一部 json",
            "GTO 分析の中間ファイル + design notes",
            "Vol3 全章の根拠",
        ),
        "vol3-mtt-postflop/findings/3bp25_raw": (
            "MTT 25bb 3-bet pot postflop raw",
            "BTN_BB / CO_BB × 8 board (742/765/A72/K72/...) の hand-level",
            "Vol3 ch07 3BP の SBR=25",
        ),
        "vol3-mtt-postflop/findings/3bp50_raw": (
            "MTT 50bb 3-bet pot postflop raw",
            "BTN_BB / CO_BB × 8 board の hand-level",
            "Vol3 ch07 3BP の SBR=50",
        ),
        "vol3-mtt-postflop/findings/3bp100_raw": (
            "Cash 100bb 3-bet pot postflop raw",
            "BTN_BB / CO_BB × 8 board の hand-level",
            "Vol3 ch07 3BP の Cash 100bb 比較",
        ),
        "vol3-mtt-postflop/findings/cash50bb_raw": (
            "Cash 50bb postflop (limited, BTN_BB K72_rain のみ)",
            "1 ボードのみ、補助参考",
            "Cash 50bb の参考データ",
        ),
        "vol3-mtt-postflop/findings/def_cash100_bb_raw": (
            "Cash 100bb BB defense flop raw",
            "BTN_BB × 8 board (742_rain/fd, 765_rain/fd, A72_rain/fd, K72, T98)",
            "Vol3 ch05 BB defense Cash 100bb",
        ),
        "vol3-mtt-postflop/findings/def_cash100_bb_turn_raw": (
            "Cash 100bb BB defense Turn raw",
            "K72 ボードベース × 複数 turn cards (3/7/A/K)",
            "Vol3 ch02 Turn defense Cash 100bb",
        ),
        "vol3-mtt-postflop/findings/def_cash100_bb_river_raw": (
            "Cash 100bb BB defense River raw",
            "K72 / KJT 等ボード × 複数 turn/river cards",
            "Vol3 ch03 River defense Cash 100bb",
        ),
        "vol3-mtt-postflop/findings/def_mtt25_bb_raw": (
            "MTT 25bb BB defense flop raw",
            "BTN_BB × 8 board の hand-level",
            "Vol3 ch05 depth 別 fold 率",
        ),
        "vol3-mtt-postflop/findings/def_mtt50_bb_raw": (
            "MTT 50bb BB defense flop raw",
            "BTN_BB × 8 board の hand-level",
            "Vol3 ch05 + ch02 Turn defense の前準備",
        ),
        "vol3-mtt-postflop/findings/def_mtt100_bb_raw": (
            "MTT 100bb BB defense flop raw",
            "BTN_BB × 8 board の hand-level",
            "Vol3 ch05 depth 別比較",
        ),
        "vol3-mtt-postflop/findings/def_mtt50_bb_turn_raw": (
            "MTT 50bb BB defense Turn raw",
            "ボード × turn cards の hand-level",
            "Vol3 ch02 MTT 50bb Turn v9",
        ),
        "vol3-mtt-postflop/findings/def_mtt50_bb_river_raw": (
            "MTT 50bb BB defense River raw",
            "ボード × turn/river cards の hand-level",
            "Vol3 ch03 MTT 50bb River v15",
        ),
        "research/v3-additional/findings": (
            "Preflop hand-level 追加調査 (2026-06-04)",
            "BB defense 5 シナリオ + squeeze N=1/2 13 シナリオ",
            "Vol1 ch04 §4.1 + ch05 §5.2-§5.3",
        ),
    }

    # Output
    print("# GTO 研究データ Inventory (集約版 / 2026-06-04)")
    print()
    print("**目的**: Claude / 作業者が既存データを再取得しないための、ディレクトリ単位の網羅サマリ。")
    print()
    print("詳細な個別ファイル一覧は `RESEARCH_INVENTORY_DETAIL.md` 参照。")
    print()

    total_files = sum(len(by_dir[d]["files"]) for d in by_dir)
    print(f"**合計 JSON ファイル数**: {total_files}")
    print()

    # Summary by directory
    print("## ディレクトリ別カバー範囲")
    print()
    for d in sorted(by_dir.keys()):
        info = by_dir[d]
        title, scenarios, purpose = DIR_INFO.get(d, ("(未注記)", "?", "?"))
        print(f"### `{d}/`")
        print()
        print(f"- **概要**: {title}")
        print(f"- **シナリオ**: {scenarios}")
        print(f"- **書籍参照**: {purpose}")
        print(f"- **ファイル数**: {len(info['files'])} / **合計サイズ**: {info['size_kb']} KB")
        levels = ", ".join(f"{lvl}={n}" for lvl, n in sorted(info["levels"].items(), key=lambda x: -x[1]))
        print(f"- **データレベル**: {levels}")
        # 最初の 5 ファイル名を例示
        if info["files"]:
            sample = ", ".join(info["files"][:5])
            print(f"- **例ファイル**: {sample}" + ("..." if len(info["files"]) > 5 else ""))
        print()


if __name__ == "__main__":
    main()
