import deckyPlugin from "@decky/rollup";
import { readdirSync, readFileSync } from "node:fs";
import { basename, join } from "node:path";

const LOCALES_DIR = "src/locales";
const VIRTUAL_LOCALES = "virtual:locales";
const RESOLVED_LOCALES = "\0" + VIRTUAL_LOCALES;

// Bundles every src/locales/*.json as `import locales from "virtual:locales"`,
// so adding a language is just dropping a new JSON file there (specs/007-multi-idioma).
function locales() {
  return {
    name: "ssm-locales",
    resolveId(id) {
      return id === VIRTUAL_LOCALES ? RESOLVED_LOCALES : null;
    },
    load(id) {
      if (id !== RESOLVED_LOCALES) return null;
      this.addWatchFile(LOCALES_DIR);
      const all = {};
      for (const file of readdirSync(LOCALES_DIR).filter((f) => f.endsWith(".json")).sort()) {
        const path = join(LOCALES_DIR, file);
        this.addWatchFile(path);
        all[basename(file, ".json")] = JSON.parse(readFileSync(path, "utf-8"));
      }
      return `export default ${JSON.stringify(all)};`;
    },
  };
}

export default deckyPlugin({ plugins: [locales()] });
