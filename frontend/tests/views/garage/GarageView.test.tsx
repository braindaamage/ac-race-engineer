import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { GarageView } from "../../../src/views/garage";
import { renderWithRouter } from "../../helpers/renderWithRouter";

const mockCars = [
  {
    car_name: "ks_ferrari_488_gt3",
    display_name: "Ferrari 488 GT3",
    brand: "Ferrari",
    car_class: "GT3",
    badge_url: "/cars/ks_ferrari_488_gt3/badge",
    track_count: 3,
    session_count: 10,
    last_session_date: "2026-03-15T14:30:00",
  },
  {
    car_name: "ks_porsche_911",
    display_name: "Porsche 911 GT3 R",
    brand: "Porsche",
    car_class: "GT3",
    badge_url: null,
    track_count: 1,
    session_count: 2,
    last_session_date: "2026-03-10T09:00:00",
  },
];

vi.mock("../../../src/hooks/useCarStats", () => ({
  useCarStats: vi.fn(() => ({
    cars: mockCars,
    isLoading: false,
    error: null,
    refetch: vi.fn(),
  })),
}));

import { useCarStats } from "../../../src/hooks/useCarStats";

const mockedUseCarStats = vi.mocked(useCarStats);

describe("GarageView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseCarStats.mockReturnValue({
      cars: mockCars,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("renders car cards with correct data", () => {
    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    expect(screen.getByText("Ferrari 488 GT3")).toBeInTheDocument();
    expect(screen.getByText("Porsche 911 GT3 R")).toBeInTheDocument();
    expect(screen.getByText("Ferrari · GT3")).toBeInTheDocument();
  });

  it("shows search input", () => {
    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    expect(screen.getByTestId("garage-search")).toBeInTheDocument();
  });

  it("filters cards by display name", () => {
    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    const search = screen.getByTestId("garage-search");
    fireEvent.change(search, { target: { value: "ferrari" } });

    expect(screen.getByText("Ferrari 488 GT3")).toBeInTheDocument();
    expect(screen.queryByText("Porsche 911 GT3 R")).not.toBeInTheDocument();
  });

  it("filters cards by brand", () => {
    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    const search = screen.getByTestId("garage-search");
    fireEvent.change(search, { target: { value: "porsche" } });

    expect(screen.queryByText("Ferrari 488 GT3")).not.toBeInTheDocument();
    expect(screen.getByText("Porsche 911 GT3 R")).toBeInTheDocument();
  });

  it("shows no-results state when search matches nothing", () => {
    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    const search = screen.getByTestId("garage-search");
    fireEvent.change(search, { target: { value: "nonexistent" } });

    expect(screen.getByText("No cars match your search")).toBeInTheDocument();
  });

  it("shows empty state when no sessions", () => {
    mockedUseCarStats.mockReturnValue({
      cars: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    expect(
      screen.getByText("Your cars with session data will appear here."),
    ).toBeInTheDocument();
  });

  it("shows loading skeleton", () => {
    mockedUseCarStats.mockReturnValue({
      cars: [],
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    expect(screen.getByTestId("garage-view")).toBeInTheDocument();
    // Should not show car cards or empty state while loading
    expect(screen.queryByText("Ferrari 488 GT3")).not.toBeInTheDocument();
    expect(
      screen.queryByText("Your cars with session data will appear here."),
    ).not.toBeInTheDocument();
  });

  it("navigates to tracks on card click", () => {
    const { router } = renderWithRouter(<GarageView />, {
      path: "/garage",
      route: "/garage",
    });

    const card = screen.getByTestId("car-card-ks_ferrari_488_gt3");
    fireEvent.click(card);

    expect(router.state.location.pathname).toBe(
      "/garage/ks_ferrari_488_gt3/tracks",
    );
  });

  it("shows fallback icon when badge_url is null", () => {
    renderWithRouter(<GarageView />, { path: "/garage", route: "/garage" });

    // The porsche card has badge_url: null, so fallback icon should be visible
    const porscheCard = screen.getByTestId("car-card-ks_porsche_911");
    const fallback = porscheCard.querySelector(".ace-car-badge__fallback");
    expect(fallback).toBeInTheDocument();
    expect(fallback?.classList.contains("ace-hidden")).toBe(false);
  });
});
