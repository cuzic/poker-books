import { unified } from "unified";
import remarkParse from "remark-parse";
import remarkGfm from "remark-gfm";
import remarkCjkFriendly from "remark-cjk-friendly";
import remarkCjkFriendlyGfmStrikethrough from "remark-cjk-friendly-gfm-strikethrough";
import remarkRehype from "remark-rehype";
import rehypeRaw from "rehype-raw";
import rehypeStringify from "rehype-stringify";
import EPub from "epub-gen-memory";
import { readdir, mkdir, writeFile, readFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, basename, extname } from "node:path";
import { tmpdir } from "node:os";
import { spawn } from "node:child_process";
import { createHash } from "node:crypto";

interface BookConfig {
  title: string;
  subtitle?: string;
  author: string;
  language: string;
  identifier: string;
  publisher: string;
  description: string;
  cover?: string;
}

interface Chapter {
  title: string;
  content: string;
  filename: string;
}

type OutputFormat = "html" | "xhtml" | "epub" | "site" | "all";
type BookId = "preflop" | "flop" | "flop-advanced" | "volume4" | "volume5" | "volume6" | "digest" | "vol2" | "tell";

const ROOT = join(import.meta.dir, "..");
const BOOKS: BookId[] = ["preflop", "flop", "flop-advanced", "volume4", "volume5", "volume6", "digest", "vol2", "tell"];

// 各 book ID とディレクトリの対応（同名でない場合のみ記載）
const BOOK_DIRS: Partial<Record<BookId, string>> = {};

const EPUB_FILENAMES: Record<BookId, string> = {
  preflop: "mayowanai-poker-01-preflop.epub",
  flop: "mayowanai-poker-02-flop.epub",
  "flop-advanced": "mayowanai-poker-03-flop-advanced.epub",
  volume4: "mayowanai-poker-04-turn-river-basic.epub",
  volume5: "mayowanai-poker-05-turn-river-advanced.epub",
  volume6: "mayowanai-poker-06-tournament.epub",
  digest: "mayowanai-poker-digest.epub",
  vol2: "mayowanai-poker-vol2-flop-river-basics.epub",
  tell: "exploit-poker-player-types.epub",
};

function bookDir(bookId: BookId): string {
  return BOOK_DIRS[bookId] ?? bookId;
}

async function loadBookConfig(bookId: BookId): Promise<BookConfig> {
  const configPath = join(ROOT, bookDir(bookId), "book.json");
  return await Bun.file(configPath).json();
}

async function getChapterFiles(bookId: BookId): Promise<string[]> {
  const chaptersDir = join(ROOT, bookDir(bookId), "chapters");
  const files = await readdir(chaptersDir);
  return files
    .filter((f) => extname(f) === ".md")
    .sort()
    .map((f) => join(chaptersDir, f));
}

function createHtmlProcessor() {
  return unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkCjkFriendly)
    .use(remarkCjkFriendlyGfmStrikethrough)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeStringify);
}

function createXhtmlProcessor() {
  return unified()
    .use(remarkParse)
    .use(remarkGfm)
    .use(remarkCjkFriendly)
    .use(remarkCjkFriendlyGfmStrikethrough)
    .use(remarkRehype, { allowDangerousHtml: true })
    .use(rehypeRaw)
    .use(rehypeStringify, {
      closeSelfClosing: true,
      tightSelfClosing: false,
      upperDoctype: true,
    });
}

// ─── Mermaid 前処理 ───────────────────────────────────────────────────────────
// mmdc (mermaid-cli) を呼び出して mermaid コードブロックを SVG に置換。
// SVG は HTML/XHTML/EPUB すべてで描画可能。同じソースは MERMAID_CACHE で再利用。
const MERMAID_CACHE = join(ROOT, ".mermaid-cache");

async function ensureMermaidCache() {
  if (!existsSync(MERMAID_CACHE)) {
    await mkdir(MERMAID_CACHE, { recursive: true });
  }
}

