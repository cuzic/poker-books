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

## 現在のサブスクリプション状況（確定版 2026-05-19）

**現在のプラン: PREMIUM ($79/月)**

### Preflop Spot Solution API アクセス結果

| ゲームタイプ | アクセス | 備考 |
|---|---|---|
| `MTTGeneral` (8-max, BB ante) | ✅ 完全アクセス可能 | SBR 8〜100、Phase 1/2/5 収集完了 |
| `MTTMRonlyGeneral` (8-max, MR-only) | ✅ アクセス可能 | SBR 8〜25 収集済み（126ファイル） |
| `MTTGeneral` depth=整数 (no ante) | ❌ PERMISSION_DENIED | Classic/no-ante 比較不可 |
| `MTTGeneralV2` | ❌ PERMISSION_DENIED | — |
| `MTTGeneral_8m` / `_7m` / `_5m` / `_3m` | ❌ PERMISSION_DENIED | 異テーブルサイズ不可 |
| `MTT6mGeneral` / `MTT6mSimple` | ❌ PERMISSION_DENIED | 6-max 不可 |
| `MTT9mGeneral` / `MTT9mMRonlyGeneral` | ❌ PERMISSION_DENIED | 9-max 不可 |
| `MTTHUGeneral` | ❌ 400 Bad Request | HU 不可 |
| **ICM 全種** (`MTTGeneral_ICM*`) | ❌ **PERMISSION_DENIED** | Elite/Ultra プラン必要 |
| `MTTGeneral_ICM8m200PTBUBBLEEARLY/LATE` | ⚠ 404 NOT_FOUND | プリフロップ解が未計算 |
| `MTTGeneral_ICM8m200PTBUBBLEMID/FT/START/T2/T3/PCT75` | ❌ PERMISSION_DENIED | 存在するが権限なし |
| `MTTGeneral_ICMPKO*` | ❌ PERMISSION_DENIED | PKO 不可 |
| `MTTSimpleTest_ICM*` | ❌ PERMISSION_DENIED | テストバリアント不可 |

### 重要な知見

- **"75,000+ ICM solutions"（Premium 特典）は Postflop ICM のみ**。Preflop ICM ソリューション（`/v4/solutions/spot-solution/` 経由）は別権限が必要。
- ICM Preflop 解を取得するには Elite ($139) または Ultra ($229) プランへのアップグレードが必要と推定。
- BURBBLEEARLY/LATE は game-modes API には存在するが、Preflop ソリューション自体が未計算（404）。

### 実用上の結論

**現プランで取得可能なデータで書ける内容:**
- Push/Fold ゾーン（SBR 8〜20BB）: ChipEV 8-max, BB ante
- Open-Raise ゾーン（SBR 20〜40BB）: 同上
- MW 多人数ポット（3〜4way）: 同上
- SB リンプ効果（MTTGeneral vs MTTMRonlyGeneral 比較）

**ICM の扱い:**
- GTO Wizard Preflop ICM データは取得不可（Premium プランの壁）
- vol6 既存 ICM 理論（BF=1.875、M値）は維持
- 「ICM 補正は +X BB に相当」はチップEV データから理論計算で推定

---

## API エンドポイント（確認済み）

```
GET /v4/game-modes/?variant_in=NLHOLDEM&format_in={format}
GET /v4/solutions/spot-solution/?gametype={type}&depth={depth}&preflop_actions={actions}
```

認証: `Authorization: Bearer {token}`
必須ヘッダー: `gwclientid: 930036c8-...`（固定値）
