# フロップ・ターン・リバー アクション判断仕様書

Given/When/Then（Gherkin 風）形式によるアクション判断の網羅的定義。

---

## 前提条件（全シナリオ共通）

本仕様書の全シナリオは以下の条件を前提とする。

| 項目 | 値 |
|------|-----|
| ゲーム形式 | 6-max キャッシュゲーム、100BB スタート |
| ポット構造 | SRP（シングルレイズドポット）。3bet/4bet ポットは別シナリオ |
| 人数 | HU（ヘッドアップ）到達後のフロップ以降 |
| IP 定義 | プリフロップ最終アグレッサー（PFR）= CBet 権利保有者 |
| OOP 定義 | プリフロップコーラー（BB または コーラー） |
| ベットサイズ | ポット比率表記（33% = ポットの 1/3） |
| HS・B スケール | 0-100 の整数。`calc_hand_score` / `calc_board_score` 準拠 |

> **注意**: 本仕様は実装のデフォルト戦略を定義する。GTO との乖離は各シナリオの「GTO 実測」注記を参照。

---

## 凡例

- **HS**: Hand Score（ハンドスコア）
- **B**: Board Score（ボードスコア、`calc_board_score` が返す 0-100 の値）
- **T1/T2/T3**: ハンドのティア（T1: HS≥65、T2: HS≥20、T3: HS<20）
- **IP**: In Position（ポジション有利側）
- **OOP**: Out of Position（ポジション不利側）
- **CBet**: Continuation Bet（コンティニュエーションベット）
- **CR**: Check-Raise（チェックレイズ）
- **BC**: Bluff Catcher（ブラフキャッチャー）
- **BDFD**: Backdoor Flush Draw（バックドアフラッシュドロー）

---

## Flop

### Board Score リファレンス

| ボードタイプ      | B 値 |
|-----------------|------|
| paired_high     | 83   |
| mono            | 70   |
| rainbow_connected | 67 |
| rainbow_AK      | 62   |
| paired_low      | 71   |
| rainbow_Q       | 58   |
| rainbow         | 55   |
| 2tone           | 50   |
| 2tone_AK        | 56   |

### Hand Score 計算式

```
HS = role_score + draw_bonus(outs × 4) + 2OC_bonus(+24) + BDFD(+6)

役スコア:
  セット          : 85
  オーバーペア    : 70-80
  2ペア           : 72
  TPTK            : 65
  TPGK            : 60
  TPMK            : 55
  TPWK            : 50
  セカンドペア    : 42（キッカー良）/ 38（キッカー弱）
  ボトムペア      : 30
  Air             : 25 / 20 / 15
```

---

### Scenario: Flop-IP-01 T1 ハンドによる常時 CBet

```
Given  IP が CBet 権利を保有している（プリフロップ最終アグレッサー）
  And  フロップが開かれた
  And  HS ≥ 65（T1: TPTK 以上）
When   フロップアクションを決定する
Then   CBet を実行する
  And  サイズはボードタイプに従う（後述の CBet サイズシナリオを参照）
```

例: hand=AsKh, board=Kd7c2s → HS=65(TPTK), B=55(rainbow) → CBet 33%

---

### Scenario: Flop-IP-02 T2 ハンドかつ高 B によるミディアム CBet

```
Given  IP が CBet 権利を保有している
  And  HS ≥ 20 かつ HS < 65（T2）
  And  B ≥ 58
When   フロップアクションを決定する
Then   CBet を実行する
  And  サイズはボードタイプに従う
```

例: hand=8h8d, board=Kd7c2s → HS=38(セカンドペア), B=55 → B<58 のためチェック
例: hand=8h8d, board=Qs7s2h → HS=38(セカンドペア), B=58(rainbow_Q) → CBet 33%

---

### Scenario: Flop-IP-03 T2 ハンドかつ低 B によるチェック

```
Given  IP が CBet 権利を保有している
  And  HS ≥ 20 かつ HS < 65（T2）
  And  B < 58
When   フロップアクションを決定する
Then   チェックする（CBet なし）
```

例: hand=8h8d, board=Ac6d2s → HS=38, B=55(rainbow) → チェック

---

### Scenario: Flop-IP-04 T3 ハンドかつ高 B によるブラフ CBet

```
Given  IP が CBet 権利を保有している
  And  HS < 20（T3: Air/ボトムペア弱）
  And  B ≥ 62
When   フロップアクションを決定する
Then   ブラフ CBet を実行する
  And  サイズはボードタイプに従う（通常 33%）
  And  ドローバックドアを含む場合は優先候補
```

例: hand=AhJd, board=Ks8h3c → HS=15(Air 無オーバー), B=62(rainbow_AK) → ブラフ CBet 33%

---

### Scenario: Flop-IP-05 T3 ハンドかつ低 B によるチェック

```
Given  IP が CBet 権利を保有している
  And  HS < 20（T3）
  And  B < 62
When   フロップアクションを決定する
Then   チェックする（ブラフ CBet 不可）
```

例: hand=7h6h, board=As5d2c → HS=15(Air), B=55(rainbow) → チェック

---

### Scenario: Flop-IP-06 paired_high ボードの CBet サイズ

```
Given  IP が CBet を実行する判断になっている
  And  B ≥ 83（paired_high: KK7, QQ3 等）
When   CBet サイズを決定する
Then   HS ≥ 80（トリップス・オーバーペア強）→ 75% pot ベット（大サイズでバリュー最大化）
  And  HS < 80（TPTK・TPGK 等）→ 33% pot ベット（小サイズで広くベット、ブラフも含める）
  And  理由: ペアボードは IP のレンジがポーラーになりやすい
            HS≥80 でナッツ（トリップス）→ 大サイズ。T1 だが HS<80 → 小サイズで頻度重視
  And  GTO 実測: paired_high フォールド率 23-33%（中程度）→ サイズ選択の余地あり
```

