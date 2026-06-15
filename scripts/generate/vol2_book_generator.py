"""
vol2_book_generator.py
『迷わないポーカー Vol2 — ポストフロップ完全版』(MATCHA Framework 編) 章原稿ジェネレーター

設計方針:
  - MATCHA Score 公式 (Score = Grid + DV*mult + 2*oc + 4*pot - 2*bs) を本核に再構成
  - 12 cells Grid と例外 11 ルールは本書の魔法核心
  - 数値は MATCHA_SCORE_FINAL.md / HUGE_LOSS_V3.md / INSIGHTS_2026-06-08_*.md から引用
  - 用語は TERMINOLOGY.md に厳格遵守 (エア / アンダーペア / トップペア以上 / 2P+)

実行: uv run scripts/generate/vol2_book_generator.py
"""
from __future__ import annotations
from pathlib import Path

# ===================================================================
# パス設定
# ===================================================================
ROOT    = Path(__file__).parent.parent.parent
OUT_DIR = ROOT / 'vol2-postflop' / 'chapters'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ===================================================================
# MATCHA Score 公式 SSOT
# ===================================================================

# 12 cells Grid (4 カテゴリ × 3 board)
# tier index: 0=エア, 1=アンダーペア, 2=TP+, 3=2P+
# board index: 0=dry, 1=paired, 2=wet
GRID = [
    [ 3,  5,  1],   # エア
    [18, 40, 10],   # アンダーペア
    [38, 10, 31],   # トップペア以上
    [25, 28, 23],   # 2P+
]

TIER_NAMES   = ['エア', 'アンダーペア', 'トップペア以上', '2P+']
BOARD_NAMES  = ['dry', 'paired', 'wet']

# DV street multiplier
MULT_FLOP, MULT_TURN, MULT_RIVER = 3, 2, 0

# pot 値
POT_VAL = {'SRP': 0, 'vs CR': 2, '3BP': 2, '4BP': 4}

# bs 値
BS_VAL = {
    'small_33':    0,
    'med_75p':     1,
    'med_100p':    2,
    'overbet':     3,
    'overbet_185': 4,
    'allin':       5,
}

# 係数
W_DV, W_OC, W_POT, W_BS = None, 2, 4, 2   # DV は street 別
T_CALL  = 14
T_RAISE = 43

# 性能数値 (audit 結果)
AUDIT = dict(
    n_spots   = 154216,
    avg_loss  = 0.3587,
    huge_pct  = 1.49,
    old_avg   = 0.4165,
    old_huge  = 1.77,
    avg_delta = -14,
    huge_delta= -16,
)

# 街別 huge%
STREET_HUGE = {'flop': 1.10, 'turn': 1.69, 'river': 2.55}

# pot 別 huge%
POT_HUGE_NEW = {'SRP': 2.62, 'vs CR': 1.45, '3BP': 1.45, '4BP': 0.53}
POT_HUGE_OLD = {'SRP': 1.99, 'vs CR': 1.02, '3BP': 0.83, '4BP': 3.37}

# 例外 11 ルール (huge_loss 5 + 確実 cell 3 + Turn CR専用 2 + River Donk 1)
# ※ 旧 ex9/ex10 (DEF共通) は DEF T_raise=49 閾値補正で吸収 (ex11→ex9, ex12→ex10, ex13→ex11 に繰り上げ)
EXCEPTIONS = [
    dict(num=1, tier='トップペア以上', board='wet',    street='flop',  pot='SRP',        pred='call',  best='fold',           n=350,   avg=14.5,
         note='wet 板の TP+ は SRP オーバーベット受けで fold (TPR 含む)'),
    dict(num=2, tier='2P+',            board='wet',    street='river', pot='SRP',        pred='call',  best='raise',          n=258,   avg=15.4,
         note='river の wet × SRP は強ハンドで value raise'),
    dict(num=3, tier='アンダーペア',     board='wet',    street='turn',  pot='vs CR',      pred='call',  best='fold',           n=179,   avg= 9.9,
         note='wet × turn × CR/donk 受けはアンダーペア fold'),
    dict(num=4, tier='エア',           board='wet',    street='turn',  pot='3BP',        pred='fold',  best='call',           n=159,   avg= 9.5,
         note='3BP × wet × turn は bluff catch (相手の bluff 多)'),
    dict(num=5, tier='2P+',            board='wet',    street='flop',  pot='SRP',        pred='call',  best='fold',           n=125,   avg=12.5,
         note='2P × wet 大ベット受けは諦める'),
    # --- 確実 cell 例外 ---
    dict(num=6, tier='2P+',            board='paired_low (X<5)', street='any', pot='any', pred='any', best='確実 bet',       n=3,     avg=0.0,
         note='paired_low (例: 2-2-4, 3-3-2) で 2P+ は trips 対策不要。 公式無視して bet 確定 (SD 8pp)'),
    dict(num=7, tier='アンダーペア',     board='monotone', street='any', pot='any',         pred='any',  best='確実 check',     n=7,     avg=0.0,
         note='3 同 suit board でアンダーペアは flush に負ける。 Score 値に関わらず check'),
    dict(num=8, tier='エア',           board='monotone', street='any', pot='any',         pred='any',  best='check 寄り',     n=7,     avg=0.0,
         note='monotone でエアの bluff は禁物。 公式 bet 判定を抑制'),
    # --- Turn CR 専用例外 (⚠️ Donk には適用しない) ---
    dict(num=9, tier='アンダーペア/TP+', board='dry',     street='turn', pot='vs CR only',      pred='call',  best='fold',    n=338,   avg=3.60,
         note='Turn vs CR で dry × アンダーペア/TP+ は villain range が strong すぎ。 ミドル GTO FOLD 71.5% / TP+ FOLD 56%。 ⚠️ Donk 不可'),
    dict(num=10, tier='トップペア以上', board='wet',     street='turn', pot='vs CR only',      pred='call',  best='fold',    n=215,   avg=2.40,
         note='Turn vs CR で wet × TP+ は villain range (straight/flush) に劣位。 GTO FOLD 62.3%。 ⚠️ Donk 不可'),
    # --- River Donk 専用例外 ---
    dict(num=11, tier='2P+ (trips/FH/quads)', board='paired', street='river', pot='vs Donk only', pred='call', best='raise (value)', n=66, avg=2.51,
         note='River vs Donk で paired × trips以上は GTO RAISE 100%。 villain donk range は弱い'),
]

# ===================================================================
# ヘルパ
# ===================================================================
def write(filename: str, content: str):
    path = OUT_DIR / filename
    path.write_text(content, encoding='utf-8')
    print(f'  wrote: {filename} ({len(content):,} chars)')

def grid_md_table() -> str:
    """12 cells Grid の markdown 表"""
    out = ['|           | dry | paired | wet |',
           '|-----------|----:|-------:|----:|']
    for i, name in enumerate(TIER_NAMES):
        d, p, w = GRID[i]
        out.append(f'| {name} | {d} | {p} | {w} |')
    return '\n'.join(out)

def score_calc(tier_idx: int, board_idx: int, dv: int, street: str,
               oc: int, pot: str, bs_key: str) -> tuple[int, str]:
    """暗算手順を文字列で返す"""
    g = GRID[tier_idx][board_idx]
    mult = {'flop': 3, 'turn': 2, 'river': 0}[street]
    pot_v = POT_VAL[pot]
    bs_v  = BS_VAL[bs_key]
    score = g + dv * mult + W_OC * oc + W_POT * pot_v - W_BS * bs_v
    detail = (f'Grid[{TIER_NAMES[tier_idx]}][{BOARD_NAMES[board_idx]}]={g}'
              f' + DV×mult={dv}×{mult}={dv*mult}'
              f' + 2×oc={2*oc} + 4×pot={4*pot_v} − 2×bs={2*bs_v}'
              f' = **{score}**')
    return score, detail

# ===================================================================
# 序章 (ch00)
# ===================================================================
def gen_ch00() -> str:
    return f"""\
# 第 0 章　ポストフロップを 5 秒で解く

## 0.1 本書は「1 つの式」でポストフロップを解く

本書は、 ポストフロップ判断を **1 つの公式 + 12 個の数字 + DEF 閾値補正 + 11 の例外ルール** に圧縮します。

```
Score = Grid[カテゴリ][board] + DV × mult[street]
      + 2 × オーバーカード + 4 × pot − 2 × bs

if Score ≥ {T_RAISE}: レイズ
elif Score ≥ {T_CALL}: コール
else:                  フォールド
```

この公式の名前は **MATCHA Score** です。

## 0.2 暗記項目は 56 個

| 項目 | 数 |
|------|---:|
| 公式: 12 cells Grid + 加算式 | 13 |
| DEF 閾値補正: vs CR/Donk 時 T_raise=49 (通常 43) | 1 |
| 例外: 11 ルール (huge_loss 5 + 確実 cell 3 + Turn CR 専用 2 + River Donk 1) | 11 |
| 境界ハンド (sub-family × カテゴリ の outlier) | ~30 |
| ポット補正 + スタック補正 | ~8 |
| **計** | **~64 項目** |

## 0.3 公式の精度

GTO データ全 **{AUDIT['n_spots']:,} spots** で検証した結果:

| 指標 | 値 |
|---|---:|
| avg loss (BB) | **{AUDIT['avg_loss']:.4f}** |
| huge% (>5 BB) | **{AUDIT['huge_pct']:.2f}%** |
| Grid cells | **12** |
| カテゴリ 数 | **4** |

特に **4BP では huge% を 0.53%** に抑制。 4BP を含む統合 audit での最大の成果です。

## 0.4 「5 秒で解く」 とはどういうことか

公式は加算と引き算だけです。 9 + 6 + 2 = 17 のような単純な暗算で済みます。
熟練者は 5 秒、 慣れた読者なら 10 秒で答えが出ます。

### 暗算手順 (3 ステップ)

1. **カテゴリ と board を判定** → Grid から数字を 1 つ拾う (12 cells のどれか)
2. **加算項を足す** (DV × mult、 2 × overcards、 4 × pot)
3. **減算項を引く** (2 × bs)、 閾値 14 / 43 と比較

### 具体例

board: Kh 7c 2d (dry)、 hand: AhTh、 street: flop、 pot: SRP、 bs: med_100p

- カテゴリ = エア (no_made_hand)
- Grid[エア][dry] = **3**
- DV = 0 (no draw)、 0 × 3 = 0
- oc = 1 (A > K)、 2 × 1 = **2**
- pot = SRP = 0、 4 × 0 = 0
- bs = med_100p = 2、 −2 × 2 = **−4**
- Score = 3 + 0 + 2 + 0 − 4 = **1**
- 1 < 14 → **フォールド**

## 0.5 本書の構成

| 部 | 章 | 内容 |
|---|---|------|
| 序章 | 0 | この章 |
| 第 1 部 | 1-5 | MATCHA Score 公式の各要素 |
| 第 2 部 | 6-9 | 12 cells Grid の核心 / 境界 / 例外 11 ルール + DEF 閾値補正 |
| 第 3 部 | 10-12 | 公式の理論的背景 (4 つの判定軸) |
| 第 4 部 | 13-16 | ポット種別 (SRP / 3BP / 4BP / vs CR) |
| 第 5 部 | 17-19 | スタック深度 + Cash/MTT パラメータ差 |
| 第 6 部 | 20-23 | ICM / バブル / MW / テーブルサイズ別 (定性) |
| 第 7 部 | 24-26 | 境界総覧 / ドリル抜粋 / チートシート |
| 付録 | A-D | 早見 / 最適化経緯 / 4BP audit / データ取得 |

## 0.6 連携アプリ — poker-drill

本書の数値は計算しただけでは身につきません。 連携アプリ **poker-drill**
(<https://poker-drill.vercel.app>) で 200+ cards のドリルを反復してください。

- 基本 (32 例題)
- ヒント大 (60 spots、 軸判定済み + 表参照)
- 応用 (60 spots、 シナリオから軸判定)
- 境界 spot ドリル (50 spots)

## この章で覚える項目 (3 items)

1. 公式: `Score = Grid + DV × mult + 2×oc + 4×pot − 2×bs`
2. 閾値: ≥ {T_RAISE} レイズ / ≥ {T_CALL} コール / それ未満フォールド
3. 暗算手順: カテゴリ+board で Grid → 加算 → 減算 → 比較
"""

# ===================================================================
# 第 1 部 (ch01-05)
# ===================================================================
def gen_ch01() -> str:
    return f"""\
# 第 1 章　公式の全体像

## 1.1 公式そのもの

本書の中核は次の 1 行です。

```
Score = Grid[カテゴリ][board]
      + DV × mult[street]
      + 2 × overcards
      + 4 × pot
      − 2 × bs

if Score ≥ {T_RAISE}: レイズ
elif Score ≥ {T_CALL}: コール
else:                 フォールド
```

すべての変数は整数値で、 暗算可能です。

## 1.2 各項目の役割

| 項 | 範囲 | 由来 |
|---|---|---|
| `Grid[カテゴリ][board]` | 1〜40 | hand と board の interaction (本書の魔法核心) |
| `DV × mult` | 0〜12 | draw value × Rule of 4/2 整数化 |
| `2 × overcards` | 0〜4 | hero のカードがボード最高 rank より上の枚数 |
| `4 × pot` | 0〜16 | pot 種別 (SRP/vs CR/3BP/4BP) |
| `−2 × bs` | 0〜−10 | 相手の bet サイズが大きいほど不利 |

スコア理論上の最大は約 40+12+4+16 = 72、 最小は約 1−10 = −9 ですが、
実戦の大半は **0〜50** に収まります。

## 1.3 判定の閾値

| Score | 行動 |
|------:|------|
| ≥ {T_RAISE} | **レイズ** (バリュー / ブラフレイズ) |
| {T_CALL}〜{T_RAISE-1} | **コール** (ショーダウン / ブラフキャッチ) |
| < {T_CALL} | **フォールド** |

閾値 14 と 43 は data から決まった整数値です。 半端な値ですが、 暗算では
「15 弱・40 強」と覚えれば十分です。 詳細は を参照。

## 1.4 公式が解いている問題

本公式は、 ポストフロップの **「相手の bet 受けで call / raise / fold を出す」**
状況を一括で扱います。 すなわち:

- ベット側 (hero がベット / レイズする場面)
- コール側 (hero が受ける場面)
- SRP / 3BP / 4BP / vs CR

これら全部が **1 つの式** で解けます。

## 1.5 5 つの判定軸との関係

MATCHA Framework では、 ポストフロップ判断は次の 5 軸で記述されます (詳細は第 3 部)。

1. レンジ分布 (board の形状)
2. ハンドストレングス
3. ベットサイジング
4. SPR
5. エクイティバケット

MATCHA Score 公式はこの 5 軸を **整数の重み付け和** に圧縮したものです。
「エクイティバケット」は本公式に数値として吸収されており、 独立の暗記対象ではありません。

## 1.6 性能まとめ

GTO データ全 {AUDIT['n_spots']:,} spots での検証結果:

- **avg loss = {AUDIT['avg_loss']:.4f} BB**
- **huge loss% (>5 BB) = {AUDIT['huge_pct']:.2f}%**

### 街別 huge%

| street | huge% |
|---|---:|
| flop | {STREET_HUGE['flop']:.2f}% |
| turn | {STREET_HUGE['turn']:.2f}% |
| river | {STREET_HUGE['river']:.2f}% |

river が最も high です。 例外 11 ルールの #2 (2P+ × wet × river × SRP)
で大幅救済します。

### pot 別 huge%

| pot | huge% |
|---|---:|
| SRP | {POT_HUGE_NEW['SRP']:.2f}% |
| vs CR | {POT_HUGE_NEW['vs CR']:.2f}% |
| 3BP | {POT_HUGE_NEW['3BP']:.2f}% |
| **4BP** | **{POT_HUGE_NEW['4BP']:.2f}%** ★ |

**4BP huge% {POT_HUGE_NEW['4BP']:.2f}%** は本公式の最大の成果。 「2P+」 (2P〜SF) を 1 階層に
統合したことで、 4BP の高 EV spots が的確に捕らえられます。

## この章で覚える項目 (3 items)

1. 公式 1 行 (`Score = Grid + DV × mult + 2×oc + 4×pot − 2×bs`)
2. 閾値 `≥{T_RAISE} レイズ / ≥{T_CALL} コール`
3. avg loss = {AUDIT['avg_loss']:.4f} BB / huge = {AUDIT['huge_pct']:.2f}%
"""

def gen_ch02() -> str:
    return f"""\
# 第 2 章　カテゴリ — ハンドストレングス 4 段階

## 2.1 4 段階の階層

MATCHA Score では hand を 4 段階の **カテゴリ** に分類します。

| index | カテゴリ 名 | 含まれるハンド (mv_cat) |
|---:|------|------|
| 0 | **エア** | no_made_hand、 king_high、 ace_high |
| 1 | **アンダーペア** | second_pair、 third_pair、 underpair、 low_pair |
| 2 | **トップペア以上** (TP+) | top_pair、 overpair |
| 3 | **2P+** | two_pair、 set、 trips、 straight、 flush、 fullhouse、 quads、 straight_flush |

## 2.2 各 カテゴリ の定義詳細

### エア (カテゴリ 0)

ボードと噛み合わないハンド全般です。

- no_made_hand: high card にすらならない (例: J8o on Kh 7c 2d)
- king_high: K-high の no pair (例: AKo on Q-7-2、 board K より下のキッカー)
- ace_high: A-high の no pair (例: AKo on Q-7-2、 hero に A あり)

draw が付いていても「メイドはエア」として扱います。 draw 価値は DV で別途加算
されるため、 カテゴリ には含めません。

### アンダーペア (カテゴリ 1)

ボードのトップではないペアです。

- second_pair: ボード 2 位の rank とのペア (例: K-7-2 で 77)
- third_pair: ボード 3 位の rank とのペア
- underpair: ボード最低 rank より下のポケットペア (例: K-7-2 で 55)
- low_pair: ボード最低 rank とのペア

### トップペア以上 (TP+、 カテゴリ 2)

ボードのトップを叩いた / ボードを上回るペアです。

- top_pair: ボード最高 rank とのペア (例: K-7-2 で AK、 KQ、 KJ ...)
- overpair: ボードを越えるポケットペア (例: K-7-2 で AA、 QQ)

### 2P+ — ツーペア以上のメイドハンド (カテゴリ 3)

本書では **2P+** (ツーペア以上、 英語業界の "two pair plus" の略記) を 1 つの カテゴリ
として扱います。 含まれる役は以下の 8 種類すべて:

- **2P** (ツーペア): 例 K-7-2 で K7、 72
- **セット**: ポケットペア × ボードヒット (例 7-K-2 で 77)
- **トリップス**: ボードペア × hand の rank (例 K-K-2 で AK)
- **ストレート / フラッシュ / フルハウス / クアッズ / ストレートフラッシュ**

**初出につき詳しく**: 2P+ は「ツーペア以上」 を表す本書略記。 TP+ (トップペア以上)
と対称的な表記です。 旧来の「ストロング+」 「ナッツメイド」 などの呼び方を集約。
以降本書では **2P+** と短縮表記します。

4BP の huge% を 3.37% → 0.53% (−85%) にした立役者で、 本書最大の発見の 1 つです。

## 2.3 なぜ 4 段階で十分か (data 駆動の発見)

旧来は 6 階層 (ナッツ / ストロング / 2P / TP+ / ミドル / エア) でしたが、
audit で 6 階層 vs 4 階層を直接比較した結果:

| カテゴリ 数 | Grid cells | avg loss |
|---:|---:|---:|
| 6 (旧) | 18 | 0.3722 BB |
| 5 | 15 | 0.4084 BB (集約過剰) |
| **4 (本書)** | **12** | **0.3587 BB ★** |
| 7 (細分化) | 21 | 0.3874 BB (overfit) |

**4 階層に集約した方が性能が良い** のです。 これは「2P〜SF を統合した
2P+」 が情報損失なしで暗記コストを 1/2 にしたためです。

集約のキーは「実 GTO ではナッツメイド (FH / quads) も 2P もどちらも value bet
の主役で、 出力アクションがほぼ同じ」 という観察。 細分化しても判断は変わりません。

## 2.4 カテゴリ 判定の手順

ハンドを見たら、 上から順に判定します。

1. **2P+か?** (ツーペア / set / トリップス / straight / flush / FH / quads / SF)
   - はい → カテゴリ 3、 終了
2. **トップペア以上か?** (top_pair / overpair)
   - はい → カテゴリ 2、 終了
3. **ペアか?** (second_pair〜low_pair / underpair)
   - はい → カテゴリ 1 (アンダーペア)、 終了
4. それ以外 → カテゴリ 0 (エア)

draw だけのハンド (例: T9 on K-Q-2、 OESD) は **エア**。 draw 価値は DV で加算。

## 2.5 mv_cat 17 種類との対応表

GTO ソルバー 内部の `mv_cat` (made-value category) との対応:

| mv_cat | 本書 カテゴリ |
|---|---|
| no_made_hand | エア |
| king_high / ace_high | エア |
| second_pair / third_pair / underpair / low_pair | アンダーペア |
| top_pair / overpair | トップペア以上 |
| two_pair | 2P+ |
| set / trips | 2P+ |
| straight / flush | 2P+ |
| fullhouse / quads / straight_flush | 2P+ |

17 種類が 4 階層に集約されています。

## 2.6 旧 6 階層 → MATCHA 4 カテゴリ 対応表

ポーカーの古典文献 (Sklansky-Malmuth / Janda / 旧 MATCHA Framework 等) では
hand strength を **6 階層** に細分化していました。 本書はこれを 4 カテゴリ に集約します。

| 旧 6 階層 | 旧定義 | MATCHA 4 カテゴリ | 集約理由 |
|---|---|---|---|
| ナッツメイド | FH / quads / SF | **2P+** | GTO 出力同一 (value heavy) |
| ストロング | set / flush / straight | **2P+** | 同上 |
| ツーペア | 2P 単独 | **2P+** | 4BP で 2P 以上同挙動 |
| トップペア以上 | top_pair / overpair | **トップペア以上 (TP+)** | 維持 |
| アンダーペア | 2nd / 3rd / underpair / low | **アンダーペア** | 維持 |
| エア | high card / king / ace_high | **エア** | 維持 |

### 上位 3 階層を「2P+」 に統合した data 駆動根拠 (簡潔版)

audit で次の発見:

- **4BP × set vs 4BP × 2P**: 両者とも slowplay 率 96%、 GTO 出力ほぼ同一
- **dry × ナッツメイド vs dry × ストロング**: 両者とも value bet 強行、 細分化情報過多
- **paired × 2P**: 0-30% bet (slowplay)、 ナッツと同じ check 寄り挙動

→ 上位 3 階層を細分化しても GTO 出力が変わりません。 「2P+」 に集約する
ことで Grid 18 → Grid 12 に圧縮し、 暗記コストを 1/3 削減できます (詳細根拠は第 11 章)。

### 集約の audit 効果

| 構成 | Grid cells | avg loss | 4BP huge% |
|---|---:|---:|---:|
| 旧 6 階層 (細分化) | 18 | 0.3722 BB | 3.37% |
| **MATCHA 4 カテゴリ (本書、 上位統合)** | **12** | **0.3587 BB** | **0.53%** ★ |

→ **4BP huge% を −85% 削減** (本書最大成果)。 「2P+」 統合が
立役者であることは付録 C で詳述します。

### Sklansky Hand Groups (1976) との関係

旧来の preflop ハンド分類 Sklansky Hand Groups (8 群):

- 群 1-2 (AA / KK / AKs 等) → 本書 **2P+** 系譜
- 群 3-4 (TT / 99 / AQs 等) → **トップペア以上** 系譜
- 群 5-7 (中位 broadway / SC) → **アンダーペア** 系譜
- 群 8 以下 (rag) → **エア** 系譜

ただし Sklansky は preflop 分類、 本書は postflop カテゴリ。 詳細は第 13 章
(旧来理論との橋渡し) で扱います。

## この章で覚える項目 (5 items)

1. カテゴリ 4 段階の順序 (エア / アンダーペア / TP+ / 2P+)
2. エアは「ペアもないハンド全部」
3. アンダーペアは「トップ以外のペアと underpair」
4. TP+ は「top pair と overpair」
5. 2P+は「2P 以上全部」 (旧 6 階層の上位 3 つ統合)
"""

def gen_ch03() -> str:
    return f"""\
# 第 3 章　board — 3 タイプ

## 3.1 3 タイプの定義

MATCHA Score では board を **dry / paired / wet** の 3 タイプに分類します。

| タイプ | 定義 |
|---|---|
| **paired** | 同じ rank が 2 枚以上 (ペア板) |
| **wet** | モノトーン (3 枚同 suit) または connected (span ≤ 4) |
| **dry** | 上記以外 (unpaired かつ非 connected かつ非 monotone) |

判定は **フロップの 3 枚のみ** を見ます。 ターン・リバーの追加カードは無視。

## 3.2 判定の手順 (3 ステップ)

```
1. 同 rank が 2 枚以上 → paired
2. モノトーン (3 枚同 suit) または span ≤ 4 で連結 → wet
3. それ以外 → dry
```

### 「connected (span ≤ 4)」 の意味

3 枚の rank を昇順に並べたとき、 **最大と最小の差 (span) が 4 以下** (= 5 連続 rank の窓内)
の場合を connected と呼びます。 隣接カード間の差は問いません。

例:
- T-9-8 → span 2 (10−8)、 wet (connected)
- T-9-7 → span 3 (10−7)、 wet (5 窓 T9876 に収まる)
- T-9-6 → span 4 (10−6)、 wet ← 隣接差が 3 でも wet
- T-9-5 → span 5 (10−5)、 dry (5 窓に収まらない)

**注意**: 隣接カード差 (adj gap) ではなく span (max − min) で判定します。
T-9-6 は隣接差が 1 と 3 ですが、span=4 ≤ 4 なので **wet** です。
GTO データ検証 (10 境界ボード) で cbet 平均 27.2% ≈ wet ベースライン (31.7%) と確認。

## 3.3 具体例

| board | 判定 | 理由 |
|---|---|---|
| Kh 7c 2d | **dry** | 非 paired、 非 connected、 非 mono |
| Kh Kc 7d | **paired** | K が 2 枚 |
| Th 9h 8s | **wet** | span 2 で連結 |
| Th 9h 4h | **wet** | モノトーン |
| Ah Ks 4d | **dry** | span 10、 非 connected |
| Qh Jc Th | **wet** | span 2 で連結 |
| 7h 5c 4d | **wet** | span 3 で連結 |
| Qh 9c 8d | **wet** | span 4 (12−8=4) ≤ 4 で connected |
| Tc 9h 6d | **wet** | span 4 (10−6=4) ≤ 4、 隣接差 1,3 でも wet |
| Tc 9h 5d | **dry** | span 5 (10−5=5) > 4 で非 connected |
| Ah 8s 3d | **dry** | span 11、 非 connected |
| Ah 3s 2d | **wet** (A-low 例外) | wheel draw あり → wet 扱い (後述 3.6) |
| Ah 5s 4d | **wet** (A-low 例外) | wheel draw あり → wet 扱い (後述 3.6) |

## 3.4 旧 6 ボードファミリーとの対応

| 旧 family | 新分類 |
|---|---|
| dry_high (A/K/Q high dry) | dry |
| low_dry (低 rank dry) | dry |
| dynamic (中程度 connector) | wet |
| dynamic_2tone (2 tone connected) | wet |
| monotone | wet |
| paired | paired |

旧 6 → 新 3 で集約していますが、 audit で性能差は出ませんでした (Grid 12 が Grid 18
より優秀)。 詳細は第 10 章 (Range Morphology) で扱います。

## 3.5 ターン以降の board 変化

board 判定は **フロップ固定** が原則ですが、 ターンで board structure が劇的に
変わる場合は注意が必要です。

- ターンで rank がペアになった (例: K72 → K72-7) → 例外 11 ルール候補に
- ターンで flush draw 完成 (例: K72 → K72-h で 3 tone) → DV が変化、 board は dry 維持

board 判定そのものは変えず、 DV と例外ルールで吸収するのが本書の方針です。

## 3.6 A-low board 例外 (GTO 実測)

**A-low board** (フロップに A があり、 他の 2 枚が両方 ≤ 6) は span が 9〜12 と大きく
通常ルールでは dry に分類されますが、 GTO 実挙動は wet と同等です。

### 根拠: BTN cbet 実測値 (GTO Wizard)

| カテゴリ | 代表例 | BTN cbet 平均 |
|---|---|---:|
| dry baseline (K/Q high) | K72, K83, Q83 | 66.1% |
| **A-low board** | A32, A43, A54, A65 | **47.7%** |
| wet baseline | 987, T96, 654 | 42.7% |

A-low board の BTN cbet (47.7%) は wet baseline (42.7%) に **5pp 差**、
dry baseline (66.1%) に **18pp 差**。 wet 扱いが妥当です。

### 理由: wheel straight draw

A はポーカーでは高カード (A=14) と同時に低 ace (A=1) としても機能します。
A-3-2 フロップでは **4 か 5 が来ると A-2-3-4-5 (wheel straight) が完成**します。
この wheel draw の存在が board texture を湿らせ、 BTN が cbet できるハンドの
range を wet board 並みに絞ります。

A-5-4 では 2/3 で wheel 完成、 6/7 でも複数の straight が射程に入るため同様です。

### 実用ルール

```
A-low board: A と ≤6 のカード 2 枚が揃う → wet 扱い

wet 例: A32, A42, A43, A52, A53, A54, A62, A63, A64, A65
dry 維持例: A83, A84, A94 (7 以上のカードがあれば dry のまま)
```

A84 のように 7 以上のカードが入ると wheel draw の強度が大幅に落ちるため、
通常の dry として扱います。

## 3.7 board 判定の落とし穴

- **A-low board (A + ≤6 の 2 枚)**: span 大でも **wet** (3.6 参照)
- **A-high mid board (A83, A84 等)**: span 大かつ 7 以上あり → dry のまま
- **2 tone**: それ自体は wet ではない (mono のみ wet)、 ただし span ≤ 4 なら wet
- **rainbow + connected**: span ≤ 4 なら wet (suit と独立)
- **3 broadway (JTQ)**: span 2 (12−10=2) なので wet
- **AK7 rainbow**: span 7 (14−7=7) > 4 で dry
- **T-9-6**: span 4 (10−6=4) ≤ 4 → wet (隣接差 3,1 は無関係)

## 3.8 古典ボード 7 分類 → MATCHA 3 分類 集約表

ポーカーの古典文献 (Janda "Applications"、 Acevedo "Modern Poker Theory" 等) では
board を **7 分類** に細分化していました。 本書はこれを 3 分類に集約します。

| 古典 7 分類 | 典型例 | MATCHA 3 分類 | 集約根拠 |
|---|---|---|---|
| Dry rainbow (A/K-high) | Kh 7c 2d、 Ah 8s 3d | **dry** | unpaired + 非 connected + rainbow |
| Dry connected (低 gap) | 7-5-2 (span 5、 非 wet) | **dry** | span > 4 で connected ではない (低 rank dry) |
| Wet (中 connector) | T-9-8、 7-6-5 | **wet** | span ≤ 4 で連結 |
| Monotone (3 同 suit) | 9h 7h 3h | **wet** | mono は wet 扱い (flush 警戒) |
| Two-tone (connected) | T-9-8 2tone (h-h-c) | **wet** | span ≤ 4 で wet (suit 別問わない) |
| Paired high (K-K-X 等) | K-K-7、 A-A-2 | **paired** | 同 rank 2 枚以上 |
| Paired low (7-7-X 等) | 7-7-2、 4-4-3 | **paired** | 同 rank 2 枚以上 |

### 集約後の各分類の例 board

| 新分類 | 古典分類混合例 |
|---|---|
| **dry** (4 系混合) | Kh 7c 2d (dry rainbow) / Ah 8s 3d (A-high dry) / 7-5-2 (low dry) |
| **paired** (2 系統合) | K-K-7 (paired high) / 7-7-2 (paired low) |
| **wet** (3 系統合) | Q-9-8 (connected) / 9h 7h 3h (mono) / Th 9h 4s (2tone wet) |

### 判定手順 (3 分類版、 古典 7 → 3 早見)

```
1. 同 rank 2 枚以上 → paired (古典 paired high / paired low 統合)
2. span ≤ 4 (5 窓内 3 枚) または monotone → wet (古典 wet / mono / 2tone 統合)
3. 上記以外 → dry (古典 dry rainbow / dry connected 統合)
```

### 集約根拠 (data 検証)

audit で 7 分類 → 3 分類への集約は性能を悪化させない:

| 構成 | Grid cells | avg loss |
|---|---:|---:|
| 7 board family × 4 カテゴリ | 28 | 0.3611 BB |
| 6 board family × 4 カテゴリ | 24 | 0.3654 BB |
| **3 board family × 4 カテゴリ (本書)** | **12** | **0.3587 BB ★** |
| 2 board family × 4 カテゴリ | 8 | 0.3892 BB |

**3 分類で 90% カバー**。 sub-family の差は **Grid 値の hand × board interaction**
(例えば「ミドル × paired = 40 vs ミドル × wet = 10」) で吸収されるため、 board 軸
細分化は不要 (詳細は第 10 章)。

### 旧来理論との対応詳細

古典 7 分類は Janda の "Applications of No-Limit Hold'em" や Acevedo の
"Modern Poker Theory" で標準的に使われる分類です。 本書はこれを 3 分類に
圧縮しましたが、 各古典分類の「本書での扱い」 は第 13 章 (旧来理論との橋渡し)
に詳細な対応表があります。

## この章で覚える項目 (5 items)

1. 3 タイプ: dry / paired / wet (古典 7 分類を集約)
2. 判定手順: paired → wet → dry の順
3. wet の条件: モノトーン または span ≤ 4 (= max_rank − min_rank ≤ 4)
4. フロップ 3 枚で固定 (ターン以降は変えない)
5. **A-low 例外**: A + ≤6 の 2 枚 → wet (BTN cbet 実測 ~48% ≈ wet 水準)
"""

def gen_ch04() -> str:
    return f"""\
# 第 4 章　DV と street multiplier — Rule of 4/2 の整数化

## 4.1 DV (Draw Value) の値

ヒーローが持っている draw の強さを 0〜4 の整数で表します。

| draw 種類 | dv_cat | 値 |
|---|---|---:|
| コンボドロー (FD + SD) | combo_draw | **4** |
| フラッシュドロー (FD / NFD) | flush_draw / nut_flush_draw | **3** |
| OESD (オープンエンド) | oesd | **3** |
| ガットショット | gutshot | **1** |
| BDFD (バックドアフラッシュドロー、 2 枚) | twocards_bdfd | **1** |
| BDFD (1 枚) / no draw | onecard_bdfd / no_draw | **0** |

## 4.2 street multiplier

street ごとに DV にかかる倍率です。

| street | multiplier | 由来 |
|---|---:|---|
| flop | **×3** | Rule of 4 (out × ~8% per out × 2 残り street) |
| turn | **×2** | Rule of 2 (out × ~4% per out × 1 残り street) |
| **river** | **×0** | draw 完成不可 (board confirmed) |

## 4.3 Rule of 4/2 との関係

ポーカーで古典的に知られる **Rule of 4/2**:

- フロップで完成までの確率 ≈ outs × 4 (%)
- ターンで完成までの確率 ≈ outs × 2 (%)

これを整数化したのが本書の DV × mult 系です。 OESD (8 outs) でフロップの場合:

- 古典 Rule of 4: 8 × 4 = 32% 完成
- 本書: DV(3) × mult(3) = 9 points 加算

9 points は Score 14 → 23 への押し上げで、 マージナルな call/fold の境界を
跨ぐ大きさです。 「Rule of 4 を Score 単位に置換」 という関係です。

## 4.4 river で DV = 0 になる根拠

river では board の 5 枚が確定し、 draw は完成しないため DV の意味はゼロです。
audit でも `mult[river] = 0` 以外の値は性能を悪化させます。

ただし river では **made hand の絶対価値** がそのまま勝負を決めるため、 Grid 値
そのものが効きます。 river での Grid 値が高い カテゴリ (TP+ × dry = 38、 2P+
ハンド × dry = 25) はそのまま value range です。

## 4.5 DV をなぜ カテゴリ に統合しないか

「draw 込みで カテゴリ を 1 段上げれば良くないか?」 と思うかもしれません。
しかし draw と made hand は **独立次元** で、 統合すると以下の問題が起きます:

- OESD + TP は「TP+ カテゴリ」 でも「2P+ カテゴリ」 でもない
- combo draw (FD + SD) はエアだが Score 上は TP+ 並みに強い
- river では draw の意味が消える → カテゴリ ベースだと river を別扱いに

そのため DV は独立項として加算する設計が最良です。

## 4.6 DV 判定の実例

board: Th 9h 4c (wet flop)

| hand | 役 (mv) | DV |
|---|---|---:|
| Th Ts (set) | 2P+ | 0 (made 完成、 draw 不要) |
| Kh Jh (FD + gutshot) | エア | combo_draw = 4 |
| Qh Jh (FD + OESD) | エア | combo_draw = 4 |
| Ah 2h (NFD) | エア | flush_draw = 3 |
| J 8 (OESD) | エア | oesd = 3 |
| K Q (gutshot) | エア | gutshot = 1 |
| A K (BDFD with Ah) | エア | twocards_bdfd = 1 |
| 7 6 (no draw) | エア | no_draw = 0 |

注意点: combo_draw は **FD と OESD/SD が両立** している場合のみ。 OESD のみ、
FD のみは値 3 です。

## 4.7 DV と カテゴリ の合算ルール

ある hand に複数の判定がつく場合 (例: TP + FD)、 カテゴリ と DV は **両方加算**
されます。

- top_pair (カテゴリ 2) + flush_draw (DV 3) on flop
- Grid[TP+][?] + DV(3) × mult(3) = Grid + 9

つまり draw 込みの強さは Score にちゃんと反映されます。

## この章で覚える項目 (4 items)

1. DV 値: combo=4 / FD or OESD=3 / gutshot or BDFD=1 / no draw=0
2. street multiplier: flop=3 / turn=2 / river=0
3. Rule of 4/2 の整数化版
4. DV と カテゴリ は独立加算
"""

