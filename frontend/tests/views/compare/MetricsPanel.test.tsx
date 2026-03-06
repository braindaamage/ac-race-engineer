import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MetricsPanel } from "../../../src/views/compare/MetricsPanel";
import type { MetricDeltas } from "../../../src/lib/types";

const testDeltas: MetricDeltas = {
  lap_time_delta_s: -0.45,
  tyre_temp_delta: { FL: -1.2, FR: -0.8, RL: -0.5, RR: -0.3 },
  slip_angle_delta: { FL: -0.2, FR: -0.1, RL: 0.0, RR: 0.1 },
  slip_ratio_delta: { FL: 0.0, FR: 0.0, RL: 0.0, RR: 0.0 },
  peak_lat_g_delta: 0.05,
};

describe("MetricsPanel", () => {
  it("displays lap time delta with sign prefix and unit", () => {
    render(<MetricsPanel deltas={testDeltas} stintAIndex={0} stintBIndex={1} />);

    expect(screen.getByText("-0.450s")).toBeInTheDocument();
  });

  it("displays peak lat G delta", () => {
    render(<MetricsPanel deltas={testDeltas} stintAIndex={0} stintBIndex={1} />);

    expect(screen.getByText("+0.0500")).toBeInTheDocument();
  });

  it("applies green color for improvement (negative lap_time_delta)", () => {
    const { container } = render(
      <MetricsPanel deltas={testDeltas} stintAIndex={0} stintBIndex={1} />,
    );

    const positiveDeltas = container.querySelectorAll(".ace-metrics-delta--positive");
    expect(positiveDeltas.length).toBeGreaterThan(0);
  });

  it("applies red color for degradations", () => {
    const badDeltas: MetricDeltas = {
      ...testDeltas,
      lap_time_delta_s: 0.5,
      peak_lat_g_delta: -0.1,
    };
    const { container } = render(
      <MetricsPanel deltas={badDeltas} stintAIndex={0} stintBIndex={1} />,
    );

    const negativeDeltas = container.querySelectorAll(".ace-metrics-delta--negative");
    expect(negativeDeltas.length).toBeGreaterThan(0);
  });

  it("shows N/A for null values", () => {
    const nullDeltas: MetricDeltas = {
      lap_time_delta_s: null,
      tyre_temp_delta: {},
      slip_angle_delta: {},
      slip_ratio_delta: {},
      peak_lat_g_delta: null,
    };
    render(<MetricsPanel deltas={nullDeltas} stintAIndex={0} stintBIndex={1} />);

    const naElements = screen.getAllByText("N/A");
    expect(naElements.length).toBeGreaterThanOrEqual(2);
  });

  it("renders tyre temp deltas per wheel position", () => {
    render(<MetricsPanel deltas={testDeltas} stintAIndex={0} stintBIndex={1} />);

    // Each wheel label appears 3 times (tyre temp, slip angle, slip ratio)
    expect(screen.getAllByText("FL")).toHaveLength(3);
    expect(screen.getAllByText("FR")).toHaveLength(3);
    expect(screen.getAllByText("RL")).toHaveLength(3);
    expect(screen.getAllByText("RR")).toHaveLength(3);
  });
});
