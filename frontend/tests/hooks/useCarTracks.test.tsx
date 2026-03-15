import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useCarTracks } from "../../src/hooks/useCarTracks";
import type { ReactNode } from "react";

vi.mock("../../src/lib/api", () => ({
  apiGet: vi.fn(),
}));

import { apiGet } from "../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);

const testResponse = {
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
  ],
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useCarTracks", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns tracks data for a car", async () => {
    mockedApiGet.mockResolvedValue(testResponse);

    const { result } = renderHook(() => useCarTracks("ks_ferrari_488_gt3"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data!.car_name).toBe("ks_ferrari_488_gt3");
    expect(result.current.data!.tracks).toHaveLength(1);
    expect(result.current.isLoading).toBe(false);
  });

  it("is disabled when carId is empty", () => {
    const { result } = renderHook(() => useCarTracks(undefined), {
      wrapper: createWrapper(),
    });

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
    expect(mockedApiGet).not.toHaveBeenCalled();
  });

  it("returns loading state", () => {
    mockedApiGet.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useCarTracks("some_car"), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();
  });
});
