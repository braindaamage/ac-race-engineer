import { useUIStore } from "../../store/uiStore";
import { Sidebar } from "./Sidebar";
import { ToastContainer } from "./ToastContainer";
import { SessionsView } from "../../views/sessions";
import { AnalysisView } from "../../views/analysis";
import { CompareView } from "../../views/compare";
import { EngineerView } from "../../views/engineer";
import { SettingsView } from "../../views/settings";
import "./AppShell.css";

const VIEW_MAP: Record<string, React.ComponentType> = {
  sessions: SessionsView,
  analysis: AnalysisView,
  compare: CompareView,
  engineer: EngineerView,
  settings: SettingsView,
};

export function AppShell() {
  const activeSection = useUIStore((s) => s.activeSection);
  const ActiveView = VIEW_MAP[activeSection] ?? SessionsView;

  return (
    <div className="ace-app-shell">
      <Sidebar />
      <main className="ace-app-shell__content">
        <ActiveView />
      </main>
      <ToastContainer />
    </div>
  );
}
