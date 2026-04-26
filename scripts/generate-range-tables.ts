/**
 * generate-range-tables.ts
 *
 * poker-books のレンジテーブルをすべて SVG/PNG で生成
 * 出力: preflop/chapters/images/ と flop/chapters/images/
 *
 * 使い方:  bun run scripts/generate-range-tables.ts
 */

import { Resvg } from "@resvg/resvg-js";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

// ---- 定数 ----

const RANKS = "AKQJT98765432".split("");
const ri = (r: string) => RANKS.indexOf(r.toUpperCase());
const POS_ORDER = ["UTG", "HJ", "CO", "BTN", "SB", "BB"] as const;

const POS_COLORS: Record<string, string> = {
  UTG: "#3266ad",
  HJ: "#1a8a4a",
  CO: "#d48a12",
  BTN: "#cc3333",
  SB: "#7a5db5",
  BB: "#2a8a8a",
};
const FOLD_COLOR = "#4d4d55";

const ACTION_COLORS: Record<string, string> = {
  value3bet: "#922b21",
  bluff3bet:  "#ba4a00",
  call:        "#1a5276",
  "4bet":      "#6c3483",
  "4betbluff": "#ba4a00",
  call4bet:    "#1a5276",
  fold:        FOLD_COLOR,
};
const ACTION_LABELS: Record<string, string> = {
  value3bet: "3bet",
  bluff3bet:  "3bet*",
  call:        "Call",
  "4bet":      "4bet",
  "4betbluff": "4bet*",
  call4bet:    "Call",
  fold:        "",
};

const CW = 56, CH = 56, G = 2, PX = 8, PY = 8;

// フォントサイズ定数（タイトルは一段階大きく、外部テキストはすべて白）
const FS_TITLE  = 20; // 図タイトル（太字・最大）
const FS_CELL1  = 19; // セル1行（単行表示）
const FS_CELL_H = 15; // セル2行・上段（ハンド名）
const FS_CELL_A = 17; // セル2行・下段（アクション/スコア）
const FS_LEGEND = 16; // 凡例
const FS_ANNOT  = 14; // 欄外注釈（ヒートマップ閾値など）

// ---- パーサー ----

function expandNotation(n: string): string[] {
  n = n.trim().replace(/（.*?）/g, "");
  if (!n) return [];
  const hands: string[] = [];

  if (/^([AKQJT2-9])\1\+$/.test(n)) {
    const idx = ri(n[0]);
    for (let i = 0; i <= idx; i++) hands.push(RANKS[i] + RANKS[i]);
  } else if (/^([AKQJT2-9])\1$/.test(n)) {
    hands.push(n.toUpperCase());
  } else if (/^([AKQJT2-9])([AKQJT2-9])([so])\+$/i.test(n)) {
    const m = n.match(/^([AKQJT2-9])([AKQJT2-9])([so])\+$/i)!;
    const hi = ri(m[1]), lo = ri(m[2]), sf = m[3].toLowerCase();
    for (let i = hi + 1; i <= lo; i++) hands.push(RANKS[hi] + RANKS[i] + sf);
  } else if (/^([AKQJT2-9])([AKQJT2-9])([so])$/i.test(n)) {
    const m = n.match(/^([AKQJT2-9])([AKQJT2-9])([so])$/i)!;
    hands.push(m[1].toUpperCase() + m[2].toUpperCase() + m[3].toLowerCase());
  }
  return hands;
}

function parseTokens(notation: string): Set<string> {
  const s = new Set<string>();
  for (const token of notation.split(/[,、]\s*/)) {
    expandNotation(token.trim()).forEach((h) => s.add(h));
  }
  return s;
}

