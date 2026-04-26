#!/usr/bin/env python3
"""巻4 検証タスク #102 (ターン CBet 頻度モデル) 用シナリオ JSON 生成スクリプト.

30 フロップ × 9 ターンカード = 270 シナリオを生成し、
/home/cuzic/poker-books/knowledges/volume4/scenarios/102/ 配下に
1 シナリオ = 1 JSON ファイルとして出力する。

30 フロップは `verify_flop_gto.py` の GTO_BOARD_DATA (ボードラベル + GTO CBet 頻度)
を出典とし、ラベル → 具体カード (例: K72r → ['Kc','7d','2s']) に正規化する。

9 ターンカードは 5 分類 (オーバーカード / ブランク / ペア / フラッシュ / 連結) を
カバーするように残り 49 枚から選定する。各分類の優先度付きカウントで合計 9 枚を確保。

スキーマ: /home/cuzic/poker-gto/docs/schemas/scenario.schema.json (draft-07)
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
RANK_VALUES = {r: i + 2 for i, r in enumerate(RANKS)}  # "2"->2, ..., "A"->14
SUITS = ["c", "d", "h", "s"]

# 出力先ディレクトリ
OUTPUT_DIR = Path(
    "/home/cuzic/poker-books/knowledges/volume4/scenarios/102"
)

# スキーマ位置 (検証用、任意)
SCHEMA_PATH = Path(
    "/home/cuzic/poker-gto/docs/schemas/scenario.schema.json"
)


# ---------------------------------------------------------------------------
# 30 フロップ: verify_flop_gto.py の GTO_BOARD_DATA 由来
# 各ラベルを具体カード 3 枚に正規化 (suit の割付はルール通り)。
#
# ラベル末尾:
#   r    = rainbow (全 3 枚異スート)。慣例として c/d/s の 3 スートを割付
#   ss   = two-tone (2 枚同スート)。上位 2 枚を s、下位 1 枚を h とする
#   mono = monotone (3 枚同スート)。全て s
#   末尾無し = 裸のランクのみ (K44, AAK など)。ペアボードは rainbow 化:
#             ペアの 2 枚を c/d、ペア外を s に割付
# ---------------------------------------------------------------------------


def _cards_for_label(label: str) -> Tuple[List[str], str]:
    """ボードラベル → (3 枚のカード配列, suit 分類タグ).

    返り値の 2 要素目は "rainbow" / "two-tone" / "monotone" / "paired-rainbow" の
    いずれか。ターンカード分類のフラッシュ判定に使う。
    """
    # ランク部分を抽出 (T/J/Q/K/A は 1 文字、数字も 1 文字)
    ranks: List[str] = []
    i = 0
    while i < len(label) and label[i] in RANK_VALUES:
        ranks.append(label[i])
        i += 1
    tail = label[i:].lower()

    if tail == "mono":
        # 3 枚同スート
        suits = ["s", "s", "s"]
        tag = "monotone"
    elif tail == "ss":
        # 2 枚同スート (ss) — 上位 2 枚を s、最下位を h
        suits = ["s", "s", "h"]
        tag = "two-tone"
    elif tail == "r":
        # rainbow 3 種
        suits = ["c", "d", "s"]
        tag = "rainbow"
    elif tail == "":
        # 裸のランクのみ (ペアボードなど)。rainbow と見做す
        suits = ["c", "d", "s"]
        tag = "paired-rainbow" if len(set(ranks)) < len(ranks) else "rainbow"
    else:
        raise ValueError(f"unknown board label tail: {label!r}")

    cards = [r + s for r, s in zip(ranks, suits)]
    # 重複カードがないことを念のため確認
    if len(set(cards)) != len(cards):
        raise ValueError(f"duplicate card in label {label!r}: {cards}")
    return cards, tag


# verify_flop_gto.py の GTO_BOARD_DATA から 30 ボードラベル (順序維持)
GTO_BOARD_LABELS: List[str] = [
    "K72r", "A72r", "K44", "Q53r", "A82r", "K83r", "A52r", "K95r",  # ドライ 8
    "KT5r", "J75r", "Q83ss", "AT7ss", "J84ss", "QJ9r", "T87r", "876r",  # セミウェット 8
    "987ss", "JT9ss", "987mono", "KQTss", "AKQmono", "JT8ss", "T98r", "T98ss",  # ウェット 8
    "772", "AAK", "KK9", "965r", "632r", "A99",  # 特殊 (ペアボード等) 6
]

assert len(GTO_BOARD_LABELS) == 30, "30 flops expected"


# ---------------------------------------------------------------------------
# 9 ターンカード選定ロジック
# ---------------------------------------------------------------------------


def _board_suit_counts(board_cards: List[str]) -> Counter:
    return Counter(c[1] for c in board_cards)


def _classify_turn(
    turn_card: str, board_cards: List[str]
) -> str:
    """ターンカードを 5 分類のいずれかに割り当てる (優先度順).

    優先度:
      1. pair       : ボードのいずれかのランクと一致
      2. overcard   : ボード最高ランクより上
      3. flush      : そのスートがボードに既に 2 枚以上ある (フラッシュドロー接近)
      4. connector  : 3 枚でストレートを形成しうる連結域 (隣接ランク ±2 以内、
                      かつボードランクのいずれかと差 2 以内) — 真にストレート接近するカードのみ
      5. blank      : 上記以外 (ボードから離れたミドル/ローで関連が薄い)
    """
    r = turn_card[0]
    s = turn_card[1]
    r_val = RANK_VALUES[r]
    board_ranks = [RANK_VALUES[c[0]] for c in board_cards]
    max_rank = max(board_ranks)

    # 1. ペア判定
    if r_val in board_ranks:
        return "pair"

    # 2. オーバーカード (同一ランクは pair で先に判定済)
    if r_val > max_rank:
        return "overcard"

    # 3. フラッシュ系 (ボードに同スートが既に 2+ 枚)
    suit_counts = _board_suit_counts(board_cards)
    if suit_counts.get(s, 0) >= 2:
        return "flush"

    # 4. 連結系: ボードランクに接近 (±2 以内) で、かつボードの 2 枚以上と "ストレート距離"
    #    (= sorted(board ∪ {turn}) の隣接 gap が全て ≤3) が近いものに限定。
    sorted_with = sorted(set(board_ranks) | {r_val}, reverse=True)
    # 最大の隣接 gap
    gaps = [
        sorted_with[i] - sorted_with[i + 1] for i in range(len(sorted_with) - 1)
    ]
    max_gap = max(gaps) if gaps else 99
    near_any = any(abs(r_val - br) <= 2 for br in board_ranks)
    if near_any and max_gap <= 3:
        return "connector"

    # 5. ブランク
    return "blank"


def _all_remaining_cards(board_cards: List[str]) -> List[str]:
    used = set(board_cards)
    return [r + s for r in RANKS for s in SUITS if (r + s) not in used]


# 分類ごとの目標枚数 (合計 9)
CATEGORY_TARGETS: Dict[str, int] = {
    "overcard": 2,
    "blank": 2,
    "pair": 2,
    "flush": 1,
    "connector": 2,
}
assert sum(CATEGORY_TARGETS.values()) == 9


def _pick_turn_cards(board_cards: List[str]) -> List[Tuple[str, str]]:
    """(turn_card, category) のリストを 9 個返す.

    手順:
      1. 49 枚残りカードを全て分類済みバケットに仕分け
      2. カテゴリごとの目標枚数を順に満たす (ランクを分散させるため rank 差大きい順)
      3. 不足分は余剰カテゴリから補充 (カテゴリ名は "flex" として記録)
    """
    remaining = _all_remaining_cards(board_cards)
    buckets: Dict[str, List[str]] = {
        "overcard": [],
        "blank": [],
        "pair": [],
        "flush": [],
        "connector": [],
    }
    for card in remaining:
        cat = _classify_turn(card, board_cards)
        buckets[cat].append(card)

    # ランクが被りすぎないよう、各バケット内を「rank 値の偏り」を減らす順に並べる
    # 具体的には、rank 値に基づいて先頭と末尾から交互に取ると多様性が増す。
    def _diversify(cards: List[str]) -> List[str]:
        # rank 昇順で並べ、先頭/末尾を交互に取り出す
        s = sorted(cards, key=lambda c: (RANK_VALUES[c[0]], c[1]))
        result: List[str] = []
        lo, hi = 0, len(s) - 1
        pick_high = True
        while lo <= hi:
            if pick_high:
                result.append(s[hi])
                hi -= 1
            else:
                result.append(s[lo])
                lo += 1
            pick_high = not pick_high
        return result

    for k in buckets:
        buckets[k] = _diversify(buckets[k])

    picked: List[Tuple[str, str]] = []
    picked_set: set = set()

    # 第一段階 (a): 各カテゴリから可能な限り "最低 1 枚" を確保
    #   (空バケットは飛ばす)。これで 5 分類のカバレッジを最大化する。
    for cat in CATEGORY_TARGETS.keys():
        for card in buckets[cat]:
            if card in picked_set:
                continue
            picked.append((card, cat))
            picked_set.add(card)
            break

    # 第一段階 (b): 各カテゴリの目標枚数を埋める
    for cat, target in CATEGORY_TARGETS.items():
        taken = sum(1 for _, c in picked if c == cat)
        for card in buckets[cat]:
            if taken >= target:
                break
            if card in picked_set:
                continue
            picked.append((card, cat))
            picked_set.add(card)
            taken += 1

    # 第二段階: 不足している場合、非空カテゴリから補充
    # ボードによっては分類そのものが存在しない (例: AKQmono で overcard は A のみ、
    # pair は 9 枚存在など) ので、不足時は全バケットから rank/suit 多様性を見て補う
    if len(picked) < 9:
        # 補充用プール: 未採用カード全て
        pool: List[Tuple[str, str]] = []
        for cat, cards in buckets.items():
            for card in cards:
                if card not in picked_set:
                    pool.append((card, cat))
        # ボード最高ランクと被らないランク優先 → rank 差が大きい方が分類上情報量あり
        board_ranks = [RANK_VALUES[c[0]] for c in board_cards]

        def _diversity_key(item: Tuple[str, str]) -> Tuple[int, int]:
            card, _ = item
            r_val = RANK_VALUES[card[0]]
            # すでに採用したターンランクの集合
            taken_ranks = {RANK_VALUES[c[0]] for c, _ in picked}
            rank_clash = 1 if r_val in taken_ranks else 0
            board_dist = min(abs(r_val - br) for br in board_ranks)
            # 既存ランクと被らない方を優先、board から遠い方を優先
            return (rank_clash, -board_dist)

        pool.sort(key=_diversity_key)
        for card, cat in pool:
            if len(picked) >= 9:
                break
            picked.append((card, cat))
            picked_set.add(card)

    # 第三段階: 超過があれば切り詰め (ここでは起きないはず)
    picked = picked[:9]

    if len(picked) != 9:
        raise RuntimeError(
            f"failed to pick 9 turns for board {board_cards}: got {len(picked)}"
        )
    return picked


# ---------------------------------------------------------------------------
# シナリオ JSON ビルド
# ---------------------------------------------------------------------------


def _build_scenario(
    board_label: str,
    board_cards: List[str],
    turn_card: str,
    category: str,
) -> Dict:
    """270 のうち 1 シナリオ分の dict を構築する."""
    category_ja = {
        "overcard": "オーバーカード",
        "blank": "ブランク",
        "pair": "ペア",
        "flush": "フラッシュ",
        "connector": "連結",
    }[category]

    scenario_id = f"turn_cbet_102_{board_label}_{turn_card}"
    description = f"{board_label} + {turn_card} ({category_ja})"

    return {
        "scenario_id": scenario_id,
        "description": description,
        "street_to_solve": "turn",
        "board": [*board_cards, turn_card],
        # プリフロップ: BTN 2.5x, BB call, フロップ cbet 33% call → ≈10 BB
        "pot_bb": 10,
        # 100bb エフェクティブから、オープン 2.5 + フロップ cbet 1.8 ≈ 4.3 投入、
        # 残り 95.7。丸めて 92 (ターン cbet への最大 bet 余力)
        "effective_stack_bb": 92,
        # BTN オープン側が IP → "BTN" を採用 (hero_position enum に含まれる)
        "hero_position": "BTN",
        "hero_range": {"preset": "BtnOpen100bb"},
        "villain_range": {"preset": "BbDefendVsBtn"},
        "bet_sizes_to_evaluate": [0.33, 0.5, 0.75, 1.5],
        "solver_config": {
            "algorithm": "ES_MCCFR",
            "iterations": 5000,
            "timeout_sec": 60,
            "rng_seed": 42,
            "exploitability_target_bb": 0.05,
        },
    }


# ---------------------------------------------------------------------------
# ファイル出力
# ---------------------------------------------------------------------------


def _write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _validate_against_schema(scenario: Dict, schema: Optional[Dict]) -> None:
    if schema is None:
        return
    try:
        import jsonschema  # 遅延 import
    except ImportError:
        return
    jsonschema.validate(scenario, schema)


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> None:
    # スキーマ読み込み (任意)
    schema: Optional[Dict] = None
    if SCHEMA_PATH.exists():
        try:
            schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            schema = None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 冪等性のため、既存の turn_cbet_102_*.json / index.json を一旦クリア
    for p in OUTPUT_DIR.glob("turn_cbet_102_*.json"):
        p.unlink()
    index_path = OUTPUT_DIR / "index.json"
    if index_path.exists():
        index_path.unlink()

    index_scenarios: List[Dict[str, Any]] = []
    category_counter: Counter = Counter()

    for board_label in GTO_BOARD_LABELS:
        board_cards, _ = _cards_for_label(board_label)
        turns = _pick_turn_cards(board_cards)

        for turn_card, category in turns:
            scenario = _build_scenario(
                board_label=board_label,
                board_cards=board_cards,
                turn_card=turn_card,
                category=category,
            )
            _validate_against_schema(scenario, schema)

            out_path = OUTPUT_DIR / f"{scenario['scenario_id']}.json"
            _write_json(out_path, scenario)

            index_scenarios.append(
                {
                    "scenario_id": scenario["scenario_id"],
                    "board_label": board_label,
                    "flop_cards": board_cards,
                    "turn_card": turn_card,
                    "category": category,
                    "file": out_path.name,
                }
            )
            category_counter[category] += 1

    # index.json を書き出す
    index_payload = {
        "task": "102",
        "title": "ターン CBet 頻度モデル (BDM_turn)",
        "total": len(index_scenarios),
        "flops": len(GTO_BOARD_LABELS),
        "turns_per_flop": 9,
        "categories": dict(category_counter),
        "scenarios": index_scenarios,
    }
    _write_json(OUTPUT_DIR / "index.json", index_payload)

    # 終了サマリを標準出力
    print(f"generated {len(index_scenarios)} scenarios in {OUTPUT_DIR}")
    print("categories:", dict(category_counter))


if __name__ == "__main__":
    main()
