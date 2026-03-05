import { WS_BASE_URL, WS_MAX_RETRIES, WS_BASE_DELAY } from "./constants";
import { useJobStore } from "../store/jobStore";
import { useNotificationStore } from "../store/notificationStore";

interface WSMessage {
  event: string;
  job_id: string;
  status: string;
  progress: number;
  current_step: string | null;
  result: unknown;
  error: string | null;
}

class JobWSManager {
  private connections = new Map<string, WebSocket>();
  private retries = new Map<string, number>();

  trackJob(jobId: string): void {
    if (this.connections.has(jobId)) return;
    this.retries.set(jobId, 0);
    this.connect(jobId);
  }

  stopTracking(jobId: string): void {
    const ws = this.connections.get(jobId);
    if (ws) {
      ws.close();
      this.connections.delete(jobId);
    }
    this.retries.delete(jobId);
  }

  private connect(jobId: string): void {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/jobs/${jobId}`);
    this.connections.set(jobId, ws);

    ws.onmessage = (event: MessageEvent) => {
      const data = JSON.parse(event.data as string) as WSMessage;

      useJobStore.getState().updateJobProgress(jobId, {
        status: data.status as "pending" | "running" | "completed" | "failed",
        progress: data.progress,
        currentStep: data.current_step,
        result: data.result,
        error: data.error,
      });

      if (data.event === "completed") {
        useNotificationStore
          .getState()
          .addNotification("success", `Job ${jobId} completed`);
        this.cleanup(jobId);
      } else if (data.event === "error") {
        useNotificationStore
          .getState()
          .addNotification("error", data.error ?? `Job ${jobId} failed`);
        this.cleanup(jobId);
      }
    };

    ws.onclose = (event: CloseEvent) => {
      if (!this.connections.has(jobId)) return; // intentional close
      if (event.wasClean) return;

      const retryCount = this.retries.get(jobId) ?? 0;
      if (retryCount >= WS_MAX_RETRIES) {
        useNotificationStore
          .getState()
          .addNotification("error", "Live updates unavailable for this job");
        this.cleanup(jobId);
        return;
      }

      this.retries.set(jobId, retryCount + 1);
      const delay =
        WS_BASE_DELAY * Math.pow(2, retryCount) +
        Math.random() * 500;
      setTimeout(() => {
        if (this.retries.has(jobId)) {
          this.connect(jobId);
        }
      }, delay);
    };

    ws.onerror = () => {
      // onclose will fire after onerror
    };
  }

  private cleanup(jobId: string): void {
    const ws = this.connections.get(jobId);
    if (ws) {
      ws.close();
    }
    this.connections.delete(jobId);
    this.retries.delete(jobId);
  }
}

export const jobWSManager = new JobWSManager();