def gen_ch05() -> str:
    return f"""\
# 第 5 章　pot / bs / overcards の値

## 5.1 pot — 4 段階

ポット種別を表す軸です。 値は係数 4 倍されて Score に加算されます。

| pot | 略称 | 値 |
|---|---|---:|
| Single Raised Pot | **SRP** | 0 |
| vs Check-Raise / vs Donk Bet | **vs CR** | 2 |
| 3-bet Pot | **3BP** | 2 |
| 4-bet Pot | **4BP** | 4 |

**4 × pot** の効果:
- SRP: 0 (基準)
- vs CR / 3BP: +8
- 4BP: +16

4BP は Score を +16 押し上げる **巨大な上方補正** です。 これが 4BP で
「アンダーペアでもコール / 2P+はレイズ強行」 を引き起こす源。

## 5.2 bs (ベットサイズ) — 6 段階

相手の bet サイズです。 値は係数 −2 倍されて Score から引かれます。

| key | 名前 | pot 比 | 値 |
|---|---|---|---:|
| small_33 | スモールベット | ~33% | 0 |
| med_75p | ミディアムベット | ~75% | 1 |
| med_100p | ミディアムベット | ~100% | 2 |
| overbet | オーバーベット | 125-150% | 3 |
| overbet_185 | オーバーベット | ~185% | 4 |
| allin | オールイン | 100% effective | 5 |

**−2 × bs** の効果:
- small_33: 0 (補正なし)
- med_75: −2
- med_100: −4
- overbet: −6
- overbet_185: −8
- allin: −10

## 5.3 overcards (oc)

hero の 2 枚のうち、 board の最高 rank より上の枚数です。 値 0 / 1 / 2。

```
oc = (hero card 1 > max(board) ? 1 : 0)
   + (hero card 2 > max(board) ? 1 : 0)
```

### 具体例

| board 最高 rank | hand | oc |
|---|---|---:|
| Kh 7c 2d (K-high) | AhTh | 1 (A のみ) |
| Kh 7c 2d | AsAd | 2 (A 2 枚) |
| Kh 7c 2d | QJs | 0 (両方 K 以下) |
| Th 9h 4c (T-high) | KQs | 2 |
| Th 9h 4c | 88 | 0 |

### overcards の意味

A-K-Q-J など overcards は将来 turn / river で TP+ に化ける **潜在 equity**。
2 × oc で Score に小幅加算され、 マージナルな call/fold で「コール側」 に動かす役。

特に「Kh 7c 2d で AhTh → エア + oc 1 → Score 微増」 のように、 raw エア でも
overcard でわずかに救済される設計。

## 5.4 各係数の意味

| 係数 | 値 | 意味 |
|---|---:|---|
| `+4 × pot` | 4 | ポット拡大の上方補正 (4BP で +16) |
| `−2 × bs` | −2 | bet サイズの不利補正 (overbet で −6) |
| `+2 × oc` | 2 | overcard の潜在 equity (+2 〜 +4) |

係数 4 / 2 / 2 は **暗算しやすい小整数** に最適化済 (付録 B 参照)。 これらは
Optuna で連続値最適化したあと、 暗算可能な整数に丸めた結果が
偶然 (もしくは設計的に) 整っています。

## 5.5 pot × bs の interaction を加法分解した理由

「4BP × overbet は特殊なはず」 と思うかもしれません。 audit では:

- interaction matrix (pot 4 × bs 6 = 24 cells) を試した → 集約過剰で性能悪化
- 加法分解 (`4 × pot − 2 × bs`) → 最良

つまり pot と bs は **独立** に効きます。 これは pot 種別が「相手のレンジ構造を
決める」、 bs が「ポットオッズ」 を決める、 という別次元の情報だからです。

## 5.6 実例: 全要素を合わせた計算

board: Kh 7c 2d (dry)、 hand: KsQs (TP+)、 street: flop、 pot: 3BP、 bs: overbet (140%)、 oc: 0

- カテゴリ = TP+
- Grid[TP+][dry] = **38**
- DV = 0 (made TP+、 draw なし)
- 2 × oc = 0
- 4 × pot = 4 × 2 = **+8**
- −2 × bs = −2 × 3 = **−6**
- Score = 38 + 0 + 0 + 8 − 6 = **40**
- 14 ≤ 40 < 43 → **コール**

(GTO best: call、 公式 pred も call、 一致)

## この章で覚える項目 (3 items)

1. pot 値: SRP=0 / vs CR=2 / 3BP=2 / 4BP=4 (係数 4)
2. bs 値: small=0 / med=1〜2 / overbet=3〜4 / allin=5 (係数 −2)
3. overcards: 0/1/2 のうち board 最高超え枚数 (係数 2)
"""

# ===================================================================
# 第 2 部 (ch06-09)
# ===================================================================
def gen_ch06() -> str:
    grid_table = grid_md_table()
    return f"""\
# 第 6 章　12 cells grid の完全解説 ★本書の魔法核心

> **本章は本書の最大の難所であり、 最大の発見です。**
> 12 cells grid は **線形ではありません**。 「役が強いほど値が大きい」 でも「dry board ほど
> 値が大きい」 でもありません。 hand × board の **複雑な interaction** で値が増減する、
> 直感に反する数値表です。 この interaction を「12 の物語」 として理解することが
> 本書の核心です。

## 6.1 12 cells grid の全表

{grid_table}

最高値は **アンダーペア × paired = 40**。 直感に反する位置にあります。

## 6.2 直感に反する 6 つの発見

### 発見 1: ミドル × paired = 40 が最高値

直感: アンダーペアは中位の手、 paired board は trip 警戒 → 値は低いはず。

**真実**: paired board では相手の range が **wide で air-heavy** に偏ります。
相手がペア板を bet するときは bluff 率が高く、 また value 側はトリップス〜FH
に偏ります。 hero がアンダーペアであれば「相手の bluff には勝つ」 という位置に
立ち、 range 中の上位として value 取り可能。 結果 40 という驚異的な値に。

paired board × アンダーペア × bet 受けの huge% は audit で **0.0%** (n=4,776)。
公式予測がほぼ完璧にマッチします。

### 発見 2: TP+ × paired = 10 (中位の低値)

直感: TP+ は強い手、 どこでも価値あるはず。

**真実**: paired board では TP+ は **trip range に直接負ける** ハンドです。
A-K-K で AK を持っていても、 相手の K (any kicker) には負ける。 paired board
での TP+ は「アンダーペアとほぼ同価値 (10)」 という大幅減になります。

### 発見 3: 2P+ × dry = 25 < 2P+ × paired = 28

直感: dry こそ強い手の主戦場のはず。

**真実**: dry では over-protection 不要 (相手の draw が少ない)、 一方 paired
では 2P〜FH range で **取りに行く価値が高い** (相手のキッカー range が広い)。
このため paired の値がわずかに高くなります。

### 発見 4: 2P+ × wet = 23 が最低の2P+値

直感: 2P+は wet でも強いはず。

**真実**: wet board の draw 完成 / set / straight / flush で **互角の range**
ができ、 厚すぎる value bet は逆効果。 23 は「無理せず call ベース」 という
signal。 例外 2 (river × SRP × wet × 2P+ → raise) でカバー。

### 発見 5: エア × dry = 3 < エア × paired = 5

直感: dry の方が hero エアでも勝機あり (board 弱)。

**真実**: paired board では **相対 range** で意外と call できます。 相手も air
が多いため、 hero エアでも「相手より弱くない」 局面があり、 5 の小さなプラスが
重要に。

### 発見 6: TP+ × dry = 38 vs TP+ × wet = 31 (差はわずか 7)

直感: TP+ は dry だけ強く、 wet では大幅弱体化のはず。

**真実**: wet でも TP+ は **相手の draw range に対し range advantage** を持続。
draw は完成確率 30-40%、 hero TP+ は eq 60%+。 wet で 31 と高値維持されます。

## 6.3 12 cells の 4 つの暗記原則

各 cell の数値はランダムではなく、 4 つの原則の組合せで覚えられます。

### 原則 1: paired board の wide-range effect

相手の range が広がる → 中位 hand (ミドル / エア) の相対価値↑、 強 hand
(TP+ / 2P+) の相対価値↓。

- ミドル × paired = 40 (最大)
- エア × paired = 5 (dry より +2)
- TP+ × paired = 10 (大幅減)

### 原則 2: dry board の polarization effect

相手の range が分極化 → TP+ 一辺倒で最強、 中位は不利。

- TP+ × dry = 38 (準最大)
- ミドル × dry = 18 (paired の半分)
- エア × dry = 3 (base)

### 原則 3: wet board の equity sharing

draw の存在で eq が共有 → 2P+の value↓、 TP+ の defense は持続。

- 2P+ × wet = 23 (最低の2P+値)
- TP+ × wet = 31 (dry 比 −7、 まだ高値)
- ミドル × wet = 10 (paired の 1/4)

### 原則 4: エアの flat pattern

どの board でも 1-5 の low range、 sizing / oc / pot で補正。

- エア × dry = 3
- エア × paired = 5
- エア × wet = 1

エアの Grid は「base 補正」 程度の役割で、 主な変動は加算項 (DV / oc / pot / bs)
で決まります。

## 6.4 12 cells すべての数値の覚え方

| キー | 値 | 連想 |
|---|---:|---|
| ミドル × paired | **40** | 最高峰、 paired の bluff range 例外 |
| TP+ × dry | **38** | TPTK 王道、 dry polarization |
| TP+ × wet | 31 | 一の位 1 = "still strong" |
| 2P+ × paired | 28 | FH potential、 2P 取り |
| 2P+ × dry | 25 | 5×5、 set / 2P default |
| 2P+ × wet | 23 | dry 比 −2 = draw sharing |
| ミドル × dry | 18 | paired の半分弱 |
| ミドル × wet | 10 | wet で半減 |
| TP+ × paired | 10 | trip discount |
| エア × paired | 5 | wide range premium |
| エア × dry | 3 | base |
| エア × wet | 1 | floor |

「40 / 38 / 31 / 28 / 25 / 23 / 18 / 10 / 10 / 5 / 3 / 1」 を一列で覚えると、
それぞれの行と列の位置に当てはめるだけで済みます。

## 6.5 カテゴリ × board 別 huge%

audit (n={AUDIT['n_spots']:,}) での huge% (>5 BB):

| カテゴリ | dry | paired | wet |
|---|---:|---:|---:|
| エア | 0.6% | 0.4% | 1.1% |
| アンダーペア | 1.2% | **0.0%** ★ | 1.2% |
| TP+ | 2.5% | 1.7% | 4.2% |
| 2P+ | 3.7% | 5.3% | 4.3% |

- アンダーペア × paired = **0.0%** (Grid=40 で完璧マッチ)
- 弱点: 2P+ × paired (5.3%)、 wet 全般

弱点は例外 11 ルール (第 9 章) で大部分救済します。

## 6.6 12 cells の最適化過程

- 4 カテゴリ × 3 board の 12 自由度を Optuna TPE で全 {AUDIT['n_spots']:,} spots に最適化
- 旧 6 カテゴリ × 3 board (Grid 18) との比較で **集約しても性能向上** が確定
  - Grid 18: avg 0.3722 BB
  - **Grid 12: avg 0.3587 BB ★**
- 「ミドル × paired = 40」 は data から発見された値で、 GTO 理論から演繹的に導出する
  のは困難 → これこそが本公式の **最大価値**

詳細経緯は付録 B を参照。

## 6.7 数値暗記法 ★mnemonic — 12 cells を 5 分で覚える

12 個の整数 (3 / 5 / 1 / 18 / 40 / 10 / 38 / 10 / 31 / 25 / 28 / 23) を
丸暗記するのは大変です。 本節では **構造化暗記** / **物語アンカー** /
**古典役名アンカー** / **連想数式** の 4 つの mnemonic 手法で、 5 分で
12 cells が定着するようにします。

### 6.7.1 構造化暗記 — 数値を 4 group に分ける

12 cells を「値の高低」 で 4 group に分けると暗記負荷が激減します。

| group | 値 | cells | 共通点 |
|---|---|---|---|
| **最高 group** | 40 / 38 / 31 / 28 / 25 / 23 | ミドル×paired (40) / TP+×dry (38) / TP+×wet (31) / 2P+×paired (28) / 2P+×dry (25) / 2P+×wet (23) | **value 主役**、 raise 閾値 (43) に近づく |
| **中位 group** | 18 | ミドル×dry (18) | 唯一の中位、 dry の中ペア |
| **低位 group** | 10 / 10 / 5 / 3 / 1 | ミドル×wet (10) / TP+×paired (10) / エア×paired (5) / エア×dry (3) / エア×wet (1) | call 閾値 (14) 未満が多い |

### 6.7.2 物語アンカー — 各 cell に短い物語

| cell | 値 | 物語 |
|---|---:|---|
| ミドル × paired | **40** | 「ペア板の王様」 — 相手の bluff range で大儲け、 paired board の予想外スター |
| TP+ × dry | **38** | 「TPTK の王道」 — dry の支配者、 polar range で最強 |
| TP+ × wet | 31 | 「TPTK 健在」 — wet でも range advantage 持続、 31 の "1" は "still strong" |
| 2P+ × paired | 28 | 「FH potential」 — 2P から FH への伸びしろ |
| 2P+ × dry | 25 | 「5 × 5、 set の default」 — dry で set / 2P が安定 value |
| 2P+ × wet | 23 | 「draw に分け前」 — wet では draw 完成で互角に、 控えめに |
| ミドル × dry | 18 | 「中ペアの dry 限定」 — paired (40) の半分弱 |
| ミドル × wet | 10 | 「wet で半減」 — paired の 1/4 |
| TP+ × paired | 10 | 「trip 警戒で陥落」 — TPTK が paired でミドル並みに |
| エア × paired | 5 | 「wide range premium」 — 相手も air、 air でも call できる |
| エア × dry | 3 | 「base」 — エアの基準、 何もない |
| エア × wet | 1 | 「floor」 — エアの最低、 draw 期待のみ |

物語は **語呂的に短く** が肝心。 例:「ミドル paired は王様 40、 TP+ dry は王道 38、
TP+ wet は健在 31、 ...」 と読み上げると 30 秒で 12 cells が浮かびます。

### 6.7.3 古典役名アンカー — 旧用語と新 カテゴリ を結ぶ

旧来のポーカー文献 (Sklansky、 Janda 等) で使われる古典役名と、 本書 4 カテゴリ の対応:

| 本書 カテゴリ | 古典役名 | アンカー連想 |
|---|---|---|
| 2P+ | "monster"、 セット以上 | 古典の「strong made hand」、 値 23-28 (Grid 3 cells 平均 ~25) |
| TP+ | "TPTK"、 トップペア・トップキッカー | TP+ × dry 38 は「TPTK の王道」、 旧文献の "premium TP" |
| アンダーペア | "mid pair"、 セカンドペア | 旧文献の "marginal pair"、 paired 板で例外的に強い (40) |
| エア | "nothing hand"、 air、 high card | 旧文献の "drawing dead 寸前"、 すべて 1-5 の low |

「TPTK = 38 (王道)」 「monster = 23-28 (Grid 3 cells で 25 平均)」 と古典役名で
セルを呼ぶ習慣が付くと、 暗算中に Grid を引き直す手間が消えます。

### 6.7.4 連想数式 — 数字同士の関係で覚える

12 cells の数値は完全にランダムではなく、 連想数式で導出可能なものがあります。

| 関係 | 計算 | cells |
|---|---|---|
| ミドル paired から ミドル dry | **40 ÷ 2 − 2 = 18** | 40, 18 |
| 2P+ dry から 2P+ wet | **25 − 2 = 23** (draw sharing) | 25, 23 |
| エア paired から エア wet | **5 ÷ 5 = 1** (1/5 化) | 5, 1 |
| エア paired から エア dry | **5 − 2 = 3** | 5, 3 |
| TP+ dry から TP+ wet | **38 − 7 = 31** (一の位 1 = still strong) | 38, 31 |
| 2P+ paired = 2P+ dry + 3 | **25 + 3 = 28** (FH potential) | 25, 28 |
| TP+ paired = エア paired × 2 | **5 × 2 = 10** (trip discount) | 5, 10 |
| ミドル wet = TP+ paired | **両方 10** (paired と wet の TP+/ミドル境界) | 10, 10 |

特に「**両方 10** (ミドル wet と TP+ paired)」 は試験対策の鉄板で、 一気に
2 cells が定着します。

### 6.7.5 暗記の優先順位 — どれから覚えるべきか

12 cells を全部一気に覚えなくても、 優先度の高い 3 cells から始めれば
80% の場面に対応できます。

#### Tier 1 (最重要、 3 cells)

| cell | 値 | 重要度の理由 |
|---|---:|---|
| **ミドル × paired** | **40** | 最高値、 paired board の bluff range で頻発、 audit huge% 0.0% |
| **TP+ × dry** | **38** | TPTK の主戦場、 最頻出 spot (SRP dry 30%) |
| **エア × wet** | **1** | 最低値、 fold 判断の anchor、 wet × air は 8% spots |

→ 3 cells 覚えるだけで 50%+ の spots に対応。

#### Tier 2 (重要、 4 cells)

| cell | 値 | 重要度の理由 |
|---|---:|---|
| 2P+ × dry | 25 | dry の value 主役、 raise 閾値判定によく出る |
| 2P+ × paired | 28 | paired board の FH potential、 例外候補 |
| 2P+ × wet | 23 | 例外 2 で raise 変換 (wet × river × SRP) |
| TP+ × wet | 31 | 例外 1 で fold 強制 (wet × flop × SRP)、 注意必須 |

→ Tier 1 + 2 で 7 cells、 75% の spots カバー。

#### Tier 3 (補助、 5 cells)

| cell | 値 | 重要度の理由 |
|---|---:|---|
| ミドル × dry | 18 | dry の中ペア、 borderline call/fold |
| ミドル × wet | 10 | 例外 3 で fold 強制 (wet × turn × vs CR) |
| TP+ × paired | 10 | paired × TP+ の trip discount、 ミドル wet と同値 |
| エア × paired | 5 | wide range premium、 paired での bluff catch |
| エア × dry | 3 | エアの base、 SRP dry で fold base |

### 6.7.6 5 分暗記プロトコル

実践的な暗記手順:

1. **30 秒**: Tier 1 の 3 cells を読み上げ (40 / 38 / 1)
2. **1 分**: Tier 2 の 4 cells を物語アンカーで結合 (FH 28 / set 25 / 健在 31 / 控えめ 23)
3. **1 分**: Tier 3 の 5 cells を「両方 10」 で覚える (ミドル wet と TP+ paired)
4. **1 分**: 連想数式で確認 (40÷2−2=18、 5−2=3、 5÷5=1)
5. **30 秒**: 12 cells 全部を一気に読み上げ self-test

5 分で 90% 定着、 翌日 reviewing で 99% 定着。 反復は **poker-drill** アプリの
「grid 暗記 deck」 (https://poker-drill.vercel.app) で。

## この章で覚える項目 (16 items)

1〜12. 12 cells のすべての数値 (Tier 1 → 2 → 3 の優先順で)
13. 直感に反する 6 つの発見 (paired で逆転する場面)
14. 原則 1: paired の wide-range effect
15. 原則 2: dry の polarization effect
16. 原則 3: wet の equity sharing
"""

def gen_ch07() -> str:
    return f"""\
# 第 7 章　境界ハンド集 — Hand Strength の outlier

## 7.1 逆 U 字パターンの発見

GTO ソルバーの 6 カテゴリ × 42 boards 集計 (BTN attacker、 cbet 平均):

| カテゴリ | avg cbet | 隣接差 |
|------|---:|---:|
| ナッツメイド (FH / quads) | 9% | — (slowplay base) |
| ストロング (set / flush) | 29% | +20% |
| **ツーペア** | **67%** | +38% (peak) |
| トップペア以上 | 52% | −15% |
| アンダーペア | 24% | −28% |
| エア (bluff) | 37% | +13% (逆転) |

**山型 (逆 U 字) パターン: ツーペアが最高頻度 (67%)**。

直感的には「ナッツが一番 bet される」 と思いがちですが、 実 GTO では
**ツーペアが peak**。 これは:

- ナッツメイド (FH / quads): slowplay (trap)、 相手の bluff を引き出すため check
- 2P: 相対 nut、 bet で value 最大化
- TP: 値 52% は protection bet、 ある程度 thin value 含む
- アンダーペア: 24% は bluff catch range の中位
- エア: 37% は bluff catch / 純 bluff

本書ではこの分布を 4 カテゴリ (エア / ミドル / TP+ / 2P+) に集約し、
Grid 12 cells で吸収しています。 ツーペア peak は 「2P+ × paired = 28」
「2P+ × wet = 23」 で間接的に表現。

## 7.2 ツーペア 67% peak の意味

paired board で意外にも 2P は最も bet されにくい (per board family):

| board | 2P bet 頻度 |
|---|---|
| dry | 70%+ |
| wet | 60-70% |
| paired | **0-30%** (極端な減少) |

paired board × 2P が低頻度の理由:
- paired board で 2P は **set / FH に勝てない**
- 相手の trip range が広い → bet で価値を取りに行けない
- slowplay 化 (call → showdown ベース)

→ 例外 5 (2P+ × wet × flop × SRP → fold) と関連、 paired での 2P
扱いは別の例外候補。

## 7.3 ボトムペア vs アンダーペアの境界

ボード K-7-2 で:

| ペアの種類 | カテゴリ | 例 |
|---|---|---|
| top_pair (K) | TP+ | AK、 KQ、 KJ、 K9s |
| second_pair (7) | アンダーペア | A7、 87、 76s |
| third_pair (2) | アンダーペア | A2、 32 |
| underpair (≤6) | アンダーペア | 66、 55、 44、 33 |

注意: **ポケットペアでボード最低 rank と並ぶ** (例: K72 で 77) は second_pair
扱い (board 上の 7 と並ぶ → セット化はしてない)。

## 7.4 mv_cat 別 outlier 一覧

### top_pair のキッカー強弱

| キッカー強さ | mv_cat | 実 GTO 扱い |
|---|---|---|
| TPTK (top kicker) | top_pair | TP+ 完全相当 |
| TPGK (good kicker、 例: K72 で KQ) | top_pair | TP+ |
| TPWK (weak kicker、 例: K72 で K6) | top_pair | TP+ だがリバーで弱体化 |
| TP no kicker (例: K7 で K7) | top_pair | TP+ but trap |

Score 公式は **キッカー強弱を無視** します。 これは audit で「キッカー分離は
情報過多」 という結果が出たためで、 マージナル境界では他軸 (oc / pot / bs)
で吸収しています。

### second_pair vs third_pair

両方アンダーペアですが、 second は third より +3〜+5 BB の avg gain。 ただし
Grid 集約上は同 カテゴリ (18 / 40 / 10)。

## 7.5 境界ハンド ~15 個の暗記リスト

公式から外れる代表ハンド (各 spot の追加調整推奨):

| ハンド | spot | 補正 | 理由 |
|---|---|---|---|
| A2s on A82 | TP+ × dry | -2 | TPWK、 weak kicker |
| K9 on K72 | TP+ × dry | -1 | TPGK |
| 88 on K72 | ミドル × dry | +2 | underpair 高め |
| 77 on K72 | ミドル × dry | +3 | second pair |
| 55 on K72 | ミドル × dry | -1 | underpair 低め |
| A7s on AA7 | TP+ × paired | +5 | 2P 化、 2P+候補 |
| TT on T87 | 2P+ × wet | -2 | set だが wet |
| 65 on 998 | エア × paired | +3 | OESD あり (DV で吸収) |
| Q8s on T98 | エア × wet | +1 | gutshot + 2 over |
| A5s on K72 | エア × dry | +2 | bdfd + nut blocker |
| KQ on AKQ | TP+ × wet | -3 | 2nd pair top kicker |
| 99 on T87 | ミドル × wet | -2 | underpair on wet |
| AQ on Q72 (mono Q) | TP+ × wet | -3 | mono で flush 警戒 |
| JJ on AQT | ミドル × wet | -3 | underpair + scary |
| 76s on 985 | エア × wet | +4 | OESD + bdfd (DV で大半吸収) |

これらは「公式値 ± 補正」 で覚えてください。 補正値は本書の audit が「ほぼ Grid 内に
吸収できる」 と示しているため、 多くの場合は無視可能です。

## この章で覚える項目 (5 items)

1. 逆 U 字パターン (ツーペア 67% peak)
2. paired × 2P = 0% 近辺 (slowplay)
3. キッカー強弱は公式は無視 (oc / pot で吸収)
4. underpair はアンダーペア カテゴリ
5. 境界ハンド ~15 個の補正 (大半は無視可能、 例外 5 で救済)
"""

def gen_ch08() -> str:
    return f"""\
# 第 8 章　境界ボード集 — Range Morphology の修正

## 8.1 現行 heuristic と実 GTO の一致率 19%

GTO ソルバーの 13 sub-family × cbet 平均 (BTN attacker、 Cash100 SRP):

| empirical class | sub-family | cbet 平均 | 範囲 |
|---|---|---:|---|
| **MERGED** (>45%) | paired_low | 50.1% | 45-57% |
| | Khigh_spread | 48.0% | 44-50% |
| | Ahigh_spread | 46.0% | 25-50% |
| **CONDENSED** (40-45%) | broadway_dry | 44.9% | 28-52% |
| | paired_mid | 42.0% | 40-45% |
| | paired_high | 41.1% | 33-43% |
| | connected_low | 41.3% | 32-59% |
| **POLAR** (30-40%) | low_dry | 33.9% | 33-35% |
| | mid_dry | 33.3% | 28-39% |
| | connected_broadway | 32.5% | 17-40% |
| **POLAR extreme** (<30%) | monotone | 29.2% | 15-38% |
| | connected_mid | 28.5% | 21-48% |

旧 heuristic との一致率: **4/21 (19%)** → 修正必要。

## 8.2 paired board の特殊性

paired board は 1 種類ではありません。 sub-family で挙動が大きく異なります。

### paired_low (例: 7-7-2)

- cbet 50%+ (MERGED 系)
- 相手の range が wide → hero attacker は cbet 強行
- アンダーペア × paired_low = 40 (Grid 値そのまま)

### paired_mid (例: 8-8-K)

- cbet 42% (CONDENSED 系)
- middle 適度、 hero の condense range が活きる

### paired_high (例: K-K-2)

- cbet 41% (CONDENSED 系)
- TP+ range advantage が hero (attacker) に
- paired × TP+ = 10 ですが、 board K にヒットしたペアは別物です

→ Score 公式は **paired を 1 種類で扱う** が、 paired_high と paired_low の
差は **oc** と **DV** で部分的に吸収されます。

## 8.3 paired × 2P = 0% の発見

paired board で hero が 2P を持っているとき (例: K-K-7 で K7):

- 実 GTO 上の bet 頻度: **0% 近辺**
- 理由: 相手の K (any kicker) と相互勝ち負け、 set / FH に常時負ける
- 推奨: check call ベース (本書では Score < {T_RAISE} → call)

これは Grid「2P+ × paired = 28」 + Score < 43 → call で正しく
表現されています (28 + 0 + ... < 43)。

## 8.4 paired × overpair が wet 寄り

paired board で hero が overpair (例: T-T-2 で QQ):

- TP+ 扱いですが、 board のペア化で「相手の T range」 に弱体化します
- 実 GTO では wet board 並みの controlled play
- Grid「TP+ × paired = 10」 で低めに評価されている (適切)

## 8.5 low_dry の修正

旧 heuristic では low_dry は dry の 1 種でしたが、 実 GTO データでは:

- cbet 33-35% (POLAR 系) で wet/paired_low より低い
- 相手の range が **ほぼ flat** で fold equity が低い
- 推奨: bet サイズ大、 頻度低 (polarized strategy)

Score 公式上は「low_dry も dry カテゴリ」 として吸収。 例外的に「low_dry × エア
× SRP」 では bs を上げて bluff 比率を下げる調整。

## 8.6 wet 内の sub-family

wet と一括りにしていますが、 sub-family が 4 つあります。

| sub-family | 特徴 | 推奨対応 |
|---|---|---|
| dynamic_2tone (例: T98 2 tone) | 強 connected | Grid wet を厳格適用 |
| monotone (例: T98hhh) | 3 mono | DV を高めに、 oc を厳しめに |
| straight-heavy connector (例: 765) | 4-connected | wet 中の最 wet |
| connected_broadway (例: QJT) | 高 connector | wet だが range が equity 共有 |

これらは Grid「wet」 1 種で扱い、 DV と例外 11 ルールで救済しています。

## 8.7 77 boards cross-tab から抜粋した outlier ~15 個

| board | 旧分類 | 修正 | 理由 |
|---|---|---|---|
| 7-7-2 (paired_low) | paired | paired (MERGED) | cbet 50%、 wide attack |
| 9-9-K (paired_mid) | paired | paired (CONDENSED) | TP+ で対応 |
| K-K-2 (paired_high) | paired | paired (CONDENSED) | TP+ adv |
| 6-5-4 (connected_low) | wet | wet+ (CONDENSED) | cbet 41% |
| Q-J-T (connected_broadway) | wet | wet (POLAR) | 32.5% |
| T-8-7 (connected_mid) | wet | wet (POLAR extreme) | 28.5% |
| 7-5-2 (mid_dry) | dry | dry (POLAR) | 33.3%、 polar |
| A-7-2 (Ahigh_spread) | dry | dry (MERGED) | A blocker effect |
| K-8-3 (Khigh_spread) | dry | dry (MERGED) | 48% |
| K-Q-J (broadway_dry) | dry | dry (CONDENSED) | 44.9% |
| 9-8-7 hhh (mono) | wet | wet (POLAR extreme) | mono 警戒 |
| 4-3-2 (low_dry) | dry | dry (POLAR) | 33% |
| T-9-2 (mid + connector) | wet | wet 寄り | gap 1 |
| A-K-2 (broadway dry) | dry | dry (CONDENSED) | A blocker |
| 8-7-2 (mid + connector, gap 1) | wet | wet (CONDENSED) | gap で wet 判定 |

→ Score 公式上は **3 タイプ集約で十分** と判明。 sub-family の細かい差は
audit で「Grid 12 → Grid 18」 への分離試行で性能向上せず、 集約のメリットの方が
勝ちました。

## この章で覚える項目 (4 items)

1. 旧 heuristic 一致率 19% → 集約は data 駆動で判断
2. paired_low / paired_mid / paired_high の sub-family
3. paired × 2P = 0% (slowplay)
4. low_dry は実は POLAR (旧 dry より bet 低頻度)
"""

