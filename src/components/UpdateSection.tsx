import { ButtonItem, ConfirmModal, Field, Focusable, PanelSection, PanelSectionRow, ToggleField, showModal } from "@decky/ui";
import { ReactNode } from "react";
import { COLORS } from "../format";
import { t } from "../i18n";
import { useBackendSettings, useUpdates } from "../updates";

const AMBER = "#ffb300";

// Every line is focusable so the D-pad can reach it (REQ-622).
function Row({ label, color, children }: { label: string; color?: string; children: ReactNode }) {
  return (
    <PanelSectionRow>
      <Field label={label} focusable>
        <span style={{ color, fontVariantNumeric: "tabular-nums" }}>{children}</span>
      </Field>
    </PanelSectionRow>
  );
}

/** Full-width focusable sentence (a label/value Field would squeeze it into half the width). */
function Note({ color, children }: { color?: string; children: ReactNode }) {
  return (
    <PanelSectionRow>
      <Focusable style={{ color, fontSize: 13, lineHeight: 1.35, padding: "6px 0", width: "100%" }}>{children}</Focusable>
    </PanelSectionRow>
  );
}

/** Settings toggles that the backend owns (REQ-604, REQ-650/651). */
export function UpdateSettings({ onChannelChange }: { onChannelChange: () => void }) {
  const { cfg, update } = useBackendSettings();
  if (!cfg) return null;
  return (
    <>
      <PanelSectionRow>
        <ToggleField
          label={t("update.autoCheck")}
          checked={cfg.auto_check}
          onChange={(v) => update({ auto_check: v })}
        />
      </PanelSectionRow>
      <PanelSectionRow>
        <ToggleField
          label={t("update.testChannel")}
          checked={cfg.test_channel}
          onChange={(v) => {
            if (!v) {
              update({ test_channel: false }).then(onChannelChange);
              return;
            }
            // REQ-651: turning it ON needs an explicit, controller-friendly confirmation.
            showModal(
              <ConfirmModal
                strTitle={t("update.testEnableTitle")}
                strDescription={t("update.testWarning")}
                strOKButtonText={t("update.testEnableOk")}
                strCancelButtonText={t("update.testEnableCancel")}
                onOK={() => {
                  update({ test_channel: true }).then(onChannelChange);
                }}
              />,
            );
          }}
        />
      </PanelSectionRow>
      {cfg.test_channel && <Note color={AMBER}>{t("update.testHint")}</Note>}
    </>
  );
}

/** "Updates" section, always at the end of the panel (REQ-620). */
export function UpdateSection({ u }: { u: ReturnType<typeof useUpdates> }) {
  const { state, busy, message, check, install } = u;
  const isTest = state?.latest_kind === "test";
  const current = state
    ? `v${state.current}` +
      (state.current_kind === "test" && state.current_commit
        ? ` · ${t("update.testLabel", { c: state.current_commit })}` // REQ-664
        : !state.current_kind && state.current_commit
          ? ` · ${state.current_commit}`
          : "")
    : "—";
  return (
    <PanelSection title={t("update.title")}>
      <Row label={t("update.current")} color={state?.current_kind === "test" ? AMBER : undefined}>
        {current}
      </Row>
      {state?.available && (
        <Row label={t("update.latest")} color={isTest ? AMBER : COLORS.ok}>
          v{state.latest}
          {isTest && state.commit ? ` · ${t("update.testLabel", { c: state.commit })}` : ""}
        </Row>
      )}
      {state?.checked && !state.available && !state.error && <Row label={t("update.status")}>{t("update.upToDate")}</Row>}
      {state && !state.checked && <Row label={t("update.status")}>{t("update.notChecked")}</Row>}
      {message && <Note>{message}</Note>}
      <PanelSectionRow>
        {state?.available ? (
          <ButtonItem layout="below" disabled={busy !== null} onClick={install}>
            {busy === "install"
              ? t("update.installing")
              : t(isTest ? "update.installTest" : "update.install", { v: `v${state.latest}` })}
          </ButtonItem>
        ) : (
          <ButtonItem layout="below" disabled={busy !== null} onClick={check}>
            {busy === "check" ? t("update.checking") : t("update.checkNow")}
          </ButtonItem>
        )}
      </PanelSectionRow>
    </PanelSection>
  );
}
