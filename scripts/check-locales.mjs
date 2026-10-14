// Validates src/locales/*.json against en.json (specs/007-multi-idioma, FR-9) and
// exercises the Steam language matching. Run with: pnpm check:i18n
import { readdirSync, readFileSync } from "node:fs";
import { basename, join } from "node:path";
import { matchLanguage } from "../src/i18n-match.ts";

const DIR = "src/locales";
const REFERENCE = "en";
const errors = [];

const locales = {};
for (const file of readdirSync(DIR).filter((f) => f.endsWith(".json")).sort()) {
  try {
    locales[basename(file, ".json")] = JSON.parse(readFileSync(join(DIR, file), "utf-8"));
  } catch (e) {
    errors.push(`${file}: invalid JSON (${e.message})`);
  }
}

const params = (text) => [...String(text).matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort().join(",");
const ref = locales[REFERENCE];
if (!ref) errors.push(`${REFERENCE}.json (reference) is missing`);

const claimed = new Map();
for (const [code, data] of Object.entries(locales)) {
  const meta = data._meta;
  if (!meta || typeof meta.name !== "string" || !Array.isArray(meta.steamLanguages)) {
    errors.push(`${code}: "_meta" needs "name" and "steamLanguages"`);
  } else {
    for (const lang of meta.steamLanguages) {
      if (claimed.has(lang)) errors.push(`${code}: Steam language "${lang}" already used by ${claimed.get(lang)}`);
      claimed.set(lang, code);
    }
  }
  if (!ref || code === REFERENCE) continue;
  for (const key of Object.keys(ref)) {
    if (key === "_meta") continue;
    if (!(key in data)) errors.push(`${code}: missing "${key}"`);
    else if (params(data[key]) !== params(ref[key])) errors.push(`${code}: "${key}" placeholders differ from ${REFERENCE}`);
  }
  for (const key of Object.keys(data)) {
    if (key !== "_meta" && !(key in ref)) errors.push(`${code}: extra key "${key}" (not in ${REFERENCE}.json)`);
  }
}

// Steam language detection (AC-4)
const metas = Object.fromEntries(Object.entries(locales).map(([code, d]) => [code, d._meta ?? { name: code, steamLanguages: [] }]));
const expectations = {
  brazilian: "pt-BR", portuguese: "pt-BR", english: "en", spanish: "es", latam: "es",
  german: "en", "pt-BR": "pt-BR", "es-MX": "es", "en-US": "en", "": "en",
};
for (const [input, expected] of Object.entries(expectations)) {
  if (!locales[expected]) continue;
  const got = matchLanguage(input, metas);
  if (got !== expected) errors.push(`matchLanguage("${input}") = "${got}", expected "${expected}"`);
}

if (errors.length) {
  console.error(`✗ ${errors.length} problem(s):\n  ` + errors.join("\n  "));
  process.exit(1);
}
console.log(`✓ ${Object.keys(locales).join(", ")} — ${Object.keys(ref).length - 1} keys each, language matching ok`);
