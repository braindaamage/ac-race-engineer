import { useState, useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useSessions } from "../../hooks/useSessions";
import { useSessionStore } from "../../store/sessionStore";
import { useJobStore } from "../../store/jobStore";
import { useNotificationStore } from "../../store/notificationStore";
import { jobWSManager } from "../../lib/wsManager";
import { apiPost, apiDelete } from "../../lib/api";
import type { ProcessResponse, SyncResult, ProcessingJobInfo } from "../../lib/types";
import { Button, EmptyState, Skeleton, Modal } from "../../components/ui";
import { SessionCard } from "./SessionCard";
import { getUISessionState } from "./utils";
import "./SessionsView.css";

export function SessionsView() {
  const { sessions, isLoading, error, refetch } = useSessions();
  const queryClient = useQueryClient();
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId);
  const selectSession = useSessionStore((s) => s.selectSession);
  const clearSession = useSessionStore((s) => s.clearSession);
  const jobProgress = useJobStore((s) => s.jobProgress);
  const addNotification = useNotificationStore((s) => s.addNotification);

  const [processingJobs, setProcessingJobs] = useState<Map<string, ProcessingJobInfo>>(
    () => new Map(),
  );
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);

  useEffect(() => {
    setProcessingJobs((prev) => {
      const next = new Map(prev);
      let changed = false;

      for (const [sessionId, info] of prev) {
        const jp = jobProgress[info.jobId];
        if (!jp) continue;

        if (jp.status === "completed") {
          next.delete(sessionId);
          jobWSManager.stopTracking(info.jobId);
          changed = true;
        } else if (jp.status === "failed") {
          if (info.error === null) {
            next.set(sessionId, { ...info, error: jp.error ?? "Processing failed" });
            jobWSManager.stopTracking(info.jobId);
            changed = true;
          }
        }
      }

      if (changed) {
        queryClient.invalidateQueries({ queryKey: ["sessions"] });
      }

      return changed ? next : prev;
    });
  }, [jobProgress, queryClient]);

  const handleProcess = async (sessionId: string) => {
    try {
      const response = await apiPost<ProcessResponse>(`/sessions/${sessionId}/process`);
      setProcessingJobs((prev) => {
        const next = new Map(prev);
        next.set(sessionId, { jobId: response.job_id, error: null });
        return next;
      });
      jobWSManager.trackJob(response.job_id);
    } catch (err) {
      addNotification("error", `Failed to start processing: ${(err as Error).message}`);
    }
  };

  const handleSelect = (sessionId: string) => {
    selectSession(sessionId);
  };

  const handleDelete = (sessionId: string) => {
    setPendingDeleteId(sessionId);
  };

  const confirmDelete = async () => {
    if (!pendingDeleteId) return;
    try {
      await apiDelete(`/sessions/${pendingDeleteId}`);
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      if (pendingDeleteId === selectedSessionId) {
        clearSession();
      }
    } catch (err) {
      addNotification("error", `Failed to delete session: ${(err as Error).message}`);
    } finally {
      setPendingDeleteId(null);
    }
  };

  const cancelDelete = () => {
    setPendingDeleteId(null);
  };

  const handleSync = async () => {
    setIsSyncing(true);
    try {
      const result = await apiPost<SyncResult>("/sessions/sync");
      queryClient.invalidateQueries({ queryKey: ["sessions"] });
      if (result.discovered > 0) {
        addNotification("success", `Found ${result.discovered} new session(s)`);
      } else {
        addNotification("info", "All sessions up to date");
      }
    } catch (err) {
      addNotification("error", `Sync failed: ${(err as Error).message}`);
    } finally {
      setIsSyncing(false);
    }
  };

  const pendingSession = pendingDeleteId
    ? sessions.find((s) => s.session_id === pendingDeleteId)
    : null;

  const sortedSessions = [...sessions].sort(
    (a, b) => new Date(b.session_date).getTime() - new Date(a.session_date).getTime(),
  );

  return (
    <div className="ace-sessions">
      <div className="ace-sessions__header">
        <h1>Sessions</h1>
        <Button variant="secondary" onClick={handleSync} disabled={isSyncing}>
          {isSyncing ? "Syncing..." : "Sync"}
        </Button>
      </div>

      {isLoading && (
        <div className="ace-sessions__list">
          <Skeleton variant="rect" height="100px" />
          <Skeleton variant="rect" height="100px" />
          <Skeleton variant="rect" height="100px" />
        </div>
      )}

      {!isLoading && error && (
        <EmptyState
          icon={<span>&#9888;</span>}
          title="Failed to load sessions"
          description={error.message}
          action={{ label: "Retry", onClick: () => refetch() }}
        />
      )}

      {!isLoading && !error && sessions.length === 0 && (
        <EmptyState
          icon={<span>&#128203;</span>}
          title="No sessions recorded yet"
          description="Sessions are recorded automatically while you drive in Assetto Corsa. Make sure the AC Race Engineer app is installed in your Assetto Corsa folder, then go for a drive!"
        />
      )}

      {!isLoading && !error && sessions.length > 0 && (
        <div className="ace-sessions__list">
          {sortedSessions.map((session) => {
            const uiState = getUISessionState(session, processingJobs);
            const jobInfo = processingJobs.get(session.session_id);
            const jp = jobInfo ? jobProgress[jobInfo.jobId] : undefined;
            return (
              <SessionCard
                key={session.session_id}
                session={session}
                uiState={uiState}
                isSelected={session.session_id === selectedSessionId}
                jobProgress={jp}
                jobError={jobInfo?.error ?? null}
                onProcess={() => handleProcess(session.session_id)}
                onSelect={() => handleSelect(session.session_id)}
                onDelete={() => handleDelete(session.session_id)}
              />
            );
          })}
        </div>
      )}

      <Modal
        open={pendingDeleteId !== null}
        onClose={cancelDelete}
        title="Delete Session"
        actions={{
          confirm: { label: "Delete", onClick: confirmDelete, variant: "primary" },
          cancel: { label: "Cancel", onClick: cancelDelete },
        }}
      >
        {pendingSession ? (
          <p>
            Delete session <strong>{pendingSession.car}</strong> at{" "}
            <strong>{pendingSession.track}</strong>?
          </p>
        ) : (
          <p>Delete this session?</p>
        )}
      </Modal>
    </div>
  );
}