例: hand=7h7d, board=QsQd7c → HS=90+(フルハウス) → 75% pot
例: hand=AhKs, board=QsQd7c → HS=65(TPTK) → 33% pot
例: hand=AhAd, board=KsKd7c → HS=80+(オーバーペア) → 75% pot

---

### Scenario: Flop-IP-07 mono ボードの CBet サイズ

```
Given  IP が CBet を実行する判断になっている
  And  ボードタイプが mono（全スーツ統一, B≥70）
When   CBet サイズを決定する
Then   75% pot ベット
  And  理由: モノトーンは全フラッシュドローが完成形 → 大サイズでエクイティを守る
```

例: hand=AsJs, board=9s7s4h → B=70(mono), CBet 75%

---

### Scenario: Flop-IP-07b 2tone・connected ボードの CBet サイズ

```
Given  IP が CBet を実行する判断になっている
  And  ボードタイプが 2tone または connected（B=50-70）
When   CBet サイズを決定する
Then   50% pot ベット
  And  理由: ドローは存在するが完成ではない → 中サイズでドローにコスト
```

例: hand=AhQh, board=Jh7h2c → B=62(2tone), CBet 50%
例: hand=KhQd, board=Jd9c5h → B=60(connected), CBet 50%

---

### Scenario: Flop-IP-08 2tone_AK ボードの CBet サイズ

```
Given  IP が CBet を実行する判断になっている
  And  ボードタイプが 2tone_AK（B=56）
When   CBet サイズを決定する
Then   50% pot ベット
  And  理由: A/K ハイボードは OOP も当たりやすく中サイズが適正
```

例: hand=AhQd, board=Ad8h3h → B=56(2tone_AK), CBet 50%

---

### Scenario: Flop-IP-09 その他ボードの CBet サイズ（デフォルト）

```
Given  IP が CBet を実行する判断になっている
  And  B < 70 かつ ボードタイプが 2tone_AK でない
When   CBet サイズを決定する
Then   33% pot ベット（小サイズ）
  And  理由: 中程度のドロー・バランスを取りやすいレンジでは小サイズが収支最大化
```

例: hand=KhQh, board=Kd5c2h → B=55(rainbow), CBet 33%

---

### Scenario: Flop-OOP-01 vs CBet 33%: 極弱ハンドのフォールド

```
Given  OOP がフロップチェック後に IP から CBet 33% を受けた
  And  HS < 15（BDFD・BDSD ボーナス込みの最終 HS）
When   フォールド閾値を判定する
Then   フォールドする
  And  注意: HS には BDFD(+6)・BDSD(+3) が既に含まれる
            Air(10) + BDFD(6) = HS=16 → コール対象（Flop-OOP-02 へ）
            Air(10) + BDSD(3) = HS=13 → HS<15 のためフォールド
```

例: hand=3h2d, board=Kd9s5c → HS=10(Air, BDFD/BDSD なし) → フォールド
例: hand=3h2h, board=Kd9h5c → HS=10+3=13(Air+BDSD) → HS<15 → フォールド

---

### Scenario: Flop-OOP-02 vs CBet 33%: HS ≥ 15 によるコール（通常ボード）

```
Given  OOP がフロップチェック後に IP から CBet 33% を受けた
  And  HS ≥ 15（BDFD・BDSD ボーナス込みの最終 HS）
  And  ボードタイプ補正なし（通常ボード）
When   フォールド閾値を判定する
Then   コールする（フォールドしない）
  And  BDFD 保有の Air ハンド例: Air(10) + BDFD(6) = HS=16 ≥ 15 → コール
```

例: hand=Ah7d, board=Kd9s5c → HS=20(Air+OC1) → コール
例: hand=7h6h, board=Kd9s5c → HS=10+6=16(Air+BDFD) → HS≥15 → コール（BDFD含め閾値クリア）

---

### Scenario: Flop-OOP-03 vs CBet 75%: HS < 35 のフォールド

```
Given  OOP がフロップチェック後に IP から CBet 75% を受けた
  And  HS < 35
  And  ボードタイプ補正なし
When   フォールド閾値を判定する
Then   フォールドする
```

例: hand=8h6d, board=As9c3s → HS=30(ボトムペア), vs 75% → フォールド

---

### Scenario: Flop-OOP-04 vs CBet 75%: HS ≥ 35 によるコール

```
Given  OOP がフロップチェック後に IP から CBet 75% を受けた
  And  HS ≥ 35
  And  ボードタイプ補正なし
When   フォールド閾値を判定する
Then   コールする
```

例: hand=Ah8d, board=As9c3s → HS=50(TPWK), vs 75% → コール

---

### Scenario: Flop-OOP-05 ペアボード補正による守備閾値の引き下げ（-10）

```
Given  OOP が CBet を受けた
  And  ボードタイプが paired（ペアボード）
When   フォールド閾値を算出する
Then   ベースライン閾値から -10 して判定する
  And  理由: OOP のトリップス・フルハウスが多くなるため守備容易
```

例: vs 75% のベースライン=35 → ペアボード補正後=25 → HS ≥ 25 でコール可能
例: hand=7c6d, board=7d7s3c → HS=30(ボトムペア), 補正後閾値 25 → コール（30≥25）

---

### Scenario: Flop-OOP-06 2tone ボード補正による守備閾値の引き上げ（+5）

