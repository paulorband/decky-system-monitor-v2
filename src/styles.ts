// Scoped with the "ssm-" prefix so nothing leaks into the Steam UI.
export const CSS = `
.ssm-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px; margin: 4px 0 8px; }
.ssm-tile { background: rgba(255,255,255,0.05); border-radius: 6px; padding: 6px 2px; text-align: center; }
.ssm-tile-label { font-size: 10px; letter-spacing: 0.08em; color: #8b929a; text-transform: uppercase; }
.ssm-tile-value { font-size: 17px; font-weight: 700; line-height: 1.2; font-variant-numeric: tabular-nums; }

.ssm-card { background: rgba(255,255,255,0.04); border: 2px solid transparent; border-radius: 8px;
  padding: 8px 10px; margin-bottom: 8px; transition: border-color 120ms, background 120ms; }
.ssm-card.ssm-focus { border-color: rgba(255,255,255,0.75); background: rgba(255,255,255,0.09); }
.ssm-card-head { display: flex; align-items: baseline; justify-content: space-between; gap: 6px; }
.ssm-card-title { font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; }
.ssm-card-chevron { font-size: 10px; color: #8b929a; margin-left: 4px; }
.ssm-big { font-size: 24px; font-weight: 700; line-height: 1.1; font-variant-numeric: tabular-nums; }
.ssm-big small { font-size: 12px; font-weight: 400; color: #b8bcbf; margin-left: 4px; }
.ssm-stats { display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: 4px; font-size: 12px; color: #dcdedf; }
.ssm-stat b { font-weight: 600; font-variant-numeric: tabular-nums; }
.ssm-stat span { color: #8b929a; margin-right: 3px; }
.ssm-details { margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.08); font-size: 12px; }
.ssm-sub { display: flex; justify-content: space-between; font-size: 11px; color: #b8bcbf; margin: 6px 0 2px; }

.ssm-bar { height: 6px; border-radius: 3px; background: rgba(255,255,255,0.1); overflow: hidden; margin-top: 6px; }
.ssm-bar-fill { height: 100%; border-radius: 3px; transition: width 300ms ease-out; }

.ssm-spark { display: block; width: 100%; height: 28px; margin-top: 6px; }

.ssm-cores { display: grid; grid-template-columns: repeat(8, 1fr); gap: 3px; align-items: end; }
.ssm-core { background: rgba(255,255,255,0.1); border-radius: 2px; height: 24px; display: flex; align-items: flex-end; overflow: hidden; }
.ssm-core-fill { width: 100%; }
.ssm-muted { color: #8b929a; }
.ssm-error { color: #ff5c5c; font-size: 12px; padding: 4px 0; }
`;

// Full-screen process manager. The table body is its own scroll container so the
// column header stays visible while the D-pad moves focus through the rows.
export const PROCESS_CSS = `
.ssm-page { margin-top: 40px; height: calc(100vh - 40px - 48px); box-sizing: border-box; padding: 12px 28px 0; color: #dcdedf; }
.ssm-page-inner { display: flex; flex-direction: column; height: 100%; }
.ssm-proc-top { display: flex; align-items: baseline; justify-content: space-between; gap: 16px; flex-wrap: wrap; }
.ssm-proc-title { font-size: 26px; font-weight: 700; }
.ssm-proc-summary { display: flex; gap: 20px; align-items: center; font-size: 15px; font-variant-numeric: tabular-nums; }
.ssm-chip { color: #111; font-size: 11px; font-weight: 800; padding: 2px 8px; border-radius: 10px; letter-spacing: 0.06em; }
.ssm-proc-toolbar { display: flex; align-items: center; gap: 8px; margin: 10px 0; }
.ssm-proc-toolbar .ssm-tool-btn { width: auto; min-width: 0; padding: 6px 16px; font-size: 14px; }
.ssm-hint { margin-left: auto; font-size: 12px; color: #8b929a; }
.ssm-hint b { color: #dcdedf; }

.ssm-tr { display: grid; grid-template-columns: minmax(0, 1fr) 90px 130px 120px; align-items: center; column-gap: 8px; }
.ssm-thead { border-bottom: 1px solid rgba(255,255,255,0.15); padding: 0 10px 4px; font-size: 13px; }
.ssm-th { display: flex; align-items: center; gap: 4px; padding: 6px 8px; color: #8b929a; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.05em; border-radius: 4px; border: 2px solid transparent; }
.ssm-th-active { color: #fff; }
.ssm-th-focus { border-color: rgba(255,255,255,0.75); background: rgba(255,255,255,0.1); }
.ssm-th-arrow { font-size: 10px; min-width: 10px; }
.ssm-num { justify-content: flex-end; text-align: right; font-variant-numeric: tabular-nums; }

.ssm-tbody { flex: 1; overflow-y: auto; padding-bottom: 12px; }
.ssm-row { padding: 0 10px; border-radius: 4px; border: 2px solid transparent; }
.ssm-row-odd { background: rgba(255,255,255,0.035); }
.ssm-row-focus { border-color: rgba(255,255,255,0.75); background: rgba(255,255,255,0.1); }
.ssm-td { padding: 7px 8px; font-size: 15px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; position: relative; }
.ssm-name { font-weight: 600; }
.ssm-cpu-bar { position: absolute; right: 0; top: 4px; bottom: 4px; opacity: 0.18; border-radius: 3px; max-width: 100%; }
.ssm-row-details { padding: 2px 8px 8px; font-size: 12px; }
.ssm-cmd { font-family: monospace; color: #b8bcbf; word-break: break-all; margin-bottom: 4px; }
.ssm-more-btn { margin-top: 8px; }
`;

// Process grouping (spec 005)
export const GROUP_CSS = `
.ssm-badge { display: inline-block; margin-left: 8px; padding: 0 7px; border-radius: 9px; font-size: 12px;
  font-weight: 700; background: rgba(79,176,255,0.22); color: #9fd3ff; vertical-align: 1px; }
.ssm-caret { display: inline-block; width: 16px; color: #8b929a; }
.ssm-row-open { background: rgba(79,176,255,0.10); }
.ssm-member { margin-left: 24px; border-left: 2px solid rgba(79,176,255,0.35); border-radius: 0 4px 4px 0; }
.ssm-member .ssm-td { font-size: 13px; padding-top: 5px; padding-bottom: 5px; }
.ssm-member .ssm-name { font-weight: 400; color: #b8bcbf; }
.ssm-member-last { margin-bottom: 6px; }

/* Game grouping (spec 006) */
.ssm-game-badge { display: inline-block; margin-right: 8px; padding: 0 6px; border-radius: 4px; font-size: 11px;
  font-weight: 800; letter-spacing: 0.06em; background: #5ed47a; color: #10161c; vertical-align: 2px; }
.ssm-row-game:not(.ssm-row-focus) { background: rgba(94,212,122,0.10); }
`;
