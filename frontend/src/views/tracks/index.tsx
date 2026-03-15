import { useParams } from "react-router-dom";
import { EmptyState } from "../../components/ui";
import { formatCarTrack } from "../sessions/utils";
import "./CarTracksView.css";

export function CarTracksView() {
  const { carId } = useParams<{ carId: string }>();

  return (
    <div className="ace-tracks" data-testid="tracks-view">
      <EmptyState
        icon={<i className="fa-solid fa-road" />}
        title={`Tracks for ${formatCarTrack(carId ?? "")}`}
        description="Tracks driven with this car will appear here."
      />
    </div>
  );
}
