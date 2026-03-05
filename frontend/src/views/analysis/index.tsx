import { EmptyState } from "../../components/ui";
import { useUIStore } from "../../store/uiStore";

export function AnalysisView() {
  return (
    <EmptyState
      icon={<span>&#128202;</span>}
      title="Select a session to analyze laps"
      description="Go to Sessions and select a session to view detailed lap analysis."
      action={{
        label: "Go to Sessions",
        onClick: () => useUIStore.getState().setActiveSection("sessions"),
      }}
    />
  );
}
