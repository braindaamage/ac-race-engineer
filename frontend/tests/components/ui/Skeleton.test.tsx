import { describe, it, expect, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { Skeleton } from "../../../src/components/ui/Skeleton";

describe("Skeleton", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it("text variant (default) has .ace-skeleton--text", () => {
    const { container } = render(<Skeleton />);
    const el = container.querySelector(".ace-skeleton--text");
    expect(el).toBeTruthy();
  });

  it("circle variant has .ace-skeleton--circle", () => {
    const { container } = render(<Skeleton variant="circle" />);
    const el = container.querySelector(".ace-skeleton--circle");
    expect(el).toBeTruthy();
  });

  it("rect variant has .ace-skeleton--rect", () => {
    const { container } = render(<Skeleton variant="rect" />);
    const el = container.querySelector(".ace-skeleton--rect");
    expect(el).toBeTruthy();
  });

  it("custom width/height applied as inline styles", () => {
    const { container } = render(<Skeleton width="200px" height="40px" />);
    const el = container.querySelector(".ace-skeleton") as HTMLElement;
    expect(el.style.width).toBe("200px");
    expect(el.style.height).toBe("40px");
  });

  it("has shimmer animation class .ace-skeleton", () => {
    const { container } = render(<Skeleton />);
    const el = container.querySelector(".ace-skeleton");
    expect(el).toBeTruthy();
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";
    const { container } = render(<Skeleton />);
    expect(container.querySelector(".ace-skeleton")).toBeTruthy();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";
    const { container } = render(<Skeleton />);
    expect(container.querySelector(".ace-skeleton")).toBeTruthy();
  });
});
