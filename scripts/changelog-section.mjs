// Prints the CHANGELOG.md section of a version (spec 009 REQ-721); exits 1 when it is missing,
// so a release cannot be published without notes. Usage: node scripts/changelog-section.mjs 0.3.0
import { readFileSync } from "node:fs";

const version = (process.argv[2] || "").replace(/^v/, "");
if (!version) {
  console.error("usage: changelog-section.mjs <version>");
  process.exit(2);
}

const lines = readFileSync(process.argv[3] || "CHANGELOG.md", "utf-8").split(/\r?\n/);
const heading = /^## \[([^\]]+)\]/;
const start = lines.findIndex((l) => heading.exec(l)?.[1] === version);
if (start < 0) {
  console.error(`CHANGELOG.md has no "## [${version}]" section`);
  process.exit(1);
}
let end = lines.findIndex((l, i) => i > start && heading.test(l));
if (end < 0) end = lines.length;
const body = lines.slice(start + 1, end).join("\n").trim();
if (!body) {
  console.error(`CHANGELOG.md section [${version}] is empty`);
  process.exit(1);
}
console.log(body);
