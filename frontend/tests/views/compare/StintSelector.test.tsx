import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { StintSelector } from "../../../src/views/compare/StintSelector";
import type { StintMetrics } from "../../../src/lib/types";

const makeStint = (overrides: Partial<StintMetrics> = {}): StintMetrics => ({
  stint_index: 0,
  setup_filename: "baseline.ini",
  lap_numbers: [1, 2, 3],
  flying_lap_count: 2,
  aggregated: {
    lap_time_mean_s: 82.45,
    lap_time_stddev_s: 0.32,
    tyre_temp_avg: { FL: 91, FR: 92, RL: 88, RR: 89 },
    slip_angle_avg: { FL: 3.2, FR: 3.1, RL: 2.8, RR: 2.9 },
    slip_ratio_avg: { FL: 0.05, FR: 0.05, RL: 0.04, RR: 0.04 },
    peak_lat_g_avg: 1.42,
  },
  trends: null,
  ...overrides,
});

const testStints: StintMetrics[] = [
  makeStint({ stint_index: 0, setup_filename: "baseline.ini", flying_lap_count: 3 }),
  makeStint({ stint_index: 1, setup_filename: "softer_front.ini", flying_lap_count: 4, aggregated: { ...makeStint().aggregated, lap_time_mean_s: 81.20 } }),
  makeStint({ stint_index: 2, setup_filename: null, flying_lap_count: 2, aggregated: { ...makeStint().aggregated, lap_time_mean_s: 83.10 } }),
];

describe("StintSelector", () => {
  it("renders all stints with 1-indexed labels", () => {
    render(
      <StintSelector
        stints={testStints}
        selectedStints={[0, null]}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.getByText("Stint 1")).toBeInTheDocument();
    expect(screen.getByText("Stint 2")).toBeInTheDocument();
    expect(screen.getByText("Stint 3")).toBeInTheDocument();
  });

  it("shows setup filename for each stint", () => {
    render(
      <StintSelector
        stints={testStints}
        selectedStints={[0, null]}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.getByText("baseline.ini")).toBeInTheDocument();
    expect(screen.getByText("softer_front.ini")).toBeInTheDocument();
  });

  it("shows 'No setup' when setup_filename is null", () => {
    render(
      <StintSelector
        stints={testStints}
        selectedStints={[0, null]}
        onSelect={vi.fn()}
      />,
    );

    expect(screen.getByText("No setup")).toBeInTheDocument();
  });

  it("shows flying lap count and avg time", () => {
    render(
      <StintSelector
        stints={testStints}
        selectedStints={[0, null]}
        onSelect={vi.fn()}
      />,
    );

    // flying lap counts
    expect(screen.getByText("3 laps")).toBeInTheDocument();
    expect(screen.getByText("4 laps")).toBeInTheDocument();
    expect(screen.getByText("2 laps")).toBeInTheDocument();
  });

  it("highlights selected stints", () => {
    const { container } = render(
      <StintSelector
        stints={testStints}
        selectedStints={[0, 2]}
        onSelect={vi.fn()}
      />,
    );

    const selectedItems = container.querySelectorAll(".ace-stint-item--selected");
    expect(selectedItems).toHaveLength(2);
  });

  it("calls onSelect when clicking a stint", () => {
    const onSelect = vi.fn();
    render(
      <StintSelector
        stints={testStints}
        selectedStints={[0, null]}
        onSelect={onSelect}
      />,
    );

    fireEvent.click(screen.getByText("Stint 2"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });
});
