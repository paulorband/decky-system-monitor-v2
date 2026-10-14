import { Metrics } from "./api";

export const HISTORY_SIZE = 60;

export type HistoryKey = "cpu" | "gpu" | "ram";

// Lives outside React so history survives the QAM panel being closed and reopened.
const history: Record<HistoryKey, number[]> = { cpu: [], gpu: [], ram: [] };
let lastTs = 0;

function push(key: HistoryKey, value: number | null | undefined) {
  if (value == null) return;
  const buf = history[key];
  buf.push(value);
  if (buf.length > HISTORY_SIZE) buf.shift();
}

export function recordMetrics(m: Metrics) {
  if (m.ts === lastTs) return;
  lastTs = m.ts;
  push("cpu", m.cpu.usage);
  push("gpu", m.gpu?.usage);
  push("ram", m.memory.percent);
}

export function getHistory(key: HistoryKey): number[] {
  return history[key];
}
