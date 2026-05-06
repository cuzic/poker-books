# poker-drill UI 新スケール対応 変更点

実施日: 2026-05-05
担当: Agent (UI コンポーネント新スケール対応)

新 HandScore (0-100 equity %) スケールおよび新後手スコア式 (`HandScore + A − C − M`、閾値 40/20) への UI 対応完了。

## 1. 修正ファイル

| ファイル | 変更箇所数 | 変更内容 |
|---|---:|---|
| `src/components/CardFlip/FlopCardBacks.tsx` | 14 | HS 閾値 14/7 → 65/35、役スコア 30 → 80、ROLE_HS_RULE、cbetJudge、cbet3bpJudge、判定セル detail、H_BUCKET_ROWS、3BP CBet 判定、ドロー加点公式表記 |
| `src/components/CardFlip/TurnRiverCardBacks.tsx` | 約 30 | 後手閾値 8/0 → 40/20、HS 閾値 14/7/18/30 → 65/35/70/85、A係数 1/2/3 → 0/6/12、C係数 3/5/7/9/11 → 12/17/22/25/30、M係数 0/3/6 → 0/12/22、ナッツ判定 30→88、Rivers の `−3` 基礎控除を削除、cCoeff 帯色閾値、_RIVER_CBET_ROWS、cbet バケツ getHandScoreBucket、riverJudge、bucketJudge、facingJudge、ブロッカー値 +3/+2/+0 → +5/+3/+2/+0、説明文の数値全般 |
| `src/core/glossary.ts` | 1 | HandScore / H1/H2/H3 説明文を新スケールに |
| `src/components/Common/VerifyChecklist.tsx` | 1 | コメント例の HS 値を更新 |

## 2. 主な変更パターン

### 2.1 後手スコア式の閾値変更

```
旧: ≥ 8 → CR / 0〜7 → コール / < 0 → フォールド
新: ≥ 40 → CR / 20〜39 → コール / < 20 → フォールド
```

### 2.2 HandScore バケツ閾値

```
旧フロップ: H3 ≥ 14 / H2 ≥ 7 / H1 < 7
新フロップ: H3 ≥ 65 / H2 ≥ 35 / H1 < 35

旧リバー V/M/B: V ≥ 18 / M ≥ 10 / B < 10
新リバー V/M/B: V ≥ 70 / M ≥ 35 / B < 35
```

### 2.3 後手スコア式の係数

```
旧: HandScore + A − 3 − C [− M]
    A: ドライ 3 / セミ 2 / ウェット 1
    C: 33%=3 / 50%=5 / 75%=7 / 100%=9 / 150%=11
    M: HU=0 / 3way=3 / 4way+=6

新: HandScore + A − C [− M]   (基礎控除 −3 を削除)
    A: ドライ 12 / セミ 6 / ウェット 0
    C: 33%=12 / 50%=17 / 75%=22 / 100%=25 / 150%=30
    M: HU=0 / 3way=12 / 4way+=22
```

### 2.4 ブロッカー加点

```
旧: ナッツ +3 / 準ナッツ +2 / なし +0
新: ナッツ +5 / 上位 +3 / バリュー +2 / なし +0
```

### 2.5 役スコア値（説明文中の参照値）

```
旧: TPGK 15 / TPMK 8 / TPTK 18 / セット+ 30
新: TPGK 62 / TPMK 50 / TPTK 70 / セット+ 85+
```

### 2.6 ドロー加点公式表記

```
旧: アウツ × 1.5、上限 +15
新: フロップ アウツ × 4 (上限 +50) / ターン × 2 / リバー 0
```

### 2.7 cCoeff 帯色閾値（QuickJudgeDefense）

```
旧: cCoeff <= 3 / 5 / 7、 >= 9 / 7
新: cCoeff <= 12 / 17 / 22、 >= 25 / 22
```

## 3. 維持されたもの

- バケツラベル `H1` / `H2` / `H3` (フロップ・ターン後手 / リバーの一部 Defense)
- バケツラベル `V` / `M` / `B` (リバー)
- 役割ラベル `攻める` / `守る` / `捨てる` / `ショーダウンバリュー`
- バレルスコア閾値 (≥7 / 4-6 / ≤3) — 仕様で不変
- α / MDF テーブル — 旧から不変
- 数値ながら他の意味を持つ箇所:
  - `kicker >= 12` / `kicker >= 13` (ランク値)
  - `boardTopRank >= 13` / `>= 12` (ボードランク)
  - `pct >= 70` (頻度)
  - SPR 閾値 (`< 3` / `<= 6`)
  - `barrelScore >= 7` / `< 7` / `>= 11` (バレル独自スケール)

## 4. ビルド結果

```
$ cd /home/cuzic/poker-drill && bun run build
✓ built in 959ms
```

ビルド成功。型エラー・コンパイルエラーなし。

## 5. E2E テストへの影響予想

```
src/components/CardFlip/__tests__/RiverDefenseBack.e2e.test.tsx
src/components/CardFlip/__tests__/TurnCbetBack.e2e.test.tsx
src/components/CardFlip/__tests__/TurnBack.e2e.test.tsx
src/components/CardFlip/__tests__/BeginnerVerifiability.smoke.test.tsx
+ 約 13 ファイル
```

- **影響大**: 数値期待値 (例: `expect(hs).toBe(15)` → `62` 等)
  - VerifyChecklist の `judge` テキスト ("HS X ≥ 18 → V" → "HS X ≥ 70 → V")
  - 後手スコア計算結果の文字列マッチ
- **影響小**: 役割・バケツ・アクション ラベル (不変)
  - "H3" / "V" / "CR" / "コール" など

期待値更新は次タスク (#315) で対応予定、約 50-100 件想定。

## 6. 残課題

- TurnRiverCardBacks.tsx の `barrelScore >= 11` (line 621/630) は OB 条件で、バレル スコア 8+3 = 11 がドライ × OC ターン (ペア) の上限値。新スケールで barrelScore 自体は不変なので維持。
- ALPHA_TABLE_ROWS (α/MDF) は従来通り α 値で表現 (旧スケール影響なし)。
- 既存の "係数表まとめ" 表示中、`STREET_CARD_LABELS` 系は不変。
