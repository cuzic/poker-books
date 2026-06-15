# 第 22 章　vs Donk Bet — ドンクベットへの対応

## 22.1 ドンクベットとは

**ドンクベット (Donk Bet)** = ポストフロップで IP（先手）の c-bet を待たずに
OOP（後手）が先にベットしてくる行動です。

```
通常フロー: OOP check → IP bet → OOP call/raise/fold
ドンク   : OOP bet (= donk) → IP call/raise/fold
```

IP は「自分がアクション側」になるはずの局面で、突然ディフェンス側に回されます。

## 22.2 ドンクの発生頻度 — ターンカードが鍵

GTO データで判明した重要な事実があります：**ドンクの頻度はターンカードで激変します**。

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

## 22.3 vs Donk のレンジ分析 — vs CR と真逆

同じ pot=2 の文脈でも、相手のレンジ構造が vs CR と大きく異なります。

| 文脈 | opp strong% | opp weak% | 意味 |
|---|---:|---:|---|
| vs CR (チェックレイズ受け) | 46% | 22% | 相手 value-heavy |
| vs Donk (ドンクベット受け) | 14% | 61% | 相手 air-heavy |

→ **ドンクは相手が弱いシグナル**です。IP は wide defense で対応できますよ。

## 22.4 MATCHA Score での計算

vs Donk も **pot = 2** として扱います（vs CR と同じです）。

```
Score = Grid + DV × mult + 2 × oc + 4 × pot − 2 × bs
                                        ↑ pot=2 → +8
```

ただし、**vs CR 専用例外 (ex9/ex10) は vs Donk に適用しない**ようにしましょう。

| 例外 | vs CR | vs Donk |
|---|---|---|
| ex9: UP/TP+ × dry × turn → fold | ✓ 適用 | ✗ 不適用 |
| ex10: TP+ × wet × turn → fold | ✓ 適用 | ✗ 不適用 |

理由としては、ex9/ex10 は「vs CR では相手が value-heavy」という前提に基づいています。
vs Donk では相手が air-heavy ですので、fold は損になってしまいます。

## 22.5 ターンドンク — ボードペア時の対応

ターンがボードをペアしてきた場合 (e.g., Ks7d2c → **Kh** or **7c**)、
OOP のドンク頻度が 19-41% に跳ね上がります。

| 自分のハンド | Score 計算 | 推奨アクション |
|---|---|---|
| 2P+ (セット/ツーペア) | Grid 高 + 8 ≥ 43 | **call / 状況によりraise** |
| TP+ | Grid 38 + 8 = 46 → DEF T=49 | **call** |
| アンダーペア | Grid 低 + 8 | 公式に従い call or fold |
| エア | Grid 1 + 8 = 9 | fold |

> **ポイント**: ボードペア時の donk は、相手が trips を持っている可能性が高いです。
> こちらも trips 以上 (ex11) なら raise、それ以下は call または fold で対応しましょう。

## 22.6 vs Donk 専用例外

### 例外 11: 2P+ × paired × river × vs Donk → raise (value)

```
river × paired board × 自分が 2P+(trips/FH/quads) × vs Donk → RAISE
```

- GTO RAISE: 100%
- 理由: river vs Donk のレンジは bluff が多く、IP の 2P+ はナッツ優位です
- ターンへの適用は不可（ターンでは slowplay が有効なため）

## 22.7 フロップドンク — 対応指針

フロップドンクは GTO では稀（≈0%）ですが、ライブや低ステークスでは起こることがあります。

- 相手のドンクはレンジ逸脱 → wide defense をしましょう
- Score を pot=2 で計算してそのまま適用します
- TP+ 以上: call
- 2P+: raise を検討してみましょう（相手のドンクが弱い手である可能性が高いため）
- エア: fold

## 22.8 リバードンク — ポラライゼーション

OOP がリバーをドンクする場合、ポラライズされた range (ナッツ or ブラフ) になります。

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