```
Given  OOP が CBet を受けた
  And  ボードタイプが 2tone（フラッシュドロー存在）
When   フォールド閾値を算出する
Then   ベースライン閾値に +5 して判定する
  And  理由: ドローで IP が広くベット → OOP はより強いハンドで守備すべき
```

例: vs 33% のベースライン=15 → 2tone 補正後=20 → HS < 20 でフォールド
例: hand=5h4d, board=Ah8h3c → HS=15(Air), 補正後閾値 20 → フォールド

---

### Scenario: Flop-OOP-07 モノトーン補正による守備閾値の引き下げ（-5）

```
Given  OOP が CBet を受けた
  And  ボードタイプが mono（全同スーツ）
When   フォールド閾値を算出する
Then   ベースライン閾値から -5 して判定する
  And  理由: OOP のフラッシュ完成率が高まるため守備しやすい
```

例: vs 75% のベースライン=35 → mono 補正後=30 → HS ≥ 30 でコール可能
例: hand=Kh9h, board=Ah5h2h → HS=30(KFD強) → コール（30≥30）

---

### Scenario: Flop-OOP-08 チェックレイズ（強ハンド + 高 B）

```
Given  OOP がフロップをチェックし、IP から CBet を受けた
  And  HS ≥ 70（セット、2ペア、強オーバーペア等）
  And  B ≥ 58（ドロー多・ポラリゼーション有利ボード）
When   アクションを決定する
Then   チェックレイズを実行する
  And  サイズ: 通常 pot の 2.5-3x
  And  目的: バリューとドロー保護を兼ねる
```

例: hand=7s7d, board=7h9s2c → HS=85(セット), B=55 → B<58 のためフラットコール推奨
例: hand=9h9d, board=9s8h5h → HS=85(セット), B=58(rainbow_Q境界) → CR 候補

---

### Scenario: Flop-OOP-09 チェックレイズブラフ（ナッツブロッカー保有）

```
Given  OOP がフロップをチェックし、IP から CBet を受けた
  And  HS < 35（ミディアム以下のハンド）
  And  ナッツブロッカーを保有している（例: ナッツフラッシュドロー Aスーツ等）
  And  B ≥ 58
When   アクションを決定する
Then   ブラフチェックレイズを実行することができる
  And  条件: ブロッカーにより相手のナッツ保有確率が低下している場合に優位
  And  サイズ: pot の 2.5x 程度
```

例: hand=AhJd, board=Kh9h4c → HS=25(Air+BDFD), Ah でフラッシュブロック → BR候補（B=55<58 は不可、B≥58 時のみ）

---

### Scenario: Flop-境界値-01 HS=65 の CBet 判断（T1/T2 境界）

```
Given  IP が CBet 権利を保有
  And  HS = 65（TPTK 境界: T1 の下限）
  And  B = 50（2tone）
When   CBet 判断をする
Then   T1 として扱い CBet を実行する（HS ≥ 65 条件を満たすため）
```

---

### Scenario: Flop-境界値-02 HS=20 かつ B=58 の CBet 判断（T2/B=58 境界）

```
Given  IP が CBet 権利を保有
  And  HS = 20（T2 下限）
  And  B = 58
When   CBet 判断をする
Then   T2 かつ B ≥ 58 を満たすため CBet を実行する
```

---

### Scenario: Flop-境界値-03 HS=20 かつ B=57 の場合（T2 だが B 不足）

```
Given  IP が CBet 権利を保有
  And  HS = 20（T2 下限）
  And  B = 57（B < 58）
When   CBet 判断をする
Then   チェックする（T2 だが B < 58 のため CBet 不可）
```

---

## Turn

### Turn Tag リファレンス（優先順位順）

| タグ  | 条件                                           | 優先順位 |
|------|------------------------------------------------|---------|
| PB   | ターンカードのランクがフロップのいずれかと同じ    | 1 (最高) |
| SC   | ターンカードで「1枚ホールカード完成」直線窓が新生  | 2       |
| FC   | ターンカードでボード同スーツが 3 枚目             | 3       |
| OC   | ターンカードがフロップ最高ランクより高い           | 4       |
| blank| 上記なし                                        | 5 (最低) |

### GTO 実測値（参考）

| ターンタグ | IP バレル率 |
|-----------|------------|
| PB        | 96%        |
| OC        | 84%        |
| blank     | 83%        |
| SC        | 72%        |
| FC        | 68%        |

---

### Scenario: Turn-IP-01 PB ターン（ペアボード）での広バレル

```
Given  IP がフロップ CBet 後にターンを迎えた（またはフロップチェックバック後）
  And  ターンカードのランクがフロップのいずれかと同じ（PB タグ）
  And  HS ≥ 20（T2 以上、または T3 も含む）
When   ターンアクションを決定する
Then   バレル（ベット）を実行する
  And  サイズ: 33% pot（デフォルト）
  And  理由: PB でボード上のペアが強化 → IP のトリップス・フルハウスレンジが強く OOP は守備困難
  And  GTO 実測バレル率 96% を反映した積極バレル
```

例: hand=AsKd, board=Kc9s3d, turn=9h(PB) → HS=65(2ペア), HS≥20 → バレル 33%
例: hand=7h6s, board=Qs5d3c, turn=Qh(PB) → HS=20(Air) → PB なのでバレル可

---

### Scenario: Turn-IP-02 SC ターン（ストレート完成危機）での慎重バレル

```
Given  IP がターンを迎えた
  And  ターンカードで「1枚ホールカード完成」ストレート窓が新生（SC タグ）
  And  HS ≥ 65（T1 のみ）
When   ターンアクションを決定する
Then   バレルを実行する
  And  サイズ: 33% pot
  And  理由: SC はストレート完成リスクが高く、IP は強ハンドのみでバレル継続
```

