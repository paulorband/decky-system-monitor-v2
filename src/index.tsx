import { staticClasses } from "@decky/ui";
import { definePlugin } from "@decky/api";
import { FaChartLine } from "react-icons/fa";
import { Dashboard } from "./views/Dashboard";

export default definePlugin(() => ({
  name: "System Monitor",
  titleView: <div className={staticClasses.Title}>System Monitor</div>,
  content: <Dashboard />,
  icon: <FaChartLine />,
}));
