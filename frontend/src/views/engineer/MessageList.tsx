import { useEffect, useRef, useCallback } from "react";
import { UserMessage } from "./UserMessage";
import { AssistantMessage } from "./AssistantMessage";
import { RecommendationCard } from "./RecommendationCard";
import { DriverFeedbackCard } from "./DriverFeedbackCard";
import { TypingIndicator } from "./TypingIndicator";
import { AnalysisProgress } from "./AnalysisProgress";
import type {
  MessageResponse,
  RecommendationDetailResponse,
  FeedItem,
} from "../../lib/types";
import type { JobProgress } from "../../store/jobStore";

interface MessageListProps {
  messages: MessageResponse[];
  recommendations: RecommendationDetailResponse[];
  activeJobType: "engineer" | "chat" | null;
  jobProgress: JobProgress | undefined;
  onApply: (recommendationId: string) => void;
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

export function MessageList({
  messages,
  recommendations,
  activeJobType,
  jobProgress,
  onApply,
}: MessageListProps) {
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
          return msg.role === "user" ? (
            <UserMessage
              key={msg.message_id}
              content={msg.content}
              timestamp={msg.created_at}
            />
          ) : (
            <AssistantMessage
              key={msg.message_id}
              content={msg.content}
              timestamp={msg.created_at}
            />
          );
        }
        const rec = item.data;
        return (
          <div key={rec.recommendation_id}>
            <RecommendationCard recommendation={rec} onApply={onApply} />
            {rec.driver_feedback.map((fb, j) => (
              <DriverFeedbackCard key={j} feedback={fb} />
            ))}
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
    </div>
  );
}
