/**
 * generate-range-tables.ts
 *
 * poker-books (preflop/flop) のレンジテーブルを SVG/PNG で生成
 * poker-book の新しいロジック（expandNotation + parseInput）を使用
 *
 * 使い方:
 *   bun run scripts/generate-range-tables.ts
 */

import { Resvg } from "@resvg/resvg-js";
import { mkdir } from "node:fs/promises";
import { join } from "node:path";

// ---- ランク定義 ----

const RANKS = "AKQJT98765432".split("");
const ri = (r: string) => RANKS.indexOf(r.toUpperCase());
const POS_ORDER = ["UTG", "HJ", "CO", "BTN", "SB", "BB"] as const;
const DEF_COLORS = {
  UTG: "#3266ad",
  HJ: "#1a8a4a",
  CO: "#d48a12",
  BTN: "#cc3333",
  SB: "#7a5db5",
  BB: "#2a8a8a",
};
const FOLD_COLOR = "#6b6960";

// ---- レンジパーサー（poker-book と同じロジック） ----

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
    const hi = ri(m[1]),
      lo = ri(m[2]),
      sf = m[3].toLowerCase();
    for (let i = hi + 1; i <= lo; i++) hands.push(RANKS[hi] + RANKS[i] + sf);
  } else if (/^([AKQJT2-9])([AKQJT2-9])([so])$/i.test(n)) {
    const m = n.match(/^([AKQJT2-9])([AKQJT2-9])([so])$/i)!;
    hands.push(m[1].toUpperCase() + m[2].toUpperCase() + m[3].toLowerCase());
  }
  return hands;
}

function parseInput(text: string): Record<string, { hands: Set<string>; pct: string }> {
  const positions: Record<string, { hands: Set<string>; pct: string }> = {};
  let cur: string | null = null;

  for (const line of text.split("\n")) {
    const pm = line.match(/^(UTG|HJ|CO|BTN|SB|BB)\b/i);
    if (pm) {
      cur = pm[1].toUpperCase();
      const pct = line.match(/([\d]+)\s*[〜~\-–]\s*([\d]+)\s*%/);
      positions[cur] = {
        hands: new Set(),
        pct: pct ? `${pct[1]}–${pct[2]}%` : "",
      };
      const afterColon = line.match(/[:：]\s*(.+)/);
      if (afterColon) {
        afterColon[1].split(/[,、]\s*/).forEach((p) => {
          expandNotation(p).forEach((h) => positions[cur!].hands.add(h));
        });
      }
      continue;
    }
    if (!cur) continue;
    const hm = line.match(
      /(?:ペア|スーテッド|オフスート|Pairs?|Suited|Offsuit|suited|offsuit)\s*[:：]\s*(.+)/i
    );
    if (hm) {
      hm[1].split(/[,、]\s*/).forEach((p) => {
        expandNotation(p).forEach((h) => positions[cur!].hands.add(h));
      });
    }
  }
  return positions;
}

