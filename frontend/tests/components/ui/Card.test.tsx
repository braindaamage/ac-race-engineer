import { describe, it, expect, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { Card } from "../../../src/components/ui/Card";

describe("Card", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it("default variant has ace-card class without --ai modifier", () => {
    const { container } = render(<Card>Content</Card>);
    const card = container.firstElementChild as HTMLElement;
    expect(card.classList.contains("ace-card")).toBe(true);
    expect(card.classList.contains("ace-card--ai")).toBe(false);
  });

  it("ai variant has ace-card--ai class", () => {
    const { container } = render(<Card variant="ai">Content</Card>);
    const card = container.firstElementChild as HTMLElement;
    expect(card.classList.contains("ace-card--ai")).toBe(true);
  });

  it("renders title as heading when provided", () => {
    render(<Card title="My Title">Content</Card>);
    const heading = screen.getByRole("heading", { name: "My Title" });
    expect(heading).toBeDefined();
    expect(heading.tagName).toBe("H3");
  });

  it("does not render heading when title is not provided", () => {
    render(<Card>Content</Card>);
    expect(screen.queryByRole("heading")).toBeNull();
  });

  it('padding "sm" applies ace-card--padding-sm class', () => {
    const { container } = render(<Card padding="sm">Content</Card>);
    const card = container.firstElementChild as HTMLElement;
    expect(card.classList.contains("ace-card--padding-sm")).toBe(true);
  });

  it('padding "md" applies ace-card--padding-md class', () => {
    const { container } = render(<Card padding="md">Content</Card>);
    const card = container.firstElementChild as HTMLElement;
    expect(card.classList.contains("ace-card--padding-md")).toBe(true);
  });

  it('padding "lg" applies ace-card--padding-lg class', () => {
    const { container } = render(<Card padding="lg">Content</Card>);
    const card = container.firstElementChild as HTMLElement;
    expect(card.classList.contains("ace-card--padding-lg")).toBe(true);
  });

  it("renders children", () => {
    render(
      <Card>
        <span data-testid="child">Hello</span>
      </Card>,
    );
    expect(screen.getByTestId("child")).toBeDefined();
    expect(screen.getByText("Hello")).toBeDefined();
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";
    const { container } = render(<Card>Dark</Card>);
    expect(container.firstElementChild).toBeDefined();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";
    const { container } = render(<Card>Light</Card>);
    expect(container.firstElementChild).toBeDefined();
  });
});
