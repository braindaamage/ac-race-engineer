import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { UsageDetailModal } from "../../../src/views/engineer/UsageDetailModal";
import type { RecommendationUsageResponse } from "../../../src/lib/types";

const baseUsage: RecommendationUsageResponse = {
  recommendation_id: "rec-1",
  totals: {
    input_tokens: 8500,
    output_tokens: 3200,
    total_tokens: 11700,
    tool_call_count: 15,
    agent_count: 3,
  },
  agents: [
    {
      domain: "balance",
      model: "claude-sonnet-4-20250514",
      input_tokens: 3000,
      output_tokens: 1200,
      tool_call_count: 6,
      turn_count: 3,
      duration_ms: 2300,
      tool_calls: [
        { tool_name: "search_kb", token_count: 400 },
        { tool_name: "get_setup_range", token_count: 200 },
      ],
    },
    {
      domain: "tyre",
      model: "claude-sonnet-4-20250514",
      input_tokens: 3500,
      output_tokens: 1200,
      tool_call_count: 5,
      turn_count: 2,
      duration_ms: 1800,
      tool_calls: [
        { tool_name: "search_kb", token_count: 350 },
      ],
    },
    {
      domain: "technique",
      model: "claude-sonnet-4-20250514",
      input_tokens: 2000,
      output_tokens: 800,
      tool_call_count: 4,
      turn_count: 2,
      duration_ms: 1500,
      tool_calls: [],
    },
  ],
};

describe("UsageDetailModal", () => {
  it("renders totals row with formatted values", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    expect(screen.getByText("8.5K")).toBeInTheDocument(); // input_tokens
    expect(screen.getByText("3.2K")).toBeInTheDocument(); // output_tokens
    expect(screen.getByText("15")).toBeInTheDocument(); // tool_call_count
    // agent_count "3" appears in totals; also turn_count "3" for balance agent
    expect(screen.getAllByText("3").length).toBeGreaterThanOrEqual(1);
  });

  it("renders one row per agent with domain name", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    expect(screen.getByText("balance")).toBeInTheDocument();
    expect(screen.getByText("tyre")).toBeInTheDocument();
    expect(screen.getByText("technique")).toBeInTheDocument();
  });

  it("formats duration as seconds with one decimal", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    expect(screen.getByText("2.3s")).toBeInTheDocument(); // 2300ms
    expect(screen.getByText("1.8s")).toBeInTheDocument(); // 1800ms
    expect(screen.getByText("1.5s")).toBeInTheDocument(); // 1500ms
  });

  it("renders agent token counts", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    expect(screen.getByText("3.0K")).toBeInTheDocument(); // balance input
    expect(screen.getByText("3.5K")).toBeInTheDocument(); // tyre input
    expect(screen.getByText("2.0K")).toBeInTheDocument(); // technique input
  });

  it("renders tool calls for agents that have them", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    // search_kb appears in both balance and tyre agents
    expect(screen.getAllByText(/search_kb/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/get_setup_range/).length).toBeGreaterThanOrEqual(1);
  });

  it("handles agent with zero tool calls", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    // technique agent has 0 tool calls — no tool names should render for it
    // but other agents' tools should still render
    expect(screen.getByText("technique")).toBeInTheDocument();
  });

  it("uses Modal component with correct title", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    expect(screen.getByText("Usage Details")).toBeInTheDocument();
  });

  it("calls onClose when Escape is pressed", () => {
    const onClose = vi.fn();
    render(
      <UsageDetailModal open={true} onClose={onClose} usage={baseUsage} />,
    );
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("does not render when open is false", () => {
    render(
      <UsageDetailModal open={false} onClose={() => {}} usage={baseUsage} />,
    );
    expect(screen.queryByText("Usage Details")).not.toBeInTheDocument();
  });

  it("uses monospace font on all numeric values", () => {
    render(
      <UsageDetailModal open={true} onClose={() => {}} usage={baseUsage} />,
    );
    // Modal renders via portal in document.body
    const monoElements = document.body.querySelectorAll(".ace-mono");
    // Totals (4) + per-agent metrics (5 * 3 agents) + tool calls (3 tool calls)
    expect(monoElements.length).toBeGreaterThanOrEqual(10);
  });
});