async function renderMermaidBlock(source: string): Promise<Buffer> {
  await ensureMermaidCache();
  const hash = createHash("sha256").update(source).digest("hex").slice(0, 16);
  const pngPath = join(MERMAID_CACHE, `${hash}.png`);
  if (existsSync(pngPath)) {
    return await readFile(pngPath);
  }

  const mmdPath = join(tmpdir(), `mermaid-${hash}.mmd`);
  await writeFile(mmdPath, source, "utf-8");

  await new Promise<void>((resolve, reject) => {
    // PNG 出力: SVG だと epubcheck が <foreignObject><p>...</p></foreignObject>
    // を namespace エラーにするため、PNG に統一する。スケール 2 で高 DPI 対応。
    const child = spawn(
      "bunx",
      ["mmdc", "-i", mmdPath, "-o", pngPath, "-s", "2", "-w", "1200"],
      { stdio: ["ignore", "pipe", "pipe"] }
    );
    let stderr = "";
    child.stderr.on("data", (d) => (stderr += d.toString()));
    child.on("error", reject);
    child.on("close", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`mmdc exited ${code}: ${stderr}`));
    });
  });
  return await readFile(pngPath);
}

// Mermaid 図を PNG として <bookDir>/chapters/images/mermaid-{hash}.png に保存し、
// `<img src="images/...">` で参照する。既存の rewriteImagesToFileUrls パイプラインが
// EPUB 用の file:// URL 変換、HTML 用の base64 埋め込みを担当する。
// SVG は mermaid の <foreignObject> による HTML 要素混入で epubcheck エラーになるため、
// PNG に統一する (スケール ×2 で 1200px 幅、高 DPI 対応)。
async function preprocessMermaid(markdown: string, bookDirPath: string): Promise<string> {
  const re = /```mermaid\n([\s\S]*?)\n```/g;
  const blocks: { match: string; source: string }[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(markdown)) !== null) {
    blocks.push({ match: m[0], source: m[1] });
  }
  if (blocks.length === 0) return markdown;

  const imagesDir = join(bookDirPath, "chapters", "images");
  if (!existsSync(imagesDir)) {
    await mkdir(imagesDir, { recursive: true });
  }

  let result = markdown;
  for (const { match, source } of blocks) {
    const png = await renderMermaidBlock(source);
    const hash = createHash("sha256").update(source).digest("hex").slice(0, 16);
    const filename = `mermaid-${hash}.png`;
    const outPath = join(imagesDir, filename);
    if (!existsSync(outPath)) {
      await writeFile(outPath, png);
    }
    const wrapped = `<figure class="mermaid-figure"><img src="images/${filename}" alt="Mermaid diagram"/></figure>`;
    result = result.replace(match, `\n\n${wrapped}\n\n`);
  }
  return result;
}

