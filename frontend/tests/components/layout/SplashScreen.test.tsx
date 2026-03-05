import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { SplashScreen } from "../../../src/components/layout/SplashScreen";

describe("SplashScreen", () => {
  it('shows "AC Race Engineer" text in polling state', () => {
    render(<SplashScreen status="polling" onRetry={() => {}} />);
    expect(screen.getByText("AC Race Engineer")).toBeInTheDocument();
  });

  it('shows "Starting backend..." message in polling state', () => {
    render(<SplashScreen status="polling" onRetry={() => {}} />);
    expect(screen.getByText("Starting backend...")).toBeInTheDocument();
  });

  it("shows spinner element in polling state", () => {
    const { container } = render(
      <SplashScreen status="polling" onRetry={() => {}} />,
    );
    expect(container.querySelector(".ace-splash__spinner")).toBeInTheDocument();
  });

  it('shows "Backend failed to start" message in error state', () => {
    render(<SplashScreen status="error" onRetry={() => {}} />);
    expect(screen.getByText("Backend failed to start")).toBeInTheDocument();
  });

  it('shows "Retry" button in error state', () => {
    render(<SplashScreen status="error" onRetry={() => {}} />);
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("calls onRetry when Retry button is clicked", () => {
    const onRetry = vi.fn();
    render(<SplashScreen status="error" onRetry={onRetry} />);
    fireEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("renders in dark theme", () => {
    const { container } = render(
      <div data-theme="dark">
        <SplashScreen status="polling" onRetry={() => {}} />
      </div>,
    );
    expect(container.querySelector(".ace-splash")).toBeInTheDocument();
  });

  it("renders in light theme", () => {
    const { container } = render(
      <div data-theme="light">
        <SplashScreen status="polling" onRetry={() => {}} />
      </div>,
    );
    expect(container.querySelector(".ace-splash")).toBeInTheDocument();
  });
});
