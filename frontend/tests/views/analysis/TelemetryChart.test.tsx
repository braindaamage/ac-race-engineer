import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock recharts
vi.mock("recharts", () => ({
  LineChart: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="mock-linechart">{children}</div>
  ),
  Line: (props: { dataKey: string; strokeDasharray?: string }) => (
    <div
      data-testid={`line-${props.dataKey}`}
      data-dash={props.strokeDasharray ?? ""}
    />
  ),
  XAxis: () => <div />,
  YAxis: () => <div />,
  Tooltip: () => <div />,
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

import { TelemetryChart } from "../../../src/views/analysis/TelemetryChart";
import type { LapTelemetryResponse } from "../../../src/lib/types";

const makeTelemetry = (lapNumber: number): LapTelemetryResponse => ({
  session_id: "sess-1",
  lap_number: lapNumber,
  sample_count: 5,
  channels: {
    normalized_position: [0, 0.25, 0.5, 0.75, 1.0],
    throttle: [0.8, 0.9, 1.0, 0.7, 0.6],
    brake: [0.0, 0.0, 0.0, 0.3, 0.5],
    steering: [0.1, 0.0, -0.1, -0.2, 0.0],
    speed_kmh: [200, 220, 240, 210, 190],
    gear: [4, 5, 5, 4, 3],
  },
});

describe("TelemetryChart", () => {
  it("renders 5 chart containers (one per channel)", () => {
    render(
      <TelemetryChart
        primaryTelemetry={makeTelemetry(1)}
        primaryLapNumber={1}
        isLoading={false}
      />,
    );

    expect(screen.getByTestId("chart-throttle")).toBeInTheDocument();
    expect(screen.getByTestId("chart-brake")).toBeInTheDocument();
    expect(screen.getByTestId("chart-steering")).toBeInTheDocument();
    expect(screen.getByTestId("chart-speed_kmh")).toBeInTheDocument();
    expect(screen.getByTestId("chart-gear")).toBeInTheDocument();
  });

  it("shows loading skeleton when data is pending", () => {
    render(
      <TelemetryChart
        primaryTelemetry={undefined}
        primaryLapNumber={1}
        isLoading={true}
      />,
    );

    expect(screen.getByTestId("telemetry-loading")).toBeInTheDocument();
  });

  it("shows channel labels", () => {
    render(
      <TelemetryChart
        primaryTelemetry={makeTelemetry(1)}
        primaryLapNumber={1}
        isLoading={false}
      />,
    );

    expect(screen.getByText("Throttle")).toBeInTheDocument();
    expect(screen.getByText("Brake")).toBeInTheDocument();
    expect(screen.getByText("Steering")).toBeInTheDocument();
    expect(screen.getByText("Speed")).toBeInTheDocument();
    expect(screen.getByText("Gear")).toBeInTheDocument();
  });

  it("renders with mock telemetry data without errors", () => {
    const { container } = render(
      <TelemetryChart
        primaryTelemetry={makeTelemetry(1)}
        primaryLapNumber={1}
        isLoading={false}
      />,
    );

    expect(container.querySelector(".ace-telemetry")).toBeInTheDocument();
    expect(screen.getByTestId("telemetry-charts")).toBeInTheDocument();
  });

  it("renders two Line elements per channel when secondary data is present", () => {
    render(
      <TelemetryChart
        primaryTelemetry={makeTelemetry(1)}
        primaryLapNumber={1}
        secondaryTelemetry={makeTelemetry(2)}
        secondaryLapNumber={2}
        isLoading={false}
      />,
    );

    // Primary lines
    expect(screen.getByTestId("line-throttle")).toBeInTheDocument();
    expect(screen.getByTestId("line-brake")).toBeInTheDocument();

    // Secondary lines (dashed)
    expect(screen.getByTestId("line-throttle_2")).toBeInTheDocument();
    expect(screen.getByTestId("line-brake_2")).toBeInTheDocument();
  });

  it("secondary lines use dashed styling", () => {
    render(
      <TelemetryChart
        primaryTelemetry={makeTelemetry(1)}
        primaryLapNumber={1}
        secondaryTelemetry={makeTelemetry(2)}
        secondaryLapNumber={2}
        isLoading={false}
      />,
    );

    const secondaryLine = screen.getByTestId("line-throttle_2");
    expect(secondaryLine.getAttribute("data-dash")).toBe("5 5");
  });

  it("deselecting second lap returns to single-lap display", () => {
    const { rerender } = render(
      <TelemetryChart
        primaryTelemetry={makeTelemetry(1)}
        primaryLapNumber={1}
        secondaryTelemetry={makeTelemetry(2)}
        secondaryLapNumber={2}
        isLoading={false}
      />,
    );

    expect(screen.getByTestId("line-throttle_2")).toBeInTheDocument();

    rerender(
      <TelemetryChart
        primaryTelemetry={makeTelemetry(1)}
        primaryLapNumber={1}
        isLoading={false}
      />,
    );

    expect(screen.queryByTestId("line-throttle_2")).not.toBeInTheDocument();
  });
});
