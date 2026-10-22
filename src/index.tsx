import { staticClasses } from "@decky/ui";
import { definePlugin, routerHook } from "@decky/api";
import { FaChartLine } from "react-icons/fa";
import { initI18n } from "./i18n";
import { PROCESSES_ROUTE } from "./routes";
import { startupUpdateCheck } from "./updates";
import { Dashboard } from "./views/Dashboard";
import { ProcessManager } from "./views/ProcessManager";

export default definePlugin(() => {
  // The update toast must follow the plugin language, so check only once it is resolved (spec 008 REQ-610).
  initI18n().then(startupUpdateCheck);
  routerHook.addRoute(PROCESSES_ROUTE, ProcessManager, { exact: true });

  return {
    name: "System Monitor",
    titleView: <div className={staticClasses.Title}>System Monitor</div>,
    content: <Dashboard />,
    icon: <FaChartLine />,
    onDismount() {
      routerHook.removeRoute(PROCESSES_ROUTE);
    },
  };
});
