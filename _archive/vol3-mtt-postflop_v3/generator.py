#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
"""
MTT ポストフロップ 書籍ジェネレーター
Usage:
  uv run generator.py                     # Generate all chapters (recommended)
  uv run generator.py specs/mtt/ch02.yaml # Generate single chapter
  uv run --with pyyaml python3 generator.py  # Alternative
"""

import json
import glob
import sys
from collections import defaultdict
from pathlib import Path
from datetime import date
import yaml

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
FINDINGS_DIR = BASE_DIR / "findings"
SPECS_DIR = BASE_DIR / "specs" / "mtt"
CHAPTERS_DIR = BASE_DIR / "chapters"

# ─── CBS System Tables ────────────────────────────────────────────────────────
HP_TABLE = {
    'no_made_hand': 5,
    'ace_high':     5,
    'king_high':    5,
    'low_pair':     2,
    'third_pair':   3,
    'underpair':    5,
    'second_pair':  5,
    'top_pair':     7,
    'overpair':     7,
    'two_pair':     9,
    'straight':     9,
    'set':          5,   # slowplay correction
    'trips':        9,
    'fullhouse':    2,   # extreme slowplay
    'quads':        3,
}

DP_TABLE = {
    'no_draw':        0,
    'onecard_bdfd':   0,
    'twocards_bdfd':  0,
    'gutshot':        1,
    'flush_draw':     2,
    'nut_flush_draw': 2,
    'oesd':           2,
    'combo_draw':     3,
}

# Thresholds
THRESHOLD_BTN  = 5
THRESHOLD_SB   = 7
THRESHOLD_LIMP = 7

# Confidence frequency table
FREQ_TABLE = {
    ('HIGH', True):  79,
    ('HIGH', False): 42,   # validated: actual 41.8%
    ('MID',  True):  67,
    ('MID',  False): 39,   # validated: actual 38.8%
    ('LOW',  True):  58,
    ('LOW',  False): 37,   # validated: actual 36.5%
}

# ─── Defense System ──────────────────────────────────────────────────────────
# Ace Dominance Principle: OOP defense Confidence by board type
# High defense Conf = OOP must CR immediately to protect vulnerable TP
# Low defense Conf  = OOP can trap with call (TPTK near-nuts) or manage pot (draws)
DEFENSE_CONF_BY_TYPE = {
    1: 'LOW',     # A高: OOP TPTK ≈ ナッツ（AA only beats it）→ trap
    2: 'HIGH',    # K/Q高: TPMK dominated by AA(6)+AK(9+) → protect now
    3: 'LOW',     # コネクト: many draws → inflating pot hurts OOP
    4: 'LOW',     # ローウェット: same as type 3
    5: 'HIGH',    # ミッド: TPMK vs AA/KK/AK → protect now
    6: 'HIGH',    # ロードライ: TPWK vs all overcards → protect now
    7: 'SPECIAL', # ペア板: second_pair exception; treat as HIGH in practice
}

# OOP top_pair CR% by defense Confidence (GTO-validated, SRP25 BTN vs BB)
DEFENSE_CR_FREQ = {
    'HIGH':    80,   # empirical range: 76–85%
    'LOW':     38,   # empirical range: 37–39%
    'SPECIAL': 55,   # second_pair on paired board
}

def calc_defense_confidence(board_type: int) -> str:
    """Return OOP CR Confidence based on Ace Dominance Principle."""
    return DEFENSE_CONF_BY_TYPE.get(board_type, 'MID')

def calc_cr_threshold(board_type: int, spr_scenario: str = 'SRP25') -> int:
    """Return minimum HP required for OOP to CR (Ace Dominance framework)."""
    is_wet = board_type in (3, 4)
    if spr_scenario == 'SRP25':
        return 7
    elif spr_scenario == 'SRP20':
        return 5 if is_wet else 7
    elif spr_scenario == '3BP':
        return 5
    return 7

# Opener position → defense_study scenarios mapping
# 各 opener が open した SRP シナリオの jsonl ファイル群
OPENER_TO_SCENARIOS = {
    'sb':   ['SRP25_SB_OOP','SRP20_SB_OOP'],
    'btn':  ['SRP25_OOP','SRP20_OOP'],
    'co':   ['CO_BB_SRP25','CO_BB_SRP20'],
    'hj':   ['HJ_BB_SRP25','HJ_BB_SRP20'],
    'lj':   ['EP3_BB_SRP25','EP3_BB_SRP20'],
    'utg1': ['EP2_BB_SRP20'],
    'utg':  ['EP1_BB_SRP20'],
}

# Hands that always have showdown value (defense never folds with these)
PAIR_HANDS_DEFENSE = {
    'low_pair','third_pair','underpair','second_pair','top_pair',
    'overpair','two_pair','set','trips','fullhouse','quads',
    'straight','flush',
}
STRONG_DRAWS_DEFENSE = {'flush_draw','nut_flush_draw','combo_draw','oesd'}

