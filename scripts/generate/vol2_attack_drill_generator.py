#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
vol2_attack_drill_generator.py
アタックルール (BET vs CHECK) ドリルカード生成
出力: poker-drill/src/data/matcha-framework-attack-decisions-cards.ts

実行: uv run scripts/generate/vol2_attack_drill_generator.py
"""
from __future__ import annotations
import json
from pathlib import Path

POKER_DRILL = Path(__file__).parent.parent.parent.parent / "poker-drill"
OUT = POKER_DRILL / "src" / "data" / "matcha-framework-attack-decisions-cards.ts"

DECK_ID = "matcha_framework_attack_decisions"
EXPORT_NAME = "matchaFrameworkAttackDecisionsCards"
PREFIX = "mfatk"


def card(seq: int, group: str, group_label: str,
         scenario: str, question: str,
         answer: str, body: str, bullets: list[str],
         board: str = "", hand: str = "",
         tables: list[dict] | None = None) -> dict:
    front: dict = {"scenario": scenario, "question": question}
    if board:
        front["board"] = board
    if hand:
        front["hand"] = hand
    detail: dict = {"body": body, "bullets": bullets}
    if tables:
        detail["tables"] = tables
    return {
        "id": f"{PREFIX}_{seq:03d}",
        "model": "knowledge",
        "deck": DECK_ID,
        "group": group,
        "groupLabel": group_label,
        "front": front,
        "back": {"answer": answer, "knowledgeDetail": detail},
    }


RULE_TABLE = {
    "title": "SRP アタックロジック — ストリート別 BET 条件 (v6d: 精度 76.3%)",
    "headers": ["ストリート", "ポジション", "BET 条件", "なぜか"],
    "rows": [
        ["フロップ", "IP", "2P+ / TP+×dry・paired / UP×paired / UP×dry+draw / エア×dry・wet+strong draw / エア×paired+draw", "各条件が「BET しても EV がプラス」になる構造を持つ。エア×dry+gutshot は CHECK"],
        ["フロップ", "OOP", "なし（常にCHECK）", "IP のアクションを先に見る方が有利"],
        ["ターン SRP", "IP", "2P+ / TP++draw / エア+gutshot以上", "TP+×dry×no draw は CHECK（40%）。draw が必須"],
        ["ターン 3BP", "IP", "2P+ / TP+×dry / TP++gutshot / UP×paired×10+ / no_made_hand×dry×draw→BET ★。エア(ace/king/low/3rd)→全CHECK ★", "旧「エア×dry+draw → BET」は誤り。low_pair no_draw=22%、ace_high gutshot=22%"],
        ["ターン 4BP IP dry", "IP", "TP+/2P/third_pair/low_pair/no_made_hand→BET。king_high/ace_high→CHECK ★（24-30%）", "king_high no_draw=24%がCHECK、third_pair=64-100%がBET。逆直感"],
        ["ターン 4BP OOP dry", "OOP", "top_pair/trips→BET。overpair→CHECK ★（30%）。second/third_pair×gutshot→BET ★（88-92%）", "4BP OOP: overpair CHECK が最大の逆直感ルール"],
        ["ターン", "OOP", "SRP: 2P+×wet/dry / 3BP: TP+ + no_made_hand×draw / 4BP: top_pair/trips + second_pair×gutshot", "OOP 基本は CHECK、限定条件のみ BET"],
        ["リバー IP SRP", "delayed attack", "2P+ / TP+×dry・paired / UP×paired / エア（全 board）", "3回チェック後のエアはどのboardでも delayed bluff"],
        ["リバー SRP", "OOP", "TP+ / 2P+ → BET（UP・エアはCHECK）", "TP+ 80%/2P+ 55% BET、UP 42%/エア → CHECK"],
        ["リバー 3BP", "OOP", "UP/TP+/2P+ + エア×dry → BET（wet/paired エアは CHECK）", "3BP OOP: UP も BET — dry board エアも delayed bluff"],
        ["リバー 4BP", "OOP", "エア以外 BET（UP 70% が最強 BET カテゴリ）", "4BP OOP: UP が逆転して最強 BET カテゴリに"],
    ],
}

POT_TYPE_TURN_TABLE = {
    "title": "ポット種別 × ターン IP — 決定ロジック (GTO 実測値更新)",
    "headers": ["カテゴリ", "SRP", "3BP", "4BP dry/paired"],
    "rows": [
        ["2P+",            "BET",                              "BET",                               "BET (IP dry 61-78%)"],
        ["TP+",            "BET+draw / dry no_draw→CHECK",    "BET×dry/gutshot / wet・paired→CHECK", "BET（IP 77%/OOP top_pair 59%）"],
        ["third_pair",     "CHECK",                            "CHECK ★（GTO 29%）",                "BET ★（IP dry 64-100%/OOP×gutshot 88%）"],
        ["アンダーペア",   "CHECK（draw も×）",               "BET paired×10+ のみ",               "dry: no_made_hand/low_pair→BET ★"],
        ["エア（ace/king）", "BET（gutshot/FD 以上）",        "CHECK ★（ace_high 22%、low_pair 22%）", "CHECK ★（king_high 24%、ace_high 23-50%）"],
        ["no_made_hand",   "BET（gutshot 以上）",             "dry×gutshot/FD → BET ★（55-84%）",  "dry×no_draw/gutshot → BET ★（56-58%）"],
    ],
}

POT_TYPE_RIVER_TABLE = {
    "title": "ポット種別 × リバー IP — 決定ロジック（delayed attack）",
    "headers": ["カテゴリ", "SRP", "3BP", "4BP"],
    "rows": [
        ["2P+",          "BET",               "BET",              "ALLIN"],
        ["TP+",          "BET dry・paired",   "BET",              "BET/ALLIN"],
        ["アンダーペア", "BET paired のみ",   "CHECK",            "ALLIN paired のみ"],
        ["エア",         "BET（全 board）",   "BET wet・dry",     "CHECK"],
    ],
}

POT_TYPE_ATTACK_TABLE = {
    "title": "ポット種別 × フロップ IP — 決定ロジック",
    "headers": ["カテゴリ", "SRP IP", "3BP IP", "4BP IP"],
    "rows": [
        ["2P+",          "BET",               "BET",       "CHECK ← トラップ"],
        ["TP+",          "BET dry/paired",    "BET",       "BET dry/wet（paired は CHECK）"],
        ["アンダーペア", "BET paired のみ",   "CHECK",     "BET ← 逆転"],
        ["エア",         "CHECK",             "CHECK",     "CHECK"],
    ],
}

TIER_TABLE = {
    "title": "MATCHA カテゴリ 定義（復習）",
    "headers": ["カテゴリ", "ハンド例"],
    "rows": [
        ["エア", "役なし、Aハイ、Kハイ"],
        ["アンダーペア (UP)", "second pair / underpair（ペアボード以外の TP 未満ペア）"],
        ["TP+（トップペア以上）", "top pair / overpair"],
        ["2P+（ツーペア以上）", "two pair / trips / straight / flush / fullhouse / quads"],
    ],
}

DV_TABLE = {
    "title": "DV（Draw Value）定義（復習）",
    "headers": ["DV", "ドロー種別"],
    "rows": [
        ["4", "combo draw（FD + OESD）"],
        ["3", "FD（flush draw）または OESD（オープンエンドストレートドロー）"],
        ["1", "gutshot または BDFD（バックドアフラッシュドロー）"],
        ["0", "draw なし"],
    ],
}


def build_cards() -> list[dict]:
    cards = []

    # ─── Group 1: 全体ルール概要 ───
    g1 = "overview"
    g1l = "アタックルール / 全体概要"

    cards.append(card(
        1, g1, g1l,
        scenario="アタック = 自分から最初に賭けを開始する BET/C-BET の場面。",
        question="ストリート・ポジション別のアタック判断の全体構造は？",
        answer="フロップ IP: 5条件BET / ターン IP: 3条件BET / リバー IP: delayed attack条件あり / OOP: polarization",
        body=(
            "**アタックはディフェンス（MATCHA Score）とは独立した判断ロジック**\n\n"
            "Score 公式は「相手のベットに対する自ハンドの防御価値」を測る式。\n"
            "アタックの問い（自分がベットしたとき相手が降りるか）とは別の問いです。\n\n"
            "Score でアタック判断すると TP+×paired → fold 相当（本来は BET）、\n"
            "UP×paired → call 相当（本来は BET）と逆転が生じます。\n\n"
            "**アタックの構造**: ハンド × ボード × ポジション × ポット種別 → BET/CHECK を決定する。"
        ),
        bullets=[
            "ディフェンス: MATCHA Score 公式（相手ベットへの対応）",
            "アタック: 本章の決定ロジック（自分からベットする場面）",
            "両者は独立。混用すると逆判断になる",
        ],
        tables=[RULE_TABLE, TIER_TABLE],
    ))

    cards.append(card(
        2, g1, g1l,
        scenario="フロップ IP。2P+ の強いハンドを持っている。",
        question="ボードタイプ（dry/paired/wet）に関わらず何をすべきか？",
        answer="BET（2P+ はボード問わず BET）",
        body=(
            "**ルール①: IP 2P+ × ボード問わず → BET（SRP/3BP）**\n\n"
            "2P+(ツーペア以上)は最強ハンド群。IP からは全 board で BET。\n"
            "BET してもコールされる手は負けていない、フォールドされても EV プラス。\n\n"
            "**重要例外（3BP のスローレイ）**: セット × 3BP → CHECK / フラッシュ × 3BP → CHECK\n"
            "3BP は相手レンジが AK/QQ+ に絞られ SPR が浅いため、強い手は CHECK してトラップ。\n\n"
            "**OOP は 2P+ でも CHECK**: OOP フロップは 2P+ 以上でも原則 CHECK（スローレイ）。\n"
            "「OOP は全 CHECK」が鉄則。\n\n"
            "4BP は全く別の戦略（レンジベット 20% pot）→ TP+ も BET。旧「4BP 2P+→CHECK」は誤り。"
        ),
        bullets=[
            "2P+ = two pair / trips / straight / flush / fullhouse / quads",
            "SRP IP フロップ: dry/paired/wet すべてで BET",
            "3BP 例外: セット × 3BP → CHECK / フラッシュ × 3BP → CHECK（スローレイ）",
            "OOP は 2P+ でも全 CHECK（スローレイ）",
            "4BP はレンジベット 20% pot — TP+ → BET（2P+→CHECK の旧ルールは誤り）",
        ],
        tables=[TIER_TABLE],
    ))

    # ─── Group 2: フロップ IP 個別条件 ───
    g2 = "flop_ip"
    g2l = "アタックルール / フロップ IP"

    cards.append(card(
        3, g2, g2l,
        scenario="Cash 100bb、BTN open → BB call。フロップ。Hero = BTN (IP)。BB check。",
        question="Hero の カテゴリ = TP+、board = dry。BET か CHECK か？",
        answer="BET（TP+ は dry/paired board でバリューベットできる強度がある）",
        board="K♠ 7♦ 2♣",
        hand="A♥ K♦",
        body=(
            "**ルール②: TP+ × dry / paired → BET**\n\n"
            "トップペア以上は dry/paired ボードで価値ベットできる強度があります。\n"
            "wet ボードでは例外（ルール⑤）を除いて CHECK を選ぶことに注意。"
        ),
        bullets=[
            "TP+×dry → BET（dry board では相手のレンジに打ち勝てる強度がある）",
            "TP+×paired → BET（paired board でも TP+ はバリューを出せる）",
            "TP+×wet → ルール⑤(ドロー付きのみBET) でなければ CHECK",
        ],
        tables=[RULE_TABLE],
    ))

    cards.append(card(
        4, g2, g2l,
        scenario="Cash 100bb、BTN open → BB call。フロップ。Hero = BTN (IP)。BB check。",
        question="Hero の カテゴリ = アンダーペア (UP)、board = paired。BET か CHECK か？",
        answer="BET（paired board では相手レンジに 8x が少なく、UP が相対的に強化される）",
        board="8♥ 8♦ 3♣",
        hand="6♠ 6♥",
        body=(
            "**ルール③: アンダーペア × paired → BET**\n\n"
            "ペアボードでは相手のレンジに 8x が少なく、自分のポケット 6 が相対的に強化されます。\n"
            "dry/wet では UP は CHECK が原則ですが、paired では BET が有利。"
        ),
        bullets=[
            "UP×paired → BET（相手レンジに board ペアが少なく UP の相対的価値が上がる）",
            "UP×dry → CHECK（dry board では相手のトップペアに負けやすく BET 価値がない）",
            "UP×wet → CHECK（wet board では相手のドローやトップペアに対して UP は弱い）",
        ],
        tables=[TIER_TABLE],
    ))

    cards.append(card(
        5, g2, g2l,
        scenario="Cash 100bb、BTN open → BB call。フロップ。Hero = BTN (IP)。BB check。",
        question="Hero の カテゴリ = エア、gutshot あり (DV=1)、board = dry。BET か CHECK か？",
        answer="CHECK（エア×dry+gutshot は 45.3% BET のみ = CHECK 多数。strong draw のみ BET）",
        board="K♠ 7♦ 2♣",
        hand="J♠ T♥",
        body=(
            "**ルール⑤: エア×dry の BET 条件は strong draw（FD/OESD/combo）のみ**\n\n"
            "v6d 重要修正: エア×dry+gutshot は BET に見えるが、実測ではCHECK多数（45.3% BET）。\n"
            "gutshot では不十分 — FD/OESD/combo draw が必要。\n\n"
            "実測 BET 率（エア×dry フロップ IP SRP）:\n"
            "- gutshot: **45.3%** BET（CHECK が多数 54.7%）\n"
            "- OESD/FD: 90-100% BET（strong draw = 確実 BET）\n"
            "- no_draw: 23% BET（CHECK が多数）\n\n"
            "対比: エア×paired+gutshot は 67% BET（paired では gutshot でも OK）"
        ),
        bullets=[
            "エア × dry + gutshot → CHECK（45% BET のみ — strong draw と混同しやすい罠）",
            "エア × dry + FD/OESD/combo → BET（strong draw = セミブラフ確定）",
            "エア × paired + gutshot 以上 → BET（paired では gutshot でも相対価値上昇）",
            "エア × wet + FD/OESD → BET（strong draw があれば wet でも機能）",
            "UP × dry + gutshot → BET（UP は gutshot で補強されれば機能）",
        ],
        tables=[DV_TABLE],
    ))

    cards.append(card(
        6, g2, g2l,
        scenario="Cash 100bb、BTN open → BB call。フロップ。Hero = BTN (IP)。BB check。",
        question="Hero の カテゴリ = TP+、DV = 3 (FD あり)、board = wet。BET か CHECK か？",
        answer="BET（TP+ のバリュー＋FD のセミブラフが合わさり、wet board でも BET EV がプラスに転じる）",
        board="T♠ 9♥ 6♠",
        hand="A♠ T♦",
        body=(
            "**ルール⑤: FD/OESD + TP+ × wet → BET**\n\n"
            "TP+ × wet は通常 CHECK（TP+ × wet のルール②外）ですが、\n"
            "強いドロー（FD/OESD）が付いている場合はバリュー＋セミブラフとして BET。"
        ),
        bullets=[
            "TP+ × wet + DV=0 → CHECK（ドローなしでは wet board の TP+ は守勢に回る）",
            "TP+ × wet + DV≥3 → BET（FD/OESD がバリューとセミブラフを兼ねて BET EV がプラス）",
            "TP+ × wet + DV=1 (gut) → CHECK（gutshot では追加エクイティが不十分）",
        ],
        tables=[DV_TABLE, RULE_TABLE],
    ))

    cards.append(card(
        7, g2, g2l,
        scenario="Cash 100bb、BTN open → BB call。フロップ。Hero = BTN (IP)。BB check。",
        question="Hero = OOP（BB 側）。カテゴリ = TP+、board = dry。何をすべきか？",
        answer="CHECK（OOP フロップは常に CHECK）",
        board="K♠ 7♦ 2♣",
        hand="A♥ K♦",
        body=(
            "**OOP フロップ: 常に CHECK**\n\n"
            "フロップ OOP からの先制ベット（donk bet）は GTO では基本的に存在しません。\n"
            "TP+ の強いハンドでも OOP では CHECK して相手のアクションを待ちます。\n"
            "（Donk bet は例外的な上級戦略で本書のスコープ外）"
        ),
        bullets=[
            "OOP フロップ = 常に CHECK",
            "カテゴリ に関わらず適用",
            "donk bet は本書対象外",
        ],
        tables=[RULE_TABLE],
    ))

    # ─── Group 2b: フロップ 重要例外ルール ───
    g2b = "flop_key_exceptions"
    g2bl = "アタックルール / フロップ 重要例外ルール"

    cards.append(card(
        39, g2b, g2bl,
        scenario="Cash 100bb、BTN open → BB call（SRP）。フロップ。Hero = BTN（IP）。BB check。手: A♠ T♠（TP+ = top pair）。",
        question="board = T♠ 9♥ 6♠（wet）、draw なし（no_draw）の場合、BET か CHECK か？",
        answer="CHECK ★（TP × wet × no draw → CHECK。wet では draw なし TP は CR/draw に脆弱）",
        board="T♠ 9♥ 6♠",
        hand="A♠ T♦",
        body=(
            "**★ 最重要例外: TP × wet × no draw → CHECK**\n\n"
            "wet ボードでトップペアを持っていても、ドローがなければ CHECK が正解。\n\n"
            "理由:\n"
            "- 相手が FD/OESD/combo_draw で CR（チェックレイズ）してきたとき対応できない\n"
            "- BET → CR → コールは EV がマイナスになりやすい\n"
            "- ドローなし TP は showdown value を守る方が EV 高い\n\n"
            "比較（wet TP の判断）:\n"
            "- TP × wet × no draw → **CHECK** ★（draw なしは守勢）\n"
            "- TP × wet × GS → **CHECK**（GS も不十分）\n"
            "- TP × wet × OESD/FD → **BET**（strong draw でバリュー＋セミブラフ補完）\n\n"
            "dry ボードでは draw があってもなくても TP+ → BET が基本。"
        ),
        bullets=[
            "TP × wet × no draw → CHECK ★（wet TP のデフォルトは CHECK）",
            "TP × wet × OESD/FD/combo → BET（strong draw で BET EV プラス）",
            "TP × dry → BET（draw の有無に関わらず dry では BET）",
            "GS は 'no draw' 扱い — wet TP+GS は CHECK",
        ],
        tables=[DV_TABLE],
    ))

    cards.append(card(
        40, g2b, g2bl,
        scenario="Cash 100bb、SRP vs 3BP 比較。フロップ。Hero = IP（BTN）。BB check。手: Q♥ Q♦（OP = overpair）。board = T♠ 9♥ 6♠（wet）、draw なし。",
        question="SRP と 3BP で OP × wet × no draw の判断はどう変わるか？",
        answer="SRP → CHECK ★（34%）。3BP → BET（97%）。SPR の違いで逆転。",
        board="T♠ 9♥ 6♠",
        hand="Q♥ Q♦",
        body=(
            "**OP × wet × no draw: SRP と 3BP で逆転する**\n\n"
            "| ポット | GTO BET% | 推奨 | 理由 |\n"
            "|---|---|---|---|\n"
            "| SRP | 34% | **CHECK ★** | SPR≈10 — showdown 保護が優先 |\n"
            "| 3BP | 97% | **BET** | SPR≈5 — SPR が浅くバリューを即回収 |\n\n"
            "**SRP での理由**: SPR が深いため、wet board での OP は相手の CR やドロー完成に脆弱。\n"
            "showdown までポットを守る方が EV 高い（34% BET = CHECK 多数）。\n\n"
            "**3BP での理由**: SPR≈5 まで浅くなるため、相手の手に関わらず OP がバリューを持つ。\n"
            "97% BET = GTO はほぼ全て BET。スタックを早期に動かす。\n\n"
            "**TP vs OP の違い**: TP×wet×no_draw は SRP でも 3BP でも CHECK。\n"
            "OP×wet×no_draw は **SRP のみ CHECK、3BP は BET に転換**。"
        ),
        bullets=[
            "OP × wet × no draw × SRP → CHECK ★（34% BET — showdown 保護）",
            "OP × wet × no draw × 3BP → BET（97% BET — SPR 浅く即バリュー）",
            "TP × wet × no draw → CHECK（SRP/3BP 問わず）",
            "SPR が浅いほど OP の wet no_draw も BET に転換",
        ],
        tables=[DV_TABLE],
    ))

    cards.append(card(
        41, g2b, g2bl,
        scenario="Cash 100bb、3-bet Pot（3BP）。フロップ。Hero = IP（BTN）。BB check。手: 9♠ 9♦（セット、board = 9♥ 7♦ 2♣）。",
        question="3BP でセット（9-9-9）を持っている。IP。BET か CHECK か？",
        answer="CHECK（3BP セット → スローレイ。SPR≈5 で相手をコミットさせてから大きく取る）",
        board="9♥ 7♦ 2♣",
        hand="9♠ 9♦",
        body=(
            "**3BP セット → CHECK（スローレイ）★**\n\n"
            "SRP（SPR≈10）ではセット → BET が正解ですが、3BP（SPR≈5）では **CHECK** が有利。\n\n"
            "**スローレイの理由（3BP）**:\n"
            "- 相手の 3bet レンジは AK/QQ+ に絞られている（コンデンス）\n"
            "- BET → fold された場合、EV が低くなる\n"
            "- CHECK で相手のブラフ CBet を誘い、check-raise（CR）で大きく取る\n"
            "- SPR≈5 では次のターンでオールインに近い勝負ができる\n\n"
            "**フラッシュも同様**: フラッシュ × 3BP → CHECK（スローレイ）。\n\n"
            "比較:\n"
            "- セット × SRP → **BET**（SPR 深く、相手をコールさせてバリューを積む）\n"
            "- セット × 3BP → **CHECK**（SPR 浅く、スローレイで CR EV が高い）\n"
            "- セット × 4BP → **BET**（SPR 極浅く、スローレイの余裕なし）"
        ),
        bullets=[
            "セット × 3BP → CHECK（スローレイ: CR で大きく取る）★",
            "フラッシュ × 3BP → CHECK（スローレイ: 同様）★",
            "セット × SRP → BET（SPR 深い = コールさせてバリュー積む）",
            "セット × 4BP → BET（SPR 極浅い = スローレイ不要）",
            "「3BP = SPR 浅い = スローレイが有効」をセットで覚える",
        ],
        tables=[],
    ))

    # ─── Group 3: ターン IP ───
    g3 = "turn_ip"
    g3l = "アタックルール / ターン IP"

    cards.append(card(
        8, g3, g3l,
        scenario="Cash 100bb、SRP。ターン。Hero = IP。相手がチェック。",
        question="Hero の カテゴリ = 2P+、board = dry。BET か CHECK か？",
        answer="BET（2P+ はターンでも全 board でバリュー確定：BET してフォールドされても、コールされても EV+）",
        board="K♠ 7♦ 2♣ 9♥",
        hand="K♥ 9♠",
        body=(
            "**ターン IP ルール①: 2P+ → BET**\n\n"
            "ターンでも 2P+ は積極的にバリューベット。\n"
            "BET して相手がフォールドしても、コールしても EV がプラス。"
        ),
        bullets=[
            "2P+ × ターン IP → BET（board 問わず）",
            "ターン IP は 3 条件のみ BET、他はCHECK",
        ],
        tables=[RULE_TABLE],
    ))

    cards.append(card(
        9, g3, g3l,
        scenario="Cash 100bb、SRP。ターン。Hero = IP。相手がチェック。",
        question="Hero の カテゴリ = TP+、draw なし (DV=0)、board = dry。BET か CHECK か？",
        answer="CHECK（v6d 重要修正: TP+×dry+no draw は 40.3% BET = CHECK 多数。draw が必須）",
        board="K♠ 7♦ 2♣ 9♥",
        hand="A♥ K♦",
        body=(
            "**ターン IP ルール②: TP+×dry+draw → BET。no draw → CHECK（反直感）**\n\n"
            "v6d で修正された反直感ルール: dry ターンで TP+ でも draw なしは CHECK が GTO 多数。\n"
            "実測: TP+×dry×no_draw = **40.3% BET** = CHECK が多数（59.7%）。\n\n"
            "「dry board では TP+ が通る」は誤解。\n"
            "相手チェックの後でも、draw なし TP+ はスローダウンするのが GTO。\n\n"
            "理由: ターン到達後の dry board で両者チェックが続いた場合、\n"
            "相手の range も TP 相当以上に narrow されており、TP+ の優位が薄れる。"
        ),
        bullets=[
            "TP+×dry + DV=0 → CHECK（40% BET のみ — draw なしでは BET が逆効果）",
            "TP+×dry + gutshot/FD/OESD → BET（draw で補強された TP+ は BET が有効）",
            "TP+×wet + DV=0 → CHECK（wet × no draw では慎重）",
            "TP+×wet + DV≥3 → BET（draw 付き wet TP+ はバリュー + セミブラフ）",
        ],
        tables=[DV_TABLE, RULE_TABLE],
    ))

    cards.append(card(
        10, g3, g3l,
        scenario="Cash 100bb、SRP。ターン。Hero = IP。相手がチェック。",
        question="Hero の カテゴリ = TP+、FD あり (DV=3)。BET か CHECK か？",
        answer="BET（TP+ のバリュー＋FD のセミブラフが合わさり、ターンでも BET EV がプラスになる）",
        board="K♠ 8♠ 2♣ 5♠",
        hand="A♥ K♦",
        body=(
            "**ターン IP ルール②: TP+ + DV≥1 → BET**\n\n"
            "FD(DV=3)があることで TP+ もバリュー＋セミブラフ兼用で BET 可能。\n"
            "BET が優勢で、CHECK すると EV を逃す。"
        ),
        bullets=[
            "TP+ + FD → BET（バリュー＋ドロー完成の二重期待値で BET EV+）",
            "TP+ + gut (DV=1) → BET（フロップと異なり DV=1 でもOK：ターンは条件が緩和）",
            "フロップは DV≥3 が条件、ターンは DV≥1 に緩和",
        ],
        tables=[DV_TABLE],
    ))

    cards.append(card(
        11, g3, g3l,
        scenario="Cash 100bb、SRP。ターン。Hero = IP。相手がチェック。",
        question="Hero の カテゴリ = エア（役なし）、gutshot または FD あり。BET か CHECK か？",
        answer="BET（gutshot 以上のドローがあるエアは、ドロー完成期待値＋相手のフォールド誘発でセミブラフが成立する）",
        board="K♠ 8♠ 2♣ 5♠",
        hand="Q♠ J♥",
        body=(
            "**ターン IP ルール③: エア + gutshot 以上 → BET（dry board）**\n\n"
            "エアでも gutshot（76% BET）/ FD（69% BET）/ OESD（85% BET）があれば強いセミブラフとして BET。\n"
            "ドローが完成すれば強いハンドになり、フォールドさせれば EV+ になる。\n\n"
            "フロップとの違い: フロップではエア×dry+gutshot が 87% BET、\n"
            "ターンでも gutshot エア×dry は 76% BET — gutshot が BET 条件に入る。"
        ),
        bullets=[
            "エア + FD(DV=3) → BET（76-100%: ドロー完成価値＋フォールドエクイティで BET EV+）",
            "エア + gutshot(DV=1) → BET（76%: gutshot もターンでセミブラフとして有効）",
            "エア + DV=0 → CHECK（役なし＋ドローなしは BET する根拠がない）",
            "twocards_bdfd（2バックドアカード）のみ → CHECK（弱すぎる）",
        ],
        tables=[DV_TABLE, RULE_TABLE],
    ))

    cards.append(card(
        12, g3, g3l,
        scenario="Cash 100bb、SRP。ターン。Hero = IP。相手がチェック。",
        question="Hero の カテゴリ = アンダーペア (UP)、FD あり (DV=3)。BET か CHECK か？",
        answer="CHECK（UP はターンで BET できない：ドローがあっても UP のバリューが薄く、BET レンジに組み込めない）",
        board="K♠ 8♠ 2♣ 5♠",
        hand="7♥ 7♦",
        body=(
            "**重要な例外: アンダーペア × ターンは draw があっても CHECK**\n\n"
            "UP はターンでは draw 付きでも BET しません。\n"
            "UP のハンドはバリューとして弱く（相手のコールレンジに負けやすい）、\n"
            "ベットレンジに組み込むと BET/CHECK のレンジバランスが崩れます。"
        ),
        bullets=[
            "UP + DV=3 → CHECK（ドローがあっても UP のバリューの弱さが優先されて CHECK）← フロップと異なる注意点",
            "フロップ IP: UP × paired → BET（ルール③）",
            "ターン IP: UP は draw があっても CHECK",
        ],
        tables=[RULE_TABLE],
    ))

    # ─── Group 4: ターン OOP ───
    g4 = "turn_oop"
    g4l = "アタックルール / ターン OOP"

    cards.append(card(
        13, g4, g4l,
        scenario="Cash 100bb、SRP。ターン。Hero = OOP（BB）。",
        question="Hero の カテゴリ = 2P+、board = wet。BET か CHECK か？",
        answer="BET（2P+ × wet board では OOP でもナッツをポーラライズして先制ベットする理由がある）",
        board="T♠ 9♥ 6♠ 3♠",
        hand="T♥ 9♦",
        body=(
            "**ターン OOP ルール: 2P+ × wet のみ BET**\n\n"
            "ターン OOP からの先制ベットは基本的に CHECK ですが、\n"
            "2P+ × wet の場合のみ lead/donk が GTO 推奨。\n"
            "強いナッツを湿ったボードでポーラライズして BET します。"
        ),
        bullets=[
            "ターン OOP デフォルト = CHECK",
            "2P+ × wet → BET（wet board では 2P+ がナッツとしてポーラライズ BET で EV を最大化）",
            "2P+ × dry / paired → CHECK（dry/paired では IP のアクションを待った方が有利）",
            "TP+ × wet → CHECK（TP+ では OOP からのポーラライズが成立しない）",
        ],
        tables=[RULE_TABLE],
    ))

    cards.append(card(
        14, g4, g4l,
        scenario="Cash 100bb、SRP。ターン。Hero = OOP（BB）。",
        question="Hero の カテゴリ = 2P+、board = dry。BET か CHECK か？",
        answer="CHECK（dry board では OOP からの先制ベットは IP のポジション優位に対して損になる）",
        board="K♠ 7♦ 2♣ 4♥",
        hand="K♥ 7♠",
        body=(
            "**SRP ターン OOP: 2P+ × wet のみ BET、dry はCHECK**\n\n"
            "dry ボードでは 2P+ でも OOP から先制ベットしません。\n"
            "IP（相手）がアクションを取るのを待ち、check-raise などで対応します。"
        ),
        bullets=[
            "SRP ターン OOP 2P+ × dry → CHECK（dry では IP のポジション優位が大きく、先制ベットは損）",
            "SRP ターン OOP 2P+ × wet → BET（wet では 2P+ がナッツとしてポーラライズ BET できる）",
            "dry ボードでは IP にアクションを委ねる",
        ],
        tables=[RULE_TABLE],
    ))

    cards.append(card(
        38, g4, g4l,
        scenario="Cash 100bb、3BP または 4BP。ターン。Hero = OOP（BB）。フロップ双方チェック済み。",
        question="3BP / 4BP ターン OOP のルールは SRP OOP と何が違うか？",
        answer="3BP: TP+ → BET、2P+×wet → BET。4BP: TP+ → BET のみ。どちらも UP/エア → CHECK。",
        body=(
            "**3BP/4BP ターン OOP アタックルール**\n\n"
            "| pot_type | BET 条件 | CHECK |\n"
            "|---|---|---|\n"
            "| SRP | 2P+×wet | TP+/UP/エア（dry/paired）|\n"
            "| 3BP | TP+ (dry/wet) / 2P+×wet | UP / エア / 2P+×dry |\n"
            "| 4BP | TP+ のみ | UP / 2P+ / エア |\n\n"
            "**3BP OOP ターン**: TP+ は dry（81%）/ wet（69%）双方で BET。\n"
            "2P+×dry は 45% BET のみなので CHECK がデフォルト。\n\n"
            "**4BP OOP ターン**: TP+ のみが BET（dry 57%/wet 69%）。\n"
            "UP×dry は 52%（ほぼ五分五分）なので CHECK がデフォルト。"
        ),
        bullets=[
            "3BP OOP ターン: TP+ → BET（dry 81%/wet 69%）、2P+×wet → BET",
            "4BP OOP ターン: TP+ → BET のみ（UP は五分五分 52% → CHECK デフォルト）",
            "SRP OOP ターン: 2P+×wet のみ → BET",
            "共通: UP/エア → CHECK（pot_type によらずほぼ全 CHECK）",
        ],
        tables=[RULE_TABLE],
    ))

    # ─── Group 5: リバー IP ───
    g5 = "river_ip"
    g5l = "アタックルール / リバー IP"

    cards.append(card(
        15, g5, g5l,
        scenario="Cash 100bb、SRP。リバー。Hero = IP。フロップ・ターン双方チェック済み。OOP がリバーチェック。",
        question="「delayed attack（双方パッシブ後のリバー）」で 2P+ の場合、BET か CHECK か？",
        answer="BET（2P+ は delayed attack リバーで最強ハンド：相手の showdown 志向ハンドからバリューを取れる）",
        board="K♠ 7♦ 2♣ 9♥ A♠",
        hand="K♥ 9♠",
        body=(
            "**SRP リバー IP — delayed attack（フロップ+ターン双方チェック後）**\n\n"
            "フロップと ターンで両者がチェックし合い、リバーで OOP がチェックした場面。\n"
            "この「delayed attack」局面では、一般的なリバー IP ルールと異なり BET 条件があります。\n\n"
            "| カテゴリ | board | 推奨 |\n"
            "|---|---|---|\n"
            "| 2P+ | 全 board | **BET** |\n"
            "| TP+ | dry・paired | BET |\n"
            "| UP | paired のみ | BET |\n"
            "| エア | wet・paired | BET（ブラフ） |\n\n"
            "**「delayed attack」の意味**: 双方パッシブ = お互いが弱いレンジ。ドローがミスしたエアもブラフとして機能する局面。"
        ),
        bullets=[
            "delayed attack = フロップ・ターン双方チェック後のリバー",
            "2P+ → BET 全 board（双方パッシブ後は 2P+ が最強ハンドとしてバリューを取れる）",
            "TP+ → BET dry/paired（wet は相手のフラッシュに負けるリスクがある）",
            "エア × wet/paired → ブラフBET（ドローミスのハンドもこの局面でブラフ機能あり）",
        ],
        tables=[RULE_TABLE],
    ))

    cards.append(card(
        19, g5, g5l,
        scenario="Cash 100bb、SRP。リバー delayed attack。Hero = IP。UP（アンダーペア）保有。",
        question="UP で board = paired の場合は BET か CHECK か？",
        answer="BET（paired board では相手レンジに 7x が多く、UP がブラフとして相手の弱手を押し出せる）",
        board="K♠ 7♦ 7♣ 2♥ A♠",
        hand="9♥ 9♦",
        body=(
            "**SRP リバー IP delayed attack — UP × paired → BET（例外）**\n\n"
            "通常 UP はリバーでは CHECK ですが、delayed attack × paired board では BET が正解。\n\n"
            "理由: paired board では相手のレンジに 7x が多く、\n"
            "UP の 9-9 がブラフとして相手の弱手を押し出せるため。\n\n"
            "**覚え方**: delayed attack リバー UP の判断 = paired board かどうか\n"
            "- paired → BET（相手の弱手を押し出せるブラフ機能あり）\n"
            "- dry → CHECK（dry では相手の強いハンドに BET が通らない）\n"
            "- wet → CHECK（wet では相手のドロー完成ハンドに負ける）"
        ),
        bullets=[
            "リバー delayed attack: UP × paired → BET（相手レンジが 7x 等の弱手中心で押し出せる）",
            "エア × wet → BET（ドローミスのブラフが wet board では有効）",
            "エア × paired → BET（paired board ではエアのブラフが通りやすい）",
            "dry board → UP も エア も CHECK（dry では相手の強いレンジに BET が通らない）",
        ],
        tables=[POT_TYPE_RIVER_TABLE],
    ))

    # ─── Group 6: リバー OOP polarization ───
    g6 = "river_oop"
    g6l = "アタックルール / リバー OOP（polarization）"

    cards.append(card(
        16, g6, g6l,
        scenario="Cash 100bb、SRP。リバー。Hero = OOP（BB）。フロップ・ターン双方チェック。",
        question="SRP リバー OOP の正しいルールは何か？（旧: 「UP のみ CHECK」は誤り）",
        answer="TP+/2P+ → BET。UP/エアは CHECK（UP 42%/エア 44% BET — 多数は CHECK）",
        body=(
            "**SRP リバー OOP — 実測ベースの正確なルール**\n\n"
            "GTO Wizard 335 spots 実測データ（dry board）による BET 率:\n\n"
            "| カテゴリ | GTO BET 率 | 推奨 |\n"
            "|---|---|---|\n"
            "| TP+ | **80%** | BET |\n"
            "| 2P+ | 55% | BET |\n"
            "| UP | 42% | CHECK |\n"
            "| エア | 44% | CHECK |\n\n"
            "**旧ルール（誤）**: 「UP のみ CHECK、エア/TP+/2P+ は BET」\n"
            "→ エアが実際 44% BET（56% CHECK）で多数は CHECK のため誤り。\n\n"
            "**新ルール**: TP+/2P+ → BET（明確な多数）。UP・エア → CHECK（多数が CHECK）"
        ),
        bullets=[
            "TP+ → BET（80%: GTO で最も明確な BET カテゴリ）",
            "2P+ → BET（55% BET: 多数は BET）",
            "UP → CHECK（42% BET: 多数は CHECK）",
            "エア → CHECK（44% BET: 多数は CHECK）← 旧ルールの「エア BET」は誤り",
        ],
        tables=[
            {
                "title": "SRP リバー OOP アクション決定（実測 335 spots）",
                "headers": ["カテゴリ", "GTO BET%", "推奨"],
                "rows": [
                    ["2P+", "55%", "BET"],
                    ["TP+（トップペア以上）", "80%", "BET"],
                    ["アンダーペア (UP)", "42%", "CHECK"],
                    ["エア", "44%", "CHECK"],
                ],
            },
            RULE_TABLE,
        ],
    ))

    cards.append(card(
        17, g6, g6l,
        scenario="Cash 100bb、SRP。リバー。Hero = OOP（BB）。",
        question="Hero = アンダーペア（ポケット 6s、ボード K-9-4-2-Q）。BET か CHECK か？",
        answer="CHECK（UP は 42% BET のみ — 多数は CHECK。バリューとしても弱く showdown が最善）",
        board="K♠ 9♦ 4♣ 2♥ Q♦",
        hand="6♠ 6♥",
        body=(
            "**SRP リバー OOP: UP → CHECK**\n\n"
            "6-6 はアンダーペア（UP）。SRP リバーでは CHECK が多数です。\n"
            "GTO では UP は 42% しか BET せず、58% が CHECK。\n"
            "「バリューとして弱く（K 持ちにコールされる）、ブラフとしても中途半端」\n"
            "のため showdown が最善。"
        ),
        bullets=[
            "SRP OOP リバー UP → CHECK（GTO 58% CHECK が多数）",
            "旧: 「UP のみ CHECK」は概念として正しかった",
            "新追加: エアも CHECK（44% BET = 56% CHECK）",
        ],
        tables=[RULE_TABLE],
    ))

    cards.append(card(
        18, g6, g6l,
        scenario="Cash 100bb、SRP。リバー。Hero = OOP（BB）。",
        question="Hero = エア（Q ハイ、ドローミス）、board = dry。BET か CHECK か？",
        answer="CHECK（SRP OOP リバー エア×dry は CHECK。SRP OOP は TP+/2P+ のみ BET）",
        board="K♠ 9♠ 4♣ 2♥ Q♦",
        hand="J♠ T♠",
        body=(
            "**SRP リバー OOP: エア → CHECK（TP+/2P+ のみ BET）**\n\n"
            "SRP OOP リバーは「TP+/2P+ → BET、UP/エア → CHECK」。\n"
            "OOP のエアは delayed bluff として機能しない（相手 IP が range advantage を持つ）。\n\n"
            "注意: IP リバー SRP の場合は逆 — エア（全 board）→ BET（delayed bluff として機能）。\n"
            "OOP と IP でエアの扱いが異なる重要な非対称性。"
        ),
        bullets=[
            "SRP OOP リバー エア → CHECK（UP も同様）",
            "SRP IP リバー エア → BET（3 回チェック後の delayed bluff、全 board）",
            "OOP と IP の非対称性: IP はポジションで delayed bluff が通りやすい",
            "3BP OOP リバー エア×dry → BET（別ルール: dry board のみ）",
        ],
        tables=[RULE_TABLE],
    ))

    # ─── Group 8: 3BP フロップ IP ───
    g8 = "3bp_flop_ip"
    g8l = "アタックルール / 3BP フロップ IP"

    cards.append(card(
        21, g8, g8l,
        scenario="Cash 100bb、3-bet Pot (3BP)。フロップ。Hero = IP（BTN）。OOP（BB）がチェック。SPR ≈ 5。",
        question="3BP での IP フロップアタックルールは SRP と何が違うか？",
        answer="TP+ 以上でBET（シンプル化）。エア・アンダーペアのブラフは機能しにくい。",
        body=(
            "**3BP フロップ IP アタックルール**\n\n"
            "相手の 3bet レンジはコンデンスされており、エアやアンダーペアのブラフに対して\n"
            "相手はポット odds で簡単にコールできます。\n\n"
            "| カテゴリ | 推奨 | 理由 |\n"
            "|---|---|---|\n"
            "| 2P+ | BET | 最強ハンド：バリューを取れる |\n"
            "| TP+ | BET | 3BP SPR ≈ 5 でも TP+ はバリューとして成立 |\n"
            "| アンダーペア | CHECK | 相手のコンデンスレンジに BET が通らない |\n"
            "| エア | CHECK | ブラフがポット odds でコールされてしまう |\n\n"
            "**判断フロー**: TP+ または 2P+ → BET。それ以外 → CHECK。\n\n"
            "SRP との違い: SRP では UP×paired や ドロー系でも BET できたが、\n"
            "3BP ではそれらも CHECK になる。"
        ),
        bullets=[
            "3BP ルール: TP+ 以上 → BET（ボード問わず）",
            "エア・UP はドロー付きでも CHECK（3BP では相手のコンデンスレンジにブラフが通らない）",
            "SRP より BET 条件がシンプル（2 条件のみ）",
        ],
        tables=[POT_TYPE_ATTACK_TABLE],
    ))

    cards.append(card(
        22, g8, g8l,
        scenario="Cash 100bb、3BP。BTN vs BB。フロップ Ks7d2c（dry）。Hero = BTN（IP）。BB がチェック。手: 9s9d（アンダーペア）。",
        question="BTN のアクションは BET か CHECK か？",
        answer="CHECK（3BP の相手は KK/AA/AK の強いレンジ：UP のブラフはコールされてしまうリスクが高い）",
        board="Ks7d2c",
        hand="9s9d",
        body=(
            "**3BP × アンダーペア = CHECK**\n\n"
            "SRP では UP×paired → BET のルールがありましたが、3BP には適用されません。\n\n"
            "3BP の相手（BB）は KK/AA/AK の強いレンジで 3bet しており、\n"
            "K-high ボードでは相手が続けてバリューベットする可能性が高いです。\n"
            "UP でブラフすることはリスクが高く、GTO は CHECK を推奨。\n\n"
            "正解: CHECK（SRP の UP×paired ルールを 3BP に適用しないこと）"
        ),
        bullets=[
            "3BP: UP → CHECK（paired でも：相手のコンデンスレンジに UP ブラフは通らない）",
            "SRP: UP × paired → BET（SRP では相手レンジが広く UP のブラフが通りやすい）",
            "混同注意: SRP ルールを 3BP に使わない",
        ],
        tables=[POT_TYPE_ATTACK_TABLE],
    ))

    # ─── Group 9: 4BP フロップ — レンジベット戦略 ───
    g9 = "4bp_flop"
    g9l = "アタックルール / 4BP フロップ（レンジベット戦略）"

    cards.append(card(
        23, g9, g9l,
        scenario="Cash 100bb、4-bet Pot (4BP)。BTN vs BB。フロップ。SPR ≈ 2（pot ≈ 56BB、stack ≈ 44BB）。",
        question="4BP フロップのアタック戦略は SRP/3BP とどう違うか？",
        answer="4BP は 20% pot のレンジベット戦略。TP+ は BET(82-100%)。旧「2P+→CHECK」は誤り。",
        body=(
            "**4BP フロップ — レンジベット戦略（GTO Wizard データ確認済み）**\n\n"
            "GTO Wizard 24 boards プローブ結果（pot=56BB、stack=44BB）:\n\n"
            "| カテゴリ | GTO BET% | アクション | ベットサイズ |\n"
            "|---|---|---|---|\n"
            "| TP+ (any board) | 82–100% | **BET** | 20% pot (≈11BB) |\n"
            "| 2nd/3rdペア (IP) | ≈50% | BET（range-bet） | 20% pot |\n"
            "| Ultra-dry 低ボード (742/752/853) | 35–41% | **AI** | オールイン (127% pot) |\n\n"
            "**全体**: CHECK ≈ 51% / BET ≈ 49%（ほぼ 50-50 のレンジ分散）\n\n"
            "**旧「逆転ロジック（2P+→CHECK）」との違い**:\n"
            "旧仮説は「2P+はトラップ、UP はプレッシャーベット」と教えていたが、\n"
            "GTO は 2P+ でも BET。20% pot の小さなサイズで全レンジを分散させる。\n\n"
            "3BP の「セット/フラッシュ → スローレイ」も 4BP では不要（SPR 低すぎ）。"
        ),
        bullets=[
            "4BP フロップ = 20% pot レンジベット（全体 49% BET）",
            "TP+ → BET 82-100%（dry/wet/paired 問わず）",
            "Ultra-dry 低ボード（742/752/853）→ AI（20% pot でなく直接 all-in）",
            "旧「4BP 2P+→CHECK トラップ / UP→BET プレッシャー」は GTO と一致せず廃止",
            "SRP/3BP とはベットサイズ（20% pot）も戦略も別物",
        ],
        tables=[POT_TYPE_ATTACK_TABLE],
    ))

    cards.append(card(
        24, g9, g9l,
        scenario="Cash 100bb、4BP。BTN vs BB。フロップ As9d4c（dry）。Hero = BTN（IP）。BB がチェック。手: AhKh（TP top pair）。",
        question="BTN のアクションは BET か CHECK か？ベットサイズは？",
        answer="BET 20% pot（≈11BB）。4BP TP+ はポジション・ボード問わず BET(82-100%)。",
        board="As9d4c",
        hand="AhKh",
        body=(
            "**4BP × TP+ = BET 20% pot**\n\n"
            "TP+(top pair KK with A kicker)は 4BP でも即 BET。\n"
            "ベットサイズは 20% pot = ≈11BB（pot 56BB の 20%）。\n\n"
            "**なぜ 20% pot?**\n"
            "SPR≈2 で相手が次のターンでほぼ all-in になる。\n"
            "20% pot という小さなベットで全レンジをフォール/コールに振り分け、\n"
            "ポット比 EV を最大化する（= レンジベット）。\n\n"
            "**GTO BET 率**: TP+ は 82–100% BET（GTO Wizard 実測）。\n"
            "dry/wet/paired のボードタイプによらず、4BP では TP+ は BET が基本。"
        ),
        bullets=[
            "4BP TP+ → BET 20% pot（82-100% BET、GTO Wizard 確認）",
            "ベットサイズ 20% pot = ≈11BB into 56BB pot",
            "dry/wet/paired ボード問わず BET",
            "IP/OOP 問わず TP+ → BET（SRP の OOP=CHECK ルールは 4BP では緩和）",
        ],
        tables=[POT_TYPE_ATTACK_TABLE],
    ))

    cards.append(card(
        25, g9, g9l,
        scenario="Cash 100bb、4BP。BTN vs BB。フロップ 7s4d2c（ultra-dry 低ボード）。Hero = BTN（IP）。BB がチェック。",
        question="ultra-dry 低ボード（742 型）の 4BP フロップは通常と何が違う？",
        answer="AI（オールイン直行）。20% pot BET は機能しない。これだけ別扱い。",
        board="7s4d2c",
        hand="AhKh",
        body=(
            "**4BP × Ultra-dry 低ボード = AI**\n\n"
            "4s4d2c / 7s4d2c / 8s5d3c 型（極端に dry で low ランク）のボードでは、\n"
            "GTO は 20% pot でなく **AI（127% pot、全額オールイン）**を選択。\n\n"
            "GTO BET 率（このボードタイプ）:\n"
            "- AI: 35–41%\n"
            "- BET 20% pot: ほぼ 0%\n"
            "- CHECK: 59–65%\n\n"
            "**理由**: ultra-dry 低ボードでは相手レンジが disconnected で、\n"
            "小さなベット（20% pot）への対応が変わる。AI で一気に決着をつける構造。\n\n"
            "通常の 4BP（K72, T96, A54 等）は 20% pot が機能するが、\n"
            "742/752/853 のような極端な低 dry だけは AI 一本。"
        ),
        bullets=[
            "Ultra-dry 低ボード（742/752/853 型）→ AI（20% pot は使わない）",
            "通常の 4BP ボード → 20% pot レンジベット",
            "この 2 ボードタイプの区別が 4BP フロップで最重要",
        ],
        tables=[POT_TYPE_ATTACK_TABLE],
    ))

    # ─── Group 10: 3BP ターン IP ───
    g10 = "3bp_turn_ip"
    g10l = "アタックルール / 3BP ターン IP"

    cards.append(card(
        28, g10, g10l,
        scenario="Cash 100bb、3BP。BTN vs BB。フロップ・ターン双方チェック。OOP がチェック。Hero = BTN (IP)。",
        question="3BP ターン IP のアタックルールは？TP+×wet/paired の扱いは SRP と同じか？",
        answer="2P+ → BET 全。TP+×dry → BET（wet/paired は CHECK）。UP×paired → BET。エア → CHECK。",
        body=(
            "**3BP ターン IP アタックルール (v5: 精度 72%)**\n\n"
            "| カテゴリ | board | 推奨 | 理由 |\n"
            "|---|---|---|---|\n"
            "| 2P+ | 全 board | **BET** | 最強ハンド：3BP でも変わらずバリューを取る |\n"
            "| TP+ | **dry のみ** | BET | TP+×dry 85% BET。TP+×wet 46% / TP+×paired 25% → CHECK |\n"
            "| TP+ | wet/paired | **CHECK** | wet/paired では相手の強いレンジが恐く CHECK が多数 |\n"
            "| アンダーペア | paired のみ | BET | paired board で相手レンジの弱さを突く |\n"
            "| エア | 全 board | CHECK | 3BP では相手がコールしやすくブラフが通らない |\n\n"
            "**SRP ターン IP との違い**:\n"
            "- SRP では UP は draw あっても CHECK（3BP では UP×paired → BET）\n"
            "- 3BP では TP+×wet/paired → CHECK（SRP では TP+×wet+draw → BET）\n"
            "- エアは DV=3 があっても CHECK（3BP では相手のコンデンスレンジにブラフが通らない）"
        ),
        bullets=[
            "3BP ターン: 2P+ / TP+×dry → BET",
            "TP+×wet/paired → CHECK（wet 46%/paired 25% BET — 多数 CHECK）← SRP と異なる",
            "UP × paired → BET（SRP フロップの UP×paired ルールが 3BP ターンにも適用）",
            "エア → CHECK（3BP ではブラフ機能せず：相手がポット odds でコールできる）",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    cards.append(card(
        29, g10, g10l,
        scenario="Cash 100bb、3BP。フロップ Ks7d2c → ターン 7h（ペアカード）。Hero = BTN (IP)。BB がチェック。手: 9s9d（UP）。",
        question="ターンで board がペア（Ks7d2c → 7h）になった場合、UP で BET か CHECK か？",
        answer="BET（paired board で相手が 7x を絞れる：IP の UP は相手の弱いレンジ JJ/TT に対しバリューが出る）",
        board="Ks7d2c7h",
        hand="9s9d",
        body=(
            "**3BP ターン UP × paired = BET**\n\n"
            "ターンカードがボードをペア（7c → 7h でペアボード）にした場合、\n"
            "3BP での UP は BET が正解。\n\n"
            "理由: ペアボードでは相手が 7x を持っている可能性に対して、\n"
            "IP の UP（9-9）は相手の弱いレンジ（JJ/TT 等）に対してバリューが出る。\n"
            "かつ、3BP SPR ≈ 5 の中では UP のブラフ成功率も上昇。\n\n"
            "**dry・wet ターンでは CHECK**（dry/wet では相手レンジに UP が押し負けやすい）"
        ),
        bullets=[
            "3BP ターン UP × paired → BET（paired board で UP の相対的価値が上昇する）",
            "3BP ターン UP × dry → CHECK（dry では相手の強いハンドに UP が押し負ける）",
            "3BP ターン UP × wet → CHECK（wet では相手のドローや強ハンドが多く UP が不利）",
            "SRP ターン UP = draw あっても常に CHECK（3BP ターン paired との違いに注意）",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    # ─── Group 10 追加: 3BP ターン IP エア → CHECK ★ ───
    cards.append(card(
        42, g10, g10l,
        scenario="Cash 100bb、3BP（SPR ≈ 5）。ターン。Hero = BTN (IP)。BB がチェック。board = A♥ 7♦ 2♣ 5♠（dry）。手: K♦ 4♣（low pair なし、king_high）。gutshot あり。",
        question="3BP ターン IP、king_high × dry × gutshot でBET か CHECK か？",
        answer="CHECK ★（3BP IP ターン エア全 CHECK。king_high gutshot dry = 27.9%、ace_high gutshot = 22.1%。no_made_hand+draw のみBET）",
        board="Ah7d2c5s",
        hand="Kd4c",
        body=(
            "**3BP ターン IP エア = 全 CHECK ★（no_made_hand+draw 以外）**\n\n"
            "旧ルール「エア × dry × draw → BET」は GTO 実測で否定されました。\n\n"
            "| エアの種類 | dv | GTO BET% | 正解 |\n"
            "|---|---|---|---|\n"
            "| king_high | no_draw | 13.5% | **CHECK ★** |\n"
            "| king_high | gutshot | 27.9% | **CHECK ★** |\n"
            "| ace_high | no_draw | 22.0% | **CHECK ★** |\n"
            "| ace_high | gutshot | 22.1% | **CHECK ★** |\n"
            "| low_pair | no_draw | 22.4% | **CHECK ★**（L100=13.76 BB/100 の最大損失）|\n"
            "| low_pair | gutshot | 0.2% | **CHECK ★** |\n"
            "| **no_made_hand** | **gutshot** | **55.0%** | **BET ★** |\n"
            "| **no_made_hand** | **FD** | **51.8%** | **BET ★** |\n\n"
            "**核心**: no_made_hand（純ブラフ）だけが draw でセミブラフとして機能。\n"
            "king/ace-high はブロッカー価値があるが CHECK が EV 高い（ショーダウンを守る）。"
        ),
        bullets=[
            "3BP IP ターン エア → **全 CHECK ★**（no_made_hand×draw 以外は draw があっても CHECK）",
            "low_pair × dry × no_draw → CHECK（旧 BET は誤り、L100 改善=13.76 BB/100 最大）",
            "ace_high × gutshot → CHECK（22.1% BET — CHECK が GTO）",
            "例外: no_made_hand × gutshot/FD → BET（55-84%）← pure bluff のみ",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    # ─── Group 11: 4BP ターン IP ───
    g11 = "4bp_turn_ip"
    g11l = "アタックルール / 4BP ターン IP (逆転継続)"

    cards.append(card(
        30, g11, g11l,
        scenario="Cash 100bb、4BP。BTN vs BB。フロップ・ターン双方チェック。OOP がターンチェック。Hero = BTN (IP)。SPR ≈ 1.5。",
        question="4BP ターン IP の最大の特徴は何か？",
        answer="アンダーペアも BET 全（フロップの逆転パターン継続）。ターンでは 2P+ の CHECK が解除されて BET に転じる。",
        body=(
            "**4BP ターン IP — フロップ逆転パターン継続**\n\n"
            "4BP フロップでは「2P+ → CHECK（トラップ）/ UP → BET（逆転）」でしたが、\n"
            "ターンでは逆転パターンが部分的に緩和されつつ、UP の BET は継続します。\n\n"
            "| カテゴリ | 推奨 | 理由 |\n"
            "|---|---|---|\n"
            "| 2P+ | **BET 全** | ターンでは SPR ≈ 1.5 まで下がりオールイン圧力が強まる：トラップより即時バリューが有効 |\n"
            "| TP+ | **BET 全** | SPR 浅い × TP+ = オールインに向けた強いバリューポジション |\n"
            "| アンダーペア | **BET 全（逆転継続）** | SPR 浅さがターンでも UP の攻撃性を維持する |\n"
            "| エア | CHECK | |\n\n"
            "**重要**: 4BP ターンでは 2P+ も BET（フロップ CHECK からの逆転）。\n"
            "SPR が ≈1.5 まで下がり、オールイン圧力が強まるため戦略が変化。"
        ),
        bullets=[
            "4BP ターン: 2P+ / TP+ / UP 全 → BET（エアのみ CHECK）",
            "フロップ: 2P+ → CHECK（トラップ）",
            "ターン: 2P+ → BET（SPR ≈ 1.5 でトラップより即時バリューが有効）",
            "UP の BET はフロップ・ターン共通（SPR 浅さ由来）",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    cards.append(card(
        31, g11, g11l,
        scenario="Cash 100bb、4BP。フロップ As9d4c → ターン 2h。Hero = BTN (IP)。BB がチェック。手: 7h7d（UP）。",
        question="4BP ターン、UP（77）で BET か CHECK か？",
        answer="BET（4BP ターン UP は board type 問わず BET：SPR ≈ 1.5 の浅さが UP のオールイン圧力を正当化する）",
        board="As9d4c2h",
        hand="7h7d",
        body=(
            "**4BP ターン UP = BET（ブランクターンでも）**\n\n"
            "フロップ(As9d4c)で BET した UP の 7-7 が、ターン 2h（ブランク）でも BET。\n"
            "SPR ≈ 1.5 の極浅い局面では、UP のプレッシャーベットが有効。\n\n"
            "比較:\n"
            "- SRP ターン UP: CHECK（draw あっても UP の価値不足でベットレンジに入れられない）\n"
            "- 3BP ターン UP×dry: CHECK（SPR ≈ 5 では dry board で UP のブラフ圧力が弱い）\n"
            "- **4BP ターン UP: BET 全（SPR ≈ 1.5 で UP のオールイン圧力が最大化する）**\n\n"
            "4BP ではスタックが浅く、UP のブラフが相手に大きなオールイン圧力をかける。"
        ),
        bullets=[
            "4BP ターン UP → BET（board type 問わず：SPR 浅さが UP の攻撃を正当化）",
            "SRP ターン UP → CHECK（SPR 深い × UP では攻撃できない：対比として覚える）",
            "SPR が浅いほど UP の攻撃性が増す",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    # ─── Group 11b: 4BP ターン IP dry エア逆転 ───
    g11b = "4bp_turn_ip_air_reversal"
    g11bl = "アタックルール / 4BP ターン IP dry エア逆転"

    cards.append(card(
        43, g11b, g11bl,
        scenario="Cash 100bb、4BP（SPR ≈ 1.5）。ターン。Hero = BTN (IP)。BB がチェック。board = J♥ 7♦ 2♣ 5♠（dry）。",
        question="4BP ターン IP dry。以下の各ハンドはBETかCHECKか？①K♦4♣（king_high）、②7c3h（third_pair=ボトムペア）、③5c4c（no_made_hand gutshot）",
        answer="①CHECK ★（24.4%）②BET ★（64-100%）③BET ★（55.5%）。king/ace_high→CHECK、third_pair/no_made_hand→BET。逆直感に注意",
        board="Jh7d2c5s",
        body=(
            "**4BP ターン IP dry エア逆転（L100 最大改善）**\n\n"
            "| ハンドカテゴリ | board | GTO BET% | 正解 | 理由 |\n"
            "|---|---|---|---|---|\n"
            "| king_high | dry no_draw | **24.4%** | **CHECK ★** | K-high はショーダウン価値があり BET 不要 |\n"
            "| ace_high | dry no_draw | **49.9%** | CHECK/境界 | A-high も CHECK 傾向 |\n"
            "| ace_high | dry gutshot | **23.0%** | **CHECK ★** | gutshot でも A-high → CHECK |\n"
            "| **third_pair** | dry no_draw | **64.0%** | **BET ★** | ショーダウン価値なし → ブラフ最適 |\n"
            "| **third_pair** | dry gutshot | **99.9%** | **BET ★** | ほぼ 100% BET |\n"
            "| **no_made_hand** | dry no_draw | **57.8%** | **BET ★** | 純ブラフ × dry |\n"
            "| **no_made_hand** | dry gutshot | **55.5%** | **BET ★** | セミブラフが機能 |\n"
            "| エア | dry FD/OESD | **34-38%** | CHECK | 強ドロー = スローレイ傾向 |\n\n"
            "**核心**: king/ace-high（ブロッカー価値大）→ CHECK（showdown 価値を守る）\n"
            "third_pair/no_made_hand（ショーダウン価値小）→ BET（ブラフとして最適）\n\n"
            "「ブロッカーがある手がCHECK、ない手がBET」— この逆直感が4BP dry ターンの核心。"
        ),
        bullets=[
            "4BP IP dry: king_high → CHECK ★（24.4%、L100改善=14.71 BB/100 = 最大）",
            "4BP IP dry: third_pair × no_draw → BET ★（64%）、gutshot → BET ★（100%）",
            "4BP IP dry: no_made_hand × no_draw/gutshot → BET ★（56-58%）",
            "FD/OESD × エア → CHECK（強ドロー = スローレイ、34-38%）",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    cards.append(card(
        44, g11b, g11bl,
        scenario="Cash 100bb、4BP（SPR ≈ 1.5）。ターン。Hero = BTN (IP)。BB がチェック。board = Q♥ Q♦ 7♣ 5♠（paired）。",
        question="4BP ターン IP paired board。①third_pair（A♦4♣、73手）②ace_high（A♦4♣、ペアなし）③no_made_hand（5♥4♥）はBETかCHECKか？",
        answer="①③はBET ★（third_pair=90.5%、ace_high paired=59.2%）②CHECKに近い。paired boardはdryと異なる例外パターン",
        board="QhQd7c5s",
        body=(
            "**4BP ターン IP paired board — third_pair と ace_high が逆転BET**\n\n"
            "| ハンドカテゴリ | paired board | GTO BET% | 正解 |\n"
            "|---|---|---|---|\n"
            "| **third_pair** | no_draw | **90.5%** | **BET ★** |\n"
            "| **ace_high** | no_draw | **59.2%** | **BET ★** |\n"
            "| no_made_hand | no_draw | 36.7% | CHECK |\n"
            "| second_pair | no_draw | 28.8% | CHECK |\n"
            "| underpair | no_draw | 40.8% | CHECK |\n\n"
            "paired board では:\n"
            "- **third_pair（ボードの最下位ペア）**: 90.5% BET — 相手がボードペアを引きにくい場面でブラフ\n"
            "- **ace_high**: 59.2% BET — Aは paired board でのスケア（脅し）として機能\n"
            "- no_made_hand: CHECK（paired board では pure bluff のプレッシャーが弱い）"
        ),
        bullets=[
            "4BP IP paired: third_pair → BET ★（90.5%、gain=4.35 BB/100）",
            "4BP IP paired: ace_high → BET ★（59.2%）← dry では CHECK だが paired では BET",
            "4BP IP paired: no_made_hand/second_pair → CHECK（dry と逆）",
            "paired vs dry の違い: ace_high が dry→CHECK, paired→BET に逆転",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    # ─── Group 11c: 4BP ターン OOP dry 例外 ───
    g11c = "4bp_turn_oop_dry"
    g11cl = "アタックルール / 4BP ターン OOP dry 例外"

    cards.append(card(
        45, g11c, g11cl,
        scenario="Cash 100bb、4BP（SPR ≈ 1.5）。ターン。Hero = BB (OOP)。フロップチェック後、ターンでHeroがファーストアクション。board = J♥ 7♦ 2♣ 5♠（dry）。",
        question="4BP ターン OOP dry。①overpair（Q♥Q♦）②top_pair（J♣9♦）③second_pair(7♣6♦)gutshot あり でBETかCHECKか？",
        answer="①CHECK ★（29.8%）②BET（59.1%）③BET ★（91.8%）。overpairがCHECK、second_pair+gutshot が最強BET — 逆直感",
        board="Jh7d2c5s",
        body=(
            "**4BP OOP dry ターン — overpair が CHECK、lower_pair+draw が BET**\n\n"
            "| ハンドカテゴリ | dry board | GTO BET% | 正解 | 理由 |\n"
            "|---|---|---|---|---|\n"
            "| top_pair | no_draw | **59.1%** | **BET ✓** | top_pair は OOP でもバリュー |\n"
            "| trips | no_draw | **55.6%** | **BET ✓** | trips も BET |\n"
            "| **overpair** | no_draw | **29.8%** | **CHECK ★** | 4BP OOP AA/KK でも CHECK！ |\n"
            "| two_pair | no_draw | **24.0%** | **CHECK ★** | 2P dry OOP も slowplay |\n"
            "| set | no_draw | **25.9%** | CHECK | slowplay |\n"
            "| **second_pair** | **gutshot** | **91.8%** | **BET ★** | 最強ブラフ/セミ（L100=3.45） |\n"
            "| **third_pair** | **gutshot** | **88.3%** | **BET ★** | 同様に最強ブラフ |\n\n"
            "**核心**: 4BP OOP dry ターンは「overpair が CHECK、lower_pair+draw が BET」\n"
            "理由: overpair は BET すると SPR≈1.5 でほぼ全コールに負ける（相手はAK/AA+）。\n"
            "second_pair+gutshot = ショーダウン価値なし → フォールドエクイティのみ → BET 最善。"
        ),
        bullets=[
            "4BP OOP dry: overpair → CHECK ★（29.8%、gain=2.33 BB/100 — AA/KK でも CHECK）",
            "4BP OOP dry: two_pair → CHECK ★（24%）、set → CHECK（slowplay）",
            "4BP OOP dry: second_pair × gutshot → BET ★（91.8%、gain=3.45 BB/100）",
            "4BP OOP dry: third_pair × gutshot → BET ★（88.3%）",
            "top_pair/trips → BET（59%/56%）は通常どおり",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    # ─── Group 12: 3BP/4BP リバー IP ───
    g12 = "3bp_4bp_river_ip"
    g12l = "アタックルール / 3BP・4BP リバー IP"

    cards.append(card(
        32, g12, g12l,
        scenario="Cash 100bb、3BP。フロップ+ターン+リバー双方チェック。OOP がリバーチェック。Hero = BTN (IP)。ドライボード T♠7♦2♣。",
        question="3BP リバー IP delayed attack のルールは何か？ second_pair と king_high では何が違うか？",
        answer="second_pair/underpair/third_pair/no_made_hand → BET★★★。king_high/ace_high/low_pair → CHECK★★★（旧「エア全BET、UP→CHECK」は両方誤り）",
        body=(
            "**3BP リバー IP delayed attack — GTO 実測ルール**\n\n"
            "GTO Wizard 実測データ（dry board）による 3BP IP リバー BET 率:\n\n"
            "| mv_cat | GTO BET% | 推奨 | 旧ルールとの差異 |\n"
            "|---|---|---|---|\n"
            "| TP+ / 2P+ / trips | 96-100% | **BET** | 変更なし |\n"
            "| third_pair | **69.0%** | **BET ★** | 旧「UP→CHECK」は誤り |\n"
            "| second_pair | **79.5%** | **BET ★** | 旧「UP→CHECK」は最大誤り（gain=28BB/100）|\n"
            "| underpair | **59.0%** | **BET ★** | 旧「UP→CHECK」は誤り |\n"
            "| no_made_hand | **60.8%** | **BET ★** | ブラフとして機能 |\n"
            "| **king_high** | **0.4%** | **CHECK ★★★** | 旧「K/Aも例外なしBET」は誤り |\n"
            "| **ace_high** | **1.9%** | **CHECK ★★★** | ショーダウン価値→守る |\n"
            "| **low_pair** | **10.1%** | **CHECK ★★★** | gain=79.88BB/100（最大改善）|\n\n"
            "**核心**: 「エア = CHECK、UP = BET」という直感で覚える。\n"
            "- エア (king/ace_high, low_pair) = ショーダウン価値あり → CHECK\n"
            "- UP (second/third_pair, underpair) = thin value or ブラフ → BET"
        ),
        bullets=[
            "3BP IP リバー: second_pair(79.5%)/underpair(59%)/third_pair(69%)/no_made_hand(61%) → BET★★★",
            "3BP IP リバー: king_high(0.4%)/ace_high(1.9%)/low_pair(10%) → CHECK★★★（ショーダウン価値）",
            "旧「UP → CHECK」は完全に誤り — second_pair が 79.5% BET で最強 BET カテゴリ",
            "旧「エア × dry → 全 BET（K/A も例外なし）」は完全に誤り — king_high = 0.4%",
        ],
        tables=[POT_TYPE_RIVER_TABLE],
    ))

    cards.append(card(
        33, g12, g12l,
        scenario="Cash 100bb、4BP。フロップ+ターン+リバー双方チェック。OOP がリバーチェック。Hero = BTN (IP)。dry board T♠7♦2♣4♦3♠。",
        question="4BP リバー IP delayed attack。no_made_hand と second_pair は BET か CHECK か？（旧「エア→CHECK」修正）",
        answer="TP+ → ALLIN。no_made_hand(57.6%)/second_pair(54%) → BET★（旧「エア→CHECK」は誤り）。king_high/ace_high/low_pair → CHECK。",
        board="Ts7d2c4d3s",
        hand="AhKs",
        body=(
            "**4BP リバー IP delayed attack — GTO 実測ルール（no_made_hand/second_pair 解禁）**\n\n"
            "SPR ≈ 1 のリバーでは、no_made_hand と second_pair も BET が正解:\n\n"
            "| mv_cat | GTO BET% | 推奨 | 理由 |\n"
            "|---|---|---|---|\n"
            "| TP+ / 2P+ | 85-100% | **ALLIN** | SPR≈1 で全額バリュー |\n"
            "| **no_made_hand** | **57.6%** | **BET ★** | SPR≈1 でもブラフが機能（相手がフォールドかオールインのみ）|\n"
            "| **second_pair** | **54.0%** | **BET ★** | thin value（旧「エア→CHECK」は誤り: gain=44.85BB/100）|\n"
            "| king_high | 3.2% | CHECK | ショーダウン価値を守る |\n"
            "| ace_high | 1.4% | CHECK | ショーダウン価値を守る |\n"
            "| low_pair | 13.3% | CHECK | ショーダウン価値を守る |\n\n"
            "**理由**: SPR≈1 では相手は「フォールドかオールイン」の二択。\n"
            "no_made_hand はショーダウン価値ゼロなのでブラフが最善。\n"
            "second_pair は thin value（相手の ace/king_high に勝てる）。"
        ),
        bullets=[
            "4BP IP リバー: TP+/2P+ → ALLIN（SPR≈1 で全力バリュー）",
            "4BP IP リバー: no_made_hand(57.6%) → BET★（ブラフ: ショーダウン価値ゼロ→ブラフのみ）",
            "4BP IP リバー: second_pair(54%) → BET★（thin value: ace/king_high に勝てる）",
            "旧「エア→CHECK」は誤り — no_made_hand/second_pair が解禁される（king/ace_high は CHECK）",
        ],
        tables=[POT_TYPE_RIVER_TABLE],
    ))

    # ─── Group 6b: OOP 3BP/4BP リバー ───
    g6b = "river_oop_3bp_4bp"
    g6bl = "アタックルール / OOP リバー（3BP・4BP polarization）"

    cards.append(card(
        36, g6b, g6bl,
        scenario="Cash 100bb、3BP（SPR ≈ 3）。リバー。Hero = OOP（BB）。フロップ・ターン双方チェック。dry board。",
        question="3BP リバー OOP: low_pair と second_pair はどちらが BET か？（エアの細分類）",
        answer="second_pair(85%)/underpair(66%)/third_pair(75%) → BET★★★。king_high(0%)/low_pair(17%) → CHECK★★★（旧「エア以外全BET」では低_pair を BET してしまう誤り）",
        body=(
            "**3BP リバー OOP — エア細分類による正確なルール**\n\n"
            "GTO Wizard 実測データ（dry board、3BP OOP リバー）:\n\n"
            "| mv_cat | GTO BET% | 推奨 | 旧ルールとの差異 |\n"
            "|---|---|---|---|\n"
            "| TP+ (top_pair/overpair) | 74-89% | **BET** | 変更なし |\n"
            "| third_pair | **75.2%** | **BET ★** | thin value |\n"
            "| second_pair | **85.2%** | **BET ★** | 最強 BET カテゴリ |\n"
            "| underpair | **65.9%** | **BET ★** | thin value |\n"
            "| **king_high** | **0.0%** | **CHECK ★★★** | 完全 CHECK — ショーダウン価値 |\n"
            "| **ace_high** | **10.3%** | **CHECK ★★★** | gain=22.71BB/100 |\n"
            "| **low_pair** | **17.3%** | **CHECK ★★★** | **gain=65.49BB/100（最大改善！）**|\n"
            "| two_pair | 45.6% | CHECK | OOP dry × 3BP では境界 |\n\n"
            "**核心**: 「low_pair = エア = CHECK」「second_pair = UP = BET」\n"
            "- エア (king/ace_high, low_pair): ショーダウン価値あり → CHECK\n"
            "- UP (second/third_pair, underpair): thin value → BET"
        ),
        bullets=[
            "3BP OOP リバー dry: second_pair(85%)/underpair(66%)/third_pair(75%) → BET★★★",
            "3BP OOP リバー dry: king_high(0%)/ace_high(10%)/low_pair(17%) → CHECK★★★",
            "low_pair の誤BETは gain=65.49BB/100（最大改善ポイント）",
            "旧「エア=CHECK、UP=BET」という分類では low_pair を正しく分類できない（low_pair=CHECK★★★）",
        ],
        tables=[
            {
                "title": "3BP リバー OOP dry（GTO 実測）",
                "headers": ["mv_cat", "GTO BET%", "推奨"],
                "rows": [
                    ["second_pair", "85.2%", "BET★（最強）"],
                    ["third_pair", "75.2%", "BET★"],
                    ["underpair", "65.9%", "BET★"],
                    ["king_high", "0.0%", "CHECK★★★"],
                    ["ace_high", "10.3%", "CHECK★★★"],
                    ["low_pair", "17.3%", "CHECK★★★（gain=65BB/100）"],
                ],
            },
        ],
    ))

    cards.append(card(
        37, g6b, g6bl,
        scenario="Cash 100bb、4BP（SPR ≈ 1）。リバー。Hero = OOP（BB）。フロップ・ターン双方チェック。dry board。",
        question="4BP リバー OOP で overpair と third_pair はどちらが BET か？（逆転パターン）",
        answer="third_pair(76.4%)/low_pair(58%) → BET★★★。overpair(12.5%)/trips(43%) → CHECK★。「low_pair が BET、overpair が CHECK」の逆転",
        body=(
            "**4BP リバー OOP — low_pair/third_pair が BET、overpair/trips が CHECK（最大逆転）**\n\n"
            "GTO Wizard 実測データ（dry board、4BP OOP リバー）:\n\n"
            "| mv_cat | GTO BET% | 推奨 | 旧ルールとの差異 |\n"
            "|---|---|---|---|\n"
            "| top_pair / two_pair / straight | 55-88% | **BET** | 変更なし |\n"
            "| set / second_pair / underpair | 52-73% | **BET** | 変更なし |\n"
            "| **third_pair** | **76.4%** | **BET ★★★** | gain=37.71BB/100（最大誤差）|\n"
            "| **low_pair** | **57.9%** | **BET ★★★** | gain=24.47BB/100 |\n"
            "| **overpair** | **12.5%** | **CHECK ★** | gain=2.66BB/100 |\n"
            "| **trips** | **43.4%** | **CHECK ★** | trips が CHECK（逆直感）|\n"
            "| king_high / no_made_hand | 4-34% | CHECK | エアはほぼ CHECK |\n\n"
            "**理由（4BP OOP overpair → CHECK）**:\n"
            "SPR ≈ 1 で overpair は相手のオールインにコールする義務があるが、\n"
            "相手の 4BP レンジ（AA/AK+）に overpair は弱い。CHECK してショーダウン。\n\n"
            "**理由（low_pair → BET）**:\n"
            "low_pair はショーダウン価値が低いため、BET（ブラフ）の方が EV が高い。"
        ),
        bullets=[
            "4BP OOP リバー: third_pair(76.4%)/low_pair(58%) → BET★★★（ブラフ: ショーダウン価値低い）",
            "4BP OOP リバー: overpair(12.5%) → CHECK★（SPR≈1 で相手の 4BP レンジに対して守る）",
            "4BP OOP リバー: trips(43.4%) → CHECK（逆直感）",
            "「low_pair が BET、overpair が CHECK」の逆転 — 旧「エア=CHECK、エア以外=BET」は誤り",
        ],
        tables=[
            {
                "title": "4BP リバー OOP dry（GTO 実測）",
                "headers": ["mv_cat", "GTO BET%", "推奨"],
                "rows": [
                    ["third_pair", "76.4%", "BET★★★（最大 gain=37.71BB/100）"],
                    ["low_pair", "57.9%", "BET★★★（gain=24.47BB/100）"],
                    ["second_pair", "73.0%", "BET"],
                    ["top_pair / two_pair", "55-88%", "BET"],
                    ["overpair", "12.5%", "CHECK★（gain=2.66BB/100）"],
                    ["trips", "43.4%", "CHECK★"],
                ],
            },
        ],
    ))

    # ─── Group 13: リバー エア細分類 修正 ───
    g13 = "river_air_subtypes"
    g13l = "アタックルール / リバー エア細分類（GTO 修正）"

    cards.append(card(
        46, g13, g13l,
        scenario="Cash 100bb、3BP。リバー IP delayed attack。dry board K♠7♦2♣4♦3♠。Hero: K♥9♠（third_pair）。",
        question="3BP リバー IP。K♥9♠ で board = K♠7♦2♣4♦3♠（third_pair × dry）。BET か CHECK か？",
        answer="BET★（69.0%）— third_pair × 3BP IP dry は BET。旧「UP → CHECK」は誤り。second_pair(79.5%)/underpair(59%) も同様に BET★★★",
        board="Ks7d2c4d3s",
        hand="Kh9s",
        body=(
            "**3BP IP リバー干 — third_pair × dry = BET★（旧「UP→CHECK」修正）**\n\n"
            "Hero: K♥9♠（third_pair = 9ペア）。ボード: K♠7♦2♣4♦3♠（dry、ストレート draw なし）。\n\n"
            "9♠ × dry board の GTO BET 率は **69.0%** → BET が正解。\n\n"
            "| mv_cat | GTO BET% | 推奨 |\n"
            "|---|---|---|\n"
            "| second_pair（7-7） | **79.5%** | **BET★★★** |\n"
            "| third_pair（9-9 等） | **69.0%** | **BET★** |\n"
            "| underpair | **59.0%** | **BET★** |\n"
            "| no_made_hand | **60.8%** | **BET★** |\n"
            "| king_high | **0.4%** | **CHECK★★★** |\n"
            "| ace_high | **1.9%** | **CHECK★★★** |\n"
            "| low_pair | **10.1%** | **CHECK★★★** |\n\n"
            "**暗記の鍵**: 3BP dry リバーは「UP = BET、エア(ace/king/low_pair) = CHECK」。\n"
            "旧直感「UP は弱い → CHECK」の逆。thin value として BET が最善。"
        ),
        bullets=[
            "3BP IP dry リバー: third_pair(69%)/second_pair(79.5%)/underpair(59%)/no_made_hand(61%) → BET★★★",
            "3BP IP dry リバー: king_high(0.4%)/ace_high(1.9%)/low_pair(10.1%) → CHECK★★★",
            "旧「UP → CHECK」は誤り — thin value として BET が GTO（gain=28+BB/100）",
            "king/ace_high → CHECK の理由: ショーダウン価値があり、BET するより CHECK してショーダウンが EV 高い",
        ],
        tables=[POT_TYPE_RIVER_TABLE],
    ))

    cards.append(card(
        47, g13, g13l,
        scenario="Cash 100bb、4BP（SPR ≈ 1）。リバー OOP delayed attack。dry board T♠7♦2♣4♦3♠。Hero: 9♥9♦（third_pair）vs 8♠8♣（overpair）の判断。",
        question="4BP OOP dry リバー。third_pair(9-9) と overpair(8-8) ではどちらが BET か？（逆転）",
        answer="third_pair(76.4%) → BET★★★。overpair(12.5%) → CHECK★。low_pair(58%) → BET★★★。直感と逆転する。",
        board="Ts7d2c4d3s",
        hand="9h9d",
        body=(
            "**4BP OOP dry リバー — third_pair/low_pair が BET、overpair が CHECK（大逆転）**\n\n"
            "直感: 「overpair の方が強いのだから BET」 → 間違い。\n\n"
            "| mv_cat | GTO BET% | 推奨 | 理由 |\n"
            "|---|---|---|---|\n"
            "| **third_pair（9-9）** | **76.4%** | **BET ★★★** | ショーダウン価値低 → ブラフが最善（gain=37.71BB/100）|\n"
            "| **low_pair** | **57.9%** | **BET ★★★** | 同上（gain=24.47BB/100）|\n"
            "| second_pair | 73.0% | BET | 同上 |\n"
            "| set / straight / top_pair | 55-88% | BET | バリューライン |\n"
            "| **overpair（8-8）** | **12.5%** | **CHECK ★** | SPR≈1 で相手レンジ(AA/AK)に対してショーダウン |\n"
            "| **trips** | **43.4%** | **CHECK ★** | 逆直感（trips が CHECK）|\n\n"
            "**理由**: SPR ≈ 1 の 4BP では相手のレンジが AA/AK+ 中心。\n"
            "- overpair (8-8): この相手レンジに劣っている → CHECK でショーダウンが EV 高\n"
            "- third_pair (9-9): ショーダウン価値が低い → ブラフBET が最善"
        ),
        bullets=[
            "4BP OOP dry: third_pair(76.4%)/low_pair(58%) → BET★★★（ブラフ: ショーダウン価値低）",
            "4BP OOP dry: overpair(12.5%) → CHECK★（SPR≈1 では AA/AK レンジに overpair が負ける）",
            "4BP OOP dry: trips(43.4%) → CHECK★（逆直感）",
            "「低いペアが BET、高いペアが CHECK」— 4BP OOP リバーの最大逆転パターン",
        ],
        tables=[
            {
                "title": "4BP OOP dry リバー（GTO 実測、逆転パターン）",
                "headers": ["mv_cat", "GTO BET%", "推奨"],
                "rows": [
                    ["third_pair（9-9）", "76.4%", "BET★★★（逆転 BET）"],
                    ["low_pair", "57.9%", "BET★★★（逆転 BET）"],
                    ["second_pair", "73.0%", "BET"],
                    ["overpair（8-8）", "12.5%", "CHECK★（逆転 CHECK）"],
                    ["trips", "43.4%", "CHECK★（逆転 CHECK）"],
                ],
            },
        ],
    ))

    # ─── Group 7: 総合クイズ ───
    g7 = "comprehensive_quiz"
    g7l = "アタックルール / 総合クイズ"

    cards.append(card(
        34, g7, g7l,
        scenario="アタックルール 総合確認。",
        question="フロップ IP で 'always CHECK' (BET しない) カテゴリ × board の組み合わせ（最も多い）は？",
        answer="エア × dry/wet、アンダーペア × dry/wet、TP+ × wet（draw なし）",
        body=(
            "**フロップ IP の CHECK ケース（BET しないパターン）**\n\n"
            "5 ルールで BET する以外はすべて CHECK:\n"
            "- エア × dry → CHECK（役なし＋draw なし：BET する根拠がない）\n"
            "- エア × wet → CHECK（wet では相手のドローに対してブラフが機能しにくい）\n"
            "- UP × dry → CHECK（dry では相手の strong hand に UP が押し負ける）\n"
            "- UP × wet → CHECK（wet では相手のドローや TP+ に対して UP は弱い）\n"
            "- TP+ × wet + DV=0 → CHECK（draw なしでは wet board の TP+ は守勢に回る）"
        ),
        bullets=[
            "BET = 例外5条件を満たす時のみ",
            "デフォルトは CHECK（BET しない組み合わせが多数）",
            "TP+ × wet は draw なしなら CHECK（ルール⑤の条件：DV≥3 が必要）",
        ],
        tables=[RULE_TABLE],
    ))

    cards.append(card(
        35, g7, g7l,
        scenario="アタックルール 総合確認。ターン。",
        question="SRP / 3BP / 4BP それぞれで「アンダーペア × ターン」のルールを比較せよ。",
        answer="SRP=CHECK(draw も×) / 3BP=paired のみBET / 4BP=全 board BET（逆転継続）",
        body=(
            "**ポット種別 × アンダーペア × ターン 比較**\n\n"
            "UP のターン攻撃は pot_type によって全く異なります:\n\n"
            "| pot_type | ターン IP UP | 理由 |\n"
            "|---|---|---|\n"
            "| SRP | CHECK（draw あっても）| SPR ≈ 8：UP はベットレンジに入れられない |\n"
            "| 3BP | BET paired のみ | paired board で相手レンジの弱さを突ける |\n"
            "| 4BP | BET 全 board | SPR ≈ 1.5：オールイン圧力が UP の攻撃を正当化 |\n\n"
            "**覚え方**: SPR が浅いほど UP が攻撃的になる\n"
            "- SRP (SPR≈8): UP は CHECK（SPR 深い = UP に BET する場所がない）\n"
            "- 3BP (SPR≈5): UP は paired だけ BET（paired board 限定でブラフ条件が成立）\n"
            "- 4BP (SPR≈1.5): UP は全 board BET（SPR 浅い = UP でもオールイン圧力が有効）"
        ),
        bullets=[
            "SRP ターン UP: CHECK（SPR ≈ 8 では UP はベットレンジに組み込めない）",
            "3BP ターン UP: paired → BET（paired board で相手レンジの弱さを突く）/ dry・wet → CHECK",
            "4BP ターン UP: 全 board BET（SPR ≈ 1.5 のオールイン圧力が UP の攻撃を正当化）",
            "SPR が浅いほど UP の攻撃性が増す — 覚え方の核心",
        ],
        tables=[POT_TYPE_TURN_TABLE],
    ))

    return cards


def main() -> None:
    cards = build_cards()

    lines = [
        "// GENERATED FILE — DO NOT EDIT.",
        "// Regenerate via: uv run scripts/generate/vol2_attack_drill_generator.py",
        "",
        'import type { Card } from "@/core/cards/types";',
        "",
        f"export const {EXPORT_NAME} = {json.dumps(cards, ensure_ascii=False, indent=2)};",
        "",
    ]

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(cards)} cards → {OUT}")


if __name__ == "__main__":
    main()
