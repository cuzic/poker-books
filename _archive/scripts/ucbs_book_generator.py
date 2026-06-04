#!/usr/bin/env python3
"""
ucbs_book_generator.py — Vol2/Vol3 用 章 generator

Vol2 (A モデル base) と Vol3 (A モデル + 階層 layer / D モデル) の
章を YAML spec から生成する。

新フレームワーク (2026-05):
- A モデル (アグレッサー、cbet 頻度予測): メイドバリュー (MV) + ドローバリュー (DV) →
  総合バリュー (TV) → base + α + β + cat + ε
- D モデル (ディフェンダー、BB defense): メイドバリュー (MV) ベース

数値の単一情報源:
- vol3-mtt-postflop/ucbs_v3.py: A モデルパラメータ
- vol2-cash-postflop/dcbs.py: D モデルパラメータ
- 旧 Light UCBS v2 / Full UCBS-v2 は後方互換のため残存

Usage:
  uv run --with pyyaml python scripts/generate/ucbs_book_generator.py \\
    scripts/generate/specs/vol2_v2_ch01_cbs_formula.yaml \\
    --output vol2-cash-postflop/chapters/01-cbs-formula.md
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Any

# vol2-cash-postflop/ と vol3-mtt-postflop/ から実装を import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol2-cash-postflop"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "vol3-mtt-postflop"))

try:
    import yaml as _yaml
except ImportError:
    raise ImportError("pyyaml が必要です: uv run --with pyyaml python ...")

from ucbs_light_v2 import (  # type: ignore
    LIGHT_V2_BASE, LIGHT_V2_OFFSET, cbs_band, light_ucbs_v2,
)
from ucbs_v2 import (  # type: ignore
    HP_TABLE, DP_TABLE, HAND_CATEGORY, BASE_FREQ, CONTEXTS as FULL_CONTEXTS,
    extract_board_features, is_polarize_board, parse_board_type,
    calc_confidence, apply_confidence_exception, is_ax_dry_or_paired,
    ucbs2_predict,
)
from dcbs import DCBS_CONTEXTS, dcbs_predict  # type: ignore

# A モデル (アグレッサー、Vol2/Vol3 統一構造)
from ucbs_v3 import (  # type: ignore
    BASE as V3_BASE, ALPHA as V3_ALPHA, BETA as V3_BETA,
    CAT_OFFSET as V3_CAT, EPSILON as V3_EPS,
    CTX13 as V3_CTX13, CTX13_TO_5 as V3_CTX_TO_5,
    CTX_GROUP as V3_CTX_GROUP, BOARD_FAMILIES, CTX_GROUPS,
    board_family, predict_v3, predict_v2_light,
)


# ────────────────────────────────────────────────────────────────────
# 表示用ラベル
# ────────────────────────────────────────────────────────────────────

HAND_JP = {
    "no_made_hand": "ノーペア",
    "ace_high": "Aハイ",
    "king_high": "Kハイ",
    "low_pair": "ロー・ポケットペア",
    "underpair": "アンダーペア",
    "third_pair": "サードペア",
    "second_pair": "セカンドペア",
    "top_pair": "トップペア",
    "overpair": "オーバーペア",
    "two_pair": "ツーペア",
    "straight": "ストレート",
    "flush": "フラッシュ",
    "set": "セット",
    "trips": "トリップス",
    "fullhouse": "フルハウス",
    "quads": "クアッズ",
}

DRAW_JP = {
    "no_draw": "ドローなし",
    "twocards_bdfd": "BDFD",
    "gutshot": "ガットショット",
    "oesd": "OESD",
    "fd": "フラッシュドロー",
    "combo_draw": "コンボドロー",
}

CONTEXT_JP = {
    "cash": "Cash 100bb",
    "mtt_short": "MTT 25-50bb",
    "mtt_deep": "MTT 100-200bb",
    "3bp": "3-bet pot IP",
    "turn": "Turn 2nd barrel",
}

# A モデル (13 context) の日本語名
CTX13_JP = {
    "cash_100bb": "Cash 100bb",
    "mtt_25bb": "MTT 25bb",
    "mtt_50bb": "MTT 50bb",
    "mtt_100bb": "MTT 100bb",
    "mtt_200bb": "MTT 200bb",
    "mtt_3bp_20bb": "3BP 20bb",
    "mtt_3bp_25bb": "3BP 25bb",
    "mtt_3bp_50bb": "3BP 50bb",
    "mtt_3bp_100bb": "3BP 100bb",
    "mtt_25bb_turn_btn": "Turn MTT25",
    "mtt_50bb_turn_btn": "Turn MTT50",
    "mtt_100bb_turn_btn": "Turn MTT100",
    "cash_100bb_turn_btn": "Turn Cash100",
}

BOARD_FAMILY_JP = {
    "dry_high": "Dry High (J 以上のハイカード dry)",
    "paired": "Paired (ペアボード)",
    "dynamic": "Dynamic (モノトーン or 連結ツーフラ)",
    "low_dry": "Low Dry (T 以下の dry)",
}

CTX_GROUP_JP = {
    "cash": "Cash",
    "mtt_srp": "MTT SRP",
    "3bp": "3-bet Pot",
}

BAND_JP = {
    "air": "エアー (TV 0-2)",
    "weak": "弱ペア (TV 3-4)",
    "mid": "中ペア (TV 5-6)",
    "strong": "強ペア (TV 7-8)",
    "nut": "ナッツ (TV 9+)",
}


# ────────────────────────────────────────────────────────────────────
# 計算ヘルパー
# ────────────────────────────────────────────────────────────────────

def calc_light_example(hand: str, draw: str, context: str) -> dict[str, Any]:
    """Light UCBS v2 の計算過程を返す。"""
    hp = HP_TABLE.get(hand, 0)
    dp = DP_TABLE.get(draw, 0)
    cbs = hp + dp
    band = cbs_band(cbs)
    base = LIGHT_V2_BASE[context][band]
    offset = LIGHT_V2_OFFSET.get(hand, 0.0)
    final = max(0.05, min(0.95, base + offset))
    return {
        "hand": hand, "draw": draw, "context": context,
        "hp": hp, "dp": dp, "cbs": cbs, "band": band,
        "base": base, "offset": offset, "final": final,
        "hand_jp": HAND_JP.get(hand, hand),
        "draw_jp": DRAW_JP.get(draw, draw),
        "context_jp": CONTEXT_JP.get(context, context),
        "band_jp": BAND_JP.get(band, band),
    }


def calc_full_example(hand: str, draw: str, board: str, scenario: str, context: str) -> dict[str, Any]:
    """Full UCBS-v2 の計算過程を返す。"""
    d = ucbs2_predict(hand, draw, board, "", scenario, context)
    return {
        "hand": hand, "draw": draw, "board": board, "scenario": scenario,
        "context": context, "hp": d.hp, "dp": d.dp, "cbs": d.cbs,
        "confidence": d.confidence, "direction": d.direction,
        "size": d.size, "threshold": d.threshold,
        "base": d.base, "alpha": d.alpha, "beta_term": d.beta_term,
        "offset": d.offset, "frequency": d.frequency,
        "category": d.category,
        "hand_jp": HAND_JP.get(hand, hand),
        "draw_jp": DRAW_JP.get(draw, draw),
    }


def calc_v3_example(hand: str, draw: str, board: str, context: str) -> dict[str, Any]:
    """UCBS-v3 の計算過程を返す (Vol3 用 7-step)。"""
    p = predict_v3(hand, draw, board, context)
    return {
        "hand": hand, "draw": draw, "board": board, "context": context,
        "hp": p.hp, "dp": p.dp, "cbs": p.cbs, "band": p.band,
        "ctx5": p.ctx5, "ctx_group": p.ctx_group,
        "category": p.category, "family": p.family,
        "base": p.base, "alpha": p.alpha, "beta_term": p.beta_term,
        "cat_offset": p.cat_offset, "epsilon": p.epsilon,
        "frequency": p.frequency,
        "hand_jp": HAND_JP.get(hand, hand),
        "draw_jp": DRAW_JP.get(draw, draw),
        "ctx13_jp": CTX13_JP.get(context, context),
        "ctx5_jp": CONTEXT_JP.get(p.ctx5, p.ctx5),
        "family_jp": BOARD_FAMILY_JP.get(p.family, p.family),
        "band_jp": BAND_JP.get(p.band, p.band),
    }


def calc_v2light_example(hand: str, draw: str, ctx5: str) -> dict[str, Any]:
    """Vol2 Light (新 base のみ) の計算過程。"""
    r = predict_v2_light(hand, draw, ctx5)
    return {
        "hand": hand, "draw": draw, "ctx5": ctx5,
        "hp": r["hp"], "dp": r["dp"], "cbs": r["cbs"], "band": r["band"],
        "base": r["base"], "offset": r["offset"], "final": r["final"],
        "hand_jp": HAND_JP.get(hand, hand),
        "draw_jp": DRAW_JP.get(draw, draw),
        "ctx5_jp": CONTEXT_JP.get(ctx5, ctx5),
        "band_jp": BAND_JP.get(r["band"], r["band"]),
    }


def calc_dcbs_example(hand: str, context: str) -> dict[str, Any]:
    """DCBS の計算過程を返す。"""
    d = dcbs_predict(hand, context)
    return {
        "hand": hand, "context": context,
        "hp": d.hp, "base": d.base, "kicker_offset": d.kicker_offset,
        "continue_freq": d.continue_freq, "fold_freq": d.fold_freq,
        "hand_jp": HAND_JP.get(hand, hand),
        "context_jp": CONTEXT_JP.get(context, context),
    }


# ────────────────────────────────────────────────────────────────────
# テーブル render
# ────────────────────────────────────────────────────────────────────

def render_hp_table() -> str:
    """HP テーブル (16 hand → 6 バケット) を markdown 表で出力。"""
    rows = []
    by_hp: dict[int, list[str]] = {}
    for hand, hp in HP_TABLE.items():
        by_hp.setdefault(hp, []).append(hand)
    rows.append("| HP | 役 (英) | 役 (日) |")
    rows.append("|---:|---|---|")
    for hp in sorted(by_hp.keys()):
        hands = by_hp[hp]
        for h in hands:
            rows.append(f"| {hp} | {h} | {HAND_JP.get(h, h)} |")
    return "\n".join(rows)


def render_hp_buckets() -> str:
    """HP バケットを集約した markdown 表 (1 バケット 1 行)。"""
    by_hp: dict[int, list[str]] = {}
    for hand, hp in HP_TABLE.items():
        by_hp.setdefault(hp, []).append(hand)
    rows = ["| HP | 含まれる役 |", "|---:|---|"]
    for hp in sorted(by_hp.keys()):
        hands_jp = ", ".join(HAND_JP.get(h, h) for h in by_hp[hp])
        rows.append(f"| {hp} | {hands_jp} |")
    return "\n".join(rows)


def render_dp_table() -> str:
    """DP テーブルを markdown 表で出力。"""
    by_dp: dict[int, list[str]] = {}
    for draw, dp in DP_TABLE.items():
        by_dp.setdefault(dp, []).append(draw)
    rows = ["| DP | ドロー種別 |", "|---:|---|"]
    for dp in sorted(by_dp.keys()):
        draws_jp = ", ".join(DRAW_JP.get(d, d) for d in by_dp[dp])
        rows.append(f"| {dp} | {draws_jp} |")
    return "\n".join(rows)


def render_25cell_table() -> str:
    """Light UCBS v2 の 5 context × 5 band の 25 セル表。"""
    bands = ["air", "weak", "mid", "strong", "nut"]
    rows = ["| Context | " + " | ".join(BAND_JP[b].split(" ")[0] for b in bands) + " |"]
    rows.append("|---|" + "|".join(":-:" for _ in bands) + "|")
    for ctx_key, ctx_jp in CONTEXT_JP.items():
        cells = [f"{int(LIGHT_V2_BASE[ctx_key][b]*100)}%" for b in bands]
        rows.append(f"| {ctx_jp} | " + " | ".join(cells) + " |")
    table = "\n".join(rows)
    note = (
        "\n\n**例外**: " +
        ", ".join(f"`{h}` {int(v*100):+d}pt" for h, v in LIGHT_V2_OFFSET.items()) +
        " (context 共通)"
    )
    return table + note


def render_full_context_params() -> str:
    """Full UCBS-v2 の 13 context パラメータ表。"""
    rows = [
        "| Context | α | β | slowplay | trash | premium | SB lift | wide lift | A-x lift |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for ctx_name, params in FULL_CONTEXTS.items():
        pos = params.get("pos_lift", {})
        sb = pos.get("SB", 0.0)
        wide = pos.get("CO", 0.0)
        ax = params.get("ax_range_bet", 0.0)
        rows.append(
            f"| {ctx_name} | "
            f"{params['alpha']*100:+.0f} | "
            f"{params['beta']*100:+.0f} | "
            f"{params['off_slowplay']*100:+.0f} | "
            f"{params['off_trash']*100:+.0f} | "
            f"{params['off_premium']*100:+.0f} | "
            f"{sb*100:+.0f} | "
            f"{wide*100:+.0f} | "
            f"{ax*100:+.0f} |"
        )
    return "\n".join(rows)


def render_dcbs_table() -> str:
    """Full DCBS の 4 context × HP × kicker offset 表。"""
    rows = ["### DCBS HP 別 base continue freq", ""]
    rows.append("| HP | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |")
    rows.append("|---:|---:|---:|---:|---:|")
    for hp in [2, 3, 5, 7, 8, 9]:
        cells = [
            f"{int(DCBS_CONTEXTS[ctx]['base'].get(hp, 1.0)*100)}%"
            for ctx in ["mtt_25bb", "mtt_50bb", "mtt_100bb", "cash_100bb"]
        ]
        rows.append(f"| {hp} | " + " | ".join(cells) + " |")
    rows.append("")
    rows.append("### DCBS Kicker offset (HP=2 内の細分化)")
    rows.append("")
    rows.append("| Hand | mtt_25bb | mtt_50bb | mtt_100bb | cash_100bb |")
    rows.append("|---|---:|---:|---:|---:|")
    for hand in ["ace_high", "king_high", "no_made_hand", "low_pair"]:
        cells = [
            f"{int(DCBS_CONTEXTS[ctx]['kicker'].get(hand, 0.0)*100):+d}pt"
            for ctx in ["mtt_25bb", "mtt_50bb", "mtt_100bb", "cash_100bb"]
        ]
        rows.append(f"| {HAND_JP.get(hand, hand)} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def render_v3_base_table() -> str:
    """A モデル の 25 cell base 表 (Vol2 と共通)。"""
    rows = ["| Context | air (TV 0-2) | weak (3-4) | mid (5-6) | strong (7-8) | nut (9+) |",
            "|---|---:|---:|---:|---:|---:|"]
    for ctx5 in ["cash", "mtt_short", "mtt_deep", "3bp", "turn"]:
        cells = [f"{round(V3_BASE[ctx5][b]*100)}%" for b in ["air", "weak", "mid", "strong", "nut"]]
        rows.append(f"| {CONTEXT_JP.get(ctx5, ctx5)} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def render_v3_alpha_beta_table() -> str:
    """A モデル の α / β layer (13 context)。"""
    rows = ["| Context | α (コンテキスト補正) | β (強ハンド補正、TV≥7) |", "|---|---:|---:|"]
    for ctx in V3_CTX13:
        a = V3_ALPHA[ctx]
        b = V3_BETA[ctx]
        rows.append(f"| {CTX13_JP.get(ctx, ctx)} | {a*100:+.0f} | {b*100:+.0f} |")
    return "\n".join(rows)


def render_v3_cat_offset_table() -> str:
    """A モデル の hand class offset 表 (ハンドクラス補正)。"""
    rows = ["| Category | 含まれる役 | ハンドクラス補正 |", "|---|---|---:|"]
    cat_examples = {
        "default": "通常 (top_pair / second_pair / 等)",
        "slowplay": "set / trips / two_pair / fullhouse / flush / straight / quads",
        "trash": "low_pair",
        "premium": "overpair / underpair",
    }
    for cat in ["default", "slowplay", "trash", "premium"]:
        v = V3_CAT.get(cat, 0.0)
        rows.append(f"| {cat} | {cat_examples[cat]} | {v*100:+.0f}pt |")
    return "\n".join(rows)


def render_v3_epsilon_table() -> str:
    """A モデル の board family ε 表 (3 family × 3 ctx_group、ボード補正)。"""
    rows = ["| Board family | Cash | MTT SRP | 3-bet Pot |",
            "|---|---:|---:|---:|"]
    for fam in ["dry_high", "paired", "dynamic", "low_dry"]:
        cells = [f"{V3_EPS[fam][cg]*100:+.0f}pt" for cg in ["cash", "mtt_srp", "3bp"]]
        rows.append(f"| {BOARD_FAMILY_JP.get(fam, fam)} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def render_v3_board_family_rules() -> str:
    """板分類ロジックを箇条書きで出力。"""
    return ("\n".join([
        "1. **paired**: フロップ 3 枚に同ランクが含まれる",
        "2. **dynamic**: モノトーン (3 枚同スート)、または (ストレート連結 + ツーフラ)",
        "3. **dry_high**: 上記以外で、最高ランクが J 以上 (**baseline**、補正なし)",
        "4. **low_dry**: 上記以外で、最高ランクが T 以下",
    ]))


def render_hand_category_table() -> str:
    """ハンドカテゴリ (slowplay/trash/premium/default) 表。"""
    by_cat: dict[str, list[str]] = {"slowplay": [], "trash": [], "premium": [], "default": []}
    for hand in HP_TABLE.keys():
        cat = HAND_CATEGORY.get(hand, "default")
        by_cat[cat].append(hand)
    rows = ["| カテゴリ | 含まれる役 |", "|---|---|"]
    for cat in ["slowplay", "trash", "premium", "default"]:
        hands_jp = ", ".join(HAND_JP.get(h, h) for h in by_cat[cat])
        rows.append(f"| {cat} | {hands_jp} |")
    return "\n".join(rows)


def render_light_example(example: dict[str, Any]) -> str:
    """Light UCBS 計算過程を prose で出力。"""
    e = example
    lines = [
        f"**例**: {e['hand_jp']} ({e['hand']}) + {e['draw_jp']} on {e['context_jp']}",
        "",
        f"1. HP = **{e['hp']}** ({e['hand']} のバケット)",
        f"2. DP = **{e['dp']}** ({e['draw_jp']})",
        f"3. CBS = HP + DP = {e['hp']} + {e['dp']} = **{e['cbs']}**",
        f"4. CBS バンド: {e['band_jp']}",
        f"5. base = LIGHT_V2_BASE[{e['context']}][{e['band']}] = **{int(e['base']*100)}%**",
    ]
    if e['offset'] != 0:
        lines.append(f"6. {e['hand']} の例外 offset: {int(e['offset']*100):+d}pt")
    lines.append(f"→ **連続 bet 頻度 ≈ {int(e['final']*100)}%**")
    return "\n".join(lines)


def render_full_example(example: dict[str, Any]) -> str:
    """Full UCBS-v2 計算過程を prose で出力。"""
    e = example
    lines = [
        f"**例**: {e['hand_jp']} ({e['hand']}) on `{e['board']}` ({e['scenario']}, context={e['context']})",
        "",
        f"1. HP = {e['hp']}, DP = {e['dp']}, CBS = **{e['cbs']}**",
        f"2. threshold = {e['threshold']}, |CBS-T| → confidence = **{e['confidence']}**",
        f"3. direction = (CBS≥T) = **{e['direction']}**",
        f"4. size = **{e['size']}%** ({'polarize' if e['size']==116 else 'small'})",
        f"5. base_freq[({e['confidence']}, {e['direction']}, {e['size']})] = **{int(e['base']*100)}%**",
        f"6. α = {int(e['alpha']*100):+d}, β·I(CBS≥7) = {int(e['beta_term']*100):+d}, offset({e['category']}) = {int(e['offset']*100):+d}",
        f"→ **frequency = {int(e['frequency']*100)}%**",
    ]
    return "\n".join(lines)


def render_v3_example(example: dict[str, Any]) -> str:
    """A モデル (7-step) の計算過程を prose で出力。"""
    e = example
    lines = [
        f"**例**: {e['hand_jp']} ({e['hand']}) + {e['draw_jp']} on `{e['board']}` ({e['ctx13_jp']})",
        "",
        f"1. MV = **{e['hp']}** ({e['hand']})、DV = **{e['dp']}** ({e['draw_jp']})",
        f"2. TV = MV + DV = {e['hp']} + {e['dp']} = **{e['cbs']}** → band: {e['band_jp']}",
        f"3. ctx5 = {e['ctx5_jp']} → base = base[{e['ctx5']}][{e['band']}] = **{round(e['base']*100)}%**",
        f"4. α[{e['context']}] (コンテキスト補正) = **{round(e['alpha']*100):+d}pt**",
        f"5. β[{e['context']}]·I(TV≥7) (強ハンド補正) = **{round(e['beta_term']*100):+d}pt**",
        f"6. cat[{e['category']}] (ハンドクラス補正) = **{round(e['cat_offset']*100):+d}pt**",
        f"7. 板分類: {e['family_jp']} → ε[{e['family']}][{e['ctx_group']}] (ボード補正) = **{round(e['epsilon']*100):+d}pt**",
        "",
        f"→ **連続 bet 頻度 ≈ {round(e['frequency']*100)}%**",
    ]
    return "\n".join(lines)


def render_v2light_example(example: dict[str, Any]) -> str:
    """Vol2 A モデル base (4-step) の計算過程。"""
    e = example
    lines = [
        f"**例**: {e['hand_jp']} ({e['hand']}) + {e['draw_jp']} on {e['ctx5_jp']}",
        "",
        f"1. MV = **{e['hp']}** ({e['hand']})、DV = **{e['dp']}** ({e['draw_jp']})",
        f"2. TV = MV + DV = {e['hp']} + {e['dp']} = **{e['cbs']}** → band: {e['band_jp']}",
        f"3. base = 25cell[{e['ctx5']}][{e['band']}] = **{round(e['base']*100)}%**",
    ]
    if e['offset'] != 0:
        lines.append(f"4. low_pair 例外: {round(e['offset']*100):+d}pt")
    lines.append("")
    lines.append(f"→ **連続 bet 頻度 ≈ {round(e['final']*100)}%**")
    return "\n".join(lines)


def render_dcbs_example(example: dict[str, Any]) -> str:
    """DCBS 計算過程を prose で出力。"""
    e = example
    lines = [
        f"**例**: {e['hand_jp']} ({e['hand']}) を {e['context_jp']} で defense",
        "",
        f"1. HP = **{e['hp']}**",
        f"2. base = DCBS_BASE[{e['context']}][HP={e['hp']}] = **{int(e['base']*100)}%**",
    ]
    if e['kicker_offset'] != 0:
        lines.append(f"3. kicker offset ({e['hand']}) = {int(e['kicker_offset']*100):+d}pt")
    lines.append(f"→ **continue freq = {int(e['continue_freq']*100)}%** (fold = {int(e['fold_freq']*100)}%)")
    return "\n".join(lines)


# ────────────────────────────────────────────────────────────────────
# Section render dispatcher
# ────────────────────────────────────────────────────────────────────

TABLE_RENDERERS = {
    "hp_table": render_hp_table,
    "hp_buckets": render_hp_buckets,
    "dp_table": render_dp_table,
    "25cell_table": render_25cell_table,
    "full_context_params": render_full_context_params,
    "dcbs_table": render_dcbs_table,
    "hand_category_table": render_hand_category_table,
    # UCBS-v3 (A+C3 階層型)
    "v3_base": render_v3_base_table,
    "v3_alpha_beta": render_v3_alpha_beta_table,
    "v3_cat_offset": render_v3_cat_offset_table,
    "v3_epsilon": render_v3_epsilon_table,
    "v3_board_family_rules": render_v3_board_family_rules,
}


def render_section(section: dict[str, Any]) -> str:
    """Section 1 つを markdown に render。"""
    stype = section.get("type", "prose")

    if stype == "prose":
        return section.get("body", "").rstrip()

    if stype == "table":
        template = section.get("template", "")
        if template not in TABLE_RENDERERS:
            return f"<!-- ERROR: unknown table template '{template}' -->"
        title = section.get("title", "")
        result = TABLE_RENDERERS[template]()
        return f"### {title}\n\n{result}" if title else result

    if stype == "examples":
        framework = section.get("framework", "light")
        cases = section.get("cases", [])
        title = section.get("title", "")
        outputs = []
        if title:
            outputs.append(f"### {title}")
            outputs.append("")
        for case in cases:
            if framework == "light":
                ex = calc_light_example(
                    hand=case["hand"],
                    draw=case.get("draw", "no_draw"),
                    context=case["context"],
                )
                outputs.append(render_light_example(ex))
            elif framework == "full":
                ex = calc_full_example(
                    hand=case["hand"],
                    draw=case.get("draw", "no_draw"),
                    board=case["board"],
                    scenario=case.get("scenario", "BTN"),
                    context=case["context"],
                )
                outputs.append(render_full_example(ex))
            elif framework == "dcbs":
                ex = calc_dcbs_example(
                    hand=case["hand"],
                    context=case["context"],
                )
                outputs.append(render_dcbs_example(ex))
            elif framework == "v3":
                ex = calc_v3_example(
                    hand=case["hand"],
                    draw=case.get("draw", "no_draw"),
                    board=case["board"],
                    context=case["context"],
                )
                outputs.append(render_v3_example(ex))
            elif framework == "v2light":
                ex = calc_v2light_example(
                    hand=case["hand"],
                    draw=case.get("draw", "no_draw"),
                    ctx5=case["context"],
                )
                outputs.append(render_v2light_example(ex))
            outputs.append("")
        return "\n".join(outputs).rstrip()

    if stype == "heading":
        level = section.get("level", 2)
        text = section.get("text", "")
        return ("#" * level) + f" {text}"

    return f"<!-- ERROR: unknown section type '{stype}' -->"


# ────────────────────────────────────────────────────────────────────
# Chapter generation
# ────────────────────────────────────────────────────────────────────

def generate_chapter(spec_path: Path) -> str:
    """YAML spec から章 markdown を生成。"""
    spec = _yaml.safe_load(spec_path.read_text(encoding='utf-8'))
    title = spec.get("title", "")
    chapter_num = spec.get("chapter_num", "??")
    volume = spec.get("volume", "VolN")
    summary = spec.get("summary", "")
    sections = spec.get("sections", [])

    out_lines = [f"# 第{chapter_num}章 {title}"]
    if summary:
        out_lines.append("")
        out_lines.append(summary.rstrip())

    for section in sections:
        out_lines.append("")
        out_lines.append(render_section(section))

    out_lines.append("")
    return "\n".join(out_lines)


# ────────────────────────────────────────────────────────────────────
# CLI
# ────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="UCBS-aware book chapter generator")
    ap.add_argument("spec", type=Path, help="YAML spec file")
    ap.add_argument("--output", "-o", type=Path, help="Output .md path")
    args = ap.parse_args()

    if not args.spec.exists():
        sys.exit(f"Spec not found: {args.spec}")

    content = generate_chapter(args.spec)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
        chars = len(content)
        print(f"Wrote {args.output} ({chars} chars)")
    else:
        print(content)


if __name__ == "__main__":
    main()