def should_fold(hand_type: str, draw_type: str, board_type: int,
                opener: str = 'btn') -> bool:
    """OOP defense fold rule (open位置別、SRP).

    opener:
      'sb'    - SB open（BB OOP、HU的、コール多）
      'btn'   - BTN open（広いレンジ）
      'co'    - CO open
      'hj'    - HJ open
      'ep'    - LJ/UTG1/UTG open（狭いレンジ）

    精度（個別オープナー検証、n=114254）:
      SB:   90%+ / BTN: 95%+ / CO: 91% / HJ/LJ: 91% / UTG/UTG1: 90%
    """
    # ─── SB は別ロジック（HU 的でコール多） ───
    if opener == 'sb':
        if hand_type in PAIR_HANDS_DEFENSE:
            return False  # SB相手はペア以上ほぼ全部コール
        if draw_type in STRONG_DRAWS_DEFENSE:
            return False
        if draw_type == 'gutshot':
            return board_type == 3  # 型3のみfold
        if draw_type == 'twocards_bdfd':
            return False  # SB相手はBDFDあれば全コール
        # Aハイ/Kハイ no_draw
        if hand_type == 'ace_high':
            return board_type in (2, 3, 4, 5, 7)  # 型6/型1のみcall(型1データなし→fold)
        if hand_type == 'king_high':
            # 型1/2/7 は SB 相手だと混合だがコール寄り
            return board_type in (3, 4, 5, 6)
        return True  # 純エアー no_draw

    # ─── 非SB（BTN/CO/HJ/LJ/EP）共通 ───
    is_wide = opener == 'btn'
    is_mid  = opener == 'co'
    is_tight = opener in ('hj', 'lj', 'ep', 'utg', 'utg1')

    # ─ ペア以上 ─
    if hand_type in PAIR_HANDS_DEFENSE:
        # 中堅ペア × コネクト板の撤退
        if hand_type == 'second_pair':
            if board_type == 3 and is_tight: return True
            if board_type == 4 and opener in ('co','hj'): return True
        if hand_type == 'third_pair':
            if board_type == 3 and not is_wide: return True   # CO以降 fold
            if board_type == 4 and not is_wide: return True   # CO以降 fold
            if board_type == 1 and opener in ('ep','utg','utg1'): return True
        return False

    # ─ 強ドロー ─
    if draw_type in STRONG_DRAWS_DEFENSE - {'oesd'}:
        return False
    if draw_type == 'oesd':
        if board_type == 3 and is_tight: return True
        return False

    # ─ ガットショット ─
    if draw_type == 'gutshot':
        if board_type == 3: return True
        if board_type == 4: return not is_wide  # wide以外 fold
        return False

    # ─ バックドアFD ─
    if draw_type == 'twocards_bdfd':
        if hand_type in ('ace_high', 'king_high'):
            if board_type == 3: return True
            if board_type == 6: return False
            if board_type == 7: return False
            if is_tight:
                if hand_type == 'king_high' and board_type in (1, 4, 5): return True
                if hand_type == 'ace_high' and board_type == 5: return True
            if is_mid:
                if hand_type == 'king_high' and board_type in (1, 4): return True
            return False
        # 純エアー + BDFD
        if board_type == 6:
            return is_mid  # midのみ混合(52%)
        return True

    # ─ Aハイ no_draw ─
    if hand_type == 'ace_high':
        if board_type == 6:
            # BTN F=32%混合、CO F=41%混合、tight F=0%
            return is_mid  # CO のみ fold 判定
        if board_type == 5:
            # BTN F=63% → fold、SB除き全fold
            return True
        return True

    # ─ Kハイ no_draw ─
    if hand_type == 'king_high':
        if board_type == 6:
            # BTN/CO F=68-74% fold、HJ以降 F=46-55% mixed
            return not is_tight  # tight 以外 fold
        if board_type == 7:
            return True  # 全 opener fold (BTN F=61%)
        return True

    # ─ 純エアー no_draw ─
    return True

# ─── Board Classification ─────────────────────────────────────────────────────
def classify_board(board_id: str) -> int:
    """Return board type 1-7 from board_id like 'K98_rain' or 'A72_dry'.

    Type 1: A-high non-connected        (A72, A94)
    Type 2: K/Q-high non-connected      (K98, Q83)  ← was unreachable; fixed
    Type 3: connected high/mid          (T98, KJT)
    Type 4: low connected/wet           (765, 654)
    Type 5: J/T-high non-connected      (J73, T74)
    Type 6: low non-connected/dry       (742, 632)  ← off-by-one fixed
    Type 7: paired board                (KK8, AA7)
    """
    b = board_id.split('_')[0]
    # pair board detection (first two chars identical)
    if len(b) >= 2 and b[0] == b[1]:
        return 7
    rank_vals = []
    for x in b[:3]:
        if x == 'A':   rank_vals.append(14)
        elif x == 'K': rank_vals.append(13)
        elif x == 'Q': rank_vals.append(12)
        elif x == 'J': rank_vals.append(11)
        elif x == 'T': rank_vals.append(10)
        else:
            try:   rank_vals.append(int(x))
            except: continue
    if len(rank_vals) < 3:
        return 0
    rank_vals = sorted(rank_vals, reverse=True)
    top, mid, bot = rank_vals
    if top == mid or mid == bot:
        return 7
    total_gap = top - bot
    # Connected zone (gap ≤ 4): type 3 for high/mid, type 4 for low
    if total_gap <= 4:
        return 3 if top >= 9 else 4
    # Non-connected zone (gap ≥ 5) from here:
    if top == 14:   return 1   # A-high
    if top >= 12:   return 2   # K/Q-high
    if top >= 10:   return 5   # J/T-high
    return 6                   # low card (top ≤ 9, gap ≥ 5 → dry)

# ─── CBS Calculation ──────────────────────────────────────────────────────────
def calc_cbs(hand_type: str, draw_type: str) -> int:
    """Compute CBS score for a hand_type × draw_type combination."""
    hp = HP_TABLE.get(hand_type, 0)
    dp = DP_TABLE.get(draw_type, 0)
    # Air paradox: no_made_hand + oesd → CBS = HP - 2
    if hand_type == 'no_made_hand' and draw_type == 'oesd':
        return hp - 2
    return hp + dp

def calc_confidence(cbs: int, threshold: int, board_type: int) -> str:
    """Return HIGH / MID / LOW confidence."""
    distance = abs(cbs - threshold)
    if distance >= 3:
        return 'HIGH'
    if board_type == 1 and distance <= 2:
        return 'HIGH'   # ace-high dry: reliable even at distance=2
    if board_type == 7 and distance == 0:
        return 'HIGH'   # pair board: only reliable at exact threshold
    if board_type == 7 and distance == 1:
        return 'LOW'    # pair board distance=1: CBS direction empirically unreliable
    if distance == 2:
        return 'MID'
    # distance 0-1 from here
    if board_type == 5:
        return 'MID'
    if board_type in (3, 4):
        return 'LOW'
    return 'MID'

def bet_direction(cbs: int, threshold: int) -> bool:
    return cbs >= threshold