例: hand=AhKh, board=Js8d4c, turn=7s(SC: 8-7-4の直線窓新生想定) → HS=65 → バレル
例: hand=9h8d, board=Js8d4c, turn=7s(SC) → HS=38(セカンドペア), HS<65 → チェック

---

### Scenario: Turn-IP-03 SC ターンで T2 以下によるチェックバック

```
Given  IP がターンを迎えた
  And  ターンカードが SC タグ
  And  HS < 65（T2 または T3）
When   ターンアクションを決定する
Then   チェックバックする
  And  理由: SC ターンは OOP のドロー完成・ストレートリスクが高く、T1 未満ではバレル損失
```

例: hand=KhQd, board=Jh9d5c, turn=8s(SC) → HS=50(TPWK), HS<65 → チェックバック

---

### Scenario: Turn-IP-04 FC ターン（フラッシュ完成ターン）での慎重バレル

```
Given  IP がターンを迎えた
  And  ターンカードでボード同スーツが 3 枚目（FC タグ）
  And  HS ≥ 65（T1 のみ）
When   ターンアクションを決定する
Then   バレルを実行する
  And  サイズ: 33% pot
  And  理由: FC はフラッシュ完成リスクが高く、強ハンドのみでプレッシャーを継続
```

例: hand=AsKs, board=Qs9d3h, turn=9s(PB 優先: ランク重複) → PB で判断（優先順位注意）
例: hand=AcKd, board=Qh8h4h, turn=2h(FC) → HS=65(TPTK想定) → FC バレル 33%

---

### Scenario: Turn-IP-05 FC ターンで T2 以下によるチェックバック

```
Given  IP がターンを迎えた
  And  ターンカードが FC タグ
  And  HS < 65
When   ターンアクションを決定する
Then   チェックバックする
  And  理由: フラッシュ完成ボードで弱ハンドのバレルは OOP のフラッシュ完成に対し無力
```

例: hand=Kh9d, board=Qh8h4h, turn=2h(FC) → HS=55(TPMK), HS<65 → チェックバック

---

### Scenario: Turn-IP-06 OC ターン（オーバーカード落下）での通常バレル

```
Given  IP がターンを迎えた
  And  ターンカードがフロップ最高ランクより高い（OC タグ）
  And  HS ≥ 20（T1 または T2）
When   ターンアクションを決定する
Then   バレルを実行する
  And  サイズ: 33% pot
  And  GTO 実測バレル率 84%
```

例: hand=AhJd, board=Ts8c3d, turn=Qs(OC) → HS=65(TPTK 変化時), バレル 33%

---

### Scenario: Turn-IP-07 blank ターンでの通常バレル

```
Given  IP がターンを迎えた
  And  ターンカードがいずれのタグにも該当しない（blank タグ）
  And  HS ≥ 20（T1 または T2）
When   ターンアクションを決定する
Then   バレルを実行する
  And  サイズ: 33% pot
  And  GTO 実測バレル率 83%
```

例: hand=KhKd, board=Kc9s3d, turn=2c(blank) → HS=85(セット), バレル 33%

---

### Scenario: Turn-IP-08 PB ターンで HS ≥ 80 の大サイズ選択肢

```
Given  IP がターンを迎えた
  And  ターンカードが PB タグ
  And  HS ≥ 80（フルハウス・クワッズ等）
When   ターンアクションを決定する
Then   33% pot ベットを基本とし、75% pot ベットも選択可能
  And  理由: 超強ハンドでポット最大化を図る場合は大サイズを選択
```

例: hand=9d9s, board=9h3c3d, turn=3s(PB) → HS=90+(フルハウス) → 75% pot も選択肢

---

### Scenario: Turn-OOP-01 vs バレル 33%: HS < 20 のフォールド（通常ボード）

```
Given  OOP がターンチェック後に IP から 33% ベットを受けた
  And  ターンタグ補正なし（OC または blank）
  And  HS < 20
When   フォールド閾値を判定する
Then   フォールドする
```

例: hand=7h6d, board=As9c3d, turn=2s(blank) → HS=15(Air), vs 33% → フォールド

---

### Scenario: Turn-OOP-02 vs バレル 33%: HS ≥ 20 のコール（通常ボード）

```
Given  OOP がターンチェック後に IP から 33% ベットを受けた
  And  ターンタグ補正なし
  And  HS ≥ 20
When   フォールド閾値を判定する
Then   コールする
```

例: hand=Ah7d, board=As9c3d, turn=2s(blank) → HS=50(TPWK), vs 33% → コール

---

### Scenario: Turn-OOP-03 vs バレル 75%: HS < 40 のフォールド（通常ボード）

```
Given  OOP がターンチェック後に IP から 75% ベットを受けた
  And  ターンタグ補正なし
  And  HS < 40
When   フォールド閾値を判定する
Then   フォールドする
```

例: hand=8h7d, board=As9c3d, turn=2s → HS=30(セカンドペア弱), vs 75% → フォールド

---

### Scenario: Turn-OOP-04 vs バレル 75%: HS ≥ 40 のコール（通常ボード）

```
Given  OOP がターンチェック後に IP から 75% ベットを受けた
  And  ターンタグ補正なし
  And  HS ≥ 40
When   フォールド閾値を判定する
Then   コールする
```

例: hand=KhQd, board=As9c3d, turn=2s → HS=42(セカンドペア良), vs 75% → コール

---

### Scenario: Turn-OOP-05 PB ターン補正による守備閾値引き下げ（-10）

