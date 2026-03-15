import { EmptyState } from "../../components/ui";
import "./GarageView.css";

export function GarageView() {
  return (
    <div className="ace-garage" data-testid="garage-view">
      <EmptyState
        icon={<i className="fa-solid fa-car" />}
        title="My Garage"
        description="Your cars with session data will appear here."
      />
    </div>
  );
}