# ─── GTO Data Loading ─────────────────────────────────────────────────────────
def get_scenario_cat(fname: str) -> str:
    name = Path(fname).stem.replace('draw_study_', '')
    tokens = set(name.split('_'))   # token-level match prevents 'SBR' hitting 'SB'
    if 'SBR25' in name:
        return 'EXCLUDE'
    if 'SB_cc' in name:
        return 'BTN'      # SB called BTN raise → BTN is IP
    if 'LIMP' in name:
        return 'LIMP'
    if '3BP' in name and 'SB' in tokens:
        return '3BP_OOP'  # SB is 3bettor (OOP), leads postflop
    if '3BP' in name:
        return '3BP_IP'   # BTN is caller (IP), leads postflop
    if 'SB' in tokens:
        return 'SB'
    if 'CO' in name:
        return 'CO'
    return 'BTN'

def load_gto_data() -> dict:
    """
    Returns: {scenario: {hand_type|draw_type: mean_pct}}
    Scenario categories: BTN, SB, LIMP, 3BP
    """
    files = glob.glob(str(FINDINGS_DIR / "draw_study_*.jsonl"))
    raw = defaultdict(lambda: defaultdict(list))

    for f in files:
        cat = get_scenario_cat(f)
        if cat == 'EXCLUDE':
            continue
        with open(f) as fh:
            for line in fh:
                try:
                    board = json.loads(line)
                    for key, val in board['cross'].items():
                        raw[cat][key].append(val['avg'])
                except (json.JSONDecodeError, KeyError):
                    continue

    result = {}
    for cat, entries in raw.items():
        result[cat] = {k: sum(v) / len(v) for k, v in entries.items()}
    return result

# Global GTO data (loaded once)
_GTO_DATA: dict = {}

def get_gto_data() -> dict:
    global _GTO_DATA
    if not _GTO_DATA:
        _GTO_DATA = load_gto_data()
    return _GTO_DATA

# ─── Defense GTO Data Loading ─────────────────────────────────────────────────
def load_defense_data() -> dict:
    """
    Load defense_study_*.jsonl files.
    Returns: {scenario: {board_type: {hand|draw: {raise_pct, call_pct, fold_pct, n}}}}
    Aggregates multiple boards of the same type with n-weighted averaging.
    """
    files = glob.glob(str(FINDINGS_DIR / "defense_study_*.jsonl"))
    raw: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    for f in files:
        scenario = Path(f).stem.replace("defense_study_", "")
        with open(f) as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                    bt = rec.get("board_type", 0)
                    for key, val in rec.get("cross", {}).items():
                        if isinstance(val, dict) and val.get("n", 0) >= 5:
                            raw[scenario][bt][key].append(val)
                except (json.JSONDecodeError, KeyError):
                    continue

    result: dict = {}
    for scenario, board_data in raw.items():
        result[scenario] = {}
        for bt, hand_data in board_data.items():
            result[scenario][bt] = {}
            for key, vals in hand_data.items():
                tot_n = sum(v["n"] for v in vals)
                if tot_n > 0:
                    result[scenario][bt][key] = {
                        "raise_pct": sum(v["raise_pct"] * v["n"] for v in vals) / tot_n,
                        "call_pct":  sum(v["call_pct"]  * v["n"] for v in vals) / tot_n,
                        "fold_pct":  sum(v["fold_pct"]  * v["n"] for v in vals) / tot_n,
                        "n": tot_n,
                    }
    return result

_DEFENSE_DATA: dict = {}

def get_defense_data() -> dict:
    global _DEFENSE_DATA
    if not _DEFENSE_DATA:
        _DEFENSE_DATA = load_defense_data()
    return _DEFENSE_DATA

def defense_cr_avg(hand_type: str, draw_type: str, board_type: int,
                   scenario: str = 'SRP25_OOP') -> 'float | None':
    """Return n-weighted mean OOP CR% for hand × draw × board_type × scenario."""
    data = get_defense_data()
    key = f"{hand_type}|{draw_type}"
    entry = data.get(scenario, {}).get(board_type, {}).get(key)
    return entry["raise_pct"] if entry else None

def defense_cr_avg_all_types(hand_type: str, draw_type: str,
                              scenario: str) -> 'float | None':
    """Return n-weighted mean OOP CR% across all board types for a scenario."""
    data = get_defense_data()
    key = f"{hand_type}|{draw_type}"
    all_entries = [
        entry for bt_data in data.get(scenario, {}).values()
        if (entry := bt_data.get(key)) is not None
    ]
    if not all_entries:
        return None
    tot_n = sum(e["n"] for e in all_entries)
    return sum(e["raise_pct"] * e["n"] for e in all_entries) / tot_n

def defense_cr_avg_types(hand_type: str, draw_type: str,
                          board_types: tuple, scenario: str) -> 'float | None':
    """Return n-weighted mean OOP CR% filtered to specific board types."""
    data = get_defense_data()
    key = f"{hand_type}|{draw_type}"
    entries = [
        entry for bt in board_types
        if (entry := data.get(scenario, {}).get(bt, {}).get(key)) is not None
    ]
    if not entries:
        return None
    tot_n = sum(e["n"] for e in entries)
    return sum(e["raise_pct"] * e["n"] for e in entries) / tot_n

def gto_avg(hand_type: str, draw_type: str, scenario: str = 'BTN') -> 'float | None':
    """Return mean GTO CBet% for a hand × draw × scenario combo."""
    data = get_gto_data()
    key = f"{hand_type}|{draw_type}"
    cat_data = data.get(scenario, {})
    return cat_data.get(key, None)

# ─── Section Renderers ────────────────────────────────────────────────────────

def render_text(section: dict) -> str:
    return section.get('content', '')

