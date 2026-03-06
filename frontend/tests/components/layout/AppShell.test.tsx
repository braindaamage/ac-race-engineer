import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "../../../src/components/layout/AppShell";

// Mock stores
let mockSelectedSessionId: string | null = null;
const mockClearSession = vi.fn();
const mockSelectSession = vi.fn();

vi.mock("../../../src/store/sessionStore", () => ({
  useSessionStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      selectedSessionId: mockSelectedSessionId,
      selectSession: mockSelectSession,
      clearSession: mockClearSession,
    }),
}));

vi.mock("../../../src/store/uiStore", () => ({
  useUIStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ activeSection: "sessions" }),
}));

// Mock views to simplify rendering
vi.mock("../../../src/views/sessions", () => ({
  SessionsView: () => <div data-testid="sessions-view">Sessions</div>,
}));

vi.mock("../../../src/views/analysis", () => ({
  AnalysisView: () => <div>Analysis</div>,
}));

vi.mock("../../../src/views/compare", () => ({
  CompareView: () => <div>Compare</div>,
}));

vi.mock("../../../src/views/engineer", () => ({
  EngineerView: () => <div>Engineer</div>,
}));

vi.mock("../../../src/views/settings", () => ({
  SettingsView: () => <div>Settings</div>,
}));

// Mock Sidebar and ToastContainer
vi.mock("../../../src/components/layout/Sidebar", () => ({
  Sidebar: () => <nav data-testid="sidebar">Sidebar</nav>,
}));

vi.mock("../../../src/components/layout/ToastContainer", () => ({
  ToastContainer: () => <div data-testid="toast-container" />,
}));

// Mock api
vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

// Mock jobStore
vi.mock("../../../src/store/jobStore", () => ({
  useJobStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ jobProgress: {} }),
}));

// Mock notificationStore
vi.mock("../../../src/store/notificationStore", () => ({
  useNotificationStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ addNotification: vi.fn() }),
}));

// Mock wsManager
vi.mock("../../../src/lib/wsManager", () => ({
  jobWSManager: { trackJob: vi.fn(), stopTracking: vi.fn() },
}));

const testSessions = [
  {
    session_id: "sess-1",
    car: "ks_ferrari_488_gt3",
    track: "spa",
    session_date: "2026-03-01T12:00:00Z",
    lap_count: 5,
    best_lap_time: 120.5,
    state: "analyzed",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
  },
];

function renderWithQuery(
  ui: React.ReactElement,
  queryClient?: QueryClient,
) {
  const qc =
    queryClient ??
    new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
  return { ...render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>), queryClient: qc };
}

describe("AppShell - SelectedSessionStrip", () => {
  beforeEach(() => {
    mockSelectedSessionId = null;
    mockClearSession.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("when selectedSessionId is null, no strip is rendered", () => {
    const { container } = renderWithQuery(<AppShell />);
    expect(container.querySelector(".ace-session-strip")).not.toBeInTheDocument();
  });

  it("when selectedSessionId is set and session exists in cache, strip shows car and track", () => {
    mockSelectedSessionId = "sess-1";
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(["sessions"], { sessions: testSessions });

    const { container } = renderWithQuery(<AppShell />, queryClient);

    const strip = container.querySelector(".ace-session-strip");
    expect(strip).toBeInTheDocument();
    expect(strip!.textContent).toContain("ferrari 488 gt3");
    expect(strip!.textContent).toContain("spa");
  });

  it("clicking close button in strip calls clearSession", () => {
    mockSelectedSessionId = "sess-1";
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(["sessions"], { sessions: testSessions });

    renderWithQuery(<AppShell />, queryClient);

    fireEvent.click(screen.getByLabelText("Clear selection"));
    expect(mockClearSession).toHaveBeenCalledTimes(1);
  });

  it("strip renders between sidebar and content area", () => {
    mockSelectedSessionId = "sess-1";
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    queryClient.setQueryData(["sessions"], { sessions: testSessions });

    const { container } = renderWithQuery(<AppShell />, queryClient);

    const mainDiv = container.querySelector(".ace-app-shell__main");
    expect(mainDiv).toBeInTheDocument();
    const children = Array.from(mainDiv!.children);
    // Strip should come before main content
    expect(children[0]!.className).toContain("ace-session-strip");
    expect(children[1]!.className).toContain("ace-app-shell__content");
  });
});
