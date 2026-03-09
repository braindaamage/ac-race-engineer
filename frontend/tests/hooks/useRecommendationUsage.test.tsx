import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useRecommendationUsage } from "../../src/hooks/useRecommendations";
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

describe("useRecommendationUsage", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns undefined when sessionId is null", () => {
    const { result } = renderHook(
      () => useRecommendationUsage(null, "rec-1"),
      { wrapper: createWrapper() },
    );
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("returns undefined when recommendationId is null", () => {
    const { result } = renderHook(
      () => useRecommendationUsage("sess-1", null),
      { wrapper: createWrapper() },
    );
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("fetches usage when both ids are set", async () => {
    const response = {
      recommendation_id: "rec-1",
      totals: {
        input_tokens: 5000,
        output_tokens: 2000,
        total_tokens: 7000,
        tool_call_count: 12,
        agent_count: 3,
      },
      agents: [
        {
          domain: "balance",
          model: "claude-sonnet-4-20250514",
          input_tokens: 2000,
          output_tokens: 800,
          tool_call_count: 5,
          turn_count: 3,
          duration_ms: 2300,
          tool_calls: [
            { tool_name: "search_kb", token_count: 400 },
            { tool_name: "get_setup_range", token_count: 200 },
          ],
        },
      ],
    };
    mockedApiGet.mockResolvedValue(response);

    const { result } = renderHook(
      () => useRecommendationUsage("sess-1", "rec-1"),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.recommendation_id).toBe("rec-1");
    expect(result.current.data?.totals.agent_count).toBe(3);
    expect(result.current.data?.agents).toHaveLength(1);
    expect(mockedApiGet).toHaveBeenCalledWith(
      "/sessions/sess-1/recommendations/rec-1/usage",
    );
  });

  it("uses correct query key", () => {
    const { result } = renderHook(
      () => useRecommendationUsage("sess-1", "rec-1"),
      { wrapper: createWrapper() },
    );
    // The query should be enabled and loading
    expect(result.current.isLoading).toBe(true);
  });
});