def render_hp_table(section: dict) -> str:
    """Generate HP table with GTO-validated actual CBet% columns."""
    title = section.get('title', 'HPテーブル（GTO実測値付き）')
    lines = [f"### {title}", ""]
    lines.append("| ハンド種別 | HP | DP例 | CBS | BTN実測% | SB実測% | ベット方向(BTN) |")
    lines.append("|----------|----|----|-----|---------|--------|--------------|")

    hand_types = [
        ('no_made_hand', 'no_draw',        'エアー'),
        ('ace_high',     'no_draw',        'Aハイ'),
        ('king_high',    'no_draw',        'Kハイ'),
        ('low_pair',     'no_draw',        'ロウペア'),
        ('third_pair',   'no_draw',        'サードペア'),
        ('second_pair',  'no_draw',        'セカンドペア'),
        ('top_pair',     'no_draw',        'トップペア'),
        ('overpair',     'no_draw',        'オーバーペア'),
        ('two_pair',     'no_draw',        'ツーペア'),
        ('set',          'no_draw',        'セット'),
        ('trips',        'no_draw',        'トリップス'),
        ('fullhouse',    'no_draw',        'フルハウス'),
        ('no_made_hand', 'flush_draw',     'エアー+FD'),
        ('no_made_hand', 'oesd',           'エアー+OESD'),
        ('second_pair',  'flush_draw',     '2ndペア+FD'),
        ('top_pair',     'flush_draw',     'TP+FD'),
    ]

    for hand_type, draw_type, label in hand_types:
        hp = HP_TABLE.get(hand_type, 0)
        dp = DP_TABLE.get(draw_type, 0)
        if hand_type == 'no_made_hand' and draw_type == 'oesd':
            cbs = hp - 2
        else:
            cbs = hp + dp
        btn_pct = gto_avg(hand_type, draw_type, 'BTN')
        sb_pct  = gto_avg(hand_type, draw_type, 'SB')
        btn_pct_str = f"{btn_pct:.0f}%" if btn_pct is not None else "—"
        sb_pct_str  = f"{sb_pct:.0f}%"  if sb_pct  is not None else "—"
        direction   = "ベット" if cbs >= THRESHOLD_BTN else "チェック"
        lines.append(f"| {label} | {hp} | {draw_type} | {cbs} | {btn_pct_str} | {sb_pct_str} | {direction} |")

    lines.append("")
    lines.append("> **閾値**: BTN は CBS≥5 でベット方向、SB/LIMP は CBS≥7 でベット方向。")
    lines.append("")
    return "\n".join(lines)

def render_cbs_examples(section: dict) -> str:
    """Generate CBS examples table with actual GTO data."""
    title = section.get('title', 'CBS計算例')
    examples = section.get('examples', [])
    lines = [f"### {title}", ""]
    lines.append("| ハンド | ボード | 手の種別 | HP | DP | CBS | 閾値 | GTO実測% | 判断 |")
    lines.append("|------|------|---------|----|----|-----|------|---------|------|")

    for ex in examples:
        hand      = ex.get('hand', '')
        board     = ex.get('board', '')
        hand_type = ex.get('hand_type', '')
        draw_type = ex.get('draw_type', 'no_draw')
        scenario  = ex.get('scenario', 'BTN')
        label     = ex.get('label', '')
        threshold_label = ex.get('threshold', 'BTN(5)')

        hp = HP_TABLE.get(hand_type, 0)
        dp = DP_TABLE.get(draw_type, 0)
        if hand_type == 'no_made_hand' and draw_type == 'oesd':
            cbs = hp - 2
        else:
            cbs = hp + dp

        if scenario == 'BTN':
            thresh = THRESHOLD_BTN
        elif scenario == 'LIMP':
            thresh = THRESHOLD_LIMP
        else:
            thresh = THRESHOLD_SB

        gto_pct = gto_avg(hand_type, draw_type, scenario)
        gto_str = f"{gto_pct:.0f}%" if gto_pct is not None else "—"
        direction = "ベット✓" if cbs >= thresh else "チェック"

        lines.append(f"| {hand} | {board} | {label} | {hp} | {dp} | {cbs} | {threshold_label} | {gto_str} | {direction} |")

    lines.append("")
    return "\n".join(lines)

def render_confidence_examples(section: dict) -> str:
    """Show same hand on dry vs wet board (HIGH vs LOW confidence)."""
    title = section.get('title', 'コンフィデンス例')
    cases = section.get('cases', [])
    lines = [f"### {title}", ""]

    for case in cases:
        hand_type  = case.get('hand_type', 'second_pair')
        draw_type  = case.get('draw_type', 'no_draw')
        boards     = case.get('boards', [])
        scenario   = case.get('scenario', 'BTN')
        hand_label = case.get('hand_label', '')

        if scenario == 'BTN':
            thresh = THRESHOLD_BTN
        elif scenario == 'LIMP':
            thresh = THRESHOLD_LIMP
        else:
            thresh = THRESHOLD_SB
        cbs    = calc_cbs(hand_type, draw_type)
        dist   = abs(cbs - thresh)
        is_bet = bet_direction(cbs, thresh)

        gto_pct = gto_avg(hand_type, draw_type, scenario)
        gto_str = f"GTO実測: {gto_pct:.0f}%" if gto_pct is not None else ""

        lines.append(f"**{hand_label}** (CBS={cbs}, 距離={dist}, {gto_str})")
        lines.append("")
        lines.append("| ボード | ボード型 | コンフィデンス | ベット頻度目安 |")
        lines.append("|------|---------|--------------|-------------|")

        for b in boards:
            board_id   = b.get('board_id', '')
            board_type = classify_board(board_id)
            conf       = calc_confidence(cbs, thresh, board_type)
            freq_key   = (conf, is_bet)
            freq       = FREQ_TABLE.get(freq_key, 50)
            lines.append(f"| {b.get('label','')}{board_id} | 型{board_type} | {conf} | {freq}% |")

        lines.append("")

    return "\n".join(lines)

def render_commit_table(section: dict) -> str:
    """SPR × commit HS table."""
    title = section.get('title', 'コミットライン（SPR別）')
    rows  = section.get('rows', [])
    lines = [f"### {title}", ""]
    lines.append("| SPR | コミット最低HS | 手の例 | バブル補正 | バブル最低HS |")
    lines.append("|-----|------------|------|---------|-----------|")

    for row in rows:
        spr   = row.get('spr', '')
        hs    = row.get('hs', '')
        hand  = row.get('hand', '')
        bub   = row.get('bubble_adj', '+10HS')
        bubble_hs = row.get('bubble_hs', '')
        lines.append(f"| {spr} | {hs} | {hand} | {bub} | {bubble_hs} |")

    lines.append("")
    return "\n".join(lines)

