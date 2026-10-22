import { callable, toaster } from "@decky/api";
import { useCallback, useEffect, useState } from "react";
import { t } from "./i18n";

// Auto-update (specs/008-auto-atualizacao), ported from the previous plugin.
export interface UpdateState {
  current: string;
  latest?: string;
  latest_kind?: "stable" | "test";
  commit?: string;
  current_commit?: string | null;
  current_kind?: "stable" | "test" | null;
  retry_minutes?: number;
  channel?: "stable" | "test";
  available: boolean;
  checked: boolean;
  error?: string;
  /** Release notes of the version on offer (spec 009 REQ-722). */
  notes?: string;
}

/** The saved previous version (spec 009 REQ-703). */
export interface RollbackInfo {
  version: string;
  commit: string | null;
  kind: "stable" | "test" | null;
}

/** Backend-owned settings (REQ-670). */
export interface BackendSettings {
  auto_check: boolean;
  test_channel: boolean;
}

const getUpdateState = callable<[], UpdateState>("get_update_state");
const checkUpdate = callable<[boolean], UpdateState>("check_update");
const installUpdate = callable<[], { ok: boolean; version?: string; error?: string }>("install_update");
const getSettings = callable<[], BackendSettings>("get_settings");
const setSettings = callable<[BackendSettings], BackendSettings>("set_settings");
const getRollbackInfo = callable<[], RollbackInfo | null>("get_rollback_info");
const rollbackUpdate = callable<[], { ok: boolean; version?: string; error?: string }>("rollback");
export const getChangelog = callable<[], string>("get_changelog");

/** REQ-600/610: once per plugin start, after the language is known; silent on any failure (REQ-602). */
export async function startupUpdateCheck(): Promise<void> {
  try {
    const cfg = await getSettings();
    if (!cfg.auto_check) return; // REQ-604
    const st = await checkUpdate(false);
    if (st.available && st.latest) {
      const test = st.latest_kind === "test";
      toaster.toast({
        title: t("update.toastTitle"),
        body: t(test ? "update.toastBodyTest" : "update.toastBody", { v: `v${st.latest}` }),
        duration: 10000,
      });
    }
  } catch {
    // offline / backend not ready
  }
}

export function useBackendSettings() {
  const [cfg, setCfg] = useState<BackendSettings | null>(null);
  useEffect(() => {
    let alive = true;
    getSettings().then((s) => alive && setCfg(s)).catch(() => {});
    return () => {
      alive = false;
    };
  }, []);
  const update = useCallback(async (patch: Partial<BackendSettings>) => {
    if (!cfg) return;
    setCfg(await setSettings({ ...cfg, ...patch }));
  }, [cfg]);
  return { cfg, update };
}

export type Busy = "check" | "install" | "rollback" | null;

export function useUpdates() {
  const [state, setState] = useState<UpdateState | null>(null);
  const [busy, setBusy] = useState<Busy>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [previous, setPrevious] = useState<RollbackInfo | null>(null);

  useEffect(() => {
    let alive = true;
    getUpdateState()
      .then((s) => alive && setState(s))
      .catch((e) => alive && setMessage(t("update.checkFailed", { e: String(e) })));
    getRollbackInfo()
      .then((r) => alive && setPrevious(r))
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);

  /** After install/rollback succeeds Decky restarts; if it does not within ~20 s, say what to do (REQ-636). */
  const waitForRestart = (okKey: string, version?: string) => {
    setMessage(t(okKey, { v: `v${version}` }));
    setTimeout(() => {
      setMessage(t("update.restartHint"));
      setBusy(null);
      setState((p) => (p ? { ...p, available: false } : p));
      setPrevious(null);
    }, 20000);
  };

  const check = useCallback(async () => {
    setBusy("check");
    setMessage(null);
    try {
      const s = await checkUpdate(true);
      setState(s);
      if (s.retry_minutes) setMessage(t("update.rateLimited", { m: s.retry_minutes })); // REQ-662
      else if (s.error) setMessage(t("update.checkFailed", { e: s.error }));
    } catch (e) {
      setMessage(t("update.checkFailed", { e: String(e) }));
    } finally {
      setBusy(null);
    }
  }, []);

  const install = useCallback(async () => {
    setBusy("install");
    setMessage(null);
    try {
      const r = await installUpdate();
      if (r.ok) {
        waitForRestart("update.installOk", r.version);
      } else {
        setMessage(t("update.installFailed", { e: r.error ?? "?" }));
        setBusy(null);
      }
    } catch (e) {
      setMessage(t("update.installFailed", { e: String(e) }));
      setBusy(null);
    }
  }, []);

  const rollback = useCallback(async () => {
    setBusy("rollback");
    setMessage(null);
    try {
      const r = await rollbackUpdate();
      if (r.ok) waitForRestart("update.rollbackOk", r.version);
      else {
        setMessage(t("update.rollbackFailed", { e: r.error ?? "?" }));
        setBusy(null);
      }
    } catch (e) {
      setMessage(t("update.rollbackFailed", { e: String(e) }));
      setBusy(null);
    }
  }, []);

  return { state, busy, message, previous, check, install, rollback };
}
