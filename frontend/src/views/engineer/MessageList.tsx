import { useEffect, useRef, useCallback } from "react";
import { useState } from "react";
import { Button } from "../../components/ui";
import { UserMessage } from "./UserMessage";
import { AssistantMessage } from "./AssistantMessage";
import { RecommendationCard } from "./RecommendationCard";
import { TypingIndicator } from "./TypingIndicator";
import { AnalysisProgress } from "./AnalysisProgress";
import { UsageSummaryBar } from "./UsageSummaryBar";
import { UsageDetailModal } from "./UsageDetailModal";
import { TraceModal } from "./TraceModal";
import { useTrace } from "../../hooks/useTrace";
import type {
  MessageResponse,
  RecommendationDetailResponse,
  RecommendationUsageResponse,
  MessageUsageResponse,
  FeedItem,
} from "../../lib/types";
import type { JobProgress } from "../../store/jobStore";

interface MessageListProps {
  messages: MessageResponse[];
  recommendations: RecommendationDetailResponse[];
  sessionId: string | null;
  activeJobType: "engineer" | "chat" | null;
  jobProgress: JobProgress | undefined;
  onApply: (recommendationId: string) => void;
  usageMap?: Map<string, RecommendationUsageResponse>;
  messageUsageMap?: Map<string, MessageUsageResponse>;
}

function buildFeed(
  messages: MessageResponse[],
  recommendations: RecommendationDetailResponse[],
): FeedItem[] {
  const items: FeedItem[] = [
    ...messages.map(
      (m) => ({ type: "message", data: m }) as FeedItem,
    ),
    ...recommendations.map(
      (r) => ({ type: "recommendation", data: r }) as FeedItem,
    ),
  ];
  items.sort((a, b) => {
    const tA = a.type === "message" ? a.data.created_at : a.data.created_at;
    const tB = b.type === "message" ? b.data.created_at : b.data.created_at;
    return tA.localeCompare(tB);
  });
  return items;
}

function AssistantMessageWithTrace({
  msg,
  sessionId,
  msgUsage,
  onViewUsageDetails,
}: {
  msg: MessageResponse;
  sessionId: string | null;
  msgUsage?: MessageUsageResponse;
  onViewUsageDetails: (id: string) => void;
}) {
  const [showTraceModal, setShowTraceModal] = useState(false);
  const traceQuery = useTrace(sessionId, "message", msg.message_id);

  return (
    <div key={msg.message_id}>
      <AssistantMessage
        content={msg.content}
        timestamp={msg.created_at}
      />
      <div className="ace-message-actions">
        {msgUsage && (
          <UsageSummaryBar
            totals={msgUsage.totals}
            onViewDetails={() => onViewUsageDetails(msg.message_id)}
          />
        )}
        {traceQuery.data?.available && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowTraceModal(true)}
          >
            Trace
          </Button>
        )}
      </div>
      <TraceModal
        open={showTraceModal}
        onClose={() => setShowTraceModal(false)}
        traceContent={traceQuery.data?.content ?? null}
      />
    </div>
  );
}

export function MessageList({
  messages,
  recommendations,
  sessionId,
  activeJobType,
  jobProgress,
  onApply,
  usageMap,
  messageUsageMap,
}: MessageListProps) {
  const [usageDetailMsgId, setUsageDetailMsgId] = useState<string | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  const handleScroll = useCallback(() => {
    const el = listRef.current;
    if (!el) return;
    const threshold = 50;
    userScrolledUp.current =
      el.scrollHeight - el.scrollTop - el.clientHeight > threshold;
  }, []);

  const scrollToBottom = useCallback(() => {
    if (userScrolledUp.current) return;
    const el = listRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages.length, recommendations.length, activeJobType, scrollToBottom]);

  const feed = buildFeed(messages, recommendations);

  if (feed.length === 0 && !activeJobType) {
    return (
      <div className="ace-message-list" ref={listRef}>
        <div className="ace-message-list__empty">
          No conversation yet. Analyze the session or ask a question to get
          started.
        </div>
      </div>
    );
  }

  return (
    <div className="ace-message-list" ref={listRef} onScroll={handleScroll}>
      {feed.map((item) => {
        if (item.type === "message") {
          const msg = item.data;
          if (msg.role === "user") {
            return (
              <UserMessage
                key={msg.message_id}
                content={msg.content}
                timestamp={msg.created_at}
              />
            );
          }
          const msgUsage = messageUsageMap?.get(msg.message_id);
          return (
            <AssistantMessageWithTrace
              key={msg.message_id}
              msg={msg}
              sessionId={sessionId}
              msgUsage={msgUsage}
              onViewUsageDetails={setUsageDetailMsgId}
            />
          );
        }
        const rec = item.data;
        return (
          <div key={rec.recommendation_id}>
            <RecommendationCard
              recommendation={rec}
              sessionId={sessionId}
              onApply={onApply}
              usage={usageMap?.get(rec.recommendation_id)}
            />
          </div>
        );
      })}
      {activeJobType === "engineer" && jobProgress && (
        <AnalysisProgress
          progress={jobProgress.progress}
          currentStep={jobProgress.currentStep}
        />
      )}
      {activeJobType === "chat" && <TypingIndicator />}
      {usageDetailMsgId && messageUsageMap?.get(usageDetailMsgId) && (
        <UsageDetailModal
          open={true}
          onClose={() => setUsageDetailMsgId(null)}
          usage={{
            recommendation_id: usageDetailMsgId,
            totals: messageUsageMap.get(usageDetailMsgId)!.totals,
            agents: messageUsageMap.get(usageDetailMsgId)!.agents,
          }}
        />
      )}
    </div>
  );
}