// ポジション別テキストブロックを解析（RFI / フロップ用）
function parseInput(text: string): Record<string, { hands: Set<string>; pct: string }> {
  const positions: Record<string, { hands: Set<string>; pct: string }> = {};
  let cur: string | null = null;

  for (const line of text.split("\n")) {
    const pm = line.match(/^(UTG|HJ|MP|CO|BTN|SB|BB)\b/i);
    if (pm) {
      cur = pm[1].toUpperCase() === "MP" ? "HJ" : pm[1].toUpperCase();
      const pct = line.match(/([\d]+)\s*[〜~\-–]\s*([\d]+)\s*%/);
      positions[cur] = { hands: new Set(), pct: pct ? `${pct[1]}–${pct[2]}%` : "" };
      const afterColon = line.match(/[:：]\s*(.+)/);
      if (afterColon) parseTokens(afterColon[1]).forEach((h) => positions[cur!].hands.add(h));
      continue;
    }
    if (!cur) continue;
    const hm = line.match(
      /(?:ペア|スーテッド|オフスート|Pairs?|Suited|Offsuit)\s*[:：]\s*(.+)/i
    );
    if (hm) parseTokens(hm[1]).forEach((h) => positions[cur!].hands.add(h));
  }
  return positions;
}

// アクション別セクションを解析（3bet/コール/フォールドなど）
function parseActionInput(sections: Array<{ action: string; notation: string }>): Record<string, string> {
  const map: Record<string, string> = {};
  for (const { action, notation } of sections) {
    for (const h of parseTokens(notation)) {
      if (!map[h]) map[h] = action;
    }
  }
  return map;
}

function buildPositionGrid(positions: Record<string, { hands: Set<string>; pct: string }>): Record<string, string> {
  const map: Record<string, string> = {};
  for (const p of POS_ORDER) {
    if (!positions[p]) continue;
    for (const h of positions[p].hands) {
      if (!map[h]) map[h] = p;
    }
  }
  return map;
}

function handName(r: number, c: number): string {
  if (r === c) return RANKS[r] + RANKS[c];
  if (r < c) return RANKS[r] + RANKS[c] + "s";
  return RANKS[c] + RANKS[r] + "o";
}

// ---- スコア計算 ----

function calcScore(r: number, c: number): number {
  const hiIdx = Math.min(r, c);
  const loIdx = Math.max(r, c);
  const hiRank = 14 - hiIdx;
  const loRank = 14 - loIdx;
  if (r === c) return hiRank + loRank + 10; // ペア
  const diff = loIdx - hiIdx;
  const isSuited = r < c;
  let score = hiRank + loRank;
  if (isSuited) score += 2;
  if (diff === 1) score += 1;
  else if (diff === 2) score += 0.5;
  else if (diff >= 4) score -= 1;
  if (hiRank < 9 && loRank < 9) score -= 1;
  return score;
}

function scoreToColor(score: number): string {
  const t = Math.max(0, Math.min(1, (score - 7) / (38 - 7)));
  let r: number, g: number, b: number;
  if (t < 0.35) {
    const u = t / 0.35;
    r = Math.round(70 + u * 130); g = Math.round(70 + u * 30); b = Math.round(80 - u * 40);
  } else if (t < 0.65) {
    const u = (t - 0.35) / 0.30;
    r = Math.round(200 + u * 35); g = Math.round(100 + u * 100); b = Math.round(40 - u * 40);
  } else {
    const u = (t - 0.65) / 0.35;
    r = Math.round(235 - u * 175); g = Math.round(200 + u * 30); b = Math.round(0 + u * 70);
  }
  return `rgb(${r},${g},${b})`;
}

// ---- SVG ベース ----

function svgOpen(w: number, h: number): string {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${w} ${h}" width="${w}"><rect width="${w}" height="${h}" rx="6" fill="#1a1a2e"/>`;
}

function gridDims(titleH: number, legendH: number) {
  const tw = 13 * CW + 12 * G + PX * 2;
  const th = PY + titleH + 13 * CH + 12 * G + PY + legendH + PY;
  return { tw, th };
}

function renderTitle(tw: number, title: string, y: number): string {
  return `<text x="${tw / 2}" y="${y}" font-family="'Courier New',monospace" font-size="${FS_TITLE}" font-weight="700" fill="#fff" text-anchor="middle">${title}</text>`;
}

