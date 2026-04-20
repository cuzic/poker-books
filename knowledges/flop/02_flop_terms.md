# フロップ編 第2章：本書を読むための用語集

検索日: 2026-04-20

## 概要

フロップ編の第2章で使用する専門用語19項目について、標準的定義・使用例・初級者が混同しやすいポイントをまとめた。GTO Wizard・Upswing Poker・888poker・PokerNews等、複数の主要ストラテジーサイトの記述を参照した。

---

## 1. SPR（Stack-to-Pot Ratio）

### 定義

実効スタック ÷ フロップ開始時点のポットサイズ。有効スタックは両者のうち少ない方を使う。

**計算例**: ポット $100、両者スタック $150 と $200 → 実効スタック $150 ÷ $100 = SPR 1.5

### 境界値と意味

| SPR | 区分 | 目安 |
|-----|------|------|
| 0〜3 | 低SPR | ワンペアでスタックオフ可 |
| 3〜6 | 中SPR（決断ゾーン） | ポジション・テクスチャ・レンジで判断が変わる |
| 6〜15 | 高SPR | セット以上でないと慎重に |
| 15以上 | 超深いスタック | ドローハンドの潜在価値が大きい、複数ストリート計画が必要 |

### 初級者が混同しやすい点

- 実効スタック（少ない方）を使う点を忘れてスタック合計を使いがち
- SPR はフロップ開始時点で固定する（ベット後に再計算しない）

### 出典

