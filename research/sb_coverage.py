#!/usr/bin/env python3
"""
sb_coverage.py — SB postflop の既存データ網羅性を詳細検証

SB が関与する postflop シナリオ:
  1. SB open → BB call → SB cbet (BvB SRP)
  2. SB open → BB 3bet → SB call (BvB 3BP)
  3. SB squeeze (vs UTG/HJ/CO/BTN + caller) postflop
  4. Cold call SB cold-call → IP raisers vs SB 3-way (multiway)

各シナリオで:
  - flop / turn / river のどこまで既存データがあるか
  - actor が誰か (SB cbet / BB call back / etc)
  - depth 別 (Cash 100, MTT 25/50/100, Cash 200)
"""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path.home() / "poker-books"


def analyze_file(p: Path) -> dict | None:
    try:
        with open(p) as f:
            data = json.load(f) if p.suffix == ".json" else json.loads(f.readline())
    except Exception:
        return None
    game = data.get("game", {})
    players = game.get("players", [])
    acts = data.get("action_solutions", [])

    chips = {p.get("position", "?"): float(p.get("chips_on_table", "0") or 0) for p in players}
    stacks_orig = {p.get("position", "?"): float(p.get("stack", "0") or 0) for p in players}
    actor = acts[0].get("action", {}).get("position", "?") if acts else "?"
    board = game.get("board", "")
    n_players_active = sum(1 for p in players if not p.get("is_folded", True))

    # Board length → phase
    blen = len(board) if board else 0
    phase = "preflop" if blen == 0 else ("flop" if blen == 6 else ("turn" if blen == 8 else ("river" if blen >= 10 else "?")))

    # depth
    depth = max(stacks_orig.values()) if stacks_orig else 0

    # SB が opener か? (chips_on_table が SB のみ blind 0.5 を超えており、他に raise した人がいない)
    # 検出ロジック: chips の最大値 が SB の値と一致し、それが BB の chips 以上なら SB opener
    sb_chips = chips.get("SB", 0)
    bb_chips = chips.get("BB", 0)
    btn_chips = chips.get("BTN", 0)
    co_chips = chips.get("CO", 0)
    hj_chips = chips.get("HJ", 0)
    utg_chips = chips.get("UTG", 0)

    # 投入額順
    max_chips = max(chips.values()) if chips else 0
    contenders = [pos for pos, v in chips.items() if abs(v - max_chips) < 0.01]

    sb_is_opener = (sb_chips > 0.6 and  # SB は 0.5 blind を超えて raise
                    btn_chips < 0.5 and co_chips < 0.5 and
                    hj_chips < 0.5 and utg_chips < 0.5 and
                    bb_chips < sb_chips - 0.5)  # BB がまだ blind 1 BB のみ、または SB に合わせて call/raise

    sb_in_pot = sb_chips >= 1.0  # SB が何らかの形で参加

    # SB が「BB と single raised pot で対戦」(SB_BB SRP)
    sb_bb_srp = (sb_in_pot and bb_chips > 0 and
                 btn_chips < 0.5 and co_chips < 0.5 and hj_chips < 0.5 and utg_chips < 0.5)

    # SB が「3BP / 4BP」(別の player も raise した)
    raises_count = sum(1 for pos, v in chips.items() if v > (1.0 if pos == "BB" else (0.5 if pos == "SB" else 0)))

    return {
        "path": str(p.relative_to(ROOT)),
        "phase": phase,
        "depth": int(depth),
        "actor": actor,
        "sb_chips": sb_chips,
        "bb_chips": bb_chips,
        "sb_is_opener": sb_is_opener,
        "sb_bb_srp": sb_bb_srp,
        "sb_in_pot": sb_in_pot,
        "raises_in_pot": raises_count,
        "n_active": n_players_active,
    }


def main():
    paths = []
    for d in [ROOT/"vol2-cash-postflop"/"findings",
              ROOT/"vol3-mtt-postflop"/"findings",
              ROOT/"research"/"v3-additional"/"findings"]:
        if d.exists():
            paths.extend(d.rglob("*.json"))

    sb_files = []
    for p in paths:
        info = analyze_file(p)
        if not info:
            continue
        # SB が関与する postflop のみ
        if info["phase"] in ("preflop", "?"):
            continue
        if not info["sb_in_pot"]:
            continue
        sb_files.append(info)

    print(f"# SB postflop データ網羅性検証")
    print()
    print(f"**SB が関与する postflop ファイル数**: {len(sb_files)}")
    print()

    # ── 1. SB BvB SRP (SB open, BB call, no other) ──
    sb_bb_srp = [f for f in sb_files if f["sb_bb_srp"]]
    print("## 1. SB-BB BvB SRP postflop (SB open → BB call)")
    print()
    print(f"ファイル数: {len(sb_bb_srp)}")
    by_phase_depth = defaultdict(int)
    by_actor = defaultdict(int)
    for f in sb_bb_srp:
        by_phase_depth[(f["phase"], f["depth"])] += 1
        by_actor[f["actor"]] += 1
    print()
    print("| Phase | Depth | ファイル数 |")
    print("|-------|-------|---------|")
    for (phase, depth), n in sorted(by_phase_depth.items()):
        print(f"| {phase} | {depth} bb | {n} |")
    print()
    print("| Actor | ファイル数 |")
    print("|-------|---------|")
    for actor, n in sorted(by_actor.items(), key=lambda x: -x[1]):
        print(f"| {actor} | {n} |")
    print()

    # ── 2. SB が postflop で raise pot に参加 (3BP / 4BP / multiway) ──
    sb_other = [f for f in sb_files if not f["sb_bb_srp"]]
    print("## 2. SB postflop その他 (3BP / multiway 含む)")
    print()
    print(f"ファイル数: {len(sb_other)}")
    by_phase_depth_other = defaultdict(int)
    by_actor_other = defaultdict(int)
    for f in sb_other:
        by_phase_depth_other[(f["phase"], f["depth"])] += 1
        by_actor_other[f["actor"]] += 1
    print()
    print("| Phase | Depth | ファイル数 |")
    print("|-------|-------|---------|")
    for (phase, depth), n in sorted(by_phase_depth_other.items()):
        print(f"| {phase} | {depth} bb | {n} |")
    print()

    # サンプルファイルを 5 個表示
    print("### サンプルファイル (最初の 10)")
    print()
    for f in sb_other[:10]:
        print(f"- `{f['path']}` (phase={f['phase']}, depth={f['depth']}, actor={f['actor']}, raises={f['raises_in_pot']}, n_active={f['n_active']})")
    print()


if __name__ == "__main__":
    main()
