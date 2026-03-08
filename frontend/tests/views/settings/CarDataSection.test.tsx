import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

const mockUseCars = vi.fn();

vi.mock("../../../src/hooks/useCars", () => ({
  useCars: () => mockUseCars(),
}));

import { CarDataSection } from "../../../src/views/settings/CarDataSection";

const resolvedCar = {
  car_name: "ks_ferrari_488_gt3",
  status: "resolved" as const,
  tier: 2,
  has_defaults: true,
  resolved_at: "2026-03-08T14:30:00+00:00",
};

const unresolvedCar = {
  car_name: "my_mod_car",
  status: "unresolved" as const,
  tier: null,
  has_defaults: null,
  resolved_at: null,
};

describe("CarDataSection", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders car list table with car names and status badges", () => {
    mockUseCars.mockReturnValue({
      cars: [resolvedCar, unresolvedCar],
      isLoading: false,
      error: null,
      invalidateCar: vi.fn(),
      invalidateAll: vi.fn(),
      isInvalidating: false,
    });

    render(<CarDataSection />);

    expect(screen.getByText("ks_ferrari_488_gt3")).toBeDefined();
    expect(screen.getByText("my_mod_car")).toBeDefined();
  });

  it("resolved cars show tier badge", () => {
    mockUseCars.mockReturnValue({
      cars: [resolvedCar],
      isLoading: false,
      error: null,
      invalidateCar: vi.fn(),
      invalidateAll: vi.fn(),
      isInvalidating: false,
    });

    render(<CarDataSection />);

    expect(screen.getByText("Tier 2")).toBeDefined();
  });

  it("unresolved cars show Unresolved status", () => {
    mockUseCars.mockReturnValue({
      cars: [unresolvedCar],
      isLoading: false,
      error: null,
      invalidateCar: vi.fn(),
      invalidateAll: vi.fn(),
      isInvalidating: false,
    });

    render(<CarDataSection />);

    expect(screen.getByText("Unresolved")).toBeDefined();
  });

  it("clicking Invalidate button calls invalidateCar", () => {
    const invalidateCar = vi.fn();
    mockUseCars.mockReturnValue({
      cars: [resolvedCar],
      isLoading: false,
      error: null,
      invalidateCar,
      invalidateAll: vi.fn(),
      isInvalidating: false,
    });

    render(<CarDataSection />);

    fireEvent.click(screen.getByText("Invalidate"));
    expect(invalidateCar).toHaveBeenCalledWith("ks_ferrari_488_gt3");
  });

  it("Invalidate All button calls invalidateAll", () => {
    const invalidateAll = vi.fn();
    mockUseCars.mockReturnValue({
      cars: [resolvedCar],
      isLoading: false,
      error: null,
      invalidateCar: vi.fn(),
      invalidateAll,
      isInvalidating: false,
    });

    render(<CarDataSection />);

    fireEvent.click(screen.getByText("Invalidate All"));
    expect(invalidateAll).toHaveBeenCalled();
  });

  it("empty state when no cars", () => {
    mockUseCars.mockReturnValue({
      cars: [],
      isLoading: false,
      error: null,
      invalidateCar: vi.fn(),
      invalidateAll: vi.fn(),
      isInvalidating: false,
    });

    render(<CarDataSection />);

    expect(screen.getByText(/no cars found/i)).toBeDefined();
  });

  it("loading state shows skeleton", () => {
    mockUseCars.mockReturnValue({
      cars: [],
      isLoading: true,
      error: null,
      invalidateCar: vi.fn(),
      invalidateAll: vi.fn(),
      isInvalidating: false,
    });

    const { container } = render(<CarDataSection />);

    // Skeleton component renders a div with ace-skeleton class
    expect(container.querySelector(".ace-skeleton")).not.toBeNull();
  });

  it("error state shows configuration message", () => {
    mockUseCars.mockReturnValue({
      cars: [],
      isLoading: false,
      error: new Error("API 400"),
      invalidateCar: vi.fn(),
      invalidateAll: vi.fn(),
      isInvalidating: false,
    });

    render(<CarDataSection />);

    expect(screen.getByText(/installation path is not configured/i)).toBeDefined();
  });
});
