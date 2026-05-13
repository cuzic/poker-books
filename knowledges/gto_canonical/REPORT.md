# pot=10 統一 GTO 検証レポート

生成日: 2026-05-13（中間報告: 44/68 シナリオ完了）
ワーカー: 残 24 シナリオ実行中

---

## 要約

| 項目 | GTO 実測 | 現 calc.py | 判定 |
|------|---------|-----------|------|
| IP CBet 頻度（全体） | 92.6% | T1/T2/T3 閾値で判断 | ✅ 設計思想OK（閾値で制御） |
| **CBet サイズ（dry/rainbow）** | **33%: 78%** | **デフォルト 75%** | **⚠️ 要修正** |
| OOP fold vs 33% | 26.9% | 閾値 HS<15 | ✅ MDF 25% に合致 |
| OOP fold vs 75% | 45.2% | 閾値 HS<35 | ✅ MDF 43% に合致 |

**主な発見: CBet サイズのデフォルトが GTO と逆転している**
GTO は dry rainbow board で 33% を 78% の頻度で使用するが、現 `calc_cbet_size()` は 75% をデフォルトにしている。

---

## 1. IP CBet 頻度

平均 IP CBet%: **92.6%**（44 シナリオ中間集計）

### シナリオ種別

| 種別 | avg CBet% | n | 説明 |
|------|----------|---|------|
| acc30（accuracy30 ボード） | 96.3% | 12 | dry 代表 |
| rr（rainbow→rainbow） | 90.8% | 30 | dry メイン |
| cc（check-check ライン） | 96.7% | 2 | サブサンプル |

**解釈**: GTO は pot=10 の SRP dry board でほぼ全ハンドで CBet する。これは「range bet」戦略であり、Air（T3）も含め 93.7% で CBet する。

書籍の T3 閾値（B≥62）は「どのハンドをブラフとして混ぜるか」の基準であり、全体頻度とは別の概念。**設計思想は正しい**。

---

## 2. ハンドカテゴリ別 CBet%（GTO 実測）

| カテゴリ | GTO 実測% | 備考 |
|---------|---------|------|
| オーバーペア | 90.2% | dry board では ほぼ全 CBet |
| トップペア | 93.5% | dry board での range-bet |
| Air (T3) | 93.7% | dry board では Air も CBet |

**注意**: GTO の Air CBet 93.7% は dry rainbow board での値。wet board や connected board では Air CBet 頻度は大幅に低下する（本シナリオは dry 中心のため高値）。

---

## 3. CBet サイズ分析【要修正】

### rainbow/dry ボード（rr プレフィックス 30 件）

| サイズ | GTO 平均% | GTO 構成比 |
|-------|---------|---------|
| **33% pot** | **71.0%** | **78.2%** |
| 75% pot | 19.8% | 21.8% |

### 全シナリオ平均

| サイズ | GTO 平均% | GTO 構成比 |
|-------|---------|---------|
| **33% pot** | **69.4%** | **75.0%** |
| 75% pot | 23.2% | 25.0% |

**現 calc_cbet_size() の問題点**:
```python
def calc_cbet_size(texture_label: str) -> int:
    if texture_label in ("paired_high", "mono"):
        return 50
    return 75  # ← GTO では dry board でほぼ使わない
```

**推奨修正**:
```python
def calc_cbet_size(texture_label: str) -> int:
    if texture_label in ("mono",):
        return 75   # モノトーン: ドローへのチャージ
    if texture_label in ("paired_high",):
        return 50   # ペアボード: 中サイズ
    if texture_label in ("2tone", "connected"):
        return 50   # wet board: ドロー意識
    return 33       # dry rainbow: GTO は 78% が 33%
```

---

## 4. OOP フォールド率（✅ 確認済み）

| ベットサイズ | GTO 実測% | MDF 理論 fold% | 差 |
|------------|---------|-------------|-----|
| vs 33% | 26.9% | 25.0% | +1.9 |
| vs 75% | 45.2% | 43.0% | +2.2 |

**判定**: OOP フォールド率は MDF 理論（1-α）と 2pt 以内で整合。
書籍の fold 閾値（HS<15 vs 33%、HS<35 vs 75%）は変更不要。

---

## 5. 書籍・calc.py への反映推奨事項

### 必須修正（⚠️）

**`calc_cbet_size()` のデフォルトを 75% → 33% に修正**
- dry rainbow: 33%（GTO 構成比 78%）
- wet 2-tone/connected: 50%（ドロー意識）
- mono: 75%（ドローへのチャージ）
- paired_high: 50%（中サイズ）

### 変更不要（✅）

- OOP fold 閾値（MDF と整合）
- T3 CBet 閾値 B≥62（wet board での bluff 頻度制御は別問題）
- T1/T2 CBet 頻度全般

### 書籍への追記推奨

- dry board では IP は 33% small CBet が GTO 均衡（range bet）
- 75% large CBet は wet board や強いバリューハンド（HS≥80）に限定
- この説明は vol3 ch05（CBet サイズ選択）に追加

---

## 6. 残 24 シナリオ完了後の再実行

```bash
cd /home/cuzic/poker-books/scripts/gcp_study_pot10
gsutil -m cp gs://poker-gto-study/pot10_study/results/*.json \
  /home/cuzic/poker-books/knowledges/gto_canonical/results/
python3 analyze_pot10.py
```

<!-- 中間レポート generated manually from partial analysis -->
<!-- Full: 44/68 scenarios as of 2026-05-13 -->
