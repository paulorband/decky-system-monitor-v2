import { useState } from "react";

const PREFIX = "steam-system-monitor:";

function load<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(PREFIX + key);
    return raw == null ? fallback : (JSON.parse(raw) as T);
  } catch {
    return fallback;
  }
}

function save<T>(key: string, value: T) {
  try {
    window.localStorage.setItem(PREFIX + key, JSON.stringify(value));
  } catch {
    // storage unavailable: setting just won't persist
  }
}

export function usePersistentState<T>(key: string, fallback: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => load(key, fallback));
  const update = (next: T) => {
    setValue(next);
    save(key, next);
  };
  return [value, update];
}

export const REFRESH_OPTIONS = [
  { data: 500, label: "0,5 s" },
  { data: 1000, label: "1 s" },
  { data: 2000, label: "2 s" },
  { data: 5000, label: "5 s" },
];
