import { describe, it, expect, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { render } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AppShell } from "../../../src/components/layout/AppShell";

// Mock Header, TabBar, and ToastContainer to simple divs
vi.mock("../../../src/components/layout/Header", () => ({
  Header: () => <div data-testid="header">Header</div>,
}));

vi.mock("../../../src/components/layout/TabBar", () => ({
  TabBar: () => <div data-testid="tabbar">TabBar</div>,
}));

vi.mock("../../../src/components/layout/ToastContainer", () => ({
  ToastContainer: () => <div data-testid="toast-container" />,
}));

vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

function renderAppShell(route = "/test") {
  const routes = [
    {
      path: "/",
      element: <AppShell />,
      children: [
        {
          path: "test",
          element: <div data-testid="child-content">Child content</div>,
        },
      ],
    },
  ];

  const router = createMemoryRouter(routes, {
    initialEntries: [route],
  });

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>,
    ),
    router,
  };
}

describe("AppShell", () => {
  it("renders Header", async () => {
    renderAppShell();
    await waitFor(() => {
      expect(screen.getByTestId("header")).toBeInTheDocument();
    });
  });

  it("renders TabBar", async () => {
    renderAppShell();
    await waitFor(() => {
      expect(screen.getByTestId("tabbar")).toBeInTheDocument();
    });
  });

  it("renders Outlet child content", async () => {
    renderAppShell();
    await waitFor(() => {
      expect(screen.getByTestId("child-content")).toBeInTheDocument();
    });
    expect(screen.getByTestId("child-content").textContent).toBe(
      "Child content",
    );
  });

  it("renders ToastContainer", async () => {
    renderAppShell();
    await waitFor(() => {
      expect(screen.getByTestId("toast-container")).toBeInTheDocument();
    });
  });
});
