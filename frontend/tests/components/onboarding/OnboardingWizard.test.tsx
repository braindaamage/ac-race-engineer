import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { OnboardingWizard } from "../../../src/components/onboarding/OnboardingWizard";

// Mock the api module
vi.mock("../../../src/lib/api", () => ({
  apiGet: vi.fn(),
  apiPatch: vi.fn(),
  apiPost: vi.fn(),
}));

import { apiGet, apiPatch, apiPost } from "../../../src/lib/api";

const mockedApiGet = vi.mocked(apiGet);
const mockedApiPatch = vi.mocked(apiPatch);
const mockedApiPost = vi.mocked(apiPost);

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

describe("OnboardingWizard", () => {
  beforeEach(() => {
    mockedApiGet.mockResolvedValue({
      ac_install_path: "",
      setups_path: "",
      llm_provider: "anthropic",
      llm_model: "",
      ui_theme: "dark",
      api_key: "",
      onboarding_completed: false,
    });
    mockedApiPatch.mockResolvedValue({
      ac_install_path: "",
      setups_path: "",
      llm_provider: "anthropic",
      llm_model: "",
      ui_theme: "dark",
      api_key: "",
      onboarding_completed: true,
    });
    mockedApiPost.mockResolvedValue({ status: "valid", message: "OK" });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders Step 1 initially", () => {
    renderWithQuery(<OnboardingWizard onComplete={() => {}} />);
    expect(
      screen.getByText("Where is Assetto Corsa installed?"),
    ).toBeDefined();
    expect(screen.getByText("Step 1 of 4")).toBeDefined();
  });

  it("navigates forward to Step 2", () => {
    renderWithQuery(<OnboardingWizard onComplete={() => {}} />);
    fireEvent.click(screen.getByText("Next"));
    expect(screen.getByText("Where are your setup files?")).toBeDefined();
    expect(screen.getByText("Step 2 of 4")).toBeDefined();
  });

  it("navigates backward from Step 2 to Step 1", () => {
    renderWithQuery(<OnboardingWizard onComplete={() => {}} />);
    fireEvent.click(screen.getByText("Next"));
    fireEvent.click(screen.getByText("Back"));
    expect(
      screen.getByText("Where is Assetto Corsa installed?"),
    ).toBeDefined();
  });

  it("preserves input state across navigation", () => {
    renderWithQuery(<OnboardingWizard onComplete={() => {}} />);

    const input = screen.getByRole("textbox");
    fireEvent.change(input, { target: { value: "C:\\Games\\AC" } });
    fireEvent.click(screen.getByText("Next"));

    // Go back
    fireEvent.click(screen.getByText("Back"));

    const restoredInput = screen.getByRole("textbox") as HTMLInputElement;
    expect(restoredInput.value).toBe("C:\\Games\\AC");
  });

  it("navigates to Step 3 (AI provider placeholder)", () => {
    renderWithQuery(<OnboardingWizard onComplete={() => {}} />);
    fireEvent.click(screen.getByText("Next")); // Step 2
    fireEvent.click(screen.getByText("Next")); // Step 3
    expect(screen.getByText("Connect an AI provider")).toBeDefined();
    expect(screen.getByText("Step 3 of 4")).toBeDefined();
  });

  it("skip AI step navigates to Step 4", () => {
    renderWithQuery(<OnboardingWizard onComplete={() => {}} />);
    fireEvent.click(screen.getByText("Next")); // 2
    fireEvent.click(screen.getByText("Next")); // 3
    fireEvent.click(screen.getByText("Skip for now"));
    expect(screen.getByText("Review your configuration")).toBeDefined();
  });

  it("Finish calls PATCH /config with onboarding_completed true", async () => {
    const onComplete = vi.fn();
    renderWithQuery(<OnboardingWizard onComplete={onComplete} />);

    // Navigate to Step 4
    fireEvent.click(screen.getByText("Next")); // 2
    fireEvent.click(screen.getByText("Next")); // 3
    fireEvent.click(screen.getByText("Skip for now")); // 4

    await act(async () => {
      fireEvent.click(screen.getByText("Finish"));
    });

    await waitFor(() => {
      expect(mockedApiPatch).toHaveBeenCalledWith(
        "/config",
        expect.objectContaining({ onboarding_completed: true }),
      );
    });

    await waitFor(() => {
      expect(onComplete).toHaveBeenCalled();
    });
  });

  it("shows progress dots", () => {
    const { container } = renderWithQuery(
      <OnboardingWizard onComplete={() => {}} />,
    );
    const dots = container.querySelectorAll(".ace-onboarding__progress-dot");
    expect(dots.length).toBe(4);
    // First dot is active
    expect(
      dots[0]!.classList.contains("ace-onboarding__progress-dot--active"),
    ).toBe(true);
  });
});
