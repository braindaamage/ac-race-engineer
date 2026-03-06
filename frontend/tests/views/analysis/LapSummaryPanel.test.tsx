import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { LapSummaryPanel } from "../../../src/views/analysis/LapSummaryPanel";
import type { LapDetailResponse, LapSummary } from "../../../src/lib/types";

const makeDetail = (overrides: Partial<LapDetailResponse> = {}): LapDetailResponse => ({
  session_id: "sess-1",
  lap_number: 1,
  classification: "flying",
  is_invalid: false,
  metrics: {
    timing: { lap_time_s: 92.456, sector_times_s: [30.1, 35.2, 27.156] },
    speed: { max_speed: 245.7, min_speed: 60.0, avg_speed: 150.0 },
    driver_inputs: {
      full_throttle_pct: 65.0,
      partial_throttle_pct: 15.0,
      off_throttle_pct: 20.0,
      braking_pct: 12.0,
      avg_steering_angle: 0.05,
      gear_distribution: { 3: 25, 4: 40, 5: 35 },
    },
    tyres: {
      temps_avg: {
        fl: { core: 85, inner: 87, mid: 84, outer: 82 },
        fr: { core: 86, inner: 88, mid: 85, outer: 83 },
        rl: { core: 83, inner: 85, mid: 82, outer: 80 },
        rr: { core: 84, inner: 86, mid: 83, outer: 81 },
      },
      temps_peak: {
        fl: { core: 95, inner: 97, mid: 94, outer: 92 },
        fr: { core: 96, inner: 98, mid: 95, outer: 93 },
        rl: { core: 93, inner: 95, mid: 92, outer: 90 },
        rr: { core: 94, inner: 96, mid: 93, outer: 91 },
      },
      pressure_avg: { fl: 27.5, fr: 27.5, rl: 26.0, rr: 26.0 },
      temp_spread: { fl: 5, fr: 5, rl: 5, rr: 5 },
      front_rear_balance: 0.52,
      wear_rate: null,
    },
    grip: {
      slip_angle_avg: { fl: 0.02, fr: 0.02, rl: 0.03, rr: 0.03 },
      slip_angle_peak: { fl: 0.05, fr: 0.05, rl: 0.06, rr: 0.06 },
      slip_ratio_avg: { fl: 0.01, fr: 0.01, rl: 0.015, rr: 0.015 },
      slip_ratio_peak: { fl: 0.03, fr: 0.03, rl: 0.04, rr: 0.04 },
      peak_lat_g: 1.5,
      peak_lon_g: 0.8,
    },
    fuel: null,
    suspension: {
      travel_avg: { fl: 0.05, fr: 0.05, rl: 0.04, rr: 0.04 },
      travel_peak: { fl: 0.08, fr: 0.08, rl: 0.07, rr: 0.07 },
      travel_range: { fl: 0.03, fr: 0.03, rl: 0.03, rr: 0.03 },
    },
  },
  corners: [],
  ...overrides,
});

const allLaps: LapSummary[] = [
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
];

describe("LapSummaryPanel", () => {
  it("renders timing and speed metrics", () => {
    render(
      <LapSummaryPanel
        primaryDetail={makeDetail()}
        allLaps={allLaps}
      />,
    );

    expect(screen.getByTestId("summary-panel")).toBeInTheDocument();
    expect(screen.getByText("Lap Time")).toBeInTheDocument();
    expect(screen.getByText("Max Speed")).toBeInTheDocument();
    expect(screen.getByText("Avg Speed")).toBeInTheDocument();
    expect(screen.getByText("Full Throttle")).toBeInTheDocument();
    expect(screen.getByText("Braking")).toBeInTheDocument();
  });

  it("shows sector times when available", () => {
    render(
      <LapSummaryPanel
        primaryDetail={makeDetail()}
        allLaps={allLaps}
      />,
    );

    expect(screen.getByTestId("sector-times")).toBeInTheDocument();
    expect(screen.getByText("Sector 1")).toBeInTheDocument();
    expect(screen.getByText("Sector 2")).toBeInTheDocument();
    expect(screen.getByText("Sector 3")).toBeInTheDocument();
  });

  it("omits sector section when sector_times_s is null", () => {
    const detail = makeDetail();
    detail.metrics.timing.sector_times_s = null;

    render(
      <LapSummaryPanel
        primaryDetail={detail}
        allLaps={allLaps}
      />,
    );

    expect(screen.queryByTestId("sector-times")).not.toBeInTheDocument();
  });

  it("highlights best-in-session sectors", () => {
    // Lap 2 has best sectors (29.8, 34.5, 26.934) — use lap 2's data
    const detail = makeDetail({
      lap_number: 2,
      metrics: {
        ...makeDetail().metrics,
        timing: { lap_time_s: 91.234, sector_times_s: [29.8, 34.5, 26.934] },
      },
    });

    render(
      <LapSummaryPanel
        primaryDetail={detail}
        allLaps={allLaps}
      />,
    );

    // Should have "Best" badges for all 3 sectors (since lap 2 has best in all)
    const bestBadges = screen.getAllByText("Best");
    expect(bestBadges.length).toBe(3);
  });

  it("shows delta values when two laps compared", () => {
    const primary = makeDetail({ lap_number: 1 });
    const secondary = makeDetail({
      lap_number: 2,
      metrics: {
        ...makeDetail().metrics,
        timing: { lap_time_s: 91.234, sector_times_s: [29.8, 34.5, 26.934] },
        speed: { max_speed: 248.3, min_speed: 62.0, avg_speed: 155.0 },
      },
    });

    const { container } = render(
      <LapSummaryPanel
        primaryDetail={primary}
        secondaryDetail={secondary}
        allLaps={allLaps}
      />,
    );

    // Delta values should be rendered
    const deltas = container.querySelectorAll("[class*='delta']");
    expect(deltas.length).toBeGreaterThan(0);
  });
});
