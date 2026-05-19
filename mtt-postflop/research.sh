#!/usr/bin/env bash
# GTO Wizard MTT調査スクリプト
# 使い方: TOKEN=<新しいトークン> bash research.sh [phase]
# 例: TOKEN=eyJ... bash research.sh 1

set -euo pipefail

TOKEN="${TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  echo "❌ TOKEN が未設定です。GTO Wizard でログイン後、curl コマンドから Bearer トークンをコピーしてください。"
  echo "   TOKEN=eyJ... bash research.sh 1"
  exit 1
fi

OUTDIR="$(dirname "$0")/findings"
mkdir -p "$OUTDIR"

PHASE="${1:-1}"

# ── 共通関数 ──────────────────────────────────────────────

call_api() {
  local gametype="$1" depth="$2" stacks="$3" preflop="$4" flop="$5" turn="$6" river="$7" board="$8"
  curl -s "https://api.gtowizard.com/v4/solutions/spot-solution/?gametype=${gametype}&depth=${depth}&stacks=${stacks}&preflop_actions=${preflop}&flop_actions=${flop}&turn_actions=${river}&river_actions=${river}&board=${board}" \
    -H 'accept: application/json, text/plain, */*' \
    -H "authorization: Bearer ${TOKEN}" \
    -H 'origin: https://app.gtowizard.com' \
    -H 'referer: https://app.gtowizard.com/'
}

check_auth() {
  local resp
  resp=$(call_api "MTTGeneral_ICM8m200PTT3" "50" "50-50-50-50-50-50-50-50" "" "" "" "" "")
  if echo "$resp" | grep -q "AUTHENTICATION_FAILED"; then
    echo "❌ 認証失敗：トークンが無効または期限切れです"
    exit 1
  fi
  echo "✅ 認証OK"
}

# ── Phase 1: SBR別コミットライン ──────────────────────────

phase1() {
  echo "=== Phase 1: SBR別コミットライン ==="
  local OUT="$OUTDIR/phase1_commit_lines.jsonl"
  > "$OUT"

  # gametype: 8-max ICM 200players PTT3
  local GT="MTTGeneral_ICM8m200PTT3"

  # ボード (型1:ハイドライ / 型2:ハイウェット / 型4:ローウェット)
  declare -A BOARDS=(
    ["type1_K72"]="Ks7d2c"
    ["type2_Q83s"]="Qh8d3s"
    ["type4_T98s"]="Th9s8d"
  )

  # SBR別スタック設定 (BTN=hero, BB=villain, 残り6人は平均値付近)
  # スタックはBB単位。BBアンテありで SBR≈stack/2
  # depth = BTN実効スタック（BTN vs BB の小さい方）
  declare -A SBRS=(
    ["sbr30_60bb"]="60"
    ["sbr25_50bb"]="50"
    ["sbr20_40bb"]="40"
    ["sbr15_30bb"]="30"
    ["sbr10_20bb"]="20"
  )

  # preflop: BTN open 2.5BB, BB call
  # GTO Wizard のアクションエンコーディング (要確認: r=raise/bet, c=call, f=fold)
  local PF_BTN_OPEN_BB_CALL="r2.5c"

  for sbr_label in "${!SBRS[@]}"; do
    local hero_stack="${SBRS[$sbr_label]}"
    # villain (BB) も同スタック。残り6人は平均スタックとして hero_stack*0.8
    local avg=$( echo "$hero_stack * 0.8" | bc )
    local stacks="${hero_stack}-${hero_stack}-${avg}-${avg}-${avg}-${avg}-${avg}-${avg}"

    for board_label in "${!BOARDS[@]}"; do
      local board="${BOARDS[$board_label]}"
      echo -n "  [$sbr_label / $board_label] ... "

      local resp
      resp=$(call_api "$GT" "$hero_stack" "$stacks" "$PF_BTN_OPEN_BB_CALL" "" "" "" "$board")

      echo "$resp" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('OK - keys:', list(data.keys())[:5])
except:
    raw = sys.stdin.read() if sys.stdin.readable() else ''
    print('ERROR:', raw[:100])
"
      # 結果をJSONLに保存
      echo "{\"phase\":1,\"sbr\":\"$sbr_label\",\"board\":\"$board_label\",\"stacks\":\"$stacks\",\"depth\":\"$hero_stack\",\"response\":$(echo "$resp" | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin)))' 2>/dev/null || echo 'null')}" >> "$OUT"

    done
  done

  echo ""
  echo "Phase 1 完了 → $OUT"
}

