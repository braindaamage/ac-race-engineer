import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { Header } from "../../../src/components/layout/Header";
import { renderWithRouter } from "../../helpers/renderWithRouter";

vi.mock("../../../src/assets/logo.png", () => ({
  default: "test-logo.png",
}));

vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

// Mock Breadcrumb to isolate Header tests
vi.mock("../../../src/components/layout/Breadcrumb", () => ({
  Breadcrumb: () => <div data-testid="breadcrumb">Breadcrumb</div>,
}));

describe("Header", () => {
  it("renders logo image with alt text 'AC Race Engineer'", () => {
    renderWithRouter(<Header />);
    const logo = screen.getByAltText("AC Race Engineer");
    expect(logo).toBeInTheDocument();
    expect(logo.tagName).toBe("IMG");
  });

  it("renders Settings link with href /settings", () => {
    renderWithRouter(<Header />);
    const settingsLink = screen.getByLabelText("Settings");
    expect(settingsLink).toBeInTheDocument();
    expect(settingsLink).toHaveAttribute("href", "/settings");
  });

  it("renders brand title text 'AC Race Engineer'", () => {
    renderWithRouter(<Header />);
    expect(screen.getByText("AC Race Engineer")).toBeInTheDocument();
  });
});
