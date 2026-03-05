import { EmptyState } from "../../components/ui";
import { useUIStore } from "../../store/uiStore";

export function CompareView() {
  return (
    <EmptyState
      icon={<span>&#128260;</span>}
      title="Select a session to compare setups"
      description="Go to Sessions and select a session to compare setup configurations."
      action={{
        label: "Go to Sessions",
        onClick: () => useUIStore.getState().setActiveSection("sessions"),
      }}
    />
  );
}
