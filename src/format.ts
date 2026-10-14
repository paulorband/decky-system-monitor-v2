import { fmtNumber, t } from "./i18n";

export const DASH = "—";

export const COLORS = {
  ok: "#5ed47a",
  warn: "#f5c542",
  crit: "#ff5c5c",
  muted: "#8b929a",
  cpu: "#4fb0ff",
  gpu: "#b083ff",
  ram: "#3fd0c9",
  battery: "#5ed47a",
};

export function loadColor(percent: number | null | undefined): string {
  if (percent == null) return COLORS.muted;
  if (percent > 85) return COLORS.crit;
  if (percent >= 60) return COLORS.warn;
  return COLORS.ok;
}

export function tempColor(celsius: number | null | undefined): string {
  if (celsius == null) return COLORS.muted;
  if (celsius > 85) return COLORS.crit;
  if (celsius >= 70) return COLORS.warn;
  return COLORS.ok;
}

/** Battery is inverted: low charge is the problem. */
export function batteryColor(percent: number | null | undefined): string {
  if (percent == null) return COLORS.muted;
  if (percent < 15) return COLORS.crit;
  if (percent < 30) return COLORS.warn;
  return COLORS.ok;
}

export function fmtPct(v: number | null | undefined, digits = 0): string {
  return v == null ? DASH : `${fmtNumber(v, digits)}%`;
}

export function fmtTemp(v: number | null | undefined): string {
  return v == null ? DASH : `${Math.round(v)}°C`;
}

export function fmtMhz(v: number | null | undefined): string {
  if (v == null) return DASH;
  return v >= 1000 ? `${fmtNumber(v / 1000, 2)} GHz` : `${fmtNumber(v)} MHz`;
}

export function fmtWatts(v: number | null | undefined): string {
  return v == null ? DASH : `${fmtNumber(v, 1)} W`;
}

export function fmtMb(v: number | null | undefined): string {
  if (v == null) return DASH;
  return v >= 1024 ? `${fmtNumber(v / 1024, 1)} GB` : `${fmtNumber(v)} MB`;
}

export function fmtDuration(minutes: number | null | undefined): string {
  if (minutes == null) return DASH;
  const h = Math.floor(minutes / 60);
  const m = Math.round(minutes % 60);
  return h > 0 ? `${h}h ${m.toString().padStart(2, "0")}m` : `${m}m`;
}

const BATTERY_STATUS_KEYS: Record<string, string> = {
  Charging: "battery.status.Charging",
  Discharging: "battery.status.Discharging",
  Full: "battery.status.Full",
  "Not charging": "battery.status.NotCharging",
  Unknown: "battery.status.Unknown",
};

export function fmtBatteryStatus(status: string | null | undefined): string {
  if (!status) return DASH;
  const key = BATTERY_STATUS_KEYS[status];
  return key ? t(key) : status;
}

/** Friendly fan name: known driver labels are translated; unlabeled fans become
 *  "Fan" (numbered when there is more than one). */
export function fmtFanLabel(label: string | null, index: number, total: number): string {
  if (label === "cpu_fan") return "CPU";
  if (label === "gpu_fan") return "GPU";
  if (label === "mid_fan") return t("fans.mid");
  if (label) return label;
  return total > 1 ? t("fans.fanNumbered", { n: index + 1 }) : t("fans.fan");
}