async function processMarkdown(
  filePath: string,
  processor: ReturnType<typeof createHtmlProcessor>,
  bookDirPath: string
): Promise<Chapter> {
  const rawContent = await Bun.file(filePath).text();
  const content = await preprocessMermaid(rawContent, bookDirPath);
  const result = await processor.process(content);
  const titleMatch = rawContent.match(/^#\s+(.+)$/m);
  const title = titleMatch ? titleMatch[1] : basename(filePath, ".md");
  return {
    title,
    content: String(result),
    filename: basename(filePath, ".md"),
  };
}

function wrapHtml(content: string, title: string, isXhtml: boolean): string {
  if (isXhtml) {
    return `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="ja">
<head>
  <meta http-equiv="Content-Type" content="application/xhtml+xml; charset=utf-8" />
  <title>${title}</title>
  <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
${content}
</body>
</html>`;
  }
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
${content}
</body>
</html>`;
}

function wrapHtmlWithNav(
  content: string,
  title: string,
  nav: string,
  bookTitle: string
): string {
  return `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title} - ${bookTitle}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
${nav}
<main>
${content}
</main>
${nav}
</body>
</html>`;
}

async function loadCss(): Promise<string> {
  const cssPath = join(ROOT, "src", "assets", "style.css");
  const file = Bun.file(cssPath);
  if (await file.exists()) {
    return await file.text();
  }
  return "";
}

async function buildHtml(bookId: BookId): Promise<void> {
  const outDir = join(ROOT, "dist", bookId, "html");
  await mkdir(outDir, { recursive: true });
  const processor = createHtmlProcessor();
  for (const chapterPath of await getChapterFiles(bookId)) {
    const chapter = await processMarkdown(chapterPath, processor, join(ROOT, bookDir(bookId)));
    const html = wrapHtml(chapter.content, chapter.title, false);
    await Bun.write(join(outDir, `${chapter.filename}.html`), html);
  }
  await Bun.write(join(outDir, "style.css"), await loadCss());
  console.log(`[${bookId}] html built → ${outDir}`);
}

async function buildXhtml(bookId: BookId): Promise<void> {
  const outDir = join(ROOT, "dist", bookId, "xhtml");
  await mkdir(outDir, { recursive: true });
  const processor = createXhtmlProcessor();
  for (const chapterPath of await getChapterFiles(bookId)) {
    const chapter = await processMarkdown(chapterPath, processor, join(ROOT, bookDir(bookId)));
    const xhtml = wrapHtml(chapter.content, chapter.title, true);
    await Bun.write(join(outDir, `${chapter.filename}.xhtml`), xhtml);
  }
  await Bun.write(join(outDir, "style.css"), await loadCss());
  console.log(`[${bookId}] xhtml built → ${outDir}`);
}

/**
 * Replace `src="images/X.jpg"` with embedded base64 data URI.
 * Used for HTML/XHTML output where images can be inlined.
 */
async function embedImages(bookId: BookId, content: string): Promise<string> {
  const imagesDir = join(ROOT, bookDir(bookId), "chapters", "images");
  const imgRegex = /src="images\/([^"]+)"/g;
  const matches = [...content.matchAll(imgRegex)];
  let result = content;
  const missingFiles: string[] = [];
  for (const match of matches) {
    const [fullMatch, filename] = match;
    const imagePath = join(imagesDir, filename);
    const imageFile = Bun.file(imagePath);
    if (await imageFile.exists()) {
      const data = await imageFile.arrayBuffer();
      const base64 = Buffer.from(data).toString("base64");
      const ext = filename.split(".").pop()?.toLowerCase();
      const mimeType =
        ext === "png"
          ? "image/png"
          : ext === "jpg" || ext === "jpeg"
          ? "image/jpeg"
          : "image/png";
      result = result.replace(
        fullMatch,
        `src="data:${mimeType};base64,${base64}"`
      );
    } else {
      missingFiles.push(filename);
    }
  }
  result = stripMissingImageFigures(bookId, result, missingFiles);
  return result;
}

/**
 * Replace `src="images/X.jpg"` with `src="file:///absolute/path/to/X.jpg"`.
 * Used for EPUB output: epub-gen-memory's fetchable.js handles file:// URLs
 * via fs.readFile, and mime.getType() infers proper extension/mediaType from
 * the file path. Embedding base64 data URIs causes mime.getType() to return
 * null and the resulting EPUB fails epubcheck (PKG-011, RSC-032).
 */
async function rewriteImagesToFileUrls(
  bookId: BookId,
  content: string
): Promise<string> {
  const imagesDir = join(ROOT, bookDir(bookId), "chapters", "images");
  const imgRegex = /src="images\/([^"]+)"/g;
  const matches = [...content.matchAll(imgRegex)];
  let result = content;
  const missingFiles: string[] = [];
  for (const match of matches) {
    const [fullMatch, filename] = match;
    const imagePath = join(imagesDir, filename);
    const imageFile = Bun.file(imagePath);
    if (await imageFile.exists()) {
      // file:// URL with proper file extension lets epub-gen-memory infer
      // mediaType correctly via mime.getType().
      result = result.replace(fullMatch, `src="file://${imagePath}"`);
    } else {
      missingFiles.push(filename);
    }
  }
  result = stripMissingImageFigures(bookId, result, missingFiles);
  return result;
}

function stripMissingImageFigures(
  bookId: BookId,
  content: string,
  missingFiles: string[]
): string {
  let result = content;
  for (const filename of missingFiles) {
    const figureRegex = new RegExp(
      `<figure>\\s*<img[^>]*src="images/${filename.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&")}"[^>]*/>\\s*(?:<figcaption>([^<]*)</figcaption>)?\\s*</figure>`,
      "g"
    );
    result = result.replace(figureRegex, (_full, caption) =>
      caption ? `<p><em>[図: ${caption}]</em></p>` : ""
    );
    console.warn(`[${bookId}] missing image stripped: images/${filename}`);
  }
  return result;
}

