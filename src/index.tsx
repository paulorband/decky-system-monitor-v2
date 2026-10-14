import { staticClasses } from "@decky/ui";
import { definePlugin, routerHook } from "@decky/api";
import { FaChartLine } from "react-icons/fa";
import { PROCESSES_ROUTE } from "./routes";
import { Dashboard } from "./views/Dashboard";
import { ProcessManager } from "./views/ProcessManager";

export default definePlugin(() => {
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
