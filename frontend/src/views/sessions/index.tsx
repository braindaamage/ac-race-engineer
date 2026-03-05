import { EmptyState } from "../../components/ui";

export function SessionsView() {
  return (
    <EmptyState
      icon={<span>&#128203;</span>}
      title="No sessions recorded yet"
      description="Record a session in Assetto Corsa and it will appear here automatically."
    />
  );
}
