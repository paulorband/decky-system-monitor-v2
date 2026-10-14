import { useEffect, useState } from "react";
import rawLocales from "virtual:locales";
import { LocaleMeta, matchLanguage as matchSupported } from "./i18n-match";
import { loadSetting, saveSetting } from "./settings";

// Translations live in src/locales/<code>.json (specs/007-multi-idioma).

type Locale = Record<string, string>;

const FALLBACK = "en";
const AUTO = "auto";
const PREF_KEY = "language";

const locales: Record<string, Locale> = {};
const metas: Record<string, LocaleMeta> = {};
for (const [code, file] of Object.entries(rawLocales)) {
  const { _meta, ...strings } = file as { _meta: LocaleMeta } & Record<string, string>;
  locales[code] = strings;
  metas[code] = _meta;
}

export function matchLanguage(lang: string | null | undefined): string {
  return matchSupported(lang, metas, FALLBACK);
}

async function steamLanguage(): Promise<string | null> {
  const w = window as unknown as {
    SteamClient?: { Settings?: { GetCurrentLanguage?: () => Promise<string> } };
    LocalizationManager?: { m_rgLocalesToUse?: string[] };
  };
  try {
    const lang = await w.SteamClient?.Settings?.GetCurrentLanguage?.();
    if (lang) return lang;
  } catch {
    // older clients: fall through
  }
  return w.LocalizationManager?.m_rgLocalesToUse?.[0] ?? navigator.language ?? null;
}

// ---------------------------------------------------------------- store

let preference: string = loadSetting<string>(PREF_KEY, AUTO);
let steamDetected: string = FALLBACK;
let current: string = preference !== AUTO && locales[preference] ? preference : FALLBACK;
const listeners = new Set<() => void>();
const numberFormats = new Map<string, Intl.NumberFormat>();

function apply() {
  const next = preference !== AUTO && locales[preference] ? preference : steamDetected;
  if (next === current) return;
  current = next;
  numberFormats.clear();
  listeners.forEach((l) => l());
}

/** Called once when the plugin loads; resolves the Steam UI language for "auto". */
export async function initI18n() {
  steamDetected = matchLanguage(await steamLanguage());
  apply();
}

export function setLanguagePreference(pref: string) {
  preference = pref;
  saveSetting(PREF_KEY, pref);
  apply();
  listeners.forEach((l) => l()); // the selector shows the preference even if the language is unchanged
}

/** Translate `key`, falling back to English, then to the key itself; `{name}` placeholders are replaced. */
export function t(key: string, params?: Record<string, string | number>): string {
  let text = locales[current]?.[key] ?? locales[FALLBACK]?.[key] ?? key;
  if (params) {
    for (const [name, value] of Object.entries(params)) text = text.split(`{${name}}`).join(String(value));
  }
  return text;
}

/** Locale-aware number with a fixed number of decimals ("0,5" in pt-BR, "0.5" in en). */
export function fmtNumber(value: number, digits = 0): string {
  const cacheKey = `${digits}`;
  let nf = numberFormats.get(cacheKey);
  if (!nf) {
    try {
      nf = new Intl.NumberFormat(current, { minimumFractionDigits: digits, maximumFractionDigits: digits });
    } catch {
      nf = new Intl.NumberFormat("en", { minimumFractionDigits: digits, maximumFractionDigits: digits });
    }
    numberFormats.set(cacheKey, nf);
  }
  return nf.format(value);
}

export interface LanguageOption {
  code: string;
  name: string;
}

export const AUTO_LANGUAGE = AUTO;

export function availableLanguages(): LanguageOption[] {
  return Object.entries(metas)
    .map(([code, meta]) => ({ code, name: meta.name }))
    .sort((a, b) => a.name.localeCompare(b.name));
}

/** Re-renders the component when the language changes. */
export function useI18n() {
  const [, setTick] = useState(0);
  useEffect(() => {
    const listener = () => setTick((n) => n + 1);
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  }, []);
  return { t, language: current, preference };
}
