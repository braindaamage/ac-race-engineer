import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  useRecommendations,
  useRecommendationDetail,
} from "../../src/hooks/useRecommendations";
import type { ReactNode } from "react";

vi.mock("../../src/lib/api", () => ({
  apiGet: vi.fn(),
}));

import { apiGet } from "../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useRecommendations", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns undefined when no sessionId", () => {
    const { result } = renderHook(() => useRecommendations(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("fetches recommendations when sessionId is set", async () => {
    const response = {
      session_id: "sess-1",
      recommendations: [
        {
          recommendation_id: "rec-1",
          session_id: "sess-1",
          status: "proposed",
          summary: "Increase front ARB",
          change_count: 2,
          created_at: "2026-03-01T12:00:00Z",
        },
      ],
    };
    mockedApiGet.mockResolvedValue(response);

    const { result } = renderHook(() => useRecommendations("sess-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.session_id).toBe("sess-1");
    expect(result.current.data?.recommendations).toHaveLength(1);
    expect(result.current.data?.recommendations[0]!.summary).toBe(
      "Increase front ARB",
    );
    expect(mockedApiGet).toHaveBeenCalledWith(
      "/sessions/sess-1/recommendations",
    );
  });
});

describe("useRecommendationDetail", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns undefined when no sessionId", () => {
    const { result } = renderHook(
      () => useRecommendationDetail(null, "rec-1"),
      { wrapper: createWrapper() },
    );

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("returns undefined when no recommendationId", () => {
    const { result } = renderHook(
      () => useRecommendationDetail("sess-1", null),
      { wrapper: createWrapper() },
    );

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("fetches detail when both ids are set", async () => {
    const response = {
      recommendation_id: "rec-1",
      session_id: "sess-1",
      status: "proposed",
      summary: "Increase front ARB",
      explanation: "The car understeers in slow corners",
      confidence: "high",
      signals_addressed: ["understeer_entry"],
      setup_changes: [
        {
          section: "ARB",
          parameter: "FRONT",
          old_value: "3",
          new_value: "5",
          reasoning: "Stiffer front ARB reduces understeer",
          expected_effect: "Better turn-in",
          confidence: "high",
        },
      ],
      driver_feedback: [
        {
          area: "braking",
          observation: "Late braking into Turn 3",
          suggestion: "Brake 10m earlier",
          corners_affected: [3],
          severity: "medium",
        },
      ],
      created_at: "2026-03-01T12:00:00Z",
    };
    mockedApiGet.mockResolvedValue(response);

    const { result } = renderHook(
      () => useRecommendationDetail("sess-1", "rec-1"),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.recommendation_id).toBe("rec-1");
    expect(result.current.data?.setup_changes).toHaveLength(1);
    expect(result.current.data?.driver_feedback).toHaveLength(1);
    expect(mockedApiGet).toHaveBeenCalledWith(
      "/sessions/sess-1/recommendations/rec-1",
    );
  });
});