```
Given  OOP が IP のターンバレルを受けた
  And  ターンタグが PB
When   フォールド閾値を算出する
Then   ベースライン閾値から -10 して判定する
  And  理由: PB ターンで IP は HS≥20（T2/Air 含む広レンジ）でバレル → IP ベット中のブラフ比率が高い
            → OOP は MDF を保つためより多くコールする必要 → フォールド閾値が下がる
  And  注意: IP はナッツ（FH/trips）も多く持つが、同時にブラフも多い（GTO バレル率 96%）
            → OOP 視点では閾値を下げてコール範囲を広げるのが正解
```

例: vs 33% ベースライン=20 → PB 補正後=10 → HS ≥ 10 でコール
例: hand=3h2d, board=9s9d5c, turn=5h(PB) → HS=15(ボトムペア弱) → 補正後閾値 10 → コール（15≥10）

---

### Scenario: Turn-OOP-06 SC/FC ターン補正による守備閾値引き上げ（+5）

```
Given  OOP が IP のターンバレルを受けた
  And  ターンタグが SC または FC
When   フォールド閾値を算出する
Then   ベースライン閾値に +5 して判定する
  And  理由: IP は T1 主体でのみバレル → OOP はより強いハンドが必要
```

例: vs 33% ベースライン=20 → SC/FC 補正後=25 → HS < 25 でフォールド
例: hand=Kh7d, board=Jh9d5c, turn=8s(SC) → HS=20(セカンドペア弱), 補正後 25 → フォールド（20<25）

---

### Scenario: Turn-OOP-07 優先順位の競合例（PB vs FC の優先）

```
Given  ターンカードのランクがフロップのいずれかと同じ（PB 条件）
  And  かつターンカードでボード同スーツが 3 枚目（FC 条件）も同時に成立
When   ターンタグを決定する
Then   PB を優先して採用する（PB > SC > FC の優先順位）
  And  フォールド閾値は PB の補正（-10）を適用する
```

例: board=Kh9s4h, turn=Kh（既出ランクかつ 3 枚目スーツ） → PB 優先

---

### Scenario: Turn-境界値-01 HS=65 かつ SC タグ

```
Given  IP がターンを迎えた
  And  ターンタグが SC
  And  HS = 65（T1 下限）
When   ターンアクションを決定する
Then   バレルを実行する（HS ≥ 65 を満たすため）
```

---

### Scenario: Turn-境界値-02 HS=64 かつ SC タグ

```
Given  IP がターンを迎えた
  And  ターンタグが SC
  And  HS = 64（T1 を 1 下回る）
When   ターンアクションを決定する
Then   チェックバックする（HS < 65 のため SC ではバレル不可）
```

---

### Scenario: Turn-境界値-03 HS=20 かつ PB タグ

```
Given  IP がターンを迎えた
  And  ターンタグが PB
  And  HS = 20（T2 下限）
When   ターンアクションを決定する
Then   バレルを実行する（PB は HS ≥ 20 でバレル可）
```

---

## River

### River Tag リファレンス（ランアウト判断用、優先順位順）

| タグ  | 条件                                             | 優先順位 |
|------|--------------------------------------------------|---------|
| PB   | リバーカードのランクがターンボード（4枚）のいずれかと同じ | 1 (最高) |
| SC   | リバーカードで「1枚ホールカード完成」直線窓が新生         | 2       |
| FC   | リバーカードでボード同スーツが 4 枚目                    | 3       |
| OC   | リバーカードがターンボード最高ランクより高い               | 4       |
| blank| 上記なし                                           | 5 (最低) |

### River Board Type リファレンス（OOP リード判断用）

| ボードタイプ | 条件                                              |
|------------|---------------------------------------------------|
| PB         | 5 枚ボードにペアあり                               |
| FC         | 同スーツ 4 枚以上                                   |
| SC         | `_count_straight_windows(ranks, max_hole=2) >= 3` |
| blank      | 上記なし                                           |

### River VMB バケット

| バケット | HS 範囲 | 説明          |
|---------|---------|---------------|
| V       | ≥ 70    | バリューハンド |
| M+      | 55-69   | ミディアム強   |
| M-      | 35-54   | ミディアム弱   |
| B       | < 35    | ブラフゾーン   |

### GTO 実測値（参考）

- IP TPTK(HS=65) ベット率: blank=62-99%, OC=42%, SC≈0%, PB=0%
- セット(HS=85-90) ベット率: blank=80%, SC/OC=68-83%, PB=50%
- OOP donk 率: SC=46-53%, FC=28%, PB=16-18%, blank=15-25%

---

### Scenario: River-IP-01 blank ランアウトでのミディアム以上バリューベット

```
Given  IP がリバーを迎えた
  And  river_tag が blank
  And  HS ≥ 55（M+ 以上）
When   リバーアクションを決定する
Then   ベットする
  And  サイズ: board_score ≥ 83 なら 100% pot、それ以外は 50% pot
  And  GTO 実測ベット率 62-99%（TPTK 相当）
```

例: hand=AsKs, board=Kd9c3h, turn=2d, river=7c(blank) → HS=65(TPTK), HS≥55 → ベット 50%

---

### Scenario: River-IP-02 blank ランアウトで M- 以下のチェック

```
Given  IP がリバーを迎えた
  And  river_tag が blank
  And  HS < 55
When   リバーアクションを決定する
Then   チェックする
```

例: hand=Ah7d, board=Kd9c3h, turn=2d, river=7c(blank) → HS=42(セカンドペア), HS<55 → チェック

---

### Scenario: River-IP-03 OC ランアウトでの強ハンドベット

