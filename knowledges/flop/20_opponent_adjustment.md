# 相手タイプとスタック深度によるしきい値調整

検索日: 2026-04-20

## 概要

フロップ戦略は相手の傾向（VPIP/PFR で表現されるプレイタイプ）とスタック深度（SPR）によって大きく変わる。GTO をベースラインとしながら、相手のエクスプロイタブルな偏りを特定し、CBet 頻度・サイズ・手のレンジを調整することで EV を最大化できる。

---

## 主要な知見

### 1. 相手タイプ別 CBet 調整

#### タイト・パッシブ（TP / Nit）

- VPIP/PFR の目安：12〜18 / 8〜14（ギャップ小）
- 特徴：ヒットしないとフォールド、リレイズは本物だけ
- **CBet 戦略：ブラフ CBet を増やす**
  - フォールドツー CBet が高い（70%+）のでエア含むすべてのレンジで CBet 推奨
  - ヒットしなければ 1 バレルで終わり、コールされたら諦める
  - レイズを受けたら即折り（TP は弱いハンドでレイズしない）
- 出典: [Different types of poker players and how you exploit them](https://www.bluffthespot.com/blog/player-types)

#### タイト・アグレッシブ（TAG / Reg）

- VPIP/PFR の目安：19〜25 / 17〜23（ギャップ極小）
- 特徴：バランスされたレンジ、GTO に近い、ノッテいる
- **CBet 戦略：GTO バランスを基準に微調整**
  - 過度なブラフは逆用されるリスク
  - ポジションとボードテクスチャに従った標準的な CBet 頻度（IP: ~60-70%、OOP: ~50-55%）
  - 相手の特定の偏り（例：フロップコール後にターンでフォールドが多い等）を HUD データで見つければそこだけ搾取
- 出典: [Poker Playing Styles and How to Exploit Them](https://ultimatepokercoaching.com/blog/poker-playing-styles-and-how-to-exploit-them/)

#### ルース・パッシブ（LP / コーリングステーション）

- VPIP/PFR の目安：40〜60 / 5〜15（ギャップ大）
- 特徴：なんでもコール、フォールドしない、レイズはほぼ本物
- **CBet 戦略：バリュー重視、ブラフ禁止**
  - ブラフ CBet は EV マイナス。フォールドしてくれないため損するだけ
  - バリューベットのしきい値を下げる（薄いバリューでも積極的にベット）
  - ベットサイズを大きくしてバリューを最大化
  - チェックバックはナッツレベルの手でも不要（チェックレイズされても滅多にない）
- 出典: [How to Crush Calling Stations in Poker](https://www.pokercode.com/blog/calling-stations)
- 出典: [The Five Imbalances of Exploitative Poker | GTO Wizard](https://blog.gtowizard.com/the-five-imbalances-of-exploitative-poker/)

#### ルース・アグレッシブ（LAG / マニアック）

- VPIP/PFR の目安：30〜50 / 25〜45（ギャップ小〜中）
- 特徴：広いレンジでベット・レイズ、3 バレルも辞さない
- **CBet 戦略：タイトに絞り、トラップ重視**
  - ナッツクラスの手はスロープレー（チェックコール or チェックレイズ）
  - 相手が自らバレルを打ってくれる → 誘導してポットを膨らませる
  - ターンで大きいレイズを仕掛けるとオーバーエクステンドさせやすい
  - ブラフ CBet は減らす（相手は広くコール/レイズしてくるため）
- 出典: [LAG Poker Strategy: Crush Loose Aggressive Players](https://pokercoaching.com/blog/lag-poker/)
- 出典: [Play Like, or Against a Poker Maniac](https://www.888poker.com/magazine/strategy/how-to-beat-a-poker-maniac)

---

### 2. スタック深度補正（SPR ベース）

SPR（Stack-to-Pot Ratio）= 残スタック ÷ フロップポット

| スタック深度 | 目安 BB | フロップ SPR | 戦略方針 |
|---|---|---|---|
| ディープ | 150BB+ | 12〜20 | ドロー価値↑、ナッツ志向 |
| 標準 | 100BB | 8〜12 | 本書の基準 |
| ショート | 40BB 以下 | 2〜4 | プリフロップ決着志向 |

#### ディープ（150BB+）

- スーテッドコネクター（98s, 87s）や小ペア、スーテッドエースの価値が大幅上昇
- フロップでの CBet サイズは小さく（33〜50% pot）してポットコントロール
- ストレート・フラッシュ完成時のインプライドオッズが最大化
- 1 ペアハンドは慎重に（後続ストリートで 2 回以上のレイズに耐えられない）
- OOP での 4 ベットや SPR が極めて高い状況では、ナッツポテンシャルのない手を折りやすく
- 出典: [How Stack Sizes Change Your Range | GTO Wizard](https://blog.gtowizard.com/how-stack-sizes-change-your-range/)
- 出典: [Deep Stack Poker: How To Adjust Your Strategy | Pokercode](https://www.pokercode.com/blog/deep-stack-poker-strategy)

#### 標準（100BB）

- 本書の全章のデフォルト前提
- GTO ベースの CBet 頻度・サイズが最も機能する
- SPR ~10 程度、ほとんどのハンドカテゴリを使用可能

#### ショート（40BB 以下）

- SPR 2〜4 では複雑なポストフロップライン（フロート・トリプルバレル等）は成立しない
- プリフロップでオールインを見据えた意思決定が主体
- フロップ CBet はほぼオールインコミットに近い意味を持つ
- プレミアムハンド以外はプリフロップでフォールドが最善になりやすい
- 出典: [Mastering SPR and Effective Stack Depth | PokerCoaching](https://pokercoaching.com/blog/poker-spr/)
- 出典: [Short Stack Poker Strategy | BlackRain79](https://www.blackrain79.com/2018/08/short-stack-poker-strategy.html)

---

### 3. 相手の CBet 頻度を読む

#### CBet 頻度の目安と解釈

| CBet 頻度 | 解釈 | 搾取方法 |
|---|---|---|
| 70%以上 | 過剰 CBet（エアも多い） | コール範囲を広げる、フロートしてターンで奪う |
| 50〜65% | GTO 近似（対処難しい） | ボードテクスチャと他スタッツで補完判断 |
| 30%以下 | タイト CBet（ほぼヒットのみ） | フォールド広く、コールは強いハンドのみ |

#### マルチストリート CBet パターン

- **フロップ高・ターン低（例：80% → 33%）**: ワンアンドダンタイプ。フロートが有効
- **フロップ高・ターン高（例：75% → 70%）**: 過剰バレラー。ターンでフロートorレイズが機能
- **フォールド to CBet 70%+**: エアも含め CBet すべし。コールされたら降りる
- **フォールド to CBet 35%以下**: バリューのみ CBet、ブラフは控える

- 出典: [Make These Two Profitable Exploits with HUD Statistics](https://smartpokerstudy.com/make-these-two-profitable-exploits-with-hud-statistics/)
- 出典: [Exploiting Excessive C-Betting by OOP | GTO Wizard](https://blog.gtowizard.com/exploiting-excessive-c-betting-by-oop/)

---

### 4. VPIP / PFR から相手タイプを推定

```
VPIP / PFR の組み合わせによる分類

             PFR低 (〜12%)     PFR中 (12〜22%)    PFR高 (22%+)
VPIP低(〜20%) Nit (TP)        TAG (標準 Reg)      ほぼ存在しない
VPIP中(20〜35%) Passive Reg   Solid TAG           LAG
VPIP高(35%+) Calling Station  -                  Maniac (LAG極端)
```

- VPIP と PFR のギャップが大きい（例：45/12）= コーリングステーション
- VPIP と PFR のギャップが小さい（例：22/20）= アグレッシブプレイヤー
- 100 ハンドで大まかな傾向、1000 ハンドで精度高い推定が可能
- CBet 頻度・フォールドツー CBet を合わせて見ることで搾取ライン確定

- 出典: [VPIP and PFR - Poker Statistics](https://pokercopilot.com/poker-statistics/vpip-pfr)
- 出典: [Profiling Players | Become a Poker Detective - Automatic Poker](https://automaticpoker.com/strategy/profiling-opponents/)

---

### 5. エクスプロイト戦略のフロップ版

GTO 戦略は「搾取されない」ことを保証するが、EV を最大化しない。相手の偏りに応じて意図的に GTO から逸脱することが利益を生む。

#### フロップでの 5 つのエクスプロイタブルなアンバランス（GTO Wizard 分類）

1. **CBet 頻度の偏り**: 高すぎる or 低すぎる CBet → コール/フォールド調整
2. **ベットサイズの偏り**: 常に小さい/大きい → サイズに応じた偏りの逆用
3. **チェックレンジの弱さ**: OOP でチェックが弱いなら、チェック後のベットで奪える
4. **降りすぎ傾向**: フォールド to CBet 高い → ブラフ増加
5. **コールしすぎ傾向**: コーリングステーション → バリューベット増加、ブラフゼロ

- 出典: [The Five Imbalances of Exploitative Poker | GTO Wizard](https://blog.gtowizard.com/the-five-imbalances-of-exploitative-poker/)
- 出典: [GTO vs Exploitative Play: Which is the Better Strategy? - Upswing Poker](https://upswingpoker.com/gto-vs-exploitative-play-game-theory-optimal-strategy/)

---

## 本書への適用

| 章 | 活用内容 |
|---|---|
| 第20章「相手タイプとスタック深度によるしきい値調整」| 本ページの内容がそのまま章の骨格 |
| 第14章（プレイヤータイプ搾取） | VPIP/PFR による相手タイプ分類の基礎部分と連携 |
| 第10章（ベットサイズ理論） | コーリングステーション相手のサイズ増加戦術と連携 |
| 第12章（レンジ思考） | TAG 相手のバランス CBet と相手レンジ想定の接続 |
| 第15章（GTO とエクスプロイトの融合） | 5 つのアンバランス分類を参照として引用 |

### 執筆上の注意点

- 「しきい値」とは CBet するか否かの判断基準（エクイティ・ポジション・相手タイプの合成）
- 相手タイプ別のしきい値の「ずらし方」を数値で示すことが重要
  - 例：標準では CBet しきい値 40% エクイティ → TP 相手は 30% まで下げてブラフ増
  - 例：LP 相手はブラフ CBet しきい値を無限大に（＝ブラフゼロ）
- ショートスタック時はフロップ CBet の判断基準が「コミットか否か」に移行することを明示
