import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { SessionsView } from "../../../src/views/sessions";
import { renderWithRouter } from "../../helpers/renderWithRouter";

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
vi.mock("../../../src/store/jobStore", () => ({
  useJobStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ jobProgress: {} }),
}));

const mockAddNotification = vi.fn();
vi.mock("../../../src/store/notificationStore", () => ({
  useNotificationStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ addNotification: mockAddNotification }),
}));

// Mock useCarTracks
vi.mock("../../../src/hooks/useCarTracks", () => ({
  useCarTracks: vi.fn(() => ({
    data: undefined,
    isLoading: false,
    error: null,
  })),
}));

import { apiGet, apiPost, apiDelete } from "../../../src/lib/api";
import { jobWSManager } from "../../../src/lib/wsManager";

const mockedApiGet = vi.mocked(apiGet);
const mockedApiPost = vi.mocked(apiPost);
const mockedApiDelete = vi.mocked(apiDelete);

import { useCarTracks } from "../../../src/hooks/useCarTracks";
const mockedUseCarTracks = vi.mocked(useCarTracks);

const testSessions = [
  {
    session_id: "sess-1",
    car: "ks_ferrari_488_gt3",
    track: "spa",
    track_config: "",
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
    car: "ks_ferrari_488_gt3",
    track: "spa",
    track_config: "",
    session_date: "2026-03-02T14:00:00Z",
    lap_count: 10,
    best_lap_time: 105.3,
    state: "analyzed",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
  },
];

function renderSessions() {
  return renderWithRouter(<SessionsView />, {
    path: "/garage/:carId/tracks/:trackId/sessions",
    route: "/garage/ks_ferrari_488_gt3/tracks/spa/sessions",
  });
}

describe("SessionsView", () => {
  beforeEach(() => {
    mockedApiGet.mockResolvedValue({ sessions: testSessions });
    mockedApiPost.mockResolvedValue({ job_id: "job-1", session_id: "sess-1" });
    mockedApiDelete.mockResolvedValue(undefined);
    mockAddNotification.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // --- US1: View All Sessions ---

  it("renders session list from mocked GET /sessions response", async () => {
    renderSessions();

    await waitFor(() => {
      // Both sessions share the same car; verify we see two session cards
      const carNames = screen.getAllByText("ferrari 488 gt3");
      expect(carNames).toHaveLength(2);
    });
  });

  it("sessions are sorted by date descending", async () => {
    renderSessions();

    await waitFor(() => {
      const carNames = screen.getAllByText("ferrari 488 gt3");
      expect(carNames).toHaveLength(2);
    });

    const cards = screen.getAllByText(/laps/);
    // sess-2 (2026-03-02) should come before sess-1 (2026-03-01)
    expect(cards[0]).toHaveTextContent("10 laps");
    expect(cards[1]).toHaveTextContent("5 laps");
  });

  it("shows Skeleton components while loading", () => {
    mockedApiGet.mockReturnValue(new Promise(() => {})); // never resolves
    const { container } = renderSessions();

    const skeletons = container.querySelectorAll(".ace-skeleton");
    expect(skeletons.length).toBe(3);
  });

  it("shows EmptyState when sessions array is empty", async () => {
    mockedApiGet.mockResolvedValue({ sessions: [] });
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("No sessions recorded yet")).toBeInTheDocument();
    });
  });

  it("shows error EmptyState with retry button when query fails", async () => {
    mockedApiGet.mockRejectedValue(new Error("Network error"));
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("Failed to load sessions")).toBeInTheDocument();
    });
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("Sync button is visible", async () => {
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("Sync")).toBeInTheDocument();
    });
  });

  // --- US2: Process a Session ---

  it("clicking Process button calls apiPost with /sessions/{id}/process", async () => {
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("5 laps")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Process"));

    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith("/sessions/sess-1/process");
    });
  });

  it("after successful process call, jobWSManager.trackJob is called", async () => {
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("5 laps")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Process"));

    await waitFor(() => {
      expect(jobWSManager.trackJob).toHaveBeenCalledWith("job-1");
    });
  });

  it('Process button is not rendered on "Ready" sessions', async () => {
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("10 laps")).toBeInTheDocument();
    });

    // Only one Process button (for the "new" session)
    const processButtons = screen.getAllByText("Process");
    expect(processButtons).toHaveLength(1);
  });

  // --- US3: Select a Session ---

  it('clicking a "Ready" session card navigates to session detail', async () => {
    const { router } = renderSessions();

    await waitFor(() => {
      expect(screen.getByText("10 laps")).toBeInTheDocument();
    });

    // Find the card for the ready session (sess-2)
    const cards = document.querySelectorAll(".ace-session-card");
    // sess-2 is first in sorted order (more recent date)
    fireEvent.click(cards[0]!);

    // Should navigate to session detail
    expect(router.state.location.pathname).toBe("/session/sess-2/laps");
  });

  it('clicking a "New" session card does NOT navigate', async () => {
    const { router } = renderSessions();

    await waitFor(() => {
      expect(screen.getByText("5 laps")).toBeInTheDocument();
    });

    const cards = document.querySelectorAll(".ace-session-card");
    // sess-1 is second (earlier date), state=discovered -> uiState=new
    fireEvent.click(cards[1]!);

    // Should stay on the sessions page
    expect(router.state.location.pathname).toBe("/garage/ks_ferrari_488_gt3/tracks/spa/sessions");
  });

  // --- US4: Sync ---

  it("clicking Sync button calls apiPost with /sessions/sync", async () => {
    mockedApiPost.mockResolvedValue({ discovered: 2, already_known: 3, incomplete: 0 });
    renderSessions();

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

    renderSessions();

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
    renderSessions();

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
    renderSessions();

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
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("5 laps")).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByLabelText("Delete session");
    fireEvent.click(deleteButtons[1]!); // sess-1 is second in sorted order

    await waitFor(() => {
      expect(screen.getByText("Delete Session")).toBeInTheDocument();
    });
  });

  it("clicking confirm in Modal calls apiDelete", async () => {
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("5 laps")).toBeInTheDocument();
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
    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("5 laps")).toBeInTheDocument();
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

  // --- Contextual Header ---

  it("shows contextual header when car/track metadata available", async () => {
    mockedUseCarTracks.mockReturnValue({
      data: {
        car_name: "ks_ferrari_488_gt3",
        car_display_name: "Ferrari 488 GT3",
        car_brand: "Ferrari",
        car_class: "GT3",
        badge_url: null,
        track_count: 2,
        session_count: 5,
        last_session_date: "2026-03-15",
        tracks: [
          {
            track_name: "spa",
            track_config: "",
            display_name: "Spa-Francorchamps",
            country: "Belgium",
            length_m: 7004,
            preview_url: null,
            session_count: 3,
            best_lap_time: 105.3,
            last_session_date: "2026-03-15",
          },
        ],
      },
      isLoading: false,
      error: null,
    });

    renderSessions();

    await waitFor(() => {
      expect(screen.getByTestId("sessions-context-header")).toBeInTheDocument();
    });
    expect(screen.getByText("Ferrari 488 GT3")).toBeInTheDocument();
    expect(screen.getByText("Spa-Francorchamps")).toBeInTheDocument();
  });

  it("does not show contextual header without car/track data", async () => {
    mockedUseCarTracks.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: null,
    });

    renderSessions();

    await waitFor(() => {
      expect(screen.getByText("Sessions")).toBeInTheDocument();
    });
    expect(screen.queryByTestId("sessions-context-header")).not.toBeInTheDocument();
  });
});
