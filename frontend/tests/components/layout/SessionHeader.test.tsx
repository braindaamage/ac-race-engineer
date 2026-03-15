import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { SessionHeader } from "../../../src/components/layout/SessionHeader";

vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiGet } from "../../../src/lib/api";

const mockSession = {
  session_id: "sess-1",
  car: "ks_ferrari_488_gt3",
  track: "ks_silverstone",
  track_config: "gp",
  session_date: "2026-03-10T14:00:00",
  lap_count: 12,
  best_lap_time: 102.156,
  state: "analyzed",
  session_type: "practice",
  csv_path: null,
  meta_path: null,
};

const mockCarTracks = {
  car_name: "ks_ferrari_488_gt3",
  car_display_name: "Ferrari 488 GT3",
  car_brand: "Ferrari",
  car_class: "GT3",
  badge_url: "/cars/ks_ferrari_488_gt3/badge",
  track_count: 3,
  session_count: 10,
  last_session_date: "2026-03-10T14:00:00",
  tracks: [
    {
      track_name: "ks_silverstone",
      track_config: "gp",
      display_name: "Silverstone Circuit",
      country: "United Kingdom",
      length_m: 5891,
      preview_url: "/tracks/ks_silverstone/preview",
      session_count: 5,
      best_lap_time: 102.156,
      last_session_date: "2026-03-10T14:00:00",
    },
  ],
};

function renderWithProviders(sessionId: string = "sess-1") {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter initialEntries={[`/session/${sessionId}`]}>
        <Routes>
          <Route path="/session/:sessionId" element={<SessionHeader />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("SessionHeader", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders car display name and track display name", async () => {
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions") return Promise.resolve({ sessions: [mockSession] });
      if (url.includes("/tracks"))
        return Promise.resolve(mockCarTracks);
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText("Ferrari 488 GT3")).toBeInTheDocument();
    });
    expect(
      screen.getByText("Silverstone Circuit - gp"),
    ).toBeInTheDocument();
  });

  it("renders session date, lap count, and best lap time", async () => {
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions") return Promise.resolve({ sessions: [mockSession] });
      if (url.includes("/tracks"))
        return Promise.resolve(mockCarTracks);
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText("12")).toBeInTheDocument();
    });
    expect(screen.getByText("1:42.156")).toBeInTheDocument();
  });

  it("renders status badge with correct variant for analyzed state", async () => {
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions") return Promise.resolve({ sessions: [mockSession] });
      if (url.includes("/tracks"))
        return Promise.resolve(mockCarTracks);
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      const badge = screen.getByText("analyzed");
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass("ace-badge--info");
    });
  });

  it("renders status badge with success variant for engineered state", async () => {
    const engineeredSession = { ...mockSession, state: "engineered" };
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions")
        return Promise.resolve({ sessions: [engineeredSession] });
      if (url.includes("/tracks"))
        return Promise.resolve(mockCarTracks);
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      const badge = screen.getByText("engineered");
      expect(badge).toBeInTheDocument();
      expect(badge).toHaveClass("ace-badge--success");
    });
  });

  it('shows "—" for best lap time when null', async () => {
    const noTimeSession = { ...mockSession, best_lap_time: null };
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions")
        return Promise.resolve({ sessions: [noTimeSession] });
      if (url.includes("/tracks"))
        return Promise.resolve(mockCarTracks);
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText("\u2014")).toBeInTheDocument();
    });
  });

  it("shows car placeholder icon when badge image fails to load", async () => {
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions") return Promise.resolve({ sessions: [mockSession] });
      if (url.includes("/tracks"))
        return Promise.resolve(mockCarTracks);
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText("Ferrari 488 GT3")).toBeInTheDocument();
    });

    const carImg = screen.getByAltText("Ferrari 488 GT3");
    fireEvent.error(carImg);

    expect(carImg).toHaveStyle({ display: "none" });
  });

  it("shows track placeholder icon when preview image fails to load", async () => {
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions") return Promise.resolve({ sessions: [mockSession] });
      if (url.includes("/tracks"))
        return Promise.resolve(mockCarTracks);
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      expect(
        screen.getByText("Silverstone Circuit - gp"),
      ).toBeInTheDocument();
    });

    const trackImg = screen.getByAltText("Silverstone Circuit - gp");
    fireEvent.error(trackImg);

    expect(trackImg).toHaveStyle({ display: "none" });
  });

  it("shows raw identifiers when useCarTracks returns no data", async () => {
    vi.mocked(apiGet).mockImplementation((url: string) => {
      if (url === "/sessions") return Promise.resolve({ sessions: [mockSession] });
      if (url.includes("/tracks"))
        return Promise.reject(new Error("not found"));
      return Promise.resolve({});
    });

    renderWithProviders();

    await waitFor(() => {
      expect(screen.getByText("ks_ferrari_488_gt3")).toBeInTheDocument();
    });
    expect(screen.getByText("ks_silverstone - gp")).toBeInTheDocument();
  });
});
