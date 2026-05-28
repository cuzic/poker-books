# 第00章 はじめに——Full UCBS-v2 で MTT を制する

本書は Vol2（キャッシュ Light UCBS-v2）を読了した方を対象に、
MTT（マルチテーブルトーナメント）ポストフロップを Full UCBS-v2（13 context × 5 軸）で
精緻に体系化します。
Vol2 の用語（HP/DP/CBS/型1-7/MDF）を共有しながら、depth × SPR × turn の
13 context でキャッシュを大幅に超える精度で MTT を扱います。

## この本が解く問題——Cash と MTT のポストフロップは何が違うか

Vol2 でキャッシュポストフロップを学んだ後、「MTT でも同じ式が使えるか？」という
疑問を持つのは自然なことです。
答えは「使えます——ただし context を MTT 用に切り替える必要があります」です。

Cash と MTT のポストフロップが異なる点は本質的には 2 点だけです。
1 点目は「MTT は SPR が浅いのがデフォルト」であること。
たとえば中盤 SBR=25 なら SRP のフロップ SPR は約 9 と、
キャッシュ（SPR≈16）の半分以下になります。
2 点目は「ICM がフォールド閾値を押し上げる」こと。
バブルや FT では 1 チップでも大きな賞金差があるため、
通常より大きな优位性がないと積極的にコールできません。

この 2 点を押さえれば、MTT ポストフロップはキャッシュの延長で学べます。

## MTT 固有のスタック深度分布（SBR 分布）

SBR（Stack-to-Blind Ratio）は「スタック ÷ ビッグブラインド」で計算する深さの指標です。
MTT では SBR がトーナメントの進行とともに変動します。
序盤（SBR≥100）の深スタック期、中盤（SBR 40〜70）のバブル前後、
終盤（SBR 20〜35）の push 圏直前、という段階を経るのが典型的です。

各 SBR 帯でフロップ SPR が変わり、最適な cbet 頻度も変わります。
たとえば SBR=25 の終盤では β（強い役の追加 lift）が +0.31 と高く、
強い役は積極的に bet できます。
一方 SBR=100 の序盤では α が +0.15 と突出して高く、
全体的に wide な cbet が GTO 最善になります。
このように depth ごとに最適なパラメータが異なるため、13 context が必要なのです。

## Full UCBS-v2 とは——Light v2 との違いと 5 軸の概観

Vol2 では Light UCBS-v2（5 context）を学びました。
Full UCBS-v2 はその完全版で、13 context × 5 軸で cbet 頻度を決定します。
5 軸とは HP（役の強さ）・DP（ドローの価値）・Confidence（信頼度）・
Size（ベットサイズ）・Context（状況）です。

Light v2 と Full v2 の最大の違いは context の粒度です。
Light v2 の `mtt_short`（25〜50bb を一括処理）を、
Full v2 では `mtt_25bb` と `mtt_50bb` に分離します。
3BP も Light v2 の `3bp`（1 種類）から Full v2 の 4 深度（20/25/50/100bb）に細分化します。
この細分化によって、特に mtt_3bp_50bb（WRMSE 8.62%）や
mtt_25bb_turn（WRMSE 7.02%）で飛躍的な精度向上を達成しました。

### Light v2 (5 context) と Full v2 (13 context) の精度比較

以下に Light v2 と Full v2 の精度比較を示します。

Light v2（Vol2）の代表精度:
- mtt_short（25/50bb 一括）: WRMSE 約 14%（25bb と 50bb の平均）
- 3bp（SPR 一括）: WRMSE 約 18〜23%

Full v2（Vol3）の精度:
- mtt_25bb: WRMSE 15.46%（Light と同等）
- mtt_50bb: WRMSE 12.96%（Light より改善）
- mtt_3bp_50bb: WRMSE 8.62%（全 context 中最高精度）
- mtt_25bb_turn: WRMSE 7.02%（Turn 系最高精度）
- mtt_100bb: WRMSE 21.95%（精度低め、注意が必要）
- 全 13 context 平均 WRMSE ≈ 16%

## 本書の読み方——前提知識と各章の位置づけ

本書を読むための前提知識は以下の 2 点です。
まず Vol2（Cash Light UCBS-v2）で学んだ CBS/HP/DP/型1-7/Confidence/DCBS の基礎、
次に Vol1（プリフロップ）で学んだ SBR の概念です。
どちらも本書の随所で前提として使います。

推奨する読み進め方は以下の通りです。
初読者は ch01（5 軸）→ ch02（Confidence）→ ch06〜09（MTT depth 別）→ ch16（例題）
という順に読むと体系が整理されます。
実戦でリファレンスとして使う場合は
付録 A（13 context 完全表）→ 付録 C（チートシート）を手元に置くと便利です。

前提用語の確認として、HP・DP・CBS・型1〜7・MDF は Vol2 の定義をそのまま使います。
念のため ch01 の冒頭でも再確認します。

## 本書 16 章 + 3 付録の構成

本書は全 16 章と 3 つの付録で構成されます。

前半（ch00〜ch05）では Full UCBS-v2 の骨格を解説します。
ch01 で 5 軸全体を概観し、ch02 で Confidence の判定詳細、
ch03 で Size 軸（MTT=33% 固定）、ch04 で 13 context の使い分け、
ch05 でポジション補正を学びます。

中盤（ch06〜ch11）では MTT 各 depth と特殊シナリオを扱います。
ch06〜09 が MTT 25/50/100/200bb の深度別 cbet 戦略、
ch10 が 3BP IP 4 deep シリーズ、ch11 が Turn cbet 4 context です。

後半（ch12〜ch16）では守備・例外・限界・ICM・例題を扱います。
ch12 で Full DCBS（4 context の守備）、ch13 で例外ルール 4 つ、
ch14 で苦手領域と限界、ch15 で ICM 補正、ch16 で 20 問の例題集です。

付録 A は 13 context パラメータ完全表、付録 B は DCBS 4 context 表、
付録 C は実戦用チートシートです。

## シリーズ全体図——Vol1〜Vol3 の連携

本シリーズの巻構成は以下の通りです。

Vol1（プリフロップ）: Score 式でハンドを評価し、オープン/コール/3bet を判断します。
Vol2（Cash Light UCBS-v2）: フロップで CBS を計算し、キャッシュの cbet/defense を判断します。
Vol3（本書 Full UCBS-v2）: MTT 全 depth × 3BP × Turn を 13 context で精緻化します。

Vol2 の用語（HP/DP/CBS/型1-7）は Vol3 でそのまま使います。
Vol3 で新たに学ぶ概念は α（context uniform lift）・β（強い役の追加 lift）・
off_slowplay/off_trash/off_premium（役柄カテゴリ補正）・pos_lift（ポジション補正）・
ax_range_lift（A-x range bet）・DCBS 4 context です。

本書を読み終えた後は、MTT のほぼすべてのポストフロップシナリオで
「式 1 本と 13 context の選択」だけで cbet 頻度を暗算できるようになります。
暗記対象の総計は 128 数値 + 1 式 + 4 例外です。

### 暗記対象の概算

128 数値という数字は多く見えますが、段階的に習得できます。

Vol2 との共通部分（18 数値）:
HP テーブル 6 値、DP テーブル 4 値、BASE_FREQ 8 セル。

Vol3 で追加する部分（110 数値）:
13 context × 各 7 パラメータ（α/β/off×3/SB lift/wide lift）が ~78 数値、
DCBS 4 context の base 表と kicker offset 表が 32 数値です。
各章で 1 context ずつ習得していけば、
読み終える頃には自然に身についています。
