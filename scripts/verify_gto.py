#!/usr/bin/env python3
"""本書の基本スコア式と標準 GTO レンジの一致率を検証する。

データソース: GTO Wizard の公開プリフロップチャートに基づく
              標準的な 6-max 100BB キャッシュのオープン/3bet レンジ
本書の式:
  Score = H + L + ボーナス − ペナルティ
  ポジション別しきい値: UTG 24 / MP 22 / CO 20 / BTN 18 / SB 20

対 3bet のしきい値も同様に検証する。
"""
from __future__ import annotations

# ------------------------------------------------------------------------
# 本書の基本スコア式
# ------------------------------------------------------------------------

RANK_VALUES = {
    "A": 14, "K": 13, "Q": 12, "J": 11, "T": 10,
    "9": 9, "8": 8, "7": 7, "6": 6, "5": 5, "4": 4, "3": 3, "2": 2,
}
RANK_ORDER = ["A", "K", "Q", "J", "T", "9", "8", "7", "6", "5", "4", "3", "2"]


def calc_score(c1: str, c2: str, suited: bool) -> float:
    """基本スコア式 Score = H + L + ボーナス − ペナルティ"""
    v1, v2 = RANK_VALUES[c1], RANK_VALUES[c2]
    h, l = max(v1, v2), min(v1, v2)
    is_pair = c1 == c2
    diff = abs(v1 - v2)

    # Wheel 特例: A-5 の A は 1 として扱う（本書 5 章に従う）
    # ただし本書は素朴に差で判定するので、標準的に A=14 で計算。

    score = h + l
    # ペア: +10 だが、ペアにはその他のボーナス/ペナルティは適用しない
    if is_pair:
        return score + 10
    # スーテッド: +2
    if suited:
        score += 2
    # コネクター: diff == 1 → +1
    if diff == 1:
        score += 1
    # ギャップ2以内（diff 2〜3）: +0.5
    elif diff in (2, 3):
        score += 0.5
    # ギャップ3以上（diff >= 4）: −1
    if diff >= 4:
        score -= 1
    # 両方 9 未満: −1（ペアには適用しないが、ペアは上で早期 return）
    if h < 9:
        score -= 1
    return score


# ポジション別オープンしきい値（本書 5-2 節）
OPEN_THRESHOLDS = {
    "UTG": 24,
    "MP": 22,
    "CO": 20,
    "BTN": 18,
    "SB": 20,
    # BB はオープンしない
}

# 対オープン者別 3bet しきい値（本書 12 章）
THREEBET_THRESHOLDS = {
    "UTG": 23,
    "MP": 21,
    "CO": 19,
    "BTN": 18,
    "SB": 20,  # 本書 21 章で新設
}


# ------------------------------------------------------------------------
# GTO レンジ（GTO Wizard の公開チャートに基づく 6-max 100BB キャッシュの標準値）
# ------------------------------------------------------------------------

GTO_OPEN_RANGES = {
    "UTG": "22+,ATs+,KTs+,QTs+,JTs,AJo+,KQo",
    "MP": "22+,A9s+,KTs+,QTs+,JTs,T9s,98s,ATo+,KQo",
    "CO": "22+,A2s+,K5s+,Q8s+,J8s+,T8s+,98s,87s,76s,65s,A5o+,KTo+,QTo+,JTo",
    "BTN": "22+,A2s+,K2s+,Q4s+,J6s+,T6s+,96s+,85s+,75s+,65s,54s,A2o+,K8o+,Q9o+,J8o+,T8o+,98o,87o",
    "SB": "22+,A2s+,K2s+,Q6s+,J7s+,T7s+,97s+,86s+,76s,65s,54s,A3o+,K8o+,Q9o+,J9o+,T9o",
}

GTO_3BET_RANGES = {
    "UTG": "QQ+,AKs,AKo",
    "MP": "JJ+,AKs,AQs,AKo",
    "CO": "TT+,AJs+,AQo+,KQs",
    "BTN": "88+,ATs+,AJo+,KQs,KJs,QJs",
    "SB": "77+,A9s+,ATo+,KTs+,KQo,QJs,JTs",
}


# ------------------------------------------------------------------------
# レンジ文字列のパース
# ------------------------------------------------------------------------

def rank_index(r: str) -> int:
    return RANK_ORDER.index(r)


