import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "../../../src/views/engineer/MessageList";

vi.mock("../../../src/hooks/useTrace", () => ({
  useTrace: () => ({ data: undefined, isLoading: false }),
}));
import type {
  MessageResponse,
  RecommendationDetailResponse,
  MessageUsageResponse,
} from "../../../src/lib/types";
import type { JobProgress } from "../../../src/store/jobStore";

const makeMsg = (
  id: string,
  role: "user" | "assistant",
  content: string,
  time: string,
): MessageResponse => ({
  message_id: id,
  role,
  content,
  created_at: time,
});

const makeRec = (
  id: string,
  time: string,
  overrides?: Partial<RecommendationDetailResponse>,
): RecommendationDetailResponse => ({
  recommendation_id: id,
  session_id: "sess-1",
  status: "proposed",
  summary: `Recommendation ${id}`,
  explanation: "Explanation",
  confidence: "high",
  signals_addressed: [],
  setup_changes: [
    {
      section: "ARB",
      parameter: "FRONT",
      old_value: "3",
      new_value: "5",
      reasoning: "Reason",
      expected_effect: "Effect",
      confidence: "high",
      storage_value_before: null,
      storage_value_after: null,
      storage_convention: null,
    },
  ],
  driver_feedback: [],
  created_at: time,
  ...overrides,
});

describe("MessageList", () => {
  it("renders empty state when no feed items", () => {
    render(
      <MessageList
        messages={[]}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
      />,
    );
    expect(screen.getByText(/No conversation yet/)).toBeInTheDocument();
  });

  it("renders user messages as UserMessage bubbles", () => {
    const msgs = [makeMsg("m1", "user", "Hello engineer", "2026-03-01T12:00:00Z")];
    render(
      <MessageList
        messages={msgs}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
      />,
    );
    expect(screen.getByText("Hello engineer")).toBeInTheDocument();
  });

  it("renders assistant messages as AssistantMessage bubbles", () => {
    const msgs = [
      makeMsg("m1", "assistant", "I see understeer", "2026-03-01T12:00:00Z"),
    ];
    render(
      <MessageList
        messages={msgs}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
      />,
    );
    expect(screen.getByText("I see understeer")).toBeInTheDocument();
  });

  it("renders recommendation items as RecommendationCard", () => {
    const recs = [makeRec("r1", "2026-03-01T12:01:00Z")];
    render(
      <MessageList
        messages={[]}
        recommendations={recs}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
      />,
    );
    expect(screen.getByText("Recommendation r1")).toBeInTheDocument();
  });

  it("merge-sorts messages and recommendations by created_at", () => {
    const msgs = [
      makeMsg("m1", "user", "First", "2026-03-01T12:00:00Z"),
      makeMsg("m2", "assistant", "Third", "2026-03-01T12:02:00Z"),
    ];
    const recs = [makeRec("r1", "2026-03-01T12:01:00Z")];

    const { container } = render(
      <MessageList
        messages={msgs}
        recommendations={recs}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
      />,
    );

    const listEl = container.querySelector(".ace-message-list");
    const children = listEl?.children;
    expect(children).toBeDefined();
    // First: user message "First", then rec card, then assistant "Third"
    expect(children![0]!.textContent).toContain("First");
    expect(children![1]!.textContent).toContain("Recommendation r1");
    expect(children![2]!.textContent).toContain("Third");
  });

  it("shows AnalysisProgress when activeJobType is engineer", () => {
    const progress: JobProgress = {
      jobId: "j1",
      status: "running",
      progress: 50,
      currentStep: "Analyzing corners",
      result: null,
      error: null,
    };
    render(
      <MessageList
        messages={[]}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType="engineer"
        jobProgress={progress}
        onApply={() => {}}
      />,
    );
    expect(screen.getByText("Analyzing corners")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("shows TypingIndicator when activeJobType is chat", () => {
    const { container } = render(
      <MessageList
        messages={[]}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType="chat"
        jobProgress={undefined}
        onApply={() => {}}
      />,
    );
    expect(
      container.querySelector(".ace-typing-indicator"),
    ).toBeInTheDocument();
  });

  it("does not show TypingIndicator when activeJobType is engineer", () => {
    const progress: JobProgress = {
      jobId: "j1",
      status: "running",
      progress: 50,
      currentStep: "Loading",
      result: null,
      error: null,
    };
    const { container } = render(
      <MessageList
        messages={[]}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType="engineer"
        jobProgress={progress}
        onApply={() => {}}
      />,
    );
    expect(container.querySelector(".ace-typing-indicator")).toBeNull();
  });

  it("renders UsageSummaryBar below assistant messages with usage data", () => {
    const msgs = [
      makeMsg("m1", "assistant", "Here is your analysis", "2026-03-01T12:00:00Z"),
    ];
    const usageMap = new Map<string, MessageUsageResponse>();
    usageMap.set("m1", {
      message_id: "m1",
      totals: {
        input_tokens: 1520,
        output_tokens: 340,
        total_tokens: 1860,
        cache_read_tokens: 0,
        cache_write_tokens: 0,
        tool_call_count: 2,
        agent_count: 1,
      },
      agents: [],
    });

    const { container } = render(
      <MessageList
        messages={msgs}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
        messageUsageMap={usageMap}
      />,
    );
    expect(container.querySelector(".ace-usage-summary")).toBeInTheDocument();
  });

  it("does NOT render UsageSummaryBar for messages without usage data", () => {
    const msgs = [
      makeMsg("m1", "assistant", "Plain response", "2026-03-01T12:00:00Z"),
    ];

    const { container } = render(
      <MessageList
        messages={msgs}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
        messageUsageMap={new Map()}
      />,
    );
    expect(container.querySelector(".ace-usage-summary")).toBeNull();
  });

  it("does NOT render UsageSummaryBar for user messages", () => {
    const msgs = [
      makeMsg("m1", "user", "A question", "2026-03-01T12:00:00Z"),
    ];
    const usageMap = new Map<string, MessageUsageResponse>();
    // Even if somehow there was usage data for a user msg, it shouldn't render
    usageMap.set("m1", {
      message_id: "m1",
      totals: {
        input_tokens: 100,
        output_tokens: 50,
        total_tokens: 150,
        cache_read_tokens: 0,
        cache_write_tokens: 0,
        tool_call_count: 0,
        agent_count: 1,
      },
      agents: [],
    });

    const { container } = render(
      <MessageList
        messages={msgs}
        recommendations={[]}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
        messageUsageMap={usageMap}
      />,
    );
    expect(container.querySelector(".ace-usage-summary")).toBeNull();
  });

  it("driver feedback renders only inside RecommendationCard, not duplicated", () => {
    const recs = [
      makeRec("r1", "2026-03-01T12:01:00Z", {
        driver_feedback: [
          {
            area: "balance",
            observation: "Understeer in T3",
            suggestion: "Trail brake deeper",
            corners_affected: [3],
            severity: "medium" as const,
          },
        ],
      }),
    ];

    render(
      <MessageList
        messages={[]}
        recommendations={recs}
        sessionId="sess-1"
        activeJobType={null}
        jobProgress={undefined}
        onApply={() => {}}
      />,
    );
    // The feedback text should appear exactly once (inside RecommendationCard)
    const feedbackElements = screen.getAllByText("Understeer in T3");
    expect(feedbackElements).toHaveLength(1);
  });
});