function buildGrid(
  positions: Record<string, { hands: Set<string>; pct: string }>
): Record<string, string> {
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

// ---- レンジテキスト定義 ----

// プリフロップ RFI (Raise First In) レンジ
// poker-books preflop/chapters/23-appendix.md の付録A より抽出
// スコア式ベースのポジション別オープンレンジ
const preflopRFIRange = `UTG（しきい値 24）
ペア:     77+
スーテッド: AKs, AQs, AJs, ATs, KQs, KJs, KTs, QJs, JTs, A9s
オフスート: AKo, AQo, AJo

MP（しきい値 22）
ペア:     66+
スーテッド: A2s+, K9s+, QTs+, JTs, T9s, 98s, KQs, KJs, KTs, QJs, JTs, A9s, A8s
オフスート: AKo, AQo, AJo, ATo, KQo

CO（しきい値 20）
ペア:     55+
スーテッド: A2s+, K8s+, Q9s+, J9s+, T9s, 87s, 98s, A9s, A8s, A7s
オフスート: A9o+, AJo+, KQo, KJo

BTN（しきい値 18）
ペア:     22+
スーテッド: A2s+, K2s+, Q2s+, J2s+, T3s+, 94s+, 84s+, 74s+, 63s+, 53s+, 43s+
オフスート: A2o+, K8o+, Q9o+, J9o+, T8o+, 98o

SB（しきい値 20、特殊）
ペア:     55+
スーテッド: A2s+, K8s+, Q9s+, JTs, T9s
オフスート: AJo+, KQo`;

// フロップ プリフロップオープンレンジ
// poker-books flop/chapters/02-who-leads.md より抽出
// SRP（シングルレイズポット）でのポジション別オープンレンジ
const flopCbetRange = `UTG（17〜18%）
ペア:     TT+
スーテッド: ATs+, A5s, KTs+, QTs+, JTs, T9s, 98s
オフスート: AJo+, KQo

MP/HJ（21〜22%）
ペア:     55+
スーテッド: A2s+, K6s+, Q9s+, J9s+, T9s, 98s, 87s, 76s
オフスート: ATo+, KTo+, QTo+

CO（27〜28%）
ペア:     33+
スーテッド: A2s+, K3s+, Q6s+, J8s+, T7s+, 97s+, 87s, 76s
オフスート: A8o+, KTo+, QTo+, JTo

BTN（43〜45%）
ペア:     33+
スーテッド: A2s+, K2s+, Q3s+, J4s+, T6s+, 96s+, 85s+, 75s+, 64s+, 53s+
オフスート: A4o+, K8o+, Q9o+, J9o+, T8o+, 98o

SB（39〜47%）
ペア:     55+
スーテッド: A2s+, K8s+, Q9s+, J9s+, T9s, 98s, 87s, 76s
オフスート: AJo+, KQo`;

// ---- SVG生成関数 ----

function generateSVG(positions: Record<string, { hands: Set<string>; pct: string }>): string {
  const map = buildGrid(positions);

  const CW = 52,
    CH = 52,
    G = 2,
    PX = 8,
    PY = 8;
  const tw = 13 * CW + 12 * G + PX * 2;
  const legendH = 30;
  const th = PY + 13 * CH + 12 * G + PY + legendH + PY;

  let s = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${tw} ${th}" width="${tw}">`;
  s += `<rect width="${tw}" height="${th}" rx="6" fill="#1a1a2e"/>`;

  for (let r = 0; r < 13; r++) {
    for (let c = 0; c < 13; c++) {
      const h = handName(r, c);
      const pos = map[h] || "fold";
      const bg = pos === "fold" ? FOLD_COLOR : DEF_COLORS[pos as keyof typeof DEF_COLORS];
      const fg = pos === "fold" ? "#d0cec6" : "#fff";
      const x = PX + c * (CW + G);
      const y = PY + r * (CH + G);
      s += `<rect x="${x}" y="${y}" width="${CW}" height="${CH}" rx="3" fill="${bg}"/>`;
      s += `<text x="${x + CW / 2}" y="${y + CH / 2 + 6}" font-family="'Courier New', Courier, monospace" font-size="16" font-weight="700" fill="${fg}" text-anchor="middle" dominant-baseline="middle">${h}</text>`;
    }
  }

  const legendY = PY + 13 * CH + 12 * G + PY + 6;
  let lx = PX;
  for (const p of POS_ORDER) {
    if (!positions[p]) continue;
    s += `<rect x="${lx}" y="${legendY}" width="14" height="14" rx="2" fill="${DEF_COLORS[p as keyof typeof DEF_COLORS]}"/>`;
    s += `<text x="${lx + 18}" y="${legendY + 11}" font-family="'Courier New', Courier, monospace" font-size="16" font-weight="700" fill="#fff">${p}</text>`;
    lx += 80;
  }
  s += `<rect x="${lx}" y="${legendY}" width="14" height="14" rx="2" fill="${FOLD_COLOR}"/>`;
  s += `<text x="${lx + 18}" y="${legendY + 11}" font-family="'Courier New', Courier, monospace" font-size="16" font-weight="700" fill="#fff">Fold</text>`;

  s += `</svg>`;
  return s;
}

async function generateImage(
  title: string,
  rangeText: string,
  outputPath: string
): Promise<void> {
  const positions = parseInput(rangeText);
  const svg = generateSVG(positions);
  const resvg = new Resvg(svg, { fitTo: { mode: "original" } });
  const pngBuffer = resvg.render().asPng();

  await mkdir(outputPath.replace(/[/\\][^/\\]+$/, ""), { recursive: true });
  await Bun.write(outputPath, pngBuffer);

  console.log(`✓ ${title} 生成完了: ${outputPath}`);
  console.log(`  ファイルサイズ: ${(pngBuffer.length / 1024).toFixed(1)} KB`);
}

async function main(): Promise<void> {
  console.log("📊 poker-books レンジテーブル生成を開始...\n");

  // プリフロップ RFI レンジ表生成
  const preflopPath = join(import.meta.dir, "..", "preflop", "chapters", "images", "range-table-rfi.png");
  await generateImage("プリフロップ RFI", preflopRFIRange, preflopPath);

  // フロップ C-bet レンジ表生成
  const flopPath = join(import.meta.dir, "..", "flop", "chapters", "images", "range-table-cbet.png");
  await generateImage("フロップ C-Bet", flopCbetRange, flopPath);

  console.log("\n✅ すべてのレンジテーブル生成が完了しました");
}

main().catch(console.error);