function renderCell(x: number, y: number, bg: string, line1: string, line2: string, fg = "#fff"): string {
  let s = `<rect x="${x}" y="${y}" width="${CW}" height="${CH}" rx="3" fill="${bg}"/>`;
  if (line2) {
    s += `<text x="${x + CW / 2}" y="${y + 19}" font-family="'Courier New',monospace" font-size="${FS_CELL_H}" font-weight="700" fill="${fg}" text-anchor="middle">${line1}</text>`;
    s += `<text x="${x + CW / 2}" y="${y + 40}" font-family="'Courier New',monospace" font-size="${FS_CELL_A}" font-weight="700" fill="#fff" text-anchor="middle">${line2}</text>`;
  } else {
    s += `<text x="${x + CW / 2}" y="${y + CH / 2 + 7}" font-family="'Courier New',monospace" font-size="${FS_CELL1}" font-weight="700" fill="${fg}" text-anchor="middle">${line1}</text>`;
  }
  return s;
}

// ---- 1. RFI レンジグリッド ----

function generateRFISVG(positions: Record<string, { hands: Set<string>; pct: string }>): string {
  const map = buildPositionGrid(positions);
  const { tw, th } = gridDims(0, 32);
  let s = svgOpen(tw, th);

  for (let r = 0; r < 13; r++) {
    for (let c = 0; c < 13; c++) {
      const h = handName(r, c);
      const pos = map[h] || "fold";
      const bg = pos === "fold" ? FOLD_COLOR : POS_COLORS[pos];
      const x = PX + c * (CW + G), y = PY + r * (CH + G);
      s += renderCell(x, y, bg, h, "");
    }
  }

  const legendY = PY + 13 * CH + 12 * G + PY + 5;
  let lx = PX;
  for (const p of POS_ORDER) {
    if (!positions[p]) continue;
    s += `<rect x="${lx}" y="${legendY}" width="16" height="16" rx="2" fill="${POS_COLORS[p]}"/>`;
    s += `<text x="${lx + 20}" y="${legendY + 13}" font-family="'Courier New',monospace" font-size="${FS_LEGEND}" font-weight="700" fill="#fff">${p}</text>`;
    lx += 82;
  }
  s += `<rect x="${lx}" y="${legendY}" width="16" height="16" rx="2" fill="${FOLD_COLOR}"/>`;
  s += `<text x="${lx + 20}" y="${legendY + 13}" font-family="'Courier New',monospace" font-size="${FS_LEGEND}" font-weight="700" fill="#fff">Fold</text>`;
  return s + `</svg>`;
}

// ---- 2. スコア ヒートマップ ----

function generateScoreHeatmapSVG(): string {
  const titleH = 36;
  const legendH = 50;
  const { tw, th } = gridDims(titleH, legendH);
  let s = svgOpen(tw, th);
  s += renderTitle(tw, "ハンドスコア ヒートマップ（AA=38 〜 72o=7）", PY + 21);

  for (let r = 0; r < 13; r++) {
    for (let c = 0; c < 13; c++) {
      const score = calcScore(r, c);
      const bg = scoreToColor(score);
      const x = PX + c * (CW + G), y = PY + titleH + r * (CH + G);
      s += renderCell(x, y, bg, handName(r, c), String(score));
    }
  }

  // グラデーションバー
  const barY = PY + titleH + 13 * CH + 12 * G + PY + 4;
  const barW = 13 * CW + 12 * G;
  const steps = 60;
  for (let i = 0; i < steps; i++) {
    const score = 7 + (i / steps) * 31;
    const bx = PX + (i * barW) / steps;
    s += `<rect x="${bx}" y="${barY}" width="${barW / steps + 1}" height="14" fill="${scoreToColor(score)}"/>`;
  }
  // しきい値マーカー
  for (const [score, label] of [
    [24, "UTG≥24"],
    [22, "HJ≥22"],
    [20, "CO≥20"],
    [18, "BTN≥18"],
  ] as [number, string][]) {
    const bx = PX + ((score - 7) / 31) * barW;
    s += `<line x1="${bx}" y1="${barY - 2}" x2="${bx}" y2="${barY + 14}" stroke="#fff" stroke-width="2"/>`;
    s += `<text x="${bx}" y="${barY + 32}" font-family="'Courier New',monospace" font-size="${FS_ANNOT}" font-weight="700" fill="#fff" text-anchor="middle">${label}</text>`;
  }
  s += `<text x="${PX}" y="${barY + 32}" font-family="'Courier New',monospace" font-size="${FS_ANNOT}" fill="#fff">7</text>`;
  s += `<text x="${PX + barW}" y="${barY + 32}" font-family="'Courier New',monospace" font-size="${FS_ANNOT}" fill="#fff" text-anchor="end">38</text>`;

  return s + `</svg>`;
}

