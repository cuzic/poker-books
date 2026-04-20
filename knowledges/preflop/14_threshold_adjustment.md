# 第14章：相手タイプとスタック深度で閾値を動かす

検索日: 2026-04-19

## 概要

固定しきい値（スコア閾値）は「標準100BBのGTO近似」として機能するが、実戦では相手のVPIP/PFR・スタック深度の2軸で動的に補正する必要がある。本章は「静的チャートから動的判断へ」の橋渡しを担う。

---

## 1. プレイヤータイプ分類

### 1-1. VPIP/PFR で4分割する

| タイプ | VPIP | PFR | 別名 |
|--------|------|-----|------|
| タイト・パッシブ | <20% | <<VPIP | Nit/Rock |
| タイト・アグレッシブ (TAG) | <20% | ≈VPIP | 標準的な上級者 |
| ルース・パッシブ | >30% | <<VPIP | Calling Station |
| ルース・アグレッシブ (LAG) | >30% | ≈VPIP | Maniac |

VPIP/PFRの「差（ギャップ）」がパッシブ度を示す。差が2〜6ポイントは正常範囲、15ポイント以上はコーリングステーション確定。

- 出典: [VPIP and PFR - Poker Statistics](https://pokercopilot.com/poker-statistics/vpip-pfr) (PokerCopilot)
- 出典: [How to Spot and Exploit the 4 Common Poker Player Types](https://smartpokerstudy.com/4-common-poker-player-types/) (SmartPokerStudy)

### 1-2. 各タイプの特徴

**タイト・パッシブ（Nit）**
- ポット参加時は強いハンドのみ。リレイズはほぼ本物。
- ブラフが有効な唯一のレクリエーション層。
- ブラインドスチール成功率が高い（頻繁に降りる）。

**タイト・アグレッシブ（TAG）**
- VPIP/PFR が 15/13 〜 17/15 程度が典型値。
- GTO近似に近いため搾取は困難。基本GTOラインで対応。
- エクスプロイトを試みるのは損。大きくずれるプレイはEVを落とす。

**ルース・パッシブ（Calling Station）**
- VPIP/PFR が 40/10 や 37/11 が典型値。
- ブラフは禁物。バリューベットを薄く打つ戦略に切り替える。
- ポット参加頻度が高いがアグレッションが低い（リレイズが少ない）。

**ルース・アグレッシブ（Maniac）**
- 多くのハンドをレイズで入る。3betも多い。
- 自分からタフなリレイズはしない。レンジを広げてコールし、ポストフロップで価値を出す。
- 右隣に座れるとアドバンテージ最大化。

出典: [Different types of poker players and how you exploit them](https://www.bluffthespot.com/blog/player-types) (BluffTheSpot, 2024年確認)

---

## 2. 相手タイプ別しきい値補正

### 2-1. 基本補正値の根拠

```
タイト相手 (VPIP < 20%)：しきい値 +2
ルース相手 (VPIP > 30%)：しきい値 −2
```

**なぜ +2 か（タイト相手）**
- タイト相手はポット参加時に本物のハンドを持つ確率が高い。
- 相手の3bet・コールに対してこちらが降りる頻度を上げることで、マージナルハンドでの損失を避ける。
- ただし「ブラインドスチール」の文脈では逆に攻める。つまり、相手が参加してきたら強度を上げ（しきい値+2でオープン自体は慎重に）、不参加なら頻繁にスチールする。
- しきい値+2 = 「相手から強いアクションが来た場合の対応レンジを絞る」ことを意味する。

**なぜ −2 か（ルース相手）**
- ルース相手はウィークハンドでポット参加している確率が高い。
- こちらのバリューハンドで取れる期待値が増える。
- マージナルハンドでも参加する価値が上がるため、しきい値を2ポイント下げて参加頻度を上げる。
- 「コーリングステーション相手にブラフを減らし、バリューを増やす」原則の派生。

出典: [How to Utilize VPIP Poker Stat to Your Advantage](https://pokercoaching.com/blog/vpip-poker-stat/) (PokerCoaching)
出典: [VPIP Poker Guide](https://somuchpoker.com/poker-term/vpip-poker-strategic-advantage) (SoMuchPoker)

### 2-2. タイプ別具体的エクスプロイト

| 相手タイプ | しきい値補正 | 主な戦術 |
|-----------|------------|---------|
| タイト・パッシブ | +2 | ブラインドスチール積極化、強いアクションへは降りる |
| タイト・アグレッシブ (TAG) | ±0（GTO維持） | エクスプロイト避け、バランス重視 |
| ルース・パッシブ | −2 | バリューベット薄く大きく、ブラフ削減 |
| ルース・アグレッシブ | −2 + コール幅拡大 | レンジを広げてコール、ポストフロップで価値 |

出典: [What is PFR in Poker & How to Adjust against Different Players?](https://www.pokercode.com/blog/pfr) (PokerCode)

---

## 3. スタック深度による補正

### 3-1. スタック深度とハンドの価値変化

スタック深度が変わるとSPR（スタック対ポット比）が変わり、各ハンドカテゴリの価値が変動する。

| スタック深度 | SPR（シングルレイズポット） | 戦略の重心 |
|------------|------------------------|-----------|
| 200BB | 20前後 | ポストフロップ価値・インプライドオッズ最大 |
| 150BB | 15前後 | スーテッド・コネクターの価値が高い |
| 100BB | 10前後 | 標準（チャートの基準） |
| 60BB | 6前後 | SC弱体化開始、ブロードウェイ重視 |
| 40BB | 4前後 | SC実質無価値、ハイカード + ペア中心 |
| 20BB以下 | 2以下 | プッシュ/フォールド戦略 |

出典: [How Stack Sizes Change Your Range | GTO Wizard](https://blog.gtowizard.com/how-stack-sizes-change-your-range/) (GTOWizard)
出典: [Mastering SPR and Effective Stack Depth](https://pokercoaching.com/blog/poker-spr/) (PokerCoaching)

### 3-2. ディープスタック（150BB以上）の補正

**スーテッド・コネクター（SC）のスコア +1**

根拠：
- 150BB以上では、フロップ後に残るスタックが大きく、ストレート・フラッシュを完成させた際のインプライドオッズが最大化する。
- 3人以上のマルチウェイポットではさらに価値が増す（複数の相手から価値を取れる）。
- 150BBではオープン2.2〜2.5BB、3bet 7〜8BBとしても3ストリート分十分なスタックが残るため、ポストフロップでの操作余地が広い。
- 60BB以下のスタックに対する3betブラフでは逆にSCを使わない（SPRが低すぎてマニューバビリティが消失する）。

具体例：98s は100BBでは境界線上のハンドだが、150BBではSPRが上がりインプライドオッズが改善するためスコア+1が正当化される。

出典: [5 Strategic Mistakes Poker Players Should Avoid with Suited Connectors](https://upswingpoker.com/suited-connectors-poker-strategy/) (Upswing Poker)
出典: [Poker Starting Hands with Deep Stacks](https://flopturnriver.com/poker-strategy/poker-hand-strategy-poker-starting-hands-with-deep-stacks-19736/) (FlopTurnRiver)

### 3-3. ショートスタック（40BB以下）の補正

**SC 実質無視、ブロッカー +1**

根拠：
1. **SC無視の理由**
   - 40BB以下ではSPRが低く、ストレート・フラッシュを完成させてもスタックを全部取れない（深いポットが作れない）。
   - インプライドオッズが消失し、ドロー系ハンドの主な価値源がなくなる。
   - GTO Wizardの分析でも、50BBで44・33・22などのスモールペアが価値を失い始め、ロースーテッド・コネクターも同様に脱落する。

2. **ブロッカー +1 の理由**
   - 40BB以下になるとプリフロップでの決着（オールイン）が増える。
   - Aをブロック（A5s のAなど）すると、相手がAAやAKを持つ確率が低下し、オールインの勝率が向上する。
   - A5s は20BBでのシャブには弱いが、3bet/fold 範囲として活用でき、Aブロッカー効果でフォールドエクイティが増す。
   - ショートスタックでは「フォールドエクイティ + 生の勝率」がほぼ全てのEVを決定する。

出典: [Short-Stacked Play in MTTs | GTO Wizard](https://blog.gtowizard.com/short-stacked-play-in-mtts/) (GTOWizard Blog)
出典: [10 Push Fold Charts for Poker Tournaments](https://upswingpoker.com/push-fold-tournament-strategy-charts/) (Upswing Poker)
出典: [The Best Short Stack Poker Strategy](https://www.blackrain79.com/2018/08/short-stack-poker-strategy.html) (BlackRain79)

---

## 4. ショートスタック戦略の詳細

### 4-1. 40BB以下の戦略転換

- プリフロップでの意思決定の重みが、ポストフロップよりはるかに大きくなる。
- ミニレイズ（min-raise）戦略が有効：スタックを温存しつつ、レイズ/フォールドオプションを残す。
- 30BB以下になるとミニレイズが主要アクションに。

### 4-2. プッシュ/フォールドの閾値

- 純粋なプッシュ/フォールド戦略は概ね12〜15BB以下で最適。
- 40BBでは通常のオープンがまだ有効だが、SCなどのスペキュラティブハンドは脱落する。
- 20BB以下ではスモールペア（22〜55）も「raw equity」ベースで価値が戻ってくる（相手が広いレンジでコールするため）。

| スタック深度 | 主なアクション | 有効なハンドカテゴリ |
|------------|--------------|-------------------|
| 40BB | オープン/3bet/フォールド | ブロードウェイ・中〜大ペア・強いAx |
| 20-30BB | ミニレイズ多用 | ハイカード主体、ペアはTT+ |
| 12-15BB | プッシュ/フォールド開始 | 強いAx、ブロードウェイ、大ペア |
| 8BB以下 | ほぼ全ハンドでプッシュ検討 | raw equityで判断 |

出典: [Short-Stacked Play in MTTs | GTO Wizard](https://blog.gtowizard.com/short-stacked-play-in-mtts/)
出典: [Open-Raising with a Short Stack in Tournaments](https://upswingpoker.com/open-raising-with-a-short-stack-tournaments/) (Upswing Poker)

---

## 5. ディープスタック戦略の詳細

### 5-1. 150BB以上でのハンド価値変化

- インプライドオッズが増加し、スペキュラティブハンド（SC・スモールペア）の価値が最大化。
- ポストフロップでの操作余地が広いため、「プレイアビリティ」がハンド評価の重要指標になる。
- ナッツポテンシャル（最強ハンドになれるか）が深いスタックで特に重要。

### 5-2. ディープでの注意点

- ヘッズアップの3betポットでは逆にSCが弱くなる（ポットが大きくなりSPRが下がるため）。
- マルチウェイ（3人以上）ポットでSCの期待値は最大化する。
- AQsやTT+のようなリニアなハンドがヘッズアップ3betポットでは優位。

出典: [Deep Stack Poker: Strategy for Cash Games and Tournaments](https://www.pokerology.com/poker/strategy/deep-stack/) (Pokerology)
出典: [What Is Effective Stack Size & Why Does It Matter?](https://upswingpoker.com/effective-stack-size/) (Upswing Poker)

---

## 6. GTOとエクスプロイトのバランス

### 6-1. GTO を基準ラインとして使う

- GTOは「どんな相手にも負けない均衡戦略」。最強の相手に対するベースライン。
- エクスプロイトは「相手の不均衡（ミス）を意図的に突く戦略」。

**実践的な使い分け：**
- TAGやレギュラー相手 → GTO近似を維持（エクスプロイト試みはEV損）
- 明らかなレクリエーション（VPIP>35%など）相手 → エクスプロイト戦略に切り替え

### 6-2. 5つの不均衡（GTO Wizard分析）

相手の不均衡は5カテゴリに分類できる：

1. **Betting Volume（ベット量）**：過剰フォールド相手にはブラフ頻度上げ、過剰コール相手にはバリューを大きく
2. **Equity Management（エクイティ管理）**：過剰ブラフ相手にはコール増加
3. **Polarity（ポラリティ）**：凝縮レンジ相手には大きいサイズで攻める
4. **Elasticity（サイズ感度）**：サイズ無感覚な相手にはオーバーベット統一
5. **Board Coverage（ボードカバレッジ）**：カバー外のボードで積極的にリード

相手の不均衡が大きいほど、自分のレンジバランスを崩しても問題ない（搾取が優先される）。

出典: [The Five Imbalances of Exploitative Poker | GTO Wizard](https://blog.gtowizard.com/the-five-imbalances-of-exploitative-poker/) (GTOWizard Blog)

### 6-3. エクスプロイトの限界とリスク

- エクスプロイトは「相手が同じミスを繰り返す」前提で成立する。
- 相手が適応（調整）してきたら元のGTOラインに戻す。
- サンプルサイズが重要：VPIP/PFRは最低数十ハンド、理想は数百ハンドのデータが必要。

---

## 7. 補正値の統合フレームワーク

### 本書の第14章で示す補正テーブル案

```
基本しきい値 ± 相手タイプ補正 ± スタック補正 = 実戦しきい値

相手タイプ補正:
  VPIP < 20%（タイト）：+2
  VPIP 20-30%（標準）：±0
  VPIP > 30%（ルース）：−2

スタック深度補正:
  150BB以上：SC +1
  100BB（標準）：±0
  40BB以下：SC 除外、ブロッカー +1
```

例：ルース相手（VPIP35%）に150BBでCO からオープンを検討する 98s
- 基本しきい値（CO）: 18
- 相手ルース補正: −2 → 16
- ディープスタック SC 補正: +1 → しきい値 17 に引き下がる
- → よりオープンしやすくなる

---

## 8. VPIP/PFR の具体的な数値目安

| VPIP値 | 分類 | 推奨対応 |
|--------|------|---------|
| 1〜10% | 極度にタイト | ポット参加時は確実に強い。ブラインドスチール頻発。強アクションへは即フォールド |
| 11〜20% | タイト | しきい値+2。強いアクションを尊重。スチールは有効 |
| 21〜30% | 標準 | ±0。GTO近似で対応 |
| 31〜40% | ルース | しきい値−2。バリューベット中心 |
| 41%以上 | 極度にルース | しきい値−2以上も検討。ブラフ禁止・バリュー最大化 |

出典: [VPIP Poker Explained: How to Read Player Styles](https://www.pokerology.com/poker/strategy/vpip/) (Pokerology)
出典: [Understanding VPIP in Poker](https://www.poker.org/poker-strategy/understanding-vpip-in-poker-aYzqE5A8dTMo/) (Poker.org)

---

## 本書への適用

### 第14章での活用

- **第II部（スコア式）と第III部（対応アクション）で固定していたしきい値を動かす技術として位置づけ**
- 「しきい値は相手とスタックで変わる」という動的思考への転換点
- 2軸（相手タイプ × スタック深度）の補正表を中央に配置し、読者が参照できる形式にする
- ミニクイズ：「VPIP35%の相手に150BBでCO から 98s を3betされた。コールするか？」

### 図解提案

1. 4象限図：VPIP vs PFR で4タイプを視覚化
2. スタック深度 × ハンドカテゴリの価値変化グラフ（縦軸：価値、横軸：スタック深度BB）
3. 補正テーブル：2軸マトリクス（相手タイプ × スタック）でしきい値変動を一覧化

### GTOとのズレ（コラム）

- GTOは100BB固定・相手タイプ不問を前提とする。現実は相手が不均衡だらけ。
- 「相手が適応してきたらGTOに戻す」という動的なバランスが本章のテーマ。
- 最適なエクスプロイトは「GTOとの偏差を相手の偏差量だけ取る」という原則を提示。
