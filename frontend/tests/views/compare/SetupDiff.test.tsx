import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { SetupDiff } from "../../../src/views/compare/SetupDiff";
import type { SetupParameterDelta } from "../../../src/lib/types";

const testChanges: SetupParameterDelta[] = [
  { section: "WING", name: "REAR", value_a: 12, value_b: 10 },
  { section: "WING", name: "FRONT", value_a: 5, value_b: 7 },
  { section: "TYRES", name: "PRESSURE_LF", value_a: 26.5, value_b: 27.0 },
  { section: "SUSPENSION", name: "SPRING_RATE_LF", value_a: 80000, value_b: 85000 },
];

describe("SetupDiff", () => {
  it("groups parameters by section", () => {
    render(<SetupDiff changes={testChanges} stintAIndex={0} stintBIndex={1} />);

    expect(screen.getByText("WING")).toBeInTheDocument();
    expect(screen.getByText("TYRES")).toBeInTheDocument();
    expect(screen.getByText("SUSPENSION")).toBeInTheDocument();
  });

  it("shows value_a and value_b for each parameter", () => {
    render(<SetupDiff changes={testChanges} stintAIndex={0} stintBIndex={1} />);

    // WING > REAR: 12 → 10
    expect(screen.getByText("REAR")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
  });

  it("shows directional arrow for numeric deltas", () => {
    const { container } = render(
      <SetupDiff changes={testChanges} stintAIndex={0} stintBIndex={1} />,
    );

    const arrows = container.querySelectorAll(".ace-diff-arrow");
    expect(arrows.length).toBeGreaterThan(0);
  });

  it("renders 'No setup changes' when changes array is empty", () => {
    render(<SetupDiff changes={[]} stintAIndex={0} stintBIndex={1} />);

    expect(
      screen.getByText("No setup changes between these stints"),
    ).toBeInTheDocument();
  });

  it("handles mixed numeric and string values", () => {
    const mixedChanges: SetupParameterDelta[] = [
      { section: "CAR", name: "MODEL_CFG", value_a: "default", value_b: "modified" },
    ];
    render(<SetupDiff changes={mixedChanges} stintAIndex={0} stintBIndex={1} />);

    expect(screen.getByText("default")).toBeInTheDocument();
    expect(screen.getByText("modified")).toBeInTheDocument();
  });

  it("shows dash arrow for string changes", () => {
    const stringChanges: SetupParameterDelta[] = [
      { section: "CAR", name: "MODEL_CFG", value_a: "default", value_b: "modified" },
    ];
    const { container } = render(
      <SetupDiff changes={stringChanges} stintAIndex={0} stintBIndex={1} />,
    );

    // 2 arrows: header row (empty) + data row
    const arrows = container.querySelectorAll(".ace-diff-arrow");
    expect(arrows.length).toBe(2);
    // Data row arrow should be right arrow for string changes
    expect(arrows[1]!.textContent).toBe("\u2192");
  });

  it("shows 'Showing changed parameters only' info label", () => {
    render(<SetupDiff changes={testChanges} stintAIndex={0} stintBIndex={1} />);

    expect(
      screen.getByText("Showing changed parameters only"),
    ).toBeInTheDocument();
  });
});
