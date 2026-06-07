# 2026-06-07 Pre-3-Volume Restructure Archive

3 巻構成 (preflop / postflop / tell+exploit) 移行に伴い、4 巻構成時代の不要な章・設計書をここに集約。

## 移行内容

### 4 巻 → 3 巻構成決定 (2026-06-07)
- UDG v2 で Cash 100bb と MTT chipEV (100bb) が完全同一公式と判明
- 旧 Vol2/Vol3 の内容が 8 割重複 → 統合書 1 冊で十分
- ICM/PKO postflop は GTO Wizard API tier 制限で取得不可、将来別冊で対応

### 保管対象

| ディレクトリ / ファイル | 内容 | 数 |
|---------------------|------|---:|
| `specs/` | 旧 vol2 / vol3 / vol4 / vol5 specs (UDG で superseded) | 109 |
| `outlines/` | 旧 章 outline (全 vol2/3) | 42 |
| `scripts-toc/` | 旧 toc draft (vol2_vol3 / vol4_vol5) | 2 |
| `scripts-generate/tier1_generator.py` | 旧 tier1 generator (vol2 一括出力用) | 1 |
| `postflop-tournament/` | 旧 vol6 (tournament) findings | 1 dir |
| `BOOK_DESIGN_2026-06-01.md` | 旧 Vol2/Vol3 設計書 (UDG v2 で吸収済) | 1 |
| `RESTRUCTURE_PLAN.md` | 4 巻 → 3 巻 restructure plan (今回完了) | 1 |
| `chatgpt_review_vol2_vol5_*.md` | 旧 vol レビュー 3 ラウンド | 3 |

## 現行構成 (2026-06-07 以降)

```
poker-books/
├── vol1-preflop/   Vol1: プリフロップ完全版 (Cash+MTT統合)
├── vol2-postflop/  Vol2: ポストフロップ完全版 (UDG v2)
└── vol3-tell/      Vol3: エクスプロイト・テル (旧 Vol4)
```

## 関連メモリ

- `project_vol2_postflop_udg.md` — 3 巻構成決定 + UDG v2 概要
- `project_postflop_3rule_formula.md` — 旧 v9b/v10/v15 (UDG v2 で吸収)
- `project_probe_priority_findings.md` — UDG 設計のためのデータ収集
- `feedback_book_writing_workflow` — 章原稿は generator 経由必須
