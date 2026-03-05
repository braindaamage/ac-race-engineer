import { create } from "zustand";

export interface JobProgress {
  jobId: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  currentStep: string | null;
  result: unknown;
  error: string | null;
}

interface JobState {
  jobProgress: Record<string, JobProgress>;
  updateJobProgress: (jobId: string, update: Partial<JobProgress>) => void;
  removeJob: (jobId: string) => void;
}

export const useJobStore = create<JobState>((set) => ({
  jobProgress: {},
  updateJobProgress: (jobId, update) =>
    set((s) => ({
      jobProgress: {
        ...s.jobProgress,
        [jobId]: {
          ...({
            jobId,
            status: "pending",
            progress: 0,
            currentStep: null,
            result: null,
            error: null,
          } satisfies JobProgress),
          ...s.jobProgress[jobId],
          ...update,
        },
      },
    })),
  removeJob: (jobId) =>
    set((s) => {
      const { [jobId]: _, ...rest } = s.jobProgress;
      return { jobProgress: rest };
    }),
}));