def render_icm_table(section: dict) -> str:
    """Stage × ICM correction table."""
    title = section.get('title', 'ステージ別ICM補正')
    rows  = section.get('rows', [])
    lines = [f"### {title}", ""]
    lines.append("| ステージ | ICM補正 | コール閾値効果 | エアーCBet | まとめ |")
    lines.append("|--------|--------|------------|----------|------|")

    for row in rows:
        stage   = row.get('stage', '')
        icm     = row.get('icm', '')
        call_eff = row.get('call_effect', '')
        air     = row.get('air_cbet', '')
        summary = row.get('summary', '')
        lines.append(f"| {stage} | {icm} | {call_eff} | {air} | {summary} |")

    lines.append("")
    return "\n".join(lines)

def render_quiz(section: dict) -> str:
    """Quiz questions with answer key."""
    title     = section.get('title', 'クイズ')
    questions = section.get('questions', [])
    lines     = [f"### {title}", ""]

    for i, q in enumerate(questions, 1):
        setup  = q.get('setup', '')
        ask    = q.get('question', '')
        answer = q.get('answer', '')
        reason = q.get('reason', '')
        lines.append(f"**Q{i}.** {setup}")
        lines.append(f"  → {ask}")
        lines.append("")

    lines.append("---")
    lines.append("**解答**")
    lines.append("")
    for i, q in enumerate(questions, 1):
        answer = q.get('answer', '')
        reason = q.get('reason', '')
        lines.append(f"**A{i}.** {answer}")
        if reason:
            lines.append(f"  （理由: {reason}）")
        lines.append("")

    return "\n".join(lines)

def render_3bp_table(section: dict) -> str:
    """3BP postflop decision tables for OOP and IP."""
    title = section.get('title', '3BPポストフロップ判断表')
    lines = [f"### {title}", ""]

    data = get_gto_data()

    # OOP table
    lines.append("#### OOP（3ベット側）: 「ナッツだけチェック」")
    lines.append("")
    lines.append("| カテゴリ | ハンド | 行動 | GTO実測% |")
    lines.append("|--------|------|------|---------|")

    oop_nut_hands = [
        ('set', 'no_draw'), ('two_pair', 'no_draw'), ('straight', 'no_draw'),
    ]
    oop_bet_hands = [
        ('overpair', 'no_draw'), ('top_pair', 'no_draw'), ('underpair', 'no_draw'),
        ('no_made_hand', 'no_draw'), ('ace_high', 'no_draw'), ('trips', 'no_draw'),
    ]

    hand_labels = {
        'set': 'セット', 'two_pair': 'ツーペア', 'straight': 'ストレート',
        'overpair': 'オーバーペア', 'top_pair': 'トップペア', 'underpair': 'アンダーペア',
        'no_made_hand': 'エアー', 'ace_high': 'Aハイ', 'king_high': 'Kハイ',
        'trips': 'トリップス', 'second_pair': 'セカンドペア', 'third_pair': 'サードペア',
        'low_pair': 'ローペア',
    }

    for ht, dt in oop_nut_hands:
        pct = data.get('3BP_OOP', {}).get(f"{ht}|{dt}")
        pct_str = f"{pct:.0f}%" if pct is not None else "—"
        lines.append(f"| ナッツ（CHECK） | {hand_labels.get(ht, ht)} | チェック（CR） | {pct_str} |")
    for ht, dt in oop_bet_hands:
        pct = data.get('3BP_OOP', {}).get(f"{ht}|{dt}")
        pct_str = f"{pct:.0f}%" if pct is not None else "—"
        lines.append(f"| 非ナッツ（CBet） | {hand_labels.get(ht, ht)} | CBet | {pct_str} |")

    lines.append("")
    lines.append("> **精度: 74%** (CBS比+21pt) | GTO平均CBet: 非ナッツ74.5%")
    lines.append("")

    # IP table
    lines.append("#### IP（コール側）: 「アーチ型ベット」")
    lines.append("")
    lines.append("| カテゴリ | ハンド | 行動 | GTO実測% |")
    lines.append("|--------|------|------|---------|")

    ip_rows = [
        ('撤退帯',  'CHECK（諦め）',   [('no_made_hand','no_draw'),('ace_high','no_draw'),('king_high','no_draw'),('low_pair','no_draw')]),
        ('価値帯',  'BET（価値）',    [('third_pair','no_draw'),('second_pair','no_draw'),('underpair','no_draw'),('top_pair','no_draw'),('trips','no_draw')]),
        ('トラップ帯', 'CHECK（罠）', [('overpair','no_draw'),('set','no_draw'),('straight','no_draw')]),
        ('Kハイ+OESD', 'BET（エクイティ）', [('king_high','oesd')]),
    ]

    for cat_name, action, hands in ip_rows:
        for ht, dt in hands:
            pct = data.get('3BP_IP', {}).get(f"{ht}|{dt}")
            pct_str = f"{pct:.0f}%" if pct is not None else "—"
            lines.append(f"| {cat_name} | {hand_labels.get(ht,ht)}{'(+OESD)' if dt=='oesd' else ''} | {action} | {pct_str} |")

    lines.append("")
    lines.append("> **精度: 70%** (CBS比+17pt)")
    lines.append("")

    return "\n".join(lines)


