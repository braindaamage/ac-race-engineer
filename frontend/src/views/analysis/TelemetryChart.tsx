import { useMemo } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Skeleton } from "../../components/ui";
import type { LapTelemetryResponse } from "../../lib/types";

interface TelemetryChartProps {
  primaryTelemetry: LapTelemetryResponse | undefined;
  primaryLapNumber: number;
  secondaryTelemetry?: LapTelemetryResponse | undefined;
  secondaryLapNumber?: number;
  isLoading: boolean;
}

interface ChannelConfig {
  key: string;
  label: string;
  color: string;
  domain?: [number, number];
}

const CHANNELS: ChannelConfig[] = [
  { key: "throttle", label: "Throttle", color: "var(--green-500)", domain: [0, 1] },
  { key: "brake", label: "Brake", color: "var(--red-500)", domain: [0, 1] },
  { key: "steering", label: "Steering", color: "var(--blue-500)", domain: [-1, 1] },
  { key: "speed_kmh", label: "Speed", color: "var(--amber-500)" },
  { key: "gear", label: "Gear", color: "var(--gray-400)" },
];

function buildRows(
  primary: LapTelemetryResponse | undefined,
  secondary: LapTelemetryResponse | undefined,
): Record<string, number>[] {
  if (!primary) return [];

  const ch = primary.channels;
  const rows: Record<string, number>[] = ch.normalized_position.map((pos, i) => ({
    position: Math.round(pos * 1000) / 10, // 0-100 with 1 decimal
    throttle: ch.throttle[i] ?? 0,
    brake: ch.brake[i] ?? 0,
    steering: ch.steering[i] ?? 0,
    speed_kmh: ch.speed_kmh[i] ?? 0,
    gear: ch.gear[i] ?? 0,
  }));

  if (secondary) {
    const sCh = secondary.channels;
    // Merge secondary data by nearest position
    let si = 0;
    for (const row of rows) {
      const pos = row["position"] ?? 0;
      // Advance secondary index to nearest position
      while (
        si < sCh.normalized_position.length - 1 &&
        Math.abs((sCh.normalized_position[si + 1] ?? 0) * 100 - pos) <
          Math.abs((sCh.normalized_position[si] ?? 0) * 100 - pos)
      ) {
        si++;
      }
      if (si < sCh.normalized_position.length) {
        row["throttle_2"] = sCh.throttle[si] ?? 0;
        row["brake_2"] = sCh.brake[si] ?? 0;
        row["steering_2"] = sCh.steering[si] ?? 0;
        row["speed_kmh_2"] = sCh.speed_kmh[si] ?? 0;
        row["gear_2"] = sCh.gear[si] ?? 0;
      }
    }
  }

  return rows;
}

function CustomTooltip({
  active,
  payload,
  primaryLapNumber,
  secondaryLapNumber,
  channelKey,
}: {
  active?: boolean;
  payload?: Array<{ value: number; dataKey: string }>;
  primaryLapNumber: number;
  secondaryLapNumber?: number;
  channelKey: string;
}) {
  if (!active || !payload || payload.length === 0) return null;

  const primaryVal = payload.find((p) => p.dataKey === channelKey);
  const secondaryVal = payload.find((p) => p.dataKey === `${channelKey}_2`);

  return (
    <div
      style={{
        background: "var(--bg-surface)",
        border: "1px solid var(--border-primary)",
        padding: "4px 8px",
        borderRadius: "4px",
        fontSize: "var(--font-size-xs)",
        fontFamily: "var(--font-mono)",
      }}
    >
      {primaryVal != null && (
        <div>
          Lap {primaryLapNumber}: {typeof primaryVal.value === "number" ? primaryVal.value.toFixed(2) : primaryVal.value}
        </div>
      )}
      {secondaryVal != null && secondaryLapNumber != null && (
        <div style={{ opacity: 0.7 }}>
          Lap {secondaryLapNumber}: {typeof secondaryVal.value === "number" ? secondaryVal.value.toFixed(2) : secondaryVal.value}
        </div>
      )}
    </div>
  );
}

export function TelemetryChart({
  primaryTelemetry,
  primaryLapNumber,
  secondaryTelemetry,
  secondaryLapNumber,
  isLoading,
}: TelemetryChartProps) {
  const rows = useMemo(
    () => buildRows(primaryTelemetry, secondaryTelemetry),
    [primaryTelemetry, secondaryTelemetry],
  );

  const hasSecondary = !!secondaryTelemetry;

  if (isLoading) {
    return (
      <div className="ace-telemetry" data-testid="telemetry-loading">
        {CHANNELS.map((ch) => (
          <Skeleton key={ch.key} height="100px" />
        ))}
      </div>
    );
  }

  if (rows.length === 0) return null;

  return (
    <div className="ace-telemetry" data-testid="telemetry-charts">
      {CHANNELS.map((ch) => (
        <div key={ch.key} className="ace-telemetry__chart" data-testid={`chart-${ch.key}`}>
          <div className="ace-telemetry__label">{ch.label}</div>
          <ResponsiveContainer width="100%" height={100}>
            <LineChart data={rows} syncId="telemetry" margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
              <XAxis
                dataKey="position"
                type="number"
                domain={[0, 100]}
                tick={false}
                axisLine={false}
              />
              <YAxis
                domain={ch.domain ?? ["auto", "auto"]}
                tick={false}
                axisLine={false}
                width={0}
              />
              <Tooltip
                content={
                  <CustomTooltip
                    primaryLapNumber={primaryLapNumber}
                    secondaryLapNumber={secondaryLapNumber}
                    channelKey={ch.key}
                  />
                }
              />
              <Line
                type="monotone"
                dataKey={ch.key}
                stroke={ch.color}
                dot={false}
                strokeWidth={1.5}
                isAnimationActive={false}
              />
              {hasSecondary && (
                <Line
                  type="monotone"
                  dataKey={`${ch.key}_2`}
                  stroke={ch.color}
                  dot={false}
                  strokeWidth={1.5}
                  strokeDasharray="5 5"
                  opacity={0.6}
                  isAnimationActive={false}
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      ))}
    </div>
  );
}
