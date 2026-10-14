import { ButtonItem, DropdownItem, Navigation, PanelSection, PanelSectionRow } from "@decky/ui";
import { useQuickAccessVisible } from "@decky/api";
import { Metrics, getMetrics } from "../api";
import { Bar } from "../components/Bar";
import { MetricCard, Stat } from "../components/MetricCard";
import { Sparkline } from "../components/Sparkline";
import { SummaryStrip } from "../components/SummaryStrip";
import {
  COLORS,
  batteryColor,
  fmtBatteryStatus,
  fmtDuration,
  fmtFanLabel,
  fmtMb,
  fmtMhz,
  fmtPct,
  fmtTemp,
  fmtWatts,
  loadColor,
  tempColor,
} from "../format";
import { usePolling } from "../hooks/usePolling";
import { PROCESSES_ROUTE } from "../routes";
import { REFRESH_OPTIONS, usePersistentState } from "../settings";
import { getHistory, recordMetrics } from "../store";
import { CSS } from "../styles";

async function fetchAndRecord(): Promise<Metrics> {
  const m = await getMetrics();
  recordMetrics(m);
  return m;
}

function CpuCard({ m }: { m: Metrics }) {
  const cpu = m.cpu;
  const cols = Math.min(Math.max(cpu.per_core.length, 1), 8);
  return (
    <MetricCard
      title="CPU"
      color={COLORS.cpu}
      headline={<span style={{ color: loadColor(cpu.usage) }}>{fmtPct(cpu.usage)}</span>}
      details={
        <>
          <div className="ssm-cores" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
            {cpu.per_core.map((u, i) => (
              <div key={i} className="ssm-core" title={`CPU${i}`}>
                <div className="ssm-core-fill" style={{ height: `${u}%`, background: loadColor(u) }} />
              </div>
            ))}
          </div>
          <div className="ssm-stats">
            <Stat label="Load" value={cpu.load_avg ? cpu.load_avg.map((l) => l.toFixed(2)).join(" ") : "—"} />
            <Stat label="Máx" value={fmtMhz(cpu.freq_max_mhz)} />
          </div>
          {cpu.model && <div className="ssm-muted" style={{ marginTop: 4 }}>{cpu.model}</div>}
        </>
      }
    >
      <div className="ssm-stats">
        <Stat label="Temp" value={fmtTemp(cpu.temp_c)} color={tempColor(cpu.temp_c)} />
        <Stat label="Clock" value={fmtMhz(cpu.freq_mhz)} />
        {cpu.cores != null && <Stat label="Núcleos" value={cpu.cores} />}
      </div>
      <Bar percent={cpu.usage} />
      <Sparkline values={getHistory("cpu")} color={COLORS.cpu} />
    </MetricCard>
  );
}

function GpuCard({ m }: { m: Metrics }) {
  const gpu = m.gpu;
  if (!gpu) return null;
  const vramPct = gpu.vram_total_mb ? (gpu.vram_used_mb ?? 0) * 100 / gpu.vram_total_mb : null;
  const gttPct = gpu.gtt_total_mb ? (gpu.gtt_used_mb ?? 0) * 100 / gpu.gtt_total_mb : null;
  const hasMem = vramPct != null || gttPct != null;
  return (
    <MetricCard
      title={gpu.name ? `GPU ${gpu.name}` : "GPU"}
      color={COLORS.gpu}
      headline={<span style={{ color: loadColor(gpu.usage) }}>{fmtPct(gpu.usage)}</span>}
      details={
        hasMem ? (
          <>
            {vramPct != null && (
              <>
                <div className="ssm-sub">
                  <span>VRAM</span>
                  <span>{fmtMb(gpu.vram_used_mb)} / {fmtMb(gpu.vram_total_mb)}</span>
                </div>
                <Bar percent={vramPct} color={COLORS.gpu} />
              </>
            )}
            {gttPct != null && (
              <>
                <div className="ssm-sub">
                  <span>GTT (memória compartilhada)</span>
                  <span>{fmtMb(gpu.gtt_used_mb)} / {fmtMb(gpu.gtt_total_mb)}</span>
                </div>
                <Bar percent={gttPct} color={COLORS.gpu} />
              </>
            )}
          </>
        ) : undefined
      }
    >
      <div className="ssm-stats">
        <Stat label="Temp" value={fmtTemp(gpu.temp_c)} color={tempColor(gpu.temp_c)} />
        <Stat label="Clock" value={fmtMhz(gpu.freq_mhz)} />
        <Stat label="APU" value={fmtWatts(gpu.power_w)} />
      </div>
      <Bar percent={gpu.usage} />
      <Sparkline values={getHistory("gpu")} color={COLORS.gpu} />
    </MetricCard>
  );
}

