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
  label: string;
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
