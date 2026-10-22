// Writes out/release.json describing out/steam-system-monitor.zip (spec 010 REQ-800/805).
// Usage: node scripts/release-manifest.mjs <tag> <commit> [notes-file]
//   tag: vX.Y.Z for a release, "test-build" for the rolling test build.
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";

const [tag, commit, notesFile] = process.argv.slice(2);
if (!tag || !commit) {
  console.error("usage: release-manifest.mjs <tag> <commit> [notes-file]");
  process.exit(2);
}
const version = JSON.parse(readFileSync("package.json", "utf-8")).version;
if (tag !== "test-build" && tag !== `v${version}`) {
  console.error(`tag ${tag} != v${version} (package.json)`);
  process.exit(1);
}

const ASSET = "steam-system-monitor.zip";
const zip = readFileSync(`out/${ASSET}`);
const manifest = {
  schema: 1,
  tag,
  version,
  kind: tag === "test-build" ? "test" : "stable",
  commit,
  asset: ASSET,
  sha256: createHash("sha256").update(zip).digest("hex"),
  size: zip.length,
  notes: notesFile ? readFileSync(notesFile, "utf-8").slice(0, 8000) : "",
};
writeFileSync("out/release.json", JSON.stringify(manifest, null, 2) + "\n");
console.log(`out/release.json: ${tag} ${manifest.sha256} (${zip.length} bytes)`);
