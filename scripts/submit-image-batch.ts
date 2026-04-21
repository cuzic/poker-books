import { join } from "node:path";
import { mkdir } from "node:fs/promises";

const BASE_URL = "https://generativelanguage.googleapis.com";
const MODEL = "gemini-3-pro-image-preview";
const ROOT = join(import.meta.dir, "..");
const BOOKS = ["preflop", "flop"] as const;
type BookId = (typeof BOOKS)[number];

async function uploadFile(apiKey: string, filePath: string, displayName: string) {
  const file = Bun.file(filePath);
  const content = await file.text();
  const numBytes = new TextEncoder().encode(content).length;

  const startResponse = await fetch(`${BASE_URL}/upload/v1beta/files`, {
    method: "POST",
    headers: {
      "x-goog-api-key": apiKey,
      "X-Goog-Upload-Protocol": "resumable",
      "X-Goog-Upload-Command": "start",
      "X-Goog-Upload-Header-Content-Length": numBytes.toString(),
      "X-Goog-Upload-Header-Content-Type": "text/plain",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ file: { display_name: displayName } }),
  });
  if (!startResponse.ok) throw new Error(`Failed to start upload: ${await startResponse.text()}`);
  const uploadUrl = startResponse.headers.get("X-Goog-Upload-URL");
  if (!uploadUrl) throw new Error("No upload URL returned");

  const uploadResponse = await fetch(uploadUrl, {
    method: "PUT",
    headers: {
      "X-Goog-Upload-Command": "upload, finalize",
      "X-Goog-Upload-Offset": "0",
      "Content-Type": "text/plain",
    },
    body: content,
  });
  if (!uploadResponse.ok) throw new Error(`Failed to upload file: ${await uploadResponse.text()}`);
  return uploadResponse.json() as Promise<{
    file: { name: string; uri: string };
  }>;
}

async function createBatchJob(apiKey: string, fileName: string, displayName: string) {
  const response = await fetch(
    `${BASE_URL}/v1beta/models/${MODEL}:batchGenerateContent`,
    {
      method: "POST",
      headers: {
        "x-goog-api-key": apiKey,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        batch: {
          display_name: displayName,
          input_config: { file_name: fileName },
        },
      }),
    }
  );
  if (!response.ok) throw new Error(`Failed to create batch job: ${await response.text()}`);
  return response.json() as Promise<{ name: string; state: string }>;
}

async function submitBook(apiKey: string, bookId: BookId) {
  const batchFilePath = join(ROOT, "dist", bookId, "batch-requests.jsonl");
  if (!(await Bun.file(batchFilePath).exists())) {
    console.log(`[${bookId}] batch-requests.jsonl not found, skipping. Run generate-image-batch first.`);
    return;
  }

  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const displayName = `${bookId}-images-${timestamp}`;

  console.log(`[${bookId}] uploading ${batchFilePath}...`);
  const uploadResult = await uploadFile(apiKey, batchFilePath, displayName);
  console.log(`[${bookId}] uploaded: ${uploadResult.file.name}`);

  console.log(`[${bookId}] creating batch job...`);
  const batchJob = await createBatchJob(apiKey, uploadResult.file.name, displayName);
  console.log(`[${bookId}] batch job: ${batchJob.name} (${batchJob.state})`);

  const outDir = join(ROOT, "dist", bookId);
  await mkdir(outDir, { recursive: true });
  const jobInfoPath = join(outDir, "batch-job.json");
  await Bun.write(
    jobInfoPath,
    JSON.stringify(
      {
        name: batchJob.name,
        state: batchJob.state,
        fileName: uploadResult.file.name,
        fileUri: uploadResult.file.uri,
        displayName,
        bookId,
        createdAt: new Date().toISOString(),
      },
      null,
      2
    )
  );
  console.log(`[${bookId}] job info: ${jobInfoPath}`);
}

async function main() {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    console.error("Error: GEMINI_API_KEY environment variable is not set");
    process.exit(1);
  }

  const args = process.argv.slice(2);
  let target: BookId | "all" = "all";
  const bookIdx = args.indexOf("--book");
  if (bookIdx !== -1 && args[bookIdx + 1]) {
    const requested = args[bookIdx + 1] as BookId | "all";
    if (["preflop", "flop", "all"].includes(requested)) target = requested;
  }
  const targets: BookId[] = target === "all" ? [...BOOKS] : [target];
  for (const id of targets) await submitBook(apiKey, id);

  console.log("\nUse `bun run images:status` to poll.");
  console.log("Use `bun run images:download` to fetch results.");
}

main().catch((err) => {
  console.error("Error:", err.message);
  process.exit(1);
});