```
Given  IP がリバーを迎えた
  And  river_tag が OC
  And  HS ≥ 60
When   リバーアクションを決定する
Then   ベットする
  And  サイズ: board_score ≥ 83 なら 100% pot、それ以外は 50% pot
  And  GTO 実測ベット率: TPTK(65) で 42%、セット(85)で 68-83%
```

例: hand=AsKs, board=Kd9c3h, turn=2d, river=Ah(OC) → HS=72(2ペア), HS≥60 → ベット 50%

---

### Scenario: River-IP-04 OC ランアウトで HS < 60 のチェック

```
Given  IP がリバーを迎えた
  And  river_tag が OC
  And  HS < 60
When   リバーアクションを決定する
Then   チェックする
  And  理由: OC で IP のバリューレンジが強化され OOP のブラフキャッチ率が上がる
```

例: hand=QhJd, board=Kd9c3h, turn=2d, river=Ah(OC) → HS=50(TPWK相当) → チェック

---

### Scenario: River-IP-05 SC ランアウトでの T1 限定ベット

```
Given  IP がリバーを迎えた
  And  river_tag が SC
  And  HS ≥ 70（V バケット）
When   リバーアクションを決定する
Then   ベットする
  And  サイズ: 50% pot（通常ボード）
  And  GTO 実測ベット率: TPTK(65) ≈ 0% ← SC では TPTK でもベット不可に近い
```

例: hand=AsAs, board=Kd9c3h, turn=8d, river=7s(SC) → HS=80(オーバーペア強) → ベット可
例: hand=AsKs, board=Kd9c3h, turn=8d, river=7s(SC) → HS=65(TPTK), HS<70 → チェック

---

### Scenario: River-IP-06 SC ランアウトで HS < 70 のチェック

```
Given  IP がリバーを迎えた
  And  river_tag が SC
  And  HS < 70
When   リバーアクションを決定する
Then   チェックする
  And  理由: ストレート完成ボードでは OOP がストレートを保有しやすく、IP の M+以下はバリューベット損
```

例: hand=AsKs, board=Jd9c4h, turn=8d, river=7s(SC) → HS=65(TPTK), HS<70 → チェック

---

### Scenario: River-IP-07 FC ランアウトでの T1 限定ベット

```
Given  IP がリバーを迎えた
  And  river_tag が FC
  And  HS ≥ 70
When   リバーアクションを決定する
Then   ベットする
  And  サイズ: 50% pot
```

例: hand=8h8d, board=Qs8s4h, turn=3h, river=5s(FC) → HS=85(セット), フラッシュなし → HS≥70 → ベット 50%
例: hand=AsKs, board=Qs8s4h, turn=3h, river=5s(FC) → HS=90+(ナッツフラッシュ) → HS≥70 → ベット 50%
例: hand=2h2d, board=Qs8s4h, turn=3h, river=5s(FC) → HS=30(ボトムペア), フラッシュなし → HS<70 → チェック
<!-- ※ AsKs は Qs8s4h+3h+5s で 5 枚スペードとなりナッツフラッシュになる点に注意 -->

---

### Scenario: River-IP-08 PB ランアウトでの超強ハンドのみベット

```
Given  IP がリバーを迎えた
  And  river_tag が PB
  And  HS ≥ 80
When   リバーアクションを決定する
Then   ベットする
  And  サイズ: board_score ≥ 83 なら 100% pot、それ以外は 50% pot
  And  GTO 実測ベット率: セット(85) で 50%（PB ボードは OOP もフルハウス候補あり）
```

例: hand=9d9s, board=9h7c3d, turn=7h(PB), river=3c(PB) → HS=90+(フルハウス) → ベット 100%（paired_high時）

---

### Scenario: River-IP-09 PB ランアウトで HS < 80 のチェック

```
Given  IP がリバーを迎えた
  And  river_tag が PB
  And  HS < 80
When   リバーアクションを決定する
Then   チェックする
  And  理由: PB（ペアード）ボードでは OOP がフルハウスを持つ可能性があり、M+/M- は危険
  And  GTO 実測: TPTK(65) ベット率 ≈ 0%
```

例: hand=AsKd, board=Kc9s3d, turn=7h, river=9c(PB) → HS=65(TPTK) → HS<80 → チェック

---

### Scenario: River-IP-10 paired_high ボードの 100% pot ベット

```
Given  IP がリバーでベットする判断になっている
  And  board_score ≥ 83（paired_high ボード）
When   サイズを決定する
Then   100% pot ベット
  And  理由: ペアドボードでバリューレンジが絞られるためポーラーなサイジングが最適
```

例: hand=KhKd, board=KcQs3d, turn=5h, river=2c → board_score=83, HS=80+ → 100% pot

---

### Scenario: River-OOP-01 SC/FC ボードでのリードベット（donk）

```
Given  OOP がリバーを迎えてチェックするかリードするかを選択する
  And  `classify_river_board()` が SC または FC を返す
  And  HS ≥ 70（V バケット）
When   リバーアクションを決定する
Then   LEAD（ドンクベット）を実行する
  And  サイズ: 50% pot
  And  GTO 実測 donk 率: SC=46-53%, FC=28%
```

例: hand=AsQs, board=Js8s4d, turn=2s, river=6s(FC完成) → HS=70(フラッシュ完成+) → LEAD 50%
例: hand=KhJd, board=Qh9d5c, turn=8c, river=7h(SC 直線完成) → HS=72(ストレート) → LEAD 50%

---

### Scenario: River-OOP-02 PB または blank ボードでのチェック

```
Given  OOP がリバーを迎えてチェックするかリードするかを選択する
  And  `classify_river_board()` が PB または blank を返す
  And  HS = 任意
When   リバーアクションを決定する
Then   チェックする（LEAD しない）
  And  GTO 実測 donk 率: PB=16-18%, blank=15-25% → 低率のため基本チェック
```

