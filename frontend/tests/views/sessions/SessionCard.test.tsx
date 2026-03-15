import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SessionCard } from "../../../src/views/sessions/SessionCard";
import type { SessionRecord } from "../../../src/lib/types";

const baseSession: SessionRecord = {
  session_id: "sess-1",
  car: "ks_ferrari_488_gt3",
  track: "spa",
  track_config: "",
  session_date: "2026-03-01T12:00:00Z",
  lap_count: 5,
  best_lap_time: 120.5,
  state: "discovered",
  session_type: "practice",
  csv_path: null,
  meta_path: null,
};

const noop = () => {};

describe("SessionCard", () => {
  it("renders car name, track name, formatted date, and lap count", () => {
    render(
      <SessionCard
        session={baseSession}
        uiState="new"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    expect(screen.getByText("ferrari 488 gt3")).toBeInTheDocument();
    expect(screen.getByText("spa")).toBeInTheDocument();
    expect(screen.getByText("5 laps")).toBeInTheDocument();
    expect(screen.getByText(new Date("2026-03-01T12:00:00Z").toLocaleDateString())).toBeInTheDocument();
  });

  it('renders Badge with variant "info" and text "New" when uiState="new"', () => {
    render(
      <SessionCard
        session={baseSession}
        uiState="new"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    const badge = screen.getByText("New");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("ace-badge--info");
  });

  it('renders Badge "success"/"Ready" for uiState="ready"', () => {
    render(
      <SessionCard
        session={{ ...baseSession, state: "analyzed" }}
        uiState="ready"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    const badge = screen.getByText("Ready");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("ace-badge--success");
  });

  it('renders Badge "success"/"Engineered" for uiState="engineered"', () => {
    render(
      <SessionCard
        session={{ ...baseSession, state: "engineered" }}
        uiState="engineered"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    const badge = screen.getByText("Engineered");
    expect(badge).toBeInTheDocument();
    expect(badge.className).toContain("ace-badge--success");
  });

  it("adds CSS class ace-session-card--selected when isSelected=true", () => {
    const { container } = render(
      <SessionCard
        session={baseSession}
        uiState="ready"
        isSelected={true}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    expect(container.querySelector(".ace-session-card--selected")).toBeInTheDocument();
  });

  it('calls onSelect when card is clicked and uiState is "ready"', () => {
    const onSelect = vi.fn();
    const { container } = render(
      <SessionCard
        session={baseSession}
        uiState="ready"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={onSelect}
        onDelete={noop}
      />,
    );

    fireEvent.click(container.querySelector(".ace-session-card")!);
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('calls onSelect when card is clicked and uiState is "engineered"', () => {
    const onSelect = vi.fn();
    const { container } = render(
      <SessionCard
        session={baseSession}
        uiState="engineered"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={onSelect}
        onDelete={noop}
      />,
    );

    fireEvent.click(container.querySelector(".ace-session-card")!);
    expect(onSelect).toHaveBeenCalledTimes(1);
  });

  it('does NOT call onSelect when uiState is "new"', () => {
    const onSelect = vi.fn();
    const { container } = render(
      <SessionCard
        session={baseSession}
        uiState="new"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={onSelect}
        onDelete={noop}
      />,
    );

    fireEvent.click(container.querySelector(".ace-session-card")!);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('does NOT call onSelect when uiState is "processing"', () => {
    const onSelect = vi.fn();
    const { container } = render(
      <SessionCard
        session={baseSession}
        uiState="processing"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={onSelect}
        onDelete={noop}
      />,
    );

    fireEvent.click(container.querySelector(".ace-session-card")!);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it('does NOT call onSelect when uiState is "failed"', () => {
    const onSelect = vi.fn();
    const { container } = render(
      <SessionCard
        session={baseSession}
        uiState="failed"
        isSelected={false}
        jobProgress={undefined}
        jobError="some error"
        onProcess={noop}
        onSelect={onSelect}
        onDelete={noop}
      />,
    );

    fireEvent.click(container.querySelector(".ace-session-card")!);
    expect(onSelect).not.toHaveBeenCalled();
  });

  it("calls onDelete when delete button is clicked", () => {
    const onDelete = vi.fn();
    render(
      <SessionCard
        session={baseSession}
        uiState="ready"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={onDelete}
      />,
    );

    fireEvent.click(screen.getByLabelText("Delete session"));
    expect(onDelete).toHaveBeenCalledTimes(1);
  });

  it('shows "Process" button when uiState is "new" that calls onProcess', () => {
    const onProcess = vi.fn();
    render(
      <SessionCard
        session={baseSession}
        uiState="new"
        isSelected={false}
        jobProgress={undefined}
        jobError={null}
        onProcess={onProcess}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    const processBtn = screen.getByText("Process");
    expect(processBtn).toBeInTheDocument();
    fireEvent.click(processBtn);
    expect(onProcess).toHaveBeenCalledTimes(1);
  });

  // T011 - Processing state tests
  it("renders ProgressBar when uiState=processing with jobProgress", () => {
    render(
      <SessionCard
        session={baseSession}
        uiState="processing"
        isSelected={false}
        jobProgress={{
          jobId: "job-1",
          status: "running",
          progress: 50,
          currentStep: "Parsing telemetry",
          result: null,
          error: null,
        }}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "50");
    expect(screen.getByText("Parsing telemetry")).toBeInTheDocument();
  });

  it("renders error message when uiState=failed", () => {
    render(
      <SessionCard
        session={baseSession}
        uiState="failed"
        isSelected={false}
        jobProgress={undefined}
        jobError="CSV file corrupted"
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    expect(screen.getByText("CSV file corrupted")).toBeInTheDocument();
  });

  it('renders "Retry" button when uiState=failed that calls onProcess', () => {
    const onProcess = vi.fn();
    render(
      <SessionCard
        session={baseSession}
        uiState="failed"
        isSelected={false}
        jobProgress={undefined}
        jobError="some error"
        onProcess={onProcess}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    const retryBtn = screen.getByText("Retry");
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);
    expect(onProcess).toHaveBeenCalledTimes(1);
  });

  it('"Process" button is not rendered when uiState=processing', () => {
    render(
      <SessionCard
        session={baseSession}
        uiState="processing"
        isSelected={false}
        jobProgress={{
          jobId: "job-1",
          status: "running",
          progress: 30,
          currentStep: null,
          result: null,
          error: null,
        }}
        jobError={null}
        onProcess={noop}
        onSelect={noop}
        onDelete={noop}
      />,
    );

    expect(screen.queryByText("Process")).not.toBeInTheDocument();
  });
});
