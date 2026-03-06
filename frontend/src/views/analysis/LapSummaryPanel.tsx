import { Badge, DataCell } from "../../components/ui";
import type { LapDetailResponse, LapSummary } from "../../lib/types";
import {
  formatLapTime,
  formatSpeed,
  formatPercentage,
  formatTemperature,
  formatDelta,
} from "./utils";

interface LapSummaryPanelProps {
  primaryDetail: LapDetailResponse | undefined;
  secondaryDetail?: LapDetailResponse | undefined;
  allLaps: LapSummary[];
}

function computeBestSectors(allLaps: LapSummary[]): number[] | null {
  const validSectors = allLaps
    .filter((l) => !l.is_invalid && l.sector_times_s != null)
    .map((l) => l.sector_times_s!);

  if (validSectors.length === 0) return null;

  const sectorCount = validSectors[0]!.length;
  const bests: number[] = [];
  for (let i = 0; i < sectorCount; i++) {
    bests.push(Math.min(...validSectors.map((s) => s[i] ?? Infinity)));
  }
  return bests;
}

export function LapSummaryPanel({
  primaryDetail,
  secondaryDetail,
  allLaps,
}: LapSummaryPanelProps) {
  if (!primaryDetail) return null;

  const pm = primaryDetail.metrics;
  const sm = secondaryDetail?.metrics;

  const sectorTimes = pm.timing.sector_times_s;
  const bestSectors = computeBestSectors(allLaps);

  return (
    <div data-testid="summary-panel">
      <div className="ace-summary-panel">
        <div className="ace-summary-panel__item">
          <span className="ace-summary-panel__label">Lap Time</span>
          <span className="ace-summary-panel__value">
            <DataCell
              value={formatLapTime(pm.timing.lap_time_s)}
              delta={
                sm
                  ? Math.round((pm.timing.lap_time_s - sm.timing.lap_time_s) * 1000) / 1000
                  : undefined
              }
            />
          </span>
        </div>
        <div className="ace-summary-panel__item">
          <span className="ace-summary-panel__label">Max Speed</span>
          <span className="ace-summary-panel__value">
            <DataCell
              value={formatSpeed(pm.speed.max_speed)}
              delta={
                sm
                  ? Math.round((pm.speed.max_speed - sm.speed.max_speed) * 10) / 10
                  : undefined
              }
            />
          </span>
        </div>
        <div className="ace-summary-panel__item">
          <span className="ace-summary-panel__label">Avg Speed</span>
          <span className="ace-summary-panel__value">
            <DataCell
              value={formatSpeed(pm.speed.avg_speed)}
              delta={
                sm
                  ? Math.round((pm.speed.avg_speed - sm.speed.avg_speed) * 10) / 10
                  : undefined
              }
            />
          </span>
        </div>
        <div className="ace-summary-panel__item">
          <span className="ace-summary-panel__label">Full Throttle</span>
          <span className="ace-summary-panel__value">
            <DataCell
              value={formatPercentage(pm.driver_inputs.full_throttle_pct)}
              delta={
                sm
                  ? Math.round((pm.driver_inputs.full_throttle_pct - sm.driver_inputs.full_throttle_pct) * 10) / 10
                  : undefined
              }
            />
          </span>
        </div>
        <div className="ace-summary-panel__item">
          <span className="ace-summary-panel__label">Braking</span>
          <span className="ace-summary-panel__value">
            <DataCell
              value={formatPercentage(pm.driver_inputs.braking_pct)}
              delta={
                sm
                  ? Math.round((pm.driver_inputs.braking_pct - sm.driver_inputs.braking_pct) * 10) / 10
                  : undefined
              }
            />
          </span>
        </div>
        <div className="ace-summary-panel__item">
          <span className="ace-summary-panel__label">Tyre Temps</span>
          <span className="ace-summary-panel__value">
            {Object.entries(pm.tyres.temps_avg).map(([wheel, zones]) => (
              <span key={wheel} style={{ marginRight: 8 }}>
                {wheel.toUpperCase()}: {formatTemperature(zones.core)}
              </span>
            ))}
          </span>
        </div>
      </div>

      {sectorTimes && sectorTimes.length > 0 && (
        <div className="ace-sectors" data-testid="sector-times">
          {sectorTimes.map((time, i) => {
            const isBest = bestSectors != null && bestSectors[i] != null && Math.abs(time - bestSectors[i]) < 0.001;
            const secTime = sm?.timing.sector_times_s?.[i];
            return (
              <div key={i} className="ace-sectors__item">
                <span className="ace-sectors__label">
                  Sector {i + 1}
                  {isBest && (
                    <Badge variant="success">Best</Badge>
                  )}
                </span>
                <span className="ace-sectors__time">
                  <DataCell
                    value={formatDelta(time).replace("+", "")}
                    delta={secTime != null ? Math.round((time - secTime) * 1000) / 1000 : undefined}
                  />
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
