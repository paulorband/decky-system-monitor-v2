import { loadColor } from "../format";

export function Bar({ percent, color }: { percent: number | null | undefined; color?: string }) {
  const width = Math.max(0, Math.min(100, percent ?? 0));
  return (
    <div className="ssm-bar">
      <div className="ssm-bar-fill" style={{ width: `${width}%`, background: color ?? loadColor(percent) }} />
    </div>
  );
}
