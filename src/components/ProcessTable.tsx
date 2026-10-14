import { Focusable } from "@decky/ui";
import { ProcessInfo, ProcessItem, SortKey } from "../api";
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

function CpuCell({ cpu }: { cpu: number }) {
  return (
    <div className="ssm-td ssm-num">
      <span className="ssm-cpu-bar" style={{ width: `${Math.min(cpu, 100)}%`, background: loadColor(cpu) }} />
      <span style={{ color: cpu >= 1 ? loadColor(cpu) : undefined }}>{fmtPct(cpu, 1)}</span>
    </div>
  );
}

function Details({ p }: { p: ProcessInfo }) {
  return (
    <div className="ssm-row-details">
      {p.cmd && <div className="ssm-cmd">{p.cmd}</div>}
      <div className="ssm-stats">
        <span className="ssm-stat"><span>Estado</span><b>{STATE_LABELS[p.state] ?? p.state}</b></span>
        <span className="ssm-stat"><span>PPID</span><b>{p.ppid}</b></span>
        <span className="ssm-stat"><span>Threads</span><b>{p.threads}</b></span>
        <span className="ssm-stat"><span>RAM</span><b>{fmtPct(p.mem_percent, 1)}</b></span>
      </div>
    </div>
  );
}

interface RowProps {
  item: ProcessItem;
  index: number;
  expanded: boolean;
  onToggle: (key: string) => void;
}

/** A process or a group. Group members are rendered by the caller as sibling MemberRows,
 *  because nested Focusables would swallow the row's own focus. */
export function ProcessRow({ item, index, expanded, onToggle }: RowProps) {
  const isGroup = item.count > 1;
  return (
    <Focusable
      className={`ssm-row${index % 2 ? " ssm-row-odd" : ""}${isGroup && expanded ? " ssm-row-open" : ""}`}
      focusClassName="ssm-row-focus"
      noFocusRing
      onActivate={() => onToggle(item.key)}
      onOKActionDescription={expanded ? "Recolher" : isGroup ? "Ver instâncias" : "Detalhes"}
    >
      <div className="ssm-tr">
        <div className="ssm-td ssm-name">
          {isGroup && <span className="ssm-caret">{expanded ? "▾" : "▸"}</span>}
          {item.name}
          {isGroup && <span className="ssm-badge">×{item.count}</span>}
        </div>
        <div className="ssm-td ssm-num ssm-muted">{isGroup ? `${item.count} proc.` : item.pid}</div>
        <CpuCell cpu={item.cpu} />
        <div className="ssm-td ssm-num">{fmtMb(item.mem_mb)}</div>
      </div>
      {expanded && !isGroup && <Details p={item} />}
    </Focusable>
  );
}

interface MemberProps {
  p: ProcessInfo;
  last: boolean;
  expanded: boolean;
  onToggle: (key: string) => void;
}

export function MemberRow({ p, last, expanded, onToggle }: MemberProps) {
  return (
    <Focusable
      className={`ssm-row ssm-member${last ? " ssm-member-last" : ""}`}
      focusClassName="ssm-row-focus"
      noFocusRing
      onActivate={() => onToggle(`pid:${p.pid}`)}
      onOKActionDescription={expanded ? "Recolher" : "Detalhes"}
    >
      <div className="ssm-tr">
        <div className="ssm-td ssm-name">{p.name}</div>
        <div className="ssm-td ssm-num ssm-muted">{p.pid}</div>
        <CpuCell cpu={p.cpu} />
        <div className="ssm-td ssm-num">{fmtMb(p.mem_mb)}</div>
      </div>
      {expanded && <Details p={p} />}
    </Focusable>
  );
}
