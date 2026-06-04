"""GTO Wizard strategy[169] のハンド順序マッピング。

仮説 7 (確定): 全 169 hand を high-first 表記で生成 → ASCII sort。
例: AA=80, KK=126, AKs=84, 22=0, 72o=25。
"""
HIGH = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']


def all_hands_canonical_sort() -> list[str]:
    """169 ハンドを ASCII sort で返す。GTO Wizard の strategy[] と同順序。"""
    out = []
    for i, hi in enumerate(HIGH):
        out.append(f"{hi}{hi}")
        for lo in HIGH[i+1:]:
            out.append(f"{hi}{lo}o")
            out.append(f"{hi}{lo}s")
    return sorted(out)


HANDS = all_hands_canonical_sort()
HAND_TO_INDEX = {h: i for i, h in enumerate(HANDS)}

assert len(HANDS) == 169
assert HANDS[80] == "AA", f"AA should be 80 but got {HANDS[80]}"
assert HANDS[126] == "KK", f"KK should be 126 but got {HANDS[126]}"
assert HANDS[84] == "AKs", f"AKs should be 84 but got {HANDS[84]}"
assert HANDS[0] == "22"