// ---- 3–8. アクション別グリッド ----

function generateActionSVG(
  title: string,
  actionMap: Record<string, string>,
  legendItems: Array<{ action: string; label: string }>,
): string {
  const titleH = 34;
  const legendH = 34;
  const { tw, th } = gridDims(titleH, legendH);
  let s = svgOpen(tw, th);
  s += renderTitle(tw, title, PY + 20);

  for (let r = 0; r < 13; r++) {
    for (let c = 0; c < 13; c++) {
      const h = handName(r, c);
      const action = actionMap[h] || "fold";
      const bg = ACTION_COLORS[action] ?? FOLD_COLOR;
      const x = PX + c * (CW + G), y = PY + titleH + r * (CH + G);
      const actLabel = ACTION_LABELS[action] ?? "";
      s += renderCell(x, y, bg, h, actLabel);
    }
  }

  const legendY = PY + titleH + 13 * CH + 12 * G + PY + 5;
  let lx = PX;
  for (const { action, label } of legendItems) {
    const color = ACTION_COLORS[action] ?? FOLD_COLOR;
    s += `<rect x="${lx}" y="${legendY}" width="16" height="16" rx="2" fill="${color}"/>`;
    s += `<text x="${lx + 20}" y="${legendY + 13}" font-family="'Courier New',monospace" font-size="${FS_LEGEND}" font-weight="700" fill="#fff">${label}</text>`;
    lx += label.length * 9 + 32;
  }
  return s + `</svg>`;
}

// ---- PNG 出力 ----

async function writePNG(svg: string, outputPath: string, label: string): Promise<void> {
  const resvg = new Resvg(svg, { fitTo: { mode: "original" } });
  const pngBuffer = resvg.render().asPng();
  await mkdir(outputPath.replace(/[/\\][^/\\]+$/, ""), { recursive: true });
  await Bun.write(outputPath, pngBuffer);
  console.log(`✓ ${label} → ${outputPath.split(/[/\\]/).slice(-2).join("/")} (${(pngBuffer.length / 1024).toFixed(1)} KB)`);
}

// ========== レンジデータ ==========

// ① プリフロップ RFI（付録A）
const preflopRFIRange = `UTG（しきい値 24）
ペア: 77+
スーテッド: A9s+, KTs+, QJs, JTs
オフスート: AJo+

HJ（しきい値 22）
ペア: 66+
スーテッド: A8s+, K9s+, QTs+, JTs, T9s, 98s
オフスート: ATo+, KQo

CO（しきい値 20）
ペア: 55+
スーテッド: A2s+, K8s+, Q9s+, J9s+, T9s, 98s, 87s
オフスート: A9o+, KJo+

BTN（しきい値 18）
ペア: 22+
スーテッド: A2s+, K2s+, Q2s+, J2s+, T3s+, 94s+, 84s+, 74s+, 63s+, 53s+, 43s
オフスート: A2o+, K8o+, Q9o+, J9o+, T8o+, 98o

SB（しきい値 20、特殊）
ペア: 55+
スーテッド: A2s+, K8s+, Q9s+, JTs, T9s
オフスート: AJo+, KQo`;

