import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useCars } from "../../src/hooks/useCars";
import type { ReactNode } from "react";

vi.mock("../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiDelete: vi.fn(),
}));

import { apiGet, apiDelete } from "../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);
const mockedApiDelete = vi.mocked(apiDelete);

const testCars = [
  {
    car_name: "ks_ferrari_488_gt3",
    status: "resolved" as const,
    tier: 2,
    has_defaults: true,
    resolved_at: "2026-03-08T14:30:00+00:00",
  },
  {
    car_name: "my_mod_car",
    status: "unresolved" as const,
    tier: null,
    has_defaults: null,
    resolved_at: null,
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

describe("useCars", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("fetches car list from /cars endpoint", async () => {
    mockedApiGet.mockResolvedValue({ cars: testCars, total: 2 });

    const { result } = renderHook(() => useCars(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.cars).toHaveLength(2);
    });

    expect(result.current.cars[0]!.car_name).toBe("ks_ferrari_488_gt3");
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it("invalidateCar calls DELETE /cars/{car_name}/cache", async () => {
    mockedApiGet.mockResolvedValue({ cars: testCars, total: 2 });
    mockedApiDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useCars(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.cars).toHaveLength(2);
    });

    await act(async () => {
      result.current.invalidateCar("ks_ferrari_488_gt3");
    });

    await waitFor(() => {
      expect(mockedApiDelete).toHaveBeenCalledWith("/cars/ks_ferrari_488_gt3/cache");
    });
  });

  it("invalidateAll calls DELETE /cars/cache", async () => {
    mockedApiGet.mockResolvedValue({ cars: testCars, total: 2 });
    mockedApiDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useCars(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.cars).toHaveLength(2);
    });

    await act(async () => {
      result.current.invalidateAll();
    });

    await waitFor(() => {
      expect(mockedApiDelete).toHaveBeenCalledWith("/cars/cache");
    });
  });

  it("returns error state when API fails", async () => {
    mockedApiGet.mockRejectedValue(new Error("API 400: path not configured"));

    const { result } = renderHook(() => useCars(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.error).not.toBe(null);
    });

    expect(result.current.cars).toEqual([]);
  });
});
