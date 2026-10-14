import { callable } from "@decky/api";

// Mirrors the get_metrics() contract (specs/001-coletor-metricas).
export interface CpuMetrics {
  usage: number | null;
  per_core: number[];
  temp_c: number | null;
  freq_mhz: number | null;
  freq_max_mhz: number | null;
  cores: number | null;
  model: string | null;
  load_avg: number[] | null;
}

export interface GpuMetrics {
  name: string | null;
  usage: number | null;
  temp_c: number | null;
  freq_mhz: number | null;
  vram_used_mb: number | null;
  vram_total_mb: number | null;
  gtt_used_mb: number | null;
  gtt_total_mb: number | null;
  power_w: number | null;
}

export interface MemoryMetrics {
  total_mb: number;
  used_mb: number;
  available_mb: number;
  percent: number | null;
  swap_total_mb: number;
  swap_used_mb: number;
  swap_percent: number;
}

export interface BatteryMetrics {
  percent: number | null;
  status: string | null;
  power_w: number | null;
  time_left_min: number | null;
  health_percent: number | null;
}

export interface Fan {
  /** Driver label (e.g. "cpu_fan"); null when the driver provides none. */
  label: string | null;
  rpm: number;
}

export interface Metrics {
  ts: number;
  uptime_s: number | null;
  cpu: CpuMetrics;
  gpu: GpuMetrics | null;
  memory: MemoryMetrics;
  battery: BatteryMetrics | null;
  fans: Fan[];
}

export const getMetrics = callable<[], Metrics>("get_metrics");

// Mirrors the get_processes() contract (specs/003-gerenciador-processos).
export type SortKey = "name" | "cpu" | "mem";

export interface ProcessInfo {
  pid: number;
  name: string;
  cmd: string;
  cpu: number;
  mem_mb: number;
  mem_percent: number | null;
  threads: number;
  state: string;
  ppid: number;
}

/** A process, or a group of same-named processes (specs/005-agrupamento-processos). */
export interface ProcessItem extends ProcessInfo {
  key: string;
  count: number;
  members: ProcessInfo[];
}

export interface ProcessList {
  total: number;
  shown: number;
  process_count: number;
  cpu_count: number;
  mem_total_mb: number | null;
  processes: ProcessItem[];
}

export const getProcesses = callable<[SortKey, boolean, number, boolean, boolean], ProcessList>("get_processes");
