import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { EngineerView } from "../../../src/views/engineer/index";
import type { ReactNode } from "react";

// Mock stores
vi.mock("../../../src/store/sessionStore", () => ({
  useSessionStore: vi.fn((selector: unknown) => {
    // Default: no session
    const state = { selectedSessionId: null };
    return (selector as (s: typeof state) => unknown)(state);
  }),
}));

vi.mock("../../../src/store/uiStore", () => ({
  useUIStore: { getState: () => ({ setActiveSection: vi.fn() }) },
}));

vi.mock("../../../src/store/notificationStore", () => ({
  useNotificationStore: vi.fn(() => vi.fn()),
}));

// Mock hooks
vi.mock("../../../src/hooks/useSessions", () => ({
  useSessions: vi.fn(() => ({
    sessions: [],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
}));

vi.mock("../../../src/hooks/useMessages", () => ({
  useMessages: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
}));

vi.mock("../../../src/hooks/useRecommendations", () => ({
  useRecommendations: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
}));

vi.mock("../../../src/hooks/useJobProgress", () => ({
  useJobProgress: vi.fn(() => undefined),
}));

vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

vi.mock("../../../src/lib/wsManager", () => ({
  jobWSManager: { trackJob: vi.fn(), stopTracking: vi.fn() },
}));

import { useSessionStore } from "../../../src/store/sessionStore";
import { useNotificationStore } from "../../../src/store/notificationStore";
import { useSessions } from "../../../src/hooks/useSessions";
import { useMessages } from "../../../src/hooks/useMessages";
import { useRecommendations } from "../../../src/hooks/useRecommendations";
import { useJobProgress } from "../../../src/hooks/useJobProgress";
import { apiGet, apiPost } from "../../../src/lib/api";

const mockedUseSessionStore = vi.mocked(useSessionStore);
const mockedUseSessions = vi.mocked(useSessions);
const mockedUseMessages = vi.mocked(useMessages);
const mockedUseRecommendations = vi.mocked(useRecommendations);
const mockedUseJobProgress = vi.mocked(useJobProgress);
const mockedUseNotificationStore = vi.mocked(useNotificationStore);
const mockedApiGet = vi.mocked(apiGet);
const mockedApiPost = vi.mocked(apiPost);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

function setupMocksForSession(overrides?: {
  sessionId?: string | null;
  sessionState?: string;
  messages?: unknown[];
  recommendations?: unknown[];
}) {
  const sessionId = overrides?.sessionId ?? "sess-1";
  const sessionState = overrides?.sessionState ?? "analyzed";
  const messages = overrides?.messages ?? [];
  const recommendations = overrides?.recommendations ?? [];

  mockedUseSessionStore.mockImplementation((selector: unknown) => {
    const state = { selectedSessionId: sessionId };
    return (selector as (s: typeof state) => unknown)(state);
  });

  mockedUseNotificationStore.mockImplementation(() => vi.fn());

  mockedUseSessions.mockReturnValue({
    sessions: sessionId
      ? [
          {
            session_id: sessionId,
            car: "ferrari_488",
            track: "spa",
            session_date: "2026-03-01T12:00:00Z",
            lap_count: 10,
            best_lap_time: 120.5,
            state: sessionState,
            session_type: "practice",
            csv_path: null,
            meta_path: null,
          },
        ]
      : [],
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  });

  mockedUseMessages.mockReturnValue({
    data: { session_id: sessionId ?? "", messages },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useMessages>);

  mockedUseRecommendations.mockReturnValue({
    data: { session_id: sessionId ?? "", recommendations },
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  } as unknown as ReturnType<typeof useRecommendations>);

  mockedUseJobProgress.mockReturnValue(undefined);
}

describe("EngineerView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  // US1: Trigger Full Session Analysis
  describe("US1 — Trigger Full Session Analysis", () => {
    it("shows 'Select a session' empty state when no session selected", () => {
      // Use factory defaults (sessionId: null, sessions: [])
      mockedUseNotificationStore.mockImplementation(() => vi.fn());
      render(<EngineerView />, { wrapper: createWrapper() });
      expect(screen.getByText("Select a session")).toBeInTheDocument();
    });

    it("shows 'Analysis required' empty state when session not analyzed", () => {
      setupMocksForSession({ sessionState: "discovered" });
      render(<EngineerView />, { wrapper: createWrapper() });
      expect(screen.getByText("Analysis required")).toBeInTheDocument();
    });

    it("shows empty conversation with Analyze Session button when session is analyzed", () => {
      setupMocksForSession();
      render(<EngineerView />, { wrapper: createWrapper() });
      expect(screen.getByText(/No conversation yet/)).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Analyze Session" }),
      ).toBeInTheDocument();
    });

    it("clicking Analyze Session calls POST /sessions/{id}/engineer", async () => {
      setupMocksForSession();
      mockedApiPost.mockResolvedValue({ job_id: "j1", session_id: "sess-1" });

      render(<EngineerView />, { wrapper: createWrapper() });
      fireEvent.click(
        screen.getByRole("button", { name: "Analyze Session" }),
      );

      await waitFor(() => {
        expect(mockedApiPost).toHaveBeenCalledWith(
          "/sessions/sess-1/engineer",
        );
      });
    });

    it("shows session info in header", () => {
      setupMocksForSession();
      render(<EngineerView />, { wrapper: createWrapper() });
      expect(screen.getByText(/ferrari_488/)).toBeInTheDocument();
      expect(screen.getByText(/spa/)).toBeInTheDocument();
    });
  });

  // US2: Follow-up Questions
  describe("US2 — Ask Follow-Up Questions", () => {
    it("typing and sending a message calls POST /sessions/{id}/messages", async () => {
      setupMocksForSession();
      mockedApiPost.mockResolvedValue({ job_id: "j2", message_id: "m1" });

      render(<EngineerView />, { wrapper: createWrapper() });
      const textarea = screen.getByPlaceholderText("Ask your engineer...");
      fireEvent.change(textarea, {
        target: { value: "What about understeer?" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Send" }));

      await waitFor(() => {
        expect(mockedApiPost).toHaveBeenCalledWith(
          "/sessions/sess-1/messages",
          { content: "What about understeer?" },
        );
      });
    });

    it("input enabled when no job is running", () => {
      setupMocksForSession();
      render(<EngineerView />, { wrapper: createWrapper() });
      expect(
        screen.getByPlaceholderText("Ask your engineer..."),
      ).not.toBeDisabled();
    });
  });

  // US3: Apply Setup Recommendations
  describe("US3 — Apply Setup Recommendations", () => {
    const recDetail = {
      recommendation_id: "rec-1",
      session_id: "sess-1",
      status: "proposed" as const,
      summary: "Stiffen front ARB",
      explanation: "Understeer detected",
      confidence: "high" as const,
      signals_addressed: [] as string[],
      setup_changes: [
        {
          section: "ARB",
          parameter: "FRONT",
          old_value: "3",
          new_value: "5",
          reasoning: "Reason",
          expected_effect: "Effect",
          confidence: "high" as const,
        },
      ],
      driver_feedback: [] as never[],
      created_at: "2026-03-01T12:00:00Z",
    };

    function setupWithRec() {
      setupMocksForSession({
        recommendations: [
          {
            recommendation_id: "rec-1",
            session_id: "sess-1",
            status: "proposed",
            summary: "Stiffen front ARB",
            change_count: 1,
            created_at: "2026-03-01T12:00:00Z",
          },
        ],
      });
      mockedApiGet.mockResolvedValue(recDetail);
    }

    it("renders recommendation cards in the feed", async () => {
      setupWithRec();
      render(<EngineerView />, { wrapper: createWrapper() });
      await waitFor(() => {
        expect(screen.getByText("Stiffen front ARB")).toBeInTheDocument();
      });
    });

    it("clicking Apply on recommendation card opens modal", async () => {
      setupWithRec();
      render(<EngineerView />, { wrapper: createWrapper() });
      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Apply" })).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole("button", { name: "Apply" }));
      expect(screen.getByText("Apply Setup Changes")).toBeInTheDocument();
    });

    it("confirming apply calls POST apply endpoint", async () => {
      setupWithRec();
      mockedApiPost.mockResolvedValue({
        recommendation_id: "rec-1",
        status: "applied",
        backup_path: "/backup/setup.ini.bak",
        changes_applied: 1,
      });

      render(<EngineerView />, { wrapper: createWrapper() });
      await waitFor(() => {
        expect(screen.getByRole("button", { name: "Apply" })).toBeInTheDocument();
      });
      fireEvent.click(screen.getByRole("button", { name: "Apply" }));
      fireEvent.click(
        screen.getByRole("button", { name: "Apply Changes" }),
      );

      await waitFor(() => {
        expect(mockedApiPost).toHaveBeenCalledWith(
          "/sessions/sess-1/recommendations/rec-1/apply",
          { setup_path: "" },
        );
      });
    });
  });

  // US4: Persistent Conversation History
  describe("US4 — Persistent Conversation History", () => {
    it("on mount with existing messages, renders full conversation history", () => {
      setupMocksForSession({
        messages: [
          {
            message_id: "m1",
            role: "user",
            content: "What about Turn 3?",
            created_at: "2026-03-01T12:00:00Z",
          },
          {
            message_id: "m2",
            role: "assistant",
            content: "Turn 3 shows understeer",
            created_at: "2026-03-01T12:01:00Z",
          },
        ],
      });

      render(<EngineerView />, { wrapper: createWrapper() });
      expect(screen.getByText("What about Turn 3?")).toBeInTheDocument();
      expect(
        screen.getByText("Turn 3 shows understeer"),
      ).toBeInTheDocument();
    });

    it("on mount with applied recommendations, shows Applied status", async () => {
      setupMocksForSession({
        sessionState: "engineered",
        recommendations: [
          {
            recommendation_id: "rec-1",
            session_id: "sess-1",
            status: "applied",
            summary: "Already applied rec",
            change_count: 1,
            created_at: "2026-03-01T12:00:00Z",
          },
        ],
      });

      mockedApiGet.mockResolvedValue({
        recommendation_id: "rec-1",
        session_id: "sess-1",
        status: "applied",
        summary: "Already applied rec",
        explanation: "Done",
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
        created_at: "2026-03-01T12:00:00Z",
      });

      render(<EngineerView />, { wrapper: createWrapper() });
      await waitFor(() => {
        const appliedElements = screen.getAllByText("Applied");
        expect(appliedElements.length).toBeGreaterThanOrEqual(1);
      });
    });
  });

  // US5: Progress and Status Indicators
  describe("US5 — Progress and Status Indicators", () => {
    it("re-analysis warning modal appears when conversation exists", () => {
      setupMocksForSession({
        messages: [
          {
            message_id: "m1",
            role: "user",
            content: "Hello",
            created_at: "2026-03-01T12:00:00Z",
          },
        ],
      });

      render(<EngineerView />, { wrapper: createWrapper() });
      fireEvent.click(
        screen.getByRole("button", { name: "Analyze Session" }),
      );
      expect(screen.getByText("Re-analyze session?")).toBeInTheDocument();
    });

    it("re-analysis proceeds after confirmation", async () => {
      setupMocksForSession({
        messages: [
          {
            message_id: "m1",
            role: "user",
            content: "Hello",
            created_at: "2026-03-01T12:00:00Z",
          },
        ],
      });
      mockedApiPost.mockResolvedValue({ job_id: "j1", session_id: "sess-1" });

      render(<EngineerView />, { wrapper: createWrapper() });
      fireEvent.click(
        screen.getByRole("button", { name: "Analyze Session" }),
      );
      fireEvent.click(screen.getByRole("button", { name: "Proceed" }));

      await waitFor(() => {
        expect(mockedApiPost).toHaveBeenCalledWith(
          "/sessions/sess-1/engineer",
        );
      });
    });

    it("re-analysis cancelled does not start job", () => {
      setupMocksForSession({
        messages: [
          {
            message_id: "m1",
            role: "user",
            content: "Hello",
            created_at: "2026-03-01T12:00:00Z",
          },
        ],
      });

      render(<EngineerView />, { wrapper: createWrapper() });
      fireEvent.click(
        screen.getByRole("button", { name: "Analyze Session" }),
      );
      fireEvent.click(screen.getByRole("button", { name: "Cancel" }));

      expect(mockedApiPost).not.toHaveBeenCalled();
    });
  });
});
