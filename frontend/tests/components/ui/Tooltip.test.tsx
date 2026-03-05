import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { Tooltip } from "../../../src/components/ui/Tooltip";

describe("Tooltip", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    document.documentElement.dataset.theme = "dark";
  });

  it("is hidden by default", () => {
    render(
      <Tooltip content="Hint text">
        <button>Hover me</button>
      </Tooltip>,
    );

    expect(screen.queryByText("Hint text")).toBeNull();
  });

  it("shows on hover after delay", () => {
    render(
      <Tooltip content="Hint text">
        <button>Hover me</button>
      </Tooltip>,
    );

    const wrapper = screen.getByText("Hover me").closest(".ace-tooltip-wrapper")!;
    fireEvent.mouseEnter(wrapper);

    // Not visible before delay
    expect(screen.queryByText("Hint text")).toBeNull();

    act(() => {
      vi.advanceTimersByTime(200);
    });

    expect(screen.getByText("Hint text")).toBeTruthy();
  });

  it("hides on mouse leave", () => {
    render(
      <Tooltip content="Hint text">
        <button>Hover me</button>
      </Tooltip>,
    );

    const wrapper = screen.getByText("Hover me").closest(".ace-tooltip-wrapper")!;
    fireEvent.mouseEnter(wrapper);

    act(() => {
      vi.advanceTimersByTime(200);
    });

    expect(screen.getByText("Hint text")).toBeTruthy();

    fireEvent.mouseLeave(wrapper);

    expect(screen.queryByText("Hint text")).toBeNull();
  });

  it.each(["top", "bottom", "left", "right"] as const)(
    "sets correct class for position '%s'",
    (position) => {
      render(
        <Tooltip content="Positioned tip" position={position}>
          <button>Target</button>
        </Tooltip>,
      );

      const wrapper = screen.getByText("Target").closest(".ace-tooltip-wrapper")!;
      fireEvent.mouseEnter(wrapper);

      act(() => {
        vi.advanceTimersByTime(200);
      });

      const tooltip = screen.getByText("Positioned tip");
      expect(tooltip.classList.contains(`ace-tooltip--${position}`)).toBe(true);
    },
  );

  it("renders content in tooltip", () => {
    render(
      <Tooltip content="Custom content here">
        <span>Child</span>
      </Tooltip>,
    );

    const wrapper = screen.getByText("Child").closest(".ace-tooltip-wrapper")!;
    fireEvent.mouseEnter(wrapper);

    act(() => {
      vi.advanceTimersByTime(200);
    });

    expect(screen.getByText("Custom content here")).toBeTruthy();
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";

    render(
      <Tooltip content="Dark tip">
        <span>Child</span>
      </Tooltip>,
    );

    const wrapper = screen.getByText("Child").closest(".ace-tooltip-wrapper")!;
    fireEvent.mouseEnter(wrapper);

    act(() => {
      vi.advanceTimersByTime(200);
    });

    expect(screen.getByText("Dark tip")).toBeTruthy();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";

    render(
      <Tooltip content="Light tip">
        <span>Child</span>
      </Tooltip>,
    );

    const wrapper = screen.getByText("Child").closest(".ace-tooltip-wrapper")!;
    fireEvent.mouseEnter(wrapper);

    act(() => {
      vi.advanceTimersByTime(200);
    });

    expect(screen.getByText("Light tip")).toBeTruthy();
  });
});
