// Pure language matching, kept free of imports so scripts/check-locales.mjs can test it with Node.

export interface LocaleMeta {
  name: string;
  steamLanguages: string[];
}

/** Steam language name ("brazilian", "latam"...) or BCP 47 tag ("pt-BR") -> supported locale code. */
export function matchLanguage(lang: string | null | undefined, metas: Record<string, LocaleMeta>, fallback = "en"): string {
  if (!lang) return fallback;
  const value = lang.toLowerCase();
  const codes = Object.keys(metas);
  for (const code of codes) {
    if (metas[code].steamLanguages.some((s) => s.toLowerCase() === value)) return code;
  }
  const exact = codes.find((code) => code.toLowerCase() === value);
  if (exact) return exact;
  const prefix = value.split(/[-_]/)[0];
  return codes.find((code) => code.toLowerCase().split("-")[0] === prefix) ?? fallback;
}