def gen_ch09() -> str:
    ex1_5_lines = []
    for ex in EXCEPTIONS[:5]:
        ex1_5_lines.append(f"### 例外 {ex['num']}: {ex['tier']} × {ex['board']} × {ex['street']} × {ex['pot']} → **{ex['best']}**")
        ex1_5_lines.append('')
        ex1_5_lines.append(f"- 公式 pred: `{ex['pred']}` / GTO best: **`{ex['best']}`**")
        ex1_5_lines.append(f"- サンプル: n = {ex['n']}、 平均 loss = {ex['avg']} BB")
        ex1_5_lines.append(f"- 理由: {ex['note']}")
        ex1_5_lines.append('')
        ex1_5_lines.append(f"**適用条件**: カテゴリ = {ex['tier']}、 board = {ex['board']}、 street = {ex['street']}、 pot = {ex['pot']} が **すべて成立** し、 かつ公式 pred が `{ex['pred']}` のとき。")
        ex1_5_lines.append('')
    body_ex1_5 = '\n'.join(ex1_5_lines)

    return f"""\
# 第 9 章　例外 11 ルール + DEF 閾値補正 (huge loss 回避)

## 9.1 例外ルールの設計思想

MATCHA Score 公式は {AUDIT['n_spots']:,} spots で avg loss {AUDIT['avg_loss']:.4f} BB の
高精度を達成しますが、 **huge loss (>5 BB) spots** が {AUDIT['huge_pct']:.2f}% 残ります。
n = 2,303 個の huge spots は **特定 pattern に集中** しており、 DEF 閾値補正 + 11 の例外ルールを
追加することで大部分を救済できます。

まず **DEF 閾値補正** を適用し、 次に例外ルールを 4 グループに分けて覚えます:

| グループ | ルール番号 | 説明 |
|---|---|---|
| **DEF 閾値補正** | — | vs CR / Donk 時は T_raise=49 (通常 43 から引き上げ)。 精度 DEF_all 80.0 |
| **huge_loss 5** | ex1〜ex5 | wet board 中心の最大損失スポット |
| **確実 cell 3** | ex6〜ex8 | 公式無視で確実 bet / check する特殊 board |
| **Turn CR 専用 2** | ex9〜ex10 | turn × vs CR のみ fold に変換 (⚠️ Donk 不可) |
| **River Donk 1** | ex11 | river × vs Donk × strong で value raise |

## 9.2 huge loss の Pred → Best confusion

公式 pred と GTO best の不一致パターン (n = 2,303):

| 公式 pred | GTO best | n | % |
|---|---|---:|---:|
| call | fold | 1,003 | 43.6% |
| fold | call | 528 | 22.9% |
| call | raise | 501 | 21.8% |
| raise | call | 133 | 5.8% |
| fold | raise | 102 | 4.4% |
| raise | fold | 36 | 1.6% |

「公式が call を出したが本当は fold」 が 43.6% で最多。 これは「相手の overbet
受けでマージナルな TP+/2P+を過大評価」 する公式の癖を示しています。

## 9.3 例外 ex1〜ex5 (huge_loss 5 ルール)

{body_ex1_5}

## 9.4 例外 ex6〜ex8 (確実 cell 3 ルール)

### 例外 6: 2P+ × paired_low (board 最高 rank < 5) → 確実 bet

- 理由: paired_low (例: 2-2-4、 3-3-2) で 2P+ は相手の trips がレンジに入らない。 公式 Score 値に関係なく bet/raise 確定 (SD 8pp)
- **適用条件**: board 最高 rank が 4 以下の paired board で 2P+ カテゴリ。

### 例外 7: アンダーペア × monotone (3 同 suit) → 確実 check

- 理由: 3 同 suit board でアンダーペアは相手の flush 完成 range に完敗。 Score 値に関わらず check (SD 6.5pp)
- **適用条件**: board が 3 同 suit (monotone) でアンダーペア カテゴリ。

### 例外 8: エア × monotone → check 寄り (bet 抑制)

- 理由: monotone でエアのブラフは相手の call range (flush 完成) が固く低 EV。 公式 bet 判定を抑制 (SD 9pp)
- **適用条件**: board が 3 同 suit (monotone) でエア カテゴリ、 かつ公式 pred が bet/raise。

## 9.5 DEF 閾値補正 (vs CR / vs Donk 共通)

DEF 補正 (pot = 2、 +8 bonus) が **raise を誤発生**させる 2 パターン (ミドル×paired と TP+×dry)。
これらは例外ルールではなく、 **DEF 文脈での閾値変更** で対応します。

> **DEF 閾値補正**: vs CR または vs Donk のとき、 T_raise = **49** (通常 43 から引き上げ)

- ミドル × paired × DEF: Score = 40 + 8 = 48 → T=49 では **call** (旧: raise が誤判定)
- TP+ × dry × DEF: Score = 38 + 8 = 46 → T=49 では **call** (旧: raise が誤判定)
- 精度: DEF_all 80.0 Grade S (208K hands 検証)

## 9.6 例外 ex9〜ex10 (Turn CR 専用 2 ルール)

**⚠️ この 2 ルールは vs CR (チェックレイズ) 専用です。 vs Donk (ドンクベット) には適用しないでください。**

### 例外 9: (アンダーペア / TP+) × dry × turn × vs CR → fold に override

- アンダーペア: 公式 pred: `call` (Score ≈ 18 + 8 = 26) / GTO best: **`fold`** (GTO FOLD 71.5%、 RAISE 26.4%、 CALL 2.1%) — n = 144、 avg = 5.54 BB
- TP+: 公式 pred: `call` (Score ≈ 38 + 8 = 46) / GTO best: **`fold`** (GTO FOLD 56%) — n = 194、 avg = 2.13 BB
- サンプル計: n = 338、 平均 loss = 3.60 BB avg
- 理由: Turn vs CR で dry board × アンダーペア/TP+ は villain range が strong すぎ call 維持不可。 dry × turn CR は「set/trips 確定」文脈。
- **適用条件**: カテゴリ = アンダーペアまたはトップペア以上、 board = dry、 street = turn、 pot = vs CR のみ。 ⚠️ vs Donk 不可 (Donk turn × dry は call が正解)。

### 例外 10: トップペア以上 × wet × turn × vs CR → fold に override

- 公式 pred: `call` (Score ≈ 31 + 8 = 39) / GTO best: **`fold`** (GTO FOLD 62.3%、 CALL 37.0%)
- サンプル: n = 215、 平均 loss = 2.40 BB avg
- 理由: Turn vs CR で wet board × TP+ は villain range (straight/flush 完成 or set) に劣位。
- **適用条件**: カテゴリ = トップペア以上、 board = wet、 street = turn、 pot = vs CR のみ。 ⚠️ vs Donk 不可 (Donk turn × TP+×wet は GTO CALL 87%)。

## 9.7 例外 ex11 (River Donk 専用 1 ルール)

### 例外 11: 2P+ (trips/FH/quads) × paired × river × vs Donk → raise (value)

- 公式 pred: `call` (Score = 28 + 8 = 36 or nearby) / GTO best: **`raise`** (GTO RAISE 100%)
- サンプル: n = 66、 平均 loss = 2.51 BB avg
- 理由: River vs Donk で paired board × trips 以上は villain の donk range が弱く value raise が正解。
- **適用条件**: カテゴリ = 2P+ (trips/FH/quads)、 board = paired、 street = river、 pot = vs Donk のみ。

## 9.8 例外ルールの適用順序

1. vs CR / vs Donk のとき: **T_raise = 49** を使う (DEF 閾値補正)
2. 公式で Score を計算 → call / raise / fold の暫定アクション
3. カテゴリ / board / street / pot を例外 11 ルール表と照合
4. 該当があり、 公式 pred = 表の pred と一致 → 表の best にオーバーライド
5. 該当なし → 公式 pred を採用

ex6-8 は「公式 pred に関わらず」 強制 override する点に注意。

## 9.9 例外 11 ルール採用効果と精度

7 context × 208,888 hands での総合精度:

| context | n | 正解率 | avg loss BB | 総合精度 |
|---|---:|---:|---:|---:|
| SRP flop | 39,736 | 79.3% | 0.007 | **94.6** ★S |
| 3BP flop | 47,040 | 84.9% | 0.019 | **94.8** ★S |
| 4BP flop | 47,040 | 65.7% | 0.120 | **84.0** ★S |
| TURN | 21,227 | 64.9% | 0.013 | **90.6** ★S |
| RIVER | 19,753 | 70.1% | 0.042 | **88.2** ★S |
| vs CR | 15,576 | 76.0% | 0.200 | **80.5** ★S |
| vs Donk | 18,516 | 68.7% | 0.141 | **82.7** ★S |
| **統合** | **208,888** | **74%** | **0.065** | **89.1 ★S** |

全 7 context が Grade S (≥ 80) 達成。

## 9.10 例外を覚える key word

- **DEF (vs CR/Donk)**: T_raise = **49** (通常 43 から引き上げ、 例外ではなく閾値補正)
  - ミドル×paired: Score=48 → T=49 で call。 TP+×dry: Score=46 → T=49 で call
- **wet × ?** → ex1〜ex5 候補 (wet board に集中)
- **monotone** → ex7/ex8 (check / 抑制)
- **paired_low** → ex6 (確実 bet)
- **turn × vs CR + call** → ex9/ex10 (fold に変換、 ⚠️ Donk 不可)
- **river × vs Donk + paired × strong** → ex11 (value raise)

## 9.8 outlier rule v3 (5 context 別の役ベース判別、 2026-06-11 追加)

例外 11 ルールに加えて、 174K hands 検証で **5 context 別の outlier 判別ルール** が data 駆動で確定しました。 これらは「公式判定が大きく外れる役 × board pattern」 を見つけて警告するルールです。

| context | Best Rule | F1 | precision | avg loss/hit |
|---|---|---:|---:|---:|
| **SRP** | set OR trips OR (overpair × dry) | 30.8% | 26.6% | 0.064 BB |
| **3BP** ★ | **TP+ カテゴリ 全 mv** (= top_pair 以上 or set/trips) | **45.2%** | 44.0% | 0.20 BB |
| **4BP** ★ | paired × (TP+/ミドル) OR エア × paired | 26.4% | 29.3% | 0.21 BB |
| **TURN** | TP+ × non-paired OR ミドル × paired OR overpair | 33.0% | 17.7% | 0.28 BB |
| **RIVER** | 役確定なので split rule (made/no_made → bet) で代替 | — | — | acc +25pp |

### 暗算フロー (5 context 統合)

```
Step 1: context 判別 (SRP/3BP/4BP/TURN/RIVER)
Step 2: context 別判定
  ├─ SRP/3BP → Score 公式 (Grid + DV + 補正)
  ├─ 4BP    → 4 cells lookup (第 16 章)
  ├─ TURN   → 3 cells lookup + overpair + bluff (第 17 章)
  └─ RIVER  → split rule (第 18 章)
Step 3: 役 × board で outlier rule 確認 (上記表)
```

### outlier rule の data 駆動裏付け

各 context の outlier (loss > 0.05 BB) の主要因 役単独 bet 率:

- **SRP** (outlier 2.6%): trips 34% / set 23% / overpair (dry) 22%
- **3BP** (outlier 13.5%): overpair 69% / straight 53% / trips 45% / top_pair 38%
- **4BP** (outlier 33.5%): top_pair 73% / second_pair 68% / 2P 47% / set 41%
- **TURN** (outlier ~18%): set 66% / FH 59% / overpair 37% / 2P 30%
- **RIVER** (outlier ~50%): set 100% / FH 98% / trips 97% / 2P 94% / straight 92%

各 context の outlier rule はこれらの高 bet 率の役を捕捉するよう data 駆動で設計されました。

## この章で覚える項目 (5 + 5 items)

1. 例外 1: wet × TP+ × flop × SRP → fold
2. 例外 2: wet × 2P+ × river × SRP → raise
3. 例外 3: wet × ミドル × turn × vs CR → fold
4. 例外 4: wet × エア × turn × 3BP → call (bluff catch)
5. 例外 5: wet × 2P+ × flop × SRP → fold

**outlier rule (オプション、 暗算負荷増)**:
6. SRP outlier: set/trips OR overpair × dry
7. 3BP outlier: TP+ カテゴリ 全 mv (覚えやすい広域 rule)
8. 4BP outlier: paired × TP+/ミドル + エア × paired
9. TURN outlier: TP+ × non-paired + ミドル × paired + overpair
10. RIVER: outlier rule 不要 (split rule で代替)
"""

# ===================================================================
# 第 3 部 (ch10-12)
# ===================================================================
def gen_ch10() -> str:
    return """\
# 第 10 章　Range Morphology — board 分類の data 裏付け

> 本章以降は **公式の理論的背景** です。 公式だけ使う読者は読み飛ばし可能です。

## 10.1 旧 6 ボードファミリーと現行 3 タイプ

旧来は board を 6 種に分類していました:

| 旧 family | 例 | 新分類 |
|---|---|---|
| dry_high (A/K/Q high dry) | K-7-2 | dry |
| low_dry (低 rank dry) | 7-5-2 | dry |
| dynamic (中程度 connector) | T-8-5 | wet |
| dynamic_2tone (2 tone connected) | T-9-8 (2 tone) | wet |
| monotone | 9-7-3 (mono) | wet |
| paired | 7-7-2 | paired |

これを **dry / paired / wet の 3 タイプに集約** したのが本書です。 集約しても
性能が向上したため (Grid 18 → Grid 12 で avg 0.3722 → 0.3587 BB) の data 駆動決定。

## 10.2 現行 heuristic 一致率 19% の経緯

「sub-family を細かく分類すれば精度上がるはず」 という仮説を audit で検証した結果:

- 13 sub-family × cbet 平均で、 旧 heuristic 一致率 **4/21 (19%)**
- 実 GTO は heuristic より複雑な non-linear 振る舞い
- 「分類を細かくしても heuristic とは合わない」 → 集約してかつ Grid で逆補正の方が筋

## 10.3 data-driven な 3 タイプ集約

集約のキーは「Grid 12 cells の hand × board interaction で sub-family の差を吸収」
する設計です。 つまり sub-family を board 軸ではなく Grid 値で表現します。

例:
- paired_low (cbet 50%) と paired_high (cbet 41%) の差
  → Grid「アンダーペア × paired = 40」 vs 「TP+ × paired = 10」 で表現
- low_dry と broadway_dry の差
  → oc 値の差 (broadway は oc 1-2、 low_dry は oc 0) で表現

「軸を増やすより interaction を高めた方が暗算しやすい」 という決定。

## 10.4 sub-family × カテゴリ の cross-tab (15 × 6 = 90 cell の発見)

膨大なデータの中で発見された outlier (audit ):

| sub-family | カテゴリ | bet 頻度 | outlier 度 |
|---|---|---:|---|
| paired × 2P | 2P+ | 0-30% | 🟢 強 (slowplay) |
| connected_mid × ミドル | ミドル | 73% | 🟡 高 (SPR=1.3) |
| paired_high × overpair | TP+ | 50%+ | 🟡 mid |
| monotone × FD | 2P+ | 65%+ | 🟢 強 (nut flush) |
| broadway_dry × ace_high | エア | 35%+ | 🟡 mid (oc 効果) |

これら outlier の大半は Grid 12 cells に吸収済。 残りは例外 11 ルールで救済。

## 10.5 なぜ 3 タイプで Score 公式に十分か

audit 結果:

| board 分類 | Grid 形 | avg loss |
|---|---|---:|
| 6 family × 4 カテゴリ | Grid 24 | 0.3654 BB (overfit) |
| 4 family × 4 カテゴリ | Grid 16 | 0.3601 BB |
| **3 family × 4 カテゴリ (本書)** | **Grid 12** | **0.3587 BB ★** |
| 2 family × 4 カテゴリ | Grid 8 | 0.3892 BB (under) |

3 family が **sweet spot**。 これより細かくしても overfit、 粗くしても情報損失。
情報量と暗記コストの最良バランスが 3 タイプ集約です。

## この章で覚える項目 (3 items)

1. 旧 6 family → 新 3 タイプの集約
2. sub-family の差は Grid 値で表現される
3. Grid 12 (3 board × 4 カテゴリ) が最良 bin (audit 検証済)
"""

def gen_ch11() -> str:
    return """\
# 第 11 章　Hand Strength — 6 階層 → 4 集約の理由

## 11.1 旧 6 階層

| index | 名前 | 含むハンド |
|---:|---|---|
| 5 | ナッツメイド | FH / quads / SF |
| 4 | ストロング | set / flush / straight / 2P |
| 3 | ツーペア | (旧分類で独立) |
| 2 | トップペア以上 | TP / overpair |
| 1 | アンダーペア | second / third / underpair |
| 0 | エア | high card / king / ace high |

実は旧 6 階層は「ストロング」「ツーペア」「ナッツメイド」 を細分化したものです。

## 11.2 4 集約の data 駆動根拠

audit で カテゴリ 数を変えた直接比較:

| 構成 | Grid cells | avg loss | 採否 |
|---|---:|---:|---|
| 6 カテゴリ (旧) | 18 | 0.3722 BB | × |
| 5 カテゴリ | 15 | 0.4084 BB | × (集約過剰) |
| **4 カテゴリ-B (本書)** | **12** | **0.3587 BB** | **★採用** |
| 4 カテゴリ-A (ペア統合) | 12 | 0.3843 BB | × |
| 7 カテゴリ (細分化) | 21 | 0.3874 BB | × (overfit) |

**4 カテゴリ-B (上位統合) が最良**。 「ナッツ / ストロング / 2P」 を「2P+
ハンド」 1 階層に統合した版が勝者です。

## 11.3 「2P+」 統合の決定的役割

統合のキー: 4BP での huge% −85% 削減。

| 構成 | 4BP huge% |
|---|---:|
| 旧 6 カテゴリ | 3.37% |
| **新 4 カテゴリ (2P+)** | **0.53%** ★ |

4BP では 2P 以上はすべて「強行 value」 が GTO 最適で、 細分化しても出力が
同じになります (call / raise の中で混合)。 統合することで Score 公式の
4BP 補正 (+16) が直接効くようになり、 huge spot が激減しました。

## 11.4 mv_cat 17 種類 → 4 集約の対応

GTO ソルバー 内部の mv_cat 17 種類が本書 4 カテゴリ に対応します。

```
2P+: two_pair, set, trips, straight, flush, fullhouse, quads, straight_flush
トップペア以上:    top_pair, overpair
アンダーペア:        second_pair, third_pair, underpair, low_pair
エア:              no_made_hand, king_high, ace_high
```

第 2 章で詳述したとおり。

## 11.5 6 → 4 集約の理論的妥当性

「上位 3 階層を統合して情報損失ないか?」 という不安への audit 回答:

- ナッツ × paired と 2P × paired は GTO 出力が「99% 同じ」 (両方とも slowplay → call)
- set と flush は wet board で「両方とも check call base」
- straight と FH は dry board で「両方とも value raise」

→ 細分化しても出力は変わりません。 集約することで Grid を 12 に減らし、 暗記コストを
半減できます。

## 11.6 旧 5 軸モデルの「エクイティバケット」 との関係

MATCHA Framework の旧 5 軸モデルでは:

- ハンドストレングス (6 階層)
- エクイティバケット (4 段階、 2P+ / 良 / 弱 / ブラフ)

の 2 軸を持っていました。 本書では:

- ハンドストレングスを 4 階層に集約 (上 3 つ統合)
- **エクイティバケットは独立軸として廃止**、 Grid 値に吸収

これは「ハンドストレングスとエクイティバケットの情報が重複していた」 という発見
に基づきます。 単純化により暗算が大幅楽になりました。

## この章で覚える項目 (3 items)

1. 4 カテゴリ-B (上位統合) で audit 最良 (0.3587 BB)
2. 2P+統合が 4BP huge −85% を実現
3. エクイティバケット軸は廃止、 Grid に吸収済
"""

def gen_ch12() -> str:
    return """\
# 第 12 章　Bet Sizing と SPR — 2 段階と反転点

## 12.1 Bet Sizing は 2 段階で 90% カバー

旧 MATCHA Framework は bet サイズを 4 段階で扱っていました:

| 旧 4 段階 | 範囲 |
|---|---|
| スモールベット | ~33% |
| ミディアムベット | 50-100% |
| オーバーベット | 125-185% |
| オールイン | all-in |

audit でこれを bet サイズ 2 種類に簡略化しても 90% カバー:

| 新 2 段階 | 範囲 | freq (全 boards) |
|---|---|---:|
| **small 33%** | 1.5-2 bb cbet | 45-50% |
| **over 100%+** | 5-10 bb cbet | 30-35% |
| medium (75-100%) | mid | < 10% |

**medium (50-75%) は実 GTO ではほぼ未使用**。 4 段階を 2 段階に簡略化しても
情報損失なし。

Score 公式は 6 段階 (small_33 / med_75 / med_100 / overbet / overbet_185 / allin)
の値を持ちますが、 実戦では「small (0) と overbet (3-4) のどちらか」 を覚えれば
ほぼ事足ります。

## 12.2 board family 別の dominant sizing

| board family | dominant sizing | freq |
|---|---|---|
| dry MERGED (K-7-2、 paired_low) | small 33% | 40-50% |
| connected wet (T-9-8、 6-5-4) | large 100%+ | 2-6% (低頻度・大サイズ) |
| broadway dry | small 33% | 40-50% |
| low_dry / mid_dry | large 100%+ | 33% |

「dry → small bet 多用、 wet → 高頻度 check + 時々 large bet」 という基本パターン。

## 12.3 SPR 4 段階

| SPR 段階 | 範囲 | 典型 |
|---|---|---|
| オールインSPR | < 1 | 4BP、 short stack push |
| ローSPR | 1-3 | 3BP、 短スタック |
| ミディアムSPR | 3-7 | SRP の turn 後 |
| ディープSPR | > 7 | Cash 100bb の flop、 200bb |

## 12.4 SPR=3 が GTO 戦略反転点

同 board (Ks 7d 2c) × SPR variation の cbet 頻度 (実 audit):

| カテゴリ | SPR 1.3 (4BP) | SPR 3.4 (3BP) | SPR 8 (Cash50) | SPR 16 (Cash100) |
|---|---:|---:|---:|---:|
| 2P+ (set) | **4%** | 41% | 69% | **96%** |
| ツーペア | 18% | 80% | 97% | 83% |
| トップペア以上 | 61% | 70% | 68% | 61% |
| アンダーペア | **73%** | 49% | 43% | 55% |
| エア | 41% | 46% | 46% | 44% |

### SPR=3 を境に逆転

- **SPR < 3 (4BP / shallow)**: 強い手 slowplay、 アンダーペア突撃 (set 4% / ミドル 73%)
- **SPR > 3 (deep)**: 強い手 fastplay、 アンダーペア 抑制 (set 96% / ミドル 55%)

これは Score 公式上では `4 × pot` で表現:
- 4BP (pot=4) → Score +16、 アンダーペアが call 閾値超え
- SRP (pot=0) → Score 補正なし

## 12.5 4BP でアンダーペア 73% > set 4% の逆転現象

直感に反する事実: **4BP では set より アンダーペアの方が bet 頻度高い**。

理由:
- 4BP は SPR < 2、 effective stack/pot 比が極小
- set は slowplay 価値が大 (相手の 3BP/4BP コミット range は wide で trap 効く)
- アンダーペアは「迷う」 範囲、 GTO は jam-or-fold で jam 寄せ
- 結果 ミドル 73% bet vs set 4% slowplay

この逆転を Score 公式は **「2P+ × 4BP」 で +16 補正 + slowplay 隅**
で間接表現。 Score 値そのものは set が高いが、 アンダーペアでも 4BP 補正で
call 閾値を悠々越えるので強気の判断に出ます。

## 12.6 4BP は別ゲーム (Tier A) の証拠

4BP の特殊性は audit でも明確に分離されます。

- Cash 4BP と MTT 100bb 4BP は **同構造** (audit で確認)
- SRP / 3BP / vs CR とは別系統
- huge% の劇的改善 (3.37% → 0.53%) は本書の最大成果

→ 「4BP モードは別公式」 と思いたくなるが、 Score 公式は 1 つで対応可能
(`4 × pot = +16` で吸収)。

## この章で覚える項目 (4 items)

1. Bet sizing は実質 2 段階 (small 33% / over 100%+) で 90% カバー
2. SPR 4 段階 (オールイン / ロー / ミディアム / ディープ)
3. SPR=3 が GTO 戦略反転点
4. 4BP で アンダーペア 73% > set 4% の逆転 (4BP は別ゲーム)
"""

# ===================================================================
# 新章 13: 旧来のポーカー理論との橋渡し ★暗記補助
# ===================================================================
def gen_ch13_bridge() -> str:
    return f"""\
# 第 13 章　旧来のポーカー理論との橋渡し ★暗記補助

> 本章は **MATCHA Score の数値・分類を、 既知のポーカー古典理論にアンカー** する
> ことで暗記負荷を下げる橋渡し章です。 Rule of 4/2 / Sklansky Hand Groups /
> Theory of Poker / Range Morphology / Pot Odds / MDF など、 ポーカー文献で
> 標準的な概念と、 本書 4 カテゴリ × 3 board × 12 cells Grid の対応を整理します。
>
> **既知の理論にアンカーすることで、 12 cells や 5 例外を「丸暗記」 ではなく
> 「既存知識の再構成」 として吸収できる** ようになります。

## 13.1 Outs と Rule of 4/2 (Petriv et al.) — DV multiplier の整数化根拠

ポーカーで最も古典的な暗算ルールが **Rule of 4/2** (Phil Gordon、 Anton Petriv 等
が広めた)。 本書の `DV × mult[street]` はこの整数化です。

### 各 draw の outs カウント表

| draw 種類 | outs | dv_cat | DV 値 |
|---|---:|---|---:|
| combo (FD + OESD) | 12-15 | combo_draw | 4 |
| flush draw (FD/NFD) | 9 | flush_draw | 3 |
| OESD (オープンエンド) | 8 | oesd | 3 |
| gutshot (ガットショット) | 4 | gutshot | 1 |
| BDFD (2枚) | 2 | twocards_bdfd | 1 |
| BDFD (1枚) / no draw | 0-1 | onecard_bdfd / no_draw | 0 |

### Rule of 4 / Rule of 2 の定義

- **Rule of 4** (フロップで完成までの確率): `outs × 4 (%)` ≈ flop → river の 2 枚 ヒット確率
- **Rule of 2** (ターンで完成までの確率): `outs × 2 (%)` ≈ turn → river の 1 枚 ヒット確率

例: OESD (8 outs)
- flop: 8 × 4 = **32% 完成**
- turn: 8 × 2 = **16% 完成**

### DV multiplier (flop ×3 / turn ×2 / river ×0) が Rule of 4/2 の整数化である理由

本書の Score 公式:
```
DV × mult[street]
flop: ×3
turn: ×2
river: ×0
```

OESD (DV = 3) の場合:
- flop: 3 × 3 = **9 points 加算** (Score 14 → 23 の閾値跨ぎ可能)
- turn: 3 × 2 = 6 points
- river: 3 × 0 = 0

これは Rule of 4/2 を「Score 単位の整数」 に置換したもの:
- 8 outs × 4% ≈ 32% 完成、 これを 9 points (Score 単位) に変換
- 9 / 32% ≈ 0.28 (= 1 point per ~3.5% equity)

→ **公式の DV 計算は Rule of 4/2 を整数で覚えるだけ**。 draw 計算を
暗算可能な整数に変換した結果が DV × mult です。

### river で DV ×0 になる根拠

river では board が確定し、 draw は完成しません:
- outs × 0% = 0% (Rule of 0)
- ただし made hand の Grid 値はそのまま効く (TP+ × dry = 38 等)

→ river の判断は「made hand の絶対 value」 のみで決まり、 DV は無視。

## 13.2 古典ボード 7 分類 → MATCHA 3 分類 集約マトリックス

### 古典 7 分類 (Janda "Applications"、 Acevedo "Modern Poker Theory")

| 古典分類 | 典型 | 古典戦略 |
|---|---|---|
| Dry rainbow | Kh 7c 2d | small cbet 多用、 polar |
| Dry connected (低 gap) | 7-5-2 (span 5) | small cbet、 やや tight |
| Wet | T-9-8 | big cbet 低頻度、 protection |
| Monotone | 9h 7h 3h | small cbet、 flush 警戒 |
| Two-tone | Th 9h 4c | mixed、 span で connected 判定 |
| Paired high | K-K-7 | small cbet 多用、 TP+ adv |
| Paired low | 7-7-2 | small cbet 多用、 MERGED |

### MATCHA 3 分類への集約

| 古典 7 | MATCHA 3 | 根拠 |
|---|---|---|
| Dry rainbow / Dry connected | **dry** | unpaired + span > 4 (非 connected) |
| Wet / Monotone / Two-tone (connected) | **wet** | span ≤ 4 または mono |
| Paired high / Paired low | **paired** | 同 rank 2+ |

### 例 board の対応詳細

| board | 古典 | MATCHA | Score 影響 |
|---|---|---|---|
| K-7-2 rainbow | Dry rainbow | **dry** | Grid TP+ × dry = 38 |
| Q-9-8 ss | Wet (connected) | **wet** | Grid TP+ × wet = 31 |
| A-8-5 ds | Dry rainbow | **dry** | Grid TP+ × dry = 38 |
| J-7-2 ss | Two-tone (span 9) | **dry** | span 9 > 4 で connected ではない |
| K-K-7 | Paired high | **paired** | Grid TP+ × paired = 10 |
| T-9-8 ss | Wet 2-tone | **wet** | span 2 ≤ 4 で wet |
| 9h 7h 3h | Monotone | **wet** | mono で wet |
| 7-7-2 | Paired low | **paired** | Grid ミドル × paired = 40 |

→ 古典 7 分類で「どこに該当するか」 を判定したら、 集約 column を見るだけ。

### 集約根拠 (data 検証)

audit (n={AUDIT['n_spots']:,}) の結果 (詳細は第 10 章):

| 構成 | Grid cells | avg loss |
|---|---:|---:|
| 7 分類 × 4 カテゴリ | 28 | 0.3611 BB |
| 6 分類 × 4 カテゴリ | 24 | 0.3654 BB |
| **3 分類 × 4 カテゴリ (本書)** | **12** | **0.3587 BB ★** |
| 2 分類 × 4 カテゴリ | 8 | 0.3892 BB |

→ 3 分類で最良、 集約により情報損失なし。 sub-family の差は **Grid 値の hand×board
interaction** (例えば「ミドル × paired = 40 vs ミドル × wet = 10」) で吸収。

## 13.3 旧 6 階層 Hand Strength → MATCHA 4 カテゴリ 対応

### 旧 6 階層の定義 (Sklansky-Malmuth、 旧 MATCHA Framework)

| 階層 | 名前 | 含むハンド (例) |
|---:|---|---|
| 5 | ナッツメイド | FH / quads / SF |
| 4 | ストロング | set / flush / straight / 2P (3 系統合) |
| 3 | ツーペア | (独立扱い) |
| 2 | トップペア以上 | TP / overpair |
| 1 | アンダーペア | second / third / underpair |
| 0 | エア | high / king / ace high |

### MATCHA 4 カテゴリ への集約

| 旧 6 階層 | MATCHA 4 カテゴリ | 集約根拠 |
|---|---|---|
| ナッツメイド | **2P+** | 4BP で 2P 以上同挙動 |
| ストロング | **2P+** | dry で value bet 強行同一 |
| ツーペア | **2P+** | paired で slowplay 同様 |
| トップペア以上 | **トップペア以上 (TP+)** | 維持 |
| アンダーペア | **アンダーペア** | 維持 |
| エア | **エア** | 維持 |

### mv_cat (17 種) → 4 カテゴリ 対応表

GTO ソルバー 内部の `mv_cat` (made-value category) との対応:

```
2P+ (8 mv_cat):
  two_pair / set / trips / straight / flush
  fullhouse / quads / straight_flush

トップペア以上 (2 mv_cat):
  top_pair / overpair

アンダーペア (4 mv_cat):
  second_pair / third_pair / underpair / low_pair

エア (3 mv_cat):
  no_made_hand / king_high / ace_high
```

合計 17 mv_cat → 4 カテゴリ 集約。

### 「ツーペアを2P+に統合した data 駆動根拠」 (4BP huge -85%)

4BP audit (Cash 4BP + MTT 100bb 4BP 合算):

| 旧 6 階層 | 4BP huge spots | 4BP huge% |
|---|---:|---:|
| ナッツメイド | 18 | 3.1% |
| ストロング | 47 | 4.2% |
| ツーペア | 38 | 2.8% |
| トップペア以上 | 53 | 3.5% |
| アンダーペア | 41 | 2.9% |
| エア | 64 | 2.6% |

→ ナッツ / ストロング / 2P すべてが 3%+ huge (wet board 中心)。

| MATCHA 4 カテゴリ | 4BP huge spots | 4BP huge% |
|---|---:|---:|
| **2P+ (旧 3 つ統合)** | **18** | **0.4%** ★ |
| TP+ | 71 | 0.7% |
| ミドル | 89 | 0.6% |
| エア | 83 | 0.5% |

→ 2P+統合で 4BP huge% **0.4% に激減**、 全体 4BP huge% は **3.37% → 0.53%
(−85%)**。 「2P 以上は 4BP では強行 value」 という単純規則がうまくマッチしたため。



## 13.4 SPR 理論 (Flynn "Professional No-Limit Hold'em")

Ed Miller、 Sunny Mehta、 Matt Flynn 著 "Professional No-Limit Hold'em" (2007)
で確立された SPR (Stack-to-Pot Ratio) 理論。

### 古典 SPR 切り分け (1-3-7)

| 古典 SPR | 範囲 | 古典戦略 |
|---|---|---|
| Low SPR | < 1 | jam-or-fold |
| Mid SPR | 1-3 | commit decision (3BP 主流) |
| High SPR | 3-7 | post-flop play、 turn 計画 |
| Very high SPR | > 7 | deep stack、 implied odds |

### MATCHA 4 段階

| MATCHA SPR | 範囲 | 典型 |
|---|---|---|
| オールインSPR | < 1 | 4BP、 short stack push |
| ローSPR | 1-3 | 3BP、 短スタック |
| ミディアムSPR | 3-7 | SRP の turn 後 |
| ディープSPR | > 7 | Cash 100bb の flop、 200bb |

古典 4 段階と MATCHA 4 段階はほぼ同一定義。 境界の **1 / 3 / 7** が共通。

### SPR=3 が GTO 戦略反転点 — 同 K72 × SPR variation

audit で同 board (Ks 7d 2c) × SPR variation の cbet 頻度:

| カテゴリ | SPR 1.3 (4BP) | SPR 3.4 (3BP) | SPR 8 (Cash50) | SPR 16 (Cash100) |
|---|---:|---:|---:|---:|
| 2P+ (set) | **4%** | 41% | 69% | **96%** |
| ツーペア | 18% | 80% | 97% | 83% |
| トップペア以上 | 61% | 70% | 68% | 61% |
| アンダーペア | **73%** | 49% | 43% | 55% |
| エア | 41% | 46% | 46% | 44% |

SPR < 3 と SPR > 3 で挙動が **真逆**:
- SPR < 3: set 4% (slowplay)、 ミドル 73% (jam)
- SPR > 3: set 96% (fastplay)、 ミドル 55% (抑制)

これは古典 SPR 理論の「1-3-7 境界」 の **3** が反転点である data 駆動裏付け。

### 公式が SPR を pot 軸で吸収する仕組み

MATCHA Score は SPR を **直接** 持たず、 `4 × pot` で間接表現:

| pot | 値 | Score 補正 | 典型 SPR |
|---|---:|---:|---|
| SRP | 0 | 0 | 17 (ディープ) |
| vs CR | 2 | +8 | 4-5 (ミディアム) |
| 3BP | 2 | +8 | 4-5 (ミディアム) |
| 4BP | 4 | +16 | 1.5-2 (オールイン境界) |

pot 補正により、 SPR が低い場面 (3BP / 4BP) では Score が押し上げられ、 強気判断
(call / raise) に偏ります。 SPR を直接軸に取らずに済むのは「pot 種別が SPR を
ほぼ決める」 という data 検証された関係に基づきます。

## 13.5 Pot Odds と MDF (Minimum Defense Frequency)

ポーカーの古典定理: コール判断は **pot odds** で、 ベット側の bluff 抑制は
**MDF** で測られます。

### Pot Odds の定義

```
pot_odds = bet / (pot + 2 × bet)
必要 eq = pot_odds × 100 (%)
```

### MDF (Minimum Defense Frequency) の定義

ベット側が bluff を profitable にしないために、 受け側が必要な最低 defense 頻度:

```
MDF = 1 − pot / (pot + 2 × bet)
    = (pot + bet) / (pot + 2 × bet)
```

または「bet サイズ別 MDF」:
- 33% bet: MDF = 1 − 1/(1+2/3) = 60% (= bet 0.33pot vs pot 1.33+0.66)
- 75% bet: MDF = 1 − 1/(1+1.5) = 67%
- 100% bet: MDF = 1 − 1/3 = 67%
- 150% (overbet): MDF = 1 − 1/4 = 75%

### bs 別 pot odds 表

| bs key | pot 比 | pot odds | 必要 eq | MDF |
|---|---|---|---:|---:|
| small_33 | 33% | 1.66/4.66 | **25.4%** | 60% |
| med_75p | 75% | 3.75/8.75 | **30.0%** | 67% |
| med_100p | 100% | 5/12 | **33.3%** | 67% |
| overbet | 125-150% | 6.25/13.75 | **35-38%** | 67-75% |
| overbet_185 | 185% | 9.25/17.45 | **41%** | 73% |
| allin | 100%+ | varies | 33-50% | 67-100% |

### 公式閾値 ≥14 call、 ≥43 raise の意味づけ (MDF と Score の関係)

MATCHA Score の閾値 **14 と 43** は、 audit 駆動で決まった整数値ですが、 解釈する
と MDF / pot odds と整合します:

- **Score 14 (call 閾値)**: 必要 eq ≈ 25-33% に相当 (small-med bet で defend 可能)
- **Score 43 (raise 閾値)**: 必要 eq ≈ 50%+、 value range 確定

これは **MDF と公式 Score の関係**:
- Score が高い → MDF を満たす hand range で defense 可能
- Score が低い → fold (相手の bluff も含めて勝てない)

「Score 14 = pot odds 25% = small bet 受けの最低 defense 線」 と覚えると暗算が
自然に意味づきます。

## 13.6 Range Morphology (Janda "Applications"、 Sweeney "Quantum Poker")

Matthew Janda "Applications of No-Limit Hold'em" (2013) と Will Tipton "Expert
Heads Up No-Limit Hold'em" 等で確立された range structure 理論。 Pat Sweeney
"Quantum Poker" (2010) でも論じられる。

### 伝統用語の定義

| 伝統用語 | 定義 | 例 |
|---|---|---|
| **polarized** | 強い hand と bluff の二極構造 | river bet range = nut + air |
| **linear (merged)** | 中位 hand 中心の合算構造 | 早めの street、 value heavy |
| **capped** | 上限がある構造 (nut 含まない) | call back range、 weak |

### MATCHA との対応

| MATCHA レンジ分布 | 伝統用語 | 本書での扱い |
|---|---|---|
| **2 極化型** | polarized | dry board の cbet range、 polar value + bluff |
| **混在型** | linear / merged | wet board、 中位 hand 多 |
| **密集型** | capped | wet board の call back range |

### 各 morphology に対する戦略 (旧 vs MATCHA)

| morphology | 旧戦略 (Janda) | MATCHA Score での扱い |
|---|---|---|
| polarized | bluff catch wider、 raise narrow | dry board × Grid 値 (TP+ 38、 エア 3) で対応 |
| linear | thin value、 bluff catch narrow | wet board × Grid 値 (TP+ 31、 2P+ 23) |
| capped | overbet で攻める | 例外 11 ルール (wet × SRP) で表現 |

MATCHA は伝統的な range morphology 概念を board × カテゴリ × Grid に **吸収**
しています。 「相手のレンジを読む」 という抽象判断を Grid 12 cells の数値に
ダウンキャストしたのが本書のアプローチ。

## 13.7 Sklansky Hand Groups (1976 "Hold'em Poker")

David Sklansky の preflop hand groups (8 群、 後に Sklansky-Malmuth で 9 群)。
preflop 分類ですが、 postflop カテゴリ の **系譜** として理解できます。

### 群 1-8 の定義 (preflop、 一部抜粋)

| 群 | 例 hand | 古典評価 |
|---|---|---|
| 群 1 | AA / KK / QQ / AKs | premium |
| 群 2 | JJ / TT / AQs / AKo | very strong |
| 群 3 | 99 / JTs / QJs / KQs | strong |
| 群 4 | 88 / KJs / QTs / AJo | standard |
| 群 5 | 77 / 65s / 76s / KTs / QJo | playable |
| 群 6 | 66 / A9s / A2s | marginal |
| 群 7 | 55 / 44 / K9s / Q9s | weak playable |
| 群 8 以下 | 33 / 22 / J9o / 87o | weak |

### postflop カテゴリ (本書) との対応

Sklansky は preflop の group ですが、 hit したときの postflop カテゴリ は:

| Sklansky 群 | postflop カテゴリ (hit したとき) | 連想 |
|---|---|---|
| 群 1-2 (AA / KK / AKs) | **2P+** | set / flush / 強 overpair |
| 群 3-4 (JJ / TT / AQs / KQs) | **トップペア以上** | TP / mid overpair |
| 群 5-7 (mid SC / mid suited) | **アンダーペア** | second/third pair、 OESD |
| 群 8 以下 (rag) | **エア** | no pair、 weak draw |

→ Sklansky の preflop 群が高いほど、 postflop で2P+/TP+ に化ける確率が高い。

### 「Sklansky は preflop だが、 postflop カテゴリ の系譜」

Sklansky-Malmuth はあくまで preflop の暗算ルール (Chen Formula と並ぶ古典)
ですが、 「ハンドを階層化する」 という発想は本書 MATCHA Score の preflop 版 (Vol1)
にも、 postflop 版 (本書) にも生きています。

Vol1 (MATCHA Formula、 preflop) は Chen Formula と Sklansky Hand Groups の現代版。
Vol2 (本書、 postflop) はその postflop 拡張、 と理解してください。

## 13.8 Theory of Poker (Sklansky 1987)

David Sklansky "The Theory of Poker" (1987) の **Fundamental Theorem of Poker**:

### 定義

> 「相手のカードを見ながらプレイした場合と、 知らずにプレイした場合の EV ギャップが、
> 自分が間違うことで相手に与えた利益、 または相手が間違うことで自分が得た利益である」

要するに、 「**もし相手の手札が全部見えていたら何 EV か」 と「実プレイの EV」 の差**
が「自分の誤り」 で測られる、 という定理。

### MATCHA Score がこのギャップを整数近似で最小化する仕組み

MATCHA Score の audit は:

```
avg loss = E[ EV(GTO best action) − EV(formula action) ]
        = 0.3587 BB (per spot)
```

これは Theory of Poker の「自分の誤り」 を 0.3587 BB に近似的に抑える、 という
ことです。 「相手の手札を見たら GTO best action が分かる、 公式はその近似」。

### 「公式は Theory of Poker の暗算実装」

Theory of Poker は理論であり、 実プレイでは「相手の hand を読む」 こと自体が
困難です。 MATCHA Score は **整数化された カテゴリ × board × DV × pot × bs** で
「読む量」 を 5 軸の重み付け和に圧縮し、 「読む手間」 を 5-10 秒に短縮しました。

→ **公式は Theory of Poker の暗算実装版**。 Sklansky の理論を「実戦で 5 秒で
回せる形」 に落としたもの、 と理解してください。

## 13.9 Bet Sizing 理論 (modern GTO)

modern GTO 理論 (PIO Solver、 GTO ソルバー、 Acevedo "Modern Poker Theory") で
確立された bet sizing の意味づけ。

### 各 sizing の意味づけ

| sizing | 名前 | 意味 |
|---|---|---|
| **33%** | small (range cbet、 protection) | range advantage 利用、 wide range で bluff も含む |
| **75%** | medium polar | value heavy、 bluff も含む polar 構造 |
| **100%** | polar (nut advantage) | range advantage + nut advantage、 polar value |
| **overbet 125-185%** | super polar (capped opponent) | 相手 capped、 polar value + over-bluff |
| **all-in** | commit | committed range、 jam-or-fold |

### MATCHA bs 6 段階の根拠

本書の bs key は modern GTO の bet sizing 理論に基づく:

| bs key | 古典 sizing | 値 | 補正 |
|---|---|---:|---:|
| small_33 | range cbet | 0 | 0 |
| med_75p | medium polar | 1 | −2 |
| med_100p | polar (nut adv) | 2 | −4 |
| overbet | super polar | 3 | −6 |
| overbet_185 | very super polar | 4 | −8 |
| allin | commit | 5 | −10 |

各 sizing で「hero の必要 eq」 が変わるため、 Score に `−2 × bs` の減算項で
正確に反映。

### bet sizing 戦略の旧 vs MATCHA

| 状況 | 旧戦略 | MATCHA 公式 |
|---|---|---|
| dry board + range adv | small 33% | bs=0、 補正 0 |
| wet board + nut adv | polar 100% | bs=2、 補正 −4 |
| capped opp + nut adv | overbet 150% | bs=3、 補正 −6 |
| short stack push | all-in | bs=5、 補正 −10 |

→ MATCHA Score は bet sizing 理論を **数値の引き算** で吸収。 戦略を覚える代わりに
公式で計算するだけで対応可能。

## 13.10 暗記項目: 旧 → 新 対応 1 ページ早見表

詳細は **付録 B (旧来理論との橋渡し早見表)** に再掲。 ここでは 8 つの主要対応を
1 ページに集約:

| 旧来理論 | MATCHA 対応 |
|---|---|
| Outs と Rule of 4/2 | DV × mult[street] (flop ×3 / turn ×2 / river ×0) |
| 古典ボード 7 分類 | 3 タイプ集約 (dry / paired / wet) |
| 旧 6 階層 Hand Strength | 4 カテゴリ 集約 (上位 3 つを 2P+統合) |
| SPR 1-3-7 切り分け | MATCHA 4 段階 (オールイン / ロー / ミディアム / ディープ)、 SPR=3 反転点 |
| Pot Odds / MDF | bs 別 pot odds (25-41%)、 Score 閾値 14/43 |
| Range Morphology (polar/linear/capped) | 2 極化型 / 混在型 / 密集型、 Grid 値で吸収 |
| Sklansky Hand Groups (preflop) | postflop カテゴリ の系譜、 群 1-2 → 2P+ |
| Theory of Poker (Sklansky) | Score 公式が EV ギャップを整数近似で最小化 |
| Bet Sizing 理論 (modern GTO) | bs 6 段階、 −2 × bs で補正 |

旧来理論を学んだ読者は、 この対応表 1 つで MATCHA Score の各要素が「既知の概念の
再構成」 として理解できるはずです。

## Cash/MTT note

旧来理論との対応は Cash / MTT chipEV で共通です。 Sklansky / Janda / Flynn の古典
文献は主に Cash 100bb / heads-up を想定していましたが、 本書の 4 カテゴリ × 3 board ×
Grid 12 cells は **Cash 100bb と MTT chipEV (25/50/100/200bb) で同公式**。

ただし、 古典理論の前提 (deep stack、 no ante、 chipEV) は MTT 後期 / バブル
では崩れます。 第 21-23 章 (ICM/MW) の補正は古典理論の **拡張** として理解
してください。

## この章で覚える項目 (9 items)

1. Rule of 4/2 → DV × mult (flop ×3 / turn ×2 / river ×0)
2. 古典ボード 7 分類 → MATCHA 3 分類 (dry / paired / wet)
3. 旧 6 階層 Hand Strength → MATCHA 4 カテゴリ (2P+統合)
4. 古典 SPR 1-3-7 → MATCHA 4 段階、 SPR=3 反転点
5. Pot Odds: bs 33%→25% / 75%→30% / 100%→33% / overbet→38%
6. MDF と Score 閾値の対応 (14 = pot odds 25% / 43 = 50%+)
7. Range Morphology: polar / linear / capped → MATCHA 2極化 / 混在 / 密集
8. Sklansky 群 1-2 = 2P+、 群 3-4 = TP+、 群 5-7 = ミドル、 群 8 = エア
9. Theory of Poker (Sklansky 1987) = Score 公式が EV ギャップを整数近似で最小化
"""

