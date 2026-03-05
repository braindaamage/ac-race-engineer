import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Button } from "../../../src/components/ui/Button";

describe("Button", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it('renders with variant "primary" class', () => {
    render(<Button>Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.classList.contains("ace-button--primary")).toBe(true);
  });

  it('renders with variant "secondary" class', () => {
    render(<Button variant="secondary">Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.classList.contains("ace-button--secondary")).toBe(true);
  });

  it('renders with variant "ghost" class', () => {
    render(<Button variant="ghost">Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.classList.contains("ace-button--ghost")).toBe(true);
  });

  it('renders with size "sm" class', () => {
    render(<Button size="sm">Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.classList.contains("ace-button--sm")).toBe(true);
  });

  it('renders with size "md" class', () => {
    render(<Button size="md">Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.classList.contains("ace-button--md")).toBe(true);
  });

  it('renders with size "lg" class', () => {
    render(<Button size="lg">Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.classList.contains("ace-button--lg")).toBe(true);
  });

  it("disabled button has ace-button class and disabled attribute", () => {
    render(<Button disabled>Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    expect(btn.classList.contains("ace-button")).toBe(true);
    expect(btn).toBeDisabled();
  });

  it("clicking a disabled button does not fire onClick", () => {
    const handler = vi.fn();
    render(
      <Button disabled onClick={handler}>
        Click
      </Button>,
    );
    const btn = screen.getByRole("button", { name: "Click" });
    fireEvent.click(btn);
    expect(handler).not.toHaveBeenCalled();
  });

  it("click handler fires on click", () => {
    const handler = vi.fn();
    render(<Button onClick={handler}>Click</Button>);
    const btn = screen.getByRole("button", { name: "Click" });
    fireEvent.click(btn);
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";
    render(<Button>Dark</Button>);
    expect(screen.getByRole("button", { name: "Dark" })).toBeDefined();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";
    render(<Button>Light</Button>);
    expect(screen.getByRole("button", { name: "Light" })).toBeDefined();
  });
});
