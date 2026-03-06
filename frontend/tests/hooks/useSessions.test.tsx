import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useSessions } from "../../src/hooks/useSessions";
import type { ReactNode } from "react";

vi.mock("../../src/lib/api", () => ({
  apiGet: vi.fn(),
}));

import { apiGet } from "../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);

const testSessions = [
  {
    session_id: "sess-1",
    car: "ks_ferrari_488_gt3",
    track: "spa",
    session_date: "2026-03-01T12:00:00Z",
    lap_count: 5,
    best_lap_time: 120.5,
    state: "discovered",
    session_type: "practice",
    csv_path: null,
    meta_path: null,
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

describe("useSessions", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns sessions from mocked apiGet", async () => {
    mockedApiGet.mockResolvedValue({ sessions: testSessions });

    const { result } = renderHook(() => useSessions(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.sessions).toHaveLength(1);
    });

    expect(result.current.sessions[0]!.session_id).toBe("sess-1");
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it("returns empty array when loading", () => {
    mockedApiGet.mockReturnValue(new Promise(() => {}));

    const { result } = renderHook(() => useSessions(), { wrapper: createWrapper() });

    expect(result.current.sessions).toEqual([]);
    expect(result.current.isLoading).toBe(true);
  });

  it("hook is configured with refetchInterval", async () => {
    mockedApiGet.mockResolvedValue({ sessions: testSessions });

    const { result } = renderHook(() => useSessions(), { wrapper: createWrapper() });

    await waitFor(() => {
      expect(result.current.sessions).toHaveLength(1);
    });

    const initialCalls = mockedApiGet.mock.calls.length;

    // Wait for at least one refetch cycle (5s interval + buffer)
    await new Promise((r) => setTimeout(r, 6000));

    expect(mockedApiGet.mock.calls.length).toBeGreaterThan(initialCalls);
  }, 10000);
});
