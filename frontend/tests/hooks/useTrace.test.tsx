import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useTrace } from "../../src/hooks/useTrace";
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

describe("useTrace", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("does not fetch when sessionId is null", () => {
    const { result } = renderHook(
      () => useTrace(null, "recommendation", "rec-1"),
      { wrapper: createWrapper() },
    );
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("does not fetch when id is null", () => {
    const { result } = renderHook(
      () => useTrace("sess-1", "recommendation", null),
      { wrapper: createWrapper() },
    );
    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("fetches recommendation trace from correct endpoint", async () => {
    const response = {
      available: true,
      content: "# Trace\nTest content",
      trace_type: "recommendation",
      id: "rec-1",
    };
    mockedApiGet.mockResolvedValue(response);

    const { result } = renderHook(
      () => useTrace("sess-1", "recommendation", "rec-1"),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.available).toBe(true);
    expect(result.current.data?.content).toBe("# Trace\nTest content");
    expect(mockedApiGet).toHaveBeenCalledWith(
      "/sessions/sess-1/recommendations/rec-1/trace",
    );
  });

  it("fetches message trace from correct endpoint", async () => {
    const response = {
      available: false,
      content: null,
      trace_type: "message",
      id: "msg-1",
    };
    mockedApiGet.mockResolvedValue(response);

    const { result } = renderHook(
      () => useTrace("sess-1", "message", "msg-1"),
      { wrapper: createWrapper() },
    );

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.available).toBe(false);
    expect(result.current.data?.content).toBeNull();
    expect(mockedApiGet).toHaveBeenCalledWith(
      "/sessions/sess-1/messages/msg-1/trace",
    );
  });
});
