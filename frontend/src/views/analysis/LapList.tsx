import { Badge } from "../../components/ui";
import type { LapSummary } from "../../lib/types";
import { formatLapTime, formatSpeed, formatPercentage, formatTemperature } from "./utils";

interface LapListProps {
  laps: LapSummary[];
  fastestLapNumber: number | null;
  selectedLaps: number[];
  onToggleLap: (lapNumber: number) => void;
}

export function LapList({ laps, fastestLapNumber, selectedLaps, onToggleLap }: LapListProps) {
  return (
    <div className="ace-analysis__sidebar">
      <h2>Laps</h2>
      {laps.map((lap) => {
        const isSelected = selectedLaps.includes(lap.lap_number);
        const isFastest = lap.lap_number === fastestLapNumber;
        const classNames = ["ace-lap-item"];
        if (isSelected) classNames.push("ace-lap-item--selected");
        if (lap.is_invalid) classNames.push("ace-lap-item--invalid");

        const avgTyreTemp =
          Object.values(lap.tyre_temps_avg).length > 0
            ? Object.values(lap.tyre_temps_avg).reduce((a, b) => a + b, 0) /
              Object.values(lap.tyre_temps_avg).length
            : 0;

        return (
          <div
            key={lap.lap_number}
            className={classNames.join(" ")}
            onClick={() => onToggleLap(lap.lap_number)}
            data-testid={`lap-item-${lap.lap_number}`}
          >
            <span className="ace-lap-item__number">{lap.lap_number}</span>
            <span className="ace-lap-item__time">
              {formatLapTime(lap.lap_time_s)}
            </span>
            <span className="ace-lap-item__meta">
              <span>{formatSpeed(lap.max_speed)}</span>
              <span>{formatPercentage(lap.full_throttle_pct)}</span>
              <span>{formatTemperature(avgTyreTemp)}</span>
            </span>
            {isFastest && <Badge variant="success">Fastest</Badge>}
            {lap.is_invalid && (
              <Badge variant="warning">{lap.classification}</Badge>
            )}
          </div>
        );
      })}
    </div>
  );
}
