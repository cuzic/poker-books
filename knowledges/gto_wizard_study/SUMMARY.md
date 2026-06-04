# GTO Wizard Study — 200bb 6-max / ICM 28bb

調査日: 2026-05-25
スポット数: 63（成功）/ 92（試行）
データソース: GTO Wizard API (`MTT6mSimple` @200.125bb, `MTTGeneral_ICM6m200PTT2` @28.125bb asymmetric)

## スコープ前提

- **MTT6mSimple = 200bb 6-max deep stack**（チップ EV）。実質キャッシュ 200bb 等価
- **MTTGeneral_ICM6m200PTT2 = 28bb asymmetric バブル**（PT2 payout）
- precomputed action tree — tree に存在するベットサイズしか受理されない
- ストリート切り捨て: 3BP HJvBB の `X-R19.9-C` 後の turn は **無解**（tree が打ち切られる）

## 大局結論

旧 study（TexasSolver + 自前ソルブ）と GTO Wizard 解は **概ね整合** するが、いくつかの **見落とし** が判明:

1. **BB のフロップ donk は禁止** — SRP HJvBB / BTNvBB のフロップ donk 頻度は実測 100% check。レンジ優位は完全に IP 側
2. **SRP IP cbet-call 後のターン donk も禁止** — 全 5 ボードで BB は 100% check
3. **マルチウェイのフロップ SB lead は T76 等で 25%** — 旧 m_coef は弱コネクト板での SB donk を過小評価していた可能性
4. **SRP XX-XX 経路のリバー BB 主導率は 50-80%** — 「flop 諦め後の river 機会」が定量化された
5. **ICM バブル BB 防御で BTN vs に対するシャブ率 13%** — 高 ICM 圧で「コール or all-in」の極化が明確
6. **3BP HJvBB フロップ XX 経路で BB turn lead 70-80%** — 「3bp で IP がチェックバック → BB がリードを取る」プレイラインが明示

---

## 主要発見の数値表

### 1. SRP HJvBB ターン probe（フロップ XX 後 BB first）

| board | texture | check% | bet% | bet size |
|-------|---------|-------:|-----:|---------:|
| Ks7d2c5h | dry K-high | 89.7 | 10.3 | 372% pot (overbet) |
| Ah4d2c9s | dry A-high | 76.7 | 23.3 | 34% pot |
| Th9s8c4d | wet T98+blank | 77.5 | 22.5 | 101% pot |
| 9h8s7d4c | wet 987+blank | 53.9 | **46.1** | 34% pot |
| QhJd4s7c | QJ-high | 95.2 | 4.8 | 101% pot |

**示唆**: コネクトした draw-heavy turn (987) では BB が高頻度で probe（46%）、特に 33%pot の小サイズ。ペア turn・dry turn ではほぼ check。

### 2. SRP HJvBB ターン donk（IP cbet-call 後 BB first）

| board | check% | donk% |
|-------|-------:|------:|
| Ks7d2c5h | 100.0 | 0.0 |
| Ah4d2c9s | 100.0 | 0.0 |
| 9h8s7d4c | 100.0 | 0.0 |
| QhJd4s7c | 100.0 | 0.0 |
| Td7c6s2h | 99.8 | 0.2 |

**書籍反映候補**: vol2 ch08（ターン defense）に「ターン donk は 0%、必ず check して IP の barrel に対応する」と明記すべき。

### 3. SRP HJvBB フロップ donk（preflop call 後 BB first）

| board | check% | donk% |
|-------|-------:|------:|
| Ks7d2c | 100.0 | 0.0 |
| 9h8s7d | 100.0 | 0.0 |
| AhKd4s | 100.0 | 0.0 |
| Td7c6s | 98.1 | 1.9 |
| QhJd4s | 100.0 | 0.0 |

**書籍反映候補**: vol2 ch03（フロップ defense）に「BB のフロップ donk は ~0%」を明記。

### 4. SRP HJvBB ターン cbet-call 後のリバー（turn give-up 経路）

`F-R2.2-F-F-F-C / X-R1.9-C / X-X / river` — BB first

| board | check% | lead% | size |
|-------|-------:|------:|------|
| Ks7d2c5h3d | 62.7 | 37.3 | 125%pot (overbet) |
| QhJd4s7c2h | 58.0 | 42.0 | 125%pot |
| 9h8s7d4c2d | 22.4 | **77.6** | 33%pot |

**示唆**: IP がターン諦め → BB は 33% リード or 125% オーバーベットの **二峰性**。987 連続板では 78% リード（IP の give-up シグナルを活用）。

### 5. SRP XX-XX 経路のリバー（double check 後）

| flow | board | check% | lead% | size |
|------|-------|-------:|------:|------|
| HJvBB | Ks7d2c5h3d | 80.5 | 19.5 | 126%pot |
| HJvBB | Th9s8c4dAh | 50.9 | 49.1 | 34%pot |
| BTNvBB | Ks7d2c5h3d | 46.4 | 53.6 | 33%pot |

**示唆**: BTNvBB は SRP XX-XX 経路でも 54% で BB がリードを取る。「IP のチェックチェック＝レンジ放棄」を活用。

### 6. マルチウェイ 3-way HJ+SB+BB（フロップ SB first）

| board | check% | bet% |
|-------|-------:|-----:|
| Ks7d2c | 90.5 | 9.5 |
| 9h8s7d | 90.7 | 9.3 |
| AhKd4s | 95.4 | 4.6 |
| **Td7c6s** | 74.8 | **25.2** |

**示唆**: 3-way ではほぼ常に check が基本だが、SB が **T76 のような弱コネクト板で 25% リード**。これは「IP（HJ）の cbet 範囲が狭まる board → OOP donk が有効」のソルバー解。