def render_defense_conf_table(section: dict) -> str:
    """OOP CR Confidence by board type (Ace Dominance Principle)."""
    title    = section.get('title', 'OOP守備：エース支配原理によるCR信頼度')
    scenario = section.get('scenario', 'SRP25_OOP')
    lines    = [f"### {title}", ""]

    lines.append("| ボード型 | 代表例 | OOPのTP種別 | 守備Conf | top_pair CR% | 行動指針 |")
    lines.append("|---------|------|-----------|---------|------------|--------|")

    board_rows = [
        (1, "A72r",  "TPTK",  "A保有 ≈ ナッツ → AA のみ上回る"),
        (2, "K98r",  "TPMK",  "AA(6)+AK(9+) に支配される"),
        (3, "T98r",  "TPWK",  "ドロー多 → CR でポット膨張はリスク"),
        (4, "765r",  "TPWK",  "同上"),
        (5, "J73r",  "TPMK",  "AA/KK/AK 多数に支配される"),
        (6, "742r",  "TPWK",  "全オーバーカードに支配される"),
        (7, "KK8",   "—",     "second_pair が例外的にCR有効"),
    ]

    for bt, board_ex, tp_name, reason in board_rows:
        conf    = calc_defense_confidence(bt)
        cr_pct  = defense_cr_avg('top_pair', 'no_draw', bt, scenario)
        cr_str  = f"**{cr_pct:.1f}%**" if cr_pct is not None else "—"
        action  = "**CR（即守備）**" if conf == 'HIGH' else (
                  "コール（トラップ）"   if conf == 'LOW' else "混合（特殊）")
        lines.append(
            f"| 型{bt}　{board_ex} | {tp_name} | {reason} | **{conf}** | {cr_str} | {action} |"
        )

    lines.append("")
    lines.append(
        "> **エース支配原理**：Aがボード上 → OOPのTPはほぼナッツ → コールトラップ。"
        "非A高ドライ → OOPのTPはAA/AKに支配 → 即CR。ウェット → ドロー多でポット管理。"
    )
    lines.append("")
    return "\n".join(lines)


def render_defense_examples(section: dict) -> str:
    """OOP CR decision examples: hand × board_type → CR / call / fold."""
    title    = section.get('title', 'OOP守備の判断例')
    examples = section.get('examples', [])
    scenario = section.get('scenario', 'SRP25_OOP')
    spr_scen = section.get('spr_scenario', 'SRP25')
    lines    = [f"### {title}", ""]

    default_opener = section.get('opener', 'btn')

    lines.append(f"| ハンド | ボード | 種別 | HP | 守備Conf | 行動（vs {default_opener.upper()}） | GTO R/C/F% |")
    lines.append("|------|------|-----|----|---------|--------------------|------------|")

    data = get_defense_data()
    for ex in examples:
        hand       = ex.get('hand', '')
        board      = ex.get('board', '')
        hand_type  = ex.get('hand_type', '')
        draw_type  = ex.get('draw_type', 'no_draw')
        board_type = ex.get('board_type', 0)
        label      = ex.get('label', hand_type)
        spr_s      = ex.get('spr_scenario', spr_scen)
        opener     = ex.get('opener', default_opener)

        hp       = HP_TABLE.get(hand_type, 0)
        conf     = calc_defense_confidence(board_type)
        cr_thr   = calc_cr_threshold(board_type, spr_s)
        fold_pred = should_fold(hand_type, draw_type, board_type, opener)

        # 3択判定: フォールド → CR → コール
        if fold_pred:
            action = "**フォールド**"
        elif conf == 'SPECIAL':
            action = "ペア板ルール参照"
        elif hp >= cr_thr and conf == 'HIGH':
            action = "**CR**"
        elif hp >= cr_thr and conf == 'LOW':
            action = "コール（トラップ）"
        elif conf == 'HIGH' and hp < cr_thr:
            action = "コール（CR閾値未満）"
        else:
            action = "コール"

        # GTO 実測 R/C/F% — opener に応じたシナリオから取得
        key = f"{hand_type}|{draw_type}"
        scs = OPENER_TO_SCENARIOS.get(opener, [scenario])
        f_sum = c_sum = r_sum = n_sum = 0.0
        for sc in scs:
            entry = data.get(sc, {}).get(board_type, {}).get(key)
            if entry and entry['n'] > 0:
                f_sum += entry['fold_pct'] * entry['n']
                c_sum += entry['call_pct'] * entry['n']
                r_sum += entry['raise_pct'] * entry['n']
                n_sum += entry['n']
        if n_sum > 0:
            gto_str = f"R={r_sum/n_sum:.0f}% C={c_sum/n_sum:.0f}% F={f_sum/n_sum:.0f}%"
        else:
            gto_str = "—"

        lines.append(
            f"| {hand} | {board} | {label} | {hp} | {conf} | {action} | {gto_str} |"
        )

    lines.append("")
    return "\n".join(lines)


def render_defense_opener_compare(section: dict) -> str:
    """同じハンド×板で複数 opener の判定とGTO実測を並べて比較する renderer."""
    title = section.get('title', '同一ハンド・同一ボードでの opener 別判定')
    lines = [f"### {title}", ""]
    data = get_defense_data()

    examples = section.get('examples', [])
    opener_order = section.get('openers', ['utg','hj','co','btn','sb'])

    header = "| ハンド | ボード | 型 | 種別 |" + "|".join(f' vs {o.upper()} ' for o in opener_order) + "|"
    sep    = "|------|------|----|-----|" + "|".join('--------' for _ in opener_order) + "|"
    lines.append(header)
    lines.append(sep)

    for ex in examples:
        hand       = ex.get('hand', '')
        board      = ex.get('board', '')
        hand_type  = ex.get('hand_type', '')
        draw_type  = ex.get('draw_type', 'no_draw')
        board_type = ex.get('board_type', 0)
        label      = ex.get('label', hand_type)

        row = f"| {hand} | {board} | 型{board_type} | {label} |"
        for op in opener_order:
            scs = OPENER_TO_SCENARIOS.get(op, [])
            key = f"{hand_type}|{draw_type}"
            f_sum = n_sum = 0.0
            for sc in scs:
                entry = data.get(sc, {}).get(board_type, {}).get(key)
                if entry and entry['n'] > 0:
                    f_sum += entry['fold_pct'] * entry['n']
                    n_sum += entry['n']
            actual_f = (f_sum/n_sum) if n_sum > 0 else None
            pred_fold = should_fold(hand_type, draw_type, board_type, op)
            pred_str = "F" if pred_fold else "C"
            if actual_f is None:
                cell = f" {pred_str}/  — "
            else:
                mark = '●' if actual_f >= 60 else ('○' if actual_f >= 30 else ' ')
                cell = f" {pred_str}/{mark}{actual_f:>2.0f}%"
            row += f" {cell} |"
        lines.append(row)

    lines.append("")
    lines.append("> **読み方**: `予測/実測` の形式。`F=フォールド`, `C=コール`, ●≥60%fold, ○30-60%, 空白<30%")
    lines.append("")
    return "\n".join(lines)