def expand_token(token: str) -> set[tuple[str, str, bool]]:
    """レンジトークンを (hi_rank, lo_rank, is_suited) の集合に展開。
    例: "22+" → {("2","2",False), ("3","3",False), ..., ("A","A",False)}
        "ATs+" → {("A","T",True), ("A","J",True), ("A","Q",True), ("A","K",True)}
        "KQo" → {("K","Q",False)}
        "AKs" → {("A","K",True)}
    """
    result: set[tuple[str, str, bool]] = set()
    has_plus = token.endswith("+")
    if has_plus:
        token = token[:-1]

    # ペア
    if len(token) == 2 and token[0] == token[1]:
        rank = token[0]
        start_idx = rank_index(rank)
        end_idx = 0  # A
        if has_plus:
            for i in range(end_idx, start_idx + 1):
                r = RANK_ORDER[i]
                result.add((r, r, False))
        else:
            result.add((rank, rank, False))
        return result

    # ハイカード+ロー+スーテッド指示子
    if len(token) == 3 and token[2] in ("s", "o"):
        hi, lo, s = token[0], token[1], token[2] == "s"
        hi_idx = rank_index(hi)
        lo_idx = rank_index(lo)
        if has_plus:
            # ローを上に詰める: ATs+ → AT, AJ, AQ, AK（ロー rank が上がる）
            for i in range(lo_idx, hi_idx, -1):
                r_lo = RANK_ORDER[i]
                result.add((hi, r_lo, s))
        else:
            result.add((hi, lo, s))
        return result

    # 簡易フォールバック: 未対応形式はスキップ
    return result


def parse_range(range_str: str) -> set[tuple[str, str, bool]]:
    """GTO レンジ文字列 → ハンド集合"""
    hands: set[tuple[str, str, bool]] = set()
    for token in range_str.split(","):
        token = token.strip()
        if not token:
            continue
        hands |= expand_token(token)
    return hands


# ------------------------------------------------------------------------
# 検証: 169 ハンド全てについて 本書式 vs GTO の一致を計算
# ------------------------------------------------------------------------

def enumerate_169_hands() -> list[tuple[str, str, bool]]:
    """169 種類のハンドを列挙"""
    hands = []
    for i, r1 in enumerate(RANK_ORDER):
        for j, r2 in enumerate(RANK_ORDER):
            if i == j:
                hands.append((r1, r1, False))  # ペア
            elif i < j:
                hands.append((r1, r2, True))   # スーテッド
                hands.append((r1, r2, False))  # オフスート
    return hands


def hand_label(h: tuple[str, str, bool]) -> str:
    r1, r2, s = h
    if r1 == r2:
        return r1 + r2
    return f"{r1}{r2}{'s' if s else 'o'}"


def verify_open() -> dict[str, dict[str, int]]:
    """ポジション別オープン判定の本書 vs GTO 比較"""
    stats = {}
    for pos, threshold in OPEN_THRESHOLDS.items():
        gto_hands = parse_range(GTO_OPEN_RANGES[pos])
        tp = fp = tn = fn = 0  # 本書 open=T/F × GTO open=T/F の2x2
        disagreements = []
        for hand in enumerate_169_hands():
            r1, r2, suited = hand
            score = calc_score(r1, r2, suited)
            book_opens = score >= threshold
            gto_opens = hand in gto_hands
            if book_opens and gto_opens:
                tp += 1
            elif book_opens and not gto_opens:
                fp += 1
                disagreements.append(("FP", hand_label(hand), score, threshold))
            elif not book_opens and gto_opens:
                fn += 1
                disagreements.append(("FN", hand_label(hand), score, threshold))
            else:
                tn += 1
        stats[pos] = {
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "accuracy": (tp + tn) / (tp + fp + tn + fn),
            "precision": tp / (tp + fp) if tp + fp > 0 else 0.0,
            "recall": tp / (tp + fn) if tp + fn > 0 else 0.0,
            "disagreements": disagreements,
        }
    return stats


def verify_3bet() -> dict[str, dict[str, int]]:
    """対オープン者別 3bet 判定の本書 vs GTO 比較"""
    stats = {}
    for pos, threshold in THREEBET_THRESHOLDS.items():
        if pos not in GTO_3BET_RANGES:
            continue
        gto_hands = parse_range(GTO_3BET_RANGES[pos])
        tp = fp = tn = fn = 0
        disagreements = []
        for hand in enumerate_169_hands():
            r1, r2, suited = hand
            # 3bet スコア式は簡易的に Score (base) を使用。
            # 本書 12 章の 3bet スコア式は base に H + 0.5L + B + S + C − G − R の補正を入れるが、
            # この検証では base score で閾値判定を行う（定性的な傾向を見る）。
            score = calc_score(r1, r2, suited)
            book_3bets = score >= threshold
            gto_3bets = hand in gto_hands
            if book_3bets and gto_3bets:
                tp += 1
            elif book_3bets and not gto_3bets:
                fp += 1
                disagreements.append(("FP", hand_label(hand), score, threshold))
            elif not book_3bets and gto_3bets:
                fn += 1
                disagreements.append(("FN", hand_label(hand), score, threshold))
            else:
                tn += 1
        stats[pos] = {
            "TP": tp, "FP": fp, "TN": tn, "FN": fn,
            "accuracy": (tp + tn) / (tp + fp + tn + fn),
            "precision": tp / (tp + fp) if tp + fp > 0 else 0.0,
            "recall": tp / (tp + fn) if tp + fn > 0 else 0.0,
            "disagreements": disagreements,
        }
    return stats


