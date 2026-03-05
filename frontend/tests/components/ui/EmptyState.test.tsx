import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { EmptyState } from "../../../src/components/ui/EmptyState";

describe("EmptyState", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it("icon renders", () => {
    render(
      <EmptyState
        icon={<span data-testid="icon">ICON</span>}
        title="No data"
        description="Nothing here"
      />,
    );

    expect(screen.getByTestId("icon")).toBeTruthy();
  });

  it("title renders", () => {
    render(
      <EmptyState
        icon={<span>ICON</span>}
        title="No sessions found"
        description="Start a session to see data"
      />,
    );

    expect(screen.getByText("No sessions found")).toBeTruthy();
  });

  it("description renders", () => {
    render(
      <EmptyState
        icon={<span>ICON</span>}
        title="Empty"
        description="There is nothing to display"
      />,
    );

    expect(screen.getByText("There is nothing to display")).toBeTruthy();
  });

  it("action button renders when provided", () => {
    const handler = vi.fn();

    render(
      <EmptyState
        icon={<span>ICON</span>}
        title="Empty"
        description="Nothing here"
        action={{ label: "Create new", onClick: handler }}
      />,
    );

    expect(screen.getByText("Create new")).toBeTruthy();
  });

  it("action button click calls handler", () => {
    const handler = vi.fn();

    render(
      <EmptyState
        icon={<span>ICON</span>}
        title="Empty"
        description="Nothing here"
        action={{ label: "Retry", onClick: handler }}
      />,
    );

    fireEvent.click(screen.getByText("Retry"));
    expect(handler).toHaveBeenCalledOnce();
  });

  it("no action button when not provided", () => {
    render(
      <EmptyState
        icon={<span>ICON</span>}
        title="Empty"
        description="Nothing here"
      />,
    );

    const buttons = screen.queryAllByRole("button");
    expect(buttons).toHaveLength(0);
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";

    render(
      <EmptyState
        icon={<span>ICON</span>}
        title="Dark empty"
        description="Dark desc"
      />,
    );

    expect(screen.getByText("Dark empty")).toBeTruthy();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";

    render(
      <EmptyState
        icon={<span>ICON</span>}
        title="Light empty"
        description="Light desc"
      />,
    );

    expect(screen.getByText("Light empty")).toBeTruthy();
  });
});
