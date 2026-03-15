import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "../src/App";

// Mock all API calls
vi.mock("../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPatch: vi.fn(),
  apiPost: vi.fn(),
}));

// Mock useBackendStatus
vi.mock("../src/hooks/useBackendStatus", () => ({
  useBackendStatus: vi.fn(),
}));

// Mock useTheme
vi.mock("../src/hooks/useTheme", () => ({
  useTheme: () => ({ theme: "dark", toggleTheme: vi.fn() }),
}));

// Mock the router module to avoid deep rendering of all views
vi.mock("../src/router", async () => {
  const React = await import("react");
  const { createMemoryRouter } = await import("react-router-dom");
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: React.createElement("div", null, "Router loaded"),
        children: [
          { index: true, element: React.createElement("div", null, "Garage placeholder") },
        ],
      },
    ],
    { initialEntries: ["/"] },
  );
  return { router };
});

import { apiGet } from "../src/lib/api";
import { useBackendStatus } from "../src/hooks/useBackendStatus";

const mockedApiGet = vi.mocked(apiGet);
const mockedUseBackendStatus = vi.mocked(useBackendStatus);

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("App", () => {
  beforeEach(() => {
    mockedUseBackendStatus.mockReturnValue({
      status: "ready",
      retry: vi.fn(),
      shutdown: vi.fn().mockResolvedValue(undefined),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows wizard when onboarding_completed is false", async () => {
    mockedApiGet.mockResolvedValue({
      ac_install_path: "",
      setups_path: "",
      llm_provider: "anthropic",
      llm_model: "",
      ui_theme: "dark",
      api_key: "",
      onboarding_completed: false,
    });

    renderWithQuery(<App />);

    await waitFor(() => {
      expect(
        screen.getByText("Where is Assetto Corsa installed?"),
      ).toBeDefined();
    });
  });

  it("shows router content when onboarding_completed is true", async () => {
    mockedApiGet.mockResolvedValue({
      ac_install_path: "C:\\AC",
      setups_path: "C:\\AC\\setups",
      llm_provider: "anthropic",
      llm_model: "",
      ui_theme: "dark",
      api_key: "",
      onboarding_completed: true,
    });

    renderWithQuery(<App />);

    await waitFor(() => {
      expect(screen.getByText("Router loaded")).toBeDefined();
    });
  });

  it("shows splash screen when backend is not ready", () => {
    mockedUseBackendStatus.mockReturnValue({
      status: "polling",
      retry: vi.fn(),
      shutdown: vi.fn().mockResolvedValue(undefined),
    });

    renderWithQuery(<App />);

    // SplashScreen should be shown — look for its content
    expect(screen.queryByText("Where is Assetto Corsa installed?")).toBeNull();
  });
});
