import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MessageList } from "../../../src/views/engineer/MessageList";
import type {
  MessageResponse,
  RecommendationDetailResponse,
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
        activeJobType="engineer"
        jobProgress={progress}
        onApply={() => {}}
      />,
    );
    expect(container.querySelector(".ace-typing-indicator")).toBeNull();
  });
});
