# 第20章「簡易式からGTOへ：学習ロードマップ」調査結果

検索日: 2026-04-19

## 概要

本書を卒業した読者が次のステップとして活用できるGTOツール・書籍・コミュニティ・学習ルーチンに関する情報を整理する。ツールの実際の機能・価格・使い方から、日本語リソースまで網羅した。

---

## 1. GTO Wizard

### 無料版でできること

- 毎日のトレーナーとソリューションブラウザへのアクセス（利用上限あり）
- プリフロップチャートの全閲覧
- ローテーション制のポストフロップドリル
- マルチウェイプリフロップの解析（10bb以下は無料）
- GTO Reportsでのプリフロップ統計比較（一部機能）

### 有料プラン（Starter / Premium / Elite / Ultra）

- プランが上がるにつれてサポート・ツール・機能が大幅に拡充される
- Ultra: カスタムマルチウェイプリフロップ解析が可能
- 出典: [GTO Wizard Review 2026 - Is It Worth Your Money?](https://www.vip-grinders.com/poker-tools/gto-wizard/)
- 出典: [Single Size Solutions Are Live. New Pricing.](https://blog.gtowizard.com/single-size-solutions-are-live-new-pricing-50x-more-solutions/)

### プリフロップ解析の基本操作（GTO Reports）

2025年3月に公開されたGTO Reportsは、自分のプリフロップ統計をGTOベンチマークと直接比較できる機能。

- 分析対象統計: VPIP、PFR、RFI（レイズファーストイン）、Limp、Squeeze、3-Bet、4-Bet、5-Bet
- カラーコードによる視覚的なズレの表示
- EV損失の大きい順にミスリスト表示
- ポジション別マトリクス分析
- 現時点ではキャッシュゲーム（100bb/200bbスタック）のみ対応。トーナメントとポストフロップは今後対応予定
- 出典: [GTO Wizard Introduces Game-Changing Feature](https://www.pokernews.com/news/2025/03/gto-wizard-game-changing-feature-48276.htm)
- 出典: [Redesigned Analyzer & Upgraded GTO Reports](https://blog.gtowizard.com/redesigned_analyzer_and_upgraded_gto_reports/)

### Range Builder機能

プリフロップとポストフロップのレンジを視覚的に構築・分析できる機能。自分のレンジとGTO解のズレを確認するのに適している。

- 出典: [How To Use Range Builder in GTO Wizard](https://blog.gtowizard.com/how-to-use-range-builder-in-gto-wizard-to-improve-your-game/)

---

## 2. その他のソルバー

### PIOSolver（上級者向け・ポストフロップ特化）

- ローカルインストール型（Windows）
- NLHE ポストフロップ解析のデファクトスタンダード
- レンジ・ベットサイズ・レイクを自由に設定可能
- EVと頻度の詳細なアウトプットを生成
- 価格: $249〜$1,099（プランによる）
- 特徴: 最速クラスのソルバーの一つ
- 出典: [5 Best GTO Poker Solvers: Top Picks for 2026](https://www.hudstore.poker/5-best-gto-poker-solvers)
- 出典: [Poker Solvers: A Beginner's Guide 2026](https://pokerfuse.com/learn-poker/tools/poker-solvers/)

### MonkerSolver（マルチウェイ・PLO対応）

- ポストフロップ・プリフロップ・マルチウェイ・PLO全対応
- PLO（ポットリミットオマハ）のプリフロップとポストフロップ解析では業界標準
- HEのマルチウェイスポットにも対応
- 価格: €499（約5.5万円）
- 出典: [The Best 5 Poker Solvers in 2025](https://www.primedope.com/the-best-5-poker-solvers-in-2025/)

### RangeConverter（プリソルブドレンジの購入・活用）

- PIOSolverとMonkerSolver向けのプリソルブドプリフロップレンジを提供
- MTT、ICMレンジ、PLOレンジ、キャッシュゲームレンジ（HU/6max/9maxフルリング）を網羅
- サーバーレンタルや自力シム不要でGTOレンジを即座に入手可能
- 用途: 自分で解かずにGTO最適解を参照したい中上級者向け
- 出典: [RangeConverter - GTO preflop ranges for PioSolver and Monkersolver](https://rangeconverter.com/gto-preflop-ranges-for-piosolver-and-monkersolver)

---

## 3. 頻度ベースの読み方

### ミックス戦略の理解

- GTOチャートは各ハンドコンボに対してアクション（ベット/チェック/コール/フォールド）の頻度を示す
- 色分けで「60%ベット・40%チェック」のような混合アクションを表示
- 人間は完璧にランダム化できないため、論理的なキューで近似することが現実的
- 重要: 精確な頻度の暗記より、大まかな傾向とパターンの把握を優先する
- 出典: [Principles of GTO | GTO Wizard](https://blog.gtowizard.com/principles-of-gto/)
- 出典: [GTO Poker - A Beginner's Guide](https://www.rangeconverter.com/articles/gto-poker-beginners-guide)

### EVグラフの解釈

- 正のEV = 平均的にチップを獲得するアクション
- 負のEV = 平均的にチップを失うアクション
- GTOはすべての相手レンジに対して最大EVのアクションを選択する
- EV損失の大きいスポットを優先して修正するのが効率的な学習法
- 出典: [PocketSolver | Understanding GTO](https://www.pocketsolver.com/documentation/understandinggto)
- 出典: [GTO in Poker: Game Theory Optimal Strategy](https://blog.optimuspoker.com/en/what-is-gto-in-poker-understand-the-basics-of-the-strategy)

---

## 4. 次に読むべき本（推薦図書リスト）

### 1. 『Modern Poker Theory』- Michael Acevedo（2019）

- 出版: D&B Poker（2019年）
- GTO原則に基づく徹底的で数学的なガイド
- ソルバーベースの理論を網羅、数千時間のソルバー研究に基づく
- PioSolverの開発にも関与した著者による
- 対象: 中上級者。数式・チャートが多く密度が高い
- 評価: 「現在最も重要なポーカー書籍の一つ」と広く評価される
- 出典: [Amazon - Modern Poker Theory](https://www.amazon.com/Modern-Poker-Theory-unbeatable-principles/dp/1909457892)

### 2. 『Applications of No-Limit Hold'em』- Matthew Janda（2013）

- 出版: Two Plus Two Publishing（2013年）
- 理論的に健全なポーカー戦略の教科書
- ベットサイジングとレンジ構築の理論的根拠を体系的に解説
- 対象: マイクロステークス上位〜2/5ライブ以上のプレイヤー
- 注意: 出版から10年以上経過しているが、基礎理論は今も有効
- 出典: [Amazon - Applications of No-Limit Hold 'em](https://www.amazon.com/Applications-No-Limit-Hold-Matthew-Janda/dp/1880685558)

### 3. 『GTO Poker Simplified』- Dara O'Kearney & Barry Carter（2022）

- GTOに対して天才でなくても理解できるアプローチを提供
- プリフロップレンジ、フロップ/ターン/リバー、マルチウェイポット、ICM、トーナメント、マインドセット、バンクロールを網羅
- ソルバーの専門用語を排除し、即実践できる知見を提供
- 対象: GTO入門者〜中級者。本書の次のステップとして最適
- 出典: [GTO Poker Simplified on Amazon](https://www.amazon.com/GTO-Poker-Simplified-Strategy-tournament/dp/151369913X)

### 4. 『Beyond GTO: Poker Exploits Simplified』- Dara O'Kearney & Barry Carter（2024）

- GTO Poker Simplifiedの続編
- ソルバーを活用して相手の弱点をエクスプロイトする方法を解説
- プリフロップリークとポストフロップリークの特定と修正
- 対典: [Beyond GTO on Amazon](https://www.amazon.com/Beyond-GTO-Exploits-Simplified-Solved-ebook/dp/B0CSZK21FH)

### 5.（参考）『Poker's 1%』- Ed Miller（2014）

- 上位プレイヤーの秘密を解説するポップな入門書
- 注意: 近年のソルバー研究でミラーが主張するピラミッド型のベットパターンは否定されており、内容の一部は旧式
- 批判的に読む必要があるが、考え方の導入として参考にはなる
- 出典: [Important Poker Books In 2026 | SplitSuit Poker](https://www.splitsuit.com/important-poker-books)

---

## 5. トラッキングソフト

### 主要ソフト

| ソフト | 特徴 |
|--------|------|
| PokerTracker 4 | 業界標準の一つ。無料トライアルあり |
| Hold'em Manager 3 | PT4と並ぶ人気ソフト。無料トライアルあり |
| Hand2Note | 高度なフィルタリングに強みがあり上級者向け |
| Poker Copilot | Mac対応が強みのトラッカー |

出典: [Best Poker Tracker - Complete Guide 2026](https://pokersciences.com/en/articles/best-trackers-guide)

### HUD（ヘッズアップディスプレイ）の基本

HUDはリアルタイムでテーブル上に相手の統計を重ねて表示するツール。

- VPIP（Voluntarily Put In Pot）: プリフロップで自発的にポットに参加した割合
  - 例: VPIP 45% = 非常にルーズなプレイヤー
- PFR（Pre-Flop Raise）: プリフロップでレイズした割合
  - 例: VPIP 30% / PFR 5% = 多くのハンドを参加するがほぼ受け身のコーリングステーション
- 推奨開始統計: VPIP、PFR、アグレッションファクターの3つのみ。過剰な統計は判断を妨げる

出典: [Poker HUD: The Ultimate Guide For Beginners](https://hand2noteguide.com/poker/poker-hud/)
出典: [Poker Tracking Software Guide: PokerTracker vs Hold'em Manager](https://pokr.com/article/poker-tracking-software-pokertracker-holdem-manager.html)

### 自分のVPIP/PFRを把握する意義

- 自分のプリフロップ傾向をデータで客観視できる
- GTO Reportsと自分のトラッキングデータを組み合わせることで、どのポジション・状況でズレがあるかを特定できる
- GTO Reportsの比較機能はPokerTracker/HM3のデータをインポートして使うことが前提

---

## 6. 学習ルーチン（時間の目安）

### 週4〜6時間の場合（週3〜4日プレイヤー）

| 曜日 | 内容 | 時間 |
|------|------|------|
| 月 | PokerTrackerで5〜10ハンドのマーク済みハンドをレビュー | 30分 |
| 水 | c-betなど特定トピックの動画1本視聴＋3つのポイントを書き出す | 30分 |
| 金 | GTO Wizardトレーナーまたはハンドディスカッション | 30分 |
| 土日 | 特定コンセプト（ポットオッズ、ブラフキャッチ等）の深掘り | 60分 |

### 1日30〜60分の場合（多忙なプレイヤー）

- セッション前: GTO Wizardトレーナーでウォームアップ（10〜15分）
- セッション後: 印象的なハンドをメモして翌日レビュー

### GTO特化ルーチン（週5〜7時間）

- 1〜2時間/日の学習が理想。GTO Wizardの全機能を活用する
- 1トピックを2週間かけて集中的に学ぶ（例: フロップCベット → 次の2週間はブラインドディフェンス）
- 出典: [How to Create a Poker Study Routine](https://www.tightpoker.com/how-to-build-a-poker-study-routine/)
- 出典: [6-Month GTO Poker Training Plan](https://pokergtosolver.com/en/blog/gto-poker-training-plan)
- 出典: [Studying Poker: Your Weekly Study Guide In 2026 | SplitSuit](https://www.splitsuit.com/ultimate-weekly-poker-study-guide)

---

## 7. 日本語リソース

### 書籍（日本語）

- 世界のヨコサワ著（2024年6月発売）: YouTubeで89万人登録のポーカー教育者による著書。7日間で習得できる構成、300ページ超えフルカラー。初心者向け
- 『トーナメント教科書』: 日本人プロ執筆。ポーカー開始3カ月〜1年の初心者から中級者向け
- 出典: [2025年最新 初心者〜中級者向けポーカー本おすすめ10選](https://tokyo-pokerroom-rent.jp/blog/goods/books)
- 出典: [2025年最新版 ポーカーの勉強におすすめの本](https://poker101.jp/blog/poker-books/)

### YouTube（日本語）

- **世界のヨコサワ**: 海外キャッシュゲームのプレイ映像を日本語解説付きで配信。登録者89万人
- **POKER GUILD（ポーカーギルド）**: GOGなど海外ポーカーシーンの切り抜きと日本語解説が人気

### 学習サイト（日本語）

- [poker101.jp](https://poker101.jp): 初心者〜中級者向けのポーカー攻略情報
- [TrustPlus](https://my.beyond-ss.com/poker-study/): プロ監修のポーカー勉強法解説

---

## 8. コミュニティ（Discord・フォーラム等）

### 日本語コミュニティ

- **DISBOARD ポーカータグ**: 日本語ポーカーDiscordサーバーの検索・一覧ポータル
  - ハンドレビューや交流ができるサーバーが複数存在
  - 450人規模のコミュニティも
  - 出典: [DISBOARDポーカーサーバー一覧](https://disboard.org/ja/servers/tag/%E3%83%9D%E3%83%BC%E3%82%AB%E3%83%BC)

- **3Million Poker Club**: 有料オンラインサロン。コーチ陣による限定配信、わかば講習（初心者向け）を含むレベル別講習プラン、Discord内で自由に交流可能
  - 出典: [3million-pokerclub.com](https://3million-pokerclub.com/)

- **GGPoker オンラインポーカーコミュニティ**: GGPokerが提供する日本語コミュニティ情報
  - 出典: [GGPoker - オンラインポーカーコミュニティ](https://ggpoker.com/ja/blog/beginner-strategy/online-poker-communities/)

### 英語コミュニティ（上級向け）

- **Run It Once**: Phil Galfondが運営するポーカートレーニングサイト。フォーラムも活発で世界最高レベルの議論が行われる
  - 出典: [Run It Once - Ultimate GTO Reading List](https://www.runitonce.com/nlhe/ultimate-gto-reading-list/)

---

## 本書への適用

- **第20章全体**: 本章は「本書の次のステップ」として、GTO Wizard→書籍→トラッキングソフト→コミュニティの順で学習ロードマップを提示する構成が適切
- **GTO Wizardの紹介**: 無料版から始められる点を強調。GTO Reportsで自分のプリフロップ統計を客観的に把握する体験が入口として効果的
- **書籍ロードマップ**: 本書（簡易式）→ GTO Poker Simplified → Modern Poker Theory という3段階の読書ルートを提示
- **学習ルーチン**: 週2〜3時間でも継続できる具体的なスケジュール例を掲載し、読者の挫折を防ぐ
- **日本語リソース**: 世界のヨコサワ、poker101等の日本語コミュニティを積極的に紹介し、国内ユーザーの定着を図る
- **PokerTracker/HM3**: VPIP/PFRを自分で計測することで、本書で学んだ「プリフロップ判断の目安」が数値として現れることを説明するのに適した文脈

---

## 要確認事項

- GTO Wizardの現時点の料金プラン詳細（Starter/Premium/Elite/Ultraの価格、2026年時点）: 公式サイトで最新価格を確認すること
- 世界のヨコサワの書籍タイトル正式名称（検索結果では著者名のみ確認）
- 3Million Poker Clubの月額料金（公式サイトに掲載されているが検索結果では不明）
