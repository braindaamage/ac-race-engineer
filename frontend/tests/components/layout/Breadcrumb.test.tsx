import { describe, it, expect, vi } from "vitest";
import { screen } from "@testing-library/react";
import { render } from "@testing-library/react";
import {
  createMemoryRouter,
  RouterProvider,
  Outlet,
} from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Breadcrumb } from "../../../src/components/layout/Breadcrumb";

vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiDelete: vi.fn(),
}));

function renderBreadcrumbAt(route: string) {
  // Build a route tree that matches the app's param structure
  const Layout = () => (
    <div>
      <Breadcrumb />
      <Outlet />
    </div>
  );

  const routes = [
    {
      path: "/",
      element: <Layout />,
      children: [
        { path: "garage", element: <div data-testid="garage-page">Garage</div> },
        {
          path: "garage/:carId/tracks",
          element: <div data-testid="tracks-page">Tracks</div>,
        },
        {
          path: "garage/:carId/tracks/:trackId/sessions",
          element: <div data-testid="sessions-page">Sessions</div>,
        },
        {
          path: "session/:sessionId",
          element: <div data-testid="session-page">Session</div>,
          children: [
            { path: "laps", element: <div>Laps</div> },
          ],
        },
        { path: "settings", element: <div data-testid="settings-page">Settings</div> },
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
    queryClient,
  };
}

describe("Breadcrumb", () => {
  it("at /garage: only home icon segment, marked as current", () => {
    renderBreadcrumbAt("/garage");
    const nav = screen.getByLabelText("Breadcrumb");
    // Should have the home icon as current (span, not link)
    const current = nav.querySelector(".ace-breadcrumb__current");
    expect(current).toBeInTheDocument();
    expect(current!.querySelector(".fa-house")).toBeInTheDocument();
    // No links — only segment is current
    const links = nav.querySelectorAll(".ace-breadcrumb__link");
    expect(links).toHaveLength(0);
  });

  it("at /garage/ks_bmw_m3_e30/tracks: home link + car name segment", () => {
    renderBreadcrumbAt("/garage/ks_bmw_m3_e30/tracks");
    const nav = screen.getByLabelText("Breadcrumb");
    // Home icon should be a link (not current)
    const homeLink = nav.querySelector(".ace-breadcrumb__link");
    expect(homeLink).toBeInTheDocument();
    expect(homeLink!.querySelector(".fa-house")).toBeInTheDocument();
    // Car name should be current — formatCarTrack("ks_bmw_m3_e30") => "bmw m3 e30"
    const current = nav.querySelector(".ace-breadcrumb__current");
    expect(current).toBeInTheDocument();
    expect(current!.textContent).toBe("bmw m3 e30");
  });

  it("at /settings: home link + 'Settings' text as current", () => {
    renderBreadcrumbAt("/settings");
    const nav = screen.getByLabelText("Breadcrumb");
    // Home icon should be a link
    const homeLink = nav.querySelector(".ace-breadcrumb__link");
    expect(homeLink).toBeInTheDocument();
    expect(homeLink!.querySelector(".fa-house")).toBeInTheDocument();
    // "Settings" should be current
    const current = nav.querySelector(".ace-breadcrumb__current");
    expect(current).toBeInTheDocument();
    expect(current!.textContent).toBe("Settings");
  });

  it("breadcrumb home link has correct href for navigation", () => {
    renderBreadcrumbAt("/settings");
    const nav = screen.getByLabelText("Breadcrumb");
    // Home icon is a link at /settings
    const homeLink = nav.querySelector(".ace-breadcrumb__link") as HTMLAnchorElement;
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/garage");
  });

  it("breadcrumb at car tracks route has correct home link href", () => {
    renderBreadcrumbAt("/garage/ks_bmw_m3_e30/tracks");
    const nav = screen.getByLabelText("Breadcrumb");
    const homeLink = nav.querySelector(".ace-breadcrumb__link") as HTMLAnchorElement;
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/garage");
  });
});
