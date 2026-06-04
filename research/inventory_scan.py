#!/usr/bin/env python3
"""
inventory_scan.py — 既存 GTO 研究データを全数スキャンしてドキュメント化

対象:
  - vol2-cash-postflop/findings/
  - vol3-mtt-postflop/findings/ (および raw 配下)
  - research/v3-additional/findings/

各 JSON から以下を抽出:
  - ファイル名
  - depth (100bb / 50bb / 25bb 等)
  - シナリオ (BB vs BTN / 3BP / etc)
  - phase (preflop / flop / turn / river)
  - data level (aggregate / per-category / hand-level)
  - ボード数 / ハンド数

出力: research/RESEARCH_INVENTORY.md
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


def classify_data_level(data) -> str:
    """ファイル内容から data level を推定。

    - hand-level: 169 ハンドの個別頻度を含む (strategy[169])
    - per-category: 5-cat (V/BC/WD/Air) や mv-cat (overpair/TP 等) で集約
    - aggregate: 全体集約 (cbet_pct 等)
    """
    def walk(obj, depth=0):
        if depth > 5:
            return None
        if isinstance(obj, dict):
            keys = set(obj.keys())
            # hand-level signature
            if "hand_freqs" in keys or "strategy" in keys:
                return "hand-level"
            # 169 array
            for k, v in obj.items():
                if isinstance(v, list) and len(v) == 169:
                    return "hand-level"
                if isinstance(v, dict):
                    cat_keys = set(v.keys()) if isinstance(v, dict) else set()
                    if cat_keys & {"V", "BC", "WD", "Air", "D"}:
                        return "per-5cat"
                    if cat_keys & {"overpair", "top_pair", "set", "no_made_hand"}:
                        return "per-mv-cat"
                    if cat_keys & {"バリュー", "ブラフキャッチャー", "エアー"}:
                        return "per-5cat-jp"
                result = walk(v, depth+1)
                if result:
                    return result
        elif isinstance(obj, list) and obj:
            return walk(obj[0], depth+1)
        return None
    return walk(data) or "aggregate"


def extract_metadata(data, file_name: str) -> dict:
    """ファイル内容からメタデータを抽出。"""
    md = {
        "data_level": classify_data_level(data),
        "depth_hints": [],
        "scenarios": [],
        "board_count": 0,
        "hand_count_per_call": 0,
        "phase_hints": [],
    }
    # depth hint from filename
    if "100" in file_name or "_cash" in file_name.lower():
        md["depth_hints"].append("100bb")
    if "50bb" in file_name or "_50" in file_name:
        md["depth_hints"].append("50bb")
    if "25bb" in file_name or "_25" in file_name:
        md["depth_hints"].append("25bb")
    # phase hint
    for p in ["flop", "turn", "river", "preflop"]:
        if p in file_name.lower():
            md["phase_hints"].append(p)

    # walk for scenarios/boards
    boards = set()
    scenarios = set()
    def walk(obj, depth=0):
        if depth > 4:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                if "scenario" in k.lower() or k in ("scenarios",):
                    if isinstance(v, str):
                        scenarios.add(v)
                    elif isinstance(v, list):
                        for s in v:
                            if isinstance(s, str):
                                scenarios.add(s)
                if k == "board" and isinstance(v, str):
                    boards.add(v)
                if k in ("BB_vs_UTG", "BB_vs_HJ", "BB_vs_CO", "BB_vs_BTN", "BB_vs_SB",
                        "BTN_BB", "CO_BB", "HJ_BB", "UTG_BB", "SB_BB"):
                    scenarios.add(k)
                walk(v, depth+1)
        elif isinstance(obj, list):
            for item in obj[:30]:
                walk(item, depth+1)
    walk(data)
    md["scenarios"] = sorted(scenarios)[:10]
    md["board_count"] = len(boards)
    return md


def scan_file(path: Path) -> dict | None:
    try:
        with open(path) as f:
            if path.suffix == ".jsonl":
                # JSON lines: read first line for shape
                lines = f.readlines()
                if not lines:
                    return None
                data = json.loads(lines[0])
                return {
                    "path": str(path.relative_to(ROOT)),
                    "size_kb": path.stat().st_size // 1024,
                    "lines": len(lines),
                    **extract_metadata(data, path.name),
                }
            else:
                data = json.load(f)
                return {
                    "path": str(path.relative_to(ROOT)),
                    "size_kb": path.stat().st_size // 1024,
                    **extract_metadata(data, path.name),
                }
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    except Exception as e:
        return {"path": str(path.relative_to(ROOT)), "error": str(e)[:80]}


def main():
    all_files = []
    for target in TARGETS:
        if not target.exists():
            continue
        for p in sorted(target.rglob("*.json")):
            info = scan_file(p)
            if info:
                all_files.append(info)
        for p in sorted(target.rglob("*.jsonl")):
            info = scan_file(p)
            if info:
                all_files.append(info)

    # Group by directory
    by_dir = defaultdict(list)
    for f in all_files:
        d = "/".join(f["path"].split("/")[:-1])
        by_dir[d].append(f)

    # Output Markdown
    print("# GTO 研究データ Inventory (2026-06-04 自動生成)")
    print()
    print("**目的**: 既存の GTO Wizard 研究データを Claude / 作業者が再取得しないための網羅リスト。")
    print()
    print("各ファイルが何のシナリオ・ボード・フェーズ・データレベルをカバーしているかを記載。")
    print()
    print(f"**合計 JSON ファイル数**: {len(all_files)}")
    print()

    # Data level distribution
    levels = defaultdict(int)
    for f in all_files:
        levels[f.get("data_level", "?")] += 1
    print("## データレベル別集計")
    print()
    print("| データレベル | ファイル数 | 説明 |")
    print("|------------|---------|------|")
    for lvl, n in sorted(levels.items(), key=lambda x: -x[1]):
        desc = {
            "hand-level": "169 starting hands の個別頻度",
            "per-mv-cat": "16 役 (mv) 別の集約頻度",
            "per-5cat": "5-category (V/BC/WD/Air) 別の集約",
            "per-5cat-jp": "5-category (バリュー/ブラフキャッチャー/エアー) 日本語",
            "aggregate": "全体集約 (cbet_pct 等)",
        }.get(lvl, lvl)
        print(f"| {lvl} | {n} | {desc} |")
    print()

    # Files by directory
    for d in sorted(by_dir.keys()):
        files = by_dir[d]
        print(f"## {d}/")
        print()
        print(f"**ファイル数**: {len(files)}")
        print()
        print("| ファイル | サイズ | データレベル | depth | シナリオ | board 数 |")
        print("|---------|-------|------------|-------|---------|---------|")
        for f in files:
            name = f["path"].split("/")[-1]
            size = f"{f.get('size_kb', 0)}KB" if f.get("size_kb") else "-"
            level = f.get("data_level", "?")
            depth = ",".join(f.get("depth_hints", [])) or "-"
            sc = (",".join(f.get("scenarios", []))[:60] + "..." if len(",".join(f.get("scenarios", []))) > 60 else ",".join(f.get("scenarios", []))) or "-"
            boards = f.get("board_count", 0)
            print(f"| `{name}` | {size} | {level} | {depth} | {sc} | {boards} |")
        print()


if __name__ == "__main__":
    main()
