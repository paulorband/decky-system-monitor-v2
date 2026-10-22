import { DialogButton, Focusable, ModalRoot, showModal } from "@decky/ui";
import { CSSProperties, Fragment, ReactNode } from "react";
import { t } from "../i18n";

// Spec 009 REQ-724: release notes / CHANGELOG.md in a controller-friendly modal.
// A tiny Markdown subset is enough for our own changelog: headings, bullets, **bold**, `code` and [links](url).

type Block = { kind: "h1" | "h2" | "h3" | "li" | "p"; text: string };

function parse(md: string): Block[] {
  const blocks: Block[] = [];
  for (const raw of md.replace(/\r/g, "").split("\n")) {
    const line = raw.trimEnd();
    if (!line.trim()) continue;
    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    const bullet = /^\s*[-*]\s+(.*)$/.exec(line);
    if (heading) blocks.push({ kind: heading[1].length === 1 ? "h1" : heading[1].length === 2 ? "h2" : "h3", text: heading[2] });
    else if (bullet) blocks.push({ kind: "li", text: bullet[1] });
    else if (/^\s+\S/.test(line) && blocks.length && blocks[blocks.length - 1].kind === "li") {
      blocks[blocks.length - 1].text += " " + line.trim(); // wrapped continuation of a bullet
    } else blocks.push({ kind: "p", text: line.trim() });
  }
  return blocks;
}

function inline(text: string): ReactNode[] {
  const out: ReactNode[] = [];
  const re = /\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\([^)]*\)|\*([^*]+)\*/g;
  let last = 0;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(text.slice(last, m.index));
    if (m[1]) out.push(<b key={out.length}>{m[1]}</b>);
    else if (m[2]) out.push(<code key={out.length} style={{ fontSize: "0.9em", opacity: 0.9 }}>{m[2]}</code>);
    else if (m[3]) out.push(m[3]); // links are shown as text: no browser in Game Mode
    else if (m[4]) out.push(<i key={out.length}>{m[4]}</i>);
    last = re.lastIndex;
  }
  if (last < text.length) out.push(text.slice(last));
  return out;
}

const STYLES: Record<Block["kind"], CSSProperties> = {
  h1: { fontSize: 20, fontWeight: 700, margin: "4px 0 6px" },
  h2: { fontSize: 17, fontWeight: 700, margin: "14px 0 4px", color: "#9fd3ff" },
  h3: { fontSize: 14, fontWeight: 700, margin: "8px 0 2px", textTransform: "uppercase", letterSpacing: "0.05em", color: "#b8bcbf" },
  li: { fontSize: 14, lineHeight: 1.4, margin: "2px 0", paddingLeft: 16, textIndent: -12 },
  p: { fontSize: 14, lineHeight: 1.4, margin: "4px 0", color: "#b8bcbf" },
};

function ChangelogModal({ title, markdown, closeModal }: { title: string; markdown: string; closeModal?: () => void }) {
  const blocks = parse(markdown);
  return (
    <ModalRoot closeModal={closeModal} onCancel={closeModal}>
      <div style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>{title}</div>
      {/* Each block is focusable so the D-pad scrolls through long notes; B closes the modal. */}
      <Focusable style={{ maxHeight: "55vh", overflowY: "auto", paddingRight: 8 }} flow-children="column">
        {blocks.length === 0 && <div style={STYLES.p}>{t("update.noNotes")}</div>}
        {blocks.map((b, i) => (
          <Fragment key={i}>
            <Focusable style={STYLES[b.kind]} focusClassName="ssm-note-focus" noFocusRing onActivate={() => {}}>
              {b.kind === "li" ? "• " : ""}
              {inline(b.text)}
            </Focusable>
          </Fragment>
        ))}
      </Focusable>
      <DialogButton style={{ marginTop: 12 }} onClick={closeModal}>
        {t("update.close")}
      </DialogButton>
      <style>{".ssm-note-focus { background: rgba(255,255,255,0.08); border-radius: 4px; }"}</style>
    </ModalRoot>
  );
}

export function showChangelog(title: string, markdown: string) {
  showModal(<ChangelogModal title={title} markdown={markdown} />);
}
