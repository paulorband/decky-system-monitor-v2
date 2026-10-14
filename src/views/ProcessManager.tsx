import { DialogButton, Focusable } from "@decky/ui";
import { Fragment, useState } from "react";
import { GroupMode, SortKey, getMetrics, getProcesses } from "../api";
import { MemberRow, ProcessRow, ProcessTableHeader } from "../components/ProcessTable";
import { COLORS, fmtMb, fmtPct, loadColor } from "../format";
import { usePolling } from "../hooks/usePolling";
import { usePersistentState } from "../settings";
import { recordMetrics } from "../store";
import { CSS, GROUP_CSS, PROCESS_CSS } from "../styles";

const PAGE_SIZE = 40;
const REFRESH_MS = 2000;
const SORT_CYCLE: SortKey[] = ["cpu", "mem", "name"];
const SORT_LABELS: Record<SortKey, string> = { cpu: "CPU", mem: "RAM", name: "Nome" };
const GROUP_CYCLE: GroupMode[] = ["app", "name", "none"];
const GROUP_LABELS: Record<GroupMode, string> = { app: "Agrupar: jogos", name: "Agrupar: nome", none: "Sem grupos" };

export function ProcessManager() {
  const [sortKey, setSortKey] = usePersistentState<SortKey>("procSort", "cpu");
  const [descending, setDescending] = usePersistentState<boolean>("procDesc", true);
  const [includeKernel, setIncludeKernel] = usePersistentState<boolean>("procKernel", false);
  const [groupMode, setGroupMode] = usePersistentState<GroupMode>("procGroupMode", "app");
  const [limit, setLimit] = useState(PAGE_SIZE);
  const [paused, setPaused] = useState(false);
  // Keyed by item key ("name:x" / "pid:n") so open rows survive reordering.
  const [openGroup, setOpenGroup] = useState<string | null>(null);
  const [openDetail, setOpenDetail] = useState<string | null>(null);

  const { data, error } = usePolling(
    async () => {
      const [procs, metrics] = await Promise.all([
        getProcesses(sortKey, descending, limit, includeKernel, groupMode),
        getMetrics(),
      ]);
      recordMetrics(metrics);
      return { procs, metrics };
    },
    REFRESH_MS,
    !paused,
    [sortKey, descending, limit, includeKernel, groupMode],
  );

  // Any change to what is listed resumes updates, so the user sees the new order.
  const applySort = (key: SortKey, desc: boolean) => {
    setSortKey(key);
    setDescending(desc);
    setPaused(false);
  };
  const onSort = (key: SortKey) => {
    if (key === sortKey) applySort(key, !descending);
    else applySort(key, key !== "name");
  };
  const nextSort = SORT_CYCLE[(SORT_CYCLE.indexOf(sortKey) + 1) % SORT_CYCLE.length];
  const cycleSort = () => applySort(nextSort, nextSort !== "name");
  const togglePause = () => setPaused(!paused);
  const toggleKernel = () => {
    setIncludeKernel(!includeKernel);
    setPaused(false);
  };
  const toggleGrouped = () => {
    setGroupMode(GROUP_CYCLE[(GROUP_CYCLE.indexOf(groupMode) + 1) % GROUP_CYCLE.length]);
    setOpenGroup(null);
    setPaused(false);
  };
  const toggleGroup = (key: string) => setOpenGroup(openGroup === key ? null : key);
  const toggleDetail = (key: string) => setOpenDetail(openDetail === key ? null : key);

  const procs = data?.procs;
  const metrics = data?.metrics;
  const remaining = procs ? procs.total - procs.shown : 0;

  return (
    <div className="ssm-page">
      <style>{CSS + PROCESS_CSS + GROUP_CSS}</style>
      <Focusable
        className="ssm-page-inner"
        flow-children="column"
        onSecondaryButton={cycleSort}
        onSecondaryActionDescription={`Ordenar: ${SORT_LABELS[nextSort]}`}
        onOptionsButton={togglePause}
        onOptionsActionDescription={paused ? "Retomar" : "Pausar"}
      >
        <div className="ssm-proc-top">
          <div className="ssm-proc-title">Processos</div>
          <div className="ssm-proc-summary">
            <span>
              <span className="ssm-muted">Processos </span>
              <b>{procs?.process_count ?? "—"}</b>
            </span>
            {groupMode !== "none" && procs && (
              <span>
                <span className="ssm-muted">Grupos </span>
                <b>{procs.total}</b>
              </span>
            )}
            <span>
              <span className="ssm-muted">CPU </span>
              <b style={{ color: loadColor(metrics?.cpu.usage) }}>{fmtPct(metrics?.cpu.usage)}</b>
            </span>
            <span>
              <span className="ssm-muted">RAM </span>
              <b style={{ color: loadColor(metrics?.memory.percent) }}>
                {metrics ? `${fmtMb(metrics.memory.used_mb)} / ${fmtMb(metrics.memory.total_mb)}` : "—"}
              </b>
            </span>
            {paused && <span className="ssm-chip" style={{ background: COLORS.warn }}>PAUSADO</span>}
          </div>
        </div>

        <Focusable flow-children="row" className="ssm-proc-toolbar">
          <DialogButton className="ssm-tool-btn" onClick={togglePause}>
            {paused ? "▶ Retomar" : "❚❚ Pausar"}
          </DialogButton>
          <DialogButton className="ssm-tool-btn" onClick={toggleGrouped}>
            {GROUP_LABELS[groupMode]}
          </DialogButton>
          <DialogButton className="ssm-tool-btn" onClick={toggleKernel}>
            {includeKernel ? "Ocultar kernel" : "Mostrar kernel"}
          </DialogButton>
          <div className="ssm-hint">
            <b>X</b> ordenar · <b>Y</b> pausar · <b>A</b> detalhes · <b>B</b> voltar
          </div>
        </Focusable>

        <ProcessTableHeader sortKey={sortKey} descending={descending} onSort={onSort} />

        <Focusable flow-children="column" className="ssm-tbody">
          {error && <div className="ssm-error">Erro ao ler processos: {error}</div>}
          {!procs && !error && <div className="ssm-muted" style={{ padding: 12 }}>Carregando…</div>}
          {procs?.processes.map((item, i) => {
            const isGroup = item.count > 1;
            const open = isGroup ? openGroup === item.key : openDetail === item.key;
            return (
              <Fragment key={item.key}>
                <ProcessRow item={item} index={i} expanded={open} onToggle={isGroup ? toggleGroup : toggleDetail} />
                {isGroup &&
                  open &&
                  item.members.map((m, j) => (
                    <MemberRow
                      key={m.pid}
                      p={m}
                      last={j === item.members.length - 1}
                      expanded={openDetail === `pid:${m.pid}`}
                      onToggle={toggleDetail}
                    />
                  ))}
              </Fragment>
            );
          })}
          {remaining > 0 && (
            <DialogButton className="ssm-more-btn" onClick={() => setLimit(limit + PAGE_SIZE)}>
              Mostrar mais ({remaining} restantes)
            </DialogButton>
          )}
        </Focusable>
      </Focusable>
    </div>
  );
}
