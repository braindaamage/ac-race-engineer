import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RecommendationCard } from "../../../src/views/engineer/RecommendationCard";
import type { RecommendationDetailResponse } from "../../../src/lib/types";

vi.mock("../../../src/hooks/useTrace", () => ({
  useTrace: () => ({ data: undefined, isLoading: false }),
}));

const baseRecommendation: RecommendationDetailResponse = {
  recommendation_id: "rec-1",
  session_id: "sess-1",
  status: "proposed",
  summary: "Stiffen front anti-roll bar",
  explanation: "Understeer detected in slow corners",
  confidence: "high",
  signals_addressed: ["understeer_entry"],
  setup_changes: [
    {
      section: "ARB",
      parameter: "FRONT",
      old_value: "3",
      new_value: "5",
      reasoning: "Stiffer front ARB reduces understeer",
      expected_effect: "Better turn-in response",
      confidence: "high",
      storage_value_before: null,
      storage_value_after: null,
      storage_convention: null,
    },
    {
      section: "SPRINGS",
      parameter: "FRONT",
      old_value: "80000",
      new_value: "85000",
      reasoning: "Complement ARB change",
      expected_effect: "More front grip",
      confidence: "medium",
      storage_value_before: null,
      storage_value_after: null,
      storage_convention: null,
    },
  ],
  driver_feedback: [
    {
      area: "braking",
      observation: "Late braking into Turn 3",
      suggestion: "Brake 10m earlier for better entry speed",
      corners_affected: [3, 7],
      severity: "medium",
    },
  ],
  created_at: "2026-03-01T12:00:00Z",
};

describe("RecommendationCard", () => {
  it("renders summary text", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    expect(screen.getByText("Stiffen front anti-roll bar")).toBeInTheDocument();
  });

  it("renders setup changes with all fields", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    expect(screen.getByText("[ARB] FRONT")).toBeInTheDocument();
    expect(screen.getByText("[SPRINGS] FRONT")).toBeInTheDocument();
    expect(screen.getByText("Stiffer front ARB reduces understeer")).toBeInTheDocument();
    expect(screen.getByText("Better turn-in response")).toBeInTheDocument();
    expect(screen.getByText("Complement ARB change")).toBeInTheDocument();
    expect(screen.getByText("More front grip")).toBeInTheDocument();
  });

  it("renders old and new values", () => {
    const { container } = render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    const valuesCells = container.querySelectorAll(".ace-setup-change__values");
    expect(valuesCells).toHaveLength(2);
    expect(valuesCells[0]!.textContent).toContain("3");
    expect(valuesCells[0]!.textContent).toContain("5");
  });

  it("renders driver feedback items", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    expect(screen.getByText("braking")).toBeInTheDocument();
    expect(screen.getByText("Late braking into Turn 3")).toBeInTheDocument();
    expect(screen.getByText("Brake 10m earlier for better entry speed")).toBeInTheDocument();
    expect(screen.getByText("Turn 3, Turn 7")).toBeInTheDocument();
  });

  it("shows Apply button enabled for proposed status", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    const applyBtn = screen.getByRole("button", { name: "Apply" });
    expect(applyBtn).not.toBeDisabled();
  });

  it("shows Apply button disabled for applied status", () => {
    const applied = { ...baseRecommendation, status: "applied" as const };
    render(
      <RecommendationCard recommendation={applied} sessionId="sess-1" onApply={() => {}} />,
    );
    const applyBtn = screen.getByRole("button", { name: "Applied" });
    expect(applyBtn).toBeDisabled();
  });

  it("calls onApply with recommendation_id when Apply clicked", () => {
    const onApply = vi.fn();
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={onApply} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(onApply).toHaveBeenCalledWith("rec-1");
  });

  it("shows correct status badge for proposed", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    expect(screen.getByText("Proposed")).toBeInTheDocument();
  });

  it("shows correct status badge for applied", () => {
    const applied = { ...baseRecommendation, status: "applied" as const };
    render(
      <RecommendationCard recommendation={applied} sessionId="sess-1" onApply={() => {}} />,
    );
    const appliedTexts = screen.getAllByText("Applied");
    // Badge + button text
    expect(appliedTexts.length).toBeGreaterThanOrEqual(1);
  });

  it("renders confidence badges for each setup change", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    // Overall confidence + 2 change confidences = at least 2 "high" badges
    const highBadges = screen.getAllByText("high");
    expect(highBadges.length).toBeGreaterThanOrEqual(2);
    // "medium" appears in change confidence and driver feedback severity
    const mediumBadges = screen.getAllByText("medium");
    expect(mediumBadges.length).toBeGreaterThanOrEqual(1);
  });

  // -------------------------------------------------------------------
  // Explanation section tests (Phase 12)
  // -------------------------------------------------------------------

  it("shows explanation toggle collapsed by default when explanation is non-empty", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    const toggle = screen.getByRole("button", { name: "Show details" });
    expect(toggle).toBeInTheDocument();
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    // Explanation text should not be visible
    expect(screen.queryByText("Understeer detected in slow corners")).not.toBeInTheDocument();
  });

  it("expands explanation on click and shows paragraph content", () => {
    const rec = {
      ...baseRecommendation,
      explanation: "First paragraph about understeer.\n\nSecond paragraph about trade-offs.",
    };
    render(
      <RecommendationCard recommendation={rec} sessionId="sess-1" onApply={() => {}} />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Show details" }));
    expect(screen.getByText("First paragraph about understeer.")).toBeInTheDocument();
    expect(screen.getByText("Second paragraph about trade-offs.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Hide details" })).toHaveAttribute("aria-expanded", "true");
  });

  it("hides explanation section when explanation is empty string", () => {
    const rec = { ...baseRecommendation, explanation: "" };
    render(
      <RecommendationCard recommendation={rec} sessionId="sess-1" onApply={() => {}} />,
    );
    expect(screen.queryByRole("button", { name: "Show details" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Hide details" })).not.toBeInTheDocument();
  });

  it("summary remains visible regardless of explanation state", () => {
    render(
      <RecommendationCard recommendation={baseRecommendation} sessionId="sess-1" onApply={() => {}} />,
    );
    // Summary visible before expand
    expect(screen.getByText("Stiffen front anti-roll bar")).toBeInTheDocument();
    // Expand explanation
    fireEvent.click(screen.getByRole("button", { name: "Show details" }));
    // Summary still visible after expand
    expect(screen.getByText("Stiffen front anti-roll bar")).toBeInTheDocument();
  });
});