- [Stack-to-Pot Ratio | GTO Wizard](https://blog.gtowizard.com/stack-to-pot-ratio/)
- [Stack To Pot Ratio | The Poker Bank](https://www.thepokerbank.com/strategy/concepts/spr/)
- [SPR in Poker | 888poker](https://www.888poker.com/magazine/strategy/spr-in-poker)

---

## 2. CBet（継続ベット / Continuation Bet）

### 定義

プリフロップで最後にレイズ（アグレッション）した側が、フロップ以降のストリートでもベットし続けること。フロップをヒットしたかどうかに関わらず打てる。

### 頻度の目安

- ヘッズアップポット：50〜70%が標準
- マルチウェイ：プレイヤー数が増えるほど頻度を下げる
- 現代（GTO寄り）：40〜60%が一般的

### Range CBet とは

保有ハンドに関わらず、「そのスポットでレンジ全体として常にベットする」戦略。ドライボード（K-7-2 レインボー等）でポジションのある側が使いやすい。

### 初級者が混同しやすい点

- ヒットしたからベット、ヒットしないからチェック、という二元論から脱却する必要がある
- マルチウェイでも同じ頻度でCBetすると過剰ブラフになる

### 出典

- [Continuation Bet | PokerNews](https://www.pokernews.com/pokerterms/continuation-bet.htm)
- [C-Bet Strategy: Frequency and Sizing | PokerRRRApp](https://www.pokerrrrapp.com/single-post/c-bet-strategy-frequency-and-sizing)
- [How Often Should You CBet? | BlackRain79](https://www.blackrain79.com/2020/02/how-often-should-you-cbet-poker.html)

---

## 3. ボードテクスチャ（ドライ／セミウェット／ウェット）

### 分類基準

フロップの3枚が両者のレンジにどれだけ「絡むか」で判断する。

| 種類 | 特徴 | 代表例 |
|------|------|--------|
| ドライ（Dry） | コネクトしにくい、ドローが少ない | K♠7♦2♣（レインボー） |
| セミウェット | 中程度のドロー可能性 | A♥8♦6♣ |
| ウェット（Wet） | ストレートドロー・フラッシュドローが豊富 | J♠8♠6♦、Q♥J♥T♣ |

### 戦略的影響

- ドライボード：CBetのフォールドエクイティが高い、ブラフが通りやすい
- ウェットボード：ドロー対応のため、相手がコールしやすく CBet の利益が下がる

### 出典

- [What Is Board Texture in Poker? | MasterClass](https://www.masterclass.com/articles/what-is-board-texture-in-poker)
- [Poker Board Textures | 888poker](https://www.888poker.com/magazine/poker-board-textures)
- [Upswing Poker: 10 Tips for Common Flop Types](https://upswingpoker.com/board-texture-tips/)

---

## 4. BDFD（バックドアフラッシュドロー / Backdoor Flush Draw）

### 定義

フロップ時点で同スーツのカードが2枚（ホールカード1枚＋コミュニティ1枚、またはホールカード2枚）あり、ターンとリバーの両方で同スーツが必要なドロー。

### アウツ換算と価値評価

- 標準的評価：**2アウツ相当**（J ハイ BDFD も同様）
- 実現確率：フロップ時点でターン・リバー両方ヒット ≈ 約4%
- 単独では通話根拠にならない（22.5:1 以上のポットオッズが必要）
- 他のエクイティ（ペア、ガットショット等）と組み合わせることでコンティニューの根拠になる

### 初級者が混同しやすい点

- 「フラッシュドロー」（1枚ターンで完成）と混同しがち
- 単独 BDFD でフロップコールするのは GTO 的に誤り

### 出典

- [MDF & Alpha | GTO Wizard](https://blog.gtowizard.com/mdf-alpha/)
- [Backdoor Flush Draw | Upswing Poker](https://upswingpoker.com/backdoor-flush-straight-draw-tips/)

---

## 5. BDSD（バックドアストレートドロー / Backdoor Straight Draw）

### 定義

フロップで3枚の連続・準連続カードが揃い、ターンとリバーで残り2枚が必要なストレートドロー。

### 種類（ギャップ数）

| 種類 | 例 | 特徴 |
|------|-----|------|
| 0-gap（ノーギャップ） | 8-7-6 | ターンでOESDに変換しやすい |
| 1-gap | 8-7-5 | 特定カード必要 |
| 2-gap | 8-6-4 | さらに制限あり |

### 価値評価

- 実現確率：約 2〜3%（ターン・リバー両方ヒット ≈ 4.2%）
- 単独では意思決定を変える根拠にはなりにくい
- ただし、コール／フォールドの境界線上でタイブレーカー的に機能する

### 初級者が混同しやすい点

- 「ガットショット（フラッシュドロー1枚で完成）」と混同しがち
- 2-gap BDSD はほぼ無価値として扱ってよい

### 出典

- [What is a BDSD? | Americas Cardroom](https://www.americascardroom.eu/how-to/poker-terms/bdsd-backdoor-straight-draw/)
- [Backdoor Draws | Upswing Poker](https://upswingpoker.com/backdoor-flush-straight-draw-tips/)

---

## 6. モノトーン（Monotone）

### 定義

フロップの3枚が**全て同じスーツ**で構成されるボード（例：K♥7♥2♥）。

### 戦略的特徴

- フラッシュ完成コンボ数が少ないため、両者のレンジが均等化されやすい
- CBet 頻度：約50%、サイズ：ポットの25〜33%が標準（小さめ）
- フラッシュドロー以外のハンドはドライ同様に折れやすい
- ハイカード入りのモノトーン（K♥7♥2♥）は SB 有利になりやすい（ナッツブロッカー効果）

### 初級者が混同しやすい点

- 「ウェット」と混同しがち（ストレートドローがなくフラッシュドローのみ）
- 4枚目の同スーツが落ちても均衡は崩れにくい

### 出典

- [Maximizing Value on Monotone Flops | GTO Wizard](https://blog.gtowizard.com/maximizing-value-on-monotone-flops/)
- [5 Expert Strategies for Monotone Flops | Upswing Poker](https://upswingpoker.com/monotone-flops-poker-strategy/)

---

## 7. ペアード（Paired Board）

### 定義

フロップに同ランクのカードが2枚落ちている状態（例：K♠K♦7♣、A♥A♦2♣）。

### 戦略的影響

- セット・フルハウス・クワッズが相手レンジに存在する可能性
- トップペア以下のハンドの相対的価値が下がる
- ナッツを持つ側（アグレッサー）のベットサイズを大きく取れる場面も

### ペアード vs 通常ボードの違い

通常ボードと比べてセット・ツーペアの組み合わせ数が変化し、レンジアドバンテージの計算が変わる。ポケットペアを多く持つ側（多くはプリフロップレイザー）が有利になりやすい。

### 出典

- [Paired Board Poker Strategy | Upswing Poker](https://upswingpoker.com/paired-board-poker-flops-strategy/)
- [How to Play Double-Paired Boards | Upswing Poker](https://upswingpoker.com/double-paired-boards/)

---

## 8. レンジアドバンテージ（Range Advantage）

### 定義

特定のボードテクスチャ上で、一方のプレイヤーのレンジ全体が持つ**平均的なエクイティ**が相手を上回っている状態。

### 具体例

A♠K♦7♥ のボードでは、プリフロップ3ベットを打ったレンジは AA・KK・AK 等を多く含み、相手レンジよりエクイティが高い → レンジアドバンテージあり。

### ナッツアドバンテージとの違い

- **レンジアドバンテージ**：レンジ全体の平均エクイティが高い
- **ナッツアドバンテージ**（次項）：最強クラスのコンボ数が多い

「ベット頻度を上げる根拠はレンジアドバンテージ、ベットサイズを大きくする根拠はナッツアドバンテージ」が目安。

### 出典

- [Range Advantage | GTO Wizard Glossary](https://gtowizard.com/glossary/range-advantage/)
- [Range Advantage | Upswing Poker](https://upswingpoker.com/nut-range-positional-advantage/)

---

## 9. ナッツアドバンテージ（Nuts Advantage）

### 定義

特定ボード上でセット・ストレート・フラッシュ等の**ナッツ級コンボ**を相手より多く保有している状態。

### 戦略的影響

- ナッツアドバンテージを持つ側はオーバーベットを使いやすい
- ナッツを表現できるため、ブラフの信憑性も上がる
- チェックレイズの根拠としても使われる

### 初級者が混同しやすい点

- レンジアドバンテージ（全体エクイティ）とナッツアドバンテージ（最強コンボ数）は別概念
- ナッツアドバンテージがなくてもレンジアドバンテージはある場合がある

### 出典

- [Nuts advantage | GTO Wizard Glossary](https://pages.gtowizard.com/en/glossary/nuts-advantage/)
- [Nut and Range Advantage | Upswing Poker](https://upswingpoker.com/nut-range-positional-advantage/)

---

## 10. MDF（最低防衛頻度 / Minimum Defense Frequency）

### 定義

相手のブラフを自動利益にさせないために、コール（またはレイズ）で**最低限ディフェンドしなければならない頻度**。

### 計算式

```
MDF = ポットサイズ ÷ (ポットサイズ + ベットサイズ)
```

**例**: ポット $100、ベット $50 の場合
MDF = 100 ÷ (100 + 50) = 66.7%

つまり、この状況で 66.7% 以上コンティニュー（コール＋レイズ）しないと相手のブラフが自動プロフィットになる。

### 初級者が混同しやすい点

- MDF はブラフを「無効化」する頻度であり、バリューハンドの正当性とは別問題
- マルチウェイでは各プレイヤーが MDF を満たす必要はない（合算で満たせばよい）
- 実際にはポジション・ハンドストレングスで補正が必要

### 出典

- [MDF & Alpha | GTO Wizard](https://blog.gtowizard.com/mdf-alpha/)
- [Minimum Defense Frequency | PokerCoaching](https://pokercoaching.com/blog/mdf-poker/)
- [MDF 101 | SplitSuit Poker](https://www.splitsuit.com/mdf-101-and-free-calculator)

---

## 11. チェックレイズ（Check-Raise）

### 定義

チェックした後、相手のベットに対してレイズすること。フロップ・ターン・リバーいずれでも可能。

### 種類

| 種類 | 目的 | 典型ハンド例 |
|------|------|-------------|
| バリューチェックレイズ | ポットを膨らませて価値を最大化 | セット、2ペア、ナッツフラッシュ |
| セミブラフチェックレイズ | 今は弱いが改善可能なドロー | フラッシュドロー＋ガットショット |
| ブラフチェックレイズ | 相手にフォールドを強制 | 完全なエア（高頻度には不向き） |

### 最適条件

- ウェット・コネクテッドボードでレンジアドバンテージがある場面
- 相手の CBet 頻度が高い場合
- スタックが深い（SPR 6以上）場合

### 出典

- [Check-Raise Strategy | CardPlayer](https://www.cardplayer.com/online-poker/check-raise-strategy-in-poker)
- [When to Check-Raise Bluff on the Flop | Hand2Note](https://hand2note.com/Blog/Features/when_to_check-raise_bluff_on_the_flop)

---

## 12. ドンクベット（Donk Bet）

### 定義

前のストリートでアグレッション（レイズ等）を取られた側が、次のストリートで OOP（アウトオブポジション）から先にベットすること。

**例**: BB が BTN のオープンをコール → フロップで BB が最初にベット

### なぜ「悪い」とされるか（伝統的見解）

1. アグレッサー側のCBetを「無料で」使わせなくなる
2. 自分のレンジに弱いシグナルを送る可能性がある
3. ポジション的に不利な状態でポットを大きくするリスク

### 現代的評価（GTO視点）

- 特定のボードテクスチャ（自分のレンジに有利なロウボード等）ではドンクベットが正当化される
- アグレッサーの CBet 頻度が低い傾向のある現代ゲームでは有効な場面が増加
- 要確認：GTO ソルバーはローボード（2-4-7等）でBB のドンクベットを一定頻度推奨する

### 出典

- [What is Donk Betting | Upswing Poker](https://upswingpoker.com/donk-bet-lead-flop-strategy/)
- [How and Why to Use Turn Donk Bets | GTO Wizard](https://blog.gtowizard.com/how-and-why-you-should-use-turn-donk-bets/)

---

## 13. フロート（Float）

### 定義

相手のCBet に対して、現時点では強いハンドがなくても、**次のストリートでブラフを打つ計画でコールする**こと。

### 有効条件

- **ポジション優位**（IP）が必須
- 相手の CBet 頻度が高くダブルバレル頻度が低い
- ドライボードで相手がターンにチェックしやすい状況
- ヘッズアップ（マルチウェイは難しい）

### フロートの展開

1. フロップ：相手 CBet → こちらコール（フロート）
2. ターン：相手チェック → こちらベット（pot の 1/2〜2/3 が目安）

### 初級者が混同しやすい点

- フロートはブラフ計画を持つコール（将来のアクションが前提）
- 単なるコールや引きを待つドローコールとは区別する

### 出典

- [The Float Play | Pokerology.com](https://www.pokerology.com/lessons/the-float-play/)
- [What is Float | 888poker](https://www.888poker.com/magazine/poker-terms/float)
- [The Art of Floating | GGPoker](https://ggpoker.com/blog/the-art-of-floating/)

---

## 14. プローブベット（Probe Bet）

### 定義

プリフロップアグレッサーがフロップをチェックバック（IP 側がチェックで返す）した後、OOP プレイヤーがターンで**先制ベット**すること。

**例**: BTN がプリフロップオープン → BB コール → フロップ BB チェック → BTN チェック → **ターン BB ベット（プローブベット）**

### 狙い

- BTN がフロップチェックバックをすることで「レンジが弱い」シグナルが出る
- OOP 側がそれを利用してポットを取りにいく

### サイジングと頻度

- 標準サイジング：ポットの 50〜75%
- 自分のレンジに有利なターンカードでは高頻度・小サイズ
- 不利なターンカードでは低頻度・大サイズ

### ドンクベットとの違い

ドンクベットはフロップで OOP が先にベットする行為。プローブベットはターン以降に OOP が先にベットする（フロップチェックバック後）点が異なる。

### 出典

- [The Turn Probe Bet | GTO Wizard](https://blog.gtowizard.com/the-turn-probe-bet/)
- [Probe Betting | GTO Wizard](https://blog.gtowizard.com/probe-betting/)
- [When to Attack After Checks Back | Upswing Poker](https://upswingpoker.com/turn-probe-kanu7/)

---

## 15. ディレイドCBet（Delayed C-Bet）

### 定義

プリフロップアグレッサーがフロップをチェックし、**ターンで初めてベットする**こと。

**例**: BTN オープン → BB コール → フロップ BB チェック → BTN チェック → **ターン BB チェック → BTN ベット（ディレイドCBet）**

### 使用理由

- フロップのボードテクスチャが悪い（相手レンジに有利）
- ターンカードで自分のレンジが改善した
- ポット管理（小さいポットで有利な状況に持ち込む）

### プローブベットとの混同

ディレイドCBetは IP 側（プリフロップアグレッサー）がターンで打つ行為。プローブベットは OOP 側が打つ。

### 出典

- [What is a Delayed C-Bet | Upswing Poker](https://upswingpoker.com/delayed-continuation-bet-c-bet-strategy/)

---

## 16. ダブルバレル（Double Barrel）

### 定義

プリフロップアグレッサーが**フロップとターンの2ストリート連続してベット**すること。

### 使用基準

- バリューハンド（TPTK 以上）が典型的な使用場面
- セミブラフ（フラッシュドロー＋ストレートドロー）でも有効
- 相手のレンジが弱い（フォールドエクイティが高い）ターンカード

### ターンカードの選択

| ターンカード | ダブルバレル適性 |
|-------------|----------------|
| ブランクカード（自分のレンジに関係ない） | 低（相手がコールしやすい） |
| 自分のレンジを強化するカード | 高（信憑性が増す） |
| 相手レンジを弱化するカード（ドローミス等） | 高 |

### 出典

- [Double Barrel Definition | Club Poker](https://en.clubpoker.net/double-barrel/definition-157)
- [Double Barreling in Poker | VIP-Grinders](https://www.vip-grinders.com/double-barreling-in-poker-when-to-fire-a-second-barrel/)
- [3 Tips for Double Barreling | PokerStars Learn](https://www.pokerstars.com/poker/learn/strategies/3-top-tips-for-double-barreling-in-poker/)

---

## 17. オーバーベット（Overbet）

### 定義

**ポットサイズを超えるベット**。例：ポット $100 に対して $150 のベット。

### 使用条件

- **ポラライズドレンジ**（ナッツまたはブラフのみ）の場合
- 相手のレンジがキャップされている（強いハンドを持ちにくい）場面
- ナッツアドバンテージが自分にある場面

### サイジングの目安

- 1.5〜2倍ポットが一般的なオーバーベットサイズ
- 2倍ポットの場合、バリュー60%：ブラフ40% の比率で打つ必要がある

### フロップ vs ターン vs リバー

オーバーベットはリバーで最も多く使われ、次いでターン、フロップでは比較的少ない（ポラリゼーションが進むほど有効）。

### 出典

- [The Art of the Flop Overbet | GTO Wizard](https://blog.gtowizard.com/the_art_of_the_flop_overbet_and_why_youre_probably_doing_it_wrong/)
- [3 Pro Tips for Overbetting | Upswing Poker](https://upswingpoker.com/overbet-flop-tips/)

---

## 18. ブロッカー（Blocker）

### 定義

自分のホールカードが相手の強いコンボの組み合わせ数を**物理的に減少させる**効果を持つカード（またはその効果そのもの）。

### フロップ文脈での意味

- **ナッツブロッカー**：フラッシュボードでナッツフラッシュ（A のスーツ）を持つ → 相手のナッツフラッシュコンボを0に減らせる
- **セットブロッカー**：K♦ を持つ → KK のコンボを 6 から 3 に削減
- **ブラフ時の活用**：ナッツをブロックしながらブラフすることで相手のコールレンジを弱化

### コンボ削減の例

| 保有カード | 対象コンボ | 削減前 | 削減後 |
|-----------|-----------|-------|-------|
| K♦ | KK（ポケットキングス） | 6コンボ | 3コンボ |
| K♦ | AK | 16コンボ | 12コンボ |
| A♣（フラッシュボード） | ナッツフラッシュ | 複数コンボ | 0コンボ |

### 初級者が混同しやすい点

- ブロッカーは確率を操作するのではなく、**組み合わせ数を物理的に削減**する
- ブロッカーを持つことが常に有利とは限らない（コールレンジをブロックする逆効果も）

### 出典

- [Understanding Blockers in Poker | GTO Wizard](https://blog.gtowizard.com/understanding-blockers-in-poker/)
- [Blocker Definition | PokerStrategy](https://www.pokerstrategy.com/glossary/Blocker/)
- [Poker Combos & Blockers 101 | SplitSuit](https://www.splitsuit.com/poker-combos-blockers)

---

## 19. 役（Made Hand）の呼称

### 主要な呼称一覧

| 略称 | 正式名称 | 意味 | 例 |
|------|----------|------|----|
| TPTK | Top Pair Top Kicker | トップペア＋最高キッカー | AK → K-7-2 ボードでKペア |
| TP | Top Pair | トップペア（キッカー問わず） | K9 → K-7-2 ボードでKペア |
| MP / SP | Middle Pair / Second Pair | ミドルペア / セカンドペア | J9 → K-J-2 ボードでJペア |
| OP / Overpair | Overpair | ボード最高カードより大きいポケットペア | AA → K-7-2 ボードで AA |
| UP | Underpair | ボード最高カードより小さいポケットペア | 88 → K-7-2 ボードで 88 |
| Set | Set | ポケットペア＋ボードに同ランクが1枚 | 77 → K-7-2 ボードでセット |
| Trips | Trips | ボードのペア＋ホールカード1枚で3カード | K9 → K-K-2 ボードで K9 |
| TPWK | Top Pair Weak Kicker | トップペア＋弱いキッカー | K2 → K-7-2 ボードでKペア |
| 2P | Two Pair | ツーペア | K7 → K-7-2 ボードで KK+77 |
| FH | Full House | フルハウス | 77 → K-7-7 ボードでフルハウス |

### 注意事項

- **Set（セット）vs Trips（トリップス）**：セットはポケットペアを使う3カード、トリップスはボードのペアを使う3カード。セットの方が隠れやすく価値が高い。
- **TPTK は状況依存**：相手レンジやSPRによって、スタックオフの根拠になる場合もならない場合もある。

### 出典

- [What is TPTK in Poker? | MyPokerCoaching](https://www.mypokercoaching.com/poker-terms/tptk/)
- [Glossary of Poker Terms | Wikipedia](https://en.wikipedia.org/wiki/Glossary_of_poker_terms)
- [Poker Glossary | Red Chip Poker](https://redchippoker.com/poker-glossary-terms-definitions/)

---

## 本書への適用

### 第2章「本書を読むための用語」での活用

| 用語グループ | 第2章での扱い |
|-------------|-------------|
| SPR・MDF | 数値で示される概念として定義ページに掲載 |
| CBet・ドンクベット・フロート・プローブベット・ディレイドCBet・ダブルバレル | ベッティングアクション用語として一覧化 |
| ボードテクスチャ・モノトーン・ペアード | ボード分類用語として図付きで解説 |
| BDFD・BDSD | ドロー用語として「バックドア」概念とセットで説明 |
| レンジアドバンテージ・ナッツアドバンテージ | レンジ思考の基礎概念として早期に導入 |
| ブロッカー | 中級概念として第2章末尾または第3章へ繰り越し検討 |
| 役の呼称（TPTK・セット等） | 表として付録的に配置 |

### 推奨レイアウト

初級者向けに「数式が必要な用語（SPR・MDF）」と「概念的な用語（ボードテクスチャ等）」を分けて提示すると理解しやすい。具体的なボードとハンドの例を各項目に必ず添付することを推奨する。
