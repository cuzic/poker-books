import { $ } from "bun";
import { join } from "node:path";
import { mkdir } from "node:fs/promises";

const EPUBCHECK_VERSION = "5.1.0";
const EPUBCHECK_URL = `https://github.com/w3c/epubcheck/releases/download/v${EPUBCHECK_VERSION}/epubcheck-${EPUBCHECK_VERSION}.zip`;
const ROOT = join(import.meta.dir, "..");
const BOOKS = ["preflop", "flop", "flop-advanced", "volume4", "volume5", "volume6", "digest"] as const;
type BookId = (typeof BOOKS)[number];

// Build と同じ EPUB ファイル名マッピング（scripts/build.ts と一致させる）
const EPUB_FILENAMES: Record<BookId, string> = {
  preflop: "mayowanai-poker-01-preflop.epub",
  flop: "mayowanai-poker-02-flop.epub",
  "flop-advanced": "mayowanai-poker-03-flop-advanced.epub",
  volume4: "mayowanai-poker-04-turn-river-basic.epub",
  volume5: "mayowanai-poker-05-turn-river-advanced.epub",
  volume6: "mayowanai-poker-06-tournament.epub",
  digest: "mayowanai-poker-digest.epub",
};

async function ensureEpubcheck(): Promise<string> {
  const toolsDir = join(ROOT, ".tools");
  const epubcheckDir = join(toolsDir, `epubcheck-${EPUBCHECK_VERSION}`);
  const jarPath = join(epubcheckDir, `epubcheck.jar`);

  if (await Bun.file(jarPath).exists()) return jarPath;

  console.log(`Downloading epubcheck v${EPUBCHECK_VERSION}...`);
  await mkdir(toolsDir, { recursive: true });
  const zipPath = join(toolsDir, "epubcheck.zip");
  await $`curl -L -o ${zipPath} ${EPUBCHECK_URL}`;
  console.log("Extracting epubcheck...");
  await $`unzip -q -o ${zipPath} -d ${toolsDir}`;
  await $`rm ${zipPath}`;
  console.log(`epubcheck installed at ${epubcheckDir}`);
  return jarPath;
}

async function checkOne(jarPath: string, bookId: BookId): Promise<number> {
  const epubPath = join(ROOT, "dist", bookId, EPUB_FILENAMES[bookId]);
  if (!(await Bun.file(epubPath).exists())) {
    console.error(`[${bookId}] EPUB not found: ${epubPath}`);
    console.error(`Run: bun run build:epub (or build:${bookId})`);
    return 1;
  }
  console.log(`\n=== Checking ${bookId}: ${epubPath} ===\n`);
  const result = await $`java -jar ${jarPath} ${epubPath}`.nothrow();
  return result.exitCode ?? 0;
}

async function main() {
  const args = process.argv.slice(2);
  let target: BookId | "all" = "all";
  const bookIdx = args.indexOf("--book");
  if (bookIdx !== -1 && args[bookIdx + 1]) {
    const requested = args[bookIdx + 1] as BookId | "all";
    if ([...BOOKS, "all"].includes(requested as string)) target = requested;
  }

  const jarPath = await ensureEpubcheck();
  const targets: BookId[] = target === "all" ? [...BOOKS] : [target];

  let exitCode = 0;
  for (const id of targets) {
    const code = await checkOne(jarPath, id);
    if (code !== 0) exitCode = code;
  }
  process.exit(exitCode);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