// ⑧ フロップ到達時レンジ（flop/chapters/02-who-leads.md）
const flopCbetRange = `UTG（17〜18%）
ペア: TT+
スーテッド: ATs+, A5s, KTs+, QTs+, JTs, T9s, 98s
オフスート: AJo+, KQo

HJ（21〜22%）
ペア: 55+
スーテッド: A2s+, K6s+, Q9s+, J9s+, T9s, 98s, 87s, 76s
オフスート: ATo+, KTo+, QTo+

CO（27〜28%）
ペア: 33+
スーテッド: A2s+, K3s+, Q6s+, J8s+, T7s+, 97s+, 87s, 76s
オフスート: A8o+, KTo+, QTo+, JTo

BTN（43〜45%）
ペア: 33+
スーテッド: A2s+, K2s+, Q3s+, J4s+, T6s+, 96s+, 85s+, 75s+, 64s+, 53s+
オフスート: A4o+, K8o+, Q9o+, J9o+, T8o+, 98o

SB（39〜47%）
ペア: 55+
スーテッド: A2s+, K8s+, Q9s+, J9s+, T9s, 98s, 87s, 76s
オフスート: AJo+, KQo`;

// ③ 3bet vs UTG（ポーラライズ型・付録F⑥⑦⑧参照）
const threeBetVsUTG = [
  { action: "value3bet", notation: "QQ+, AKs, AKo, AQs" },
  { action: "bluff3bet",  notation: "A5s, A4s, A3s" },
  { action: "call",        notation: "JJ, TT, 99, 88, 77, 66, 55, 44, 33, 22, AJs, ATs, A9s, A8s, A7s, A6s, A2s, KQs, KJs, KTs, K9s, QJs, QTs, JTs, T9s, 98s, 87s, 76s, AJo, KQo" },
];

// ④ 3bet vs BTN（リニア型）
const threeBetVsBTN = [
  { action: "value3bet", notation: "QQ+, AKs, AKo, JJ, TT, AQs, AJs" },
  { action: "bluff3bet",  notation: "A5s, A4s, A3s, A2s" },
  { action: "call",        notation: "99, 88, 77, 66, 55, 44, 33, 22, ATs, A9s, A8s, A7s, A6s, KQs, KJs, KTs, K9s, K8s, QJs, QTs, Q9s, JTs, J9s, T9s, 98s, 87s, 76s, 65s, AQo, AJo, ATo, KQo, KJo, QJo" },
];

// ⑤ BBディフェンス vs UTG
const bbDefVsUTG = [
  { action: "value3bet", notation: "QQ+, AKs, AKo, AQs" },
  { action: "bluff3bet",  notation: "A5s, A4s, A3s" },
  { action: "call",        notation: "JJ, TT, 99, 88, 77, 66, 55, 44, 33, 22, AJs, ATs, A9s, A8s, A7s, A6s, A2s, KQs, KJs, KTs, K9s, QJs, QTs, JTs, T9s, 98s, 87s, 76s, AJo, KQo" },
];

// ⑥ BBディフェンス vs BTN
const bbDefVsBTN = [
  { action: "value3bet", notation: "QQ+, AKs, AKo, JJ, TT, AQs" },
  { action: "bluff3bet",  notation: "A5s, A4s, A3s, A2s, KJs, QJs" },
  { action: "call",        notation: "99, 88, 77, 66, 55, 44, 33, 22, AJs, ATs, A9s, A8s, A7s, A6s, KQs, KTs, K9s, K8s, QTs, Q9s, JTs, J9s, T9s, 98s, 87s, 76s, 65s, 54s, AJo, ATo, A9o, A8o, KQo, KJo, QJo, JTo, T9o, 98o" },
];

