import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ApplyConfirmModal } from "../../../src/views/engineer/ApplyConfirmModal";
import type { RecommendationDetailResponse } from "../../../src/lib/types";

const testRecommendation: RecommendationDetailResponse = {
  recommendation_id: "rec-1",
  session_id: "sess-1",
  status: "proposed",
  summary: "Increase front ARB",
  explanation: "Understeer in slow corners",
  confidence: "high",
  signals_addressed: ["understeer_entry"],
  setup_changes: [
    {
      section: "ARB",
      parameter: "FRONT",
      old_value: "3",
      new_value: "5",
      reasoning: "Reduce understeer",
      expected_effect: "Better turn-in",
      confidence: "high",
      storage_value_before: 2,
      storage_value_after: 4,
      storage_convention: "index",
    },
    {
      section: "SPRINGS",
      parameter: "FRONT",
      old_value: "80000",
      new_value: "85000",
      reasoning: "Complement ARB",
      expected_effect: "More front grip",
      confidence: "medium",
      storage_value_before: null,
      storage_value_after: null,
      storage_convention: "direct",
    },
  ],
  driver_feedback: [],
  created_at: "2026-03-01T12:00:00Z",
};

describe("ApplyConfirmModal", () => {
  it("renders nothing when open is false", () => {
    const { container } = render(
      <ApplyConfirmModal
        open={false}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    expect(container.innerHTML).toBe("");
  });

  it("renders modal with title when open is true", () => {
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    expect(screen.getByText("Apply Setup Changes")).toBeInTheDocument();
  });

  it("shows table of setup changes", () => {
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    expect(screen.getByText("ARB")).toBeInTheDocument();
    expect(screen.getByText("SPRINGS")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
    expect(screen.getByText("80000")).toBeInTheDocument();
    expect(screen.getByText("85000")).toBeInTheDocument();
  });

  it("shows confirm and cancel buttons", () => {
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Apply Changes" }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Cancel" }),
    ).toBeInTheDocument();
  });

  it("calls onConfirm when confirm clicked", () => {
    const onConfirm = vi.fn();
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={onConfirm}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Apply Changes" }));
    expect(onConfirm).toHaveBeenCalled();
  });

  it("calls onClose when cancel clicked", () => {
    const onClose = vi.fn();
    render(
      <ApplyConfirmModal
        open={true}
        onClose={onClose}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onClose).toHaveBeenCalled();
  });

  it("shows loading text when isApplying is true", () => {
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={true}
      />,
    );
    expect(
      screen.getByRole("button", { name: "Applying..." }),
    ).toBeInTheDocument();
  });

  it("shows Setup File column header", () => {
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    expect(screen.getByText("Setup File")).toBeInTheDocument();
  });

  it("renders index convention as click X → Y", () => {
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    expect(screen.getByText("click 2 → 4")).toBeInTheDocument();
  });

  it("renders direct convention as em dash", () => {
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={testRecommendation}
        isApplying={false}
      />,
    );
    const dashes = screen.getAllByText("—");
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it("renders scaled convention as X → Y", () => {
    const scaledRec: RecommendationDetailResponse = {
      ...testRecommendation,
      setup_changes: [
        {
          section: "CAMBER_LF",
          parameter: "VALUE",
          old_value: "-1.8",
          new_value: "-0.8",
          reasoning: "Reduce camber",
          expected_effect: "Less wear",
          confidence: "high",
          storage_value_before: -18,
          storage_value_after: -8,
          storage_convention: "scaled",
        },
      ],
    };
    render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={scaledRec}
        isApplying={false}
      />,
    );
    expect(screen.getByText("-18 → -8")).toBeInTheDocument();
  });

  it("renders nothing when recommendation is null", () => {
    const { container } = render(
      <ApplyConfirmModal
        open={true}
        onClose={() => {}}
        onConfirm={() => {}}
        recommendation={null}
        isApplying={false}
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});
