import { describe, it, expect, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { ProgressBar } from "../../../src/components/ui/ProgressBar";

describe("ProgressBar", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it("value 0 sets width to 0%", () => {
    const { container } = render(<ProgressBar value={0} />);
    const fill = container.querySelector("[class*='ace-progress__fill']") as HTMLElement;
    expect(fill.style.width).toBe("0%");
  });

  it("value 50 sets width to 50%", () => {
    const { container } = render(<ProgressBar value={50} />);
    const fill = container.querySelector("[class*='ace-progress__fill']") as HTMLElement;
    expect(fill.style.width).toBe("50%");
  });

  it("value 100 sets width to 100%", () => {
    const { container } = render(<ProgressBar value={100} />);
    const fill = container.querySelector("[class*='ace-progress__fill']") as HTMLElement;
    expect(fill.style.width).toBe("100%");
  });

  it("default variant has ace-progress class", () => {
    const { container } = render(<ProgressBar value={50} />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.classList.contains("ace-progress")).toBe(true);
  });

  it("default variant fill has ace-progress__fill--default class", () => {
    const { container } = render(<ProgressBar value={50} />);
    const fill = container.querySelector(".ace-progress__fill--default");
    expect(fill).not.toBeNull();
  });

  it("success variant has ace-progress__fill--success class", () => {
    const { container } = render(<ProgressBar value={50} variant="success" />);
    const fill = container.querySelector(".ace-progress__fill--success");
    expect(fill).not.toBeNull();
  });

  it("error variant has ace-progress__fill--error class", () => {
    const { container } = render(<ProgressBar value={50} variant="error" />);
    const fill = container.querySelector(".ace-progress__fill--error");
    expect(fill).not.toBeNull();
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";
    const { container } = render(<ProgressBar value={25} />);
    expect(container.firstElementChild).toBeDefined();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";
    const { container } = render(<ProgressBar value={25} />);
    expect(container.firstElementChild).toBeDefined();
  });
});
