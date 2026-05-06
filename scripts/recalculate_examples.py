#!/usr/bin/env python3
"""ドリル問題と worked example を新スケールで自動再計算する。

Usage:
    # 1 ファイルを diff モードで表示
    python3 scripts/recalculate_examples.py --file volume4/chapters/13-oop-defense-basic.md

    # 全章を一括処理 (確認モード)
    python3 scripts/recalculate_examples.py --all --dry-run

    # 確定後に書き換え
    python3 scripts/recalculate_examples.py --all --apply

機能:
- markdown ファイルから「後手スコア = HS + A − 3 − C − M」「α = ベット ÷ ...」等を抽出
- 旧スケール → 新スケール に変換
- 計算結果を新スケールで再計算
- 結論 (CR/コール/フォールド) が変わる場合はマーク
- diff 形式で出力

仕様: knowledges/ds_redesign_v2/SPEC_HANDSCORE.md, SPEC_OTHER_FORMULAS.md
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ============================================================
# 旧 → 新 変換テーブル
# ============================================================

# 旧 C 値 → 新 C 値
OLD_TO_NEW_C = {3: 12, 4: 17, 5: 17, 6: 22, 7: 22, 9: 25, 11: 30}
# 旧 A 値 → 新 A 値
OLD_TO_NEW_A = {3: 12, 2: 6, 1: 0, 0: 0}
# 旧 M 値 → 新 M 値
OLD_TO_NEW_M = {0: 0, 3: 12, 6: 22}

# α と new C の対応
ALPHA_TO_C = {25: 12, 33: 17, 43: 22, 50: 25, 60: 30}
PCT_TO_C = {33: 12, 50: 17, 75: 22, 100: 25, 150: 30}

# 旧 HS → 新 HS の代表対応 (文脈ヒントで分岐)
OLD_HS_TO_NEW = {
    0: 8,    # 完全空振り
    2: 25,   # ハイカード弱
    3: 30,   # セカンドペア弱
    4: 32,   # ボトムペア
    5: 40,   # アンダーペア中
    6: 45,   # TPWK / アンダーペア高
    8: 50,   # TPMK
    10: 50,  # TPMK 相当 (補助)
    12: 55,  # ※非典型 (補助)
    14: 60,  # TPGK 弱め
    15: 62,  # TPGK
    16: 65,  # TPGK 強
    18: 70,  # TPTK / 2pair (top+bot)
    20: 72,  # オーバーペア中 / 2pair (top+mid)
    22: 75,  # 2pair (top+mid)
    25: 80,  # ストレート / 2pair top
    28: 85,  # ストレート上
    30: 88,  # セット / フラッシュ
}

# 文脈ヒントワード → 役カテゴリ → 新 HS
ROLE_HINTS = {
    "TPTK": 70,
    "TPGK": 62,
    "TPMK": 50,
    "TPWK": 45,
    "トップセット": 92,
    "ミドルセット": 88,
    "ボトムセット": 85,
    "セット": 88,
    "オーバーペア": 72,
    "2ペア": 75,
    "2 ペア": 75,
    "ツーペア": 75,
    "アンダーペア": 40,
    "セカンドペア": 35,
    "ボトムペア": 32,
    "フラッシュ": 85,
    "ストレート": 80,
    "クワッズ": 95,
    "フルハウス": 92,
}

# 後手スコア閾値 (新)
NEW_THRESH_RAISE = 40
NEW_THRESH_CALL = 20
# 旧
OLD_THRESH_RAISE = 8
OLD_THRESH_CALL = 0


def predict_new(score: int) -> str:
    if score >= NEW_THRESH_RAISE:
        return "CR"
    if score >= NEW_THRESH_CALL:
        return "コール"
    return "フォールド"


def predict_old(score: int) -> str:
    if score >= OLD_THRESH_RAISE:
        return "CR"
    if score >= OLD_THRESH_CALL:
        return "コール"
    return "フォールド"


# ============================================================
# 正規表現 (検出パターン)
# ============================================================

# 数字を許す (半角/全角マイナス, ハイフン)
_MINUS = r"[-−–—]"
_NUM = r"[+-−–—]?\d+"

# 後手スコア = HS + A − 3 − C [− M] = result → label
RE_BACK_SCORE_FULL = re.compile(
    r"後手スコア\s*=\s*"
    r"(?P<hs>\d+)\s*\+\s*"
    r"(?P<a>\d+)\s*" + _MINUS + r"\s*3\s*" + _MINUS + r"\s*"
    r"(?P<c>\d+)"
    r"(?:\s*" + _MINUS + r"\s*(?P<m>\d+))?"
    r"\s*=\s*(?P<result>" + _NUM + r")"
    r"(?:\s*→\s*(?P<label>\S+))?"
)

# 後手スコア = HS + A − 3 − C (M 無し、result なし版にも対応)
RE_BACK_SCORE_NO_RESULT = re.compile(
    r"後手スコア\s*=\s*"
    r"(?P<hs>\d+)\s*\+\s*"
    r"(?P<a>\d+)\s*" + _MINUS + r"\s*3\s*" + _MINUS + r"\s*"
    r"(?P<c>\d+)"
    r"(?:\s*" + _MINUS + r"\s*(?P<m>\d+))?"
    r"(?!\s*=)"
)

# α = bet ÷ (pot + bet) ≈ 0.XX
RE_ALPHA = re.compile(
    r"α\s*=\s*(?P<bet>\d+)\s*[÷/]\s*\(?\s*"
    r"(?P<pot>\d+)\s*\+\s*(?P<bet2>\d+)\s*\)?"
    r"\s*[≈=]\s*0?\.(?P<dec>\d+)"
)

# HandScore = N (単独行)
RE_HANDSCORE_VAL = re.compile(r"HandScore\s*[=≈]\s*(?P<hs>\d+)(?!\d)")

# 後手スコア = N → result (シンプル版、式なし)
RE_BACK_SCORE_SIMPLE = re.compile(
    r"後手スコア\s*=\s*(?P<score>" + _NUM + r")\s*→\s*(?P<label>\S+)"
)

# CR閾値 (≥N) 等
RE_THRESH_CR = re.compile(r"CR\s*閾値[（(]\s*[≥>=]+\s*(?P<n>\d+)\s*[）)]")
RE_THRESH_CALL_RANGE = re.compile(r"後手スコア\s+(?P<lo>\d+)〜(?P<hi>\d+)")


# ============================================================
# データ構造
# ============================================================
@dataclass
class Match:
    line_no: int
    kind: str  # "back_score_full" / "alpha" / "handscore" / "back_score_simple" / "thresh"
    original: str  # 原文行
    new: str  # 置換後の行
    needs_review: bool = False
    note: str = ""
    decision_change: bool = False
    span: tuple[int, int] = (0, 0)  # 行内のスパン


@dataclass
class FileResult:
    path: Path
    matches: list[Match] = field(default_factory=list)
    new_lines: list[str] = field(default_factory=list)
    total_lines: int = 0


# ============================================================
# 旧スケール HS の自動推測
# ============================================================
def infer_role_score(old_hs: int, context: str) -> tuple[int, bool, str]:
    """旧 HS 値と文脈から新 HS を推測。

    Returns:
        (new_hs, needs_review, note)
    """
    # 文脈から役カテゴリヒントを探す
    for keyword, new_hs in ROLE_HINTS.items():
        if keyword in context:
            # 旧値とヒントが乖離してたら警告
            expected_old = {
                70: 18, 62: 15, 50: 8, 45: 6, 92: 30, 88: 30, 85: 30,
                72: 20, 75: 22, 80: 25, 95: 30, 40: 5, 35: 4, 32: 4,
            }.get(new_hs, None)
            if expected_old is not None and abs(old_hs - expected_old) > 4:
                return new_hs, True, f"文脈は {keyword} だが旧 HS={old_hs} と乖離"
            return new_hs, False, f"文脈ヒント: {keyword}"

    # 文脈なし: テーブル値で変換
    if old_hs in OLD_HS_TO_NEW:
        new_hs = OLD_HS_TO_NEW[old_hs]
        # 役カテゴリ複数該当の旧値は要確認
        ambiguous = old_hs in {18, 20, 30, 0}
        return new_hs, ambiguous, ""

    # テーブル外: 線形補間 (旧 × 4 + 18)
    new_hs = min(100, old_hs * 4 + 18)
    return new_hs, True, f"テーブル外 旧HS={old_hs} を線形補間"


# ============================================================
# 後手スコア式の再計算
# ============================================================
def recalc_back_score(old_hs: int, old_a: int, old_c: int, old_m: int,
                       context: str) -> dict:
    """旧 HS/A/C/M を新スケールに変換し、新後手スコアを計算。"""
    new_hs, hs_review, hs_note = infer_role_score(old_hs, context)
    new_a = OLD_TO_NEW_A.get(old_a, old_a * 4)
    new_c = OLD_TO_NEW_C.get(old_c, old_c * 3)
    new_m = OLD_TO_NEW_M.get(old_m, old_m * 4)

    # 新式: HS + A − C − M (− 3 を A に吸収)
    new_score = new_hs + new_a - new_c - new_m
    old_score = old_hs + old_a - 3 - old_c - old_m

    return {
        "new_hs": new_hs, "new_a": new_a, "new_c": new_c, "new_m": new_m,
        "new_score": new_score, "old_score": old_score,
        "needs_review": hs_review,
        "note": hs_note,
        "old_decision": predict_old(old_score),
        "new_decision": predict_new(new_score),
    }


# ============================================================
# 行単位の処理
# ============================================================
def process_line(line: str, context_window: str) -> list[Match]:
    """1 行から検出されるすべてのマッチを返す。"""
    matches: list[Match] = []

    # --- 1. 後手スコア = HS + A − 3 − C [− M] = N (full) ---
    for m in RE_BACK_SCORE_FULL.finditer(line):
        old_hs = int(m.group("hs"))
        old_a = int(m.group("a"))
        old_c = int(m.group("c"))
        old_m = int(m.group("m") or 0)
        result = m.group("result")
        old_label = (m.group("label") or "").strip()

        ctx = context_window + " " + line
        recalc = recalc_back_score(old_hs, old_a, old_c, old_m, ctx)
        new_score = recalc["new_score"]
        new_label = predict_new(new_score)

        # 新式生成: HS + A − C [− M] (負の score は ASCII の "-" を全角ライクに)
        score_str = f"{new_score}" if new_score >= 0 else f"−{abs(new_score)}"
        if old_m > 0:
            new_expr = (
                f"後手スコア = {recalc['new_hs']} + {recalc['new_a']} "
                f"− {recalc['new_c']} − {recalc['new_m']} = {score_str}"
            )
        else:
            new_expr = (
                f"後手スコア = {recalc['new_hs']} + {recalc['new_a']} "
                f"− {recalc['new_c']} = {score_str}"
            )
        if old_label:
            new_expr += f" → {new_label}"

        # 判定変化検出: 「テキストラベル vs 新計算ラベル」
        # ラベルに "CR"/"コール"/"フォールド"/"レイズ" が含まれるか確認
        def normalize_label(s: str) -> str:
            s = s.replace("検討", "").replace("確定", "").replace("域", "")
            for k in ("CR", "コール", "フォールド", "レイズ"):
                if k in s:
                    if k == "レイズ":
                        return "CR"
                    return k
            return s

        old_label_norm = normalize_label(old_label) if old_label else \
            recalc["old_decision"]
        new_label_norm = recalc["new_decision"]

        decision_change = bool(old_label) and (old_label_norm != new_label_norm)
        # ラベルなしのケースは数値閾値で判定
        if not old_label:
            decision_change = (recalc["old_decision"] != recalc["new_decision"])

        note = recalc["note"]
        if decision_change:
            note += (f"  [判定変化! 旧 {old_label_norm} "
                     f"→ 新 {new_label_norm}]")

        matches.append(Match(
            line_no=0, kind="back_score_full",
            original=line[m.start():m.end()],
            new=new_expr,
            needs_review=recalc["needs_review"],
            note=note,
            decision_change=decision_change,
            span=(m.start(), m.end()),
        ))

    # --- 2. α 計算 (旧→新は変更なしなので情報のみ) ---
    for m in RE_ALPHA.finditer(line):
        # α 値はストリート関係なく不変
        bet = int(m.group("bet"))
        pot = int(m.group("pot"))
        dec = m.group("dec")
        # α = bet / (pot + bet)
        alpha = bet / (pot + bet)
        new_expr = f"α = {bet} ÷ ({pot} + {bet}) ≈ {alpha:.2f}"
        # 値は同じなので置換不要
        matches.append(Match(
            line_no=0, kind="alpha",
            original=line[m.start():m.end()],
            new=new_expr,
            needs_review=False,
            note="α 値は不変 (新旧共通)",
            span=(m.start(), m.end()),
        ))

    # --- 3. HandScore = N (単独) ---
    for m in RE_HANDSCORE_VAL.finditer(line):
        old_hs = int(m.group("hs"))
        # 既に新スケール (40+ 等) ならスキップ
        if old_hs >= 35 and old_hs not in {35}:
            # 新スケール値の可能性 (HS=50/62/70/85 等)
            # 既知の旧→新マッピングで重複する値 (8, 30, 18, 25, 22, 20, 15, 14, 6, 4, 0, 2, 3, 5, 10, 12)
            # >= 35 かつ 旧値マッピングに無い (or 新スケール値) はスキップ
            if old_hs not in OLD_HS_TO_NEW:
                continue
            # 既存値が新スケール値 (50, 62, 70, 85, 88, 92, 95) ならスキップ
            new_scale_values = {32, 40, 42, 45, 50, 55, 60, 62, 65, 68, 70, 72,
                                75, 78, 80, 82, 85, 88, 90, 92, 95}
            if old_hs in new_scale_values:
                continue

        ctx = context_window + " " + line
        new_hs, needs_review, note = infer_role_score(old_hs, ctx)

        # 値が変わらない場合 (例: 既に新スケール) はスキップ
        if new_hs == old_hs:
            continue

        new_expr = f"HandScore = {new_hs}"
        matches.append(Match(
            line_no=0, kind="handscore",
            original=line[m.start():m.end()],
            new=new_expr,
            needs_review=needs_review,
            note=note,
            span=(m.start(), m.end()),
        ))

    # --- 4. CR 閾値 (≥N) → 新閾値 ---
    for m in RE_THRESH_CR.finditer(line):
        n = int(m.group("n"))
        if n == OLD_THRESH_RAISE:
            new_expr = f"CR閾値（≥{NEW_THRESH_RAISE}）"
            matches.append(Match(
                line_no=0, kind="thresh",
                original=line[m.start():m.end()],
                new=new_expr,
                needs_review=False,
                note="閾値 8 → 40",
                span=(m.start(), m.end()),
            ))

    return matches


# ============================================================
# ファイル単位処理
# ============================================================
def process_markdown(path: Path, apply: bool = False) -> FileResult:
    """ファイルを処理して結果を返す。"""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    result = FileResult(path=path, total_lines=len(lines))
    new_lines: list[str] = []

    for i, line in enumerate(lines):
        # 文脈は前後 3 行
        ctx_lo = max(0, i - 3)
        ctx_hi = min(len(lines), i + 3)
        context_window = "".join(lines[ctx_lo:ctx_hi])

        line_matches = process_line(line, context_window)

        if not line_matches:
            new_lines.append(line)
            continue

        # 行内のスパンを後ろから置換
        new_line = line
        sorted_matches = sorted(line_matches, key=lambda x: -x.span[0])
        for m in sorted_matches:
            m.line_no = i + 1
            # 置換 (改行を保持)
            new_line = (new_line[:m.span[0]] + m.new + new_line[m.span[1]:])
            result.matches.append(m)

        new_lines.append(new_line)

    result.new_lines = new_lines

    if apply:
        path.write_text("".join(new_lines), encoding="utf-8")

    return result


# ============================================================
# 出力フォーマット
# ============================================================
def format_diff(result: FileResult) -> str:
    """diff 形式で出力。"""
    out: list[str] = []
    out.append(f"=== {result.path.absolute()} ===\n")
    if not result.matches:
        out.append("  (検出なし)\n")
        return "".join(out)

    for m in result.matches:
        marker = ""
        if m.decision_change:
            marker = " ⚠ 判定変化"
        elif m.needs_review:
            marker = " ⚠ 要手動確認"
        out.append(f"L{m.line_no} [{m.kind}]{marker}:\n")
        out.append(f"  - {m.original.strip()}\n")
        out.append(f"  + {m.new.strip()}\n")
        if m.note:
            out.append(f"    note: {m.note}\n")
    return "".join(out)


# ============================================================
# メイン
# ============================================================
def collect_chapter_files(root: Path) -> list[Path]:
    """全巻の chapters/*.md を収集。"""
    files: list[Path] = []
    for book in ["preflop", "flop", "flop-advanced", "volume4", "volume5",
                 "volume6", "digest"]:
        ch_dir = root / book / "chapters"
        if ch_dir.is_dir():
            files.extend(sorted(ch_dir.glob("*.md")))
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=str, help="単一ファイル指定 (相対 or 絶対)")
    parser.add_argument("--all", action="store_true", help="全巻 chapters を処理")
    parser.add_argument("--apply", action="store_true", help="ファイルを書き換え")
    parser.add_argument("--dry-run", action="store_true", help="プレビューのみ")
    parser.add_argument("--root", type=str,
                        default="/home/cuzic/poker-books",
                        help="リポジトリルート")
    args = parser.parse_args()

    root = Path(args.root)
    apply = args.apply and not args.dry_run

    files: list[Path] = []
    if args.file:
        p = Path(args.file)
        if not p.is_absolute():
            p = root / p
        files = [p]
    elif args.all:
        files = collect_chapter_files(root)
    else:
        parser.print_help()
        return 1

    total_matches = 0
    auto_count = 0
    review_count = 0
    decision_count = 0
    file_count = 0

    for f in files:
        if not f.is_file():
            continue
        file_count += 1
        result = process_markdown(f, apply=apply)
        if not result.matches:
            continue
        sys.stdout.write(format_diff(result))
        sys.stdout.write("\n")

        total_matches += len(result.matches)
        for m in result.matches:
            if m.needs_review:
                review_count += 1
            else:
                auto_count += 1
            if m.decision_change:
                decision_count += 1

    sys.stdout.write("=" * 60 + "\n")
    sys.stdout.write("=== サマリー ===\n")
    sys.stdout.write(f"  処理ファイル: {file_count}\n")
    sys.stdout.write(f"  検出計算式: {total_matches} 件\n")
    sys.stdout.write(f"  自動変換: {auto_count} 件\n")
    sys.stdout.write(f"  要手動確認: {review_count} 件\n")
    sys.stdout.write(f"  判定変化: {decision_count} 件\n")
    if apply:
        sys.stdout.write("\n  [apply モード] ファイルを書き換えました\n")
    else:
        sys.stdout.write("\n  [dry-run] --apply で書き換え可能\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