async function buildEpub(bookId: BookId, config: BookConfig): Promise<void> {
  const outDir = join(ROOT, "dist", bookId);
  await mkdir(outDir, { recursive: true });
  const processor = createXhtmlProcessor();
  const epubChapters: Array<{ title: string; content: string }> = [];
  for (const chapterPath of await getChapterFiles(bookId)) {
    const chapter = await processMarkdown(chapterPath, processor, join(ROOT, bookDir(bookId)));
    // EPUB: rewrite image refs to file:// URLs so epub-gen-memory can fetch
    // them with proper mediaType inference (vs base64 data URIs which fail).
    const contentWithImages = await rewriteImagesToFileUrls(
      bookId,
      chapter.content
    );
    epubChapters.push({
      title: chapter.title,
      content: contentWithImages,
    });
  }
  const css = await loadCss();
  let coverPath = "";
  let coverExists = false;
  if (config.cover) {
    coverPath = join(ROOT, bookDir(bookId), config.cover);
    coverExists = await Bun.file(coverPath).exists();
  }
  const epubOptions: Parameters<typeof EPub>[0] = {
    title: config.title,
    author: config.author,
    lang: config.language,
    identifier: config.identifier,
    publisher: config.publisher,
    description: config.description,
    prependChapterTitles: false,
    css,
  };
  if (coverExists) {
    epubOptions.cover = coverPath;
  }
  const epub = await EPub(epubOptions, epubChapters);
  const outPath = join(outDir, EPUB_FILENAMES[bookId]);
  await Bun.write(outPath, epub);
  console.log(`[${bookId}] epub built → ${outPath}`);
}

async function copyImages(bookId: BookId, siteDir: string): Promise<void> {
  const srcImagesDir = join(ROOT, bookDir(bookId), "chapters", "images");
  const destImagesDir = join(siteDir, "images");
  const chapterImagesDir = join(siteDir, "chapters", "images");
  try {
    const files = await readdir(srcImagesDir);
    if (files.length === 0) return;
    await mkdir(destImagesDir, { recursive: true });
    await mkdir(chapterImagesDir, { recursive: true });
    for (const file of files) {
      const srcFile = Bun.file(join(srcImagesDir, file));
      await Bun.write(join(destImagesDir, file), srcFile);
      await Bun.write(join(chapterImagesDir, file), srcFile);
    }
  } catch {
    /* no images directory */
  }
}