# ===================================================================
# 第 4 部 (ch14-17、 renumber 後): SRP / 3BP / 4BP / vs CR
# ===================================================================
def gen_ch13() -> str:
    return f"""\
# 第 15 章　SRP — 標準 100bb

## 13.1 SRP の定義

**SRP** (Single Raised Pot) = プリフロップで 1 回のレイズ + 1 回のコールで成立した
ポット。 最も基本的な pot 種別。

Score 公式上は **pot = 0**、 公式そのままで対応します:

```
Score = Grid[カテゴリ][board] + DV × mult + 2 × oc − 2 × bs
```

(4 × pot = 0 のため省略可能)

## 13.2 audit 全体での SRP の位置

audit (n = {AUDIT['n_spots']:,}) の SRP セグメント:

- n = 43,660 (28.3%)
- huge%: {POT_HUGE_NEW['SRP']:.2f}% (旧 {POT_HUGE_OLD['SRP']:.2f}% から +32%、 やや悪化)
- 主な huge: 例外 1 (TP+ × wet × flop × SRP → fold) と例外 2 (2P+ × wet × river × SRP → raise)

SRP は huge% が新公式で **悪化** している唯一の pot 種別ですが、 これは「4BP を救う
代わりの代償」 として設計上許容されています。 例外 1〜2、 5 でほぼ救済。

## 13.3 BTN open vs BB call を基準とした全 spots audit

最も頻出の SRP spot 構造:

- BTN open (2.5bb) → BB call → flop
- effective stack: ~97.5bb
- pot: 5.5bb
- SPR: ~17 (ディープSPR)

このセットアップで GTO ソルバー 解析を回した spot 群が SRP audit の主体。

## 13.4 SRP 特有のパターン

### dry board での polarization

K-7-2 / A-7-2 / K-8-3 など dry board:
- BTN cbet 大多数 (40-50%、 small 33% 多用)
- TP+ は Grid 38 で強気 raise/call
- エアは bluff frequency 中心

### wet board での check 多用

T-9-8 / 7-6-5 など wet board:
- BTN cbet 低頻度 (28-35%、 大サイズ時のみ)
- 2P+は slowplay 寄り (Grid 23、 raise 閾値跨ぎにくい)
- 例外 5 (2P+ × wet × flop × SRP → fold) で 2P 過大評価を修正

### paired board での wide bet

K-K-2 / 7-7-2 / J-J-5 など paired board:
- アンダーペア × paired = 40 で強気
- TP+ × paired = 10 で慎重
- 例外なし (paired は概ね公式マッチ)

## 13.5 SRP × turn 以降の注意点

SRP の turn では effective SPR がまだ 5-8 と高めです:

- turn DV mult = 2 (Rule of 2)
- アンダーペアの value は flop より低下 (turn で TP の確定度↑)
- 例外 3 (ミドル × wet × turn × vs CR → fold) は SRP では発動せず (pot vs CR)

SRP の river では DV = 0 で made hand 勝負:

- TP+ × dry = 38 (river でも最大値の一つ)
- 2P+ × wet × river × SRP → 例外 2 で **raise** 強制 (公式 pred call)

## 13.6 SRP 内 huge% 内訳

SRP の huge spots は主に:

1. **TP+ × wet × flop × SRP → fold** (例外 1、 n=350)
2. **2P+ × wet × river × SRP → raise** (例外 2、 n=258)
3. **2P+ × wet × flop × SRP → fold** (例外 5、 n=125)
4. その他 (n < 100)

→ SRP の huge は **wet board** に集中。 dry / paired board の SRP は huge% < 1%。

## この章で覚える項目 (3 items)

1. SRP = Single Raised Pot、 pot 値 = 0
2. dry board は cbet 多用、 wet は慎重、 paired は wide
3. SRP の huge は wet board に集中 (例外 1 / 2 / 5 で救済)
"""

def gen_ch14() -> str:
    return f"""\
# 第 16 章　3BP — 3-bet Pot

## 22.1 3BP の定義

**3BP** (3-bet Pot) = プリフロップで 3-bet (再レイズ) + コールで成立した pot。

Score 公式上は **pot = 2** → **+ 4 × 2 = +8** の上方補正。

```
Score = Grid + DV × mult + 2 × oc + 8 − 2 × bs
```

## 22.2 3BP 特有の SPR 低下

3BP の typical setup:

- BTN open 2.5bb → SB 3-bet 10bb → BTN call
- effective stack: ~90bb
- pot: ~21bb
- SPR: ~4-5 (ミディアムSPR 寄り)

flop 後 effective SPR は 4 前後。 Cash 100bb の SRP (SPR 17) と比べ約 1/4。

## 22.3 +8 補正の意味

Score 公式の `4 × pot = +8` (3BP):

- 例: TP+ × dry × flop × 3BP × small_33
  - Grid[TP+][dry] = 38
  - + 4 × 2 = +8 (3BP)
  - − 2 × 0 = 0 (small)
  - Score = 38 + 0 + 0 + 8 − 0 = **46**
  - 46 ≥ 43 → **raise** (3BP で TP+ は強気)

SRP (pot=0) では Score 38 で call 閾値の下限近くだったハンドも、 3BP では Score 46
で raise 閾値を超え、 強気の出力に変わります。

## 22.4 3BP audit セグメント

- n = 27,648 (17.9%)
- huge%: {POT_HUGE_NEW['3BP']:.2f}% (旧 {POT_HUGE_OLD['3BP']:.2f}% から +75%)
- 主な huge: 例外 4 (エア × wet × turn × 3BP → call)

3BP の huge は SRP / 4BP より小さく、 大半は公式マッチ。

## 22.5 例外 4 のサンプリング

**エア × wet × turn × 3BP → call** (公式 pred fold、 n=159、 avg 9.5 BB)

具体例:
- BB 3-bet → BTN call → flop T-9-8 → turn 2
- BB hero ハンド: AQs (no pair、 board 4 つ overcards)
- 公式: Grid[エア][wet] = 1、 + 2 × 2 (oc) + 8 (3BP) − 4 (bs med_100) = 7 → fold
- GTO best: **call** (bluff catch range として残す)

例外 4 の理由: 3BP では相手の 3BP range が valudy ですが、 turn で **bluff 比率が上がる**
(opp は flop で cbet を bluff 強行している)。 hero エアでも overcard が多ければ
bluff catch 価値あり。

## 22.6 3BP の board family 別注意

### dry board × 3BP

- TP+ で強気 raise (Score 46-50)
- アンダーペアは要注意 (Score 26 で fold 閾値ぎりぎり)

### wet board × 3BP

- 2P+は slowplay 候補
- エアは例外 4 で bluff catch (turn 限定)

### paired board × 3BP

- ミドル × paired × 3BP = Grid 40 + 8 = 48 → raise 強行
- 公式に最も従順な spot

## 22.7 3BP × 4BP の境界

3BP の更に raise されると 4BP (第 16 章) になります。 Score 公式上:

| pot | 値 | Score 補正 |
|---|---:|---:|
| 3BP | 2 | +8 |
| 4BP | 4 | +16 |

差は +8。 これが 4BP で「2P+が call → raise」 「アンダーペアが fold → call」
に変わる原因。

## この章で覚える項目 (3 items)

1. 3BP = 3-bet Pot、 pot 値 = 2、 Score +8 補正
2. effective SPR ~4-5 (ミディアムSPR 寄り)
3. 例外 4 (エア × wet × turn × 3BP → call) で bluff catch
"""

def gen_ch15() -> str:
    return f"""\
# 第 17 章　4BP — 専用 lookup table (公式の代わりに役 × board で即決) ★

## 16.1 4BP は Score 公式が機能しない領域

**重要な発見**: 4BP では Score 公式は **acc 57.4% / MQS 71.3** に留まり、 12 cells のうち **D 級が 4 個** 残りました。

| cell | 平均 eq | bet 率 | 解釈 |
|---|---:|---:|---|
| **2P+ × paired** | **95.5%** | **15%** ★ | eq 高いのに check 主体 |
| 2P+ × dry | 91.0% | 41% | 同上 |
| 2P+ × wet | 85.8% | 25% | 同上 |
| TP+ × dry | 81.8% | 65% | ← bet 推奨 |
| TP+ × wet | 70.5% | 75% | ← bet 推奨 |
| ミドル × dry | 64.1% | 68% | ← bet 推奨 |
| ミドル × paired | 66.0% | 67% | ← bet 推奨 |
| エア × 全 board | 36-41% | 29-40% | check 推奨 |

→ **eq 95.5% でも bet 率 15%** という anomaly。 これは BB の **super tight 4-bet range** が FH/quads heavy で、 2P+ ですら blocker (相手の強 hand と被る) として check が GTO となるため。

eq-based grid + threshold モデルでは 4BP の特殊構造を捕捉できません。

## 16.2 解決: data 駆動の simple lookup

47,040 hands data で「bet 率 > 50% の cell」 を抽出すると、 **わずか 4 cells** に絞られます。

| カテゴリ | dry | paired | wet |
|---|---|---|---|
| 2P+ | check (41%) | check (15%) ★ | check (25%) |
| **TP+** | **bet (65%)** ★ | check (37%) | **bet (75%)** ★ |
| **ミドル** | **bet (68%)** ★ | **bet (67%)** ★ | check (43%) |
| エア | check (40%) | check (29%) | check (36%) |

### 4BP 専用ルール (公式 Score の代わりに lookup)

1. **TP+ × (dry or wet)** → **bet**
2. **ミドル × (dry or paired)** → **bet**
3. それ以外 (8 cells) → **check** (含む 2P+ も全 board check が GTO)

## 16.3 直感的解釈 — なぜ 2P+ ですら check か

4BP は BB の super tight 4-bet range (上位 ~3-5%) を相手にする状況。 相手のレンジは:

- FH / quads / set の確率が SRP の 5-10 倍
- TPTK 以下の hand は希少 (相手は 4-bet で folded)

このため自分が 2P+ を持っても:

- **相手の FH/quads と blocker 関係** (相手の hand と自分の hand が同じ rank を共有)
- bet すれば「相手の強 hand のみ continue」 = fold equity ゼロ
- check で showdown まで進める方が EV 高い

アンダーペア (= 自分の pocket pair が board に当たらず under) や TP は中間 hand で、 相手の TPTK/overpair から call を取れるので value bet が GTO。

## 16.4 アンダーペア × paired board の 67% bet (anomaly の本質)

ch12 で触れた「4BP × アンダーペア × paired で 73% bet」 は本 lookup で **再確認**:

- ミドル × paired: bet 率 67% (47K hands)
- 相手 4-bet range には paired board に hit する hand が少ない → fold equity 高い
- アンダーペアで「相手は board に当たってない」 と判定 → value/bluff hybrid bet

set/2P+ で bet しない代わりに、 アンダーペアで bet する **「逆 polarization」** が 4BP の GTO 特徴。

## 16.5 効果 (data 検証)

| 指標 | SRP grid + pot=+0.20 | 4BP 専用 lookup |
|---|---:|---:|
| Acc | 57.4% | **65.7%** (+8.3pp) |
| avg loss BB/hand | 0.120 | **0.120** |
| Cov (B 級以上 cell 比率) | 77.4% | **100.0%** ★ |
| **MQS v6** | **71.3** | **78.4** (+7.1) ★ |
| Cell grade dist | S=0 A=0 B=8 C=0 **D=4** | S=0 A=0 **B=12** C=0 **D=0** |

→ Lookup 採用で **全 cell が B 級以上**、 D cell が完全消滅。

## 16.6 4BP 公式無視の覚悟

第 1 部の Score 公式 (Grid + DV + 補正) は **SRP/3BP で完璧**ですが、 4BP では捨てて lookup に従う方が良い結果。 これは「文脈別に最適戦略が異なる」 ことの典型例。

## この章で覚える項目 (4 items)

1. **4BP では Score 公式を使わない**、 専用 lookup を使う
2. **bet 推奨 4 cells**: TP+ × dry/wet、 ミドル × dry/paired
3. **2P+ × paired bet 率 15%** ← BB super tight range で blocker 警戒
4. lookup 採用で MQS 71.3 → 78.4 (+7.1)、 全 cell B 級以上
"""


def gen_ch_turn_lookup() -> str:
    return f"""\
# 第 18 章　TURN — 専用 lookup + split rule (2P+ → bet、 overpair → bet、 役なし bluff)

## 17.1 TURN は SRP X-X 後の polarization 開始点

SRP context で flop check-check 後の turn first action は **bet 率 39%** とやや控えめです。 ところが cell 別に分解すると、 強 hand と完全 air の二極化が始まっています。

| カテゴリ | dry | paired | wet |
|---|---:|---:|---:|
| **2P+** | **81%** ★ | **72%** ★ | **53%** ★ |
| TP+ | 50% | 43% | 44% |
| ミドル | 19% | 48% | 19% |
| エア | 35% | 43% | 37% |

bet 率 > 50% のセルは **2P+ の 3 cells のみ**。

## 17.2 TURN 専用ルール (Score 公式の代わりに simple lookup + split rule)

```
① 2P+ (= 2P / set / trips / straight / flush / FH / quads / SF) → bet
② overpair (board の最高 rank より大きい pocket pair) → bet ★
③ no_made_hand (= 完全 air、 役にも high card にも到達せず) × paired/wet → bluff bet ★
④ それ以外 (TP / ミドル / エア with showdown value) → check
```

## 17.3 各ルールの data 裏付け

### ① 2P+ → bet (lookup 主体)

47K hands で全 2P+ cell が bet 率 > 50%。 turn での value bet 機会は強 hand に明確に集中。

### ② overpair → bet (split rule、 +1.2pp 改善)

TP+ × dry/wet は cell 平均で bet 率 50% boundary。 中でも **overpair (QQ-AA on under-board) は確定 bet**:

- 元来「TP+ × dry → check 50%」 の cell に overpair を分離追加
- acc 64.27% → 64.94% (+0.67pp)、 avg loss 0.0173 → 0.0134 (**-22%**) ★

### ③ no_made_hand × paired/wet → bluff bet (polarization 入口)

驚くべき発見: **完全 air (役なし、 draw も完成不可) でも turn で 50.7% bet** が GTO。

- no_made_hand × paired: 60.9% bet ★
- no_made_hand × wet: 45.6% bet
- no_made_hand × dry: 39.8% (採用しない、 boundary 以下)

これは GTO 理論の **polarization 戦略** の data 確証。 turn から「強 hand bet + 完全 air bluff bet」 の二極化が始まる。

## 17.4 ストリート別 polarization の中間段階

完全 air × no_draw の bet 率推移:

| ストリート | 完全 air の bet 率 | 段階 |
|---|---:|---|
| SRP flop | 6-32% | merged (bluff 抑制) |
| **TURN** | **50.7%** ★ | **polarization 入口** |
| RIVER | 56-74% | fully polarized |

turn は **「flop の merged 戦略から river の polarized 戦略への移行点」**。 強 hand bet と完全 air bluff の比率が同等程度になります。

## 17.5 効果 (data 検証)

| 指標 | Score 公式のまま | TURN 専用 lookup + split |
|---|---:|---:|
| Acc | 60.9% | **64.9%** (+4.0pp) |
| avg loss BB/hand | 0.0173 | **0.0134** (-22%) ★ |
| Cov | 94.0% | **100.0%** (D cell 消滅) |
| **MQS v6** | 77.8 | 75.7 (※) |
| **MQS v7 (実害)** | - | **90.6** ★ |

※ MQS v6 の機械的低下は outlier 数自体が減ったため (Outl F1 が分母縮小で下がる)。 v7 (avg loss ベース) では 90.6 と高評価。

## この章で覚える項目 (4 items)

1. **2P+ → 確定 bet** (3 cells lookup)
2. **overpair → 確定 bet** (split rule)
3. **no_made_hand × paired/wet → bluff bet** (polarization 入口)
4. turn から polarization 戦略開始、 完全 air の bluff bet 50%
"""


def gen_ch_river_split() -> str:
    return f"""\
# 第 19 章　RIVER — split rule v6 (役で value bet + 役なしで bluff bet)

## 18.1 RIVER は polarized strategy が最適

RIVER の構造的特徴: **役確定済み (draw 完成不可)** で、 equity が 0% / 100% に二極化します。 これにより GTO は **polarized strategy** (両端 bet、 中間 check) が最適となります。

## 18.2 RIVER 専用ルール (Score 公式無視)

```
① top_pair 以上 (= overpair / 2P / set / trips / straight / flush / FH / quads / SF) → value bet
② no_made_hand (= 完全に役なし、 high card にもならない) → bluff bet ★
③ それ以外 (ace_high / king_high / second_pair / low_pair etc.) → check
```

## 18.3 完全 air が 74% bet する GTO 理論の data 確証

| 場面 | bet 率 |
|---|---:|
| no_made_hand 全体 | 62.9% |
| × dry | 56.1% |
| × paired | 64.2% |
| **× wet** | **74.2%** ★ |

→ **「役なし、 draw なし、 call されたら 100% 負け確定」 の hand を 74% bet** が GTO 解。 これは相手の bluff catcher を fold させるための **bluff frequency 維持**。

教科書 (Janda、 Acevedo) が定性的に語ってきた polarization 理論を、 174K hands で初めて定量化した data です。

## 18.4 効果 (data 検証、 段階別)

| ルール | acc | avg loss BB/hand |
|---|---:|---:|
| baseline (Score 公式) | 45.05% | 0.384 |
| v1: top_pair 以上 → bet のみ | 65.52% | 0.086 |
| **v6: + no_made_hand → bluff** | **70.13%** ★ | **0.042** (-50%) |
| 参考 v8: + second_pair × paired/wet | 71.24% | 0.040 |

v1 → v6 で **+4.6pp acc / -52% loss**。 v8 は更に微改善だが暗算負荷増のため v6 を採用。

## 18.5 中間役 (ace_high, low_pair, second_pair) は check

これらは「**showdown value 保持 hand**」:

| 役 | river bet 率 | 解釈 |
|---|---:|---|
| ace_high | 14.9% | showdown まで進めば call 勝ち |
| king_high | 24.1% | 同上 (相手の queen_high 等に勝つ) |
| low_pair | 12.2% | bluff catcher、 相手の bluff に call |
| second_pair | 49.0% | boundary (paired board のみ bet 寄り) |

これらを bet すると「相手の TP+ に call され負け」 で大損。 「中間役は **check で showdown へ**」 が GTO 最適。

## 18.6 直感的解釈

RIVER は equity が 0% / 100% に近づく street:

- **強 hand (made)** = value bet (相手の bluff catcher から call を取る)
- **完全 air** = bluff bet (call されたら負け確定ですが、 fold equity 大)
- **中間 hand** = check (showdown で勝つか相手の bluff に call)

これは **「両端 bet、 中間 check」** の polarized strategy。 flop/turn では merged だった戦略が river で完全に二極化します。

## 18.7 効果 (data 検証)

| 指標 | Score 公式のまま | RIVER split v6 |
|---|---:|---:|
| Acc | 45.1% | **70.1%** (+25pp) ★★ |
| avg loss BB/hand | 0.384 | **0.042** (-89%) ★★ |
| Cov | 49.8% | **93.6%** (D cell 7 → 0) ★ |
| MQS v6 | 58.0 | **76.6** (+18.6) |
| **MQS v7 (実害)** | - | **88.2** ★★ |

→ **公式の中で最大の改善幅**。 5 context 中で RIVER だけ Score 公式が崩壊していたのが、 split rule で完全復活。

## この章で覚える項目 (4 items)

1. **役確定 (top_pair 以上) → 確定 value bet**
2. **役なし完全 air → 確定 bluff bet** ← 直感に反するが GTO 最適
3. 中間役 (ace_high, low_pair etc.) → **check で showdown へ**
4. RIVER acc 45 → 70% (+25pp)、 avg loss -89%、 公式中最大の改善
"""


def gen_ch_polarization() -> str:
    return f"""\
# 第 20 章　ストリート別 polarization — 完全 air が river で 74% bet する理由

## 18.1 GTO 理論の data 駆動の絵

ポストフロップにおける GTO 戦略は、 ストリート進行とともに **merged から polarized へ移行** します。 この理論は教科書 (Matthew Janda『Applications of No-Limit Hold'em』、 Michael Acevedo『Modern Poker Theory』) で定性的に語られてきましたが、 本書では **174K hands の data で初めて定量化** しました。

## 18.2 完全 air × no_draw の bet 率 (全 context 横断)

「役なし、 draw 完成不可、 call されたら 100% 負け確定」 の hand の bet 率:

| context | × dry | × paired | × wet | 段階 |
|---|---:|---:|---:|---|
| **SRP flop** | 13.4% | 9.6% | 6.3% | merged (bluff 抑制) |
| **3BP flop** | 14.8% | 16.8% | 22.0% | merged |
| **4BP flop** | 32.5% | 21.7% | 32.4% | merged (SPR 1.5 で aggression up) |
| **TURN** ★ | 39.8% | **60.9%** | 45.6% | **polarization 入口** |
| **RIVER** ★★ | 56.1% | 64.2% | **74.2%** | **fully polarized** |

### 解釈

- **flop (SRP/3BP)**: bluff bet 6-22% で **公式の check 推奨は GTO 平均的に正しい**
- **4BP flop**: SPR 1.5 と低いため bluff 頻度がやや上がる
- **turn**: paired board で 60.9% bet 開始、 polarization 入口
- **river**: 全 board で 56-74% bet、 fully polarized

## 18.3 なぜ river で完全 air が 74% bet するのか

直感的には「役なし、 draw なし、 call されたら 100% 負け確定」 の hand を bet するのは無謀です。 しかし GTO は polarization のために bet を要求します:

### bluff frequency 維持の必要性

相手の bluff catcher (中間 hand) を fold させるには、 bet レンジ内に十分な bluff combo を含める必要があります。

- 自分の **value range** (TP+ 以上) が bet → 相手 fold すると EV 損失
- **bluff range** (完全 air) も bet → 相手の bluff catcher を fold させて EV 獲得
- value : bluff の最適比率は **pot odds 由来** (例: 1/2 pot bet なら 2:1)

完全 air は call されたら 100% 負けますが、 **相手が中間 hand で fold する確率が高い** ため、 期待値プラスの bluff になります。

### 完全 air を bet する具体例

board: A♠ K♦ 5♣ T♥ 2♣ (river)
自分: 7♣ 6♣ (no_made_hand、 high card は 7)

- showdown まで進めば 100% 負け (相手の king_high にも負ける)
- でも相手の low_pair (= ace_high より弱い bluff catcher) を fold させれば pot 獲得
- → 74% の頻度で bet するのが GTO

## 18.4 ストリート別の戦略変化

| ストリート | 戦略 | 完全 air の扱い |
|---|---|---|
| **flop** | **merged**: 強 hand は thin value + medium hand mix | check 主体 (公式) |
| **turn** | **transition**: polarization 開始、 paired board から air bet 増 | 部分的 bluff bet |
| **river** | **polarized**: 強 hand value bet + 弱 hand bluff bet | **高頻度 bluff bet** |

## 18.5 暗算では何を覚えるか

この発見は MATCHA 公式に既に組み込み済み:

- **flop (SRP/3BP)**: Score 公式の check 判定が GTO 平均的に正しい → 何もしない
- **TURN**: 「no_made_hand × paired/wet → bluff bet」 ルール (第 17 章)
- **RIVER**: 「no_made_hand → bluff bet」 ルール (第 18 章)

実戦では特に意識せず、 各 context の lookup/split rule に従えば自動的に polarization 戦略が実現されます。

## 18.6 教科書理論の data 確証

| 教科書 | 提唱内容 | data 確証 |
|---|---|---|
| Matthew Janda (2013) | 「river で bluff frequency 維持」 | RIVER bluff 56-74% ★ |
| Michael Acevedo (2019) | 「ストリート別 polarization 移行」 | flop 6-32% → river 74% |
| Will Tipton (2018) | 「polarization は equity 分布で決まる」 | river equity 二極化を確認 |

本書はこれらを **暗算可能な lookup/split rule に翻訳** しました。

## この章で覚える項目 (3 items)

1. **flop は merged、 turn は transition、 river は fully polarized**
2. **river の完全 air は 74% bet** (相手の bluff catcher を fold させる)
3. 公式は既に polarization を組み込み済み (第 18/19 章)、 意識せず lookup に従えば OK
"""


def gen_appendix_c() -> str:
    return f"""\
# 付録 C　MATCHA Quality Score (MQS) — 公式の品質保証指標

## C.1 MQS とは

**MATCHA Quality Score (MQS)** は MATCHA Score 公式の総合品質を **0-100 で評価する指標** です。 174K hands × 5 context (SRP/3BP/4BP/TURN/RIVER) の検証で **公式が data 駆動で何 %正解か** を定量化します。

## C.2 5 component の評価軸

| Component | weight | 評価対象 |
|---|---:|---|
| Action Accuracy | 0.20 | 公式判定 = GTO 最適 の一致率 |
| Loss Quality (median) | 0.30 | 中央値 loss の小ささ (大半 hand で 0 BB か) |
| High-Conf Coverage | 0.20 | S/A/B 信頼度 cell に属する hand 比率 |
| Outlier Detection F1 | 0.15 | 役ベース outlier rule の検出能力 |
| Cross-Context Robustness | 0.15 | 5 context 間の MQS 標準偏差の逆数 |

## C.3 検証結果 (174,793 hands × 5 context)

| context | n | Acc | avg loss BB | Cov | MQS v6 | MQS v7 (実害) |
|---|---:|---:|---:|---:|---:|---:|
| **SRP** | 39,736 | 79.3% | 0.0066 | 100% | **82.9** | **94.6** ★ |
| **3BP** | 47,040 | 84.9% | 0.0190 | 100% | **84.3** | **94.8** ★ |
| **4BP** | 47,040 | 65.7% | 0.1199 | 100% | **78.4** | **84.0** |
| **TURN** | 21,227 | 64.9% | 0.0134 | 100% | **75.7** | **90.6** |
| **RIVER** | 19,753 | 70.1% | 0.0415 | 94% | **76.6** | **88.2** |
| **Integrated** | **174,793** | **73.0%** | **0.040 BB** | **98.7%** | **82.0** | **91.2** ★ |

**Grade**: **S (≥80)** / A (70-80) / B (60-70) / C (50-60) / D (<50)

→ **MATCHA Score 公式は Grade S 確定** (v6=82.0、 v7=91.2)。

## C.4 MQS v6 と v7 の違い

- **MQS v6 (保守的)**: Outl F1 ベースで 82.0 — 「公式 outlier 検出能力」 込みの厳しい評価
- **MQS v7 (実害)**: avg loss ベースで 91.2 — 「実際の BB loss」 を直接測定した真の品質

v7 が「公式が実戦で何 BB 損させるか」 を直接表す **真の品質指標** です。

## C.5 MQS 改善の歴史

| 版 | 改良点 | Integrated MQS |
|---|---|---:|
| v1 | 初版 (cell 別 SD 評価) | 74.8 |
| v3 | outlier rule 確定 (5 context 別) | 78.9 |
| **v4** | data 倍増 (20→40 spots × 4 ctx) | **80.6** ★ |
| **v6** | 4BP/TURN lookup + RIVER split v6 | **82.0** ★ |
| **v7** | 実害ベース指標 (avg loss) | **91.2** ★★ |

## C.6 MQS の天井理由

**MQS v6 = 82.0 は暗算可能な公式での実質的天井** です。 これを超えるには:

- 公式の outlier の主因 = **cell 内の hand-level eq 差** (cell 平均では bet/check 判定できない)
- 弱 カテゴリ × draw / bluff bet の見落とし: SRP/3BP の outlier の 32-53% を占めるが、 flop では no_made_hand bet 率が 15-24% で「弱 カテゴリ → bet」 ルールは GTO に逆行
- 真の改善には **hand-level eq 計算** が必要 = solver-level (暗算放棄)

つまり MQS 82 は「**暗算 philosophy を維持した最適点**」 です。

## C.7 公式品質保証宣言

本書の MATCHA Score 公式 (5 章のルール) は:

- **174,793 hands で検証**
- **avg loss 0.040 BB/hand** (100 hand 平均で 4 BB の損失)
- **Grade S (MQS 82.0 / 91.2)**
- 全 cell が B 級以上 (D cell 完全消滅)

→ **「暗算で回せる公式」 で実 GTO に最も近い精度** を達成しました。

"""


