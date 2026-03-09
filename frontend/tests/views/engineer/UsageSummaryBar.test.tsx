import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { UsageSummaryBar } from "../../../src/views/engineer/UsageSummaryBar";
import type { UsageTotals } from "../../../src/lib/types";

const baseTotals: UsageTotals = {
  input_tokens: 5200,
  output_tokens: 1800,
  total_tokens: 7000,
  tool_call_count: 12,
  agent_count: 3,
};

describe("UsageSummaryBar", () => {
  it("renders all totals fields with formatted values", () => {
    render(<UsageSummaryBar totals={baseTotals} onViewDetails={() => {}} />);
    expect(screen.getByText("3")).toBeInTheDocument(); // agent_count
    expect(screen.getByText("5.2K")).toBeInTheDocument(); // input_tokens
    expect(screen.getByText("1.8K")).toBeInTheDocument(); // output_tokens
    expect(screen.getByText("12")).toBeInTheDocument(); // tool_call_count
  });

  it("renders details button", () => {
    render(<UsageSummaryBar totals={baseTotals} onViewDetails={() => {}} />);
    expect(screen.getByRole("button", { name: /details/i })).toBeInTheDocument();
  });

  it("calls onViewDetails when details button is clicked", () => {
    const onViewDetails = vi.fn();
    render(<UsageSummaryBar totals={baseTotals} onViewDetails={onViewDetails} />);
    fireEvent.click(screen.getByRole("button", { name: /details/i }));
    expect(onViewDetails).toHaveBeenCalledOnce();
  });

  it("uses monospace font class on numeric values", () => {
    const { container } = render(
      <UsageSummaryBar totals={baseTotals} onViewDetails={() => {}} />,
    );
    const monoElements = container.querySelectorAll(".ace-mono");
    expect(monoElements.length).toBeGreaterThanOrEqual(4);
  });

  it("handles zero-value totals", () => {
    const zeroTotals: UsageTotals = {
      input_tokens: 0,
      output_tokens: 0,
      total_tokens: 0,
      tool_call_count: 0,
      agent_count: 0,
    };
    render(<UsageSummaryBar totals={zeroTotals} onViewDetails={() => {}} />);
    const zeros = screen.getAllByText("0");
    expect(zeros.length).toBeGreaterThanOrEqual(4);
  });

  it("renders compact formatting for large values", () => {
    const largeTotals: UsageTotals = {
      input_tokens: 1200000,
      output_tokens: 350000,
      total_tokens: 1550000,
      tool_call_count: 45,
      agent_count: 4,
    };
    render(<UsageSummaryBar totals={largeTotals} onViewDetails={() => {}} />);
    expect(screen.getByText("1.2M")).toBeInTheDocument();
    expect(screen.getByText("350.0K")).toBeInTheDocument();
  });
});
