import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SessionsView } from "../../../src/views/sessions";

// Mock api
vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

// Mock wsManager
vi.mock("../../../src/lib/wsManager", () => ({
  jobWSManager: {
    trackJob: vi.fn(),
    stopTracking: vi.fn(),
  },
}));

// Mock stores
const mockSelectSession = vi.fn();
const mockClearSession = vi.fn();
let mockSelectedSessionId: string | null = null;

vi.mock("../../../src/store/sessionStore", () => ({
  useSessionStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      selectedSessionId: mockSelectedSessionId,
      selectSession: mockSelectSession,
      clearSession: mockClearSession,
    }),
}));

vi.mock("../../../src/store/jobStore", () => ({
  useJobStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ jobProgress: {} }),
}));

const mockAddNotification = vi.fn();
vi.mock("../../../src/store/notificationStore", () => ({
  useNotificationStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ addNotification: mockAddNotification }),
}));

import { apiGet, apiPost, apiDelete } from "../../../src/lib/api";
import { jobWSManager } from "../../../src/lib/wsManager";

const mockedApiGet = vi.mocked(apiGet);
const mockedApiPost = vi.mocked(apiPost);
const mockedApiDelete = vi.mocked(apiDelete);

const testSessions = [
  {
    session_id: "sess-1",
    car: "ks_ferrari_488_gt3",
    track: "spa",
    session_date: "2026-03-01T12:00:00Z",
    lap_count: 5,
    best_lap_time: 120.5,
    state: "discovered",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
  },
  {
    session_id: "sess-2",
    car: "ks_porsche_911_gt3_r",
    track: "monza",
    session_date: "2026-03-02T14:00:00Z",
    lap_count: 10,
    best_lap_time: 105.3,
    state: "analyzed",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
  },
];

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("SessionsView", () => {
  beforeEach(() => {
    mockSelectedSessionId = null;
    mockedApiGet.mockResolvedValue({ sessions: testSessions });
    mockedApiPost.mockResolvedValue({ job_id: "job-1", session_id: "sess-1" });
    mockedApiDelete.mockResolvedValue(undefined);
    mockSelectSession.mockClear();
    mockClearSession.mockClear();
    mockAddNotification.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // --- US1: View All Sessions ---

  it("renders session list from mocked GET /sessions response", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });
    expect(screen.getByText("porsche 911 gt3 r")).toBeInTheDocument();
  });

  it("sessions are sorted by date descending", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    const cards = screen.getAllByText(/laps/);
    // sess-2 (2026-03-02) should come before sess-1 (2026-03-01)
    expect(cards[0]).toHaveTextContent("10 laps");
    expect(cards[1]).toHaveTextContent("5 laps");
  });

  it("shows Skeleton components while loading", () => {
    mockedApiGet.mockReturnValue(new Promise(() => {})); // never resolves
    const { container } = renderWithQuery(<SessionsView />);

    const skeletons = container.querySelectorAll(".ace-skeleton");
    expect(skeletons.length).toBe(3);
  });

  it("shows EmptyState when sessions array is empty", async () => {
    mockedApiGet.mockResolvedValue({ sessions: [] });
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("No sessions recorded yet")).toBeInTheDocument();
    });
  });

  it("shows error EmptyState with retry button when query fails", async () => {
    mockedApiGet.mockRejectedValue(new Error("Network error"));
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("Failed to load sessions")).toBeInTheDocument();
    });
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("Sync button is visible", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("Sync")).toBeInTheDocument();
    });
  });

  // --- US2: Process a Session ---

  it("clicking Process button calls apiPost with /sessions/{id}/process", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Process"));

    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith("/sessions/sess-1/process");
    });
  });

  it("after successful process call, jobWSManager.trackJob is called", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Process"));

    await waitFor(() => {
      expect(jobWSManager.trackJob).toHaveBeenCalledWith("job-1");
    });
  });

  it('Process button is not rendered on "Ready" sessions', async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("porsche 911 gt3 r")).toBeInTheDocument();
    });

    // Only one Process button (for the "new" session)
    const processButtons = screen.getAllByText("Process");
    expect(processButtons).toHaveLength(1);
  });

  // --- US3: Select a Session ---

  it('clicking a "Ready" session card calls selectSession', async () => {
    const { container } = renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("porsche 911 gt3 r")).toBeInTheDocument();
    });

    // Find the card for the ready session (sess-2)
    const cards = container.querySelectorAll(".ace-session-card");
    // sess-2 is first in sorted order (more recent date)
    fireEvent.click(cards[0]!);

    expect(mockSelectSession).toHaveBeenCalledWith("sess-2");
  });

  it('clicking a "New" session card does NOT call selectSession', async () => {
    const { container } = renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    const cards = container.querySelectorAll(".ace-session-card");
    // sess-1 is second (earlier date), state=discovered → uiState=new
    fireEvent.click(cards[1]!);

    expect(mockSelectSession).not.toHaveBeenCalled();
  });

  it("the selected session has isSelected=true", async () => {
    mockSelectedSessionId = "sess-2";
    const { container } = renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("porsche 911 gt3 r")).toBeInTheDocument();
    });

    const selectedCards = container.querySelectorAll(".ace-session-card--selected");
    expect(selectedCards).toHaveLength(1);
  });

  // --- US4: Sync ---

  it("clicking Sync button calls apiPost with /sessions/sync", async () => {
    mockedApiPost.mockResolvedValue({ discovered: 2, already_known: 3, incomplete: 0 });
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("Sync")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Sync"));

    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith("/sessions/sync");
    });
  });

  it("Sync button shows Syncing... while in-flight", async () => {
    let resolveSync: (v: unknown) => void;
    mockedApiPost.mockImplementation(
      (path) => {
        if (typeof path === "string" && path.includes("sync")) {
          return new Promise((resolve) => { resolveSync = resolve; });
        }
        return Promise.resolve({ job_id: "job-1", session_id: "sess-1" });
      },
    );

    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("Sync")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Sync"));

    await waitFor(() => {
      expect(screen.getByText("Syncing...")).toBeInTheDocument();
    });

    resolveSync!({ discovered: 0, already_known: 5, incomplete: 0 });

    await waitFor(() => {
      expect(screen.getByText("Sync")).toBeInTheDocument();
    });
  });

  it("toast notification appears after sync with discovered > 0", async () => {
    mockedApiPost.mockResolvedValue({ discovered: 2, already_known: 3, incomplete: 0 });
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("Sync")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Sync"));

    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith("success", "Found 2 new session(s)");
    });
  });

  it("toast notification appears after sync with discovered === 0", async () => {
    mockedApiPost.mockResolvedValue({ discovered: 0, already_known: 5, incomplete: 0 });
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("Sync")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Sync"));

    await waitFor(() => {
      expect(mockAddNotification).toHaveBeenCalledWith("info", "All sessions up to date");
    });
  });

  // --- US5: Delete ---

  it("clicking delete button opens Modal with confirmation text", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByLabelText("Delete session");
    fireEvent.click(deleteButtons[1]!); // sess-1 is second in sorted order

    await waitFor(() => {
      expect(screen.getByText("Delete Session")).toBeInTheDocument();
    });
  });

  it("clicking confirm in Modal calls apiDelete", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByLabelText("Delete session");
    fireEvent.click(deleteButtons[1]!);

    await waitFor(() => {
      expect(screen.getByText("Delete Session")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Delete"));

    await waitFor(() => {
      expect(mockedApiDelete).toHaveBeenCalledWith("/sessions/sess-1");
    });
  });

  it("clicking cancel in Modal closes it without calling apiDelete", async () => {
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByLabelText("Delete session");
    fireEvent.click(deleteButtons[1]!);

    await waitFor(() => {
      expect(screen.getByText("Delete Session")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Cancel"));

    await waitFor(() => {
      expect(screen.queryByText("Delete Session")).not.toBeInTheDocument();
    });
    expect(mockedApiDelete).not.toHaveBeenCalled();
  });

  it("if deleted session was selectedSessionId, clearSession is called", async () => {
    mockSelectedSessionId = "sess-1";
    renderWithQuery(<SessionsView />);

    await waitFor(() => {
      expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByLabelText("Delete session");
    fireEvent.click(deleteButtons[1]!); // sess-1

    await waitFor(() => {
      expect(screen.getByText("Delete Session")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Delete"));

    await waitFor(() => {
      expect(mockClearSession).toHaveBeenCalled();
    });
  });
});