def gen_ch16() -> str:
    return f"""\
# 第 21 章　vs CR (CR ディフェンス) — turn donk vs CR は真逆

## 20.1 vs CR の定義

**vs CR** (CR ディフェンス) = hero が cbet 後に相手から **チェックレイズ**
または **ドンクベット** を受けた場面。 「DEF」 という旧称は廃止。

Score 公式上は **pot = 2** → **+ 4 × 2 = +8** (3BP と同じ補正)。

```
Score = Grid + DV × mult + 2 × oc + 8 − 2 × bs
```

## 20.2 vs CR の typical setup

- BTN open → BB call → flop → BTN cbet → BB raise → BTN ?
- pot は cbet 倍率分膨らんでいる (SRP × 1.5〜2 程度)
- effective SPR: 3-5 (ミディアムSPR)

## 20.3 turn donk vs turn CR は真逆

データ検証で判明した重要事実:

| シナリオ | 相手の range 構造 | hero defense 推奨 |
|---|---|---|
| **vs CR** (check raise 受け) | opp value-heavy (46% strong) | tight defense、 fold 多用 |
| **vs Donk** (ドンクベット受け) | opp air-heavy (54-61% weak) | wide defense、 call 多用 |

同じ pot 種別 (vs CR = 2、 vs Donk = 2) なのに **相手のレンジ構造が真逆**。

### audit データ

| 状況 | opp_strong% | opp_weak% |
|---|---:|---:|
| BTN flop cbet → BB CR | 46% | 22% |
| BB flop donk (BTN は preflop raiser) | 18% | 54% |
| BTN turn check → BB bet (donk) | 14% | 61% |

→ CR は「相手が強い signal」、 Donk は「相手が弱い signal」。

## 20.4 Score 公式での扱い

本書は両者を **pot=2 (+8)** で同一扱いします。 これは:

- audit で「pot 軸を vs CR / vs Donk に分離しても性能向上せず」
- 例外 3 (ミドル × wet × turn × vs CR → fold) と例外 4 のような **個別例外** で差を吸収

例外 3 は vs CR の「相手 value-heavy」 を反映。 例外 4 は 3BP × wet × turn の bluff
catch (vs Donk と似た構造)。

## 20.5 vs CR audit セグメント

- n = 34,092 (22.1%)
- huge%: {POT_HUGE_NEW['vs CR']:.2f}% (旧 {POT_HUGE_OLD['vs CR']:.2f}%)
- 主な huge: DEF T_raise=49 補正 + ex9/ex10 Turn CR fold 不足
- vs CR 総合精度: **80.5 Grade S** (208K hands 検証)

## 20.6 vs CR の board family 別注意

### dry × vs CR

- TP+: Grid 38 + 8 = 46 → **DEF T_raise=49** → call (GTO CALL 61%)
  - ⚠️ DEF 文脈 T_raise=49 を使う。 Score=46 < 49 → call
- TP+ × dry × turn × vs CR: **ex10 でさらに fold** に変換 (GTO FOLD 62.3%)
  - turn だけ「fold まで下げる」 point に注意 (flop/river は call)
- ミドル × dry: Grid 18 + 8 = 26 → call (踏ん張る)
- TP+/ミドル × dry × turn × vs CR: **ex9 で fold** に変換 (TP+ GTO FOLD 56%、 ミドル GTO FOLD 71.5%)
  - ⚠️ vs Donk には ex9/ex10 を適用しない

### wet × vs CR

- ミドル × wet × turn × vs CR: 例外 3 で **fold 強制**
  - 公式 Score: Grid 10 + 0 (turn DV=0 if no draw) + 8 − 4 (bs med_100) = 14 → call
  - 実 GTO: fold (相手 value-heavy)
- 2P+ は Grid 23 + 8 = 31 → call (slowplay)
- エアは Grid 1 + 8 − 4 = 5 → fold

### paired × vs CR

- ミドル × paired: Grid 40 + 8 = 48 → **DEF T_raise=49** → call (GTO CALL 91-97%)
  - ⚠️ DEF 文脈 T_raise=49 を使う。 Score=48 < 49 → call
- TP+ × paired = 10 + 8 = 18 → call (trip 警戒)

## 20.7 ドンクベット受け (vs Donk) の扱い

vs Donk も pot = 2 として同じ式で扱いますが、 相手の range が異なるため:

- vs Donk × エア: 公式上は fold 寄りですが、 実 GTO は call 寄り (bluff catch)
- vs Donk × TP+: 公式上 call、 実 GTO もそのまま (donk への TP+ は call 維持)

**DEF 閾値補正 (vs Donk でも適用):**
- ミドル × paired: Score=48 → T_raise=49 → call (旧 raise 誤判定を解消)
- TP+ × dry: Score=46 → T_raise=49 → call (旧 raise 誤判定を解消)

**vs Donk 専用例外:**
- **ex11**: 2P+ (trips/FH/quads) × paired × river × vs Donk → raise (value)。 Donk の river range は弱く GTO RAISE 100%

## この章で覚える項目 (6 items)

1. vs CR = check raise/donk 受け、 pot 値 = 2、 Score +8 補正
2. vs CR は opp value-heavy (相手 46% strong)
3. vs Donk は opp air-heavy (相手 54-61% weak、 真逆)
4. **DEF 閾値補正**: vs CR/Donk では T_raise = **49** を使う (通常 43 から引き上げ)
5. **ex9**: (アンダーペア/TP+) × dry × turn × vs CR → fold (⚠️ vs Donk 不可)
6. **ex10**: TP+ × wet × turn × vs CR → fold (⚠️ vs Donk 不可)
7. **ex11**: river × vs Donk × trips以上 × paired → value raise
"""

# ===================================================================
# 第 22 章　vs Donk Bet 専門
# ===================================================================
def gen_ch_vs_donk() -> str:
    return """\
# 第 22 章　vs Donk Bet — ドンクベットへの対応

## 21.1 ドンクベットとは

**ドンクベット (Donk Bet)** = ポストフロップで IP（先手）の c-bet を待たずに
OOP（後手）が先にベットしてくる行動です。

```
通常フロー: OOP check → IP bet → OOP call/raise/fold
ドンク   : OOP bet (= donk) → IP call/raise/fold
```

IP は「自分がアクション側」になるはずの局面で、突然ディフェンス側に回されます。

## 21.2 ドンクの発生頻度 — ターンカードが鍵

GTO データで判明した重要事実: **ドンクの頻度はターンカードで激変します**。

| ターンカードの種類 | ドンク頻度 | 代表例 |
|---|---:|---|
| ブランク / オーバーカード | ≈ 0% | Ks7d2c **5h** / **Jh** |
| ストレート完成カード | 7-14% | Td7c6s **8h** |
| ボードペアカード | 19-41% | Ks7d2c **Kh** / **7c** |

> OOP がターンをドンクするのは「ボードペアカードでトリップス以上を作った」か、
> 「ストレートを完成させた」場合がほとんどです。

### フロップドンク

フロップは SRP でほぼ 0% (例: Ks7d2c 0%, 9h8s7d 0%)。
OOP がフロップをドンクしてきた場合は **レンジの逸脱** と判断してよいです。

## 21.3 vs Donk のレンジ分析 — vs CR と真逆

同じ pot=2 の文脈でも、相手のレンジ構造が vs CR と真逆です。

| 文脈 | opp strong% | opp weak% | 意味 |
|---|---:|---:|---|
| vs CR (チェックレイズ受け) | 46% | 22% | 相手 value-heavy |
| vs Donk (ドンクベット受け) | 14% | 61% | 相手 air-heavy |

→ **ドンクは相手が弱いシグナル**。IP は wide defense で対応できます。

## 21.4 MATCHA Score での計算

vs Donk も **pot = 2** として扱います（vs CR と同じ）。

```
Score = Grid + DV × mult + 2 × oc + 4 × pot − 2 × bs
                                        ↑ pot=2 → +8
```

ただし **vs CR 専用例外 (ex9/ex10) は vs Donk に適用しない**こと。

| 例外 | vs CR | vs Donk |
|---|---|---|
| ex9: UP/TP+ × dry × turn → fold | ✓ 適用 | ✗ 不適用 |
| ex10: TP+ × wet × turn → fold | ✓ 適用 | ✗ 不適用 |

理由: ex9/ex10 は「vs CR では相手が value-heavy」という前提。
vs Donk では相手が air-heavy なので fold は損。

## 21.5 ターンドンク — ボードペア時の対応

ターンがボードをペアしてきた場合 (e.g., Ks7d2c → **Kh** or **7c**)、
OOP のドンク頻度が 19-41% に跳ね上がります。

| 自分のハンド | Score 計算 | 推奨アクション |
|---|---|---|
| 2P+ (セット/ツーペア) | Grid 高 + 8 ≥ 43 | **call / 状況によりraise** |
| TP+ | Grid 38 + 8 = 46 → DEF T=49 | **call** |
| アンダーペア | Grid 低 + 8 | 公式に従い call or fold |
| エア | Grid 1 + 8 = 9 | fold |

> **ポイント**: ボードペア時の donk は相手が trips を持っている可能性が高い。
> こちらも trips 以上 (ex11) なら raise、それ以下は call または fold で対応。

## 21.6 vs Donk 専用例外

### 例外 11: 2P+ × paired × river × vs Donk → raise (value)

```
river × paired board × 自分が 2P+(trips/FH/quads) × vs Donk → RAISE
```

- GTO RAISE: 100%
- 理由: river vs Donk のレンジは bluff が多く、IP の 2P+ はナッツ優位
- ターンへの適用は不可（ターンでは slowplay が有効）

## 21.7 フロップドンク — 対応指針

フロップドンクは GTO では稀（≈0%）ですが、ライブや低ステークスでは起こります。

- 相手のドンクはレンジ逸脱 → wide defense
- Score を pot=2 で計算してそのまま適用
- TP+ 以上: call
- 2P+: raise を検討（相手のドンクが弱い手である可能性高）
- エア: fold

## 21.8 リバードンク — ポラライゼーション

OOP がリバーをドンクする場合: ポラライズされた range (ナッツ or ブラフ)。

| 自分のハンド | 対応 |
|---|---|
| 2P+(trips+) × paired | → raise (ex11) |
| TP+ | → call |
| アンダーペア | → DEF T=49 で判断 |
| エア | → fold |

## この章で覚える項目 (6 items)

1. ドンクはターン **ボードペアカード** で頻度急増 (19-41%)、それ以外は ≈0%
2. vs Donk のレンジは **air-heavy** (54-61% weak)、vs CR と真逆
3. Score 計算は pot=2 (+8) — vs CR と **同じ公式**
4. **ex9/ex10 は vs Donk に不適用** (fold → call に留める)
5. **DEF 閾値補正**: T_raise = 49 は vs Donk でも適用
6. **ex11**: river × paired × 2P+(trips+) × vs Donk → raise
"""


# ===================================================================
# 第 5 部 (ch17-19)
# ===================================================================
def gen_ch17() -> str:
    return f"""\
# 第 24 章　短スタック (≤ 25bb)

## 17.1 短スタックでの Score 公式の挙動

short stack (effective ≤ 25bb) では SPR が自動的に低下します:

| typical | stack | pot 初期 | flop SPR |
|---|---:|---:|---:|
| Cash 100bb SRP | 100 | 5.5 | ~17 |
| MTT 50bb SRP | 50 | 5.5 | ~8 |
| MTT 25bb SRP | 25 | 5.5 | **~3.5** |
| MTT 15bb SRP | 15 | 5.5 | ~1.7 |

短スタックでは **ディープSPR → ミディアムSPR → ローSPR** に自動下がりし、
SPR=3 の戦略反転点をしばしば跨ぎます。

## 17.2 short stack の committed range

SPR < 3 では「ペア以上 = コール」 が GTO 推奨 (committed range):

- アンダーペア以上 → all-in 受けでもコール (例: K72 で 55、 effective 20bb)
- エア + draw → ふつう fold ですが、 SPR < 2 の場合は jam 候補

Score 公式上は **4 × pot** が小さいため pot 補正が効かない一方、 short stack では
**bs (実際の bet サイズ) が pot に対して大きく出る** ため −2 × bs が効きすぎる
ことがあります。

→ short stack では bs を厳密に判定 (例: 8bb pot に 5bb cbet = 62% → med_75p 扱い)。

## 17.3 MTT 25 での Score 閾値補正

MTT 25bb のような short stack では、 経験的に閾値を以下のように補正:

- T_call: 14 → **12** (call wide 化、 committed range で fold しすぎない)
- T_raise: 43 → **40** (raise threshold やや下げる、 jam-or-call を促進)

ただしこれは大まかな目安。 厳密には例外ルールで対応します。

## 17.4 short stack での例外ルール調整

例外 11 ルール (第 9 章) のうち、 short stack で挙動が変わるもの:

- 例外 1 (TP+ × wet × flop × SRP → fold): short stack では Score 18 + DV ≈ 24 で fold せず call。 short stack は committed。
- 例外 2 (2P+ × wet × river × SRP → raise): short stack でも有効、 むしろ jam 化
- 例外 3 (ミドル × wet × turn × vs CR → fold): short stack では call 維持 (committed)

→ short stack では **例外 1 と 3 を無効化** が指針。

## 17.5 ICM 連携 (短スタック × バブル)

short stack × バブル では Score 公式に追加補正が必要 (第 22 章 参照)。

- バブルでは t_call +5〜+10 (fold tight 化)
- short stack × バブル の short stack は **「fold 寄りの jam-or-fold」**

詳細は第 6 部 (ICM/MW) で扱います。

## この章で覚える項目 (3 items)

1. short stack (≤25bb) は SPR 自動下げ、 SPR=3 を跨ぐことが多い
2. T_call 14 → 12、 T_raise 43 → 40 で補正
3. 例外 1 と 3 は short stack で無効化 (committed)
"""

def gen_ch18() -> str:
    return f"""\
# 第 25 章　深スタック (200bb+)

## 17.1 深スタックでの Score 公式の挙動

deep stack (effective 200bb+) では SPR が自動的に上昇します:

| typical | stack | pot 初期 | flop SPR |
|---|---:|---:|---:|
| Cash 100bb SRP | 100 | 5.5 | ~17 |
| Cash 200bb SRP | 200 | 5.5 | **~35** |
| Cash 500bb SRP (high stake) | 500 | 5.5 | ~90 |

deep stack ではディープSPR が更に深くなり、 implied odds が大きく効きます。

## 17.2 deep stack での implied odds

SPR > 20 では:

- アンダーペア × flop → コール (set up 価値、 turn / river で 2P / set 完成期待)
- gutshot / OESD → コール (大量の implied odds)
- スーテッドコネクター → wide call

Score 公式の DV × mult は flop で 12 (combo draw)、 turn で 8 まで上がります。
これに deep stack の implied odds を考慮するなら +2〜+3 の補正:

- DV(3) → 実 implied DV(4) on deep stack
- gutshot DV(1) → 実 DV(2)

ただしこれは大まかな目安、 厳密化は本書のスコープ外。

## 17.3 200bb での Score 閾値補正

Cash 200bb の audit (limited data) から推定する補正:

- T_call: 14 → **16** (call slightly tight、 deep stack では bluff catch 慎重に)
- T_raise: 43 → **45** (raise threshold やや上げる、 over-protection 抑制)

→ deep stack では **post-flop の implied odds 価値を Score に乗せる** より、
閾値を上げて「強い手だけ raise / value 重視」 が GTO 推奨。

## 17.4 Cash 200bb と MTT 200bb の同構造性

audit (limited、 ~10K rows) で Cash 200bb と MTT 200bb の挙動を比較:

- 同 board / 同 hand での GTO action 一致率 92%+
- huge spots の構造が同じ (主に wet × river)
- 例外ルール 5 つはそのまま適用可能

→ MATCHA Score は **stack depth 軸でも汎用** と確認。

## 17.5 deep stack での board family 別注意

### dry × deep

- TP+: 慎重 (Score 38 + 0 = 38 → call)、 overprotection 控える
- 2P+: slowplay 強化 (deep stack では trap が効く)
- ミドル: 18 + 0 = 18 → call (implied odds で許容)

### wet × deep

- 例外 1 (TP+ × wet × flop × SRP → fold) は deep stack でも有効
- 2P+ × wet × river × SRP → raise (例外 2)、 deep stack でこそ
  pot コントロール後の overbet 価値が出る

### paired × deep

- ミドル × paired = 40 → raise 強行 (deep stack でも変わらず)

## 17.6 200bb での例外ルール調整

例外 11 ルール (第 9 章) のうち、 deep stack で挙動が変わるもの:

- 例外 1 (TP+ × wet × flop × SRP → fold): deep stack で **更に強化** (fold 厳格に)
- 例外 2 (2P+ × wet × river × SRP → raise): deep stack でこそ overbet 化
- 例外 4 (エア × wet × turn × 3BP → call): deep stack でも有効 (bluff catch)

deep stack では例外 1 と 2 が最頻出パターン、 確実に覚える。

## この章で覚える項目 (3 items)

1. deep stack (200bb+) は SPR 自動上げ、 implied odds 大
2. T_call 14 → 16、 T_raise 43 → 45 で補正
3. Cash 200bb = MTT 200bb の同構造性 (MATCHA Score 汎用)
"""

# ===================================================================
# 第 6 部 (ch20-23) — 定性 + テーブルサイズ
# ===================================================================
def gen_ch19() -> str:
    return """\
# 第 27 章　ICM 入門 — chipEV と $EV のズレ ★定性

> **本章は定性記述のみ**。 ICM/PKO の postflop GTO data は データ取得 tier
> 制限で取得不能なため、 数値モデル化は将来 Vol2.5 (ICM/PKO 別冊) で対応予定。
> 本章では MATCHA Score を ICM 局面で使う際の **方針** のみを示します。

## 20.1 chipEV と $EV の違い

本書のメイン公式 MATCHA Score は **chipEV** ベースで最適化されています。

- **chipEV**: チップ単位の期待値 (1 チップ = 1 単位として計算)
- **$EV** ($/dollar EV): 実払戻し ($) ベースの期待値

Cash と MTT chipEV (25/50/100/200bb) では両者が一致するため、 MATCHA Score は
そのまま適用可能。 一方 **ICM ステージ (賞金圏直前以降)** では両者に大きな乖離が
生じ、 chipEV ベースの判断が損失を生むことがあります。

## 20.2 リスクプレミアム

「リスクプレミアム」 (risk premium) とは:

- 同 chipEV ハンドが ICM ステージで $EV− になる現象
- 短スタックは「fold すると一気に減るマージン」 が薄く、 jam を厳しめに
- チップリーダーは「bust リスクなし」 で wide pressure 可能

### 数値感覚

| ICM ステージ | 推定リスクプレミアム |
|---|---:|
| ICM なし (chipEV) | 0% |
| FT 9-handed | 2-5% |
| FT 5-handed | 5-10% |
| FT 3-handed | 10-15% |
| バブル (賞金圏直前) | **15-25%** |
| heads-up | 5-15% |

リスクプレミアム ≈「Score の閾値を引き上げる相当量」 と考えてください。

## 20.3 ICM Pressure の階層

ICM Pressure (圧力) は次の階層で増加:

1. **early-mid stage MTT** → chipEV 同等 (本書公式 そのまま)
2. **late stage MTT** → ICM 軽い (補正 +2 程度)
3. **バブル** → ICM 最大 (補正 +5〜+10)
4. **賞金圏内 FT** → ICM 強 (補正 +3〜+8)
5. **heads-up** → 軽く戻る (補正 +1〜+3)

## 20.4 MATCHA Score の ICM 修正方針 (定性)

ICM ステージで MATCHA Score を使う際の **方針** (数値は目安):

- **T_call を引き上げ**: 14 → 16〜20 (call wide 化抑制)
- **T_raise を引き上げ**: 43 → 45〜50 (raise tight 化)
- **大きな pot を避ける**: 4BP / vs CR は特に慎重 (bust リスク高)
- **2P+以外の overbet 受け fold 化** (bluff catch range 削減)

これらは厳密な data 駆動ではなく、 ICM 一般理論からの推定。 実 ICM データを
audit するには GTO ソルバー ICM tier (現在 取得不能) が必要。

## 20.5 short stack vs chip leader

ICM 局面では stack size で挙動が真逆に分かれます:

| stack 立場 | 行動方針 | Score 補正 |
|---|---|---|
| chip leader | wide pressure、 bully | T_call −3〜−5 (緩める) |
| big stack (top 3) | tight value | T_call +0〜+2 |
| mid stack | tight pressure 受け | T_call +5〜+10 (厳しめ) |
| short stack | jam-or-fold | T_call +0 (commit 状態) |

chip leader は「bust リスクなし」 で wide で、 mid stack は「両側に挟まれる」
立場で最も tight。

## 20.6 なぜ ICM data モデル化が困難か

ICM の数値モデル化は将来課題 (Vol2.5) です。 理由:

1. **データ取得制限**: GTO ソルバー ICM tier は postflop tier で 403 (取得不能)
2. **context の組合せ爆発**: stack 配分 (3+ players) × payout 構造 × position
3. **stage 別の動的変化**: 同じハンドが stage 進行で挙動変化
4. **データ scarcity**: chipEV データほど豊富にない

→ 当面は **MATCHA Score + ICM 補正 (定性)** で運用。

## この章で覚える項目 (4 items、 すべて定性)

1. chipEV (本書前提) と $EV (実払戻し) は ICM で乖離
2. リスクプレミアム = Score 閾値の引き上げ相当量
3. バブルが ICM 最大 (補正 +5〜+10)
4. ICM 数値モデル化は将来 Vol2.5 で対応予定
"""

def gen_ch20() -> str:
    return """\
# 第 28 章　バブル戦略 — リスクプレミアムの極大化 ★定性

> **本章は定性記述のみ**。 ICM/PKO 数値モデル化は将来 Vol2.5 で対応予定。

## 21.1 バブルの定義

**バブル** = MTT で「賞金圏直前」 の状況。 例: 全 100 人で in-the-money 15 人なら、
残り 16 人になった瞬間からバブル。 1 人飛ぶと 15 人全員が賞金獲得 → ICM Pressure 最大。

## 21.2 ICM Pressure の最大化

バブルでは ICM Pressure (リスクプレミアム) が **最大** になります:

- **short stack**: jam しないと先送りされ blinds で消耗、 一方 jam で bust 致命傷
- **chip leader**: bust リスクなしで wide pressure
- **mid stack**: 両側に挟まれる、 行動できない (lock-up 現象)

## 21.3 short stack jam range の絞り

chipEV (本書 デフォルト) の jam range より **tight** な jam range が GTO 推奨:

| ICM ステージ | short stack (15bb) jam range |
|---|---|
| chipEV (no ICM) | ~30% (LP open + reraise) |
| ICM mild (FT 9) | ~25% |
| ICM heavy (FT 5) | ~20% |
| **バブル** | **~15%** (Premium + 高エクイティのみ) |

→ MATCHA Score の T_call / T_raise を「Score +5〜+10」 相当に引き上げる。

## 21.4 chip leader の wide steal

chip leader は逆に bully:

- 全 position で wide open (BTN 60%、 CO 45%、 etc.)
- short / mid stack の defense は tight になるため、 fold equity 高
- 4BP / 5BP の jam を受け止める stack も持つ

→ chip leader 視点では MATCHA Score の T_open / T_3bet を緩める。

## 21.5 mid stack の受難

mid stack (上から 3-5 番手) は最も厳しい:

- chip leader からの pressure を受ける (fold せざるを得ない)
- short stack の jam を受け止めにくい (bust すると mid 失格)
- 結果: **tight 一方通行**、 行動不能

mid stack の survival 戦略:

- premium hand のみ play (AA / KK / QQ / AK)
- speculative hand (SC / mid pair) は fold
- bubble 通過後に通常 strategy 復帰

## 21.6 short stack スタイルの jam threshold (定性)

short stack (≤ 12bb) の jam range は ICM stage 別に変化:

| stack | chipEV jam range | バブル jam range |
|---|---|---|
| 10bb | 30% (LP) | 18% |
| 8bb | 40% | 25% |
| 5bb | 60% | 45% |
| 3bb | 90% | 80% (any 2 fold 困難) |

short stack 程 ICM 影響小 (もう committed の領域)。 大きい short stack ほど tight 化。

## 21.7 MATCHA Score 適用上の注意

バブルで MATCHA Score を使う際:

1. **T_call を +5〜+10 引き上げ** (14 → 19〜24)
2. **T_raise も同等引き上げ** (43 → 48〜53)
3. **4BP / vs CR は特に慎重** (bust リスクの大きい pot)
4. **2P+以外の wet × river overbet 受け → 強制 fold** (例外 2 を逆方向に override)

例:
- ミドル × dry × flop × SRP × small_33: chipEV Score = 18 → call (≥14)
- バブル補正後: T_call = 20 → 18 < 20 → fold

## 21.8 バブル通過後の再調整

バブル通過 (= 賞金圏 in 後) では:

- ICM Pressure 一段下がる (バブル → FT 過渡期)
- short stack は再 jam 化 (chipEV 寄りに復帰)
- mid stack は息を吹き返す

→ MATCHA Score の補正を **+5 → +2** 程度に戻す。

## この章で覚える項目 (4 items、 すべて定性)

1. バブル = ICM Pressure 最大、 リスクプレミアム 15-25%
2. short stack jam range 大幅 tight 化 (~15%)
3. mid stack は受難、 premium only
4. MATCHA Score T_call/raise +5〜+10 補正
"""

def gen_ch21() -> str:
    return """\
# 第 29 章　マルチウェイ (3+ way) — 公式の前提崩れ ★Vol3 連携

> **本章は定性記述のみ**。 MW の詳細は Vol3 (MATCHA Exploits) ch16 で扱います。

## 23.1 公式の単独 villain 前提

MATCHA Score は **hero vs 1 villain** の構造で最適化されています。 これが 3+way
(マルチウェイ、 MW) では大きく崩れます:

- **fold equity の急減**: 全員が fold する確率は (1 − f)^n で n が増えるほど低下
- **range の overlap**: 複数 villain がそれぞれ独立 range を持つため hero の equity 低下
- **bluff range の機能不全**: bluff してもどこかで call される

## 23.2 MW での MATCHA Score の限界

MW (3+ way) で MATCHA Score をそのまま使うと:

- **bluff frequency 過剰** → EV−
- **薄い value bet** → multiple caller で勝てない
- **強気の cbet** → range 全体で −EV

→ MW では **公式値を強制下方修正** か、 そもそも別ルール (MW 5 原則) を使いましょう。

## 23.3 MW 5 原則 (Vol3 詳細)

Vol3 (MATCHA Exploits) ch16 で扱う MW 5 原則 (要点のみ):

### 原則 1: ブラフ生成禁止

3+ way では fold equity 急減 (1 − f)^n。 ブラフ range は作らないようにしましょう。

### 原則 2: バリュー集中

薄バリュー控え、 強 hand 主体 (TP+ 以上)。 アンダーペアは showdown 寄り。

### 原則 3: ハンド選好変更

SC・小ペアを優遇 (multiway で implied odds 大)、 broadway off (KQo 等) 弱体化。

### 原則 4: T_open 引き上げ (+3〜+12 程度)

プリフロップで MW を予想したら open range tight 化:

- HU 想定 T_open 22 → MW (3 way 想定) T_open 28
- 効果: そもそも MW を回避

### 原則 5: アイソレート優先

squeeze で先に 1 vs 1 に戻せれば公式 +shift 復活。 MW を避ける動き。

## 23.4 short stack 混在時の effective SPR 管理

MW で short stack 混在する場合 (例: BTN 100bb、 SB 15bb、 BB 100bb の 3way):

- vs short stack の effective SPR = 1.5 (短スタック側)
- vs BB の effective SPR = 17 (deep stack 側)

→ **villain ごとに effective SPR が異なる**。 short side に対しては jam-or-fold、
deep side に対しては slowplay と **真逆の戦略** が同時に必要。

これは MATCHA Score (HU 前提) では表現不可能。 MW では「強い手は short side jam、
deep side slowplay」 という分離行動が GTO 推奨。

## 23.5 MW での MATCHA Score 適用上の注意

緊急時に MW で MATCHA Score を使うなら:

1. **T_call を +10〜+15 引き上げ** (14 → 24〜29)
2. **bluff を一切やらない** (Score < T_raise でも raise しない)
3. **2P+以外の wet board → fold ベース**
4. **オープナー補正 (CO/HJ open river)** で形勢を 1 段階下げ

## 23.6 詳細は Vol3 へ

MW の data 駆動 strategy は **Vol3 (MATCHA Exploits) ch16** で詳述します。
本書 (Vol2) では「MW では公式が崩れる」 という事実のみ示し、 詳細は姉妹巻に
誘導。

Vol3 (MATCHA Exploits) ch16 では:
- MW 5 原則の data 裏付け
- player type (ニット / TAG / LAG / CS / マニアック) 別の MW exploit
- short stack 混在時の position 別 SPR 管理

を扱います。

## この章で覚える項目 (5 items、 すべて定性)

1. MW (3+ way) では fold equity 急減
2. MW 5 原則: bluff 禁止 / value 集中 / hand 選好変更 / T_open 引上げ / アイソレート
3. short stack 混在で villain ごとに effective SPR が異なる
4. MATCHA Score 単独 villain 前提が崩れる
5. 詳細は Vol3 ch16 で対応
"""

# ===================================================================
# 第 7 部 (ch24-26)
# ===================================================================
def gen_ch22() -> str:
    grid_table = grid_md_table()
    return f"""\
# 第 31 章　境界ハンド総覧

## 18.1 本書の暗記対象を 1 表に集約

本書を通じて出てきた **境界ハンド / 境界 board / 例外ルール** を 1 章にまとめます。
全 56 項目のうち、 暗記必須は次の通り。

## 18.2 公式の核心

```
Score = Grid[カテゴリ][board] + DV × mult[street] + 2 × oc + 4 × pot − 2 × bs

≥ {T_RAISE}: レイズ / ≥ {T_CALL}: コール / else: フォールド
```

## 18.3 12 cells Grid

{grid_table}

## 18.4 加算項の値

| 軸 | 値 |
|---|---|
| **DV** (combo / FD or OESD / gutshot or BDFD / no) | 4 / 3 / 1 / 0 |
| **street mult** (flop / turn / river) | 3 / 2 / 0 |
| **pot** (SRP / vs CR / 3BP / 4BP) | 0 / 2 / 2 / 4 (× 4) |
| **bs** (small / med75 / med100 / overbet / 185 / allin) | 0 / 1 / 2 / 3 / 4 / 5 (× −2) |
| **oc** (board 最高超え数) | 0 / 1 / 2 (× 2) |

## 18.5 例外 11 ルール

| # | 条件 | 公式 pred | 真の解 | n |
|--:|---|---|---|---:|
| 1 | TP+ × wet × flop × SRP | call | **fold** | 350 |
| 2 | 2P+ × wet × river × SRP | call | **raise** | 258 |
| 3 | ミドル × wet × turn × vs CR | call | **fold** | 179 |
| 4 | エア × wet × turn × 3BP | fold | **call** | 159 |
| 5 | 2P+ × wet × flop × SRP | call | **fold** | 125 |

→ すべて **wet** に集中。 「wet × ?」 を見たら例外候補。

## 18.6 境界ハンド ~15 個 (第 7 章より抜粋)

公式値 ± 補正で覚える境界ハンド (multi spots):

| ハンド | spot | 補正 | 備考 |
|---|---|---|---|
| A2s on A82 | TP+ × dry | -2 | TPWK |
| K9 on K72 | TP+ × dry | -1 | TPGK |
| 77 on K72 | ミドル × dry | +3 | second pair |
| A7s on AA7 | TP+ × paired | +5 | 2P 化 |
| TT on T87 | 2P+ × wet | -2 | set on wet |
| 65 on 998 | エア × paired | +3 | DV 効果 |
| 76s on 985 | エア × wet | +4 | OESD + bdfd |
| QQ on T98 | ミドル/TP+ 境界 | -3 | overpair on wet |

詳細は第 7 章参照。

## 18.7 境界 board ~10 個 (第 8 章より抜粋)

| board | 旧分類 | 修正 |
|---|---|---|
| 7-7-2 | paired | paired (MERGED、 wide attack) |
| K-K-2 | paired | paired (CONDENSED、 TP+ adv) |
| Q-J-T | wet | wet (POLAR) |
| T-9-8 | wet | wet (CONDENSED) |
| 7-5-2 | dry | dry (POLAR、 low_dry) |
| A-7-2 | dry | dry (MERGED、 A blocker) |
| Tdh 9h 4h (mono) | wet | wet (POLAR extreme) |

詳細は第 8 章参照。

## 18.8 short / deep stack 補正 (第 18-19 章より)

| stack 深度 | T_call | T_raise |
|---|---:|---:|
| 短スタック (≤ 25bb) | 12 | 40 |
| 標準 (100bb、 本書 default) | **14** | **43** |
| 深スタック (200bb+) | 16 | 45 |

ICM/MW では更に上方修正 (第 21-23 章)。

## 18.9 暗記項目の累積

| カテゴリ | 項目数 |
|---|---:|
| 公式 1 行 | 1 |
| 12 cells Grid | 12 |
| 加算項の値 (DV / mult / pot / bs / oc) | 5 |
| 例外 11 ルール | 5 |
| 境界ハンド | ~15 |
| 境界 board | ~10 |
| stack 補正 | 2 |
| ICM/MW 方針 | 2 |
| **計** | **~52 項目** |

(toc.md 当初目標 56 項目とほぼ一致)

暗記 52 項目で幅広いポストフロップ状況を網羅します。

## この章で覚える項目 (累計表示のみ、 既出のため新規 0)

(本章は復習章のため、 新規暗記項目なし)
"""

