import { describe, it, expect, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "../../../src/components/ui/Badge";

describe("Badge", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it('variant "info" renders with ace-badge--info class', () => {
    render(<Badge variant="info">Info</Badge>);
    const badge = screen.getByText("Info");
    expect(badge.classList.contains("ace-badge--info")).toBe(true);
  });

  it('variant "success" renders with ace-badge--success class', () => {
    render(<Badge variant="success">Success</Badge>);
    const badge = screen.getByText("Success");
    expect(badge.classList.contains("ace-badge--success")).toBe(true);
  });

  it('variant "warning" renders with ace-badge--warning class', () => {
    render(<Badge variant="warning">Warning</Badge>);
    const badge = screen.getByText("Warning");
    expect(badge.classList.contains("ace-badge--warning")).toBe(true);
  });

  it('variant "error" renders with ace-badge--error class', () => {
    render(<Badge variant="error">Error</Badge>);
    const badge = screen.getByText("Error");
    expect(badge.classList.contains("ace-badge--error")).toBe(true);
  });

  it('variant "neutral" renders with ace-badge--neutral class', () => {
    render(<Badge variant="neutral">Neutral</Badge>);
    const badge = screen.getByText("Neutral");
    expect(badge.classList.contains("ace-badge--neutral")).toBe(true);
  });

  it("text content renders", () => {
    render(<Badge variant="info">Some Text</Badge>);
    expect(screen.getByText("Some Text")).toBeDefined();
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";
    render(<Badge variant="info">Dark</Badge>);
    expect(screen.getByText("Dark")).toBeDefined();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";
    render(<Badge variant="info">Light</Badge>);
    expect(screen.getByText("Light")).toBeDefined();
  });
});
