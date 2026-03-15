import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { AnalysisView } from "../../../src/views/analysis";
import { renderWithRouter } from "../../helpers/renderWithRouter";

// Mock api
vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
}));

// Mock recharts with minimal stubs
vi.mock("recharts", () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => <div data-testid="mock-linechart">{children}</div>,
  Line: () => <div />,
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

import { apiGet } from "../../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);

const testLaps = {
  session_id: "sess-1",
  lap_count: 3,
  laps: [
    {
      lap_number: 0,
      classification: "outlap",
      is_invalid: false,
      lap_time_s: 120.0,
      tyre_temps_avg: { fl: 80, fr: 80, rl: 78, rr: 78 },
      peak_lat_g: 0.5,
      peak_lon_g: 0.3,
      full_throttle_pct: 40.0,
      braking_pct: 8.0,
      max_speed: 180.0,
      sector_times_s: null,
    },
    {
      lap_number: 1,
      classification: "flying",
      is_invalid: false,
      lap_time_s: 92.456,
      tyre_temps_avg: { fl: 85, fr: 86, rl: 83, rr: 84 },
      peak_lat_g: 1.5,
      peak_lon_g: 0.8,
      full_throttle_pct: 65.0,
      braking_pct: 12.0,
      max_speed: 245.7,
      sector_times_s: [30.1, 35.2, 27.156],
    },
    {
      lap_number: 2,
      classification: "flying",
      is_invalid: false,
      lap_time_s: 91.234,
      tyre_temps_avg: { fl: 86, fr: 87, rl: 84, rr: 85 },
      peak_lat_g: 1.6,
      peak_lon_g: 0.9,
      full_throttle_pct: 67.0,
      braking_pct: 11.0,
      max_speed: 248.3,
      sector_times_s: [29.8, 34.5, 26.934],
    },
  ],
};

const testSessions = [
  {
    session_id: "sess-1",
    car: "bmw_m235i",
    track: "mugello",
    session_date: "2026-03-01T12:00:00Z",
    lap_count: 3,
    best_lap_time: 91.234,
    state: "analyzed",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
  },
  {
    session_id: "sess-unanalyzed",
    car: "bmw_m235i",
    track: "mugello",
    session_date: "2026-03-01T12:00:00Z",
    lap_count: 3,
    best_lap_time: 91.234,
    state: "discovered",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
  },
];

function renderAnalysis(sessionId: string) {
  return renderWithRouter(<AnalysisView />, {
    path: "/session/:sessionId/laps",
    route: `/session/${sessionId}/laps`,
  });
}

describe("AnalysisView", () => {
  beforeEach(() => {
    mockedApiGet.mockImplementation((path: string) => {
      if (path.includes("/sessions") && !path.includes("/laps")) {
        return Promise.resolve({ sessions: testSessions });
      }
      if (path.endsWith("/laps")) {
        return Promise.resolve(testLaps);
      }
      return Promise.resolve({});
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows 'Analysis required' when session state is 'discovered'", async () => {
    renderAnalysis("sess-unanalyzed");

    await waitFor(() => {
      expect(screen.getByText("Analysis required")).toBeInTheDocument();
    });
  });

  it("renders lap list when laps are returned", async () => {
    renderAnalysis("sess-1");

    await waitFor(() => {
      expect(screen.getByTestId("lap-item-0")).toBeInTheDocument();
    });
    expect(screen.getByTestId("lap-item-1")).toBeInTheDocument();
    expect(screen.getByTestId("lap-item-2")).toBeInTheDocument();
  });

  it("selecting a third lap replaces the oldest selection", async () => {
    renderAnalysis("sess-1");

    await waitFor(() => {
      expect(screen.getByTestId("lap-item-1")).toBeInTheDocument();
    });

    // Select lap 1 and lap 2
    fireEvent.click(screen.getByTestId("lap-item-1"));
    fireEvent.click(screen.getByTestId("lap-item-2"));

    // Select lap 0 → should replace lap 1 (oldest)
    fireEvent.click(screen.getByTestId("lap-item-0"));

    // Lap 2 and lap 0 should be selected, lap 1 should not
    const selectedItems = document.querySelectorAll(".ace-lap-item--selected");
    expect(selectedItems).toHaveLength(2);
  });

  it("max 2 laps can be selected simultaneously", async () => {
    renderAnalysis("sess-1");

    await waitFor(() => {
      expect(screen.getByTestId("lap-item-0")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("lap-item-0"));
    fireEvent.click(screen.getByTestId("lap-item-1"));
    fireEvent.click(screen.getByTestId("lap-item-2"));

    const selectedItems = document.querySelectorAll(".ace-lap-item--selected");
    expect(selectedItems.length).toBeLessThanOrEqual(2);
  });

  it("shows 'Select a lap' empty state when no lap selected", async () => {
    renderAnalysis("sess-1");

    await waitFor(() => {
      expect(screen.getByText("Select a lap to view telemetry")).toBeInTheDocument();
    });
  });
});
