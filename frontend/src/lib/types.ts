export interface SessionRecord {
  session_id: string;
  car: string;
  track: string;
  session_date: string;
  lap_count: number;
  best_lap_time: number | null;
  state: string;
  session_type: string | null;
  csv_path: string | null;
  meta_path: string | null;
}

export interface SessionListResponse {
  sessions: SessionRecord[];
}

export interface ProcessResponse {
  job_id: string;
  session_id: string;
}

export interface SyncResult {
  discovered: number;
  already_known: number;
  incomplete: number;
}

export type UISessionState = "new" | "processing" | "ready" | "engineered" | "failed";

export interface ProcessingJobInfo {
  jobId: string;
  error: string | null;
}