例: hand=AsKd, board=Kh9d3c, turn=9s, river=2c(PB ボード確定) → チェック

---

### Scenario: River-OOP-03 SC ボードだが HS < 70 のチェック

```
Given  OOP がリバーを迎えた
  And  `classify_river_board()` が SC を返す
  And  HS < 70
When   リバーアクションを決定する
Then   チェックする（LEAD しない）
  And  理由: SC ボードでも HS < 70 ではバリューリードが不十分
```

例: hand=KhQd, board=Jh9d5c, turn=8c, river=7h(SC) → HS=55(TPMK) → チェック

---

### Scenario: River-OOP-04 vs IP ベット 33%: HS < 35 のフォールド（通常）

```
Given  OOP がリバーチェック後に IP から 33% ベットを受けた
  And  river_tag 補正なし（OC または blank）
  And  HS < 35
When   フォールド閾値を判定する
Then   フォールドする
```

例: hand=7h6d, board=As9c3d, turn=2h, river=8c(blank) → HS=20(Air) → フォールド

---

### Scenario: River-OOP-05 vs IP ベット 33%: HS ≥ 35 のコール

```
Given  OOP がリバーチェック後に IP から 33% ベットを受けた
  And  river_tag 補正なし
  And  HS ≥ 35
When   フォールド閾値を判定する
Then   コールする
```

例: hand=8h7d, board=As9c3d, turn=2h, river=8c(blank) → HS=38(セカンドペア) → コール

---

### Scenario: River-OOP-06 vs IP ベット 50%: HS < 42 のフォールド（通常）

```
Given  OOP がリバーチェック後に IP から 50% ベットを受けた
  And  river_tag 補正なし
  And  HS < 42
When   フォールド閾値を判定する
Then   フォールドする
```

例: hand=Kh8d, board=As9c3d, turn=2h, river=7c(blank) → HS=38 → HS<42 → フォールド

---

### Scenario: River-OOP-07 vs IP ベット 75%: HS < 50 のフォールド（通常）

```
Given  OOP がリバーチェック後に IP から 75% ベットを受けた
  And  river_tag 補正なし
  And  HS < 50
When   フォールド閾値を判定する
Then   フォールドする
```

例: hand=Ks8d, board=Ah9c3d, turn=2h, river=7c → HS=42 → HS<50 → フォールド

---

### Scenario: River-OOP-08 vs IP ベット 100%: HS < 55 のフォールド（通常）

```
Given  OOP がリバーチェック後に IP から 100% ベットを受けた
  And  river_tag 補正なし
  And  HS < 55
When   フォールド閾値を判定する
Then   フォールドする
```

例: hand=Kh9d, board=As3d2c, turn=7h, river=8c(blank) → HS=50(TPWK) → HS<55 → フォールド

---

### Scenario: River-OOP-09 PB river_tag 補正（+10）による守備閾値引き上げ

```
Given  OOP が IP のリバーベットを受けた
  And  river_tag が PB
When   フォールド閾値を算出する
Then   ベースライン閾値に +10 して判定する
  And  理由: PB ボードで IP はトリップス・フルハウスの強レンジでのみベット → より強い手が必要
```

例: vs 50% ベースライン=42 → PB 補正後=52 → HS < 52 でフォールド
例: hand=AhKd, board=Kc9s3d, turn=7h, river=9c(PB) → HS=50(TPWK) → 補正後 52 → フォールド

---

### Scenario: River-OOP-10 SC river_tag 補正（-5）による守備閾値引き下げ

```
Given  OOP が IP のリバーベットを受けた
  And  river_tag が SC
When   フォールド閾値を算出する
Then   ベースライン閾値から -5 して判定する
  And  理由1（レンジ強化）: SC ボードでは OOP（BB）のレンジにストレート完成が多い
            → OOP 全体のレンジが強い → 同じ HS でも相対的強度が高く守備容易
  And  理由2（ポーラー化）: IP は HS≥70 のみでバレル（中間値ハンドはチェック）
            → IP のバレルレンジがナッツとブラフにポーラー化 → ブラフ比率が高まる
            → OOP の BC コール価値が高まる（River-OOP-13 参照）
```

例: vs 50% ベースライン=42 → SC 補正後=37 → HS ≥ 37 でコール可能
例: hand=KhJd, board=Jh9d5c, turn=8c, river=7h(SC) → HS=42(セカンドペア) → 補正後 37 → コール

---

### Scenario: River-OOP-11 FC river_tag 補正（-5）による守備閾値引き下げ

```
Given  OOP が IP のリバーベットを受けた
  And  river_tag が FC
When   フォールド閾値を算出する
Then   ベースライン閾値から -5 して判定する
  And  理由1（レンジ強化）: FC ボードでは OOP（BB）のレンジにフラッシュ完成が多い（スーテッドハンド多）
            → OOP 全体のレンジが強い → 同じ HS でも相対的強度が高く守備容易
  And  理由2（ポーラー化）: IP は HS≥70 のみでバレル（中間値ハンドはチェック）
            → IP のバレルレンジがナッツとブラフにポーラー化 → ブラフ比率が高まる
            → OOP の BC コール価値が高まる（River-OOP-13 参照）
```

例: vs 50% ベースライン=42 → FC 補正後=37 → HS ≥ 37 でコール
例: hand=Ks9d, board=As8s4h, turn=3h, river=5s(FC) → HS=42(セカンドペア) → 補正後 37 → コール

---

### Scenario: River-OOP-12 OC river_tag 補正（+5）による守備閾値引き上げ

