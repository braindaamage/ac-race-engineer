import type { MetricDeltas } from "../../lib/types";
import { formatDelta, isImprovement, isNearZero } from "./utils";

interface MetricsPanelProps {
  deltas: MetricDeltas;
  stintAIndex: number;
  stintBIndex: number;
}

function deltaClass(metricKey: string, value: number | null, precision: number = 2): string {
  if (value == null || value === 0 || isNearZero(value, precision)) return "";
  return isImprovement(metricKey, value)
    ? "ace-metrics-delta--positive"
    : "ace-metrics-delta--negative";
}

const WHEEL_ORDER = ["fl", "fr", "rl", "rr"] as const;

function WheelGrid({
  label,
  metricKey,
  data,
  precision = 2,
}: {
  label: string;
  metricKey: string;
  data: Record<string, number>;
  precision?: number;
}) {
  return (
    <div className="ace-metrics-item">
      <span className="ace-metrics-item__label">{label}</span>
      <div className="ace-metrics-wheels">
        {WHEEL_ORDER.map((pos) => {
          const val = data[pos] ?? null;
          return (
            <div key={pos} className="ace-metrics-wheel">
              <span className="ace-metrics-wheel__label">{pos.toUpperCase()}</span>
              <span
                className={`ace-metrics-wheel__value ${deltaClass(metricKey, val, precision)}`}
              >
                {formatDelta(val, precision)}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function MetricsPanel({ deltas, stintAIndex, stintBIndex }: MetricsPanelProps) {
  return (
    <div className="ace-metrics-panel">
      <h3>
        Performance: Stint {stintAIndex + 1} vs Stint {stintBIndex + 1}
      </h3>

      <div className="ace-metrics-primary">
        <div className="ace-metrics-item">
          <span className="ace-metrics-item__label">Lap Time Delta</span>
          <span
            className={`ace-metrics-item__value ${deltaClass("lap_time_delta_s", deltas.lap_time_delta_s, 3)}`}
          >
            {deltas.lap_time_delta_s != null
              ? `${formatDelta(deltas.lap_time_delta_s, 3)}s`
              : "N/A"}
          </span>
        </div>

        <div className="ace-metrics-item">
          <span className="ace-metrics-item__label">Peak Lateral G Delta</span>
          <span
            className={`ace-metrics-item__value ${deltaClass("peak_lat_g_delta", deltas.peak_lat_g_delta, 4)}`}
          >
            {deltas.peak_lat_g_delta != null
              ? formatDelta(deltas.peak_lat_g_delta, 4)
              : "N/A"}
          </span>
        </div>
      </div>

      <WheelGrid
        label="Tyre Temp Delta"
        metricKey="tyre_temp_delta"
        data={deltas.tyre_temp_delta}
      />
      <WheelGrid
        label="Slip Angle Delta"
        metricKey="slip_angle_delta"
        data={deltas.slip_angle_delta}
        precision={3}
      />
      <WheelGrid
        label="Slip Ratio Delta"
        metricKey="slip_ratio_delta"
        data={deltas.slip_ratio_delta}
        precision={4}
      />
    </div>
  );
}
