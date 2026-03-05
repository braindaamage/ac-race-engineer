import { useEffect } from "react";
import { useJobStore, type JobProgress } from "../store/jobStore";
import { jobWSManager } from "../lib/wsManager";

export function useJobProgress(jobId: string | null): JobProgress | undefined {
  useEffect(() => {
    if (!jobId) return;
    jobWSManager.trackJob(jobId);
    return () => {
      jobWSManager.stopTracking(jobId);
    };
  }, [jobId]);

  return useJobStore((s) => (jobId ? s.jobProgress[jobId] : undefined));
}
