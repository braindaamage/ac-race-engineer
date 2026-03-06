import { Card, Badge, Button, ProgressBar } from "../../components/ui";
import type { SessionRecord, UISessionState } from "../../lib/types";
import type { JobProgress } from "../../store/jobStore";
import { formatCarTrack } from "./utils";

interface SessionCardProps {
  session: SessionRecord;
  uiState: UISessionState;
  isSelected: boolean;
  jobProgress: JobProgress | undefined;
  jobError: string | null;
  onProcess: () => void;
  onSelect: () => void;
  onDelete: () => void;
}

const BADGE_VARIANT: Record<UISessionState, "info" | "neutral" | "success" | "error"> = {
  new: "info",
  processing: "neutral",
  ready: "success",
  engineered: "success",
  failed: "error",
};

const BADGE_LABEL: Record<UISessionState, string> = {
  new: "New",
  processing: "Processing",
  ready: "Ready",
  engineered: "Engineered",
  failed: "Failed",
};

export function SessionCard({
  session,
  uiState,
  isSelected,
  jobProgress,
  jobError,
  onProcess,
  onSelect,
  onDelete,
}: SessionCardProps) {
  const classNames = ["ace-session-card"];
  if (isSelected) classNames.push("ace-session-card--selected");

  const handleClick = () => {
    if (uiState === "ready" || uiState === "engineered") {
      onSelect();
    }
  };

  return (
    <div className={classNames.join(" ")} onClick={handleClick}>
      <Card>
        <div className="ace-session-card__header">
          <div className="ace-session-card__info">
            <span className="ace-session-card__car">{formatCarTrack(session.car)}</span>
            <span className="ace-session-card__track">{formatCarTrack(session.track)}</span>
          </div>
          <div className="ace-session-card__actions">
            <Badge variant={BADGE_VARIANT[uiState]}>{BADGE_LABEL[uiState]}</Badge>
            <button
              className="ace-session-card__delete"
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              aria-label="Delete session"
            >
              &times;
            </button>
          </div>
        </div>
        <div className="ace-session-card__meta">
          <span>{new Date(session.session_date).toLocaleDateString()}</span>
          <span>{session.lap_count} laps</span>
        </div>
        {uiState === "new" && (
          <div className="ace-session-card__actions">
            <Button
              variant="secondary"
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation();
                onProcess();
              }}
            >
              Process
            </Button>
          </div>
        )}
        {uiState === "processing" && jobProgress && (
          <div className="ace-session-card__progress">
            <ProgressBar value={jobProgress.progress} />
            {jobProgress.currentStep && (
              <span className="ace-session-card__step">{jobProgress.currentStep}</span>
            )}
          </div>
        )}
        {uiState === "failed" && (
          <div className="ace-session-card__error-area">
            {jobError && <span className="ace-session-card__error">{jobError}</span>}
            <Button
              variant="secondary"
              onClick={(e: React.MouseEvent) => {
                e.stopPropagation();
                onProcess();
              }}
            >
              Retry
            </Button>
          </div>
        )}
      </Card>
    </div>
  );
}