async function buildSite(bookId: BookId, config: BookConfig): Promise<void> {
  const siteDir = join(ROOT, "dist", "site", bookId);
  const chaptersDir = join(siteDir, "chapters");
  await mkdir(siteDir, { recursive: true });
  await mkdir(chaptersDir, { recursive: true });

  const processor = createHtmlProcessor();
  const chapterFiles = await getChapterFiles(bookId);
  const chapters: Chapter[] = [];
  for (const chapterPath of chapterFiles) {
    chapters.push(await processMarkdown(chapterPath, processor, join(ROOT, bookDir(bookId))));
  }

  for (let i = 0; i < chapters.length; i++) {
    const chapter = chapters[i];
    const prev = i > 0 ? chapters[i - 1] : null;
    const next = i < chapters.length - 1 ? chapters[i + 1] : null;
    const nav = `
<nav class="chapter-nav">
  ${
    prev
      ? `<a href="${prev.filename}.html" class="prev">&larr; ${prev.title}</a>`
      : '<span class="prev"></span>'
  }
  <a href="../index.html" class="toc">目次</a>
  ${
    next
      ? `<a href="${next.filename}.html" class="next">${next.title} &rarr;</a>`
      : '<span class="next"></span>'
  }
</nav>`;
    const html = wrapHtmlWithNav(chapter.content, chapter.title, nav, config.title);
    await Bun.write(join(chaptersDir, `${chapter.filename}.html`), html);
  }

  const allContent = chapters
    .map((ch) => `<article id="${ch.filename}">\n${ch.content}\n</article>`)
    .join('\n<hr class="chapter-break">\n');
  const singleNav = `<nav class="chapter-nav"><a href="index.html" class="toc">← 目次</a> <a href="../index.html" class="toc">シリーズ一覧</a></nav>`;
  const singleHtml = wrapHtmlWithNav(
    allContent,
    `${config.title} - 全章`,
    singleNav,
    config.title
  );
  await Bun.write(join(siteDir, "single.html"), singleHtml);

  const tocItems = chapters
    .map(
      (ch) =>
        `    <li><a href="chapters/${ch.filename}.html">${ch.title}</a></li>`
    )
    .join("\n");
  const indexHtml = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${config.title}</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="book-header">
    <h1>${config.title}</h1>
    ${config.subtitle ? `<p class="subtitle">${config.subtitle}</p>` : ""}
    <p class="author">${config.author}</p>
  </header>
  <nav class="book-nav">
    <a href="single.html" class="single-page-link">全章を1ページで読む</a>
    <a href="${EPUB_FILENAMES[bookId]}" class="epub-link" download>EPUBをダウンロード</a>
    <a href="../index.html" class="toc">← シリーズ一覧へ</a>
  </nav>
  <main>
    <h2>目次</h2>
    <ol class="toc">
${tocItems}
    </ol>
  </main>
  <footer>
    <p>${config.publisher}</p>
  </footer>
</body>
</html>`;
  await Bun.write(join(siteDir, "index.html"), indexHtml);

  const css = await loadCss();
  await Bun.write(join(siteDir, "style.css"), css);
  await Bun.write(join(chaptersDir, "style.css"), css);

  const epubFilename = EPUB_FILENAMES[bookId];
  const epubSrc = join(ROOT, "dist", bookId, epubFilename);
  const epubFile = Bun.file(epubSrc);
  if (await epubFile.exists()) {
    await Bun.write(join(siteDir, epubFilename), epubFile);
  }

  await copyImages(bookId, siteDir);
  console.log(`[${bookId}] site built → ${siteDir}`);
}

async function buildLanding(): Promise<void> {
  const siteDir = join(ROOT, "dist", "site");
  await mkdir(siteDir, { recursive: true });

  const cards = await Promise.all(
    BOOKS.map(async (id) => {
      const cfg = await loadBookConfig(id);
      return `
    <article class="book">
      <h2>${cfg.title}</h2>
      ${cfg.subtitle ? `<p class="subtitle">${cfg.subtitle}</p>` : ""}
      <p class="description">${cfg.description.slice(0, 200)}...</p>
      <a class="read" href="${id}/index.html">目次へ →</a>
    </article>`;
    })
  );

  const landingHtml = `<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>迷わないポーカー シリーズ</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <header class="book-header">
    <h1>迷わないポーカー</h1>
    <p class="subtitle">暗算できる計算式で判断する、初級者〜中級者向けの書籍シリーズ</p>
  </header>
  <main class="landing">
${cards.join("\n")}
  </main>
  <footer>
    <p>ソース：<a href="https://github.com/cuzic/poker-books">cuzic/poker-books</a></p>
  </footer>
</body>
</html>`;

  await Bun.write(join(siteDir, "index.html"), landingHtml);
  await Bun.write(join(siteDir, "style.css"), await loadCss());
  console.log(`[landing] site index built → ${siteDir}/index.html`);
}

async function buildBook(bookId: BookId, format: OutputFormat): Promise<void> {
  const config = await loadBookConfig(bookId);
  console.log(`Building ${bookId} (format: ${format})...`);
  if (format === "all" || format === "html") await buildHtml(bookId);
  if (format === "all" || format === "xhtml") await buildXhtml(bookId);
  if (format === "all" || format === "epub" || format === "site") {
    await buildEpub(bookId, config);
  }
  if (format === "all" || format === "site") await buildSite(bookId, config);
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  let format: OutputFormat = "all";
  const formatIndex = args.indexOf("--format");
  if (formatIndex !== -1 && args[formatIndex + 1]) {
    const requested = args[formatIndex + 1] as OutputFormat;
    if (["html", "xhtml", "epub", "site", "all"].includes(requested)) {
      format = requested;
    }
  }

  let bookArg: BookId | "all" = "all";
  const bookIndex = args.indexOf("--book");
  if (bookIndex !== -1 && args[bookIndex + 1]) {
    const requested = args[bookIndex + 1] as BookId | "all";
    if (["preflop", "flop", "flop-advanced", "volume4", "volume5", "volume6", "digest", "all"].includes(requested)) {
      bookArg = requested;
    }
  }

  const targets: BookId[] = bookArg === "all" ? BOOKS : [bookArg];
  for (const id of targets) {
    await buildBook(id, format);
  }

  if (format === "all" || format === "site") {
    await buildLanding();
  }

  console.log("Build complete.");
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