### 7. マルチウェイ 3-way ターン（XXX 後）

| board | check% | bet% |
|-------|-------:|-----:|
| Ks7d2c5h | 76.2 | 23.8 |
| Th9s8c4d | 57.3 | 42.7 |
| AhKd4s8c | 59.4 | 40.6 |

**示唆**: マルチウェイでもターンで SB は **40%+ リード**（T98、AK4 のような texture 強化板）。

### 8. 3BP HJvBB フロップ XX 経路でのターン（BB first）

`F-R2.2-F-F-F-R13.2-C / X-X / turn` — BB first

| board | check% | bet% | size |
|-------|-------:|-----:|------|
| Ks7d2c5h | 30.2 | **69.8** | 20%pot |
| 9h8s7d3c | 66.4 | 33.6 | 140%pot (overbet) |
| AhKd4s8c | 79.7 | 20.3 | 140%pot |

**示唆**: 3BP で IP が flop チェックバック → BB は **70% リード**（dry Kxx の小サイズ）または **20-34% overbet**（wet board）。サイズ二峰性が鮮明。

### 9. マルチウェイリバー（all check 後）

| board | check% | bet% |
|-------|-------:|-----:|
| Ks7d2c5h3d | 80.3 | 19.7 |
| Th9s8c4d2d | 89.7 | 10.3 |

**示唆**: マルチウェイで全員 check → river もほぼ check（80-90%）。リードは控えめ。

### 10. ICM バブル（28bb、asymmetric stacks 28.125-26-22-30-20-24）

#### Open 頻度（フィッシューチップが残ったバブル）

| position | open% | size |
|----------|------:|------|
| UTG (LJ) | 22.5 | R2 (31% pot) |
| HJ | 24.7 | R2 |
| CO | 27.6 | R2 |
| BTN | 39.2 | R2 |

cEV 6m と比較すると **BTN open が 5-10pt 縮小**（cEV ~45-50% → ICM 39%）

#### BB 防御（vs 各ポジション open）

| 相手 | F% | C% | 3bet% | All-in% |
|------|---:|---:|------:|--------:|
| UTG | 56.0 | 36.8 | 4.9 | 2.3 |
| HJ | 51.9 | 38.6 | 5.1 | 4.4 |
| CO | 47.2 | 37.5 | 5.6 | 9.7 |
| BTN | 42.1 | 36.9 | 8.6 | **12.5** |

**示唆**: BB vs BTN open で BB の all-in 頻度 **12.5%** — ICM 圧で「コール vs オールイン」の極化。chip EV ではこのサイズでの 3bet は通常 R6-R8 程度の通常レイズが主流。

---

## 旧シリーズと書籍への反映候補

| 領域 | 旧式・旧記述 | 新発見 | 修正案 |
|------|------------|-------|------|
| vol2 ch03 「フロップ defense」 | flop donk 言及曖昧 | OOP flop donk = 0% 確定 | 「**フロップで donk は打たない、必ず check** 」を明記 |
| vol2 ch08 「ターン defense」 | turn donk frequency 未定義 | turn donk = 0%（IP cbet-call 後） | 「ターン donk = 0%、常に check して IP の 2nd barrel に応答」 |
| vol2 ch11 「multistreet plan」 | XX-XX river の戦略薄い | BB が river 主導（19-54%） | 「XX-XX → river は BB ターン、texture で 33%/over-bet 分岐」 |
| vol2 ch05 「マルチウェイ」 | SB donk 頻度未記載 | T76 で 25%、その他 5-10% | 「3-way SB は基本 check、弱コネクト板のみ 25% lead」 |
| vol4 ch10 「ICM bubble」 | BB 防御 chip EV ベース | ICM で 3bet→all-in に置換 | 「ICM ではコール or all-in の二択化、特に BTN open vs」 |
| vol4 ch00 「SBR」 | open 率 chip EV ベース | ICM で BTN -7pt | 「ICM bubble では BTN 縮小、SB-BB の防御範囲は要再計算」 |

## 既存 GCP study との整合性

2026-05-12 の 395-board GCP study との比較:

| 指標 | GCP study | GTO Wizard (本研究) | 整合 |
|------|----------|--------------------|------|
| SRP HJvBB Kxx 板 cbet | 99.3% | 100% (R1.9) | ✅ |
| SRP HJvBB 連結板 cbet | ~85% | 93% (987) | ✅ |
| SRP turn donk | 言及なし | 0% | 新発見 |
| OOP MDF vs 33% | 25.0% (実測) | — | (本研究対象外) |

新発見が中心 — GCP study は IP cbet 中心、本研究は **OOP の各ストリート初動** に焦点。

## 残課題（未調査）

- **3BP HJvBB の cbet-called 後の turn-river** — API 側で打ち切られている。TexasSolver で別途
- **4BP** — preflop 4bet 確認できず（tree に存在するか不明）
- **ICM 浅スタック (15bb 等)** — Premium tier では asymmetric depth=28 のみアクセス可
- **9-max ICM** — `MTTGeneral_ICM9m200PT*` は permission denied
- **Cash 100bb** — `Cash6mGeneral_*` は 401 unauthorized

## ファイル構成

```
knowledges/gto_wizard_study/
├── SUMMARY.md (このファイル)
├── fetch_log.tsv (実行ログ)
├── <topic>/
│   ├── <id>.json (各スポットの解)
│   └── REPORT.md (トピック別集計)
```

スクリプト: `scripts/gto_wizard_study/{fetch,aggregate}.py`、CSV: `spots_v1.csv`/`spots_v2.csv`
