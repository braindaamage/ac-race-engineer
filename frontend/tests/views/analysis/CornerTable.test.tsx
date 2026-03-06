import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { CornerTable } from "../../../src/views/analysis/CornerTable";
import type { CornerMetrics } from "../../../src/lib/types";

const makeCorner = (overrides: Partial<CornerMetrics> = {}): CornerMetrics => ({
  corner_number: 1,
  performance: {
    entry_speed_kmh: 185.3,
    apex_speed_kmh: 112.5,
    exit_speed_kmh: 145.7,
    duration_s: 3.2,
  },
  grip: {
    peak_lat_g: 2.1,
    avg_lat_g: 1.8,
    understeer_ratio: null,
  },
  technique: {
    brake_point_norm: 0.12,
    throttle_on_norm: 0.65,
    trail_braking_intensity: 0.4,
  },
  ...overrides,
});

describe("CornerTable", () => {
  it("renders corner rows with correct speeds", () => {
    render(
      <CornerTable
        primaryCorners={[makeCorner(), makeCorner({ corner_number: 2 })]}
        primaryLapNumber={1}
      />,
    );

    expect(screen.getByTestId("corner-table")).toBeInTheDocument();
    // Two data rows
    const rows = screen.getByTestId("corner-table").querySelectorAll("tbody tr");
    expect(rows).toHaveLength(2);

    // Check entry speed is formatted
    expect(screen.getAllByText("185.3 km/h").length).toBeGreaterThanOrEqual(1);
  });

  it("shows understeer badge based on understeer_ratio > 0.05", () => {
    render(
      <CornerTable
        primaryCorners={[
          makeCorner({
            corner_number: 1,
            grip: { peak_lat_g: 2.1, avg_lat_g: 1.8, understeer_ratio: 0.2 },
          }),
        ]}
        primaryLapNumber={1}
      />,
    );

    expect(screen.getByText("Understeer")).toBeInTheDocument();
  });

  it("shows oversteer badge based on understeer_ratio < -0.05", () => {
    render(
      <CornerTable
        primaryCorners={[
          makeCorner({
            corner_number: 1,
            grip: { peak_lat_g: 2.1, avg_lat_g: 1.8, understeer_ratio: -0.2 },
          }),
        ]}
        primaryLapNumber={1}
      />,
    );

    expect(screen.getByText("Oversteer")).toBeInTheDocument();
  });

  it("shows neutral badge when understeer_ratio is near zero", () => {
    render(
      <CornerTable
        primaryCorners={[
          makeCorner({
            corner_number: 1,
            grip: { peak_lat_g: 2.1, avg_lat_g: 1.8, understeer_ratio: 0.01 },
          }),
        ]}
        primaryLapNumber={1}
      />,
    );

    expect(screen.getByText("Neutral")).toBeInTheDocument();
  });

  it("shows delta values when two laps are compared", () => {
    const primary = [
      makeCorner({
        corner_number: 1,
        performance: { entry_speed_kmh: 190.0, apex_speed_kmh: 115.0, exit_speed_kmh: 150.0, duration_s: 3.0 },
      }),
    ];
    const secondary = [
      makeCorner({
        corner_number: 1,
        performance: { entry_speed_kmh: 185.0, apex_speed_kmh: 110.0, exit_speed_kmh: 145.0, duration_s: 3.2 },
      }),
    ];

    const { container } = render(
      <CornerTable
        primaryCorners={primary}
        primaryLapNumber={1}
        secondaryCorners={secondary}
        secondaryLapNumber={2}
      />,
    );

    // Delta should appear (positive = primary faster entry)
    // DataCell renders delta with + sign
    const deltas = container.querySelectorAll("[class*='delta']");
    expect(deltas.length).toBeGreaterThan(0);
  });

  it("handles mismatched corner counts", () => {
    const primary = [makeCorner({ corner_number: 1 })];
    const secondary = [
      makeCorner({ corner_number: 1 }),
      makeCorner({ corner_number: 2 }),
    ];

    render(
      <CornerTable
        primaryCorners={primary}
        primaryLapNumber={1}
        secondaryCorners={secondary}
        secondaryLapNumber={2}
      />,
    );

    // Should show both corners (1 from primary, corner 2 from secondary only)
    const rows = screen.getByTestId("corner-table").querySelectorAll("tbody tr");
    expect(rows).toHaveLength(2);
  });

  it("shows empty state when no corners detected", () => {
    render(
      <CornerTable
        primaryCorners={[]}
        primaryLapNumber={1}
      />,
    );

    expect(screen.getByText("No corners detected")).toBeInTheDocument();
  });
});