# ── Phase 2: ICM補正値の定量化 ──────────────────────────

phase2() {
  echo "=== Phase 2: ICM補正値の定量化 ==="
  local OUT="$OUTDIR/phase2_icm_adjustment.jsonl"
  > "$OUT"

  # 同一ハンド・同一ボードをICM有無で比較
  # ボード: Q♠7♦2♣ (型1 ハイドライ、ニュートラル)
  local BOARD="Qs7d2c"
  local DEPTH="40"  # SBR=20固定
  local PF="r2.5c"  # BTN open, BB call

  # ICMあり (バブル近辺 = 残りプレイヤーがITMの1.15倍)
  local GT_ICM="MTTGeneral_ICM8m200PTT3"
  # Chip-EV比較用 (ICMなし) — gametypeを変える必要あり
  # ※ 実際のgametypeはGTOWizardの仕様確認後に修正
  local GT_CEV="MTTGeneral_CEV8m200PTT3"  # 仮: CEVモードが存在する場合

  for gt_label in "ICM:${GT_ICM}" "CEV:${GT_CEV}"; do
    local label="${gt_label%%:*}"
    local gt="${gt_label##*:}"

    # バブル想定スタック (8人、平均40BB、ショートスタック混在)
    local stacks="40-40-40-40-40-20-60-60"

    echo -n "  [$label / Q72 / SBR=20] ... "
    local resp
    resp=$(call_api "$gt" "$DEPTH" "$stacks" "$PF" "" "" "" "$BOARD")
    echo "$resp" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print('OK')
except: print('ERROR')
"
    echo "{\"phase\":2,\"mode\":\"$label\",\"board\":\"$BOARD\",\"depth\":\"$DEPTH\",\"response\":$(echo "$resp" | python3 -c 'import sys,json; print(json.dumps(json.load(sys.stdin)))' 2>/dev/null || echo 'null')}" >> "$OUT"
  done

  echo "Phase 2 完了 → $OUT"
}

# ── レスポンス解析ツール ──────────────────────────────────

analyze() {
  echo "=== レスポンス解析 ==="
  local FILE="${1:-$OUTDIR/phase1_commit_lines.jsonl}"
  if [[ ! -f "$FILE" ]]; then
    echo "ファイルが見つかりません: $FILE"
    exit 1
  fi
  python3 << 'PYEOF'
import sys, json

file = sys.argv[1] if len(sys.argv) > 1 else None
import os
file = file or os.path.expanduser("~/poker-books/postflop-tournament/findings/phase1_commit_lines.jsonl")

with open(file) as f:
    for line in f:
        try:
            rec = json.loads(line)
            resp = rec.get("response", {})
            if resp and isinstance(resp, dict):
                print(f"\n[{rec.get('sbr','?')} / {rec.get('board','?')}]")
                # アクション情報を抽出
                for key in ["actions", "strategy", "hands", "spots"]:
                    if key in resp:
                        print(f"  {key}: {str(resp[key])[:200]}")
        except Exception as e:
            print(f"Parse error: {e}")
PYEOF
}

# ── メイン ────────────────────────────────────────────────

echo "GTO Wizard MTT 調査スクリプト"
echo "Phase: $PHASE"
echo ""

check_auth

case "$PHASE" in
  1) phase1 ;;
  2) phase2 ;;
  analyze) analyze "${2:-}" ;;
  all) phase1; phase2 ;;
  *)
    echo "使い方: TOKEN=... bash research.sh [1|2|analyze|all]"
    ;;
esac
