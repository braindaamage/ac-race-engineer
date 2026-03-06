import { useQueryClient } from "@tanstack/react-query";
import { useUIStore } from "../../store/uiStore";
import { useSessionStore } from "../../store/sessionStore";
import type { SessionListResponse } from "../../lib/types";
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

function SelectedSessionStrip() {
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId);
  const clearSession = useSessionStore((s) => s.clearSession);
  const queryClient = useQueryClient();

  const sessions =
    queryClient.getQueryData<SessionListResponse>(["sessions"])?.sessions ?? [];
  const selectedSession = sessions.find((s) => s.session_id === selectedSessionId);

  if (!selectedSessionId || !selectedSession) return null;

  const formatName = (name: string) => {
    let formatted = name;
    if (formatted.startsWith("ks_")) formatted = formatted.slice(3);
    return formatted.replace(/_/g, " ");
  };

  return (
    <div className="ace-session-strip">
      <span className="ace-session-strip__label">{formatName(selectedSession.car)}</span>
      <span>{formatName(selectedSession.track)}</span>
      <button className="ace-session-strip__close" onClick={clearSession} aria-label="Clear selection">
        &times;
      </button>
    </div>
  );
}

export function AppShell() {
  const activeSection = useUIStore((s) => s.activeSection);
  const ActiveView = VIEW_MAP[activeSection] ?? SessionsView;

  return (
    <div className="ace-app-shell">
      <Sidebar />
      <div className="ace-app-shell__main">
        <SelectedSessionStrip />
        <main className="ace-app-shell__content">
          <ActiveView />
        </main>
      </div>
      <ToastContainer />
    </div>
  );
}
