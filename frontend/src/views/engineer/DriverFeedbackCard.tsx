import { Badge } from "../../components/ui";
import type { DriverFeedbackDetail } from "../../lib/types";

interface DriverFeedbackCardProps {
  feedback: DriverFeedbackDetail;
}

const SEVERITY_VARIANT: Record<string, "error" | "warning" | "info"> = {
  high: "error",
  medium: "warning",
  low: "info",
};

export function DriverFeedbackCard({ feedback }: DriverFeedbackCardProps) {
  const cornersText =
    feedback.corners_affected.length > 0
      ? feedback.corners_affected.map((c) => `Turn ${c}`).join(", ")
      : null;

  return (
    <div className="ace-driver-feedback">
      <div className="ace-driver-feedback__header">
        <span className="ace-driver-feedback__area">{feedback.area}</span>
        <Badge variant={SEVERITY_VARIANT[feedback.severity] ?? "info"}>
          {feedback.severity}
        </Badge>
      </div>
      <div className="ace-driver-feedback__observation">
        {feedback.observation}
      </div>
      <div className="ace-driver-feedback__suggestion">
        {feedback.suggestion}
      </div>
      {cornersText && (
        <div className="ace-driver-feedback__corners">{cornersText}</div>
      )}
    </div>
  );
}
