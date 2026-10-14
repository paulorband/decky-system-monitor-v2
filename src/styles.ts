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
