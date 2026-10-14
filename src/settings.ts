import { useState } from "react";

const PREFIX = "steam-system-monitor:";

export function loadSetting<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(PREFIX + key);
    return raw == null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

export function saveSetting<T>(key: string, value: T) {
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    // storage unavailable: setting just won't persist
  }
}

export function usePersistentState<T>(key: string, fallback: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => loadSetting(key, fallback));
  const update = (next: T) => {
    setValue(next);
    saveSetting(key, next);
  };
  return [value, update];
}

export const REFRESH_INTERVALS_MS = [500, 1000, 2000, 5000];
