import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { LapList } from "../../../src/views/analysis/LapList";
import type { LapSummary } from "../../../src/lib/types";

const makeLap = (overrides: Partial<LapSummary> = {}): LapSummary => ({
  lap_number: 1,
  classification: "flying",
  is_invalid: false,
  lap_time_s: 92.456,
  tyre_temps_avg: { fl: 85, fr: 86, rl: 83, rr: 84 },
  peak_lat_g: 1.5,
  peak_lon_g: 0.8,
  full_throttle_pct: 65.3,
  braking_pct: 12.1,
  max_speed: 245.7,
  sector_times_s: null,
  ...overrides,
});

const testLaps: LapSummary[] = [
  makeLap({ lap_number: 0, classification: "outlap", lap_time_s: 120.0, max_speed: 180.0 }),
  makeLap({ lap_number: 1, lap_time_s: 92.456, max_speed: 245.7 }),
  makeLap({ lap_number: 2, lap_time_s: 91.234, max_speed: 248.3 }),
  makeLap({ lap_number: 3, classification: "invalid", is_invalid: true, lap_time_s: 95.0, max_speed: 200.0 }),
];

describe("LapList", () => {
  it("renders all laps with correct metrics", () => {
    render(
      <LapList
        laps={testLaps}
        fastestLapNumber={2}
        selectedLaps={[]}
        onToggleLap={vi.fn()}
      />,
    );

    expect(screen.getByTestId("lap-item-0")).toBeInTheDocument();
    expect(screen.getByTestId("lap-item-1")).toBeInTheDocument();
    expect(screen.getByTestId("lap-item-2")).toBeInTheDocument();
    expect(screen.getByTestId("lap-item-3")).toBeInTheDocument();

    // Check formatted time appears
    expect(screen.getByText("1:32.456")).toBeInTheDocument();
    expect(screen.getByText("1:31.234")).toBeInTheDocument();
  });

  it("fastest lap has success badge", () => {
    render(
      <LapList
        laps={testLaps}
        fastestLapNumber={2}
        selectedLaps={[]}
        onToggleLap={vi.fn()}
      />,
    );

    expect(screen.getByText("Fastest")).toBeInTheDocument();
  });

  it("invalid laps show classification badge and reduced emphasis", () => {
    const { container } = render(
      <LapList
        laps={testLaps}
        fastestLapNumber={2}
        selectedLaps={[]}
        onToggleLap={vi.fn()}
      />,
    );

    // Invalid lap has warning badge
    expect(screen.getByText("invalid")).toBeInTheDocument();

    // Invalid lap has reduced opacity class
    const invalidItem = container.querySelector(".ace-lap-item--invalid");
    expect(invalidItem).toBeInTheDocument();
  });

  it("clicking a lap calls onToggleLap", () => {
    const onToggle = vi.fn();
    render(
      <LapList
        laps={testLaps}
        fastestLapNumber={2}
        selectedLaps={[]}
        onToggleLap={onToggle}
      />,
    );

    fireEvent.click(screen.getByTestId("lap-item-1"));
    expect(onToggle).toHaveBeenCalledWith(1);
  });

  it("selected laps have visual selected state", () => {
    const { container } = render(
      <LapList
        laps={testLaps}
        fastestLapNumber={2}
        selectedLaps={[1]}
        onToggleLap={vi.fn()}
      />,
    );

    const selectedItems = container.querySelectorAll(".ace-lap-item--selected");
    expect(selectedItems).toHaveLength(1);
  });
});
