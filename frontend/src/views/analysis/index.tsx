import { useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { EmptyState, Skeleton } from "../../components/ui";
import { useLaps, useLapDetail, useLapTelemetry } from "../../hooks/useLaps";
import { useSessions } from "../../hooks/useSessions";
import { LapList } from "./LapList";
import { TelemetryChart } from "./TelemetryChart";
import { CornerTable } from "./CornerTable";
import { LapSummaryPanel } from "./LapSummaryPanel";
import "./AnalysisView.css";

export function AnalysisView() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { sessions } = useSessions();
  const [selectedLaps, setSelectedLaps] = useState<number[]>([]);

  const { data: lapData, isLoading: lapsLoading } = useLaps(sessionId ?? null);

  const primaryLap = selectedLaps[0] ?? null;
  const secondaryLap = selectedLaps[1] ?? null;

  const { data: primaryDetail } = useLapDetail(
    sessionId ?? null,
    primaryLap,
    primaryLap != null,
  );
  const { data: secondaryDetail } = useLapDetail(
    sessionId ?? null,
    secondaryLap,
    secondaryLap != null,
  );
  const { data: primaryTelemetry, isLoading: telemetryLoading } = useLapTelemetry(
    sessionId ?? null,
    primaryLap,
    primaryLap != null,
  );
  const { data: secondaryTelemetry } = useLapTelemetry(
    sessionId ?? null,
    secondaryLap,
    secondaryLap != null,
  );

  const handleToggleLap = useCallback((lapNumber: number) => {
    setSelectedLaps((prev) => {
      if (prev.includes(lapNumber)) {
        return prev.filter((n) => n !== lapNumber);
      }
      if (prev.length >= 2) {
        // Replace oldest (first) selection
        return [prev[1]!, lapNumber];
      }
      return [...prev, lapNumber];
    });
  }, []);

  // Empty state: no session selected
  if (!sessionId) {
    navigate("/garage");
    return null;
  }

  // Check session state
  const session = sessions.find((s) => s.session_id === sessionId);
  if (session && session.state !== "analyzed" && session.state !== "engineered") {
    return (
      <EmptyState
        icon={<i className="fa-solid fa-triangle-exclamation" />}
        title="Analysis required"
        description="This session needs to be processed before lap analysis is available."
      />
    );
  }

  // Loading
  if (lapsLoading) {
    return (
      <div className="ace-analysis">
        <div className="ace-analysis__sidebar">
          <Skeleton height="24px" width="100px" />
          <Skeleton height="40px" />
          <Skeleton height="40px" />
          <Skeleton height="40px" />
        </div>
        <div className="ace-analysis__main">
          <Skeleton height="200px" />
        </div>
      </div>
    );
  }

  const laps = lapData?.laps ?? [];

  // No laps
  if (laps.length === 0) {
    return (
      <EmptyState
        icon={<i className="fa-solid fa-chart-line" />}
        title="No laps found"
        description="This session has no laps to analyze."
      />
    );
  }

  // Find fastest flying lap
  const flyingLaps = laps.filter((l) => l.classification === "flying" && !l.is_invalid);
  const fastestLap = flyingLaps.length > 0
    ? flyingLaps.reduce((best, lap) =>
        lap.lap_time_s < best.lap_time_s ? lap : best,
      )
    : null;

  return (
    <div className="ace-analysis">
      <LapList
        laps={laps}
        fastestLapNumber={fastestLap?.lap_number ?? null}
        selectedLaps={selectedLaps}
        onToggleLap={handleToggleLap}
      />
      <div className="ace-analysis__main">
        {primaryLap == null ? (
          <EmptyState
            icon={<i className="fa-solid fa-chart-line" />}
            title="Select a lap to view telemetry"
            description="Click a lap in the sidebar to view its telemetry data."
          />
        ) : (
          <>
            <LapSummaryPanel
              primaryDetail={primaryDetail}
              secondaryDetail={secondaryDetail}
              allLaps={laps}
            />
            <TelemetryChart
              primaryTelemetry={primaryTelemetry}
              primaryLapNumber={primaryLap}
              secondaryTelemetry={secondaryTelemetry}
              secondaryLapNumber={secondaryLap ?? undefined}
              isLoading={telemetryLoading}
            />
            <CornerTable
              primaryCorners={primaryDetail?.corners ?? []}
              primaryLapNumber={primaryLap}
              secondaryCorners={secondaryDetail?.corners}
              secondaryLapNumber={secondaryLap ?? undefined}
            />
          </>
        )}
      </div>
    </div>
  );
}
