import { join } from "node:path";

const ROOT = join(import.meta.dir, "..");
const BOOKS = ["preflop", "flop"] as const;
type BookId = (typeof BOOKS)[number];

interface BookJson {
  title: string;
  subtitle?: string;
  author: string;
  language: string;
  publisher: string;
  description: string;
  kdp?: {
    keywords?: string[];
    categories?: string[];
    bisac?: string[];
    bisacLabels?: string[];
    targetAudience?: string;
    aiContentDisclosure?: {
      textAssisted?: boolean;
      imageGenerated?: boolean;
      note?: string;
    };
    pricing?: {
      currency?: string;
      listPrice?: number;
      kdpSelect?: boolean;
    };
  };
}

function formatKdp(cfg: BookJson): string {
  const kdp = cfg.kdp ?? {};
  const pricing = kdp.pricing ?? {};
  const disclosure = kdp.aiContentDisclosure ?? {};
  const lines: string[] = [];

  lines.push("============================================================");
  lines.push("KDP出版用メタデータ（コピペ用）");
  lines.push("============================================================");
  lines.push("");
  lines.push("■ タイトル");
  lines.push(cfg.title);
  lines.push("");

  if (cfg.subtitle) {
    lines.push("■ サブタイトル");
    lines.push(cfg.subtitle);
    lines.push("");
  }

  lines.push("■ 著者名");
  lines.push(cfg.author);
  lines.push("");
  lines.push("■ 出版社");
  lines.push(cfg.publisher);
  lines.push("");
  lines.push("■ 言語");
  lines.push(cfg.language === "ja" ? "日本語" : cfg.language);
  lines.push("");

  if (pricing.listPrice !== undefined) {
    lines.push("■ 価格");
    lines.push(`${pricing.listPrice}円（${pricing.currency ?? "JPY"}）`);
    lines.push("");
  }
  if (pricing.kdpSelect !== undefined) {
    lines.push("■ KDP Select");
    lines.push(pricing.kdpSelect ? "はい" : "いいえ");
    lines.push("");
  }

  lines.push("■ 内容紹介");
  lines.push(cfg.description);
  lines.push("");

  if (kdp.keywords && kdp.keywords.length > 0) {
    lines.push(`■ キーワード（${kdp.keywords.length}個）`);
    for (const k of kdp.keywords) lines.push(k);
    lines.push("");
  }

  if (kdp.categories && kdp.categories.length > 0) {
    lines.push("■ カテゴリ");
    for (const c of kdp.categories) lines.push(c);
    lines.push("");
  }

  if (kdp.bisac && kdp.bisac.length > 0) {
    lines.push("■ BISACコード");
    const labels = kdp.bisacLabels ?? [];
    kdp.bisac.forEach((code, i) => {
      const label = labels[i] ?? "";
      lines.push(label ? `${code} - ${label}` : code);
    });
    lines.push("");
  }

  if (kdp.targetAudience) {
    lines.push("■ 想定読者");
    lines.push(kdp.targetAudience);
    lines.push("");
  }

  if (disclosure.textAssisted !== undefined || disclosure.imageGenerated !== undefined) {
    lines.push("■ AI生成コンテンツ申告");
    if (disclosure.textAssisted) {
      lines.push(
        "テキスト：AI補助あり（" +
          (disclosure.note ?? "") +
          "）"
      );
    }
    if (disclosure.imageGenerated) {
      lines.push("画像：AI生成あり");
    }
    lines.push("");
  }

  return lines.join("\n");
}

async function main() {
  for (const bookId of BOOKS) {
    const cfgPath = join(ROOT, bookId, "book.json");
    const cfg = (await Bun.file(cfgPath).json()) as BookJson;
    const outPath = join(ROOT, bookId, "kdp-metadata.txt");
    await Bun.write(outPath, formatKdp(cfg));
    console.log(`[${bookId}] generated ${outPath}`);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
