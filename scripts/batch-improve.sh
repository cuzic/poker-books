#!/bin/bash
# 夜間バッチ処理スクリプト
# Claude CLI を使って lint チェックと修正を繰り返す
# 対象: preflop/chapters/**/*.md, flop/chapters/**/*.md

set -e

MAX_ITERATIONS=${1:-5}
SLEEP_BETWEEN=${2:-10}

echo "=== 夜間バッチ処理開始 ==="
echo "最大繰り返し回数: $MAX_ITERATIONS"
echo "開始時刻: $(date)"
echo ""

for i in $(seq 1 $MAX_ITERATIONS); do
    echo "--- イテレーション $i/$MAX_ITERATIONS ---"

    # lint チェック
    echo "lint チェック実行中..."
    if bun run lint 2>&1; then
        echo "✅ lint エラーなし。バッチ処理完了。"
        break
    fi

    echo ""
    echo "❌ lint エラーあり。Claude で修正を試みます..."
    echo ""

    # Claude CLI で修正を実行
    claude --print "
以下のタスクを実行してください：

1. bun run lint を実行してエラーを確認
2. 自動修正可能なものは bun run lint:fix で修正
3. 手動修正が必要なエラーを修正：
   - textlint エラー：文を書き換え、助詞の連続を解消
   - markdownlint エラー：フォーマットを修正
4. 修正後、再度 bun run lint で確認
5. 修正内容を簡潔に報告

対象ファイル: preflop/chapters/*.md, flop/chapters/*.md
注意:
- preflop/toc.md, flop/toc.md は対象外
- 各書籍の本文は全て対象
- 局所的に無視が必要なケースは <!-- textlint-disable ... --> / <!-- markdownlint-disable ... --> を適切に挿入
"

    echo ""
    echo "修正完了。次のイテレーションまで ${SLEEP_BETWEEN}秒 待機..."
    sleep $SLEEP_BETWEEN
done

# 最終確認
echo ""
echo "=== 最終確認 ==="
if bun run lint 2>&1; then
    echo "✅ 全ての lint エラーが解消されました"

    # 変更があればコミット
    if ! git diff --quiet preflop/chapters/ flop/chapters/; then
        echo ""
        echo "変更をコミットします..."
        git add preflop/chapters/ flop/chapters/
        git commit -m "fix: 夜間バッチ処理による lint 修正

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>"
        echo "✅ コミット完了"
    else
        echo "変更なし。コミット不要。"
    fi
else
    echo "⚠️ 一部の lint エラーが残っています"
    echo "手動での対応が必要です。"
fi

echo ""
echo "終了時刻: $(date)"
echo "=== 夜間バッチ処理終了 ==="
