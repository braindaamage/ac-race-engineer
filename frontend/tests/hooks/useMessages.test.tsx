import { describe, it, expect, vi, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMessages } from "../../src/hooks/useMessages";
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

describe("useMessages", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("returns undefined when no sessionId", () => {
    const { result } = renderHook(() => useMessages(null), {
      wrapper: createWrapper(),
    });

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });

  it("fetches messages when sessionId is set", async () => {
    const response = {
      session_id: "sess-1",
      messages: [
        {
          message_id: "msg-1",
          role: "user",
          content: "Hello",
          created_at: "2026-03-01T12:00:00Z",
        },
      ],
    };
    mockedApiGet.mockResolvedValue(response);

    const { result } = renderHook(() => useMessages("sess-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data?.session_id).toBe("sess-1");
    expect(result.current.data?.messages).toHaveLength(1);
    expect(result.current.data?.messages[0]!.content).toBe("Hello");
    expect(mockedApiGet).toHaveBeenCalledWith("/sessions/sess-1/messages");
  });

  it("returns MessageListResponse shape", async () => {
    const response = {
      session_id: "sess-2",
      messages: [
        {
          message_id: "msg-1",
          role: "user",
          content: "Test",
          created_at: "2026-03-01T12:00:00Z",
        },
        {
          message_id: "msg-2",
          role: "assistant",
          content: "Response",
          created_at: "2026-03-01T12:01:00Z",
        },
      ],
    };
    mockedApiGet.mockResolvedValue(response);

    const { result } = renderHook(() => useMessages("sess-2"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.data).toBeDefined();
    });

    expect(result.current.data).toHaveProperty("session_id");
    expect(result.current.data).toHaveProperty("messages");
    expect(result.current.data?.messages[0]).toHaveProperty("message_id");
    expect(result.current.data?.messages[0]).toHaveProperty("role");
    expect(result.current.data?.messages[0]).toHaveProperty("content");
    expect(result.current.data?.messages[0]).toHaveProperty("created_at");
  });
});
