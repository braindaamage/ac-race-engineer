import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { render } from "@testing-library/react";
import {
  createMemoryRouter,
  RouterProvider,
  Outlet,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { TabBar } from "../../../src/components/layout/TabBar";

vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

function renderTabBarAt(route: string) {
  // Wrap TabBar + Outlet so that route params are available
  const Shell = () => (
    <div>
      <TabBar />
      <Outlet />
    </div>
  );

  const routes = [
    {
      path: "/",
      element: <Shell />,
      children: [
        { path: "garage", element: <div data-testid="garage-page" /> },
        {
          path: "garage/:carId/tracks",
          element: <div data-testid="tracks-page" />,
        },
        {
          path: "garage/:carId/tracks/:trackId/sessions",
          element: <div data-testid="sessions-page" />,
        },
        { path: "settings", element: <div data-testid="settings-page" /> },
        {
          path: "session/:sessionId",
          element: <Outlet />,
          children: [
            { path: "laps", element: <div data-testid="laps-page" /> },
            { path: "setup", element: <div data-testid="setup-page" /> },
            { path: "engineer", element: <div data-testid="engineer-page" /> },
          ],
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

describe("TabBar", () => {
  it("at /garage: shows global nav tabs with Tracks and Sessions disabled", () => {
    renderTabBarAt("/garage");

    expect(screen.getByText("Garage Home")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();

    // Tracks and Sessions should be disabled (rendered as spans, not links)
    const tracksTab = screen.getByText("Tracks");
    expect(tracksTab.tagName).toBe("SPAN");
    expect(tracksTab.className).toContain("ace-tabbar__tab--disabled");

    const sessionsTab = screen.getByText("Sessions");
    expect(sessionsTab.tagName).toBe("SPAN");
    expect(sessionsTab.className).toContain("ace-tabbar__tab--disabled");
  });

  it("at /garage/test-car/tracks: Tracks tab is enabled", () => {
    renderTabBarAt("/garage/test-car/tracks");

    // Use the nav context to find the Tracks tab, not the page content
    const nav = screen.getByLabelText("Navigation tabs");
    const tracksTab = nav.querySelector("a[href*='tracks']") as HTMLElement;
    expect(tracksTab).toBeInTheDocument();
    expect(tracksTab.tagName).toBe("A");
    expect(tracksTab.className).not.toContain("ace-tabbar__tab--disabled");
    expect(tracksTab.textContent).toBe("Tracks");
  });

  it("at /session/test-id/laps: shows work tabs (Lap Analysis, Setup Compare, Engineer)", () => {
    renderTabBarAt("/session/test-id/laps");

    expect(screen.getByText("Lap Analysis")).toBeInTheDocument();
    expect(screen.getByText("Setup Compare")).toBeInTheDocument();
    expect(screen.getByText("Engineer")).toBeInTheDocument();

    // Global tabs should not be present
    expect(screen.queryByText("Garage Home")).not.toBeInTheDocument();
  });

  it("active tab has the active class", () => {
    renderTabBarAt("/session/test-id/laps");

    const lapTab = screen.getByText("Lap Analysis");
    expect(lapTab.className).toContain("ace-tabbar__tab--active");

    const setupTab = screen.getByText("Setup Compare");
    expect(setupTab.className).not.toContain("ace-tabbar__tab--active");
  });
});