def format_report(open_stats, threebet_stats) -> str:
    out = ["# 本書基本スコア式 vs GTO レンジ 検証結果\n"]
    out.append("データソース: GTO Wizard の公開チャート（6-max 100BB キャッシュ）\n")
    out.append("169 ハンド全てについて、本書のオープン／3bet 判定と GTO レンジの一致率を算出。\n")

    out.append("\n## オープン判定\n\n")
    out.append("| ポジション | しきい値 | 一致率 | 精度 | 再現率 | TP | FP | TN | FN |\n")
    out.append("|-----------|---------|-------|-----|-------|----|----|----|----|\n")
    for pos, s in open_stats.items():
        out.append(
            f"| {pos} | {OPEN_THRESHOLDS[pos]} | {s['accuracy']*100:.1f}% | "
            f"{s['precision']*100:.1f}% | {s['recall']*100:.1f}% | "
            f"{s['TP']} | {s['FP']} | {s['TN']} | {s['FN']} |\n"
        )

    out.append("\n### オープン：各ポジションの不一致ハンド（サンプル）\n")
    for pos, s in open_stats.items():
        if not s["disagreements"]:
            continue
        fp = [d for d in s["disagreements"] if d[0] == "FP"]
        fn = [d for d in s["disagreements"] if d[0] == "FN"]
        out.append(f"\n**{pos}**（しきい値 {OPEN_THRESHOLDS[pos]}）\n")
        if fp:
            out.append(f"- FP（本書は打つが GTO は打たない）: {', '.join(d[1] for d in fp[:8])}\n")
        if fn:
            out.append(f"- FN（本書は打たないが GTO は打つ）: {', '.join(d[1] for d in fn[:8])}\n")

    out.append("\n## 3bet 判定（本書 12 章の対オープン者別しきい値）\n\n")
    out.append("| 対ポジション | しきい値 | 一致率 | 精度 | 再現率 | TP | FP | TN | FN |\n")
    out.append("|------------|---------|-------|-----|-------|----|----|----|----|\n")
    for pos, s in threebet_stats.items():
        out.append(
            f"| 対{pos} | {THREEBET_THRESHOLDS[pos]} | {s['accuracy']*100:.1f}% | "
            f"{s['precision']*100:.1f}% | {s['recall']*100:.1f}% | "
            f"{s['TP']} | {s['FP']} | {s['TN']} | {s['FN']} |\n"
        )

    out.append("\n### 3bet：不一致ハンド（サンプル）\n")
    for pos, s in threebet_stats.items():
        if not s["disagreements"]:
            continue
        fp = [d for d in s["disagreements"] if d[0] == "FP"]
        fn = [d for d in s["disagreements"] if d[0] == "FN"]
        out.append(f"\n**対{pos}**（しきい値 {THREEBET_THRESHOLDS[pos]}）\n")
        if fp:
            out.append(f"- FP: {', '.join(d[1] for d in fp[:8])}\n")
        if fn:
            out.append(f"- FN: {', '.join(d[1] for d in fn[:8])}\n")

    # 全体集計
    total_tp = sum(s["TP"] for s in open_stats.values())
    total_fp = sum(s["FP"] for s in open_stats.values())
    total_fn = sum(s["FN"] for s in open_stats.values())
    total_tn = sum(s["TN"] for s in open_stats.values())
    total = total_tp + total_fp + total_fn + total_tn
    out.append(f"\n## 全体集計\n\n")
    out.append(f"- **オープン判定**: {total_tp + total_tn}/{total} 一致 = "
               f"{(total_tp + total_tn) / total * 100:.1f}%\n")
    out.append(f"  - FP（本書過剰）: {total_fp} ハンド ({total_fp / total * 100:.1f}%)\n")
    out.append(f"  - FN（本書不足）: {total_fn} ハンド ({total_fn / total * 100:.1f}%)\n")

    t_tp = sum(s["TP"] for s in threebet_stats.values())
    t_fp = sum(s["FP"] for s in threebet_stats.values())
    t_fn = sum(s["FN"] for s in threebet_stats.values())
    t_tn = sum(s["TN"] for s in threebet_stats.values())
    t = t_tp + t_fp + t_fn + t_tn
    out.append(f"- **3bet 判定**: {t_tp + t_tn}/{t} 一致 = "
               f"{(t_tp + t_tn) / t * 100:.1f}%\n")
    out.append(f"  - FP: {t_fp} ({t_fp / t * 100:.1f}%)\n")
    out.append(f"  - FN: {t_fn} ({t_fn / t * 100:.1f}%)\n")
    return "".join(out)


def main() -> None:
    open_stats = verify_open()
    threebet_stats = verify_3bet()
    print(format_report(open_stats, threebet_stats))


if __name__ == "__main__":
    main()
