import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const checkMode = process.argv.includes("--check");
const assetsDir = join(dirname(fileURLToPath(import.meta.url)), "..", "dist", "assets");

const budgets = [
  { pattern: /^react-.*\.js$/, maxBytes: 700_000 },
  { pattern: /^icons-.*\.js$/, maxBytes: 500_000 },
  { pattern: /^vendor-.*\.js$/, maxBytes: 700_000 },
  { pattern: /.*\.js$/, maxBytes: 500_000 },
];

function budgetFor(fileName) {
  return budgets.find((budget) => budget.pattern.test(fileName));
}

function formatBytes(bytes) {
  return `${(bytes / 1024).toFixed(1)} KiB`;
}

if (!existsSync(assetsDir)) {
  console.error("No built frontend assets found. Run `npm --prefix frontend run build` first.");
  process.exit(1);
}

const chunks = readdirSync(assetsDir)
  .filter((fileName) => fileName.endsWith(".js"))
  .map((fileName) => {
    const filePath = join(assetsDir, fileName);
    const size = statSync(filePath).size;
    const gzipSize = gzipSync(readFileSync(filePath)).byteLength;
    return { fileName, size, gzipSize, budget: budgetFor(fileName) };
  })
  .sort((left, right) => right.size - left.size);

console.log("Largest frontend chunks:");
for (const chunk of chunks.slice(0, 10)) {
  const max = chunk.budget ? ` / budget ${formatBytes(chunk.budget.maxBytes)}` : "";
  console.log(`- ${chunk.fileName}: ${formatBytes(chunk.size)} raw, ${formatBytes(chunk.gzipSize)} gzip${max}`);
}

const failures = chunks.filter((chunk) => chunk.budget && chunk.size > chunk.budget.maxBytes);
if (checkMode && failures.length > 0) {
  console.error("\nBundle budget exceeded:");
  for (const failure of failures) {
    console.error(`- ${failure.fileName}: ${formatBytes(failure.size)} > ${formatBytes(failure.budget.maxBytes)}`);
  }
  process.exitCode = 1;
}
