import type { StintMetrics } from "../../lib/types";
import { formatLapTime } from "./utils";

interface StintSelectorProps {
  stints: StintMetrics[];
  selectedStints: [number, number | null];
  onSelect: (stintIndex: number) => void;
}

export function StintSelector({ stints, selectedStints, onSelect }: StintSelectorProps) {
  const isSelected = (index: number) =>
    selectedStints[0] === index || selectedStints[1] === index;

  return (
    <div className="ace-compare__sidebar">
      <h2>Stints</h2>
      {stints.map((stint) => (
        <div
          key={stint.stint_index}
          className={`ace-stint-item${isSelected(stint.stint_index) ? " ace-stint-item--selected" : ""}`}
          onClick={() => onSelect(stint.stint_index)}
          data-testid={`stint-item-${stint.stint_index}`}
        >
          <span className="ace-stint-item__number">
            Stint {stint.stint_index + 1}
          </span>
          <span className="ace-stint-item__setup">
            {stint.setup_filename ?? "No setup"}
          </span>
          <span className="ace-stint-item__meta">
            <span>{stint.flying_lap_count} laps</span>
            <span>{formatLapTime(stint.aggregated.lap_time_mean_s)}</span>
          </span>
        </div>
      ))}
    </div>
  );
}
