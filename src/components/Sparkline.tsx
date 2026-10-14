import { HISTORY_SIZE } from "../store";

const W = HISTORY_SIZE - 1;
const H = 20;

/** Fixed 0–100 scale, newest sample on the right. */
export function Sparkline({ values, color }: { values: number[]; color: string }) {
  if (values.length < 2) return <svg className="ssm-spark" />;
  const offset = HISTORY_SIZE - values.length;
  const points = values
    .map((v, i) => `${offset + i},${(H - (Math.max(0, Math.min(100, v)) / 100) * H).toFixed(1)}`)
    .join(" ");
  const area = `${offset},${H} ${points} ${W},${H}`;
  return (
    <svg className="ssm-spark" viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <polygon points={area} fill={color} fillOpacity={0.18} />
      <polyline points={points} fill="none" stroke={color} strokeWidth={1.5} vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
