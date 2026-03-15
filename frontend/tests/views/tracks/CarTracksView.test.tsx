import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, fireEvent } from "@testing-library/react";
import { CarTracksView } from "../../../src/views/tracks";
import { renderWithRouter } from "../../helpers/renderWithRouter";

const mockTracksResponse = {
  car_name: "ks_ferrari_488_gt3",
  car_display_name: "Ferrari 488 GT3",
  car_brand: "Ferrari",
  car_class: "GT3",
  badge_url: "/cars/ks_ferrari_488_gt3/badge",
  track_count: 2,
  session_count: 5,
  last_session_date: "2026-03-15T14:30:00",
  tracks: [
    {
      track_name: "ks_monza",
      track_config: "",
      display_name: "Autodromo Nazionale Monza",
      country: "Italy",
      length_m: 5793.0,
      preview_url: "/tracks/ks_monza/preview",
      session_count: 3,
      best_lap_time: 108.5,
      last_session_date: "2026-03-15T14:30:00",
    },
    {
      track_name: "ks_nurburgring",
      track_config: "gp",
      display_name: "Nürburgring",
      country: "Germany",
      length_m: 5137.0,
      preview_url: "/tracks/ks_nurburgring/preview?config=gp",
      session_count: 2,
      best_lap_time: 120.35,
      last_session_date: "2026-03-12T18:00:00",
    },
  ],
};

vi.mock("../../../src/hooks/useCarTracks", () => ({
  useCarTracks: vi.fn(() => ({
    data: mockTracksResponse,
    isLoading: false,
    error: null,
  })),
}));

import { useCarTracks } from "../../../src/hooks/useCarTracks";

const mockedUseCarTracks = vi.mocked(useCarTracks);

function renderView() {
  return renderWithRouter(<CarTracksView />, {
    path: "/garage/:carId/tracks",
    route: "/garage/ks_ferrari_488_gt3/tracks",
  });
}

describe("CarTracksView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedUseCarTracks.mockReturnValue({
      data: mockTracksResponse,
      isLoading: false,
      error: null,
    });
  });

  it("renders car header with correct info", () => {
    renderView();

    expect(screen.getByText("Ferrari 488 GT3")).toBeInTheDocument();
    expect(screen.getByText("Ferrari · GT3")).toBeInTheDocument();
  });

  it("renders track cards with stats", () => {
    renderView();

    expect(screen.getByText("Autodromo Nazionale Monza")).toBeInTheDocument();
    expect(screen.getByText("Italy")).toBeInTheDocument();
    // Lap time: 108.5 -> 1:48.500
    expect(screen.getByText("1:48.500")).toBeInTheDocument();
    // Length: 5793 -> 5.8km
    expect(screen.getByText("5.8km")).toBeInTheDocument();
  });

  it("shows layout suffix for non-empty track_config", () => {
    renderView();

    // Nürburgring with config "gp" should show suffix
    expect(screen.getByText(/Nürburgring - gp/)).toBeInTheDocument();
  });

  it("formats lap time correctly", () => {
    renderView();

    // 120.35s -> 2:00.350
    expect(screen.getByText("2:00.350")).toBeInTheDocument();
  });

  it("navigates to sessions on track card click", () => {
    const { router } = renderView();

    const card = screen.getByTestId("track-card-ks_monza");
    fireEvent.click(card);

    expect(router.state.location.pathname).toBe(
      "/garage/ks_ferrari_488_gt3/tracks/ks_monza/sessions",
    );
  });

  it("includes config query param in navigation for non-empty config", () => {
    const { router } = renderView();

    const card = screen.getByTestId("track-card-ks_nurburgring");
    fireEvent.click(card);

    expect(router.state.location.pathname).toBe(
      "/garage/ks_ferrari_488_gt3/tracks/ks_nurburgring/sessions",
    );
    expect(router.state.location.search).toBe("?config=gp");
  });

  it("shows loading state", () => {
    mockedUseCarTracks.mockReturnValue({
      data: undefined,
      isLoading: true,
      error: null,
    });

    renderView();

    expect(screen.getByTestId("tracks-view")).toBeInTheDocument();
    expect(screen.queryByText("Ferrari 488 GT3")).not.toBeInTheDocument();
  });

  it("shows empty state when no tracks", () => {
    mockedUseCarTracks.mockReturnValue({
      data: { ...mockTracksResponse, tracks: [] },
      isLoading: false,
      error: null,
    });

    renderView();

    expect(screen.getByText("No tracks yet")).toBeInTheDocument();
  });

  it("shows fallback icon when preview_url is null", () => {
    mockedUseCarTracks.mockReturnValue({
      data: {
        ...mockTracksResponse,
        tracks: [
          { ...mockTracksResponse.tracks[0]!, preview_url: null },
        ],
      },
      isLoading: false,
      error: null,
    });

    renderView();

    const card = screen.getByTestId("track-card-ks_monza");
    const fallback = card.querySelector(".ace-track-preview__fallback");
    expect(fallback).toBeInTheDocument();
    expect(fallback?.classList.contains("ace-hidden")).toBe(false);
  });
});