function MemoryCard({ m }: { m: Metrics }) {
  const mem = m.memory;
  return (
    <MetricCard
      title="Memória"
      color={COLORS.ram}
      headline={<span style={{ color: loadColor(mem.percent) }}>{fmtPct(mem.percent)}</span>}
    >
      <div className="ssm-sub">
        <span>RAM</span>
        <span>{fmtMb(mem.used_mb)} / {fmtMb(mem.total_mb)}</span>
      </div>
      <Bar percent={mem.percent} />
      {mem.swap_total_mb > 0 && (
        <>
          <div className="ssm-sub">
            <span>Swap</span>
            <span>{fmtMb(mem.swap_used_mb)} / {fmtMb(mem.swap_total_mb)}</span>
          </div>
          <Bar percent={mem.swap_percent} />
        </>
      )}
    </MetricCard>
  );
}

function BatteryCard({ m }: { m: Metrics }) {
  const bat = m.battery;
  if (!bat) return null;
  const charging = bat.status === "Charging";
  return (
    <MetricCard
      title="Bateria"
      color={COLORS.battery}
      headline={<span style={{ color: batteryColor(bat.percent) }}>{fmtPct(bat.percent)}</span>}
      details={
        bat.health_percent != null ? (
          <div className="ssm-stats">
            <Stat label="Saúde" value={fmtPct(bat.health_percent, 1)} />
          </div>
        ) : undefined
      }
    >
      <div className="ssm-stats">
        <Stat label="" value={fmtBatteryStatus(bat.status)} />
        <Stat label={charging ? "Entrada" : "Consumo"} value={fmtWatts(bat.power_w)} />
        {bat.time_left_min != null && (
          <Stat label={charging ? "Cheia em" : "Restam"} value={fmtDuration(bat.time_left_min)} />
        )}
      </div>
      <Bar percent={bat.percent} color={batteryColor(bat.percent)} />
    </MetricCard>
  );
}

function FansCard({ m }: { m: Metrics }) {
  if (!m.fans.length) return null;
  return (
    <MetricCard title="Ventoinhas" color={COLORS.muted} headline={null}>
      <div className="ssm-stats">
        {m.fans.map((f, i) => (
          <Stat key={i} label={fmtFanLabel(f.label, i, m.fans.length)} value={`${f.rpm} RPM`} />
        ))}
      </div>
    </MetricCard>
  );
}

export function Dashboard() {
  const visible = useQuickAccessVisible();
  const [refreshMs, setRefreshMs] = usePersistentState<number>("refreshMs", 1000);
  const { data: m, error } = usePolling(fetchAndRecord, refreshMs, visible);

  const openProcesses = () => {
    Navigation.Navigate(PROCESSES_ROUTE);
    Navigation.CloseSideMenus();
  };

  return (
    <>
      <style>{CSS}</style>
      <PanelSection>
        <PanelSectionRow>
          <ButtonItem layout="below" onClick={openProcesses}>
            Gerenciador de processos
          </ButtonItem>
        </PanelSectionRow>
        {error && <div className="ssm-error">Erro ao ler métricas: {error}</div>}
        {!m && !error && <div className="ssm-muted">Carregando…</div>}
        {m && (
          <>
            <SummaryStrip m={m} />
            <CpuCard m={m} />
            <GpuCard m={m} />
            <MemoryCard m={m} />
            <BatteryCard m={m} />
            <FansCard m={m} />
          </>
        )}
      </PanelSection>
      <PanelSection title="Configurações">
        <PanelSectionRow>
          <DropdownItem
            label="Atualização"
            rgOptions={REFRESH_OPTIONS}
            selectedOption={refreshMs}
            onChange={(opt) => setRefreshMs(opt.data as number)}
          />
        </PanelSectionRow>
      </PanelSection>
    </>
  );
}