def render_defense_position_matrix(section: dict) -> str:
    """OOP defense fold matrix by individual opener position (7-way)."""
    title = section.get('title', 'OOP守備 — オープナー別 fold% 詳細マトリクス')
    lines = [f"### {title}", ""]
    data = get_defense_data()

    # 個別 opener × シナリオ（左→右で tight→HU 方向）
    position_order = section.get('openers', ['utg','utg1','lj','hj','co','btn','sb'])
    positions = [(op.upper(), OPENER_TO_SCENARIOS.get(op, [])) for op in position_order]

    def fpct(scs, ht, dt, bt):
        f_sum = n_sum = 0
        for sc in scs:
            entry = data.get(sc, {}).get(bt, {}).get(f'{ht}|{dt}')
            if entry and entry['n'] > 0:
                f_sum += entry['fold_pct'] * entry['n']
                n_sum += entry['n']
        return (f_sum/n_sum) if n_sum > 0 else None

    def cell(f):
        if f is None: return ' —  '
        mark = '●' if f >= 60 else ('○' if f >= 30 else ' ')
        return f'{mark}{f:>2.0f}%'

    rows = section.get('rows', [])
    if not rows:
        rows = [
            ('Aハイ',         'ace_high',     'no_draw',       2),
            ('Aハイ',         'ace_high',     'no_draw',       5),
            ('Aハイ',         'ace_high',     'no_draw',       6),
            ('Kハイ',         'king_high',    'no_draw',       1),
            ('Kハイ',         'king_high',    'no_draw',       5),
            ('Kハイ',         'king_high',    'no_draw',       6),
            ('Kハイ',         'king_high',    'no_draw',       7),
            ('Kハイ+BDFD',    'king_high',    'twocards_bdfd', 1),
            ('Kハイ+BDFD',    'king_high',    'twocards_bdfd', 4),
            ('Aハイ+BDFD',    'ace_high',     'twocards_bdfd', 5),
            ('純エアー+BDFD', 'no_made_hand', 'twocards_bdfd', 6),
            ('純GS',          'no_made_hand', 'gutshot',       4),
            ('OESD',          'no_made_hand', 'oesd',          3),
            ('2ndペア',       'second_pair',  'no_draw',       3),
            ('2ndペア',       'second_pair',  'no_draw',       4),
            ('3rdペア',       'third_pair',   'no_draw',       1),
            ('3rdペア',       'third_pair',   'no_draw',       3),
            ('3rdペア',       'third_pair',   'no_draw',       4),
        ]

    header = "| ハンド | 型 |" + "|".join(f' {p:^5} ' for p,_ in positions) + "|"
    sep    = "|------|----|" + "|".join('-------' for _ in positions) + "|"
    lines.append(header)
    lines.append(sep)

    for label, ht, dt, bt in rows:
        row = f"| {label} | 型{bt} |"
        for _, scs in positions:
            f = fpct(scs, ht, dt, bt)
            row += f" {cell(f)} |"
        lines.append(row)

    lines.append("")
    lines.append("> **記号**: ●=fold優位(F≥60%) ○=混合(30-60%) 空白=コール優位(F<30%)")
    lines.append("> 読み方: 左→右で相手 open 位置が UTG（tight）→ SB（HU）に変化")
    lines.append("")
    return "\n".join(lines)


def render_3bp_defense(section: dict) -> str:
    """3BP is_pair based defense table for OOP or IP."""
    title = section.get('title', '3BPフロップ守備（is_pair ルール）')
    side  = section.get('side', 'OOP')  # 'OOP' or 'IP'
    lines = [f"### {title}", ""]
    get_defense_data()  # pre-load

    hand_labels = {
        'no_made_hand': 'エアー',    'ace_high':   'Aハイ',
        'king_high':    'Kハイ',     'low_pair':   'ローペア',
        'third_pair':   'サードペア', 'second_pair': 'セカンドペア',
        'underpair':    'アンダーペア','top_pair':   'トップペア',
        'overpair':     'オーバーペア','two_pair':   'ツーペア',
        'set':          'セット',     'trips':      'トリップス',
        'fullhouse':    'フルハウス',  'straight':   'ストレート',
    }

    if side == 'OOP':
        scenario = '3BP20_OOP'
        lines.append(
            "OOP（3ベット側）がIPのCBetに応答する局面。SPR≈2.2のコミット圏。"
            "CBS（HPスコア）は機能しないため **is_pair フラグ** で判断します。"
        )
        lines.append("")
        lines.append("> **WRMSE=30.5%**（常時50%=38.2%を上回る最良ルール）")
        lines.append("")
        lines.append("| is_pair | ハンド | HP | 行動 | GTO CR% |")
        lines.append("|--------|------|----|------|---------|")

        rows = [
            (False, 'no_made_hand', 'no_draw',  'フォールド'),
            (False, 'ace_high',     'no_draw',  'フォールド'),
            (False, 'king_high',    'no_draw',  'フォールド'),
            (True,  'underpair',    'no_draw',  'CR（コミット）'),
            (True,  'second_pair',  'no_draw',  'CR（コミット）'),
            (True,  'top_pair',     'no_draw',  'CR（コミット）'),
            (True,  'overpair',     'no_draw',  'CR（コミット）'),
            (None,  'set',          'no_draw',  'コール（スロープレイ）'),
            (None,  'two_pair',     'no_draw',  '混合（ボード型依存）'),
        ]

        for is_pair, ht, dt, action in rows:
            hp = HP_TABLE.get(ht, 0)
            avg_cr = defense_cr_avg_all_types(ht, dt, scenario)
            gto_str = f"CR={avg_cr:.0f}%" if avg_cr is not None else "—"
            flag = "✓" if is_pair is True else ("✗" if is_pair is False else "—")
            lines.append(
                f"| {flag} | {hand_labels.get(ht, ht)} | {hp} | {action} | {gto_str} |"
            )

    elif side == 'IP':
        scenario = '3BP20_IP'
        lines.append(
            "IP（コール側）がOOPのリードに応答する局面。SPR低 → 基本トラップ戦略。"
        )
        lines.append("")
        lines.append("**原則: 全ハンドでコール（トラップ）。型5/6 × HP≥5 のみCR有効。**")
        lines.append("")
        lines.append("| スコープ | ハンド | HP | 行動 | GTO CR% |")
        lines.append("|--------|------|----|------|---------|")

        rows = [
            ('全型',   'no_made_hand', 'no_draw', 'フォールド'),
            ('全型',   'ace_high',     'no_draw', 'フォールド'),
            ('全型',   'top_pair',     'no_draw', 'コール（トラップ）'),
            ('全型',   'overpair',     'no_draw', 'コール（ディープトラップ）'),
            ('全型',   'set',          'no_draw', 'コール（ディープトラップ）'),
            ('型5/6',  'underpair',    'no_draw', 'CR有効（脆弱TP保護）'),
            ('型5/6',  'second_pair',  'no_draw', 'CR有効（脆弱TP保護）'),
        ]

        for scope, ht, dt, action in rows:
            hp = HP_TABLE.get(ht, 0)
            # 型5/6スコープは型5・6限定の平均を使う（全型平均だと希釈される）
            if scope == '型5/6':
                avg_cr = defense_cr_avg_types(ht, dt, (5, 6), scenario)
            else:
                avg_cr = defense_cr_avg_all_types(ht, dt, scenario)
            gto_str = f"{avg_cr:.0f}%" if avg_cr is not None else "—"
            lines.append(
                f"| {scope} | {hand_labels.get(ht, ht)} | {hp} | {action} | {gto_str} |"
            )

    lines.append("")
    return "\n".join(lines)


