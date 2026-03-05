import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StepAiProvider } from "../../../src/components/onboarding/StepAiProvider";

vi.mock("../../../src/lib/api", () => ({
  apiPost: vi.fn(),
}));

import { apiPost } from "../../../src/lib/api";

const mockedApiPost = vi.mocked(apiPost);

function renderWithQuery(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>,
  );
}

const defaultProps = {
  provider: "anthropic",
  onProviderChange: vi.fn(),
  apiKey: "",
  onApiKeyChange: vi.fn(),
  onNext: vi.fn(),
  onBack: vi.fn(),
  onSkip: vi.fn(),
};

describe("StepAiProvider", () => {
  beforeEach(() => {
    mockedApiPost.mockResolvedValue({ valid: true, message: "Key is valid." });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("renders provider selector and key input", () => {
    renderWithQuery(<StepAiProvider {...defaultProps} />);
    expect(screen.getByText("Connect an AI provider")).toBeDefined();
    expect(screen.getByDisplayValue("Anthropic Claude")).toBeDefined();
    expect(screen.getByPlaceholderText("Enter your API key")).toBeDefined();
  });

  it("key is masked by default", () => {
    renderWithQuery(<StepAiProvider {...defaultProps} apiKey="sk-secret" />);
    const input = screen.getByPlaceholderText("Enter your API key") as HTMLInputElement;
    expect(input.type).toBe("password");
  });

  it("toggle reveals key text", () => {
    renderWithQuery(<StepAiProvider {...defaultProps} apiKey="sk-secret" />);
    fireEvent.click(screen.getByText("Show"));
    const input = screen.getByPlaceholderText("Enter your API key") as HTMLInputElement;
    expect(input.type).toBe("text");
  });

  it("Test Connection calls POST /config/validate-api-key and shows result", async () => {
    mockedApiPost.mockResolvedValue({ valid: true, message: "API key is valid." });

    renderWithQuery(<StepAiProvider {...defaultProps} apiKey="sk-ant-test" />);

    fireEvent.click(screen.getByText("Test Connection"));

    await waitFor(() => {
      expect(mockedApiPost).toHaveBeenCalledWith("/config/validate-api-key", {
        provider: "anthropic",
        api_key: "sk-ant-test",
      });
    });

    await waitFor(() => {
      expect(screen.getByText(/API key is valid/)).toBeDefined();
    });
  });

  it("Skip calls onSkip", () => {
    const onSkip = vi.fn();
    renderWithQuery(<StepAiProvider {...defaultProps} onSkip={onSkip} />);
    fireEvent.click(screen.getByText("Skip for now"));
    expect(onSkip).toHaveBeenCalled();
  });

  it("Test Connection disabled when no key", () => {
    renderWithQuery(<StepAiProvider {...defaultProps} apiKey="" />);
    const btn = screen.getByText("Test Connection");
    expect(btn).toBeDisabled();
  });

  it("Back button calls onBack", () => {
    const onBack = vi.fn();
    renderWithQuery(<StepAiProvider {...defaultProps} onBack={onBack} />);
    fireEvent.click(screen.getByText("Back"));
    expect(onBack).toHaveBeenCalled();
  });

  it("Next button calls onNext", () => {
    const onNext = vi.fn();
    renderWithQuery(<StepAiProvider {...defaultProps} onNext={onNext} />);
    fireEvent.click(screen.getByText("Next"));
    expect(onNext).toHaveBeenCalled();
  });
});
