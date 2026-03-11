import { useState, useCallback, useMemo } from "react";
import { useQueryClient, useQueries } from "@tanstack/react-query";
import { EmptyState, Button } from "../../components/ui";
import { useSessionStore } from "../../store/sessionStore";
import { useUIStore } from "../../store/uiStore";
import { useNotificationStore } from "../../store/notificationStore";
import { useSessions } from "../../hooks/useSessions";
import { useMessages } from "../../hooks/useMessages";
import { useRecommendations } from "../../hooks/useRecommendations";
import { useJobProgress } from "../../hooks/useJobProgress";
import { apiGet, apiPost } from "../../lib/api";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { ApplyConfirmModal } from "./ApplyConfirmModal";
import type {
  EngineerJobResponse,
  ChatJobResponse,
  ApplyResponse,
  RecommendationDetailResponse,
  RecommendationUsageResponse,
  MessageUsageResponse,
} from "../../lib/types";
import { Modal } from "../../components/ui";
import "./EngineerView.css";

export function EngineerView() {
  const selectedSessionId = useSessionStore((s) => s.selectedSessionId);
  const { sessions } = useSessions();
  const queryClient = useQueryClient();
  const addNotification = useNotificationStore((s) => s.addNotification);

  const session = useMemo(
    () => sessions.find((s) => s.session_id === selectedSessionId) ?? null,
    [sessions, selectedSessionId],
  );

  const isAnalyzed =
    session?.state === "analyzed" || session?.state === "engineered";

  // Data fetching
  const messagesQuery = useMessages(isAnalyzed ? selectedSessionId : null);
  const recsQuery = useRecommendations(isAnalyzed ? selectedSessionId : null);

  // Fetch detail for each recommendation via useQueries (safe with dynamic arrays)
  const recSummaries = recsQuery.data?.recommendations ?? [];
  const recDetailResults = useQueries({
    queries: recSummaries.map((r) => ({
      queryKey: ["recommendation", selectedSessionId, r.recommendation_id],
      queryFn: () =>
        apiGet<RecommendationDetailResponse>(
          `/sessions/${selectedSessionId}/recommendations/${r.recommendation_id}`,
        ),
      staleTime: Infinity,
      enabled: !!selectedSessionId && !!r.recommendation_id,
    })),
  });
  const recDetails: RecommendationDetailResponse[] = recDetailResults
    .map((q) => q.data)
    .filter((d): d is RecommendationDetailResponse => d != null);

  // Fetch usage data for each recommendation
  const recUsageResults = useQueries({
    queries: recSummaries.map((r) => ({
      queryKey: ["recommendation-usage", selectedSessionId, r.recommendation_id],
      queryFn: () =>
        apiGet<RecommendationUsageResponse>(
          `/sessions/${selectedSessionId}/recommendations/${r.recommendation_id}/usage`,
        ),
      staleTime: Infinity,
      enabled: !!selectedSessionId && !!r.recommendation_id,
    })),
  });
  const recUsageMap = useMemo(() => {
    const map = new Map<string, RecommendationUsageResponse>();
    for (const q of recUsageResults) {
      if (q.data) {
        map.set(q.data.recommendation_id, q.data);
      }
    }
    return map;
  }, [recUsageResults]);

  const messages = messagesQuery.data?.messages ?? [];

  // Fetch usage data for each assistant message
  const assistantMessageIds = useMemo(
    () =>
      messages
        .filter((m) => m.role === "assistant")
        .map((m) => m.message_id),
    [messages],
  );
  const msgUsageResults = useQueries({
    queries: assistantMessageIds.map((mid) => ({
      queryKey: ["message-usage", selectedSessionId, mid],
      queryFn: () =>
        apiGet<MessageUsageResponse>(
          `/sessions/${selectedSessionId}/messages/${mid}/usage`,
        ),
      staleTime: Infinity,
      enabled: !!selectedSessionId && !!mid,
    })),
  });
  const messageUsageMap = useMemo(() => {
    const map = new Map<string, MessageUsageResponse>();
    for (const q of msgUsageResults) {
      if (q.data && q.data.totals.total_tokens > 0) {
        map.set(q.data.message_id, q.data);
      }
    }
    return map;
  }, [msgUsageResults]);

  // Job management
  const [engineerJobId, setEngineerJobId] = useState<string | null>(null);
  const [chatJobId, setChatJobId] = useState<string | null>(null);
  const engineerProgress = useJobProgress(engineerJobId);
  const chatProgress = useJobProgress(chatJobId);

  const engineerDone =
    engineerProgress?.status === "completed" ||
    engineerProgress?.status === "failed";
  const chatDone =
    chatProgress?.status === "completed" ||
    chatProgress?.status === "failed";

  // Clear completed jobs and refetch
  if (engineerJobId && engineerDone) {
    if (engineerProgress?.status === "completed") {
      queryClient.invalidateQueries({ queryKey: ["messages", selectedSessionId] });
      queryClient.invalidateQueries({ queryKey: ["recommendations", selectedSessionId] });
    }
    if (engineerProgress?.status === "failed") {
      addNotification("error", engineerProgress.error ?? "Analysis failed");
    }
    setEngineerJobId(null);
  }
  if (chatJobId && chatDone) {
    if (chatProgress?.status === "completed") {
      queryClient.invalidateQueries({ queryKey: ["messages", selectedSessionId] });
    }
    if (chatProgress?.status === "failed") {
      addNotification("error", chatProgress.error ?? "Chat response failed");
    }
    setChatJobId(null);
  }

  const activeJobType: "engineer" | "chat" | null = engineerJobId
    ? "engineer"
    : chatJobId
      ? "chat"
      : null;
  const jobProgress = engineerJobId ? engineerProgress : chatProgress;
  const isJobRunning = activeJobType !== null;

  // Re-analysis warning
  const [showReanalysisWarning, setShowReanalysisWarning] = useState(false);

  const hasConversation = messages.length > 0 || recDetails.length > 0;

  const startAnalysis = useCallback(async () => {
    if (!selectedSessionId) return;
    try {
      const res = await apiPost<EngineerJobResponse>(
        `/sessions/${selectedSessionId}/engineer`,
      );
      setEngineerJobId(res.job_id);
    } catch (err) {
      addNotification(
        "error",
        err instanceof Error ? err.message : "Failed to start analysis",
      );
    }
  }, [selectedSessionId, addNotification]);

  const handleAnalyze = useCallback(() => {
    if (hasConversation) {
      setShowReanalysisWarning(true);
    } else {
      startAnalysis();
    }
  }, [hasConversation, startAnalysis]);

  const handleConfirmReanalysis = useCallback(() => {
    setShowReanalysisWarning(false);
    startAnalysis();
  }, [startAnalysis]);

  // Chat
  const handleSendMessage = useCallback(
    async (content: string) => {
      if (!selectedSessionId) return;
      try {
        const res = await apiPost<ChatJobResponse>(
          `/sessions/${selectedSessionId}/messages`,
          { content },
        );
        setChatJobId(res.job_id);
        // Refetch to show the user message immediately
        queryClient.invalidateQueries({ queryKey: ["messages", selectedSessionId] });
      } catch (err) {
        addNotification(
          "error",
          err instanceof Error ? err.message : "Failed to send message",
        );
      }
    },
    [selectedSessionId, addNotification, queryClient],
  );

  // Apply recommendation
  const [applyingRecId, setApplyingRecId] = useState<string | null>(null);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [isApplying, setIsApplying] = useState(false);

  const applyingRec = recDetails.find(
    (r) => r.recommendation_id === applyingRecId,
  ) ?? null;

  const handleApply = useCallback((recId: string) => {
    setApplyingRecId(recId);
    setShowApplyModal(true);
  }, []);

  const handleConfirmApply = useCallback(async () => {
    if (!selectedSessionId || !applyingRecId) return;
    setIsApplying(true);
    try {
      await apiPost<ApplyResponse>(
        `/sessions/${selectedSessionId}/recommendations/${applyingRecId}/apply`,
        { setup_path: "" },
      );
      addNotification("success", "Setup changes applied successfully");
      queryClient.invalidateQueries({
        queryKey: ["recommendations", selectedSessionId],
      });
      // Invalidate the detail cache so it refetches with updated status
      queryClient.invalidateQueries({
        queryKey: ["recommendation", selectedSessionId, applyingRecId],
      });
    } catch (err) {
      addNotification(
        "error",
        err instanceof Error ? err.message : "Failed to apply changes",
      );
    } finally {
      setIsApplying(false);
      setShowApplyModal(false);
      setApplyingRecId(null);
    }
  }, [selectedSessionId, applyingRecId, addNotification, queryClient]);

  // Empty states
  if (!selectedSessionId) {
    return (
      <EmptyState
        icon={<span>&#129302;</span>}
        title="Select a session"
        description="Go to Sessions and select a session to get AI-powered setup recommendations."
        action={{
          label: "Go to Sessions",
          onClick: () => useUIStore.getState().setActiveSection("sessions"),
        }}
      />
    );
  }

  if (!isAnalyzed) {
    return (
      <EmptyState
        icon={<span>&#128269;</span>}
        title="Analysis required"
        description="This session needs to be processed and analyzed before the engineer can review it."
      />
    );
  }

  return (
    <div className="ace-engineer-view">
      <div className="ace-engineer-header">
        <div className="ace-engineer-header__info">
          {session && (
            <span>
              {session.car} &mdash; {session.track}
            </span>
          )}
        </div>
        <div className="ace-engineer-header__actions">
          <Button
            variant="primary"
            size="sm"
            disabled={isJobRunning}
            onClick={handleAnalyze}
          >
            Analyze Session
          </Button>
        </div>
      </div>

      <MessageList
        messages={messages}
        recommendations={recDetails}
        sessionId={selectedSessionId}
        activeJobType={activeJobType}
        jobProgress={jobProgress ?? undefined}
        onApply={handleApply}
        usageMap={recUsageMap}
        messageUsageMap={messageUsageMap}
      />

      <ChatInput onSend={handleSendMessage} disabled={isJobRunning} />

      <ApplyConfirmModal
        open={showApplyModal}
        onClose={() => {
          setShowApplyModal(false);
          setApplyingRecId(null);
        }}
        onConfirm={handleConfirmApply}
        recommendation={applyingRec}
        isApplying={isApplying}
      />

      <Modal
        open={showReanalysisWarning}
        onClose={() => setShowReanalysisWarning(false)}
        title="Re-analyze session?"
        actions={{
          confirm: {
            label: "Proceed",
            onClick: handleConfirmReanalysis,
          },
          cancel: {
            label: "Cancel",
            onClick: () => setShowReanalysisWarning(false),
          },
        }}
      >
        <p>
          This session already has conversation history. Running a new analysis
          will add new recommendations to the existing conversation.
        </p>
      </Modal>
    </div>
  );
}
