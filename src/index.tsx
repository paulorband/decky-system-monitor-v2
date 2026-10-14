import { PanelSection, PanelSectionRow, staticClasses } from "@decky/ui";
import { definePlugin } from "@decky/api";
import { FaChartLine } from "react-icons/fa";

function Content() {
  return (
    <PanelSection title="System Monitor">
      <PanelSectionRow>Em construção</PanelSectionRow>
    </PanelSection>
  );
}

export default definePlugin(() => ({
  name: "System Monitor",
  titleView: <div className={staticClasses.Title}>System Monitor</div>,
  content: <Content />,
  icon: <FaChartLine />,
}));