def render_summary_card(items: list) -> str:
    lines = ["---", ""]
    lines.append("## まとめカード")
    lines.append("")
    for item in items:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)

# ─── Section Dispatcher ───────────────────────────────────────────────────────
def render_section(section: dict) -> str:
    stype = section.get('type', 'text')
    if stype == 'text':
        return render_text(section)
    elif stype == 'hp_table':
        return render_hp_table(section)
    elif stype == 'cbs_examples':
        return render_cbs_examples(section)
    elif stype == 'confidence_examples':
        return render_confidence_examples(section)
    elif stype == 'commit_table':
        return render_commit_table(section)
    elif stype == 'icm_table':
        return render_icm_table(section)
    elif stype == 'quiz':
        return render_quiz(section)
    elif stype == '3bp_table':
        return render_3bp_table(section)
    elif stype == 'defense_conf_table':
        return render_defense_conf_table(section)
    elif stype == 'defense_examples':
        return render_defense_examples(section)
    elif stype == 'defense_position_matrix':
        return render_defense_position_matrix(section)
    elif stype == 'defense_opener_compare':
        return render_defense_opener_compare(section)
    elif stype == '3bp_defense':
        return render_3bp_defense(section)
    else:
        return f"<!-- Unknown section type: {stype} -->\n"

# ─── Chapter Generator ────────────────────────────────────────────────────────
def generate_chapter(spec_path: Path) -> None:
    with open(spec_path) as f:
        spec = yaml.safe_load(f)

    ch_num  = spec.get('chapter_num', '')
    title   = spec.get('title', '')
    slug    = spec.get('slug', spec_path.stem)
    output  = spec.get('output', f"chapters/{slug}.md")
    summary = spec.get('summary', '')

    output_path = BASE_DIR / output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()

    # Build chapter header
    ch_num_str = str(ch_num)
    if not ch_num_str or ch_num_str.startswith('付') or ch_num_str == '0':
        header = f"# {title}"
    else:
        header = f"# 第{ch_num_str}章　{title}"

    parts = []
    parts.append(f"<!-- Auto-generated by generator.py on {today} -->")
    parts.append("")
    parts.append(header)
    parts.append("")
    parts.append("<!-- markdownlint-disable MD026 MD033 MD036 MD040 MD060 -->")
    parts.append("")

    if summary:
        parts.append(summary.strip())
        parts.append("")
        parts.append("---")
        parts.append("")

    # Render sections
    for section in spec.get('sections', []):
        rendered = render_section(section)
        if rendered.strip():
            parts.append(rendered.strip())
            parts.append("")

    # Summary card
    summary_card = spec.get('summary_card', [])
    if summary_card:
        parts.append(render_summary_card(summary_card).strip())
        parts.append("")

    content = "\n".join(parts) + "\n"
    output_path.write_text(content, encoding='utf-8')
    print(f"  ✓ Generated: {output_path.relative_to(BASE_DIR)}")

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Pre-load GTO data
    print("Loading GTO data...")
    data = get_gto_data()
    total = sum(len(v) for v in data.values())
    print(f"  Loaded {total} hand×draw×scenario combinations (attack)")

    print("Loading defense data...")
    defense_data = get_defense_data()
    def_total = sum(
        sum(len(hd) for hd in bd.values())
        for bd in defense_data.values()
    )
    print(f"  Loaded {def_total} hand×draw×board_type combinations ({len(defense_data)} scenarios)")
    print()

    if len(sys.argv) > 1:
        # Single spec file
        spec_path = Path(sys.argv[1])
        if not spec_path.is_absolute():
            spec_path = Path.cwd() / spec_path
        print(f"Generating chapter from {spec_path}...")
        generate_chapter(spec_path)
    else:
        # All specs in specs/mtt/
        specs = sorted(SPECS_DIR.glob("ch*.yaml")) + sorted(SPECS_DIR.glob("appendix*.yaml"))
        if not specs:
            print(f"No YAML specs found in {SPECS_DIR}")
            sys.exit(1)
        print(f"Generating {len(specs)} chapters from {SPECS_DIR}...")
        print()
        for spec_path in specs:
            generate_chapter(spec_path)

    print()
    print("Done.")

if __name__ == '__main__':
    main()
