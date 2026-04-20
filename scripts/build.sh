#!/usr/bin/env bash
set -euo pipefail

# Usage: build.sh <book-id>
#   book-id: preflop | flop | all
#
# Example:
#   bash scripts/build.sh preflop      # → dist/preflop/book.html
#   bash scripts/build.sh flop         # → dist/flop/book.html
#   bash scripts/build.sh all          # 両方

ROOT="/home/cuzic/poker-books"
BOOK_ID="${1:-}"

if [ -z "$BOOK_ID" ]; then
  echo "Usage: $0 <preflop|flop|all>" >&2
  exit 1
fi

build_book() {
  local id="$1"
  local src_dir="$ROOT/$id/chapters"
  local out_dir="$ROOT/dist/$id"
  local merged_md="$out_dir/book.md"
  local out_html="$out_dir/book.html"
  local book_json="$ROOT/$id/book.json"

  if [ ! -d "$src_dir" ]; then
    echo "Skip: $src_dir does not exist" >&2
    return 0
  fi

  mkdir -p "$out_dir"

  # Extract title/subtitle from book.json if available
  local title subtitle author
  if [ -f "$book_json" ]; then
    title=$(python3 -c "import json; print(json.load(open('$book_json')).get('title', ''))")
    subtitle=$(python3 -c "import json; print(json.load(open('$book_json')).get('subtitle', ''))")
    author=$(python3 -c "import json; print(json.load(open('$book_json')).get('author', ''))")
  else
    title="$id"
    subtitle=""
    author=""
  fi

  # Front matter
  cat > "$merged_md" <<EOF
---
title: "$title"
subtitle: "$subtitle"
author: "$author"
date: "$(date +%Y-%m-%d)"
lang: ja
---

EOF

  # Optional preface from $id/preface.md
  if [ -f "$ROOT/$id/preface.md" ]; then
    cat "$ROOT/$id/preface.md" >> "$merged_md"
    echo -e "\n\n\\\\newpage\n\n" >> "$merged_md"
  fi

  # Merge chapter files in alphabetical order
  for f in "$src_dir"/*.md; do
    echo "Merging: $f" >&2
    cat "$f" >> "$merged_md"
    echo -e "\n\n\\\\newpage\n\n" >> "$merged_md"
  done

  # Run pandoc
  pandoc "$merged_md" \
    --from markdown+yaml_metadata_block+table_captions+pipe_tables \
    --to html5 \
    --standalone \
    --toc \
    --toc-depth=2 \
    --self-contained \
    --metadata title="$title" \
    --css <(cat <<'CSS'
:root {
  --fg: #222;
  --bg: #fafafa;
  --accent: #3b6ea8;
  --code-bg: #f0f0f0;
  --border: #ddd;
}
* { box-sizing: border-box; }
html { font-size: 16px; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Kaku Gothic ProN", "Yu Gothic", Meiryo, sans-serif;
  color: var(--fg);
  background: var(--bg);
  max-width: 780px;
  margin: 0 auto;
  padding: 2em 1em 6em;
  line-height: 1.85;
}
header { text-align: center; margin-bottom: 3em; padding-bottom: 2em; border-bottom: 2px solid var(--accent); }
h1.title { font-size: 2em; margin-bottom: 0.3em; }
p.subtitle { font-size: 1.1em; color: #666; }
p.author { color: #888; }
h1, h2, h3, h4 { color: var(--accent); line-height: 1.4; }
h1 { font-size: 1.6em; border-bottom: 2px solid var(--accent); padding-bottom: 0.3em; margin-top: 2em; }
h2 { font-size: 1.3em; border-left: 4px solid var(--accent); padding-left: 0.6em; margin-top: 2em; }
h3 { font-size: 1.1em; margin-top: 1.5em; }
h4 { font-size: 1em; margin-top: 1.2em; }
p { margin: 0.8em 0; }
blockquote {
  border-left: 4px solid #ccc;
  background: #f5f5f5;
  padding: 0.8em 1em;
  color: #555;
  margin: 1em 0;
  border-radius: 0 4px 4px 0;
}
code {
  background: var(--code-bg);
  padding: 2px 5px;
  border-radius: 3px;
  font-family: "SF Mono", Menlo, Consolas, monospace;
  font-size: 0.9em;
}
pre {
  background: #2d2d2d;
  color: #eee;
  padding: 1em;
  border-radius: 6px;
  overflow-x: auto;
  line-height: 1.5;
}
pre code { background: transparent; color: inherit; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; font-size: 0.95em; }
th, td { border: 1px solid var(--border); padding: 0.5em 0.8em; text-align: left; }
th { background: #e8eff7; color: var(--accent); }
tr:nth-child(even) td { background: #f5f5f5; }
hr { border: 0; border-top: 1px solid var(--border); margin: 2em 0; }
a { color: var(--accent); }
#TOC { background: #fff; border: 1px solid var(--border); padding: 1.5em 2em; border-radius: 6px; margin: 2em 0; }
#TOC > ul { margin: 0; padding-left: 1.5em; }
#TOC a { color: var(--fg); text-decoration: none; }
#TOC a:hover { color: var(--accent); text-decoration: underline; }
CSS
) \
    -o "$out_html"

  echo ""
  echo "=== Build complete: $id ==="
  echo "Output: $out_html"
  echo "Size: $(du -h "$out_html" | cut -f1)"
}

case "$BOOK_ID" in
  preflop|flop)
    build_book "$BOOK_ID"
    ;;
  all)
    build_book preflop
    build_book flop
    ;;
  *)
    echo "Unknown book-id: $BOOK_ID. Use preflop | flop | all" >&2
    exit 1
    ;;
esac
