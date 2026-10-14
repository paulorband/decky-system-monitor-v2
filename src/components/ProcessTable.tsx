import { Focusable } from "@decky/ui";
import { ProcessInfo, SortKey } from "../api";
import { fmtMb, fmtPct, loadColor } from "../format";

const STATE_LABELS: Record<string, string> = {
  R: "Executando",
  S: "Dormindo",
  D: "Aguardando E/S",
  Z: "Zumbi",
  T: "Parado",
  t: "Rastreado",
  I: "Ocioso",
};

interface HeaderProps {
  sortKey: SortKey;
  descending: boolean;
  onSort: (key: SortKey) => void;
}

function HeaderCell({ label, k, align, props }: { label: string; k: SortKey; align?: "right"; props: HeaderProps }) {
  const active = props.sortKey === k;
  return (
    <Focusable
      className={`ssm-th ssm-th-sortable${active ? " ssm-th-active" : ""}`}
      focusClassName="ssm-th-focus"
      noFocusRing
      style={align ? { justifyContent: "flex-end" } : undefined}
      onActivate={() => props.onSort(k)}
      onOKActionDescription={active ? "Inverter ordem" : `Ordenar por ${label}`}
    >
      {label}
      <span className="ssm-th-arrow">{active ? (props.descending ? "▼" : "▲") : ""}</span>
    </Focusable>
  );
}

export function ProcessTableHeader(props: HeaderProps) {
  return (
    <Focusable flow-children="row" className="ssm-tr ssm-thead">
      <HeaderCell label="Processo" k="name" props={props} />
      <div className="ssm-th ssm-num">PID</div>
      <HeaderCell label="CPU" k="cpu" align="right" props={props} />
      <HeaderCell label="RAM" k="mem" align="right" props={props} />
    </Focusable>
  );
}

interface RowProps {
  p: ProcessInfo;
  index: number;
  expanded: boolean;
  onToggle: (pid: number) => void;
}

export function ProcessRow({ p, index, expanded, onToggle }: RowProps) {
  return (
    <Focusable
      className={`ssm-row${index % 2 ? " ssm-row-odd" : ""}`}
      focusClassName="ssm-row-focus"
      noFocusRing
      onActivate={() => onToggle(p.pid)}
      onOKActionDescription={expanded ? "Recolher" : "Detalhes"}
    >
      <div className="ssm-tr">
        <div className="ssm-td ssm-name">{p.name}</div>
        <div className="ssm-td ssm-num ssm-muted">{p.pid}</div>
        <div className="ssm-td ssm-num">
          <span className="ssm-cpu-bar" style={{ width: `${Math.min(p.cpu, 100)}%`, background: loadColor(p.cpu) }} />
          <span style={{ color: p.cpu >= 1 ? loadColor(p.cpu) : undefined }}>{fmtPct(p.cpu, 1)}</span>
        </div>
        <div className="ssm-td ssm-num">{fmtMb(p.mem_mb)}</div>
      </div>
      {expanded && (
        <div className="ssm-row-details">
          {p.cmd && <div className="ssm-cmd">{p.cmd}</div>}
          <div className="ssm-stats">
            <span className="ssm-stat"><span>Estado</span><b>{STATE_LABELS[p.state] ?? p.state}</b></span>
            <span className="ssm-stat"><span>PPID</span><b>{p.ppid}</b></span>
            <span className="ssm-stat"><span>Threads</span><b>{p.threads}</b></span>
            <span className="ssm-stat"><span>RAM</span><b>{fmtPct(p.mem_percent, 1)}</b></span>
          </div>
        </div>
      )}
    </Focusable>
  );
}
