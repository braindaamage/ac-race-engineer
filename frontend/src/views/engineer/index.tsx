import { EmptyState } from "../../components/ui";
import { useUIStore } from "../../store/uiStore";

export function EngineerView() {
  return (
    <EmptyState
      icon={<span>&#129302;</span>}
      title="Select a session to talk with your engineer"
      description="Go to Sessions and select a session to get AI-powered setup recommendations."
      action={{
        label: "Go to Sessions",
        onClick: () => useUIStore.getState().setActiveSection("sessions"),
      }}
    />
  );
}
