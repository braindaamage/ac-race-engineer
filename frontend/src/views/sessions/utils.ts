import type { SessionRecord, UISessionState, ProcessingJobInfo } from "../../lib/types";

export function getUISessionState(
  session: SessionRecord,
  processingJobs: Map<string, ProcessingJobInfo>,
): UISessionState {
  const jobInfo = processingJobs.get(session.session_id);
  if (jobInfo) {
    if (jobInfo.error !== null) return "failed";
    return "processing";
  }

  switch (session.state) {
    case "analyzed":
      return "ready";
    case "engineered":
      return "engineered";
    default:
      return "new";
  }
}

export function formatCarTrack(name: string): string {
  let formatted = name;
  if (formatted.startsWith("ks_")) {
    formatted = formatted.slice(3);
  }
  return formatted.replace(/_/g, " ");
}