def gen_ch23() -> str:
    drills = [
        # part 1 (公式)
        dict(part='公式', q='board: Kh 7c 2d (dry)、 hand: AhTh、 street: flop、 pot: SRP、 bs: med_100p (oc=1)。 Score と判定は?',
             calc='カテゴリ=エア、 Grid[エア][dry]=3、 DV=0、 oc=1 → 2、 pot=0、 bs=2 → −4。 Score = 3 + 0 + 2 + 0 − 4 = **1**',
             ans='**fold** (1 < 14)'),
        dict(part='公式', q='board: Th 9h 4c (wet)、 hand: TsTd (set)、 street: flop、 pot: SRP、 bs: small_33。 Score と判定は?',
             calc='カテゴリ=2P+、 Grid[2P+][wet]=23、 DV=0、 oc=0、 pot=0、 bs=0。 Score = 23',
             ans='**call** (14 ≤ 23 < 43)'),
        # part 2 (境界・例外)
        dict(part='境界', q='アンダーペア × paired × flop × SRP × small_33 (oc=0、 DV=0)。 Score と判定は?',
             calc='Grid[ミドル][paired]=40、 他項 0。 Score = **40**',
             ans='**call** (14 ≤ 40 < 43)。 paired board の最強 cell'),
        dict(part='例外', q='hero: AQs on Ts9s8c-2c (turn)、 pot: 3BP、 bs: med_75。 公式と例外で判定が変わるか?',
             calc='カテゴリ=エア、 Grid[エア][wet]=1、 DV=0 (no draw)、 oc=2 → 4、 pot=2 → 8、 bs=1 → −2。 Score = 1 + 0 + 4 + 8 − 2 = **11** → fold',
             ans='**call** (例外 4: エア × wet × turn × 3BP → call で override)'),
        # part 3 (4 軸)
        dict(part='4 軸', q='SPR=1.3 (4BP)、 hand: 77 on K-7-2 (set)、 board=dry。 実 GTO bet 頻度は?',
             calc='第 12 章および第 13 章: SPR=1.3 で set の bet 頻度 = **4%** (slowplay)。',
             ans='**slowplay (check)**。 Score 公式上は Grid 25 + 16 = 41 で call も整合'),
        dict(part='4 軸', q='hero: J9 on K-Q-T (paired board ではなく wet) で gutshot 持ち。 DV と Score は?',
             calc='K-Q-T は span 3 (K=13, T=10、 13−10=3) ≤ 4 → wet。 hand J9 (no pair) + gutshot (J9 → JT9 完成可)。 カテゴリ=エア、 DV=1 (gutshot)。 Grid[エア][wet]=1、 + DV×3=3、 + oc 0、 pot 0、 bs (vs small_33) 0。 Score = 1 + 3 = **4**',
             ans='**fold** (4 < 14)。 gutshot だけで eq 不足'),
        # part 4 (pot)
        dict(part='pot', q='4BP × dry × flop × hero K9s on K-7-2 (TPGK)、 bs: med_100p (oc=0)。 Score と判定は?',
             calc='カテゴリ=TP+、 Grid[TP+][dry]=38、 + 4×4=16、 − 2×2=−4。 Score = 38 + 16 − 4 = **50**',
             ans='**raise** (50 ≥ 43)'),
        dict(part='pot', q='vs CR × wet × turn × hero 99 on Q-J-T-2 (ミドル)、 bs: med_75 (oc=0)。 Score と判定は?',
             calc='カテゴリ=ミドル、 Grid[ミドル][wet]=10、 + 4×2=8、 − 2×1=−2。 Score = 10 + 8 − 2 = **16** → call',
             ans='**fold** (例外 3: ミドル × wet × turn × vs CR → fold で override)'),
        # part 5 (深度)
        dict(part='深度', q='short stack (20bb effective)、 hero 55 on K-7-2 × turn × vs CR、 bs: med_75。 committed range として判定は?',
             calc='Score: Grid[ミドル][dry]=18、 + 4×2=8、 − 2=6、 Score = 18 + 0 + 0 + 8 − 2 = **24** → call。 short stack 補正 T_call=12 で更に call 寄り',
             ans='**call** (committed range)'),
        dict(part='深度', q='deep stack (200bb)、 hero KQs on A-K-T (turn 2P 完成 board) × SRP × overbet。 Score と判定は?',
             calc='hand KQs → AKT で KQ → TP (K) + Q kicker = top_pair。 カテゴリ=TP+。 board AKT は span 4 (A=14, T=10、 14−10=4) ≤ 4 → wet。 Grid[TP+][wet]=31、 + 0 (DV) + 0 (oc、 A は board)、 + 0 (SRP)、 − 2 × 3 = −6。 Score = 31 − 6 = **25** → call。 deep stack 補正 T_call 16 でも call',
             ans='**call** (25 ≥ 14)'),
        # part 6 (ICM/MW)
        dict(part='ICM', q='バブル × short stack (12bb)、 hero AJo BTN open vs SB jam。 chipEV では call?',
             calc='chipEV では BTN AJo vs SB short jam は call wide (Score ≥ 14)。 バブル補正 T_call 14 → 22 (+8)。 AJo の Score 推定 ≈ 18 で call 閾値ぎりぎり。',
             ans='**fold** (バブル ICM 補正で T_call 22 を下回る)'),
        dict(part='MW', q='3way pot、 hero KQo on K-7-2 (TPGK)、 SRP、 vs 2 villains call。 公式値で raise?',
             calc='HU 想定 Score: Grid[TP+][dry]=38、 + 0 + 0 + 0 = 38 → call。 MW 補正 T_call +10 → 24。 38 ≥ 24 → call。 raise しない (MW 原則 1)',
             ans='**call** (薄い value、 MW では raise 禁止)'),
    ]

    out_parts = []
    for i, d in enumerate(drills, 1):
        out_parts.append(f"### 問 {i} ({d['part']})\n")
        out_parts.append(f"**問題**: {d['q']}\n")
        out_parts.append(f"**計算**: {d['calc']}\n")
        out_parts.append(f"**解答**: {d['ans']}\n")

    drills_body = '\n'.join(out_parts)

    return f"""\
# 第 32 章　ドリル抜粋 (12 問)

## 26.1 本章の位置づけ

本書全体から **代表 12 問** を抜粋しました。 各部 (公式 / 境界 / 4 軸 / pot / 深度 /
ICM・MW) から 2 問ずつ。

詳細な 200+ cards のドリルは **poker-drill アプリ** で提供します:

- <https://poker-drill.vercel.app>
- 基本 (32 例題)
- ヒント大 (60 spots、 軸判定済み + 表参照)
- 応用 (60 spots、 シナリオから軸判定)
- 境界 spot ドリル (50 spots)

本書のドリルは「公式の使い方を体感する」 ため。 反復練習はアプリで行ってください。

## 26.2 ドリル 12 問

{drills_body}

## 26.3 ドリルの解き方手順

すべての問題で以下の手順を踏みます:

1. **カテゴリ 判定** (エア / ミドル / TP+ / 2P+)
2. **board 判定** (dry / paired / wet)
3. **Grid 値を Lookup** (12 cells のどれか)
4. **加算項を計算** (DV × mult + 2 × oc + 4 × pot)
5. **減算項を引く** (− 2 × bs)
6. **Score と閾値 14 / 43 で比較**
7. **例外 11 ルールチェック** (wet × … パターン)

慣れれば 5-10 秒。 反復で身につけてください。

## この章で覚える項目 (反復ドリル、 新規 0)

(本章は実戦練習章のため、 新規暗記項目なし)
"""

def gen_ch24() -> str:
    grid_table = grid_md_table()
    return f"""\
# 第 33 章　チートシート (A4 1 枚)

> 本章は印刷推奨。 A4 1 枚に圧縮した公式 + Grid + 例外 11 ルール。
> 実戦中はこのページだけ目を通せば判断可能。

---

## MATCHA Score (ポストフロップ暗算公式)

```
Score = Grid[カテゴリ][board]
      + DV × mult[street]
      + 2 × overcards
      + 4 × pot
      − 2 × bs

if Score ≥ {T_RAISE}: レイズ
elif Score ≥ {T_CALL}: コール
else:                 フォールド
```

## 12 cells Grid (覚える数字)

{grid_table}

## 加算項の値

**DV**: combo=4 / FD or OESD=3 / gut or BDFD=1 / no=0
**mult**: flop=3 / turn=2 / river=0
**pot**: SRP=0 / vs CR=2 / 3BP=2 / 4BP=4 (係数 ×4)
**bs**: small=0 / med75=1 / med100=2 / over=3 / over185=4 / allin=5 (係数 ×−2)
**oc**: 0 / 1 / 2 (係数 ×2)

## 例外 11 ルール (すべて wet)

| # | カテゴリ × board × street × pot | 公式 → 真解 |
|--:|---|---|
| 1 | **TP+ × wet × flop × SRP** | call → **fold** |
| 2 | **2P+ × wet × river × SRP** | call → **raise** |
| 3 | **ミドル × wet × turn × vs CR** | call → **fold** |
| 4 | **エア × wet × turn × 3BP** | fold → **call** |
| 5 | **2P+ × wet × flop × SRP** | call → **fold** |

## 短スタック / 深スタック補正

| stack | T_call | T_raise |
|---|---:|---:|
| ≤ 25bb | 12 | 40 |
| 100bb (本書 default) | **14** | **43** |
| 200bb+ | 16 | 45 |

ICM/MW: 上記 + 5〜+10 上方修正 (定性)

## 暗算手順 (5-10 秒)

1. カテゴリ 判定 (4 段階)
2. board 判定 (3 タイプ)
3. Grid 12 から数字 1 つ拾う
4. + DV × mult、 + 2 × oc、 + 4 × pot
5. − 2 × bs
6. 14 / 43 と比較、 wet なら例外チェック

## 性能 (audit、 n={AUDIT['n_spots']:,})

- avg loss: **{AUDIT['avg_loss']:.4f} BB**
- huge%: **{AUDIT['huge_pct']:.2f}%**
- 4BP huge: **{POT_HUGE_NEW['4BP']:.2f}%** ★

---

## (ポケット版) 表紙の裏に貼る用

```
Score = Grid[カテゴリ][board] + DV×{{3,2,0}} + 2oc + 4pot − 2bs
≥43: R / ≥14: C / <14: F

           dry  paired  wet
エア        3     5     1
ミドル     18    40    10
TP+        38    10    31
2P+  25    28    23

例外 5: wet × [TP+ flop SRP / 2P+ river SRP /
        ミドル turn vsCR / エア turn 3BP /
        2P+ flop SRP]
```

## この章で覚える項目

(本章はリファレンス章、 新規暗記項目なし)
"""

# ===================================================================
# 付録 A-D
# ===================================================================
def gen_appendix_a() -> str:
    grid_table = grid_md_table()
    return f"""\
# 付録 A. MATCHA Score 公式 + Grid 早見

## A.1 公式 1 行

```
Score = Grid[カテゴリ][board] + DV × mult[street] + 2 × oc + 4 × pot − 2 × bs

≥ {T_RAISE}: raise / ≥ {T_CALL}: call / else: fold
```

## A.2 Grid 12 cells

{grid_table}

## A.3 各軸の値早見

### カテゴリ (4 段階)

| index | 名前 | 含むハンド |
|---:|---|---|
| 0 | エア | no_made / king_high / ace_high |
| 1 | アンダーペア | 2nd / 3rd / under / low pair |
| 2 | TP+ | top_pair / overpair |
| 3 | 2P+ | 2P / set / trips / straight / flush / FH / quads / SF |

### board (3 タイプ)

| 名前 | 条件 |
|---|---|
| paired | 同 rank 2+ |
| wet | span ≤ 4 (connected) または mono |
| dry | 上記以外 |

### DV (Draw Value)

| dv_cat | 値 |
|---|---:|
| combo_draw | 4 |
| flush_draw / nut_flush_draw / oesd | 3 |
| gutshot / twocards_bdfd | 1 |
| onecard_bdfd / no_draw | 0 |

### street mult

| street | mult |
|---|---:|
| flop | 3 |
| turn | 2 |
| river | 0 |

### pot (係数 4)

| pot | 値 | 補正 |
|---|---:|---:|
| SRP | 0 | 0 |
| vs CR | 2 | +8 |
| 3BP | 2 | +8 |
| 4BP | 4 | +16 |

### bs (係数 −2)

| name | 値 | 補正 |
|---|---:|---:|
| small_33 | 0 | 0 |
| med_75p | 1 | −2 |
| med_100p | 2 | −4 |
| overbet | 3 | −6 |
| overbet_185 | 4 | −8 |
| allin | 5 | −10 |

### overcards (係数 2)

| oc | 補正 |
|---:|---:|
| 0 | 0 |
| 1 | +2 |
| 2 | +4 |

## A.4 例外 11 ルール

| # | カテゴリ | board | street | pot | 公式 pred → 真の解 |
|--:|---|---|---|---|---|
| 1 | TP+ | wet | flop | SRP | call → **fold** |
| 2 | 2P+ | wet | river | SRP | call → **raise** |
| 3 | ミドル | wet | turn | vs CR | call → **fold** |
| 4 | エア | wet | turn | 3BP | fold → **call** |
| 5 | 2P+ | wet | flop | SRP | call → **fold** |

## A.5 stack 補正

| stack | T_call | T_raise |
|---|---:|---:|
| ≤ 25bb | 12 | 40 |
| 100bb | **14** | **43** |
| 200bb+ | 16 | 45 |
| バブル (ICM) | +5〜+10 (定性) | 同 |
| MW (3+ way) | +10〜+15 (定性) | 同 |
"""

def gen_appendix_b() -> str:
    return """\
# 付録 B. 旧来理論との橋渡し早見表 ★暗記補助

> 本付録は **第 13 章 (旧来のポーカー理論との橋渡し)** を 1 ページに凝縮した
> 早見表です。 既知の理論にアンカーすることで MATCHA Score の各要素を「再構成」
> として吸収できます。 詳細は第 13 章 を参照。

## B.1 DV と Rule of 4/2 早見

| draw | outs | DV 値 | flop (×3) | turn (×2) | river (×0) |
|---|---:|---:|---:|---:|---:|
| combo (FD + SD) | 12-15 | **4** | +12 | +8 | 0 |
| FD / OESD | 8-9 | **3** | +9 | +6 | 0 |
| gutshot / BDFD (2 枚) | 4 / 2 | **1** | +3 | +2 | 0 |
| no draw | 0-1 | 0 | 0 | 0 | 0 |

**Rule of 4/2**: outs × 4% (flop) / outs × 2% (turn)。 OESD (8 outs) flop で
32% 完成 ≈ DV 3 × 3 = 9 points。

## B.2 古典ボード 7 → MATCHA 3 分類

| 古典分類 | 例 | MATCHA |
|---|---|---|
| Dry rainbow / Dry connected (低 gap) | K-7-2 / 7-5-2 | **dry** |
| Wet / Monotone / Two-tone (connected) | T-9-8 / 9h7h3h | **wet** |
| Paired high / Paired low | K-K-7 / 7-7-2 | **paired** |

**判定**: paired → wet → dry の順。

## B.3 旧 6 階層 Hand Strength → MATCHA 4 カテゴリ

| 旧 6 階層 | MATCHA 4 カテゴリ | 根拠 |
|---|---|---|
| ナッツメイド (FH / quads / SF) | **2P+** | 4BP で 2P 以上同挙動 |
| ストロング (set / flush / straight) | **2P+** | dry で value bet 同一 |
| ツーペア | **2P+** | paired で slowplay 同様 |
| トップペア以上 (TP / overpair) | **トップペア以上 (TP+)** | 維持 |
| アンダーペア (2nd / 3rd / underpair) | **アンダーペア** | 維持 |
| エア (high / king / ace high) | **エア** | 維持 |

**4BP huge%**: 旧 3.37% → 新 0.53% (**−85%**)、 「2P+」 統合が立役者。

## B.4 SPR 切り分け (古典 vs MATCHA)

| 古典 (Flynn 2007) | MATCHA 4 段階 | 範囲 | 典型 |
|---|---|---|---|
| Low SPR (< 1) | **オールインSPR** | < 1 | 4BP、 short push |
| Mid SPR (1-3) | **ローSPR** | 1-3 | 3BP、 短スタック |
| High SPR (3-7) | **ミディアムSPR** | 3-7 | SRP turn 後 |
| Very high SPR (> 7) | **ディープSPR** | > 7 | Cash 100bb flop、 200bb |

**SPR=3 反転点**: 同 K72 × SPR variation で set 4% → 96% (+92pp)。

## B.5 Pot Odds と Score 閾値

| bs key | pot 比 | pot odds (必要 eq) | MDF |
|---|---|---:|---:|
| small_33 | 33% | **25%** | 60% |
| med_75p | 75% | 30% | 67% |
| med_100p | 100% | **33%** | 67% |
| overbet | 125-150% | 35-38% | 67-75% |
| overbet_185 | 185% | 41% | 73% |
| allin | varies | 33-50% | 67-100% |

**Score 閾値の意味**:
- Score 14 (call) = 必要 eq 25-33% (small-med bet で defend)
- Score 43 (raise) = 必要 eq 50%+、 value range 確定

## B.6 Range Morphology 用語対応

| 古典 (Janda / Sweeney) | MATCHA レンジ分布 | 例 board |
|---|---|---|
| polarized | **2 極化型** | dry board の cbet range |
| linear (merged) | **混在型** | wet board、 中位 hand 多 |
| capped | **密集型** | wet board の call back range |

MATCHA は morphology を board × カテゴリ × Grid 値に **吸収**。

## B.7 Sklansky Hand Groups → カテゴリ

| Sklansky 群 | preflop 例 | postflop カテゴリ (hit 時) |
|---|---|---|
| 群 1-2 (AA / KK / AKs) | premium | **2P+** |
| 群 3-4 (JJ / TT / AQs / KQs) | strong | **トップペア以上** |
| 群 5-7 (mid SC / mid suited) | playable | **アンダーペア** |
| 群 8 以下 (rag) | weak | **エア** |

**Theory of Poker (Sklansky 1987)**: Score 公式が「相手のカードを見ながらプレイ」
と「知らずにプレイ」 の EV ギャップを **整数近似で最小化** (avg loss 0.3587 BB)。

## B.8 bs 6 段階と古典 sizing

| MATCHA bs key | 古典 sizing | 意味 | Score 補正 |
|---|---|---|---:|
| small_33 | range cbet (33%、 protection) | range adv 利用 | 0 |
| med_75p | medium polar (75%) | value heavy + bluff | −2 |
| med_100p | polar (100%、 nut adv) | range adv + nut adv | −4 |
| overbet | super polar (125-150%) | 相手 capped、 polar | −6 |
| overbet_185 | very super polar (185%) | over-bluff 含む | −8 |
| allin | commit (all-in) | jam-or-fold | −10 |

## B.9 1 ページ早見の使い方

1. **draw 判定** → E.1 で DV × mult を計算
2. **board 判定** → E.2 で 3 タイプに集約 (dry/paired/wet)
3. **hand 判定** → E.3 で 4 カテゴリ に集約 (エア/ミドル/TP+/2P+)
4. **SPR 確認** → E.4 で 4 段階、 SPR=3 反転点に注意
5. **bs/pot 確認** → E.5 で必要 eq、 E.8 で sizing 解釈
6. **Score 計算** → Grid + DV×mult + 2×oc + 4×pot − 2×bs
7. **閾値比較** → ≥14 call / ≥43 raise / 14 = 25% eq

本付録 + 付録 A (公式 + Grid 早見) +  で実戦運用に必要な
全リファレンスが揃います。

## B.10 詳細は第 13 章へ

各対応の **data 駆動根拠** (audit 結果、 比較表) は第 13 章で詳述します:

- 13.1 Outs と Rule of 4/2
- 13.2 古典ボード 7 → MATCHA 3 集約マトリックス
- 13.3 旧 6 階層 → MATCHA 4 カテゴリ (4BP huge -85% の根拠)
- 13.4 SPR 理論 (Flynn) と SPR=3 反転点
- 13.5 Pot Odds と MDF (公式閾値の意味づけ)
- 13.6 Range Morphology (Janda / Sweeney)
- 13.7 Sklansky Hand Groups (1976)
- 13.8 Theory of Poker (Sklansky 1987)
- 13.9 Bet Sizing 理論 (modern GTO)
"""


# ===================================================================
# 新章 19: Cash vs MTT chipEV パラメータ差
# ===================================================================
def gen_ch19_cash_vs_mtt() -> str:
    return """\
# 第 26 章　Cash vs MTT chipEV のパラメータ差

> 本書 MATCHA Score は **Cash 100bb と MTT chipEV (25/50/100/200bb)** で同一公式
> として最適化されています。 ただし両者には **構造的パラメータ差** があり、
> 同じ Score 値でも「実 EV 解釈」 が微妙に異なります。 本章ではその差分を 8 つの
> 観点で整理し、 暗算公式の運用上の注意点を 1 ページの早見表にまとめます。

## 20.1 本章の位置づけ

MATCHA Score 公式そのもの (Grid + DV + oc + pot − bs) は Cash と MTT chipEV で
**同形** です。 154,216 spots の audit でも両者統合で huge 1.49% を達成しました。

しかし「同じ Score 値が実 EV でも同じ意味か」 を厳密に問うと、 以下 7 つの
パラメータが両者で異なります。

| パラメータ | Cash 100bb | MTT chipEV |
|---|---|---|
| ante | なし | 10-12.5% of BB (typical) |
| BB ante | なし | 1bb (pre-pot) |
| rake | あり (2.5-5%、 cap あり) | なし (chip 計算のみ) |
| open-raise sizing | 2.5bb 標準 | 2.0-2.25bb (ante 影響) |
| 3-bet sizing | 9-11bb | 6-8bb (effective SPR 維持) |
| 4-bet sizing | 21-26bb | 16-20bb |
| pot 初期サイズ | 5.5bb (SRP) | 6.5-7.5bb (ante 込み) |

これら 7 つの差が **bs (bet size) 解釈・SPR 計算・range 構造** を介して
MATCHA Score の運用に影響します。

## 20.2 ante の影響 — pot サイズと bs 解釈

### ante 込み pot

MTT で **ante 12.5% of BB** (例: 100bb の MTT で 12.5% ante = 0.125bb × 9 players
= 1.125bb)、 BB 1bb、 SB 0.5bb が pre-pot。 100bb effective、 BTN open 2.25bb、
BB call の SRP 初期 pot:

- Cash 100bb: SB 0.5 + BB 1.0 + BTN 2.5 + BB 1.5 = **5.5bb**
- MTT 100bb (ante 12.5%): ante 1.125 + SB 0.5 + BB 1.0 + BTN 2.25 + BB 1.25
  = **6.125bb** (+11%)

ante が大きい late MTT (20-25% of BB) では更に +20-25%、 最大 **+25-50%** の
pot 増加。

### bs 解釈の調整

「33% bet」 は **pot に対する比率** ですが、 ante 込み pot では実 ante 含めて
**eq 必要量** が増えます。

| spot | bet サイズ | hero 必要 eq (pot odds) |
|---|---|---:|
| Cash SRP、 33% cbet (pot 5.5、 bet 1.8) | 1.8bb call | **25%** (pot odds 25.0%) |
| MTT 25bb、 33% cbet (pot 6.1、 bet 2.0) | 2.0bb call | **25%** (同じ) |

pot odds 自体は同一 (33% bet → 25% eq) ですが、 **実効 SPR が違う** ため
turn 以降の implied odds が変わります。

→ MATCHA Score 上は **bs は同じ key (small_33 = 0)** で扱う。 ただし MTT では
ante 込みで「実効 pot」 が大きく、 bs の bbeq 解釈が +10-20% 厚い。

## 20.3 BB ante の影響 — BB defense 広げ / SB squeeze 絞り

late MTT の **BB ante** ルール (= 1bb pre-pot から BB が拠出): pot に 1bb
追加される構造で、 以下の戦略変化:

### BB defense range wider

BB が pre-pot に拠出済 → 「降りるとロス」 のマージン拡大 → **BB の defense
レンジ wider 化**:

- Cash 100bb (no ante): BB vs BTN 2.5bb open call range 約 38%
- MTT 100bb (BB ante): BB vs BTN 2.0bb open call range 約 **45%** (+7pp)
- Cash 100bb での BB defense は MATCHA Score 上 t_call=14 でも、 MTT では
  実質 t_call=12 程度 (wider)

### SB squeeze tighter

逆に SB は steal 失敗の損が増える (steal 試行で BB が wider defend) → SB squeeze
range tighter:

- Cash: SB 3-bet vs BTN open 約 12%
- MTT BB ante: SB 3-bet vs BTN open 約 **8%** (-4pp)

→ MATCHA Score 上は SRP/3BP の pot 値は同じですが、 **MTT BB ante 時は SB 寄り
3BP の頻度が下がる**。

## 20.4 rake の有無 — Cash thin value 効率↓

Cash では rake (typically 2.5-5%、 cap $3-5) が pot から引かれます。 これが
**thin value spots** に重く効く:

### thin value threshold

「flat call の EV ≈ 0.05 BB」 の thin spot で:

- Cash: rake 0.03 BB → 実 EV = 0.02 BB (微 +EV)
- MTT chipEV: 0.05 BB (純 chip 計算)

→ Cash では「微 +EV の薄いコール」 は rake で潰される可能性大。 MATCHA Score
上では t_call=14 を **t_call=15-16 程度に上げる** のが Cash 厳密運用の指針。

### check 寄りの判断

「thin value vs check」 が微妙な spot:

- river × dry × トップペア以上 × 弱いキッカー (TPWK) で薄 value bet:
  - Cash: rake 込みで EV 0 付近 → check が正解
  - MTT: 純 chip で微 +EV → 薄 bet

MATCHA Score 上は Grid + 補正で 38 → 36 程度に微減 (= 「raise しない、 call
止まり」 になりがち) で対応。

## 20.5 open-raise sizing 差 — SPR 計算への影響

- **Cash 100bb**: BTN open 2.5bb 標準
- **MTT 100bb** (ante 12.5%): BTN open 2.25bb 標準
- **MTT 25bb** (ante 12.5%): BTN open 2.0bb (min-raise 寄り)

flop での effective SPR:

| spot | open | SRP pot | flop SPR (BB call) |
|---|---:|---:|---:|
| Cash 100bb | 2.5bb | 5.5 | 17.7 |
| MTT 100bb (ante) | 2.25bb | 6.0 | 16.3 |
| MTT 50bb (ante) | 2.25bb | 6.0 | 7.9 |
| MTT 25bb (ante) | 2.0bb | 5.5 | **4.2** |

SPR は MTT で若干低く、 **SPR=3 反転点 (第 12 章)** を Cash より早く跨ぐ傾向。

→ MATCHA Score 上は bs 解釈に直接影響 (MTT では同じ「33% bet」 でも実 bb が
小さい)。 short stack MTT では bs の判定を厳しく (1bb の bet も 25% over なら
med_75p 扱い)。

## 20.6 3-bet / 4-bet sizing 差 — 3BP/4BP の SPR

- Cash 3-bet IP: 9bb (3.6× of 2.5bb open)
- Cash 3-bet OOP: 11bb (4.4×)
- MTT 3-bet IP: 6-7bb (2.7-3.1× of 2.25bb)
- MTT 3-bet OOP: 8bb (3.6×)

3BP での flop SPR:

| spot | 3-bet | 3BP pot | flop SPR |
|---|---:|---:|---:|
| Cash 100bb 3BP IP | 9bb | 19.5 | 4.6 |
| MTT 100bb 3BP IP (ante) | 6.5bb | 14.5 | 6.2 |
| Cash 100bb 4BP IP | 21bb | 43 | 1.8 |
| MTT 100bb 4BP IP | 16bb | 33.5 | **2.5** |

→ Cash の方が SPR がやや低く、 4BP では Cash の方が「commitment 寄り」、
MTT の方が「post-flop play 余地あり」。 MATCHA Score の 4BP pot 値 (4) は両者
共通で audit 済 (huge −85% の劇的削減はCash + MTT100 統合 audit)。

## 20.7 MTT 早期 / 中期 / 後期 — chipEV の純度

MTT chipEV モデルが厳密に成り立つのは **early-mid stage** に限られます:

| stage | stack | chipEV ≈ \\$EV か | MATCHA Score |
|---|---|---|---|
| 早期 (Level 1-5) | 100bb+ | ほぼ純 chipEV | そのまま適用 |
| 中期 (Level 6-15) | 50-100bb | chipEV メイン、 ICM 微影響 | そのまま (補正 +0〜+1) |
| 後期 (Level 16-25) | 25-50bb | chipEV と \\$EV 乖離開始 | 補正 +1〜+3 |
| 賞金圏直前 (バブル) | 10-30bb | **乖離最大** | 第 22 章 (+5〜+10) |
| FT (3-9 left) | 多様 | 乖離大 | 第 21 章 (+3〜+8) |

→ 中期までは MATCHA Score そのまま、 後期から ICM 補正を意識。 賞金圏直前は
本書 (chipEV) の対象外、 将来 Vol2.5 で対応。

## 20.8 MATCHA Score の Cash/MTT 別解釈

### bs 値の解釈差

Cash と MTT で **bs key は同じ** (small_33 = 0、 ..., allin = 5) ですが、
ante の有無で「pot に対する比率」 と「実 bb 損失」 が乖離:

- Cash 33% bet: pot 5.5 の 33% = 1.8bb
- MTT 33% bet (ante 12.5%): pot 6.1 の 33% = 2.0bb

bs key 自体は変わらず、 実効 bb 単位の差は **±10%** 程度。

### SPR 計算の差

MTT では ante 込み pot で SPR が **数% 低下**。 SPR=3 反転点を跨ぐ判定は
慎重に (例: Cash で SPR 3.2 → MTT で SPR 2.9 になり、 set の bet 頻度が逆転)。

### Grid と pot/oc の係数

Grid 12 cells は両者で同一。 pot 値 (SRP=0 / vs CR=2 / 3BP=2 / 4BP=4) も同一。
**MATCHA Score は 154,216 spots 統合最適化** で Cash と MTT 同公式に揃えた。

## 20.9 Cash/MTT 差分 1 ページ早見表 (暗記推奨)

| 項目 | Cash 100bb | MTT chipEV |
|---|---|---|
| 公式 | MATCHA Score (同形) | MATCHA Score (同形) |
| ante | なし | 10-25% of BB |
| BB ante | なし | 1bb (late stage) |
| rake | あり (実 EV −0.03 BB) | なし |
| open sizing | 2.5bb | 2.0-2.25bb |
| 3bet sizing | 9-11bb | 6-8bb |
| 4bet sizing | 21-26bb | 16-20bb |
| SRP pot | 5.5bb | 6.0-7.5bb |
| flop SPR (SRP) | 17 | 16 (100bb) / 4 (25bb) |
| 4BP flop SPR | 1.8 | 2.5 |
| BB defense range (vs BTN open) | 38% | 45% (BB ante) |
| SB 3-bet vs BTN | 12% | 8% (BB ante) |
| t_call 微補正 | +0 (default) | +0 (default) |
| t_raise 微補正 | +0 | +0 |
| Cash thin value 補正 | t_call +1〜+2 (rake 込) | 不要 |
| ICM 補正 (後期 MTT) | 不要 | +1〜+3 (後期) |
| バブル補正 | 不要 | +5〜+10 (第 22 章) |
| 例外 11 ルール | 共通適用 | 共通適用 |

## 20.10 Cash 専用の運用 tip

- **rake 重い場 (online micro stake)**: t_call +2 (thin value 削除)
- **rakeback / VIP 還元あり**: t_call 補正不要 (実 rake はほぼ無)
- **live cash (rake high % / no cap)**: t_call +3 (薄 value 危険)
- **deep stack (Cash 200bb+)**: 第 24 章補正 (t_call +2)

## 20.11 MTT 専用の運用 tip

- **早期 (chipEV stage)**: MATCHA Score そのまま
- **中期 (50-100bb)**: そのまま (補正 +0〜+1)
- **後期 (25-50bb)**: 補正 +1〜+3 (慎重に)
- **賞金圏直前 (バブル)**: 第 22 章補正 (+5〜+10)
- **FT (3-9 left)**: 第 21 章補正 (+3〜+8)
- **PKO (バウンティ込み)**: 本書対象外 (将来 Vol2.5)

## 20.12 この章の結論

MATCHA Score は **Cash 100bb と MTT chipEV を 1 つの公式で扱える** ことを 154,216
spots audit で確認しました。 7 つのパラメータ差は **実効 bb 単位で ±10-20%** の
微差で、 公式の運用上は **bs と SPR の解釈** に注意するだけで対応可能。

例外 11 ルール (第 9 章)、 短/深スタック補正 (第 18-19 章)、 ICM 補正 (第 21-22 章)
はすべて Cash と MTT で共通適用してください。

## Cash/MTT note: 本章自体が Cash/MTT 差分章

本章は Cash/MTT 差分を扱う専用章のため、 差分は本文全体で詳述。 他章の Cash/MTT
note からは本章を参照する形にしています。

## この章で覚える項目 (4 items)

1. MATCHA Score 公式は Cash と MTT chipEV で同形
2. 主要パラメータ差: ante / BB ante / rake / open-raise sizing / 3-bet sizing / SRP pot / 4BP SPR
3. Cash 補正: rake 重時 t_call +2、 live cash +3
4. MTT 補正: 後期 +1〜+3、 バブル +5〜+10、 FT +3〜+8
"""

