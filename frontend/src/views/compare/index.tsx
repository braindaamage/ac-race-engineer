import { useState, useCallback, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { EmptyState, Skeleton } from "../../components/ui";
import { useSessions } from "../../hooks/useSessions";
import { useStints, useStintComparison } from "../../hooks/useStints";
import { StintSelector } from "./StintSelector";
import { SetupDiff } from "./SetupDiff";
import { MetricsPanel } from "./MetricsPanel";
import "./CompareView.css";

export function CompareView() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const { sessions } = useSessions();
  const [selectedStints, setSelectedStints] = useState<[number, number | null]>([0, null]);

  const { data: stintData, isLoading: stintsLoading } = useStints(sessionId ?? null);

  const stints = stintData?.stints ?? [];

  // Default to first two stints when data loads
  useEffect(() => {
    if (stints.length >= 2) {
      setSelectedStints([0, 1]);
    } else if (stints.length === 1) {
      setSelectedStints([0, null]);
    }
  }, [stints.length]);

  const stintA = selectedStints[0];
  const stintB = selectedStints[1];

  const { data: comparisonData } = useStintComparison(
    sessionId ?? null,
    stintA,
    stintB,
  );

  const handleSelectStint = useCallback((stintIndex: number) => {
    setSelectedStints((prev) => {
      const [a, b] = prev;
      // Deselect if already selected
      if (a === stintIndex) return [b ?? stintIndex, null];
      if (b === stintIndex) return [a, null];
      // If two already selected, replace oldest (first)
      if (b != null) return [b, stintIndex];
      // Add as second
      return [a, stintIndex];
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
        description="This session needs to be processed and analyzed before setup comparison is available."
      />
    );
  }

  // Loading
  if (stintsLoading) {
    return (
      <div className="ace-compare">
        <div className="ace-compare__sidebar">
          <Skeleton height="24px" width="100px" />
          <Skeleton height="40px" />
          <Skeleton height="40px" />
          <Skeleton height="40px" />
        </div>
        <div className="ace-compare__main">
          <Skeleton height="200px" />
        </div>
      </div>
    );
  }

  // Single stint
  if (stints.length < 2) {
    return (
      <EmptyState
        icon={<i className="fa-solid fa-code-compare" />}
        title="Not enough stints"
        description="Setup comparison requires at least 2 stints in the session. Run more stints with different setups."
      />
    );
  }

  const comparison = comparisonData?.comparison;

  return (
    <div className="ace-compare">
      <StintSelector
        stints={stints}
        selectedStints={selectedStints}
        onSelect={handleSelectStint}
      />
      <div className="ace-compare__main">
        {comparison ? (
          <>
            <SetupDiff
              changes={comparison.setup_changes}
              stintAIndex={comparison.stint_a_index}
              stintBIndex={comparison.stint_b_index}
            />
            <MetricsPanel
              deltas={comparison.metric_deltas}
              stintAIndex={comparison.stint_a_index}
              stintBIndex={comparison.stint_b_index}
            />
          </>
        ) : stintB != null ? (
          <div className="ace-compare__main">
            <Skeleton height="200px" />
          </div>
        ) : (
          <EmptyState
            icon={<i className="fa-solid fa-code-compare" />}
            title="Select two stints"
            description="Select a second stint from the sidebar to compare setup configurations."
          />
        )}
      </div>
    </div>
  );
}
