import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useCarStats } from "../../src/hooks/useCarStats";
import type { ReactNode } from "react";

vi.mock("../../src/lib/api", () => ({
  apiGet: vi.fn(),
}));

import { apiGet } from "../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);

const testCars = [
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
];

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useCarStats", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns cars from API", async () => {
    mockedApiGet.mockResolvedValue({ cars: testCars });

    const { result } = renderHook(() => useCarStats(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.cars).toHaveLength(1);
    });

    expect(result.current.cars[0]!.car_name).toBe("ks_ferrari_488_gt3");
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it("returns empty array while loading", () => {
    mockedApiGet.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useCarStats(), { wrapper: createWrapper() });

    expect(result.current.cars).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it("returns error on failure", async () => {
    mockedApiGet.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useCarStats(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
    });

    expect(result.current.error!.message).toBe("Network error");
  });
});
