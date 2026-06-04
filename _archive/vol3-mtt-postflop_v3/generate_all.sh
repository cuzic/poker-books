#!/usr/bin/env bash
# generate_all.sh — MTTポストフロップ 全章生成スクリプト
# Usage: bash generate_all.sh
#        bash generate_all.sh specs/mtt/ch02.yaml  # single chapter

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "MTT ポストフロップ 書籍ジェネレーター"
echo "======================================="

if [ "${1:-}" != "" ]; then
    # Single chapter
    echo "Generating single chapter: $1"
    uv run "$SCRIPT_DIR/generator.py" "$1"
else
    # All chapters
    echo "Generating all chapters..."
    uv run "$SCRIPT_DIR/generator.py"
fi

echo ""
echo "Generated files:"
ls -la "$SCRIPT_DIR/chapters/"*.md | awk '{print "  " $NF " (" $5 " bytes)"}'
