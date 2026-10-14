import { Focusable } from "@decky/ui";
import { ReactNode, useState } from "react";

interface Props {
  title: string;
  color: string;
  headline: ReactNode;
  children?: ReactNode;
  details?: ReactNode;
}

/** A focusable card: D-pad moves between cards, A toggles the details section. */
export function MetricCard({ title, color, headline, children, details }: Props) {
  const [expanded, setExpanded] = useState(false);
  return (
    <Focusable
      className="ssm-card"
      focusClassName="ssm-focus"
      noFocusRing
      onActivate={details ? () => setExpanded(!expanded) : () => {}}
      onOKActionDescription={details ? (expanded ? "Recolher" : "Detalhes") : undefined}
    >
      <div className="ssm-card-head">
        <span className="ssm-card-title" style={{ color }}>
          {title}
          {details && <span className="ssm-card-chevron">{expanded ? "▲" : "▼"}</span>}
        </span>
        <span className="ssm-big">{headline}</span>
      </div>
      {children}
      {expanded && details && <div className="ssm-details">{details}</div>}
    </Focusable>
  );
}

export function Stat({ label, value, color }: { label: string; value: ReactNode; color?: string }) {
  return (
    <span className="ssm-stat">
      <span>{label}</span>
      <b style={color ? { color } : undefined}>{value}</b>
    </span>
  );
}
