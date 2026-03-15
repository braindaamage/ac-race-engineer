import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { SessionLayout } from "../../../src/components/layout/SessionLayout";

vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

describe("SessionLayout", () => {
  it("renders its child route (Outlet)", async () => {
    const routes = [
      {
        path: "/session/:sessionId",
        element: <SessionLayout />,
        children: [
          {
            path: "laps",
            element: <div data-testid="child-route">Child content</div>,
          },
        ],
      },
    ];

    const router = createMemoryRouter(routes, {
      initialEntries: ["/session/test-id/laps"],
    });

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("child-route")).toBeInTheDocument();
    });
    expect(screen.getByTestId("child-route").textContent).toBe(
      "Child content",
    );
  });
});
