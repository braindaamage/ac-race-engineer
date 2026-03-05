import { describe, it, expect, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { DataCell } from "../../../src/components/ui/DataCell";

describe("DataCell", () => {
  afterEach(() => {
    document.documentElement.dataset.theme = "dark";
  });

  it("renders the value text", () => {
    render(<DataCell value="1:32.456" />);
    expect(screen.getByText("1:32.456")).toBeDefined();
  });

  it("has ace-data-cell class on the root element", () => {
    const { container } = render(<DataCell value="42" />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.classList.contains("ace-data-cell")).toBe(true);
  });

  it("positive delta shows ace-data-cell__delta--positive class", () => {
    const { container } = render(<DataCell value="100" delta={0.5} />);
    const deltaEl = container.querySelector(".ace-data-cell__delta--positive");
    expect(deltaEl).not.toBeNull();
    expect(deltaEl!.textContent).toBe("+0.5");
  });

  it("negative delta shows ace-data-cell__delta--negative class", () => {
    const { container } = render(<DataCell value="100" delta={-0.3} />);
    const deltaEl = container.querySelector(".ace-data-cell__delta--negative");
    expect(deltaEl).not.toBeNull();
    expect(deltaEl!.textContent).toBe("-0.3");
  });

  it("zero delta shows ace-data-cell__delta--neutral class", () => {
    const { container } = render(<DataCell value="100" delta={0} />);
    const deltaEl = container.querySelector(".ace-data-cell__delta--neutral");
    expect(deltaEl).not.toBeNull();
  });

  it("no delta renders no delta element", () => {
    const { container } = render(<DataCell value="100" />);
    expect(container.querySelector("[class*='ace-data-cell__delta']")).toBeNull();
  });

  it("unit suffix renders", () => {
    render(<DataCell value="120" unit="km/h" />);
    expect(screen.getByText("km/h")).toBeDefined();
  });

  it("right alignment has ace-data-cell--right class", () => {
    const { container } = render(<DataCell value="50" align="right" />);
    const root = container.firstElementChild as HTMLElement;
    expect(root.classList.contains("ace-data-cell--right")).toBe(true);
  });

  it("renders in dark theme", () => {
    document.documentElement.dataset.theme = "dark";
    render(<DataCell value="77" />);
    expect(screen.getByText("77")).toBeDefined();
  });

  it("renders in light theme", () => {
    document.documentElement.dataset.theme = "light";
    render(<DataCell value="77" />);
    expect(screen.getByText("77")).toBeDefined();
  });
});
