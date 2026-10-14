import { Metrics } from "../api";
import { batteryColor, fmtPct, loadColor } from "../format";

function Tile({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="ssm-tile">
      <div className="ssm-tile-label">{label}</div>
      <div className="ssm-tile-value" style={{ color }}>
        {value}
      </div>
    </div>
  );
}

export function SummaryStrip({ m }: { m: Metrics }) {
  return (
    <div className="ssm-strip">
      <Tile label="CPU" value={fmtPct(m.cpu.usage)} color={loadColor(m.cpu.usage)} />
      <Tile label="GPU" value={fmtPct(m.gpu?.usage)} color={loadColor(m.gpu?.usage)} />
      <Tile label="RAM" value={fmtPct(m.memory.percent)} color={loadColor(m.memory.percent)} />
      <Tile label="BAT" value={fmtPct(m.battery?.percent)} color={batteryColor(m.battery?.percent)} />
    </div>
  );
}