// ⑦ SB 3bet vs BTN（付録 ch15）
const sbVsBTN = [
  { action: "value3bet", notation: "QQ+, AKs, AKo, JJ, TT, AQs" },
  { action: "bluff3bet",  notation: "A5s, A4s, A3s, A2s, A8o, KTo" },
  { action: "call",        notation: "AJs, KQs, KJs" },
];

// ⑨ 4betレンジ（付録 ch16）
const fourBetRange = [
  { action: "4bet",      notation: "AA, KK, QQ, AKs, AKo" },
  { action: "4betbluff", notation: "A5s, A4s, A3s, A2s" },
  { action: "call4bet",  notation: "JJ, TT, AQs" },
];

// ========== main ==========

async function main(): Promise<void> {
  console.log("📊 poker-books レンジテーブル生成を開始...\n");

  const pre = join(import.meta.dir, "..", "preflop", "chapters", "images");
  const flp = join(import.meta.dir, "..", "flop", "chapters", "images");

  // ① RFI レンジ
  await writePNG(
    generateRFISVG(parseInput(preflopRFIRange)),
    join(pre, "range-table-rfi.png"),
    "① RFI レンジ（ポジション別オープン）",
  );

  // ② ハンドスコア ヒートマップ
  await writePNG(
    generateScoreHeatmapSVG(),
    join(pre, "range-table-score-heatmap.png"),
    "② ハンドスコア ヒートマップ",
  );

  const defLegend = [
    { action: "value3bet", label: "3bet バリュー" },
    { action: "bluff3bet",  label: "3bet ブラフ" },
    { action: "call",        label: "コール" },
    { action: "fold",        label: "フォールド" },
  ];

  // ③ 3bet vs UTG
  await writePNG(
    generateActionSVG("3ベット vs UTG（ポーラライズ）", parseActionInput(threeBetVsUTG), defLegend),
    join(pre, "range-table-3bet-vs-utg.png"),
    "③ 3bet vs UTG",
  );

  // ④ 3bet vs BTN
  await writePNG(
    generateActionSVG("3ベット vs BTN（リニア）", parseActionInput(threeBetVsBTN), defLegend),
    join(pre, "range-table-3bet-vs-btn.png"),
    "④ 3bet vs BTN",
  );

  // ⑤ BBディフェンス vs UTG
  await writePNG(
    generateActionSVG("BBディフェンス vs UTG", parseActionInput(bbDefVsUTG), defLegend),
    join(pre, "range-table-bb-defense-utg.png"),
    "⑤ BBディフェンス vs UTG",
  );

  // ⑥ BBディフェンス vs BTN
  await writePNG(
    generateActionSVG("BBディフェンス vs BTN", parseActionInput(bbDefVsBTN), defLegend),
    join(pre, "range-table-bb-defense-btn.png"),
    "⑥ BBディフェンス vs BTN",
  );

  // ⑦ SB 3bet vs BTN
  await writePNG(
    generateActionSVG(
      "SB 3ベット vs BTN",
      parseActionInput(sbVsBTN),
      [...defLegend, { action: "call", label: "コールド・コール" }].slice(0, 4),
    ),
    join(pre, "range-table-sb-3bet-vs-btn.png"),
    "⑦ SB 3bet vs BTN",
  );

  // ⑧ フロップ到達時レンジ
  await writePNG(
    generateRFISVG(parseInput(flopCbetRange)),
    join(flp, "range-table-cbet.png"),
    "⑧ フロップ到達時レンジ（Cbet 前提）",
  );

  // ⑨ 4betレンジ
  await writePNG(
    generateActionSVG(
      "4ベットレンジ",
      parseActionInput(fourBetRange),
      [
        { action: "4bet",      label: "4bet バリュー" },
        { action: "4betbluff", label: "4bet ブラフ" },
        { action: "call4bet",  label: "コール" },
        { action: "fold",      label: "フォールド" },
      ],
    ),
    join(pre, "range-table-4bet.png"),
    "⑨ 4betレンジ",
  );

  console.log("\n✅ 全9枚のレンジテーブル生成が完了しました");
}

main().catch(console.error);
