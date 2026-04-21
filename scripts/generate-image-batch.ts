import { join } from "node:path";
import { mkdir } from "node:fs/promises";
import { z } from "zod";

// Gemini Batch API Schema (Official)
// https://ai.google.dev/gemini-api/docs/batch-api
// https://ai.google.dev/gemini-api/docs/image-generation

const AspectRatioSchema = z.enum([
  "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"
]);
const ImageSizeSchema = z.enum(["1K", "2K", "4K"]);
const ResponseModalitiesSchema = z.array(z.enum(["TEXT", "IMAGE"])).min(1);
const ImageConfigSchema = z.object({
  aspectRatio: AspectRatioSchema,
  imageSize: ImageSizeSchema,
});
const GenerationConfigSchema = z.object({
  responseModalities: ResponseModalitiesSchema,
  imageConfig: ImageConfigSchema,
});
const PartSchema = z.object({ text: z.string().min(1) });
const ContentSchema = z.object({ parts: z.array(PartSchema).min(1) });
const RequestSchema = z.object({
  contents: z.array(ContentSchema).min(1),
  generation_config: GenerationConfigSchema,
});
const BatchRequestSchema = z.object({
  key: z
    .string()
    .min(1)
    .regex(/^[a-zA-Z0-9_-]+$/, "key must be alphanumeric with underscores/hyphens"),
  request: RequestSchema,
});
type BatchRequest = z.infer<typeof BatchRequestSchema>;

const ImageDefinitionSchema = z.object({
  name: z.string().min(1),
  prompt: z.string().min(1),
  aspectRatio: z.enum(["16:9", "4:3", "1:1", "3:4", "9:16"]),
  chapter: z.string().min(1),
  section: z.string().min(1),
  description: z.string().min(1),
});
type ImageDefinition = z.infer<typeof ImageDefinitionSchema>;

const ROOT = join(import.meta.dir, "..");
const BOOKS = ["preflop", "flop"] as const;
type BookId = (typeof BOOKS)[number];

async function generateForBook(bookId: BookId): Promise<void> {
  const configPath = join(ROOT, bookId, "images.json");
  const file = Bun.file(configPath);
  if (!(await file.exists())) {
    console.log(`[${bookId}] images.json not found, skipping.`);
    return;
  }

  const rawData = await file.json();
  const parseResult = z.array(ImageDefinitionSchema).safeParse(rawData);
  if (!parseResult.success) {
    console.error(`[${bookId}] Invalid images.json format`);
    console.error(parseResult.error.format());
    process.exit(1);
  }

  const images = parseResult.data;
  const batchRequests: string[] = [];

  for (const image of images) {
    const batchRequest: BatchRequest = {
      key: image.name,
      request: {
        contents: [{ parts: [{ text: image.prompt }] }],
        generation_config: {
          responseModalities: ["IMAGE"],
          imageConfig: { aspectRatio: image.aspectRatio, imageSize: "2K" },
        },
      },
    };
    const v = BatchRequestSchema.safeParse(batchRequest);
    if (!v.success) {
      console.error(`[${bookId}] validation failed for ${image.name}: ${v.error.message}`);
      process.exit(1);
    }
    batchRequests.push(JSON.stringify(v.data));
  }

  const outDir = join(ROOT, "dist", bookId);
  await mkdir(outDir, { recursive: true });
  const outputPath = join(outDir, "batch-requests.jsonl");
  await Bun.write(outputPath, batchRequests.join("\n") + "\n");

  console.log(`[${bookId}] batch requests: ${outputPath}`);
  console.log(`[${bookId}] total images: ${images.length}`);
}

async function main() {
  const args = process.argv.slice(2);
  let target: BookId | "all" = "all";
  const bookIdx = args.indexOf("--book");
  if (bookIdx !== -1 && args[bookIdx + 1]) {
    const requested = args[bookIdx + 1] as BookId | "all";
    if (["preflop", "flop", "all"].includes(requested)) target = requested;
  }
  const targets: BookId[] = target === "all" ? [...BOOKS] : [target];
  for (const id of targets) await generateForBook(id);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