```
Given  OOP が IP のリバーベットを受けた
  And  river_tag が OC
When   フォールド閾値を算出する
Then   ベースライン閾値に +5 して判定する
  And  理由: OC で IP のトップペア・2ペア等の強化 → ブラフ比率低下 → OOP はより強い手が必要
```

例: vs 50% ベースライン=42 → OC 補正後=47 → HS < 47 でフォールド
例: hand=QhJd, board=Kd9c3h, turn=5d, river=Ah(OC) → HS=42 → 補正後 47 → フォールド

---

### Scenario: River-OOP-13 ブラフキャッチャー（M-: SC/FC ボードでのコール）

```
Given  OOP が IP のリバーベットを受けた
  And  HS が 35-54（M- バケット）
  And  river_tag が SC または FC
  And  IP のベットレンジのブラフ比率がポットオッズを超えている
When   ブラフキャッチャーとしてコールするかを判定する
Then   コールする（ブラフキャッチャー）
  And  理由: SC/FC ボードで IP レンジがポーラー化 → ブラフ比率が高まり BC コールがEV+
  And  対象ベットサイズ: 50% 以下
```

例: hand=Ah7d, board=Jh9h5c, turn=2h, river=8h(FC) → HS=42(セカンドペア) → M- + FC → BC コール検討

---

### Scenario: River-OOP-14 ブラフキャッチャー条件不成立（M- だが PB/blank）

```
Given  OOP が IP のリバーベットを受けた
  And  HS が 35-54（M- バケット）
  And  river_tag が PB または blank
When   ブラフキャッチャーとしてコールするかを判定する
Then   フォールドする（ブラフキャッチャー条件不成立）
  And  理由: PB/blank では IP のポーラー化が弱く、ブラフ比率が BC コール閾値を下回る
```

例: hand=Ah7d, board=Kd9c3h, turn=5d, river=2c(blank) → HS=42, M- + blank → フォールド（通常ベースライン適用）

---

### Scenario: River-境界値-01 HS=70 かつ SC river_tag のベット判断

```
Given  IP がリバーを迎えた
  And  river_tag が SC
  And  HS = 70（V バケット下限、SC ベット閾値境界）
When   リバーアクションを決定する
Then   ベットする（HS ≥ 70 を満たすため）
```

---

### Scenario: River-境界値-02 HS=69 かつ SC river_tag のチェック

```
Given  IP がリバーを迎えた
  And  river_tag が SC
  And  HS = 69（V バケット 1 下回る）
When   リバーアクションを決定する
Then   チェックする（HS < 70 のため SC ではベット不可）
```

---

### Scenario: River-境界値-03 HS=55 かつ blank river_tag のベット判断

```
Given  IP がリバーを迎えた
  And  river_tag が blank
  And  HS = 55（M+ 下限、blank ベット閾値境界）
When   リバーアクションを決定する
Then   ベットする（HS ≥ 55 を満たすため）
```

---

### Scenario: River-境界値-04 HS=54 かつ blank river_tag のチェック

```
Given  IP がリバーを迎えた
  And  river_tag が blank
  And  HS = 54（M- 上限）
When   リバーアクションを決定する
Then   チェックする（HS < 55 のため blank でもベット不可）
```

---

### Scenario: River-境界値-05 vs 50% ベット、PB 補正後の境界（HS=52）

```
Given  OOP が IP の 50% リバーベットを受けた
  And  river_tag が PB
  And  HS = 52（補正後閾値 52 の境界値）
When   フォールド閾値を判定する（vs 50% ベースライン=42、PB+10 で=52）
Then   HS = 52 → コール（HS ≥ 52 を満たすため）
```

---

### Scenario: River-境界値-06 vs 50% ベット、PB 補正後 HS=51 のフォールド

```
Given  OOP が IP の 50% リバーベットを受けた
  And  river_tag が PB
  And  HS = 51
When   フォールド閾値を判定する
Then   フォールドする（HS < 52 のため）
```

---

## 付録: river_tag 別 IP ベット閾値早見表

| river_tag | IP ベット閾値 |
|-----------|-------------|
| blank     | HS ≥ 55     |
| OC        | HS ≥ 60     |
| SC        | HS ≥ 70     |
| FC        | HS ≥ 70     |
| PB        | HS ≥ 80     |

## 付録: OOP フォールド閾値（river_tag 補正後）

| ベットサイズ | ベースライン | PB (+10) | SC (-5) | FC (-5) | OC (+5) | blank (0) |
|-----------|-----------|---------|--------|--------|--------|----------|
| 33%       | 35        | 45      | 30     | 30     | 40     | 35       |
| 50%       | 42        | 52      | 37     | 37     | 47     | 42       |
| 75%       | 50        | 60      | 45     | 45     | 55     | 50       |
| 100%      | 55        | 65      | 50     | 50     | 60     | 55       |

## 付録: ターン OOP フォールド閾値（turn_tag 補正後）

| ベットサイズ | ベースライン | PB (-10) | SC (+5) | FC (+5) | OC (0) | blank (0) |
|-----------|-----------|---------|--------|--------|--------|----------|
| 33%       | 20        | 10      | 25     | 25     | 20     | 20       |
| 75%       | 40        | 30      | 45     | 45     | 40     | 40       |

## 付録: フロップ OOP フォールド閾値（ボードタイプ補正後）

| ベットサイズ | ベースライン | ペア (-10) | 2tone (+5) | mono (-5) |
|-----------|-----------|----------|----------|----------|
| 33%       | 15        | 5        | 20       | 10       |
| 75%       | 35        | 25       | 40       | 30       |