# ===================================================================
# 新章 23: テーブルサイズ別調整 (6/8/9-max)
# ===================================================================
def gen_ch23_table_size() -> str:
    return """\
# 第 30 章　テーブルサイズ別調整 (6/8/9-max)

> 本書 MATCHA Score は **6-max** (6人テーブル) を想定して最適化されています。
> 8-max / 9-max では range structure と multiway 頻度が変わるため、 Score 閾値
> と公式適用に微調整が必要です。 本章では 3 つのテーブルサイズの違いを整理し、
> 各サイズでの MATCHA Score 補正を表 1 つにまとめます。

## 24.1 本章の位置づけ

ポーカーのテーブルサイズは大別して 3 種類:

| サイズ | 席数 | 主流場面 |
|---|---:|---|
| 6-max | 6 | Online cash (NL50-NL500)、 short-handed MTT |
| 8-max | 8 | Online tournament (mid-stage)、 LIVE cash |
| 9-max | 9 | LIVE cash (1/2 NL)、 LIVE MTT、 home game |

本書のメイン想定は **6-max** で、 8-max/9-max では以下 7 つの観点で挙動が
異なります:

1. UTG (Under The Gun) の open range
2. range の structure (polar / merged)
3. 3-bet 頻度
4. multiway 頻度
5. 席選び効果の規模
6. average stack depth
7. pre-flop position 数

## 24.2 6-max — 本書のメイン想定

### UTG = 15-18% open

6-max の UTG は **3 席目** (= EP/MP/HJ/CO/BTN/SB/BB のうち HJ 相当) で、
position pressure が緩く wide open:

- UTG: **15-18%** RFI
- HJ: 18-22%
- CO: 25-30%
- BTN: 45-50%
- SB: 35-40% (limp 戦略次第)
- BB: defense 38-45%

### range が polar 寄り

6-max では「 hand 数が少なく強い hand に偏る」 傾向 → range が **polar 化**:

- 強い hand と bluff の二極
- merged (中位 hand 多い) は少ない
- value bet / bluff catch の二択が明瞭

### 3-bet 頻度高

6-max は 3-bet 頻度が **8-12%** と高い:

- 強いハンド (QQ+, AK) は当然
- bluff 3-bet (A5s、 76s 等) も豊富
- 4-bet pot も SRP 比 18%

### multiway 頻度低

6-max の SRP は **HU rate 75%、 3-way 20%、 4+way 5%**。 公式の「単独 villain
前提」 が大半で成立。

### MATCHA Score 適用

**そのまま無調整**。 154,216 spots audit の 80% 以上が 6-max の data。

## 24.3 8-max — 中間設定

### UTG = 13-15% open

8-max は UTG が **5 席目** (席数 + 2 = position pressure 中):

- UTG: **13-15%**
- UTG+1: 14-16%
- MP: 16-19%
- HJ: 18-21%
- CO: 24-28%
- BTN: 42-48%
- SB: 33-38%
- BB: defense 38-45%

### range が混在型

8-max は polar と merged の中間:

- 強い hand は polar 化
- 中位 hand (KJo, A9o) は merged 化
- bluff catch range が広がる

### 3-bet 頻度中

3-bet 頻度 **6-9%**。 6-max より控えめ、 9-max より積極。

### multiway 頻度中

8-max の SRP は HU rate **65%、 3-way 25%、 4+way 10%**。 公式の単独 villain
前提が 65% で成立、 残り 35% は注意。

### MATCHA Score 補正 (推奨)

- **t_call: 14 → 15〜16** (+1〜+2、 bluff catch やや厳格)
- **t_raise: 43 → 44〜45** (+1〜+2、 raise threshold やや上げ)
- 例外 11 ルールは共通適用

8-max 用に厳密に再 audit した data はないが、 MTT 中期 (8-max 主流) の audit
傾向から +1〜+2 補正が妥当と推定。

## 24.4 9-max — 最 tight 設定

### UTG = 10-12% open

9-max の UTG は **6 席目** (席数 + 3 = 最 tight):

- UTG: **10-12%** (KK+, AK のみ + 少数の suited broadway)
- UTG+1: 11-13%
- UTG+2: 13-15%
- MP: 14-17%
- LJ: 17-20%
- HJ: 20-24%
- CO: 26-30%
- BTN: 42-48%
- SB: 32-37%
- BB: defense 36-42%

### range が merged

9-max は「全員 tight、 弱い hand は事前 fold」 → range が **merged**:

- top range は集中 (QQ+, AK 等)
- middle range は全員持っている (JJ, AK, KQ 等)
- bluff range は少ない (合理 player ほど無 bluff)

### 3-bet 頻度低

3-bet 頻度 **4-7%**。 9-max では tight player 多く、 3-bet bluff が EV-。

### multiway 頻度高

9-max の SRP は HU rate **55%、 3-way 30%、 4+way 15%**。 **公式の単独 villain
前提が 45% で破綻**、 MW 5 原則の適用率 up。

### MATCHA Score 補正 (推奨)

- **t_call: 14 → 16〜17** (+2〜+3、 wide call 削減)
- **t_raise: 43 → 45〜46** (+2〜+3)
- **MW 警戒**: 3+way 頻度 45% で MW 5 原則 (第 23 章) を default 適用
- 例外 11 ルールは共通適用

9-max では「raise したら multiway になる」 確率が 6-max の 3 倍。 t_open
(プリフロップ open 閾値) も Vol1 推奨値より +3 tight 化。

## 24.5 テーブルサイズ × MATCHA Score 補正 1 表

| テーブル | UTG RFI | range | 3-bet | MW 頻度 | t_call 補正 | t_raise 補正 |
|---|---:|---|---:|---:|---:|---:|
| **6-max** | 15-18% | polar | 8-12% | 25% | **0** | **0** |
| **8-max** | 13-15% | mixed | 6-9% | 35% | +1〜+2 | +1〜+2 |
| **9-max** | 10-12% | merged | 4-7% | 45% | +2〜+3 | +2〜+3 |

簡略版 (実戦覚え用):

- **6-max**: 無調整
- **8-max**: +1
- **9-max**: +2

## 24.6 席選び効果の規模 (Vol3 ch15 連携)

席選びの重要度はテーブルサイズで増減:

| テーブル | 席選び効果 | 理由 |
|---|---|---|
| 6-max | 中 | 全員と頻繁に対戦、 hero 左右の影響限定 |
| 8-max | 高 | 左右 2 人 + 対面 5 人、 左の player type が hero range に大影響 |
| 9-max | **最大** | 左右 3 人の player type で hero range が 30-40% 変動 |

9-max では「hero の **左の player type**」 (CS / TAG / ニット) が hero range
構築の主要 input。 Vol3 (MATCHA Exploits) ch15 で詳述。

## 24.7 range structure 差 — polar / mixed / merged

| テーブル | range structure | 意味 |
|---|---|---|
| 6-max | **polar** | 強 hand と bluff の二極 |
| 8-max | mixed | 中位 hand も含む |
| 9-max | **merged** | tight player による中位 hand 集中 |

polar (6-max) → merged (9-max) で、 MATCHA Score の Grid 値の解釈も微差:

- polar (6-max): 「相手は強いか弱いか」 → bluff catch 効率良
- merged (9-max): 「相手は中位多」 → 薄 value 効率良 (実は 9-max は thin value
  寄りなのに、 multiway リスクで補正必要)

## 24.8 3-bet 頻度差の含意

3-bet 頻度差が hero の防御 range に影響:

| テーブル | hero open vs 3-bet 受け頻度 |
|---|---|
| 6-max | 高 (BB の 4-bet 受け 12-15%) |
| 8-max | 中 (4-bet 受け 8-10%) |
| 9-max | 低 (4-bet 受け 5-7%) |

→ 9-max では 3-bet されたら「相手は強い」 と読み、 4-bet range を tighter 化。
MATCHA Score 上は 4BP pot 値は同じですが、 4BP に持ち込まれる頻度自体が 9-max で
低い。

## 24.9 multiway 頻度の計算

「open raise vs N-1 callers」 で multiway になる確率:

| テーブル | HU | 3-way | 4+way |
|---|---:|---:|---:|
| 6-max | 75% | 20% | 5% |
| 8-max | 65% | 25% | 10% |
| 9-max | **55%** | 30% | **15%** |

9-max では「hero が open したら 4-way になる」 確率 15%、 6-max の 3 倍。 これが
9-max での 「MW 5 原則 (第 23 章) を default 適用」 の根拠。

## 24.10 テーブルサイズ × pot 種別 組合せ表

| テーブル × pot | 推奨 t_call | 推奨 t_raise | 注意点 |
|---|---:|---:|---|
| 6-max × SRP | 14 | 43 | 標準 |
| 6-max × 3BP | 14 | 43 | polar、 公式そのまま |
| 6-max × 4BP | 14 | 43 | huge −85% 適用域 |
| 8-max × SRP | 15 | 44 | mixed range 注意 |
| 8-max × 3BP | 15 | 44 | 公式 +1 |
| 8-max × 4BP | 15 | 44 | 公式 +1 |
| 9-max × SRP | 16 | 45 | MW 警戒 |
| 9-max × 3BP | 16 | 45 | 公式 +2、 MW |
| 9-max × 4BP | 16 | 45 | tight、 MW |
| 6-max × vs CR | 14 | 43 | 例外 3 適用 |
| 9-max × vs CR | 16 | 45 | 例外 3 + tight |

実戦では「テーブルサイズ補正 + pot 種別」 を併用。

## 24.11 spin & go (3-max) の補足

3-max (例: spin & go) は special:

- UTG (= BTN) = 80% 以上の wide open
- range は merged + polar 二極
- MW 頻度低 (=2 way 全部)
- ante なし or 軽い
- MATCHA Score 推奨補正: **t_call: 14 → 12** (wide call)、 **t_raise: 43 → 40**

ただし spin & go は本書のスコープ外、 概略のみ。

## 24.12 暗記項目: テーブルサイズ × 補正一覧

```
6-max: 補正 0 (本書 default)
8-max: t_call +1〜+2 / t_raise +1〜+2 / MW 注意
9-max: t_call +2〜+3 / t_raise +2〜+3 / MW 5 原則 default
3-max: t_call −2 / t_raise −3 (参考、 spin & go)
```

実戦中は **「6=0、 8=+1、 9=+2」** だけ覚えれば十分です。

## Cash/MTT note

- **Cash**: 6-max が主流 (online NL50-NL500)、 9-max は LIVE cash 主流
  - Cash 6-max: 本書公式そのまま
  - Cash 9-max LIVE: t_call +2 + LIVE 特有の弱 villain 補正 (Vol3 連携)
- **MTT**: 9-max が default (early stage)、 6-max は FT 突入後 (late stage)
  - MTT 9-max early: t_call +2 + ante 補正 (本章と第 20 章併用)
  - MTT 6-max FT: 本書公式そのまま (ICM 補正は別途、 第 21 章)

→ 「9-max + LIVE Cash」 と「9-max + early MTT」 が最も補正の重い場面。

## この章で覚える項目 (4 items)

1. テーブルサイズ補正: 6-max=0 / 8-max=+1 / 9-max=+2
2. 9-max は MW 5 原則を default 適用 (MW 頻度 45%)
3. range structure: 6-max polar / 8-max mixed / 9-max merged
4. 席選び効果: 9-max で最大 (Vol3 ch15 連携)
"""

# ===================================================================
# Cash/MTT note 自動付加 helper
# ===================================================================
CASH_MTT_NOTES = {
    '00': '本書 MATCHA Score は **Cash 100bb と MTT chipEV (25/50/100/200bb)** で同形。 ante / rake / sizing の差はあるが Score 公式は共通。 詳細は第 20 章で 1 ページ早見表。',
    '01': '公式そのものは Cash/MTT 共通。 ただし bs (bet size) は ante 込み pot で実 bb 単位が ±10% ずれ、 SPR は MTT で若干低い。 Cash で rake 重時 t_call +1〜+2 推奨。 詳細は第 20 章。',
    '02': 'カテゴリ 4 段階 (エア / アンダーペア / トップペア以上 / 2P+) は Cash と MTT で同一定義。 GTO 上の頻度差なし。 mv_cat → 4 階層対応も共通。',
    '03': 'board 3 タイプ (dry / paired / wet) の判定は Cash/MTT 共通です。 ただし late MTT (ante 大) では BB defense wider で「相手が wet board に call で残る range」 が +5-10% 広く、 board 解釈の hero edge がやや低下します。',
    '04': 'DV 値と street mult は Cash/MTT 共通。 ただし MTT short stack では river まで届く確率が低く、 DV ×3 (flop) の implied 価値が「実 EV」 として強く効く (commit 寄り)。 deep Cash 200bb と逆の動き。',
    '05': 'pot/bs/oc の係数は Cash/MTT 共通。 ただし **pot 値の解釈**: MTT は ante 込みで実 pot が +10-25% 大、 bs の bbeq 解釈もそれに応じて厚い。 4BP の huge −85% は Cash + MTT100 統合 audit の成果。',
    '06': '12 cells grid は Cash と MTT chipEV で共通最適化されています。 154,216 spots の audit で huge 1.49%。 ante / sizing 差は Score 値に内包 (bs/pot 軸が吸収)。 grid 値自体は両者で同じ整数を使います。',
    '07': '境界ハンドは Cash/MTT 共通。 ただし MTT short stack (25bb) では TPWK でも committed range で fold 不可、 境界 hand の挙動が「常に call 寄り」 に偏る。 deep Cash では境界 hand を厳密に。',
    '08': '境界 board は Cash/MTT 共通。 paired board の wide attack は MTT で更に強く (ante でレンジ wider)。 low_dry は Cash で出やすく、 MTT 後期では dynamic_2tone (wet 系) が増える。',
    '09': '例外 11 ルールは Cash と MTT で共通適用。 すべて wet 集中、 ante/rake の影響はほぼなし (huge spots は board structure 駆動)。 short stack MTT では例外 1, 3 を無効化 (committed) — 第 23 章。',
    '10': 'Range Morphology の 3 タイプは Cash/MTT 共通。 ただし 9-max (LIVE Cash / MTT early) は merged 寄り、 6-max (online Cash / MTT FT) は polar 寄り。 詳細は第 24 章。',
    '11': 'Hand Strength の 6→4 集約は Cash/MTT 共通。 「2P+」 統合の huge −85% は Cash 4BP + MTT100 4BP 並列 audit の成果 (詳細は付録 C)。',
    '12': 'Bet Sizing 2 段階 (small 33% / over 100%) は Cash/MTT 共通です。 SPR 4 段階の境界も共通ですが、 MTT は ante 込みで SPR が数% 低く、 SPR=3 反転点を Cash より早く跨ぎます (詳細は第 20 章)。',
    # 新 ch13 (旧理論橋渡し) は内蔵 Cash/MTT note を持つため除外
    '14': 'SRP は Cash/MTT 共通公式。 ただし pot 初期サイズ: Cash 5.5bb / MTT 6.0-7.5bb (ante 影響)。 flop SPR: Cash 100bb=17 / MTT 100bb=16 / MTT 25bb=4.2。 詳細は第 20 章。',
    '15': '3BP は Cash/MTT 共通。 3-bet sizing 差 (Cash 9-11bb / MTT 6-8bb) で 3BP SPR が異なる (Cash IP 4.6 / MTT IP 6.2)。 pot 値は両者で 2 共通。',
    '16': '4BP は **Cash と MTT100bb が質的同構造** (Probe Priority Findings)。 huge −85% は両者統合 audit の成果。 4BP SPR: Cash 1.8 / MTT 2.5 で MTT の方が post-flop 余地ややあり。',
    '17': 'vs CR の真逆現象 (turn donk vs turn CR で BTN defense 真逆) は Cash と MTT で共通。 例外 3 (ミドル × wet × turn × vs CR → fold) も両者適用。',
    '18': 'short stack は **MTT 主体の概念** (Cash 25bb は cap game でのみ)。 本章の補正値 (t_call 12 / t_raise 40) は MTT 25-50bb stage に最適化。 Cash の short stack は committed range の概念は同じだが頻度低。',
    '19': 'deep stack は **Cash 主体の概念** (Cash 200bb+)、 MTT 200bb は早期のみ。 本章の補正 (t_call 16 / t_raise 45) は両者共通。 Cash deep では rake 込みで t_call 更に +1-2 推奨。',
    # 新 ch20 (Cash vs MTT) は内蔵 Cash/MTT note を持つため除外
    '21': 'ICM は **MTT 専用概念** (Cash は chipEV 等価)。 本章補正 (+5〜+10) は MTT 後期/バブル/FT 専用。 Cash には ICM 補正一切不要。',
    '22': 'バブルは MTT 専用です。 Cash には存在しません。 本章補正は MTT 賞金圏直前のみ適用してください。 ante 込みの MTT late stage と組合せて運用します (第 20 章併用)。',
    '23': 'MW (3+ way) 頻度は Cash と MTT で **テーブルサイズに依存** (詳細は第 29 章): 6-max=25% / 8-max=35% / 9-max=45%。 MW 5 原則は両者共通適用。 Cash 9-max LIVE と MTT 9-max early が最頻発場面。',
    # 新 ch24 (テーブルサイズ) は内蔵 Cash/MTT note を持つため除外
    '25': '境界総覧の暗記項目は Cash/MTT 共通。 短/深スタック補正 (第 18-19 章) と ICM/MW 補正 (第 21-23 章) の Cash/MTT 別運用は第 20, 24 章を参照。',
    '26': 'ドリル 12 問のうち、 ICM (#11)、 MW (#12) は MTT 専用。 残り 10 問は Cash/MTT 共通シナリオ。 poker-drill アプリでは Cash/MTT 別 deck も用意。',
    '27': 'チートシートは Cash/MTT 共通。 補正は 1 行: **「MTT 後期 +1-3 / バブル +5-10 / 9-max +2 / Cash rake 重 +1-2」**。 詳細は第 20 章 (Cash/MTT) と第 24 章 (テーブルサイズ)。',
}

def gen_ch_basic_attack() -> str:
    return """\
# 第 14 章　アタック入門 — OOP は全チェック、IP は強手のみベット

ここまでの章で MATCHA Score の公式と、12 cells grid・例外ルール・理論背景を学びました。
第 15 章からはいよいよ「ポット種別ごとの実戦」に入ります。

その前に、**攻撃判断の大原則** を 2 つだけ押さえておきましょう。
この 2 原則を知っているだけで、ポストフロップの攻撃判断は 6 割以上正解できます。

---

## 14.1 アタックとは

**アタック** = 自分が先にベットする場面の判断 (cbet・2 バレル・3 バレルを含む)。

MATCHA Score はもともと「相手のベットを受ける場面 (守備)」を最適化した公式です。
攻撃は少し別の話になります。

大原則は 2 つだけです。

---

## 14.2 大原則 1: OOP はすべてチェック

**OOP** (Out of Position) = フロップ以降、自分が先にアクションしなければならない側。

OOP でベットすると:
- **相手に情報を与えすぎる** — ベットレンジが透けやすく、相手はレイズかコールを最適に選べる
- **レイズされたときの逃げ場がない** — OOP でドンクベット → レイズ → どうする？

GTO 解析でも、OOP の cbet 率はほぼ 0% のボードが多い (フロップ donk bet は例外的に 5-20% 程度)。

**暗算原則: OOP → 全チェック**

```
自分が OOP (BB が BTN の cbet を受ける場合など)
→ まずチェック
→ 相手のベットに MATCHA Score で応じる (第 15-23 章)
```

---

## 14.3 大原則 2: IP は強手のみベット

**IP** (In Position) = 後にアクションできる側。ポジション優位があります。

IP なら「弱いハンドでもブラフを打てる」と思いがちですが、初級〜中級では逆に損をしやすいです。

**ポジション優位だけでは弱ハンドのベットは EV が出ません**。
相手がコールすると強いハンドに当たりやすく、フォールドしても得るものが少ないです。

**暗算原則: IP → 2P+ または TP+ ならベット、それ以下はチェック**

| ハンド | 攻撃判断 |
|--------|---------|
| 2P+ (ツーペア以上) | ✅ ベット |
| TP+ (トップペア以上) | ✅ ベット |
| アンダーペア / エア | ❌ チェック |

---

## 14.4 この 2 原則だけでどこまで戦えるか

| 状況 | 2 原則の答え | GTO との差 |
|------|------------|-----------|
| OOP × 弱ハンド | チェック | ほぼ一致 |
| OOP × 強ハンド | チェック (slowplay) | ほぼ一致 |
| IP × 2P+ | ベット | ほぼ一致 |
| IP × TP+ | ベット | ほぼ一致 |
| IP × アンダーペア | チェック | ほぼ一致 |
| IP × エア (ブラフ) | チェック | **差あり** — GTO はリバーで air の 74% がベット (第 20 章) |

エア × リバー × IP の「デフォルト=チェック」は **GTO より tight** ですが、
初学者がリバーブラフで大損する事故を防ぐ意味で正解に近い。

---

## 14.5 例外は第 23 章のアタックルールで学ぶ

この 2 原則を精度 LS=91% まで高めたのが、第 23 章の **アタック 8 ルール** です。

主な追加条件:
- **IP × ターン × 2nd pair × SRP** → ドロー込みでベット (T3 ルール)
- **IP × 4BP × ターン × dry** → 底ハンドでもベット (T底 ルール)
- **リバー × エア** → ブラフベット (R4 ルール)

これらは第 15-22 章でポット種別とコンテキストを学んだ後に、改めて統合します。
**今は「OOP=チェック / IP=強手のみベット」だけで十分です**。

## この章で覚える項目 (2 items)

> 1. **OOP → 全チェック**
> 2. **IP → 2P+ または TP+ ならベット、それ以下はチェック**
"""


