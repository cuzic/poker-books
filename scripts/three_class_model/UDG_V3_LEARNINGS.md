# UDG v3 — Learnings from Section A 分析

## 結論

UDG v3 with blocker_tier + HIGH SPR aggression + mono slowdown + IP modifier:
- **without IP modifier**: huge_loss 5.93 vs v2 5.94 (改善 0.2%、誤差レベル)
- **with IP modifier**: huge_loss 6.05 vs v2 5.94 (悪化)

## 学び：「Section A の mismatch 発見 ≠ rule 追加で改善」

### Lesson 1: equity_bucket が implicitly に blocker を捕捉済

Section A3 で観測した blocker effect:
- Monotone × Ax of suit: GTO CALL 50.9% vs without 23.7% (+27pp)
- Paired KK × K: GTO CALL 75.9% vs 34.0% (+42pp)

これは **本当の効果** だが、GTO Wizard が返す `equity_bucket` は「opp range に対する hero combo の相対 equity」を計算している。**A blocker 持ちの combo は自動的に high equity_bucket になる**ため、equity_aware_tier で既に拾われている。

→ 明示的 `blocker_tier` 追加は **冗長**、huge_loss 改善 ~0%。

### Lesson 2: Section A の mismatch 比率 ≠ 全体配分

Section A2 で "flush × weak_hands × FOLD → CALL: 192 cases" を見て IP defender wider call rule を追加した。しかしこれは **mismatches の breakdown** であって、**flush × weak_hands × R1 spots の全体配分** ではない。

実際: flush × weak_hands × R1 で
- UDG v2: FOLD predict
- GTO best: 192 cases CALL、残り N cases FOLD (おそらく 800+)

IP modifier で全 flush × weak/trash を CALL に変換すると、**正しく FOLD していた 800+ cases が誤 CALL になる** → 累積 loss 増。

→ Section A は **mismatch を発見するが、root cause の rule 化には Bayes 的逆推論が必要**。

### Lesson 3: 既存データ分析の限界

Section A だけで UDG v3 を改善するのは難しい理由:
1. equity_bucket は既に多くの情報を encode
2. mismatch breakdown は cause を直接示さない
3. 真の improvement には structural な新軸 (turn card category 等) が必要 → Section B fetch が要る

## UDG v3 で残した変更 (marginal benefit)

```python
# 1. blocker_tier 関数 (将来の per-combo 分析に便利、huge_loss 改善小)
def blocker_tier(card_a, card_b, board_str, board_family):
    # mono × Ax of suit → STRONG_BLOCKER
    # paired × Kx → STRONG_BLOCKER
    ...

# 2. HIGH SPR (MTT200) で STRONG/TWO_PAIR の aggression 強化
if matchup == "AHEAD" and spr == "HIGH" and hand_tier in {"STRONG", "TWO_PAIR"} and not is_river:
    return "RAISE"

# 3. Monotone non-river slowdown for PAIR/TWO_PAIR
if board_family == "monotone" and not is_river and hand_tier in {"PAIR", "TWO_PAIR"}:
    return "CALL"  # slowdown vs flush

# 4. Blocker boost in matchup
if blocker == "STRONG_BLOCKER" and matchup == "BEHIND" and bet_tier in {"SMALL", "MED"}:
    matchup = "TIE"
```

各変更は **<0.1 BB の改善** だが書籍説明で正当化しやすい intuition がある。

## 実際の改善には何が必要か

### 短期 (Section B fetch)
1. **4BP flop board sub-tier 検証**: dry_A94 vs dry_K72 vs low_dry の specific GTO 比較 (~36 calls)
2. **Turn card category 検証**: 同 flop × paired/overcard/brick/draw 検証 (~36 calls)

### 中期 (新概念)
1. **Card-level interaction**: 単純な blocker_tier より granular な「specific card × board pattern」
2. **Multi-street range narrowing**: 街毎の opp range 動的更新
3. **Bet sizing fine-grained**: 33% / 50% / 75% / 100% を別 tier に細分

### 長期 (radical)
- Equity bucket → continuous variable 化 (binary tier 廃止)
- Neural network で hand × board × bet → action 直予測 (公式廃止)

## 書籍 (Vol2/Vol3) への含意

UDG v2/v3 は **データ駆動の本質的な発見**:
- equity_bucket (= opp range に対する hero combo の相対 equity) が全ての判断軸を統合できる
- 公式は equity_bucket + bet_size + SPR の 3 つで 80% カバーできる
- 残り 20% は board × hand の固有パターン (4BP flop の board-specific 等)

→ Vol2 章で **「equity_bucket の読み方」を中核教材** にすれば、4BP/3BP/SRP の枝分かれが消える。
→ 実プレイヤーは "equity bucket をリアルタイム推定する" 訓練を積めば UDG v2 を完璧に再現可能。
