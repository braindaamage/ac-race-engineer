import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { CompareView } from "../../../src/views/compare";
import { renderWithRouter } from "../../helpers/renderWithRouter";

// Mock api
vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
}));

import { apiGet } from "../../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);

const testSessions = [
  {
    session_id: "sess-1",
    car: "bmw_m235i",
    track: "mugello",
    session_date: "2026-03-01T12:00:00Z",
    lap_count: 10,
    best_lap_time: 82.0,
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
    lap_count: 5,
    best_lap_time: 85.0,
    state: "discovered",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
  },
];

const testStints = {
  session_id: "sess-1",
  stint_count: 2,
  stints: [
    {
      stint_index: 0,
      setup_filename: "baseline.ini",
      lap_numbers: [1, 2, 3, 4, 5],
      flying_lap_count: 3,
      aggregated: {
        lap_time_mean_s: 82.45,
        lap_time_stddev_s: 0.32,
        tyre_temp_avg: { FL: 91, FR: 92, RL: 88, RR: 89 },
        slip_angle_avg: { FL: 3.2, FR: 3.1, RL: 2.8, RR: 2.9 },
        slip_ratio_avg: { FL: 0.05, FR: 0.05, RL: 0.04, RR: 0.04 },
        peak_lat_g_avg: 1.42,
      },
      trends: null,
    },
    {
      stint_index: 1,
      setup_filename: "softer_front.ini",
      lap_numbers: [6, 7, 8, 9, 10],
      flying_lap_count: 4,
      aggregated: {
        lap_time_mean_s: 81.20,
        lap_time_stddev_s: 0.28,
        tyre_temp_avg: { FL: 89, FR: 90, RL: 87, RR: 88 },
        slip_angle_avg: { FL: 3.0, FR: 2.9, RL: 2.6, RR: 2.7 },
        slip_ratio_avg: { FL: 0.04, FR: 0.04, RL: 0.03, RR: 0.03 },
        peak_lat_g_avg: 1.47,
      },
      trends: null,
    },
  ],
};

const testComparison = {
  session_id: "sess-1",
  comparison: {
    stint_a_index: 0,
    stint_b_index: 1,
    setup_changes: [
      { section: "WING", name: "REAR", value_a: 12, value_b: 10 },
    ],
    metric_deltas: {
      lap_time_delta_s: -0.45,
      tyre_temp_delta: { FL: -1.2, FR: -0.8, RL: -0.5, RR: -0.3 },
      slip_angle_delta: { FL: -0.2, FR: -0.1, RL: 0.0, RR: 0.1 },
      slip_ratio_delta: { FL: 0.0, FR: 0.0, RL: 0.0, RR: 0.0 },
      peak_lat_g_delta: 0.05,
    },
  },
};

const singleStint = {
  session_id: "sess-1",
  stint_count: 1,
  stints: [testStints.stints[0]],
};

function renderCompare(sessionId: string) {
  return renderWithRouter(<CompareView />, {
    path: "/session/:sessionId/setup",
    route: `/session/${sessionId}/setup`,
  });
}

describe("CompareView", () => {
  beforeEach(() => {
    mockedApiGet.mockImplementation((path: string) => {
      if (path.includes("/sessions") && !path.includes("/stints") && !path.includes("/compare")) {
        return Promise.resolve({ sessions: testSessions });
      }
      if (path.endsWith("/stints")) {
        return Promise.resolve(testStints);
      }
      if (path.includes("/compare")) {
        return Promise.resolve(testComparison);
      }
      return Promise.resolve({});
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // --- User Story 1 tests ---

  it("renders stint list when session has 2+ stints", async () => {
    renderCompare("sess-1");

    await waitFor(() => {
      expect(screen.getByText("Stint 1")).toBeInTheDocument();
    });
    expect(screen.getByText("Stint 2")).toBeInTheDocument();
  });

  it("defaults selection to first two stints", async () => {
    const { container } = renderCompare("sess-1");

    await waitFor(() => {
      const selectedItems = container.querySelectorAll(".ace-stint-item--selected");
      expect(selectedItems).toHaveLength(2);
    });
  });

  it("fetches comparison and shows setup diff", async () => {
    renderCompare("sess-1");

    await waitFor(() => {
      expect(screen.getByText("WING")).toBeInTheDocument();
    });
    expect(screen.getByText("REAR")).toBeInTheDocument();
  });

  it("shows metrics panel with comparison data", async () => {
    renderCompare("sess-1");

    await waitFor(() => {
      expect(screen.getByText("-0.450s")).toBeInTheDocument();
    });
  });

  // --- User Story 2 tests ---

  it("shows 'analysis required' when session state is not analyzed", async () => {
    renderCompare("sess-unanalyzed");

    await waitFor(() => {
      expect(screen.getByText("Analysis required")).toBeInTheDocument();
    });
  });

  it("shows 'comparison needs two stints' when session has only 1 stint", async () => {
    mockedApiGet.mockImplementation((path: string) => {
      if (path.includes("/sessions") && !path.includes("/stints") && !path.includes("/compare")) {
        return Promise.resolve({ sessions: testSessions });
      }
      if (path.endsWith("/stints")) {
        return Promise.resolve(singleStint);
      }
      return Promise.resolve({});
    });
    renderCompare("sess-1");

    await waitFor(() => {
      expect(screen.getByText(/requires at least 2 stints/i)).toBeInTheDocument();
    });
  });

  it("shows Skeleton loading state while stints are loading", () => {
    mockedApiGet.mockImplementation(() => new Promise(() => {})); // never resolves
    const { container } = renderCompare("sess-1");

    const skeletons = container.querySelectorAll("[class*='ace-skeleton']");
    expect(skeletons.length).toBeGreaterThan(0);
  });
});