def gen_ch_attack_rules() -> str:
    return """\
# 第 23 章　アタックルール — BET/CHECK の決定ロジック

## 22.1 アタックとは

**アタック** = 自分から最初に賭けを開始する（BET / C-BET）行動。
ディフェンス（相手のBETに対して call / raise / fold を選ぶ）とは別のシナリオです。

本章は「相手がチェックした後、または自分がファーストアクション」の局面で
**どの条件なら BET し、どの条件なら CHECK するか** を決定ロジックとして示します。

精度根拠: 6,418 hands × 16 シナリオの GTO Wizard 実測データで検証。
全体精度 **81.09%**（v9f、DT 上限 83.2% に対し −2.1pp）。
ランクベース閾値を導入した結果、旧版 v6d（76.3%）から +4.8pp 向上。

## 22.2 なぜ MATCHA Score を使わないのか

MATCHA Score（Grid + DV×mult + 2oc + 4pot − 2bs）は **ディフェンス専用** の公式です。
アタック判断に Score を使うと、ロジックが逆転するケースが生じます。

| ハンド × board | Score の示す行動 | アタックの正解 |
|---|---|---|
| TP+ × paired (SRP) | Grid=10 → fold 相当 | **BET**（ペアボードで TP+ は相対的に強い） |
| UP × paired (SRP) | Grid=40 → call 相当 | **BET**（ペアボードで UP が値上がりする） |
| 2P+ × dry (4BP) | Grid=25 → call 相当 | **CHECK**（SPR≈2 ではトラップが有効） |

Score がアタックに使えない理由: Grid 値は「相手のベットサイズに対する自ハンドの防御価値」を表しており、
「自分からベットしたときに相手が降りるかどうか」は別の問いです。

## 22.2b BET の3動機 — フロップ・ターン・リバー共通フレーム

アタック判断の全ストリートを貫く考え方です。**なぜ BET するのか** を3種類に分けると、
複雑に見えるルールが「理由から導ける」ようになります。

| 動機 | 記号 | 意味 | 代表ハンド |
|---|---|---|---|
| **バリュー** | **V** | 相手の弱い手からコールをもらう | 2P+、TP+、second_pair（薄いV） |
| **セミブラフ** | **S** | フォールドさせる＋当たれば強い | エア + draw（gutshot/FD/OESD） |
| **ブラフ** | **B** | ショーダウン価値ゼロ → フォールドさせるしかない | no_made_hand（リバー）、4BP dry の low_pair |

**CHECK になる理由** も2種類:

| 理由 | 意味 | 代表ハンド |
|---|---|---|
| **ショーダウン守（SD守）** | 勝てる可能性があるのに BET すると損 | king_high、ace_high、low_pair（リバー） |
| **スローレイ** | 強すぎて BET すると相手が降りる | set/flush（3BP フロップ）、overpair（4BP OOP） |

> **核心**: `king_high → CHECK` / `no_made_hand → BET` の理由
> - king_high はショーダウンで勝てる可能性がある → CHECK して守る（SD守）
> - no_made_hand はショーダウンで必ず負ける（ペアなし）→ BET 以外に勝ち手がない（B）

---

## 22.2c アタック全体マップ → 8 ルール（暗算コンパクト版）

### アタック傾向マップ（ざっくり把握）

まず「大体どのハンドが BET か CHECK か」を掴みます。
◎ = BET 傾向（GTO 65%+）　△ = 境界（40〜65%）　× = CHECK 傾向（〜40%）

**フロップ**

| ハンド | SRP IP | SRP OOP | 3BP IP | 3BP OOP | 4BP |
|--------|:------:|:-------:|:------:|:-------:|:---:|
| set+ | ◎ | × | × *スロー* | × | × *スロー* |
| 2P+ | ◎ | × | ◎ | × | × *スロー* |
| TP+ | △ | × | ◎ | × | △ |
| 2nd/UP | △ | × | × | × | ◎ |
| 底ペア / no_made | △/× | × | × | × | △ |
| K/A-high | △ | × | × | × | △ |

> OOP はほぼ全部 CHECK。4BP のみ「強いハンドほど CHECK（スローレイ）、弱いハンドが BET」に逆転。

**ターン**

| ハンド | SRP IP | SRP OOP | 3BP IP | 3BP OOP | 4BP IP | 4BP OOP |
|--------|:------:|:-------:|:------:|:-------:|:------:|:-------:|
| set+ | ◎ | △ | ◎ | △ | ◎ | × *スロー* |
| 2P+ | ◎ | △ | ◎ | △ | ◎ | × *スロー* |
| TP+ | △ | × | △ | △ | ◎ | △ |
| 2nd/UP | × | × | × | × | ◎ | △ |
| 底ペア | × | × | × | × | △ | × |
| no_made | △ | × | △ | × | △ | × |
| K/A-high | △ | × | × | × | × | × |

> 4BP IP は弱いハンドまで広く BET 傾向（底ペアも △60%）。
> 4BP OOP は逆転: 2P+/set+ が CHECK（スローレイ）、弱いハンドはブラフ候補。

**リバー**

| ハンド | SRP | 3BP | 4BP IP | 4BP OOP |
|--------|:---:|:---:|:------:|:-------:|
| set+ / 2P+ | ◎ IP / △ OOP | ◎ IP / △ OOP | ◎ | △ |
| TP+ | ◎ | ◎ | ◎ | △ |
| 2nd/UP | △→◎ | ◎ | △ | ◎ |
| 底ペア | × | × | × | △ *逆転* |
| no_made | △ | △ | △ | × |
| K/A-high | **×（全場面）** | **×（全場面）** | × | × |

> K/A-high はリバーで必ず CHECK（ショーダウン価値を守る）。
> 底ペアは 4BP OOP リバーのみ逆転 BET。no_made はほぼ境界（△）だが 4BP OOP のみ CHECK。

---

### 8 ルール（暗算版）

上のマップの傾向を 8 条件に圧縮したものです。

精度: **LS=91%**（6,418 hands × 16 シナリオ実測、L100=635 BB/100）
定義: **底ハンド** = no_made_hand / low_pair / third_pair

---

### デフォルト: CHECK

以下のルールに一致しなければすべて CHECK。

---

### BET ルール（4 条件）+ BET 例外（2 条件）

| # | 条件 | アクション | 動機 |
|---|------|-----------|------|
| **R1** | **TP+ 以上（トップペア以上、2P+/set+ 含む）** | **BET** | V バリュー |
| E1★ | （R1 の例外）trips / overpair × **4BP OOP** | **CHECK** | スローレイ |
| **R2** | **2nd/UP（セカンドペア/アンダーペア）× 4BP または リバー** | **BET** | V薄バリュー |
| **R3★** | **low/3rd（ローペア/サードペア）× 4BP OOP × リバー** | **BET（逆転！）** | B 純ブラフ |
| **R4★** | **no_made_hand × リバー**（ペアなし × リバー） | **BET** | B 純ブラフ |
| E2 | （R4 の例外）no_made_hand × 4BP OOP × リバー | **CHECK** | ブラフ不成立 |

---

### ターン専用補正（3 条件）

ターンのみに適用する追加条件。4BP IP dry の「逆転」パターンを扱います。

定義: **底ハンド** = no_made_hand / low_pair / third_pair（ショーダウン価値がほぼゼロのハンド）

| # | 条件 | アクション | GTO% | 動機 |
|---|------|-----------|------|------|
| **T底★** | **底ハンド** × **4BP IP** × ターン × **dry** | **BET** | 52–68% | B 純ブラフ（逆転） |
| **T3** | 2nd/UP × **SRP IP** × ターン × **ドローあり** | **BET** | ~60% | S セミブラフ |

> **底ハンドとは**: no_made_hand（ペアなし）、low_pair（最低ペア）、third_pair（3番目ペア）の総称。
> 4BP IP dry のターンではこの3つが同じ「逆転 BET」ルールに従うため、1条件で表現できます。
> ただしリバーでは no_made と low/3rd の行動が分かれるため（後述）、底ハンドの統合は**ターンのみ**有効です。

---

### 判定の優先順位（疑似コード）

```
デフォルト = CHECK

1. E1: trips/overpair × 4BP OOP     → CHECK（最優先）
2. R1: TP+ 以上                     → BET
3. R2: 2nd/UP × (4BP or リバー)     → BET
4. T底: 底ハンド × 4BP IP ターン dry→ BET ★（逆転）
5. T3: 2nd/UP × SRP IP ターン draw  → BET
6. R3: low/3rd × 4BP OOP リバー     → BET ★（逆転）
7. E2: no_made × 4BP OOP リバー     → CHECK
8. R4: no_made × リバー             → BET ★
```

合計 **8 条件**（精度 LS=91%）

---

### なぜリバーでは底ハンドを統合できないか

リバーの 4BP OOP dry で、底ハンド内部が**逆方向**に分岐するためです：

| 底ハンドの種類 | 4BP OOP リバー GTO% | 判定 |
|---|---|---|
| **low_pair** | 57.9% | → **BET**（R3 逆転） |
| **third_pair** | 76.4% | → **BET**（R3 逆転） |
| **no_made_hand** | 33.8% | → **CHECK**（E2 例外） |

no_made のみが CHECK になる理由: 4BP OOP では相手のレンジが AA/AK 寄りに絞られており、ブラフ（no_made）が機能しません。一方 low/3rd はブラフではなく「薄いスケア」としてフォールドを誘えます。

---

### 8 ルールで何が変わるか

| ストリート | カバー範囲 |
|------------|-----------|
| **フロップ** | R1（TP+→BET）が主役。4BP は R2 で 2nd/UP も追加 |
| **ターン** | R1+R2 に加え T底（底ハンド統合・4BP IP dry 逆転）と T3（SRP IP draw） |
| **リバー** | R2+R3+R4 でほぼ完全カバー。E1/E2 で 4BP OOP 例外を処理 |

> **注意点**: 後続の 14.3〜14.9 のシナリオ別ルールを参照してください。
> 8 ルールは「9 割の局面で正解」する圧縮版です。

---

### 確実に CHECK するケース（8 ルールの前提）

8 ルールは「BET 条件に当てはまらなければ CHECK」という構造ですが、
以下のケースは **BET ルールが発火していても CHECK が正解** です。
「相手レンジが強すぎる」か「ショーダウン価値を守る」かのどちらかが理由です。

| 状況 | GTO BET% | 理由 |
|------|---------|------|
| **king_high / ace_high** — 全シナリオ | 約 27% | ショーダウン価値あり → 守る |
| **TP+ 以上 × 3BP OOP** （フロップ・ターン） | 約 46% | 相手レンジが AA/KK 寄りで BET が裏目 |
| **2nd/UP × 4BP OOP ターン** | 約 47% | 4BP OOP は IP と逆ロジック（R2 の例外） |
| **two_pair/set × 4BP OOP ターン** | 約 30% | スローレイ（E1 の適用範囲を超えた強ハンド） |
| **低ペア（low/3rd）× SRP/3BP リバー** | 約 23% | ショーダウン価値あり → 守る（4BP OOP は逆転） |

> **読み方**: 8 ルールで BET と判定されても上の表に当てはまる場合は CHECK。
> 特に 4BP OOP のターンは「強いハンドほど CHECK（スローレイ）、弱いハンドは BET（ブラフ）」と
> 覚えると逆転パターンが整理しやすい。

---

## 22.3 SRP フロップ IP — 判断ロジック

SRP（SPR ≈ 8〜12）で相手（OOP）がチェック。自分（IP）のアクション。

```
2P+?                                               → BET
TP+ かつ paired?                                   → BET
TP+ かつ dry かつ (draw あり OR Q/K/A-high)?       → BET（低 dry は CHECK）
UP かつ paired?                                    → BET（ただし A-board は CHECK）
UP かつ dry かつ gutshot?                          → BET if K/A-high のみ
エア かつ dry かつ strong draw (FD/OESD/combo)?    → BET if K/A-high
エア かつ dry かつ gutshot?                        → BET（K/A-high のみ）
エア かつ wet かつ strong draw?                    → BET if Q-high 以上
エア かつ paired かつ draw あり (gutshot 以上)?    → BET
→ CHECK
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | 最強ハンドは全ボードでバリュー確定。相手のどのコール/フォールドも EV プラス |
| ② | **V** | TP+ × dry × (draw OR Q+high) | **BET** | Q/K/A ボードは相手レンジが連動。7-5-2 等の低 dry では TP+ も CHECK |
| ③ | **V** | TP+ × paired | **BET** | ペアボードで TP+ が相手レンジを支配 |
| ④ | **V** | UP × paired（A-board 除く） | **BET** | ペアボードは相手の 7x/8x 等が減り自ペアの相対価値が上昇 |
| ⑤ | **S** | UP × dry × gutshot × K/A-high | **BET** | K/A-high dry のみ gutshot UP がセミブラフとして機能。低 dry は CHECK |
| ⑥ | **S** | エア × dry × strong draw × K/A-high | **BET** | FD/OESD/combo = セミブラフ。K/A ボードでのみ機能 |
| ⑦ | **S** | エア × wet × strong draw × Q-high+ | **BET** | Q 以上の wet ボードで strong draw がセミブラフとして機能 |
| ⑧ | **S** | エア × paired + draw | **BET** | ペアボードは相手レンジが弱まるため gutshot でもセミブラフが機能 |

> **ランク閾値の考え方**: 「ボードが K/A-high（top rank ≥ 13）か否か」で BET/CHECK が分かれる。
> 低ボード（top rank ≤ J=11）は相手レンジが連動しにくく、弱い手の攻撃効率が落ちる。
> "strong draw" = FD / OESD / combo_draw（gutshot と twocards_bdfd は対象外）

**OOP フロップ SRP**: 原則 CHECK。以下の例外のみ BET:
- TP+ × dry × no-draw × A-high のみ → BET（donk bet として A-board で機能）
- 2P+ × wet × no-draw × 6-high 以下 → BET
- 2P+ × paired × no-draw × 5-high 以下 → BET
- 2P+ × dry × no-draw × A-high のみ → BET

## 22.4 3BP フロップ IP — 判断ロジック

3-bet pot（SPR ≈ 4〜6）。相手の 3bet レンジは AK / QQ+ 寄りにコンデンスされています。

```
TP+ または 2P+? → BET（ただし TP+×wet×no-draw×J-high 以上は CHECK）
エア × paired × low (≤6-high)? → BET
エア × dry × no-draw × ≤9-high? → BET
UP × dry × gutshot × K-high 以上? → BET
→ CHECK
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | TP+ 以上（wet×no-draw 除く） | **BET** | 相手のコンデンスされたレンジに対して TP+ 以上がバリューライン |
| ② | **V** | TP+ × wet × no-draw × ≤9-high | **BET** | 低 wet ボードは TP+ でも BET（9 以下の wet）。J-high 以上 wet×no-draw は CHECK |
| ③ | **B** | エア × paired × ≤6-high | **BET** | 低ペアボードは相手レンジが弱い → エアのブラフが機能（56% BET） |
| ④ | **B** | エア × dry × no-draw × ≤9-high | **BET** | 9 以下の低 dry ボードでエアのブラフが機能（56% BET） |
| ⑤ | — | UP / エア × wet/paired×high | **CHECK** | 相手が強いレンジを持つ局面でブラフは機能しない |

> SRP との違い: SRP では「UP×dry+draw → BET」「UP×paired → BET」等の例外があったが、
> 3BP では **TP+ 以上 + 低ボード限定の例外** に絞る。精度 84.7%。

## 22.5 4BP フロップ — レンジベット戦略（SRP/3BP とは別ロジック）

4-bet pot（SPR ≈ 2）のフロップは **SRP/3BP とは根本的に別のゲーム** です。
GTO Wizard 実測データにより、4BP は **20% pot のレンジベット戦略** が最善と確認されました。

### 旧「逆転ロジック（2P+→CHECK）」は誤り

過去の仮説「4BP フロップ = 強い手はトラップ(CHECK)、弱い手はプレッシャー(BET)」は
GTO Wizard プローブデータで**否定**されました。実際の GTO は:

| | 旧仮説（誤）| GTO（正） |
|---|---|---|
| 2P+ | CHECK（トラップ） | **ほぼ BET または AI** |
| TP+ | 条件付き BET | **BET（82–100%）** |
| ベットサイズ | 大きなサイズ | **20% pot（≈11BB into 56BB）** |
| 全体 BET 頻度 | 手によって大きく変動 | **≈49% BET（レンジ分散）** |

### 4BP フロップ BET ルール

```
Ultra-dry 低ボード（4s4d2c, 7s4d2c, 8s5d3c 型）?  → AI（オールイン直行。BET 35–41%）
TP+ ?                                               → BET（IP/OOP 問わず、82–100%）
2ndペア / 3rdペア（IP）× connected?                 → BET（≈50%、レンジ分散）
→ CHECK（その他）
```

| 動機 | 条件 | アクション | GTO BET% | 理由 |
|---|---|---|---|---|
| **V** | Ultra-dry 低ボード（742/752/853 型）× any | **AI** | 35–41% AI | 20% pot は機能しません。直接 all-in が最善です |
| **V** | TP+ × all boards (IP/OOP) | **BET 20% pot** | 82–100% | SPR≈2 でバリューを即回収。slowplay の余裕なし |
| **V/B** | 2nd/3rdペア × IP × connected | **BET 20% pot** | ≈50% | range-bet でレンジ全体の EV を最大化 |

> **4BP の根本原理（レンジベット）**: SPR≈2 でベットしても相手が次のストリートで all-in になります。
> 強い手でもすぐに BET してバリューを回収する方が EV 高いです。
> 3BP での「セット/フラッシュ → CHECK（スローレイ）」は 4BP では不要です。SPR が低すぎてスローレイの旨味がありません。

> **ベットサイズ**: 20% pot（= ≈11BB into ≈56BB pot）。SRP/3BP の 33–50% pot とは全く異なる。

## 22.6 ターン IP — 判断ロジック

フロップで双方チェック後（または delayed C-BET）、ターンで相手がチェック。

### SRP ターン IP

```
2P+?                                 → BET（V バリュー）
TP+ かつ dry かつ draw あり?        → BET（V+S バリュー兼セミブラフ）
TP+ かつ draw あり?                 → BET（V+S）
エア かつ draw あり (gutshot 以上)? → BET（S セミブラフ）
→ CHECK（UP は draw あっても CHECK）
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | ターンでも最強ハンドはバリュー確定 |
| ② | **V+S** | TP+×dry + draw | **BET** | draw なし TP+ は 40% BET = CHECK 多数。draw で補完必須 |
| ③ | — | TP+×dry×no draw | **CHECK（スローレイ）** | 40.3% BET — draw なし TP+ は dry でも CHECK が GTO 多数（反直感） |
| ④ | **V+S** | TP+×wet + draw | **BET** | draw が加わった TP+ は wet でもバリュー兼セミブラフ |
| ⑤ | **S** | エア + gutshot 以上 | **BET** | gutshot エア×dry 76%、OESD/FD 85〜100% のセミブラフ値 |
| ⑥ | — | UP（draw あり） | **CHECK（SD守）** | UP のブロッカー価値 < ショーダウン価値。Draw があっても原則 CHECK |

> **重要**: TP+×dry は **draw なし = CHECK**（逆直感）。GTO はターン到達後に dry ボードの TP+ を slowplay します。
> **SRP ターン IP 精度**: 85.8%（v6d 改訂後、全シナリオ中最高クラス）

### 3BP ターン IP

```
2P+?                                              → BET
TP+ かつ dry?                                    → BET
TP+ かつ paired × no-draw × A-only?              → BET（K 以下は CHECK）
TP+ かつ gutshot?                                → BET
UP × paired × 10-high 以上?                      → BET（10 以下の低ペアは CHECK）
no_made_hand × dry × draw (gutshot/FD)?          → BET ★（55–84%）
→ CHECK（エア全て: ace_high/king_high/low_pair/third_pair は draw があっても CHECK ★）
```

| ルール | 動機 | 条件 | アクション | 理由 |
|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | 3BP でも最強ハンドは継続バリュー |
| ② | **V** | TP+×dry | **BET** | dry ターンでは TP+ が相手の 3bet レンジに対して優位（85% BET） |
| ③ | **V** | TP+×paired×A-only | **BET** | A-board ペアのみ TP+ が BET。K 以下のペアは CHECK（25% BET） |
| ④ | **V+S** | TP+×gutshot | **BET** | gutshot で強化された TP+ はセミブラフ価値が付加される |
| ⑤ | **V** | UP×paired×10+ | **BET** | J/Q/K/A-high ペアで UP に価値が出ます。9 以下の低ペアは CHECK |
| ⑥ ★ | **S** | **no_made_hand × dry × draw（gutshot/FD）** | **BET** | 純ブラフハンドのみ draw でセミブラフが機能（55–84% BET）|
| ✗ | — | エア（ace_high/king_high/low_pair/third_pair）× any | **CHECK（SD守）★** | ショーダウン価値あり → 守る。GTO: low_pair 22%、ace_high gutshot 22%。draw があっても× |

> **3BP ターン エア = 全 CHECK（no_made_hand+draw の例外のみ）**:
> 旧ルール「エア×dry×≤8-high → BET」は誤り。実測値: low_pair no_draw = 22%、ace_high gutshot = 22%。
> **no_made_hand**（ペアなし純ブラフ）だけが draw でセミブラフとして機能。King/Ace-high はブロッカー値があるが CHECK が EV 高い。

### 4BP ターン IP — ボード × ハンドカテゴリ 別ロジック

```
【dry ボード】
TP+ または two_pair 以上?                → BET（77–78%）
second_pair?                            → BET ★★（73.9%）← 重要追記
third_pair × (no_draw または gutshot)? → BET ★（64–100%）
low_pair × (no_draw または gutshot)?   → BET（51–52%）
no_made_hand × (no_draw または gutshot)? → BET ★（56–58%）
king_high × any?                        → CHECK ★（24–30%、gain=14.71 BB）
ace_high × any?                         → CHECK ★（23–50%）
エア × FD/OESD?                         → CHECK（34–38%）

【paired ボード】
TP+?                                    → BET（66%）
third_pair × no_draw?                   → BET ★（90.5%、gain=4.35 BB）
ace_high × no_draw?                     → BET ★（59.2%）
→ CHECK（no_made_hand 36.7%、second_pair 28.8% は全て CHECK）

【wet ボード】
TP+?                                    → BET（52%）
→ CHECK（エア全て: low_pair 26.8%、third_pair 28% は CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ①D | **V** | **dry**: TP+/2P | **BET** | 61–78% | SPR≈1.5 でオールイン圧力として機能 |
| ①D_b ★★ | **V薄/B** | **dry**: second_pair | **BET** | 73.9% | TP+/2P の次に位置する薄いバリュー。dry × 4BP では K/A-high コールを誘える |
| ②D ★ | **B** | **dry**: third_pair × no_draw/gutshot | **BET** | 64–100% | ショーダウン価値低 → ブラフがオールイン圧力として機能 |
| ③D ★ | **B** | **dry**: no_made_hand × no_draw/gutshot | **BET** | 56–58% | ショーダウン価値ゼロ → 純ブラフが最もプレッシャー機能 |
| ④D ★ | — | **dry**: king_high または ace_high | **CHECK（SD守）** | 24–30% | ショーダウン価値あり → 守る。BET すると相手が Kx/Ax でコール |
| ⑤D | — | **dry**: エア × FD/OESD | **CHECK（スローレイ）** | 34–38% | 強ドロー = 相手に踏み込まれると負ける → CHECK |
| ①P ★ | **B** | **paired**: third_pair × no_draw | **BET** | 90.5% | ペアボードで low_pair が「ロウ 3 枚目」→ 相手フォールド誘発 |
| ②P ★ | **B** | **paired**: ace_high × no_draw | **BET** | 59.2% | A-high はペアボードでスケア（相手のボードペアを超えた) |
| ①W | **V** | **wet**: TP+ | **BET** | 52% | wet でも TP+ はバリュー |

> **4BP ターン dry の核心**: second_pair は 73.9% BET — TP+ の次に位置する薄いバリュー（paired の 28.8% とは別物）。
> K/A-high は CHECK してショーダウンを狙う（K-high dry no_draw = 24%）。これは直感と逆だが GTO 実測済み。
> **dry × second_pair ≠ paired × second_pair**: dry では K/A-high のコールを取れるが、paired では相手のフルハウス可能性が高く BET 不可。

> 4BP ターンの位置付け: フロップ「TP+ → BET、エア→CHECK（レンジベット）」から、ターンは「low_pair/no_made_hand → BET に転換」。SPR が 2→1.5 に低下し、ブラフのプレッシャーが増す。

## 22.7 OOP ターン — 判断ロジック

双方フロップチェック後、ターンで OOP（= 自分）がファーストアクション。

### SRP ターン OOP

```
2P+ × wet × 10-high 以上? → BET（9 以下 wet は CHECK）
2P+ × dry?               → BET
2P+ × paired × ≤10-high? → BET（11 以上は CHECK）
エア × wet + draw?        → BET
エア × dry × strong × ≤11-high? → BET（12 以上 K-high は CHECK）
エア × paired × draw × ≤10-high? → BET（11 以上は CHECK）
→ CHECK
```

OOP ターン SRP の基本は **CHECK**。2P+×wet/dry（バリュー）と draw 付きエアが BET 候補。
ランク閾値: 2P+×wet は 10-high 以上のみ BET、2P+×paired は 10 以下のみ BET。

### 3BP ターン OOP

```
TP+ (top_pair, overpair, trips) × dry?       → BET（71–81%）
TP+ × paired × no-draw × ≤10-high?          → BET（11 以上は CHECK）
TP+ × wet?                                   → BET（44–69%）
no_made_hand × dry/wet × draw (gutshot/FD)?  → BET ★（59–84%）
→ CHECK（エア全て: ace_high/king_high/low_pair × any は CHECK ★）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | **TP+ × dry**（top_pair/overpair/trips） | **BET** | 64–81% | 3BP OOP はポジション不利だが TP+ は dry でバリューが勝る |
| ② | **V** | **TP+ × paired × ≤10-high** | **BET** | 65% | 高ペアボード（J/Q/K/A）は CHECK、10 以下はバリュー |
| ③ | **V** | **TP+ × wet** | **BET** | 44–69% | wet でも TP+ はバリューライン |
| ④ ★ | **S** | **no_made_hand × draw（gutshot/FD）** | **BET** | 59–84% | ショーダウン価値ゼロ × draw = セミブラフのみが機能 |
| ✗ | — | エア（ace_high/king_high/low_pair）× any | **CHECK（SD守）★** | 8–24% | ショーダウン価値あり → 守る。OOP エアは draw があっても不利 |

> **3BP OOP ターン エア = 全 CHECK**: IP 同様に、ace_high/king_high/low_pair は draw があっても CHECK が最善。
> **trips × dry → BET (71%)** を忘れずに（trips は tier_i=4、2P+ に含まれるが OOP dry で明示的に BET）。

### 4BP ターン OOP — dry で overpair/2P が逆転する

```
top_pair × dry?                      → BET（59.1%）
trips × dry?                         → BET（55.6%）
overpair × dry?                      → CHECK ★（29.8%、gain=2.33 BB）
two_pair × dry × no-draw?            → CHECK ★（24%）
set × dry?                           → CHECK（25.9%、スローレイ）
second_pair × gutshot?               → BET ★（91.8%、gain=3.45 BB）
third_pair × gutshot?                → BET ★（88.3%）
→ CHECK（other: no_made_hand 15.9%、third_pair no_draw 38%）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ①T | **V** | **top_pair × dry** | **BET** | 59.1% | OOP でも top_pair dry はバリュー優先 |
| ②T | **V** | **trips × dry** | **BET** | 55.6% | trips は OOP でも BET（GTO 実測） |
| ③T ★ | — | **overpair × dry** | **CHECK（スローレイ）** | 29.8% | 4BP OOP overpair は CHECK！相手レンジ（AK/AA+）に対して BET は危険 |
| ④T ★ | — | **two_pair × dry × no-draw** | **CHECK（スローレイ）** | 24% | SPR≈1.5 で BET→AI のリスク大 → CHECK でスタック保全 |
| ⑤T | — | **set × dry** | **CHECK（スローレイ）** | 25.9% | 強すぎて BET すると相手が降りる → CHECK でトラップ |
| ⑥T ★ | **S** | **second_pair × gutshot** | **BET** | 91.8% | ほぼ 100% BET — gutshot が付いた second_pair は最強セミブラフ |
| ⑦T ★ | **S** | **third_pair × gutshot** | **BET** | 88.3% | third_pair+gutshot も強力セミブラフ（BET でフォールドか draw 完成） |

> **4BP OOP dry ターンの核心**: "overpair が CHECK、third_pair+draw が BET"。
> 4BP で overpair を CHECK する理由: OOP × 4BP × dry の overpair は SPR≈1.5 で BET するとほぼ全ての相手のコールに負ける（相手は AK/AA+）。
> 逆に third_pair/second_pair+gutshot = ショーダウン価値がなく、フォールドエクイティのみがある → BET が最善。

## 22.8 リバー IP — 判断ロジック

フロップ・ターン双方チェック後、OOP がリバーをチェック（delayed attack 局面）。

**【リバー dry ボード共通パターン】** GTO 実測で判明したリバーの核心ルール:

| mv_cat | SRP IP | 3BP IP | 4BP IP | 理由 |
|---|---|---|---|---|
| **no_made_hand** | 61.9% → **BET** | 60.8% → **BET** | 57.6% → **BET ★** | ショーダウン価値ゼロ → ブラフのみ |
| **second_pair** | 52.7% → **BET ★** | 79.5% → **BET ★** | 54.0% → **BET ★** | thin value（弱い手のコールに勝つ） |
| **underpair** | 57.9% → **BET** | 59.0% → **BET ★** | 48.1% → 境界 | 同上 |
| **third_pair** | 25.5% → CHECK | 69.0% → **BET** | 23.2% → CHECK | 3BP のみ BET |
| **king_high** | 2.5% → **CHECK ★** | 0.4% → **CHECK ★** | 3.2% → CHECK | ショーダウン価値あり |
| **ace_high** | 22.9% → **CHECK ★** | 1.9% → **CHECK ★** | 1.4% → CHECK | ショーダウン価値あり |
| **low_pair** | 13.2% → **CHECK ★** | 10.1% → **CHECK ★** | 13.3% → CHECK | ショーダウン価値あり |

> **旧「エア×dry → 常に BET（K/A も例外なし）」は誤り**: king_high dry = 0.4-22.9%、ace_high = 1.9%。
> 旧「UP → CHECK」も誤り: second_pair = 52-79.5%、underpair = 57.9% で BET が多数。
> **no_made_hand（ペアなし純エア）はブラフ。ace/king_high はショーダウン価値を守る。**

### SRP リバー IP

```
2P+?                              → BET
TP+ × (dry または paired)?        → BET
second_pair または underpair?      → BET ★（thin value）
no_made_hand × dry/wet?           → BET ★（ブラフ）
→ CHECK（king_high/ace_high/low_pair/third_pair × dry → CHECK ★）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | 2P+ | **BET** | 91-100% | 最強ハンドはフルバリュー |
| ② | **V** | TP+ × dry/paired | **BET** | 91.4% | 3 チェック後も TP+ はバリュー |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 52.7% | 薄いバリュー — 相手の ace/king_high よりも強い |
| ④ ★ | **V薄** | **underpair × dry** | **BET** | 57.9% | 薄いバリューとして機能 |
| ⑤ ★ | **B** | **no_made_hand × dry/wet** | **BET** | 61.9% | ショーダウン価値ゼロ → ブラフが唯一の選択肢 |
| ✗ ★ | — | **king_high/ace_high/low_pair/third_pair** | **CHECK（SD守）** | 2-25% | ショーダウン価値あり → 守る。BET すると相手の強い手にコールされ損 |

### 3BP リバー IP — 最大改善（gain 上位集中）

```
TP+ 以上（top_pair, two_pair, trips, straight, flush, set, fullhouse）? → BET（96-100%）
third_pair × dry?      → BET ★（69%）
second_pair × dry?     → BET ★（79.5%、旧 CHECK は最大誤り: gain=28.53 BB/100）
underpair × dry?       → BET ★（59.0%）
no_made_hand × dry?    → BET（60.8%）
→ CHECK ★（king_high=0.4%、ace_high=1.9%、low_pair=10.1% → 全て CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | TP+ 以上 (TP+/2P+/trips/straight/flush) | **BET** | 96–100% | SPR≈3 での強バリュー |
| ② ★ | **B/V薄** | **third_pair × dry** | **BET** | 69.0% | 3BP SPR≈3 では thin value+ブラフとして機能（SRP 25.5% とは逆） |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 79.5% | 薄いバリュー（旧「UP → CHECK」は誤り：gain=28.53 BB/100） |
| ④ ★ | **V薄** | **underpair × dry** | **BET** | 59.0% | 薄いバリュー |
| ⑤ ★ | **B** | **no_made_hand × dry** | **BET** | 60.8% | ショーダウン価値ゼロ → ブラフのみ |
| ✗ ★★★ | — | **king_high × dry** | **CHECK（SD守）** | 0.4% | **0.4%** — ほぼ 100% CHECK（旧「K/A も BET」は最大の誤り）|
| ✗ ★★★ | — | **ace_high × dry** | **CHECK（SD守）** | 1.9% | ショーダウン価値あり → 守る |
| ✗ ★★★ | — | **low_pair × dry** | **CHECK（SD守）** | 10.1% | gain=79.88 BB/100 — リバー最大改善ポイント |

> **3BP IP リバー dry 核心**: "エア=CHECK、UP=BET" — 従来の TP+/UP/エアの三分類を捨てる。
> `king_high`/`ace_high`/`low_pair` → CHECK（ショーダウン価値を守る）。
> `second_pair`/`underpair`/`third_pair`/`no_made_hand` → BET（thin value or ブラフ）。

### 4BP リバー IP — no_made_hand/second_pair が解禁される

```
2P+ または TP+?         → ALLIN（SPR≈1 で全額押す）
no_made_hand × dry?    → BET ★（57.6%、gain=44.85 BB/100）
second_pair × dry?     → BET ★（54.0%）
→ CHECK（king_high/ace_high/low_pair/third_pair → CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | 2P+ / TP+ | **ALLIN** | 85-100% | SPR≈1 では全額でバリューを取る |
| ② ★ | **B** | **no_made_hand × dry** | **BET** | 57.6% | ショーダウン価値ゼロ → ブラフ：相手がフォールドするかオールインしかない |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 54.0% | 薄いバリュー（旧「エア以外は ALLIN のみ」を修正） |
| ✗ | — | king_high/ace_high/low_pair/third_pair | **CHECK（SD守）** | 1-23% | ショーダウン価値あり → 守る |

## 22.9 OOP リバー — polarization ロジック

フロップ・ターン双方チェック後、リバーで OOP がファーストアクション。

**【OOP リバー dry ボード共通パターン】**

| mv_cat | SRP OOP | 3BP OOP | 4BP OOP |
|---|---|---|---|
| **second_pair** | 67.5% → **BET ★** | 85.2% → **BET** | 73.0% → **BET** |
| **underpair** | 62.9% → **BET ★** | 65.9% → **BET** | 51.9% → BET |
| **no_made_hand** | 53.7% → **BET ★** | 50.7% → BET | 33.8% → CHECK |
| **third_pair** | 40.1% → 境界 | 75.2% → **BET** | 76.4% → **BET ★** |
| **low_pair** | 18.0% → CHECK | 17.3% → **CHECK ★★★** | 57.9% → **BET ★★★** |
| **king_high** | 48.6% → 境界 | 0.0% → **CHECK ★★★** | 4.0% → CHECK |
| **ace_high** | 20.2% → CHECK | 10.3% → **CHECK ★★★** | 34.8% → 境界 |
| **overpair** | 74.1% → BET | — | 12.5% → **CHECK ★** |
| **trips** | 45.0% → 境界 | 46.7% → 境界 | 43.4% → **CHECK ★** |

### SRP リバー OOP

```
TP+ または 2P+?                → BET
second_pair または underpair?  → BET ★（thin value）
no_made_hand × dry?            → BET ★（ブラフ）
→ CHECK（ace_high/low_pair → CHECK; king_high は境界: 48.6%）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | TP+ / 2P+ | **BET** | 64-100% | 強バリュー |
| ② ★ | **V薄** | **second_pair × dry** | **BET** | 67.5% | 薄いバリュー（旧「UP → CHECK」は誤り: gain=11.99 BB/100）|
| ③ ★ | **V薄** | **underpair × dry** | **BET** | 62.9% | 薄いバリュー |
| ④ ★ | **B** | **no_made_hand × dry** | **BET** | 53.7% | ショーダウン価値ゼロ → ブラフ（gain=6.89 BB/100）|
| ✗ | — | ace_high × dry | **CHECK（SD守）** | 20.2% | ショーダウン価値あり → 守る |
| ✗ | — | low_pair × dry | **CHECK（SD守）** | 18.0% | ショーダウン価値あり → 守る |

### 3BP リバー OOP — エア全般 CHECK（逆転）

```
TP+ (top_pair/overpair) × dry?          → BET（89%）
third_pair または second_pair?          → BET ★（75-85%）
underpair × dry?                        → BET ★（65.9%）
no_made_hand × dry?                     → BET（50.7%、ほぼ境界）
→ CHECK ★（king_high=0%、ace_high=10%、low_pair=17%、two_pair=45.6%、trips=46.7% → CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | **TP+ × dry**（top_pair/overpair） | **BET** | 74-89% | OOP でも TP+ はバリューライン |
| ② ★ | **B/V薄** | **third_pair × dry** | **BET** | 75.2% | thin value + ブラフとして機能 |
| ③ ★ | **V薄** | **second_pair × dry** | **BET** | 85.2% | 最も明確な薄いバリュー |
| ④ ★ | **V薄** | **underpair × dry** | **BET** | 65.9% | 薄いバリュー |
| ⑤ | **B** | **no_made_hand × dry** | **BET** | 50.7% | ショーダウン価値ゼロ。GTO はほぼ 50/50 だが pure air はブラフが基本方針 |
| ✗ ★★★ | — | king_high × dry | **CHECK（SD守）** | 0.0% | 完全に CHECK — ショーダウン価値あり |
| ✗ ★★★ | — | ace_high × dry | **CHECK（SD守）** | 10.3% | ショーダウン価値あり（gain=22.71 BB/100）|
| ✗ ★★★ | — | low_pair × dry | **CHECK（SD守）** | 17.3% | ショーダウン価値あり（gain=65.49 BB/100 — 最大）|
| ✗ ★ | — | two_pair × dry | **CHECK（スローレイ）** | 45.6% | OOP × dry × 3BP では two_pair も CHECK（gain=3.04）|
| ✗ | — | trips × dry | **CHECK（スローレイ）** | 46.7% | 境界（46.7%）|

> **3BP OOP dry リバー核心**: 旧「エア×dry → 全 BET」は完全に誤り。
> `king_high=0%`、`low_pair=17.3%` → CHECK ★★★（ショーダウン価値を守る）。
> `second_pair/underpair` → BET（旧「UP → CHECK」も誤り）。
> `no_made_hand` はほぼ 50/50（50.7%）— 迷ったら BET でよいが GTO 的には誤差範囲。

### 4BP リバー OOP — lower_pair が逆転 BET

```
top_pair または two_pair または straight?     → BET（55-88%）
third_pair × dry?                            → BET ★★★（76.4%、gain=37.71 BB/100）
low_pair × dry?                              → BET ★★★（57.9%、gain=24.47 BB/100）
second_pair × dry?                           → BET（73.0%）
→ CHECK（overpair=12.5% ★ / trips=43.4% / fullhouse=43.1% / king_high=4% → CHECK）
```

| ルール | 動機 | 条件 | アクション | GTO% | 理由 |
|---|---|---|---|---|---|
| ① | **V** | top_pair / two_pair / straight | **BET** | 55–88% | バリューライン |
| ② ★ | **V/B** | set / second_pair / underpair | **BET** | 52–73% | SPR≈1 でのバリュー/ブラフ |
| ③ ★★★ | **B** | **third_pair × dry** | **BET** | 76.4% | ショーダウン価値低 → ブラフが最善（gain=37.71 BB/100）|
| ④ ★★★ | **B** | **low_pair × dry** | **BET** | 57.9% | ショーダウン価値低 → ブラフ（gain=24.47 BB/100）|
| ✗ ★ | — | **overpair × dry** | **CHECK（スローレイ/SD守）** | 12.5% | SPR≈1 で相手レンジ(AA/AK)に対して守る（gain=2.66 BB/100）|
| ✗ ★ | — | **trips × dry** | **CHECK（スローレイ）** | 43.4% | trips が CHECK（逆直感）|
| ✗ | — | **king_high / no_made_hand** | **CHECK** | 4–34% | エアはほぼ CHECK |

> **4BP OOP dry リバー核心**: "lower_pair（low_pair/third_pair）が BET、overpair/trips が CHECK"。
> 旧「エア=CHECK、エア以外=BET」は誤り。low_pair(57.9%)がBET、overpair(12.5%)がCHECK。
> 理由: 4BP OOP でoverpair はSPR≈1 でオールインを押し付けられると負ける（相手=AA/AK+）。
> low_pair はショーダウン価値が低くブラフが最善。

## 22.10 BET の3動機 × ポット種別 まとめ

### V バリュー BET — 弱い手のコールをもらう

| ストリート | SRP | 3BP | 4BP |
|---|---|---|---|
| **ターン IP** | 2P+、TP+ + draw | 2P+、TP+×dry、UP×paired×10+ | TP+/2P × dry |
| **ターン OOP** | 2P+×wet/dry | TP+（trips含む）×dry | top_pair/trips × dry |
| **リバー IP** | 2P+/TP+、second_pair、underpair（薄いV） | 2P+/TP+、second_pair/underpair/third_pair（薄いV） | 2P+/TP+ → ALLIN、second_pair（薄いV） |
| **リバー OOP** | 2P+/TP+、second_pair/underpair（薄いV） | TP+、second_pair/underpair/third_pair（薄いV） | top_pair/two_pair/set/second_pair/underpair |

> **「薄いバリュー（V薄）」とは**: second_pair/underpair が ace/king_high に勝てるのでコールをもらえる。
> BET しても損しない相手（弱いエア）がいる = バリュー BET が成立。

### S セミブラフ — draw があるのでフォールドさせるか当たれば勝つ

| ストリート | SRP | 3BP | 4BP |
|---|---|---|---|
| **ターン IP** | エア + gutshot以上（76-100%） | no_made_hand × dry × draw（55-84%）| no_made_hand/third_pair × dry gutshot |
| **ターン OOP** | エア × wet + draw | no_made_hand × draw（59-84%）| second/third_pair × gutshot（88-92%）|
| **リバー** | — | — | — |

> リバーにドロー待ちは存在しない → **リバーにセミブラフはない**。
> リバーで BET する弱い手は V薄（ペアが薄いバリュー）か B（純ブラフ）のどちらか。

### B 純ブラフ — ショーダウン価値ゼロ → フォールドさせるしかない

| ストリート | SRP | 3BP | 4BP IP | 4BP OOP |
|---|---|---|---|---|
| **ターン IP** | — | — | third_pair/no_made_hand × dry | — |
| **ターン OOP** | — | — | — | third_pair+gutshot（88%）|
| **リバー IP** | no_made_hand（62%） | no_made_hand（61%） | no_made_hand（58%）| — |
| **リバー OOP** | no_made_hand（54%） | — | — | third_pair(76%)/low_pair(58%) |

> **ブラフの必要条件**: ショーダウン価値が「ほぼゼロ」= CHECK しても 0% に近い勝率。
> この条件を満たす: no_made_hand（ペアなし）、4BP OOP の low_pair/third_pair（相手レンジに負ける）。

### — CHECK — ショーダウン価値を守るか、スローレイ

| CHECK の理由 | 代表ハンド | 代表場面 |
|---|---|---|
| **ショーダウン守**: BET すると弱い手にコールされ損 | king_high、ace_high、low_pair（SRP/3BP） | 3BP リバー dry — low_pair(10%) CHECK ★★★ |
| **スローレイ**: 強すぎて BET すると降りられる | set/flush（3BP フロップ）、trips（4BP OOP） | 4BP OOP: trips(43%) CHECK |
| **中途半端**: バリューにもブラフにも機能しない | UP × dry（SRP ターン）、king/ace_high（4BP ターン dry） | SRP ターン UP: draw あっても CHECK |

**4BP ターン IP dry — 逆転パターン（重要）**:
```
薄バリュー:    second_pair → BET ★★（73.9%）← 追記
ブラフ枠:     third_pair → BET ★（64%）、no_made_hand → BET ★（57%、draw なし/gutshot のみ）
ショーダウン守: king_high/ace_high → CHECK ★（24%）
注意:         no_made_hand × FD/OESD → CHECK（強ドローでも 4BP では CHECK）
直感と逆！ 「高いカードほど CHECK、low_pair/no_made は BET、second_pair も BET」
```

**4BP OOP リバー dry — 逆転パターン（重要）**:
```
ブラフ枠:    third_pair → BET ★★★（76%）、low_pair → BET ★★★（58%）
スローレイ:  overpair → CHECK ★（12.5%）、trips → CHECK ★（43%）
直感と逆！ 「弱いペアが BET、overpair が CHECK」= SPR≈1 の圧力
```

## 22.11 SPR とロジックの関係

SPR（スタック/ポット比）がアタックロジックを支配する原理:

| SPR | 構造 | ロジック |
|---|---|---|
| ≈8〜12（SRP） | スタックが深い | UP の BET は限定的。ドロー補正が重要 |
| ≈4〜6（3BP） | 中程度 | TP+ 以上に一本化。ブラフは機能しにくい |
| ≈2（4BP フロップ） | 浅い | 強い手はトラップ、弱い手はプレッシャー（逆転） |
| ≈1.5（4BP ターン） | さらに浅い | 弱い手（UP）も BET がオールイン圧力として有効 |
| ≈1（4BP リバー） | 最浅 | 強い手は全額（ALLIN）。弱い手は CHECK |

**原則**: SPR が低いほど、ベットが相手に「フォールドかオールイン」の二択を迫る。
この圧力が有効なハンドは SPR によって変わります。

## この章で覚える項目 (17 items)

**【最優先】全ストリート統一 8 ルール**
0. **8 ルール（コンパクト版）**: 底ハンド=`no_made/low/3rd`と定義。デフォルト=CHECK。判定順: E1=`trips/overpair×4BP OOP→CHECK`→R1=`TP+→BET`→R2=`2nd/UP×(4BP/river)→BET`→T底=`底ハンド×4BP IP turn dry→BET★`→T3=`2nd/UP×SRP IP turn×draw→BET`→R3=`low/3rd×4BP OOP river→BET★`→E2=`no_made×4BP OOP river→CHECK`→R4=`no_made×river→BET★`。精度 LS=91%

**フロップ（V/S/B 分類）**
1. **SRP フロップ IP**: V=`2P+/TP+×dry-paired/UP×paired`、S=`UP×dry×gutshot×K/A/エア×strong draw×Q+`、B=`エア×low dry（低ボードでブラフ機能）`
2. **SRP フロップ OOP**: 原則 CHECK。例外 V=`TP+×dry×A-only` / `2P+×wet/paired×low`
3. **3BP フロップ IP**: V=`TP+`、B=`エア×paired≤6/エア×dry≤9`（低ボードブラフ）。スローレイ=`セット/フラッシュ→CHECK ★`
4. **4BP フロップ**: V=`TP+→BET 20%pot（82-100%）/Ultra-dry→AI`。スローレイなし（SPR低すぎ）

**ターン（V バリュー / S セミブラフ）**
5. **SRP ターン IP**: V=`2P+`、V+S=`TP++draw`、S=`エア+gutshot以上`。スローレイ=`TP+×dry×no draw → CHECK ★`、SD守=`UP → CHECK`
6. **3BP ターン IP**: V=`2P+/TP+×dry/UP×paired×10+`、S=`no_made_hand×dry×draw ★`。SD守=`ace_high/king_high/low_pair → 全 CHECK ★`
7. **4BP ターン IP dry**: V薄=`second_pair→BET ★★（73.9%）`、B=`third_pair/no_made_hand→BET ★`、V=`TP+/2P`。SD守=`king_high/ace_high→CHECK ★`（逆転！）。FD/OESD×no_made→CHECK ★（⑤D）
8. **4BP ターン IP paired**: B=`third_pair→BET ★（90%）`、B=`ace_high→BET ★（59%）`
9. **SRP OOP ターン**: V=`2P+×wet/dry`、S=`エア+draw`
10. **3BP OOP ターン**: V=`TP+(trips含む)×dry`、S=`no_made_hand×draw ★`。SD守=`エア全（ace/king/low）→ CHECK ★`
11. **4BP OOP ターン dry**: V=`top_pair/trips`、S=`second/third_pair×gutshot ★（88-92%）`。スローレイ=`overpair/two_pair → CHECK ★`（逆転！）

**リバー（V薄 / B 純ブラフ / CHECK）**
12. **SRP リバー IP**: V=`2P+/TP+`、V薄=`second_pair/underpair`、B=`no_made_hand`。SD守=`king/ace_high/low_pair/third_pair → CHECK ★`
13. **3BP リバー IP**: V=`TP+`、V薄=`second_pair(79.5%)/underpair/third_pair(69%)`、B=`no_made_hand(61%)`。SD守=`king_high(0.4%)/ace_high(1.9%)/low_pair(10%) → CHECK ★★★`（gain=80BB/100）
14. **4BP リバー IP**: V=`TP+/2P+ → ALLIN`、B=`no_made_hand(58%)`、V薄=`second_pair(54%)`
15. **SRP OOP リバー**: V=`TP+/2P+`、V薄=`second_pair/underpair`、B=`no_made_hand`。SD守=`ace_high/low_pair → CHECK`
16. **3BP OOP リバー**: V薄=`second_pair(85%)/underpair(66%)/third_pair(75%)`、B=`no_made_hand×dry(50.7%)`。SD守=`king_high(0%)/low_pair(17%)/two_pair(45.6%) → CHECK ★★★`（gain=65BB/100）。**4BP OOP**: B=`third_pair(76%)/low_pair(58%) → BET ★★★`（逆転！）、スローレイ=`overpair(12.5%)/trips(43%) → CHECK ★`
"""


def append_cash_mtt_note(ch_num: str, content: str) -> str:
    """章末の「この章で覚える項目」 の直前に Cash/MTT note を挿入"""
    if ch_num not in CASH_MTT_NOTES:
        return content
    note = CASH_MTT_NOTES[ch_num]
    note_block = f"\n## Cash/MTT note\n\n{note}\n"

    marker = '\n## この章で覚える項目'
    if marker in content:
        return content.replace(marker, note_block + marker, 1)
    # ch19/23 で既に手書き済の場合は何もしない
    return content + note_block


# ===================================================================
# メイン
# ===================================================================
def main():
    print('Vol2 (ポストフロップ完全版) 章原稿生成中...')
    print(f'出力先: {OUT_DIR}')
    print()

    # 既存 .md ファイルを一掃 (renumber に伴う stale ファイル除去)
    for old in OUT_DIR.glob('*.md'):
        old.unlink()

    # 序章
    write('00-introduction.md',       append_cash_mtt_note('00', gen_ch00()))

    # 第 1 部: MATCHA Score 公式
    write('01-formula-overview.md',   append_cash_mtt_note('01', gen_ch01()))
    write('02-category.md',               append_cash_mtt_note('02', gen_ch02()))
    write('03-board.md',               append_cash_mtt_note('03', gen_ch03()))
    write('04-dv-street.md',           append_cash_mtt_note('04', gen_ch04()))
    write('05-pot-bs-overcards.md',    append_cash_mtt_note('05', gen_ch05()))

    # 第 2 部: 境界・例外
    write('06-grid-12-cells.md',       append_cash_mtt_note('06', gen_ch06()))
    write('07-hand-boundaries.md',     append_cash_mtt_note('07', gen_ch07()))
    write('08-board-boundaries.md',    append_cash_mtt_note('08', gen_ch08()))
    write('09-exceptions-5-rules.md',  append_cash_mtt_note('09', gen_ch09()))

    # 第 3 部: 4 軸の背景
    write('10-range-morphology.md',    append_cash_mtt_note('10', gen_ch10()))
    write('11-hand-strength.md',       append_cash_mtt_note('11', gen_ch11()))
    write('12-bet-size-spr.md',        append_cash_mtt_note('12', gen_ch12()))

    # 第 3 部: 4 軸の背景 + 旧理論橋渡し (新 ch13)
    write('13-classic-bridge.md',      gen_ch13_bridge())  # 新章、 内蔵 Cash/MTT note

    # 第 4 部: ポット種別 + コンテキスト別 (ch14-23)
    write('14-basic-attack.md',        gen_ch_basic_attack())   # NEW: アタック入門 (2 大原則)
    write('23-attack-rules.md',       gen_ch_attack_rules())   # 攻撃 8 ルール (第 4 部末)

    # 第 5 部: ポット種別 (+1 シフト)
    write('15-srp.md', append_cash_mtt_note('15', gen_ch13()))  # 旧 ch13 = SRP
    write('16-3bp.md', append_cash_mtt_note('16', gen_ch14()))  # 旧 ch14 = 3BP
    write('17-4bp.md', append_cash_mtt_note('17', gen_ch15()))  # 旧 ch15 = 4BP
    write('18-turn-lookup.md',        append_cash_mtt_note('18', gen_ch_turn_lookup()))  # NEW v6
    write('19-river-split.md',        append_cash_mtt_note('19', gen_ch_river_split()))  # NEW v6
    write('21-vs-cr.md', append_cash_mtt_note('21', gen_ch16()))  # 旧 ch16 = vs CR
    write('22-vs-donk.md',            gen_ch_vs_donk())                         # vs Donk 専用章

    # 第 5 部: スタック深度 + Cash/MTT 差 (+1 シフト)
    write('24-short-stack.md', append_cash_mtt_note('24', gen_ch17()))  # 旧 ch17 = short stack
    write('25-deep-stack.md', append_cash_mtt_note('25', gen_ch18()))  # 旧 ch18 = deep stack
    write('26-cash-vs-mtt.md',         gen_ch19_cash_vs_mtt())                  # 旧 ch19 (新 ch20)、 note 内蔵
    write('20-polarization.md',       gen_ch_polarization())                   # NEW v6 polarization 新章

    # 第 6 部: ICM / バブル / MW / テーブルサイズ (+1 シフト)
    write('27-icm.md', append_cash_mtt_note('27', gen_ch19()))  # 旧 gen_ch19 = ICM
    write('28-bubble.md', append_cash_mtt_note('28', gen_ch20()))  # 旧 gen_ch20 = バブル
    write('29-multiway.md', append_cash_mtt_note('29', gen_ch21()))  # 旧 gen_ch21 = MW
    write('30-table-size.md',          gen_ch23_table_size())                   # 旧 ch23 (新 ch24)、 note 内蔵

    # 第 7 部: 実戦 (+1 シフト)
    write('31-boundary-summary.md', append_cash_mtt_note('31', gen_ch22()))  # 旧 gen_ch22 = 境界総覧
    write('32-drills.md', append_cash_mtt_note('32', gen_ch23()))  # 旧 gen_ch23 = ドリル

    write('33-cheatsheet.md', append_cash_mtt_note('33', gen_ch24()))  # 旧 gen_ch24 = チートシート

    # 付録
    write('appendix-A.md',             gen_appendix_a())
    write('appendix-B.md',             gen_appendix_b())  # 旧来理論橋渡し早見
    write('appendix-C.md',             gen_appendix_c())  # NEW v6 MQS 品質保証指標

    print()
    print(f'完了: {OUT_DIR}')
    print('ファイル一覧:')
    for f in sorted(OUT_DIR.glob('*.md')):
        size = f.stat().st_size
        print(f'  {f.name}  ({size:,} bytes)')

    n_files = len(list(OUT_DIR.glob('*.md')))
    print(f'\n合計: {n_files} ファイル')

if __name__ == '__main__':
    main()
