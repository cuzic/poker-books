# GTO Wizard API 仕様メモ — トーナメント編

**調査日**: 2026-05-19

---

## 利用可能なフォーマット

`/v4/game-modes/?format_in=` に指定できる値:

```
Cash / MTT / Spins / HuSng / Shortdeck / Straddle_ante_cash / Straddle_ante_cash_6max / Custom
```

---

## MTT ゲームタイプ一覧（重要なもの）

### 非 ICM（チップ EV）— メイン調査用

| ゲームタイプ名 | プレイヤー数 | 特徴 |
|---|---|---|
| `MTTGeneral` | 8 | **メイン**: ante 込み、depth 2〜100BB (0.125刻み) |
| `MTT9mGeneral` | 9 | 9-max（game_modes は非対称スタック中心） |
| `MTT9mMRonlyGeneral` | 9 | 9-max min-raise only |
| `MTT6mGeneral` | 6 | 6-max（depth は対称/非対称スタック混在） |
| `MTTMRonlyGeneral` | 8 | 標準 MTT min-raise のみ |

### depth エンコーディング

`depth = SBR + 0.125` （0.125 = BB ante）

例: SBR=10BB → `depth=10.125`、SBR=20BB → `depth=20.125`

`MTTGeneral` で使える SYMMETRIC（全員等スタック）の depth 一覧:

```
2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 17, 20, 25, 30, 35, 40, 50, 60, 80, 100 BB
```

（各 + 0.125 が実際の depth 値）

### ICM フェーズ — ステージ別

| ゲームタイプ名（例） | 意味 |
|---|---|
| `MTTGeneral_ICM9m200PTSTART` | 200人規模トーナメント序盤（9人テーブル） |
| `MTTGeneral_ICM8m200PTPCT75` | 全体の 75% が脱落（25% 残存） |
| `MTTGeneral_ICM8m200PTPCT50` | 50% 脱落（50% 残存） |
| `MTTGeneral_ICM8m200PTT3` | 残り 3 テーブル |
| `MTTGeneral_ICM8m200PTT2` | 残り 2 テーブル |
| `MTTGeneral_ICM8m200PTBUBBLEEARLY` | バブル序盤 |
| `MTTGeneral_ICM8m200PTBUBBLEMID` | バブル中盤 |
| `MTTGeneral_ICM8m200PTBUBBLELATE` | バブル直前 |
| `MTTGeneral_ICM8m200PTFT` | ファイナルテーブル（8人残） |
| `MTTGeneral_ICM2m〜9m200PTFT` | FT 残 2〜9 人 |
| `MTTGeneral_ICM*1000PT*` | 1000 人規模大会版 |
| `MTTGeneral_ICMPKO*` | PKO（プログレッシブノックアウト）版 |

フィールドサイズ: `200PT` = 200 人規模、`1000PT` = 1000 人規模

#### ICM ゲームタイプの名前構造

```
MTTGeneral_ICM{残人数}m{フィールドサイズ}PT{ステージ}
例: MTTGeneral_ICM8m200PTBUBBLEMID
    = ICM有り / 8人残 / 200人規模トーナメント / バブル中盤
```

---

## preflop_actions エンコーディング（Cash と同様）

MTT でもキャッシュゲームと同じ形式を使用:

```
F  = fold
C  = call / limp
R2 = raise to 2BB (min-raise)
R25 = raise to 2.5BB
RAI = all-in
```

ポジション順: LJ(UTG) → HJ → CO → BTN → SB → BB（8-max の場合）
8-max は UTG/UTG+1 相当が LJ/HJ になる可能性あり（要実機確認）

---

## Spins（Spin&Go）ゲームタイプ

| 名前 | 特徴 |
|---|---|
| `Spins` | 標準 Spin&Go（3-handed、アンテなし） |
| `SpinsAnte` | アンテあり版 |
| `SpinsAdvancedV2` / `SpinsComplexV2` | 複雑なツリー（多サイズ対応） |

---

## 現在のサブスクリプション状況

**現在のプラン: STARTER**

| カテゴリ | アクセス可否 |
|---|---|
| Cash 6m（3betV2 等） | ✅ アクセス可能（実績あり） |
| **MTT（全種）** | ❌ **PERMISSION_DENIED** |
| Spins | ❌ 未確認（おそらく不可） |
| HuSng | ❌ 未確認 |

### MTT へのアクセスに必要な対応

GTO Wizard の MTT ソリューションには **上位プランへのアップグレードが必要**。

GTO Wizard のプラン構成（2024〜2025 時点の一般情報）:
- **Starter**: 一部の Cash ソリューション（限定）
- **Essential / Pro / Elite**: MTT ソリューション含む

**次のアクション**: GTO Wizard のプラン設定ページで MTT へのアクセスを確認・アップグレード。

---

## API エンドポイント（確認済み）

```
GET /v4/game-modes/?variant_in=NLHOLDEM&format_in={format}
GET /v4/solutions/spot-solution/?gametype={type}&depth={depth}&preflop_actions={actions}
```

認証: `Authorization: Bearer {token}`
必須ヘッダー: `gwclientid: 930036c8-...`（固定値）
